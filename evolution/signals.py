#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────────────────
# Star Alliance — CAPABILITY SIGNALS  (SENSE plumbing for capability-gap discovery)
#
# The correctness loop (verify-gate → ledger verdict) already feeds the scoreboard.
# This module adds the OTHER half the engine was blind to: capability telemetry —
# which skills fire, which fire together, which workflows run or get declared-but-
# unknown, and when a member offloads doer-grade work. Each is one fail-soft
# `metric` event with meta.signal set, so scoreboard.capability() can read it back
# and engine.diagnose() can turn it into skill/workflow/coaching proposals.
#
# Design rules (same as ledger.py): APPEND-ONLY, FAIL-SOFT (never raise, never
# block a hook — this is observability, not control flow), one line per event.
# The PreToolUse hooks (high-alert, weapon-gate, workflow-gate) call emit(); they
# already fail open on their own errors, and emit() swallows everything regardless.
# ─────────────────────────────────────────────────────────────────────────────
from __future__ import annotations

import os
import sys

# Recognized capability signals (kept as a vocabulary so the scoreboard and the
# engine agree on the names; an unknown string still records, just won't be scored).
SKILL_FIRE      = "skill-fire"        # a Skill tool was invoked
MEMBER_DISPATCH = "member-dispatch"   # a real guild-member sub-agent was spawned
DOER_SUMMON     = "doer-summon"       # a doer weapon (summon.py / minimax) was drawn
WORKFLOW_FIRE   = "workflow-fire"     # a valid star-map workflow was declared
WORKFLOW_UNKNOWN = "workflow-unknown" # a workflow name was declared that isn't registered


def _here() -> str:
    return os.path.dirname(os.path.abspath(__file__))


def _turn_id() -> str:
    """The current turn's start-epoch (written by turn-start.py), used to GROUP
    signals that happened in the same turn — co-fire detection needs this, since
    the ledger has no other turn boundary. '' if unavailable (grouping degrades)."""
    proj = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    try:
        with open(os.path.join(proj, ".claude", "state", "turn-start")) as fh:
            return fh.read().strip()
    except OSError:
        return ""


def emit(signal: str, *, surface: str = "", detail: str = "",
         meta: dict | None = None) -> None:
    """Record one capability signal as a fail-soft ledger `metric` event."""
    m = {"signal": signal, "turn": _turn_id()}
    if meta:
        m.update(meta)
    try:
        sys.path.insert(0, _here())
        import ledger  # noqa: E402
        ledger.append(kind="metric", author="sense", surface=surface,
                      detail=detail or signal, meta=m)
    except Exception:
        pass  # observability must never break its caller


def once_per_turn(name: str) -> bool:
    """True the FIRST time it is called this turn for `name`, else False. Backed by
    a sentinel file under .claude/state that turn-start.py clears each new turn —
    so a signal that would otherwise fire on every work-tool call (e.g. the workflow
    banner, re-checked per tool) is recorded once per turn instead of as noise."""
    proj = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    state = os.path.join(proj, ".claude", "state")
    sent = os.path.join(state, name)
    if os.path.exists(sent):
        return False
    try:
        os.makedirs(state, exist_ok=True)
        open(sent, "w").close()
    except OSError:
        pass
    return True
