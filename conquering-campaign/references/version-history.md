# Version history — conquering-campaign

Semver: **MAJOR** = paradigm shift / artifact-layout change · **MINOR** = new section / discipline / failure-mode class · **PATCH** = clarification, enum value, sub-pattern, checklist of existing prose. Newest first.

---

### v3.8.1 — 2026-06-04 — Playbook patch: RLS-IMPERSONATE, anon-RPC reads, dormant-gate, RTL transform (PATCH)

Additive field-lessons from the latest sessions (2026-06-02 → 06-04), mined in `references/REFLECTION-2026-06-04.md`. No new gate/wave/cadence — playbook + failure-mode additions only.

**What changed:**
- **`RLS-IMPERSONATE` named pattern (#104)** — the §2a-RLS effective-access check formalized into a named both-direction proof (`BEGIN … ROLLBACK` + `SET LOCAL ROLE authenticated` + `set_config('request.jwt.claims', …)` + a discriminating table) plus the cheap class detector `pg_policies WHERE qual='true' AND 'authenticated'=ANY(roles)`. From the 2026-06-02 security audit (report/counter/HR tables shipped `USING(true)` → customer reads all rows). Added to §Named patterns, G3, db-playbook §2a.
- **G6 anon-RPC public-read sub-rule (#105)** — public/anon/SSR surfaces read through an anon-granted `SECURITY DEFINER` RPC, never a `security_invoker` view (anon base-SELECT → silent `42501`; the sitemap emitted 0 URLs). db-playbook G6 item 8.
- **Dormant-gate audience probe (#106)** — G5 close-checklist now counts the live rows a new perm/scope/tier admits; a zero-audience gate ships as `CHK-` "dormant until X", not a silent green (`admin_scope=0` admits nobody). Generalizes #92.
- **RTL directional-transform trap (#107)** — `translateX(100%)`/`right:0` in an edge slide-over doesn't flip under RTL; use `lib/rtl.ts` + `<SlideOverPanel>` + `useIsRtl`. fe-i18n-playbook §New FE lessons. Plus the E6 id-type-agnostic bulk-primitive one-liner.
- **Hardened #96** — the preview pipeline is *reliably* dead (a fresh branch is `MIGRATIONS_FAILED` AND dataless), so a prod `BEGIN…ROLLBACK` dry-run IS the validation path; don't spend turns branching. failure-modes #96 + db-playbook off-pipeline §.

**Why PATCH:** four new failure-mode rows + one named-pattern + playbook prose; no new gate/wave/cadence/artifact-layout. A campaign behaves identically; these sharpen DB-security and RTL conformity execution.

---

### v3.8.0 — 2026-06-04 — Made G0 bite: PreToolUse hook + description under-match + bar redefinition + coherence metric (MINOR)

v3.7.0 shipped Gate G0 (campaign-worthiness EXIT) on 2026-06-02. **Measured 2 days later it had not bitten.** All-roots corpus (pruned, from project root): folders grew **161→180 (+19 in 2 days)**, thin(≤3-file)% **dead flat at 71%**, a 1-file bug-fix (`2026-06-04_bug253`) still opened a folder, and **53 folders** declared `scope: medium|full` while holding ≤2 files (scope-inflation the presence-only self-health metric was blind to). Root cause is the skill's own meta-lesson, recursive: G0 is in-skill prose, read only AFTER the trigger matched and the skill loaded — but the over-invocation decision is made the instant the phrase matches. A gate inside the skill can't bounce a request that already loaded it. (An earlier "156 / −5" read was a lex-submodule-cwd undercount — trusting it was itself the #32 trap; corrected to the project-root number.)

**What changed:**
- **PreToolUse hook `g0-campaign-guard.sh` (matcher `Write`)** — surfaces a HUMAN G0 checkpoint (`permissionDecision: ask`) the instant a NEW `*-campaigns/*/00-campaign-plan.md` is written; resumes/edits pass (`os.path.exists` guard); fail-open on any parse error. The only enforcement the agent can't self-bypass. Registered in `.claude/settings.json`; project-local (NOT part of the portable skill copy). Build gotcha caught + fixed in-session: pass python via `python3 -c '…'`, not a `<<'PY'` heredoc (which hijacks stdin so the JSON never arrives).
- **Description trigger under-matches** — the over-broad phrases ("build this feature", "ship this refactor", "proceed in application") qualified inline with the bar, so the router under-fires before the skill loads (the only change acting before load).
- **G0 bar redefined** — "≥3 real surfaces" → "≥3 INDEPENDENT logical changes" (a single vertical slice RPC+mutation+UI+i18n = ONE, not "4 surfaces"; the `bug253` counter-example inlined).
- **Self-health metric: presence → coherence** — adds `scope-INFLATED` (tier ≥ medium on a ≤2-file non-content folder), `loose-files` (a `.md` directly under a `*-campaigns` root), `off-enum-status`; baseline refreshed (180/127/49/INFLATED 53/loose 1/off-enum 20). The loose-file count uses `find` not a glob (a `for f in *.md` aborts under zsh — the #32 artifact, met again while writing this metric).
- **#103** — the recursive "a gate added to cure a buried rule is itself buried" meta-failure.

**Why MINOR:** a new enforcement layer (hook) + bar redefinition + coherence metric + one failure-mode class. Backward-compatible — a genuine campaign behaves identically; only sub-bar work now meets a human gate at folder-creation. (REFLECTION-2026-06-04.md.)

---

### v3.7.1 — 2026-06-02 — Completed the lean-core-v2 extraction (§Env hazards + §Deploy/§Self-health → references) (PATCH)

A parallel `cc WIP` commit (claude-skills `af46561`, same day) had begun extracting three encyclopedic SKILL.md sections into their own reference files but left it half-done — the files existed (`references/env-hazards.md`, `references/skill-maintenance.md`) but orphaned: the sections were still inline in SKILL.md, nothing referenced the new files, and `skill-maintenance.md` was a pre-v3.7.0 snapshot (no over-invocation sprawl metric, stale self-health grep, "700" vs SKILL's "1200" core target). At Atta's "finish what's open" this completes it.

**What changed:**
- **§Environment hazards** (the dense inline paragraph) → **references/env-hazards.md** (exploded per-hazard index). SKILL.md keeps a stub heading + a one-line pointer naming the hazard #s (#20/#28/#41/#48/#51/#63/#73/#87/#95/#99).
- **§Deploy & sync** + **§Skill self-health** → **references/skill-maintenance.md** (copy-table + sync procedure + the self-health checks incl. the G0 sprawl metric). SKILL.md keeps two stub headings + pointers.
- **Refreshed `skill-maintenance.md`** to the shipped v3.7.0 self-health: the over-invocation sprawl metric (pruned of `node_modules`/worktrees), the digit-safe referenced-file grep, the corrected baseline (161 / 115 / 49-of-153), a ~700-line core target (the lean intent).
- Wired both files into SKILL.md §Reference files; the core shrank ~40 lines.

**Why stubs, not deletions:** failure-mode rows + cross-refs point at `§Environment hazards` / `§Deploy` / `§Skill self-health` by name — keeping the headings as one-line pointers preserves every anchor (the same lean-core pattern the skill already uses, "full prose in the playbooks"). Also avoided clobbering the parallel session: `af46561` is committed (not uncommitted-tree state), so this is sequential git on `main`, not the #33/#95 co-mingle hazard.

**Why PATCH:** pure doc relocation — no new gate, discipline, failure-mode, wave, cadence, or frontmatter field; behavior identical with the tool absent or present. (A small continuation of the existing v3.0.0 split, not the new reading model that made v3.0.0 a MAJOR.)

---

### v3.7.0 — 2026-06-02 — Gate G0 campaign-worthiness triage-or-EXIT + `micro` retired + multiplier scope-gate (MINOR)

Triggered by Atta — "we have used conquering campaign too much lately" — and a mine of the on-disk corpus: **161 campaign folders** (123 in the primary lex build root), **74% of the lex build folders ≤3 files** (71% across all roots), 19% never reaching `status: completed`, and a `2026-06-02_dark-mode-color-fix` campaign that auto-spawned a `/cleanup` color session (doing a `/cleanup`-mode's job twice). The skill already *told itself* to bounce small work (§Two modes "this is overkill — offer a lighter pass" + the `micro` tier) but it never fired — soft-worded, buried below the mode table, read only AFTER the skill committed, and `micro` still built a campaign. Every gate G1–G6 governed *how to execute well*; none governed *whether to run at all*. This is the skill's own v3.0.0 meta-lesson ("a buried rule fires as a user correction — front-loading is the cure, not more prose") applied to the one boundary that never got a gate.

**What changed:**
- **New Gate G0 — campaign-worthiness triage-or-EXIT (the FIRST gate, before Step 0; the only gate that decides *whether* to run, not *how*).** Clear the BUILD bar (≥3 real surfaces / multi-phase / must-stay-deployable staging) or the AUDIT bar (real doc↔code/DB reconciliation across the app), else **EXIT**: decline + route to `/cleanup <mode>` (colors/lint/i18n/postgres) · single bug-fix · direct edit under P3, creating NO folder. File count is NOT the bar — *surfaces / staging* is. Override only on explicit user insistence (`g0_override:` frontmatter).
- **`micro` tier retired** — it IS the G0 exit now (≤2-file/≤10-line work is not a campaign). Its only non-waivable keeps (tsc+lint, §5.3 vault-log P8) are project rules that apply to ANY edit regardless.
- **Trigger-precedence row 6b** — a NEW request that fails the G0 bar EXITs; row 6b gates rows 7–9 (they start a NEW campaign → only fire after clearing G0), while rows 1–6 attach to an existing campaign/predecessor and bypass G0 (never re-triage in-flight work).
- **Multiplier scope-gate** — §5.7 `/cleanup` spawn + §Step 2 `/goal` + Workflow emits fire only for scope ≥ medium. A small/express/bug-fix campaign that cleared G0 doesn't multiply into more sessions.
- **§Skill self-health sprawl metric** — every reflection pass now prints `campaigns / thin(≤3 files) / no-scope-decl` (baseline 2026-06-02: 123 / 91 / 116); a rising thin% or no-scope% means G0 isn't firing.
- **`g0_override` frontmatter field** + **#101** (over-invocation / ceremony-inflation, the umbrella) + **#102** (scope-declaration ~68% — not enforced to 100%; and a declared scope SIZES a campaign but never asks whether to open one — sizing ≠ gating).

**Considered + rejected:** (a) deleting the 91 thin folders — treats the symptom, not the cause; G0 prevents new ones, and the corpus stays as the #101/#102 evidence. (b) hard-blocking the broad trigger phrases ("ship this refactor") in the description — they legitimately match real campaigns too; G0's surface/staging test is the right discriminator, not phrase-banning. (c) making `small`/express exit too — a genuinely multi-surface 4–5-file change with staged verification IS a (small) campaign; the bar is surfaces/staging, not raw file count, so `small` stays.

**Why MINOR:** new G0 gate (new heading + discipline) + 2 failure-mode classes + 1 precedence row + 1 self-health metric + 1 frontmatter field. Fully backward-compatible — every wave, named pattern, cadence, and existing frontmatter field stays valid; a genuine campaign behaves identically. The only behavior change is that sub-campaign work now EXITs instead of spinning ceremony.

**Self-audit (an #32 caught + corrected before ship).** The first cut of #102 claimed "`scope:` declared in 0/116 plans → discipline silently dead." That zero was a measurement artifact — a zsh `for f in */00-plan.md …` glob hit `no matches found` and aborted the mining loop before it read a single file. Re-verified with `grep -l '^scope:' */00-campaign-plan.md`: **84/116 (72%) DO declare scope** (104/153 all roots). #102 was reframed from "dead" to "incompletely enforced + sizing ≠ gating," and the self-health metric was re-pruned (an unpruned `*-campaigns` find triple-counts via the #95 worktrees — 539 vs the true 161). The over-invocation thesis (#101 — the thin-folder ratio + the dark-mode→spawn-cleanup multiplier) was independently evidenced and unaffected by the error. The skill's own #32 / #8 / #100 ("an upstream count is a lead, not a fact") applied to this very reflection pass.

---

### v3.6.2 — 2026-05-30 — Worktree verification (no node_modules) + BUILD-re-verifies-AUDIT-counts (PATCH)

Reflection-pass over **Campaign A** (FE adopt-and-relocate — the audit's first FE build, shipped on `feat/campaign-a-fe-adopt`). Two field-proven clarifications to existing sections — no new wave/artifact/cadence — hence PATCH.

**What changed:**
- **#95 completed.** §Environment hazards + failure-modes `95.`: a fresh `git worktree` has NO `node_modules` (gitignored, not copied) → `tsc`/`lint`/preview can't run until you symlink every `node_modules` dir from the primary checkout (`find . -maxdepth 3 -name node_modules`); the symlink resolves workspace `@repo/*` to the primary's `packages/`, so confirm `git status packages/` is clean there first (else you verify against the concurrent-actor-dirty source). Much faster than `npm install` in the worktree. Campaign A symlinked root + `apps/web` and verified green.
- **#100 (new).** §Common failure modes + §Step 3 + G1: a BUILD extending an AUDIT must re-verify the audit's "N files share an identical block" structural count against live source before the extraction edit — Campaign A's FE-2 found the "10 files / 15 fields / byte-identical" claim held for only 4 rows / 8 fields (the other 6 diverged in casing / nullability `?` vs `| null` / field presence / mapper fallbacks / no-block). Extract only the provably-identical subset; record scope + exclusions in the primitive's doc comment; never force a merge needing consumer edits. The BUILD/extension twin of #8 + #32.

---

### v3.6.1 — 2026-05-29 — Concurrent-actor git isolation + off-pipeline migration apply + DROP show-gate + gh handoff (PATCH)

Reflection-pass over the **app-wide-consolidation audit + its first two built campaigns (B — BE mechanical simplify; E — perf FK-indexes)**. Four field-proven DB/git disciplines that the campaigns invented at execution time but the skill hadn't codified. All four are clarifications/sub-patterns to existing sections — no new wave, artifact, or cadence — hence PATCH.

**What changed:**
- **#95 worktree-isolation.** §Environment hazards + references/db-playbook.md: when a concurrent actor (#33) holds uncommitted changes in the MAIN working copy, branch via `git worktree add .claude/worktrees/<name> -b <branch>`, NEVER `git checkout -b` (moves HEAD in their tree → hijack/co-mingle). Both Campaigns B+E shipped on worktrees.
- **#96 apply-via-MCP when the preview pipeline is `MIGRATIONS_FAILED`.** references/db-playbook.md new section: the lex Supabase git→preview pipeline is failed since 2026-05-23 → apply idempotent/reversible migrations via MCP `apply_migration` after show-SQL (P3) + G3 re-probe; commit the migration file for record (idempotent on any re-apply).
- **#97 reversibility show-gate.** §Autonomous decision ladder + §5.1: under autonomous, reversible `CREATE OR REPLACE` proceeds with show-SQL; an irreversible `DROP` / money-/auth-adjacent bulk refactor ALWAYS gets full SQL shown + explicit go, carries `RESTRICT`, and runs a delete-time LIVE re-grep (Campaign B kept its `*_bak` tables, dropped the reversible orphans). Sharpens #14 with the reversibility axis.
- **#99 `gh`-absent handoff.** §5.3 + §Environment hazards: `gh` isn't installed → push + hand over the `pull/new/<branch>` URL, don't fail.

**Why PATCH:** all four refine existing sections (env hazards, the ladder, §5.1, db-playbook) + 4 catalog rows; no new heading-level discipline, fully backward-compatible.

---

### v3.6.0 — 2026-05-29 — Audit same-session lens-extension (MINOR)

From the same audit: the `2026-05-29_app-wide-consolidation` audit closed at 6 findings, then grew **in-session** with 5 new read-only investigation lenses ("at Atta's request" — access-correctness, component-substitution, droppable-schema, mergeable-columns, slow-views), each folded into the ONE `99-synthesis.md` + build-plan-proposal + vault-log. The skill had §0.0.1 (same-session BUILD pivot) but no AUDIT equivalent — so a lens-extension risked being mis-opened as a new campaign or duplicating the synthesis/vault-log.

**What changed:** new **§0.0.6 — Audit same-session lens-extension** (reopen `completed → in-progress`, append an `LN_lens` phase with `discovered_during: same-session-lens`, skip W0+W2, run focused read-only W1/W3, fold a new `NN-<lens>.md` + `## Extension lenses` synthesis block + build-plan rows IN PLACE, edit the vault-log not duplicate, re-close); a §0.0 resume-table row; a §Trigger-phrase precedence row (2b — ahead of §1.4 / §5.8); new failure mode **#98**. A lens that surfaces a shipped bug or needs a write escalates out to `bug-fix`/EXTENSION.

**Why MINOR:** new §0.0.6 sub-section (a new heading + a discipline + a failure-mode class), fully backward-compatible — no wave-structure, artifact-layout, or cadence change.

---

### v3.5.0 — 2026-05-29 — Workflow-tool deterministic orchestration EMIT (MINOR)

Pairs the skill with Claude Code's deterministic **Workflow tool** (a JS script orchestrating subagents via `parallel`/`pipeline`/`schema`-checked returns/`log`/`resume`) — the third instance of the "compose with a main-loop/external feature via a portable EMIT" move after v3.2.0 (`/goal`) and v3.3.0 (`spawn_task`). Motivated by the user asking whether the skill could be upgraded with the Workflow tool; designed + adversarially critiqued via a 4-agent workflow (which was itself the read-only structured-fan-out the integration targets).

**The honest framing (from the adversarial review).** The skill ALREADY fans out subagents in parallel via in-message `Agent`-call dispatch, and that dispatch ALREADY barriers (the main loop blocks until every tool-result returns). So the Workflow tool's marquee deterministic-barrier buys little for the everyday wave. The genuine win is NARROW: the `>20-file source-walk` is a true scripted batch (hand-rolled today with `fs.appendFileSync` + checkpoint-every-K) — `pipeline()` + `schema` + harness `resume` retires #39/#40/#42/#75 there. Write fan-outs gain `isolation:'worktree'`. Everything else is marginal.

**What changed:** §0.7 capability probe + skip table (mirrors the Ollama W0 skip table); §Step 2 emits a ready-to-run script — but **per-wave just-in-time with real paths**, NOT a single plan-approval line, because an eligible script consumes prior-wave output (explicitly NOT the same as the `/goal` single declarative line, which has no such dependency); `workflow-orchestration` named pattern; `workflow_available` / `workflow_emitted` frontmatter; full eligibility + primitive-mapping TABLE (not a copy-paste sketch — a hard-coded script with paths would double the #84 drift trap) in references/wave-playbook.md → Deterministic orchestration. New failure modes **#93** (hand-orchestrated batch non-determinism — scoped to the source-walk loop, NOT over-claiming #41/#91) + **#94** (Workflow-as-hard-dependency / unprompted-invocation — the portability + opt-in trap).

**Considered + rejected:** (a) making the script the DEFAULT path or having the skill auto-invoke it — breaks Cowork/headless portability + violates the explicit-opt-in constraint; the in-message prose dispatch stays the portable default. (b) a single plan-approval EMIT like `/goal` — the script consumes discovery output that doesn't exist at approval → placeholder arrays that fail silently. (c) encoding W1/W2/W3-audit/W4 as workflow scripts — redundant with the already-barriered in-message dispatch; only the source-walk batch + write fan-outs clear the bar.

**Why MINOR:** new §0.7 + §Step 2 sub-section + a discipline + a failure-mode class + 2 frontmatter fields, fully backward-compatible — no wave-structure, artifact-layout, cadence, or existing-frontmatter change. Every wave, named pattern (PDAAV, RIBS, source-walk, fan-out sweep), and cadence remains valid; absent the tool the skill behaves identically to v3.4.0.

---

## v3.4.0 — 2026-05-29

- §Subagent dispatch: new **fan-out sweep** named pattern — sanctioned exception to "build-W3 writes by main agent" when ≥5 disjoint sibling files need the SAME mechanical behavior-preserving refactor (one general-purpose subagent per file + canonical-reference brief), gated by a main-agent **structural-grep matrix** (tsc/lint prove compile, grep proves conversion) + line-by-line deep-review of the 1–2 riskiest. Resolves the #74 context-exhaustion vs W3-main-writes tension.
- #91 (fan-out subagents collide writing a shared doc → return summaries, main consolidates) + #92 (first live consumer of a dormant/barrel-promoted primitive hits a latent runtime bug tsc/lint miss → treat as interactive verification). From the container-action-zone-ux campaign.

### v3.3.0 — 2026-05-29 — §5.7 auto-spawns a post-campaign `/cleanup` follow-up session (MINOR)

Closes the loop with the **cleanup** skill: the user always ran `/cleanup followups` by hand after a campaign — now conquering launches it. At close (after §5.5 `status: completed` + §5.3 vault-log), §5.7 calls `mcp__ccd_session__spawn_task` to spin up a FRESH session + worktree that runs `/cleanup followups` (+ mode-specific sweeps for what the campaign touched), with a **self-contained** handoff prompt that inlines the `99-risk-sweep.md` ## Open items + touched-surface list + the campaign path.

**Mostly wiring, not new machinery:** cleanup's `followups` mode already locates the most-recent `status: completed` campaign and greps its `99-risk-sweep.md` `## Open items` / `spawn_task` / `follow-up` markers; conquering already writes that risk-sweep + flips the status. The only missing link was the spawn — now added at §5.7 + a G5 close-checklist bullet.

**Durable fallback:** if `spawn_task` is unavailable (Cowork/headless) or the chip is dismissed, the committed risk-sweep open-items ARE the queue a later `/cleanup followups` finds — the handoff survives. New failure mode **#90** (self-containment of the spawn prompt + don't-double-spawn-on-pivot).

**Why MINOR:** new §5.7 close step + G5 bullet + #90, fully backward-compatible.

---

### v3.2.0 — 2026-05-29 — Emit a ready-to-paste `/goal` line at plan approval (MINOR)

Pairs the skill with Claude Code's built-in **`/goal`** command (v2.1.139+) — a session-scoped prompt-based Stop hook that re-fires Claude after each turn until a fast model confirms the condition holds against the transcript. The user always invoked `/conquering-campaign` + `/goal` together; this collapses the double-invocation.

**What it is NOT:** a skill cannot set `/goal` (a skill is a prompt; `/goal` is user-typed / `-p`). So this is the portable Tier-1 integration, not a hard merge.

**What changed:** §Step 2 now emits ONE ready-to-paste `/goal <condition>` block at plan approval, built from the plan's Q9 success criteria + "all phases `completed`, `99-risk-sweep.md` written, tsc+lint clean, <interaction-recipe outcome>". The condition is phrased for `/goal`'s **transcript-only evaluator** (it can't read files / run tools), capped ≤4000 chars, with a turn bound. New `goal_line:` frontmatter records it for `--resume` re-paste. New failure mode **#89** (writing a `/goal` condition as unobservable file-state). Pasting the line is OPTIONAL — attended runs ride the cadence; it's for hands-off runs.

**Considered + rejected:** a Tier-2 campaign-guard Stop hook in settings.json (auto-enforces persistence while a plan is `status: in-progress`). Rejected as the default — machine-local (doesn't sync), rebuilds a maintained built-in, and a self-blocking hook is a footgun needing an `awaiting-approval`/`blocked` escape protocol. Tier 1 ships with the skill to every machine + Cowork with zero risk.

**Why MINOR:** new §Step 2 discipline + frontmatter field + failure mode, fully backward-compatible.

---

### v3.1.0 — 2026-05-29 — §Pre-flight Gate G6 (DB-object conformity) + G4 governance extension + #85–#88 (MINOR)

Mined from the **app's own binding docs** (CLAUDE.md W2–W6, `V2-CONVENTIONS.md`, `RLS-BUNDLES.md`, `DB-NAMING-OVERHAUL.md`, `DESIGN-CANON.md`) + project memory — the gap a 3-agent reconciliation found between what the app MANDATES and what the skill encoded. The skill was elite on process + failure-modes but conformed only to FE *visual* primitives (G1); a BUILD campaign creating a DB object followed great process and could still ship a non-conformant table (ad-hoc inline RLS, non-v2 view name, missing view-registry key, `.from().insert()` write, soft-delete bypass).

**New gate — G6 DB-object conformity (the DB twin of G1).** Before creating/altering any table/view/trigger/RPC, conform to the app's binding v2 conventions — **as doc-pointers, not duplicated rules** (V2-CONVENTIONS wins on conflict; the skill points, the app doc is the source of truth). Covers naming (W2), view safety (S11/S12: `security_invoker` always, append-only, no shared views), RPC/trigger security boilerplate, the ONE-`FOR ALL`-from-the-named-bundle-catalog RLS rule (W6 — never inline `EXISTS`, propose a new bundle if none fits), view-registry sync (W3), `callRpc` writes (C4/C30), soft-delete-only (C31). Full checklist in `references/db-playbook.md` → new **G6** section; wired into the §Step 3 pre-W3 checklist so it fires at the moment of action.

**G4 extended (project governance).** Sacred `> [!atta]` blocks are supreme (never edit; they outrank CLAUDE.md, docs, AND the user request — surface conflicts, don't silently pick a side); docs-before-SQL (P11/P13 — read the leaf doc before introspecting); `docs/archived/` off-limits unless granted.

**Close-step project mechanics (§5.3 / §Env hazards).** `lex_council/` is a git submodule + the workspace root has no remote → run git inside the submodule; edit `docs/*` via an atomic read-replace-write (the housekeeper daemon races the Edit tool → endless "modified since read"). Plain-English Summary made an explicit vault-log requirement.

**4 new failure modes (#85–#88):** execute_sql-rollback-swallows-RAISE · types.ts-regen-overwrite · docs-daemon-races-Edit + submodule-git · new-DB-object-skips-v2-conventions (the G6 umbrella).

**Why MINOR:** new gate + new failure-mode class + new reference section, all backward-compatible — no wave-structure / artifact-layout / frontmatter-field change. All existing campaigns, patterns, cadences, and frontmatter remain valid.

---

### v3.0.0 — 2026-05-29 — Lean-core restructure + integrity repair + 21 new failure modes (MAJOR)

Triggered by an exhaustive mine of **136 campaign folders + 159 session transcripts** (266 candidate lessons → 165 new / 39 rule-not-working / 42 reinforces) and three structural defects found in the skill itself (failure mode #84).

**Integrity repair:**
- **Recreated the dangling companion files.** v2.0.0 "externalized" failure-mode prose + version history to a `_skill-updates/` staging dir, committed once (`640d730`), then deleted the staging dir without co-locating the files next to the live SKILL.md — leaving every `FAILURE-MODES.md#N` / `VERSION-HISTORY.md` reference pointing at nothing, and the 87-line "externalized" cut losing most of the prose. v3.0.0 recovers the full #1–#61 prose from the v1.13.1 source and lands the catalog as `references/failure-modes.md` (#1–#84) + this `references/version-history.md`.
- **Re-synced the two diverged copies** (source `claude-skills/` was v1.13.1/May-18; project-local was v2.0.0/May-29) and added a **§Deploy** section listing every copy + a post-edit sync step.

**Lean-core restructure (the "efficient" goal):**
- SKILL.md cut from 2,446 lines to a lean operating core; encyclopedic detail moved (not deleted) to on-demand references: `failure-modes.md`, `db-playbook.md`, `fe-i18n-playbook.md`, plus existing `templates.md`, `wave-playbook.md`, `checkpoint-pattern.md`.
- The 7 scattered trigger tables collapsed to the single §Trigger-phrase precedence table.

**Effectiveness — front-loaded gates + new principles (the fix for the #1/#2 recurring failures):**
- **§Pre-flight Gates** — a short, unmissable block near the top: G1 reuse-before-build, G2 verify-project-id, G3 DB-wave re-probe, G4 defer-to-memory, G5 close-checklist. The mine proved the two most-frequent failures (conformity-reuse: 11/14 batches; vault-log: 10/14) were ALREADY codified but buried — front-loading + cutting bulk is the cure, not more prose.
- **P8 Defer to project memory & standing instructions over skill defaults** — resolves the preview-verification conflict (the skill told agents to run preview while the project standing-instruction + memory said "visual verification is the user's job, never hijack the dev server"). Also covers response-format (plain-English lead) and project facts (Supabase project_id).
- **P9 Reuse before build** — grep current + sibling surfaces for an existing primitive before writing any component/style/button.
- **P10 Vault-log has no exemptions** — not "small tweak", not "same conversation".

**21 new failure modes (#64–#84):** z-index→portal · sidebar-overflow portal · stepper-measure-not-count · pg function-body grep on rename · DB-cascade blind to FE callsites · ANALYZE stale stats · trigger firing-order/recursion · useTranslations bare-key · i18n JSON hygiene · codemod safety bundle · context-exhaustion silent truncation · no-heartbeat long ops · scope-survey undercount · single-instance fix sibling-scan · dual-RLS propagation + InitPlan fast-path · branch data-seeding gate · cron-only RPC prod-verify · nav-orphan after route change · merge-vs-separate planning gap · reference-hop-depth · skill self-integrity/deploy/self-health.

**Backward compatibility:** all frontmatter fields, wave names, scope tiers, named patterns, cadences, and existing campaign artifacts remain valid. Why MAJOR: the distribution shape changed (SKILL.md is now a core that REQUIRES the references for full detail) and the reading model changed (look up the table → jump to a reference).

---

### v2.0.0 — 2026-05-22 — Failure-mode catalog restructure (MAJOR, superseded by v3.0.0)
Compressed the flat 63-entry prose list into a cross-reference TABLE + (intended) companion `FAILURE-MODES.md`. **Defect:** the companion files were never co-located with the live SKILL.md → dangling refs + prose loss; repaired in v3.0.0 (failure mode #84).

### v1.15.1 — 2026-05-22 — Version-history rollup + trigger-precedence re-audit (patch)
v1.0.0→v1.12.1 entries moved to a companion file; added the `scope: bug-fix` row to trigger precedence.

### v1.15.0 — 2026-05-22 — Frontmatter master table + Scope decision tree + W0 skip-table + `scope: bug-fix` tier + Anti-pattern index
Five additive sections from a holistic review. `scope: bug-fix` for shipped-bug fixes in predecessor-excluded surfaces. Frontmatter master reference (27 fields). Scope decision tree. W0 skip-reason unified table.

### v1.14.2 — 2026-05-22 — §0.5.x ordering fix + POST-MORTEM cross-link (patch)

### v1.14.1 — 2026-05-22 — Frontmatter + procedure clarifications (patch)
`w0_useful: partial`; 4th W0-skip reason (deterministic tooling); `pN_result:` per-phase frontmatter; depth-pivot vs scope-expansion-pivot; iterative WCAG sweep (≥2 passes); defensive `?? '#hex'` anti-pattern.

### v1.14.0 — 2026-05-22 — Asymmetric-themable-color pair + Hook-auto-commit chain
Failure modes #62 (bg-lock pattern) + #63 (pre-commit hooks that auto-commit).

### v1.13.1 — 2026-05-17 — Named-pattern index + forced_gate flip-point + wikilink enforcement + RIBS-N + PDAAV-RIBS + pre-W3 checklist (patch)

### v1.13.0 — 2026-05-17 — Reflection-pass procedure + Standing principles tier + Trigger-phrase precedence
§Step 6 reflection-pass codified; failure-mode list bifurcated into Standing Principles (P1–P7) + numbered modes; trigger-precedence table.

### Pre-v1.13 (one-line summaries)
- **v1.12.1** — `forced_gate:` state-machine enum + `claude_md_path`/`wikilink_convention` probe + scoped-lint + campaign-date convention + RIBS. (#60, #61)
- **v1.12.0** — §1.4.1 ambiguous-direction gate + N=3+ union-prop audit + `scope: medium`. (#57, #58, #59)
- **v1.11.0** — Content-only campaigns + Ollama REST API + i18n discipline + mid-execution scope gate.
- **v1.10.0** — Themable-token semantic audit + `verification_class: contrast-measured` + express-mode declaration gate + stub-extension chain visibility. (#52–#56)
- **v1.9.0** — `scope: micro` + runtime cache routing + sidebar nav lock-in + JSX-structural Write. (#48–#51)
- **v1.8.0** — Express mode + symptom-reproduction gate + monorepo artifact-root + RLS effective-access. (#44–#47)
- **v1.7.0** — Pivot-chain detection + PDAAV + source-walk template. (#37–#43)
- **v1.6.0** — Subagent reality-check + post-migration ground-truth + `generation_strategy:` + `verification_class: interactive` + runtime-error provenance. (#32–#36)
- **v1.5.0** — `TodoWrite` reset + W0 prescan quality gate + `standing_instructions:` + multi-Edit atomicity. (#28–#31)
- **v1.4.0** — Same-session pivot detection + `## Reference render structure` + `## Verification recipe` + W3 pre-execution gates. (#25–#27)
- **v1.3.0** — §W3 stale-override sweep + §5.8 post-closure tweak detection + grep-before-default-change. (#23, #24)
- **v1.2.0** — Visual alignment extraction + layout direction (LTR/RTL). (#22)
- **v1.1.0** — Browser verification recipe + SSR-hydration hazard + W4-discovered phases. (#20, #21)
- **v1.0.0** — Initial: two modes (AUDIT/BUILD) + EXTENSION + 4-wave structure + 3 cadences + 3-tier model assignment + 19 initial failure modes.
