#!/usr/bin/env python3
"""Fail-open PreToolUse hook skeleton.

Contract:
  - The harness pipes the event payload as JSON on stdin.
  - exit 0  -> allow the tool call (silent).
  - exit 2  -> BLOCK the call; whatever is written to stderr is fed back to the
               model as the reason it must address before proceeding.
  - any unhandled exception MUST fall through to exit 0 (fail open) so a bug in
    this hook can never brick the session by blocking every tool call.

Copy this file, rename it, and fill in `decide()`. Wire it into settings.json:

  "hooks": {
    "PreToolUse": [
      { "matcher": "Bash",
        "hooks": [{ "type": "command",
                    "command": "python3 $CLAUDE_PROJECT_DIR/.claude/hooks/your-gate.py" }] }
    ]
  }
"""
import json
import sys


def decide(event):
    """Return (allow: bool, reason: str).

    `event` is the parsed stdin JSON. For PreToolUse it carries:
      event["tool_name"]   -> e.g. "Bash", "Write", "Edit"
      event["tool_input"]  -> the exact args the model passed (a dict)

    Read defensively — never assume a key exists. Return (False, reason) to
    block; (True, "") to allow. The default below allows everything: replace it.
    """
    tool = event.get("tool_name", "")
    args = event.get("tool_input", {}) or {}

    # --- example rule (delete): block a destructive recursive delete ---------
    if tool == "Bash":
        cmd = args.get("command", "")
        if "rm -rf /" in cmd:
            return False, "Refusing `rm -rf /` — narrow the path or confirm intent."
    # -------------------------------------------------------------------------

    return True, ""


def main():
    # Read stdin once; an empty/garbled payload must not crash the hook.
    raw = sys.stdin.read()
    try:
        event = json.loads(raw) if raw.strip() else {}
    except Exception:
        # Malformed payload -> allow. A parse failure is never a reason to block.
        sys.exit(0)

    allow, reason = decide(event)
    if not allow:
        # Block: reason goes to STDERR (the model's only guidance), exit 2.
        print(reason, file=sys.stderr)
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise  # honor our own exit codes
    except Exception:
        # CARDINAL RULE: any unexpected failure -> allow. Fail open, always.
        sys.exit(0)
