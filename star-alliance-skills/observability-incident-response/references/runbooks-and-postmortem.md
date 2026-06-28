---
type: Document
title: Runbooks and blameless post-mortems
description: Runbook anatomy and template, plus the blameless post-mortem structure and action-item discipline that closes an incident into a system change.
timestamp: 2026-06-28T00:00:00Z
---

# Runbooks and blameless post-mortems

An incident is not over when the graph recovers. It is over when (a) the next
responder will be faster — a **runbook** — and (b) the failure mode can't recur
unnoticed — a **post-mortem with owned actions**. These two artifacts are how an
incident pays for itself.

## Runbooks — operational, not narrative

A runbook is a per-symptom recipe for the on-call human at 3am. It is terse,
imperative, and tells them what to *do*, not the history of the system. The best
runbooks are written *as a byproduct of an incident*, while the steps are fresh.

A runbook entry has four parts:

1. **Symptom** — what fired / what the user sees. "Checkout error rate page;
   users see a 500 on submit."
2. **Confirm** — how to verify it's real and what flavor. "Check the checkout RED
   dashboard; `wrangler tail` for `error_code` on `/api/checkout`; check Supabase
   advisors and pool saturation."
3. **Mitigate** — ordered, concrete steps. "1. Was there a deploy in the last hour?
   If yes, roll it back. 2. Else check Postgres pool saturation; if maxed, raise
   pool / kill the longest query. 3. Else flip the `checkout_v2` flag off."
4. **Escalate** — who/what if the above fails, and when to bump severity.

Keep runbooks beside the alert that triggers them: every page links its runbook.
A page with no runbook is a gap; note it and write the runbook from the incident
you just ran.

### Minimal runbook template

```
## Runbook: <symptom name>
Severity hint: SEV<n> | Owner: <team/person>

SYMPTOM
- <what fires, what users see>

CONFIRM
- <dashboard / query / log filter to verify>

MITIGATE (in order, stop when fixed)
1. <cheapest reversible lever — usually: was there a recent deploy? roll back>
2. <next lever>
3. <next lever>

ESCALATE
- If not mitigated in <N> min → page <role>, raise to SEV<n-1>
```

## Blameless post-mortems

The post-mortem converts pain into a durable system change. Its governing
assumption: **everyone acted reasonably given the information they had at the
time.** Hindsight is not a fair lens. When you catch yourself writing "they
should have known," rewrite it as "the system didn't make X visible."

Why blameless is not just kindness: blame makes people hide context, and hidden
context is exactly what the next responder needs. A blameless culture surfaces
the real causal chain; a blaming one buries it.

### Post-mortem structure

- **Summary** — one paragraph: what broke, who was affected, how long, severity.
- **Impact** — quantified: % of requests/users, duration, error-budget spent,
  any data/financial consequence.
- **Timeline** — detection → triage → mitigation → resolution, with timestamps.
  Built from the live incident timeline.
- **Root cause(s)** — the real causal chain. Use the "5 whys" but resist stopping
  at the first human action; keep asking why the *system* allowed it. Most
  incidents have a chain, not a single villain.
- **What went well / what was hard** — name the things that helped (a good alert,
  a fast rollback) and the friction (a missing dashboard, an ambiguous runbook).
- **Action items** — the only part that prevents recurrence. Each must have an
  **owner**, a **due date**, and be a concrete system change.

### Action-item discipline

The quality of a post-mortem is the quality of its actions. A good action item is
a specific, owned, dated change to the system. A bad one is an exhortation.

- Bad: "be more careful when deploying," "watch the pool more closely."
- Good: "add a fast-burn SLO alert on checkout error rate — @dev, by 2026-07-05,"
  "add Postgres pool saturation to the on-call dashboard," "fix the checkout
  runbook step 2 which pointed at the wrong query," "add a deploy guard that
  blocks ship when the error budget is exhausted."

Every action item that is "instrument X" feeds straight back to
observability-signals — the incident named a question you couldn't answer fast
enough, so now you make it answerable. That is the loop closing: response exposes
a blind spot, observability fills it, the next incident is shorter.
