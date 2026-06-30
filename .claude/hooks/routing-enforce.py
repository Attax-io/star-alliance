#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────────────────
# Star Alliance — ROUTING ENFORCEMENT  (PreToolUse: Task|Agent, BLOCKING)
#
# THE DOCTRINE: "The Butler is the voice, not the router." He hands the brief to
# the Strategist, and the Strategist decides who handles what. The Butler never
# picks specialists directly.
#
# Until now this was prose only — the routing gate injected "the Strategist
# routes" as text, but nothing mechanically stopped the Butler from spawning
# Task(subagent_type="the-architect") directly, stepping right over the
# Strategist. This gate closes that hole.
#
# WHAT THIS HOOK DOES
# ───────────────────
# For the MAIN SESSION (Butler) only, on FULL-tier turns:
#
#   1. Task/Agent with subagent_type="the-strategist" → ALLOW (and write
#      `strategist-dispatched` state file so subsequent specialist spawns pass).
#   2. Task/Agent with subagent_type in SPECIALISTS → BLOCK unless
#      `strategist-dispatched` exists. If it exists, the Strategist was
#      consulted this exchange → ALLOW. If not → BLOCK with instructions to
#      dispatch the Strategist first.
#   3. Task/Agent with any other subagent_type (Explore, general-purpose, …)
#      → ALLOW (non-guild agents are not routed by the Strategist).
#
# Child sessions (the Strategist, specialists) are EXEMPT — the Strategist IS
# the router and may spawn specialists freely. Only the Butler (main session)
# is gated.
#
# LITE and NONE tiers are EXEMPT — low-stakes quick fixes don't need the
# Strategist. The gate fires only when `approval-pending` exists (FULL tier).
#
# BYPASSES — STRICT MODE
# ──────────────────────
# No agent-controlled bypass. Kill switches:
#   • evolution/DISARMED                        (engine-wide)
#   • .claude/state/routing-enforce-disarmed     (this hook only)
#
# FAIL POSTURE
# ────────────
# Fail OPEN on any internal error — a broken gate must never brick the session.
# ─────────────────────────────────────────────────────────────────────────────
import os
import sys
import json

# Guild specialists — the agents the Butler must NOT spawn directly.
# The Strategist is excluded (he is the router, not a specialist).
SPECIALISTS = {
    "the-architect", "the-developer", "the-designer", "the-herald",
    "the-merchant", "the-quartermaster", "the-interpreter", "the-steward",
    "the-connector",
}
ROUTER = "the-strategist"


def _proj():
    return os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def _state_dir():
    return os.path.join(_proj(), ".claude", "state")


def _is_kill_switch():
    if os.path.exists(os.path.join(_proj(), "evolution", "DISARMED")):
        return True
    if os.path.exists(os.path.join(_state_dir(), "routing-enforce-disarmed")):
        return True
    return False


def _is_child_session():
    return os.environ.get("CLAUDE_CODE_CHILD_SESSION") == "1"


def _approval_pending():
    """Check if we're in a FULL-tier approval flow (approval-pending exists)."""
    return os.path.exists(os.path.join(_state_dir(), "approval-pending"))


def _strategist_dispatched():
    """Check if the Strategist has been dispatched this exchange."""
    return os.path.exists(os.path.join(_state_dir(), "strategist-dispatched"))


def check(data):
    """Pure decision. Returns {"exit":0|2, "stderr":str, "systemMessage":str}.
    Called by the sa-pretool.py dispatcher.
    """
    if _is_kill_switch():
        return {"exit": 0}

    # Only fire in the main session (Butler). Child sessions are exempt —
    # the Strategist IS the router and may spawn specialists freely.
    if _is_child_session():
        return {"exit": 0}

    tool = data.get("tool_name", "")
    if tool not in ("Task", "Agent"):
        return {"exit": 0}

    # Only fire on FULL-tier turns (approval-pending exists).
    # LITE and NONE turns don't need routing enforcement.
    if not _approval_pending():
        return {"exit": 0}

    ti = data.get("tool_input", {}) or {}
    sub = (ti.get("subagent_type") or ti.get("subagentType") or "").strip()

    # The Strategist — always allowed. Write the dispatched flag so
    # subsequent specialist spawns know the Strategist was consulted.
    if sub == ROUTER:
        try:
            with open(os.path.join(_state_dir(), "strategist-dispatched"), "w") as fh:
                fh.write("1")
        except OSError:
            pass
        return {"exit": 0}

    # A specialist — block unless the Strategist was dispatched first.
    if sub in SPECIALISTS:
        if _strategist_dispatched():
            return {"exit": 0}
        return {
            "exit": 2,
            "stderr": (
                "⛔ ROUTING ENFORCE — you are trying to spawn The " +
                sub.replace("the-", "").replace("-", " ").title() +
                f" ({sub}) directly. The Butler does not pick specialists — "
                f"that is the Strategist's job. You must dispatch the Strategist "
                f"first:\n"
                f"     Task(subagent_type=\"the-strategist\", prompt=\"<the brief>\")\n"
                f"   The Strategist will read the brief, decide which specialist(s) "
                f"handle the work, and return the routing decision. Then you restate "
                f"it and halt for the Guild Master's approval.\n"
                f"   No agent-controlled bypass. If this is genuinely a non-FULL "
                f"task that was misclassified, the user can disable the hook:\n"
                f"     touch .claude/state/routing-enforce-disarmed\n"
            ),
        }

    # Non-guild subagent (Explore, general-purpose, …) — allow.
    return {"exit": 0}


def main():
    try:
        data = json.load(sys.stdin)
    except Exception as e:
        sys.stderr.write(f"[routing-enforce] malformed payload, failing open: {e}\n")
        sys.exit(0)
    r = check(data)
    if r.get("stderr"):
        sys.stderr.write(r["stderr"])
    sys.exit(r.get("exit", 0))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        sys.stderr.write(f"[routing-enforce] {e}, failing open\n")
        sys.exit(0)