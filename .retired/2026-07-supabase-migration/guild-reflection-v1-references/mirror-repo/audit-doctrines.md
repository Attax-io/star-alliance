---
type: Document
title: guild-reflection — four audit doctrines
description: The four self-learning audits (Individuality, Spawn-and-Release, Volume/Cadence, Evidence-only) that the AUDIT mode runs, distilled from the Self-Learning shelf.
timestamp: 2026-06-28T00:00:00Z
---

# Four audit doctrines

These four were mapped in `docs/SELF-LEARNING-MINING-2026-06.md` (TIER-3) but never built
into the loop. They are AUDIT-mode self-interrogations: each one is a question the guild asks
of its **logged behavior**, not of its feelings, and each emits a concrete diff or a retirement.

## 1 · Individuality audit (*The Secret of Success*, Atkinson)

**Reject one-size-fits-all templates. A skill that yields near-identical output across the
members who carry it is not a craft — it is a template wearing a skill's name.**

- Enumerate every skill carried by **more than one** member (shared skills).
- For each, sample real outputs across its carriers (logs / deliverables / journal cycle records).
- **Flag** any skill whose output is near-identical regardless of which member ran it: same
  structure, same phrasing, member persona absent. That skill is not adapting to the carrier.
- Verdict: **SPECIALIZE** (give the skill member-aware branches / persona hooks), **NARROW**
  (restrict it to the one member it actually fits), or **KEEP** (the uniformity is correct —
  e.g. a mechanical transform that *should* be identical, like a formatter).
- Do not flatten members into one voice to "pass" the audit — that is the failure this guards
  against, not the fix.

## 2 · Spawn-and-Release audit (*The Prophet*, Gibran)

**"Your children are not your children… they come through you but not from you." Skills are
arrows the guild looses, not heirlooms its author keeps.**

Every skill carries an **owner-after-release** and a **sunset clause**:

- **owner-after-release** — the member best placed to evolve the skill *now*, which may not be
  its author. The author has **no veto**: another member may rewrite a released skill on
  evidence (failing cycles, a better distillation) without the author's sign-off.
- **sunset clause** — a falsifiable retirement condition stated when the skill ships, e.g.
  "retire if not productively retrieved for N audit cycles" or "retire when superseded by X."
- AUDIT step: for each skill, confirm both fields exist. Missing → file the diff to add them.
  Sunset condition met → move to the Weed step / `retired-ideas.md` with the evidence.
- This composes with the Weed step: Weed finds the dead skill; Spawn-and-Release is the standing
  rule that lets *any* member retire or rewrite it without waiting on the original author.

## 3 · Volume & Cadence / Equal-Odds audit (*Mastering Creativity*, James Clear)

**Equal-odds rule: any single attempt is about as likely to break through as any other, so
**volume**, not a single perfect attempt, surfaces breakthroughs. Run the core loops on a
cadence and measure the rate.**

- Core workflows (Reflective Cycle, Guild Self-Audit, the skill routine) run on a **fixed
  cadence**, not only when someone remembers. A skipped cadence is itself a logged finding.
- Track a **per-cycle hit-rate**: `applied_upgrades / cycles_run` over the window. An *applied
  upgrade* is a committed diff to a skill / CLAUDE.md / member / workflow that came out of a
  cycle. ("No change warranted — clean run" is a valid close but is **not** a hit.)
- Persist each cadence run's tally to `guild/journal/cadence-metrics.jsonl`
  (one line: `{stamp, cycles_run, hits, hit_rate, window}`).
- Read the metric for **volume, not perfection**: a low hit-rate with high volume is healthy
  exploration; a low hit-rate with low volume means the loop isn't being run enough to ever
  surface a breakthrough — the diff is "raise the cadence," not "try harder once."
- Never weaponize the metric into pressure to manufacture trivial diffs — that corrupts the
  honest-close rule. Volume is the lever; the metric only observes it.

## 4 · Evidence-only self-audit (*Shoemaker's Self-Knowledge*, Speaks)

**There is no privileged inner sense. An agent knows its own state the same way an observer
does — through behavior and role — so "I think I did fine" is not evidence of anything.**

- Every claim the AUDIT makes about guild state **must cite a log line**: `usage-log.jsonl`,
  `data/turn-cost.jsonl`, a `guild/journal/cycle-*.json` record, a git commit, an error trace.
- Banned, unless backed by a citation: "this skill is working well," "the members are balanced,"
  "I handled that correctly," "that was a clean run" — these are introspective claims with no
  privileged access behind them.
- If a claim **cannot** be grounded in a log, the honest output is **"unknown — not measured,"**
  and the diff is to add the missing instrumentation, not to assert the flattering guess.
- This is the gate the other three audits pass through: Individuality cites sampled outputs,
  Spawn-and-Release cites the missing field / met sunset condition, Volume cites the metrics
  file. No audit verdict ships on a feeling.
