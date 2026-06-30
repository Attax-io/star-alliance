---
type: Document
title: E2E with Playwright
description: Playwright craft for a Next.js + Supabase app — auto-waiting locators, auth setup with storage state, isolation against a seeded DB, network mocking, sharding, and CI wiring.
timestamp: 2026-06-28T00:00:00Z
---

# E2E with Playwright

End-to-end tests are the apex of the pyramid: slow, few, and the most expensive to maintain —
so each one must earn its place by covering a **critical user journey** that no cheaper layer
can prove (login, the primary create/edit flow, money and irreversible flows). The discipline
is the same as everywhere else: assert the user-visible contract, and make every test
deterministic. Playwright gives you the tools; the craft is using them so the suite is fast
and never flakes.

## Locators and web-first assertions — let Playwright wait

Playwright's locators are **auto-waiting**: an assertion retries until the condition holds or a
timeout expires. This is the single biggest flake-killer in E2E — never reintroduce flake with
a manual sleep.

```ts
// Good — auto-waits for the element to be visible
await expect(page.getByRole('button', { name: 'Save' })).toBeVisible()
await page.getByLabel('Email').fill('a@b.com')
// Never:
await page.waitForTimeout(2000) // a bet on machine speed; CI loses it
```

Query the way a user perceives the page: `getByRole`, `getByLabel`, `getByText`. Reserve
`getByTestId` for elements with no accessible handle. Avoid brittle CSS/XPath selectors that
break on every restyle.

## Auth without logging in every test

Driving the full login form in every test is slow and flaky. Authenticate **once** in a setup
project and reuse the **storage state** (cookies + localStorage, including the Supabase session)
across tests.

```ts
// auth.setup.ts — runs once
await page.goto('/login')
await page.getByLabel('Email').fill(process.env.E2E_EMAIL!)
await page.getByLabel('Password').fill(process.env.E2E_PASSWORD!)
await page.getByRole('button', { name: 'Sign in' }).click()
await expect(page).toHaveURL('/dashboard')
await page.context().storageState({ path: 'playwright/.auth/user.json' })
```

Then a project depends on setup and loads that state via `storageState` in its `use` config.
Keep **separate states per role** (admin, member, anon) so RLS-sensitive journeys run as the
right identity — and write at least one journey that confirms a member **cannot** reach an
admin-only page.

## Isolation against a real database

E2E hits a real backend, so test data is the main isolation hazard. Options, best first:

- **Ephemeral seeded DB per run** — spin a disposable Supabase branch or a local stack, run
  migrations, seed a known fixture, point the app at it, tear it down after. The suite starts
  from a known state every time.
- **Per-test namespacing** — if tests share a DB, give each test its own org/tenant id (or a
  unique prefix) so they cannot collide, and clean up what they create in an `afterEach`/global
  teardown.

Never let E2E tests depend on data a previous test left behind, and never run them against a DB
whose state you do not control — that is the top cause of "passed yesterday, red today".

## Network mocking and fault injection

For third-party calls the app makes (payments, external APIs), intercept with `page.route` so
the journey is deterministic and you can force the failure path:

```ts
await page.route('**/api/payment', r => r.fulfill({ status: 500 }))
// then assert the app shows the retry/error UI
```

Do **not** mock your own backend in E2E — the point of E2E is to exercise the real wiring. Mock
only the genuinely external, slow, or money-moving edges.

## Speed: parallelism and sharding

- Playwright runs files in parallel by default; keep tests independent so this is safe.
- In CI, **shard** across machines (`--shard=1/4` … `4/4`) and merge the blob reports.
- Pin the **browser version** (Playwright bundles its own) so a browser update cannot silently
  change behaviour between local and CI.
- Capture **trace, video, and screenshot on failure** (`trace: 'on-first-retry'`) so a CI
  failure is debuggable without a local repro.

## CI wiring

- Build the app first, start it (or use the Playwright `webServer` config to boot Next.js), then
  run E2E against the built server — not the dev server, which has different behaviour.
- Run E2E as a **gate** on the main flows but allow it to be a separate, slower job than the
  unit/component/integration job so the fast feedback stays fast.
- **Quarantine, never ignore** a genuinely flaky E2E: move it to a non-blocking lane *with a
  ticket to fix it*, so the gate stays trustworthy while the flake gets a real fix. A permanently
  skipped E2E is a lie about coverage.
- Use Playwright's retry **only** to ride out true infrastructure blips, never to mask a race in
  the product — if a test only passes on retry, that is a bug to investigate, not absorb.
