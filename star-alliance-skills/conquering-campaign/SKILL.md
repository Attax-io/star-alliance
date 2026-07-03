---
name: conquering-campaign
description: "Multi-wave campaign skill for work too big for one pass. Three modes — AUDIT (reconcile docs with code/DB), BUILD (multi-phase features/refactors/migrations touching 3+ surfaces), EXTENSION (extends a recent predecessor, reusing its prescan). Gate G0 runs FIRST: work that doesn't clear the bar (3+ INDEPENDENT logical changes — one vertical slice = ONE — OR genuinely multi-phase, OR an app-wide doc-code/DB audit) is declined and routed to a lighter pass, no folder created. Triggers ONLY above that bar: 'audit my app', 'build this feature', 'ship this refactor', 'phase this migration', 'proceed in application', 'extend [campaign] to X', 'roll out [pattern] to [surface]'. Planning asks every question upfront then executes autonomously. At the BUILD wave, parallel disjoint writes deploy as a worthiness-gated SWARM via decompose-and-swarm (workers run as the member brain; conformity closes ONCE). Enforces always-on pre-flight gates, conformity, consolidation, self-verification. Full detail in references/."
metadata:
  version: 3.9.0
type: Skill

---
# Conquering Campaign

## Core philosophy

**Plan thoroughly. Then conquer without stopping.**

Two phases, hard boundary between them:

1. **Planning** — ask every question, surface every ambiguity, map every surface, get full alignment. The user is in the loop. Nothing is assumed.
2. **Execution** — work autonomously through the waves. Self-verify after every phase. At a fork, follow the decision ladder instead of asking. When done, clean up + log — unprompted.

The boundary is plan approval. Before it: ask everything. After it: conquer.

Three always-on disciplines ride through execution: **conformity** (match the app's existing patterns, don't invent), **consolidation** (extract shared primitives, never copy-paste), **self-cleanup** (dead code deleted, plan flipped to `completed`, vault-log written immediately, memory entries saved — without being asked).

---

## Pre-flight gates (always-on — these fire at the moment of action, not from memory)

A buried rule fires as a user correction because the agent doesn't reach it at the decision moment. These seven gates are short on purpose — run the relevant one *before the action*, every time, regardless of scope or cadence.

- **G0 — Campaign-worthiness triage-or-EXIT (the FIRST gate — runs before Step 0; decides *whether* to run, not *how*).** Before creating ANY folder / frontmatter / `/goal` line / spawn: does the work clear the **BUILD bar** (≥3 **INDEPENDENT logical changes**, OR genuinely multi-phase, OR must-stay-deployable staging) or the **AUDIT bar** (a real doc↔code/DB reconciliation across the app)? If NOT → **EXIT**: state "this is a {direct edit · single bug-fix · `/cleanup <mode>`}, not a campaign," route to the lighter tool, no artifacts. **Count independent changes, not layers:** one bug threading RPC + mutation + UI + i18n is ONE change, not "4 surfaces." Three independent changes = three things that could ship as three PRs. Route map: color/contrast → `/cleanup colors/lint` · i18n → `/cleanup language` · postgres → `/cleanup postgres` · lint/tsc → `/cleanup lint` · a single migration/view with no FE fan-out → direct edit · a one-file bug → just fix it (`scope: bug-fix` ONLY for a shipped bug in a predecessor-excluded surface). **File count is NOT the bar — surfaces/staging is.** `micro` is retired (it IS this exit). Override only on explicit insistence (`g0_override: <reason>`). No **scope-inflation** (`scope: medium|full` on a 1–2-file folder to pass the declaration gate — it should have EXITed). G0-as-prose alone did NOT bite (the over-invocation decision is made the instant a trigger matches), so it's ALSO enforced by a **PreToolUse hook** (`.claude/scripts/g0-campaign-guard.sh`, matcher `Write`) surfacing a human checkpoint on every NEW `00-campaign-plan.md` write (resumes/edits pass; fail-open). Full post-mortem: references/failure-modes.md #101–#103.
- **G1 — Reuse before build (before writing ANY component / style / button).** Grep current + sibling surfaces for an existing primitive first; hand-rolling one that exists is a failure (P9). Name the EXACT reference leaf file (design language lives 2 hops down: `Row → ActionBar → GhostIconButton`) and extract every token before writing. **Reusing/surfacing an existing component in a new flow counts as shipping it** — OPEN it first and confirm it speaks the project's current design register (stale chrome riding into a new flow is the same failure as hand-rolling); migrate it FIRST. Full procedure: references/fe-i18n-playbook.md → Conformity extraction. (#4 #22 #26 #27 #49 #83)
- **G2 — Verify project_id (before ANY Supabase MCP call).** Confirm the project_id from `.env` (lex_council prod = `bqgrpnsvplvicnmzxwkm`). An MCP `-32600`/permission error = WRONG project_id, NOT a harness block. **Distinguish the signature:** a network/`ERR_FAILED` on even a parameterless call, or MCP tools missing at session start, is a **stale handle on reconnect** — re-attach (`/mcp`) and retry once, don't blame `project_id` or declare it down. On a feature branch, writes target the branch project until merge. (#B2)
- **G3 — DB-wave re-probe (at the START of every DB wave).** Production schema can flip mid-session. Re-probe live schema + the `supabase_migrations` ledger; STOP + reconcile if foreign migrations interleaved. Before any rename/drop: grep ALL function bodies (text) AND FE callsites (`.from()`/`.select()`). Before diagnosing a slow query: `ANALYZE` for stale stats. On any RLS wave: sweep `pg_policies WHERE qual='true'` and PROVE effective access with `RLS-IMPERSONATE` — never read policy text as proof (#104). Full procedures: references/db-playbook.md. (#32 #33 #67 #68 #69 #104)
- **G4 — Defer to project memory & standing instructions (at plan time + before any verification action).** Read project memory + standing instructions. **The project's instruction wins over the skill's default.** Sacred `> [!atta]` blocks are supreme — never edit them; they outrank CLAUDE.md, docs, AND the user's request (on conflict surface it). Read the leaf doc BEFORE introspecting the DB (docs-before-SQL, P11/P13); `docs/archived/` is off-limits unless granted. lex_council: **preview is the USER's job — never run preview tools / never start-kill the dev server**; **lead every response with a plain-English status block**. When a project owns preview, hand off a recipe. (P8, #17)
- **G5 — Close checklist (before declaring done).** Vault-log written (no exemption — P10) + sibling-scan + nav-audit if a route changed + **dormant-gate audience probe** (a new perm/scope/tier value → COUNT the live rows that satisfy it; zero-row gate ships as `CHK-` + "dormant until X", never silent green; #106) + `99-risk-sweep.md` EXISTS + memory entries + commit if granted + spawn the cleanup follow-up (§5.7). Don't stall waiting to be told to finish. (#7 #11 #13 #77 #81 #90 #106)
- **G6 — DB-object conformity (before creating/altering ANY table / view / trigger / RPC).** The DB twin of G1 — conform to the app's binding v2 conventions, don't invent: naming, security boilerplate (`SECURITY DEFINER`+`search_path=''`+REVOKE/GRANT+`auth.uid()` guard; `security_invoker=true` views), ONE `FOR ALL` RLS policy from the named bundle catalog (W6, never inline `EXISTS`), `view-registry.ts` key (W3), `callRpc` through `lib/mutations/` (C4, never `.from().insert()`), soft-delete-only (C31). **Public/anon reads** (SSR/sitemap/robots/marketing) → anon-granted `SECURITY DEFINER` RPC, never a `security_invoker` view (anon base-SELECT fails `42501` *silently* → 0 URLs, #105). **No `USING(true)`** on an `authenticated`-granted multi-tenant table — prove effective access via `RLS-IMPERSONATE` + sweep `pg_policies WHERE qual='true'`; policy text is a lead, not proof (#104). Read the leaf doc FIRST (V2-CONVENTIONS / RLS-BUNDLES / DB-NAMING; docs-before-SQL). Full checklist: references/db-playbook.md → G6. (#88, W2–W6)

---

## Standing principles

Always-on. A violation is a campaign failure, not a "consider this." (P8–P10 were the top recurring corrections in the 136-campaign mine.)

| # | Principle |
|---|---|
| P1 | **W0 runs when Ollama is available.** Free tokens; the prescan compresses every W1 subagent's exploration. Skip only via a documented reason recorded in `w0_enabled:` (see §0.5 skip table). |
| P2 | **Plan carries the model-assignment table.** Every Agent call: task ID + subagent type + model + effort + output file. No table → plan can't be approved. |
| P3 | **Execution doesn't stop for resolvable forks.** The decision ladder handles everything that isn't irreversible+high-risk. Stopping mid-execution means the interrogation was incomplete — and don't over-ask on a clear request either. |
| P4 | **Conformity over invention.** Read the pattern docs + the reference's full render before writing FE; for any new DB object follow V2-CONVENTIONS naming + the security boilerplate + the RLS bundle catalog (G6). Inventing a new style — or a hand-rolled inline RLS policy — is a failure. |
| P5 | **Consolidation over copy-paste.** N=3 alarm fires on file-clone (#27) AND union-prop (#58). Extract before composing N times. |
| P6 | **Vault-log writes immediately at §5.3** — not "later", not "when asked". |
| P7 | **Dead code deleted at §5.1** via grep-proof + `rm`. Plans list candidates only. |
| **P8** | **Defer to project memory & standing instructions over skill defaults.** Read memory at plan time; on conflict the project's instruction wins (preview-ownership, response format, project facts). See G4. (#B-conflict) |
| **P9** | **Reuse before build.** Grep current + sibling surfaces for an existing primitive before writing any component/style/button. See G1. (top failure: 11/14 mined batches) |
| **P10** | **Vault-log has no exemptions** — not a "small tweak", not "still in the same conversation". Every code/DB change logs at close. See G5. (2nd failure: 10/14 batches) |

The numbered failure modes (references/failure-modes.md) are specific traps with cures; principles are the always-on rules.

---

## Two modes (+ extension)

| Mode | Goal | Subagents | Final artefact |
|---|---|---|---|
| **AUDIT** | Reconcile docs with code/DB reality | read-only — write findings files only | promoted source-of-truth docs + vault-log |
| **BUILD** | Ship a multi-phase feature/refactor that stays deployable at every step | may write code/migrations per phase under the cadence | shipped feature + vault-log + risk sweep + tests pass |
| **BUILD · Extension** | A build extending a predecessor that shipped ~≤30 days ago on the same surface | as BUILD, but W1 shrinks to a 1-task probe or is skipped; W0 may be skipped | shipped extension + vault-log linking the predecessor + risk sweep diffing the predecessor's |

If the user wants a quick one-file check or single bug fix, this skill is overkill — say so and offer a lighter pass. For genuinely small-but-real work, use the `scope` tiers (§Step 2) rather than refusing.

**Detect extension intent:** the user names/links a predecessor that completed recently, or describes the work as propagating recently-shipped primitives to new consumers ("extend v1.7.3 to members + clients", "roll out the portal-shell to clients"). Then: run as BUILD, set `predecessor:` frontmatter, skip W1, consider skipping W0 (§0.6).

**What "good" looks like** — AUDIT: `<root>/audit-campaigns/<date>_<topic>/` with numbered findings + `99-synthesis.md`, docs rewritten via `docs/staged/` then promoted, CHECKPOINTs registered, vault-log filed, `status: completed`. BUILD: `build-campaigns/<date>_<topic>/` with `00-campaign-plan.md` + per-phase files + `99-risk-sweep.md`, each phase independently deployable, shared primitives extracted before composing, dead code deleted, one vault-log, memory entries, `tsc + lint` clean, `status: completed`, feature ships.

---

## Step 0 — Resume, environment, prescan

Run before Step 1, every time. **Trigger precedence when several rules match: see §Trigger-phrase precedence.**

### 0.0 — Resume / pivot classification
Check `grep -rl "status: in-progress" <roots>/*-campaigns/*/00-campaign-plan.md`. The plan frontmatter (`status`, `current_phase`, `phases_completed`, `phases_remaining`, `pN_result:`) **IS the crash-recovery log** — keep it accurate after every phase (compaction can occur mid-campaign; this is the only clean resume point). If resuming: read the plan, skip W0/W1/W2, jump to the next incomplete phase.

| Situation | Rule |
|---|---|
| `in-progress` campaign on disk | Resume from frontmatter; skip W0–W2. |
| **Same-session pivot** — predecessor closed THIS session + user names a deficit ("you missed", "doesn't match X") | §0.0.1: don't open a new campaign. Reopen the predecessor plan (`completed → in-progress`, push a `P*_pivot` phase, `discovered_during: same-session-pivot`), skip W0+W1, run W3+W4, **edit the vault-log in place** (never duplicate). |
| **Pivot-chain** — ≥2 prior pivots on the predecessor + plan >6 phases + new pivot adds NEW surface | §0.0.3: batch close-out (flip status once); fire ONE spin-off `AskUserQuestion` (keep chaining / spin off / re-plan). Mark `pivot_class: depth|scope-expansion` — a pure depth-chain (same surface, tighter) skips the gate. |
| **Reset TodoWrite** | §0.0.2: a fresh campaign resets the session todo list before the first Bash/Agent call. Resume/pivot keep the list. |
| **Status-coherence** | `status: planning` + empty `phases_completed` + no risk-sweep = never-started → skip for lesson-mining, flag open. An empty folder = a planning failure (write a skeleton plan at create). |
| **Audit lens-extension** — an AUDIT closing/closed THIS session + a NEW read-only lens ("also check X", "improve the audit") | §0.0.6: reopen (`completed → in-progress`), push an `LN_lens` phase (`discovered_during: same-session-lens`), run W1/W3 read-only, fold into `99-synthesis.md` + the build-plan-proposal IN PLACE, **edit the vault-log in place**, re-close. |

### 0.0.4 — Preview reachability + ownership (probe once/session)
**First check G4 / project memory:** if the project owns preview verification, set `preview_verification: user-owned`, never run preview tools — hand off a recipe. Otherwise probe past the login wall (`curl -s -m5 <gated-route> | grep -qE 'Loading|/login|Sign in'`); auth-walled with no test session → `preview_verification: blocked-by-auth` + reason, stop adding preview steps (code-only verification is enough — say so). (#38)

### 0.0.5 — Monorepo artifact roots (probe once/session, before the plan)
`find . -maxdepth 4 -type d -name docs` + `find . -maxdepth 5 -type d -name vault-logs`. Record `campaign_folder_root`, `vault_log_root` (co-locate by default), `claude_md_path` (often workspace root even when docs nest), `wikilink_convention` (`bare-filename` co-located, `relative-path` when roots differ). At §5.2 assert every `[[…]]` matches the convention. (#46)

### 0.0.6 — Audit same-session lens-extension (read-only — the AUDIT twin of §0.0.1)
The §0.0 table "Audit lens-extension" row carries the rule (reopen, push `LN_lens`, fold IN PLACE, edit the vault-log in place, re-close — precedence ~2). Chaining lenses is fine; a lens uncovering a SHIPPED bug or demanding a WRITE escalates OUT to `bug-fix`/EXTENSION. Full prose: references/failure-modes.md #98.

### 0.1–0.6 — Environment + W0 prescan
- **Cowork:** skip 0.2–0.5, set `w0_enabled: no`, go to Step 1. **Claude Code CLI:** continue.
- **Probe Ollama** (`ollama list`). If `OLLAMA_OK`, W0 is mandatory unless a skip-row below applies — the prescan is the shared grounding doc every W1+ subagent reads FIRST.
- **Models:** auto-select from `ollama list` — `qwen2.5-coder:*` for code/grep, `qwen3:8b|14b` for summarisation; avoid `deepseek-r1`. On Apple Silicon attempt regardless of the "available RAM" reading.
- **Run the prescan** (main agent, Bash) → `00-w0-offline-prescan.md`. ALWAYS strip ANSI + thinking traces (`ollama run --hidethinking … 2>&1 | sed -E 's/\x1b\[[0-9;?]*[a-zA-Z]//g' | grep -vE '^(Thinking|Okay)'`); for JSON W3 tasks prefer the REST API (`/api/generate`, `"stream":false`) — the CLI corrupts JSON. (#16)
- **Validate the prescan (§0.5.1)** before W1 cites it: real line counts/names, or echo-back placeholders? Set `w0_useful: yes|no|partial` (+ `w0_note:`). If `no`, tell W1 to read cold. (#30)

**W0 skip table** — set `w0_enabled:` to the value when a row matches:

| Condition | `w0_enabled:` value |
|---|---|
| Ollama unavailable / Cowork | `no` |
| ≤10 files in scope | `skipped — small-scope build (<10 files)` |
| Content-only + structure already mapped (grep/diff/CSV) | `skipped — content analysis already complete via <method>` |
| Symbolic dead-code sweep (grep/find/ts-prune/knip more precise) | `skipped — deterministic tooling preferred` (+ `w0_note:`) |
| Extension of recent predecessor (§0.6) | `skipped — extension; predecessor's discovery is the input` |
| Same-session pivot (§0.0.1) | `skipped — same-session pivot` |

If none match and Ollama is available, W0 runs.

### 0.7 — Orchestration capability (probe once/session)
The deterministic **Workflow tool** (JS orchestrating subagents — `parallel`/`pipeline`/`schema`/`log`/`resume`) MAY be present on Claude Code CLI; ABSENT in Cowork/headless. Same two limits as `/goal`: opt-in only, can't ask mid-script. So the skill **EMITS** a ready-to-run script (never invokes it); the in-message parallel `Agent`-call dispatch is the portable DEFAULT (it already barriers, so a deterministic barrier buys little). The narrow win: the `>20-file source-walk` batch. Set `workflow_available:` + `workflow_emitted:` per the skip table. Full eligibility + primitive-mapping: references/wave-playbook.md → Deterministic orchestration. (#94)

**Workflow EMIT skip table** — set `workflow_emitted:` to the value when a row matches:

| Condition | `workflow_emitted:` value |
|---|---|
| Cowork / headless (tool absent) | `no — tool absent (portability)` |
| No parallel-barrier read-only wave / micro–small single-file scope | `skipped — no parallelizable wave` |
| < ~3 tasks in the biggest wave | `skipped — below fan-out threshold; direct Agent dispatch simpler` |
| Attended run already driven by the cadence | `skipped — attended run rides the cadence` |

If none match and the tool is available, emit the script per-wave (§Step 2).

---

## Step 1 — Planning interrogation

The **only** time Claude stops to ask. After approval, autonomous until conquered.

### 1.1 — Consult memory + past campaigns first (silent)
Scan project memory (`docs/memory/MEMORY-INDEX.md`) for scope-matching entries + past `99-risk-sweep.md`/`99-synthesis.md` for recurring traps on the same surfaces; read the project guidelines. Pre-loading prevents repeating past mistakes (G4/P8).

### 1.2 — Ask ALL of these in one batch (don't scatter)
**Scope:** (1) build/audit what? (2) which surfaces (schema/RLS/views/triggers/types/FE/admin/mutations/docs)? (3) constraints? **Multi-page: merge same-domain pages into one surface, or keep separate?** (#82) — **Authority:** (4) cadence (`strict`/`autonomous`/`hybrid`); (5) decision authority (default: recommended option + log); (6) edge cases (default: handle if green/amber, CHECKPOINT if red). — **Pattern:** (7) reference file/page to mirror (EXACT leaf file); (8) consolidation targets (reuse vs extract). — **Verification:** (9) success criteria + the **browser verification recipe** (smallest test proving the user-facing outcome — "set X, navigate Y, poll Z, expect W in N ms"); CRUD/editor needs BOTH render AND interaction recipe (click→type→save→reload→confirm persisted→revert→confirm restored); contrast/dark-mode needs a WCAG ratio; (10) verification method (`tsc+lint` only or also preview — honor G4 preview-ownership; content-only → JSON-validity + deep-flatten diff + placeholder-free). — **Past context (state, don't ask):** (11) memory entries I'll follow; (12) traps I'll avoid; (13) inherited standing instructions — quote VERBATIM into `standing_instructions:`, confirm they still apply (a conflicting one must be explicitly lifted + replaced, not silently carried). (#31)

If the user's prompt already answers some, acknowledge and move on — thorough, not tedious (P3). Infer the obvious ("migrate all admin pages to v2 sidebar" is clearly BUILD/autonomous/FE-only); present inferences, ask only the genuine forks.

### 1.4 — Vague-symptom gate (investigate-verb detection)
When the trigger mixes a vague symptom verb ("shows nothing", "broken", "looks weird") with imperative fixes, split planning into **Part A — investigation** (reproduce OR ask for evidence in one short question with a hypothesis; diagnose from observation, not code — a symptom maps to ≥4 internal states) and **Part B — fix planning** (only after A signs off). A precise code-visible symptom (`TypeError … at line 42`) reduces A to git-log + grep. Screenshot + vague prompt = evidence, not diagnosis. (#44)

### 1.4.1 — Ambiguous-direction gate
When the trigger names a migration by directional adjective (`horizontal/vertical`, `above/below`, `modal/page`) without stating the keeper, fire ONE `which side is the keeper?` `AskUserQuestion` BEFORE §1.2 scope locks — the filename can lie. If Q1's answer inverts a core assumption, the remaining batched questions are stale → re-batch. (#57)

---

## Step 2 — Design the campaign plan

Always the first artefact: `<campaign_folder_root>/{audit|build}-campaigns/<date>_<topic>/00-campaign-plan.md`. Templates in references/templates.md. Show the plan + get explicit approval before dispatching subagents or running a migration.

### Scope decision tree
Inputs: files touched, migrations, mass-rename sites, new public surfaces, forced-gate count.

```
files ≤2 AND lines ≤10 AND no new files AND no migrations            → NOT a campaign — EXIT at G0 (direct edit / one-file fix)
else extension of recent predecessor in a surface it HARD-excluded   → bug-fix
else files ≤5 AND migrations ≤1 AND no >15-site rename               → small (express)
else files 6–20 AND migrations ≤1 AND no >15-site rename AND ≤1 gate → medium
else                                                                  → full
```
If two tiers match, pick the SMALLER (declared trims are explicit). If work expands past the tier mid-flight, escalate + log the breach. **Declaration gate:** if `phases_remaining` skips W1/W2/per-phase files/risk-sweep, the frontmatter MUST carry `scope:` + every required field for that tier — silent trims are forbidden (#54).

| Tier | Trims | Keeps mandatory |
|---|---|---|
| ~~**micro**~~ → **EXIT at G0** | retired v3.7.0 — ≤2-file/≤10-line work is not a campaign; exits at G0 to a direct edit (#101) | tsc+lint + §5.3 vault-log (P8) STILL apply to ANY edit (#50) |
| **small / express** (≤5 files, ≤1 migration) | skip W1/W2/per-phase files/risk-sweep; investigation + phases + execution log as plan sections | §1.4 · G3 · §Step 3 PDAAV + stale-override sweep · §5.3 + §5.4 (#45) |
| **medium** (6–20 files) | skip W1/W2/per-phase files; inventory + phase list as plan sections | small's set PLUS a standalone `99-risk-sweep.md` (#59) |
| **bug-fix** (shipped bug in predecessor-excluded surface) | trims like small | + `predecessor`, `trigger`, `trigger_surface`, `predecessor_exclusion_reason`, `## Diagnosis (plain English)` |
| **full** | nothing | the whole pipeline |

### Frontmatter (always-required; full field catalog → references/templates.md → Frontmatter)
Always: `mode`, `scope`, `status` (`planning→in-progress→completed|superseded`), `approval_cadence`, `current_phase`, `phases_completed`, `phases_remaining`. The as-applicable fields (`standing_instructions`, `predecessor`, monorepo roots, `w0_*`, `preview_verification`, `verification_recipe`/`_class`, `generation_strategy`, `forced_gate`, `pN_result:`, `pivot_class`, `g0_override`, `branch_data_status`, `scope_truncated`, `goal_line`, `workflow_available`/`_emitted`) + their enums are catalogued in references/templates.md. Plans inventing undocumented fields = noise.

### The plan must include
- Mode · status · trigger/context · predecessor (extension) · standing_instructions · approval cadence · offline-resource map (W0 result).
- **Lessons from memory / past campaigns** (by ID/title) + which I'll follow/avoid (G4).
- **Wave structure** (W0 + 4 waves with task lists).
- **Per-task agent + model-assignment table** (mandatory — P2): task ID | wave | run-by (subagent type / ollama) | model | effort | output file. For a swarm phase add `swarm`: instances | partition | slices.
- **Phase list with risk tags:** green (reversible/FE/additive) — autonomous/hybrid run, strict gates; amber (schema-additive/new views/RLS/indexes) — same; red (destructive DDL / backfill / money / column drops) — ALWAYS gate.
- **Reference render structure** (REQUIRED for visual-conformity): outer wrapper → named lines → hover/transition → leaf primitives, from the reference's full render — name the EXACT leaf file (#26 #83). Empty block ⇒ plan can't be approved.
- **Verification recipe + verification_class per phase** (#20 #35 #53). **Generation strategy** for >5KB-content phases (spec, not content — #34; i18n adds intentionally-EN + cognate lists, references/fe-i18n-playbook.md).
- **Consolidation plan** (primitives, extractions, N=3 alarm) · **Cleanup plan — CANDIDATE deletions only** (grep-proof authorises the rm, #14) · **Forced single-question gates** (mass-rename >15 sites / namespace move / public rename — fire `AskUserQuestion` even under autonomous; flip `pending→satisfied` after the matching Q, cite `Q "<header>" → "<answer>"`, #15) · **Success criteria.**

### Emit the `/goal` line (at plan approval) + the Workflow script (per-wave) — EMIT, never invoke
A skill is a prompt; it can't set `/goal` or invoke the Workflow tool. So **emit ready-to-paste artifacts** the user opts into.

**`/goal` line** — Claude Code's built-in `/goal` (v2.1.139+) is a session Stop hook re-firing Claude until the condition holds (harder than prose persistence; survives context pressure, #13/#74). At plan approval emit ONE line from Q9:
```
/goal <verifiable end state from Q9> — every plan phase reads status: completed, 99-risk-sweep.md is written, tsc + lint clean[, <interaction outcome observed>]. Stop after <N> turns if not met.
```
The evaluator judges only the TRANSCRIPT (#89): phrase every clause as something Claude's output demonstrates, ≤4000 chars, always a turn bound. Record `goal_line:`; OPTIONAL; skip for scope < medium.

**Workflow script** — eligible = read-only parallel-barrier waves (W1/W2/W3-audit) + the `>20-file source-walk` (`pipeline`) + an approved NON-DB swarm write sweep (`isolation:'worktree'`). Emit **per-wave just-in-time with REAL paths** (it consumes prior-wave output; placeholders fail silently). INELIGIBLE: the interrogation, any `AskUserQuestion` gate, W3 DB/red writes, W4 synthesis. Each agent `schema` carries completeness predicates (a truncated-but-succeeded agent returns a thin-valid result); the main-agent spot-check (§Self-verification) STAYS. Record `workflow_emitted:`; OPTIONAL; skip for scope < medium. Detail: references/wave-playbook.md → Deterministic orchestration. (#93)

---

## Step 3 — Execute the four waves

Full subagent prompt templates: references/wave-playbook.md.

| Wave | AUDIT | BUILD |
|---|---|---|
| **W0** | Ollama prescan (main agent, Bash) | same, for the feature area |
| **W1** | parallel read-only: reconcile each doc vs code/DB (reads W0 first) | parallel read-only: inventory surfaces, one subagent/surface (findings only) |
| **W2** | parallel: dead code, API-route map, RLS parity, hierarchy | parallel: one subagent/phase — SQL/type/code drafts, risks, rollback (plans only) |
| **W3** | parallel: god-objects, realtime map, mutation layer | **sequential per phase, parallel within a phase** — execute under the self-verification loop |
| **W4** | sequential: synthesis → staged rewrites → promote → vault-log → cleanup | sequential: risk sweep → vault-log → memory → dead-code cleanup → `status: completed` |

Rules: wait for hard dependencies before the next wave (W4 waits for everything; W3 phases are sequential because P2 may depend on P1). Inside a wave, dispatch in parallel (one message, multiple Agent calls — for disjoint WRITES this IS the swarm, below). Respect the cadence (autonomous: stop only at red; hybrid: at red; strict: at everything). A blocked subagent → fall back to a tractable proxy (migration files, git history, AST) + emit `<!-- CHECKPOINT: CHK-<id> -->` (references/checkpoint-pattern.md).

### W3 execution loop (build) — per phase, in order
Full procedure (the Pre-W3 checklist + the 7 numbered steps + mid-execution scope-discovery thresholds) → **references/wave-playbook.md → §W3 execution loop full detail**. The recipe:

1. **Cadence check** — gate if the risk tag requires it; else proceed.
2. **Execute writes.** Serial DB phases → **PDAAV** (probe→draft→approve→apply→verify; rename+shrink → **RIBS** / **PDAAV-RIBS**). **Parallel writes across disjoint slices → SWARM (below), the default path — not serial.**
3. **Stale-override sweep** when a shared primitive's default changed (#23); single-instance fix → sibling-scan the directory (#77).
4. **Self-verification loop** (§Self-verification).
5. **Update campaign tracking** (`phases_completed`, `current_phase`, `phases_remaining`, `pN_result:`).
6. **Append "what actually ran"** to the phase file (deviations, decisions, fixed overrides with file:line).
7. **Continue.** Don't stop between green phases; the plan was approved.

Pre-W3 checklist (G1 reference + N=3 alarm · re-Read reference · G2 project_id · G3 schema re-probe · G6 DB-object conformity · themable-token audit · forced_gate · risk-tag-vs-cadence) and the mid-execution scope-discovery thresholds (≤5 silent · 6–50 log+append · >50/new-surface gate; never silently truncate → `scope_truncated:` #74; heartbeat >2min #75) are in the playbook.

### The W3 swarm — the sanctioned parallel-write primitive (default, not an exception)
When a BUILD phase writes across **disjoint slices** and the worthiness gate clears, the parallel-write path IS a **swarm via [[decompose-and-swarm]]** — the DEFAULT, not a context-exhaustion exception. The older "fan-out sweep" (one subagent per disjoint file) IS this same shared-tree swarm; the swarm is its formally-named, worthiness-gated, per-slice-critic'd version (§Subagent dispatch). Worthiness (reuse [[decompose-and-swarm]] MOVE 0): swarm ONLY if slices are **big** (≳1.5k tok each) + **disjoint** (pairwise-empty file-sets — THE invariant) + **loosely coupled** + **cheaper-net**; else run serial. **NEVER swarm DB/red writes or W4 synthesis.** Workers are Claude subagents that run as the member's Claude model (Sonnet), spawned via the Task tool (§Model assignment). **CONFORMITY-CLOSE-ONCE:** the orchestrator (campaign driver) runs conformity/verify/integration EXACTLY ONCE after all workers finish — workers never run it (intermediate parallel states fail). Per-slice critic before integration (`verdict.run_cold(slice_diff)`) keeps the critic invariant intact past the 60KB aggregate threshold. Full method → **references/wave-playbook.md → §The W3 swarm**; canonical craft → [[decompose-and-swarm]] · [[core-swarm]].

---

## Step 4 — Synthesise (audit) / Verify (build)

Write the final artefact yourself — synthesis benefits from one mind reading all the evidence; don't delegate.

**AUDIT `99-synthesis.md`:** TL;DR (drift, real bugs, security, latent gaps) · critical findings · real bugs · doc ghosts (referenced, don't exist) · doc orphans (in doc, not reality) · undocumented reality · patterns to document · per-doc rewrite checklist · code-cleanup checklist (separate PR) · open questions · re-audit cadence. **CRITICAL bugs get a build-vs-remove decision-tree with effort/risk tiers, not just a flag.** A "god-object" label needs LOC+exports, not edge-count. A `claude_hits:0` doc whose basename appears in CLAUDE.md / a wikilink is NOT archivable.

**BUILD `99-risk-sweep.md`:** TL;DR (shipped + watch items) · per-phase verification (ran-as-planned vs deviations, decisions, evidence) · **surface-coverage matrix — every "✓" needs a concrete observation (screenshot/polled DOM/network call), not an intent** · conformity & consolidation audit · risk-area sweep · post-deploy probes · memory updates · open items.

**W4-discovered phases:** a verification defect the plan didn't anticipate → don't silently inline-fix into a prior phase; allocate a new phase ID (`discovered_during: w4`), run the full self-verification loop, list it under a distinct vault-log header, note "+N W4-discovered phases" in the TL;DR. Closes only after every discovered phase passes.

---

## Step 5 — Cleanup & close (mandatory, automatic — G5)

- **5.1 Delete dead code (grep-first).** Per plan candidate: `grep -rn "<Name>\|from.*<file>" apps/web/ --include=*.ts* | grep -v "<file>:"` → confirm zero live consumers (most "surely dead" are still load-bearing — chrome migrated, content stayed). Delete only confirmed orphans; `tsc` after; record the grep proof + kept/deferred list. **Delete-time re-grep, not plan-time** — a concurrent actor may have wired a new consumer since plan-time (#97). DB drops add `RESTRICT`; defer irreversible *data* loss (a backup table) to an explicit go, never under autonomous.
- **5.2 Final verification.** `npm run check-types --force` (first run bypasses stale Turbo cache — #18) + `npm run lint`. **Provenance before blame:** a surfaced error → `git diff <start-sha>..HEAD | grep -F '<substr>'` — absent = pre-existing (`spawn_task` + continue), present = campaign-introduced (blocker); `git stash` needs `-u` (#56). **Scoped-lint:** project-wide `--max-warnings 0` failing on an untouched file → run eslint scoped to the touched list; `EXIT=0` proves the surface clean, the other warning rides as `CHK-<id>` (#61). Preview at phase exit only, and only if the project doesn't own preview (G4); `contrast-measured` runs ≥2 probe passes.
- **5.3 Vault-log** — write IMMEDIATELY (P6/P10), `<vault_log_root>/<date>_<topic>.md`, all phases + files + P13 self-audit (if MCP). Campaign-date = START date even across midnight/resume; same-session pivots edit the existing entry, never duplicate; incidental ≤3-line fixes → `## Incidental fixes`, larger → CHECKPOINT + defer. **Open with the mandatory Plain-English Summary** (project P8). **Project mechanics (lex_council, #87):** all `git` inside the `lex_council/` submodule; edit `docs/*` via atomic read-replace-write (one shell call), NOT Edit (the housekeeper daemon races it). Full mechanics: references/env-hazards.md.
- **5.4 Memory entries** — one file per surprise/trap/new convention; don't batch. **Resolve/delete a memory entry in the same campaign that fixes the bug it describes** (stale "bug present" entries cause future zero-change audits — #C7). Triggers: a lint rule firing under `--max-warnings 0`; a user correction naming an undocumented convention; a W1 surprise; a grep contradicting the user's mental model.
- **5.5 Update status** to `completed` — **gated on `99-risk-sweep.md`/`99-synthesis.md` existing on disk** (#11).
- **5.6 Promotion gate (audit)** — rewrites to `docs/staged/` first; promote after CHECKPOINTs resolved + user review; remove the empty `staged/`.
- **5.7 Spawn the post-campaign cleanup follow-up (separate session).** After 5.5, hand the loose ends to the `cleanup` skill's `followups` mode in a FRESH session via `mcp__ccd_session__spawn_task`: title `Run /cleanup for <campaign>`; a **stand-alone** prompt (the worktree has none of this context) that (a) names the plan path, (b) says run `/cleanup followups` first, (c) lists the mode sweeps for what THIS campaign touched (`lint` always · `postgres` if DB · `consolidate-code` if new components · `docs` if docs · `language` if i18n), (d) **inlines the `99-risk-sweep.md` ## Open items + touched-surface list**. If `spawn_task` is unavailable (Cowork/headless), SKIP — the committed ## Open items ARE the durable queue. Spawn ONCE per close (a reopened→reclosed pivot edits the existing note, #90). **Scope gate:** spawn ONLY for scope ≥ medium — over-spawning small campaigns is the §5.7 half of the over-invocation multiplier (#101).
- **5.8 Post-closure tweak detection** — within ~7 days, classify a same-surface tweak: "fix X too"/"while you're at it" → re-read the predecessor's re-anchor; "make X match Y" → EXTENSION sibling-sweep; 1–3 line cosmetic → inline + append to the predecessor's risk-sweep §10; 4+ files / new surface → re-open as EXTENSION (`predecessor:`, skip W1). Every tweak is logged against the campaign (an unlinked one-shot fix is a silent write); list intermediate stub-fix vault-logs in a re-opened EXTENSION's Trigger/Context (#55).

---

## Step 6 — Reflection-pass (post-campaign skill upgrade)

Triggers on "reflect on this session and propose skill upgrades", "upgrade as recommended", "review and note lessons". NOT on "summarize what we did" (that's a vault-log). **Offer proactively at close, and APPLY — don't just report.**

1. **6.1 Inputs** — the closed campaign's full artifact set + the **LIVE SKILL.md read from disk** (NOT the session-start version — it may have changed) + the session's invented disciplines/stops/re-plans.
2. **6.2 Walk** — per phase / W4-discovered / post-closure tweak: did the agent stop/re-ask (→ new gate)? invent a procedure (→ named pattern)? re-derive a discipline (→ checklist)? use a field informally (→ enum)? hit a project shape §0.0.5 didn't probe (→ extend it)?
3. **6.3 Classify** — MINOR (new section/discipline/failure-mode CLASS) vs PATCH (clarification/enum/sub-pattern) vs MAJOR (wave-structure/artifact-layout). Needs a new heading to find it? → MINOR.
4. **6.4 Release-split** — ship MINOR then PATCH as two sequential entries; don't bury paradigm changes among clarifications.
5. **6.5 Cross-ref completeness** — grep the draft: every `references/<file>`, `#N`, `§X`, `[[link]]` resolves.
6. **6.6 Apply + verify** + **6.7 report** the version path, new sections/patterns, line delta, deferred findings.

---

## Self-verification loop (after every build phase / audit wave — automatic, never ask)

**Build:** `tsc --noEmit` + `npm run lint`; both pass → log "clean", continue. Either fails → read errors, fix (≤3 attempts, re-run each); fixed → log "fixed (N attempts)"; 3 fails → CHECKPOINT + continue. **Phase touching user-facing UI/theme/auth/hydration/realtime/locale: verification is REQUIRED** — honor G4 (project owns preview → hand off the recipe, don't touch the dev server); else screenshot + polled DOM reads at multiple timestamps (100ms/500ms/1s/3s — single snapshots miss hydration), run the Q9 recipe, log actual values, `location.reload()` between a manual poke and the next read (#21). Never stop to ask about results — self-heal or mark-and-move.

**Audit:** verify all findings files exist; spot-check one for completeness; relaunch a missing/truncated task; continue.

---

## Autonomous decision ladder

| Priority | Condition | Action |
|---|---|---|
| 1 | Plan says | Follow it exactly |
| 2 | Memory / docs say | Follow the convention, log it (G4/P8) |
| 3 | Clear recommended option | Take it, log it |
| 4 | Reversible choice | Pick the safer/simpler, log it |
| 5 | **Irreversible + no guidance + high-risk** | **STOP and ask** — the only case |

Irreversible+high-risk = drop a column/table, delete data (not code — code is in git), change RLS on money-adjacent tables, any `apply_migration` altering production data shape. **Show-SQL granularity (#97):** even under `autonomous`, split DB work by reversibility — a reversible `CREATE OR REPLACE` / additive DDL proceeds with the SQL shown (P3); an irreversible `DROP` or money-/auth-adjacent bulk refactor ALWAYS gets full SQL + an explicit go (the stop-case), carries `RESTRICT` (never `CASCADE` on faith), and runs a delete-time LIVE re-grep (#33). NOT irreversible (never stop): component structure, naming, CSS, extract-now-or-later (always now), fixing a lint error the phase introduced. **Content-exclusion** ("do not include X") is a plan-gate, pre-filter before writing. Log every autonomous decision (`> Decision: … (ladder level N)`).

---

## Subagent dispatch

- Default subagent type `general-purpose`. Hand each a self-contained brief: files to read first (incl. `00-w0-offline-prescan.md`), exact output path, frontmatter, sections, **explicit read-only vs may-write**. Audit + build-W1 read-only; build-W2 writes only its phase-plan file; **build-W3 writes are by the main agent OR a swarm worker** (below), not an unapproved subagent.
- Run a wave's tasks in parallel (one message, multiple Agent calls). Track agent IDs for relaunch. Verify a dispatched file exists before claiming done. After any wait >30s, re-Read the next target before Editing (#41).
- **Source-walk template** (>20 files → JSON-on-disk, never inline) + **long batches** (N>20 → `fs.appendFileSync` sidecar progress, checkpoint every K, confirm strategy before any >5min batch): full templates in references/wave-playbook.md → §Subagent dispatch. (#39 #40 #42)

- **The SWARM — the one sanctioned parallel-write primitive (DEFAULT, not an exception).** When a wave has ≥ `min_instances` DISJOINT write-slices (each ≳1.5k output tokens, loosely coupled), the parallel-write step IS a `swarm` delegated to [[decompose-and-swarm]], followed by an inline integration step on the main thread. **One pattern, not two:** the campaign's older **"fan-out sweep"** (one `general-purpose` subagent per disjoint sibling file — its commonest shape is the ≥5-sibling mechanical behavior-preserving refactor) IS this shared-tree swarm; the swarm is its formally-named, schema-governed, worthiness-gated, per-slice-critic'd version. "build-W3 writes by the main agent" still holds for SERIAL/coupled phases and for the orchestrator's own integration. **Worthiness gate** (reuse [[decompose-and-swarm]] MOVE 0 — else run serial): slices **big** + **disjoint** (pairwise-empty file-sets = THE invariant; overlap → re-partition or escalate to `isolation:worktree`) + **loosely coupled** + **cheaper-net**. **Workers are Claude subagents** that run as the member's Claude model (Sonnet, tool-capable), spawned via the Task tool (§Model assignment). **CONFORMITY-CLOSE-ONCE:** the orchestrator (campaign driver) runs conformity + the verification gate (full `tsc` + scoped `lint` + a structural-grep matrix asserting the target shape on every file, deep-review the 1–2 riskiest line-by-line) + integration EXACTLY ONCE after all workers finish — **workers never run conformity** (intermediate parallel states fail), never write a shared doc (#91), never commit. Per-slice critic before integrating (`verdict.run_cold(slice_diff)`) keeps the critic invariant past the 60KB aggregate threshold. **NEVER swarm DB/red writes or W4 synthesis.** Full procedure: references/wave-playbook.md → §The W3 swarm; canonical craft: [[decompose-and-swarm]] · [[core-swarm]] · model doctrine [[weapon-utility]].

- **Workflow-orchestration** (named, optional executor) — on Claude Code CLI when the user opted into orchestration AND a wave is a genuine scripted batch (the `>20-file source-walk`, #42) or an approved ≥5-file NON-DB swarm, the EMITTED Workflow script (§Step 2) replaces the hand-rolled `fs.appendFileSync` batch loop with `pipeline()` + `schema`-checked auto-retried returns + `isolation:'worktree'` + `log()/phase()` heartbeat. The script writes NO shared artefact (the MAIN agent consolidates after the barrier, #91); NOT for the everyday in-message-barriered wave, NEVER for DB/red writes, gates, or W4 synthesis; absent the tool the prose dispatch runs unchanged. Detail: references/wave-playbook.md → Deterministic orchestration. (#93, #94)

**Named patterns** (declare in plan frontmatter; full procedures in the playbooks): `PDAAV` / `PDAAV-RIBS` (DB — references/db-playbook.md) · `RLS-IMPERSONATE` (#104, references/db-playbook.md) · `RIBS` / `RIBS-N` (FE — references/fe-i18n-playbook.md) · source-walk · scoped-lint (§5.2) · **swarm** / fan-out sweep ([[decompose-and-swarm]]) · workflow-orchestration (§Step 2 emit) · checkpoint markers.

---

## Environment hazards

Full per-hazard index → **references/env-hazards.md**: PostToolUse hooks (#28/#41) · JSX-pivot single-`Write` (#51) · codemod footguns (#73) · runtime-cache-not-HMR — **restart the dev server first when the runtime contradicts the file on disk** (#48) · SSR/hydration module-state (#20) · auto-commit pre-commit hooks (#63) · docs-daemon races Edit + submodule/no-remote git (#87) · concurrent-actor `git worktree add` (never `checkout -b`) + worktree-`node_modules` symlink (#95) · `gh` absent → push + `pull/new` URL (#99).

---

## Trigger-phrase precedence (the single resolution table — earlier wins; default LATER if unclear)

| Order | Trigger | Section |
|---|---|---|
| 1 | Resume `in-progress` campaign on disk | §0.0 |
| 2 | Same-session pivot (predecessor closed this session, user names a deficit) | §0.0.1 |
| 2b | Audit lens-extension (closing/closed audit + user adds a read-only new lens) | §0.0.6 |
| 3 | Pivot-chain (≥2 prior pivots, same predecessor) | §0.0.3 |
| 4 | Post-closure tweak (predecessor closed ≤7 days ago) | §5.8 |
| 5 | `scope: bug-fix` (shipped bug in a predecessor-excluded surface) | §Step 2 |
| 6 | Reflection-pass on a closed campaign | §Step 6 |
| 6b | **G0 worthiness gate** — a NEW request (not a resume/pivot/extension/reflection above) that fails the bar: ≤small single-surface · a `/cleanup` mode (colors/lint/i18n/postgres) · one-file bug | **EXIT — decline + route, create no folder (§Pre-flight G0, #101)** |
| 7 | Vague-symptom verb (Part A reproduction) | §1.4 |
| 8 | Ambiguous-direction migration verb (keeper question) | §1.4.1 |
| 9 | Standard planning interrogation | §Step 1 |

Order 2 beats 7; order 5 beats 4 when both "predecessor named" + "surface exclusion named" fire. **Row 6b gates rows 7–9** (a NEW campaign fires only AFTER the request clears G0); rows 1–6 attach to an existing campaign and bypass G0 — never re-triage in-flight work.

---

## Model assignment

| Tier | Who | When | Cost |
|---|---|---|---|
| **W0 — Ollama** | main agent via Bash | file listing, grep counts, surface map, doc summarisation | free (local) |
| **W1–W3 — sonnet** | `general-purpose` subagent | mechanical scanning, route/hook/type mapping, standard pattern work | mid |
| **W1–W3 — opus** | `general-purpose` subagent | security, RLS, synthesis, money-adjacent, schema/trigger reasoning | highest |
| **W3 swarm worker — sonnet** | Claude subagent (one per disjoint slice, spawned via the Task tool) | parallel disjoint WRITES; runs as the member's Claude model | N×mid |
| **W4 + swarm orchestrate/integrate — you** | main agent (Opus) | synthesis / risk sweep / per-slice critic + CONFORMITY-CLOSE-ONCE — never delegated | conversation turn |

**Swarm workers are Claude subagents that run as the member's Claude model (Sonnet, tool-capable)** — spawned via the Task tool; every worker is a Claude model, so each holds Edit/Write/Bash directly. This reconciles with the table: opus orchestrates + reviews red/security, sonnet subagents run disjoint mechanical/standard slices, Ollama prescans at W0. The saving is N Sonnet under one Opus. See [[decompose-and-swarm]] · [[weapon-utility]].

Effort via prompt language (no effort param): **deep** — "Reason step by step, flag uncertainty." **standard** — no phrase. **fast** — "Mechanical. List/count/map only." opus+deep for security/RLS/synthesis/money; sonnet+fast for mechanical scanning; never deep on a mechanical task; avoid haiku when W0 ran.

---

## Conformity & consolidation (the always-on disciplines — full extraction procedure in references/fe-i18n-playbook.md)

**Conformity:** read the pattern docs + the reference's FULL render before writing (G1/P4). Match visual hierarchy, token usage (`C.*`, `<MIcon>` — no hardcoded hex / raw Material Symbols / Tailwind), naming, layout direction (LTR container for Arabic DB content in an English panel). Resolve toward the majority pattern. At W4 run a conformity check + a stale doc-comment sweep for every design fact the campaign changed.

**Consolidation:** (1) inventory shared primitives; (2) extract before composing at 3+ consumers; (3) extend a near-duplicate, don't fork; (4) **grep before changing a shared default** — decide the new value across ALL sites in one pass (feeds the §W3 stale-override sweep); (5) **N=3+ union-prop audit** — a ≥3-value union prop with N-1 legacy values → drop the prop + dead branches + helpers, same phase (#58). Extraction precedes consumption. At cleanup: grep zero live imports, delete, confirm `tsc`.

---

## Deploy & sync · skill self-health (#84)

Full copy-table + sync + self-health checks → **references/skill-maintenance.md**. Canonical copy is project-local — propagate FROM it; after ANY edit to SKILL.md or references/, sync every copy + `diff -rq`. Self-health (every reflection pass): referenced-file existence · every #N has a catalog row · every §X / `[[link]]` resolves · core-size watch · the **G0 over-invocation sprawl metric** (`folders / thin / plans-missing-scope` — a rising thin% means G0 isn't firing, #101/#102).

---

## Common failure modes (#1–#107)

The full catalog — the lookup table (symptom → status → cure pointer) AND the prose/post-mortem for every mode AND the §Anti-pattern quick-lookup (code/procedure smell → named cure) — lives in **references/failure-modes.md**. Look up `#N` there. P1–P7 are the promoted ones (above). Adding a mode: append to references/failure-modes.md (table row + prose) with the next sequential `#N`; the numbered `(#N)` cites scattered through this body all resolve there.

---

## Output conventions

**AUDIT:** `00-campaign-plan.md` · `00-w0-offline-prescan.md` (if W0) · `NN-<task>.md` (8–12) · `99-synthesis.md` · `CHECKPOINTS.md` (if blockers) · updated docs · one vault-log · `audit-campaigns/README.md` (first run). **BUILD:** `00-campaign-plan.md` · `00-w0-offline-prescan.md` · `0N-phase-N-<topic>.md` · `99-risk-sweep.md` · `CHECKPOINTS.md` (if pending) · shipped code · deleted dead code · one vault-log · memory entries · `build-campaigns/README.md` (first run). Scope tiers trim per §Step 2; `micro` retired (#101).

## Reference files
- references/failure-modes.md — full catalog #1–#107 (table + prose + §Anti-pattern lookup) **[§Common failure modes table moved here]**
- references/wave-playbook.md — subagent prompt templates · **§W3 execution loop full detail** · **§The W3 swarm** (worthiness, MOVES, per-slice critic, CONFORMITY-CLOSE-ONCE) · swarm-worker model rule · source-walk/long-batch · Deterministic orchestration **[W3 detail + swarm playbook moved here]**
- references/templates.md — plan/findings/phase/synthesis/risk-sweep/checkpoint/vault-log templates · **§Frontmatter master field reference [moved here]**
- references/version-history.md — full release history **[§Version history → pointer]**
- references/REFLECTION-2026-06-04.md — the v3.8.0/v3.8.1 lessons + route
- references/db-playbook.md — G6 conformity + PDAAV/PDAAV-RIBS + DB lessons + schema facts
- references/fe-i18n-playbook.md — conformity extraction · RIBS/RIBS-N · env hazards · FE/i18n/codemod lessons
- references/checkpoint-pattern.md — CHECKPOINT markers, both modes
- references/env-hazards.md — runtime + tooling hazard index (#20/#28/#41/#48/#51/#63/#73/#87/#95/#99)
- references/skill-maintenance.md — deploy/sync + self-health checks (#84) + the G0 sprawl metric

External craft: **[[decompose-and-swarm]]** (the swarm method — five MOVES, worthiness gate, per-slice critic) · **[[core-swarm]]** (guild swarm memory core) · **[[weapon-utility]]** (each member runs as its Claude model).

## Version history
Full release history (newest first) → **references/version-history.md**. Current: **v3.9.0 — 2026-06-28** (MINOR) — swarm-era restructure: SKILL.md trimmed under the Cowork installer ceiling (failure-mode catalog · W3 execution-loop detail · swarm playbook · frontmatter catalog relocated to references); the W3 BUILD swarm is now the SANCTIONED, worthiness-gated, per-slice-critic'd DEFAULT for parallel writes via [[decompose-and-swarm]] (fan-out sweep = the same shared-tree pattern); added CONFORMITY-CLOSE-ONCE; swarm workers are Claude subagents that run as the member's Claude model (Sonnet), spawned via the Task tool. On each upgrade, bump `version:` + prepend to references/version-history.md.
