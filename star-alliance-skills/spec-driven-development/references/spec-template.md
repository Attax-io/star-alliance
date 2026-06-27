---
type: Document
title: Spec Template
description: Spec-driven-development feature specification template — WHAT/WHY, prioritized stories, measurable success criteria.
timestamp: 2026-06-27T00:00:00Z
---

# Feature Specification: [FEATURE NAME]

**Feature**: `specs/[NNN]-[short-name]/`
**Created**: [DATE]
**Status**: Draft
**Input**: User description: "[the natural-language ask]"

> Focus on **WHAT** users need and **WHY**. No tech stack, no APIs, no code structure.
> Written for a stakeholder, not a developer. Remove any section that does not apply
> (don't leave "N/A"). Max 3 `[NEEDS CLARIFICATION: ...]` markers — everything else
> gets an informed guess recorded under Assumptions.

## User Scenarios & Testing *(mandatory)*

> Stories are prioritized user journeys (P1 = most critical). Each must be
> INDEPENDENTLY TESTABLE — implement just one and you still have a viable MVP.

### User Story 1 - [Brief Title] (Priority: P1)

[Describe this user journey in plain language.]

**Why this priority**: [value + why it ranks here]
**Independent Test**: [how to verify this story alone delivers value]
**Acceptance Scenarios**:
1. **Given** [initial state], **When** [action], **Then** [expected outcome]

### User Story 2 - [Brief Title] (Priority: P2)
[…same shape…]

### User Story 3 - [Brief Title] (Priority: P3)
[…same shape…]

### Edge Cases
- [boundary / error / empty / concurrent condition and expected handling]

## Requirements *(mandatory)*

### Functional Requirements
- **FR-001**: System MUST [testable capability].
- **FR-002**: System MUST [testable capability].
- **FR-003**: Users MUST be able to [action].

> Each requirement must pass "testable and unambiguous". A vague requirement is a bug.

### Key Entities *(if data involved)*
- **[Entity]**: [what it represents, key attributes — no schema/columns here]

## Success Criteria *(mandatory)*

> Measurable AND technology-agnostic. User/business outcomes, not system internals.
- **SC-001**: [e.g., "Users complete [task] in under [N] minutes"]
- **SC-002**: [e.g., "95% of [operation] succeed on first attempt"]
- **SC-003**: [e.g., "System handles [N] concurrent [users/items]"]

## Assumptions
- [reasonable default taken instead of a clarification — record every guess here]

## Out of Scope
- [explicitly excluded, to bound the spec]
