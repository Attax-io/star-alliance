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
import re
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
    # Need a FULL prior window AND a full recent window before a trend is meaningful.
    # With fewer than 2*recent_n rows the old code let prior fall through to the same
    # rows as recent (pm==rm → delta 0.0%), so the >40% cost-trend proposal could
    # never fire in early usage. Report "insufficient data" explicitly instead.
    if len(outs) < 2 * recent_n:
        return {"recent_mean_out": None, "prior_mean_out": None,
                "delta_pct": None, "note": f"insufficient data (<{2 * recent_n} turns)"}
    recent = outs[-recent_n:]
    prior = outs[-2 * recent_n:-recent_n]
    rm = sum(recent) / len(recent)
    pm = sum(prior) / len(prior)
    # pm==0 would force delta to 0.0 and mask a real zero→nonzero jump (the same
    # "trend silently never fires" failure this guard exists to prevent), so report
    # it as undefined rather than a misleading 0%.
    if not pm:
        return {"recent_mean_out": round(rm), "prior_mean_out": round(pm),
                "delta_pct": None, "note": "prior window all-zero — trend undefined"}
    delta = (rm - pm) / pm * 100.0
    return {"recent_mean_out": round(rm), "prior_mean_out": round(pm),
            "delta_pct": round(delta, 1)}


def _learning_key(text: str) -> str:
    """Fuzzy clustering key for a learning detail. Lowercase, keep alphanumeric
    tokens >2 chars, dedupe + sort — so near-duplicate frictions ('grep misses
    utf8 files' vs 'UTF-8 files: grep silently misses') collapse to ONE recurring
    signal instead of exact-string-only matching, which never clusters reworded
    repeats. Conservative on purpose: a sorted token SET, not a loose substring."""
    toks = sorted({t for t in re.findall(r"[a-z0-9]+", text.lower()) if len(t) > 2})
    return " ".join(toks)


# Minimum skill-fire telemetry before "never fired" is trusted as "dead" rather
# than "no data yet" — guards the engine from flagging the whole roster at launch.
DEAD_SKILL_MIN_FIRES = 50


def _roster() -> tuple[set, set]:
    """(known_skill_ids, known_workflow_names) from guild-data.json — the same source
    of truth the dashboard is built from. Empty sets on any error → capability()
    degrades to ledger-only signals (no never-fired detection)."""
    skills: set = set()
    wfs: set = set()
    try:
        g = json.load(open(os.path.join(REPO, "guild-data.json"), encoding="utf-8"))
        for s in g.get("skills", []):
            sid = (s.get("id") or s.get("name")) if isinstance(s, dict) else s
            if sid:
                skills.add(sid)
        for w in g.get("workflows", []):
            nm = w.get("name") if isinstance(w, dict) else w
            if nm:
                wfs.add(nm)
    except Exception:
        pass
    return skills, wfs


def capability(since: str | None = None) -> dict:
    """The CAPABILITY half of the scoreboard — reads the Wave-1 SENSE signals
    (skill-fire / doer-summon / workflow-fire / workflow-unknown) back into the
    numbers engine.diagnose() turns into skill/workflow/coaching proposals.

    Counts, never-fired sets (roster minus fired), and skill CO-FIRE (skills sharing
    a turn id — that's why signals stamp meta.turn). 'never fired' is only meaningful
    once enough fires exist; the trust gate lives in the engine, not here."""
    events = ledger.read(since=since)
    sigs = [e for e in events
            if e.get("kind") == "metric" and (e.get("meta") or {}).get("signal")]

    def of(sig):
        return [e for e in sigs if e["meta"]["signal"] == sig]

    skill_fires = Counter(e["meta"].get("skill") for e in of("skill-fire")
                          if e["meta"].get("skill"))
    wf_runs = Counter(e["meta"].get("workflow") for e in of("workflow-fire")
                      if e["meta"].get("workflow"))
    wf_unknown = Counter(e["meta"].get("workflow") for e in of("workflow-unknown")
                         if e["meta"].get("workflow"))
    n_summon = len(of("doer-summon"))

    # co-fire: skills that share a turn id, counted as sorted pairs.
    by_turn: dict = {}
    for e in of("skill-fire"):
        key = e["meta"].get("turn") or e.get("ts")
        sk = e["meta"].get("skill")
        if sk:
            by_turn.setdefault(key, set()).add(sk)
    cofire: Counter = Counter()
    for sset in by_turn.values():
        sl = sorted(sset)
        for i in range(len(sl)):
            for j in range(i + 1, len(sl)):
                cofire[(sl[i], sl[j])] += 1

    known_skills, known_wfs = _roster()
    never_skills = sorted(known_skills - set(skill_fires)) if known_skills else []
    never_wfs = sorted(known_wfs - set(wf_runs)) if known_wfs else []

    return {
        "skill_fires": dict(skill_fires.most_common()),
        "total_skill_fires": sum(skill_fires.values()),
        "skills_never_fired": never_skills,
        "skill_cofire": {f"{a} + {b}": n for (a, b), n in cofire.most_common() if n > 1},
        "workflow_runs": dict(wf_runs.most_common()),
        "workflows_never_run": never_wfs,
        "workflow_unknown": dict(wf_unknown.most_common()),
        "doer_summons": n_summon,
        "dead_skill_trusted": sum(skill_fires.values()) >= DEAD_SKILL_MIN_FIRES,
    }


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

    # repeated learnings: cluster by a normalized token key so reworded/reordered
    # near-duplicates of the same friction count together, not only exact repeats.
    # Keyed by the fuzzy key; displayed by the first real wording seen in that group.
    groups: dict[str, dict] = {}
    for e in learnings:
        detail = (e.get("detail") or "").strip()
        if not detail:
            continue
        key = _learning_key(detail)
        if not key:
            continue
        g = groups.setdefault(key, {"count": 0, "sample": detail})
        g["count"] += 1
    repeated = {g["sample"]: g["count"] for g in groups.values() if g["count"] > 1}

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
    if ct.get("delta_pct") is None:
        print(f"  cost trend        : {ct.get('note', 'insufficient data')}")
    else:
        print(f"  cost trend        : recent {ct['recent_mean_out']} vs prior "
              f"{ct['prior_mean_out']} out-tok ({ct['delta_pct']}%)")
    print(f"  → {s['verdict']}")

    c = capability(since=a.since)
    print("\n── Capability ──")
    print(f"  skill fires       : {c['total_skill_fires']} total, "
          f"{len(c['skill_fires'])} distinct skills")
    print(f"  workflow runs     : {sum(c['workflow_runs'].values())} total, "
          f"{len(c['workflow_runs'])} distinct workflows")
    print(f"  doer summons      : {c['doer_summons']}")
    if c["workflow_unknown"]:
        print(f"  unregistered wf   : {c['workflow_unknown']}  (new-workflow candidates)")
    if c["skill_cofire"]:
        top = list(c["skill_cofire"].items())[:3]
        print(f"  top co-fires      : {top}")
    if c["dead_skill_trusted"]:
        print(f"  never-fired skills: {len(c['skills_never_fired'])} "
              f"(trusted — ≥{DEAD_SKILL_MIN_FIRES} fires observed)")
    else:
        print(f"  never-fired skills: held back — only {c['total_skill_fires']}/"
              f"{DEAD_SKILL_MIN_FIRES} fires observed (too little data to call dead)")


if __name__ == "__main__":
    _cli()
