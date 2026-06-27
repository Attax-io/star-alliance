---
type: Document
title: Plan Template
description: Spec-driven-development implementation plan template — technical context, constitution check, project structure, complexity tracking.
timestamp: 2026-06-27T00:00:00Z
---

# Implementation Plan: [FEATURE]

**Feature**: `specs/[NNN]-[short-name]/` | **Date**: [DATE] | **Spec**: [link to spec.md]

## Summary
[Primary requirement (from spec) + the technical approach in one paragraph.]

## Technical Context
- **Language/Version**: [e.g., TypeScript 5.x / Python 3.11 or NEEDS CLARIFICATION]
- **Primary Dependencies**: [e.g., Next.js, Supabase or NEEDS CLARIFICATION]
- **Storage**: [e.g., Postgres/Supabase, files or N/A]
- **Testing**: [e.g., Vitest, pytest or NEEDS CLARIFICATION]
- **Target Platform**: [e.g., web, iOS 15+, CLI]
- **Project Type**: [single / web / mobile / library / service]
- **Performance Goals**: [domain-specific, e.g., 60fps, 1000 req/s or N/A]
- **Constraints**: [e.g., <200ms p95, offline-capable or N/A]
- **Scale/Scope**: [e.g., 10k users, 50 screens]

## Constitution Check
> GATE: must pass before design. Re-check after design. In this guild the constitution is
> `CLAUDE.md` + guild conduct.
- [ ] Plan obeys CLAUDE.md (reading discipline, guild conduct, doer-first, no unrequested changes)
- [ ] No destructive op without the confirm gate
- [ ] Reuses existing components/tokens before creating new (grep first)
- [ ] [project-specific principle …]

## Project Structure
```text
specs/[NNN]-[short-name]/
├── spec.md
├── plan.md            # this file
├── research.md        # optional: decisions + rationale
├── data-model.md      # optional: entities → schema
├── contracts/         # optional: API / interface contracts
└── tasks.md           # produced by the /tasks phase
```
**Source layout decision**: [the concrete directories this feature will touch — real paths]

## Complexity Tracking
> Fill ONLY if the Constitution Check has a violation you must justify.

| Violation | Why needed | Simpler alternative rejected because |
|---|---|---|
| [e.g., new service] | [need] | [why the simpler path fails] |
