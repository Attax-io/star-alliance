# Conquering-campaign over-invocation — reflection input (2026-06-02)

> **Status: SHIPPED as v3.7.0 (2026-06-02).** Lessons + route mined from the last ~3 days of sessions
> + the on-disk campaign folder corpus. Trigger: Atta — "we have used conquering campaign too much
> lately." Now wired into SKILL.md as **Gate G0** + `micro`-retired + precedence row 6b + the multiplier
> scope-gate + the self-health sprawl metric + failure modes #101/#102. This session deliberately did
> NOT open a campaign to produce this (correct — read-only + a few notes files, exactly the bar the fix defends).
>
> **⚠ CORRECTION (same session, an #32 instance).** An earlier draft of the scope statistic below
> read "0/116 plans declare `scope:`." That zero was a measurement artifact — a zsh `for f in
> */00-plan.md …` glob hit `no matches found` and aborted the mining loop before it read a file.
> Re-verified with `grep -l '^scope:'`: **84/116 (72%) DO declare scope** (104/153 across all roots).
> The scope rows below are corrected; the thin-folder / over-invocation evidence (#101) was measured
> independently and stands. #102 was reframed from "discipline dead" to "incompletely enforced +
> sizing ≠ gating." Also: the raw folder total is **161** (pruned of `node_modules` + #95 worktree
> copies — an unpruned `*-campaigns` find triple-counts to 539); the lex build root holds 123.

---

## Plain-English summary

The skill fires for work that is too small to deserve a campaign. The machinery that is *supposed*
to stop this already exists — but it is soft-worded ("offer a lighter pass"), buried below the mode
table, and only read *after* the skill has already committed to running. So every little fix gets the
full campaign ceremony: a dated folder, frontmatter, waves, a `/goal` line, a risk-sweep, a vault-log,
and an auto-spawned `/cleanup` follow-up session. The result is folder sprawl and double-handling
(a color fix became a campaign that then spawned a `/cleanup` color session — the same work twice).
The fix is the skill's *own* proven meta-lesson turned on its last un-gated boundary: a buried rule
fires as a user correction, so **front-load the "is this even a campaign?" check into a real
pre-flight gate (G0) with an EXIT verdict** — don't add more prose.

---

## Evidence (on-disk corpus, 2026-06-02)

| Metric | Value | Reading |
|---|---|---|
| Total campaign folders (build + audit) | **136** (123 build + 13 audit) | v3.0.0 mined "136 campaigns" on 2026-05-29 — i.e. the baseline was already inflated; the reflex is the norm, not the exception |
| Build folders with **≤3 files** | **91 / 123 (74%)** | a real multi-wave BUILD = plan + per-phase + `99-risk-sweep` ≥4 files. 74% never produced the full artifact set → sub-campaign work in campaign clothes |
| Build folders with exactly **1 file** | many (`drop-gfn-linking-columns`, `user-prefs-drop-language`, `customer-gfn-access-table`, `member-filter-per-role`, `auto-contract-on-fee-invoice`, …) | single-migration / single-view jobs. Textbook over-invocation |
| Build plans recording **`scope:` frontmatter** | **84 / 116 (72%)** ✏️corrected | declared in the *majority* — so NOT "dead" (the 0/116 was a glob-abort artifact). The real gap (#102): ~28% omit it, and a declared scope only *sizes* a campaign — it never asks whether to open one |
| Build plans that **never reached `status: completed`** | **22 / 116 (19%)** | abandoned ceremony — pollutes the §0.0 resume-scan + the lesson-mine |
| Build folders with **no `00-campaign-plan.md` at all** | **7** | empty/skeleton-less folders — the §0.0 "empty folder = planning failure" smell, at volume |
| Campaigns in the **last ~3 days** | wages-tax-calculator · dark-mode-color-fix · user-manual-authoring · financial-model-build · postgres-security-perf · unified-point-ledger · auto-credit-limit | ~2.5/day for a one-maintainer app = "too much lately" confirmed |

**Cleanest single example.** `2026-06-02_dark-mode-color-fix` ran as a conquering-campaign, then
auto-spawned a *"Run /cleanup for dark-mode color fix campaign"* session (§5.7 / v3.3.0). Color fixes
are a first-class `/cleanup` mode. The campaign did the work, then spawned a second skill to do the
same class of work — the over-invocation **multiplier** in one screenshot.

**Counter-evidence (kept honest).** The session list shows lots of small work handled correctly as
plain sessions — form bugs, container bugs, styling, dev-server — that did NOT become campaigns. So
the trigger is not *universally* over-firing; the failure is concentrated where a phrase like "ship
this refactor" / "proceed in application" / "build this feature" matches a 1–2-surface job, or where
`/conquering-campaign` is typed reflexively.

---

## Lessons — why the existing guardrails fail (root cause)

The skill already has THREE things that should prevent this. All three fail for the **same structural
reason** the Pre-flight-gates block itself names: *a rule that isn't reached at the decision moment
fires as a user correction.*

1. **§Two modes, line 66** — "If the user wants a quick one-file check or single bug fix, this skill
   is overkill — say so and offer a lighter pass." Soft verb (**offer**, not **exit**), buried at the
   bottom of the mode section, and read only *after* the skill is already running. It is prose, not a
   gate.
2. **Scope decision tree (§Step 2)** — has a `micro` tier, but `micro` still produces *a campaign*
   (just trims artifacts). `scope:` IS declared in ~72% of plans (corrected — see banner), so the tree
   is mostly applied; the real flaw is that a declared scope only *sizes* a campaign and never asks
   whether to open one. `micro` is self-defeating: "files ≤2 ∧ lines ≤10 ∧ no new files ∧ no migrations
   → no plan file, conversation IS the plan" describes something that **should not be a campaign at all**.
3. **Trigger-phrase precedence (§326)** — 9 rows, *all* of which assume a campaign is happening. The
   lowest-precedence default (row 9) is "Standard planning interrogation" = run a campaign. **There is
   no EXIT row.** The table cannot bounce a request out of the skill.

**Root cause:** every existing gate (G1–G6) governs *how to execute well* — none governs *whether to
run a campaign at all*. The skill's self-image is "I'm already the right tool; now plan." The one
boundary that never got front-loaded into a gate is the over-invocation boundary.

**Second-order cost (what Atta feels):** folder sprawl + the auto-spawn multiplier. Every campaign —
regardless of size — emits a `/goal` line, emits Workflow scripts, writes a risk-sweep, and spawns a
`/cleanup` follow-up. An over-invoked small campaign therefore multiplies into *more* sessions and
*more* docs. Overuse compounds.

---

## Proposed skill upgrade route — v3.7.0 (MINOR)

Honest framing (per the v3.5.0 discipline): the machinery is **70% present**. This is a front-load +
harden + measure, not new paradigm. Mirrors how v3.0.0 fixed its top-2 failures ("already codified but
buried — front-loading + cutting bulk is the cure, not more prose").

1. **New Gate G0 — Campaign-worthiness triage (the FIRST gate, runs before Step 0).** A 30-second
   classifier with a hard **EXIT verdict**, not a soft offer:
   - Count surfaces, migrations, new public APIs, forced gates, est. files.
   - If it does NOT clear the BUILD bar (≥3 real surfaces / genuinely multi-phase / must-stay-deployable
     staging) OR the AUDIT bar (real doc↔reality reconciliation across the app) → **EXIT**: state plainly
     "this is a {direct edit | `/cleanup <mode>` | single bug fix}, not a campaign," route to the lighter
     tool, and create **no** folder / frontmatter / `/goal` / spawn. Override only on explicit user insist.
   - Specifically route: color/contrast/dark-mode → `/cleanup` (colors/lint); i18n → `/cleanup language`;
     postgres health/advisors → `/cleanup postgres`; lint/tsc → `/cleanup lint`; single migration/view
     with no FE fan-out → direct edit under P3 show-SQL; one-file bug → `bug-fix` or just fix it.
2. **Retire `micro` from the campaign ladder — fold it into the G0 EXIT.** `micro` = "not a campaign,"
   by definition. The micro row's only non-waivable keeps (tsc+lint, §5.3 vault-log) are project rules
   that already apply to *any* edit, campaign or not — they survive the exit.
3. **Trigger-precedence table gets a row 0 (EXIT) + a size qualifier on the broad phrases.** Highest
   precedence: "Request fails the G0 bar → decline + route, don't plan." Tighten the description's
   over-matching phrases ("ship this refactor", "proceed in application") with `(≥3 surfaces / multi-phase
   / migration-bearing)`.
4. **`scope:` becomes a measured invariant.** §Skill self-health gains a sprawl check it reports at
   every reflection pass: `% folders missing scope:`, `% never-completed`, `% ≤3-file`, `% no-plan`.
   Drift becomes visible so the skill self-corrects over time. (Baseline 2026-06-02, pruned: 161 folders / 115 thin (71%) / 49-of-153 plans missing scope.)
5. **Scope-gate the auto-spawn multiplier.** §5.7 `/cleanup` spawn + `/goal` emit + Workflow emit fire
   only for scope ≥ **medium**. A `small`/`bug-fix` job that slipped past G0 doesn't spawn a session.
6. **New failure modes:**
   - **#101 — Campaign over-invocation / ceremony-inflation.** Symptom: a dated folder + waves + spawn
     created for ≤small work. Evidence: 74% ≤3-file folders, 0 scope declarations, color-fix → spawned
     color-cleanup. Cure: G0 EXIT + micro-folds-into-exit + precedence row 0 + scope-gated auto-spawn.
   - **#102 — scope-declaration incompletely enforced + sizing ≠ gating.** ~28% of plans omit `scope:`
     (NOT 0% — that was a glob-abort artifact; true rate 72%), and even a declared scope only *sizes* a
     campaign, never asks whether to open one. The declaration gate (#54) operates inside "this IS a
     campaign." Cure: G0 gates the run; self-health sprawl metric (#4) pushes declaration → 100%.

**Why MINOR:** new G0 gate + 2 failure-mode classes + 1 precedence row + 1 self-health metric.
Backward-compatible — every wave, pattern, cadence, and frontmatter field stays valid; a genuine
campaign behaves identically. The only behavior change is that sub-campaign work now exits instead of
spinning ceremony.

**Files the v3.7.0 edit would touch:** `SKILL.md` (G0 block + line-66 promotion + precedence row 0 +
description-phrase qualifier + §5.7 scope-gate + §Skill self-health metric + retire `micro` row) ·
`references/failure-modes.md` (#101, #102) · `references/version-history.md` (v3.7.0 entry) · the 2
sync copies (anthropic-skills + star-alliance) per §Deploy.
