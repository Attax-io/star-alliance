#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────────────────
# Star Alliance — APPROVAL GATE  (PreToolUse: Task|Agent|Edit|Write|MultiEdit, BLOCKING)
#
# THE DOCTRINE: "The Butler frames; the Guild Master approves — the producer
# of the brief never self-approves it." For FULL-tier (high-stakes) work, no
# work tool fires until the Guild Master gives explicit approval.
#
# WHAT THIS HOOK DOES
# ───────────────────
# For the MAIN SESSION (Butler) only, on FULL-tier turns (approval-pending exists):
#
#   • approval-pending exists, approval-granted does NOT → BLOCK all work tools
#     (Task, Agent, Edit, Write, MultiEdit). The Butler must restate the brief,
#     dispatch the Strategist for routing, and halt for the Guild Master's "go."
#   • approval-granted exists → ALLOW. The Guild Master said go — work proceeds.
#   • Neither exists (LITE/NONE tier) → ALLOW. Low-stakes turns don't need approval.
#   • approval-pending exists AND approval-granted exists → ALLOW (edge case:
#     the detect hook should have cleared pending, but allow if both exist).
#
# Child sessions (the Strategist, specialists) are EXEMPT — they don't need
# the Guild Master's approval; the Butler already got it before dispatching them.
#
# The gate ALLOWS:
#   • Read-only tools (Read, Glob, Grep, Bash-read-only, WebFetch, etc.) — the
#     Butler can investigate and restate without approval.
#   • Task/Agent with subagent_type="the-strategist" — the Butler may always
#     dispatch the Strategist to route the request (routing happens BEFORE
#     approval; the Strategist's output is what the Butler restates to the
#     Guild Master for approval).
#
# BYPASSES — STRICT MODE
# ──────────────────────
# No agent-controlled bypass. Kill switches:
#   • evolution/DISARMED                        (engine-wide)
#   • .claude/state/approval-gate-disarmed       (this hook only)
#
# FAIL POSTURE
# ────────────
# Fail OPEN on any internal error — a broken gate must never brick the session.
# ─────────────────────────────────────────────────────────────────────────────
import os
import sys
import json

# Work tools that are blocked until approval.
WORK_TOOLS = {"Task", "Agent", "Edit", "Write", "MultiEdit", "NotebookEdit"}


def _proj():
    return os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def _state_dir():
    return os.path.join(_proj(), ".claude", "state")


def _is_kill_switch():
    if os.path.exists(os.path.join(_proj(), "evolution", "DISARMED")):
        return True
    if os.path.exists(os.path.join(_state_dir(), "approval-gate-disarmed")):
        return True
    return False


def _is_child_session():
    return os.environ.get("CLAUDE_CODE_CHILD_SESSION") == "1"


def _approval_pending():
    return os.path.exists(os.path.join(_state_dir(), "approval-pending"))


def _approval_granted():
    return os.path.exists(os.path.join(_state_dir(), "approval-granted"))


def _is_strategist_spawn(data):
    """Check if this is a Task/Agent spawn for the Strategist."""
    ti = data.get("tool_input", {}) or {}
    sub = (ti.get("subagent_type") or ti.get("subagentType") or "").strip()
    return sub == "the-strategist"


def check(data):
    """Pure decision. Returns {"exit":0|2, "stderr":str, "systemMessage":str}.
    Called by the sa-pretool.py dispatcher.
    """
    if _is_kill_switch():
        return {"exit": 0}

    # Only fire in the main session (Butler). Child sessions are exempt.
    if _is_child_session():
        return {"exit": 0}

    tool = data.get("tool_name", "")
    if tool not in WORK_TOOLS:
        return {"exit": 0}

    # Only fire on FULL-tier turns (approval-pending exists).
    if not _approval_pending():
        return {"exit": 0}

    # Approval already granted — work proceeds.
    if _approval_granted():
        return {"exit": 0}

    # The Butler may always dispatch the Strategist — routing happens BEFORE
    # approval. The Strategist's routing decision is what the Butler restates
    # to the Guild Master for approval.
    if tool in ("Task", "Agent") and _is_strategist_spawn(data):
        return {"exit": 0}

    # Approval pending, not yet granted, not a Strategist dispatch → BLOCK.
    return {
        "exit": 2,
        "stderr": (
            "⛔ APPROVAL GATE — this is a high-stakes turn and the Guild Master "
            "has not yet approved the brief. You must:\n"
            "   1. Dispatch the Strategist to route the request (if not yet done):\n"
            "        Task(subagent_type=\"the-strategist\", prompt=\"<the brief>\")\n"
            "   2. Restate the brief to the Guild Master in plain English — what "
            "will be touched, what the Strategist recommends.\n"
            "   3. HALT and wait for the Guild Master's explicit \"go.\"\n"
            "   Do not start the work until the Guild Master says go. The producer "
            "of the brief never self-approves it.\n"
            "   No agent-controlled bypass. If this was misclassified as high-stakes, "
            "the user can disable the hook:\n"
            "     touch .claude/state/approval-gate-disarmed\n"
        ),
    }


def main():
    try:
        data = json.load(sys.stdin)
    except Exception as e:
        sys.stderr.write(f"[approval-gate] malformed payload, failing open: {e}\n")
        sys.exit(0)
    r = check(data)
    if r.get("stderr"):
        sys.stderr.write(r["stderr"])
    sys.exit(r.get("exit", 0))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        sys.stderr.write(f"[approval-gate] {e}, failing open\n")
        sys.exit(0)