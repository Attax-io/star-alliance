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

import uuid

OUTBOX_PATH = Path(os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())) / ".claude" / "state" / "outbox.jsonl"

PROJECT_NAME = "star-alliance"


def device_id_slug():
    """Stable per-machine id: 'mac-' + the OS user. Same convention used by
    turn-cost.py, bin/sa (cmd_log), and tools/backfill_guild.py — never
    derive this independently."""
    import getpass
    try:
        return "mac-" + getpass.getuser()
    except Exception:
        return "mac-unknown"


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    if data.get("tool_name", "") not in ("Task", "Agent"):
        sys.exit(0)

    inp = data.get("tool_input") or {}
    agent = inp.get("subagent_type") or inp.get("subagentType") or "unknown"
    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "kind": "spawn",
        "agent": agent,
        "description": inp.get("description", ""),
    }
    # Phase 3 decision (approved 2026-07-12): STOP the legacy dual-write to
    # dispatch-log.jsonl — outbox only, from now on. Removes the double-count
    # risk of the same spawn landing in both dispatch-log.jsonl (read by some
    # local tooling) AND guild.events via a later backfill pass.
    try:
        outbox_row = {
            "table": "events",
            "client_uuid": str(uuid.uuid4()),
            "payload": {
                "ts": entry["timestamp"],
                "device_id": device_id_slug(),
                "project": PROJECT_NAME,
                "kind": "spawn",
                "subject": agent,
                "detail": entry,
            },
        }
        OUTBOX_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(OUTBOX_PATH, "a") as f:
            f.write(json.dumps(outbox_row) + "\n")
    except Exception:
        pass  # telemetry must never break the session
    sys.exit(0)


if __name__ == "__main__":
    main()
