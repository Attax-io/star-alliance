#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────────────────
# Star Alliance — EVOLUTION STATUS  (read-only JSON for the dashboard)
#
# The serve.cjs /api/evolution endpoint execs this. It bundles everything the
# dashboard's Evolution panel SHOWS — the fitness score, capability signals,
# schedule + due-state, recent reflections, and the list of recurring scheduled
# tasks (routines) — into one JSON document. PURE READ: it never mutates. Always
# prints valid JSON; on any failure it prints {"error": "..."} so the UI degrades
# gracefully instead of seeing a 500.
# ─────────────────────────────────────────────────────────────────────────────
from __future__ import annotations

import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)


def _safe(fn, default):
    try:
        return fn()
    except Exception:
        return default


def routines() -> list:
    """Recurring scheduled tasks, read from ~/.claude/scheduled-tasks/*/SKILL.md
    frontmatter — the same store the app's 'Scheduled' sidebar uses. cron is best-
    effort (the MCP keeps the canonical schedule outside the file)."""
    base = os.path.join(os.path.expanduser("~"), ".claude", "scheduled-tasks")
    out = []
    try:
        ids = sorted(os.listdir(base))
    except OSError:
        return out
    for tid in ids:
        sk = os.path.join(base, tid, "SKILL.md")
        if not os.path.isfile(sk):
            continue
        desc, cron = "", ""
        try:
            txt = open(sk, encoding="utf-8").read()
            m = re.search(r"^description:\s*(.+)$", txt, re.M)
            if m:
                desc = m.group(1).strip().strip('"\'')
            m = re.search(r"(?:cron[_A-Za-z]*|schedule)\s*[:=]\s*['\"]?([^'\"\n]+)", txt, re.I)
            if m:
                cron = m.group(1).strip()
        except OSError:
            pass
        out.append({"id": tid, "description": desc[:240], "cron": cron,
                    "is_evolution": tid == "evolution-reflector"})
    return out


def main() -> None:
    import scoreboard  # noqa: E402
    import reflect     # noqa: E402
    import ledger      # noqa: E402

    sched = _safe(lambda: reflect.load_schedule(), {})
    due = _safe(lambda: reflect.is_due(sched, reflect._now()), (False, ""))
    recent = _safe(lambda: [e for e in ledger.read(limit=400)
                            if (e.get("meta") or {}).get("signal") == "reflection"][-10:], [])
    doc = {
        "score": _safe(lambda: scoreboard.score(), {}),
        "capability": _safe(lambda: scoreboard.capability(), {}),
        "schedule": {k: v for k, v in sched.items() if not str(k).startswith("_")},
        "cadences": sched.get("_cadences", ["off", "hourly", "daily", "weekly"]),
        "due": {"due": bool(due[0]), "reason": due[1]},
        "recent_reflections": recent,
        "routines": routines(),
        "disarmed": os.path.exists(os.path.join(HERE, "DISARMED")),
    }
    print(json.dumps(doc, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(json.dumps({"error": str(e)}))
