# Conquering-campaign reflection — lessons + upgrade route (2026-06-04)

> **Status: PROPOSED (not yet applied).** Mined from the latest sessions (2026-06-02 → 06-04),
> the on-disk campaign corpus, and the post-v3.7.1 campaign artifacts. Trigger: Atta — "from all
> the latest sessions, note down the lessons and route for upgrading the conquering campaign skill."
> This session did NOT open a campaign to produce it (correct — read-only reflection + one notes
> file, exactly the bar G0 defends; mirrors the `OVERUSE-ANALYSIS-2026-06-02.md` precedent).
>
> Two buckets: **META** (the skill auditing itself — did v3.7.0's G0 actually work?) and
> **EXECUTION** (new field lessons the live skill doesn't yet capture).

---

## Plain-English summary

v3.7.0 (2026-06-02) added Gate **G0** to stop the skill firing for work too small to deserve a
campaign. Measured two days later: **G0 is not firing.** A one-file bug fix (`bug253`) got a full
campaign folder on 06-04; fifty-three folders across the corpus declare themselves `medium`/`full`
while holding one or two files. The thin-folder ratio is dead flat at 71%, and the corpus actually
*grew* +19 folders in those two days. Root cause is the skill's own proven meta-lesson, recursive: **G0 is
still prose the agent must self-reach at t=0 — and the over-invocation decision is made the instant
a trigger phrase matches, before any in-skill gate is read.** A gate inside the skill cannot bounce
a request that already loaded the skill. The cure is not a better-worded gate; it is to intercept
*before* the skill commits — tighten the trigger description so it under-matches, and/or add a
mechanical folder-creation guard. Separately, six real execution lessons surfaced (RLS impersonation
proof, anon-RPC public reads, dormant-gate hazard, RTL transform trap, preview-is-dead-not-flaky,
id-type-agnostic bulk primitives) that belong in the playbooks.

---

## META — did G0 work? (measured 2026-06-04, post-ship corpus)

Sprawl metric now vs the v3.7.0 baseline (both **all roots, pruned, from project root** — an earlier
156 read was a lex-submodule-cwd undercount; trusting it was itself the #32 trap, corrected here):

| Metric | Baseline 06-02 | Now 06-04 | Reading |
|---|---|---|---|
| campaign-folders (all roots, pruned) | 161 | **180** | **+19 in 2 days** — over-invocation *continued* right through the G0-prose period |
| thin (≤3 files) | 115 / 71% | 127 / **71%** | **dead flat** — G0-as-prose did not move the needle at all |
| plans missing `scope:` | 49 | 49 | unchanged |
| **scope-INFLATED** (≤2 files, tier ≥ medium) | (not measured) | **53** | the dominant pathology the presence-only metric was *blind* to — agents write a higher tier to pass the declaration gate |
| loose `.md` / off-enum `status:` | (not measured) | 1 / 20 | malformed artifacts (M4) |

**M1 — G0 EXIT verdict is not honored, even by careful runs.** `2026-06-04_bug253-file-owner-reassignment/`
is a single-file bug fix with a folder, dated **two days after G0 shipped**. Its frontmatter is
*excellent* (flags an `[!atta]` conflict, records `mcp_status`, emits no `/goal` per the scope-gate) —
the agent reasoned well and *still* opened a campaign. So this is not a sloppiness failure; it is a
classification failure: the request matched a campaign trigger at t=0, the skill loaded, and once
loaded, G0 (an in-skill prose gate) had already lost — the skill's self-image is "I'm the right tool,
now plan." Other post-ship suspects: `attachments-sort-card` (2 files), `portal-scrollbar-alignment`
(2 files — a `/cleanup` or direct edit), `attachments-access-tab` (1 file), `financial-model-fe-tail`
(2 files — a §5.8 post-closure tweak, not a fresh folder).

**M2 — scope-inflation defeats the self-health metric.** The v3.7.0 metric counts plans *missing*
`scope:`. It does not catch a plan declaring the *wrong* tier. **53 folders across all roots** declare
`medium`/`full` while holding ≤2 files (the 13 lex-build ones created since 06-02 shown here):

```
manual-in-app-editor(2,full) notification-log-into-devtools(2,med) points-ledger-tab(2,med)
security-fixes(2,full) senior-attorney-file-admin(1,full) softdelete-flag-wiring(2,med)
user-manual-authoring(2,full) wages-tax-calculator(2,med) attachments-access-tab(1,med)
attachments-sort-card(2,med) doc-version-merge(2,med) financial-model-fe-tail(2,med)
portal-scrollbar-alignment(2,med)
```

(Some — `manual-in-app-editor`, `user-manual-authoring` — are content-authoring where the deliverable
is the manual, not findings files, so a 2-file folder is legitimate. But `senior-attorney-file-admin`
= 1 file, `scope: full` is a clean mismatch: a "full" campaign whose only artifact is its plan.) The
missing-scope count is flat at 49 (all roots), but **scope-INFLATED=53** is the real story: agents now
*write* `scope: full` on one-file folders to satisfy the declaration gate — the problem migrated from
*missing* to *wrong*, and the old presence-only metric counted the wrong thing and called it progress.
**`scope:` is no longer a reliable size signal, so the metric reported false health.**

**M3 — the G0 bar over-counts vertical slices.** G0's bar is "≥3 real surfaces." But a single logical
bug fix naturally threads RPC + mutation + UI + i18n = reads as "4 surfaces" and auto-clears. `bug253`
is exactly this: one change, four layers, clears a surface-count gate. The bar must count
**independent logical changes**, not the layers one vertical slice passes through.

**M4 — malformed artifacts the self-health scan misses.** `2026-06-03_portfolio-audit.md` is a 21 KB
**loose file** directly under `build-campaigns/` (not a folder, and an *audit* living under the *build*
root). The sprawl scan iterates `*/` dirs and never sees loose files. Also `people-to-contacts-rename`
carries `status: blocked` — a value not in the declared enum (`planning→in-progress→completed|superseded`).

---

## EXECUTION — new field lessons (post-v3.7.1, not yet in the skill)

**E1 — RLS cross-tenant leaks: prove with impersonation, detect with `qual='true'`.**
(`2026-06-02_app-wide-security` audit — 7 Critical OPEN, report-only.) The money/access core was clean,
but report/counter/HR tables (`member_hr_records`, `advances_member_counters`, `folder_counts`,
`task_counts`, `org_calendar`) shipped `USING(true)` for `authenticated` → a customer reads every row.
Two reusable moves: (a) **cheap deterministic detector** — sweep `pg_policies WHERE qual='true'` on any
multi-tenant table granted to `authenticated`; (b) **both-direction proof** — the impersonation harness
(`SET LOCAL ROLE authenticated` + `set_config('request.jwt.claims', …)` inside a `BEGIN … ROLLBACK`,
pick a *discriminating* table). Policy *text* lies; only the harness proves effective access.
`10-rls-effective-access.md` is now the regression suite. Sharpens #47, which only flags the class.
→ named pattern (`RLS-IMPERSONATE`) + db-playbook procedure + a G3/G6 sub-step.
[[discovery_qual-true-rls-cross-tenant-leaks]] [[discovery_rls-impersonation-harness-mcp]]

**E2 — public/anon read surfaces MUST read through an anon-granted SECURITY DEFINER RPC, never a
`security_invoker` view.** (sitemap/insights, 06-02.) The sitemap silently emitted **0 article URLs**
because it queried a client-scoped `security_invoker` view as anon → base-table SELECT → `42501`. The
fix: a `SECURITY DEFINER` RPC granted to `anon` (`get_public_team`, `get_public_articles`). G6 today
only covers *authenticated* v2 objects — it has no rule for the public/anon read path, and the failure
is *silent* (empty result, not an error the build catches). → new G6 sub-rule + failure mode.
[[discovery_public-marketing-anon-rpc]] [[discovery_sitemap-anon-forbidden-view-insights-seo]]

**E3 — dormant-gate / dormant-tier hazard: a permission gate no current row satisfies is a silent
no-op, not a feature.** `admin_scope` = 1 for all 90 users, 0 for none → every `admin_scope=0` gate
admits nobody (wages-edit closed to *all*). The financial-model build shipped a "firm tier" that is
likewise dormant. Generalizes #92 (first-consumer dormant primitive). → §5/close-checklist probe:
when a BUILD ships a new gate / scope value / tier, **count the intended audience against live data
before declaring done**; a zero-audience gate ships as `CHK-` + an explicit "dormant until X" note.
[[discovery_admin-scope-global-tier-dormant]] [[discovery_financial-model-build-blockers]]

**E4 — RTL directional-transform trap.** (`2026-06-02_rtl-positioning-consolidation`.) A hand-rolled
`translateX(100%)` in a slide-over is *physical* — it does not flip under RTL, so an Arabic panel
sticks mid-screen. Canon: `lib/rtl.ts` helpers (`slideHiddenTransform`/`panelEdgeShadow`/
`physicalSlideEdge`) + `useIsRtl` + the `<SlideOverPanel>` shell; LTR stays byte-identical. A literal
`translateX(100%)` / `right: 0` in an edge panel is the smell. → fe-i18n conformity catalog (a G1
primitive) + anti-pattern row. [[discovery_rtl-slide-helper-canon]]

**E5 — the Supabase preview pipeline is *reliably* dead, not intermittently.** Re-confirmed 06-02: a
fresh branch comes up `MIGRATIONS_FAILED` **and dataless** — you cannot validate on it at all. Don't
burn time creating a branch to validate; the canonical substitute is a prod `BEGIN … ROLLBACK`
dry-run (paired with the E1 harness for RLS). Hardens #96 from "if the pipeline failed" to "assume
failed; the dry-run *is* the validation path." [[discovery_supabase-preview-branch-still-broken]]

**E6 (minor) — bulk-select primitives must be entity-id-type-agnostic.** `useBulkEntityActions<Id
extends string|number = number>` to cover uuid member ids; `MemberListRow` gained `selectable` with a
leading checkbox; watch `checked` ≠ `selected` (panel-open must not tick the box). Reinforces the
existing primitive-agnosticism rule; a one-line conformity note, not a new section.
[[discovery_person-domain-bulk-delete-pattern]] [[discovery_primitive-collection-agnosticism]]

---

## Proposed upgrade route

Ship in two version steps. The META fixes are the headline (v3.8.0 — they correct a *shipped gate that
didn't bite*); the EXECUTION lessons are an additive playbook PATCH (v3.8.1).

### v3.8.0 — MAKE G0 BITE (MINOR) — the headline

The honest read: G0 is the right idea executed in the wrong layer. A gate *inside* the skill cannot
bounce a request that already loaded the skill. Three moves, lightest-touch first:

1. **Tighten the description trigger so it under-matches (do first — zero-risk, no harness change).**
   The over-broad phrases ("ship this refactor", "build this feature", "proceed in application") match
   1–2-surface jobs. Qualify them inline in the `description:` frontmatter with the bar itself —
   `build this feature (≥3 independent surfaces / multi-phase / migration-bearing)` — so the *router*
   under-fires instead of the *gate* over-firing. This is the only change that acts before the skill
   loads.

2. **Redefine the G0 bar to count independent logical changes, not layers (M3).** Replace "≥3 real
   surfaces" with "≥3 *independent* changes (a single vertical slice — RPC+mutation+UI+i18n for one
   logical change — counts as ONE)." Add the worked `bug253` counter-example inline so the next run
   doesn't repeat it.

3. **Upgrade the self-health metric from presence to coherence (M2).** Stop counting *missing* `scope:`;
   count **scope-vs-reality mismatch** — a folder whose `scope:` tier outranks its file/surface count
   (`full`/`medium` with ≤2 files and no `generation_strategy: content`). Add a loose-file check (M4):
   flag any `*.md` sitting directly under a `*-campaigns/` root, and any `status:` value outside the
   enum. Refresh the baseline (all roots: 180 / 127 / missing-scope 49 / **INFLATED 53** / loose 1 /
   off-enum 20) and record the 06-02→06-04 *regression* honestly (+19 folders, thin% flat at 71%).

4. **`#103` — shipped gate didn't bite (the recursive meta-lesson).** Symptom: a gate added to fix a
   buried-rule failure is *itself* buried, so the failure persists. Evidence: G0 shipped 06-02, `bug253`
   folder 06-04, thin% flat. Cure: enforce at the layer *before* the decision (trigger description /
   router / hook), not with a deeper in-skill gate. Status: `active`.

5. **OPTIONAL (needs Atta's call) — mechanical folder-creation guard.** A `PreToolUse` hook (settings.json)
   on `Write`/`Bash mkdir` targeting `*-campaigns/*/00-campaign-plan.md` that prompts "G0: ≥3 independent
   surfaces? else EXIT." This is the *only* move that makes G0 unconditional — a hook the harness runs,
   not prose the agent must reach. It is a harness change, not a skill-doc change, so it is a separate
   decision (see the question to Atta).

### v3.8.1 — PLAYBOOK PATCH (the execution lessons) — additive, backward-compatible

| Lesson | Lands in | Form |
|---|---|---|
| E1 RLS impersonation proof + `qual='true'` detector | `db-playbook.md` + G3/G6 + §Named patterns | `RLS-IMPERSONATE` named pattern; #104 |
| E2 anon-RPC public reads (silent 42501) | G6 sub-rule + `db-playbook.md` | #105 |
| E3 dormant-gate audience probe | §5 close-checklist + G5 | generalize #92; #106 |
| E4 RTL transform trap | `fe-i18n-playbook.md` conformity catalog + anti-pattern row | #107 |
| E5 preview reliably-dead → dry-run is the path | `db-playbook.md` (harden #96) | edit #96 |
| E6 id-type-agnostic bulk primitive | §Conformity one-liner | no new # |

### Sequencing

1. v3.8.0 moves 1–4 (description + bar + metric + #103) — pure SKILL.md / references edits, ship now.
2. Ask Atta on move 5 (the hook) — highest leverage, but a harness change.
3. v3.8.1 playbook patch — fold E1–E6 into the two playbooks + 4 new failure modes (#104–#107) +
   harden #96.
4. Per §Deploy: sync both copies (anthropic-skills + star-alliance), `diff -rq`, bump
   `version-history.md`.

**Why this order:** moves 1–4 are zero-risk doc edits that correct a measured regression; move 5 is the
real fix but needs a decision; the playbook patch is independent and can ride after. The whole route is
backward-compatible — a genuine campaign behaves identically; only sub-bar work exits earlier and the
self-health metric stops lying.
