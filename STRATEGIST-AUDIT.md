---
title: Star Alliance — Strategist's Audit
author: The Strategist (ultra-brainstorming, 4-model panel)
date: 2026-06-26
project_version_at_audit: 6.30.29
method: ultra-brainstorming v1.0.0 — 5-phase multi-model synthesis
---

# Star Alliance — The Strategist's Audit

> Run through the **`ultra-brainstorming`** skill: a feature-by-feature loop (Phase 1) framed into
> one brief, then brainstormed across a real multi-model panel (Phase 2), converged (Phase 3),
> synthesized (Phase 4), and graded (Phase 5). Below is the Phase-4 plan with the Phase-5 grade
> attached. Panel takes are condensed in the appendix.

## Panel composition — and the first finding

The Strategist's *named* ultra-brainstorm panel is **opus · gpt-5.5 · deepseek-v4-pro · glm-5.2 ·
kimi-k2.7**. Only **two of those five can fire today.** I ran the panel with the weapons that
actually shoot:

| Panelist | Engine | Status | Lens |
|---|---|---|---|
| MiniMax M3 | `minimax.py` (direct API) | ✓ fired | repo default doer |
| GLM-5.2 | `ollama_cloud.py glm-5.2:cloud` | ✓ fired (pulled) | analytical frame |
| Opus | Claude (Task tool) | ✓ fired | deepest structural reasoning |
| Sonnet | Claude (Task tool) | ✓ fired | fast pragmatic second opinion |
| ~~gpt-5.5~~ | OpenAI-direct | ✗ **no key** (summon exit 69) | sat out |
| ~~kimi-k2.7~~ | ollama | ✗ **not pulled** | sat out — *and it is the #1 "primary" weapon for 6 of 9 members* |
| ~~deepseek-v4-pro~~ | ollama | ✗ **not pulled** | sat out |

**That the audit could not assemble its own named panel is Finding #1.** The guild's marquee
capability runs at 2-of-5 today, silently.

---

## Verdict at a glance

| Question | Verdict | Confidence |
|---|---|---|
| **1. Understanding** | A personal, mostly-Lex-Council agent OS in guild costume — not a general guild | 10/10 (4/4 unanimous) |
| **2. Achieves its goal?** | Half. Sound *design*, hollow *execution*. **Grade C+ / 5** | 9/10 |
| **3. Each member unique?** | No — 5 strong, **3 hollow** (Merchant, Developer, Engineer) | 9/10 |
| **4. Conform with each other?** | Consistent in *form*, drifted in *fact* — and the checker is a **false witness** | 10/10 |
| **5. Upgrade paths** | 14 ranked upgrades, 3 lenses (below) | 8/10 |
| **The audit itself** | A− (verified, unanimous spine, one brilliant orphan idea) | — |
| **The project itself** | C+ / B− (works; oversold; self-audit is blind) | — |

---

## Phase 1 — the feature loop (what was inspected)

### Members (9) — `*` = skill unique to that member

| Member | Model | Unique skills | Shared skills | Verdict |
|---|---|---|---|---|
| the-butler | opus | members-formation* | weapon-utility | **Strong** — owns routing, irreplaceable |
| the-architect | sonnet | transactions-domain-model* | db-rename-sweep, supabase, supabase-pg (w/ Dev) | **OK** — overlap w/ Dev is *justified* (design vs build) |
| the-developer | sonnet | **none** | bug-fix-workflow, db-rename-sweep, dev-server, supabase, supabase-pg, full-output, obsidian-md | **Weak** — 0 unique; it's the *base class*, not a peer |
| the-designer | sonnet | 12 (design-taste, brandkit, image-to-code, imagegen×2, impeccable, …) | weapon-utility | **Strongest** — structurally irreplaceable |
| the-strategist | opus | ultra-brainstorming*, conquering-campaign*, performance*, strategies-review*, vault-log-compliance* | storm-investigation, bug-fix-workflow | **Strong** — 5 unique |
| the-translator | sonnet | codex-law-translate*, article-creator* | obsidian-markdown (w/ Dev) | **Strong** — tight, coherent |
| the-engineer | sonnet | graphify* | dev-server, full-output (both w/ Dev) | **Weak** — Engineer ⊂ Developer + graphify |
| the-merchant | opus | **none** | storm-investigation | **Stub** — 4 tools "to be recruited"; vaporware |
| the-quartermaster | sonnet | skillsmith*, guild-log*, cleanup* | storm-investigation | **Strong** — 3 unique |

### Infrastructure (looped)

| Feature | State | Note |
|---|---|---|
| 35 skills, versioned under `metadata.version`, Cowork-checked | ✓ solid | 28 lean · 6 large · 1 near word-ceiling · 0 hard violations |
| `build.py` → `guild-data.js` → buildless dashboard | ✓ real, non-trivial | a genuine feat |
| guild-log → SemVer replay (`6.30.29`) | ✓ clever | but measures *activity*, not capability (see orphan idea) |
| `conformity_check.py` | ⚠ **false-green** | passes while 5 drift facts and 2 phantom weapons coexist |
| arsenal (`summon.py` router) | ⚠ **half-real** | 2 callable text weapons (minimax, glm) + Claude native; 3 named thinkers dead |
| meta files (members/skills/domains/workflows) | ⚠ drifted | `domains.json` says 32 skills (actual 35) |

---

## Phase 4 — the five answers (synthesized)

### 1. What this project really is
Stripped of the guild mythology, Star Alliance is **Atta's personal agent operating system**, built
primarily to serve Lex Council, dressed as a medieval guild. The 9 "members" are not capabilities —
they are **curated views over one shared skill pool**. The load-bearing substrate is three things: the
**skill-metadata/versioning discipline**, the **arsenal model-router**, and the **guild-log-as-version**
trick. The agent roster is the *least* load-bearing layer; the "general guild of AI agents" line is an
organizing fiction. It serves three declared domains (Star Alliance, Lex Council App, Lex Council
Business) but functionally orbits one. *(4/4 unanimous.)*

### 2. Does it achieve its goal? — Grade C+ / 5
The architecture delivers the *shape* of the goal (defined members, shared+unique skills, a router, a
build pipeline, version tracking — all real). The *substance* is hollowed in three load-bearing places:
1. **3 of 9 members are not specialists** — Merchant is a stub, Developer has zero unique skills, Engineer is a strict subset of Developer.
2. **The flagship capability is broken** — `kimi-k2.7` is the declared #1 primary weapon for 6/9 members but isn't pulled; `gpt-5.5` is in 6 loadouts + the ultra-brainstorm panel but has no key. The marquee 5-thinker panel fires at **2/5**.
3. **The generalist framing is oversold** — ~8 of 35 skills are hard-wired to Lex Council (`transactions-domain-model`, `codex-law-translate`, `vault-log-compliance`, `article-creator`, `bug-fix-workflow` reads a Lex table, `cleanup` on Lex i18n, `supabase`, `db-rename-sweep`). Architect/Developer/Translator are Lex specialists in guild colors.

*Aspirationally met, operationally hollowed.*

### 3. Is each member truly unique?
**No — uniqueness is a power-law, not a guild.** Five members are real and well-shaped (Designer with
12 unique, Strategist 5, Quartermaster 3, Butler and Translator with tight irreplaceable craft). Three
are not:
- **the-merchant** — the worst: 0 unique skills, file still advertises "4 tools to be recruited." A placeholder masquerading as a member. *Nothing it does can't be covered by Strategist + Quartermaster today.*
- **the-developer** — 0 unique skills; *every* skill is shared. It isn't a specialist, it's the **base class** other members draw from. Calling it a "peer member" confuses a role with a skill-bundle.
- **the-engineer** — `graphify` is its only unique skill; otherwise **Engineer ⊂ Developer**. The clearest redundancy in the repo.

**Justified** overlaps: Architect↔Developer on the DB skills (design vs. implementation), Strategist↔Developer on `bug-fix-workflow` (diagnose vs. fix), and `storm-investigation` across Strategist/Merchant/Quartermaster (one method, three lenses). **Unjustified:** Engineer/Developer, and the Merchant stub.

### 4. Conformity — consistent in form, drifted in fact
The metadata contract (versions, cross-references) is followed well enough that the system *looks*
coherent. But at least **five facts have drifted**, and `conformity_check.py` reports **✓ FULL
CONFORMITY** straight through all of them:
1. README says "34 skills" (twice) — actual is **35** (`VERSIONS.md` is correct; README is stale).
2. `domains.json` star-alliance domain lists **32** skills and says "32 skills" — missing the 3 guild-mechanics skills (`members-formation`, `ultra-brainstorming`, `weapon-utility`).
3. README "Shared skills" section omits two real shared pairs: `bug-fix-workflow` (Dev+Strat), `obsidian-markdown` (Dev+Translator).
4. README roster still labels Merchant "(skills to be recruited)" after `storm-investigation` was added.
5. `fallen-sword-design-language` has **no `metadata.version`** — every other own-skill has one.

**The checker is not trustworthy.** It validates the easy invariant (referenced X exists) but not the
hard ones (do counts and prose match the data; does every own-skill carry a version; does every
*declared weapon actually fire*). A green checker that passes over five real drifts is **worse than no
checker** — it manufactures false confidence and trains the maintainer to stop verifying. It is
decorative exactly where it most needs to be load-bearing.

### 5. Upgrade paths — see the ranked plan below.

---

## Phase 4 — ranked upgrade plan (3 lenses)

Each item: the move, the **PRO for this project**, and a confidence.

### (a) FILL GAPS — close the holes between claim and reality

1. **Make `conformity_check.py` assert the claims it currently ignores** — skill-count parity (README/domains/actual), `metadata.version` presence, README↔data freshness, shared-pair coverage, **and weapon liveness**. — *PRO: the highest-leverage fix; every other drift recurs without it. Converts a rubber-stamp into the conscience the brand implies.* **[conf 10/10]**
2. **Provision or strip the phantom weapons** — add the `gpt-5.5` key (or remove it from 6 loadouts + the panel); `ollama pull` `kimi-k2.7`/`deepseek-v4-pro` (or demote them from "primary"). — *PRO: 6 members' declared primary fires for the first time; the ultra-brainstorm panel goes 2/5 → 5/5; the one feature named "ultra" becomes ultra.* **[conf 10/10]**
3. **Collapse the-engineer into the-developer** (Developer absorbs `graphify`) → roster drops to 8 well-shaped members. — *PRO: fixes BOTH the Engineer-subset and the Developer-0-unique problems in one move.* **[conf 7/10 — depends on whether you value the Engineer narrative]**
4. **Resolve the-merchant** — demote from the roster until its 4 tools exist, or recruit them. — *PRO: stops advertising a member that does nothing unique. (Note: your Lex Council Business domain is speccing BD/marketing/intake agents — none of which is "trading," so Merchant is genuinely orphaned right now.)* **[conf 7/10 — your intent]**
5. **Fix the 5 drift facts** (README 34→35, domains 32→35 + add the 3 skills, README shared-skills section, Merchant roster row, `fallen-sword` version). — *PRO: ~15 minutes; restores doc truth.* **[conf 10/10]**

### (b) RAISE CEILING — make the abstraction earn its keep

6. **Extract the 8 Lex-coupled skills behind a "domain pack" interface** (`transactions-domain-model`, `codex-law-translate`, `vault-log-compliance`, `cleanup`, etc. become one pluggable Lex pack; the core guild stays domain-agnostic). — *PRO: closes the identity tension by construction — the "general guild" claim becomes defensible, and Architect/Developer/Translator can work non-Lex jobs.* **[conf 8/10]**
7. **Promote weapon→member binding to a runtime contract** — a member declares required weapons; the Butler refuses to route (or degrades *explicitly*) when they aren't live. — *PRO: turns "guild" from a naming convention into a real capability/scheduling system. This is the upgrade that makes the multi-agent framing TRUE rather than decorative.* **[conf 8/10]**
8. **Let members compose skills (inheritance/bundles) instead of hand-curated lists.** — *PRO: kills the Engineer⊂Developer *class* of redundancy structurally, not by manual roster-tending.* **[conf 7/10]**
9. **Add an inter-member hand-off protocol** — there is currently *no* mechanism for one member to invoke, hand off to, or chain with another. The Butler "routes" — but to what, via what? — *PRO: this is the connective tissue that separates "a collection of agents" from "a guild." Without it the org chart is metaphor.* **[conf 8/10]**
10. **Give the orphaned MiniMax media weapons an owner** (image-01 has a helper; video/speech/music have none) — a media-production surface for the Designer, or a new member. — *PRO: the Designer's 12 unique skills are bottlenecked on one media helper; unlocking motion/audio compounds the strongest asset.* **[conf 6/10]**

### (c) HARDEN — protect what already works

11. **CI-gate the build** — `build.py` + the *real* conformity check + a weapon-liveness probe must pass before commit. — *PRO: all 5 drifts landed in a committed repo; the discipline exists but isn't enforced at the boundary.* **[conf 9/10]**
12. **Arsenal liveness check** (`arsenal/check_weapons.py`) — dry-fire each declared weapon, print a live status table. — *PRO: surfaces declared-vs-callable proactively instead of mid-task; failures stop being silent.* **[conf 9/10]**
13. **Treat `guild-log.json` as a tamper-evident append-only ledger** — the SemVer is replayed from it, so the log *is* the project's state-of-truth. — *PRO: a corrupted/edited log silently corrupts the version; if it's load-bearing it must be integrity-checked.* **[conf 8/10]**
14. **Document the log-as-version mechanic + require a version on every skill.** — *PRO: an outside reader sees `6.30.29` and assumes 6 breaking eras; one README paragraph prevents the confusion. Version-presence enforced kills the `fallen-sword` anomaly.* **[conf 9/10]**

---

## Phase 3 — convergence map (the work behind the plan)

- **High-confidence spine (2+ models agreed):** personal Lex-Council OS in costume · C-grade (sound design / hollow execution) · 3 weak members (Merchant/Developer/Engineer) · conformity checker is a false witness · fix-the-checker + provision-weapons are the top two fills. *All four models independently reached these.*
- **Contradictions resolved:**
  - *Top priority — checker vs weapons?* MiniMax ranked weapons #1; Opus/GLM/Sonnet ranked the checker #1. **Resolved: checker first** (it's the meta-fix that makes every other gap visible and stops recurrence), weapons a close #2 (most user-visible). Both are urgent.
  - *Developer — give-unique vs fold?* Opus reframed Developer as the legitimate "base class"; others said fix-or-fold. **Resolved: collapse Engineer→Developer**, which makes Developer's breadth a feature (the implementation base) instead of an embarrassment.
  - *Merchant — recruit vs delete?* **Resolved: demote until recruited** — your own `domains.json` shows no domain that needs trading, so it's orphaned, not just thin.
- **Orphan gems (one model each, worth keeping):**
  - **Opus — capability-hash version.** Stop replaying a log to mint SemVer; make the version a **hash of the live capability surface** (live weapons × wieldable skills × firing members). It would then *mean* something falsifiable and **would have caught all 5 drifts for free**. The current `6.30.29` measures activity; a capability-hash measures truth. *(The single best idea in the panel.)*
  - **GLM — no inter-member protocol** (became upgrade #9).
  - **MiniMax — a "Guild Recruitment" workflow** in `workflows.json` that scaffolds a new member behind a gate (≥3 unique skills, ≥1 *provisioned* weapon, conformity pass) — making the guild literally recruitable and retroactively hardening every existing member through the same door.
  - **Sonnet — mine `guild-log.json` for skill-usage frequency** (declared vs actually invoked) → data-driven roster/skill pruning instead of audit-by-inspection.
- **Shared blind spot (what ALL four missed):** every model audited the *wrapper* (roster, arsenal, conformity) and took the **skills themselves as given** — none asked whether the individual SKILL.md files are actually good, nor whether the **member layer earns its existence at all** vs. invoking skills directly. The activity data (`models-usage.json`: MiniMax 0.2M of 100M tokens spent) hints the system may be **barely used** — a usage-and-value lens (the missing 6th angle) could overturn the roster conclusions entirely.

---

## Phase 5 — peer-review gate (the honesty grade)

- **Weakest link:** the Merchant (demote vs recruit) and Engineer (fold vs keep) calls depend on **your intent**, not on anything in the repo. Harden by deciding: *do you want a trading capability, and do you value the Engineer role-narrative enough to keep a near-duplicate member?*
- **Model-bias check:** Opus's framings dominated the *conceptual* synthesis (base-class, capability-hash, false-witness). Appropriate for the deepest-reasoning seat, and the practical reads (Sonnet, MiniMax) converged independently — bias is low. GLM contributed the inter-member-protocol gem on its own. Diversity held even at 4/5 panel strength.
- **The missing 6th angle:** a **usage/operator lens** — is the system actually used, and does the member abstraction reduce effort vs. raw skills? Spend data suggests low usage; this could change the verdict on the whole roster. Recommended as the next investigation.
- **Overall grade:** the **audit** is **A−** (facts verified against source, unanimous spine, concrete ranked plan, one brilliant orphan). The **project** is **C+ / B−** (sound design, hollow execution, a self-audit blind to its own drift). Fix the checker and the weapons and it jumps a full grade.

---

## Appendix — condensed panel positions

| Panelist | Sharpest line |
|---|---|
| **Opus** | "An audit instrument that certifies its own blind spots. Everything else is downstream of that." Capability-hash version is the cure. |
| **GLM-5.2** | "The guild has no inter-member communication protocol… 'guild' is a metaphor, not an architecture." |
| **MiniMax M3** | "A 1–2 working-model system in a 5-model costume, and the linter is applauding." Add a gated Guild-Recruitment workflow. |
| **Sonnet** | "A guild whose primary weapon is declared but unloaded is not deployable — it is a blueprint." Mine the log for real skill ROI. |

---

## Post-audit actions (2026-06-26) — decisions by the Guild Master

The Guild Master reviewed this audit and ruled on the two open calls:

- **the-merchant — KEPT.** A separate trading project is incoming and will recruit the Merchant's tools. The stub stands as a reserved seat, not dead weight. *(Upgrade #4 resolved by decision.)*
- **the-engineer — FOLDED into the-developer.** Executed and wired *(Upgrade #3 — done)*:
  - `the-developer` absorbed `graphify` + the `minimax-m3` weapon and the dev-server / tooling / knowledge-graph craft; weapon order re-validated (doers→thinkers→sonnet).
  - `the-engineer.md` + its portrait retired; updated `members-meta.json`, `domains.json`, `workflows.json` (tooling step reassigned to the Developer), `the-butler.md` (roster + routing), `members-formation` (SKILL 1.0.0→1.0.1 + crystallize reference), `gen-member-art.cjs`, and `README.md`.
  - **Roster is now 8 members.** While wiring, corrected the conformity drift in every touched file (README 34→35 skills, `domains.json` 32→35 + the 3 missing guild-mechanics skills, README shared-skills section). Logged as guild-log decision **#38**; `VERSIONS.md` + `guild-data` regenerated.
  - `conformity_check.py` → **✓ FULL CONFORMITY** (members=8, skills=35, exit 0).

- **the-herald — RECRUITED (new marketing member).** Marketing was a total gap implied by the audit's "general guild vs. reality" finding — the pool had **zero** marketing skills and no marketing member (the Merchant is trading; the lex-council-business `marketing-agent` was an unbuilt stub reference). Created `the-herald` (opus) with a new **unique** skill **`growth-marketing`** (4 modes: content-seo · brand-positioning · email-nurture · social-paid, tuned for legal-services) + assembled `article-creator`, `brandkit`, `storm-investigation`. Deliberately *not* a stub — it carries a real unique craft, the lesson the Merchant taught. Skill body drafted by **MiniMax M3** (doer), curated + Cowork-validated by the guild (thinker) — **0 hard violations**. Roster **8 → 9**, skills **35 → 36**. Logged as decision **#39**; `conformity_check.py` → ✓ FULL CONFORMITY (members=9, skills=36).

**Update (2026-06-26) — the plan's hardening items are now done:**
- **#1 done** — `conformity_check.py` hardened with the assertions it was blind to: skill/member count parity (README + domains vs actual), `metadata.version` presence on every skill, weapon routability (hard) + weapon liveness (NOTE). It now *catches* the drift that used to ship green.
- **#2 done (bar one)** — weapons provisioned: `kimi-k2.7` → `kimi-k2.7-code:cloud` and `nemotron-3-ultra` → `nemotron-3-super:cloud` now fire (verified end-to-end via `summon`). `summon.py`'s stale cloud tags were corrected. **Only `gpt-5.5` remains dead** (no API key) — supply a key or strip it from the 8 loadouts. The liveness NOTE surfaces it so it no longer ships silently.
- **Drift closed** — `fallen-sword-design-language` now carries `metadata.version 1.0.0`.

---

*Generated by the Strategist via `ultra-brainstorming` — many minds in, one graded plan out.*
