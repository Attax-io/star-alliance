#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────────────────
# Star Alliance — INDEPENDENT VERDICT  (the VERIFY organ)
#
# The audit's #1 finding: the Critic (star-alliance-arsenal/critique.py) existed,
# worked, and was a deliberately-different model family — but NOTHING called it.
# The verify-gate only printed prose recommending it; routines self-approved. So a
# regression shipped through Strategic Audit with no independent eyes.
#
# This module closes that gap: it RUNS the critic on a diff and returns a parsed,
# structured verdict that a gate or a routine can branch on. It is the single
# choke point every self-modifying path routes its review through.
#
#   run_cold(diff_text)  -> Verdict   # text-only critic (glm-5.2), ~60-120s
#
# Verdict = {decision: pass|concerns|block|error, raw: <critic text>, model: <id>}
#
# DECISION SEMANTICS (deliberately conservative):
#   block     → the critic found a blocker. The gate MUST stop the commit.
#   concerns  → non-blocking findings. Allowed, but logged to the ledger so the
#               scoreboard tracks concern-density over time.
#   pass      → clean.
#   error     → the critic could not be reached (no network / backend down). This
#               is NOT a pass. Callers decide: a hook FAILS OPEN (never trap a
#               session on infra), a routine FAILS CLOSED (an unsupervised nightly
#               run must not commit unreviewed — it files a proposal instead).
#
# COLD vs GROUNDED: cold critique reads TEXT only and misses *absence* bugs (a
# stale id in a file the diff didn't include). For load-bearing source the gate
# should escalate to a GROUNDED Claude review agent. Cold is the always-available
# floor; grounded is the backstop. See weapon-utility §The Critic seat.
# ─────────────────────────────────────────────────────────────────────────────
from __future__ import annotations

import os
import re
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CRITIQUE = os.path.join(REPO, "star-alliance-arsenal", "critique.py")

_VERDICT_RE = re.compile(r"(?im)^\s*VERDICT:\s*(pass|concerns|block)\b")


class Verdict:
    __slots__ = ("decision", "raw", "model")

    def __init__(self, decision: str, raw: str = "", model: str = ""):
        self.decision = decision
        self.raw = raw
        self.model = model

    @property
    def is_block(self) -> bool:
        return self.decision == "block"

    @property
    def reached(self) -> bool:
        """True if the critic actually rendered a verdict (not infra error)."""
        return self.decision in ("pass", "concerns", "block")

    def __repr__(self):
        return f"Verdict({self.decision})"


def parse(text: str) -> str:
    """Extract pass|concerns|block from critic output. SAFETY RULE: a response with
    NO explicit VERDICT line is 'error', not 'concerns' — an unclear critic must
    fail TOWARD review (gate degrades to manual), never auto-pass on a verdict-less
    skim. Only a literal `VERDICT: pass|concerns|block` line is trusted."""
    matches = _VERDICT_RE.findall(text or "")
    if matches:
        return matches[-1].lower()              # last VERDICT line wins
    return "error"


def run_cold(diff_text: str, timeout: int = 180) -> Verdict:
    """Pipe a diff/plan to the cold critic and return a parsed Verdict. Never
    raises — an unreachable critic returns decision='error', not a crash."""
    if not (diff_text or "").strip():
        return Verdict("pass", raw="(empty diff — nothing to review)")
    if not os.path.exists(CRITIQUE):
        return Verdict("error", raw=f"critique.py not found at {CRITIQUE}")
    try:
        r = subprocess.run(
            ["python3", CRITIQUE],
            input=diff_text, capture_output=True, text=True, timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return Verdict("error", raw=f"critic timed out after {timeout}s")
    except Exception as e:
        return Verdict("error", raw=f"critic invocation failed: {e}")

    out = (r.stdout or "") + (("\n" + r.stderr) if r.stderr else "")
    decision = parse(r.stdout)
    # decision == 'error' means no trustworthy VERDICT line — whether the backend
    # was unreachable (non-zero exit) or it exited 0 with a verdict-less skim. Either
    # way it is NOT a pass: surface 'error' so callers degrade to manual / fail-closed.
    if decision == "error":
        why = "critic backend unreachable" if r.returncode != 0 else "critic returned no VERDICT line"
        return Verdict("error", raw=out.strip() or why)
    return Verdict(decision, raw=out.strip())


# ── CLI: `git diff HEAD | python3 evolution/verdict.py` → exit 2 on block ─────
def _cli():
    import argparse
    ap = argparse.ArgumentParser(prog="verdict",
                                 description="Run the independent critic, parse the verdict.")
    ap.add_argument("-f", "--file", default=None)
    ap.add_argument("--timeout", type=int, default=180)
    ap.add_argument("--fail-closed", action="store_true",
                    help="exit 2 when the critic is unreachable (routine mode)")
    a = ap.parse_args()
    text = open(a.file, encoding="utf-8").read() if a.file else sys.stdin.read()
    v = run_cold(text, timeout=a.timeout)
    print(v.raw)
    print(f"\n[verdict] decision={v.decision}")
    if v.is_block:
        sys.exit(2)
    if v.decision == "error":
        sys.exit(2 if a.fail_closed else 0)
    sys.exit(0)


if __name__ == "__main__":
    _cli()
