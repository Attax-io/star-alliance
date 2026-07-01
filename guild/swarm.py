"""swarm.py — pure swarm-plan resolver for guild/run.py.

run.py is a headless subprocess. It cannot spawn parallel Claude subagents (no
Task tool) — only a live session can. `plan_swarm` never fakes that parallelism;
it turns a step's `swarm` object into a recorded plan so run.py can log the
fan-out that *would* happen in a live session, then degrade to one worker.

Caps are single-sourced from data/harness.json's `swarm_caps` key — the same
file and key tools/conformity_check.py already reads — so doctrine (5/12) can
never diverge between the two readers. Fail-soft: a missing file/key falls back
to the same 5/12 defaults conformity_check.py uses.
"""
from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
HARNESS_JSON = REPO_ROOT / "data" / "harness.json"


def _load_caps() -> dict:
    try:
        cfg = json.loads(HARNESS_JSON.read_text(encoding="utf-8"))
        caps = cfg.get("swarm_caps", {})
    except Exception:
        caps = {}
    return {
        "max_swarm": caps.get("max_swarm", 5),
        "max_total_workers": caps.get("max_total_workers", 12),
    }


def plan_swarm(step: dict) -> dict:
    """Resolve a step's `swarm` object into a recorded (never-executed) plan.

    Returns:
        {
          "fan": bool,          # True iff the step is swarm-worthy
          "instances": int,     # clamped instance count (>=1; 1 when not fanning)
          "member": str | None, # the actor the swarm would fan out
          "partition": str | None,
          "reason": str,        # human-readable verdict, always present
        }

    Worthiness requires: a `swarm` object is present, `max_instances` is an int
    with `max_instances >= min_instances >= 2`, and a `partition` is set. Any
    other shape resolves to fan=False with the reason stated — run.py always
    degrades to the existing single-`delegate()` path regardless of the verdict.
    """
    sw = step.get("swarm")
    if not sw or not isinstance(sw, dict):
        return {
            "fan": False,
            "instances": 1,
            "member": step.get("actor"),
            "partition": None,
            "reason": "no swarm object on this step",
        }

    caps = _load_caps()
    max_swarm = caps["max_swarm"]

    member = sw.get("agent") or sw.get("member") or step.get("actor")
    max_i = sw.get("max_instances")
    min_i = sw.get("min_instances")
    partition = sw.get("partition")

    if not isinstance(max_i, int) or not isinstance(min_i, int):
        return {
            "fan": False,
            "instances": 1,
            "member": member,
            "partition": partition,
            "reason": "max_instances/min_instances missing or not integers",
        }

    if not (max_i >= min_i >= 2):
        return {
            "fan": False,
            "instances": 1,
            "member": member,
            "partition": partition,
            "reason": f"instance bounds not worthy (max_instances={max_i!r}, "
                      f"min_instances={min_i!r}; need max >= min >= 2)",
        }

    if not partition:
        return {
            "fan": False,
            "instances": 1,
            "member": member,
            "partition": partition,
            "reason": "no partition set",
        }

    instances = min(max_i, max_swarm)
    return {
        "fan": True,
        "instances": instances,
        "member": member,
        "partition": partition,
        "reason": f"worthy: {instances}x {member} by {partition} "
                  f"(clamped to max_swarm={max_swarm})",
    }
