---
type: Reference
title: Grounding Findings
skill: code-review-craft
---

# Grounding findings in evidence

A finding is a claim that something is wrong. To be actionable it must say **where**,
**what**, and **when it breaks** — and end in a path to confirmation.

## The three parts of an evidenced finding

1. **Location** — `path:line` (or a line range). A finding with no location is a vibe;
   the author cannot act on it without re-hunting.
2. **The problem** — what is wrong, in one clause.
3. **The failing case** — the concrete input, state, or sequence that triggers the
   problem. This is what separates a finding from a worry.

If you cannot produce part 3, you do not have a finding yet. You have a **question** —
ask it as a question ("L60: is `items` guaranteed non-empty here? if not, `.reduce`
throws"), do not dress it up as a defect.

## The finding line format

One finding per line, severity-tagged, fix attached:

```
path:line — SEVERITY: problem (failing case). suggested fix.
```

Examples:

```
api/ledger.ts:42 — HIGH: parseAmount('') returns NaN, written to the ledger (blank amount field). guard empty/NaN before write.
auth/cache.ts:77 — CRITICAL: cache key lacks tenant prefix → cross-tenant read (two tenants, same user id). namespace the key by tenant.
ui/Invoice.tsx:30 — LOW: re-implements utils/formatDate. reuse the helper, drop 9 lines.
```

Keep the line scannable. If the fix needs more than a clause, say "fix: see note below"
and add one short paragraph after the list — do not bloat the line.

## Weak vs grounded

| Weak (reject) | Grounded (ship) |
|---|---|
| "Error handling looks fragile." | "L88: rejected `fetchUser` escapes the `try` and crashes the route — repro: deleted user id." |
| "This could be slow." | "L120: query inside the `for` loop → N+1; 1 query per row. batch with a single `WHERE id IN (...)`." |
| "Might have a security issue." | "L33: `query(\`... ${name}\`)` interpolates raw input → SQL injection. parameterize." |
| "Naming is confusing." | (drop — does not change behavior; nitpick noise.) |

## The review-then-verify handoff

A read-only review produces claims of two kinds. End the review by separating them:

- **Evidenced** — confirmed by reading the code; the failing case is mechanical and
  certain. State it as fact.
- **Needs a run to confirm** — plausible from the code but not proven without executing.
  Name the exact check that would settle it: the test to run, the input to submit, the
  query to inspect, the log to watch.

For any **Critical or High** finding, prefer to actually reproduce it (run the case,
write a failing test, query the DB) rather than assert it — a false Critical erodes
trust as fast as a missed one. The review is complete when every load-bearing claim is
either evidenced or explicitly tagged "needs a run to confirm," with the confirming
check named. Accumulating findings without closing this loop is data, not a review.
