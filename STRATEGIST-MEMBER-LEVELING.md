---
title: Star Alliance — Member Leveling System (Implementation Plan)
author: The Strategist (planned; gated by the Guild Master)
date: 2026-06-26
project_version_at_plan: 6.49.42
status: APPROVED 2026-06-26 — §8 decisions ratified (level=craft depth · checklists as calibrated · demotion policy A). Campaign in execution.
owners: Strategist plans · Developer implements · Quartermaster operates
method: conquering-campaign (BUILD) — five waves, prerequisites-as-checklist standard
---

# Star Alliance — Member Leveling System

> The Guild Master's order: *"give each member a level… decided by his skills and speciality.
> The more we improve the member, the more they level up. It should show which member is lagging
> behind. We need a clear standard for future runs. The Quartermaster upgrades a member's level
> when he finds they've reached the prerequisites. Have the Strategist plan it."*

This is the campaign plan. It does **not** touch code — it specifies what gets built, by whom,
and in what order. Wave 1 begins on the Guild Master's word.

---

## 1. The headline decision — what a "level" *measures*

A member's level is a **craft-depth meter, not a hierarchy.** It grades the depth and sharpness of
a member's arsenal and specialty — exactly as a *skill's* level (Foundational → Master) grades the
skill's depth without claiming one skill outranks another.

**Level is explicitly decoupled from standing.** The Butler leads the guild and routes every order;
his level reads low only because orchestration is one craft held thin in *skills*, not because he
ranks below anyone. Reading "Butler = Foundational" as a demotion is a category error — the same way
"the dagger is a Foundational weapon" doesn't make Haiku lesser. The level says one true thing:
*this member's arsenal is deepenable.* That is the signal the Guild Master asked for — "who is
lagging behind" — working as designed.

Two members surface thin today (Butler, Merchant). That is the feature proving itself, not a flaw to
paper over. (Considered and rejected: a per-role rubric or a leadership floor — both require
subjective judgment the guild can't recompute identically on a future run, which would break the one
hard requirement, *a clear standard for future runs*. See §7.)

---

## 2. The standard — earned by checklist, conferred by the Quartermaster, recorded in the ledger

This mirrors the guild's existing law for the project version: **state is derived from objective
signals and recorded in the guild log — never hand-judged, never drifting.** Three moving parts:

1. **Earned tier** — computed by `build.py` from the repo, every build. Objective. Reproducible.
2. **Conferred tier** — the ratified level stored in `members-meta.json`. The *only* hand-touched
   field, and only the Quartermaster touches it, and only when the checklist is met.
3. **The ledger** — every promotion is a `member-upgrade` guild-log entry (an existing type; it
   already bumps the project version a PATCH tier, so a level-up *pumps the guild version for free*).

The Quartermaster is the gate the Guild Master asked for: `build.py` says *who has earned what*, and
the Quartermaster **verifies the prerequisites, confers the tier, and logs it.** Earned ≠ conferred
until the Quartermaster ratifies — but the Quartermaster cannot confer a tier the checklist doesn't
support. Standard and gate, both honored.

### 2.1 The five tiers (reusing the existing ramp)

The dashboard's `LEVEL_RAMP` already defines five colors — `Elite` (amber) was reserved and unused.
Members reuse it verbatim, so member badges inherit the skill-badge palette with zero new design:

| Tier | Ramp color | Meaning |
|---|---|---|
| **Foundational** | gray | Present, carries a specialty, profile stood up. |
| **Intermediate** | blue | A real arsenal with a defining specialty. |
| **Advanced** | teal | Deep, multi-skill craft with high-tier skills. |
| **Elite** | amber | A master-tier skill anchoring a broad, sharp arsenal. |
| **Master** | purple | Two master-tier skills atop the deepest arsenal in the guild. |

### 2.2 The signals (all repo-derived, all recomputable)

| Signal | Definition | Source |
|---|---|---|
| **Arsenal Depth (AD)** | Σ over carried craft skills of the skill's own level-weight: Foundational 1, Intermediate 2, Advanced 3, Master 4. `weapon-utility` (universal) is excluded. | skill `level` × membership |
| **Skill count** | craft skills carried (excl. `weapon-utility`). | member `skills` |
| **Unique (specialty)** | skills this member alone carries (`len(skill.members) == 1`). | reverse index |
| **Peak skill** | highest skill level in the arsenal (has-an-Advanced, has-a-Master). | skill `level` |
| **Weapons** | count of models in the kit. | member `weapons` |
| **Profile** | `does[]` AND `doesnt[]` non-empty, `summary` present. | members-meta |
| **Conformity-clean** | member raises zero `build.py`/`conformity_check.py` validation warnings. | build validators |

> Deliberately **not** used: guild-log "track record." The log's `who` is often a person (Atta) and
> `ref` points at skills, not members — there is no clean member attribution today. Adding one is a
> separate future lever (§7), not a launch dependency.

### 2.3 The prerequisite checklists

Each tier requires **the tier below it, plus all of its own rows.** The Quartermaster checks the box;
`build.py` computes every box from the repo so the check is mechanical, not a judgment call.

| Tier | Prerequisites (ALL required, on top of the tier below) |
|---|---|
| **Foundational** | carries `weapon-utility` · ≥1 craft skill · `summary` present |
| **Intermediate** | AD ≥ 8 · ≥2 craft skills · ≥1 unique skill · `does[]` + `doesnt[]` filled |
| **Advanced** | AD ≥ 12 · ≥1 Advanced-or-higher skill · ≥2 unique skills · ≥6 weapons¹ |
| **Elite** | AD ≥ 18 · ≥1 Master-level skill · ≥3 unique skills · conformity-clean |
| **Master** | AD ≥ 24 · ≥2 Master-level skills · ≥3 unique skills · conformity-clean · profile complete |

¹ Every current member already carries ≥6 weapons, so this row binds nothing today — it's a floor
for thin-kit future recruits, not a gate on the existing roster.

Thresholds live in one `MEMBER_TIERS` config block in `build.py` (next to `LEVEL_RAMP` /
`VERSION_*_TYPES`), tunable in one place. Calibrated against today's roster they yield a clean,
differentiated ladder (no clumping at top or bottom):

| Member | AD | Unique | Earned tier |
|---|---:|---:|---|
| The Strategist | 25 | 8 | **Master** |
| The Designer | 20 | 6 | **Elite** |
| The Quartermaster | 14 | 5 | **Advanced** |
| The Herald | 14 | 2 | **Advanced** |
| The Developer | 13 | 3 | **Advanced** |
| The Architect | 12 | 2 | **Advanced** |
| The Translator | 9 | 2 | **Intermediate** |
| The Merchant | 6 | 1 | **Foundational** |
| The Butler | 5 | 2 | **Foundational** |

This is the seed state Wave 5 ratifies. The numbers are a starting calibration — Wave 2 confirms the
spread stays differentiated and the Guild Master signs off before any tier is conferred.

### 2.4 "The more we improve them, the more they level up" — the roadmap property

Because every tier is a checklist of concrete, repo-derived gaps, each member's *next* tier **is** a
to-do list. The Merchant reaches Intermediate the moment he recruits 1 more craft skill (to ≥2) and
lifts AD to 8 — i.e. one Advanced-or-two-Intermediate skills. The dashboard renders this as
"progress to next tier: AD 6/8, unique 1/1 ✓, skills 2/2 ✓." Improving a member *is* climbing the
checklist; the level moves with the craft, exactly as ordered.

---

## 3. Where it lives (the seams — no invented machinery)

Every piece slots into an existing seam:

- **The standard (this doc's §2)** → committed as `star-alliance-skills/skillsmith/references/member-leveling.md`
  (the Quartermaster's own toolkit, where he reads his procedures). This doc is the plan; that file
  is the operating manual.
- **The scorer + validators** → `build.py` gains a `compute_member_levels()` pass (alongside
  `compute_reverse_indices()`), emitting per-member `earned`, `conferred`, `nextTier`, `progress[]`,
  and a `dueForPromotion` / `overConferred` flag. `members-meta.json` gains one field: `level`
  (conferred).
- **The conformity gate** → `conformity_check.py` surfaces two member-level **notices, neither a hard
  fail**: `dueForPromotion` (earned > conferred — the QM's promotion queue) and `overConferred`
  (earned < conferred — a regression that queues a demotion review, §6). Both are loud, neither
  breaks the build. This is deliberate: leveling is QM-gated and human-in-the-loop, so drift belongs
  in the Quartermaster's queue, not in a gate that would block unrelated commits. `member_level.py
  promote` already blocks bad *promotions* at promote-time, which is where the hard check belongs.
- **The Quartermaster's operation** → a new `member_level.py` helper + a thin `skillsmith` surface
  (a `level` mode, or a sub-step of the daily `routine` Stage D). It reports the promotion queue and
  the laggard board, and on `--promote <member>` it verifies the checklist, writes the conferred
  `level`, logs the `member-upgrade` entry, and runs the conformity-close.
- **The ledger** → reuses the existing `member-upgrade` log type (→ PATCH). No `build.py`
  version-type change needed.
- **The dashboard** → member cards/tooltips already render skill `level` badges via `rampClass`;
  members reuse it. Add a tier badge + progress bar + a roster sort/filter by level, and a "lagging"
  / "ready to promote" surface.

---

## 4. The waves

A BUILD campaign, five waves, each independently committable and revertible. Conformity-close
(`build.py` + `conformity_check.py` → FULL CONFORMITY) closes **every** wave per Invariant #8.

### Wave 1 — Ratify the standard *(Strategist + Guild Master)*
- Guild Master approves §1 (level = craft depth) and §2.3 thresholds.
- Commit `skillsmith/references/member-leveling.md` (the standard, lifted from §2).
- Log a `decision` entry: *what a member level means, and why per-role/floor models were rejected.*
- **Gate:** no code yet. Approval is the deliverable.

### Wave 2 — The scorer in `build.py` *(Developer)*
- Add `MEMBER_TIERS` config + `compute_member_levels()`; emit `earned/conferred/nextTier/progress/
  flags` into `GUILD.members`. Handle thin/zero arsenals without dividing by zero.
- Add `level: "Foundational"` to every member in `members-meta.json` as the conferred floor (no one
  is *born* promoted; Wave 5 confers the earned tiers through the proper gate).
- Print earned-vs-conferred in `build.py --report`. Confirm the §2.3 ladder reproduces and stays
  differentiated; if it clumps, retune `MEMBER_TIERS` and re-log.
- **Gate:** `--report` shows the §2.3 distribution; conformity-close green.

### Wave 3 — The Quartermaster's tooling + invariant *(Developer builds, QM owns)*
- `member_level.py`: `report` (promotion queue + laggard board) and `promote <member>` (verify
  checklist → write conferred `level` → log `member-upgrade` → conformity-close).
- `conformity_check.py`: add the *conferred ≤ earned* invariant (fail) + `dueForPromotion` notice.
- Wire a `level` surface into `skillsmith` (mode or routine sub-step) + a §Changelog/version bump.
- **Gate:** `member_level.py report` lists Strategist/Designer/etc. as due; conformity-close green.

### Wave 4 — Dashboard surface *(Designer + Developer)*
- Member tier badge (reusing `rampClass` colors) on cards + roster.
- Progress-to-next-tier bar from `progress[]`; roster sort/filter by level.
- A "lagging behind" view (lowest tier, most unmet prerequisites) and a "ready to promote" marker.
- **Gate:** dashboard renders all nine tiers + the laggard board; `dashboard` log entry.

### Wave 5 — Confer the seed levels *(Quartermaster)*
- Run `member_level.py promote` for each member the checklist supports (the §2.3 ladder), each its
  own logged `member-upgrade`. The guild version pumps once per promotion, automatically.
- Final conformity-close; Run Summary.
- **Gate:** conferred == earned for all nine; FULL CONFORMITY; README roster table notes levels.

### Wave 6 — The Activity axis *(deferred — needs log attribution first)*
A member's level meters **capability** (craft depth). It deliberately does **not** meter **usage** —
how often a member is actually deployed. Those are orthogonal: folding usage into level would rocket
the Butler (deployed on every order, thin arsenal) up the ladder, re-opening the standing problem §1
closes, and would import a noisy, non-reproducible signal (session-transcript mining — the friction
the Quartermaster fought across skillsmith 1.1.3→1.1.9) into a standard that must recompute
identically forever. So usage rides a **second axis beside level, never inside it.** The two together
are the real "who's lagging" read:

| | **Low usage** | **High usage** |
|---|---|---|
| **High craft** | Underused asset — deploy more (the Merchant, once ramped) | Stars |
| **Low craft** | Genuinely lagging — recruit or retire | Workhorse stretched thin — deepen the arsenal |

**Hard prerequisite — clean member attribution.** Today the guild log's `who` is often a person
(*Atta*) and `ref` points at skills, not members; there is no reliable "the Developer shipped this."
Wave 6 cannot begin until the log gains a `member` attribution convention (the workflows already name
member actors — `build.py` validates step actors against member ids — so the foundation exists).

- **W6a (enabling):** add a `member` field to the guild-log entry schema + `log_event.py`; backfill
  where unambiguous. This is the gate; everything else waits on it.
- **W6b:** `build.py` derives an `activity` count per member from attributed entries; emit beside
  `earned`. Treat as **coarse** (the log is ~60 entries) — a deployment-frequency signal from
  session/routine telemetry is a later, separate refinement, kept out of the conferral path.
- **W6c:** dashboard renders the 2×2 (craft level × activity) — the laggard board gains its second
  dimension.
- **Invariant:** activity **never** feeds the tier checklist or the conferral gate. Level stays pure
  craft depth. Activity is a sibling meter, full stop.
- **Gate:** attribution lands and validates before any activity number is shown; no change to §2.3.

---

## 5. The repeatable loop (how it runs "for future runs")

After Wave 5 the system self-sustains with no new ceremony:

1. A member's arsenal improves (a skill is added, a skill levels up, a new specialty is forged).
2. Next `build.py` recomputes `earned`; if it now clears the next tier, the member shows
   `dueForPromotion` on the dashboard and in `member_level.py report`.
3. On the Quartermaster's daily `routine` (or on demand), he runs `member_level.py report`, sees the
   queue, verifies the checklist, and `promote`s — one logged entry each.
4. Conformity-close proves conferred ≤ earned. The guild version pumps. The ledger remembers.

The laggard board is always live: the lowest tiers with the most unmet boxes are the guild's
improvement backlog, surfaced without anyone asking.

---

## 6. Demotion — the one policy the Guild Master should set

Levels are *earned and conferred*. If a member's arsenal **regresses** below their conferred tier (a
skill is removed or downgraded), `earned < conferred` raises the `overConferred` notice (§3) — a
loud flag in the QM's queue, **not** a build-breaker, so it never blocks an unrelated commit. Two
options for what the QM does with it — the Guild Master picks one in Wave 1:

- **(A) Honest meter (recommended):** the QM is flagged to either restore the arsenal or record a
  downward `member-upgrade` (a demotion). Level always reflects current craft. Truthful, matches
  "level = craft depth."
- **(B) Ratchet:** conferred tiers never fall; regression only blocks *further* promotion. Kinder,
  but a conferred level can then overstate the live arsenal — a small, permanent drift the guild
  otherwise never tolerates.

Recommendation: **(A)** — it's the only one consistent with the no-drift philosophy. Demotions will
be rare and always logged. **→ Ratified: (A) honest meter.**

---

## 7. Deferred levers (not launch dependencies)

- **Track-record / usage signal** — promoted to **Wave 6** (the Activity axis). A *sibling* meter to
  level, never folded in; gated on log attribution. See §4 Wave 6.
- **Per-member XP number** — the checklist is the gate; a cosmetic 0–100 progress score could ride on
  top later. Not needed for launch.
- **Cross-axis "standing" meter** — if the Guild Master ever wants leadership/seniority shown, it is a
  *second* axis beside craft level, never folded into it. Explicitly out of scope here.

---

## 8. Decisions — ratified by the Guild Master (2026-06-26)

1. **§1 — level = craft depth, decoupled from standing** (Butler/Merchant read low by design). **→ APPROVED.**
2. **§2.3 thresholds** — the five checklists and the seed ladder. **→ APPROVED.**
3. **Demotion policy (§6)** — **(A) honest meter.** **→ APPROVED.**
4. **Usage metering** — added as **Wave 6**, a sibling Activity axis (deferred, never folded into level). **→ APPROVED.**

The standard is ratified; the campaign is in execution. Wave 1 commits the standard reference and logs the decision.
