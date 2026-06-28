---
title: Integration Resilience & Auth
type: reference
---
# Integration Resilience & Auth

When you *consume* a third party, their failure must not become yours (Principle 6) and every
credential must be scoped, expiring, and verified (Principle 5).

## The outbound-call envelope

Wrap every third-party call in these layers, outermost to innermost:

1. **Timeout** — always finite. A call with no timeout blocks a thread forever during their outage.
   Set both a connect and a read timeout; size them to your own SLA, not their best case.
2. **Retry with backoff + jitter** — only on **transient** failures: connection errors, `5xx`, `429`.
   Never retry a `4xx` the caller caused (it will fail again). Delay grows exponentially
   (`base * 2^n`) with random jitter to avoid thundering-herd synchronization; cap attempts and total
   time. **Honor `Retry-After`** when present — it overrides your computed delay.
3. **Circuit-breaker** — track recent failures; after a threshold of consecutive failures, **open**
   the circuit and fail fast (or fall back) without calling, so a dead dependency stops consuming your
   threads and gets room to recover. After a cooldown, **half-open**: allow one probe; success closes
   it, failure re-opens.
4. **Bulkhead / concurrency cap** — bound concurrent calls to one dependency so its slowness can't
   drain your whole pool.

## Rate limits

- Read the provider's limit headers (`X-RateLimit-Remaining`, `X-RateLimit-Reset`) and **self-throttle
  before** they `429` you — proactive is cheaper than reactive.
- On `429`, back off using `Retry-After`; do not blindly retry.
- For bursty work, use a client-side token bucket so you stay under their ceiling.

## Degraded behavior — decide on purpose

When the dependency is down, your fallback is a design decision, not an accident:

- **Fail closed** — reject the operation (correct for payments, anything unsafe to fake).
- **Fall back** — serve cached/last-known data or a default (correct for non-critical reads).
- **Queue + replay** — accept the request, enqueue it, process when the dependency returns
  (correct for async, fire-and-forget side effects). Make the replayed work idempotent (Principle 3).

## Replay & dead-letters

- Persist failed outbound operations with enough context to retry later.
- A dead-letter queue + a manual/automatic replay path turns a transient outage into a delay, not a
  data-loss event.

## Auth (per surface, least privilege)

| Mechanism | Use for | Notes |
|-----------|---------|-------|
| **API key** | server-to-server | Simple. Scope per integration; store as a secret; rotate. Never in client code. |
| **OAuth 2.0** | delegated user access | Authorization-code + refresh for user data; client-credentials for service-to-service. Store refresh tokens encrypted; handle refresh + revocation. |
| **JWT** | stateless sessions / service identity | Short expiry; **verify the signature and `aud`/`iss`/`exp`** on every request; rotate signing keys (JWKS). A JWT you don't verify is just a claim. |

Cross-cutting rules:
- **Least privilege**: scope every credential to exactly what the integration needs.
- **Expiry + rotation**: nothing lives forever; support overlapping secrets during rotation.
- **Never trust unsigned input**: verify signatures on inbound callbacks/webhooks before acting.
- **Secrets out of code and logs**: env/secret-manager only; redact tokens in error reporting.
