---
type: Document
title: guild-reflection recipe
description: Step-by-step procedure for the CYCLE and AUDIT modes of guild-reflection.
timestamp: 2026-06-27T00:00:00Z
---

# guild-reflection — full recipe

## CYCLE (after a non-trivial task)

1. **Trigger.** Any task that touched code, doctrine, a workflow, or produced a deliverable, AND
   any task where a retry, user correction, or unexpected tool result occurred. Trivial one-liners
   are exempt.
2. **Fill the 6 fields** (see SKILL.md). Write `description` FIRST and write it raw — what actually
   happened, including the embarrassing parts. Marcus Aurelius' split goes in `analysis`:
   controllable vs not.
3. **Find the seed.** Do not stop at "the output was wrong." Ask: which skill, prompt line, memory
   fragment, or routing rule produced it? That is the seed. The diff targets the seed.
4. **Write the diff.** Name the file. `star-alliance-skills/<x>/SKILL.md`, `CLAUDE.md`, a member
   `.md`, or `workflows.json`. If small + safe → apply now. If large/risky → file to backlog and
   surface to the Guild Master.
5. **Persist.** Append the record to `guild/journal/cycle-<ISO-stamp>.json`.
6. **Close.** Non-trivial work cannot report "done" with an empty `action_plan`. Valid closes:
   an applied diff, a filed backlog item, or an explicit "no change warranted — run was clean."

## AUDIT (cadence — weekly or every N sessions)

Run as the closing step of a Guild Self-Audit workflow.

1. **Load** the last N cycle records + audit reports from `guild/journal/`, plus
   `star-alliance-arsenal/usage-log.jsonl` and `data/turn-cost.jsonl` for real behavior.
2. **Weed.** Enumerate loaded skills; flag any with no productive retrieval in N cycles for demote
   or sunset. (Delegate the inventory scan to a MiniMax doer; keep judgment in the thinker.)
3. **Retire bad ideas.** For each held assumption: evidence-for / falsifier / bad-idea-defended →
   KEEP-WITH-EVIDENCE / RETIRE / REPLACE. Append retirements to `retired-ideas.md` with evidence.
4. **Rebalance.** Per-member load + error rate + skill usage vs declared intent. Flag imbalance.
5. **Interrogate.** Answer `self-interrogation.md` gut-honestly.
6. **Synthesize.** Turn findings into concrete diffs. High-confidence + low-blast-radius → apply.
   Anything touching security/RLS/destructive scope → surface, never auto-apply.
7. **Write** `guild/journal/audit-<stamp>.md` and update the Quartermaster's memory if a finding
   earns a durable memory file.

## Doer/thinker split

- **Doer (MiniMax first):** scan logs, enumerate skills, tally usage, draft the description field,
  extract candidate patterns.
- **Thinker (the Quartermaster):** decide root cause, decide what to retire, write the diff, judge
  blast radius, apply or escalate.

## Guardrails

- One method to completion, not three half-applied (*Science of Being Well*). An audit picks its
  cuts and finishes them.
- Evidence over introspection (*Shoemaker*). Every claim about guild state cites a log line.
- Externalize everything (*Life Balance*). Nothing of value stays in private turn context.
