---
name: observability-incident-response
metadata:
  version: 1.0.0
type: Skill
description: "Keep a live service observable and respond when it breaks. Covers the three signals (structured logs, RED/USE metrics, distributed traces), alerting thresholds tied to SLOs and error budgets, and the incident lifecycle: detect, triage, mitigate, resolve, then a blameless post-mortem with a runbook. Grounded in the guild stack (Next.js on Cloudflare/OpenNext Workers, Supabase/Postgres). Triggers: 'the app is down', 'triage this outage', 'set up alerting', 'write a runbook', 'post-mortem this incident', 'add logging', 'add metrics', 'what's our SLO', 'are we paging on the right thing'. Differs from dev-ops-command-pack (the deploy/rollback/release loop), performance (profiling and optimization of healthy code), and bug-fix-workflow (a single tracked bug in the table) — this is run-time visibility and the live-failure response that surrounds them."
---

# Observability & Incident Response

The craft of running a service you can **see into**, and responding with calm
discipline when it breaks. Observability is the standing investment — the
instrumentation that lets you ask new questions of a live system without
shipping new code. Incident response is the acute skill — the ordered loop that
turns a 3am page into a mitigated service and a learned-from write-up.

The two are one craft because they feed each other: every incident exposes a
blind spot to instrument, and every good signal shortens the next incident.
A team that only instruments is blind to its own response gaps; a team that only
firefights re-fights the same fire. This skill keeps both halves honest.

Ground it in the guild stack: a Next.js app on Cloudflare via OpenNext Workers,
with Supabase/Postgres behind it. The signals live in Worker logs / `wrangler
tail`, Cloudflare analytics, and Supabase logs + advisors. The principles below
are stack-agnostic; the examples are not.

## What it is

- A **signals doctrine**: structured logs, metrics (RED for request-driven
  surfaces, USE for resources), and distributed traces — and when to reach for each.
- An **alerting philosophy**: page on symptoms users feel, derived from SLOs and
  spent against an error budget — not on every twitchy internal metric.
- An **incident lifecycle**: detect → triage → mitigate → resolve → post-mortem,
  with mitigation ranked above root-cause during the live event.
- A **memory discipline**: runbooks that capture the response, and blameless
  retros that convert pain into a system change, not a scapegoat.

## What it is not

- **Not dev-ops-command-pack** — that is the deploy / rollback / release loop.
  This skill watches what that loop ships and responds when it misbehaves. (Rollback
  is often the fastest *mitigation* here, but the deploy machinery lives there.)
- **Not performance** — that profiles and optimizes healthy code for speed. This
  is run-time *visibility* and *failure response*; a latency SLO breach may hand
  off to performance, but triage comes first.
- **Not bug-fix-workflow** — that works a single tracked row in `bug_reports`. An
  incident may *spawn* such a bug, but an incident is a live-service event with a
  clock running, not a backlog item.

## Generative principles

These compose; they are not a checklist. Read them as axioms you can apply to a
situation the examples never named.

### 1. Instrument for unknown questions, not known dashboards

A dashboard answers a question you already had. Observability is the ability to
ask a question you *didn't* anticipate — at 3am, about a request you've never
seen — without deploying. That means **high-cardinality, structured, contextual**
signals over pre-aggregated counters.

- Emit logs as structured JSON with stable keys, never prose. A Worker log line
  carrying `{ request_id, route, user_id, supabase_latency_ms, status, error_code }`
  lets you slice by any field after the fact. `console.log("slow query!")` does not.
- Thread a **request/trace id** from the Worker through every Supabase call and
  back into the response header, so one failing user request is reconstructible
  end-to-end.
- Prefer a few wide events per request over many narrow metrics. One rich event
  per request beats fifteen disconnected counters you can't join.

The test: when something breaks in a way you didn't predict, can you answer the
new question from existing data? If you must ship code to see, you were blind.

### 2. Measure the user's experience, then the machine's — RED over USE at the edge

There are two metric families and they answer different questions. **RED** (Rate,
Errors, Duration) describes *request-driven* surfaces — your routes, your API,
your edge. **USE** (Utilization, Saturation, Errors) describes *resources* — the
Postgres connection pool, Worker CPU/subrequest limits, memory.

- For each Next.js route and Supabase RPC, track RED: requests/sec, error rate,
  and p50/p95/p99 latency. p99 is where users actually suffer; a healthy average
  hides a burning tail.
- For each resource, track USE: Postgres pool utilization and saturation (queued
  connections), Worker subrequest count against the platform cap, CPU-time per
  invocation. Saturation predicts the outage RED will later report.
- **Symptoms (RED) page humans; causes (USE) explain.** Alert on the error rate
  users feel; let pool-saturation be the thing you *look at* once paged.

### 3. Alert on SLOs spent against an error budget — page on pain, not on noise

An alert that doesn't correspond to user harm trains the team to ignore alerts.
Define a handful of **SLOs** (e.g. "99.5% of checkout requests succeed under
800ms over 28 days"). The allowed failure is your **error budget**. Page when the
budget is burning *fast*, not at every momentary blip.

- Tie every page to an SLO and a user-visible symptom. "Postgres CPU at 70%" is
  not pageable; "checkout error rate breached its fast-burn budget" is.
- Use **burn-rate** alerting: a fast burn (budget gone in hours) pages now; a slow
  burn (gone in days) opens a ticket. Two thresholds, two urgencies.
- The error budget is also a **release brake**: budget exhausted means freeze
  risky deploys and spend the next cycle on reliability — a concrete, non-political
  signal that hands off to dev-ops-command-pack.

If a pager goes off and the right human response was "ignore it," the alert is the
bug. Delete or re-threshold it.

### 4. In a live incident, mitigate before you diagnose — the clock is the boss

Root cause is a luxury of calm. During an incident the goal is to **stop user
pain fastest**, even if the why is still unknown. The lifecycle is
detect → triage → **mitigate** → resolve → post-mortem, and mitigate is
deliberately ahead of resolve.

- Reach first for the cheapest reversible lever: roll back the last OpenNext
  deploy, flip a feature flag, scale or drain a resource, fail over. A rollback
  that fixes it now beats a perfect patch in an hour.
- Run the incident with explicit **roles** — one Incident Commander who owns
  decisions and comms, separate from the hands-on responder — so coordination
  doesn't compete with the fix. Keep one running timeline as you go.
- Resolve (the real fix) and the *understanding* come **after** mitigation. Note
  the hypothesis, but don't gate stopping the bleed on proving it.

### 5. Close every incident into the system — runbook and blameless retro, or it recurs

An incident isn't over when the graph recovers; it's over when it can't recur the
same way unnoticed. The artifacts are a **runbook** (so the next responder is
faster) and a **blameless post-mortem** (so the system, not a person, changes).

- A runbook is operational, not narrative: symptom → how to confirm → mitigation
  steps → escalation. Write it *from* the incident while it's fresh; the best
  runbooks are post-mortem byproducts.
- Run the retro **blameless**: assume everyone acted reasonably on the information
  they had. The output is system change — an alert, a guardrail, a fixed runbook,
  an instrumentation gap closed — with an owner and a date, never "be more careful."
- Feed the loop back to principle 1: the incident named a question you couldn't
  answer fast enough. Instrument it now, so next time you can.

## References

- `references/observability-signals.md` — logs, metrics (RED/USE), tracing, and
  what each looks like on the Next.js / Cloudflare-OpenNext / Supabase stack.
- `references/slos-and-alerting.md` — SLIs, SLOs, error budgets, burn-rate
  alerting, and the symptom-vs-cause paging rule with worked thresholds.
- `references/incident-lifecycle.md` — the detect→resolve loop, incident roles and
  severity, and the live-event mitigation playbook for the guild stack.
- `references/runbooks-and-postmortem.md` — runbook anatomy and a template, plus
  the blameless post-mortem structure and action-item discipline.

Plugin knowledge worth pulling alongside this skill: `operations:runbook` (runbook
authoring) and `engineering:incident-response` (incident process patterns).
