# DB playbook — conquering-campaign

Load this for any phase touching schema / RLS / views / triggers / functions / migrations. SKILL.md keeps the one-line gates (G2, G3) + the named-pattern index; the full procedures + the project-specific schema facts live here.

---

## PDAAV — probe → draft → approve → apply → verify (the DB sub-pattern)

Every DB phase follows this. Declare `db_pattern: PDAAV` in the plan.

1. **Probe** — `execute_sql` against `information_schema.columns`, `pg_policies`, `pg_views`, `pg_class.reloptions`, `information_schema.routines` to find the existing pattern to mimic AND to confirm every structural claim a W1 subagent made (column locations, RLS shape, view conventions). W1 subagents reliably mis-locate columns in three patterns: tables renamed mid-history; a column that conceptually "belongs" to entity A but lives on an overlay table B (`is_programmer` lives on `admin_perms`, not `council_members`); a column exposed only via a join view. **Probe before you draft** — never write a migration on faith of a W1 claim (failure mode #32).
2. **Draft** — write the migration SQL inline in the conversation. Don't execute.
3. **Approve** — `AskUserQuestion` with the SQL visible + 3 options: `Apply (Recommended)` / `Tighten <axis>` / `Hold`. P3 (No Silent Writes) is the contract. Red-tagged phases gate regardless of cadence.
4. **Apply** — `apply_migration` on approval. Single MCP call.
5. **Verify** — post-flight `execute_sql` against the LIVE schema (failure mode #33). `{"success": true}` is NOT ground truth, especially after a fixed-and-retried migration:
   ```sql
   -- table + columns landed?
   select column_name, data_type, is_nullable from information_schema.columns
   where table_schema='public' and table_name='<t>';
   -- RLS policies present with the intended qual?
   select policyname, cmd, qual, with_check from pg_policies
   where schemaname='public' and tablename='<t>';
   -- view kept security_invoker = true? (CREATE OR REPLACE VIEW silently drops it)
   select c.relname, c.reloptions from pg_class c
   join pg_namespace n on n.oid=c.relnamespace
   where n.nspname='public' and c.relname='<v>' and c.relkind='v';
   ```
   Record the SELECT results in the phase change-log as evidence.

### 2a-RLS — effective-access check (when a phase changed an RLS policy / grant / view-security)
Qual-text-matches-intent is necessary; effective-access-matches-intent is sufficient (failure mode #47). A policy text can match while a restrictive policy on the same table, a missing grant, or a `security_invoker=false` wrapping view blocks/admits the user. Run a representative SELECT under a simulated authenticated context for BOTH an admit-user and a deny-user:
```sql
set local role authenticated;
set local request.jwt.claim.sub to '<uuid-that-SHOULD-see-rows>';
select count(*) from <view_or_table>;     -- expect > 0
reset role; set local role authenticated;
set local request.jwt.claim.sub to '<uuid-that-should-NOT>';
select count(*) from <view_or_table>;     -- expect 0
```
Record both counts. When a phase bundles ≥2 access-control-layer changes (RLS + grant, grant + view-security), assign sub-phase IDs (`P1a`, `P1b`) and verify each layer independently (§2b phase atomicity).

### Concurrent-actor re-probe (failure mode #33 extension, G3)
Production schema can flip mid-session from another actor's migrations. A subagent's live read can be stale before it executes. **Re-probe the live schema + check the `supabase_migrations` ledger at the START of every DB wave**, not just at plan-write time. If interleaved foreign migrations appear, STOP and reconcile before drafting. (`v2-trigger-column-drift` drafted nickname fixes against a snapshot a parallel campaign had already reversed — the fix would have hard-broken prod.)

---

## PDAAV-RIBS — SQL rename + body shrink (mirror of FE RIBS)

When a DB phase renames a function/view/trigger AND shrinks its body. Declare `db_pattern: PDAAV-RIBS`.

1. **Probe** every dependent of the old name via `information_schema.routines` / `pg_views` / `pg_policies` — the dependents list is the migration's planning artifact.
2. **Draft** atomically: `CREATE OR REPLACE FUNCTION new_name(...)` (shrunken body); for views `CREATE OR REPLACE VIEW new_name AS …; ALTER VIEW new_name SET (security_invoker = true);` (the `ALTER VIEW` is MANDATORY — `CREATE OR REPLACE VIEW` silently drops it); `UPDATE` every dependent body (RLS quals, view bodies, trigger bodies); `DROP … old_name` LAST.
3. **Approve / 4. Apply** as PDAAV.
5. **Verify**: `pg_get_functiondef` shows the shrunken body; `information_schema.routines` count for `old_name` = 0; every dependent now references `new_name`; `security_invoker=true` re-confirmed; re-run 2a-RLS if policies were touched.

---

## New DB lessons (v3.0.0 mine)

### Function bodies are TEXT, not OID-bound (#67)
`ALTER TABLE … RENAME` (column or table) auto-resolves views / RLS / triggers via OID, but NOT function bodies — `pg_proc.prosrc` references columns by literal text. A missed body stays silent until something forces a re-plan (a `VOLATILE → STABLE` change altered planner eagerness and surfaced a broken column reference long after the rename). On ANY column/table rename:
```sql
-- enumerate EVERY function body (no language filter — SQL functions are missed by plpgsql-only scans)
select n.nspname, p.proname, pg_get_functiondef(p.oid)
from pg_proc p join pg_namespace n on n.oid=p.pronamespace
where n.nspname in ('public','private')
  and pg_get_functiondef(p.oid) ilike '%<old_name>%';
```
A `DROP <column>` WITHOUT `CASCADE` is a useful pre-flight: it errors listing every dependent, exposing bodies the rename won't auto-fix. Lex memory `[[discovery_sql-functions-missed-by-plpgsql-scan]]`.

### DB cascade audit is blind to FE callsites (#68)
`pg_depend` maps DB-side consumers only. Before any DROP / rename, grep the FRONTEND too:
```bash
grep -rn "\.from('<table>')\|\.from(\"<table>\")" apps/web/app/api apps/web/lib/mutations apps/web/hooks apps/web --include=*.ts --include=*.tsx
grep -rn "'<old_col>'\|\"<old_col>\"" apps/web --include=*.ts --include=*.tsx
```
`.from('tsl')` in an API route and `SettingsPanel.tsx` reading `users.nickname` directly both survived DB-side-clean phases and would have broken prod.

### ANALYZE stale stats before diagnosing slow queries (#69)
A timeout is often not a query problem. Check first:
```sql
select relname, n_live_tup, last_autoanalyze, last_analyze
from pg_stat_user_tables where relname='<t>';
```
`last_autoanalyze = NULL` / a row estimate frozen far below reality → the planner picks catastrophic nested-loop plans. `ANALYZE <t>;` is the fix. Run ANALYZE after any big backfill, and check stats BEFORE rewriting a slow query.

### Trigger firing-order + AFTER-recursion (#70)
- BEFORE row triggers fire **alphabetically** — name a new one to control order (`aa_users_access_btr` deliberately sorts after `aa_branches_access_invariant_btr`); document the intended order in the trigger COMMENT.
- An AFTER trigger that `UPDATE`s its own table re-fires all AFTER triggers (incl. itself) → recursion / double-compute. Cure: a BEFORE trigger that mutates `NEW` directly instead of issuing an UPDATE.

### Dual-RLS propagation + InitPlan fast-path (#78, positive patterns)
- When every view over a table is `security_invoker = true`, add the predicate to the BASE-TABLE RLS (`USING(deleted_at IS NULL)`) — it propagates to all views automatically. `soft-delete-rollout` skipped an ~80-view rewrite this way.
- A per-user attribute check independent of the filtered row, wrapped as a subquery, is hoisted to InitPlan (one eval/query) so the `OR <per-row-check>` short-circuits:
  ```sql
  USING(
    (SELECT EXISTS(SELECT 1 FROM user_permissions
       WHERE ap_uuid=(SELECT auth.uid()) AND <perm_col>=true))
    OR <per_row_visibility_check>
  )
  ```
  The `(SELECT …)` wrapper is mandatory for the planner to recognize it as non-row-dependent.

### Branch data-seeding gate (#79)
A preview branch created WITHOUT production data has 0 `auth.users` → login fails ("email/password incorrect", "verify your account"), which looks like an auth code bug. Before any UI-testing phase on a branch: `select count(*) from auth.users;` — if 0, forced gate → user recreates the branch with "Include production data" ON. Record `branch_data_status: populated | empty | unknown`.

### Cron-only RPC appears dead on a branch (#80)
pg_cron state may not transfer to branches. Verify cron-invoked RPCs against PRODUCTION `cron.job`, never a branch, before classifying them dead.

---

## Project-specific schema facts (lex_council — verify live, but expect these)
- **`users` PK is two columns:** legacy `ar` (bigint, used in some old FKs) and `id` (uuid, the auth identity). New RPCs/mutations/FKs targeting members use `users.id` (uuid). Verify via `information_schema.table_constraints` + `key_column_usage`.
- **GFN auto-create:** inserting a customer `ppl` row fires a trigger that creates the `file_class=1` GFN. An RPC must LOOK UP the trigger-created GFN via `fd_access.customer_ref_id`, never INSERT a `file_class=1 fd` manually. Lex memory `[[discovery_ppl-on-fd-a-auto-creates-gfn]]`.
- **Nullable bool in a computed column** needs `COALESCE(col, false)`, never `IS TRUE`, in every trigger/view expression that reads it.
- **Append-only view rule (42P16):** `CREATE OR REPLACE VIEW` cannot rename or reorder existing columns — new columns go at the END of the SELECT. Pre-check column order at PLAN time, not at apply time. Lex memory `[[feedback_create-or-replace-view-append-only]]`.
- **Silent-write columns = a third state:** columns populated by DEFAULT / sequence / trigger but never SELECTed are neither dead nor alive. A dead-column audit must run an INSERT/UPDATE-callsite pass before declaring a drop safe.
- **`%I` breaks on reserved words** (`case`, `select`, `index`…) in dynamic `DO`/`format()` — use `%s` + `quote_ident()` outside the format call, or prefer explicit `CREATE OR REPLACE` per function over a DO-block loop.
- **Project ref is `bqgrpnsvplvicnmzxwkm`** (production). A `-32600`/permission MCP error means WRONG project_id, not a harness block (G2). On a feature branch, writes go to the branch's project_id, never production, until merge. Lex memory `[[discovery_supabase-project-ref]]`, `[[discovery_concurrent-migration-actor]]`.
- **Member soft-delete** can pair `auth.users SET banned_until='infinity'` atomically inside the same SECURITY DEFINER RPC (service-role has auth-schema write) — no separate edge function; restore clears `banned_until`.
