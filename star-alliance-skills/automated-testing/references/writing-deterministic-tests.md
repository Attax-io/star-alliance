---
type: Document
title: Writing deterministic tests
description: Killing flake at the source — time, randomness, async, ordering, shared state, network — plus factories, fixtures, and where to mock in a Next.js + Supabase suite.
timestamp: 2026-06-28T00:00:00Z
---

# Writing deterministic tests

A test must return the **same verdict every run, on every machine**. Flake is not a minor
annoyance — it is corrosive: a suite that cries wolf trains the team to merge over red, and
then the one real failure is invisible. Determinism is the price of a suite anyone trusts.
Every source of nondeterminism below has a fix; apply it at authoring time, not after the
suite starts flaking.

## The sources of flake and their fixes

### Time

Never let an assertion depend on the wall clock. A test that computes "days until expiry" from
`new Date()` passes today and fails next month.

```ts
import { vi } from 'vitest'
beforeEach(() => { vi.useFakeTimers(); vi.setSystemTime(new Date('2026-01-01T00:00:00Z')) })
afterEach(() => vi.useRealTimers())
// advance deliberately:
vi.advanceTimersByTime(1000)
```

Inject the clock where you can (`now: () => Date`), so production code does not read the clock
directly and tests pass a fixed one.

### Randomness and ids

`Math.random`, `crypto.randomUUID`, and faker without a seed make assertions and snapshots
unstable. Seed faker (`faker.seed(1)`), stub the RNG, or — better — make ids an **input** to
the code under test rather than something it generates internally.

### Async — await the outcome, never sleep

A fixed `sleep(500)` is a bet that the machine is fast enough; CI loses that bet. Wait on the
**condition**, not the clock.

- Testing Library: use `findBy*` (async query that retries) and `waitFor(() => expect(...))`.
  Wrap user interactions so pending updates flush; assert on the resolved DOM.
- Never assert immediately after an action that triggers async work without awaiting it.

```ts
await userEvent.click(screen.getByRole('button', { name: 'Save' }))
expect(await screen.findByText('Saved')).toBeVisible() // retries until it appears
```

### Order and shared state

Tests must pass **in any order and in isolation**. The classic flake is test B relying on a row
test A inserted. Defenses:

- Reset between tests: clear mocks (`vi.clearAllMocks()`), reset the jsdom/render, and **truncate
  or transaction-rollback the test DB** between integration tests (or give each test its own
  org/tenant id so they cannot collide).
- No module-level mutable state shared across tests. No ordering assumptions.
- Run the suite in a randomized order in CI occasionally to flush out hidden coupling.

### Network

Real third-party calls make the suite hostage to someone else's uptime and rate limits, and
introduce latency variance. Intercept at the boundary:

- **MSW** (Mock Service Worker) for `fetch`/HTTP in unit and component tests — one place to
  define handlers, reused across the suite.
- In Playwright, `page.route(...)` to stub or fault-inject specific requests.
- Keep the contract honest: stub the **shape** the real API returns, and have at least one
  integration test that hits the real boundary so the stub cannot drift forever.

## Factories over fixtures-as-literals

Hand-built object literals are a maintenance bomb: add a required field and dozens of tests
break at once, none of them about that field. Generate data through factories that accept
overrides; each test then states **only the field it cares about**.

```ts
export const makeInvoice = (o: Partial<Invoice> = {}): Invoice => ({
  id: crypto.randomUUID(),
  orgId: 'org_1',
  status: 'draft',
  cents: 1000,
  createdAt: '2026-01-01T00:00:00Z',
  ...o,
})
// a test about paid invoices says only that:
const paid = makeInvoice({ status: 'paid' })
```

A small set of well-named factories beats a sprawling `fixtures.json`. Keep factory defaults
**valid** (they pass your schema) so an override is the only thing a reader must reason about.

## Where to mock — boundaries, not your own code

Mock the edges you do **not** own: the clock, the RNG, the network, a third-party SDK, the
email/payment provider. Do **not** mock your own modules to avoid wiring them — that is the
integration layer's purpose, and over-mocking produces a suite that is green while the product
is broken, because every seam was faked.

For Supabase specifically:

- **Component test** that merely renders data: mock the data-fetching function or pass data as
  props. The DB is irrelevant to whether the component renders the rows.
- **Integration test** of a server action / query / RLS policy: use a **real seeded test DB** —
  a local `supabase` CLI instance or a disposable branch — so constraints, triggers, and RLS
  run for real. A hand-faked `supabase-js` client cannot prove RLS; only the real engine can.
- Reach for a fake client only in a thin unit test where you are testing *your* glue logic and
  the DB genuinely does not matter.

## A determinism checklist for any test

- No `new Date()`, `Math.random`, or unseeded faker in the path under assertion.
- No `setTimeout`/`waitForTimeout`/`sleep` — wait on conditions.
- Passes alone and passes in a randomized order; leaves no residue in the DB or shared state.
- No real network; boundaries intercepted; stubs match the real shape.
- Re-running it 50 times in a loop is green 50 times. If not, it has found a real race — fix the
  cause, never add a retry.
