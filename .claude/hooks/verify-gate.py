#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────────────────
# Star Alliance — INDEPENDENT-VERIFICATION GATE  (Stop hook, BLOCKING)
#
# THE DOCTRINE (HARNESS-BOOKS principle 9.9): "verification must be independent —
# never let the system grade its own work." The implementer always believes it's
# "basically done"; a model believes it even harder. So before a turn that changed
# SOURCE code is allowed to close (and turn-finalize commits it), a verification
# must be on record — ideally produced by a DIFFERENT model than the implementer.
#
# WHY THIS PLACEMENT IS SAFE (resolves the panel's heaviest risk — opus's
# "hook-stack collapse"): commits happen in turn-finalize.sh, a LATER Stop hook.
# This gate is wired to run BEFORE turn-finalize. So when it blocks (exit 2),
# turn-finalize never runs and NOTHING is committed — the work stays in the
# working tree, unverified and uncommitted. There is never an un-commit to do.
# Recovery is forward-only ("keep working", principle 9.7): verify → mark → close.
#
# FLOW when it blocks:
#   1. A different member/model reviews the working-tree diff against intent
#      (cheap doer is fine — partitioning, not horsepower, is the point — 9.8).
#   2. Record the pass:
#         python3 .claude/hooks/verify_hash.py > .claude/state/verify-pass
#      (the marker is the fingerprint of the exact diff that was reviewed; any
#       further edit changes the fingerprint and re-arms the gate — re-verify.)
#   3. End the turn again → this gate sees the matching marker → allows →
#      turn-finalize commits the now-verified work.
#
# CONTROLS:
#   • Armed only when  .claude/state/verify-gate-armed  exists (deliberate opt-in).
#   • Bypass one turn:  SA_SKIP_VERIFY=1
#   • Fails OPEN on any internal error — a broken gate must never trap the session.
# ─────────────────────────────────────────────────────────────────────────────
import os
import sys
import json
import subprocess


def main():
    try:
        json.load(sys.stdin)            # drain the Stop payload; we don't need it
    except Exception:
        pass

    proj = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    state = os.path.join(proj, ".claude", "state")

    # Opt-in: do nothing unless explicitly armed.
    if not os.path.exists(os.path.join(state, "verify-gate-armed")):
        sys.exit(0)
    # One-turn human bypass.
    if os.environ.get("SA_SKIP_VERIFY") == "1":
        sys.exit(0)

    hash_script = os.path.join(proj, ".claude", "hooks", "verify_hash.py")
    try:
        cur = subprocess.run(
            ["python3", hash_script], capture_output=True, text=True, timeout=20
        ).stdout.strip()
    except Exception as e:
        sys.stderr.write(f"[verify-gate] hash failed, failing open: {e}\n")
        sys.exit(0)

    # No source changed (or not a repo) → nothing to verify.
    if cur in ("CLEAN", "NOREPO", ""):
        sys.exit(0)

    # Baseline-aware: turn-start.py snapshots the source fingerprint at the start
    # of every REAL turn. If the fingerprint is unchanged since then, nothing was
    # implemented THIS turn — stand aside even when the tree carries pre-existing
    # uncommitted source. Without this the gate fired on ANY dirty tree and
    # re-prompted the model every turn (the "triple response" loop). When the
    # baseline is absent (rare), fall back to the verify-pass comparison below.
    bfile = os.path.join(state, "verify-baseline")
    if not os.path.exists(bfile):
        # No turn-start baseline (the snapshot subprocess failed). We cannot tell
        # what changed THIS turn, so fail OPEN rather than risk re-prompting every
        # turn on a pre-existing dirty tree — consistent with every other hook here.
        sys.exit(0)
    baseline = ""
    try:
        baseline = open(bfile).read().strip()
    except OSError:
        baseline = ""
    if baseline and cur == baseline:
        sys.exit(0)

    passfile = os.path.join(state, "verify-pass")
    prev = ""
    if os.path.exists(passfile):
        try:
            prev = open(passfile).read().strip()
        except OSError:
            prev = ""

    if prev == cur:
        sys.exit(0)                     # this exact diff was independently verified

    sys.stderr.write(
        "⛔ VERIFICATION GATE — source changed this turn but has NOT been "
        "independently verified.\n"
        "   The implementer must not grade its own work (HARNESS-BOOKS 9.9).\n"
        "   1. Have the CRITIC seat (a DIFFERENT model than the brain) review the diff:\n"
        "      COLD  = git diff HEAD | python3 star-alliance-arsenal/critique.py  (glm-5.2, text-only)\n"
        "      GROUNDED = Task a Claude review agent that runs the checks (grep/build/git).\n"
        "   2. Record the pass for THIS exact diff:\n"
        f"        python3 .claude/hooks/verify_hash.py > .claude/state/verify-pass\n"
        f"      (expected fingerprint: {cur})\n"
        "   3. End the turn again — the gate clears and turn-finalize commits.\n"
        "   Nothing is committed while this blocks (forward-fix only, never un-commit).\n"
        "   One-turn bypass: SA_SKIP_VERIFY=1 . Disarm: rm .claude/state/verify-gate-armed\n"
    )
    sys.exit(2)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        sys.stderr.write(f"[verify-gate] {e}, failing open\n")
        sys.exit(0)
