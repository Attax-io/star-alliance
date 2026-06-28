#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────────────────
# Star Alliance — FITNESS SCOREBOARD  (the REMEMBER/SCORE organ)
#
# "Self-improving" without a scoreboard is a random walk. The audit found rich
# fitness data (data/turn-cost.jsonl) that NOTHING read back. This module reads
# the evolution ledger (+ turn-cost as a secondary source) and computes the
# numbers the reflector optimizes against and the human reviews:
#
#   regression_escapes  changes committed that a LATER verdict called block
#                       — the single most important number: did junk reach the repo?
#   block_rate          verdicts that blocked / total verdicts (critic catch rate)
#   concern_density     concerns per change (rising = doctrine drift)
#   repeated_learnings   same learning seen >1× (a recurring, unfixed friction)
#   tierB_pending       proposals on load-bearing surfaces awaiting human go
#   cost_trend           recent vs older mean output tokens/turn (efficiency drift)
#
# The score is descriptive, not punitive: it tells the reflector where to look and
# tells the human whether the loop is converging (escapes→0, blocks caught early)
# or diverging. A change is judged to have "stuck" if no later block references its
# diff_hash within the window.
# ─────────────────────────────────────────────────────────────────────────────
from __future__ import annotations

import json
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
TURNCOST = os.path.join(REPO, "data", "turn-cost.jsonl")

sys.path.insert(0, HERE)
import ledger  # noqa: E402


def _turncost_trend(recent_n: int = 10) -> dict:
    """Mean output tokens over the most-recent N turns vs the N before them."""
    rows = []
    if os.path.exists(TURNCOST):
        try:
            with open(TURNCOST, encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if line:
                        try:
                            rows.append(json.loads(line))
                        except Exception:
                            continue
        except Exception:
            pass
    outs = [r.get("out", 0) for r in rows if isinstance(r.get("out", 0), (int, float))]
    if len(outs) < 2:
        return {"recent_mean_out": None, "prior_mean_out": None, "delta_pct": None}
    recent = outs[-recent_n:]
    prior = outs[-2 * recent_n:-recent_n] or outs[:-recent_n] or recent
    rm = sum(recent) / len(recent)
    pm = sum(prior) / len(prior) if prior else rm
    delta = ((rm - pm) / pm * 100.0) if pm else 0.0
    return {"recent_mean_out": round(rm), "prior_mean_out": round(pm),
            "delta_pct": round(delta, 1)}


def score(since: str | None = None) -> dict:
    """Compute the fitness scoreboard over the ledger (optionally since an ISO ts)."""
    events = ledger.read(since=since)
    changes = [e for e in events if e.get("kind") == "change"]
    verdicts = [e for e in events if e.get("kind") in ("verdict", "block")]
    blocks = [e for e in verdicts if e.get("verdict") == "block"]
    learnings = [e for e in events if e.get("kind") == "learning"]
    proposals = [e for e in events if e.get("kind") == "proposal"]

    # regression escapes: a change committed, then a LATER block names its diff_hash.
    committed = {}
    for e in changes:
        h = e.get("diff_hash")
        if h:
            committed[h] = e["ts"]
    escapes = [b for b in blocks
               if b.get("diff_hash") in committed and b["ts"] > committed[b["diff_hash"]]]

    # repeated learnings: identical detail text seen more than once.
    ltexts = Counter((e.get("detail") or "").strip().lower()
                     for e in learnings if (e.get("detail") or "").strip())
    repeated = {k: n for k, n in ltexts.items() if n > 1}

    n_changes = len(changes) or 1
    concerns = [v for v in verdicts if v.get("verdict") == "concerns"]
    tierB_pending = [p for p in proposals if p.get("tier") == "B"]

    return {
        "window_events": len(events),
        "changes": len(changes),
        "verdicts": len(verdicts),
        "regression_escapes": len(escapes),
        "escape_hashes": [e.get("diff_hash") for e in escapes],
        "block_rate": round(len(blocks) / (len(verdicts) or 1), 3),
        "concern_density": round(len(concerns) / n_changes, 3),
        "repeated_learnings": repeated,
        "tierB_pending": len(tierB_pending),
        "cost_trend": _turncost_trend(),
        "verdict": _health(len(escapes), len(blocks), len(verdicts)),
    }


def _health(escapes: int, blocks: int, verdicts: int) -> str:
    if escapes > 0:
        return "DIVERGING — regressions reached the repo; tighten the gate"
    if verdicts == 0:
        return "BLIND — no verdicts on record; the critic is not in the loop"
    return "CONVERGING — changes are being reviewed and nothing escaped"


def _cli():
    import argparse
    ap = argparse.ArgumentParser(prog="scoreboard", description="Evolution fitness scoreboard")
    ap.add_argument("--since", default=None, help="ISO timestamp lower bound")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    s = score(since=a.since)
    if a.json:
        print(json.dumps(s, ensure_ascii=False, indent=2))
        return
    print("── Evolution Scoreboard ──")
    print(f"  window events     : {s['window_events']}")
    print(f"  changes           : {s['changes']}")
    print(f"  verdicts          : {s['verdicts']}  (block rate {s['block_rate']})")
    print(f"  regression escapes: {s['regression_escapes']}  {s['escape_hashes'] or ''}")
    print(f"  concern density   : {s['concern_density']} per change")
    print(f"  repeated learnings: {len(s['repeated_learnings'])}")
    print(f"  tier-B pending    : {s['tierB_pending']} (awaiting human go)")
    ct = s["cost_trend"]
    print(f"  cost trend        : recent {ct['recent_mean_out']} vs prior "
          f"{ct['prior_mean_out']} out-tok ({ct['delta_pct']}%)")
    print(f"  → {s['verdict']}")


if __name__ == "__main__":
    _cli()
