---
type: Document
title: Test pyramid and strategy
description: Choosing the right test layer, what to test vs skip, coverage strategy, and how the four layers map onto a Next.js + TypeScript + Supabase app.
timestamp: 2026-06-28T00:00:00Z
---

# Test pyramid and strategy

The pyramid is a budget. You have finite time to write and finite seconds to run; spend
both where they buy the most confidence per unit. Lower layers are cheap and precise;
higher layers are expensive but prove the pieces connect. Author each behaviour at the
**lowest layer that can honestly verify it**, and let the higher layers prove only the
seams the lower ones cannot reach.

## The four layers in this stack

| Layer | Tool | Proves | Speed | Count |
|---|---|---|---|---|
| Unit | Vitest / Jest | pure logic, schemas, predicates, reducers | µs–ms | many |
| Component | Testing Library + jsdom | a component behaves as a user sees it | ms | many |
| Integration | Vitest + seeded Supabase | a boundary works end-to-end (server action ↔ DB, RLS) | ms–s | some |
| E2E | Playwright | a real user journey through the built app | s | few |

### Unit — the base

Pure functions and pure logic, no DOM and no network. In a Next.js app this is: Zod schema
validation, money/date/format helpers, permission predicates (`canEdit(user, doc)`), reducers
and pure hooks' logic, server-side mappers that turn a DB row into a view model. These are the
bulk of the suite because they are where branching logic lives and where bugs are cheapest to
localize. If a function takes data in and returns data out, it is a unit test.

### Component — user-visible behaviour

A rendered React component, queried the way a user perceives it. Test: it renders the rows it
is given, it shows the validation error, the submit button disables while pending, the empty
state appears when the list is empty. Render with Testing Library, query by role/label/text,
interact with `userEvent`, assert on the DOM. Mock the data-fetching boundary (the server
action or the `supabase-js` call) so the component test stays about *the component*, not the DB.

### Integration — the seams

Several real units across one boundary, with the boundary real. The highest-value examples in
this stack:

- A **server action** or **route handler** that validates input and writes to Supabase — run
  it against a **seeded test database**, assert the row landed and the return value is correct.
- The **query/data layer** — run a real query as a real (impersonated) user and assert the rows
  and the **RLS** outcome.
- A **trigger or constraint** firing on insert — let the real DB enforce it.

Integration tests are where "all the units pass but the app is broken" gets caught. Do not mock
your own DB here; mock only what is genuinely external (a payment SDK, an email provider).

### E2E — the journey

Playwright drives the built app in a real browser through a critical path: sign in → create a
record → see it in the list → sign out. These are slow and the most expensive to maintain, so
keep them **few and load-bearing**: the signup/login flow, the primary create/edit flow, the
money or irreversible flows, and one happy path per critical feature. Do **not** test every
branch and error message through E2E — push those down to component/unit.

## What to test, and what to skip

**Test:**
- Every branch of meaningful business logic (each `if`, each guard, each error path).
- Every public contract a module promises its callers.
- Authorization boundaries — and the **negative** case especially (wrong user gets nothing).
- The unhappy paths: failed fetch, empty state, validation error, expired session.
- Anything a bug-fix just touched — leave a regression test so it never returns.

**Skip (or test thinly):**
- Trivial passthroughs and generated code (typed Supabase clients, codegen, framework glue).
- Pure configuration and constants.
- Third-party libraries — assume they work; test *your use* of them at a boundary, not them.
- Visual exactness — that is a snapshot/visual-regression concern, not a behaviour assertion.

## Coverage strategy

Coverage is a **flashlight, not a target**. It answers "which lines did no test touch?" — read
it to find untested branches in important code, then decide case-by-case which deserve a test.
The moment a coverage percentage becomes the goal, people write decorative tests to color lines
green and the number stops meaning anything (Goodhart's law).

Practical policy:

- Require coverage **not to regress** in critical directories on a PR, rather than a single
  global floor everyone games.
- Treat an untested branch in money/auth/data code as a gap to close; treat an untested trivial
  getter as noise.
- The real test of the suite is the **mutation question**: if you flipped a `>` to `>=` or
  deleted a guard, would a test go red? If not, the behaviour is uncovered no matter what the
  line-coverage report says.

## Naming and structure

- Name the file beside the unit (`price.ts` → `price.test.ts`) or under a parallel `__tests__`/
  `e2e/` tree; be consistent across the repo.
- Name each test for the **behaviour**: `test('disables submit while saving')`, not
  `test('button works')`. The test name is the spec line.
- Keep the **same run command** local and in CI so green means the same thing everywhere.
