---
type: Reference
title: Review Dimensions
skill: code-review-craft
---

# The four review dimensions

Walk the diff once per dimension, in priority order. The dimensions are a stack, not a
flat list: when attention or time runs short, you drop from the bottom, never the top.

## 1. Correctness (highest priority)

Does the code do what it claims, for every input it will actually see? Hunt the cases
the happy path skips.

- **Edge inputs:** empty, null/undefined, zero, negative, very large, unicode,
  duplicate, unsorted. Which one returns a wrong value or throws?
- **Boundary conditions:** off-by-one, inclusive/exclusive ranges, first/last element,
  empty collection.
- **State and order:** is a value read before it is set? Does a second call behave like
  the first (idempotency)? Are async results awaited, and in the right order?
- **Error paths:** is a thrown/rejected error caught at the right level, or does it
  escape and crash? Is a failure swallowed silently (an anti-pattern — errors should be
  loud)?
- **Contract drift:** does the change still satisfy every caller? Did a return shape,
  null-ness, or unit change underneath callers that were not updated?
- **Concurrency:** shared mutable state, race between read and write, missing lock or
  transaction boundary.

> Grounded finding shape: "L42: `parseAmount('')` returns `NaN`, written straight to the
> ledger — repro: submit the form with the amount field blank."

## 2. Security

Assume input is hostile and secrets are valuable.

- **Injection:** untrusted input concatenated into SQL, shell, HTML, a path, or a
  template. Is it parameterized/escaped?
- **AuthZ/AuthN:** is the actor checked before the action? Does a cache key, query, or
  filter include the tenant/owner id, or can one user read another's data?
- **Secrets:** keys, tokens, passwords in code, logs, or error messages.
- **Unsafe deserialization / eval / SSRF / path traversal:** any place external data
  chooses code, a URL, or a file path.
- **Over-broad scope:** a new RLS policy, CORS rule, or permission that grants more than
  the feature needs.

> Grounded finding shape: "L77: the cache key is `user:{id}` with no tenant prefix —
> two tenants sharing a user id cross-read each other's records."

For a security-sensitive diff, run the **OWASP Top-10 lens and the scan recipes** in
`references/security-owasp.md`: it maps each finding above to an OWASP id (A01 broken
access → RLS/auth, A03 injection → parameterized queries, A06 vulnerable deps →
`npm audit --audit-level=high`, …) and gives copy-paste greps for hardcoded secrets,
direct-DB-call-vs-context-wrapper counts, missing auth checks, and SSRF.

## 3. Simplification and reuse

The best change removes code or reuses what exists.

- **Reinvention:** does a helper, constant, component, or design token already exist for
  this? Flag the duplication and point at the existing one.
- **Dead weight:** unreachable branch, unused variable/import, a flag that is never
  false, commented-out code left behind.
- **Needless complexity:** a nested ladder that flattens to a guard clause; a manual loop
  that a built-in expresses; a clever abstraction with one caller.
- **Hardcoding:** a literal hex, magic number, or string that should be a named
  constant/token.

> Grounded finding shape: "L30: inlines a date format that `utils/formatDate` already
> provides — reuse it, drop 9 lines."

## 4. Efficiency (lowest priority — never at the cost of correctness)

Only after the above. Real cost, not micro-theater.

- **Algorithmic:** an O(n²) scan inside a loop over the same data; a query in a loop
  (N+1) that one batched query replaces.
- **Wasted work:** re-fetching/re-computing an unchanged value; loading a whole table to
  count rows; building a large structure to read one field.
- **Resource leaks:** an opened handle, connection, or subscription never closed.

A finding here is only worth raising when the cost is on a real hot path or scales with
input. A micro-optimization on a once-per-request line that hurts readability is itself
a finding against the change.
