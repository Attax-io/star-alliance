---
name: safe-agentic-orchestration
metadata:
  version: 1.1.0
type: Skill
description: "Orchestrate a coordinated multi-agent AI team using the SAFe-agentic doctrine distilled from a production harness: a fixed role roster with hard boundaries, a spec-then-execute pre-implementation gate, an iterate-until-blocked-then-escalate agent loop, evidence-based delivery with an independent QAS verification gate, a layered handoff-and-gate pipeline ending in human merge, and machine-enforced quality-gate hooks (TeammateIdle / TaskCompleted, exit code 2 blocks idle-or-done until criteria pass). Use it whenever you must split a large deliverable across specialists and want the work to stay verifiable and traceable. Triggers: 'orchestrate this team', 'coordinate these agents', 'design the agent roles', 'who should own this work', 'set up the delivery pipeline', 'enforce a quality gate', 'spawn an agent team'. Unlike ultra-brainstorming (one mind across many models) or members-formation (Butler routing one request), this teaches durable team structure, role separation, and spec-execute-release gating."
---

# Safe Agentic Orchestration

Coordinating several AI agents on one deliverable is not "spawn more workers." It is a question of **structure**: who is allowed to do what, in what order, and with what proof. This skill distills the generative doctrine of a production-tested SAFe-style harness (11 roles, layered gates, evidence-based delivery) into a small set of axioms a Star Alliance member can apply to orchestrate any multi-agent team — without copying the harness's specific code, tickets, or tooling.

The aim is a pipeline where **planning precedes implementation, implementation precedes independent verification, and nothing merges without proof and a human's final yes.**

## What it is / is not

**It is:**
- A doctrine for *structuring* a multi-agent team: fixed roles with hard boundaries, an orchestrator that routes but does not execute, and a spec → plan → execute → verify → release pipeline.
- A set of *generative principles* you adapt to the task at hand (a story, a feature, an epic), not a fixed script.
- Agnostic to the coordination mechanism — the same axioms hold whether agents are subagents, an Agent-Teams shared task list, or sequential handoffs.

**It is not:**
- A reimplementation of the source harness (Linear, Prisma, yarn ci, slash commands are *their* substrate — yours will differ).
- A replacement for ultra-brainstorming (a model ensemble inside one mind) or members-formation (the Butler's per-request routing). This is about a *standing team* working a deliverable.
- A licence to spawn agents freely — team size is bounded; coordination overhead is real (see `references/coordination-patterns.md`).

## Core principles

### 1. Separate the orchestrator from the executors — and keep the manager out of the work
There is one primary orchestrator (the harness calls it ARCHitect-in-CLI) that owns routing, sequencing, and architectural judgment. Crucially, the *delivery manager* role (TDM) is **reactive, not an orchestrator**: it tracks progress, resolves blockers, and attaches evidence, but never assigns features or executes technical work. Mixing "who decides the plan" with "who tracks the plan" with "who does the work" is the first cause of an unsteerable team. Name these three jobs and keep them in different hands.

### 2. One role per kind of work — wrong-agent assignment is a stop-the-line error
Each work type has exactly one correct owner and explicit "never use" alternatives: database/migrations → Data Engineer (never a BE Developer), security/RLS → Security Engineer (never QA), docs → Tech Writer, specs → BSA, architecture → System Architect. The boundary is not bureaucracy — it is what makes review meaningful and keeps a generalist from silently doing security or schema work it is not accountable for. See `references/role-architecture.md`.

### 3. No implementation without a spec — the pre-implementation gate is mandatory
Before any agent writes code, an analyst (BSA) produces a spec with **testable acceptance criteria, pattern references for the executor, and a runnable success-validation command**; the architect reviews it for pattern and security compliance; *then* a specialist executes. A spec that says "just do the thing," has no pattern pointer, or no command to verify "done" is forbidden. Planning is a gate, not a courtesy. See `references/gating-and-release.md`.

### 4. Iterate until success or blocked, then escalate with context
Every task runs the same loop: define goal → discover existing patterns → implement → run validation → on pass attach evidence, on fail analyze-and-retry, on blocked **escalate with full context** (what you tried, time blocked, the specific ask). An agent that silently continues past a real blocker wastes the run; one that escalates a one-line "it's broken" wastes the reviewer's. Escalation is structured, time-bounded (blocker > 1h → manager, > 4h → architect), and routed by concern (security → SecEng). See `references/coordination-patterns.md`.

### 5. Evidence-based delivery — never let the implementer grade its own work
"Trust me, it works" is banned. Every phase attaches verifiable proof (test output, command logs, screenshots, a session id for the audit trail). The QAS verification gate is an **independence gate: not collapsible** — it must be a separate agent that validates acceptance criteria, never the one that wrote the code. Security review is independent for the same reason. This mirrors the Star Alliance verify-gate doctrine: the critic is a different mind from the implementer.

### 6. Layered gates and explicit exit states — handoffs are contracts, merge is human
The pipeline is a chain of gates, each with an owner and an explicit exit state: implementer ends at "Ready for QAS", QAS at "Approved for RTE", release engineer at "Ready for HITL", architect at "Stage 1 Approved". A gate either passes or stops the line — there is no soft pass. The release engineer shepherds the PR but writes no code and does not merge; **final merge authority is always the human (HITL).** Roles may collapse (the PR shepherd can fold into the implementer) only when they are *not* independence gates. See `references/gating-and-release.md`.

### 7. Right-size the team and bound the blast radius
More agents is not more throughput past a point — coordination overhead dominates, and Agent-Teams cost can run ~7x a single session. Match team size to scope (single story → 2-3 agents, feature → 3-5, epic → 5-8), give each agent disjoint files to avoid write conflicts, broadcast only for stop-the-line events, and prefer subagents when you just need a focused worker that reports back. See `references/coordination-patterns.md`.

### 8. Enforce the load-bearing gates with hooks — a gate you only trust is a gate that gets skipped
Doctrine says an agent *should* not skip the QAS gate or declare done what isn't; a **hook** makes it *cannot*. Wire the team-lifecycle hooks so the line mechanically stops at the gate: a **TaskCompleted** hook (exit code 2 BLOCKS a task being marked done until acceptance criteria verify and evidence is attached) and a **TeammateIdle** hook (exit code 2 BLOCKS an agent going idle with assigned work unfinished or unverified). exit 2 + a precise stderr message turns the block into a corrective instruction. This is the team-level mirror of the Star Alliance verify-gate — the single-session critic-on-the-diff extended to a coordinated team; the human merge gate still sits above it. See `references/hook-enforcement.md`.

## Reference index

- `references/role-architecture.md` — the 11-role roster, each role's mandate and boundary, the orchestrator-vs-manager-vs-executor split, and which roles are collapsible vs independence gates.
- `references/gating-and-release.md` — the spec → plan → execute → verify → release pipeline: the pre-implementation gate, the spec contract (acceptance criteria + pattern refs + validation command), the QAS independence gate, exit states, and HITL merge.
- `references/coordination-patterns.md` — the agent loop, evidence-based delivery, structured escalation, team-vs-subagent-vs-background choice, team sizing, communication discipline, and quality-gate hooks.
- `references/hook-enforcement.md` — the machine-enforced gate mechanism: the TeammateIdle / TaskCompleted hooks (exit code 2 to BLOCK idle/completion until acceptance criteria are met), the exit-code contract, `.claude/settings.json` wiring, what each check must actually verify, and the mapping back onto the doctrine gates and the verify-gate.

## Changelog

- **1.1.0** — Added the hook-as-enforcement mechanism: new `references/hook-enforcement.md` (TeammateIdle / TaskCompleted quality-gate hooks, exit-code-2 block contract, settings.json wiring, check anatomy, verify-gate mapping) + Core principle 8. Turns the gate doctrine into machine-enforced invariants mirroring the guild verify-gate.
- **1.0.0** — Initial release: SAFe-agentic orchestration doctrine (role architecture, gating-and-release, coordination patterns) distilled from a production harness.
