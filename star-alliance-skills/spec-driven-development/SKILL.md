---
name: spec-driven-development
description: "The Architect's discipline for building from an executable specification instead of vibe-coding — the spec→plan→tasks→implement→converge pipeline distilled from GitHub Spec Kit. Write WHAT/WHY first (a testable spec, no tech stack), gate it against a checklist (unit tests for the requirements writing, not the code), derive a HOW plan checked against the constitution (CLAUDE.md), slice into independently-testable user-story tasks (P1=MVP), analyze the artifacts for coverage/drift, implement story-by-story on checkpoints, then converge the built code back against spec/plan/tasks and append any remaining work. Every phase is a gate: unresolved clarifications or a failed constitution check stops the line. Use to plan a feature before code, stop vibe-coding, or structure a multi-surface build. Triggers: 'spec this out', 'spec-driven', 'write a spec first', 'plan before we build', 'turn this into a spec', 'break this into tasks', 'what's the MVP slice', 'converge the code', 'reconcile what we built'. Differentiate from conquering-campaign (multi-wave execution engine — this is the planning discipline it runs on), ultra-brainstorming (model-ensemble fan-out), and schema-evolution (one additive data-model change)."
metadata:
  version: 1.1.0
type: Skill

---
# Spec-Driven Development — the Architect's discipline

Code was king for decades; the spec was scaffolding thrown away once the "real work" began.
Spec-Driven Development flips it: **the specification is the source of truth, and the
implementation flows from it.** You do not start typing code. You write down WHAT the user
needs and WHY, prove it is testable and unambiguous, derive HOW from it, slice the HOW into
independently-shippable tasks, and only then build — one verifiable slice at a time.

Distilled from GitHub's Spec Kit. The CLI is theirs; the discipline is now yours.

## The pipeline

```
constitution → /specify → /clarify → /plan → /tasks → /analyze → /implement → /converge
   (once)        WHAT       fill gaps    HOW     slices   audit     build      reconcile
```

Each arrow is a **gate**. You do not cross it until the prior artifact passes its checklist.

1. **Constitution** (set once per project) — the non-negotiable principles every plan is
   checked against. **In this guild the constitution already exists: `CLAUDE.md` + guild
   conduct.** Do not author a second one; treat CLAUDE.md as the governing law a plan must
   not violate. (`references/constitution-template.md` is the shape, for non-guild repos.)

2. **Specify** — turn the natural-language ask into `spec.md`: prioritized user stories
   (P1=MVP), testable functional requirements, measurable + technology-agnostic success
   criteria, key entities, edge cases. **Focus on WHAT and WHY — never HOW.** No tech stack,
   no APIs, no code structure. Written for a stakeholder, not a developer.
   → `references/spec-template.md`

3. **Clarify** — resolve ambiguity. Mark unknowns inline as `[NEEDS CLARIFICATION: question]`,
   **max 3**, prioritized scope > security/privacy > UX > technical detail. Present each as an
   options table (A/B/C/Custom + implications) and wait for the answer. Everything else: make
   an informed guess and record it in an **Assumptions** section. A spec with unresolved
   markers does not advance.

4. **Plan** — derive `plan.md`: the technical context (language, deps, storage, testing,
   target, scale), the project structure, and the approach. **Constitution Check is a hard
   gate** — re-run it after design. Any violation goes in a Complexity Tracking table with a
   justification and the simpler alternative you rejected, or you simplify until it passes.
   → `references/plan-template.md`

5. **Tasks** — break the plan into `tasks.md`, **grouped by user story** so each story is
   independently implementable, testable, and deliverable. Mark `[P]` for tasks that can run
   in parallel (different files, no shared dependency). Order: Setup → Foundational (blocks
   all stories) → US1 (MVP) → US2 → US3 → Polish. Models before services before endpoints.
   → `references/tasks-template.md`

6. **Analyze** — cross-artifact consistency audit before building, and it emits a **concrete
   artifact** (strictly read-only — never edits a file): a severity-tagged findings table
   (CRITICAL/HIGH/MEDIUM/LOW, capped at 50 rows), a requirement→task **coverage table**, and a
   **metrics block** (Total Requirements, Total Tasks, Coverage %, Ambiguity Count, Duplication
   Count, Critical Issues Count). Does every requirement map to a task? Every task trace to a
   requirement? Any contradiction across spec/plan/tasks? Fix drift here, on paper, where it is
   cheap. → `references/analyze-report.md`

7. **Implement** — execute tasks in dependency order. **Stop at each checkpoint** (end of each
   user story) and validate that story independently before moving on. MVP-first: ship US1,
   prove it, then layer US2/US3 — each adds value without breaking the last.

8. **Converge** (after Implement) — post-implement reconciliation: assess the **built code**
   against spec/plan/tasks, classify each gap as `missing` / `partial` / `contradicts` /
   `unrequested`, and **append** severity-ordered, traceable tasks to `tasks.md`
   (`- [ ] T### … per <source-ref> (<gap-type>)`) under a new `## Phase N: Convergence` —
   **APPEND-ONLY, never rewrite** an existing task — or report **"Converged."** when the code
   already satisfies everything (leaving `tasks.md` byte-for-byte unchanged). Distinct from
   /analyze: /analyze is paper-only (artifacts vs each other); /converge is code-vs-artifacts.
   Re-run /implement on the appended tasks, then /converge again until converged.
   → `references/converge-stage.md`

## The quality gates (why this beats vibe-coding)

- **Spec gate** — testable, unambiguous, no implementation leak, success criteria measurable
  and technology-agnostic, scope bounded, ≤3 clarifications. (`references/checklist-template.md`)
- **Plan gate** — passes the Constitution Check (CLAUDE.md) both before and after design;
  violations justified or removed.
- **Task gate** — every story independently testable; no cross-story dependency that breaks
  independence; no two `[P]` tasks touching the same file.
- **Analyze gate** — full requirement↔task traceability, zero contradictions across artifacts.
  Emits the concrete artifact: severity-tagged findings table + coverage table + metrics block
  (Coverage %, Ambiguity/Duplication/Critical counts). (`references/analyze-report.md`)
- **Converge gate** — after build, every gap between code and spec/plan/tasks is classified and
  appended as a traceable task, or the result is a clean "Converged." (`references/converge-stage.md`)

A vague requirement should **fail** the "testable and unambiguous" item. That failure is the
point — catch it on paper, not in code.

### Checklists are "unit tests for English"

A checklist validates the **requirements writing**, not the implementation. It tests whether
each requirement is complete, clear, consistent, measurable, and covers its scenarios — never
whether the code works. **Ban** items that start with *Verify / Test / Confirm / Check* + a
behavior ("Verify the button clicks") — those are QA steps, not requirement tests. Write
quality questions instead ("Is 'prominent display' quantified? [Clarity, Spec §FR-004]"), tag
each with `[Gap]` / `[Ambiguity]` / `[Conflict]`, number them `CHK###`, and keep **≥80%** of
items traceable to a spec section or marker. → `references/checklist-unit-tests-for-english.md`

## Success criteria: measurable + technology-agnostic

| Good (user-facing, measurable) | Bad (implementation-focused) |
|---|---|
| "Users complete checkout in under 3 minutes" | "API response time under 200ms" |
| "95% of searches return in under 1 second" | "Redis cache hit rate above 80%" |
| "System supports 10,000 concurrent users" | "React components render efficiently" |

Write the left column. The right column belongs in the plan, not the spec.

## How you work (guild form)

1. **Constitution is CLAUDE.md.** Read it; every plan is checked against it. Do not create a
   second constitution file in this repo.
2. **Spec first, always.** For any non-trivial feature, write `spec.md` before touching code.
   WHAT/WHY only. Store feature artifacts under `specs/<NNN>-<short-name>/`.
3. **Gate, don't gallop.** Run each phase's checklist before advancing. Unresolved
   `[NEEDS CLARIFICATION]` (max 3) or a failed Constitution Check stops the line.
4. **Draw your doer.** Per `weapon-utility`, hand the bulk drafting of spec/plan/tasks to a
   doer (minimax-m3 first): plan the structure → prompt the doer with the template → review
   the draft against the gate → re-prompt until it conforms. The thinker holds the gate.
5. **Slice to MVP.** Tasks grouped by user story, P1 is the smallest viable slice. Ship and
   validate US1 before US2.
6. **Implement on checkpoints.** Stop after each story, prove it independently, then continue.
7. **Converge to close.** After implement, reconcile the built code against spec/plan/tasks;
   append remaining work as traceable tasks (append-only) and re-implement until "Converged."

## What it is / is not

- It IS: the planning-and-slicing discipline — spec → plan → tasks → implement, each gated.
- It is NOT: `conquering-campaign` — that is the multi-wave *execution* engine. This is the
  planning method a campaign can run on; pair them (spec/plan/tasks → campaign waves).
- It is NOT: `ultra-brainstorming` — that fans one decision across thinker models. This is a
  sequential, gated pipeline. Use ultra-brainstorm *inside* the plan phase when a design
  choice is contested.
- It is NOT: `schema-evolution` — that is one additive data-model change. This frames an
  entire feature.
- It is NOT: a CLI install. Do not vendor GitHub Spec Kit's Python `specify` tool; the method
  lives in this skill and its templates.

## Pairs with

`ultra-brainstorming` (contested design inside /plan) · `conquering-campaign` (execution engine
for the resulting tasks) · `schema-evolution` (when the plan adds a data-model field) ·
`graphify` (visualize the plan's structure) · `weapon-utility` (doer dispatch for drafting).

---

Own skill. Bump `metadata.version` on any change (PATCH: wording/refs · MINOR: new section/template ·
MAJOR: method contract change). Regenerate `VERSIONS.md` with
`python3 star-alliance-skills/skillsmith/scripts/skill_registry.py write` after a bump, then
`python3 build.py`.
