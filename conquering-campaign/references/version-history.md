# Version history — conquering-campaign

Semver: **MAJOR** = paradigm shift / artifact-layout change · **MINOR** = new section / discipline / failure-mode class · **PATCH** = clarification, enum value, sub-pattern, checklist of existing prose. Newest first.

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
