---
type: Document
title: Guild Journal — the persistent reflective notebook
timestamp: 2026-06-28T00:00:00Z
---

# Guild Journal

The durable notebook the `guild-reflection` skill writes to — the missing `guild/journal/`
the self-learning mining named (SELF-LEARNING-MINING-2026-06.md:60). Non-trivial work is not
done when it ships; it is done when it has produced either an applied doctrine diff or an
explicit "no change warranted." This directory is where that reflection lands and persists.

## What goes here

One dated entry per reflective close: `YYYY-MM-DD-<slug>.md`. Each entry records, for a piece
of finished work:

- **What shipped** — the change-set, in one line.
- **What was learned** — the generative lesson, not the procedure.
- **The loop close** — either the applied doctrine/skill/memory diff, or "no change warranted"
  with the reason.

## Why a directory, not a single log

A flat log rots; a directory of dated entries is greppable, diffable, and survives context
resets. It complements (does not replace) the durable memory graph (`MEMORY.md`) and the
evolution ledger (`evolution/ledger.jsonl`): the ledger records WHAT changed and its verdict,
memory records DURABLE facts, this journal records the REFLECTION that closed the loop.
