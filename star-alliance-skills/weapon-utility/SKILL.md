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

- Not **weapon selection** — that contract has moved out of this skill. The arsenal (Brain /
  Doer / Critic / Bench) is defined once in `star-alliance-arsenal/models.json` → `seats`; which
  weapon a member draws for a given job lives in the cross-system dispatch layer and the
  `dual-model-review` skill, not here. v4.0.0 retires the old "which weapon do I draw" content;
  the universal-seat doctrine is documented in `models.json` + `dispatch.py` + the agent SOULs.
- Not **routing** — *which member* works a request is the Butler's `members-formation`. This
  skill is one layer below that, measuring usage once a member (and its weapons) is already chosen.
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

Universal skill — every member reads it. It does **not** answer weapon-selection questions; if
the user wants to know "which model should I draw for this job", route to the arsenal registry
(`models.json` → `seats`) and the dispatch layer, not here.

## Where it sits

```
members-formation   →  which MEMBER works (the Butler)
   weapon-utility    →  how RELIED-ON each member / skill / workflow is  ← here
   dual-model-review →  which WEAPON to draw + the critic loop
   ultra-brainstorming →  fan every thinker at once
```

`weapon-utility` (usage), `dual-model-review` (selection), and `ultra-brainstorming` (fan-out)
are three orthogonal axes of the arsenal contract. v4.0.0 collapses the old "which weapon do I
draw" content out of this skill; selection doctrine lives where the seats are defined.

## Versioning

Own skill. Bump `metadata.version` on any change (PATCH: wording/refs · MINOR: a new curve point
or new namespace · MAJOR: a change to the level contract or the seam model). Then
`python3 build.py`. The curve constants in `xp.py` are the canonical truth — any change there
must bump MAJOR here.

## Changelog
- **4.0.0** — **Purpose split: usage-level meter (this skill) vs. weapon selection (elsewhere).** The skill is no longer about *which weapon a member draws*; that contract has moved to the arsenal registry (`models.json` → `seats`) and the cross-system dispatch layer. This skill is now the **usage-level doctrine**: every member, skill, and workflow carries a numeric LEVEL derived solely from append-only invocation logs (`tools/xp.py`); the level curve (cost(1→2)=10, cost(n→n+1)=floor(1.1×prev+1) → L2=10, L3=22, L4=36, L5=52, …) is the canonical truth; the seams are members per-dispatch (`dispatch-log`), skills per-fire (skill-seam PostToolUse), workflows once-per-turn (`workflow-gate`); build.py stamps level onto guild-data; the dashboard surfaces both load-bearing (high level) and unused (level-1 / 0 XP) craft. Universal skill — every member reads it. Trigger phrases: "what's the level", "how much is this used", "usage meter", "invocation log", "should we retire this". Retires the entire v3.x weapon-selection body (Brain/Doer/ doctrine, thinker↔doer loop, SWARM dispatch, per-seat backend rule, cost-per-tier baseline) — that content lives in `models.json` + `dispatch.py` + the agent SOULs + the `dual-model-review` skill going forward. Selection-contract change → MAJOR.
- **3.2.0** — **Per-seat Hermes backend rule (HARD RULE).** New §Each seat loads through its own backend: when a member's doer-grade work runs inside its Hermes profile (`tools/dispatch.py`), the three seats do NOT share one provider — each loads through its own backend as named in `models.json`. **minimax-m3** (Doer) → `backend: "minimax-direct"`, direct API (NOT the cloud-pull route). **glm-5.2** (Brain / escalation, also Critic fallback) → `backend: "ollama-cloud"`, `cloud_tag: "glm-5.2:cloud"`. **kimi-k2.7** (Critic) → `backend: "ollama-cloud"`, `cloud_tag: "kimi-k2.7-code:cloud"`. Cross-routing a seat onto another seat's provider was the recurring Hermes dispatch stall; the rule names the canonical `models.json` backends so an unavailable seat falls through to the loop's next-of-kind instead of silently retrying on the wrong provider. New availability/selection rule → MINOR.
- **3.1.1** — **Critic-seat re-sync.** The 3.0.0 universalization moved the arsenal into `models.json` seats but the prose still named the OLD critic (`glm-5.2`) and the OLD example (Opus-brain + GLM-critic). Registry truth is now Critic default `kimi-k2.7` (glm-5.2 → deepseek-v4-pro fallback) over GLM-5.2 brains — a GLM critic would now share the brain's family and violate the ST rule, which is precisely why the seat moved. Updated the Critic bullet, the Critic-seat default, and the family example to match. Refs/wording → PATCH.
- **3.1.0** — **Member-instance swarm clause (second exception).** Adds the Butler's
  [[decompose-and-swarm]] path as a second exception to the one-thinker-per-member rule. Each
  instance runs as the member's Brain (tool-capable Claude model, e.g. Sonnet) — NEVER a
  doer-tier model (minimax-m3 / Ollama weapons cannot hold Edit/Write/Bash tools). Doer seat
  still works inside each instance; Butler (Opus) coordinates + integrates; Critic (glm-5.2)
  reviews the aggregate diff. Instances never commit independently, cross-edit, or spawn
  sub-instances. New selection rule (second thinker exception) → MINOR.
- **3.0.0** — **Universal arsenal (4 seats).** The arsenal is no longer nine hand-kept per-member loadouts — it is ONE universal set of seats (Brain/Doer/Bench) defined in `models.json` → `seats`. New §The arsenal is universal. Only the **Brain/Doer/Bench_pull.py`. build.py now DERIVES each member's arsenal from the seats; per-member `weapons:`/`weaponsDesc` deleted (drift class killed); conformity retired A/PD/W/S/WT, added ST. Selection-contract change (source of the arsenal) → MAJOR. Phase 2–4 of the 4-seat Architecture Build.
- **2.2.0** — ** (third seat).** New §The : Brain/Doer/Bench), emitted to guild-data. Phase 1 of the 4-seat Architecture Build (additive; the full per-member→universal arsenal rewrite is Phase 2). New seat doctrine → MINOR.
- **2.1.1** — Removed the dead `gpt-5.5` reference from the escalation-thinker list and the availability example (model retired from the arsenal — Strategic Audit 2026-06-28). Refs → PATCH.
- **2.1.0** — **Swarm dispatch (mined from SWARM Parallelism, `yandex-research/swarm`).** New §Swarm dispatch maps three ideas from training over unreliable/heterogeneous/preemptible nodes onto the doer fan-out: **(1) throughput-weighted fan-out** — split a mixed doer pool ∝ each doer's measured speed/reliability (give `minimax-m3` the bulk), not round-robin; heterogeneity self-balances. **(2) mid-flight slice reroute** — a `None` in the `delegate_many` result is a *preempted peer, not a dead job*: re-dispatch that one slice to the next doer right (same plan/prompt), the left→right doer-fallback applied at SLICE granularity mid-flight instead of whole-job; only an exhausted pool for that slice fails up to the thinker. Closes the prior gap where the skill cited `delegate_many`'s `None` contract (1.5.0) but gave no doctrine for handling it. **(3) stable-coordinator / swappable-workers** — names the *why* behind reroute: the thinker (Claude brain) is SWARM's stable cheap monitor (always reachable, holds plan + tool buttons); doers are the preemptible GPU peers — never put the plan or tool calls on a weapon that can vanish. New dispatch doctrine → MINOR.
- **2.0.0** — **Brain = personality (the model the member runs as).** Redefines the member's mind: the **brain is its session model** (`model:`) — the live model that actually thinks and orchestrates in a session — NOT "whichever thinker leads the arsenal." `opus` and the other thinkers are reframed as **escalation weapons** the brain delegates to, not the member's identity. The dashboard now flags the **BRAIN** (session-model weapon) and the **DOER** (prime doer, `minimax-m3`) on each member's cards; `conformity_check.py` replaces the `PT` (prime-thinker==opus) check with **`BR`** (the session model is a carried, thinking weapon) + **`PD`** (prime doer leads). Supersedes the §5 "prime thinker = first thinker weapon = opus" decision. Selection-contract change → MAJOR.
- **1.8.0** — **Draw no weapon — script it.** New lead rule in §Drawing the right weapon: before picking a thinker or doer, ask whether the job needs a *model* at all. An exact, mechanical transform (field-preserving JSON merge, literal extraction, deterministic rename) is a **script**, not a summon — an LLM doer *or* thinker silently drops a field or rewords a value on a precision-critical merge, where a `node -e` eval + Python merge will not. Draw a model only for generative/judgemental work. Mined from the model-armory consolidation, where the 15×16-field registry merge was done by script (not minimax) precisely to avoid transcription loss. New selection rule → MINOR.
- **1.7.0** — **`gemma4` reclassed doer → thinker.** It now joins the thinker bench (light, fast
  second mind, esp. content/marketing) — the guild leans on `minimax-m3` (direct API) as the prime
  doer, so the Ollama bench is read as thinkers. `conformity_check.ROLE` updated to match. Also
  enforced **≤ 3 Ollama thinkers per member** (best-3-by-craft): trimmed `nemotron-3-ultra` from
  butler/architect/strategist/merchant and `qwen3.5` from butler; added `gemma4` to the-herald.
  `nemotron-3-ultra`/`qwen3.5` stay valid reserve weapons, just not in any loadout. Also
  **consolidated all model facts into one registry** `star-alliance-arsenal/models.json` (role ·
  backend · cloud_tag · status · pull · weight); `summon.py`, `conformity_check.py`, the
  weapon-gate hook, `serve.cjs`, `build.py`, and the model docs now all DERIVE from it instead of
  hand-copying. New role classification → MINOR.
- **1.6.0** — New §Cost-per-tier baseline: documents how to read the now-reliable tier split in `efficiency_report.py`, defines decision rules for tier calibration (when to loosen small-signals vs leave it), and restates the safety-first order (stakes check before any model-mix change). Depends on B1 sidecar fix (turn-cost.jsonl `tier` field now reliable). New doctrine → MINOR.
- **1.5.0** — **Batched doer fan-out.** Named the concrete mechanism behind the always-available doer fan-out: `minimax.py --batch <file.jsonl>` (one process, one keep-alive HTTPS connection, ordered JSONL results) and its wrapper `guild/delegate.py:delegate_many(prompts)` (ordered list, failed slice → `None`). Prior to this the skill preached "fan doers in parallel" (1.2.0) but never pointed at the cheap path, so N-way doer splits kept paying N subprocess spawns + N TLS handshakes. The thinker↔doer review loop is unchanged — batch only removes the per-call tax; minimax-only today, other backends degrade to a sequential loop with the same ordered contract. Mined from the harness-efficiency build (Phase 2). New mechanism doctrine → MINOR.
- **1.4.0** — **The tool boundary (hard rule).** Added an explicit section stating a doer **returns content as text** and **never invokes tools** — Edit/Write/Bash/git/MCP/computer-use are wielded **only by the thinker** (a Claude model). Splits "write" into *author content* (doer) vs *invoke the write tool* (thinker): doer authors the bytes, thinker reviews then runs `Write`/`Edit` itself to commit — no re-authoring. Forbids the category error of summoning a non-Claude doer to "use" a Claude Code tool; if a slice needs a tool inside the doer's own run, that is the Claude-only-tool case → draw `sonnet`. Closes the-developer's mistake of handing a tool call to a non-Claude model.
- **1.3.0** — Named `opus` the **prime thinker** (best mind, first thinker in every arsenal) alongside `minimax-m3` the prime doer, and added the **Sonnet Claude-only-tool fallback**: when a doer needs a tool only Claude models can run, draw `sonnet` (the dual at the tail) directly — an expected fall-through, not a failure — so the run never stalls. `conformity_check` now enforces minimax-m3-first, opus-first-thinker, sonnet-last.
- **1.2.0** — **Parallel doers.** A member's thinker may now dispatch several doer agents at once — many of one doer model or a mix of different doer models — each on an independent slice, with the thinker reviewing every return against the plan. Previously the doer side was strictly one-at-a-time (next doer only on failure); that is now the **floor, not the ceiling**. Thinker stays one-per-member except under [[ultra-brainstorming]], which now layers thinker fan-out on top of the always-available doer fan-out.
- **1.1.1** — Added **"Sizing a big doer job"** to the thinker↔doer loop: for large reads/generations the backend default output cap (16k) and timeout (180s) silently truncate, so pass `--max-tokens`/`--timeout` through `summon.py` (now translated per backend — `--max-tokens` for minimax, `--num-predict` for cloud), loop chunks one at a time, and treat a mid-sentence draft as truncation → re-run larger. Mined from the `japanese-candlesticks` source-distillation run.
- **1.1.0** — Thinker-bench reclass. `glm-5.2`, `kimi-k2.7`, `nemotron-3-ultra`, `qwen3.5` moved
  from doer/dual → **thinker** (join `opus`, `gpt-5.5`, `deepseek-v4-pro`). `minimax-m3` named the
  **prime doer** — every member's first-drawn hand. Doer pool now `minimax-m3`, `haiku`, `gemma4` +
  forge doers; `sonnet` the sole remaining dual. All 9 member arsenals reordered minimax-first.
- **1.0.0** — Initial release. Defines thinker vs doer weapons, the plan → do → review loop,
  left-to-right priority selection with doer-fallback and availability rules, one-weapon-at-a-time
  default, and the ultra-brainstorming exception (all thinkers fan out, top thinker consolidates
  before the doer). Positioned as the atomic layer beneath members-formation and ultra-brainstorming.
