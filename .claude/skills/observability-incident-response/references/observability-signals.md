---
type: Document
title: Observability signals — logs, metrics, traces
description: The three pillars (structured logs, RED/USE metrics, distributed traces) and how each lands on the Next.js / Cloudflare-OpenNext / Supabase stack.
timestamp: 2026-06-28T00:00:00Z
---

# Observability signals

Three signal types answer three different questions. You want all three, joinable
by a shared id.

| Signal | Answers | Cardinality | Cost |
| --- | --- | --- | --- |
| **Logs** | "What exactly happened to *this* request?" | High | Per-event |
| **Metrics** | "What's the rate/shape across *all* requests?" | Low (aggregated) | Cheap |
| **Traces** | "Where did the time/error go across services?" | High | Sampled |

The craft is wiring them so one `request_id` lets you pivot from a metric spike →
to the traces in that window → to the exact log lines.

## Structured logs

Logs are the most flexible signal and the easiest to do badly. Rules:

- **JSON, not prose.** Stable keys; values typed. A Worker line:
  `{ "ts": "...", "level": "error", "request_id": "...", "route": "/api/checkout", "user_id": "...", "supabase_latency_ms": 412, "status": 500, "error_code": "PGRST301" }`.
- **One canonical id per request**, generated at the Worker edge and threaded into
  every downstream Supabase call (pass it as a header / RPC arg) and back out in a
  response header (`x-request-id`). This is what makes a single user complaint
  reconstructible.
- **Levels mean something.** `error` = a request failed or an invariant broke;
  `warn` = degraded but served; `info` = lifecycle; `debug` = off in prod. Pages
  key off `error`, so don't cry-wolf at that level.
- **Never log secrets or PII you don't need** — tokens, full rows, auth headers.
  Log the `user_id`, not the session JWT.

On the stack: Worker logs are visible via `wrangler tail` (live) and the
Cloudflare dashboard / Logpush (retained). Supabase has its own logs +
`get_advisors` for security/perf findings. Treat all three as one corpus joined by
`request_id`.

## Metrics — RED and USE

Two families, two purposes. Don't mix them up.

**RED — for request-driven surfaces** (routes, APIs, RPCs):
- **Rate** — requests/sec per route. Sudden drop can mean an upstream outage
  *before* errors show.
- **Errors** — error rate (5xx, thrown RPCs, failed auth). The headline user-pain
  number.
- **Duration** — latency distribution. **Track p50/p95/p99, never just the mean.**
  The mean is a comfortable lie; p99 is the user who rage-quits.

**USE — for resources** (Postgres pool, Worker limits, memory):
- **Utilization** — % of the resource busy (pool connections in use).
- **Saturation** — queued/waiting work (connections waiting on the pool). Rising
  saturation is the **leading indicator** of the outage RED will soon report.
- **Errors** — resource-level failures (pool timeouts, subrequest-cap hits,
  OOM/CPU-time exceeded on the Worker).

Guild-stack resources to watch with USE: Postgres connection-pool (Supabase
pooler) utilization & wait; Worker CPU-time per invocation and subrequest count
against the platform cap; any KV/D1/cache hit-rate.

**Pairing rule:** RED tells you users are hurting; USE tells you which resource is
why. Page on RED, diagnose with USE.

## Distributed tracing

A trace follows one request across hops (Worker → Supabase → Postgres → back),
each hop a timed **span**. Traces answer "*where* did the 800ms go?" in a way logs
and metrics can't.

- Propagate the trace/request id across every boundary so spans stitch into one
  waterfall.
- **Sample** — you don't need every trace; sample a percentage plus *always keep
  errors and slow requests* (tail-based sampling). Full-fidelity tracing is
  expensive and rarely needed.
- The payoff in an incident: a p99 latency alert → open a slow trace from that
  window → see instantly whether the time is in the Worker, the network, or a
  specific Postgres query.

## The joinability test

The whole system works only if the signals connect. Before you call a service
observable, confirm: from a metric anomaly, can you reach the traces in that
window, and from a trace, the exact log lines — all by one shared id? If any pivot
requires guesswork, that's the gap to close next.
