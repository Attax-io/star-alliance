---
name: automated-testing
metadata:
  version: 1.1.0
type: Skill
description: "Author automated tests for a modern web app — the JS/TS plus application layer, grounded in Next.js/TypeScript plus Supabase. Covers the four layers (unit with Vitest/Jest, component with Testing Library, integration against a real or seeded DB, and E2E with Playwright), the test pyramid and coverage strategy, what is worth testing and what is not, deterministic flake-free design, fixtures/mocks/factories, testing async and RLS-guarded data, and CI wiring. Use on 'write tests for this', 'add test coverage', 'set up Playwright', 'why is this test flaky', 'mock Supabase', 'test this server action', 'how do I test RLS'. Differs from bug-fix-workflow (fixes one known reported bug), performance (profiling/optimizing speed), and python-master (Python-library pytest only — this is the JS/TS and app layer)."
---

# Automated Testing

The craft of building a test suite a team **trusts** — one that fails only when the
product is broken, and whose green is worth believing. Grounded in the guild stack:
**Next.js + TypeScript + Supabase (Postgres + RLS)**, with **Vitest/Jest** for unit,
**Testing Library** for components, real-DB integration tests, and **Playwright** for E2E.

A test suite is not a pile of assertions; it is a **specification of behaviour you
refuse to regress**. Authoring tests well is a design act: you decide what the system
promises, then encode each promise once, at the cheapest layer that can prove it.

## What it is

- Choosing the **right layer** for each behaviour and writing the test there.
- Tests that are **deterministic** — same input, same verdict, every run, on every machine.
- **Coverage of behaviour and contracts**, not coverage of lines for its own sake.
- Real data shapes: async flows, Supabase queries, **RLS** boundaries, auth context.
- Wiring it all so CI is the gate and local runs are fast.

## What it is not

- Not **bug-fix-workflow** — that pulls one reported bug, reproduces, fixes, closes. This
  builds the *net* that catches the next one. (After a bug-fix, leave a regression test here.)
- Not **performance** — that profiles and optimizes. A test asserting "under 200ms" is a flake
  factory; assert behaviour, measure speed elsewhere.
- Not **python-master** — that is Python-library pytest. This is the **JS/TS + web-app** layer.
- Not a coverage-percentage trophy. 100% line coverage of trivial getters proves nothing.

## Principles

### 1. Put each behaviour at the cheapest layer that can prove it (the pyramid)

The pyramid is an economic claim: lower tests are faster, more numerous, and isolate
faults precisely; higher tests are slower, fewer, and prove the pieces actually connect.
Pick the **lowest** layer that can honestly verify a given behaviour.

- **Unit** (Vitest/Jest) — pure logic: a price calculator, a date formatter, a reducer, a
  Zod schema, a permission predicate. No DOM, no network, microseconds each. The bulk.
- **Component** (Testing Library) — a rendered React component's behaviour *as a user sees
  it*: it shows the error, the button disables while submitting, the list renders the rows.
- **Integration** — several real units across a boundary: a server action that writes to a
  seeded Supabase test DB, a route handler, a query layer. Proves the wiring, including RLS.
- **E2E** (Playwright) — a whole user journey through the real app: log in, create a record,
  see it in the list. Few, precious, slow. Reserve for critical paths and money flows.

> A bug found at the unit layer costs seconds to localize; the same bug found only by an
> E2E test costs a debugging session. Push tests **down** whenever truth allows.

**Anti-pattern — the ice-cream cone:** mostly E2E, few unit. Slow, flaky, and when one
breaks you cannot tell *which* unit lied. If you are reaching for E2E to test branching
logic, that logic wants a unit test.

### 2. Test the contract, not the implementation

Assert what the unit **promises to its caller** — inputs to outputs, rendered result,
the row that lands in the DB — never its private steps. Tests bound to internals shatter
on every refactor and stop teaching anything; they become a tax on change.

- Component: query by **role/label/text** a user perceives (`getByRole('button', {name})`),
  never by CSS class, test-id-as-crutch, or internal state. If the markup changes but the
  user experience is identical, the test must stay green.
- Avoid asserting that a mock was *called a certain way* unless the call **is** the contract
  (e.g. "we must send exactly one analytics event"). Prefer asserting the observable effect.
- A good test reads as documentation: a newcomer learns the feature's promises by reading it.

```ts
// Bad — couples to implementation detail
expect(component.state.isOpen).toBe(true)
// Good — asserts the user-visible contract
expect(screen.getByRole('dialog')).toBeVisible()
```

### 3. Determinism is non-negotiable — a flaky test is worse than no test

A test that fails 1-in-20 for no product reason trains the team to ignore red, and the
one real failure drowns. Hunt every source of nondeterminism out of the suite.

- **Time:** never let a test read the wall clock. Freeze it (`vi.useFakeTimers()`,
  `vi.setSystemTime(...)`) and advance deliberately. No `new Date()` leaking into assertions.
- **Randomness / ids:** seed or stub `Math.random`, `crypto.randomUUID`, faker seeds.
- **Order & shared state:** tests must pass in any order and in isolation. No test depends on
  data a previous test left behind; reset DB/mocks between tests.
- **Async:** await the *outcome*, never `sleep(500)`. In Testing Library use `findBy*` and
  `waitFor`; in Playwright rely on its **web-first auto-waiting** assertions
  (`await expect(locator).toBeVisible()`), never `page.waitForTimeout`.
- **Network:** no real third-party calls in unit/component/integration — they make the suite
  hostage to someone else's uptime. Intercept at the boundary (MSW, route mocks).

> When a test flakes, it has found a real race or a hidden shared-state coupling — in the
> test **or the product**. Fix the cause; never paper over it with a retry or a longer sleep.

### 4. Build data with factories; mock only at trust boundaries

Hand-built object literals rot: add a required field and fifty tests break. Generate test
data through **factories** that take overrides, so each test states only the field it cares
about and the rest are valid defaults.

```ts
const makeUser = (o = {}) => ({ id: crypto.randomUUID(), role: 'member', orgId: 'org_1', ...o })
// a test about admins says only what matters:
const admin = makeUser({ role: 'admin' })
```

**Mock at boundaries, not in the middle.** Mock the network, the clock, the third-party SDK
— the edges you do not own. Do **not** mock your own modules to dodge wiring them up; that
is the integration layer's whole job, and over-mocking yields a suite that is green while
the app is broken. Prefer a **seeded real Supabase test database** (a local CLI instance or a
disposable branch) over a hand-faked client, so RLS, constraints, and triggers are exercised
for real. Reach for a fake `supabase-js` only for a thin unit test where the DB is irrelevant.

### 5. Test the async and the security boundary on purpose — especially RLS

The defects that reach users in this stack cluster in two places: **async edges** and
**authorization**. Cover them deliberately, including the unhappy paths.

- **Async:** test the loading state, the resolved state, **and the rejected state**. A feature
  that has never been tested against a failing fetch will mishandle one in production. Assert
  the error UI renders and the optimistic update rolls back.
- **RLS / authZ is a behaviour, so it gets tests** — and the most important case is the
  **negative** one. Run the query *as the wrong user* and assert it returns zero rows or
  errors; run it as the right user and assert it succeeds. A passing positive test alone can
  hide a policy that lets everyone read everything.

```ts
// integration, against a seeded test DB with RLS on
test('member cannot read another org\'s rows', async () => {
  const asMember = clientFor(memberInOrgA)
  const { data } = await asMember.from('invoices').select().eq('org_id', 'org_B')
  expect(data).toEqual([]) // RLS denies — the load-bearing assertion
})
```

- Test auth context (signed-in vs anon), expired sessions, and role transitions where the
  product makes promises about them.

### 6. Coverage measures the gaps, it is not the goal

Coverage tells you which lines no test touched — useful as a **flashlight**, dangerous as a
**target** (Goodhart: a number you optimize stops measuring quality). Chase *behaviours*,
not percentages.

- Cover every **branch of meaningful logic** and every **public contract**; skip exhaustive
  tests of trivial passthroughs, generated code, and pure config.
- A diff that adds a code path should add the test that exercises it. New `if`, new test.
- Use coverage to find **untested branches in important code**, then decide case-by-case
  whether each deserves a test — do not blindly write tests to color a line green.
- The honest metric is "would this suite catch the next regression in this feature?" If a
  mutation to the logic leaves the suite green, the test is decorative.

### 7. CI is the gate; keep the inner loop fast

Tests earn trust only when they run automatically and block merges. Local runs earn use only
when they are fast enough to run constantly.

- Run unit + component + integration on every PR; they must be fast (seconds to low minutes).
- Run E2E on a built app, ideally against a seeded ephemeral DB (a Supabase branch), pinned to
  a known browser version; shard for speed. Quarantine — never ignore — a genuinely flaky E2E.
- Make the **same command** work locally and in CI; no "passes on my machine" config drift.
- Fail the build on test failure *and* on a coverage **regression** in critical paths — not on
  an arbitrary global floor.

### 8. Hand off verifiable evidence, and gate the push on it

A green run on your own machine is a claim, not proof. Non-trivial test work is not done when
it passes locally — it is done when the run leaves a **structured evidence block** on the PR or
tracker that a reviewer can trust without re-running anything, produced by the same command
that gates the push.

- After the suite runs, emit an evidence block (Markdown) into the PR/ticket: **Test Suite**,
  the **Files Changed** it speaks for, the **total / passed / failed / skipped** tally, a
  **coverage** block when collected, the **exact commands run**, and the trimmed **output**.
- The numbers are **generated, never hand-typed** — paste the real runner and coverage output;
  invented numbers launder a guess as a fact. **Failed must be 0** to hand off, and each skip
  needs a reason or a ticket.
- Treat the pre-push `ci:validate`-style command (typecheck + lint + unit + format) as **the
  gate**: it must pass before pushing, it is identical locally and in CI, and its run is what
  produces the evidence — the gate and the receipt are two faces of one verification.

```bash
pnpm ci:validate   # one command, same locally and in CI — its green run is the evidence
```

## References

- `references/test-pyramid-and-strategy.md` — choosing the layer, what to test vs skip, the
  coverage strategy, and how the four layers map onto a Next.js + Supabase app.
- `references/writing-deterministic-tests.md` — killing flake: time, randomness, async,
  ordering, shared state, network; factories, fixtures, and where to mock.
- `references/e2e-playwright.md` — Playwright craft: auto-waiting locators, auth setup/storage
  state, test isolation against a seeded DB, network mocking, sharding, CI wiring.
- `references/evidence-packaging-and-handoff.md` — turning a green run into a deliverable: the
  structured pass/coverage evidence block for the PR/tracker, field discipline (zero failures,
  reasoned skips, reported-not-chased coverage), and the pre-push `ci:validate` gate that
  produces it.

## Changelog

- **1.1.0** — Added the evidence-packaging-and-handoff reference and Principle 8: after a suite
  runs, emit a structured pass/coverage evidence block (Test Suite, total/passed/failed/skipped,
  coverage, commands-run, output) for the PR/tracker, and treat the pre-push `ci:validate`-style
  command as the gate that produces it.
- **1.0.0** — Initial: four-layer authoring, the pyramid, contract-not-implementation,
  determinism, factories/mocks, RLS and async boundaries, coverage strategy, CI wiring.
