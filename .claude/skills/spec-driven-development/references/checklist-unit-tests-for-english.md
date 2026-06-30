---
type: Document
title: Checklists are unit tests for English
description: Spec-driven-development checklist doctrine — a checklist validates the REQUIREMENTS writing (completeness/clarity/consistency/measurability/coverage), not the implementation. Banned verbs, [Gap]/[Ambiguity]/[Conflict] markers, CHK### ids, ≥80% traceability.
timestamp: 2026-06-28T00:00:00Z
---

# Checklists are "unit tests for English"

**CRITICAL CONCEPT.** A checklist is a **unit-test suite for the requirements writing** — it
validates the quality, clarity, and completeness of the requirements in a domain. It does
**NOT** test the implementation. If your spec is code written in English, the checklist is its
unit tests: you are testing whether the *requirements* are well-written, complete,
unambiguous, and ready to build — never whether the *code* works.

> Adapted from GitHub Spec Kit's `checklist.md`.

## NOT for verification/testing

- ❌ NOT "Verify the button clicks correctly"
- ❌ NOT "Test error handling works"
- ❌ NOT "Confirm the API returns 200"
- ❌ NOT checking whether code/implementation matches the spec

## FOR requirements-quality validation

- ✅ "Are visual-hierarchy requirements defined for all card types?" [Completeness]
- ✅ "Is 'prominent display' quantified with specific sizing/positioning?" [Clarity]
- ✅ "Are hover-state requirements consistent across all interactive elements?" [Consistency]
- ✅ "Are accessibility requirements defined for keyboard navigation?" [Coverage]
- ✅ "Does the spec define what happens when the logo image fails to load?" [Edge Case]

## The five quality dimensions every item tests

- **Completeness** — are all necessary requirements present?
- **Clarity** — are requirements unambiguous and specific?
- **Consistency** — do requirements align with each other without conflict?
- **Measurability** — can a requirement be objectively verified?
- **Coverage** — are all scenarios / edge cases addressed?

## Category structure

Requirement Completeness · Requirement Clarity · Requirement Consistency · Acceptance Criteria
Quality · Scenario Coverage · Edge Case Coverage · Non-Functional Requirements (perf, security,
a11y) · Dependencies & Assumptions · Ambiguities & Conflicts.

## Item structure

Each item is a **question about requirement quality**, focused on what is (or is not) written
in the spec/plan, tagged with its quality dimension in brackets, and traceable:

```markdown
- [ ] CHK001 Are the number and layout of featured episodes explicitly specified? [Completeness, Spec §FR-001]
- [ ] CHK002 Is "prominent display" quantified with measurable visual properties? [Clarity, Spec §FR-004]
- [ ] CHK003 Is the selection criteria for related episodes documented? [Gap, Spec §FR-005]
- [ ] CHK004 Are rollback requirements defined for migration failures? [Gap]
```

- Question format asking about requirement quality.
- Reference the spec section `[Spec §X.Y]` when checking an existing requirement.
- Use `[Gap]` for a missing requirement, `[Ambiguity]` for a vague one, `[Conflict]` for two
  that disagree, `[Assumption]` for an unvalidated premise.
- Globally incrementing IDs starting at `CHK001`. Append-only across runs — if the file
  exists, continue from the last CHK id; never delete or replace existing items.

## Traceability requirement

**≥80% of items MUST carry at least one traceability reference** — a spec section `[Spec §X.Y]`
or a marker `[Gap]` / `[Ambiguity]` / `[Conflict]` / `[Assumption]`. If no id scheme exists
yet, the first item is: "Is a requirement & acceptance-criteria ID scheme established?
[Traceability]".

## 🚫 Absolutely prohibited (these make it an implementation test)

- Any item starting with **Verify / Test / Confirm / Check** + implementation behavior.
- References to code execution, user actions, or system behavior — "click", "navigate",
  "render", "load", "execute", "displays correctly", "works properly".
- Test cases, test plans, QA procedures, framework/API/algorithm details.

## ✅ Required patterns (these test requirements quality)

- "Are [requirement type] defined/specified/documented for [scenario]?"
- "Is [vague term] quantified/clarified with specific criteria?"
- "Are requirements consistent between [section A] and [section B]?"
- "Can [requirement] be objectively measured/verified?"
- "Are [edge cases / scenarios] addressed in requirements?"
- "Does the spec define [missing aspect]?"

## The one-line test before you write any item

Wrong tests whether the system works; correct tests whether the requirement is written
correctly. Wrong: "Does it do X?" Correct: "Is X clearly specified?" If your item could be a
QA step, it belongs in `/implement` validation — not here.
