---
type: Document
title: Converge Stage — post-implement reconciliation
description: Spec-driven-development /converge stage — assess built code against spec/plan/tasks, classify each gap, and append severity-ordered traceable tasks to tasks.md (append-only). Distinct from /analyze, which is paper-only.
timestamp: 2026-06-28T00:00:00Z
---

# /converge — close the gap between the spec and the built code

`/converge` runs **after `/implement`**. Where `/analyze` audits the three artifacts on
paper (spec vs plan vs tasks, no code), `/converge` audits the **built code against those
artifacts** and appends any remaining unbuilt work back into `tasks.md` so a follow-up
`/implement` pass can finish it. It is post-implement reconciliation, not a paper review.

> Adapted from GitHub Spec Kit's `converge.md`. The discipline is yours; the loop is the same.

## When to run

Only after `/implement` has run against the current `tasks.md`, and after `/tasks` produced a
complete `tasks.md`. If `spec.md`, `plan.md`, or `tasks.md` is missing, STOP and name the
prerequisite stage to run (`/specify`, `/plan`, or `/tasks`).

This is **not** a diff tool and does **not** track git history. It assesses the *present
state* of the code relative to the feature's artifacts — no branch comparison, no history.

## Operating constraint — APPEND-ONLY, NEVER REWRITE

The stage's **only** write is appending a new `## Phase N: Convergence` section to the end of
`tasks.md`. It MUST NOT:

- modify `spec.md` or `plan.md` in any way;
- rewrite, renumber, reorder, or delete any existing task (including tasks from a prior
  Convergence phase) — a new Convergence phase is added *below* an old one, never on top of it;
- modify, create, or delete any application code — completing the appended tasks is the job
  of `/implement`.

When the codebase already satisfies everything, leave `tasks.md` **byte-for-byte unchanged**
(no empty Convergence header) and report the converged result.

The constitution (CLAUDE.md + guild conduct) is non-negotiable: code that violates a MUST
principle is the highest-severity finding and produces a CRITICAL remediation task.

## Execution

### 1. Load artifacts (progressive disclosure)

- **spec.md**: Functional Requirements (FR-###); Success Criteria (SC-###) that require
  buildable work (exclude post-launch outcome metrics / business KPIs); user stories and their
  acceptance scenarios; edge cases.
- **plan.md**: architecture/stack decisions; data-model references; phases and named
  touch-points (files/components the plan says will be created or edited); technical constraints.
- **tasks.md**: task IDs (to compute the next ID and next phase number), descriptions, phase
  grouping, referenced file paths.
- **constitution** (CLAUDE.md): MUST/SHOULD normative statements.

### 2. Build the intent inventory

- **Requirements inventory**: one stable key per FR-### / SC-### / acceptance scenario (e.g.
  `US1/AC2`), plus plan decisions and constitution principles that impose buildable obligations.
- **Code-scope map**: from the file paths named in `plan.md` and `tasks.md` plus a keyword
  search for each requirement's concept, derive the set of source files in scope. Bound the
  assessment to these — do **not** infer scope beyond what the artifacts define.

### 3. Assess the code and classify each gap

Inspect the in-scope code for each inventory item; emit a `Finding` **only where there is a
gap**. Classify every finding by **gap type**:

- **`missing`** — the required work is absent from the code entirely.
- **`partial`** — the work exists but does not yet fully satisfy the requirement / acceptance
  criterion / plan decision.
- **`contradicts`** — the code does something that conflicts with stated intent or a
  constitution MUST principle.
- **`unrequested`** — the code contains work not called for by the spec, plan, or tasks
  (surfaced for awareness; converge does not delete code — it appends a task to review/justify
  or remove it).

Edge cases: **little or no code yet** → treat the entire specified scope as `missing`
remaining work rather than failing. **Nothing remains** → zero findings, follow the converged
branch below.

### 4. Assign severity

- **CRITICAL** — violates a constitution MUST, or a `missing`/`contradicts` gap that blocks
  baseline functionality of a P1 user story.
- **HIGH** — a `missing`/`partial` gap on a core functional requirement or acceptance criterion.
- **MEDIUM** — a `partial` gap on a secondary requirement, or an `unrequested` addition with
  unclear justification.
- **LOW** — minor partial gaps, polish, or low-risk `unrequested` additions.

### 5. Present the in-session findings summary (no writes yet)

## Convergence Findings

| ID | Gap Type | Severity | Source | Evidence | Remaining Work |
|----|----------|----------|--------|----------|----------------|
| F1 | missing  | HIGH     | FR-008 | No append-only guard in path/to/module when writing tasks.md | Add append-only enforcement |

**Summary metrics:** requirements/acceptance criteria checked · plan decisions checked ·
constitution principles checked (or "skipped — template") · findings by gap type
(missing / partial / contradicts / unrequested) · findings by severity.

### 6. Append convergence tasks (or report converged)

**If there are one or more actionable findings** (`tasks_appended`):

1. Scan all existing task IDs; let `M` be the maximum. Determine the next phase number `N`
   (highest existing phase + 1).
2. Write a single new header `## Phase N: Convergence`.
3. Emit one checklist item per finding, **ordered CRITICAL/HIGH first**, with zero-padded IDs
   `T{M+1:03d}, T{M+2:03d}, …`:

   ```markdown
   - [ ] T042 <imperative description> per <source-ref> (<gap-type>)
   ```

   `<source-ref>` traces the task to its origin: e.g. `FR-003`, `SC-002`, `US1/AC2`,
   `plan: storage decision`, `Constitution II`. `<gap-type>` is one of `missing`, `partial`,
   `contradicts`, `unrequested`. Constitution-violation tasks are emitted first and described
   as CRITICAL.
4. Never reuse or renumber existing IDs. A prior Convergence phase is left untouched; a new,
   separately-numbered phase is added below it.

**If there are no actionable findings** (`converged`):

- Do **not** modify `tasks.md` at all — no empty phase header.
- Report: **"Converged — the implementation satisfies the spec, plan, and tasks."**
- Include the summary counts of what was checked.

### 7. Handoff

- On `tasks_appended`: state how many tasks were appended under which phase and recommend
  running `/implement` to complete them; note a follow-up `/converge` will then find fewer or
  no remaining items.
- On `converged`: recommend proceeding to review / opening a PR. No further `/implement` pass is
  needed for this feature's specified scope.

## /converge vs /analyze

| | `/analyze` | `/converge` |
|---|---|---|
| When | after `/tasks`, before `/implement` | after `/implement` |
| Reads | spec + plan + tasks (paper only) | the **built code** vs spec/plan/tasks |
| Output | read-only findings report (no writes) | **appends** Convergence tasks to tasks.md |
| Question | "do the artifacts agree?" | "does the code match the artifacts?" |
