---
name: weapon-utility
description: "The numeric usage-level doctrine: every member, skill, and workflow has a LEVEL derived solely from append-only invocation logs, never conferred. Level measures usage (reliance), not capability. XP = invocation count; curve: cost(1→2)=10, cost(n→n+1)=floor(1.1×prev+1) → L2=10, L3=22, L4=36, L5=52, … Seams: skills per-fire, workflows once-per-turn, members per-dispatch. KNOWN GAP (v4.1): skill usage is captured ONLY when a skill fires as the literal top-level Skill tool — when a member/subagent applies a skill by Reading its SKILL.md, nothing is recorded, so ~125/127 skills read as never-invoked. Level-1 / 0-XP 'retire it' calls are therefore NOT trustworthy until capture also covers the Read-of-SKILL.md and subagent paths. Point: surface unused craft for review, and load-bearing craft so edits there count as regressions. Triggers: 'what's the level', 'how much is this used', 'usage meter', 'invocation log', 'should we retire this'. Universal skill — every member reads it."
metadata:
  version: 4.1.0
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

Three namespaces, three append-only usage streams:

| Namespace | What it tracks | Capture seam |
|---|---|---|
| **members** | dispatch counts per agent | per-dispatch — one row per `delegate_task` to that agent |
| **skills** | fire counts per skill | per-fire — **but only the literal top-level Skill-tool fire (see gap below)** |
| **workflows** | gate crossings per workflow | once-per-turn — one row per turn that crossed that workflow's gate |

A "dispatch" for a member = one `delegate_task` to that agent. A "workflow" hit = one turn that
crossed that workflow's gate. A "fire" for a skill is *meant* to be one application of the skill —
but see the gap immediately below. The seam is the only place that writes; everything else reads.

## Known gap — the skills seam under-counts (v4.1, unfixed)

The skills counter is, right now, **structurally meaningless** and its numbers must not be trusted:

- Skill usage is recorded **only when a skill fires as the literal top-level `Skill` tool**.
- The *dominant* way skills are actually applied is invisible to that capture: a member or a spawned
  subagent applies a skill by **Reading its `SKILL.md`** and following it. That Read is not a
  top-level `Skill` fire, so nothing is recorded. The whole subagent path is likewise uncounted.
- Result: roughly **125 of 127** skills read as *never-invoked* — not because they are dead, but
  because the seam never saw the Read-of-`SKILL.md` and subagent applications that carried them.

**Consequence for this skill's own promise.** The "level-1 / 0-XP → owed a review, maybe retire"
cue below is the whole point of the meter, and for skills it is **not trustworthy until the capture
seam also counts the Read-of-`SKILL.md` path and the subagent path.** Until then: treat a low skill
level as *"unmeasured,"* not *"unused,"* and do **not** retire, merge, or downweight a skill on the
strength of its skill-level alone. The members (per-dispatch) and workflows (once-per-turn) seams are
not affected by this gap — only the skills namespace. The fix (broaden capture to the Read-of-
`SKILL.md` and subagent paths) is recorded as a finding for the post-freeze queue.

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

The curve is **fixed and shared** across all three namespaces; do not re-derive per skill or per
workflow. The grow-rate (1.1×+1) is the gentle curve the XP brief locked in: early levels are cheap
to climb, later levels cost real usage. `level_from_xp(xp)` returns `{xp, level, xpIntoLevel,
xpForNextLevel}`.

## How a level is resolved

1. A resolver reads each namespace's usage stream **once**, caches the counts, and applies
   `level_from_xp` per id. A failed/unreadable stream resolves every id in that namespace to level 1,
   0 XP — resolution is **fail-soft by design** and must never crash a build or a caller.
2. The resolved level is stamped onto the id (the dashboard reads it; cards show the numeric badge +
   a `level·version` tooltip on hover).
3. The dashboard surfaces two views from the same stamp:
   - **High level** → load-bearing craft. Edits here are treated as **regressions** by review:
     a level-7 skill changing shape is a bigger deal than a level-1 skill doing it.
   - **Low level / 0 XP** → *candidate* unused craft. For members and workflows this is a real review
     cue (promote, merge, or retire — a human decides). **For skills it is currently a false signal**
     — see the known gap above — so read a low skill level as "unmeasured," not "dead."

## Trigger phrases

This skill is the right answer when the user asks:

- "what's the level of X" / "how loaded is X" / "how much is X used"
- "usage meter" / "invocation log" / "how many times has X fired"
- "should we retire X" / "is X still earning its keep" / "what's dead weight"

Universal skill — every member reads it. It does **not** answer model-selection questions; if
the user wants to know "which Claude model runs this job", read the member's `model:` frontmatter
and the registry (`models.json`), not here. And when the question is "should we retire this *skill*",
lead with the caveat: the skill-usage numbers under-count today and can't decide a retirement.

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

Own skill. Bump `metadata.version` on any change (PATCH: wording/refs · MINOR: a new curve point,
new namespace, or a documented gap/caveat in the seam · MAJOR: a change to the level contract or the
seam model). The curve constants are the canonical truth — any change there must bump MAJOR here.

## Changelog
- **4.1.0** — **Skills-usage seam is under-counting — documented, not yet fixed.** Evidence: ~125 of 127 skills read as *never-invoked* because skill usage is captured only when a skill fires as the literal top-level `Skill` tool, while the dominant path — a member or subagent applying a skill by **Reading its `SKILL.md`** — records nothing, and the subagent path is uncounted too. New §Known gap makes the counter's blind spot explicit and rules that the level-1 / 0-XP "retire this" cue is **not trustworthy for skills** until capture also covers the Read-of-`SKILL.md` and subagent paths; low skill level now reads as "unmeasured," not "unused." Members (per-dispatch) and workflows (once-per-turn) seams are unaffected. Phrased mechanism-neutrally (captured-vs-missed *paths*, not hook names) so it stays true across the retired hook and the current DB-view capture. The broaden-capture fix is queued as a finding. Documented seam gap → MINOR.
- **4.0.0** — **Purpose split: usage-level meter (this skill) vs. model selection (elsewhere).** The skill is no longer about *which model a member runs as*; that contract now lives in the model registry (`models.json`) and each member's `model:` frontmatter. This skill is now the **usage-level doctrine**: every member, skill, and workflow carries a numeric LEVEL derived solely from append-only invocation logs; the level curve (cost(1→2)=10, cost(n→n+1)=floor(1.1×prev+1) → L2=10, L3=22, L4=36, L5=52, …) is the canonical truth; the seams are members per-dispatch, skills per-fire, workflows once-per-turn; the dashboard surfaces both load-bearing (high level) and unused (level-1 / 0 XP) craft. Universal skill — every member reads it. Trigger phrases: "what's the level", "how much is this used", "usage meter", "invocation log", "should we retire this". Retires the entire v3.x model-selection body — that content now lives in `models.json` + the member cards + the `decompose-and-swarm` skill. Selection-contract change → MAJOR.
- **3.2.0** — **Each member runs as its own Claude model (HARD RULE).** New §Each member's model: when a member does work it runs as the single Claude model named in its `model:` frontmatter — `opus` (the Architect), `haiku` (the Quartermaster), `sonnet` (everyone else), with the Butler being the live session. There is no separate provider or backend to route through; the member IS the Claude model. Bulk or parallel work is done by that model fanning out to Claude subagents (Task tool), never by handing off to an external engine. New model rule → MINOR.
- **3.1.1** — **Model roster re-sync.** The 3.0.0 universalization moved the model list into `models.json` but the prose still named retired non-Claude models. Registry truth is now the three Claude models only (`opus`/`sonnet`/`haiku`); updated the model bullets and the example to match. Refs/wording → PATCH.
- **3.1.0** — **Member-instance swarm clause.** Adds the Butler's
  [[decompose-and-swarm]] path: a member may fan its work out to N parallel Claude subagents. Each
  instance runs as the member's Claude model (Sonnet, tool-capable) — the same model the member
  runs as, since every member IS a Claude model. The Butler (the live session, Opus) coordinates +
  integrates and reviews the aggregate diff. Instances never commit independently, cross-edit, or
  spawn sub-instances. New fan-out rule → MINOR.
- **3.0.0** — **Universal roster (three Claude models).** The roster is no longer nine hand-kept per-member loadouts — it is ONE set of three Claude models (`opus`/`sonnet`/`haiku`) defined in `models.json`, with each member's `model:` frontmatter naming one. New §The roster is universal. Each member's model is DERIVED from the registry; per-member `weapons:` deleted (drift class killed); conformity retired the old loadout checks. Selection-contract change → MAJOR. Phase 2–4 of the Architecture Build.
- **2.2.0** — New §The three Claude models, emitted to guild-data. Phase 1 of the Architecture Build (additive; the full per-member→universal rewrite is Phase 2). New model doctrine → MINOR.
- **2.1.1** — Removed a retired non-Claude model reference from the escalation list and the availability example (model dropped from the roster — Strategic Audit 2026-06-28). Refs → PATCH.
- **2.1.0** — **Swarm fan-out.** New §Swarm fan-out maps three ideas onto the Claude-subagent fan-out: **(1)** split a wave into disjoint slices and spawn one Claude subagent per slice, in parallel. **(2) mid-flight slice re-spawn** — a failed/empty subagent result is *a slice to relaunch, not a dead job*: re-spawn that one slice with the same brief; only an exhausted retry budget for that slice fails up to the coordinator. **(3) stable-coordinator / swappable-workers** — the coordinator (the live session, a Claude model) is the stable monitor holding the plan and the tool calls; the subagents are the replaceable workers — never put the plan or the commit on a worker that can fail. New fan-out doctrine → MINOR.
- **2.0.0** — **A member IS the model it runs as (`model:`).** Redefines the member's mind: the **member runs as its session model** (`model:`) — the live Claude model that thinks and orchestrates in a session — NOT "whichever thinker leads a loadout." The dashboard now flags each member's **MODEL** on its cards; conformity enforces that the named model is one of the three Claude models. Selection-contract change → MAJOR.
- **1.8.0** — **Run no model — script it.** New lead rule: before spawning any subagent, ask whether the job needs a *model* at all. An exact, mechanical transform (field-preserving JSON merge, literal extraction, deterministic rename) is a **script**, not a spawn — an LLM silently drops a field or rewords a value on a precision-critical merge, where a `node -e` eval + Python merge will not. Spawn a Claude subagent only for generative/judgemental work. Mined from the model-armory consolidation, where the 15×16-field registry merge was done by script precisely to avoid transcription loss. New rule → MINOR.
- **1.7.0** — **Roster consolidation.** Consolidated all model facts into one registry
  `star-alliance-arsenal/models.json` (the three Claude models + `seats.brain`); the routing gate and
  the model docs now all DERIVE from it instead of hand-copying. New roster classification → MINOR.
- **1.6.0** — New §Cost-per-tier baseline: documents how to read the tier split, defines decision rules for tier calibration, and restates the safety-first order (stakes check before any model-mix change). New doctrine → MINOR.
- **1.5.0** — **Batched subagent fan-out.** Named the concrete mechanism behind the fan-out: spawn several Claude subagents in a single message (multiple Task calls) so they run concurrently, and collect the ordered results; a failed slice comes back to be re-spawned. Prior to this the skill preached "fan out in parallel" (1.2.0) but never pointed at the cheap path. The plan→do→review loop is unchanged — batching only removes the per-call tax. Mined from the harness-efficiency build (Phase 2). New mechanism doctrine → MINOR.
- **1.4.0** — **The tool boundary (hard rule).** Every member is a Claude model, so it wields Edit/Write/Bash/git/MCP/computer-use directly — there is no non-Claude helper to hand a tool call to. When a big generative slice is fanned out, each Claude subagent authors its own bytes and the coordinator reviews and integrates. Forbids the old category error of routing a tool call to a non-Claude engine.
- **1.3.0** — Named `opus` the **deepest model** (the Architect) and clarified the Claude-only fallback: work always runs on a Claude model, so there is no non-Claude fall-through to stall on. Conformity enforces that every member's model is one of the three Claude models.
- **1.2.0** — **Parallel subagents.** A member may now fan its work out to several Claude subagents at once — each on an independent slice, with the member reviewing every return against the plan. Previously fan-out was strictly one-at-a-time; that is now the **floor, not the ceiling**. Layers on top of [[decompose-and-swarm]].
- **1.1.1** — Added **"Sizing a big subagent job"** to the plan→do→review loop: for large reads/generations, split the work into chunks, spawn one Claude subagent per chunk, and treat a mid-sentence draft as truncation → re-run larger. Mined from the `japanese-candlesticks` source-distillation run.
- **1.1.0** — Model-roster reclass. The roster is the three Claude models (`opus`/`sonnet`/`haiku`);
  `opus` is the deepest (the Architect), `haiku` the lightest (the Quartermaster), `sonnet` the
  workhorse everyone else runs as. All member cards reordered to name their single Claude model.
- **1.0.0** — Initial release. Defines the plan → do → review loop, the one-model-per-member
  default, and the swarm exception (fan out to parallel Claude subagents, the coordinator
  consolidates). Positioned as the atomic layer beneath members-formation and decompose-and-swarm.