---
name: guild-reflection
description: "The Quartermaster's self-improvement engine — turn finished work into durable guild upgrades through a structured reflective loop, instead of accumulating data the guild never learns from. Two modes: CYCLE (after any non-trivial task, run the 6-field reflective cycle — what happened, friction signals, evaluate vs intent, diagnose root cause, extract one generalizable rule, commit a concrete diff to a skill / CLAUDE.md / member trait — not closed until the action_plan mutates guild doctrine) and AUDIT (on a cadence, sweep the guild: weed skills unused for N cycles, retire 'bad ideas' with falsifying evidence, rebalance member load, write findings to the guild journal). Fuses five self-improvement doctrines: Gibbs' reflective cycle, Marcus Aurelius' Stoic audit, Enneagram self-interrogation, Life-Balance looping, As-a-Man-Thinketh root-cause weeding. Use whenever the guild should LEARN from a run, not just finish it. Triggers: 'reflect on this', 'run the reflective cycle', 'guild self-audit', 'what did we learn', 'weed the skills', 'close the loop', 'self-improve the guild'. Distinct from session-mining (patterns from raw chat history) and skillsmith (mechanically syncs/versions skills) — guild-reflection decides WHAT should change and writes the plan they execute."
metadata:
  version: 1.0.0
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

## The journal (persistence is the point)

Self-knowledge has no privileged inner sense (*Shoemaker*) — the guild knows its state only by
its **logged behavior**, never by introspective claim. So every reflection is written, not felt.

- `guild/journal/cycle-<stamp>.json` — one CYCLE record per non-trivial run.
- `guild/journal/audit-<stamp>.md` — one AUDIT report per cadence sweep.
- `guild/journal/retired-ideas.md` — append-only graveyard of retired doctrine + the evidence.

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

See `references/recipe.md` for the full step-by-step and `references/self-interrogation.md` for
the fixed audit questionnaire.
