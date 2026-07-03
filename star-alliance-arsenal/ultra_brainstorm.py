#!/usr/bin/env python3
"""ultra_brainstorm.py — deprecated fan-out runner (Claude-only harness).

WHAT CHANGED
------------
This script used to fire a panel of external, non-Claude "bench" models (over the
now-removed summon.py) to get independent brainstorm candidates for the
`ultra-brainstorming` skill. The guild is now **Claude-only**: there is no
external doer/bench layer to fan out to.

Ultra-brainstorming now runs as **parallel Claude subagents**. The orchestrator
(the live session) spawns several Claude helpers with the Task/Agent tool — each
seeded with the same brief but a distinct angle — then converges and synthesizes
their candidates itself. That fan-out is native to the session, so no external
runner is needed.

HOW TO RUN THE PANEL NOW (in the orchestrating session, not this script):
    For a brief B, spawn N Task/Agent calls in ONE message so they run
    concurrently. Give each the same brief and the panel instruction below, ask
    each for ONE JSON candidate, then converge in Phases 3-5 of the skill.

This file is kept only so old references don't break. Invoked directly, it prints
this explanation as JSON and exits non-zero (nothing was run).

See: ../star-alliance-skills/ultra-brainstorming/SKILL.md
"""

import json
import sys

PANEL_SYSTEM = (
    "You are ONE independent mind on a multi-model brainstorm panel. Other minds "
    "see the same brief separately; your value is a DIFFERENT angle, not consensus. "
    "Read the brief and respond with ONLY a JSON object, no prose around it: "
    '{"best_plan":["step 1","step 2","step 3"],'
    '"heaviest_risk":"the single risk you weigh most",'
    '"orphan_idea":"one idea you doubt any other mind would propose"}'
)


def main():
    msg = (
        "ultra_brainstorm.py is deprecated. The guild is Claude-only — there is no "
        "external bench to fan out to. Run the panel as parallel Claude subagents: "
        "spawn several Task/Agent calls in ONE message, each with the same brief and "
        "the panel instruction, then converge and synthesize their candidates in the "
        "orchestrating session. See ../star-alliance-skills/ultra-brainstorming/SKILL.md."
    )
    sys.stderr.write(msg + "\n")
    print(json.dumps({
        "deprecated": True,
        "reason": "Claude-only harness; fan-out is now parallel Claude subagents.",
        "panel_system": PANEL_SYSTEM,
        "how": "Spawn N Task/Agent Claude helpers in one message, then synthesize.",
    }, indent=2))
    sys.exit(2)


if __name__ == "__main__":
    main()
