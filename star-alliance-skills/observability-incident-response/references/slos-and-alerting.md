---
type: Document
title: SLOs, error budgets, and alerting
description: SLIs/SLOs/error budgets, burn-rate alerting, and the symptom-vs-cause paging rule with worked thresholds for the guild stack.
timestamp: 2026-06-28T00:00:00Z
---

# SLOs, error budgets, and alerting

The goal of this discipline: every page corresponds to real user pain, and the
team trusts the pager enough to act on it at 3am. Alert fatigue is the enemy; it
is caused by paging on internal causes instead of user-felt symptoms.

## The ladder: SLI → SLO → error budget

- **SLI (Service Level Indicator)** — a *measured* number that proxies user
  happiness. Good SLIs are ratios of good events to valid events:
  `successful checkout requests / total checkout requests`, or
  `requests under 800ms / total requests`.
- **SLO (Service Level Objective)** — the *target* for an SLI over a window.
  "99.5% of checkout requests succeed within 800ms, measured over a rolling 28
  days." Pick a number you'd actually defend, not 100% (unaffordable, and removes
  all room to ship).
- **Error budget** — the inverse: `100% − SLO`. A 99.5% SLO grants a **0.5%**
  budget of failures. This is not a target to hit zero — it is a *resource to
  spend* on releases, experiments, and risk.

Choosing SLOs: start from the **critical user journeys** (load app, auth, the one
or two flows that are the product — for Lex Council, the transaction flows). Two
to four SLOs total. More than that and none of them mean anything.

## The error budget as a decision tool

The budget turns reliability from vibes into a number:

- **Budget healthy** → ship freely, take risks, run experiments.
- **Budget burning fast** → page (see below).
- **Budget exhausted** → freeze risky deploys, redirect the next cycle to
  reliability. This is an objective release brake that hands off to
  dev-ops-command-pack — not a political argument about "is it stable enough."

## Burn-rate alerting

Don't page the instant the SLI dips — page on how *fast* the budget is being
consumed. **Burn rate** = how many times faster than the sustainable rate you're
spending budget.

- **Fast burn** — e.g. the whole 28-day budget would be gone in a few hours.
  This is a real, now incident. **Page a human.**
- **Slow burn** — budget would be gone in days. Degrading but not acute. **Open a
  ticket**, look at it in working hours.

Worked example (99.5% / 28-day SLO on checkout):
- Fast-burn page: 2% error rate sustained over 5 min AND 1 hr (multi-window to
  avoid flapping) → budget would exhaust in hours → page.
- Slow-burn ticket: 0.7% error rate sustained over 6 hr → slow leak → ticket.

Multi-window (short AND long) thresholds stop a single 30-second blip from
paging while still catching a genuine fast burn quickly.

## The paging rule: symptoms page, causes inform

This is the single most important alerting decision.

- **Page on symptoms** — things users feel, expressed as SLO/RED breaches:
  elevated checkout error rate, p99 latency past the SLO, app unreachable.
- **Do NOT page on causes** — internal/USE metrics: "Postgres CPU 70%", "pool 60%
  utilized", "Worker CPU-time rising". These are dashboards you *consult once
  paged*, not pagers themselves.

Why: causes have many benign states and change constantly; paging on them buries
the team. A symptom page plus good cause dashboards means you wake up only for
real harm, then immediately see why.

## Alert hygiene

- Every alert names the SLO/symptom it protects and links the runbook for it.
- If the correct human response to an alert was "ignore," the alert is a bug —
  delete it or re-threshold it. An ignored alert poisons every alert beside it.
- Review alert→incident correlation periodically: alerts that never precede real
  incidents are noise; incidents with no preceding alert are coverage gaps to
  instrument (back to observability-signals).
