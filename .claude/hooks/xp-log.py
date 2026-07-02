#!/usr/bin/env python3
"""
Star Alliance — XP LOG  (post_tool_call, non-blocking).

Port of .claude/hooks/xp-log.py. Appends ONE line to .claude/state/xp-log.jsonl
every time a Skill tool fires. This is the single source of truth for skill XP.

Hermes-side: fires on skill_view, skills_list, skill_manage (plus the Claude
Skill/skills/skill names for parity). Extracts the skill name from whichever
input field the surface uses.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import load_payload, project_root  # noqa: E402

# Tool names that count as a skill "fire" on either surface.
_SKILL_TOOLS = frozenset({
    # Claude Code
    "Skill", "skills", "skill",
    # Hermes Agent
    "skill_view", "skills_list", "skill_manage",
})


def main() -> int:
    try:
        payload = load_payload()
        tool = payload.get("tool_name", "")
        if tool not in _SKILL_TOOLS:
            return 0
        ti = payload.get("tool_input") or {}

        # Try every known input field for the skill name.
        # Claude's Skill tool uses "skill" or "name".
        # Hermes skill_view uses "name". skill_manage uses "name".
        # skills_list has no single skill name — skip it (it's a listing, not a fire).
        if tool == "skills_list":
            return 0

        name = ti.get("skill") or ti.get("name")
        if not name:
            return 0

        entry = {
            "type": "skill",
            "name": str(name).strip(),
            "ts": datetime.now(timezone.utc).isoformat(),
            "surface": "hermes",  # tag the origin for future analysis
        }
        path = os.path.join(project_root(), ".claude", "state", "xp-log.jsonl")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "a") as fh:
            fh.write(json.dumps(entry) + "\n")
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())