#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────────────────
# Star Alliance — REFLECTOR RUNNER  (the scheduled entrypoint for the engine)
#
# The cron fires this hourly; it is the cadence-aware wrapper around engine.run().
# It reads evolution/schedule.json — the SINGLE source the dashboard edits — and
# decides whether a reflection is DUE (enabled AND enough time since last_run for
# the chosen cadence) or FORCED (--now / dashboard "Run now"). Because the runner
# self-gates on the file, switching hourly⇄daily⇄off is a one-field edit with NO
# cron change.
#
# SAFETY (unchanged from the engine's envelope):
#   • SHADOW by default — proposes, commits nothing. --apply only relaxes Tier-A
#     (engine.py still gates Tier-B and still honors DISARMED).
#   • DISARMED kill switch respected here too.
#   • Every run ledgers a 'reflection' metric (count + mode) so the scoreboard can
#     see the loop is actually turning.
#
# Exit 0 always (a scheduled job that errd should not wedge the scheduler) — the
# outcome is in stdout + the ledger.
# ─────────────────────────────────────────────────────────────────────────────
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
SCHEDULE = os.path.join(HERE, "schedule.json")
DISARMED = os.path.join(HERE, "DISARMED")

sys.path.insert(0, HERE)
import ledger        # noqa: E402
import engine        # noqa: E402

CADENCE_SECS = {"hourly": 3600, "daily": 86400, "weekly": 604800}
DEFAULTS = {"cadence": "daily", "enabled": True, "last_run": None, "last_proposals": None}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def load_schedule() -> dict:
    try:
        with open(SCHEDULE, encoding="utf-8") as fh:
            data = json.load(fh)
    except Exception:
        data = {}
    out = dict(DEFAULTS)
    out.update({k: v for k, v in data.items() if not k.startswith("_")})
    # preserve doc/meta keys so we don't clobber them on write-back
    for k, v in data.items():
        if k.startswith("_"):
            out[k] = v
    return out


def save_schedule(sched: dict) -> None:
    try:
        with open(SCHEDULE, "w", encoding="utf-8") as fh:
            json.dump(sched, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
    except Exception as e:
        sys.stderr.write(f"[reflect] could not write schedule.json: {e}\n")


def is_due(sched: dict, now: datetime) -> tuple[bool, str]:
    """(due, reason). cadence=off → never due. No last_run → due (first run)."""
    cadence = sched.get("cadence", "daily")
    if cadence == "off":
        return False, "cadence is off"
    if not sched.get("enabled", True):
        return False, "disabled"
    last = sched.get("last_run")
    if not last:
        return True, "no prior run"
    try:
        prev = datetime.fromisoformat(last.replace("Z", "+00:00"))
    except Exception:
        return True, "unparsable last_run"
    secs = CADENCE_SECS.get(cadence, 86400)
    elapsed = (now - prev).total_seconds()
    if elapsed >= secs:
        return True, f"{int(elapsed)}s since last (cadence {cadence}={secs}s)"
    return False, f"only {int(elapsed)}s since last (need {secs}s)"


def run(force: bool = False, apply: bool = False) -> dict:
    now = _now()
    if os.path.exists(DISARMED):
        ledger.append("metric", author="reflector", surface="",
                      detail="reflection skipped — engine DISARMED",
                      meta={"signal": "reflection", "skipped": "disarmed"})
        return {"ran": False, "reason": "DISARMED"}

    sched = load_schedule()
    due, reason = is_due(sched, now)
    if not (due or force):
        return {"ran": False, "reason": reason}

    result = engine.run(apply=apply)
    n = result.get("proposals", 0)
    sched["last_run"] = _iso(now)
    sched["last_proposals"] = n
    save_schedule(sched)
    ledger.append("metric", author="reflector", surface="",
                  detail=f"reflection ran ({'forced' if force else reason}) — {n} proposal(s), mode {result.get('mode')}",
                  meta={"signal": "reflection", "proposals": n, "mode": result.get("mode"),
                        "forced": force})
    return {"ran": True, "reason": "forced" if force else reason, "result": result}


def _cli():
    import argparse
    ap = argparse.ArgumentParser(prog="reflect", description="Cadence-aware Evolution reflector")
    ap.add_argument("--now", action="store_true", help="force a run now, ignoring cadence")
    ap.add_argument("--apply", action="store_true", help="relax Tier-A auto-apply (Tier-B still gated)")
    ap.add_argument("--status", action="store_true", help="print schedule + due-state and exit")
    a = ap.parse_args()

    if a.status:
        sched = load_schedule()
        due, reason = is_due(sched, _now())
        print(json.dumps({"schedule": {k: v for k, v in sched.items() if not k.startswith("_")},
                          "due": due, "reason": reason}, indent=2))
        return

    r = run(force=a.now, apply=a.apply)
    if r["ran"]:
        res = r["result"]
        print(f"── Reflector [{res['mode']}] ran ({r['reason']}) — {res['proposals']} proposal(s)")
        for p in res.get("tierB_gated", []):
            print(f"   ⛔ Tier-B (needs go): [{p['surface']}] {p['detail']}")
        for p in res.get("tierA", []):
            print(f"   ▸ Tier-A: [{p['surface']}] {p['detail']}")
    else:
        print(f"── Reflector idle — {r['reason']}")


if __name__ == "__main__":
    _cli()
    sys.exit(0)
