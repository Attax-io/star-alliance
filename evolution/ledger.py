#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────────────────
# Star Alliance — EVOLUTION LEDGER  (the SENSE organ)
#
# ONE append-only event stream that every self-modifying path writes to: turns,
# the nightly reflector, skillsmith, Strategic Audit. Before the Evolution Engine
# this signal was scattered across three stores that nothing read back
# (learnings.jsonl, turn-cost.jsonl, skillsmith routine-logs). The ledger unifies
# them so the scoreboard (REMEMBER) and reflector (DIAGNOSE) have a single, typed
# source of truth.
#
# An event is one JSON object per line:
#   {ts, kind, author, surface, diff_hash, verdict, severity, tier, detail, meta}
#
#   kind      change | verdict | learning | metric | proposal | revert | block
#   author    who acted — a model id (opus/sonnet/glm-5.2) or a routine name
#   surface   what was touched — skills | memory | docs | hooks | doctrine |
#             gates | arsenal | workflows | product  (tier A = first three)
#   diff_hash verify_hash fingerprint of the source diff this event is about ("" if n/a)
#   verdict   pass | concerns | block | ""   (set on kind=verdict/block)
#   tier      A (reversible, auto-appliable) | B (load-bearing, human-gated) | ""
#   detail    one-line human summary
#   meta      free dict for kind-specific fields (cost tokens, confidence, etc.)
#
# Design rules:
#   • APPEND ONLY. Never rewrite history — the scoreboard trusts the stream.
#   • FAIL SOFT. A ledger write must never crash its caller (a gate, a routine).
#     Logging is observability, not control flow.
#   • Git-TRACKED. evolution/ledger.jsonl is durable memory, committed like
#     learnings.jsonl — not ephemeral session state.
# ─────────────────────────────────────────────────────────────────────────────
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.join(HERE, "ledger.jsonl")

KINDS = {"change", "verdict", "learning", "metric", "proposal", "revert", "block"}
TIER_A_SURFACES = {"skills", "memory", "docs"}          # reversible → auto-appliable
TIER_B_SURFACES = {"hooks", "doctrine", "gates", "arsenal", "workflows"}  # human-gated


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def tier_for(surface: str) -> str:
    """Reversibility tier of a surface — A auto-appliable, B human-gated, '' unknown."""
    if surface in TIER_A_SURFACES:
        return "A"
    if surface in TIER_B_SURFACES:
        return "B"
    return ""


def append(kind: str, *, author: str = "", surface: str = "", diff_hash: str = "",
           verdict: str = "", severity: str = "", tier: str = "",
           detail: str = "", meta: dict | None = None, when: str | None = None) -> dict:
    """Append one event. Returns the event dict. Never raises — logging is not
    control flow; a broken ledger must not trap a gate or a routine."""
    ev = {
        "ts": when or _now(),
        "kind": kind if kind in KINDS else "metric",
        "author": author,
        "surface": surface,
        "diff_hash": diff_hash,
        "verdict": verdict,
        "severity": severity,
        "tier": tier or tier_for(surface),
        "detail": detail,
        "meta": meta or {},
    }
    try:
        with open(LEDGER, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(ev, ensure_ascii=False) + "\n")
    except Exception as e:                         # fail soft — observability, not control
        sys.stderr.write(f"[ledger] write failed (non-fatal): {e}\n")
    return ev


def read(limit: int | None = None, kind: str | None = None,
         since: str | None = None) -> list[dict]:
    """Read events newest-last. Filter by kind / ISO `since` timestamp. A corrupt
    line is skipped, never fatal."""
    out: list[dict] = []
    if not os.path.exists(LEDGER):
        return out
    try:
        with open(LEDGER, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    ev = json.loads(line)
                except Exception:
                    continue
                if kind and ev.get("kind") != kind:
                    continue
                if since and ev.get("ts", "") < since:
                    continue
                out.append(ev)
    except Exception as e:
        sys.stderr.write(f"[ledger] read failed: {e}\n")
    if limit:
        out = out[-limit:]
    return out


# ── CLI: append from a routine/hook, or tail for inspection ──────────────────
def _cli():
    import argparse
    ap = argparse.ArgumentParser(prog="ledger", description="Evolution ledger I/O")
    sub = ap.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("add", help="append one event")
    a.add_argument("kind", choices=sorted(KINDS))
    a.add_argument("--author", default="")
    a.add_argument("--surface", default="")
    a.add_argument("--diff-hash", default="", dest="diff_hash")
    a.add_argument("--verdict", default="")
    a.add_argument("--severity", default="")
    a.add_argument("--tier", default="")
    a.add_argument("--detail", default="")
    a.add_argument("--meta", default="", help="JSON object string")

    t = sub.add_parser("tail", help="print recent events")
    t.add_argument("-n", type=int, default=20)
    t.add_argument("--kind", default=None)

    args = ap.parse_args()
    if args.cmd == "add":
        meta = {}
        if args.meta:
            try:
                meta = json.loads(args.meta)
            except Exception:
                sys.stderr.write("[ledger] --meta is not valid JSON; ignoring\n")
        ev = append(args.kind, author=args.author, surface=args.surface,
                    diff_hash=args.diff_hash, verdict=args.verdict,
                    severity=args.severity, tier=args.tier, detail=args.detail, meta=meta)
        print(json.dumps(ev, ensure_ascii=False))
    elif args.cmd == "tail":
        for ev in read(limit=args.n, kind=args.kind):
            print(f"{ev['ts']}  {ev['kind']:8} {ev.get('surface',''):10} "
                  f"{ev.get('verdict',''):8} {ev.get('detail','')}")


if __name__ == "__main__":
    _cli()
