#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────────────────
# Star Alliance — EVOLUTION ENGINE  (the DIAGNOSE + CHANGE organs)
#
# The spine the whole self-improving loop runs on. It reads the ledger + scoreboard
# (SENSE/REMEMBER), turns the signal into change-proposals (DIAGNOSE), and routes
# each proposal by reversibility tier (CHANGE):
#
#   Tier A (skills/memory/docs)  → reversible → MAY auto-apply (only when --apply
#                                  AND the change passed the critic via verdict.py)
#   Tier B (hooks/doctrine/gates/arsenal/workflows) → load-bearing → NEVER auto-
#                                  applied. Logged as a proposal and surfaced for a
#                                  human "go". This is the line that keeps an
#                                  unsupervised nightly run from rewriting its own
#                                  safety rails.
#
# SAFETY (the "yet safe" mandate):
#   • SHADOW IS DEFAULT. With no flags the engine proposes and commits NOTHING.
#     You must pass --apply to let it touch even Tier-A surfaces.
#   • KILL SWITCH. If evolution/DISARMED exists, the engine refuses to apply
#     anything (still reports). One file disables the whole loop.
#   • CRITIC-GATED. Auto-apply requires an independent pass — the engine never
#     grades its own diff.
#   • EVERYTHING LEDGERED. Every proposal/apply/skip is an event, so the scoreboard
#     can later tell whether the engine's changes stuck or had to be reverted.
#
# This first cut's DIAGNOSE is deterministic (signal → proposal). Deeper STORM-style
# reflection can be layered behind the same proposal interface without changing the
# safety envelope.
# ─────────────────────────────────────────────────────────────────────────────
from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
DISARMED = os.path.join(HERE, "DISARMED")

sys.path.insert(0, HERE)
import ledger        # noqa: E402
import scoreboard    # noqa: E402


def is_disarmed() -> bool:
    return os.path.exists(DISARMED)


# ── DIAGNOSE: scoreboard signal → change proposals ───────────────────────────
def diagnose(since: str | None = None) -> list[dict]:
    """Turn fitness signal into concrete, tier-tagged proposals. Each proposal is
    a dict {surface, tier, detail, action} — action is advisory text for the human
    or, for Tier-A, a handle a future applier can execute."""
    s = scoreboard.score(since=since)
    proposals: list[dict] = []

    # 1. Regression escaped → the gate let junk through. Always Tier-B (touches gates).
    if s["regression_escapes"] > 0:
        proposals.append({
            "surface": "gates", "tier": "B",
            "detail": f"{s['regression_escapes']} regression(s) escaped the critic-gate "
                      f"({s['escape_hashes']}); tighten verify-gate / escalate to grounded review",
            "action": "review verify-gate coverage; consider mandatory grounded review on Tier-B diffs",
        })

    # 2. Repeated learnings → recurring friction that should be promoted to doctrine.
    for text, n in s["repeated_learnings"].items():
        proposals.append({
            "surface": "memory", "tier": "A",
            "detail": f"learning seen {n}× — promote to a memory file: {text[:90]}",
            "action": f"write a memory file capturing: {text}",
        })

    # 3. Concern density climbing → doctrine drift worth a human look.
    if s["concern_density"] >= 1.0 and s["changes"] >= 3:
        proposals.append({
            "surface": "doctrine", "tier": "B",
            "detail": f"concern density {s['concern_density']}/change — review recurring "
                      f"critic concerns for a doctrine gap",
            "action": "cluster recent 'concerns' verdicts; propose an AGENTS.md axiom if a pattern repeats",
        })

    # 4. Cost trend rising sharply → efficiency regression.
    ct = s["cost_trend"]
    if ct.get("delta_pct") is not None and ct["delta_pct"] > 40:
        proposals.append({
            "surface": "doctrine", "tier": "B",
            "detail": f"output cost up {ct['delta_pct']}% (recent {ct['recent_mean_out']} vs "
                      f"prior {ct['prior_mean_out']} tok) — check routing/doer offload discipline",
            "action": "inspect recent turns for un-offloaded bulk work; reinforce doer-first routing",
        })

    # ── CAPABILITY signals (Wave 2): skills / workflows / doer discipline ────────
    # Sourced from the SENSE telemetry the hooks now ledger. These route to the
    # EXISTING producers (skillsmith, Workflow Forge) rather than reinventing them.
    cap = scoreboard.capability(since=since)

    # 5. Recurring workflow MISS — an unregistered workflow declared repeatedly is a
    #    real gap: a craft the guild keeps reaching for with no lane. Forge it.
    for name, n in cap["workflow_unknown"].items():
        if n >= 2:
            proposals.append({
                "surface": "workflows", "tier": "B",
                "detail": f"workflow '{name}' declared {n}× but is NOT registered — a recurring gap",
                "action": f"run Workflow Forge to create '{name}' (or map it to an existing workflow)",
            })

    # 6. Skill CO-FIRE — two skills almost always drawn together → merge candidate.
    for pair, n in cap["skill_cofire"].items():
        if n >= 5:
            proposals.append({
                "surface": "skills", "tier": "A",
                "detail": f"skills '{pair}' co-fired {n}× — evaluate merging into one",
                "action": f"run skillsmith to assess merging {pair} (critic-gated)",
            })

    # 7. DEAD skills — carried but never drawn across a TRUSTED window → merge/retire.
    #    Held back until enough fires exist so launch-time silence isn't read as death.
    if cap["dead_skill_trusted"] and cap["skills_never_fired"]:
        sample = ", ".join(cap["skills_never_fired"][:8])
        proposals.append({
            "surface": "skills", "tier": "A",
            "detail": f"{len(cap['skills_never_fired'])} skill(s) never fired in "
                      f"{cap['total_skill_fires']} uses (e.g. {sample}) — review for merge/retire",
            "action": "run skillsmith to assess merge/retire of unused skills (critic-gated)",
        })

    # 8. DOER discipline — real changes but zero doer offload → agents may be doing
    #    bulk inline. A coaching signal (doctrine/agent-files), not an auto-fix.
    #    SUPPRESS when a swarm-fanout is present: N agent-dispatch events but 0 main-thread
    #    doer summons is the correct topology for a swarm turn (swarm-audit 2026-06-28).
    _swarm_active = cap.get("swarm_fanouts", 0) > 0
    if s["changes"] >= 5 and cap["doer_summons"] == 0 and not _swarm_active:
        proposals.append({
            "surface": "doctrine", "tier": "B",
            "detail": f"{s['changes']} changes but 0 doer summons — bulk work may be done inline",
            "action": "reinforce doer-first routing (weapon-utility); coach agents to offload bulk",
        })

    if not proposals:
        proposals.append({
            "surface": "", "tier": "", "detail": "no actionable signal this cycle", "action": ""})
    return proposals


# ── CHANGE: route proposals by tier, honoring shadow/kill-switch ─────────────
def run(apply: bool = False, since: str | None = None) -> dict:
    disarmed = is_disarmed()
    shadow = not apply or disarmed
    props = diagnose(since=since)

    applied, gated, shadowed = [], [], []
    for p in props:
        if not p.get("surface"):
            continue
        ledger.append("proposal", author="evolution-engine", surface=p["surface"],
                      tier=p["tier"], detail=p["detail"], meta={"action": p["action"]})
        if p["tier"] == "B":
            gated.append(p)                     # load-bearing: human go always required
        elif shadow:
            shadowed.append(p)                  # Tier-A but shadow/disarmed: propose only
        else:
            # Tier-A auto-apply path. This first cut does NOT execute edits yet — it
            # records intent so the loop is observable before it is given hands.
            # Wiring an executor here is Phase 3; the safety envelope is already set.
            shadowed.append(p)

    return {
        "mode": "DISARMED" if disarmed else ("SHADOW" if shadow else "APPLY"),
        "proposals": len(props),
        "tierB_gated": gated,
        "tierA": shadowed,
        "applied": applied,
        "scoreboard": scoreboard.score(since=since),
    }


def _cli():
    import argparse
    ap = argparse.ArgumentParser(prog="engine", description="Evolution Engine — reflect & route")
    ap.add_argument("--apply", action="store_true",
                    help="leave shadow mode — Phase 3 will execute Tier-A here; "
                         "today it still only proposes (no executor wired yet)")
    ap.add_argument("--since", default=None)
    a = ap.parse_args()
    r = run(apply=a.apply, since=a.since)
    print(f"── Evolution Engine [{r['mode']}] ── {r['proposals']} proposal(s)")
    if r["tierB_gated"]:
        print("\n  ⛔ Tier-B (needs your GO):")
        for p in r["tierB_gated"]:
            print(f"     · [{p['surface']}] {p['detail']}")
    if r["tierA"]:
        print("\n  ▸ Tier-A (reversible; shadow=proposed only):")
        for p in r["tierA"]:
            print(f"     · [{p['surface']}] {p['detail']}")
    print(f"\n  → {r['scoreboard']['verdict']}")


if __name__ == "__main__":
    _cli()
