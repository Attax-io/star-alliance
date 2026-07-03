#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────────────────
# Star Alliance — UNITY GATE  (PreToolUse, advisory systemMessage)
#
# Enforces the "one source of truth" doctrine for code. Before a Developer or
# Architect creates a new file or writes a large new block of declarations, this
# gate injects a mandatory UNITY CHECK reminder.
#
# WHY THIS EXISTS: Fragmentation — the same type, constant, utility, or service
# defined in multiple places — is the #1 cause of cleanup work, token waste, and
# future bugs. The doctrine is "check before you build": if a canonical SoT module
# already exists for this domain, extend it; never create a parallel one.
#
# TRIGGERS:
#   1. Write tool — the file path looks like a new SoT-candidate module (types,
#      constants, config, utils, services, clients, stores, schema, models, api).
#   2. Edit / MultiEdit — the new content introduces >= 3 new top-level declarations
#      AND is substantial (> 200 chars) — signs of a new SoT being minted inline.
#   3. Bash — the command dispatches to the developer or architect Hermes profile.
#
# BEHAVIOUR: non-blocking (exit 0 always). Emits a systemMessage JSON to stdout.
# The developer must confirm the check; the verify-gate critic (Stop hook) blocks
# any diff that introduces actual SoT fragmentation.
#
# FAIL-OPEN: any internal error silently exits 0 — a broken gate must never brick
# a session. The unity doctrine is still enforced by the verify-gate critic.
# ─────────────────────────────────────────────────────────────────────────────
import json
import os
import re
import sys

# File name/path patterns that suggest a new "source of truth" module is being created.
_SOT_PATH_RE = re.compile(
    r"[/\\](types?|constants?|config|utils?|helpers?|hooks?|"
    r"services?|clients?|stores?|schema|models?|api|lib)[/\\]?[^/\\]*"
    r"\.(ts|tsx|js|jsx|py|go|rs)$",
    re.IGNORECASE,
)

# Top-level declaration patterns in new content.
_DECL_RE = re.compile(
    r"^\s*(export\s+)?(const\s+[A-Z_]{2,}|type\s+\w+|interface\s+\w+|"
    r"enum\s+\w+|class\s+\w+|function\s+\w+)",
    re.MULTILINE,
)

# Dispatch command pattern — fires when Bash dispatches to dev or architect.
_DISPATCH_RE = re.compile(
    r"dispatch\.py\s+(the-)?(developer|architect)\b",
    re.IGNORECASE,
)

_MSG = (
    "⚡ UNITY GATE — ONE SOURCE OF TRUTH CHECK\n"
    "\n"
    "Before proceeding, you MUST confirm:\n"
    "  1. Search: does a canonical module for this domain already exist?\n"
    "     (types, constants, config, utils, services, API client, store, schema)\n"
    "  2. If YES  → extend that canonical file; do NOT create a parallel one.\n"
    "  3. If FRAGMENTED (same domain split across multiple files)\n"
    "     → run the code-unity skill (audit → unify phase) BEFORE adding anything new.\n"
    "  4. If genuinely new domain with no existing SoT → proceed, then document\n"
    "     it in CODE-UNITY.md as the new canonical home.\n"
    "\n"
    "The verify-gate critic will BLOCK any diff that introduces new SoT fragmentation.\n"
    "Skill: code-unity  |  Doctrine: CODE-UNITY.md"
)


def _should_fire(payload: dict) -> bool:
    """Return True if this tool call should trigger the unity reminder."""
    tool = payload.get("tool_name", "")
    inp = payload.get("tool_input", {}) or {}

    if tool == "Write":
        path = inp.get("file_path", "")
        return bool(_SOT_PATH_RE.search(path))

    if tool in ("Edit", "MultiEdit"):
        if tool == "Edit":
            new_text = inp.get("new_string", "")
        else:
            new_text = "".join(
                e.get("new_string", "") for e in (inp.get("edits") or [])
            )
        if len(new_text) < 200:
            return False
        return len(_DECL_RE.findall(new_text)) >= 3

    if tool == "Bash":
        cmd = inp.get("command", "")
        return bool(_DISPATCH_RE.search(cmd))

    return False


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    try:
        if _should_fire(payload):
            print(json.dumps({"systemMessage": _MSG}))
    except Exception:
        pass  # fail open — never let this gate block a session

    sys.exit(0)


if __name__ == "__main__":
    main()
