---
type: Document
title: Staged Swarm Methodology — Build-Ready Plan
status: approved-for-later (not yet implemented)
date: 2026-06-28
---

# Staged Swarm Methodology — Build-Ready Plan

> Planning artifact. **Approved for later build, not yet implemented.** Drafted by the
> Strategist, reviewed by the Butler. Repo: `/Users/attaselim/Documents/Claude/Projects/star-alliance`.

## Locked decisions (Guild Master, 2026-06-28)
- **Scope v1 = the safe 80%:** teams on NON-OVERLAPPING files (Waves 0–3 + 5). The
  same-file "private workspace" path (git worktrees, Wave 4) is a **separate, later,
  human-gated** job — most swarms never need it and it carries the only data-loss risk.
- **MAX_SWARM = 5** (the comfortable parallel window; Butler uses fewer when smaller).
- **Stage expression = implicit** per-step `"stage": "<name>"` string (zero migration).
- **Leave today's `parallel:true` fan-out steps as-is;** reserve `swarm` for partitioned
  WRITE work only.

## Plain-English summary
A workflow becomes **stages** (waves). At a stage the Butler may deploy a **swarm** — N
copies of one specialist (Developer-1, -2, -3), each owning a separate slice of the work,
launched in one message, running in parallel. Two hard rules keep it safe: (1) no two
parallel writers touch the same file; (2) a swarm is always followed by an inline
**integrate + verify** step so the independent review sees the combined result. A
"don't-swarm-tiny-jobs" guard stops it from costing more than it saves.

## 1. Concept
- **Step** (unchanged): one `steps[]` entry, one member.
- **Stage** (new, optional): a named group of steps sharing `"stage": "<name>"`. Additive
  sugar — a workflow with no stage tags is exactly today's flat list.
- **Swarm** (new): N instances of ONE member, each a disjoint self-contained brief, fanned
  out by the Butler in a single message. Declared by a `swarm` object on a member step.
  `swarm` implies `exec:"spawn"` + `parallel:true`.

## 2. Schema (`workflows.json`)
Optional `swarm` object on a `kind:"member"` step (absent = today's behavior):
```jsonc
"swarm": {
  "member": "the-developer",      // must equal the step's actor
  "max_instances": 4,             // 1 < n <= MAX_SWARM(5)
  "min_instances": 2,             // below this, run as a single step
  "partition": "by-module",       // by-file | by-module | by-subtask
  "isolation": "shared-tree",     // shared-tree | worktree (worktree = Wave 4, deferred)
  "integration_step": true        // an inline same-actor integration step MUST follow in-stage
}
```
Stages via per-step `"stage": "<name>"`. `gen_workflows_lite.py` must pass through (or
strip) the new keys so the generated lite file never drifts.

## 3. The Butler's `decompose-and-swarm` skill (the make-or-break craft)
New skill `star-alliance-skills/decompose-and-swarm/SKILL.md`, carried by `the-butler`.
Five moves:
- **MOVE 0 — Worthiness gate.** Swarm ONLY if all true, else single step: big enough
  (~1.5k+ tokens/instance), splittable (≥ min_instances clean slices), loosely coupled
  (slices don't need each other's in-progress state), cheaper-net (workers cheaper than
  the Opus main thread). This guard is the most important line — over-decomposition is the
  #1 way swarms destroy value.
- **MOVE 1 — Cut disjoint slices.** Partition by file/module/subtask. Build each
  instance's file-set; **assert pairwise-empty intersection**. Overlap → re-partition or
  escalate that pair to `isolation:worktree`. Never fan out overlapping slices on a shared
  tree. (THE cash invariant.)
- **MOVE 2 — One self-contained brief per instance, each carrying the shared contract:**
  exact files owned + "touch nothing else"; shared conventions (design tokens, naming,
  reading discipline); the exact interfaces/seams with sibling slices (so isolated
  instances agree on names/types without seeing each other); deliverable shape; "do NOT
  commit / cross-edit / spawn".
- **MOVE 3 — Fan out in ONE message** (true parallelism). The Butler (main thread) does
  the whole fan-out; instances can't spawn instances.
- **MOVE 4 — Collect, integrate, verify INLINE** on the main thread: assemble slices,
  reconcile seams against the contract, run the build; the armed Stop verify-gate Critic
  (glm-5.2) reviews the **aggregate diff**; commit once. Integration is inline precisely so
  this review sees everything.
- **Failure handling:** one instance fails → re-dispatch just that slice; seam mismatch →
  fix inline or re-dispatch the two affected slices with a corrected contract; a slice that
  fails ≥2× → Butler does it inline or invokes the Confusion Protocol.

## 4. Worktrees (Wave 4 — DEFERRED, separate later job)
Only when two writers MUST edit the same file. `guild/spawn.py` provisions a git worktree
per writer under `runs/<run-id>/` (already out of conformity scope); `guild/merge_runs.py`
merges branches back **sequentially on the main thread**; conflict = Confusion-Protocol
stop, never silent auto-resolve. Doctrine: prefer re-partitioning over worktrees.

## 5. Guardrails (mechanical, in `tools/conformity_check.py`)
- `MAX_SWARM = 5`.
- `SW1` swarm.member == actor · `SW2` 1 < max_instances ≤ 5, 2 ≤ min ≤ max · `SW3`
  partition/isolation enums valid · `SW4` swarm step with integration_step is followed
  in-stage by an inline same-actor step · `SW5` swarm.member is a real member; the
  `decompose-and-swarm` skill is carried by **the-butler**.
- Partition-disjoint invariant + integration-always-follows-swarm + verify-stays-inline are
  the three safety locks. Parallel writers are ungated *because* the serial integration is
  gated.

## 6. Brief + dashboard
Deployment brief shows the multiplier + slices:
```
▸ Workflow — Architecture Build · Stage: Build (swarm)
Deploying 4 agents:
  • The Developer ×3 — MiniMax M3 — slices: [auth] [billing] [notifications]
  • The Developer ×1 — Sonnet — integrate + verify (inline)
```
The existing banner-enforcer bullet regex already matches `• The Developer ×3 — …` — **no
hook change required.** Live feed shows N sibling rows under one stage header, derived from
run status (no new source of truth).

## 7. Phased build (safe-first)
| Wave | Deliverable | Risk |
|---|---|---|
| 0 — Doctrine | `decompose-and-swarm` SKILL.md + `[[core-swarm]]` memory; carry on the-butler | LOW |
| 1 — Schema | `swarm` + `stage` in workflows.json + STEP-SCHEMA.md; gen_workflows_lite pass-through; one pilot swarm step in Architecture Build (behind defaults) | LOW |
| 2 — Butler skill live | Real disjoint-file/module swarm, shared tree, inline integration | MEDIUM |
| 3 — Brief + dashboard | `×N`/slices in brief; N rows in feed | LOW |
| **4 — Worktrees** | `guild/spawn.py` + `merge_runs.py`; same-file `isolation:worktree` | **HIGH — DEFERRED** |
| 5 — Guardrails | MAX_SWARM + SW1–SW5 in conformity_check.py; VERSIONS bump; rebuild | MEDIUM |

v1 = Waves 0,1,2,3,5. Wave 4 is a later, separate, human-gated campaign.

## 8. Risks & mitigations (top)
- **Same-file data loss** → disjoint-partition invariant + worktree escape (deferred).
- **Incoherent outputs** → shared-contract block in every brief + inline integration.
- **Cost blowup / over-decomposition** → worthiness gate + "≥2 fat independent slices or
  it's one step".
- **Verify dishonesty** → integration inline so the aggregate diff is Critic-reviewed and
  committed once.
- **Coupled work mis-swarmed** → loose-coupling test; coupled slices are sequenced, not
  swarmed.

## Verification per wave
Each wave ends with: `conformity_check.py` exit 0, a real dry-run of the new behavior, and
an independent review of the diff. The 8 existing fan-out steps must keep working at every
wave.
