#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────────────────
# Star Alliance — EFFICIENCY REPORT  (Phase 0 reporter)
#
# Joins the two measurement streams Phase 0 lays down:
#   • star-alliance-arsenal/usage-log.jsonl — every offloaded model call (the
#     cheaper Claude subagent doing bulk work), now with phase + wall_ms.
#   • data/turn-cost.jsonl — per-turn premium (Opus) tokens + routing tier,
#     written by the turn-cost Stop hook.
# and prints the ONE thing the harness could never show before: a real net-saved
# figure plus a per-turn-type breakdown — the baseline every later phase is
# measured against. No estimates baked into the harness; the assumptions for the
# "net" line are printed inline so the number stays honest and auditable.
#
# Usage:  python3 tools/efficiency_report.py [--days N] [--json]
# ─────────────────────────────────────────────────────────────────────────────
import argparse
import json
import os
import sys
import time
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
USAGE_LOG = os.path.join(REPO, "star-alliance-arsenal", "usage-log.jsonl")
TURN_LOG = os.path.join(REPO, "data", "turn-cost.jsonl")

# Assumption for the "net saved" line, printed inline so it stays honest:
# one output token produced by the cheap bench is one output token Opus did NOT
# have to produce. We value displaced work at OUTPUT tokens only (the bench's
# input is context it had to be fed; only its generation is work Opus avoided).
# This is a deliberately conservative proxy, NOT a billing figure.


def _load(path):
    rows = []
    if not os.path.exists(path):
        return rows
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except Exception:
            continue
    return rows


def _parse_ts(ts):
    try:
        return time.mktime(time.strptime(ts, "%Y-%m-%dT%H:%M:%SZ"))
    except Exception:
        return None


def _within(rows, days):
    if not days:
        return rows
    cutoff = time.time() - days * 86400
    out = []
    for r in rows:
        t = _parse_ts(r.get("ts", ""))
        if t is None or t >= cutoff:
            out.append(r)
    return out


def _median(xs):
    xs = sorted(x for x in xs if x is not None)
    if not xs:
        return 0
    n = len(xs)
    mid = n // 2
    return xs[mid] if n % 2 else (xs[mid - 1] + xs[mid]) / 2


def build_report(days):
    usage = _within(_load(USAGE_LOG), days)
    turns = _within(_load(TURN_LOG), days)

    # ── Offload side ────────────────────────────────────────────────────────
    by_model = defaultdict(lambda: {"calls": 0, "in": 0, "out": 0, "wall_ms": []})
    offload_out = 0
    for r in usage:
        m = r.get("model", "unknown")
        b = by_model[m]
        b["calls"] += 1
        b["in"] += int(r.get("in", 0) or 0)
        b["out"] += int(r.get("out", 0) or 0)
        if "wall_ms" in r:
            b["wall_ms"].append(r.get("wall_ms"))
        offload_out += int(r.get("out", 0) or 0)

    # ── Premium side, split by routing tier ─────────────────────────────────
    by_tier = defaultdict(lambda: {"turns": 0, "in": 0, "out": 0})
    premium_in = premium_out = 0
    for r in turns:
        t = r.get("tier", "unknown")
        bt = by_tier[t]
        bt["turns"] += 1
        bt["in"] += int(r.get("in", 0) or 0)
        bt["out"] += int(r.get("out", 0) or 0)
        premium_in += int(r.get("in", 0) or 0)
        premium_out += int(r.get("out", 0) or 0)

    # Net: bench output displaced minus premium output actually spent.
    net_out = offload_out - premium_out

    return {
        "window_days": days or "all",
        "offload": {
            "total_calls": sum(b["calls"] for b in by_model.values()),
            "total_out": offload_out,
            "by_model": {
                m: {
                    "calls": b["calls"], "in": b["in"], "out": b["out"],
                    "median_wall_ms": _median(b["wall_ms"]),
                }
                for m, b in sorted(by_model.items(), key=lambda kv: -kv[1]["calls"])
            },
        },
        "premium": {
            "total_turns": sum(t["turns"] for t in by_tier.values()),
            "total_in": premium_in,
            "total_out": premium_out,
            "median_in_per_turn": _median([int(r.get("in", 0) or 0) for r in turns]),
            "by_tier": {
                t: {
                    "turns": v["turns"], "in": v["in"], "out": v["out"],
                    "median_in_per_turn": _median(
                        [int(r.get("in", 0) or 0) for r in turns if r.get("tier") == t]
                    ),
                }
                for t, v in sorted(by_tier.items())
            },
        },
        "net_displaced_out_tokens": net_out,
    }


def print_human(rep):
    print(f"━━ Star Alliance Efficiency Report  (window: {rep['window_days']} days) ━━\n")

    off = rep["offload"]
    print(f"OFFLOAD (cheaper Claude subagent doing bulk work)")
    print(f"  total calls: {off['total_calls']:>8}    total out-tokens: {off['total_out']:>10}")
    print(f"  {'model':<18}{'calls':>7}{'in':>11}{'out':>11}{'med ms':>9}")
    for m, b in off["by_model"].items():
        print(f"  {m:<18}{b['calls']:>7}{b['in']:>11}{b['out']:>11}{int(b['median_wall_ms']):>9}")

    prem = rep["premium"]
    print(f"\nPREMIUM (Opus per-turn, by routing tier)")
    if prem["total_turns"] == 0:
        print("  (no turn-cost data yet — the turn-cost Stop hook records this as you work)")
    else:
        print(f"  total turns: {prem['total_turns']:>8}    median in/turn: {int(prem['median_in_per_turn']):>8}")
        print(f"  {'tier':<10}{'turns':>7}{'in':>12}{'out':>11}{'med in/turn':>13}")
        for t, v in prem["by_tier"].items():
            print(f"  {t:<10}{v['turns']:>7}{v['in']:>12}{v['out']:>11}{int(v['median_in_per_turn']):>13}")

    print(f"\nNET (conservative proxy: bench out-tokens − premium out-tokens)")
    print(f"  displaced output tokens: {rep['net_displaced_out_tokens']:>12}")
    print("  assumption: 1 bench output token = 1 Opus output token avoided (out only).")
    if prem["total_turns"] == 0:
        print("  ⚠ baseline incomplete — let the turn-cost hook accrue ≥1 week of turns,")
        print("    then the LITE-vs-FULL split proves Phase 1's per-turn savings.")


def main():
    ap = argparse.ArgumentParser(description="Star Alliance efficiency report")
    ap.add_argument("--days", type=int, default=0, help="Trailing window in days (0 = all).")
    ap.add_argument("--json", action="store_true", help="Emit raw JSON instead of a table.")
    args = ap.parse_args()
    rep = build_report(args.days)
    if args.json:
        print(json.dumps(rep, indent=2))
    else:
        print_human(rep)
    return 0


if __name__ == "__main__":
    sys.exit(main())
