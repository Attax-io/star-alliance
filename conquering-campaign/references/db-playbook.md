# DB playbook — conquering-campaign

Load this for any phase touching schema / RLS / views / triggers / functions / migrations. SKILL.md keeps the one-line gates (G2, G3, G6) + the named-pattern index; the full procedures + the project-specific schema facts live here.

---

## G6 — DB-object conformity (before creating OR altering any table / view / trigger / RPC)

The DB twin of G1. The rules are NOT restated here — they live in the app docs, and the app doc is the source of truth. **Conform, don't invent; point, don't duplicate.** Read the leaf doc first (docs-before-SQL, P11/P13), then probe, then draft. On any conflict `docs/V2-CONVENTIONS.md` wins (W5); for RLS `docs/RLS-BUNDLES.md`; for names `docs/DB-NAMING-OVERHAUL.md`. If the app doc and this checklist ever disagree, follow the doc and flag the drift.

1. **Naming (W2 / DB-NAMING).** Tables = plain snake_case nouns. Page view = `{portal}_{section}_{entity}_{purpose}` (no `_js`). Foundation view = `{entity}_{role}` (only 4 exist — resist a 5th; write page-scoped views instead). Trigger fn (`private` schema) = `{owner}_on_{watched}_{bef|aft}_{ins|upd|del}[_purpose]`, ≤63 chars. pg_trigger object = `trg_{timing}_{ops}` (never repeat the table name). Public RPC = `{verb}_{object}` (`get_`/`is_`/`has_`/`check_`). FK = `{table}_{col}_fkey`. Type file = `{entity}-{role}-{shape}.ts` all-hyphen.
2. **View safety (S11/S12).** `WITH (security_invoker = true)` ALWAYS — `CREATE OR REPLACE VIEW` silently drops it, so re-`ALTER VIEW … SET (security_invoker = true)` every time. Append-only columns (new cols at the END of the SELECT — 42P16). No shared views — every consumer page gets its own, even if the SELECT is identical. Max view-chain depth = 2.
3. **Security boilerplate.** Public RPC = `SECURITY DEFINER` + `SET search_path TO ''` + fully-qualified refs (`public.x`, never bare `x`) + `REVOKE EXECUTE … FROM PUBLIC, anon` + `GRANT EXECUTE … TO authenticated, service_role` + first line `IF (SELECT auth.uid()) IS NULL THEN RAISE EXCEPTION 'unauthorized'; END IF;`. Trigger fn = the same MINUS the auth check and MINUS REVOKE/GRANT (RLS context guarantees the caller). Hand-edit `types.ts` after any RPC signature change (#86).
4. **RLS bundles (W6).** Every NEW table gets ONE `FOR ALL` policy composed from the named catalog in `RLS-BUNDLES.md` (`is_self`, `has_perm`, `can_see_file`, `not_deleted`, `trash_visible`, `parent_visible`, …): `USING` = read rule, `WITH CHECK` = write rule. **Never inline a raw `EXISTS(user_permissions …)` or a hand-rolled owner check** — if no bundle fits, PROPOSE a new bundle in RLS-BUNDLES.md, don't inline. Always `(SELECT auth.uid())`, never bare (InitPlan caching). Never add a 2nd permissive policy — OR-merge into the existing `USING`; power-admin fast-path goes FIRST in the OR (#78). Soft-delete = `not_deleted() OR trash_visible()` inside the one policy. The §2a-RLS effective-access check still runs after any policy write. (Existing-policy rollout is half-done — see `[[discovery_rls-bundle-half-built]]`.)
5. **View registry (W3).** Every view referenced from `apps/web/` is a key in `lib/view-registry.ts`; FE reads `VIEWS.<key>`, never a raw string literal. A new view = +1 registry key + 1 migration in the SAME commit.
6. **Writes via RPC (C4/C30).** All FE writes go through `lib/mutations/` via `callRpc(db().rpc('verb_object', …))`. `grep -E "db\(\)\.from\(.*\)\.(insert|update|delete|upsert)" apps/web/lib/mutations` must return 0. A new write surface = a new RPC, never a `.from().insert()`.
7. **Soft-delete is the only delete (C31).** 13 entity families: `delete*` wrappers route to `soft_delete_*` RPCs; hard-delete is programmer-only via `/admin/trash` + `hard_delete_trash_row`. A new entity that participates in trash gets a `soft_delete_*` RPC + the `not_deleted()/trash_visible()` bundle, never a raw `DELETE`.
8. **Public / anon read path = anon-granted `SECURITY DEFINER` RPC, never a `security_invoker` view (#105).** Any surface read by the `anon` role — sitemap, robots, marketing/public pages, SSR fetches before auth — must read through a `SECURITY DEFINER` RPC `GRANT EXECUTE … TO anon` (the visibility predicate computed INSIDE the RPC, e.g. `get_public_team` = `(is_attorney OR is_partner) AND is_in_service AND NOT has_left`). A `security_invoker` view runs its base SELECT *as anon*, which has no base-table grant → `42501` → **silently** swallowed into an empty result (the sitemap emitted 0 URLs this way — not a build error, nothing caught it). Never grant `anon` a base-table SELECT to make a view work; write the RPC. **No `USING(true)`** on a multi-tenant table granted to `authenticated` (item 4's twin on the read side) — prove with `RLS-IMPERSONATE` (§2a), detect with the `qual='true'` sweep.
9. **Dormant-gate audience probe (#106 — a G5/close-checklist item, repeated here for DB phases).** When a phase ships a new perm key / `admin_scope` value / tier, COUNT the live rows that satisfy it before declaring done — `admin_scope=0` matches 0 of 90 users, so every `admin_scope=0` gate admits nobody (a silent no-op, not a feature). A zero-audience gate ships as a `CHK-` with "dormant until X populated", never a silent green. (`[[discovery_admin-scope-global-tier-dormant]]`.)

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

### 2a-RLS / `RLS-IMPERSONATE` — effective-access proof (when a phase touches RLS / grants / view-security — #47, #104)
Qual-text-matches-intent is necessary; effective-access-matches-intent is sufficient (#47). Policy text can match while a restrictive policy, a missing grant, or a `security_invoker=false` wrapping view blocks/admits the user — **policy text is a lead, not proof.** The 2026-06-02 security audit proved this at cost: report/counter/HR tables (`member_hr_records`, `advances_member_counters`, `folder_counts`, `task_counts`, `org_calendar`) shipped `USING(true)` for `authenticated`, so a customer read every firm row — invisible in the policy text, obvious under impersonation (#104).

**Cheap deterministic detector** for the whole `USING(true)` class — run on any RLS-touching wave:
```sql
select schemaname, tablename, policyname, cmd
from pg_policies
where qual = 'true' and 'authenticated' = any(roles);   -- any hit on a MULTI-TENANT table is a candidate leak
```

**`RLS-IMPERSONATE` — the both-direction proof.** Wrap in `BEGIN … ROLLBACK` (nothing persists), use the `set_config` jwt.claims form (not the older `set local request.jwt.claim.sub`), and pick a **discriminating** table — one where a customer must see SOME rows but NOT all:
```sql
begin;
set local role authenticated;
select set_config('request.jwt.claims', '{"sub":"<a-real-customer-uuid>","role":"authenticated"}', true);
select count(*) from <discriminating_view_or_table>;   -- expect the customer's OWN subset, NOT the full table
-- positive control: a row they SHOULD see returns; negative: a foreign row does NOT
rollback;
```
Record both counts. A count equal to the full-table count = a cross-tenant leak. The audit's `10-rls-effective-access.md` is the standing regression suite — re-run it after any RLS change. When a phase bundles ≥2 access-control-layer changes (RLS + grant, grant + view-security), assign sub-phase IDs (`P1a`, `P1b`) and verify each layer independently (§2b phase atomicity). (lex memory `[[discovery_rls-impersonation-harness-mcp]]`, `[[discovery_qual-true-rls-cross-tenant-leaks]]`.)

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

## Applying migrations off the failed preview pipeline + concurrent-actor git isolation (#95 #96 #97 #99)

The lex_council Supabase **git→preview auto-pipeline is `MIGRATIONS_FAILED`** (since 2026-05-23 — `[[project_supabase-migrations-applied-via-mcp-not-pipeline]]`). "Push a feature branch → auto-spawn a preview" does NOT work here; assuming it does burns turns on a build that never lands. **Re-confirmed 2026-06-02 (#96/E5): the breakage is *reliable*, not intermittent — even a fresh `create_branch` comes up `MIGRATIONS_FAILED` AND dataless, so you cannot validate on a preview at all.** Stop treating "spin a branch to validate" as an option; the validation substitute is a prod `BEGIN … <DDL/DML> … ROLLBACK` dry-run (nothing persists), paired with the `RLS-IMPERSONATE` harness (§2a) for any RLS change. (`[[discovery_supabase-preview-branch-still-broken]]`.) The proven write path (Campaigns B + E, 2026-05-29, both shipped clean):

1. **Isolate git in a WORKTREE, never `git checkout -b` (#95).** A concurrent actor (#33, `[[discovery_concurrent-migration-actor]]`) keeps dozens of uncommitted FE files + interleaved `20260529*` migrations in the MAIN working copy; switching HEAD there can hijack/co-mingle their commits, and a session-end auto-commit bundles files you never touched. `git worktree add .claude/worktrees/<name> -b <branch>` (branch from HEAD) gives a clean isolated tree holding only your new files. Commit by explicit path, prove the staged set (`git diff --cached --name-only`), push, PR. Run all git INSIDE `lex_council/` (submodule; the workspace root has no remote — #87).
2. **Apply idempotent/reversible migrations via MCP `apply_migration` after showing the SQL (#96).** PDAAV still holds: G3 re-probe live → show the exact SQL (P3) → `apply_migration` to prod (project_id `bqgrpnsvplvicnmzxwkm`, G2) → ground-truth SELECT + `get_advisors`. Make the DDL idempotent (`IF NOT EXISTS` / `CREATE OR REPLACE`) so a future pipeline re-apply is a no-op. **Commit the migration FILE to the branch for record** even though it was applied out-of-band. A *manual* `create_branch` (fresh isolated project_ref, ~$0.01344/hr) still works if a real preview is genuinely needed — don't burn money retrying the failed auto-pipeline.
3. **Reversibility gates the cadence (#97).** Reversible `CREATE OR REPLACE` (function/view/trigger bodies, additive/idempotent DDL) proceeds with the SQL shown even under `autonomous`. An **irreversible `DROP` or a money-/auth-adjacent bulk refactor ALWAYS gets the full SQL shown + an explicit go**, carries `RESTRICT` (never `CASCADE` on faith — the error lists any new dependent), and runs a **delete-time LIVE re-grep** (FE + `view-registry.ts` + `pg_depend` + `supabase/migrations/`+`functions/`) at the moment of the drop, not from the plan's stale list. Campaign B dropped 16 reversible orphan views + 3 fns under show-SQL but KEPT its 3 `*_bak_20260527_pool` data tables for "a moment of certainty" (irreversible data loss). Pairs with #14 (candidate-not-committed deletions).
4. **`gh` may be absent (#99).** This machine has no `gh` CLI — don't fail the handoff: push the branch and hand the user the `github.com/<org>/<repo>/pull/new/<branch>` URL (lex: `github.com/Attax-io/lex_council/pull/new/<branch>`).

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

### execute_sql in a begin/rollback swallows trigger RAISE (#85)
Testing whether a trigger BLOCKS a write by wrapping it `begin; <dml>; rollback;` in one `execute_sql` returns `[]` (clean) whether the trigger raised or not — the rollback discards the RAISE, so you cannot tell "blocked" from "allowed". Use a plpgsql sub-transaction that captures the outcome and surfaces it as a NOTICE, then raise to discard side effects:
```sql
do $$ begin
  begin
    <dml that should be blocked>;
    raise notice 'PROBE: not blocked';
  exception when others then
    raise notice 'PROBE: blocked — %', sqlerrm;
  end;
  raise exception 'probe rollback';   -- discard any side effects
end $$;
```
Read the NOTICE from the MCP response / `get_logs`. Lex memory `[[discovery_execute-sql-swallows-raise-in-rollback]]`.

### Hand-edit types.ts for small schema changes — never regen-overwrite (#86)
`supabase gen types … > types.ts` reformats the WHOLE file (generator style diverges from the committed file) → a 19-line change becomes a ~95K-line diff even after prettier (one case: 48942+/46666− vs a 19+/9− hand-edit). For a small change (a column, an RPC signature) hand-edit the affected `Row`/`Insert`/`Update`/`Functions` blocks. Watch substring collisions when find-replacing a column name (`ppl_link` ⊂ `b_ppl_link`). Reserve a full regen for large multi-object migrations where the diff is unavoidable. Lex memory `[[feedback_supabase-typegen-reformats-whole-file]]`.

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
