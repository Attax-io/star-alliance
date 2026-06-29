#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────────────────
# Star Alliance — DISPATCH LOG  (PostToolUse, non-blocking)
#
# After a specialist successfully calls dispatch.py, log the dispatch so you
# can audit which agents were called and when. Informational only — never blocks.
# ─────────────────────────────────────────────────────────────────────────────
import json
import sys
import os
import re
from datetime import datetime
from pathlib import Path

LOG_PATH = Path(os.environ.get(
    "STAR_ALLIANCE_DISPATCH_LOG",
    Path(os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd()))
    / ".claude" / "state" / "dispatch-log.jsonl",
))

DISPATCH_MARKER = "dispatch.py"


def _extract_agent(command):
    """Try to extract the agent name from a dispatch.py command."""
    match = re.search(r'dispatch\.py\s+(\S+)', command)
    if match:
        return match.group(1).strip('"\'')
    return "unknown"


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    tool_name = data.get("tool_name", "")
    if tool_name != "Bash":
        sys.exit(0)

    command = (data.get("tool_input") or {}).get("command", "")
    if DISPATCH_MARKER not in command:
        sys.exit(0)

    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "command": command,
        "agent": _extract_agent(command),
    }

    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_PATH, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass  # logging must never break the session

    sys.exit(0)


if __name__ == "__main__":
    main()