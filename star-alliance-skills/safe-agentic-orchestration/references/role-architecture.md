---
type: Document
title: Role Architecture
description: The 11-role SAFe roster, the orchestrator-vs-manager-vs-doer split, the one-owner assignment matrix, and collapsible roles vs independence gates.
timestamp: 2026-06-28T00:00:00Z
---

# Role Architecture

The harness runs an **11-role SAFe team**. The point is not the exact titles — it is that work types are partitioned into roles with **hard boundaries and explicit "never use" alternatives**, so that review is meaningful and no generalist silently does accountable work (security, schema) it is not the owner of.

## The three layers of authority

Before listing roles, separate three jobs that are easy to conflate and fatal to mix:

1. **Orchestrator** — one primary mind (the harness's *ARCHitect-in-CLI*) that owns routing, sequencing, and architectural judgment. It decides *what happens next and who does it*.
2. **Delivery manager** — *reactive, not an orchestrator*. The TDM tracks delivery progress, updates the system of record, escalates blockers, attaches evidence. It does **not** assign features, run validation, or execute technical work. (The source flags this explicitly: "TDM is REACTIVE, not an orchestrator. ARCHitect-in-CLI is the primary orchestrator.")
3. **Doers** — the specialists who execute exactly one kind of work.

Keeping "decides the plan" / "tracks the plan" / "does the work" in different hands is the precondition for a steerable team.

## The role roster

| Role | Mandate | Done means |
| --- | --- | --- |
| **ARCHitect-in-CLI** | Primary orchestrator; Stage 2 architecture review | Routing + architecture approved |
| **TDM** (Technical Delivery Manager) | Reactive blocker resolution, evidence tracking (NOT orchestration) | Blockers resolved, evidence attached, tracker updated |
| **BSA** (Business Systems Analyst) | Requirements decomposition, acceptance criteria, testing strategy | Clear user stories, testable ACs, QA plan |
| **System Architect** | Pattern validation, Stage 1 PR review, migration approval, ADRs | ADR created, technical review complete, no conflicts |
| **FE Developer** | UI components, client-side logic | Lint + build pass |
| **BE Developer** | API routes, server logic, RLS enforcement | Integration tests pass |
| **DE** (Data Engineer) | Schema changes, migrations, DB architecture | Migration applied, RLS maintained |
| **Tech Writer** | Documentation | Docs accurate and complete |
| **QAS** (Quality Assurance) | **Gate owner**: execute testing, validate ACs, post evidence | All ACs verified, exit "Approved for RTE" |
| **SecEng** (Security Engineer) | Security validation, RLS checks, vuln assessment | Security audit passed, RLS enforced |
| **RTE** (Release Train Engineer) | **PR shepherd**: PR creation, CI monitoring (no code, no merge) | PR created, CI green, exit "Ready for HITL" |

## The assignment matrix (one owner, explicit anti-owner)

The harness treats wrong-agent assignment as a **stop-the-line error**:

| Work type | Correct owner | Never use |
| --- | --- | --- |
| Database / migrations | Data Engineer | BE Developer |
| Security / RLS | Security Engineer | QAS |
| Documentation | Tech Writer | BE/FE Developer |
| Specs / planning | BSA | Any implementer |
| Architecture | System Architect | Direct-to-developer |
| API routes | BE Developer | FE Developer |
| UI components | FE Developer | BE Developer |
| Testing / QA | QAS | The implementation team |
| PR / releases | RTE | Developers |

The generative point: **for each kind of work, name the one accountable owner and the tempting-but-wrong alternative.** The anti-owner column is what prevents drift.

## Collapsible roles vs independence gates

Not every role must be a distinct agent. The harness distinguishes:

- **Collapsible** — *RTE*. PR creation and CI shepherding can be folded into the implementer when the team is small. Convenience, no integrity loss.
- **NOT collapsible (independence gates)** — *QAS* and *SecEng*. Quality validation and security audit **require independence**: the verifier must be a different agent than the implementer, or the review is theatre. When collapsing for a small team, spawn a fresh subagent for these.

This is the same principle as the Star Alliance verify-gate: never let the implementer grade its own work. The independence is structural, not a matter of trust.

## Adapting to your team

You will not have eleven agents. Distil to the jobs that exist in your deliverable, but preserve the invariants:
- exactly one orchestrator, separate from any tracker;
- one accountable owner per work type;
- planning (analyst) and verification (QAS/security) held by *different* agents than implementation;
- a human at the end (HITL) with final merge authority.
