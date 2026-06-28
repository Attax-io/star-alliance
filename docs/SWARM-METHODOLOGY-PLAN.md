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
  • The Developer ×3 — Sonnet — slices: [auth] [billing] [notifications]
  • The Developer ×1 — Sonnet — integrate + verify (inline)
```
**Model rule (corrected by the weapon-utility audit, 2026-06-28):** a swarm worker that
EDITS FILES must run as the member's **brain** (a tool-capable Claude model, e.g. Sonnet) —
NOT MiniMax/Ollama, which cannot hold the Edit/Write/Bash tools. MiniMax is the worker's
*internal* bulk doer, not the worker itself. The saving is **N Sonnet workers under one
Opus Butler** (cheaper than Opus doing every slice serially), not a doer-tier downgrade.
Per-instance: planning = member brain (Sonnet/Opus per `model:`); execution-inside-instance
= Doer seat (minimax-m3); coordinator + integration = the Opus Butler + Critic (glm-5.2) on
the aggregate diff.
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

---

## Skills Integration Route (4-agent audit, 2026-06-28)

A read-only swarm (Quartermaster · Strategist · Architect · Developer, disjoint slices)
audited the catalogue against the swarm upgrade. Result: **no merges among the fan-out
family; a focused set of upgrades; one new skill.**

### The fan-out family (keep all; swarm is the 4th corner)
| Skill | Axis | Action |
|---|---|---|
| ultra-brainstorming | many MODELS, converge to one plan | KEEP (optional 1-line cross-ref) |
| storm-investigation | many PERSONAS, converge to one briefing | KEEP (optional cross-ref) |
| **decompose-and-swarm (NEW)** | many MEMBER INSTANCES, diverge then integrate | BUILD (Wave 0) |
| members-formation | the chooser/router over the family | thin UPGRADE — recognize `swarm`, **delegate** to decompose-and-swarm (keep decomposition logic OUT) |
| safe-agentic-orchestration | the safety doctrine over the family | KEEP + 1 cross-ref (it already states disjoint-files, independence-gate, bounded-size) |
| high-alert | the deployment-brief contract | KEEP (regex already matches `×N`); optional doc patch with a `×N` example |

### Upgrades the swarm needs to land (ranked)
1. **weapon-utility — UPGRADE (load-bearing).** Today's "one thinker per member" rule
   FORBIDS parallel member-instances outside ultra-brainstorming; its existing "swarm" is
   doer-only. Add a **Member-instance swarm clause**: worker = member brain (tool-capable,
   never a doer-tier model); Doer seat works inside each instance; Butler coordinates +
   integrates inline. This is the rule that makes the model-correction above doctrine.
2. **workflow-forge — UPGRADE (highest authoring leverage).** Teach it the `swarm`/`stage`
   schema + the SW4 "integration step must follow" rule, so newly-forged workflows can
   actually declare swarms. Without it the schema is write-only.
3. **conquering-campaign — UPGRADE.** It already has a "fan-out sweep" (≥5 disjoint files,
   one subagent each) = a swarm minus schema, but says "W3 writes by the main agent." Name
   the equivalence; make a swarm the *sanctioned* parallel-write path at a wave, not a
   context-exhaustion exception.
4. **harness-efficiency — UPGRADE.** Add swarm economics: measure the real break-even
   (instances × wall_ms vs serial) and feed it back to the worthiness gate (the ~1.5k
   tokens/instance threshold is currently a guess). Watch over-decomposition as a regression.
5. **guild-conformity — UPGRADE (swarm-close).** The orchestrator runs the conformity check
   ONCE after all workers finish — workers never run it (intermediate states would fail).
6. **models.json — small addition.** A `swarm` policy block (`max_instances:5`,
   `worker_model:"brain"`) + clarify the Bench duty (model-swarm vs instance-swarm). No new
   seat — Brain already is the worker.

### Broad-sweep finds (81 other skills)
- **Swarm-ready exemplars:** `graphify` already fans out subagents per file-chunk
  correctly — make it the canonical example. `multimodal-model-wrappers` (has
  batch_run/run_concurrently) is the doer-runner foundation a swarm should reuse, not
  reinvent.
- **Deploy-as-instances candidates:** `code-review-craft ×N` (needs a finding-merge/dedup
  contract), `bug-fix-workflow` (one worker per bug above ~5), `spec-driven-development`
  (its `[P]` parallel tasks → hand to a swarm).
- **Defensive:** `claude-code-hooks` — add "never spawn a subagent from a hook body" (hooks
  block the session).
- **Merge candidate:** `guild-sync` + `portability-audit` → one `guild-deploy` skill, two
  modes (device-sync · project-deploy); near-identical audit→reconcile procedure.
- **Thin stub:** `strategies-review` — flesh out or absorb into `trading-strategy`.

### Recommended route (revised wave order — folds skills in)
- **Wave 0** — `decompose-and-swarm` skill **+** weapon-utility swarm clause (they are one
  doctrine unit; the clause makes the new skill legal).
- **Wave 1** — schema (`swarm`/`stage`) + `workflow-forge` authoring upgrade + models.json
  `swarm` block + gen_workflows_lite pass-through.
- **Wave 2** — Butler runs a real disjoint-file swarm; `conquering-campaign` + `guild-conformity`
  swarm-close upgrades land here (campaign deploys swarms; conformity closes once).
- **Wave 3** — brief/dashboard `×N` display; `members-formation` `swarm` arrangement;
  `high-alert` doc patch.
- **Wave 4 (deferred)** — worktrees (same-file).
- **Wave 5** — guardrails SW1–SW5 + MAX_SWARM in conformity_check.py; `harness-efficiency`
  swarm-economics; cross-ref patches (ultra-brainstorming, storm-investigation,
  safe-agentic-orchestration).
- **Separate later:** `guild-sync`+`portability-audit` merge; `code-review-craft`/`bug-fix-workflow`
  swarm modes; `strategies-review` stub; `claude-code-hooks` defensive note. These are
  swarm-adjacent, not blockers.
