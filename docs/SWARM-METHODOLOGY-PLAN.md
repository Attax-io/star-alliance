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

## Decomposition Methodology — grounded by the Learning Pool deep-dive (2026-06-28)

A 4-agent read-only swarm mined `swarm-models`, `safe-agentic-workflow`, `spec-kit`,
`system_prompts_leaks`, `agent-skills`, and `codebase-memory-mcp`. This section is the
evidence-backed answer to "HOW does the Butler split the work" + the prime goal (cheaper via
rough-work-to-cheap-models). It supersedes §3 MOVE 1's hand-wave.

### The economic engine: capable bookends, cheap middle
(from safe-agentic-workflow `README.md:770` stop-the-line + `:565` non-collapsible QA gate)
Cheap delegation is net-cheap ONLY when bracketed by two capable, small gates:
- **FRONT (capable, small):** the thinker SCOUTS + DECOMPOSES + writes the seams. Decomposition
  is a thinker job — never a cheap-model job.
- **MIDDLE (cheap, parallel, bulk):** N workers fill disjoint slices. **Two levels of cheap:**
  (1) workers run as the member BRAIN (Sonnet, tool-capable) instead of the Opus coordinator;
  (2) each worker offloads its OWN rough text to the Doer seat (minimax-m3) internally. The
  saving is "N Sonnet + MiniMax-inside vs one Opus doing all of it serially."
- **BACK (capable, small):** independent Critic (glm-5.2, different family) on the AGGREGATE
  diff + a serialized, revertible merge (one commit per slice → `git revert` = rollback;
  safe-agentic `MERGE-QUEUE-POLICY.md`). A cheap worker never grades or commits its own slice.

### The decomposition procedure (the Butler's actual steps)
Assembled from spec-kit's task algorithm + codebase-memory's scout + Amp's policies.

**MOVE 0 — Worthiness gate (concrete trip condition, from Amp `amp-code.md:454`).**
"Can you name the exact files/symbols to change?" → if YES, do it inline, NO swarm. Swarm only
if each slice needs ≳1.5k output tokens AND can't be stated as "edit these 3 lines in file X."

**MOVE 0.5 — SCOUT the surface (NEW — fills the "boundaries before starting" gap).**
Run codebase-memory (CLI ok, ~3.4k tokens vs ~412k for grep):
- `get_architecture` → clusters = de-facto modules (often cut across folders) = candidate slices.
- `trace_path(boundary, both)` → cross-slice CALLS edges = coupling to declare as a seam.
- `query_graph "MATCH (a:File)-[:FILE_CHANGES_WITH]->(b:File)…"` → latent co-change coupling
  invisible to import graphs.
- `detect_changes(symbols)` → per-slice blast radius (CRITICAL/HIGH/…) sizes the seam.
Fallback if not indexed: manual directory analysis + explicit coupling note in each brief.

**MOVE 1 — Cut `[P]`-safe slices (spec-kit's exact rule, `tasks-template.md:18`).**
A slice is parallel-safe **iff (a) it touches DIFFERENT files than every concurrent slice AND
(b) it depends on no incomplete slice.** Order is mandatory: **Setup → Foundational (BLOCKS all)
→ per-story slices (parallel) → Polish.** Foundational is the synchronization barrier BEFORE
fan-out. Every slice carries explicit file paths; build the file-sets and assert pairwise-empty
intersection (mechanical, now backed by the scout, not a guess).

**MOVE 2 — Contracts-first seams (spec-kit `plan.md:141`).**
Before any worker launches, the thinker writes the seams the workers must agree on (interfaces,
types, names — spec-kit's `data-model.md` + `contracts/`). This is what stops two isolated
workers inventing two names for one boundary.

**MOVE 3 — Self-contained 3-tier brief per worker (Amp `amp-code.md:312` + agent-skills
progressive disclosure `AGENTS.md:163`).** Each worker loses all context — pack the brief:
(1) one-line routing label, (2) core brief <2k tokens (its file slice, the shared contract, the
acceptance test, do-NOT-touch files, the model to use — model is a first-class brief field, per
the Claude Code Agent schema), (3) file excerpts attached ONLY if the slice needs them.

**MOVE 4 — Fan out in one message; PER-SLICE critic; integrate + verify inline; serialized
revertible merge.** Failure isolation per slice (swarm-models `together_llm.py:96`): one worker
fails → re-dispatch just that slice; bounded batch = the Ollama concurrency tier.
**Per-slice critic (REQUIRED — engine-audit fix #1):** as each worker returns, the Butler runs
`evolution/verdict.run_cold(worker_slice_diff)` on that worker's SMALL diff *before* integrating.
This is cheaper + parallel, and it keeps the critic invariant intact — the auto-critic gate skips
diffs >60KB (`verify-gate.py:42,114`), and a swarm's AGGREGATE diff routinely exceeds that, so
without per-slice review the Stop gate would fall to a manual bypass and the "nothing enters
without a critic verdict" invariant becomes theater. Per-slice review means every constituent is
blessed before the aggregate commit; the Stop-hook aggregate review then has a per-slice ledger
trail behind it.

### Skill actions this adds (fold into the wave plan)
- **codebase-memory-mcp skill — UPGRADE:** add a "Swarm Decomposition Scout" section (the 4
  scout calls + the FILE_CHANGES_WITH Cypher recipe + CLI usage) so `decompose-and-swarm`
  cites it by wikilink. (Wave 0/2.)
- **decompose-and-swarm skill — author with the above** MOVES (0, 0.5, 1–4), the quoted `[P]`
  rule, and the 3-tier brief template. (Wave 0.)
- **spec-driven-development skill — light UPGRADE:** add the formal `[P]` rule + the mandatory
  phase structure (Setup→Foundational→stories→Polish) + "every task carries a file path."
- **multimodal-model-wrappers** is the worker-runner foundation (uniform `run`, threadpool,
  batch, retry) — reuse, don't reinvent; do NOT import swarm-models' name-only `ModelRouter`
  (it has a silent-fallthrough bug, `model_router.py:229`).
- **harness-efficiency (Wave 5):** read `Archive/Skills Pool/headroom-main` first — a cost/budget
  gating tool that maps to the worthiness "cheaper-net" check.

### Cited sources
swarm-models `base_llm.py:108`, `together_llm.py:71/96/99`, `base_multimodal_model.py:148`,
`model_router.py:229` · safe-agentic-workflow `README.md:565/770/899`, `spec_template.md:40`,
`DARK-FACTORY-GUIDE.md:290`, `MERGE-QUEUE-POLICY.md` · spec-kit `tasks-template.md:18/163`,
`tasks.md:64/182`, `plan.md:141` · system-prompts `amp-code.md:312/454/466/493`,
`claude-cowork-dispatch.md:14`, `claude-code-2.1.172-opus-4.8.md:62` · agent-skills
`AGENTS.md:163` · codebase-memory `mcp.c:355/389/4191`, `README.md:17`.

## Evolution Engine integration (audit 2026-06-28)

The self-improving engine (SENSE→VERIFY→REMEMBER→DIAGNOSE; INVARIANT: nothing enters the repo
without a critic verdict + a ledger event; Tier-A auto / Tier-B human-gated) was audited against
swarm. **Verdict: TARGETED rework, not a redo — the safety envelope is intact; the three gaps are
all in the observation/review path, mapped onto the existing waves. NOTHING blocks Wave 0 (pure
doctrine).**

| # | Gap (file:line) | Fix | Wave |
|---|---|---|---|
| 1 | Auto-critic skips diffs >60KB (`verify-gate.py:42,114`); a swarm aggregate diff exceeds it → every swarm would drop to manual bypass, invariant becomes theater | **Per-slice critic** in `decompose-and-swarm` MOVE 4: `verdict.run_cold(slice_diff)` per worker before integration (small, parallel, cheaper). No `verify-gate.py` change. | **0 (doctrine) / 2 (live)** |
| 2 | `turn-cost.jsonl` is NOT in the ledger and sub-agent costs are invisible (`scoreboard.py:33`, `turn-cost.py:156`) → engine can't measure swarm economics | Engine **Phase 2**: route per-turn cost into `ledger.jsonl` as a `metric` event + capture per-worker cost (n_workers field). Prerequisite for the worthiness gate's "cheaper-net" empiricism. | **5** (with harness-efficiency; worthiness uses the ~1.5k heuristic until then) |
| 3 | `member-dispatch` uncounted in capability metrics; doer-discipline rule (`engine.py:130`) FALSE-fires on swarm turns (N dispatches, 0 main-thread doer summons) | Add `SWARM_FANOUT` signal to `signals.py` (meta: n_workers, partition, redispatch); emit on fan-out; suppress doer-discipline when present | **2** |
| 4 | No swarm diagnose rules (over-decomposition cost>serial, high re-dispatch = bad partition) | Add 2-3 `engine.py` diagnose rules using the `swarm-fanout` signal + Phase-2 cost data | **5** |
| 5 | Tier-A/B + invariant under N parallel writers | **No change needed** — workers never commit; Butler integrates + commits once; existing surfaces (`arsenal`/`workflows`) already cover the new swarm config | — |

**Blocks Wave 0:** nothing. **Blocks Wave 2 (real runs):** fix #1 (per-slice critic doctrine) and
fix #3 (swarm signal). **Deferred to Wave 5:** fix #2 (cost-into-ledger) + fix #4 (diagnose rules).
The per-slice critic (#1) is also a *win* for the prime goal — it reviews small diffs cheaply in
parallel instead of one expensive aggregate pass.

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
