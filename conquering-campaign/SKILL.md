---
name: conquering-campaign
version: 3.5.0
description: "Multi-wave campaign skill for work too big for one pass. Three modes — AUDIT (reconcile docs with code/DB), BUILD (multi-phase features/refactors/migrations touching >=3 surfaces), EXTENSION (extends a recent predecessor — skips W1, reuses its prescan). Triggers on 'audit my app', 'build this feature', 'ship this refactor', 'phase this migration', 'proceed in application', or 'extend [campaign] to X' / 'roll out [pattern] to [surface]' / 'apply [v1.X] to [Z]'. Contract: in planning, ask every question upfront (scope, cadence, reference patterns, success criteria, memory); after the plan is approved, execute autonomously — except a phase that mass-renames imports across >15 sites, moves a namespace, or renames a public component, which earns a single-question gate. Waves use the cheapest tier that works — Ollama for free local prescans (ANSI/thinking-trace stripped), sonnet for mechanical scans, opus for security/RLS/synthesis. Execution enforces six always-on Pre-flight Gates (reuse-before-build, verify-project-id, DB-wave re-probe, defer-to-project-memory, close-checklist, db-object-conformity) plus conformity (match existing UX/docs), consolidation (extract shared primitives, never copy-paste), self-verification (tsc+lint+preview at phase exit), and an autonomous decision ladder (plan -> convention -> recommended -> safer-reversible -> stop only if irreversible+high-risk). Plans list candidate deletions, never committed deletions — grep-proof before any rm. On finish the skill self-cleans: deletes confirmed-dead code, flips status to completed, writes the vault-log immediately, saves memory entries, and spawns a self-contained follow-up `/cleanup` session (via spawn_task) — unprompted. At plan approval it emits a ready-to-paste `/goal` line built from the plan's success criteria, so one approval can run the whole campaign unattended under Claude Code's built-in goal-persistence Stop hook. Full detail lives in references/ (failure-modes, version-history, db-playbook, fe-i18n-playbook, templates, wave-playbook, checkpoint-pattern)."
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

The mine of 136 campaigns found the two most-frequent failures were ALREADY codified but buried — they fire as user corrections because the agent doesn't reach the rule at the decision moment. These six gates are short on purpose. Run the relevant one *before the action*, every time, regardless of scope or cadence.

- **G1 — Reuse before build (before writing ANY component / style / button).** Grep the current + sibling surfaces for an existing primitive first. If one exists, use it — hand-rolling a primitive that exists is a campaign failure (P9). Name the EXACT reference leaf file (design language lives 2 hops down: `Row → ActionBar → GhostIconButton`, not the row) and extract every token before writing. A `<button>` inside `<SidebarCard>` MUST use the canonical nav-row primitive. Full procedure: references/fe-i18n-playbook.md → Conformity extraction. (#4 #22 #26 #27 #49 #83)
- **G2 — Verify project_id (before ANY Supabase MCP call).** Confirm the project_id from `.env` (lex_council prod = `bqgrpnsvplvicnmzxwkm`). An MCP `-32600`/permission error means WRONG project_id, NOT a harness block — never report "MCP is down" without checking this first. On a feature branch, writes target the branch project, never prod, until merge. (#B2)
- **G3 — DB-wave re-probe (at the START of every DB wave, not just plan time).** Production schema can flip mid-session from another actor. Re-probe live schema + check the `supabase_migrations` ledger; STOP + reconcile if foreign migrations interleaved. Before any rename/drop: grep ALL function bodies (text, not OID-bound) AND FE callsites (`.from()`/`.select()` in app/api, lib/mutations, hooks). Before diagnosing a slow query: check stale stats (run `ANALYZE`). Full procedures: references/db-playbook.md. (#32 #33 #67 #68 #69)
- **G4 — Defer to project memory & standing instructions (at plan time + before any verification action).** Read project memory + the session's standing instructions. **The project's instruction wins over the skill's default.** Sacred `> [!atta]` blocks are supreme — never edit them, and they outrank CLAUDE.md, the docs, AND the user's request; on conflict surface it, don't silently pick a side. Read the relevant doc BEFORE introspecting the DB (docs-before-SQL, P11/P13); `docs/archived/` is off-limits unless the prompt grants it. Specifically for lex_council: **preview/visual verification is the USER's job — never run preview tools, never start/kill the dev server** (`[[feedback_no-dev-server-hijack]]`); **lead every response with a plain-English status block** (`[[feedback_simple-english-summary]]`). When a project owns preview, the skill hands off a verification recipe instead of running it. (P8, #17)
- **G5 — Close checklist (before declaring done).** Vault-log written (no "small tweak" / "same conversation" exemption — P10) + sibling-scan for the fix + nav-audit if a route changed + `99-risk-sweep.md` EXISTS on disk + memory entries for surprises + commit if the user granted standing perms + spawn the post-campaign cleanup follow-up (§5.7). Don't stall waiting to be told to finish. (#7 #11 #13 #77 #81 #90)
- **G6 — DB-object conformity (before creating/altering ANY table / view / trigger / RPC).** The DB twin of G1. Conform to the app's binding v2 conventions — don't invent, don't restate them: naming (`{portal}_{section}_{entity}` views, `{owner}_on_{watched}_{timing}_{ops}` trigger fns ≤63 chars, `{verb}_{object}` RPCs), security boilerplate (`SECURITY DEFINER`+`search_path=''`+REVOKE/GRANT+`auth.uid()` guard; `security_invoker=true` views — `CREATE OR REPLACE` drops it), ONE `FOR ALL` RLS policy composed from the named bundle catalog (W6 — never inline `EXISTS`; propose a new bundle if none fits), a `view-registry.ts` key (W3), `callRpc` writes through `lib/mutations/` (C4 — never `.from().insert()`), soft-delete-only (C31). The app docs are the source of truth — read the leaf doc FIRST (V2-CONVENTIONS / RLS-BUNDLES / DB-NAMING; docs-before-SQL P11/P13), then probe, then draft. Full checklist: references/db-playbook.md → G6. (#88, W2–W6)

---

## Standing principles

Always-on. A violation is a campaign failure, not a "consider this." (P1–P7 are paradigm-level; P8–P10 added v3.0.0 from the 136-campaign mine where they were the top recurring corrections.)

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

The numbered failure modes (§Common failure modes table → references/failure-modes.md) are specific traps with cures; principles are the always-on rules.

---

## Two modes (+ extension)

| Mode | Goal | Subagents | Final artefact |
|---|---|---|---|
| **AUDIT** | Reconcile docs with code/DB reality | read-only — write findings files only | promoted source-of-truth docs + vault-log |
| **BUILD** | Ship a multi-phase feature/refactor that stays deployable at every step | may write code/migrations per phase under the cadence | shipped feature + vault-log + risk sweep + tests pass |
| **BUILD · Extension** | A build extending a predecessor that shipped ~≤30 days ago on the same surface | as BUILD, but W1 shrinks to a 1-task probe or is skipped; W0 may be skipped | shipped extension + vault-log linking the predecessor + risk sweep diffing the predecessor's |

If the user wants a quick one-file check or single bug fix, this skill is overkill — say so and offer a lighter pass. For genuinely small-but-real work, use the `scope` tiers (§Step 2) rather than refusing.

**Detect extension intent:** the user names/links a predecessor that completed recently, or describes the work as propagating recently-shipped primitives to new consumers ("extend v1.7.3 to members + clients", "roll out the portal-shell to clients"). Then: run as BUILD, set `predecessor:` frontmatter, skip W1, consider skipping W0 (§0.6).

**What "good" looks like at the end** — AUDIT: a `<root>/audit-campaigns/<date>_<topic>/` with numbered findings + `99-synthesis.md`, docs rewritten via `docs/staged/` then promoted, CHECKPOINTs registered, vault-log filed, `status: completed`. BUILD: a `build-campaigns/<date>_<topic>/` with `00-campaign-plan.md` + per-phase files + `99-risk-sweep.md`, each phase independently deployable, shared primitives extracted before composing, dead code deleted, one vault-log covering all phases, memory entries, `tsc + lint` clean, `status: completed`, feature ships.

---

## Step 0 — Resume, environment, prescan

Run before Step 1, every time. **Trigger precedence when several rules match one prompt: see §Trigger-phrase precedence.**

### 0.0 — Resume / pivot classification
Check `grep -rl "status: in-progress" <roots>/*-campaigns/*/00-campaign-plan.md`. The plan frontmatter (`status`, `current_phase`, `phases_completed`, `phases_remaining`, `pN_result:`) **IS the crash-recovery log** — keep it accurate after every phase, because compaction can occur mid-campaign and this is the only clean resume point. If resuming: read the plan, skip W0/W1/W2, jump to the next incomplete phase.

| Situation | Rule |
|---|---|
| `in-progress` campaign on disk | Resume from frontmatter; skip W0–W2. |
| **Same-session pivot** — predecessor closed THIS session + user names a deficit ("you missed", "still work to match UI", "doesn't match X") | §0.0.1: don't open a new campaign. Reopen the predecessor plan (`completed → in-progress`, push a `P*_pivot` phase with `discovered_during: same-session-pivot`), skip W0+W1, run W3+W4 on the new phase, **edit the existing vault-log in place** (never duplicate). |
| **Pivot-chain** — ≥2 prior pivots on the same predecessor + plan >6 phases + new pivot adds NEW surface | §0.0.3: batch close-out (flip status once, not per pivot); fire ONE spin-off `AskUserQuestion` (keep chaining / spin off new campaign / re-plan). Mark `pivot_class: depth|scope-expansion` — a pure depth-pivot chain (same surface, tighter) does NOT need the gate. |
| **Reset TodoWrite** | §0.0.2: a fresh campaign resets the session todo list before the first Bash/Agent call (it's session-scoped, not campaign-scoped). Resume/pivot keep the list. |
| **Status-coherence** | `status: planning` + empty `phases_completed` + no risk-sweep = never-started → skip for lesson-mining, flag as an open item. An empty campaign folder = a planning failure (write a skeleton plan when you create the folder). |

### 0.0.4 — Preview reachability + ownership (probe once/session)
**First check G4 / project memory:** if the project says preview verification is the USER's job, set `preview_verification: user-owned` and never run preview tools — hand off a recipe instead. Otherwise probe whether the dev server renders past the login wall (`curl -s -m5 <gated-route> | grep -qE 'Loading|/login|Sign in'`). If auth-walled with no test session, set `preview_verification: blocked-by-auth` + a reason; stop adding preview steps to phase checklists (code-only verification is enough — say so explicitly). (#38)

### 0.0.5 — Monorepo artifact roots (probe once/session, before writing the plan)
`find . -maxdepth 4 -type d -name docs` + `find . -maxdepth 5 -type d -name vault-logs`. Record in plan frontmatter: `campaign_folder_root`, `vault_log_root` (co-locate by default — campaign-plan under the same parent as vault-logs), `claude_md_path` (often workspace root even when planet-hub docs are nested), `wikilink_convention` (`bare-filename` when co-located, `relative-path` when roots differ). At §5.2 grep every `[[…]]` and assert it matches the declared convention. (#46)

### 0.1–0.6 — Environment + W0 prescan
- **Cowork:** skip 0.2–0.5, set `w0_enabled: no`, go to Step 1 (Ollama not reliably reachable). **Claude Code CLI:** continue.
- **Probe Ollama** (`ollama list`). If `OLLAMA_OK`, W0 is mandatory unless a skip-row below applies — the prescan is the shared grounding doc every W1+ subagent reads FIRST; substituting a Claude Explore agent spends the same tokens it saves.
- **Models:** auto-select per role from `ollama list` — `qwen2.5-coder:*` for code-pattern/grep tasks, `qwen3:8b|14b` for summarisation; avoid `deepseek-r1` (too slow). On Apple Silicon attempt regardless of the "available RAM" reading (unified memory reclaims aggressively).
- **Run the prescan** (main agent, Bash — not a subagent) → `00-w0-offline-prescan.md`. ALWAYS strip ANSI + thinking traces: `ollama run --hidethinking <m> "<prompt>" 2>&1 | sed -E 's/\x1b\[[0-9;?]*[a-zA-Z]//g' | grep -vE '^(Thinking|Okay|\.\.\.done thinking)'`. For structured/JSON W3 tasks prefer the REST API (`/api/generate`, `"stream":false,"think":false`) — the CLI corrupts JSON with spinner frames. (#16)
- **Validate the prescan (§0.5.1)** before W1 cites it: does it name real line counts / file names / entities, or echo back `<file>`/`<list names>` placeholders? Set `w0_useful: yes|no|partial` (+ `w0_note:` for partial/no). If `no`, tell W1 to read files cold. (#30)

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
In Claude Code CLI the deterministic **Workflow tool** (a JS script orchestrating subagents — `parallel`/`pipeline`/`schema`-checked returns/`log` heartbeat/`resume`) MAY be present (the slash-command pointer confirms CLI at Step 0); in Cowork/headless it is ABSENT. It has the SAME two limits as `/goal`: it runs ONLY when the user explicitly opts into orchestration (keyword/ultracode/explicit ask) and it CANNOT ask an interactive question mid-script. So the skill **EMITS** a ready-to-run script (like the `/goal` line), never invokes it — and the existing in-message parallel `Agent`-call dispatch is the portable DEFAULT that runs unchanged when the tool is absent or declined. The genuine win is NARROW: the in-message dispatch already barriers (the main loop blocks until every tool-result returns), so a deterministic barrier buys little; the real gain is for the `>20-file source-walk` batch (a true scripted loop) via `pipeline()` + `schema` + `resume`. Set `workflow_available: yes|no|unknown` + `workflow_emitted:` per the skip table. Full eligibility + primitive-mapping: references/wave-playbook.md → Deterministic orchestration. (#94)

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
Scan project memory (`docs/memory/MEMORY-INDEX.md`) for entries matching the scope; scan past `99-risk-sweep.md` / `99-synthesis.md` for recurring traps on the same surfaces; read the project's guidelines. Pre-loading prevents repeating past mistakes (G4 / P8).

### 1.2 — Ask ALL of these in one batch (don't scatter)
**Scope:** (1) what are we building/auditing? (2) which surfaces (schema/RLS/views/triggers/types/FE/admin/mutations/docs)? (3) known constraints? **For multi-page campaigns also ask: merge same-domain pages into one surface, or keep separate?** (#82) — **Authority:** (4) approval cadence (`strict` / `autonomous` / `hybrid`); (5) decision authority (default: pick the recommended option + log); (6) edge cases (default: handle if green/amber, CHECKPOINT if red). — **Pattern:** (7) reference file/page to mirror (name the EXACT leaf file); (8) consolidation targets (existing primitives vs new extraction). — **Verification:** (9) success criteria + the **browser verification recipe** — the smallest test proving the user-facing outcome ("set X, navigate Y, poll Z, expect W in N ms"); CRUD/editor/form/multi-step needs BOTH a render recipe AND an interaction recipe (click→type→save→reload→confirm persisted→revert→confirm restored); accessibility/contrast/dark-mode needs a WCAG ratio measurement; (10) verification method (`tsc+lint` only, or also preview — but honor G4 preview-ownership; content-only campaigns substitute JSON-validity + deep-flatten diff + placeholder-free). — **Past context (state, don't ask):** (11) relevant memory entries I'll follow; (12) past traps I'll avoid; (13) session standing instructions inherited from earlier campaigns — quote them VERBATIM into `standing_instructions:` and confirm they still apply (an inherited instruction that conflicts with this campaign's goal must be explicitly lifted + replaced, not silently carried). (#31)

If the user's prompt already answers some, acknowledge and move on — thorough, not tedious (P3). Infer the obvious ("migrate all admin pages to v2 sidebar" is clearly BUILD/autonomous/FE-only); present inferences, ask only the genuine forks.

### 1.4 — Vague-symptom gate (investigate-verb detection)
When the trigger mixes a vague symptom verb ("shows nothing", "broken", "doesn't work", "looks weird") with imperative fixes, split planning into **Part A — investigation** (reproduce the symptom OR ask for evidence in one short question with a hypothesis; diagnose from observation, not code — a symptom can map to ≥4 internal states) and **Part B — fix planning** (only after A is signed off). Override: a precise code-visible symptom (`TypeError … at line 42`, `MISSING_MESSAGE: …`) reduces A to git-log + grep. Screenshot + vague prompt = evidence, not diagnosis — confirm interpretation before fixing. (#44)

### 1.4.1 — Ambiguous-direction gate
When the trigger names a migration by directional adjective (`horizontal/vertical`, `above/below`, `inline/block`, `modal/page`, `cascade/stacked`) without clearly stating the keeper, fire ONE `which side is the keeper?` `AskUserQuestion` BEFORE §1.2 scope locks — the filename can lie (keeper file `FilesStackHorizontal` rendered `layout="vertical"`). If Q1's answer inverts a core assumption, the remaining batched questions are stale — re-batch on the corrected core. (#57)

---

## Step 2 — Design the campaign plan

Always the first artefact: `<campaign_folder_root>/{audit|build}-campaigns/<date>_<topic>/00-campaign-plan.md`. Templates in references/templates.md. Show the plan + get explicit approval before dispatching subagents or running a migration.

### Scope decision tree
Inputs: files touched, migrations, mass-rename sites, new public-API surfaces, forced-gate count.

```
files ≤2 AND lines ≤10 AND no new files AND no migrations            → micro
else extension of recent predecessor in a surface it HARD-excluded   → bug-fix
else files ≤5 AND migrations ≤1 AND no >15-site rename               → small (express)
else files 6–20 AND migrations ≤1 AND no >15-site rename AND ≤1 gate → medium
else                                                                  → full
```
If two tiers match, pick the SMALLER (declared trims are explicit). If work expands past the tier mid-flight, escalate + log the breach. **Declaration gate:** if `phases_remaining` skips W1/W2/per-phase files/risk-sweep, the frontmatter MUST carry `scope:` + every required field for that tier — silent trims are forbidden (#54).

| Tier | Trims | Keeps mandatory |
|---|---|---|
| **micro** (≤2 files/≤10 lines) | no plan file (conversation IS the plan), no per-phase log, no memory unless surprise | §1.4 gate · tsc+lint · preview/hand-off · §5.3 vault-log (P8 never waived) (#50) |
| **small / express** (≤5 files, ≤1 migration) | skip W1/W2/per-phase files/risk-sweep; investigation + phases + execution log live as plan sections | §1.4 · §1.5d schema-reality · §2a + §2a-RLS · §2.5 stale-override · §5.3 + §5.4 (#45) |
| **medium** (6–20 files) | skip W1/W2/per-phase files; inventory + phase list as plan sections | small's set PLUS a standalone `99-risk-sweep.md` (#59) |
| **bug-fix** (shipped bug in predecessor-excluded surface) | trims like small | + `predecessor`, `trigger`, `trigger_surface`, `predecessor_exclusion_reason`, `## Diagnosis (plain English)` |
| **full** | nothing | the whole pipeline |

### Frontmatter (master reference)
Always: `mode`, `scope`, `status` (`planning→in-progress→completed|superseded`), `approval_cadence`, `current_phase`, `phases_completed`, `phases_remaining`. As applicable: `standing_instructions` (verbatim, when ≥2 campaigns/session — #31), `predecessor`, `campaign_folder_root` + `vault_log_root` + `claude_md_path` + `wikilink_convention` (monorepo — §0.0.5), `w0_enabled` + `w0_useful` + `w0_note`, `preview_verification` (`yes|user-owned|blocked-by-auth|partial|n/a`) + reason, `verification_recipe`, `verification_class` (`render|interactive|contrast-measured|content-only|static|code-only`), `generation_strategy` (`deferred-parallel-subagents|inline` when a phase emits >5KB), `forced_gate` (per-phase state machine: `pending|true|satisfied — Q "<header>" → "<answer>"|false`), `pN_result:` (one-line per closed phase — the only programmatic record when per-phase files are trimmed), `pivot_class`, `branch_data_status` (`populated|empty|unknown` — #79), `scope_truncated` (what+where, if context forced a partial — #74), `goal_line` (the `/goal` condition emitted at plan approval, for `--resume` re-paste — §Step 2), `workflow_available` (`yes|no|unknown` — §0.7 Workflow-tool probe) + `workflow_emitted` (the emitted-script run-handle/path, or a skip reason from the §0.7 table — the two EMIT artifacts sit beside `goal_line`). Plans inventing undocumented fields = noise.

### The plan must include
- Mode · status · trigger/context · predecessor (extension) · standing_instructions · approval cadence · offline-resource map (W0 result).
- **Lessons from memory / past campaigns** (by ID/title) + which I'll follow/avoid (G4).
- **Wave structure** (W0 + 4 waves with task lists).
- **Per-task agent + model-assignment table** (mandatory — P2): task ID | wave | run-by (subagent type / ollama) | model | effort | output file.
- **Phase list with risk tags:** green (reversible/FE/additive) — run under autonomous/hybrid, gate under strict; amber (schema-additive/new views/RLS/indexes) — same; red (destructive DDL / data backfill / money / column drops) — ALWAYS gate.
- **Reference render structure** (REQUIRED for visual-conformity campaigns): outer wrapper → named lines → hover/transition → leaf primitives, extracted from the reference's full render — name the EXACT leaf file (#26 #83). Empty block ⇒ plan can't be approved.
- **Verification recipe + verification_class per phase** (#20 #35 #53). **Generation strategy** for >5KB-content phases (spec, not content — #34; i18n adds intentionally-EN + cognate lists, see references/fe-i18n-playbook.md).
- **Consolidation plan** (existing primitives, extractions, N=3 alarm) · **Cleanup plan — CANDIDATE deletions only** ("verify in Phase N — grep-proof authorises the rm", #14) · **Forced single-question gates** (mass-rename >15 sites / namespace move / public rename — fire `AskUserQuestion` even under autonomous; flip `pending→satisfied` immediately after the matching planning Q resolves, cite `Q "<header>" → "<answer>"`, #15) · **Success criteria.**

### Emit the `/goal` line (at plan approval — composes with Claude Code's built-in `/goal`)
Claude Code's built-in `/goal <condition>` (v2.1.139+) is a session-scoped Stop hook: after each turn a fast model checks the condition against the conversation and re-fires Claude until it holds — a HARDER persistence guarantee than this skill's prose "conquer without stopping" (it survives context pressure, #13/#74). It can't be set from inside this skill (a skill is a prompt; `/goal` is user-typed). So **at plan approval, emit ONE ready-to-paste `/goal` line** built from the Q9 success criteria, so a single approval can run the whole campaign unattended:
```
/goal <verifiable end state from Q9> — every plan phase reads status: completed, 99-risk-sweep.md is written, tsc + lint clean[, <interaction-recipe outcome observed>]. Stop after <N> turns if not met.
```
Condition rules — the evaluator only judges the TRANSCRIPT (can't read files / run tools, #89): phrase every clause as something Claude's own output demonstrates (`npm test` exits 0; the plan's phases all print `completed`), not raw file state; ≤4000 chars; always include a turn bound. Record it as `goal_line:` in the plan frontmatter (so `--resume` can re-paste). Pasting `/goal` is OPTIONAL — attended runs are already driven by the cadence; the line is for hands-off runs.

### Emit the Workflow script (per-wave after discovery — composes with Claude Code's deterministic Workflow tool)
A skill is a prompt; it cannot invoke the Workflow tool (opt-in / main-loop only). So **emit a ready-to-run script** the user opts into — the same EMIT-not-invoke move as `/goal` + `spawn_task`. **But unlike `/goal` (one declarative line, safe at plan approval), an eligible script CONSUMES prior-wave output** (the source-walk file list comes FROM W1; W2 reads W1 findings) — so emit it **per-wave just-in-time with REAL paths filled from completed discovery**, never as a single plan-approval block with `files=['…']` placeholders (those fail silently — agents write to the wrong place). Eligible = read-only parallel-barrier waves (W1/W2/W3-audit) + the `>20-file source-walk` (`pipeline`) + an approved NON-DB fan-out write sweep (separate post-approval script, `isolation:'worktree'`). INELIGIBLE (cross-ref the boundary): the planning interrogation, every `AskUserQuestion` gate (forced_gate / pivot-chain / promotion / >5-min-batch confirm), W3 DB/red writes, W4 synthesis. Honest scope: an OPTIONAL deterministic executor for the rare hands-off / large-fan-out run — most valuable for the source-walk batch (retires #39/#40/#42/#75); the in-message dispatch already barriers, so don't expect it to upgrade the everyday attended wave. `parallel()` nulls only an ERRORED agent — a truncated-but-succeeded agent returns a thin-but-valid result, so each agent `schema` MUST carry completeness predicates (required-non-empty, min counts) and the main-agent spot-check (§Self-verification) STAYS. Record `workflow_emitted:` for `--resume` re-paste. Pasting is OPTIONAL. Detail: references/wave-playbook.md → Deterministic orchestration. (#93)

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

Rules: wait for a wave's hard dependencies before the next (W4 waits for everything; W3 phases are sequential because P2 may depend on P1). Inside a wave, dispatch in parallel (same message, multiple Agent calls). Respect the cadence (autonomous: stop only at red; hybrid: stop at red; strict: stop at everything). If a subagent comes back blocked, fall back to a tractable proxy (migration files, git history, AST) and emit `<!-- CHECKPOINT: CHK-<id> -->` (references/checkpoint-pattern.md).

### W3 execution loop (build) — per phase, in order
**Pre-W3 checklist (tick before the first Write; mark N/A explicitly if it doesn't apply):**
```
□ G1 reference render-structure filled + leaf file named (UI phases)
□ G1 N=3 alarm cleared — sibling-clone grep + base-primitive identified (UI)
□ N=3+ union-prop audit — consumer grep per value of any ≥3-value union prop (consolidation)
□ reference file re-Read THIS turn
□ G2 project_id verified (any MCP)
□ G3 schema claim verified via information_schema/pg_policies/pg_views (DB)  → references/db-playbook.md
□ G6 DB-object conformity — naming + security boilerplate + RLS bundle (W6) + view-registry (W3) + callRpc (C4) + soft-delete (C31), any DB object create/alter  → references/db-playbook.md → G6
□ themable-token semantic audit done (theme/dark-mode/contrast)  → references/fe-i18n-playbook.md
□ forced_gate read; if pending/true → AskUserQuestion fired
□ phase risk tag checked vs cadence
```

1. **Cadence check** — gate if the risk tag requires it; else proceed.
2. **Execute writes.** DB phases follow **PDAAV** (probe→draft→approve→apply→verify) — full procedure incl. post-migration ground-truth SELECT (#33), 2a-RLS effective-access check (#47), and phase-atomicity for multi-layer changes in references/db-playbook.md. Rename+shrink uses **RIBS** / **PDAAV-RIBS** (references).
3. **Stale-override sweep** (mandatory when this phase changed a shared primitive's visual default): grep every consumer override, reclassify still-correct / stale-against-old-default (fix NOW) / newly-redundant (remove); grep stale header comments (#23). **Single-instance fix → sibling-scan** the same directory (#77).
4. **Self-verification loop** (below).
5. **Update campaign tracking** (`phases_completed`, `current_phase`, `phases_remaining`, `pN_result:`).
6. **Append "what actually ran"** to the phase file (deviations, autonomous decisions, every fixed override with file:line + before/after).
7. **Continue.** Don't stop between green phases; don't ask "shall I proceed?" — the plan was approved.

**Mid-execution scope discovery:** ≤5 files/≤20 keys/same surface → proceed silently (log it); 6–50 / 21–200 → proceed + append a phase + log prominently (hybrid: one-line note, user can interrupt); >50 / >200 / any new surface → gate regardless of cadence. **Never silently truncate requested scope under context pressure** — checkpoint with what shipped + what remains + resume instructions + `scope_truncated:` (#74). Emit a heartbeat on any op >~2 min (#75).

---

## Step 4 — Synthesise (audit) / Verify (build)

Write the final artefact yourself — synthesis benefits from one mind reading all the evidence; don't delegate.

**AUDIT `99-synthesis.md`:** TL;DR (drift one-liner, real bugs, security, latent gaps) · critical findings · real bugs · doc ghosts (referenced, don't exist) · doc orphans (in doc, not in reality) · undocumented reality · patterns to document · per-doc rewrite checklist · code-cleanup checklist (separate PR) · open questions · re-audit cadence. **CRITICAL bugs get a build-vs-remove decision-tree with effort/risk tiers, not just a flag.** A graph "god-object" label needs LOC+exports confirmation, not edge-count. A `claude_hits:0` cold doc whose basename appears in CLAUDE.md / a planet-hub wikilink is NOT archivable.

**BUILD `99-risk-sweep.md`:** TL;DR (shipped + watch items) · per-phase verification (ran-as-planned vs deviations, decisions, evidence) · **surface-coverage matrix — every "✓" needs a concrete observation (screenshot / polled DOM / network call), not an intent** · conformity & consolidation audit · risk-area sweep (adjacent regressions) · post-deploy probes · memory updates · open items.

**W4-discovered phases:** browser verification sometimes surfaces a real defect the plan didn't anticipate. Don't silently inline-fix it into a prior phase — allocate a new phase ID with `discovered_during: w4`, run the full self-verification loop, list it under a distinct vault-log header, mention "+N W4-discovered phases" in the TL;DR. The campaign closes only after every discovered phase passes.

---

## Step 5 — Cleanup & close (mandatory, automatic — G5)

- **5.1 Delete dead code (grep-first).** For each candidate in the plan: `grep -rn "<Name>\|from.*<file>" apps/web/ --include=*.ts* | grep -v "<file>:"` → confirm zero live consumers. Re-categorise confirmed-orphan vs still-load-bearing (most "surely dead" candidates are still load-bearing — chrome migrated, content stayed). Delete only confirmed orphans; `tsc` after; record the grep proof + the kept/deferred list.
- **5.2 Final verification.** `npm run check-types --force` (first run/phase bypasses stale Turbo cache — #18) + `npm run lint`. **Provenance before blame:** a surfaced error/warning → `git diff <start-sha>..HEAD | grep -F '<substr>'` — absent = pre-existing (`spawn_task` + continue), present = campaign-introduced (blocker). `git stash` needs `-u` for untracked files or the check is a no-op (#56). **Scoped-lint:** when project-wide `--max-warnings 0` fails on an untouched file, run eslint scoped to the campaign-touched list (`git status --short`); `EXIT=0` proves the surface clean; the other warning rides as `CHK-<id>` (#61). Preview at phase exit only (never per Edit), AND only if the project doesn't own preview (G4). For `contrast-measured` run ≥2 probe passes.
- **5.3 Vault-log** — write IMMEDIATELY (P6/P10), `<vault_log_root>/<date>_<topic>.md`, all phases + files + P13 self-audit (if MCP used). Campaign-date = START date even across midnight/resume. Same-session pivots edit the existing entry, never duplicate. Incidental ≤3-line fixes in already-edited files → `## Incidental fixes`; anything larger → CHECKPOINT + defer. **Open with the mandatory Plain-English Summary section** (project P8, binding). **Project mechanics (lex_council, #87):** run ALL `git` inside the `lex_council/` submodule (workspace root has no remote); edit `docs/*` via an atomic read-replace-write (one shell call), NOT the Edit tool — the housekeeper daemon races Edit → endless "modified since read".
- **5.4 Memory entries** — one file per surprise/trap/new convention; don't batch. **Resolve/delete a memory entry in the same campaign that fixes the bug it describes** (stale "bug present" entries cause future zero-change audits — #C7). Explicit triggers: a lint rule firing under `--max-warnings 0` (project law); a user correction naming an undocumented convention; a W1 surprise; a grep result contradicting the user's mental model.
- **5.5 Update status** to `completed` — **gated on `99-risk-sweep.md` (or `99-synthesis.md`) existing on disk** (#11).
- **5.6 Promotion gate (audit)** — write rewrites to `docs/staged/` first; promote after CHECKPOINTs resolved + user review; remove the empty `staged/`.
- **5.7 Spawn the post-campaign cleanup follow-up (separate session).** After 5.5, hand the campaign's loose ends to the `cleanup` skill's `followups` mode in a FRESH session via `mcp__ccd_session__spawn_task`: title `Run /cleanup for <campaign>`; a **stand-alone** prompt (the spawned worktree has none of this session's context) that (a) names the campaign plan path, (b) says run `/cleanup followups` first, (c) lists the mode-specific sweeps for what THIS campaign touched (`lint` always · `postgres` if DB · `consolidate-code` if new components · `docs` if docs · `language` if i18n), and (d) **inlines the `99-risk-sweep.md` ## Open items + touched-surface list** so it's self-contained. The cleanup `followups` mode is built to consume exactly this (it locates the most-recent `status: completed` campaign + greps `## Open items` / `spawn_task` / `follow-up`). If `spawn_task` is unavailable (Cowork/headless), SKIP the spawn — the committed `99-risk-sweep.md` ## Open items ARE the durable queue a later `/cleanup followups` finds. Spawn ONCE per close; a reopened→reclosed pivot edits the existing follow-up note, never spawns a duplicate (#90).
- **5.8 Post-closure tweak detection** — within ~7 days, classify a tweak on the same surface: "fix X too"/"while you're at it" → re-read the predecessor's re-anchor, the fix lives where the original framing pointed; "make X match Y (predecessor surface)" → EXTENSION sibling-sweep; 1–3 line cosmetic → inline + append to the predecessor's risk-sweep §10; 4+ files / new surface → re-open as EXTENSION (`predecessor:` frontmatter, skip W1). Every post-closure tweak is logged against the campaign — a tweak handled in a one-shot turn with no link back is the campaign equivalent of a silent write. List intermediate stub-fix vault-logs in a re-opened EXTENSION's Trigger/Context so the chain stays reconstructable (#55).

---

## Step 6 — Reflection-pass (post-campaign skill upgrade)

Triggers on "reflect on this session and propose skill upgrades", "upgrade as recommended", "review and note lessons". NOT on "summarize what we did" (that's a vault-log). **Offer it proactively at campaign close, and APPLY — don't just report (the default is apply).**

1. **6.1 Inputs** — the closed campaign's full artifact set + the **LIVE SKILL.md read from disk** (NOT the version loaded at session start — it may have changed; users have flagged this twice) + the session's invented disciplines / stops / re-plans.
2. **6.2 Walk** — per phase + per W4-discovered + per post-closure tweak: did the agent stop/re-ask/re-plan (→ new gate)? invent a procedure (→ named pattern)? re-derive a named discipline (→ checklist)? use a frontmatter field informally (→ enum)? hit a project shape §0.0.5 didn't probe (→ extend it)?
3. **6.3 Classify** — MINOR (new section / discipline / failure-mode CLASS) vs PATCH (clarification / enum value / sub-pattern / checklist) vs MAJOR (wave-structure / artifact-layout change). Heuristic: needs a new heading to find it? → MINOR.
4. **6.4 Release-split** — ship MINOR then PATCH as two sequential entries in the same turn; don't bury paradigm changes among clarifications.
5. **6.5 Cross-ref completeness** — new §section ↔ the failure mode it cures; new `#N` ↔ its cure §; new named pattern ↔ the campaign that motivated it. Grep the draft: every `references/<file>`, `#N`, `§X`, `[[link]]` resolves.
6. **6.6 Apply + verify** + **6.7 report** the version path, new sections/modes/patterns, line delta, deferred low-signal findings.

---

## Self-verification loop (after every build phase / audit wave — automatic, never ask)

**Build:** run `tsc --noEmit` + `npm run lint`; both pass → log "clean", continue. Either fails → read errors, fix (≤3 targeted attempts, re-run after each); fixed → log "fixed (N attempts)"; 3 fails → CHECKPOINT + continue. **If the phase touches user-facing UI/theme/auth/hydration/realtime/locale: verification is REQUIRED** — BUT honor G4: when the project owns preview, hand off the recipe (don't run preview tools / don't touch the dev server); otherwise take a screenshot + polled DOM reads at multiple timestamps (100ms/500ms/1s/3s — single snapshots miss hydration timing), run the Q9 recipe, log actual values as evidence, and `location.reload()` between any manual debug poke and the next read (#21). Never stop to ask about verification results — self-heal or mark-and-move.

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

Irreversible+high-risk = drop a column/table, delete data (not code — code is in git), change RLS on money-adjacent tables, any `apply_migration` altering production data shape. NOT irreversible (never stop): component structure, file/var naming, CSS approach, extract-now-or-later (answer is always now), fixing a lint error the phase introduced. **Content-exclusion** ("do not include X") is a plan-gate, not a check-after — pre-filter before writing. Log every autonomous decision in the phase file (`> Decision: … (ladder level N)`).

---

## Subagent dispatch

- Default subagent type `general-purpose` (specialised agents have constrained write contracts). Hand each a self-contained brief: pre-existing files to read first (incl. `00-w0-offline-prescan.md`), exact output path, frontmatter, sections, and **explicit read-only vs may-write**. Audit + build-W1 are read-only; build-W2 writes only its own phase-plan file; **build-W3 writes are done by the main agent**, not an unapproved subagent.
- Run a wave's tasks in parallel (one message, multiple Agent calls). Track agent IDs for relaunch. Verify a dispatched file exists on disk before claiming done. After any wait >30s, re-Read the next target before Editing (#41).
- **Source-walk template** (>20 files inspected → JSON-on-disk, never inline): brief specifies inputs, per-item steps, exact JSON output path `<campaign>/NN-<topic>.json`, "cover every item once, dedupe by <key>, cap at <N>"; reply with counts + anomalies only. The main thread parses one file + builds SQL/UI from the typed shape (#42).
- **Long batches** (N>20 items) write progress to a sidecar via `fs.appendFileSync('progress.log', …)`, not `console.log` (stdout is buffered to non-TTY) — tailable + survives a kill (#39). Checkpoint incrementally every K (5 for ≤100, 20 for >100); confirm strategy via one `AskUserQuestion` before any >5min batch (#40).

- **Fan-out sweep** (named) — when ≥5 sibling files need the SAME mechanical, behavior-preserving refactor (apply one converted reference to N adapters), "build-W3 writes by main agent" yields to #74 (context exhaustion across N dense files): dispatch one `general-purpose` subagent per **disjoint** file, each briefed with (a) the canonical already-converted reference file, (b) a behavior-preserving mandate (every handler / guard / conditional identical — only restructure), (c) "touch ONLY your file; do NOT write shared docs (#91)". Then the MAIN agent runs the verification gate: full `tsc` + scoped `lint` + a **structural-grep matrix** asserting the target shape on every file (new API present, legacy absent) — tsc/lint prove it compiles, the grep proves it actually converted — and deep-reviews the 1–2 riskiest (money / state-machine) line-by-line; the rest ride the grep + the user's visual pass. Never fan-out writes to a shared file (#91).

- **Workflow-orchestration** (named) — on Claude Code CLI, when the user opted into orchestration AND a wave is a genuine scripted batch (the `>20-file source-walk`, #42) or an approved ≥5-file NON-DB fan-out sweep, the EMITTED Workflow script (§Step 2) replaces the hand-rolled `fs.appendFileSync` batch loop / prose barrier with `pipeline()` (no inter-stage barrier; harness checkpoint + `resume` retires #39/#40), `schema`-checked agent returns (the #42 JSON-on-disk cure, now auto-retried — carry completeness predicates so shallow truncation can't pass), `isolation:'worktree'` for parallel write sweeps, and `log()`/`phase()` heartbeat (#75). The script writes NO shared artefact — the MAIN agent consolidates the vault-log / risk-sweep after the barrier (#91). NOT for the everyday parallel `Agent`-call wave (already barriered in-message) and NEVER for DB/red writes, gates, or W4 synthesis. Absent the tool, the prose dispatch runs unchanged. Detail: references/wave-playbook.md → Deterministic orchestration. (#93, #94)

**Named patterns** (declare in plan frontmatter; full procedures in the playbooks): `PDAAV` / `PDAAV-RIBS` (DB — references/db-playbook.md) · `RIBS` / `RIBS-N` (FE rename+shrink — references/fe-i18n-playbook.md) · source-walk · scoped-lint (§5.2) · fan-out sweep · workflow-orchestration (§Step 2 emit) · checkpoint markers.

---

## Environment hazards (quick index — full prose in the playbooks)

PostToolUse hooks rewrite/strip mid-flight (prefer `Write` over chained Edits when the intermediate is lint-dirty — #28; re-Read after >30s waits — #41); JSX structural pivot via chained Edits → single `Write` (#51); mass-edit/codemod footguns — multiline-aware, `\b`≠decimal-safe, last-import insertion, `\uXXXX` double-escape, exclude canon files (#73, references/fe-i18n-playbook.md); runtime caches that don't HMR — newly-added JSON keys + SWC stale parses → **restart the dev server first when the runtime contradicts the file on disk** (#48); SSR/client hydration mismatch with module-level state (#20, references/fe-i18n-playbook.md); pre-commit hooks that auto-commit (husky/lefthook) — probe before committing, let the chain finish, document it (#63); docs housekeeper daemon races the Edit tool on `lex_council/docs/*` (bumps frontmatter between Read and Edit → endless "modified since read") — edit via an atomic read-replace-write, never retry Edit against a daemon-watched path (#87).

---

## Trigger-phrase precedence (the single resolution table — earlier wins; default LATER if unclear)

| Order | Trigger | Section |
|---|---|---|
| 1 | Resume `in-progress` campaign on disk | §0.0 |
| 2 | Same-session pivot (predecessor closed this session, user names a deficit) | §0.0.1 |
| 3 | Pivot-chain (≥2 prior pivots, same predecessor) | §0.0.3 |
| 4 | Post-closure tweak (predecessor closed ≤7 days ago) | §5.8 |
| 5 | `scope: bug-fix` (shipped bug in a predecessor-excluded surface) | §Step 2 |
| 6 | Reflection-pass on a closed campaign | §Step 6 |
| 7 | Vague-symptom verb (Part A reproduction) | §1.4 |
| 8 | Ambiguous-direction migration verb (keeper question) | §1.4.1 |
| 9 | Standard planning interrogation | §Step 1 |

Order 2 beats 7 (predecessor discovery still valid; Part A reduces to "screenshot or specific defect?"). Order 5 beats 4 when both "predecessor named" + "surface exclusion named" fire. Wrong-direction binding costs more than over-cautious re-interrogation.

---

## Model assignment

| Tier | Who | When | Cost |
|---|---|---|---|
| **W0 — Ollama** | main agent via Bash | file listing, grep counts, surface map, doc summarisation | free (local) |
| **W1–W3 — sonnet** | `general-purpose` subagent | mechanical scanning, route/hook/type mapping, standard pattern work | mid |
| **W1–W3 — opus** | `general-purpose` subagent | security, RLS, synthesis, money-adjacent, schema/trigger reasoning | highest |
| **W4 — you** | main agent | synthesis / risk sweep — never delegated | conversation turn |

Effort is set via prompt language (the Agent tool has no effort param): **deep** — "Reason step by step. Think through every implication and edge case. Flag uncertainty rather than guessing." **standard** — no special phrase. **fast** — "Mechanical task. List/count/map only. Don't reason beyond what you observe." opus+deep for security/RLS/synthesis/money; sonnet+fast for mechanical scanning; never deep on a mechanical task; avoid haiku when W0 ran.

---

## Conformity & consolidation (the always-on disciplines — full extraction procedure in references/fe-i18n-playbook.md)

**Conformity:** read the pattern docs + the reference's FULL render function before writing (G1/P4). Match visual hierarchy, token usage (`C.*`, `<MIcon>`, design tokens — no hardcoded hex / raw Material Symbols / Tailwind), naming, layout direction (LTR container for Arabic DB content in an English panel). Resolve inconsistency toward the majority pattern; don't add to it. At W4 run a conformity check incl. a stale doc-comment sweep for every design fact the campaign changed.

**Consolidation:** (1) inventory existing shared primitives; (2) extract before composing when 3+ consumers need a pattern; (3) extend a near-duplicate rather than fork; (4) **grep before changing a shared default** — decide the new value across ALL sites in one pass (the grep feeds the §W3 stale-override sweep); (5) **N=3+ union-prop audit** — when a ≥3-value render-mode union prop has N-1 legacy values, drop the prop + the dead branches + helpers used only by them, in the same phase (#58). Extraction phase comes BEFORE consumption phases. At cleanup: grep zero live imports of replaced components, delete, confirm `tsc`.

---

## Deploy & sync (added v3.0.0 — #84)

This skill exists in multiple locations that drift. After ANY edit to SKILL.md or references/, sync every copy and verify:

| Copy | Path | Role |
|---|---|---|
| Project-local (canonical) | `<project>/.claude/skills/conquering-campaign/` | what runs in this project's Claude Code |
| Slash-command pointer | `<project>/.claude/commands/conquering-campaign.md` | the `/conquering-campaign` entry point — must point at `.claude/skills/conquering-campaign/SKILL.md` (NOT a stale `_skill-updates/` path) |
| Source repo | `~/Documents/Claude/Projects/claude-skills/conquering-campaign/` | distribution source (git) |
| Cowork customize page | (web) | Cowork sessions — paste the full text |

Sync step: `diff -rq <canonical>/SKILL.md+references <source>` — must be empty (source keeps its own `evals/`). Confirm the slash-command pointer path resolves. When pasting into Cowork, paste the WHOLE file (a partial `cp` once produced duplicate frontmatter). The canonical copy is project-local; propagate FROM it.

## Skill self-health (run at every reflection pass — #84)

```bash
SK=.claude/skills/conquering-campaign
# every referenced file exists
grep -oE "references/[a-z0-9-]+\.md" $SK/SKILL.md | sort -u | while read f; do test -f "$SK/$f" || echo "MISSING $f"; done   # [a-z0-9-] so fe-i18n-playbook.md (digit) isn't silently skipped
# every #N has a catalog row
# every §X and [[link]] resolves (manual scan)
wc -l $SK/SKILL.md   # track core size — investigate if it climbs back toward 2000
```
A dangling `references/<file>` / `#N` / `§X`, or a core ballooning past ~1200 lines, is a self-health failure — fix in the same pass.

---

## Common failure modes

Full prose + post-mortem context: **references/failure-modes.md**. The table is the lookup (symptom → cure pointer + status). Adding a mode: append to references/failure-modes.md AND add a row here with the next sequential `#N`.

Status: `promoted → PN` (now a principle) · `named → X` (a named pattern) · `embedded → §X` (cure in that section) · `active` (watch-list).

| # | Title | Status | Cure |
|---|---|---|---|
| 1–7 | W0 skip · model table · stop-mid-exec · invent-style · copy-paste · dead-code · skip-vault-log | promoted → P1–P7 | principles |
| 8 | Audit: trust graph hypothesis unverified | active | §Step 3 1.5d + §Step 4 |
| 9 | Audit: skip synthesis | active | §Step 4 |
| 10 | `apply_migration` on red without approval | active | §Step 3 cadence |
| 11 | Skip risk sweep / no artifact before completed | active | §5.5 |
| 12–13 | Leave `in-progress` · stall after plan/before commit | active | §5.5 / §Core + G5 |
| 14 | Pre-commit deletions in plan | active | §Step 2 + §5.1 |
| 15 | Mass-rename without forced gate | active | §Step 2 forced_gate |
| 16 | Ollama ANSI/echo-back; validate before W1 | embedded | §0.5 |
| 17 | Preview thrash / honor preview-ownership | embedded | §5.2 + G4 |
| 18 | Turbo cache masks errors | active | §5.2 |
| 19–22 | full-render read · client-state false-green · diagnostic pollution · stale/wrong reference | active/embedded | §1.2 Q9 + G1 + §Self-verif |
| 23 | Cascading-default leak | embedded | §Step 3 stale-override sweep |
| 24 | Post-closure tweak drag | embedded | §5.8 |
| 25 | Same-session pivot misclassified | embedded | §0.0.1 |
| 26–27 | reference-render-structure · Nth clone (N=3) | active | §Step 3 1.5a/1.5b + G1 |
| 28 | Multi-Edit atomicity | active | §Env hazards |
| 29–31 | TodoWrite carryover · echo-back prescan · inherited standing-instructions | embedded | §0.0.2 / §0.5.1 / §1.2 Q13 |
| 32–33 | W1 mis-locates column · `success` ≠ ground truth (+ concurrent-actor) | active | §Step 3 1.5d/2a + G3 |
| 34 | Inline >5KB generated content | embedded | `generation_strategy:` |
| 35 | Render-only verify of CRUD/editor | active | §1.2 Q9 `interactive` |
| 36 | Runtime-error provenance (+ abandoned dirty tree) | active | §5.2 |
| 37–38 | pivot-chain scope creep · preview deferred under auth wall | embedded | §0.0.3 / §0.0.4 |
| 39–43 | batch stdout-buffer · mid-batch pivot loss · Read/Edit long-pause · source-walk JSON · PDAAV | active/named | §Subagent dispatch |
| 44–46 | symptom-from-code · express-ack gap · docs-root split | embedded | §1.4 / §Step 2 / §0.0.5 |
| 47 | RLS qual-text ≠ effective access | active | §Step 3 2a-RLS |
| 48–51 | dev-server JSON cache · sidebar nav lock-in · micro-tweak ceremony · JSX-pivot Edits | embedded | §Env / G1 / §Step 2 / §Env |
| 52–53 | misnamed themable token · contrast without WCAG | active | §Step 3 1.5e / `contrast-measured` |
| 54 | Silent express trim | embedded | §Step 2 declaration gate |
| 55–56 | stub-extension chain invisible · `git stash` untracked | embedded | §5.8 / §5.2 |
| 57–59 | directional-keeper · stale union prop · medium-scope tier | embedded | §1.4.1 / §Consolidation / §Step 2 |
| 60–61 | RIBS rename+shrink · scoped-lint | named/embedded | §Subagent / §5.2 |
| 62–63 | asymmetric-themable bg-lock · auto-commit hooks | active | §Step 3 1.5e / §Env hazards |
| **64–66** | z-index→portal · sidebar-overflow portal · stepper measure-not-count | active | references/fe-i18n-playbook.md |
| **67–70** | pg function-body grep · DB-cascade blind to FE · ANALYZE stale stats · trigger order/recursion | active | references/db-playbook.md + G3 |
| **71–73** | useTranslations bare-key · i18n JSON hygiene · codemod safety bundle | active | references/fe-i18n-playbook.md |
| **74–77** | context-exhaustion silent truncation · no-heartbeat · scope-survey undercount · single-instance/sibling-scan | active | §Step 3 + G5 |
| **78–80** | dual-RLS + InitPlan (positive) · branch data-seeding · cron-only RPC prod-verify | active | references/db-playbook.md |
| **81–83** | nav-orphan after route change · merge-vs-separate planning · reference-hop-depth | active | G5 / §1.2 / G1 |
| **84** | skill self-integrity / deploy / self-health | active | §Deploy + §Self-health + §6.1 |
| **85–86** | execute_sql rollback swallows trigger RAISE · types.ts regen-overwrite | active | references/db-playbook.md |
| **87** | docs-daemon races Edit · submodule/no-remote git | active | §5.3 + §Env hazards |
| **88** | new DB object skips v2 conventions (naming/RLS-bundle/registry/callRpc/soft-delete) | active | G6 + references/db-playbook.md |
| **89** | `/goal` condition written as file-state its transcript-only evaluator can't observe | active | §Step 2 emit-`/goal`-line |
| **90** | post-campaign cleanup spawn handoff not self-contained / double-spawned on pivot | active | §5.7 |
| **91–92** | fan-out shared-doc collision · first-consumer dormant-primitive runtime bug | active | §Subagent dispatch / §Self-verif |
| **93** | Hand-orchestrated batch is non-deterministic (prose barrier + `fs.appendFileSync` progress; no schema-check / auto-retry / resume) | active | §Subagent dispatch workflow-orchestration + §Step 2 |
| **94** | Workflow tool treated as a hard dependency or invoked unprompted (breaks Cowork/headless portability; violates opt-in) | active | §0.7 skip table + §Step 2 emit |

### Anti-pattern quick-lookup (code/procedure smells → cure)
`C.X ?? '#hex'` fallback → drop it (tokens never undefined) · hardcoded hex w/o `theme-flat:` → token or comment · themable fg on themable bg (#52) → `alwaysWhite`/theme-flat · asymmetric-themable bg + fixed fg (#62) → bg-lock · chained Edits w/ lint-dirty intermediate (#28) → single `Write` · render-only CRUD verify (#35) → interaction recipe · mass-rename w/o forced_gate (#15) → add gate · pre-commit deletions (#14) → candidate + grep-proof · silent scope trim (#54) → declare tier · stale-cache symptom chase (#48) → restart dev server first · echo-back prescan as truth (#30) → `w0_useful: no` · inherited standing instr undeclared (#31) → `standing_instructions:` · hand-rolled primitive that exists (#27/#49) → G1 grep first · preview tools run when project owns preview (G4) → hand off recipe · new DB object w/o v2 conventions (#88) → G6 · hand-rolled inline RLS `EXISTS` → named bundle from RLS-BUNDLES.md (G6/W6) · `db().from().insert/update/delete` write → `callRpc` RPC (C4/G6) · `types.ts` full regen for a small change (#86) → hand-edit Row/Insert/Update · hand-rolled `fs.appendFileSync` batch loop on CLI (#93) → emitted `pipeline()`+`schema` workflow · Workflow tool as hard dependency / unprompted (#94) → §0.7 probe + EMIT-not-invoke.

---

## Output conventions

**AUDIT:** `00-campaign-plan.md` · `00-w0-offline-prescan.md` (if W0 ran) · `NN-<task>.md` (8–12) · `99-synthesis.md` · `CHECKPOINTS.md` (if blockers) · updated live docs · one vault-log · `audit-campaigns/README.md` (first run). **BUILD:** `00-campaign-plan.md` · `00-w0-offline-prescan.md` · `0N-phase-N-<topic>.md` · `99-risk-sweep.md` · `CHECKPOINTS.md` (if pending probes) · shipped code · deleted dead code · one vault-log · memory entries · `build-campaigns/README.md` (first run). Scope tiers (micro/small/medium) trim per §Step 2.

## Reference files
- references/failure-modes.md — full catalog #1–#94 (prose + post-mortem)
- references/version-history.md — full release history
- references/db-playbook.md — G6 DB-object conformity + PDAAV / PDAAV-RIBS + DB lessons + project schema facts
- references/fe-i18n-playbook.md — conformity extraction · RIBS/RIBS-N · env hazards · FE + i18n + codemod lessons
- references/templates.md — plan / findings / phase / synthesis / risk-sweep / checkpoint / vault-log templates
- references/wave-playbook.md — wave-by-wave subagent prompt templates, both modes
- references/checkpoint-pattern.md — CHECKPOINT markers, both modes

## Version history
Full history: **references/version-history.md**. Current: **v3.5.0 — 2026-05-29** — §0.7 Workflow-tool capability probe + skip table; §Step 2 **emits a ready-to-run Workflow script** (deterministic `pipeline`/`parallel`/`schema`/`resume`) per-wave after discovery, EMIT-not-invoke like `/goal`+`spawn_task`; `workflow-orchestration` named pattern; `workflow_available`/`workflow_emitted` frontmatter; #93–#94. Prev: **v3.4.0 — 2026-05-29** — §Subagent dispatch adds the **fan-out sweep** named pattern (sanctioned ≥5-disjoint-file parallel-subagent exception to W3-main-writes + main-agent structural-grep gate) + #91–#92. Prev: **v3.3.0 — 2026-05-29** — §5.7 spawns a self-contained follow-up **`/cleanup` session** (via `spawn_task`) at campaign close, handing its `99-risk-sweep.md` open-items to the cleanup skill's `followups` mode in a fresh session/worktree; durable fallback = the committed risk-sweep open-items; + #90. Prev: **v3.2.0** — §Step 2 emits a ready-to-paste **`/goal` line** at plan approval (transcript-only-evaluator-safe) + `goal_line:` + #89. **v3.1.0** — §Pre-flight Gate **G6** (DB-object conformity, W2–W6 doc-pointers) + G4 governance extension + #85–#88. **v3.0.0** — lean-core restructure + Pre-flight Gates + P8/P9/P10 + #64–#84. Bump `version:` on each meaningful upgrade; append the entry to references/version-history.md (newest first).
