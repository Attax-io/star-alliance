---
type: Document
title: Command doctrine — the grounding behind the seven axioms
timestamp: 2026-06-28T00:00:00Z
---

# Command doctrine — where the craft comes from

The seven axioms are not invented; they are the distilled core of how human commanders have
issued orders under time pressure for a century, re-aimed at delegating to an AI subordinate.

## Mission command (Auftragstaktik) — intent over instruction

The Prussian-then-NATO doctrine of **mission command** gives a subordinate the *intent* and
the *end-state*, then freedom in *how*. Its instrument is the **Commander's Intent**: a short
statement of **purpose** (why), **key tasks** (what must happen), and **end state** (what
"done" looks like). The reason is brutal and practical: a detailed step-list breaks the
moment reality deviates from the plan, and the subordinate — who can see the ground the
commander cannot — is then paralysed or wrong. Intent survives surprise; steps do not.
→ **Axiom 1** (intent first) and **axiom 5** (bound the field — freedom *within* intent).

For an AI subordinate the parallel is exact: a member or subagent given the end-state and
the bounds resolves an unforeseen case correctly; one given only a brittle step-list fails on
the first input the steps didn't anticipate.

## BLUF — bottom line up front

US military and intelligence briefing convention: **state the conclusion or the order in the
first sentence**, then support it. It exists because a reader's attention and time are
scarcest at the moment they most need the answer. Every sentence before the bottom line is a
tax the reader pays to reach it.
→ **Axiom 2** (BLUF). The guild's own deployment brief obeys the same rule.

## The five-paragraph order (SMEAC)

The standard combat order has five parts: **S**ituation, **M**ission, **E**xecution,
**A**dministration/Logistics, **C**ommand/Signal. Stripped to what a delegated AI task needs,
it collapses to the order shape this skill uses:

| SMEAC | Order shape | Why it carries over |
|---|---|---|
| Situation | **Context** | the facts the subordinate cannot see for itself |
| Mission | **Order + Intent** | the one-line deliverable and its purpose |
| Execution | **Constraints** | the bounds and anti-goals within which it acts |
| Admin/Logistics | (folded into Context) | inputs, paths, resources |
| Command/Signal | **Output contract** | how the result reports back and how it's judged |
→ **Axioms 4 and 6** (complete the brief; contract the return).

## Precision and the round-trip tax

Every ambiguity in an order is resolved by *someone* — and a subordinate resolving it guesses
without the commander's context, so it guesses wrong as often as right. A wrong guess costs a
redo; a clarification question costs a round-trip. In the guild both are dear: a subagent spun
up on an under-specified order burns its whole budget before discovering what it was missing,
and a one-shot text call comes back wrong with no chance to correct mid-task. Precision paid up
front (axiom 3) is always cheaper than correction paid later.

## Right-sizing — the same intent, four registers

A command is read by very different subordinates, and the *same* intent must be dressed
differently for each (axiom 7): a **one-shot worker** (a Claude subagent given a text-only task)
carries no memory and returns text, so the spec lives entirely in the prompt; a **subagent**
has tools but no memory of the conversation, so every fact must travel with the order; a
**member** has craft, so command the intent and trust the method; the **Guild Master** is a
non-programmer, so lead with plain English and offer a choice, not a lecture. Misjudging the
register is its own failure mode (audit #6): hand-holding
a peer wastes everyone's time; jargon at the Guild Master breaks the plain-English mandate.
