#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────────────────
# Star Alliance — STOP-THE-LINE GATE  (PreToolUse: Write|Edit|MultiEdit, OPT-IN)
#
# Stolen from SAW's hardest gate (Learning Pool mining, 2026-06-28): a doer must
# not write SOURCE code before acceptance criteria exist. "You are NOT responsible
# for inventing AC." Kills the failure where an agent invents requirements and
# ships them.
#
# Mechanism: when ARMED (touch .claude/state/stop-line-armed), any Write/Edit to a
# SOURCE file is blocked UNLESS the current assistant turn has declared acceptance
# criteria — a line matching:  📋 Acceptance: <…>   (or  AC: <…>).
# Docs / memory / data / config edits never require AC (not implementation).
#
# DISARMED by default → returns exit 0, zero friction. Mirrors verify-gate's
# arm-file pattern so it can be trialled without bricking the tool layer.
# Bypass one turn: SA_SKIP_STOPLINE=1 . Fails OPEN on any internal error.
# ─────────────────────────────────────────────────────────────────────────────
import json
import os
import re

SRC_EXT = {".py", ".js", ".ts", ".tsx", ".jsx", ".mjs", ".cjs", ".sh",
           ".sql", ".go", ".rs", ".rb", ".php", ".vue", ".svelte", ".css"}

AC_RE = re.compile(r"(?:📋\s*)?(?:Acceptance(?:\s*Criteria)?|AC)\s*:", re.IGNORECASE)


def project_dir():
    return os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def armed():
    return os.path.exists(os.path.join(project_dir(), ".claude", "state", "stop-line-armed"))


def target_path(data):
    ti = data.get("tool_input", {})
    return (ti.get("file_path") or ti.get("path") or "").rstrip("/")


def is_source(path):
    _, ext = os.path.splitext(path)
    return ext.lower() in SRC_EXT


def _last_user_index(lines):
    idx = -1
    for i, o in enumerate(lines):
        if o.get("type") != "user":
            continue
        c = o.get("message", {}).get("content")
        is_tr = isinstance(c, list) and any(
            isinstance(b, dict) and b.get("type") == "tool_result" for b in c)
        if not is_tr:
            idx = i
    return idx


def _assistant_text_since(lines, start):
    out = []
    for o in lines[start + 1:]:
        if o.get("type") != "assistant":
            continue
        for b in o.get("message", {}).get("content", []):
            # accept text + output_text blocks (host-coupling resilience)
            if isinstance(b, dict) and b.get("type") in ("text", "output_text"):
                out.append(b.get("text", ""))
    return "\n".join(out)


def check(data):
    """Pure decision: {"exit":0|2, "stderr":str}. Called by sa-pretool.py."""
    if os.environ.get("SA_SKIP_STOPLINE") == "1" or not armed():
        return {"exit": 0}

    tool = data.get("tool_name", "")
    if tool not in {"Write", "Edit", "MultiEdit"}:
        return {"exit": 0}

    path = target_path(data)
    if not path or not is_source(path):
        return {"exit": 0}                      # only code warrants AC

    transcript = data.get("transcript_path")
    if not transcript or not os.path.exists(transcript):
        return {"exit": 0, "stderr": "[stop-line] no transcript, failing open\n"}

    try:
        lines = [json.loads(l) for l in open(transcript) if l.strip()]
    except Exception as e:
        return {"exit": 0, "stderr": f"[stop-line] read error, failing open: {e}\n"}

    ui = _last_user_index(lines)
    text = _assistant_text_since(lines, ui)
    # Race grace: at the FIRST tool of a turn the assistant text isn't flushed yet
    # (same grace workflow-gate uses). Once AC is declared it persists for the whole
    # turn — _assistant_text_since collects ALL turn text, so edit #2 still sees it.
    if not text.strip():
        return {"exit": 0}

    if AC_RE.search(text):
        return {"exit": 0}                      # acceptance criteria declared

    return {
        "exit": 2,
        "stderr": (
            "⛔ STOP-THE-LINE GATE — writing SOURCE without declared acceptance "
            "criteria.\n"
            f"   file: {path}\n"
            "   A doer must not invent requirements. Before editing code, declare what\n"
            "   'done' means — emit a line like:\n"
            "       📋 Acceptance: <observable criteria the change must satisfy>\n"
            "   then retry. If the task genuinely has no AC, route to the architect/\n"
            "   strategist to define it first.\n"
            "   Bypass one turn: SA_SKIP_STOPLINE=1 . Disarm: rm "
            ".claude/state/stop-line-armed\n"
        ),
    }


def main():
    import sys
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)
    r = check(data)
    if r.get("stderr"):
        sys.stderr.write(r["stderr"])
    sys.exit(r.get("exit", 0))


if __name__ == "__main__":
    main()
