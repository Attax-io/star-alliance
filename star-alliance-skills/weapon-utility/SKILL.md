---
name: weapon-utility
description: "The numeric usage-level doctrine: every member, skill, and workflow has a LEVEL derived solely from append-only invocation logs, never conferred. Level measures usage (reliance), not capability. XP = invocation count; curve: cost(1→2)=10, cost(n→n+1)=floor(1.1×prev+1) → L2=10, L3=22, L4=36, L5=52, … Seams: skills per-fire (PostToolUse hook), workflows once-per-turn (workflow-gate), members per-dispatch (dispatch-log). Derivation in tools/xp.py only; build.py stamps level onto guild-data; dashboard shows numeric badges + level·version tooltips. Point: surface unused craft (level 1/0 XP) for review, and surface load-bearing craft so edits there are treated as regressions. Triggers: 'what's the level', 'how much is this used', 'usage meter', 'invocation log', 'should we retire this'. Universal skill — every member reads it; it does not select weapons anymore."
metadata:
  version: 4.0.0
type: Skill

---
# Weapon Utility — numeric usage levels (what is used, not what is selected)

This skill is the guild's **usage-meter**. Every member, skill, and workflow carries a numeric
**LEVEL** derived **solely** from append-only invocation logs. Level measures **reliance** —
how often this thing has been fired — not capability. A high level means the guild leans on it
heavily; a level-1 (or 0-XP) item means nobody has touched it since install and it is owed a
review (delete? merge? retrain?). Levels are never conferred by hand, never upweighted for
"important" work, and never faked in a build: the log is the single source of truth.

Know what this skill is *not*:

- Not **model selection** — that contract has moved out of this skill. The three Claude models
  (`opus`, `sonnet`, `haiku`) are defined once in `star-alliance-arsenal/models.json`, and each
  member's `model:` frontmatter names the one it runs as; when to fan a job out to parallel Claude
  subagents lives in `decompose-and-swarm`, not here. v4.0.0 retires the old "which model do I run
  as" content; the model doctrine is documented in `models.json` + the member cards.
- Not **routing** — *which member* works a request is the Butler's `members-formation`. This
  skill is one layer below that, measuring usage once a member (and its Claude model) is already chosen.
- Not **fitness for retirement** — the ledger records usage; deciding whether a level-1 item is
  *worth keeping* is a human judgement the Quartermaster owns.

## The seam where each level is recorded

Three namespaces, three hooks, all append-only JSONL:

| Namespace | What it tracks | Where the log lives | Hook that writes it |
|---|---|---|---|
| **members** | dispatch counts per agent | `.claude/state/dispatch-log.jsonl` (keyed on `agent`) | `dispatch-log` (per-dispatch) |
| **skills** | fire counts per skill | `.claude/state/xp-log.jsonl` (rows where `type=skill`) | skill-seam (per-fire, PostToolUse) |
| **workflows** | gate crossings per workflow | `.claude/state/xp-log.jsonl` (rows where `type=workflow`) | `workflow-gate` (once-per-turn) |

A "fire" for a skill = one tool invocation inside the skill's seam. A "dispatch" for a member =
one `delegate_task` to that agent. A "workflow" hit = one turn that crossed that workflow's gate.
The seam is the only place that writes; everything else reads.

## The level curve

XP = invocation count. Level is the highest tier whose cumulative cost the XP meets or exceeds.

```
step cost(1→2) = 10
step cost(n→n+1) = floor(1.1 × cost(n-1→n) + 1)   → 10, 12, 14, 16, ...

cumulative thresholds (the XP needed to REACH that level):
  L2 = 10
  L3 = 22
  L4 = 36
  L5 = 52
  L6 = 71
  L7 = 93
  L8 = 118
  ...
```

The canonical source is `tools/xp.py` — `level_from_xp(xp)` returns `{xp, level, xpIntoLevel,
xpForNextLevel}`. The curve is **fixed and shared** across all three namespaces; do not
re-derive per skill or per workflow. The grow-rate (1.1×+1) is the gentle curve the XP brief
locked in: early levels are cheap to climb, later levels cost real usage.

## How a level is resolved

1. The build pipeline (or any caller) calls `xp.resolve_all(members, skills, workflows)` with
   the id lists it already has on hand.
2. `resolve_all` reads each log **once** (`count_dispatch_log` + `count_xp_log`), caches the
   counts, and calls `level_from_xp` per id. A failed/unreadable log resolves every id in that
   namespace to level 1, 0 XP — the module is **fail-soft by design** and must never crash a
   build or a caller.
3. The build stamps the resolved level onto the emitted `guild-data` artifact (the dashboard
   reads it; cards show the numeric badge + a `level·version` tooltip on hover).
4. The dashboard surfaces two views from the same stamp:
   - **High level** → load-bearing craft. Edits here are treated as **regressions** by review:
     a level-7 skill changing shape is a bigger deal than a level-1 skill doing it.
   - **Low level / 0 XP** → unused craft. The level-1 floor is a *review cue*: should this be
     promoted, merged into a sibling, or retired? The dashboard flags it; a human decides.

## Trigger phrases

This skill is the right answer when the user asks:

- "what's the level of X" / "how loaded is X" / "how much is X used"
- "usage meter" / "invocation log" / "how many times has X fired"
- "should we retire X" / "is X still earning its keep" / "what's dead weight"

Universal skill — every member reads it. It does **not** answer model-selection questions; if
the user wants to know "which Claude model runs this job", read the member's `model:` frontmatter
and the registry (`models.json`), not here.

## Where it sits

```
members-formation   →  which MEMBER works (the Butler)
   weapon-utility    →  how RELIED-ON each member / skill / workflow is  ← here
   decompose-and-swarm →  when to fan a job out to parallel Claude subagents
```

`weapon-utility` (usage) and `decompose-and-swarm` (fan-out) are two orthogonal axes: one measures
reliance, the other decides when one member's Claude model should split its work across several
Claude subagents. v4.0.0 collapses the old "which model do I run as" content out of this skill;
each member's model is named in its own frontmatter.

## Versioning

Own skill. Bump `metadata.version` on any change (PATCH: wording/refs · MINOR: a new curve point
or new namespace · MAJOR: a change to the level contract or the seam model). Then
`python3 build.py`. The curve constants in `xp.py` are the canonical truth — any change there
must bump MAJOR here.

## Changelog
- **4.0.0** — **Purpose split: usage-level meter (this skill) vs. model selection (elsewhere).** The skill is no longer about *which model a member runs as*; that contract now lives in the model registry (`models.json`) and each member's `model:` frontmatter. This skill is now the **usage-level doctrine**: every member, skill, and workflow carries a numeric LEVEL derived solely from append-only invocation logs (`tools/xp.py`); the level curve (cost(1→2)=10, cost(n→n+1)=floor(1.1×prev+1) → L2=10, L3=22, L4=36, L5=52, …) is the canonical truth; the seams are members per-dispatch (`dispatch-log`), skills per-fire (skill-seam PostToolUse), workflows once-per-turn (`workflow-gate`); build.py stamps level onto guild-data; the dashboard surfaces both load-bearing (high level) and unused (level-1 / 0 XP) craft. Universal skill — every member reads it. Trigger phrases: "what's the level", "how much is this used", "usage meter", "invocation log", "should we retire this". Retires the entire v3.x model-selection body — that content now lives in `models.json` + the member cards + the `decompose-and-swarm` skill. Selection-contract change → MAJOR.
- **3.2.0** — **Each member runs as its own Claude model (HARD RULE).** New §Each member's model: when a member does work it runs as the single Claude model named in its `model:` frontmatter — `opus` (the Architect), `haiku` (the Quartermaster), `sonnet` (everyone else), with the Butler being the live session. There is no separate provider or backend to route through; the member IS the Claude model. Bulk or parallel work is done by that model fanning out to Claude subagents (Task tool), never by handing off to an external engine. New model rule → MINOR.
- **3.1.1** — **Model roster re-sync.** The 3.0.0 universalization moved the model list into `models.json` but the prose still named retired non-Claude models. Registry truth is now the three Claude models only (`opus`/`sonnet`/`haiku`); updated the model bullets and the example to match. Refs/wording → PATCH.
- **3.1.0** — **Member-instance swarm clause.** Adds the Butler's
  [[decompose-and-swarm]] path: a member may fan its work out to N parallel Claude subagents. Each
  instance runs as the member's Claude model (Sonnet, tool-capable) — the same model the member
  runs as, since every member IS a Claude model. The Butler (the live session, Opus) coordinates +
  integrates and reviews the aggregate diff. Instances never commit independently, cross-edit, or
  spawn sub-instances. New fan-out rule → MINOR.
- **3.0.0** — **Universal roster (three Claude models).** The roster is no longer nine hand-kept per-member loadouts — it is ONE set of three Claude models (`opus`/`sonnet`/`haiku`) defined in `models.json`, with each member's `model:` frontmatter naming one. New §The roster is universal. build.py now DERIVES each member's model from the registry; per-member `weapons:` deleted (drift class killed); conformity retired the old loadout checks. Selection-contract change → MAJOR. Phase 2–4 of the Architecture Build.
- **2.2.0** — New §The three Claude models, emitted to guild-data. Phase 1 of the Architecture Build (additive; the full per-member→universal rewrite is Phase 2). New model doctrine → MINOR.
- **2.1.1** — Removed a retired non-Claude model reference from the escalation list and the availability example (model dropped from the roster — Strategic Audit 2026-06-28). Refs → PATCH.
- **2.1.0** — **Swarm fan-out.** New §Swarm fan-out maps three ideas onto the Claude-subagent fan-out: **(1)** split a wave into disjoint slices and spawn one Claude subagent per slice, in parallel. **(2) mid-flight slice re-spawn** — a failed/empty subagent result is *a slice to relaunch, not a dead job*: re-spawn that one slice with the same brief; only an exhausted retry budget for that slice fails up to the coordinator. **(3) stable-coordinator / swappable-workers** — the coordinator (the live session, a Claude model) is the stable monitor holding the plan and the tool calls; the subagents are the replaceable workers — never put the plan or the commit on a worker that can fail. New fan-out doctrine → MINOR.
- **2.0.0** — **A member IS the model it runs as (`model:`).** Redefines the member's mind: the **member runs as its session model** (`model:`) — the live Claude model that thinks and orchestrates in a session — NOT "whichever thinker leads a loadout." The dashboard now flags each member's **MODEL** on its cards; `conformity_check.py` enforces that the named model is one of the three Claude models. Selection-contract change → MAJOR.
- **1.8.0** — **Run no model — script it.** New lead rule: before spawning any subagent, ask whether the job needs a *model* at all. An exact, mechanical transform (field-preserving JSON merge, literal extraction, deterministic rename) is a **script**, not a spawn — an LLM silently drops a field or rewords a value on a precision-critical merge, where a `node -e` eval + Python merge will not. Spawn a Claude subagent only for generative/judgemental work. Mined from the model-armory consolidation, where the 15×16-field registry merge was done by script precisely to avoid transcription loss. New rule → MINOR.
- **1.7.0** — **Roster consolidation.** Consolidated all model facts into one registry
  `star-alliance-arsenal/models.json` (the three Claude models + `seats.brain`); `conformity_check.py`,
  the routing gate, `serve.cjs`, `build.py`, and the model docs now all DERIVE from it instead of
  hand-copying. New roster classification → MINOR.
- **1.6.0** — New §Cost-per-tier baseline: documents how to read the tier split in `efficiency_report.py`, defines decision rules for tier calibration, and restates the safety-first order (stakes check before any model-mix change). Depends on the sidecar fix (turn-cost.jsonl `tier` field now reliable). New doctrine → MINOR.
- **1.5.0** — **Batched subagent fan-out.** Named the concrete mechanism behind the fan-out: spawn several Claude subagents in a single message (multiple Task calls) so they run concurrently, and collect the ordered results; a failed slice comes back to be re-spawned. Prior to this the skill preached "fan out in parallel" (1.2.0) but never pointed at the cheap path. The plan→do→review loop is unchanged — batching only removes the per-call tax. Mined from the harness-efficiency build (Phase 2). New mechanism doctrine → MINOR.
- **1.4.0** — **The tool boundary (hard rule).** Every member is a Claude model, so it wields Edit/Write/Bash/git/MCP/computer-use directly — there is no non-Claude helper to hand a tool call to. When a big generative slice is fanned out, each Claude subagent authors its own bytes and the coordinator reviews and integrates. Forbids the old category error of routing a tool call to a non-Claude engine.
- **1.3.0** — Named `opus` the **deepest model** (the Architect) and clarified the Claude-only fallback: work always runs on a Claude model, so there is no non-Claude fall-through to stall on. `conformity_check` enforces that every member's model is one of the three Claude models.
- **1.2.0** — **Parallel subagents.** A member may now fan its work out to several Claude subagents at once — each on an independent slice, with the member reviewing every return against the plan. Previously fan-out was strictly one-at-a-time; that is now the **floor, not the ceiling**. Layers on top of [[decompose-and-swarm]].
- **1.1.1** — Added **"Sizing a big subagent job"** to the plan→do→review loop: for large reads/generations, split the work into chunks, spawn one Claude subagent per chunk, and treat a mid-sentence draft as truncation → re-run larger. Mined from the `japanese-candlesticks` source-distillation run.
- **1.1.0** — Model-roster reclass. The roster is the three Claude models (`opus`/`sonnet`/`haiku`);
  `opus` is the deepest (the Architect), `haiku` the lightest (the Quartermaster), `sonnet` the
  workhorse everyone else runs as. All member cards reordered to name their single Claude model.
- **1.0.0** — Initial release. Defines the plan → do → review loop, the one-model-per-member
  default, and the swarm exception (fan out to parallel Claude subagents, the coordinator
  consolidates). Positioned as the atomic layer beneath members-formation and decompose-and-swarm.
