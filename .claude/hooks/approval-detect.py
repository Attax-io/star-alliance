#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────────────────
# Star Alliance — APPROVAL DETECTION  (UserPromptSubmit, non-blocking)
#
# THE DOCTRINE: "The Butler frames; the Guild Master approves — the producer
# of the brief never self-approves it." For FULL-tier (high-stakes) work, the
# Butler must restate the request and HALT for the Guild Master's explicit "go"
# before any work starts.
#
# This hook is the state machine that drives the approval gate. It runs on
# every UserPromptSubmit and manages two state files:
#
#   .claude/state/approval-pending  — set when a FULL-tier request arrives and
#      cleared when the Guild Master says "go" (or on a genuinely new request).
#      Its presence tells approval-gate.py to block work tools.
#   .claude/state/approval-granted  — set when the Guild Master says "go".
#      Its presence tells approval-gate.py to allow work tools.
#
# FLOW:
#   Turn 1 (FULL request):  approval-detect reads prompt → classifies FULL →
#      sets approval-pending → approval-gate blocks work tools → Butler
#      dispatches Strategist, restates, halts for "go."
#   Turn 2 ("go"):  approval-detect reads prompt → detects approval keywords →
#      clears approval-pending, sets approval-granted → approval-gate allows
#      work tools → specialist dispatched → work done → report.
#   Turn 3 (new request):  approval-detect reads prompt → detects a new FULL
#      request (not approval, not chat) → clears old approval state, sets new
#      approval-pending → gate re-arms.
#
# The approval state files are cleared at the start of each genuinely new user
# turn (not on blocking-Stop re-prompts). "Genuinely new" means the prompt is
# not an approval keyword and the turn-start sentinel was reset.
#
# FAIL POSTURE
# ────────────
# Fail OPEN on any internal error — a broken detection must never block the
# user's prompt from being submitted. If this hook crashes, the gate defaults
# to allowing work (no state files = no gate).
# ─────────────────────────────────────────────────────────────────────────────
import sys
import os
import json
import re

# Keywords that signal the Guild Master is approving the brief. Intentionally
# broad — we'd rather false-positive on approval (letting work proceed) than
# false-negative (trapping the session in an approval loop). The Guild Master
#'s "go" can be casual: "go", "proceed", "approved", "do it", "yes go ahead".
APPROVAL_KEYWORDS = [
    # Direct approval
    "go ahead", "go for it", "go", "proceed", "approved", "approve it",
    "do it", "do the", "yes go", "ok go", "okay go", "sure go",
    "green light", "greenlight", "ship it", "make it so", "execute",
    "run it", "start the work", "start work", "begin",
    # Casual
    "yes", "ok", "okay", "sure", "yep", "yeah", "go for it",
    # "go" alone (most common) — but must be a standalone or near-standalone
]

# Keywords that signal a genuinely NEW request (not an approval, not chat).
# If the prompt contains a stake keyword AND is not an approval, it's a new
# FULL request → reset approval state and set approval-pending.
NEW_REQUEST_SIGNALS = [
    "migration", "migrate", "alter table", "drop table", "drop column",
    "rename", "git push", "force push", "force-push", "reset --hard",
    "prod", "production", "deploy", "release", "rm -rf", "delete", "truncate",
    "rls", "policy", "secret", "api key", "credential", "schema change",
    "mass edit", "all files", "every file", "across the repo", "rewrite all",
    "build", "refactor", "feature", "implement", "design", "create",
    "audit", "campaign", "overhaul", "redesign", "architecture",
]

# Read the same policy the routing gate uses, to determine FULL tier.
def _load_policy():
    proj = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    try:
        with open(os.path.join(proj, "data", "harness.json"), encoding="utf-8") as fh:
            return json.load(fh).get("policy", {})
    except Exception:
        return {}


def _is_full_tier(prompt, policy):
    """Determine if the prompt is FULL tier (same logic as guild-routing-gate.sh)."""
    p = (prompt or "").lower().strip()
    if not p:
        return True  # empty → FULL (fail-safe)

    stakes = policy.get("stakes_keywords", [])
    small = policy.get("size_small_signals", [])
    large = policy.get("size_large_signals", [])
    chat = policy.get("chat_signals", [])
    short_chars = int(policy.get("size_short_chars", 400))

    if any(k in p for k in stakes):
        return True
    has_small = any(k in p for k in small)
    has_large = any(k in p for k in large)
    has_chat = any(k in p for k in chat)
    short = len(p) <= short_chars
    if has_chat and short and not has_large:
        return False  # NONE tier
    return not (has_small and not has_large and short)  # LITE → False; else FULL


def _is_approval(prompt):
    """Check if the prompt is an approval message from the Guild Master."""
    p = (prompt or "").lower().strip()
    if not p:
        return False
    # Short prompts that match approval keywords
    if len(p) > 200:
        return False  # long prompts are real requests, not approvals
    for kw in APPROVAL_KEYWORDS:
        if kw in p:
            return True
    return False


def _state_dir():
    proj = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    return os.path.join(proj, ".claude", "state")


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    prompt = (data.get("prompt") or "").strip()
    state = _state_dir()
    os.makedirs(state, exist_ok=True)

    approval_pending = os.path.join(state, "approval-pending")
    approval_granted = os.path.join(state, "approval-granted")
    strategist_dispatched = os.path.join(state, "strategist-dispatched")

    # Check if this is an approval from the Guild Master.
    if _is_approval(prompt):
        # Guild Master said "go" — clear pending, set granted.
        try:
            if os.path.exists(approval_pending):
                os.remove(approval_pending)
        except OSError:
            pass
        try:
            with open(approval_granted, "w") as fh:
                fh.write("1")
        except OSError:
            pass
        # Print a system message so the model knows approval was detected.
        print(json.dumps({
            "systemMessage": (
                "✅ APPROVAL DETECTED — the Guild Master approved the brief. "
                "The work gate is now open. Proceed with the specialist dispatch."
            )
        }))
        sys.exit(0)

    # Not an approval — check if this is a new FULL-tier request.
    policy = _load_policy()
    if _is_full_tier(prompt, policy):
        # New FULL request — reset all approval state and set pending.
        for f in (approval_granted, strategist_dispatched):
            try:
                if os.path.exists(f):
                    os.remove(f)
            except OSError:
                pass
        try:
            with open(approval_pending, "w") as fh:
                fh.write("1")
        except OSError:
            pass
    else:
        # LITE or NONE — not a FULL request. Clear any stale approval state
        # so the gate doesn't fire on a non-FULL turn.
        for f in (approval_pending, approval_granted, strategist_dispatched):
            try:
                if os.path.exists(f):
                    os.remove(f)
            except OSError:
                pass

    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        sys.stderr.write(f"[approval-detect] {e}, failing open\n")
        sys.exit(0)