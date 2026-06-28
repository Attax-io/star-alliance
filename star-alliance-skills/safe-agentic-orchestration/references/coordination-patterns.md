---
type: Document
title: Coordination Patterns
description: The agent loop, evidence-based delivery, structured escalation, team vs subagent choice, team sizing, communication discipline, and quality-gate hooks.
timestamp: 2026-06-28T00:00:00Z
---

# Coordination Patterns

How the team actually runs once roles and gates are set: the per-task loop, how proof is attached, how blockers escalate, and how to choose the coordination mechanism and team size.

## The agent loop

Every task — by every agent — runs the same loop (the harness credits Simon Willison: *"iterate until success or blocked, then escalate"*):

1. **Goal definition** — clear acceptance criteria, from the spec/ticket.
2. **Pattern discovery** — search the codebase, docs, and prior sessions for existing patterns *before* implementing. Do not re-invent.
3. **Iterative execution**:
   - implement the approach → run validation →
   - **PASS** → proceed to evidence;
   - **FAIL** → analyze the error, adjust, repeat;
   - **BLOCKED** → escalate with context (do not silently continue).
4. **Evidence attachment** — attach proof to the system of record.
5. **QAS gate** — invoke the independent verifier before merge.

The loop's discipline is in the branches: a silent continue past a real blocker, or a "trust me" without evidence, both break it.

## Evidence-based delivery

Core principle: **"All work requires verifiable evidence — no 'trust me, it works'."** Evidence types and what each proves:

| Type | Proves |
| --- | --- |
| Test results | Code works as expected |
| Screenshots | UI changes are correct (before/after) |
| Command output | Operations completed (build/migration logs) |
| QAS report | Independent verification |
| Session ID | Full audit trail available |

Evidence is required **at every phase** (dev, staging, done), not only at the end. The system of record is the single source of truth for "what actually happened."

## Structured escalation

Escalation is time-bounded and routed by concern — never a bare "it's broken":

| Condition | Escalate to | Deadline |
| --- | --- | --- |
| Blocker > 1 hour | TDM (manager) | Immediately |
| Blocker > 4 hours | ARCHitect | Urgent |
| Architecture ambiguity | ARCHitect | Before work |
| Cross-team dependency | TDM + POPM | Same day |
| Security concern | SecEng | Immediately |

A good escalation states: what is blocked, the attempts already made, the context (ticket, time blocked, session id), and the **specific ask** (a decision? a resource?). Escalation with context is progress; escalation without it just relocates the confusion.

## Choosing the coordination mechanism

Three mechanisms, three jobs:

| Approach | Communication | Coordination | Best for |
| --- | --- | --- | --- |
| **Agent Teams** | DMs, broadcasts | Shared task list with dependencies | Complex multi-role workflows where teammates challenge each other |
| **Subagents** | Report back only | Main agent manages | Focused tasks, results only |
| **Background agents** | None | None | Fire-and-forget independent work |

Use **Teams** when agents must share findings and coordinate via gates; **subagents** when you need a focused worker that reports back; **background** when tasks are independent. Enforce quality gates across a team via **task dependencies** (`blockedBy`/`blocks`): e.g. QAS-validate is blocked-by implement-API and implement-UI, so the gate cannot fire early.

## Team sizing

| Scope | Team size | Tasks per agent |
| --- | --- | --- |
| Single story | 2-3 | 3-4 |
| Feature (multi-story) | 3-5 | 5-6 |
| Epic (parallel features) | 5-8 | 5-6 |

Rules of thumb: start small and scale up; **give each agent disjoint files** to avoid write conflicts; more than ~8 agents rarely helps (coordination overhead dominates). Agent-Teams cost can run **~7x a single session** — size deliberately.

## Communication discipline

- **Direct messages** are the default — targeted, cheap.
- **Broadcasts are expensive** — use *only* for stop-the-line events: critical blockers, an architecture change affecting everyone, a "STOP" announcement.
- **Shutdown coordination** — when all tasks complete, request shutdown from each teammate, wait for approval, then clean up the team. One team per session; clean up before the next.

## Quality-gate hooks

Gates can be mechanically enforced, not just trusted:

- **TaskCompleted hook** — validates output meets acceptance criteria before a task may be marked done; exit code 2 prevents completion and feeds back.
- **TeammateIdle hook** — validates assigned work is actually complete before an agent goes idle; exit code 2 keeps it working.

These are the team-level analogue of a Stop/verify gate: the structure enforces "done means done," so a gate cannot be skipped by an over-eager agent.
