---
name: guild-reflection
description: "The Quartermaster's self-improvement engine — turn finished work into durable guild upgrades through a structured reflective loop, not just accumulate data. Two modes: CYCLE (after any non-trivial task, run the 6-field loop — what happened, friction signals, evaluate vs intent, root cause, one generalizable rule, a concrete diff to a skill/CLAUDE.md/member; not closed until the action_plan mutates doctrine) and AUDIT (on a cadence: weed skills unused for N cycles, retire 'bad ideas' with falsifying evidence, rebalance member load, write the journal). Use whenever the guild should LEARN from a run, not just finish it. Triggers: 'reflect on this', 'run the reflective cycle', 'guild self-audit', 'what did we learn', 'weed the skills', 'retire bad ideas', 'close the loop', 'self-improve the guild', 'reflection journal'. Distinct from session-mining (mines raw chat history) and skillsmith (syncs/versions skills) — guild-reflection decides WHAT should change and writes the action plan those skills then execute."
metadata:
  version: 1.1.0
type: Skill

---

# guild-reflection

The Quartermaster's instrument for the guild's hardest mandate: **getting better on purpose.**

A guild that only executes and stores outputs is not learning — it is accumulating data
(*Learning by Doing*, Gibbs). Reflection is the step that converts a finished run into a
durable change in how the guild works. This skill makes that step mandatory, structured, and
**self-closing**: the loop is not complete until it has mutated guild doctrine.

> **The one law:** No action plan, no learning. A reflection that ends in a feeling instead of
> a committed diff is just journaling.

## The five voices that say the same thing

This skill is one loop wearing five names. They were mined independently from five books and
they agree:

| Source | Its name for the loop | What it adds |
|---|---|---|
| Gibbs — *Learning by Doing* | Description → Feelings → Evaluation → Analysis → Conclusion → **Action Plan** | the loop only closes on a concrete next-action |
| Marcus Aurelius — *Meditations* | controllable vs not → judged poorly → one correction | separate what you controlled from what you didn't |
| Enneagram intro | fixed weekly self-interrogation on recurring patterns | record the gut-truth, not the sanitized version |
| *Life Balance* | declare intent → act → measure → audit imbalance → loop | externalize intentions; private context decays |
| James Allen — *As a Man Thinketh* | weed the seed, not the symptom | trace failure to the skill/prompt/memory that caused it |

## Mode 1 · CYCLE — run after any non-trivial task

Emit a single object. Every field is required. The action_plan is a **diff**, not a wish.

```json
{
  "description": "what ACTUALLY happened (not the intended/sanitized version)",
  "signals":     "friction: errors, retries, user corrections, wasted tokens, dead ends",
  "evaluation":  "measured against the original intent — what worked, what missed",
  "analysis":    "root cause. Separate controllable (my interpretation, tool choice, reasoning) from not-controllable (ambiguous spec, tool failure). Trace the failure to its SEED.",
  "conclusion":  "one generalizable rule a future run should follow",
  "action_plan": "a concrete diff: add/edit a SKILL, a CLAUDE.md line, a member trait, or a workflow step — with the target file named"
}
```

**Closing rule (enforced by the butler):** a "task complete" report for non-trivial work is
**rejected** if `action_plan` is empty. Either you found a real upgrade and you commit it, or
you state explicitly "no change warranted — run was clean" (which is itself a valid close).

Apply the diff in the same turn when it is small and safe; otherwise file it to the journal
backlog (below) so it is not lost.

## Mode 2 · AUDIT — run on a cadence (weekly / every N sessions)

The guild-level sweep. Read the journal + recent logs, then:

1. **Weed (As a Man Thinketh).** List every actively-loaded skill. Demote/flag any whose
   retrieval has not improved a workflow in the last N cycles. A context full of unproductive
   thought-seeds silently shapes every agent.
2. **Retire bad ideas (*Bad Ideas About Writing*).** Harvest held assumptions from CLAUDE.md +
   recurring log patterns. For each: *what evidence supports it, what would falsify it, which
   bad idea is it secretly defending?* Tag KEEP-WITH-EVIDENCE / RETIRE / REPLACE. Publish a
   "Retired Ideas" list so dropped doctrine isn't quietly re-added.
3. **Rebalance (*Life Balance*).** Compare per-member load, error rates, skill usage against the
   intentions declared in CLAUDE.md + member doctrine. Flag overloaded members, dead skills,
   routing bottlenecks.
4. **Interrogate (Enneagram).** Answer the same fixed questions every cycle (see
   `references/self-interrogation.md`) about recurring failure modes — gut-truth, not the
   flattering version. Repetition over many cycles surfaces patterns one run can never reach.
5. **Write it down.** All findings + proposed diffs go to the persistent journal. Distil into
   concrete skill / CLAUDE.md / workflow edits.

## Mode 2 · AUDIT — four self-learning audits (run with the sweep)

These four extend the sweep above with named self-interrogations. Each asks a question of the
guild's **logged behavior**, not its feelings, and emits a concrete diff or a retirement. Full
procedure in `references/audit-doctrines.md`.

6. **Individuality audit (*The Secret of Success*).** For every skill carried by more than one
   member, sample real outputs across its carriers. Flag any skill whose output is
   **near-identical regardless of who ran it** — that is a one-size-fits-all template, not a
   craft. Verdict per skill: SPECIALIZE (add member-aware branches), NARROW (restrict to its one
   real fit), or KEEP (the uniformity is correct, e.g. a mechanical formatter). Do not flatten
   members into one voice to pass — that is the failure, not the fix.
7. **Spawn-and-Release audit (*The Prophet*).** Skills are arrows, not heirlooms. Confirm every
   skill declares an **owner-after-release** (the member best placed to evolve it now — which may
   not be the author) and a **sunset clause** (a falsifiable retirement condition). The author has
   **no veto**: any member may rewrite or retire a released skill on evidence. Missing fields →
   file the diff; a met sunset condition → move to Weed / `retired-ideas.md` with the evidence.
8. **Volume & Cadence audit (*Mastering Creativity*, James Clear).** Equal-odds: volume — not one
   perfect attempt — surfaces breakthroughs. Confirm the core loops ran on cadence (a skipped
   cadence is itself a finding), and track a **per-cycle hit-rate** = applied upgrades / cycles
   run. Persist each run's tally to `guild/journal/cadence-metrics.jsonl`. Read it for volume, not
   perfection: low hit-rate + low volume means the diff is "raise the cadence," never "manufacture
   a trivial diff."
9. **Evidence-only gate (*Shoemaker's Self-Knowledge*).** No privileged inner sense — the guild
   knows its state only as an observer would, by behavior and role. **Every audit claim must cite
   a log line** (`usage-log.jsonl`, `data/turn-cost.jsonl`, a `cycle-*.json` record, a commit, an
   error trace). A claim that cannot be grounded is reported as **"unknown — not measured,"** and
   the diff is to add the missing instrumentation, not to assert the flattering guess. The other
   three audits pass through this gate — no verdict ships on a feeling.

## The journal (persistence is the point)

Self-knowledge has no privileged inner sense (*Shoemaker*) — the guild knows its state only by
its **logged behavior**, never by introspective claim. So every reflection is written, not felt.

- `guild/journal/cycle-<stamp>.json` — one CYCLE record per non-trivial run.
- `guild/journal/audit-<stamp>.md` — one AUDIT report per cadence sweep.
- `guild/journal/retired-ideas.md` — append-only graveyard of retired doctrine + the evidence.
- `guild/journal/cadence-metrics.jsonl` — one line per cadence run: cycles run, hits, hit-rate.

These compound. The whole value is in coming back to them; a reflection thrown away taught
nothing.

## Anti-patterns (do not)

- **Patch the symptom.** Fixing the output without tracing the seed re-grows the weed next run.
- **Reflect without committing.** Feelings logged, doctrine unchanged = journaling, not learning.
- **Sanitize the description.** Record what you actually did. The honest version is the only one
  that upgrades anything.
- **Audit into consensus.** Retiring a bad idea preserves productive disagreement; don't flatten
  every member's voice into one (*The Secret of Success*).
- **Hoard the skill.** A reflection's output is an arrow, not an heirloom (*The Prophet*) — file
  it where another member can act on it without your veto.

See `references/recipe.md` for the full step-by-step, `references/self-interrogation.md` for
the fixed audit questionnaire, and `references/audit-doctrines.md` for the four self-learning
audits (Individuality · Spawn-and-Release · Volume & Cadence · Evidence-only).

## Changelog

| Version | Date | Summary |
|---|---|---|
| **1.1.0** | 2026-06-28 | Built the four leftover TIER-3 self-learning audits into the AUDIT surface: Individuality (*Secret of Success*), Spawn-and-Release (*The Prophet*), Volume & Cadence/Equal-Odds (*Mastering Creativity*), Evidence-only gate (*Shoemaker*). Added `references/audit-doctrines.md` + `cadence-metrics.jsonl` to the journal. |
| **1.0.1** | 2026-06-27 | Trimmed `description` under the 1024-char Cowork hard limit (was rejected on install). Triggers and the differentiator clause preserved. |
