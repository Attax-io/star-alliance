#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────────────────
# Star Alliance — XP LOG  (PostToolUse · Skill, non-blocking, fail-OPEN)
#
# Appends ONE line to .claude/state/xp-log.jsonl every time a Skill tool fires:
#   {"type": "skill", "name": "<skill id>", "ts": "<iso8601>"}
#
# This is the single source of truth for skill XP (see tools/xp.py, which
# counts these lines to derive a live level). Workflow XP is appended by
# workflow-gate.py (once-per-turn, on a valid banner) — NOT here.
#
# Uses CLAUDE_PROJECT_DIR (not cwd) so CHILD / subagent sessions — which run
# their own copy of this hook — still write to the SAME repo-root log file.
# Append-only, fail-OPEN: any error here must never block or brick a turn.
# ─────────────────────────────────────────────────────────────────────────────
import json
import os
import sys
from datetime import datetime, timezone


def project_dir() -> str:
    return os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def log_path() -> str:
    return os.path.join(project_dir(), ".claude", "state", "xp-log.jsonl")


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)  # malformed payload — fail open, never block

    try:
        tool = data.get("tool_name", "")
        if tool != "Skill":
            sys.exit(0)

        ti = data.get("tool_input", {}) or {}
        name = ti.get("skill") or ti.get("name")
        if not name:
            sys.exit(0)  # no resolvable skill name — nothing to log, still allow

        entry = {
            "type": "skill",
            "name": str(name).strip(),
            "ts": datetime.now(timezone.utc).isoformat(),
        }

        path = log_path()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "a") as fh:
            fh.write(json.dumps(entry) + "\n")
    except Exception:
        pass  # logging must NEVER break the session — fail open

    sys.exit(0)


if __name__ == "__main__":
    main()
