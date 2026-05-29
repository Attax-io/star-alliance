# Version history — conquering-campaign

Semver: **MAJOR** = paradigm shift / artifact-layout change · **MINOR** = new section / discipline / failure-mode class · **PATCH** = clarification, enum value, sub-pattern, checklist of existing prose. Newest first.

---

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
