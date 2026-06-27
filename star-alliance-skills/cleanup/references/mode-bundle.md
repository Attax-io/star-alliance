---
type: Document
timestamp: 2026-06-27T10:27:03Z
---

# Mode: bundle — full recipe

Cloudflare/OpenNext **Worker size-wall** hygiene. The app deploys via
`@opennextjs/cloudflare`, which bundles ALL server/SSR code into one Worker
script that Cloudflare validates against a hard size limit — **3 MiB gzipped on
the free plan, 10 MiB on paid**. Crossing it fails the deploy at the very last
step (the build still "succeeds"). It failed the **1.7.60** deploy (the members
Points panel `CreditStatsBar` imported `recharts` directly, so it was
server-rendered into the worker) and had bitten once before (SSR worker 15.4 MiB
raw / 3.2 MiB gzip). Fixed in 1.7.61 by the `.body` + `dynamic({ssr:false})`
split — this mode catches the class so it never silently re-crosses.

> **Script:** `python3 ~/.claude/skills/cleanup/scripts/bundle_cleanup.py <detect|measure>`
> — `detect` is static + build-free; `measure` gzips the built worker. `detect`
> exits 2 on findings (gate-friendly); `measure` exits 2 over-limit, 3 when not
> measurable (degrade-with-receipts), 0 clean.

**Two layers, split by cost + authority.** The static `detect` scan is the cheap
early warning — but it only knows the libs on `HEAVY_SSR_LIBS` (seeded with
`recharts`). The gzip `measure` is the **ground truth**: a heavy lib not on the
seed list can still push the worker over. So routine `/cleanup bundle` runs
`detect`; the **`release` gate's hard size check is `measure`** (after a build).
Don't build a mode that re-encodes the 1.7.60 blind spot — a gate that never
measures is how that deploy shipped broken.

#### Step B1 — Detect (static, always available)

```bash
python3 ~/.claude/skills/cleanup/scripts/bundle_cleanup.py detect
```

Scans `apps/web` and writes `/tmp/bundle_violations.json`. Three violation kinds:

- **direct-heavy-import** — a non-`.body` file imports a heavy lib directly, so
  Next.js server-renders it into the Worker. (Exactly what `CreditStatsBar.tsx`
  did pre-1.7.61.)
- **broken-isolation** — a `*.body` file imports a heavy lib but its sibling
  wrapper is missing or lacks `ssr: false`.
- **body-imported-outside-wrapper** — a `*.body` module is imported by something
  other than its own `dynamic({ssr:false})` wrapper, re-introducing it to SSR
  even though the naming looks correct (the proxy-rule hole).

The convention every heavy lib must obey (mirror the admin analytics charts —
`FileHealth`, `TaskCompletionTrend`, `TasksSummaryCard`, Attendance / Activity
dashboards): the impl lives in `X.body.tsx`; `X.tsx` is a thin
`dynamic(() => import('./X.body'), { ssr: false, loading: … })` wrapper so the
lib loads client-only and never enters the worker bundle.

> Detector precision: it matches the **import** (`from 'recharts'` /
> `import('recharts')`), never a substring — a comment that merely mentions
> `recharts` (the Skeleton, the activity page) is NOT a hit (the over-match trap
> §L4 / consolidate logs). `HEAVY_SSR_LIBS` is a **seed, not a guarantee** —
> extend it when a new heavy client-only lib surfaces; `measure` covers the rest.

#### Step B2 — Fix each violation (the `.body` + ssr:false split)

The script emits the recipe; **Claude / an agent applies it** (the transform has
props + loading-height nuance, so it is not auto-codegen'd). Per
`direct-heavy-import`:

1. `git mv X.tsx X.body.tsx` (impl unchanged — keep `'use client'` + the lib import).
2. New `X.tsx` wrapper: `'use client'` +
   `const X = dynamic(() => import('./X.body'), { ssr: false, loading: () => <div style={{ minHeight: N }} /> })`
   + `export default X`. Use `dynamic<Props>(…)` and import the body's `Props`
   type if the component takes props.
3. Pick `N` to reserve the body's rendered height (no layout shift).
4. Callsites are unchanged — they still import the wrapper's default export.

For `broken-isolation` / `body-imported-outside-wrapper`, follow the JSON
`recipe` field (add the missing `ssr: false`, or repoint the importer through
the wrapper). Then `npx turbo run check-types lint --filter=web` → must stay green.

#### Step B3 — Measure (build-gated ground truth — the release hard gate)

```bash
cd lex_council/apps/web && npx opennextjs-cloudflare build      # produces .open-next/worker.js
cd ../.. && python3 ~/.claude/skills/cleanup/scripts/bundle_cleanup.py measure   # --paid for the 10 MiB limit
```

gzips `.open-next/worker.js` (wrangler `main`) and compares to the wall. If the
artifact is **absent or an implausibly small placeholder** (a stale/empty
`worker.js`), it **degrades-with-receipts** (exit 3 — "not measured, run the
build"), never a silent "OK" (§L28). The authoritative number is wrangler's
deploy `Total Upload … gzip:` line; `measure` gzips the same `main` artifact as
a faithful on-disk proxy.

> **Don't burn a full OpenNext build just to test the skill.** In a routine
> sweep run `detect` (free) and let `measure` degrade. Only build when actually
> gating a release or chasing a confirmed over-limit deploy.

#### Step B4 — Verdict + closeout

- Routine `/cleanup bundle`: surface `detect` violations + recipes; if you
  applied fixes, run the Step CL patch bump + a vault log (`bundle` is a code
  mode — fixes ship in the app).
- In the `release` gate (PR2): build + `measure`; **red** if over the wall.
- Detect-only, zero fixes applied: no bump, no vault log (§L29).
