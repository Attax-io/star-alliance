---
name: head-of-department
description: "The thin authority-and-limits layer that sits between a worker and a sub-tree. Owns NO mechanics — delegates both worker craft (via [[decompose-and-swarm]]) and team doctrine (via [[safe-agentic-orchestration]]). When a mid-task piece of work outgrows one worker, the head promotes, runs a swarm as a sub-worker, and integrates one result upward. Triggers: 'I'm a head', 'spawn a sub-team', 'promote this slice', 'we need a head here', 'who heads this sub-tree', or any dispatch whose recipient is itself going to dispatch."
metadata:
  version: 1.0.0
type: Skill
---

# Head of Department

The head is a **permission boundary**, not a worker. It exists so a sub-tree can be delegated cleanly without anyone confusing the head's authority for its craft. The head routes, caps, and demotes — it does not write, review, or design.

A head that runs mechanics has stopped being a head and started being a worker wearing authority. That is the failure mode the axioms below exist to prevent.

## What it is / is not

**It is:**
- A thin authority layer with hard caps (recursion depth, swarm width, tree width) and a one-shot promote/demote lifecycle.
- A pointer to two mechanics it does not own: [[decompose-and-swarm]] (the five MOVES) and [[safe-agentic-orchestration]] (team doctrine).
- The rule that keeps a sub-tree from becoming a recursive free-for-all.

**It is not:**
- A worker, a reviewer, or an architect. The head does no craft; it authorises craft.
- A replacement for [[members-formation]] (workflow selection) or [[core-swarm]] (swarm memory). Those run above and below the head respectively.
- A licence to spawn arbitrarily. The caps are the caps.

## Six axioms

### 1. Promotion gate
Promote to head only when mid-task work has outgrown one worker. The trigger is concrete: a slice too big for one BRAIN, a sub-tree needed for orthogonal craft, or a fan-out the current node cannot run safely. *Example: a developer agent receives a build with three disjoint refactors — promote a head for the refactor sub-tree; do not promote for a single-file edit.*

### 2. Recursion-depth cap
`MAX_DEPTH = 2`. Head → sub-head → workers. No third level. A worker that needs another worker escalates to its head; a sub-head that needs another sub-head demotes back. Depth beyond 2 is a partition bug, not a structural need.

### 3. Blast-radius cap
`MAX_SWARM = 5` per fan-out. `MAX_TOTAL_WORKERS = 12` per tree (one head + up to two sub-heads + their workers). Over either cap, the head re-partitions or escalates — it never widens. The caps exist so a head's fan-out stays auditable and the orchestrator's per-slice critic stays under the 60KB aggregate threshold.

### 4. Hand off mechanics
The head delegates the swarm itself to [[decompose-and-swarm]] — runs the five MOVES (worthiness, scout, cut slices, brief, fan-out) on the sub-tree's behalf. Team structure, role boundaries, and gating come from [[safe-agentic-orchestration]]. The head invokes; it does not reimplement.

### 5. Demote-back / integrate-up
After the sub-task lands, the head demotes back to a normal worker — it does not linger as authority. It integrates **one** result upward (the sub-tree's verified, per-slice-critic'd output) and passes it to its own caller. Two results up is a partition bug; zero results up means the head swallowed the work.

### 6. Sub-worker reports to its head
Each sub-worker reports to its head, not to the orchestrator above. The head runs the per-slice critic (`verdict.run_cold(slice_diff)`) on its workers' diffs before integration; the orchestrator sees one blessed diff per sub-tree, not N. This keeps the critic invariant intact past the 60KB threshold and preserves the head as the single point of accountability for its tree.

## Quick reference

| Concern | Owner |
|---|---|
| Swarm MOVES (scout/cut/brief/fan-out/integrate) | [[decompose-and-swarm]] |
| Team doctrine (roles, spec gates, QAS) | [[safe-agentic-orchestration]] |
| Workflow selection (who runs what) | [[members-formation]] |
| Model seats (Brain / Doer / Critic) | [[weapon-utility]] |
| Swarm memory / shared state | [[core-swarm]] |
| Caps (depth=2, swarm=5, tree=12) | **this skill** |

A head that knows all six axioms by heart but cannot name which skill owns the swarm MOVES is a head that will reimplement them badly. Reference, do not restate.