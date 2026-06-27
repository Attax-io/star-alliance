---
type: Document
title: Source-of-Truth Consolidation Audit
description: Audit of every duplicated/divergent source-of-truth in the Star Alliance app, with a graded consolidation plan and the locked prime-thinker decision.
timestamp: 2026-06-27T00:00:00Z
---

# Source-of-Truth Consolidation Audit — Star Alliance

> **Status:** Report only — no code changed. Produced via Strategic Audit (5-domain
> parallel readers + synthesis). 39 duplicated facts found; 4 live contradictions.
> **Date:** 2026-06-27.
>
> **Guild Master decisions locked (this session):**
> - **Prime thinker = the highest-priority thinker model by arsenal arrangement** — the
>   first weapon whose role ∈ {thinker, both}, scanning the loadout left→right. For every
>   member that is **opus** (opus leads the thinker block; sonnet is pinned last). This is
>   exactly the definition in §5 — **confirmed**, and the UI `PRIME` flag added this
>   session already implements it correctly. *Not* the session model.
> - **Scope: report only.** Phases A/B/C in §6 are the proposed remediation, **not yet
>   executed**. Nothing below has been applied.

**Grade: D+ (structurally unsound).** Nine entities, four with live contradictions. The
repo *mostly* derives from sources via `build.py`, but three hand-maintained side-tables
and one overloaded word ("thinker") break the "one source of truth" rule.

---

## 1. The triggering conflict: "thinker" is two different things

**Symptom.** The Developer's card shows **PRIME THINKER = OPUS**, but The Developer
**runs on / is routed as SONNET**.

**Root cause.** The word **"thinker" is overloaded** across two unrelated axes that live
in two separate, divergent tables:

| Axis | What it means | Where it's stored | Value for the-developer |
|---|---|---|---|
| **(a) Session model** | The default Claude Code conversation partner when the member is summoned (person → harness) | `the-developer.md:4` frontmatter `model:` → `guild-data.json` → routing-gate.sh | **sonnet** |
| **(b) Prime thinker (weapon)** | The orchestration brain for multi-model arsenal work (harness → many models); = first weapon whose role ∈ {thinker, both} by arrangement | `app.js` MODELS.role + arsenal order → `app.js:767` prime-thinker scan | **opus** |

These are **not in conflict by intent** — they answer different questions. They *look*
like a contradiction because both surface on the same card under words that collide
("thinker" / "model" / "brain"). The fix is not to make them agree on a value; it is to
(1) name them distinctly in the UI and (2) collapse the *role* axis to one table —
because right now even axis (b) is tracked in **three divergent places**.

---

## 2. THE HEADLINE DEFECT — three divergent role tables

Weapon role (thinker / doer / both) is independently declared in **three** locations that
**disagree on sonnet**:

| # | Location | sonnet role | Authority claimed | Reality |
|---|---|---|---|---|
| 1 | `app.js:49` `MODELS.sonnet.role` | **`"doer"`** | Comment at `app.js:35-42` declares MODELS "THE ARMORY" — the source of truth | **Wrong value** |
| 2 | `tools/conformity_check.py:31` `ROLE{}` | **`"both"`** | Hardcoded second table; gate that fails the build | Correct per all prose |
| 3 | `build.py:728` regex over `app.js` | reads #1 → **`"doer"`** | Silent reader; `except: pass` fail-open at `build.py:731` | Inherits the bug, silently |

All prose (`weapon-utility/SKILL.md:40`, `STRATEGIST-WORKFLOWS.md:91`, `members-meta.json`
weaponsDesc) says **sonnet = both**. So `app.js` — the file that *claims* to be the
source — holds the **one wrong value**, `conformity_check.py` is a second hand-maintained
truth that happens to be right, and `build.py` regex-scrapes the wrong one. **This is the
structural defect to fix first.** There must be exactly one role table; the other two must
derive from it or be deleted.

> **Note on impact:** because opus leads the thinker block and sonnet is pinned last, the
> sonnet=doer-vs-both bug does **not** change the prime-thinker *winner* (still opus either
> way). It is nonetheless a live contradiction: any other consumer reading sonnet's role
> gets a different answer depending on which table it trusts.

---

## 3. Every duplicated fact

| Fact | Locations (path:line) | Divergence | Severity | Single SoT |
|---|---|---|---|---|
| **sonnet weapon role** | `app.js:49` (=doer) · `conformity_check.py:31` (=both) · `build.py:728` (regex→doer) | **live-contradiction** | **critical** | one `data/models.json` |
| **All model role/label/color/tier/host/desc** | `app.js:44-105` MODELS | live-contradiction (no `data/` source; breaks repo pattern) | high | `data/models.json` |
| build.py reads MODELS via regex | `app.js:44-105` ↔ `build.py:728` | live-contradiction (fragile, fail-open) | high | read `data/models.json`, delete regex |
| Model tier vs TIER_RANK | `app.js:45-104` · `app.js:592` | redundant-but-consistent | medium | MODELS.tier; rank derived |
| Model `.call` pulled-status prose vs runtime `_pulled` | `app.js:81-104` · `app.js:139-145` | drift-risk | medium | runtime `_pulled` (drop prose) |
| weaponsDesc per member | `app.js` MODELS.desc → `members-meta.json:weaponsDesc` | drift-risk (generated, hand-editable) | high | MODELS.desc; regen, never hand-edit |
| weaponStatus (live/reserve/deactivated) | `members-meta.json:3-11` | redundant (intentional, manual) | medium | `members-meta.json` (operational) |
| **Member session model** | `<id>.md:4` · `guild-data.json` · `guild-routing-gate.sh:108-116` · `STRATEGIST-AUDIT.md` | drift-risk (hardcoded shell copy) | high | member `.md:4` frontmatter |
| guild-routing-gate.sh member→model strings | `guild-routing-gate.sh:108-116` | drift-risk (no automation) | medium | generate from `guild-data.json` |
| **Arsenal ordering rule** | `conformity_check.py:40-52` (code) · `guild-log.json` #25 (prose) · 9× `<id>.md:7` · `build.py:359-415` | redundant-but-consistent | high | `conformity_check.py:40-52` |
| "best-first" vs "relative order preserved" | `guild-log.json:316` · `conformity_check.py:44` | drift-risk (prose ambiguous) | medium | code; reword #25 |
| Member weapon loadouts (×4 copies) | `<id>.md:7` · `guild-data.json` · `guild-data.js` · `members-meta.json` | ok (all derived) | critical | member `.md:7` |
| Prime thinker = opus | `conformity_check.py:13,42-50` · `weapon-utility.md:31` | ok | low | `conformity_check.py` |
| Prime doer = minimax-m3 | `conformity_check.py:42-47` · `weapon-utility.md:37` | ok | low | `conformity_check.py` |
| sonnet pinned last | `conformity_check.py:51` · prose | ok | low | `conformity_check.py` |
| **Prime-thinker definition** (session vs weapon) | `the-developer.md:4` (sonnet) ↔ `app.js:767` (opus) | **RESOLVED** — Guild Master fixed it to the **weapon** (see §5) | — | `app.js:767` logic + `conformity_check.py` PT check |
| guild-data.json never loaded at runtime | `build.py:822-827` writes both · `index.html:73` loads only `.js` | live-contradiction (redundant artifact) | high | `.js` primary; `.json` for tooling |
| Skill presentation meta | `skills-meta.json` · `SKILL.md` frontmatter · guild-data artifacts | redundant-but-consistent | medium | `skills-meta.json` |
| Skill→member reverse index | `<member>.md:skills[]` → `build.py:492-501` | redundant-but-consistent (derived) | low | member `.md` skills[] |
| Workflows | `workflows.json` → guild-data | redundant-but-consistent (verbatim copy) | low | `workflows.json` |

---

## 4. The one source of truth per entity (and how others derive)

| Entity | **Single SoT** | Every other location → |
|---|---|---|
| **Model armory** (label, color, tier, host, role, desc) | **`data/models.json`** (NEW) | `app.js` MODELS loaded from generated `guild-data.js`; `build.py` reads JSON (delete regex at :728); `TIER_RANK` derived from tier; `conformity_check.py` ROLE **deleted** and read from models.json; `members-meta.json` weaponsDesc **regenerated** from it |
| **Member session model** | **`star-alliance-members/<id>.md:4`** | `guild-data.json` derived by build.py (already); `guild-routing-gate.sh:108-116` **generated** from guild-data.json (or validated by pre-commit); `STRATEGIST-AUDIT.md` is a dated snapshot, not a source |
| **Arsenal order rule** | **`tools/conformity_check.py:40-52`** (`expected_order()`) | `guild-log.json` #25 = rationale record only (reword to match code); member `.md:7` order produced/validated against it; `build.py` renders from it |
| **Member weapon loadout** | **`star-alliance-members/<id>.md:7`** | `guild-data.json/.js` + `members-meta.json` weaponsDesc all generated by build.py; never hand-edit the three artifacts |
| **Skills (content)** | **`star-alliance-skills/*/SKILL.md`** | reverse index computed in `build.py:492-501` |
| **Skills (presentation)** | **`data/skills-meta.json`** | guild-data artifacts generated |
| **Workflows** | **`workflows.json`** | guild-data artifacts (verbatim + artPng) |
| **Runtime artifact** | **`guild-data.js`** (browser) | `guild-data.json` kept ONLY as offline-tooling convenience; document it as secondary, never a source |

**Delete / demote:** `conformity_check.py:31` ROLE dict (→ read from models.json);
`build.py:728` regex (→ read JSON); hardcoded `guild-routing-gate.sh:108-116` strings
(→ generated); `app.js` `.call` pulled-status prose (→ runtime `_pulled`).

---

## 5. DECISION (LOCKED): prime thinker = the WEAPON, by arrangement

**Guild Master's ruling:** a member's prime thinker is **the highest-priority thinker
model based on its arsenal arrangement** — the first weapon whose role ∈ {thinker, both},
scanning the loadout left→right. If opus is the first thinker on the left, opus it is.
**Not** the session model.

This is exactly what the UI flag added this session does (`app.js:767`:
`eff.find(role==='thinker'||'both')`) and what `conformity_check.py`'s PT check enforces
(first thinker-capable weapon must be opus). **No code change needed for the definition.**

**Justification.**
- The prime-thinker concept names the **orchestration brain for arsenal/multi-model
  work** — planning and review across many models. That is inherently a *weapon-arsenal*
  property, already enforced end-to-end (`app.js:767`, `conformity_check.py:178-180`,
  `workflows.json` step.thinker, `build.py:748-753`). Defining it as the session model
  would break all four and make sonnet-session members (developer, architect, designer,
  translator, quartermaster) claim **sonnet** as prime thinker — which conformity_check.py
  is explicitly built to forbid.
- The **session model** answers a different question (default chat partner) and already
  has a clean SoT (`<id>.md:4`). It keeps its own, separate label.

**The contradiction is removed not by changing values but by naming the two axes
distinctly** so they never read as the same word. Recommended (deferred) UI relabel:
- Keep the weapon flag as **"Prime thinker"** (optionally qualified **"· arsenal brain"**).
- Add/relabel a separate **"Session model"** (or "Runs as") badge showing `<id>.md` `model:`.
- Net: *Session model: Sonnet* (how you chat) vs *Prime thinker: Opus* (how it orchestrates
  its weapons). No value changes; only the words stop overloading.

---

## 6. Sequenced remediation — PROPOSED (not executed)

> The Guild Master chose **report only**. The steps below are the recommended path when
> work is authorized. Smallest blast radius first; each phase is independently shippable.

### DECIDE (Guild Master sign-off required)
- **D1.** ~~Define prime thinker~~ — **DECIDED** (§5: first thinker-role weapon / opus).
- **D2.** Approve canonicalizing sonnet weapon role = **`both`** everywhere (matches all prose; fixes `app.js:49`).
- **D3.** Approve creating **`data/models.json`** as the model SoT (migrating MODELS out of `app.js`).
- **D4.** Approve generating `guild-routing-gate.sh` member→model lines from guild-data (vs. keeping them hand-synced with a pre-commit validator).

### MECHANICAL — Phase A: stop the bleeding (tiny, no schema change)
- **A1.** Fix `app.js:49` `sonnet.role: "doer"` → `"both"`. Run `python3 build.py`. *(Files: `app.js`; regenerates `guild-data.*`, `members-meta.json`.)* — resolves the critical role contradiction immediately, even before the bigger migration.
- **A2.** UI relabel per §5: `app.js` (session badge → "Session model"; prime flag → "Prime thinker · arsenal brain") at `app.js:767-776, 1031`. *(Files: `app.js`, `app.css` if styling.)*
- **A3.** Reword `guild-log.json` #25 to match code: "minimax-m3 pinned to lead, other doers in original order → opus pinned to lead, other thinkers in original order → sonnet last." *(Files: `data/guild-log.json`.)*

### MECHANICAL — Phase B: kill the duplicate role tables
- **B1.** Create `data/models.json` `{models:[{id,label,color,tier,host,role,desc,ollama_desc,call,meter}]}` from current `app.js` MODELS (with sonnet=both). *(Files: `data/models.json` NEW.)*
- **B2.** `build.py`: read `data/models.json`; emit MODELS into `guild-data.js`; **delete the `app.js` regex** at `:721-732`; have `load_model_roles()` read the parsed models. *(Files: `build.py`, `app.js` MODELS now sourced from guild-data.)*
- **B3.** `conformity_check.py`: **delete the hardcoded `ROLE{}`** at `:28-33`; read roles from `data/models.json`. *(Files: `tools/conformity_check.py`.)* — now exactly **one** role table.
- **B4.** Confirm `members-meta.json` weaponsDesc regenerates from models.json (no hand-edits). *(Files: `build.py`, `data/members-meta.json`.)*

### MECHANICAL — Phase C: close remaining drift
- **C1.** Per D4: either generate `guild-routing-gate.sh:108-116` from `guild-data.json` at build time, or add a pre-commit check validating those strings against it. *(Files: `.claude/hooks/guild-routing-gate.sh`, `build.py` or new hook.)*
- **C2.** Drop hand-edited pull-status prose from `app.js` MODELS.`call`; rely on runtime `_pulled` from `/api/arsenal`. *(Files: `data/models.json`, `app.js` render.)*
- **C3.** Document `guild-data.json` as **secondary** (offline tooling only; browser loads `.js`) in `build.py` header. *(Files: `build.py`.)*
- **C4.** Mark `docs/STRATEGIST-AUDIT.md` model rows as a dated snapshot, not a source. *(Files: `docs/STRATEGIST-AUDIT.md`.)*

### VERIFY
- **V1.** `python3 build.py && python3 tools/conformity_check.py` clean; grep that no role/model literal survives outside `data/models.json` + generated artifacts; confirm card shows distinct *Session model* vs *Prime thinker* labels.

**Order rationale:** A-phase is one-line corrections that end the live contradiction with
near-zero risk; B-phase removes the duplicate tables (the structural fix); C-phase mops up
drift-risk side-copies.
