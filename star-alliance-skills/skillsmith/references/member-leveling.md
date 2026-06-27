---
type: Document
timestamp: 2026-06-27T10:27:03Z
---

# Member Leveling — the Quartermaster's operating manual

> The standard the Quartermaster applies when conferring a member's level. The full rationale and the
> campaign that built this lives in `docs/STRATEGIST-MEMBER-LEVELING.md` (repo root). This file is the
> operating manual: the signals, the checklists, and the promotion procedure.

## What a level means

A member's level is a **craft-depth meter, not a hierarchy** — it grades the depth and sharpness of a
member's arsenal and specialty, exactly as a *skill's* level grades the skill. It is **decoupled from
standing**: the Butler leads the guild regardless of tier; a low level only says *this member's
arsenal is deepenable*. Level meters **capability, never usage** (deployment frequency is a separate
axis — see the plan's Wave 6, not yet built).

## The law

State is **derived from objective signals, ratified by the Quartermaster, recorded in the ledger** —
the same law that governs the project version. Three parts:

1. **Earned tier** — `build.py` computes it from the repo every build. Objective, reproducible.
2. **Conferred tier** — the ratified `level` in `members-meta.json`. The only hand-touched field; only
   the Quartermaster touches it; only when the checklist is met.
3. **The ledger** — every promotion is a `member-upgrade` guild-log entry (bumps the project version a
   PATCH tier automatically).

`build.py` says *who has earned what*; the Quartermaster **verifies the checklist, confers the tier,
and logs it.** He cannot confer a tier the checklist doesn't support.

## The five tiers (reuse `LEVEL_RAMP`)

| Tier | Ramp color |
|---|---|
| Foundational | gray |
| Intermediate | blue |
| Advanced | teal |
| Elite | amber |
| Master | purple |

## The signals (all repo-derived)

| Signal | Definition |
|---|---|
| **Arsenal Depth (AD)** | Σ over carried craft skills of the skill's level-weight (Foundational 1, Intermediate 2, Advanced 3, Master 4). `weapon-utility` excluded. |
| **Skill count** | craft skills carried (excl. `weapon-utility`). |
| **Unique (specialty)** | skills this member alone carries (`len(skill.members) == 1`). |
| **Peak skill** | highest skill level in the arsenal. |
| **Weapons** | count of models in the kit. |
| **Profile** | `does[]` + `doesnt[]` non-empty, `summary` present. |
| **Conformity-clean** | member raises zero `build.py` / `conformity_check.py` warnings. |

## The prerequisite checklists

Each tier requires **the tier below it, plus all of its own rows.** `build.py` computes every box.

| Tier | Prerequisites (ALL required, on top of the tier below) |
|---|---|
| **Foundational** | carries `weapon-utility` · ≥1 craft skill · `summary` present |
| **Intermediate** | AD ≥ 8 · ≥2 craft skills · ≥1 unique skill · `does[]` + `doesnt[]` filled |
| **Advanced** | AD ≥ 12 · ≥1 Advanced-or-higher skill · ≥2 unique skills · ≥6 weapons |
| **Elite** | AD ≥ 18 · ≥1 Master-level skill · ≥3 unique skills · conformity-clean |
| **Master** | AD ≥ 24 · ≥2 Master-level skills · ≥3 unique skills · conformity-clean · profile complete |

Thresholds live in the `MEMBER_TIERS` config block in `build.py` — tune them in one place, then
re-log if the ladder shifts.

## Promotion procedure

1. **Review the queue.** `python3 member_level.py report` — lists members where `earned > conferred`
   (the promotion queue) and the laggard board (lowest tier, most unmet boxes).
2. **Verify.** Confirm the member's checklist for the next tier is fully met (the report shows each
   box). The script refuses a promotion the checklist doesn't support.
3. **Confer.** `python3 member_level.py promote <member>` — writes the conferred `level` in
   `members-meta.json`, logs a `member-upgrade` entry (before→after in the detail), and runs the
   conformity-close.
4. **Close.** `python3 build.py` + `python3 conformity_check.py` must report **FULL CONFORMITY** before
   the commit (Invariant #8). The member-level invariant checks `conferred ≤ earned` for everyone.

## Regression (demotion) — policy (A) honest meter

If a member's arsenal regresses below their conferred tier, `earned < conferred` raises the
`overConferred` **notice** (loud, but **not** a build-breaker — it never blocks an unrelated commit).
The Quartermaster either restores the arsenal or records a downward `member-upgrade` (a demotion).
Level always reflects current craft. Demotions are rare and always logged.

## Wave 6 — the deployment-frequency (usage / reach) axis [SPEC — next gated build]

The conferred level meters **capability** and is deliberately blind to **usage**. Wave 6 adds the
second, orthogonal axis: *how widely is this member actually deployed?* It is a **separate meter**, not
a level modifier — a Master-tier member deployed nowhere and a Foundational member running in five
projects are both honest, just on different axes. Never let reach inflate or deflate the craft level.

**Data source (now unblocked).** `install.sh` appends every deploy to
`star-alliance-skills/skillsmith/references/deploy-ledger.md` (`date · member · tier · target`). That
append-only ledger is the reach signal — no new instrumentation needed; the `deploy-member` mode (see
`deploy-playbook.md`) feeds it on every install.

**Proposed meter (to build in `build.py`, gated — not yet wired):**
- **Reach** = count of *distinct* `target` projects a member is deployed into (from the deploy ledger).
- **Recency** = days since that member's most recent deploy.
- **Tier weight** = sum of deploy tiers (a Tier-3 deploy is "deeper" reach than a Tier-1 skills-only).
- Surface as a non-blocking `members-meta.json` field (`reach`) + a Reach column in
  `member_level.py report`, exactly like `conferred`/`earned` — read-only, never a build-breaker.

**Why gated, not built now:** the meter needs real deploy-ledger rows to calibrate the thresholds (an
empty ledger makes every member reach-0). Build it once the ledger has accrued a few real deploys, so
the bands reflect actual usage rather than a guess. Until then this section is the contract; the level
axis above ships and stands alone.

## When to run it

- As a sub-step of the daily `routine` (Stage D): run `member_level.py report`, promote anyone the
  checklist now supports.
- On demand when a member's arsenal changes (a skill added, a skill leveled up, a specialty forged).
- The conformity-close already surfaces `dueForPromotion` / `overConferred` after any skill work, so
  the queue is never silent.
