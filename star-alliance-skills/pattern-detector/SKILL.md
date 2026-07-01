---
name: pattern-detector
description: "Reads the seven most recent Lex Council housekeeping run logs plus the current OPEN-ITEMS.md and identifies recurring categories or doc hot-spots (RLS gate firing repeatedly, frontend-count drift, repeated reconciler targets, stubs older than 14d without prose). Use when housekeeping findings feel repetitive or when preparing a retrospective. Triggers: 'detect patterns', 'housekeeping retrospective', 'recurring open items', 'stale stubs'."
metadata:
  version: 1.0.0
type: Skill
---

# Pattern Detector

The pattern-detector skill mines recent housekeeping history for recurring categories and doc hot-spots, so the orchestrator can convert them into durable doctrine diffs (guideline additions, memory entries, merge/split candidates) or monitor-only signals.

## Inputs

- The 7 most recent housekeeping run logs in `lex_council/docs/vault-logs/` (filter filenames matching `*_housekeeping-run-*.md`, sort by date desc, take 7).
- The current `lex_council/docs/OPEN-ITEMS.md`.

## Patterns to identify

1. **Recurring OPEN-ITEMS categories** — e.g. RLS sensitivity gate firing in N of the last 7 runs; frontend count drift; stubs-without-prose being re-flagged; any 🔴 that's been active for 10+ runs.
2. **Repeated doc-reconciler targets** — the same doc edited in ≥ 3 of the last 7 runs. Possible hot-spot or design problem (doc is too coarse-grained, belongs split).
3. **Stubs older than 14 days without prose body** — list them.

## Output

Return a structured report with up to 5 patterns, each with:

- Pattern description (1 sentence)
- Proposed action: `guideline-addition` | `memory-entry` | `merge-candidate` | `split-candidate` | `monitor`

Keep under 500 words. Do not edit any files — return-only.