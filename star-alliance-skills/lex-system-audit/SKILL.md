---
name: lex-system-audit
description: Methodology for auditing any backend subsystem in Lex Council — surveys schema, RLS, triggers, view security, state machines, dead aliases, inactive catalog entries; cross-references vault-logs and architecture docs; reads frontend for silent failures; produces a P1/P2/P3 finding list with effort and risk. Use when the user asks to audit, review, re-evaluate, health-check, find issues in, or assess the cleanliness of any subsystem — notifications, file access, attendance, transactions, advances, chat, agreements, ETO, customer portal, permissions, or any X system the user names. Also trigger on "is X clean", "find issues across X", "system review of Y", "what's wrong with Z", "what would you improve in W". This skill exists because the codebase has recurring trap families — security_invoker dropped on view rewrites, stale trigger bodies after renames, silent-swallow frontend patterns, dead aliases, namespace collisions, never-fired catalog rows — that reward a methodical pass over freeform investigation.
---

# Auditing a Lex Council subsystem

## What this skill does

Walks through a structured five-phase audit of a named subsystem (notifications, file access, attendance, transactions, etc.). Produces a ranked finding list at the end — **real bugs (P1)**, **design smells with small fixes (P2)**, **improvements (P3)** — plus a recommended next move.

Don't free-form. The phases below exist because each one catches a different class of issue. Skipping phases means missing findings.

## Phase 1 · Scope the audit

Before any reads, confirm with Atta:

1. **Which subsystem?** Get a name. If they said "audit the system", ask "which one — notifications, file access, attendance, transactions…?". An unscoped audit produces shallow findings across everything.
2. **Audit depth.** Three options:
   - *Quick* — 30-min survey, surface obvious smells, no proposals
   - *Standard* — full phased pass, ranked finding list with proposals (default)
   - *Deep* — standard + DB stats over time + comparison with sibling systems
3. **What prompted it?** Recent bug? Planned refactor? New hire onboarding? This shapes priority — if a bug just shipped, the audit should weight "what else might be lurking from the same migration" higher.

Do not proceed past this phase without a scoped subsystem name.

## Phase 2 · Read the docs first (before any DB query)

The codebase follows a solar-system structure. Navigate it in this order — every audit, no exceptions. P13 mandates this; skipping it means writing recommendations that contradict existing decisions.

1. `lex_council/docs/primary_instructions.md` — the entry point.
2. `[[Vault Core]]` — find the planet hub for this domain.
3. The Planet Hub — `BACKEND.md` for DB-shaped systems (notifications, file access, attendance), `FRONTEND.md` for UI-heavy ones (admin pages, chat), `INTEGRATION.md` for cross-cutting (auth, realtime, edge).
4. The leaf doc — e.g., `NOTIFICATION-PIPELINE.md`, `FD-ACCESS-MODEL.md`, `ATTENDANCE-V2.md`. This is the source of truth for the subsystem's design.

While reading, capture:
- The system's **table prefix** (e.g., `n_*` for notifications, `fd_*` for files, `atnd_*` for attendance). You'll use this in Phase 3 queries.
- The system's **canonical writer API** (e.g., `private.notify_many`, `private.fd_grant_access`). Direct writes that bypass it are a finding.
- The system's **view contract** (e.g., `n_member_feed` is the admin read path, `fd_cf_js` is the file-context view). Frontend code reading from a different shape is a finding.
- Any **`> [!atta]` callout blocks** in those docs. These are inviolable. Anything in the audit that contradicts an `[!atta]` block becomes a question for Atta, not a recommendation.

Then scan recent vault-logs:

```bash
ls -t lex_council/docs/vault-logs/*.md | head -20
```

Skim any from the last ~60 days that name the subsystem. Recent migrations are where rename-sweep misses, dead aliases, and stale trigger bodies hide. Note dates — anything that landed in the last 24-72 hours is highest-suspicion territory.

### Check the constructive memory index

Before running any DB queries, scan `lex_council/docs/memory/MEMORY-INDEX.md` using tiered retrieval — T1 (Hot) first, then T2 (Warm). Match the subsystem name against the entry tags. If any hot entries concern this subsystem (or a pattern likely to appear in it — view security, rename sweeps, RLS recursion, trigger bodies), read those entries in full and note them as "known traps to specifically check for" during Phase 3.

This takes two minutes and prevents recommending something the project already tried and rejected, or missing a pattern that has already caused a production incident.


## Phase 3 · Survey the live DB

Run these queries against the live schema. Each one targets a specific class of issue. The query block is generic; substitute the prefix or table list from Phase 2.

### 3a · Object inventory

```sql
-- Tables, views, materialized views in the subsystem's prefix
SELECT relname, relkind, pg_size_pretty(pg_relation_size(c.oid)) AS size
  FROM pg_class c
  JOIN pg_namespace n ON n.oid = c.relnamespace
 WHERE n.nspname = 'public'
   AND relname LIKE '<prefix>_%'
   AND relkind IN ('r','v','m')
 ORDER BY relkind, relname;
```

Cross-reference against the leaf doc's "Core tables" / "Views" tables. Anything in the doc but not in the DB → stale doc. Anything in the DB but not in the doc → undocumented surface (possible orphan from a migration).

### 3b · View security (the security_invoker trap)

```sql
SELECT c.relname, c.reloptions
  FROM pg_class c
  JOIN pg_namespace n ON n.oid = c.relnamespace
 WHERE n.nspname = 'public'
   AND c.relkind = 'v'
   AND c.relname LIKE '<prefix>_%';
```

Every member/customer-facing view should have `['security_invoker=true']`. A view that's missing it bypasses RLS for the calling user and runs as the owner — usually `postgres`, which has no RLS. This is the #1 silent security regression after a `CREATE OR REPLACE VIEW`.

### 3c · RLS enabled on tables

```sql
SELECT c.relname, c.relrowsecurity AS rls_enabled
  FROM pg_class c
  JOIN pg_namespace n ON n.oid = c.relnamespace
 WHERE n.nspname = 'public' AND c.relkind = 'r'
   AND c.relname LIKE '<prefix>_%';
```

Any user-facing table with `rls_enabled=false` is a finding. (Internal/private tables may legitimately have RLS off; flag for confirmation.)

Also check policies exist:

```sql
SELECT tablename, policyname, cmd, roles::text
  FROM pg_policies
 WHERE schemaname = 'public' AND tablename LIKE '<prefix>_%'
 ORDER BY tablename, cmd;
```

### 3d · Trigger inventory + stale body scan

```sql
-- All triggers on subsystem tables
SELECT t.tgname, t.tgrelid::regclass AS table_name,
       pg_get_triggerdef(t.oid) AS def
  FROM pg_trigger t
 WHERE NOT t.tgisinternal
   AND t.tgrelid::regclass::text LIKE 'public.<prefix>_%';
```

For each trigger function, check the function body doesn't reference renamed objects:

```sql
-- Replace <old_name> with each pre-rename name from recent vault-logs
SELECT n.nspname, p.proname
  FROM pg_proc p
  JOIN pg_namespace n ON n.oid = p.pronamespace
 WHERE n.nspname IN ('public','private')
   AND pg_get_functiondef(p.oid) ILIKE '%<old_name>%';
```

If anything comes back, that function will error at runtime when next fired. (See `db-rename-sweep` skill / memory `feedback_rename_trigger_bodies`.)

**PostgREST 42501 masking trap:** a `RAISE EXCEPTION` inside a trigger body that fires inside a WITH/RETURNING CTE surfaces to the frontend as `"new row violates row-level security policy"`, not as the actual error. If any recent vault-log or OPEN-ITEMS entry mentions an RLS error that appeared after a migration or rename, re-check trigger bodies first before auditing policies. Run: `SELECT pg_get_functiondef(p.oid) FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace WHERE n.nspname IN ('public','private') AND pg_get_functiondef(p.oid) ILIKE '%<renamed_column>%'` — if a match comes back, that trigger is the real culprit.

### 3e · State-machine sanity

For tables with a `state` / `status` column, check the histogram:

```sql
SELECT state, count(*) AS n,
       min(state_at) AS oldest, max(state_at) AS newest
  FROM public.<table>
 GROUP BY state
 ORDER BY n DESC;
```

Look for:
- **Stuck states** — rows in `'queued'` / `'pending'` for far longer than expected
- **Impossible states** — values that aren't in the documented state machine
- **All-one-state anomalies** — every row in `'sent'` when some should be `'read'` (suggests no one has read anything; likely a frontend write path is broken)
- **Cutoff lines** — sudden state distribution change at a specific timestamp suggests a migration changed insert behavior (real example: 2026-04-24 06:18 UTC for in_app deliveries)

### 3f · Dead aliases / orphan tables

If the leaf doc's "Retired artifacts" section lists tables/views that were supposed to be dropped after a migration, verify:

```sql
SELECT relname, relkind FROM pg_class c
  JOIN pg_namespace n ON n.oid = c.relnamespace
 WHERE n.nspname = 'public' AND relname IN (<list>);
```

Anything still present is a cleanup-debt finding.

### 3g · Catalog rows that never fired (for systems with a catalog)

```sql
-- Generic shape — adapt to the subsystem's catalog table
SELECT k.<key_col>,
       EXISTS (SELECT 1 FROM <events_table> e WHERE e.<key_col> = k.<key_col>) AS ever_fired,
       k.is_active
  FROM public.<catalog_table> k
 WHERE k.is_active = true;
```

Active catalog rows that have never fired = either a writer was never wired up, or the kind is dead. Either way, ask.

### 3h · Grants / privilege drift

```sql
SELECT grantee, privilege_type
  FROM information_schema.role_table_grants
 WHERE table_schema='public' AND table_name='<table>'
   AND grantee IN ('authenticated','anon','service_role');
```

Compare against the leaf doc's RLS table. Missing grants = RLS-allowed-but-PostgREST-blocked situations. Excess grants = potential bypass.

## Phase 4 · Read the frontend surfaces

For each subsystem, identify the React surfaces (the leaf doc usually lists them). Read each and scan for these recurring anti-patterns:

| Anti-pattern | Why it matters |
|---|---|
| `.then(() => {})` after `.from(…).insert/update/delete` | Swallows DB errors. The notification-bell-not-marking-read bug hid for 13 hours because of this (2026-04-24). |
| Bare `catch {}` around supabase calls | Same as above. |
| `await supabase.from(…)…` without checking `{ error }` | Same. |
| Direct `.from('<base_table>')` write where a `_js` view exists | Bypasses Law 2. RLS may behave differently than intended. |
| Hardcoded category colors / hex in JSX | Token drift. Should reference `@repo/md` `colors` or the C constants. (Memory: `feedback_never_guess_design_tokens`.) |
| Optimistic UI update with no error rollback | If the write fails, UI lies. Same notification-bell pattern. |
| RPC names that don't exist in the DB | Renamed since the frontend was last touched. Run `\df` for the RPC. |
| RLS-looking error from a mutation (`42501 "new row violates row-level security"`) when no RLS change was made | PostgREST masks trigger errors as RLS violations. The real cause is a stale column ref inside a trigger body (e.g. after a rename). Grep `pg_proc.prosrc` for the old column name before concluding the policy is broken. (Memory: `feedback_postgrest_masks_trigger_errors`) |

Concrete grep recipes:

```bash
# Silent-swallow audit
grep -rn "\.then(() => {})" apps/web/app
grep -rn "catch {" apps/web/app | grep -v "catch (e" | grep -v "catch(e"

# Direct base-table writes (substitute the system's tables)
grep -rn "\.from('<table>')" apps/web/app | grep -E "\.(insert|update|delete)"
```

## Phase 5 · Rank findings and propose

For each finding, write up:

> **<Title — one line>**
>
> *What's wrong:* concrete observation (with row counts, file:line citations, query results)
> *Why it matters:* impact in plain language — UX, observability, performance, correctness, security
> *Effort:* small (one migration / one PR) / medium (multi-file refactor) / large (multi-day)
> *Risk if unfixed:* low / medium / high
> *Proposal:* what the fix looks like; if multiple options, list them with trade-offs

Tier them:

- **P1** — real bugs causing live damage (silent failures, stuck states, security gaps, data integrity)
- **P2** — design smells that produce the next P1 (silent error swallowing, dead aliases, missing transition guards, untokenized colors)
- **P3** — improvements (retention crons, observability dashboards, UX polish)

End the audit with a "What I'd tackle first" paragraph: pick 1-2 P1/P2 items that are bundle-able as a focused next sprint, with a one-sentence rationale per pick. Don't list everything — recommend.

## Things to avoid

- **Don't audit without scoping.** "Audit the system" without a named subsystem produces shallow noise. Force scope in Phase 1.
- **Don't skip the docs.** Reading the leaf doc first prevents recommendations that contradict design decisions or `[!atta]` blocks.
- **Don't propose retention without volume data.** "Add a retention cron" is a P3 unless you've shown row counts that make it P2. Always pull a `count(*)` + age-distribution before proposing pruning.
- **Don't fix during audit.** Audit produces findings; fix is a separate session unless Atta explicitly says "and fix what you find". This skill is the surveyor, not the construction crew.
- **Don't aggregate findings into mega-PRs.** Each P1/P2 should be ship-able independently with its own vault-log.

## Done means

✓ Phase 1-2 captured: subsystem named, depth chosen, docs + recent vault-logs read
✓ Phase 3 queries run; results pasted into the audit (don't summarise away the numbers — they ARE the evidence)
✓ Phase 4 frontend surfaces scanned; specific file:line citations for any anti-pattern hit
✓ Findings tiered P1/P2/P3 with the standard write-up format
✓ "What I'd tackle first" recommendation paragraph
✓ Shareable as a single message — no follow-up "actually let me also look at X" tail

The audit's job is to compress hours of investigation into a structured artifact Atta can act on or shelve. If it reads like stream-of-consciousness, redo the synthesis pass before sending.
