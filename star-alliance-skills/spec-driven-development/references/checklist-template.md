---
type: Document
title: Quality Checklist Template
description: Spec-driven-development quality gate checklists — spec content/completeness/readiness gates run before advancing a phase.
timestamp: 2026-06-27T00:00:00Z
---

# Quality Checklist: [FEATURE NAME]

**Purpose**: gate one phase before advancing to the next.
**Feature**: [link to spec.md]

## Spec Gate — Content Quality
- [ ] No implementation details (languages, frameworks, APIs)
- [ ] Focused on user value and business needs
- [ ] Written for non-technical stakeholders
- [ ] All mandatory sections completed

## Spec Gate — Requirement Completeness
- [ ] No [NEEDS CLARIFICATION] markers remain (≤3 were used)
- [ ] Requirements are testable and unambiguous
- [ ] Success criteria are measurable
- [ ] Success criteria are technology-agnostic
- [ ] All acceptance scenarios defined
- [ ] Edge cases identified
- [ ] Scope clearly bounded
- [ ] Dependencies and assumptions identified

## Spec Gate — Feature Readiness
- [ ] Every functional requirement has clear acceptance criteria
- [ ] User scenarios cover primary flows
- [ ] Feature meets the measurable Success Criteria
- [ ] No implementation detail leaked into the spec

## Plan Gate
- [ ] Constitution Check passes (CLAUDE.md) before AND after design
- [ ] Every violation justified in Complexity Tracking, or removed
- [ ] Concrete source layout chosen (real paths)

## Tasks Gate
- [ ] Tasks grouped by user story; each story independently testable
- [ ] No cross-story dependency that breaks independence
- [ ] No two [P] tasks touch the same file
- [ ] MVP (P1) is the smallest viable slice

## Analyze Gate
- [ ] Every requirement maps to at least one task
- [ ] Every task traces to a requirement
- [ ] No contradiction across spec / plan / tasks

## Notes
- Items marked incomplete must be fixed before the next phase starts.
