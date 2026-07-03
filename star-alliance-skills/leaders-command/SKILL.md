---
name: leaders-command
description: "The Butler's down-command craft — take the Guild Master's words and re-issue them to a member or Claude subagent as one concise, precise, complete order, so it executes correctly first-time: no round-trips, minimal tokens. Built on seven axioms (intent first, bottom-line-up-front, one reading, complete-the-brief, bound-the-field, contract-the-return, right-size-to-the-subordinate) and an order shape from military mission-command and BLUF/SMEAC. Two modes: COMPOSE (write an order, right-sized to who executes it) and AUDIT (critique and rewrite a draft order). A runnable composer (guild/command.py) drafts an order from intent. Triggers: 'command the team', 'turn this into a clear order', 'write the prompt for the subagent', 'brief the agent', 'make this instruction precise', 'audit this order'. Differs from frame_brief (frames the request UP into a brief), members-formation (chooses WHO), and system-prompt-design-patterns (a model's persistent system prompt)."
metadata:
  version: 1.0.0
type: Skill
---
# Leader's Command — the Butler's down-command craft

A commander holds the whole picture; the subordinate holds almost none. A command is the
**compression** that bridges that gap — it transfers exactly enough intent and spec for
correct one-shot execution, and not one word more. Too little, and the subordinate guesses
wrong or asks back (a round-trip that costs time and tokens). Too much, and the signal
buries under detail. The craft is the **minimal sufficient order**.

This is the Butler's signature move: the Guild Master speaks in plain, sometimes loose
words; the Butler re-issues them DOWN to the chosen member or subagent as a clear,
precise, complete order — so the work comes back right the first time.

## What it is / is not

- **IS:** the craft of the delegated instruction itself — how to phrase a single order so a
  subordinate executes it correctly without re-asking. Two modes — COMPOSE and AUDIT — plus
  a runnable composer (`guild/command.py`).
- **IS NOT:** framing the Guild Master's request up into a brief (that is `frame_brief` /
  the framing step), choosing which member or workflow handles it (that is
  `members-formation`), designing a model's persistent system prompt (that is
  `system-prompt-design-patterns`), or enforcing output completeness (that is
  `full-output-enforcement`). This is the order you hand the subordinate, between "who" and
  "review the return."

## The seven axioms

1. **Intent first.** Lead with the end-state and the *why*. A subordinate who understands
   the purpose resolves the unforeseen correctly without asking. Order the *what to achieve*,
   not only the steps — steps break on the first surprise; intent does not. ("Cut login
   latency below 1s because users abandon at 3s" lets the subagent pick the method; "add an
   index on users.email" dies if the bottleneck is elsewhere.)
2. **Bottom line up front (BLUF).** Sentence one is the order; context, caveats, and
   rationale follow. The reader must know what to do before they know everything about it.
   Burying the lede is a token tax on every reader.
3. **One reading.** Every ambiguous word is a coin-flip the subordinate must resolve — often
   wrong, always costly. Name the exact file, function, table, number, and format. "Fix the
   bug" becomes "in auth/middleware.ts:42 the token-expiry check uses `<`; make it `<=`."
4. **Complete the brief — assume no shared memory.** A Claude subagent sees only your words —
   whether it is a one-shot text worker or a tool-having agent. Include every fact it cannot
   look up: the constraint, the path, the prior decision, the example. An order that forces
   "what did you mean?" has already failed its one job — the whole subagent turn spent for nothing.
5. **Bound the field.** State the scope, the limits, and explicitly what NOT to do or touch.
   Freedom *within* stated bounds is mission command; freedom without bounds is drift.
   ("Edit only X; do not touch Y; ≤200 lines; no new dependencies.")
6. **Contract the return.** Specify the output shape and the acceptance criteria, so the
   result arrives conformant and verifiable in one pass. "Return a markdown table: file |
   line | severity | fix" beats "review this." An order with no definition of done cannot be
   graded, so it always loops.
7. **Right-size to the subordinate.** Match the order's shape to who executes it: a **one-shot
   worker** (a Claude subagent given a text-only task) needs the full spec in the prompt (no
   follow-up, no memory); a **tool-having subagent** needs every fact plus the exact return
   shape (isolated, one-shot); a **member** needs intent and latitude (trust the craft); the
   **Guild Master** needs the bottom line, plain English, and options with a recommendation.
   One order style does not fit all.

## The order shape

Adapted from the military BLUF / SMEAC order — the reusable skeleton both modes use:

```
**Order:** <one line — the deliverable, bottom line up front>
**Intent:** <end-state + why>
## Context — what the subordinate cannot see
- <facts, paths, prior decisions, examples it needs>
## Constraints
- <scope, limits, explicit anti-goals>
## Output contract
- <exact return shape + acceptance criteria>
```

For a **one-shot worker** (a Claude subagent spawned via the Task tool) this maps cleanly onto
the prompt: Order + Intent + Constraints + Output-contract are the instructions; the Context
material is the input pasted in alongside them.

## Modes

- **COMPOSE** — write an order to a subordinate. Pick the template by subordinate type
  (`references/order-templates.md`), fill the shape, run the seven axioms over it. The
  runnable composer drafts a first pass: `python3 guild/command.py --target
  subagent|agent|member|human --in <intent-or-file> --out <order.md>`.
- **AUDIT** — critique a draft order against the failure modes (buried lede, ambiguity,
  missing input, no bounds, no output contract, jargon at a plain-English reader), score it,
  and rewrite. Checklist in `references/audit-checklist.md`.

## References

- [`references/order-templates.md`](references/order-templates.md) — the order shape filled
  per subordinate type (one-shot worker · tool-having subagent · member · human), with worked examples.
- [`references/audit-checklist.md`](references/audit-checklist.md) — the six command failure
  modes, the audit score, and the rewrite protocol.
- [`references/command-doctrine.md`](references/command-doctrine.md) — the grounding:
  mission-command / Auftragstaktik (commander's intent), BLUF, the SMEAC order, and how each
  maps onto delegating to an AI subordinate.

## Versioning

Own skill. Bump `metadata.version` on any change (PATCH wording/refs · MINOR new
mode/section · MAJOR contract change); regenerate `VERSIONS.md` and rebuild.

## Changelog

- **1.0.0** — Initial release. Seven axioms, the BLUF/SMEAC order shape, COMPOSE + AUDIT
  modes, the runnable `guild/command.py` composer (right-sized by --target), and three
  references. Carried by the-butler — his craft of turning the Guild Master's words into
  clear orders down to members and Claude subagents.
