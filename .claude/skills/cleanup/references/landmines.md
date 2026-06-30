---
type: Document
timestamp: 2026-06-27T10:27:03Z
---

# Lessons learned (cross-mode landmines)

> **Wired into scripts (v1.8.0):** L9/L10/L15/L17 → `postgres_cleanup.py` detect (emits + classifies the security_invoker / stale-prosrc / permissive-RLS / dead-service_role / rls-no-policy queries); L11 + L19 → `lint_cleanup.py` (baseline-delta + view-registry cross-check); L14 → `errors_cleanup.py` noise list; L16 → `i18n_cleanup.py` detect (window.confirm scan). The rest remain cross-mode prose guidance. **L25–L31 (added 2026-06-02 from mining the 2026-05-30→06-02 cleanup runs — 4 followup sweeps + 2 run-all passes) are prose-only, EXCEPT L27 → now mechanized by `scripts/commit_scope.py` (R10, v1.10.0). L25/L26/L28–L31 remain prose pending wiring.**

Patterns extracted from the 2026-05-28 solar-system doc-sync audit +
follow-up sweep. These apply across **every** cleanup mode, not just one.

### L1 — MCP-out-of-reach taxonomy

When a cleanup mode generates an action list, classify each item by
reachability **before** trying to execute:

| Class | Signal | Action |
|---|---|---|
| **doable from MCP** | Has a matching MCP tool (`apply_migration`, `execute_sql`, `deploy_edge_function`, etc.) AND falls within the autonomous-cadence remit | Do now |
| **doable from Bash/local-fs** | Local file edit, git operation, npm script — within the workspace tree | Do now |
| **needs-user-hands** | Supabase dashboard click (no `delete_edge_function` MCP), external service (cron on office NAS, third-party API), `[!atta]` block edit, signed-out user account, OS-level config | Surface as checklist |
| **accepted-permanent-exception** | Item the user has explicitly marked "leave as-is" in a prior turn; cite the prior decision verbatim | Note in findings; don't re-surface |

The 2026-05-28 solar-system audit had 8 follow-ups split 5/2/1 across
these classes. Codifying the taxonomy prevents the skill from silently
dropping needs-hands items (they become checklist-with-receipts) and
prevents accepted exceptions from re-appearing on every future cleanup.

### L2 — Behavior-parity verification post-refactor

When cleanup mode merges, consolidates, or replaces a structure (RLS
policies, hard-coded arrays, repeated CSS literals, i18n key
deduplication), the verify gate is **not** "does it compile / does
type-check pass" — it's **"does the post-state admit/produce the
exact same outputs as the pre-state for every input?"**

The FU-5 storage RLS refactor produced a 17-admit parity matrix
across 12 buckets × 5 ops:

```sql
with buckets(b) as (values (...)), ops(op) as (values (...))
select b, op, helper(b, op) as admitted from buckets, ops
where helper(b, op)  -- only show admits
order by b, op;
```

The matrix returned 17 admits — exactly matching the pre-refactor admit
set. **If parity check returns a delta, the refactor is wrong even if
type-check passes.** The look-alike-but-different trap (L4 below) is
the primary reason this check is non-negotiable for any consolidation.

### L3 — Post-rename narrative-artifact sweep

When a large rename campaign ships (v2 schema, primitive family
rename, naming overhaul), narrative documentation often retains
pre-rename names in prose **and** acquires telltale artifacts from
botched global-replaces. Two pattern classes worth a periodic grep:

**Pattern A — retained pre-rename names** (treat as documentation
drift; surface for triage, never auto-fix):

```bash
grep -rnE '\b(fd|council_members|ppl|whbd_|atnd_|n_kinds|KpiStrip|PageHeaderStrip|AdminPageShell)\b' \
  lex_council/docs/ --include="*.md"
```

**Pattern B — global-replace artifacts** (almost always a bug; the
2026-05-28 BACKEND.md audit found 3 of these):

```bash
# "X (v2; was X)" — same name on both sides of a "was" parenthetical
grep -rnoE '`([a-z_]+)` \(v2; was `\1`\)' lex_council/docs/ --include="*.md"
grep -rnoE '`([a-z_]+)` \(was `\1`\)' lex_council/docs/ --include="*.md"
```

The `docs` mode codifies this as Step D7.

### L4 — Look-alike-but-different trap

The FU-5 RLS refactor revealed that 4 storage policies LOOKED like
they hard-coded the same bucket array but actually encoded distinct
per-CMD access tiers (`200` was SELECT-only; `attendance` + `elections`
were SELECT+INSERT only; `documents`/`1`/`2` were full-CRUD). A naive
"replace all 4 with a single `is_private_bucket()` helper" would have
silently widened access on 3 buckets.

**Rule for any consolidation cleanup:** before merging N near-duplicate
literals into one helper, compare them byte-for-byte. If any pair
differs, preserve the difference in the helper's API (e.g. per-CMD CASE
arms; per-locale dispatch; etc.). Only consolidate when all N are
byte-identical.

The `language` mode's safe-to-merge detector already encodes this for
i18n (only merge when translation matches in every locale). The
`consolidate` mode (when wired up) MUST encode it for code as well.

### L5 — PostToolUse hook race conditions with Edit

The Edit tool's "file has been modified since read" guard fires when a
PostToolUse hook (linter, formatter, IDE) touches the target between
Read and Edit. The 2026-05-28 audit hit this 5+ times on INTEGRATION.md
+ vault-logs INDEX.md edits.

**Rule for any mode performing batch edits to many files:** use
`Bash` + Python (or sed) for the substitution sweep, NOT chained
`Edit` calls. The `language` mode already does this via
`scripts/i18n_cleanup.py:apply`. The `docs` mode's Step D2 frontmatter
sync should follow suit when it goes live.

For single-target edits (e.g. one-line frontmatter bump), `Edit` is
fine — race conditions are rare enough that the failure-then-retry
pattern is cheap.

### L6 — Same-session continuation markers

Atta uses brief continuation markers between turns to indicate
"keep going" without re-issuing the original directive:

- `/goal` — generic "continue toward the goal we agreed on"
- "finish the rest" / "finish [X]" — execute remaining items
- "i am done" / "i am done..." — user-side action complete; resume
  on the agent side
- "leave [X] as exception" — accept-and-skip, mark as L1 permanent-exception

When a cleanup mode is interrupted by a needs-user-hands item, the
**next-turn pickup** should preserve all in-progress state (which items
were classified as doable / needs-hands / exception). Don't re-classify
from scratch on continuation — the prior turn's findings file is the
input.

### L7 — Vault-log size threshold

For ≤3 follow-up items touching the same surface, write a single inline
vault-log entry (the `2026-05-28_solar-system-doc-sync-followups.md`
shape). For ≥4 items OR multi-surface changes, delegate to
**vault-log-compliance** for a fuller entry with P13 self-audit table.

The `language` mode always delegates because translation passes are
multi-locale by definition (5 surfaces). The `docs` + `followups`
modes pick per-pass based on scope.

### L8 — Long-running global replaces leave artifacts; periodic grep

L3 above is a specific instance of a broader pattern: any mass-edit
campaign (rename sweep, token consolidation, primitive retirement)
leaves stray artifacts that don't surface for weeks because they're
syntactically valid. The `docs` mode's Step D7 + Step D6 grep these
proactively; without periodic cleanup, the artifacts accumulate and
the next person reading the doc gets a false mental model.

When a future BUILD ships a rename, the FOLLOWING `/cleanup docs` run
should be scheduled within a week.

### L9 — `CREATE OR REPLACE VIEW` silently drops `security_invoker = true` (postgres mode)

Confirmed across 5+ independent sessions: every `CREATE OR REPLACE VIEW` statement silently
drops the `reloptions` including `security_invoker = true`, reverting the view to definer
mode. This is a silent regression — tsc and lint pass cleanly, RLS still "works" (definer
mode bypasses RLS, so the query returns data), but the security contract is broken.

**Mandatory postgres mode check:**

```sql
-- After any migration that touched views, verify ALL public views still have security_invoker
SELECT c.relname, c.reloptions
FROM pg_class c
JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE n.nspname = 'public' AND c.relkind = 'v'
AND (c.reloptions IS NULL OR NOT 'security_invoker=true' = ANY(c.reloptions));
-- Expect 0 rows. Any row = silent regression.
```

If any view is missing `security_invoker = true`, the fix is:

```sql
ALTER VIEW public.<view_name> SET (security_invoker = true);
```

The postgres mode's PG4 verify step must run this check. The docs mode's retired-name sweep
should also check for `SECURITY DEFINER` views added unintentionally.

### L10 — `get_advisors` misses overly-permissive RLS; supplement with direct query (postgres mode)

The Supabase `get_advisors` MCP tool does not catch RLS policies with `qual = 'true'`
(i.e. policies that grant access to ALL rows unconditionally). These are syntactically valid
and pass all type checks, but effectively disable row-level isolation for the table.

**Supplement to PG1 detect:**

```sql
-- Find unconditionally-permissive RLS policies
SELECT schemaname, tablename, policyname, cmd, qual, with_check
FROM pg_policies
WHERE schemaname = 'public'
AND (qual = 'true' OR qual IS NULL)
ORDER BY tablename, policyname;
```

Any result where `qual = 'true'` (not `(select auth.uid()) IS NOT NULL` or similar) is a
candidate for a `schema-campaign` item — not safe to auto-fix without understanding intent.

Also supplement with the stale-function-body scan (catches v2 rename drift):

```sql
-- Detect function bodies still referencing renamed columns/tables
SELECT p.proname, LEFT(p.prosrc, 200) AS body_preview
FROM pg_proc p
WHERE p.prosrc ILIKE '%user_preferences%nickname%'   -- old column path
   OR p.prosrc ILIKE '%folder_classes%'              -- old lookup table ref
   OR p.prosrc ILIKE '%council_members%';            -- pre-v2 table name
-- Expect 0 rows post-v2 rename
```

### L11 — Pre-existing lint warnings create baseline noise; always track delta (lint mode)

At `--max-warnings 0`, a full project-wide lint run surfaces pre-existing warnings in files
the current campaign never touched. Running the lint mode and reporting "N warnings" creates
false alarm fatigue and wastes triage time.

**Canonical pattern (from conquering-campaign scoped-lint):**

```bash
# Baseline at session start
cd lex_council && npx eslint --format json --ext .ts,.tsx apps/web packages \
  > /tmp/lint_baseline.json

# After changes, compute delta (new files only)
git status --short | awk '$1 ~ /^M/ || $1 == "M" {print $2}' > /tmp/touched.txt
npx eslint --max-warnings 0 $(cat /tmp/touched.txt | grep "^apps/web/" | sed 's|^apps/web/||')
```

The lint mode's report MUST say "N new warnings on campaign-touched files (M pre-existing
suppressed)" — not a raw count. The suppressed count IS the signal: a high suppressed count
means a lint-debt campaign is overdue.

Also: filter tsc output to exclude `.next/` paths. The `.next/` directory contains stale
`*.d 2.ts` duplicate files that produce spurious type errors unrelated to source changes.

### L12 — `no-unused-expressions` is always architectural — never auto-fix (lint mode)

The `no-unused-expressions` rule fires most often on the ternary-as-statement pattern:
`cond ? a.foo() : a.bar()`. This fails the rule because the ternary's result value is unused.
ESLint `--fix` CANNOT resolve this automatically — the correct fix is `if/else`, which changes
code structure. The pattern is common in portal pages and event handlers.

**Detection:** `grep -rn '?\s*[a-z].*\..*()' apps/web/ --include="*.tsx" | grep -v '//'`

**Fix pattern:** Always `if (cond) { a.foo() } else { a.bar() }`. Never use `void cond ?...`
or `eslint-disable-line` — the rule exists to prevent subtle bugs in React event handlers.

Similarly, `react-hooks/rules-of-hooks` is always architectural. A hook called inside a
conditional is a structural problem that requires component decomposition, not suppression.

### L13 — Scope ESLint to campaign-touched files first; grep for hex literals separately (lint mode)

Two items ESLint misses entirely that the lint mode should check as supplementary scans:

**1. Off-token hex color literals** — ESLint does not scan CSSProperties objects for `#hex`
strings. A grep sweep is more reliable:

```bash
grep -rn '#[0-9a-fA-F]\{3,6\}\b' \
  lex_council/apps/web/components \
  lex_council/apps/web/app \
  --include="*.tsx" --include="*.ts" | grep -v "//.*#" | grep "color\|background\|border"
```

Count > 10 = flag for a token-sweep campaign. Count > 50 = existing tech-debt worth a
dedicated pass.

**2. Module-level `const` style-object orphans** — `no-unused-vars` does not catch exported
objects that are declared but never imported. These accumulate after refactors. Use:

```bash
# Find style-constant files with zero downstream imports
grep -rn "^export const.*Style\|^export const.*Styles\|^export const.*STYLE" \
  lex_council/apps/web/ --include="*.ts" --include="*.tsx" | \
  while read file; do
    fname=$(echo "$file" | cut -d: -f1)
    grep -rl "$fname" lex_council/apps/web/ 2>/dev/null | grep -v "$fname" | wc -l
  done
```

### L14 — ThemeToggle + StrictMode errors are known noise in `errors` mode

Two error signatures that appear in virtually every dev session and should be suppressed
by the `errors` mode classifier without requiring triage:

1. **ThemeToggle hydration errors** — `Warning: Extra attributes from the server: class` on
   the `<html>` element. Caused by the server rendering without a theme attribute and the
   client immediately setting `data-theme`. These are not bugs — the sync bootstrap script
   in `app/layout.tsx` eliminates FOUC. Classifier: `framework-noise` + suppress.

2. **React StrictMode double-invocation errors** — components appear to error twice because
   StrictMode intentionally calls lifecycle functions twice in development. If the same error
   signature appears exactly twice consecutively with no intervening route, it's StrictMode.
   Classifier: `framework-noise` + suppress.

Add both to `errors_cleanup.py`'s noise-pattern list.

### L15 — Stale trigger bodies after v2 rename are invisible to advisor + lint (postgres mode)

The 2026-05-24 v2 campaign renamed 54 tables. Many trigger functions reference old table/column
names that no longer exist. These **pass all advisor checks** (Supabase advisor only checks
structure, not function bodies), **pass tsc** (pg functions are opaque to TypeScript), and
**pass lint** (ESLint doesn't read SQL). The functions compile and run — they just operate on
the wrong data silently.

The only way to detect this class is a `pg_proc.prosrc` full-text scan:

```sql
-- Stale trigger function body references (v2 rename targets)
SELECT p.proname AS fn_name,
       n.nspname AS schema,
       LEFT(p.prosrc, 300) AS body_preview
FROM pg_proc p
JOIN pg_namespace n ON n.oid = p.pronamespace
WHERE n.nspname IN ('public', 'private')
AND (
    p.prosrc ILIKE '%council_members%'
    OR p.prosrc ILIKE '%ppl%'
    OR p.prosrc ILIKE '%fd_access%'
    OR p.prosrc ILIKE '%cm_hr%'
    OR p.prosrc ILIKE '%admin_perms%'
    OR p.prosrc ILIKE '%whbd_%'
    OR p.prosrc ILIKE '%atnd_%'
    OR p.prosrc ILIKE '%n_kinds%'
)
ORDER BY p.proname;
-- Expect 0 rows. Each row = stale trigger body needing a campaign fix.
```

Add this as an additional detect step in the postgres mode's PG1 phase. Results classified as
`schema-campaign` (they require careful, campaign-scoped SQL surgery — not auto-fixable).

### L16 — i18n namespace scope trap: `useTranslations` scope must match the JSON file tree (language mode)

A component that calls `useTranslations('customer_wizard')` while living under a page that
loads `admin.json` will silently fall through to `getMessageFallback` and render raw key paths
in production. The correct call is `useTranslations('admin.customer_wizard')`.

This is undetectable by the `language` mode's key-scan (the key exists in the JSON; the issue
is the namespace prefix at the call site). Symptom: the Languages panel shows 0 untranslated
keys but users see literal `admin.customer_wizard.step_1_title` strings in the UI.

Detection grep (pair with the language mode's detect step):

```bash
grep -rn "useTranslations(['\"]" lex_council/apps/web/ --include="*.tsx" |
  grep -v "^.*useTranslations('admin\." |
  grep -E "(admin|portal|members|clients)" | head -20
# Results may indicate a missing namespace prefix
```

Also: **`window.confirm()` calls are untranslatable** and should be flagged as technical debt
during any language pass. The language mode's detect step should grep for `window.confirm(`
and surface a count. These must be migrated to a custom modal component before the string
can be covered by the i18n system.

### L17 — Postgres advisor requires multi-pass until clean; common recurring types (postgres mode)

The Supabase `get_advisors` result does not stabilise after fixing one batch of issues —
fixing the top-N advisories often reveals a new Nth+1 advisory that was hidden behind them.
**Loop until `get_advisors` returns an empty list** (or only known-intentional exceptions).

The two most common advisor types in this project:

| Advisor | Signal | Action |
|---|---|---|
| `rls_enabled_no_policy` | Table has `ALTER TABLE ... ENABLE ROW LEVEL SECURITY` but zero policies — usually a stale backup/archive table | Classify `schema-campaign`; user decides to DROP or add a blanket policy |
| `authenticated_security_definer_function_executable` | A `SECURITY DEFINER` function is still EXECUTE-able by `authenticated` after `REVOKE ... FROM PUBLIC` — `authenticated` inherits via PUBLIC | Add explicit `REVOKE EXECUTE ON FUNCTION ... FROM authenticated;` if not intentional; document as exception if intentional |

Dead `auth.role() = 'service_role'` in RLS policies (308 across 77 tables historically)
generate a "multiple permissive policies" advisor. These are always dead code — `service_role`
bypasses RLS entirely and the policy is never evaluated. Flag as `schema-campaign` for batch
DROP in a dedicated cleanup migration.

### L18 — `react-hooks/exhaustive-deps` suppressions on mutation callbacks are intentional (lint mode)

In this codebase, mutation callbacks are intentionally passed as stable refs and deliberately
excluded from `useEffect` dependency arrays. These lines have explicit
`// eslint-disable-next-line react-hooks/exhaustive-deps` comments.

**The lint mode must NOT remove these suppressions.** They are not technical debt — they are
correct design decisions. Classify any file with this pattern as `reviewed-intentional` and
skip it in the auto-fix pass.

Similarly, `no-undef` errors for `Buffer`, `process`, `module`, or `require` in `scripts/`
files are not real errors — the ESLint config uses browser environment, but `scripts/` files
run in Node.js. Fix is `/* eslint-env node */` at the top of the file, NOT per-line `eslint-disable`.

### L19 — TS2304 `Cannot find name 'VIEWS'` always means a missing view-registry key (lint mode)

The most common tsc error in this codebase. Whenever a new view is created and added to a
page query, it must also be added to `apps/web/lib/view-registry.ts` as a key in the `VIEWS`
constant. If this step is missed, every file that calls `VIEWS.<new_key>` fails tsc with
`TS2304 Cannot find name 'VIEWS'` or `TS2339 Property '<key>' does not exist on type...`.

The lint mode's detect step should explicitly grep for this pattern:

```bash
grep -rn "VIEWS\." lex_council/apps/web/ --include="*.tsx" --include="*.ts" |
  grep -v "view-registry" | grep -oE "VIEWS\.[a-zA-Z_]+" | sort -u > /tmp/view_usages.txt

grep -n "^\s*[a-zA-Z_]" lex_council/apps/web/lib/view-registry.ts > /tmp/view_registry.txt

# Find usages not in registry
comm -23 <(sort /tmp/view_usages.txt | sed 's/VIEWS\.//') \
         <(grep -oE "^\s*[a-zA-Z_]+" /tmp/view_registry.txt | sort)
```

Any row in the comm output = missing view-registry entry = tsc error on that page.

### L20 — `VERSION-RELEASE-WORKFLOW.md` doc-stamp drift (RESOLVED 2026-05-29; release mode)

> **RESOLVED 2026-05-29.** VERSION-RELEASE-WORKFLOW.md §4 was reconciled to the live tree (ZUSTAND-STORES removed — archived; Vault Core ×3 stamps; package.json documented as a real drift-prone mirror) and the bump procedure now lives in `references/release-procedure.md`, run by the `release` mode. The historical drift below is the record of what was wrong.

The canonical release procedure doc points its doc-header-sync step at paths that predate the
solar-system docs restructure: `docs/logs/INDEX.md`, `docs/architecture/ARCHITECTURE.md`,
`docs/architecture/frontend/ZUSTAND-STORES.md`. Current structure is `docs/vault-logs/` +
the planet hubs (Vault Core, BACKEND, FRONTEND, INTEGRATION). The workflow examples still say
`1.6.X`; the app is at **1.7.25**.

Consequence: following the workflow's hard-coded target list silently SKIPS the real version
stamps. The `release` mode's PR3 step greps for what actually carries a stamp NOW instead
of trusting the list.

Also: **app version lives in TWO places that drift** — `apps/web/config/app.config.ts`
(`APP_CONFIG.version`, canonical) AND the web `package.json` `version` field. And there are
**two hand-maintained changelog indexes** (`docs/vault-logs/INDEX.md` +
`docs/logs/INDEX.md`) synced by hand on every release. The prod live version stamp (surfaced
in the running site) is the reliable signal for whether a commit actually deployed.

**Action item beyond the skill:** reconcile `VERSION-RELEASE-WORKFLOW.md` with the current
docs structure. Until then, treat its target list as advisory, not authoritative.

### L21 — Release-time breakage is a recurring class; gate before bump (release mode)

Across the mined sessions, ~6 distinct release failures recur — each catchable by a pre-push
gate (the `release` mode). The cluster:

| Failure | Root | Catch |
|---|---|---|
| Cloudflare/OpenNext bundle wall | SSR worker 15.4 MiB raw / 3.2 MiB gzip > 3 MiB free-tier | `du`/gzip gate; webpack alias + dynamic `recharts`; `serverExternalPackages` NOT honored by OpenNext |
| `generateMetadata` in `'use client'` page | Next.js 16 hard build error | grep same-file co-occurrence; keep `page.tsx` a Server Component |
| Whole `[locale]` migration uncommitted | local-only i18n migration | `git status` → prod-only 404 |
| Import-depth off-by-one after route move | every admin file moved one dir level | 718 TS2307; webpack masks by stopping at first error |
| Migration filename not 14-digit | `YYYYMMDD` vs `YYYYMMDDHHMMSS` | Supabase branch stuck MIGRATIONS_FAILED, DB empty |
| CF Pages cache-wedge / lockfile bug | ast-grep Linux-binary npm#4828 | `optionalDependencies`; empty-retrigger commit precedent |

The automation wish the user voiced: a `measure-worker.mjs` prebuild/CI gate that fails if
gzip > 3 MiB — once size-bound on Workers, every PR is one dependency away from breaking the build.

### L22 — Code-consolidation: byte-compare before merge; the registry is pre-seeded (consolidate-code mode)

The `consolidate-code` mode ships with `CONSOLIDATION-CANDIDATES.md` pre-seeded (41 open
candidates from 146-session mining). Two load-bearing disciplines:

1. **Byte-compare before merging N near-duplicates** (§L2/§L4). The look-alike-but-different
   trap: 4 RLS storage policies looked like they hard-coded the same bucket array but encoded
   distinct per-CMD access tiers; a naive merge silently widened access on 3 buckets. Only merge
   when all N are byte-identical OR the merged API preserves every difference.

2. **Mechanical-tier first, codemod where possible.** The single biggest verified-live candidate
   is `const PANEL_WIDTH = 332` copy-declared in **44 files** while the canonical
   `PORTAL_SIDEBAR_WIDTH = 332` already exists — a pure codemod. Magic-literal dedup, orphan
   `git rm`, identical-helper extraction are all T1 (autonomous). DB view merges, RLS predicate
   extraction, and the 36-button-signature standardization are T2 (campaign).

The duplicate-detector pattern that works (session 1d944474): escalate from name-equality to
**SHA-1 body-hash** — it caught 2 missed mutation exports that name-matching missed.

### L23 — Standing instruction: dev server must survive session archive (skill-meta)

Recurring across 3+ sessions, now a standing instruction: the local dev server must NOT be tied
to the Claude Code session lifecycle — it dies when the harness archives/recycles the session,
forcing ~10 "open dev server" / "restart dev server" prompts. Launch it **detached** (outside
the harness) so it survives. This matters to the `errors` mode specifically — `/tmp/lex-dev.log`
only exists if the tee'd dev server is running; if the server died with the session, the log is
stale and `errors` mode reads nothing.

The deeper user complaint behind it: "burning all Claude tokens on basic feature work" — the
cleanup skill (and its auto-sweep modes) exist precisely to economize that spend by making
hygiene a one-command pass instead of a manual grind. Hygiene drift (i18n gaps, cross-NS dup
keys, dev-log errors, postgres advisors, lint, consolidation candidates) should be swept
automatically, not re-discovered by hand each time.

### L24 — Skill version-sync drift: skills live in multiple copies (skill-meta)

Both the `cleanup` and `conquering-campaign` skills exist in multiple locations that drift:
a CLI/staging copy (`_skill-updates/` or `.claude/skills/`) and a deployed plugin-cache copy,
plus an unverifiable cloud `anthropic-skills` copy. Sessions hit version drift (canonical at
v1.6.0 while deployed plugin-cache at v1.3.0) and manual copy-paste deploys.

For the `cleanup` skill: the canonical is `.claude/skills/cleanup/SKILL.md` (this file). When
bumping, confirm there isn't a second deployed copy serving a stale version. The recurring
"duplicate frontmatter breakage on every skill deploy" is a symptom of this multi-copy reality —
a deploy step concatenates or re-wraps frontmatter.

This is itself a consolidation candidate (registry C-skill-drift): the skill should have ONE
canonical home with a deterministic deploy, not N hand-synced copies.

---

> **L32–L37 mined 2026-06-04** from the June 3–4 sessions: the app-wide `hardcoded` extraction
> campaign (109 files / 372 keys / v1.7.42 → followups v1.7.43), the doc-version-merge followups
> (locale-parity gap), and the bug#244/#245 post-campaign sweeps (orphan-INDEX + classifier mis-tag).
> All 6 are prose-only — no script wiring yet (routes R12/R13 in UPGRADE-ROUTES.md).

### L32 — Mutation-module i18n: return error codes, not English strings; translate at consumers (hardcoded mode)

Plain `.ts` mutation modules (`lib/mutations/*.ts`, `lib/actions.ts`, hooks) cannot call
`useTranslations` — it's a React hook requiring a render context. When `hardcoded` mode
encounters user-facing English in a non-component module, the correct extraction is:

1. Return a stable **error code** string (e.g. `errors.failed_to_delete`, `errors.not_authenticated`)
   from the mutation / action. Do NOT return localized text.
2. Add a shared `useTranslateError(code: string): string` hook at the **consumer** screen — maps
   a known `errors.*` code → localized text via `t()` and passes any unknown string through
   unchanged (no-regression: DB error messages that share the same error channel stay readable).
3. Wire the consumer: `const te = useTranslateError(); ... toast.error(te(result.error))`.

**Boundary:** `_shared.ts`'s low-level `assertWritable()` impersonation string flows through ~92
generic `callRpc` consumers. Migrating all 92 screens to `useTranslateError` is an
error-channel campaign, not a follow-up. Leave as English and document as an exception
(`// i18n: error-channel-rollout needed for ~92 callRpc consumers`).

**Shipped 2026-06-03 (v1.7.43):** `useTranslateError()` at `hooks/use-translate-error.ts`; wired
into `wages.ts`, `lib/actions.ts`, and their consumers. Source: [[2026-06-03_i18n-hardcoded-extraction-followups]].

### L33 — Ternary/nullish-fallback literals escape the main `detect` pass (hardcoded mode)

The `i18n_extract.py detect` scan targets JSX text nodes, UI prop literals, and `toast.*` calls.
It regularly **misses** a second bucket — English in TypeScript expression contexts:

| Pattern | Example |
|---|---|
| Nullish fallback | `someValue ?? 'Failed to delete'` |
| Ternary fallback | `error.message ? error.message : 'Something failed'` |
| Form-validation | `'Title is required'` passed to a Zod / form validator |
| Permission error | `'You do not have permission to…'` in a hook |

These live in: hooks with `useMemo`/`useCallback`, server-action error paths, mutation callbacks,
form-schema definitions. A `hardcoded` pass should follow up with a targeted grep:

```bash
# Nullish-fallback literals in component/hook files
grep -rn "?? '[A-Z][^']\{3,\}'" apps/web --include="*.tsx" --include="*.ts" | grep -v "__tests__"
# Ternary fallback
grep -rn ": '[A-Z][^']\{3,\}'" apps/web --include="*.tsx" --include="*.ts" | grep -v "__tests__" | grep -v "style\|color\|variant\|type\|class"
```

Expect ~84 strings on a fresh scan after a main pass (source: 2026-06-03 followup across 57 files).
Extract into `errors.*` and `toasts.*` namespaces using the same key-naming + `useTranslateError` pattern.

**Mechanized (R12, v1.12.0):** `i18n_extract.py detect` now harvests this bucket directly — the new
`expr` context (nullish-fallback + ternary-tail regexes) plus `fail(` added to the call matcher. The
`detect` output prints a per-context tally (`jsx/prop/call/expr`); treat `expr` hits as higher-false-
positive (the agent layer confirms). The standalone greps above stay as a manual cross-check.

### L34 — Campaign locale propagation can leave specific locales entirely absent — parity check required (language / followups mode)

L25 covers the *detect-is-blind-to-absent-keys* gap. A more specific trap: even within a single
campaign's propagation step, the script may propagate only **some** locales (e.g. en + ar + fr
receive a new subtree; es + ru + zh are silently skipped). `language detect` only flags
*present-but-equal-to-EN* keys — a key that is **entirely absent** in a locale produces raw key
paths in the UI (`MISSING_MESSAGE`), which is worse than showing English.

Source: 2026-06-04 doc-version-merge followups — `containers.document.merge` was in en/ar/fr but
completely absent from es/ru/zh (3 of 6 locales). Invisible to `language detect`.

**Followup mode must include a locale-parity check for every campaign-added namespace:**

```bash
# Quick parity check: count keys per locale for a given namespace
for locale in en ar es fr ru zh; do
  python3 -c "import json; d=json.load(open('apps/web/public/messages/$locale/admin.json')); \
    sub=d.get('containers',{}).get('document',{}).get('merge',{}); print('$locale', len(sub))"
done
# All should print the same count; 0 = absent, not just untranslated
```

If any locale shows `0` (absent), propagate that locale first (use the EN values as placeholders),
then run `language` mode on the affected namespace.

**Mechanized (R13, v1.12.0):** `followups_cleanup.py parity <ns> [dotted.subtree]` does the per-locale
presence count and exits 2 if any locale is absent (vs merely a translation gap) — replaces the
hand-rolled loop above. Run it for every namespace a predecessor campaign added.

### L35 — i18n consolidation look-alike trap: single-word labels can be domain-specific (consolidate mode)

Reinforces §L4 for the i18n domain. Single-word labels that appear universal can encode
domain-specific semantics. The tax-calculator `Yes`/`No` toggles LOOK like `common.labels.yes`
/ `common.labels.no` but are form-field labels for specific tax-calculation scenarios — merging
them into `common.yes/no` would block per-context wording divergence later.

**Consolidate-mode rule:** before merging any single-word label, review its CALLSITE context, not
just its EN value + translation match.

| Safe to merge | Do NOT merge without callsite review |
|---|---|
| Pure UI verbs: Save, Cancel, Close, Delete, Download | Binary form toggles: Yes, No, On, Off |
| Language names: English, Arabic, French | Entity nouns: Tasks, Cases, Files, Members |
| Pure UI conjunctions: And, Or | Context-bound nouns: Details, Notes, Total |

The safe set from §C2 (universal labels in `common.actions.*` + `common.labels.*`) is correct, but
verify each candidate against `map-callsites` output before applying — "appears simple" ≠ "universal".

### L36 — Campaign vault logs reliably ship orphaned from INDEX.md; followups catches it — fix only your own (followups + docs modes)

A build/audit campaign closes by writing `docs/vault-logs/YYYY-MM-DD_<topic>.md` but **routinely
forgets to add its row to `vault-logs/INDEX.md`** — so the entry is invisible in the changelog. The
followups `docs` check (D5 orphan sweep) is the reliable backstop and has caught it on three
consecutive sweeps: bug#244 (`doc-version-merge`), bug#245 (`attachments-sort-card`), and a 7-log
batch indexed in one commit (`885dda4c` — `#240/#243/#248/#251/#255/#256/#259`). This is systemic, not
incidental — treat the orphan-INDEX check as a near-certain hit on every post-campaign sweep.

**Rule:** when a followups sweep finds the **predecessor campaign's own** log orphaned, add its INDEX
row (deterministic: basename ∉ INDEX → prepend the row). But per **L27**, add ONLY the predecessor's
row + this followups row — other concurrent sessions' orphans (the attachments sweep also saw
`balances-value-filters`, `bug248-actions-devtools-type-kind`) are flagged by `docs` but belong to
their owners; leave them uncommitted. The root-cause fix lives upstream (conquering-campaign should
write the INDEX row at campaign close) — that's a cross-skill follow-up, not a cleanup change.
Sources: [[2026-06-04_doc-version-merge-followups]], [[2026-06-04_attachments-sort-card-followups]].

**Mechanized (R13, v1.12.0):** `followups_cleanup.py orphan-index` lists disk-present / INDEX-absent
vault-logs, scopes to the located campaign's own log (the historical backlog of ~478 others is left
per L27), and emits the INDEX row template. It never edits INDEX.md — Claude writes the row.

### L37 — followups classifier over-tags environmental / prod-vs-repo items as "doable" — override to needs-hands (followups mode, sharpens L1)

`followups_cleanup.py classify` keys off the item's verbs and **cannot see where the resolution
lives**. On the doc-version-merge sweep it tagged FU-002 — "prod migration ledger diverges from local
repo" — as **doable**; it is the known apply-via-MCP steady-state
([[discovery_supabase-migrations-applied-via-mcp-not-pipeline]]), an **accepted-permanent-exception**,
and had to be overridden by hand. Sharpens **L1**: any item whose resolution is environmental
(prod-vs-repo drift, migration-ledger divergence, an external dashboard / NAS / CI surface, a `[!atta]`
gate) is needs-hands or accepted **regardless** of the script's tag. The classifier's `doable` is a
suggestion, not a verdict — re-read each surfaced item against L1's rubric before executing it. Source:
[[2026-06-04_doc-version-merge-followups]] (FU-002 disposition).

**Mechanized (R13, v1.12.0):** `followups_cleanup.py classify` now runs an `ENVIRONMENTAL_KW` guard
BEFORE the verb heuristic — prod-vs-repo / migration-ledger / "applied to prod" / concurrent-actor
items resolve to accepted-permanent-exception, so the "migration"/"verify" verbs can't mis-tag them
doable. Verified: FU-002's exact phrasing now classifies accepted, genuine doable items unaffected.

---

### L38 — Used-but-absent i18n keys leak as raw key-paths; detect them as the inverse of `hardcoded` (leaks mode)

A key referenced in code (`t('ns.key')`) but never added to the locale JSON renders as its raw uppercased dotted path (`PUBLIC.CODEX.COL_TYPE`) via next-intl `getMessageFallback` — a visible UX break invisible to BOTH `language` (only flags keys present-but-equal-to-EN, §L25/L34) and `hardcoded` (finds literals not yet keyed). The public Codex page shipped this twice (`codex.col_type` / `col_status` / `filter_status`). The `leaks` mode (v1.13.0 — `i18n_extract.py leaks`, wired into `run_all`) closes it: resolve every static `t()` key app-wide, flag EN-absent (HIGH, raw in every locale) + locale-absent (MED, raw in that locale).

Two traps baked into the resolver:

1. **A `useTranslations`-only namespace scan misses server pages.** Server components declare their namespace via `getTranslations('ns')` / `getTranslations({namespace:'ns'})`. The pre-existing `verify` matched only `useTranslations(` → it would have MISSED the exact Codex leak (a server page). The `leaks` resolver — and now `verify` — match both forms + the `{namespace:}` object. Any future i18n-resolution code MUST match all three.
2. **Verify the JSON PATH before declaring a leak.** A manual pass flagged the ADMIN Codex page as leaking ~50–80 keys by checking `admin.insights.codex.*` — the real keys live under `admin.files.insights.codex.*` (82 keys, present). The `leaks` tool resolved them correctly and cleared the false alarm: trust the resolver over an eyeballed `obj.get(path)`. (The admin page's keys are also TEMPLATE-literal — `t(\`files.insights.codex.page.${x}\`)` — which the tool skips by design; static-only resolution = zero false positives, at the cost of not catching a fully-absent dynamic prefix.)

`leaks` is detect-only — minting EN copy is `hardcoded`/human work; commit fixes with a filtered per-hunk patch because locale JSON is the most co-mingled file in the repo (§L27). The locale-absent bucket is the app-wide sibling of followups `parity` (§L34).

---

> **L25–L31 mined 2026-06-02** from the heavy 2026-05-30→06-02 cleanup usage: 4 auto-spawned
> followup sweeps (`dark-mode-color-fix`, `auto-credit-limit`, `admin-task-row-members-parity`,
> `templates-editorial-ui`) + 2 `run_all.py` passes + the v1.9.x always-on-bump runs. These are
> the lessons the L1–L24 mining (which closed 2026-05-29) could not have seen.

### L25 — `language` mode count semantics: detect vs verify, the absent-key blind spot, the real floor (language mode)

Three counting traps recur on **every** `language` pass:

1. **`verify` count > `detect` count is EXPECTED, not a regression.** `verify` re-counts every locale
   value equal to EN with **no** brand-glossary filter; `detect` filters out brand acronyms,
   placeholders, and valid cognates. Live: the task-row sweep showed `verify 551 > detect 396`.
   **Trust `detect`'s before→after delta as the success metric — never `verify`'s absolute count.**
   (memory `discovery_i18n-verify-overcounts-vs-detect`)

2. **`detect` is blind to keys ABSENT from the non-EN files.** It only flags keys *present but equal
   to EN*. A brand-new subtree added to `en/*.json` only (never mirrored to ar/es/fr/ru/zh) is
   invisible — `detect` reports 0 while the UI renders raw key paths. Propagate explicitly: set the
   dotted path in **every** locale + re-dump. When a sibling row already exists (e.g. members
   `task_card.*`), **reuse its translated values for parity** instead of re-translating — including
   literal CJK (zh `领域`, not `字段` and not `\uXXXX`). Adding a fresh EN cognate
   (`fr description_label = "Description"`) *raises* `detect` by 1 because it now equals EN = the
   cognate floor. (memory `discovery_i18n-detect-misses-absent-keys`)

3. **The floor is real — don't chase it to 0.** The 385 / 531 / 585 "untranslated" counts across runs
   are genuine cognates + brand tokens + placeholders + proper names; the apply is a verified no-op
   (`git diff` on `messages/` clean). "385 untranslated, 0 files changed" is success, not failure.

**Bonus (errors + language):** a phantom `MISSING_MESSAGE: …key…` for a key that IS present + committed
in all 5 locales is a **stale dev `messageCache`**, not a missing translation — do **not** "fix" the key.
Resolved app-side 2026-06-01 by gating the cache off in dev ([[2026-06-01_i18n-dev-cache-bypass]]);
pre-fix, a full dev-server restart was the only workaround. The `errors` mode classifier should treat
`MISSING_MESSAGE` for an existing key as `framework-noise` (dev-cache), not `code-bug`.

### L26 — `language` apply must use the project's EXACT JSON writer or the whole file churns (language mode)

The non-EN message files are written by `json.dump(…, ensure_ascii=False, indent=2)` + a trailing `\n`,
storing literal scripts (zh `领域`, not `\uXXXX`). `i18n_cleanup.py apply` already matches this.
**Anyone hand-writing keys — or any future re-dump — must match it byte-for-byte:** `ensure_ascii=False`,
2-space indent, trailing newline. A mismatch (ascii-escaping, 4-space, missing final newline) rewrites
every line of the file and buries the real change in a multi-thousand-line diff. Confirmed on the task-row
sweep: matching the writer produced a minimal diff touching only the changed keys.

### L27 — Concurrent-actor scoped commit: cleanup runs in a co-mingled working tree (skill-meta)

Recurring across the templates, task-row, and credit-limit followup sweeps: the campaign's own files sit
`modified` alongside **35–119 files of OTHER live workstreams** ([[discovery_concurrent-migration-actor]] —
a parallel session edits FE source AND DB mid-flight). A sweep that `git add -A`s the tree commits someone
else's half-finished work and can break `main`.

**Discipline (binding for any sweep that commits):**

1. Map the full uncommitted surface FIRST (`git status --porcelain`); commit **only** the campaign's own
   files; leave every other dirty file untouched.
2. Verify the staged files import only **non-dirty** siblings, so `main` stays buildable in isolation after
   the partial commit.
3. Tells that a dirty file is NOT yours (exclude it): docs heat-map counter bumps (`claude_hits: 17→20`,
   written by the docs daemon — [[discovery_docs-daemon-races-edit-tool]]), barrel-export additions you
   didn't make (`PageActionDivider` in `portal/index.ts`), all-locale i18n from a parallel tx-label run.

Strengthens L5 (Edit/hook race) + L23 (dev-server survives archive) into a commit-scoping rule. Note also:
git lives **inside** `lex_council/` (the submodule) — run `git status`/`add`/`commit` there, not at the
workspace root (memory `discovery_lex-council-git-submodule`).

**Script (R10, v1.10.0):** `scripts/commit_scope.py` mechanizes this — `scan --files/--campaign`
partitions the dirty tree into owned / foreign / tell:daemon (counter-only frontmatter) / tell:barrel
(export-only `index.ts`) / tell:i18n (`messages/*`); `buildcheck` flags an owned source file that
imports a foreign-dirty sibling (exit 2); `emit` prints the `git add` block for the owned set only. It
never commits. Wired into the followups mode as Step F5.5. Live demo on its own build: 57 dirty files
in `lex_council/`, only 2 owned — the other 55 were a concurrent session's work + 12 daemon bumps.

### L28 — When an MCP/server is offline mid-sweep, degrade WITH receipts — never silent no-op (postgres + errors modes)

`postgres` mode hard-depends on the Supabase MCP, which is often offline at session start
([[discovery_supabase-mcp-may-need-reconnect]]). `errors` mode depends on `/tmp/lex-dev.log`, which is
stale/empty if the detached dev server died (L23). When the dependency is unreachable, the mode must **not**
report "clean" — it writes the exact queries/commands it *would* have run into the vault log + a
needs-user-hands checklist ("Run `/mcp`, then execute these 4 SQL queries"), classified per L1. Live: the
credit-limit sweep surfaced 4 postgres queries to the vault log when MCP was offline rather than skipping the
check. `run_all.py` already excludes MCP-postgres from its auto-run for exactly this reason; an explicit
`/cleanup postgres` must degrade-with-receipts, not no-op.

### L29 — A zero-edit sweep skips BOTH the app patch bump and its own vault log (skill-meta)

The v1.9.0 always-on patch bump (§Workflow Step CL) and P8 both key off *did this session change app
state* — not *did a cleanup run*. Exercised live:

- **No-op detect-only run** (run-all where `language` apply changed 0 files + postgres was read-only): no
  version bump; the `/tmp/cleanup_triage.md` dashboard + a thin "backlog record" vault log IS the log — no
  separate code-change vault log ([[2026-06-01_cleanup-run-all-triage-2]]).
- **Stage-and-commit-only sweep** (templates followups: zero code edits, only committed an already-logged
  campaign): "no vault log needed — the campaign's own vault log was already written and is now committed."

So: bump the patch **and** write a fresh vault log only when the sweep edits/writes app code or DB. Pure
triage, a pure no-op apply, and pure git-plumbing (staging an already-logged change) skip both.

### L30 — Scanner self-reference false positives: exclude canon-preview / doc components (consolidate-code + lint modes)

The `consolidate-code` C.white-foreground scan flagged `CanonPreviewPanel.tsx:767` — which renders the
*rule text itself* inside a `<code>` snippet, not a real violation (dark-mode sweep). Any grep-based scanner
(off-token hex L13, C.white foreground, retired-name L3) must exclude design-canon preview/doc components
that render rule text, token names, or retired identifiers **as content**. Heuristic: a hit inside a
`<code>`/`<pre>` JSX child, or in a file on a `*Preview*` / `*Canon*` / `*DevTools*` path, is a candidate
self-reference — verify before counting it.

### L31 — Postgres advisor counts are dominated by accepted-by-convention items; net them out before reporting (postgres mode)

A raw `get_advisors` count is alarmist. On the 2026-06-01 run-all, **193 security advisors decomposed to
191 sanctioned `*_security_definer_function_executable`** (the v2 RPC/trigger pattern: SECURITY DEFINER +
`search_path=''` + REVOKE public/anon + GRANT authenticated — an **accepted exception per L17, not a
finding**) + exactly **2 real residues**: `branch_tags_all` with `WITH CHECK = true` (any authenticated user
writes any row — [[discovery_branch_tags_rls_was_broken]]) and `submission_rate_limits` rls-enabled-no-policy
(likely intentional service-role/edge-only). Likewise **170 performance advisors = 4 initplan (bare
`auth.uid()`) + 56 multiple-permissive (already owned by the rls-bundle-rollout campaign) + 103 unused-index
(review, don't blind-drop) + 6 no-PK (all dated backup snapshots → drop, don't add PKs) + 1 conn-count
notice.** The `postgres` classifier must subtract the 191 sanctioned SECURITY DEFINER rows + the
rls-bundle-tracked multiple-permissive rows before it reports a number, or every sweep cries wolf.

### L39 — Heavy client-only libs SSR'd into the OpenNext Worker bust Cloudflare's 3 MiB wall — detect statically, gate on the gzip measurement (bundle mode)

`@opennextjs/cloudflare` bundles all SSR code into one Worker script capped at
3 MiB gzipped (free) / 10 MiB (paid). A heavy client-only lib (`recharts`)
imported into a component Next.js server-renders lands in that bundle — even
when the component is `'use client'` (client components are still SSR'd for the
initial HTML). The **1.7.60** deploy failed this way: the members `CreditStatsBar`
Points panel imported `recharts` directly while every admin chart was already
isolated behind the `.body` + `dynamic({ssr:false})` convention. Two compounding
failures let it ship: (a) the `release` gate's bundle check was a manual
`du`/gzip probe nobody ran, and (b) `/cleanup` loaded a **stale shadow copy** of
this skill (global v1.2.0, no release/bundle mode at all) — the L24 multi-copy
drift made concrete. Takeaways, all mechanized into `scripts/bundle_cleanup.py`:
keep heavy libs behind the `.body`+`ssr:false` wrapper; the static detector is
**early-warning** (it only knows the seed list) while the **gzip measurement is
the hard gate** (the only thing that catches a lib off the list); measure the
**gzipped worker artifact** (`.open-next/worker.js`), not `du -sh` (raw dir ≠
gzipped worker — the incident's "15.4 raw / 3.2 gzip" proves only gzip counts);
a present-but-tiny `worker.js` is a stale placeholder → degrade-with-receipts,
never a false "OK"; and a skill upgrade is **dead on the `/cleanup` path unless
the copy that actually loads carries it** (sync the copies or the mode never
runs). Wired into the `release` gate PR2 + `run_all`.

### L40 — The unattended rotation routine has three non-negotiables: never push, one mode per run, keep the order synced (rotate.py / routine)

The hourly `lex-cleanup-rotation` task (R15, v1.16.0) runs `/cleanup` unattended,
so the safety rails that a human session enforces by judgment must be encoded:

1. **Never `git push`.** The whole reason the user asked for this routine is to
   auto-apply + commit but keep the push to `origin/main` a manual gate. A
   routine that pushes silently lands unreviewed hygiene edits (i18n rewrites,
   `eslint --fix`, additive migrations) on `main`. `rotate.py` never touches git;
   the routine prompt + `.claude/commands/cleanup-routine.md` commit only. If you
   ever wire push in, you've broken the contract.
2. **Exactly one mode per run.** Each scheduled run is a fresh, memory-less
   session. Running `run_all` or chaining modes unattended multiplies blast radius
   and makes a bad commit hard to attribute. The cursor (`next_index`) is the only
   memory; `rotate.py next` picks the single spot, `rotate.py advance` steps it.
3. **`release` is never rotated, and the order must stay synced.** A real release
   (version bump + changelog + git block) must stay human-driven — `rotate.py
   sync-order` filters `release` out and folds every *other* newly-LIVE mode into
   the rotation, so a mode added to SKILL.md doesn't silently fall out of coverage
   ("accommodate from now"). Run `sync-order` whenever a mode is added.

Corollary: each mode's own guardrails still hold under the routine — `postgres`
stays additive-only and verifies the prod `project_id` before any write; detect-only
modes (`bundle`, `leaks`) just report. The routine doesn't relax them; it inherits
them. Mechanized in `scripts/rotate.py`; full per-run recipe in SKILL.md §Step RT.

### L41 — Never `git checkout`/restore a message JSON during a live concurrent-actor session; test i18n write-paths with throwaway keys or `--out-dir /tmp`

The `public/messages/{locale}/*.json` tree is the single most contended set of
files in this repo — a concurrent actor (and the build dump) both rewrite it
live. During the v1.18.0 DB-native rewrite, a "belt-and-suspenders"
`git checkout -- public/messages/fr/clients.json` (cleaning up after an idempotent
`apply` test) **silently discarded the concurrent actor's uncommitted edit** to
that file — a nav relabel (`Calculateurs`→`Outils` + a new `nav.tabs` subtree) that
was present in all 6 locales and committed nowhere. It was recoverable only because
the actor had applied the identical change to the 5 sibling locales (still dirty),
so the fr file could be reconstructed to match (`+9 -2`, same structure). Lessons:

1. **Uncommitted ≠ recoverable.** `git checkout` on a never-staged working-tree
   change is unrecoverable from git — there is no reflog entry. Treat every dirty
   message file as potentially another session's in-flight work (§L27 commit-scope
   is the sibling rule for *staging*; this is the rule for *destroying*).
2. **Test write-paths in isolation.** Validate `apply` / delete logic with a
   throwaway key (`settings.__cleanup_selftest__`) you insert and remove, or point
   `--msg-root` / `--out-dir` at `/tmp`. Never round-trip a real tracked message
   file through a write + `git checkout` cleanup.
3. **The DB is the recovery oracle when the actor pushed.** Check whether the lost
   edit is in `app_translations` (`leaks --db` / a direct read): if the actor
   pushed, `dump-translations.mjs --namespace <ns> --locale <loc>` regenerates it.
   Here the actor's relabel was JSON-only (DB still matched HEAD), so the dump
   couldn't help — reconstruct from the sibling locales' pattern and flag it to
   Atta. Always disclose a clobber; never paper over it.
