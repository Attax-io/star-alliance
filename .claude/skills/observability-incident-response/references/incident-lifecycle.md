---
type: Document
title: The incident lifecycle
description: The detect→triage→mitigate→resolve→post-mortem loop, incident roles and severity, and the live-event mitigation playbook for the guild stack.
timestamp: 2026-06-28T00:00:00Z
---

# The incident lifecycle

An incident is a live-service event with a clock running. The discipline below
exists to keep a stressed team coordinated and biased toward *stopping pain* over
*explaining pain*.

```
detect → triage → MITIGATE → resolve → post-mortem
                  ^^^^^^^^^                 (close the loop)
                  stop the bleeding first
```

Mitigate sits ahead of resolve on purpose: the live goal is the smallest user
harm, fastest — not the correct root-cause patch.

## Severity — set it early, it's cheap to downgrade

Severity drives how many people wake up. Decide it in the first minutes from
*user impact*, not from how scary the cause looks.

- **SEV1** — critical: the product is down or a core journey is broken for most
  users (checkout failing, app unreachable, data at risk). All hands; page the IC.
- **SEV2** — major: significant degradation or a subset of users / one important
  feature down. Page the on-call.
- **SEV3** — minor: limited impact, workaround exists, no budget emergency. Handle
  in hours; may become a `bug_reports` row rather than a live incident.

It is cheap to start at SEV2 and downgrade; it is expensive to under-call a SEV1.

## Roles — separate deciding from doing

Even a two-person incident benefits from explicit roles so coordination doesn't
compete with the fix.

- **Incident Commander (IC)** — owns decisions, severity, and the single source of
  truth. Does *not* type fixes. Decides when to roll back, when to escalate, when
  it's resolved.
- **Responder(s)** — hands on keyboard, investigating and mitigating, reporting
  findings to the IC.
- **Comms / Scribe** — keeps the running timeline and updates stakeholders, so the
  responder isn't context-switching to write status updates.

In a small guild one person may wear two hats, but the IC role — the decider —
should be named out loud.

## The phases

**Detect.** A page fired (good — your SLO alerting worked) or a human reported it.
Acknowledge, open an incident channel/timeline, set a provisional severity.

**Triage.** Establish blast radius and a working hypothesis fast. Three questions:
*Who is affected?* (all users / one route / one tenant), *What changed?* (recent
OpenNext deploy, Supabase migration, config flip, upstream provider), *Which
signal screams?* (RED error rate, USE saturation, a Supabase advisor). The
single highest-yield triage question is **"what shipped recently?"** — most
incidents are change-induced.

**Mitigate — stop the bleeding.** Reach for the cheapest reversible lever first.
Ranked for the guild stack:
1. **Roll back the last deploy** — if the timeline points at a recent OpenNext
   ship, revert it. Fastest, most common fix. (The mechanics live in
   dev-ops-command-pack; the *decision* lives here.)
2. **Flip a feature flag** off — disable the offending feature without a deploy.
3. **Relieve the resource** — raise the Supabase pool/limits, kill a runaway
   query, drain or scale, clear a poisoned cache.
4. **Fail over / degrade gracefully** — serve a cached or read-only path, shed
   non-critical load.
Mitigation can leave the *why* unknown. That's acceptable — log the hypothesis
and move on. A served user is the goal.

**Resolve.** Once users are safe, land the real fix and confirm the SLI recovers
on the dashboard (not on a hunch). Only the IC declares resolved, and only when
the signal — not the relief — confirms it. If the real fix is non-trivial, file it
(it may become a tracked `bug_reports` row) rather than rushing it under pressure.

**Post-mortem.** Always, for SEV1/SEV2. Covered in runbooks-and-postmortem.

## Communication cadence

- Post an initial status within minutes ("investigating elevated checkout errors,
  SEV2, IC = X") even before you know the cause. Silence breeds escalation.
- Update on a fixed cadence (e.g. every 30 min for SEV2, more often for SEV1) and
  on every state change (mitigated, resolved).
- One channel, one timeline, one IC. Fragmented comms is how incidents double in
  length.
