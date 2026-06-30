---
title: Contract Design — REST & GraphQL
type: reference
---
# Contract Design — REST & GraphQL

The contract is the product (Principle 1) and changes additively (Principle 2). This file is the
detail behind those axioms.

## Resource modeling (REST)

- Model **nouns with stable identity**, not actions: `/invoices/{id}`, `/invoices/{id}/lines`, not
  `/getInvoice` or `/createInvoice`. Verbs live in the HTTP method.
- Use HTTP semantics honestly:
  - `GET` — safe, cacheable, no side effects.
  - `POST` — create / non-idempotent action.
  - `PUT` — full replace, idempotent.
  - `PATCH` — partial update.
  - `DELETE` — idempotent removal.
- Collections vs. members: `GET /invoices` (list) vs. `GET /invoices/{id}` (one). Sub-resources for
  composition, query params for filtering/sorting (`?status=open&sort=-created_at`).
- Keep field names stable and consistent (one casing convention; one date format — ISO-8601 UTC).

## Resource modeling (GraphQL)

- The SDL **is** the contract. Design types, fields, and **nullability** deliberately — a non-null
  field is a permanent promise; widening to nullable later is breaking for clients that assumed it.
- Prefer a small, composable type graph over many bespoke query fields. Use input types for mutations.
- Mutations should return the mutated entity (and a payload wrapper) so clients can update caches.
- Avoid the N+1 trap at design time: model list fields knowing they'll need batching (dataloader).

## Versioning

| Style | Where | Use when |
|-------|-------|----------|
| URL path | `/v1/…`, `/v2/…` | Coarse, visible, easy to route. Most public REST APIs. |
| Header | `Accept: application/vnd.app.v2+json` | Cleaner URLs, content-negotiation shops. |
| Field-level | GraphQL `@deprecated(reason: …)` | Evolve a graph without a hard cut. |

- **Additive is free**: new optional fields, new endpoints, new enum values *clients tolerate*.
- **Breaking** (new version required): removing/renaming a field, tightening a type, making optional →
  required, changing an error code's meaning, changing pagination shape.
- Announce a **deprecation window** and emit a `Deprecation`/`Sunset` header on the old version.

## Pagination

- **Cursor-based (preferred)** for large or mutating sets: return an opaque `next_cursor`; the client
  passes it back. Stable under inserts/deletes, no deep-offset cost.
  `GET /transactions?limit=50&cursor=eyJpZCI6…` → `{ "data": [...], "next_cursor": "…" }`.
- **Offset/limit** only for small, stable, human-paged sets — it skips/duplicates rows when the
  underlying data changes and gets slow at depth.
- Always cap `limit` server-side; document the max.

## Idempotency keys (the mechanism for Principle 3)

- Accept an `Idempotency-Key: <uuid>` header on unsafe operations (`POST` that creates/charges).
- Persist `(key → first response, status)` for a retention window (e.g. 24h).
- On replay with the same key: return the **stored** response, do not re-execute the side effect.
- Scope keys per endpoint + per account so collisions across callers are impossible.

## Status & error conventions

- Success: `200` (OK), `201` (Created, with `Location`), `202` (Accepted, async), `204` (No Content).
- Client error (caller can fix): `400` malformed, `401` unauthenticated, `403` unauthorized,
  `404` not found, `409` conflict, `422` validation, `429` rate-limited (+ `Retry-After`).
- Server error (caller may retry): `500`, `502`, `503` (+ `Retry-After`), `504`.
- Body: a stable structured shape, e.g.
  ```json
  { "error": { "code": "validation_failed", "message": "amount must be > 0",
               "field": "amount", "retryable": false } }
  ```
- `code` is machine-stable and part of the contract — never reword it as if it were prose.
