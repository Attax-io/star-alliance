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
>
> **§7 added (deep cascade pass) — supersedes §4/§6 where they conflict:**
> - **"Demote `guild-data.json`" is REVERSED.** It is the Python-side runtime SoT —
>   `weapon-gate.py` + `high-alert.py` `json.load` it live; deleting it breaks hooks at
>   session runtime. `guild-data.js` = browser SoT. Both kept.
> - **"Generate `guild-routing-gate.sh`" is DOWNGRADED to a lint.** Those lines are
>   hand-edited doctrine prose, and the hook gates every turn — regeneration risk > reward.
> - **Model identity lives in 20 places across 12 files** (not just the 3 role tables) —
>   see the §7.2 census. `data/models.json` owns *semantic* facts only; routing/keys stay
>   in `summon.py`, cost stays in `models-usage.json` (§7.3).

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

> **⚠ Superseded by §7.6.** The deep cascade pass re-sequenced this plan (B is bigger than
> stated; guild-data.json demotion dropped; routing-gate generation downgraded to a lint).
> Use §7.6 as the authoritative remediation order.

---

## 7. Deep cascade & dependency analysis

This addendum supersedes §1–§6 where they conflict. It maps the full dependency graph behind each proposed fix, corrects four claims from the first pass, and re-orders remediation around the lockstep couplings that pass missed.

### 7.1 Corrections to the first audit

| # | First-audit claim | Reality (verified) | Evidence |
|---|---|---|---|
| C1 | `guild-data.json` is a redundant / never-loaded build artifact → demote/delete. | **WRONG and dangerous.** `guild-data.json` is the **Python-side runtime SoT**. Live hooks `json.load` it on every invocation. `guild-data.js` is the **browser SoT** (loaded via `<script>`). They are two emissions of one source, neither redundant. Demoting/deleting `guild-data.json` **breaks hooks at session runtime**, not just at build. | `weapon-gate.py:45` (`json.load(open(.../guild-data.json))` — weapon union); `high-alert.py:28-29` (member-id set for sub-agent dispatch detection) |
| C2 | `guild-routing-gate.sh` is just generated model→member assignments. | **INCOMPLETE.** Lines 108–116 are **hand-edited pedagogical prose** — routing doctrine with rationale ("why this specialist"), not just `member→model` pairs. It **never reads `workflows.json` or `guild-data.json`**. Auto-generating it would destroy the doctrine and couple a 1.3k-token FULL injection to `build.py`. | `guild-routing-gate.sh:108-116` (e.g. `code · features · bug fixes … → the-developer (sonnet)`) |
| C3 | `turn-cost.py` / `arsenal_usage.py` hold per-model pricing. | **FALSE.** Both are logging sinks. `turn-cost.py` logs actual transcript token usage; `arsenal_usage.py` writes `usage-log.jsonl` with **zero cost data**. The **only** hand-edited cost/quota registry is `star-alliance-arsenal/models-usage.json`, read solely by `serve.cjs` at runtime. | `arsenal_usage.py:1-51`; `models-usage.json:1-13`; `serve.cjs:116` (`loadUsage`) |
| C4 | `member-table-sync.py` / `serve.cjs` re-derive roles and may clobber consolidation. | **INCOMPLETE.** `member-table-sync.py` consumes the **declared** `weapons:` array from member `.md` frontmatter as-is — it IS the consolidation mechanism, not a clobberer. `serve.cjs:238` `setMemberField()` *does* live-write member `.md` files via `/api/save`, but performs **no slug/model-id normalization of `.md` bodies** (the `NORM` dict at `serve.cjs:181` only normalizes ids when *reading* `usage-log.jsonl`). The clobber risk is real but scoped to **field edits during an open dashboard**, not model-id rewrites. | `serve.cjs:238,398`; `serve.cjs:181` |

**Net correction:** the first audit's "demote guild-data.json" recommendation is **reversed**. Keep `guild-data.json` as the primary runtime artifact; the design (master sources → `build.py` → JSON → hooks read at runtime) is already the safe one.

### 7.2 Model-identity registry census

Model identity is duplicated across **20 independent locations in 12 files, with ZERO central source.** The headline duplication is the cloud-tag map: **5 copies** of `model-id → :cloud tag` across 4 files, none importing from a common origin.

| # | Location | Attribute owned | Kind | Sync status |
|---|---|---|---|---|
| 1 | `app.js` MODELS (`:44-105`) | label, color, tier, host, role, desc, ollama_desc, call, meter | **own-independent-registry** (UI SoT) | source for build regex |
| 2 | `app.js` ARSENAL (`:114`) | display order | derives-from-source | hand-maintained literal |
| 3 | `app.js` CLOUD_TAG (`:118-122`) | model-id → :cloud tag | **duplicate** | must match #6, #9 |
| 4 | `app.js` TIER_RANK (`:592`) | model-id → sort rank | **duplicate** | hand-maintained per model add |
| 5 | `app.js` ROLE_META (`:108-111`) | role → icon/label/rule (UI) | independent (UI config) | **stays — not model data** |
| 6 | `summon.py` CLOUD_TAG (`:24-31`) | model-id → :cloud tag (**routing SoT**) | own-independent-registry | dispatcher truth |
| 7 | `summon.py` CLAUDE (`:32`) | native-model set | own-independent-registry | routing |
| 8 | `summon.py` KNOWN_IDS (`:36-38`) | sorted routable catalog | derives (#6+#7) | routing |
| 9 | `serve.cjs` CLOUD_TAG (`:118-122`) | model-id → :cloud tag | **duplicate** | dashboard pulled-badge |
| 10 | `serve.cjs` WEIGHT (`:150`) | per-model consumption weight | **duplicate** | hand-tuned |
| 11 | `serve.cjs` NORM (`:181`) | tag → canonical id | **duplicate** | usage-log read only |
| 12 | `conformity_check.py` ROLE (`:27-34`) | model-id → role | **hardcoded duplicate** (contradicts #1 on sonnet) | stale-prone |
| 13 | `conformity_check.py` CLAUDE_NATIVE / MEDIA_WEAPONS (`:36-37`) | model categorization | hardcoded duplicate | stale-prone |
| 14 | `build.py` `load_model_roles()` (`:722-733`) | model-id → role | derives-from-source (regex over #1) | fail-open (see §7.5) |
| 15 | `members-meta.json` weaponsDesc / weaponStatus | model-id keys + per-member prose + status flags | duplicate / **status authority** | derived desc, hand-edited status |
| 16 | `ultra_brainstorm.py` `_DEFAULT_ORDER` (`:53-60`) | panel order | **hardcoded duplicate** — **already drifted** from #2 (cheapest-first vs tier-then-alpha) | NO sync |
| 17 | `gen-weapon-art.cjs` WEAPONS (`:16-77`) | model-id + color + prompt | hardcoded duplicate | silent-skip new models |
| 18 | `gen-weapon-gif.cjs` WEAPONS (`:18-30`) | model-id + color hex | hardcoded duplicate | silent-skip |
| 19 | `models-usage.json` (`:1-13`) | model-id → spent/quota/unit | **cost authority** (runtime only) | never seen by build |
| 20 | `weapon-art/*.png`, `role-art/*.png` | model-id → PNG (filename convention) | implicit registry | unvalidated, orphans accumulate |

Artifacts that are **read-only** to identity (correctly derived, not sources): `guild-data.json`/`.js` (`members[].weapons[]`), `workflows.json` (`steps[].thinker/doers[]`). These must NOT be edited to add a model.

### 7.3 Separation-of-concerns ruling

**Do NOT blindly centralize.** `data/models.json` must own only **UI / semantic facts**. Routing, provider endpoints, API keys, and live cost MUST stay in the dispatcher and usage layer. Centralizing routes/keys into a browser-loaded UI registry would ship dispatch internals to the client.

| Attribute | Post-consolidation home | Rationale |
|---|---|---|
| label, color, tier, role, host, desc, ollama_desc, glyph | **`data/models.json`** (UI/semantic SoT) | static display facts; emitted into `guild-data.js`/`.json` by `build.py` |
| ARSENAL order, TIER_RANK | **`data/models.json`** (derived from tier), emitted | kills hand-maintained literals #2, #4 |
| `:cloud` tag / routing dispatch | **stays in `summon.py:24-31`** (routing SoT) | dispatch detail; `serve.cjs`/`app.js` CLOUD_TAG become **one-way synced** (or read a build-emitted copy) — never the origin |
| native-model set, KNOWN_IDS | **stays in `summon.py`** | router catalog |
| API keys, provider base URLs | **stays in `ollama_cloud.py` / `minimax.py` / env** | secrets — never in a UI registry |
| spent / quota / unit (live cost) | **stays in `models-usage.json`** | hand-edited operational, runtime-only |
| consumption WEIGHT | **stays in `serve.cjs:150`** OR moves to models.json `meter` | dashboard estimation; if moved, `/api/arsenal` must cache-bust on rebuild |
| weaponStatus (deactivated/reserve) | **stays in `members-meta.json`** | deployment-time operational status, not UI semantics |
| panel `_DEFAULT_ORDER` | derive from models.json ARSENAL | resolve the existing #16 drift |

**Ruling:** `data/models.json` is the **semantic** SoT. `summon.py` remains the **routing** SoT. `models-usage.json` remains the **cost** SoT. Conformity's `L`-check must keep validating that every loadout weapon is **routable by `summon.py`** (`conformity_check.py:339-341`), not by `models.json` — routability is a dispatcher property.

### 7.4 Cascade map per proposed fix

Severity legend: **breaks-build** (build.py errors/skips) · **breaks-runtime** (browser dashboard) · **breaks-hook** (a hook errors/mis-validates — ⚠ may BLOCK the session) · **silent-drift** (no error, data diverges) · **cosmetic**.

#### Fix A — `sonnet.role: 'doer' → 'both'`
| Must change in lockstep | Severity | Note |
|---|---|---|
| `app.js:49` (the edit itself) | breaks-runtime if mistyped | `build.py:728` regex auto-inherits new value into `guild-data.*` |
| `conformity_check.py:31` | — | already `"both"`; would now AGREE (today it silently contradicts app.js) |
| `build.py:790` `validate_step_weapons` | **silent-drift** | sonnet now passes as a workflow *thinker* where it previously failed — intended, but undocumented behavior change |
| `guild-routing-gate.sh:108-116` | **silent-drift** | hardcodes `the-developer (sonnet)` as specialist; never reads role — will NOT reflect dual status |

**Ordering:** safe to do first and standalone. It only *resolves* the live contradiction (`app.js:49`='doer' vs `conformity_check.py:31`='both'). No hook blocks.

#### Fix B — create `data/models.json` (semantic SoT)
| Must change in lockstep | Severity |
|---|---|
| `build.py:722-733` `load_model_roles()` — repoint to read JSON, keep app.js fallback | **breaks-build** |
| `conformity_check.py:27-37` ROLE/CLAUDE_NATIVE/MEDIA_WEAPONS — load from JSON via shared loader | **breaks-build** |
| `app.js:106` `modelMeta()`, `:1022` `modelLabel()` — read `GUILD.models` emitted by `guild-data.js` (not inline MODELS) | **breaks-runtime** |
| `app.js:142` `refreshArsenalData()` — `MODELS[id]._pulled` mutation must move to a client-side state object (MODELS may be immutable/emitted) | **breaks-runtime** |
| `build.py` must EMIT `MODELS`, `ARSENAL`, `TIER_RANK`, `CLOUD_TAG` into `guild-data.js` | **breaks-runtime** if omitted |
| `ultra_brainstorm.py:53-60` `_DEFAULT_ORDER` | silent-drift (already drifted) |
| `gen-weapon-art.cjs:16-77`, `gen-weapon-gif.cjs:18-30` colors | silent-drift |

**Ordering:** B must land **before** any deletion (C, D). `models.json` must validate before any `guild/*.py` or hook runs.

#### Fix C — delete `app.js` MODELS regex parsing in `build.py`
| Must change in lockstep | Severity |
|---|---|
| `build.py:722-733` — depends on B done; else `load_model_roles()` returns `{}` and `validate_step_weapons` **fail-opens silently** (workflows unvalidated) | **breaks-build** |
| `app.js` MODELS object itself — must still exist for the dashboard OR `guild-data.js` must carry full defs | **breaks-runtime** |
| `skill-md.js:55` weapon-utility prose mentions of MODELS roles | cosmetic |

**Ordering:** strictly **after** B. Deleting the regex without `models.json` in place is a build break + silent workflow-validation hole.

#### Fix D — delete `conformity_check.py` ROLE dict (`:27-34`)
| Must change in lockstep | Severity |
|---|---|
| `conformity_check.py:48,51` `expected_order()` — consumes ROLE; must read the shared loader instead | **breaks-build** (sweep) |
| `conformity_check.py:163-184` arsenal-order validation — same dependency | **breaks-build** |
| Decide SoT for member role parity: if `guild-data.json.members[].role` wins, also remove `members-meta.json.role` + its parity check, else keep both | silent-drift if undecided |

**Ordering:** after B. ROLE is a hardcoded duplicate of the new SoT.

#### Fix E — generate `guild-routing-gate.sh`
| Must change in lockstep | Severity |
|---|---|
| `guild-routing-gate.sh:108-116` — **hand-edited doctrine prose** (per C2). Generation **loses rationale**. | **silent-drift** + doctrine loss |
| New generator location (`build.py`? `guild/gen-routing.py`?) + provenance comment marking the FULL injection machine-generated | — |

**Ordering / ruling:** **Defer or reject.** This is the highest-risk, lowest-reward fix. Recommend keeping it **hand-edited** and adding a conformity check that the member→model pairs in it match `guild-data.json` (lint, not regenerate). ⚠ This hook gates the session via the workflow banner system — a malformed regeneration **blocks every turn**.

#### Fix F — demote / relabel `guild-data.json`
| Reality | Severity |
|---|---|
| `weapon-gate.py:45`, `high-alert.py:28` `json.load` it at runtime | **breaks-hook ⚠ BLOCKS SESSION** |
| Demotion reversed per C1 | — |

**Ordering / ruling:** **Reject demotion.** Permitted: the §5 **UI relabel** ("Session model" badge for `<id>.md:4` vs "Prime thinker" for arsenal weapon) — that touches `app.js:767-776` render + CSS only (**cosmetic**), and does NOT alter the artifact. Keep `guild-data.json` as primary runtime SoT.

**Session-blocking hooks to guard during migration:** `weapon-gate.py` (reads `guild-data.json` + valid model IDs at `:108`), `guild-routing-gate.sh` (FULL banner injection), `workflow-gate.py` / `workflow-banner-enforcer.py`, and `okf-gate` (blocks non-conformant `.md` writes). Any of these erroring **halts all tool use**. Run `build.py` and validate `guild-data.json` **before** these hooks fire in a fresh session.

### 7.5 Hidden coupling risks

1. **`build.py` regex fail-open masks errors.** `load_model_roles()` returns `{}` on any exception (`build.py:722-733`), and `validate_step_weapons` (`:790`) then **skips silently** — workflows become unvalidated with no error. Today this also means `app.js:49`'s `sonnet='doer'` bug is **silently inherited** into `guild-data.*`. During migration, a malformed `models.json` would fail-open the same way. **Mitigation:** make the loader **fail-closed** (raise + nonzero exit) for the duration of the migration.

2. **`serve.cjs` live-rewrites member `.md` (clobber window).** `setMemberField()` (`serve.cjs:238`) and siblings write member `.md` files via `/api/save` (`:398`) whenever the dashboard control panel is open. A hand-migration of `weapons:` frontmatter or roles can be **clobbered by a stale dashboard write-back**. **Mitigation:** stop `serve.cjs` (or close the dashboard) for the entire migration; re-read each `.md` immediately before editing (per project reading discipline).

3. **MODELS used before `guild-data.js` loads (load-timing).** Post-B, `app.js` `modelMeta()`/`modelLabel()` must read `GUILD.models` emitted into `guild-data.js`. If any top-level `app.js` constant (ARSENAL, TIER_RANK, CLOUD_TAG at `:114/:592/:118`) evaluates before the `guild-data.js` `<script>` executes, it reads `undefined`. **Mitigation:** emit those four into `guild-data.js` and ensure its `<script>` precedes `app.js`; `modelLabel()`'s existing `typeof MODELS !== 'undefined'` guard (`:1022`) must be repointed, not relied upon.

4. **Art files keyed by model-id (rename breaks art).** `weapon-art/<model-id>.png` (15 files), `role-art/*.png`, and the duplicated WEAPONS lists in `gen-weapon-art.cjs:16-77` / `gen-weapon-gif.cjs:18-30` are keyed by raw model-id with **no conformity check** for missing/orphaned tiles. Renaming a model (or its color) silently: orphans the old PNG, renders a fallback for the new id, and diverges the generator's hardcoded hex. **Per project memory, these `.png` are JPEG-bytes-named-`.png`; re-encoding in place is required, not renaming.** **Mitigation:** add a conformity check (tile exists for every routable id) and source generator color/id from `models.json`.

5. **`models-usage.json` invisible to build (`:1-13`).** Never read by `build.py`/conformity — a model present there but absent from `app.js`/`models.json` is **never caught at build**, only surfaces as a wrong dashboard gauge. **Mitigation:** add a conformity cross-check `models-usage.json` keys ⊆ `models.json` ids.

6. **`SA_MODEL_ID` single thread-point.** `summon.py:109` sets `SA_MODEL_ID`, consumed by `minimax.py:105`, `ollama_cloud.py:262`, and `arsenal_usage.py`. Inserting a routing-gate/tier shim before `summon.py` that alters this env var **mis-attributes the usage log** with no validation. Keep any gate's id-set in lock-step with `summon.py` KNOWN_IDS (`:36-38`).

### 7.6 Revised remediation order

The first audit's Phase A/B/C are re-sequenced around the lockstep dependencies above. Two reversals: **guild-data.json demotion is dropped**, and **routing-gate generation is downgraded to a lint**.

**Phase A — resolve the live contradiction (standalone, no hook risk)**
- A1. `app.js:49` `sonnet.role → 'both'`. Auto-propagates via `build.py:728` regex; now agrees with `conformity_check.py:31`. *(Fix A — cosmetic blast radius beyond the edit.)*
- A2. UI relabel "Session model" vs "Prime thinker" (`app.js:767-776` + CSS). *(The only sanctioned piece of old "demote/relabel guild-data" — cosmetic.)*
- A3. Reword `guild-log.json` #25 and `STRATEGIST-WORKFLOWS.md:25,91` to match code invariant.

**Phase B — build the semantic SoT (bigger than audit #1 assumed)**
- B1. Create `data/models.json` (label, color, tier, host, role, desc, glyph, ARSENAL order, TIER_RANK). **Routing/keys/cost excluded** (§7.3).
- B2. Make `build.py` **fail-closed** (drop fail-open) and EMIT `MODELS`/`ARSENAL`/`TIER_RANK`/`CLOUD_TAG` into `guild-data.js`/`.json`.
- B3. Repoint `build.py:722-733` and `conformity_check.py:27-37` to a **single shared loader** over `models.json`.
- B4. Repoint `app.js` `modelMeta()`/`modelLabel()`/`refreshArsenalData()` (`:106/:1022/:142`) to emitted `GUILD.models`; move `_pulled` mutation to client state.
- ⚠ **Bigger than audit #1 stated:** B is not "add a JSON file" — it is a build-emission refactor of `guild-data.js` plus 4 app.js read-path changes plus a fail-open → fail-closed flip. Do B atomically with `serve.cjs` stopped (§7.5 risk 2).

**Phase C — delete the now-redundant duplicates (strictly after B verified)**
- C1. Delete `build.py` app.js regex path (keep JSON loader). *(Fix C — breaks-build if B incomplete.)*
- C2. Delete `conformity_check.py` ROLE dict `:27-34`; `expected_order()` reads shared loader. *(Fix D.)*
- C3. Source `gen-weapon-art.cjs`/`gen-weapon-gif.cjs` colors and `ultra_brainstorm.py:53-60` order from `models.json`; resolve existing `_DEFAULT_ORDER` drift.

**Phase D — conformity hardening (new; closes the silent holes)**
- D1. Add checks: every routable id has a `weapon-art` tile; `models-usage.json` keys ⊆ `models.json`; `serve.cjs`/`app.js` CLOUD_TAG == `summon.py` CLOUD_TAG; `guild-routing-gate.sh` member→model pairs == `guild-data.json`.

**Dropped / downgraded from audit #1:**
- ~~Demote `guild-data.json`~~ → **KEPT as Python runtime SoT** (C1/F). Reversed.
- ~~Generate `guild-routing-gate.sh`~~ → **lint-only (D1)**, prose stays hand-edited. Session-blocking hook; regeneration risk > reward (Fix E).

**Lockstep one-liner:** A is independent; **nothing in C may precede B**; D follows C; F is rejected except its cosmetic relabel (folded into A2). Throughout, keep `serve.cjs` stopped and validate `guild-data.json` before a fresh session so `weapon-gate.py`/`guild-routing-gate.sh`/`workflow-gate`/`okf-gate` don't block.
