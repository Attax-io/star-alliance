---
name: api-integration-design
metadata:
  version: 1.0.0
type: Skill
description: "The Architect's craft for the API and integration boundary — designing the service contract you expose (REST or GraphQL resource modeling, versioning, pagination, idempotency, error and status conventions, webhooks, auth) and integrating the third-party APIs you consume (rate-limit handling, backoff, timeouts, circuit-breaking, replay, contract testing). The seam between two systems is where most production failures live; this craft makes that seam explicit, versioned, idempotent, and resilient. Use when designing the API for a feature, integrating a third-party API, designing webhook delivery and verification, versioning an endpoint, or hardening a flaky integration. Triggers: 'design the API for X', 'integrate this third-party API', 'design these webhooks', 'version this endpoint', 'handle rate limits', 'add idempotency', 'make this integration resilient'. Differentiate from schema-evolution (the DB schema and its consumers, not the network contract), supabase (Supabase platform features, not API contract design), and transactions-domain-model (one fixed Lex domain, not the integration boundary)."
---
# API & Integration Design — the Architect's craft

You design the seam between systems. The Architect already models the database and the domain;
this craft governs the boundary that crosses the network — both the **contract you publish** for
others to call, and the **third-party APIs you consume**. A schema lives inside one process and one
team; an API contract is read by clients you will never meet, on schedules you do not control, over
a network that drops, retries, and reorders. The seam is where most production incidents are born,
so your job is to make it explicit: a contract that is named, versioned, idempotent, honest about
its errors, and resilient when the other side misbehaves.

## What it is / is not

**It is** designing a service contract (REST or GraphQL): resource modeling, versioning, pagination,
idempotency, error/status conventions, webhook delivery and signature verification, and auth
(API keys, OAuth, JWT). And it is integrating someone else's API resiliently: timeouts, retries with
backoff, rate-limit handling, circuit-breaking, replay, and contract tests that catch drift.

**It is not** the database schema or its in-process consumers — that is `schema-evolution`. It is not
Supabase platform features (RLS, edge functions, realtime) — that is `supabase`. It is not a single
fixed business domain like Lex transactions — that is `transactions-domain-model`. This craft is the
**network boundary**: the wire contract and the integration code on both sides of it.

## Principles

Author and harden every boundary from these axioms. They compose; they are not a checklist.

### 1. The contract is the product; design it before the implementation
Clients couple to your contract, not your code. Decide the resource model, the verbs/queries, the
field names, the error shape, and the pagination style **first**, write them down (OpenAPI/GraphQL
SDL), and treat that document as the source of truth. Model resources as nouns with stable identity
(`/invoices/{id}`), not RPC verbs bolted onto URLs (`/createInvoice`). For REST, lean on HTTP
semantics — GET is safe and cacheable, PUT/DELETE are idempotent, POST creates. For GraphQL, the
schema *is* the contract; design types and nullability deliberately because every field is a promise.
> Example: "export the transactions" becomes `GET /transactions?cursor=…&limit=…` returning a typed
> page with a `next_cursor`, not a bespoke `/dumpAll` that streams an unbounded array nobody can page.

### 2. Change is inevitable; make it additive and versioned, never silently breaking
A published contract has consumers you cannot redeploy. Add fields as optional; never repurpose or
remove a field without a version step. Version explicitly (URL `/v2/`, header, or GraphQL field
deprecation with `@deprecated`) and keep the old version alive through a stated deprecation window.
Removing a field, tightening a type, or making an optional field required is a breaking change and
demands a new version — even if "nobody could possibly depend on it."
> Example: renaming `amount` to `amount_cents` is breaking; ship `amount_cents` alongside `amount`,
> deprecate `amount`, and remove it only after the window — the same additive discipline `schema-evolution`
> applies in-process, now applied across the wire.

### 3. The network lies; design for retries, so every unsafe operation is idempotent
Requests time out *after* the server committed. Clients will retry. If "create a payment" runs twice,
you double-charged. Make every non-idempotent operation safe to repeat: accept an `Idempotency-Key`,
persist the first result against it, and return that same result on replay. Webhooks have the same
hazard in reverse — deliver at-least-once and let receivers dedupe by event id. Idempotency is not a
nicety; it is the precondition that makes retries (yours and theirs) safe.
> Example: `POST /charges` with `Idempotency-Key: <uuid>` — the second arrival returns the first
> charge's response, not a second charge.

### 4. Errors are part of the contract; make them honest, structured, and actionable
Callers code against your failures as much as your successes. Use HTTP status codes for their real
meaning (4xx the caller can fix, 5xx the caller should retry), and return a **stable, structured**
error body — a machine-readable `code`, a human `message`, and enough context to act — not a bare
string or an HTML page. Signal retryability explicitly (`Retry-After`, a `retryable` flag). Never
leak stack traces or internals. On the consuming side, treat the other system's errors with the same
seriousness: distinguish "retry this" from "this will never succeed."
> Example: a rate-limited call returns `429` + `Retry-After: 2` + `{"code":"rate_limited"}`, so the
> client backs off correctly instead of hammering and guessing.

### 5. Authenticate explicitly; scope, expire, and verify every credential
State the auth mechanism per surface and match it to the caller: API keys for server-to-server, OAuth
for delegated user access, short-lived JWTs for stateless sessions. Scope credentials to least
privilege, give them expiry, and never trust input you did not sign. Webhooks must be authenticated
**inbound** — verify the HMAC signature against the raw body before you act, or anyone can forge your
events. Auth is a property of every endpoint and every received callback, not a gateway you pass once.
> Example: a Stripe-style webhook handler recomputes `HMAC-SHA256(secret, raw_body)`, constant-time
> compares it to the signature header, and rejects on mismatch — *before* parsing or trusting the payload.

### 6. The other system will fail; isolate it with timeouts, backoff, and circuit-breakers
You do not control the third party's uptime, latency, or rate limits, so a naive call lets their
outage become yours. Wrap every outbound integration: a finite **timeout** (never block forever),
**retry with exponential backoff + jitter** on transient/`5xx`/`429` (respecting `Retry-After`),
and a **circuit-breaker** that stops calling a failing dependency so it can recover and your threads
are not exhausted. Decide the degraded behavior — fail closed, fall back, or queue for replay — on
purpose, not by accident.
> Example: a flaky pricing API gets a 3s timeout, 3 backoff retries with jitter, and a breaker that
> opens after 5 consecutive failures and serves the last-known price until it half-opens.

### 7. Prove the seam with contract tests, because integrations drift silently
A boundary that "worked once" rots: the other side ships a v2, drops a field, or changes an enum, and
nothing in your unit tests notices. Pin the contract with tests that exercise the real shape —
schema/contract tests against the published spec, recorded fixtures for third parties, and a check
that runs against their sandbox. The test that fails when their `status` enum gains a value is worth
more than ten that mock the call away.
> Example: a contract test asserts the webhook payload still matches the agreed schema; when the
> provider adds `status: "partially_refunded"`, the test goes red before a customer does.

## References

- `references/contract-design.md` — REST + GraphQL resource modeling, versioning, pagination, idempotency keys, status/error conventions.
- `references/webhooks-and-events.md` — webhook delivery (at-least-once), retries, signature verification, dedupe, and event design.
- `references/integration-resilience.md` — timeouts, backoff + jitter, rate-limit handling, circuit-breaking, replay, and auth (keys/OAuth/JWT).
- `references/contract-testing.md` — contract/schema tests, provider sandboxes, fixtures, and catching drift.
