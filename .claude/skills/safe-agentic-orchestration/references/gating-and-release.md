---
type: Document
title: Gating and Release
description: The spec to plan to execute to verify to release pipeline — pre-implementation gate, the spec contract, the QAS independence gate, exit states, and human merge authority.
timestamp: 2026-06-28T00:00:00Z
---

# Gating and Release

The pipeline is a chain of **gates**, each owned by a role, each with an explicit exit state. A gate either passes (and hands off) or **stops the line** — there is no soft pass. The chain ends with a human.

## The pipeline

```
Spec (BSA) → Architect review (Stage 1) → Implement (specialist, agent loop)
   → QAS verify (independence gate) → RTE shepherds PR → ARCHitect Stage 2
   → HITL merge (human, final authority)
```

## Gate 1 — Pre-implementation gate (MANDATORY)

No agent writes code before this passes:

1. **BSA creates a spec** with: testable acceptance criteria, pattern references for the executor, a runnable success-validation command.
2. **System Architect reviews**: pattern compliance, RLS/security requirements if database work.
3. **Then** the specialist executes.

Starting to code before a spec with acceptance criteria exists is a forbidden, stop-the-line pattern.

### The spec contract

A spec is a **contract handed to the executor**, not prose. Every spec carries:

- **Summary** — one paragraph.
- **User story** — "As a [user], I want [goal] so that [benefit]."
- **Acceptance criteria** — each one testable (you can mark it pass/fail): "User can click button → modal appears", "User can only see their own data", "Invalid input shows error".
- **Pattern references** — pointers to existing patterns the executor must follow (UI / API / DB / security). This is what lets a specialist execute without re-deciding architecture.
- **Success-validation command** — a runnable command that proves "done" (e.g. a test invocation, an API probe). "Looks good to reviewer" is forbidden.
- **Demo script** — step-by-step reproducible walk-through.
- **Logical commits** — the intended commit breakdown.

Forbidden specs: "just do the thing" (no acceptance criteria), "build it however you want" (no pattern reference), "looks good to reviewer" (no validation command). Each is a stop-the-line condition.

## Gate 2 — QAS independence gate (NOT collapsible)

Before any merge, an **independent** QAS agent — never the implementer — validates:

- every acceptance criterion is met (with evidence);
- commit-message format and ticket traceability;
- code patterns (RLS, naming, structure);
- CI is green;
- evidence is attached to the system of record.

QAS writes a verdict and a validation report; its exit state is "Approved for RTE". This is the core anti-pattern guard: **the implementer never grades its own work.** Security review (SecEng) is a parallel independence gate for anything touching auth, RLS, or data exposure.

## Exit states — handoffs are contracts

Each role hands off with an explicit, named exit state, so the next gate knows the work is ready:

| Role | Exit state |
| --- | --- |
| BE / FE / Data Engineer | "Ready for QAS" |
| QAS | "Approved for RTE" |
| RTE | "Ready for HITL Review" |
| System Architect | "Stage 1 Approved — Ready for ARCHitect" |
| HITL | MERGED |

A handoff without its exit state is incomplete — the receiving gate should reject it.

## Gate quick reference

| Gate | Owner | Blocking? |
| --- | --- | --- |
| Stop-the-Line | Implementer | YES — no acceptance criteria = no work |
| QAS Gate | QAS | YES — no approval = stop |
| Stage 1 Review | System Architect | YES — pattern check |
| Stage 2 Review | ARCHitect-CLI | YES — architecture check |
| HITL Merge | Human | YES — final authority |

## The human is the last gate (HITL)

The Release Train Engineer **shepherds** the PR — creates it, watches CI — but writes no code and does not merge. **Final merge authority is always the human.** No matter how many agents passed how many gates, the deliverable is not done until a person says so. This is the non-negotiable top of the chain.

## Why the gating matters

1. **Linear history + traceability** — every commit links to a ticket; rebase-first keeps history clean.
2. **Quality gates catch issues before production** — validation runs in the loop, not after.
3. **Independence prevents self-grading** — QAS and SecEng are separate minds.
4. **Explicit exit states make handoffs auditable** — no ambiguous "I think it's done."
5. **Human merge keeps accountability where it belongs.**
