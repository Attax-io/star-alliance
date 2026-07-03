---
name: decompose-and-swarm
description: "The Butler's swarm craft — judge whether a task is worth parallelising, scout the codebase surface, cut disjoint file-slices, write contracts-first seams, brief N workers with a 3-tier self-contained prompt each, fan them out in one message, run a per-slice critic before integration, then integrate and commit once on the main thread. Triggers: 'swarm this', 'parallelise the work', 'run N agents', 'fan out', 'split the slices', or whenever a swarm step appears in a workflow. Pairs with safe-agentic-orchestration (team doctrine), members-formation (routing), weapon-utility (model seat rules), and codebase-memory-mcp (scout)."
metadata:
  version: 1.0.0
type: Skill
---

# Decompose and Swarm

Parallel workers are not free speed. They are an economic instrument: **N capable workers in parallel versus one capable worker serially.** The saving only materialises when the work is genuinely splittable, the slices are truly disjoint, and the orchestration overhead does not eat the gain. This skill is the Butler's method for judging that, executing it safely, and integrating the result with a verified seam.

The underlying structure is a **capable-bookends engine**: a small capable gate BEFORE (scout + decompose + contract), cheap parallel bulk IN THE MIDDLE (N worker instances), and a small capable gate AFTER (per-slice critic + serialised integration). Skipping either bookend turns the middle into unreviewed parallel chaos.

## What it is / is not

**It is:**
- The Butler's method for deciding whether to swarm and, if yes, executing the five moves safely.
- Applicable whenever a workflow step carries a `swarm` object or whenever the Butler judges that fan-out would be net-cheaper than the main thread doing all slices serially.
- A doctrine of generative axioms, not a fixed script — the exact scout calls and brief wording adapt to the task.

**It is not:**
- A licence to spawn freely. The worthiness gate is the most important line in this skill.
- A replacement for [[safe-agentic-orchestration]] (team structure and spec gates) or [[members-formation]] (workflow selection). Those run first; this runs when a selected workflow declares a swarm step.
- A non-Claude routing rule. Workers are Claude subagents that run as the member's Claude model (Sonnet, tool-capable) — every worker is a Claude model. See the MODEL RULE below.

**MAX_SWARM = 7.** The Butler never fans out more than seven workers in one message. _(Raised from 5 to 7 on 2026-07-01 to match the live 7-worker swarm demo; the per-slice critic reviews each slice independently, so a wider fan-out does not breach the 60KB aggregate threshold.)_

---

## The economic engine: capable bookends, cheap middle

**FRONT (the thinker scouts and decomposes).** Decomposition is never a cheap-model job. The Butler — running on Opus — does the worthiness check, scouts the codebase surface, cuts the slices, and writes the seam contracts before any worker launches. This is the bookend that makes the rest safe.

**MIDDLE (N Claude subagents, cheap).** Each worker is a Claude subagent (spawned via the Task tool) that runs as the member's Claude model (Sonnet) instead of Opus. That is the saving: N Sonnet subagents versus one Opus doing all slices serially. Each subagent does its own reads and writes as that Claude model — there is no separate engine inside it.

**BACK (capable, independent).** As each worker returns, the Butler runs `evolution/verdict.run_cold(worker_slice_diff)` on that worker's diff BEFORE integration. The aggregate diff from a swarm routinely exceeds the auto-critic's 60KB threshold — without per-slice review, every swarm would drop to a manual bypass and the "nothing enters without a critic verdict" invariant becomes theater. Per-slice review keeps every constituent blessed before the final commit. The Stop-hook aggregate review then has a per-slice ledger trail behind it.

---

## The five moves

### MOVE 0 — Worthiness gate

**Swarm only if all four hold; otherwise, single step.**

1. **Big enough.** Each slice needs roughly 1.5k+ output tokens. A task you can state as "edit these 3 lines in file X" is not a swarm.
2. **Splittable.** The task has at least `min_instances` (default 2) clean, nameable slices. If you cannot name them without effort, you have already answered the question.
3. **Loosely coupled.** No slice needs another slice's in-progress state. Slices that are coupled are sequenced, not swarmed.
4. **Cheaper net.** N workers + orchestration overhead is cheaper than the Opus main thread doing every slice serially. If it is not, it is one step.

**Concrete trip condition (from Amp doctrine):** "Can you name the exact files or symbols to change?" If yes — do it inline, no swarm. Swarm only when the work is large enough that naming the exact surface is itself the decomposition task.

Over-decomposition is the #1 way swarms destroy value. When in doubt, do not swarm.

### MOVE 0.5 — Scout the surface (via [[codebase-memory-mcp]])

Before cutting slices, the Butler scouts the codebase surface. This fills the "boundaries before starting" gap and makes slice boundaries mechanical rather than guessed.

The four scout calls, in order:

1. `get_architecture` — clusters of co-editing files = de-facto modules = candidate slices. Prefer module boundaries over folder boundaries.
2. `trace_path(from, to, direction: "both")` — cross-slice call edges = coupling to declare as a seam (not a slice boundary).
3. `query_graph "MATCH (a:File)-[:FILE_CHANGES_WITH]->(b:File) …"` — latent co-change coupling invisible to import graphs. Two files that always change together belong in the same slice.
4. `detect_changes(symbols)` — per-slice blast radius (CRITICAL / HIGH / LOW) sizes the seam contract.

**Fallback when the codebase is not indexed:** manual directory analysis + an explicit coupling note in each brief. Never guess at coupling silently.

### MOVE 1 — Cut [P]-safe slices

A slice is parallel-safe if and only if:
- **(a) it touches DIFFERENT files than every concurrent slice**, AND
- **(b) it depends on no incomplete slice.**

Both conditions are required. Either failure makes the slice sequential, not parallel.

**Mandatory phase order inside a swarm:** Setup → Foundational (this is the synchronisation barrier — it runs and completes BEFORE fan-out) → per-story slices (parallel, these are the swarm proper) → Polish (after all slices land).

After cutting slices, build the file-set for each and **assert pairwise-empty intersection** — no two slices share a file. This is the disjoint-partition invariant. An overlap means re-partition or escalate that pair to `isolation: worktree` (Wave 4, deferred). Never fan out overlapping slices on a shared tree.

### MOVE 2 — Contracts-first seams

Before any worker launches, the Butler writes the seams every worker must agree on: shared interfaces, types, names, and module boundaries. This is what stops two isolated workers inventing two names for one boundary.

The seam contract goes in every worker brief. It is also the source of the acceptance test for the per-slice critic.

### MOVE 3 — Self-contained 3-tier brief per worker

Each worker loses all context the moment it launches. Pack the brief so it is entirely self-sufficient. Three tiers:

1. **One-line routing label.** "You are the Developer — Slice: auth module — files: src/auth/\*."
2. **Core brief (keep under 2k tokens).**
   - Exact file paths owned ("touch nothing outside this set").
   - The shared contract (interfaces, types, names agreed in MOVE 2).
   - The acceptance test ("the slice passes when X is true").
   - Do-NOT-touch file list (explicitly named).
   - **The model to run** — `model: sonnet` (first-class field, per the Claude Code Agent schema). Never omit this; it is the MODEL RULE made explicit.
   - Constraints: "do NOT commit / cross-edit / spawn workers of your own."
3. **File excerpts** — attached only when the slice genuinely requires them. Do not pad the brief; bulk excerpts belong in the worker's own Read calls.

### MOVE 4 — Fan out, per-slice critic, integrate, commit

**Fan out in one message.** Dispatch all worker briefs simultaneously in a single message (multiple Agent calls). True parallelism. The Butler (main thread) does the whole fan-out; workers cannot spawn workers.

**Per-slice critic (required).** As each worker returns, immediately run:

```
python3 evolution/verdict.run_cold(worker_slice_diff)
```

On the small diff for that slice — before integrating it. This is cheaper and parallel, and it keeps the critic invariant intact when the aggregate diff would exceed the 60KB auto-critic threshold. Record the verdict in the ledger. A BLOCK stops integration of that slice; re-dispatch or fix inline.

**Integrate on the main thread.** The Butler (the live session) assembles all blessed slices, reconciles the seams against the contract, runs the build, and verifies the aggregate result — reviewing the aggregate diff itself, backed by the per-slice ledger trail. Commit once. Serialised, revertible: one commit per slice in the merge sequence so `git revert` = surgical rollback.

**Failure handling.**
- One slice fails → re-dispatch just that slice with the same brief (fault-isolated).
- Seam mismatch → fix inline or re-dispatch the two affected slices with a corrected contract.
- A slice fails twice or more → Butler does it inline, or invokes the Confusion Protocol if scope is unclear.

---

## The MODEL RULE

A swarm worker that edits files is a Claude subagent (spawned via the Task tool) that runs as the member's Claude model — Sonnet, per each member's `model:` field. Every worker is a Claude model, so it holds the Edit / Write / Bash tools directly. There is no non-Claude engine to route the work to.

The saving is N Sonnet subagents under one Opus Butler — the same work, split across cheaper Claude models instead of one deep model doing every slice serially.

The brief's `model:` field makes this explicit and machine-checkable. Per [[weapon-utility]]: each member runs as its own Claude model; a subagent simply runs as that same model on its slice.

---

## Deployment brief format

Every swarm the Butler opens must surface the multiplier and slices in the high-alert deployment brief:

```
Deploying 4 agents:
  The Developer x3 — Sonnet — slices: [auth] [billing] [notifications]
  The Developer x1 — Sonnet — integrate + verify (inline)
```

The existing banner-enforcer regex already matches `The Developer x3 —` — no hook change required. Live feed shows N sibling rows under one stage header derived from run status.

---

## Invariants enforced by conformity_check.py (SW-series)

- **SW1** `swarm.member` equals the step's `actor`.
- **SW2** `1 < max_instances <= 7` and `2 <= min_instances <= max_instances`.
- **SW3** `partition` and `isolation` enums are valid (`by-file | by-module | by-subtask`; `shared-tree | worktree`).
- **SW4** A swarm step with `integration_step: true` is followed in-stage by an inline same-actor integration step.
- **SW5** `swarm.member` names a real member; `decompose-and-swarm` is carried by the-butler.

The **disjoint-partition invariant**, **integration-always-follows-swarm**, and **verify-stays-inline** are the three safety locks. Parallel writers are ungated precisely because the serialised integration is gated.

---

## Cross-links

- [[weapon-utility]] — model doctrine; each member (and each subagent it spawns) runs as its Claude model — Sonnet for the workers, Opus for the Butler coordinator.
- [[members-formation]] — workflow selection; a swarm step is declared in the selected workflow, not improvised.
- [[safe-agentic-orchestration]] — team structure doctrine; decompose-and-swarm is the execution method, safe-agentic-orchestration is the structural envelope.
- [[codebase-memory-mcp]] — the scout tool for MOVE 0.5; the four calls + FILE_CHANGES_WITH Cypher recipe.
- [[core-swarm]] — the guild's swarm memory core; read before any swarm-surface change.

---

## Changelog

- **1.0.0** — Initial release: the five moves (worthiness gate, codebase-memory scout, [P]-safe slice cut, contracts-first seams, 3-tier brief, per-slice critic, inline integration), the capable-bookends economic engine, the MODEL RULE, an initial MAX_SWARM cap of 5, disjoint-partition invariant, failure handling, deployment brief format, and SW-series invariants. Wave 0 (doctrine) of the Staged Swarm Methodology.
