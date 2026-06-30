#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────────────────
# Star Alliance — DEV-SERVER GATE  (PreToolUse: Bash + preview_start, BLOCKING)
#
# THE RULE: agents must not start a dev server or open a browser preview on
# their own. Visual verification — "does it look right?" — is the Guild
# Master's job. If an agent spins up a server it can't see, it is faking a
# check that only a human can perform.
#
# What it blocks:
#   Bash — any command that boots a local web server:
#     npm/yarn/pnpm/bun run dev|start|serve|preview
#     next dev|start  ·  vite  ·  vite preview
#     npx serve|http-server|live-server|vite|next
#     webpack serve  ·  webpack-dev-server
#     parcel  ·  http-server  ·  live-server  ·  serve (standalone)
#     python -m http.server / SimpleHTTPServer
#     uvicorn  ·  gunicorn  ·  flask run
#     rails server / rails s  ·  ng serve
#     gatsby develop|serve  ·  hugo server  ·  jekyll serve
#     php -S  ·  deno task dev|serve
#   MCP tool — mcp__Claude_Preview__preview_start
#
# POSTURE: fail OPEN on any internal error (a broken gate must never brick the
# session). Kill switch: evolution/DISARMED (engine-wide) or
# .claude/state/devserver-gate-disarmed (this gate only).
# ─────────────────────────────────────────────────────────────────────────────
import os
import re
import sys
import json

# MCP preview tool that boots a preview server
PREVIEW_START_TOOL = "mcp__Claude_Preview__preview_start"

# Patterns that indicate a dev/web server is being started.
# Each entry: (label, compiled regex)
_PATTERNS = [
    # package-manager run scripts
    ("npm run dev/start/serve/preview",
     re.compile(r"\bnpm\s+run\s+(dev|start|serve|preview)\b", re.I)),
    ("npm start",
     re.compile(r"\bnpm\s+start\b", re.I)),
    ("yarn dev/start/serve/preview",
     re.compile(r"\byarn\s+(run\s+)?(dev|start|serve|preview)\b", re.I)),
    ("pnpm dev/start/serve/preview",
     re.compile(r"\bpnpm\s+(run\s+)?(dev|start|serve|preview)\b", re.I)),
    ("bun dev/start/serve/preview",
     re.compile(r"\bbun\s+(run\s+)?(dev|start|serve|preview)\b", re.I)),
    # framework CLIs
    ("next dev/start",
     re.compile(r"\bnext\s+(dev|start)\b", re.I)),
    ("vite",
     re.compile(r"(?<!\w)vite(\s+preview)?\b", re.I)),
    ("gatsby develop/serve",
     re.compile(r"\bgatsby\s+(develop|serve)\b", re.I)),
    ("hugo server",
     re.compile(r"\bhugo\s+server\b", re.I)),
    ("jekyll serve",
     re.compile(r"\bjekyll\s+serve\b", re.I)),
    ("ng serve",
     re.compile(r"\bng\s+serve\b", re.I)),
    ("rails server",
     re.compile(r"\brails\s+(server|s)\b", re.I)),
    ("flask run",
     re.compile(r"\bflask\s+run\b", re.I)),
    ("deno task dev/serve",
     re.compile(r"\bdeno\s+(task|run)\s+(dev|serve)\b", re.I)),
    # bundlers & static servers
    ("webpack serve",
     re.compile(r"\bwebpack(-dev-server)?\s+serve\b", re.I)),
    ("webpack-dev-server",
     re.compile(r"\bwebpack-dev-server\b", re.I)),
    ("parcel",
     re.compile(r"(?<!\w)parcel\b", re.I)),
    ("http-server",
     re.compile(r"\bhttp-server\b", re.I)),
    ("live-server",
     re.compile(r"\blive-server\b", re.I)),
    ("serve (standalone)",
     re.compile(r"(?<![a-z-])serve(\s+|$)", re.I)),
    # npx variants
    ("npx serve/http-server/live-server/vite/next",
     re.compile(r"\bnpx\s+(serve|http-server|live-server|vite|next)\b", re.I)),
    # Python HTTP servers
    ("python -m http.server",
     re.compile(r"\bpython[23]?\s+-m\s+(http\.server|SimpleHTTPServer)\b", re.I)),
    # WSGI/ASGI servers
    ("uvicorn",
     re.compile(r"\buvicorn\b", re.I)),
    ("gunicorn",
     re.compile(r"\bgunicorn\b", re.I)),
    # PHP built-in server
    ("php -S",
     re.compile(r"\bphp\s+-S\b", re.I)),
]


def _kill_switch():
    proj = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    return (
        os.path.exists(os.path.join(proj, "evolution", "DISARMED"))
        or os.path.exists(os.path.join(proj, ".claude", "state", "devserver-gate-disarmed"))
    )


def check(data):
    """Returns {"exit": 0|2, "stderr": str}."""
    if _kill_switch():
        return {"exit": 0}

    tool = data.get("tool_name", "")

    # MCP preview-start tool
    if tool == PREVIEW_START_TOOL:
        return {"exit": 2, "stderr": (
            "⛔ DEV-SERVER GATE — agents must not start a browser preview.\n"
            "   Visual verification is the Guild Master's job — only they can\n"
            "   confirm that what's on screen actually looks right.\n"
            "   Finish the code change, report what you did, and let the Guild\n"
            "   Master open the preview themselves.\n"
        )}

    if tool != "Bash":
        return {"exit": 0}

    cmd = (data.get("tool_input") or {}).get("command", "") or ""
    if not cmd.strip():
        return {"exit": 0}

    for label, pat in _PATTERNS:
        if pat.search(cmd):
            return {"exit": 2, "stderr": (
                f"⛔ DEV-SERVER GATE — matched: {label}\n"
                f"   Command: {cmd.strip()[:300]}\n"
                "   Agents must not start a dev server on their own.\n"
                "   Visual verification is the Guild Master's job — only they\n"
                "   can confirm that what's on screen looks right.\n"
                "   Finish the code change, report what you built, and let\n"
                "   the Guild Master start the server and verify.\n"
            )}

    return {"exit": 0}


def main():
    try:
        data = json.load(sys.stdin)
    except Exception as e:
        sys.stderr.write(f"[devserver-gate] malformed payload, failing open: {e}\n")
        sys.exit(0)
    try:
        r = check(data)
    except Exception as e:
        sys.stderr.write(f"[devserver-gate] error, failing open: {e}\n")
        sys.exit(0)
    if r.get("stderr"):
        sys.stderr.write(r["stderr"])
    sys.exit(r.get("exit", 0))


if __name__ == "__main__":
    main()
