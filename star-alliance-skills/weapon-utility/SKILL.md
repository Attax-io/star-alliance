---
name: weapon-utility
description: "Every member's rule for which weapon (model) to draw and how thinker and doer weapons work together. Thinker weapons read, plan, and prompt the doers; doer weapons do the job and return it; the thinker then reviews the result against the plan and re-prompts the doer until it conforms. A member draws the highest-priority AVAILABLE weapon of the kind the job needs — scanning its arsenal left to right — and wields one weapon at a time, unless ultra-brainstorming is active. Use whenever a member must pick a model, decide thinker-vs-doer, or run the plan → do → review loop. Triggers: 'which weapon', 'which model should X use', 'pick the weapon', 'thinker or doer', 'draw a weapon', 'run the weapon loop', 'how does the member choose its model'. Every member consults this before acting — it is the atomic layer beneath members-formation (which member works) and ultra-brainstorming (fuse several members across models)."
metadata:
  version: 1.1.1
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
  (`opus`, `gpt-5.5`, `deepseek-v4-pro`, `glm-5.2`, `kimi-k2.7`, `nemotron-3-ultra`, `qwen3.5`.
  `sonnet` can think too.)
- **Doer weapons** — the **hands**. They *take the thinker's prompt, do the job, and return it*.
  A doer never decides strategy; it executes. `minimax-m3` is the **prime doer** — every member's
  first-drawn hand. (`minimax-m3`, `haiku`, `gemma4`, and the MiniMax forge doers
  `image-01`/`video`/`speech`/`music`.)
- **Dual weapons** (`both`) — only `sonnet` remains dual: the universal last-resort weapon for
  **either** role. It sits at the tail of every arsenal.

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

## One weapon at a time — and the ultra-brainstorming exception

By default a member wields **exactly one weapon at a time**: one thinker plans, hands to one
doer, reviews, delivers.

**Exception — when [[ultra-brainstorming]] is active**, a member fires **all of its available
thinker weapons at once** on the same material. The **highest-priority available thinker** then
**consolidates** every thinker's output into **one plan** (this is ultra-brainstorming's
converge → synthesize step) before that single plan is prompted to the doer. Only the
**thinkers** fan out; the doer still runs one weapon at a time on the consolidated plan, and
the thinker↔doer review loop is unchanged.

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
   ultra-brainstorming →  fuse several members across models (the Strategist, on fan-in)
      weapon-utility   →  which WEAPON inside one member + the thinker↔doer loop  ← here
```

Every member loads this skill, because every member carries an arsenal. It reads the arsenal
order set by decision #25 and the roles in `MODELS`; it changes neither.

## Versioning

Own skill. Bump `metadata.version` on any change (PATCH: wording/refs · MINOR: a new selection
rule or mode · MAJOR: a change to the loop or selection contract). Then `python3 build.py`.

## Changelog
- **1.1.1** — Added **"Sizing a big doer job"** to the thinker↔doer loop: for large reads/generations the backend default output cap (16k) and timeout (180s) silently truncate, so pass `--max-tokens`/`--timeout` through `summon.py` (now translated per backend — `--max-tokens` for minimax, `--num-predict` for cloud), loop chunks one at a time, and treat a mid-sentence draft as truncation → re-run larger. Mined from the `japanese-candlesticks` source-distillation run.
- **1.1.0** — Thinker-bench reclass. `glm-5.2`, `kimi-k2.7`, `nemotron-3-ultra`, `qwen3.5` moved
  from doer/dual → **thinker** (join `opus`, `gpt-5.5`, `deepseek-v4-pro`). `minimax-m3` named the
  **prime doer** — every member's first-drawn hand. Doer pool now `minimax-m3`, `haiku`, `gemma4` +
  forge doers; `sonnet` the sole remaining dual. All 9 member arsenals reordered minimax-first.
- **1.0.0** — Initial release. Defines thinker vs doer weapons, the plan → do → review loop,
  left-to-right priority selection with doer-fallback and availability rules, one-weapon-at-a-time
  default, and the ultra-brainstorming exception (all thinkers fan out, top thinker consolidates
  before the doer). Positioned as the atomic layer beneath members-formation and ultra-brainstorming.
