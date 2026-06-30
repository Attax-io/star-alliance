---
title: Contract Testing
type: reference
---
# Contract Testing

Integrations rot silently (Principle 7): the other side ships a v2, drops a field, or grows an enum,
and nothing notices until a customer does. Contract tests pin the seam so drift fails a build, not a
user.

## What a contract test asserts

That the **shape** crossing the boundary still matches the agreed spec — field names, types,
nullability, enum values, status codes, pagination shape — independent of business logic. It answers
"does the wire format still hold?", not "is the number right?".

## Provider side (the API you publish)

- Generate or hand-write an **OpenAPI / GraphQL SDL** spec and treat it as the source of truth.
- Validate **responses against the spec** in tests: every endpoint's success and error bodies conform.
- Run a **spec-diff in CI**: compare the current spec to the last released one and flag breaking
  changes (removed field, tightened type, optional→required) so a breaking change can't merge without
  a version bump (Principle 2).
- Snapshot example payloads so reviewers see the wire shape change in the diff.

## Consumer side (the third party you call)

- Keep **recorded fixtures** of the provider's real responses (success, error, edge cases). Tests run
  against fixtures for speed and determinism — fast, offline, deterministic.
- Add a **schema test against the live sandbox** on a schedule (nightly/CI cron): hit their sandbox,
  assert the response still matches your recorded schema. This is what catches *their* drift before
  production does.
- Test the **failure paths** explicitly: `429` triggers backoff, `5xx` triggers retry then breaker,
  malformed body is rejected — the resilience envelope (Principle 6) is itself under test.
- Pin the provider's `api_version` where they offer one; a green sandbox test on a pinned version is
  your early-warning that an upgrade will (or won't) break you.

## Consumer-driven contracts (when teams share an org)

- The consumer publishes the subset of the contract it actually depends on; the provider verifies
  against every consumer's expectations before release (the Pact pattern).
- This makes the *real* coupling explicit, so the provider can change anything no consumer relies on —
  and nothing a consumer does.

## Webhook contracts

- Assert received webhook payloads still match the agreed event schema (per `type`, per `api_version`).
- The test that goes red when the provider adds `status: "partially_refunded"` is worth more than ten
  that mock the webhook away — that new enum value is exactly the silent drift this catches.

## Heuristics

- A mock that always returns the happy shape proves nothing about *their* current behavior — pair every
  mock-based unit test with at least one fixture or sandbox test grounded in reality.
- Make the contract test fail **loud and specific**: name the field and the change, so the fix is
  obvious without a debugger.
