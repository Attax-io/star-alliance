---
name: weapon-utility
description: "Every member's rule for which weapon (model) to draw and how thinker and doer weapons work together. Thinker weapons read, plan, and prompt the doers; doer weapons do the job and return it; the thinker then reviews the result against the plan and re-prompts the doer until it conforms. A member draws the highest-priority AVAILABLE weapon of the kind the job needs — scanning its arsenal left to right. One thinker plans and reviews and may dispatch several doers in parallel (many of one model or a mix); only ultra-brainstorming runs several thinkers at once. Use whenever a member must pick a model, decide thinker-vs-doer, or run the plan → do → review loop. Triggers: 'which weapon', 'which model should X use', 'pick the weapon', 'thinker or doer', 'draw a weapon', 'run the weapon loop', 'how does the member choose its model'. Every member consults this before acting — it is the atomic layer beneath members-formation (which member works) and ultra-brainstorming (fuse several members across models)."
metadata:
  version: 1.6.0
type: Skill

---
# Weapon Utility — how a member draws and wields its weapons

Every member carries an **arsenal** of weapons (AI models). This skill is the member's
standing rule for **which weapon to draw** and **how the weapons work together**. It runs
inside a single member — the layer beneath the Butler's routing.

Know what it is *not*:

- Not **`members-formation`** (the Butler's routing — *which member* works and in what
  arrangement). Formation picks the member; this picks the **weapon inside that member**.
- Not **`ultra-brainstorming`** (the Strategist fusing several members across several thinking
  models). That is a fan-in across members; this is one member choosing and wielding its own
  blades. The two meet only in the exception below.
- Not the arsenal **order** itself — that is fixed by decision **#25** (doers first, then
  thinkers/duals, then Sonnet last). This skill *reads* that order; it does not set it.

## The two kinds of weapon

Every weapon has a **role** (set in `MODELS`, app.js): `doer`, `thinker`, or `both`.

- **Thinker weapons** — the **mind**. They *read, plan, and prompt the doer on what to do*,
  then *review what comes back*. A thinker never does the bulk work itself; it directs.
  `opus` is the **prime thinker** — the best mind, and therefore the **first thinker in every
  arsenal**. The prime thinker is just whichever thinker leads the block; with `opus` present it
  is always `opus`.
  (`opus`, `gpt-5.5`, `deepseek-v4-pro`, `glm-5.2`, `kimi-k2.7`, `nemotron-3-ultra`, `qwen3.5`.
  `sonnet` can think too.)
- **Doer weapons** — the **hands**. They *take the thinker's prompt, do the job, and return it*.
  A doer never decides strategy; it executes. `minimax-m3` is the **prime doer** — every member's
  first-drawn hand. (`minimax-m3`, `haiku`, `gemma4`, and the MiniMax forge doers
  `image-01`/`video`/`speech`/`music`.)
- **Dual weapon** (`both`) — only `sonnet` remains dual, and it sits **last in every arsenal** for
  two reasons: it is the universal last-resort for **either** role, AND it is the guild's
  **Claude-capable fallback** for tools no other doer can run — see *Sonnet, the Claude-only-tool
  fallback* below.

## The tool boundary — doers return content, thinkers run tools (HARD RULE)

A doer **does not invoke tools**. It takes the thinker's prompt, generates the work, and
**returns it as text**. That is all a doer can do. Edit, Write, Bash, git, MCP, computer-use —
every Claude Code tool — are wielded **only by the thinker** (a Claude model: the prime thinker,
or `sonnet`/`haiku` as the Claude-capable hand). The thinker is the only weapon holding the buttons.

So "write" splits two ways, and the split is the rule:

- **Author content** — compose the bytes, burn the generation tokens → **the doer's job**.
- **Invoke the write tool** — paste those finished bytes to disk via `Edit`/`Write` → **the thinker's job**.

The loop is therefore: thinker plans → doer **returns the new file content as text** → thinker
**reviews it, then runs `Write`/`Edit` itself** to commit it. The thinker does **not** re-author —
step is a mechanical copy of the doer's output into the tool call. Bad doer output → thinker
**re-prompts the doer**, never authors the content itself.

**Never hand a tool call to a non-Claude doer.** A non-Claude doer (`minimax-m3`, `gemma4`, the
Ollama bench) physically **cannot** call a Claude Code tool — summoning one to "use Write / use
the MCP / run the edit" is a category error and will fail. If a slice genuinely needs a tool inside
the doer's own run (not just content the thinker can commit), that is the Claude-only-tool case →
draw `sonnet` (next section). Otherwise: doer authors the bytes, thinker pushes the button.

## Sonnet — the Claude-only-tool fallback (never let a doer stall)

Some tools can be wielded **only by Claude models** — native Claude tool-use, computer-use, and
certain MCP servers that a non-Claude weapon physically cannot call. The prime doer `minimax-m3`
(and the other non-Claude doers) will simply be **unable** to run such a tool.

When a doer's task requires a Claude-only tool, **draw `sonnet`** — the dual at the tail, present
in *every* arsenal for exactly this purpose — and run that slice on it. Treat this as a **direct,
expected fall-through, not a failure or an escalation loop**: you are not retrying a broken doer,
you are picking the only weapon that *can* hold the tool. The run continues without interruption.
(Where a member also carries `haiku`, that Claude doer can run such tools too; `sonnet` is the
**guaranteed** fallback because it is in every arsenal.)

## The thinker ↔ doer loop

This is the core mechanic. One pass:

1. **Plan** — the thinker reads the task and writes a clear, scoped plan + the exact prompt
   for the doer.
2. **Do** — the doer executes that prompt and returns the result.
3. **Review** — the thinker checks the result **against the plan as intended**.
   - **Conforms** → accept and deliver.
   - **Does not conform** → the thinker re-prompts the **same** doer with precise corrections,
     and the loop repeats from step 2.

The thinker owns the standard; the doer owns the output. Keep the loop **bounded**: if the
doer cannot bring the result into conformity after a few corrected passes, it is treated as
*can't do this job* — escalate to the **next doer** (see below), not an endless retry.

**Sizing a big doer job.** For large reads/generations (a book chapter, a long extraction), the
backend default output cap (16k tok) and timeout (180s) will silently truncate. `summon.py` passes
`--max-tokens` and `--timeout` through to the backend — give the doer room: `summon.py minimax-m3
-f "$SRC" -s "$SYS" --max-tokens 16000 --timeout 600`. (`--max-tokens` maps per backend — `--max-tokens`
for minimax, `--num-predict` for the Ollama cloud — summon translates it.) Loop chunks **one at a time**
and, on review, treat a draft that ends mid-sentence as a truncation → re-run that chunk larger.

## Drawing the right weapon

A member always draws the **highest-priority available weapon of the kind the job needs**,
scanning its arsenal **left → right** (left = highest priority, per decision #25).

- **Needs a thinker** → take the **leftmost available** thinker weapon (first weapon that can
  think). If it is unavailable, take the next thinker to its right. Exhausted → fall through to
  `sonnet`.
- **Needs a doer** → take the **leftmost available** doer weapon. If that doer **cannot do the
  job** (refuses, fails, or is unsuited) → move to the **next doer to its right** and try there.
  Exhausted doers → a dual may stand in, then `sonnet` as the universal fallback.

Because the arsenal is ordered **doers → thinkers/duals → Sonnet last**, the leftmost doer is
literally the first weapon in the list, and the leftmost thinker is the first weapon after the
doer block. The order is the priority — no separate ranking needed.

## One thinker, one-or-many doers — and the ultra-brainstorming exception

By default a member runs **exactly one thinker** — the prime thinker plans, reviews, and owns the
standard. But that thinker may put **one *or several* doers to work at once.** When the job splits
into independent slices, the thinker **fans the work across multiple doer agents in parallel** —
several instances of the *same* doer model, or a *mix* of different doer models — and reviews each
return against the plan, re-prompting or escalating any slice that doesn't conform. **One doer is
the floor, not the ceiling**; parallel doers are the norm whenever the work divides cleanly.
Splitting is the thinker's call: only fan out work that is genuinely independent — truly sequential
work stays a single doer.

**Exception — when [[ultra-brainstorming]] is active**, the *thinker* side also fans out: the
member fires **all of its available thinker weapons at once** on the same material, and the
**highest-priority available thinker** then **consolidates** every thinker's output into **one
plan** (ultra-brainstorming's converge → synthesize step). That consolidated plan is then executed
by one *or several* doers exactly as above. So ultra-brainstorming layers **thinker fan-out** on top
of the **doer fan-out** that is always available.

**Batching the doer fan-out — one process, one connection.** When the fan-out is many *independent*
prompts to the **same** prime doer (`minimax-m3`), do not spawn N subprocesses — **batch** them.
`minimax.py --batch <file.jsonl>` runs all N over ONE keep-alive HTTPS connection (one process spawn,
one TLS handshake) and emits JSONL results **in input order**; `guild/delegate.py:delegate_many(prompts)`
wraps it and returns an ordered list, a failed slice coming back `None`. This is the SAME
plan → do → review loop — the thinker still reviews every return against the plan and re-prompts any
non-conforming slice — just without the per-call subprocess + handshake tax (wall-clock ≈ one
round-trip instead of N). Reach for it on any clean N-way split: bulk extraction, per-chunk drafting,
per-file transforms. Fall back to individual `summon.py` calls when slices need *different* doer
models, or are genuinely sequential (each depends on the last). The batch path is minimax-only today;
other backends degrade gracefully to a sequential loop with the same ordered-results contract.

## Availability — when a weapon counts as drawable

A weapon is **available** only if all hold:

- it is **in the member's loadout** (and not revoked for that member);
- it is **not globally disabled** (the Arsenal kill-switch / `sa-disabled-weapons`);
- it is **actually reachable** — provisioned and pulled. `gpt-5.5` reports *not provisioned*
  and is skipped; Ollama bench weapons must be pulled first or they are skipped.

An unavailable weapon is passed over silently — the scan simply continues to the next weapon of
the same kind.

## Where it sits

```
members-formation   →   which MEMBER works (the Butler routes)
   ultra-brainstorming →  fire ALL a member's thinkers at once (any member who holds it)
      weapon-utility   →  which WEAPON inside one member + the thinker↔doer loop  ← here
```

Every member loads this skill, because every member carries an arsenal. It reads the arsenal
order set by decision #25 and the roles in `MODELS`; it changes neither.

## Versioning

Own skill. Bump `metadata.version` on any change (PATCH: wording/refs · MINOR: a new selection
rule or mode · MAJOR: a change to the loop or selection contract). Then `python3 build.py`.

## Cost-per-tier baseline (1.6.0)

The proportional routing gate (LITE vs FULL) only pays off if LITE turns demonstrably cost less. With the B1 sidecar fix (`tier` now reliable in `turn-cost.jsonl`), you can now derive a real cost baseline per tier and use it to govern model-selection decisions.

**Reading the baseline:**

```sh
python3 tools/efficiency_report.py   # shows median in/out tokens split by lite vs full
```

**Decision rule — when to recommend tier escalation:**

- If median FULL `out` tokens > 3× median LITE `out` tokens → the FULL gate is correctly separating campaign work from quick fixes. No action.
- If LITE and FULL medians converge within 1.5× → the classifier is sending too much to FULL. Loosen `size_small_signals` in `data/harness.json`.
- Never recommend a model upgrade (e.g., Opus → Sonnet) until the tier split is confirmed working. A broken classifier that sends everything to FULL inflates apparent per-turn cost and will make any model switch look better than it is.

**The safety check always wins:** before adjusting any `size_small_signals`, verify zero high-stakes turns in the LITE column (a migration, git push, deploy in a LITE-tagged turn is the hard failure). Stakes keyword list in `data/harness.json` is immutable until safety is confirmed.

## Changelog
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
