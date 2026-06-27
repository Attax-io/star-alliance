#!/usr/bin/env python3
"""bench_pull — select N available Bench models for a SWARM (doer or thinker).

The Bench seat (models.json -> seats.bench, i.e. every model not holding the
Brain/Doer/Critic seats) is the pool the Brain pulls from when one Doer or one
thinker isn't enough:
  * doer-swarm    — parallel independent slices (see guild/delegate.py delegate_many)
  * thinker-swarm — ultra-brainstorming's panel of distinct minds

This helper returns the first N bench models of the requested ROLE, skipping the
three seat holders and any non-text/dead model. It does NOT call any model — it
just picks the roster; the Brain dispatches them.

Usage:
    python3 star-alliance-arsenal/bench_pull.py doer 3
    python3 star-alliance-arsenal/bench_pull.py thinker 2 --json
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def _load():
    with open(os.path.join(HERE, "models.json"), encoding="utf-8") as fh:
        d = json.load(fh)
    return d.get("models", {}), d.get("seats", {})


def pull(role, n, models, seats):
    held = {(seats.get(s) or {}).get("default") for s in ("brain", "doer", "critic")}

    def role_ok(r):
        if role == "doer":
            return r in ("doer", "both")
        if role == "thinker":
            return r in ("thinker", "both")
        return r in ("doer", "thinker", "both")

    pool = [mid for mid, d in models.items()
            if d.get("kind", "text") == "text"
            and d.get("status") in ("live", "reserve")
            and role_ok(d.get("role"))
            and mid not in held]
    return pool[:max(0, n)]


def main():
    ap = argparse.ArgumentParser(prog="bench_pull", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("role", choices=["doer", "thinker", "any"], help="Seat role to swarm.")
    ap.add_argument("n", type=int, help="How many bench models to pull.")
    ap.add_argument("--json", action="store_true", help="Emit a JSON array.")
    a = ap.parse_args()
    try:
        models, seats = _load()
    except Exception as e:
        print(f"bench_pull: cannot read registry: {e}", file=sys.stderr)
        sys.exit(2)
    picks = pull(a.role, a.n, models, seats)
    print(json.dumps(picks) if a.json else "\n".join(picks))


if __name__ == "__main__":
    main()
