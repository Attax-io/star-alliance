# Lessons learned (cross-mode landmines)

> **Wired into scripts (v1.8.0):** L9/L10/L15/L17 → `postgres_cleanup.py` detect; L11 + L19 → `lint_cleanup.py`; L14 → `errors_cleanup.py`; L16 → `i18n_cleanup.py` detect. The rest remain cross-mode prose guidance. **L25–L31 added 2026-06-02 from the 2026-05-30→06-02 usage; L27 → `commit_scope.py` (R10).**

Patterns extracted from the 2026-05-28 solar-system doc-sync audit +
follow-up sweep. These apply across **every** cleanup mode, not just one.

## L1 — MCP-out-of-reach taxonomy

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

## L2 — Behavior-parity verification post-refactor

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

## L3 — Post-rename narrative-artifact sweep

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

## L4 — Look-alike-but-different trap

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

## L5 — PostToolUse hook race conditions with Edit

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

## L6 — Same-session continuation markers

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

## L7 — Vault-log size threshold

For ≤3 follow-up items touching the same surface, write a single inline
vault-log entry (the `2026-05-28_solar-system-doc-sync-followups.md`
shape). For ≥4 items OR multi-surface changes, delegate to
**vault-log-compliance** for a fuller entry with P13 self-audit table.

The `language` mode always delegates because translation passes are
multi-locale by definition (5 surfaces). The `docs` + `followups`
modes pick per-pass based on scope.

## L8 — Long-running global replaces leave artifacts; periodic grep

L3 above is a specific instance of a broader pattern: any mass-edit
campaign (rename sweep, token consolidation, primitive retirement)
leaves stray artifacts that don't surface for weeks because they're
syntactically valid. The `docs` mode's Step D7 + Step D6 grep these
proactively; without periodic cleanup, the artifacts accumulate and
the next person reading the doc gets a false mental model.

When a future BUILD ships a rename, the FOLLOWING `/cleanup docs` run
should be scheduled within a week.

## L9 — `CREATE OR REPLACE VIEW` silently drops `security_invoker = true` (postgres mode)

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

The postgres mode's PG4 verify step must run this check.

## L10 — `get_advisors` misses overly-permissive RLS; supplement with direct query (postgres mode)

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

Also supplement with the stale-function-body scan (catches v2 rename drift):

```sql
-- Detect function bodies still referencing renamed columns/tables
SELECT p.proname, LEFT(p.prosrc, 200) AS body_preview
FROM pg_proc p
WHERE p.prosrc ILIKE '%user_preferences%nickname%'
   OR p.prosrc ILIKE '%folder_classes%'
   OR p.prosrc ILIKE '%council_members%';
-- Expect 0 rows post-v2 rename
```

## L11 — Pre-existing lint warnings create baseline noise; always track delta (lint mode)

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

Also: filter tsc output to exclude `.next/` paths.

## L12 — `no-unused-expressions` is always architectural — never auto-fix (lint mode)

The `no-unused-expressions` rule fires most often on the ternary-as-statement pattern:
`cond ? a.foo() : a.bar()`. This fails the rule because the ternary's result value is unused.
ESLint `--fix` CANNOT resolve this automatically — the correct fix is `if/else`, which changes
code structure.

**Detection:** `grep -rn '?\s*[a-z].*\..*()' apps/web/ --include="*.tsx" | grep -v '//'`

**Fix pattern:** Always `if (cond) { a.foo() } else { a.bar() }`. Never use `void cond ?...`
or `eslint-disable-line`.

Similarly, `react-hooks/rules-of-hooks` is always architectural. A hook called inside a
conditional is a structural problem that requires component decomposition, not suppression.

## L13 — Scope ESLint to campaign-touched files first; grep for hex literals separately (lint mode)

Two items ESLint misses entirely that the lint mode should check as supplementary scans:

**1. Off-token hex color literals** — ESLint does not scan CSSProperties objects for `#hex`
strings:

```bash
grep -rn '#[0-9a-fA-F]\{3,6\}\b' \
  lex_council/apps/web/components \
  lex_council/apps/web/app \
  --include="*.tsx" --include="*.ts" | grep -v "//.*#" | grep "color\|background\|border"
```

Count > 10 = flag for a token-sweep campaign.

**2. Module-level `const` style-object orphans** — `no-unused-vars` does not catch exported
objects that are declared but never imported. Use knip/ts-prune or manual grep — out of scope
for auto-fix, surface as advisory.

## L14 — ThemeToggle + StrictMode errors are known noise in `errors` mode

Two error signatures that should be suppressed without requiring triage:

1. **ThemeToggle hydration errors** — `Warning: Extra attributes from the server: class` on
   the `<html>` element. Classifier: `framework-noise` + suppress.
2. **React StrictMode double-invocation errors** — same error signature appearing exactly twice
   consecutively with no intervening route. Classifier: `framework-noise` + suppress.

## L15 — Stale trigger bodies after v2 rename are invisible to advisor + lint (postgres mode)

The 2026-05-24 v2 campaign renamed 54 tables. Many trigger functions reference old table/column
names. These **pass all advisor checks**, **pass tsc**, and **pass lint** — they just operate on
the wrong data silently.

The only way to detect this class is a `pg_proc.prosrc` full-text scan:

```sql
SELECT p.proname AS fn_name, n.nspname AS schema, LEFT(p.prosrc, 300) AS body_preview
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

Results classified as `schema-campaign` (require careful SQL surgery — not auto-fixable).

## L16 — i18n namespace scope trap: `useTranslations` scope must match the JSON file tree (language mode)

A component that calls `useTranslations('customer_wizard')` while living under a page that
loads `admin.json` will silently fall through to `getMessageFallback` and render raw key paths
in production. The correct call is `useTranslations('admin.customer_wizard')`.

Detection grep (pair with the language mode's detect step):

```bash
grep -rn "useTranslations(['\"]" lex_council/apps/web/ --include="*.tsx" |
  grep -v "^.*useTranslations('admin\." |
  grep -E "(admin|portal|members|clients)" | head -20
```

Also: **`window.confirm()` calls are untranslatable** and should be flagged as technical debt
during any language pass. Grep for `window.confirm(` and surface a count.

## L17 — Postgres advisor requires multi-pass until clean; common recurring types (postgres mode)

Fixing the top-N advisories often reveals a new Nth+1 advisory hidden behind them.
**Loop until `get_advisors` returns an empty list** (or only known-intentional exceptions).

The two most common advisor types in this project:

| Advisor | Signal | Action |
|---|---|---|
| `rls_enabled_no_policy` | Table has `ALTER TABLE ... ENABLE ROW LEVEL SECURITY` but zero policies — usually a stale backup/archive table | Classify `schema-campaign`; user decides to DROP or add a blanket policy |
| `authenticated_security_definer_function_executable` | A `SECURITY DEFINER` function is still EXECUTE-able by `authenticated` after `REVOKE ... FROM PUBLIC` — `authenticated` inherits via PUBLIC | Add explicit `REVOKE EXECUTE ON FUNCTION ... FROM authenticated;` if not intentional; document as exception if intentional |

Dead `auth.role() = 'service_role'` in RLS policies generate a "multiple permissive policies"
advisor. These are always dead code — flag as `schema-campaign` for batch DROP.

## L18 — `react-hooks/exhaustive-deps` suppressions on mutation callbacks are intentional (lint mode)

In this codebase, mutation callbacks are intentionally passed as stable refs and deliberately
excluded from `useEffect` dependency arrays. These lines have explicit
`// eslint-disable-next-line react-hooks/exhaustive-deps` comments.

**The lint mode must NOT remove these suppressions.** Classify any file with this pattern as
`reviewed-intentional` and skip it in the auto-fix pass.

Similarly, `no-undef` errors for `Buffer`, `process`, `module`, or `require` in `scripts/`
files are not real errors — fix is `/* eslint-env node */` at the top of the file.

## L19 — TS2304 `Cannot find name 'VIEWS'` always means a missing view-registry key (lint mode)

The most common tsc error in this codebase. Whenever a new view is created and added to a
page query, it must also be added to `apps/web/lib/view-registry.ts` as a key in the `VIEWS`
constant.

Detection:

```bash
grep -rn "VIEWS\." lex_council/apps/web/ --include="*.tsx" --include="*.ts" |
  grep -v "view-registry" | grep -oE "VIEWS\.[a-zA-Z_]+" | sort -u > /tmp/view_usages.txt

grep -n "^\s*[a-zA-Z_]" lex_council/apps/web/lib/view-registry.ts > /tmp/view_registry.txt

# Find usages not in registry
comm -23 <(sort /tmp/view_usages.txt | sed 's/VIEWS\.//') \
         <(grep -oE "^\s*[a-zA-Z_]+" /tmp/view_registry.txt | sort)
```

Any row in the comm output = missing view-registry entry = tsc error on that page.

## L20 — `VERSION-RELEASE-WORKFLOW.md` doc-stamp drift (RESOLVED 2026-05-29; release mode)

> **RESOLVED 2026-05-29.** VERSION-RELEASE-WORKFLOW.md §4 was reconciled to the live tree and the bump procedure now lives in `references/release-procedure.md`. The canonical release procedure doc was pointing at paths that predate the solar-system docs restructure. The `release` mode's PR3 step greps for what actually carries a stamp NOW instead of trusting the hard-coded list.

Also: app version lives in TWO places that drift — `apps/web/config/app.config.ts`
(`APP_CONFIG.version`, canonical) AND the web `package.json` `version` field.

## L21 — Release-time breakage is a recurring class; gate before bump (release mode)

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

## L22 — Code-consolidation: byte-compare before merge; the registry is pre-seeded (consolidate-code mode)

The `consolidate-code` mode ships with `CONSOLIDATION-CANDIDATES.md` pre-seeded (41 open
candidates from 146-session mining). Two load-bearing disciplines:

1. **Byte-compare before merging N near-duplicates** (§L2/§L4). Only merge when all N are
   byte-identical OR the merged API preserves every difference.
2. **Mechanical-tier first, codemod where possible.** The single biggest verified-live candidate
   is `const PANEL_WIDTH = 332` copy-declared in **44 files** while the canonical
   `PORTAL_SIDEBAR_WIDTH = 332` already exists — a pure codemod.

The duplicate-detector pattern that works: escalate from name-equality to **SHA-1 body-hash** —
it caught 2 missed mutation exports that name-matching missed.

## L23 — Standing instruction: dev server must survive session archive (skill-meta)

Recurring across 3+ sessions: the local dev server must NOT be tied to the Claude Code session
lifecycle — it dies when the harness archives/recycles the session. Launch it **detached** (outside
the harness) so it survives. This matters to the `errors` mode specifically — `/tmp/lex-dev.log`
only exists if the tee'd dev server is running.

The deeper user complaint: "burning all Claude tokens on basic feature work" — the cleanup skill
and its auto-sweep modes exist precisely to economize that spend by making hygiene a one-command
pass instead of a manual grind.

## L24 — Skill version-sync drift: skills live in multiple copies (skill-meta)

Both the `cleanup` and `conquering-campaign` skills exist in multiple locations that drift:
a CLI/staging copy and a deployed plugin-cache copy. Sessions hit version drift (canonical at
v1.6.0 while deployed plugin-cache at v1.3.0) and manual copy-paste deploys.

For the `cleanup` skill: the canonical is `.claude/skills/cleanup/SKILL.md` (this file). When
bumping, confirm there isn't a second deployed copy serving a stale version.

This is itself a consolidation candidate (registry C-skill-drift): the skill should have ONE
canonical home with a deterministic deploy, not N hand-synced copies.

## L25 — `language` count semantics: detect vs verify, absent-key blindness, the floor (language mode)

`verify` > `detect` is EXPECTED — `verify` re-counts every locale value equal to EN with NO brand-glossary
filter; `detect` filters brand acronyms/placeholders/cognates. Trust `detect`'s before→after delta, never
`verify`'s absolute (live: task-row `verify 551 > detect 396`). `detect` is BLIND to keys absent from non-EN
files (only flags present-but-equal-to-EN) — a new `en/`-only subtree is invisible while the UI renders raw
paths; propagate explicitly into every locale + reuse a mirrored sibling's values (incl. literal CJK — zh
`领域`, not `字段`). The 385/531/585 floor is real (cognates + brand + placeholders); a no-op apply is success.
Bonus: a phantom `MISSING_MESSAGE` for a present+committed key is a stale dev `messageCache`, not a missing
translation — classify framework-noise, don't "fix" the key.

## L26 — `language` apply must match the project's exact JSON writer (language mode)

Non-EN message files are written by `json.dump(ensure_ascii=False, indent=2)` + trailing `\n`, with literal
scripts. `i18n_cleanup.py apply` matches this; any hand-write or re-dump MUST too (ascii-escaping / 4-space /
no final newline rewrites every line and buries the real change in a multi-thousand-line diff).

## L27 — Concurrent-actor scoped commit: cleanup runs in a co-mingled tree (skill-meta) — wired: `commit_scope.py`

A cleanup/followups sweep runs in a tree a PARALLEL session is editing (FE+DB+i18n) while the docs daemon
bumps frontmatter counters; 3 of the 4 2026-05-30→06-02 sweeps sat amid 35–119 foreign dirty files. `git add
-A` there commits someone else's half-finished work and can break `main`. Discipline: map `git status` FIRST,
commit ONLY campaign-owned files, verify they import only non-dirty siblings, exclude the tells (docs
`claude_hits:` counter bumps, barrel `index.ts` export-adds, parallel `messages/*`). git lives INSIDE
`lex_council/` (submodule). **Mechanized by `scripts/commit_scope.py` (R10, v1.10.0): `scan`/`buildcheck`/`emit`
— partitions owned vs foreign vs tells, flags owned→foreign imports (exit 2), emits the `git add` block for
owned only, never commits.**

## L28 — Offline MCP / dead dev-log → degrade WITH receipts (postgres + errors modes)

`postgres` mode depends on the Supabase MCP (often offline at session start); `errors` mode depends on a live
`/tmp/lex-dev.log` (stale if the detached dev server died, L23). When the dependency is unreachable, do NOT
report "clean" — write the exact queries/commands into the vault log + a needs-hands checklist ("Run `/mcp`,
then run these 4 queries"), classified per L1. `run_all.py` already excludes MCP-postgres for this reason.

## L29 — A zero-edit sweep skips BOTH the patch bump and its own vault log (skill-meta)

The always-on patch bump (v1.9.0) and P8 both key off *did this session change app state*, not *did a sweep
run*. A no-op detect-only run (e.g. language apply = 0 files) → no bump, the triage dashboard IS the log. A
stage-and-commit-only sweep (already-logged campaign) → no fresh vault log. Bump + log only on a real edit.

## L30 — Scanner self-reference false positives: exclude canon-preview / doc components (consolidate-code + lint)

A grep scanner (off-token hex L13, C.white foreground, retired-name L3) flags rule text rendered AS CONTENT —
e.g. `CanonPreviewPanel.tsx` showing the rule in a `<code>` snippet. Exclude `*Preview*` / `*Canon*` /
`*DevTools*` paths + `<code>`/`<pre>` JSX children; verify a hit before counting it.

## L31 — Postgres advisor counts are dominated by accepted-by-convention items; net them out (postgres mode)

A raw `get_advisors` count is alarmist. Live: 193 security advisors = 191 sanctioned
`*_security_definer_function_executable` (the v2 RPC pattern — accepted exception per L17) + 2 real residues
(`branch_tags_all` `WITH CHECK = true`; `submission_rate_limits` rls-no-policy). 170 perf = 4 initplan +
56 multiple-permissive (owned by rls-bundle-rollout) + 103 unused-index + 6 no-PK (backup snapshots) + 1 conn.
Subtract the sanctioned SECURITY DEFINER rows + rls-bundle-tracked multi-permissive before reporting.

