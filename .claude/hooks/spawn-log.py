#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────────────────
# Star Alliance — SPAWN LOG  (PostToolUse: Task|Agent, non-blocking)
#
# Campaign 2026-07-02_self-enclosed-harness, P5(c). dispatch-log.py only logs
# Hermes dispatch (Bash + dispatch.py) and thinker-attest only logs the main
# session, so Claude subagent spawns (Task/Agent) were invisible in telemetry.
# This records every spawn into the same dispatch-log.jsonl so agent-invocation
# counts reflect reality. Informational only — never blocks.
# ─────────────────────────────────────────────────────────────────────────────
import json
import sys
import os
from datetime import datetime
from pathlib import Path

LOG_PATH = Path(os.environ.get(
    "STAR_ALLIANCE_DISPATCH_LOG",
    Path(os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd()))
    / ".claude" / "state" / "dispatch-log.jsonl",
))


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    if data.get("tool_name", "") not in ("Task", "Agent"):
        sys.exit(0)

    inp = data.get("tool_input") or {}
    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "kind": "spawn",
        "agent": inp.get("subagent_type") or inp.get("subagentType") or "unknown",
        "description": inp.get("description", ""),
    }
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_PATH, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass  # telemetry must never break the session
    sys.exit(0)


if __name__ == "__main__":
    main()
