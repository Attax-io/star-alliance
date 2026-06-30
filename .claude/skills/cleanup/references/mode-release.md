---
type: Document
timestamp: 2026-06-27T10:27:03Z
---

# Mode: release — full recipe

The unified app-upgrade flow (merged the retired `update-app-version` skill in cleanup v1.6.0).
Two phases: **Phase 1 — hygiene gate** (PR1–PR4 below) runs the cheap LIVE-mode checks + release
hazard probes and returns a green/red verdict; **Phase 2 — version bump** runs only if the gate
is green and performs the full bump per `references/release-procedure.md`. Invoke gate-only with
`/cleanup release --gate` (stops after PR4); the bare `release` invocation runs both phases.

**Why this exists.** Release-time breakage is a recurring class (Cloudflare bundle wall, Next.js
16 hazards, uncommitted migrations, stale doc stamps). The sessions show ~6 distinct release
failures that a pre-push gate would have caught.

#### Step PR1 — Run the hygiene gate

In order, collect each mode's verdict (do not auto-fix — this is a gate, not a sweep):

1. `lint` mode detect+classify — **red if** any architectural violation on touched files
2. `errors` mode detect+classify — **red if** any unfixed code-bug in the dev log
3. `postgres` mode detect+classify — **red if** any NEW schema-campaign item vs last release

#### Step PR2 — Release-specific hazard checks

| Hazard | Probe | Verified-recurring |
|---|---|---|
| **Cloudflare/OpenNext bundle wall** | the **`bundle` mode** — `bundle detect` (static, free) for unisolated heavy libs, then **build + `bundle measure`** to gzip `.open-next/worker.js` vs the wall (3 MiB free / 10 MiB paid). **Red** if `detect` finds a violation OR `measure` is over. (`measure` is the hard gate; `detect` is early-warning — a lib off the seed list can still bust it.) | SSR worker 15.4 MiB raw / 3.2 MiB gzip + the **1.7.60** deploy (recharts SSR'd via `CreditStatsBar`) — both this class. `serverExternalPackages` NOT honored by OpenNext. |
| **`generateMetadata` in `'use client'` page** | `grep -rln "'use client'" + "generateMetadata"` same file | Hard Next.js 16 build error; keep `page.tsx` a Server Component. |
| **Uncommitted migration / route changes** | `git status` — uncommitted `[locale]` or `i18n/` or migration dirs | Whole `[locale]` migration was uncommitted → prod-only 404. |
| **Import-depth off-by-one after route move** | `tsc` TS2307 count | `[locale]` segment moved every admin file one dir level → 718 TS2307. |
| **Migration filename format** | migration names must be 14-digit `YYYYMMDDHHMMSS` | 14-digit mismatch → Supabase branch stuck MIGRATIONS_FAILED. |
| **Next.js 16 `middleware`→`proxy` deprecation** | dev-server output grep | Forward-looking; not yet blocking. |

#### Step PR3 — Doc-stamp staleness warning

`VERSION-RELEASE-WORKFLOW.md` §4 was **reconciled 2026-05-29** — its target list now matches the
live tree (and `references/release-procedure.md` carries the same list). Current version-stamp
surfaces (still worth a verify grep before trusting any list):

```bash
cd lex_council
# Find what actually carries an app-version stamp NOW
grep -rln "App version:\|app_version:\|APP_CONFIG\|Version {version}" docs/ apps/web/config/ \
  --include="*.md" --include="*.ts" --include="*.json" 2>/dev/null
```

Also: app version lives in TWO places that drift — `apps/web/config/app.config.ts`
(`APP_CONFIG.version`, the canonical) AND the web `package.json` `version` field. The prod live
stamp is the reliable deploy-lag signal.

**Side-finding to action:** reconcile `VERSION-RELEASE-WORKFLOW.md`'s target list with the current
solar-system hubs (Vault Core + the changelog INDEX files). Until then, the workflow's hard-coded
list silently skips the real stamps.

#### Step PR4 — Gate verdict

Emit a green/red gate result. **Green →** proceed to Phase 2 (the bump) unless the user passed
`--gate`. **Red →** surface the blocking items and STOP; do not bump.

No vault log for a gate-only run (no code changed). If the gate auto-fixed anything (it
shouldn't — it's a gate), delegate to vault-log-compliance.

#### Phase 2 — Version bump (only if gate green and `--gate` not passed)

Run the full bump procedure in **`references/release-procedure.md`** (R-1 … R-6): confirm scope +
classify the bump, compose the changelog, bump `apps/web/config/app.config.ts` (the canonical
literal) + decide the `package.json` mirror, write `docs/logs/X.Y.Z.md`, sync the doc stamps
(`logs/INDEX.md` + `ARCHITECTURE.md` + Vault Core ×3 — NOT the archived ZUSTAND-STORES), verify
with a version grep, and output the single git block (do NOT push unless told). This phase
absorbed the retired standalone `update-app-version` skill.
