#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────────────────
# Star Alliance — INDEPENDENT-VERIFICATION GATE  (Stop hook, BLOCKING)  v2
#
# THE DOCTRINE (HARNESS-BOOKS 9.9): "verification must be independent — never let
# the system grade its own work." Before a turn that changed SOURCE is allowed to
# close (turn-finalize commits it), an independent verdict must be on record.
#
# v2 — THE EVOLUTION ENGINE'S VERIFY ORGAN. The audit's #1 finding was that the
# Critic existed but nothing called it: the gate only printed prose, so review was
# manual and usually skipped, and a regression shipped through Strategic Audit. v2
# CLOSES the loop:
#   • ARMED BY DEFAULT. No more opt-in touch-file. The gate is the safety rail;
#     a safety rail you must remember to switch on is off when it matters.
#   • AUTO-RUNS the critic (evolution/verdict.py → star-alliance-arsenal/critique.py,
#     glm-5.2, a DIFFERENT model family). On pass/concerns it RECORDS THE PASS
#     itself and allows the turn — no human fingerprint chase. On BLOCK it stops
#     the commit and prints the critic's findings.
#   • LEDGERS every verdict so the scoreboard can measure catch-rate and escapes.
#
# RISK POSTURE — fail OPEN on infrastructure, fail CLOSED on judgment:
#   • Critic unreachable (no network) → DEGRADE to the manual path (print how to
#     review by hand), never hard-trap a human session on infra. Unsupervised
#     routines get their fail-CLOSED guarantee elsewhere: they call
#     verdict.py --fail-closed in their OWN flow before committing (see engine.py).
#   • Critic says BLOCK → stop. That is the gate doing its job.
#
# CONTROLS:
#   • Kill switch: evolution/DISARMED  (disables the whole Evolution Engine) OR the
#     legacy .claude/state/verify-gate-disarmed — either stands the gate down.
#   • One-turn bypass: SA_SKIP_VERIFY=1
#   • Disable auto-critic (manual-only): SA_AUTO_CRITIC=0
#   • Fails OPEN on any internal error — a broken gate must never trap the session.
# ─────────────────────────────────────────────────────────────────────────────
import os
import sys
import json
import subprocess

# Oversized diffs make cold (text-only) critique useless and slow; above this the
# gate asks for a grounded human/agent review instead of auto-passing on a skim.
MAX_AUTOCRITIC_BYTES = 60_000


def _ledger(repo, **kw):
    """Best-effort ledger append; never let observability break the gate."""
    try:
        sys.path.insert(0, os.path.join(repo, "evolution"))
        import ledger  # noqa: E402
        ledger.append(**kw)
    except Exception:
        pass


def main():
    try:
        json.load(sys.stdin)            # drain the Stop payload; we don't need it
    except Exception:
        pass

    proj = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    state = os.path.join(proj, ".claude", "state")

    # Kill switch — one file stands the whole engine (and this gate) down.
    if (os.path.exists(os.path.join(proj, "evolution", "DISARMED")) or
            os.path.exists(os.path.join(state, "verify-gate-disarmed"))):
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

    # Baseline-aware: turn-start.py snapshots the source fingerprint at turn start.
    # Unchanged since then → nothing implemented THIS turn → stand aside even on a
    # pre-existing dirty tree. Absent baseline → fail open (never re-prompt a human
    # every turn on a tree they didn't touch).
    bfile = os.path.join(state, "verify-baseline")
    if not os.path.exists(bfile):
        sys.exit(0)
    try:
        baseline = open(bfile).read().strip()
    except OSError:
        baseline = ""
    if baseline and cur == baseline:
        sys.exit(0)

    # Already verified this exact diff?
    passfile = os.path.join(state, "verify-pass")
    prev = ""
    if os.path.exists(passfile):
        try:
            prev = open(passfile).read().strip()
        except OSError:
            prev = ""
    if prev == cur:
        sys.exit(0)

    # ── Source changed this turn and is unverified. Try the AUTO-CRITIC first. ──
    auto = os.environ.get("SA_AUTO_CRITIC", "1") != "0"
    diff_text = _full_diff(proj)

    if auto and diff_text and len(diff_text.encode("utf-8", "ignore")) <= MAX_AUTOCRITIC_BYTES:
        verdict = _run_critic(proj, diff_text)
        if verdict is not None:
            decision, raw = verdict
            _ledger(proj, kind="verdict", author="glm-5.2", surface="gates",
                    diff_hash=cur, verdict=decision,
                    detail=f"auto-critic at Stop: {decision}")
            if decision in ("pass", "concerns"):
                # Independent review on record → record the pass and ALLOW.
                try:
                    with open(passfile, "w") as fh:
                        fh.write(cur)
                except OSError:
                    pass
                tail = "\n".join(raw.strip().splitlines()[-6:])
                sys.stderr.write(
                    f"✅ VERIFICATION GATE — independent critic (glm-5.2): {decision.upper()}. "
                    f"Auto-recorded; turn may close.\n"
                    + (f"   findings:\n{tail}\n" if decision == "concerns" and tail else ""))
                sys.exit(0)
            if decision == "block":
                _ledger(proj, kind="block", author="glm-5.2", surface="gates",
                        diff_hash=cur, verdict="block",
                        detail="auto-critic BLOCKED the diff at Stop")
                sys.stderr.write(
                    "⛔ VERIFICATION GATE — independent critic (glm-5.2) returned BLOCK.\n"
                    "   The diff has a blocker; nothing is committed. Fix forward, then re-end.\n"
                    "   Critic findings:\n"
                    + "\n".join("     " + ln for ln in raw.strip().splitlines()[-20:]) + "\n"
                    "   (override only if you judge the critic wrong: SA_SKIP_VERIFY=1)\n")
                sys.exit(2)
        # verdict is None → critic unreachable: fall through to the manual path.

    # ── Manual / grounded path (critic offline, disabled, or diff too large) ──
    why = ("diff exceeds auto-critic size cap — grounded review required"
           if len(diff_text.encode("utf-8", "ignore")) > MAX_AUTOCRITIC_BYTES
           else "auto-critic unavailable (offline or disabled)")
    sys.stderr.write(
        "⛔ VERIFICATION GATE — source changed this turn and is not yet verified.\n"
        f"   ({why})\n"
        "   The implementer must not grade its own work (HARNESS-BOOKS 9.9).\n"
        "   1. Independent review of the working-tree diff:\n"
        "      COLD     = git diff HEAD | python3 evolution/verdict.py\n"
        "      GROUNDED = Task a Claude review agent that runs the checks (grep/build/git).\n"
        "   2. Record the pass for THIS exact diff:\n"
        "        python3 .claude/hooks/verify_hash.py > .claude/state/verify-pass\n"
        f"      (expected fingerprint: {cur})\n"
        "   3. End the turn again — the gate clears and turn-finalize commits.\n"
        "   Nothing is committed while this blocks (forward-fix only, never un-commit).\n"
        "   One-turn bypass: SA_SKIP_VERIFY=1 . Kill switch: touch evolution/DISARMED\n")
    sys.exit(2)


# Source extensions the critic should see — must mirror verify_hash.SRC_EXT so the
# fingerprint (which counts untracked source) and the critic see the SAME file set.
# Without the untracked half, a turn that only ADDS new source files sends an empty
# `git diff HEAD` to the critic and auto-passes unreviewed.
_SRC_EXT = {".py", ".js", ".ts", ".tsx", ".jsx", ".mjs", ".cjs", ".sh",
            ".sql", ".go", ".rs", ".rb", ".php", ".vue", ".svelte", ".css"}
_GENERATED = {"guild-data.js", "skill-md.js", "workflow-md.js"}


def _full_diff(proj):
    """`git diff HEAD` PLUS the contents of untracked source files, rendered as
    additions — so the critic reviews exactly what the fingerprint counted."""
    parts = []
    try:
        parts.append(subprocess.run(
            ["git", "-C", proj, "diff", "HEAD"],
            capture_output=True, text=True, timeout=20).stdout)
    except Exception:
        pass
    try:
        untracked = subprocess.run(
            ["git", "-C", proj, "ls-files", "--others", "--exclude-standard"],
            capture_output=True, text=True, timeout=20).stdout.splitlines()
    except Exception:
        untracked = []
    for rel in untracked:
        rel = rel.strip()
        if not rel:
            continue
        base = os.path.basename(rel)
        _, ext = os.path.splitext(rel)
        if ext not in _SRC_EXT or base in _GENERATED:
            continue
        try:
            with open(os.path.join(proj, rel), encoding="utf-8", errors="replace") as fh:
                body = fh.read()
        except OSError:
            continue
        parts.append(f"\n--- /dev/null\n+++ b/{rel}  (new untracked source)\n"
                     + "\n".join("+" + ln for ln in body.splitlines()))
    return "\n".join(p for p in parts if p)


def _run_critic(proj, diff_text):
    """Return (decision, raw) or None if the critic could not be reached."""
    try:
        sys.path.insert(0, os.path.join(proj, "evolution"))
        import verdict as V  # noqa: E402
        # 150s cap: cold critique of a small diff is ~60-120s; on timeout the gate
        # degrades to manual rather than hang a session indefinitely. Fast interactive
        # work can opt out with SA_AUTO_CRITIC=0 and rely on routine-time review.
        v = V.run_cold(diff_text, timeout=150)
        if not v.reached:
            return None
        return v.decision, v.raw
    except Exception as e:
        sys.stderr.write(f"[verify-gate] critic error, degrading to manual: {e}\n")
        return None


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        sys.stderr.write(f"[verify-gate] {e}, failing open\n")
        sys.exit(0)
