---
type: Document
title: Analyze Gate — the cross-artifact findings report
description: Spec-driven-development /analyze artifact — a severity-tagged findings table, a requirement→task coverage table, and a metrics block, produced read-only across spec/plan/tasks before /implement.
timestamp: 2026-06-28T00:00:00Z
---

# /analyze — the concrete artifact the gate emits

The Analyze gate is no longer just "eyeball the three files." It runs a structured,
**strictly read-only** cross-artifact pass over `spec.md`, `plan.md`, and `tasks.md` and
emits a concrete report: a severity-tagged findings table, a requirement→task coverage
table, and a metrics block. Run it only after `/tasks` produced a complete `tasks.md`.

> Adapted from GitHub Spec Kit's `analyze.md`. Read-only: it never modifies a file. It may
> *offer* a remediation plan, but the user must explicitly approve before any edit.

## Build semantic models (do not echo raw artifacts)

- **Requirements inventory** — for each FR-### and SC-###, a stable key (use the explicit
  FR-/SC- id; optionally a readable imperative slug). Include only SC items needing buildable
  work (load-test infra, security tooling); exclude post-launch KPIs ("reduce tickets 50%").
- **User story / action inventory** — discrete user actions with their acceptance criteria.
- **Task coverage mapping** — map each task to one or more requirements/stories by explicit id
  reference or keyword.
- **Constitution rule set** — principle names and MUST/SHOULD statements (CLAUDE.md).

## Detection passes (high-signal; cap 50 findings, summarize overflow)

- **A. Duplication** — near-duplicate requirements; mark the weaker phrasing to consolidate.
- **B. Ambiguity** — vague adjectives (fast, scalable, secure, intuitive, robust) lacking a
  measurable criterion; unresolved placeholders (TODO, TKTK, ???, `[NEEDS CLARIFICATION]`).
- **C. Underspecification** — verbs missing an object/measurable outcome; stories without
  acceptance criteria; tasks referencing files/components not defined in spec or plan.
- **D. Constitution alignment** — any requirement/plan element conflicting with a MUST; missing
  mandated sections or quality gates.
- **E. Coverage gaps** — requirements with zero tasks; tasks with no mapped requirement;
  buildable SC (perf/security/availability) not reflected in tasks.
- **F. Inconsistency** — terminology drift; data entities in plan but absent in spec (or vice
  versa); task-ordering contradictions; directly conflicting requirements.

## Severity

- **CRITICAL** — violates a constitution MUST, missing core spec artifact, or zero-coverage
  requirement that blocks baseline functionality.
- **HIGH** — duplicate/conflicting requirement, ambiguous security/performance attribute,
  untestable acceptance criterion.
- **MEDIUM** — terminology drift, missing non-functional task coverage, underspecified edge case.
- **LOW** — wording improvements, minor redundancy not affecting execution order.

## The artifact (emit, no file writes)

### Specification Analysis Report

| ID | Category | Severity | Location(s) | Summary | Recommendation |
|----|----------|----------|-------------|---------|----------------|
| A1 | Duplication | HIGH | spec.md:L120-134 | Two near-identical requirements | Merge; keep the clearer one |

(One row per finding; stable IDs prefixed by category initial — A/B/C/D/E/F. Max 50 rows;
aggregate the remainder in an overflow line.)

### Coverage Summary

| Requirement Key | Has Task? | Task IDs | Notes |
|-----------------|-----------|----------|-------|
| FR-001 | yes | T010, T011 | |
| FR-007 | no | — | no task covers this |

**Constitution Alignment Issues:** (list, if any)

**Unmapped Tasks:** (tasks with no requirement, if any)

### Metrics

- Total Requirements
- Total Tasks
- Coverage % (requirements with ≥1 task)
- Ambiguity Count
- Duplication Count
- Critical Issues Count

## Next actions

- CRITICAL present → resolve before `/implement`.
- Only LOW/MEDIUM → may proceed; offer improvement suggestions.
- Suggest explicit follow-ups (re-run `/specify` with refinement, adjust the plan, or hand-edit
  `tasks.md` to add the missing coverage). Then ask whether to draft concrete remediation edits
  for the top N issues — **never apply them automatically.**

## Guardrails

- NEVER modify files (read-only). NEVER hallucinate a missing section — report it accurately.
- Constitution violations are always CRITICAL. Cite specific instances over generic patterns.
- Report zero issues gracefully — emit the success report with coverage statistics.
- Deterministic: re-running with no changes yields the same IDs and counts.
