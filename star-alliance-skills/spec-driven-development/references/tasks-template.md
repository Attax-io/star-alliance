---
type: Document
title: Tasks Template
description: Spec-driven-development task breakdown template — tasks grouped by user story, P-parallel markers, MVP-first ordering with checkpoints.
timestamp: 2026-06-27T00:00:00Z
---

# Tasks: [FEATURE NAME]

**Input**: `specs/[NNN]-[short-name]/` (plan.md required; spec.md for stories)

**Format**: `[ID] [P?] [Story] Description (exact file path)`
- **[P]** = can run in parallel (different files, no dependency)
- **[Story]** = which user story (US1, US2, …) for traceability
- Tests are OPTIONAL — include only if the spec requests them; if included, write them
  FIRST and ensure they FAIL before implementing.

## Phase 1: Setup
- [ ] T001 Create project/feature structure per plan.md
- [ ] T002 Install/confirm dependencies
- [ ] T003 [P] Configure lint/format

## Phase 2: Foundational (BLOCKS all stories)
> No user-story work begins until this phase is complete.
- [ ] T004 [shared schema / base models]
- [ ] T005 [P] [auth / routing / error+logging scaffolding]

**Checkpoint**: foundation ready — stories can start.

## Phase 3: User Story 1 — [Title] (P1) 🎯 MVP
**Goal**: [what it delivers] · **Independent Test**: [how to verify alone]
- [ ] T010 [P] [US1] Create [model] in [path]
- [ ] T011 [US1] Implement [service] in [path] (depends on T010)
- [ ] T012 [US1] Implement [endpoint/UI] in [path]
- [ ] T013 [US1] Validation + error handling

**Checkpoint**: US1 fully functional and independently testable — ship/demo as MVP.

## Phase 4: User Story 2 — [Title] (P2)
**Goal**: … · **Independent Test**: …
- [ ] T020 [P] [US2] …
- [ ] T021 [US2] …

**Checkpoint**: US1 AND US2 both work independently.

## Phase 5: User Story 3 — [Title] (P3)
- [ ] T030 [P] [US3] …

## Phase N: Polish & Cross-Cutting
- [ ] TXXX [P] Docs · cleanup · perf · security hardening · run quickstart validation

## Dependencies & Order
- Setup → Foundational (blocks all) → Stories (parallel or P1→P2→P3) → Polish.
- Within a story: tests (if any, must fail first) → models → services → endpoints → integration.
- [P] = different files only; never two [P] tasks on the same file.

## Implementation Strategy
- **MVP first**: Setup + Foundational + US1, then STOP and validate before US2.
- **Incremental**: each story adds value without breaking the previous.
- Commit after each task or logical group.
