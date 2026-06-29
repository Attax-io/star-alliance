---
name: add-new-view
description: "End-to-end procedure for creating or revising a view in the Lex Council Supabase backend. Use whenever the user asks to create a view, add a _js view, rewrite a view, fix a SECURITY DEFINER view lint error, update view columns, rename a view, or drop a view. Also trigger on mentions of security_invoker, CREATE OR REPLACE VIEW, get_advisors security, VIEW DEFINER, view consumer, or any task that involves the pg_views or VIEWS-CATALOG surface. This skill exists because two traps have each caused production regressions: (1) CREATE OR REPLACE VIEW silently drops security_invoker — every view rewrite must be followed by ALTER VIEW SET (security_invoker=true); (2) DROP VIEW ... CASCADE silently drops every downstream dependent — always enumerate dependents before dropping. Without this skill, Claude reliably hits one of these two traps."
version: 1.1.0
---

# Adding or Revising a View in Lex Council

## Step 1: Read VIEWS-CATALOG before touching anything

```
lex_council/docs/architecture/backend/VIEWS-CATALOG.md
```

Confirm: does a view for this purpose already exist? If so, alter it in place — don't create a duplicate. Check its consumers (components, hooks, other views) before changing its shape.

## Step 2: Naming convention

Views follow `{entity}_{purpose}_js`:

| Segment | Meaning | Examples |
|---|---|---|
| `{entity}` | The primary table or domain abbreviated | `cm` (council_members), `fd` (fd), `td` (tasks) |
| `{purpose}` | What the view computes or who it serves | `ap` (admin perms), `hr` (HR data), `op` (operations) |
| `_js` | Suffix for all Supabase views consumed by the frontend | always |

Examples: `cm_ap_js`, `fd_access_js`, `cm_hr_js`, `cm_op_js`, `n_member_feed`.

Do not invent a new naming scheme. If none of the existing entity prefixes fit, ask Atta.

## Step 3: S11 decision — which security model?

Every new view must go through this three-path decision from S11:

### Path 1 (default): `security_invoker = true`

Ship the view with `WITH (security_invoker = true)`. The caller's RLS on every source table applies transparently. This is correct-by-construction.

```sql
CREATE OR REPLACE VIEW public.my_view
WITH (security_invoker = true)
AS
  SELECT ...
  FROM public.source_table st
  ...;

-- MANDATORY — CREATE OR REPLACE silently drops security_invoker
ALTER VIEW public.my_view SET (security_invoker = true);
```

Run `get_advisors security` after. Expect zero `security_definer_view` errors for this view.

### Path 2: Widen source-table RLS (if Path 1 blocks intended callers)

If the admin audience for this view can't see the source table's rows via their existing RLS:

- **Merge** an admin-flag OR branch into the existing SELECT policy on the source table. Do NOT add a second permissive policy — that triggers lint `0006_multiple_permissive_policies`.
- Confirm with `get_advisors` after the merge.
- Then ship the view as Path 1.

### Path 3: SECURITY DEFINER RPC (last resort)

Only when widening source-table RLS would enlarge the access surface on `fd_access` / `fd_access_js` in ways that risk recursion (see `rls-recursion-antipatterns`).

- Write a `SECURITY DEFINER` function in the `private` schema.
- Pin `SET search_path TO ''` — schema-qualify every reference as `public.tablename`.
- Add admin-flag gate at top of function body.
- Apply S8: `REVOKE EXECUTE FROM PUBLIC; GRANT EXECUTE TO authenticated, service_role;`
- Drop the view (or don't create one). Frontend calls via `.rpc()`.

Never ship a `SECURITY DEFINER` view with an in-view admin-gate `WHERE EXISTS (admin_perms …)` — it leaves the Supabase lint ERROR in place.

## Step 4: The security_invoker trap — DO NOT SKIP

`CREATE OR REPLACE VIEW` does **not** preserve `reloptions`. If you rewrite an existing view that had `security_invoker = true`, the flag is silently dropped and the view reverts to running as the `postgres` owner (SECURITY DEFINER behaviour). Supabase advisor will re-flag it.

**After every `CREATE OR REPLACE VIEW`, always run:**

```sql
ALTER VIEW public.my_view SET (security_invoker = true);
```

This applies even to tiny one-column rewrites. The trap has been hit multiple times — see memory `feedback_view_security_invoker_not_preserved`.

Then run `get_advisors security` and confirm zero `0010_security_definer_view` errors for this view.

## Step 5: Check downstream dependents before DROP VIEW ... CASCADE

`DROP VIEW ... CASCADE` silently drops every view, function, or other object that depends on this view. Supabase does not warn you; you find out when production queries start returning errors.

Before any `DROP VIEW`:

```sql
-- Find all dependents
SELECT dependent_ns.nspname || '.' || dependent_view.relname AS dependent_view
FROM pg_depend
JOIN pg_rewrite ON pg_depend.objid = pg_rewrite.oid
JOIN pg_class AS dependent_view ON pg_rewrite.ev_class = dependent_view.oid
JOIN pg_class AS source_view ON pg_depend.refobjid = source_view.oid
JOIN pg_namespace AS dependent_ns ON dependent_view.relnamespace = dependent_ns.oid
WHERE source_view.relname = 'my_view'
  AND source_view.relkind = 'v'
  AND dependent_view.oid != source_view.oid;

-- Also check via information_schema
SELECT view_schema, view_name
FROM information_schema.view_column_usage
WHERE table_name = 'my_view'
  AND view_name != 'my_view';
```

If any dependents appear, recreate them in the same migration — same transaction, in the correct order (parent before child). Include `WITH (security_invoker = true)` and the follow-up `ALTER VIEW` on each recreated dependent.

## Step 6: Frontend consumers

After creating or altering a view, check whether the frontend imports its columns via TypeScript types. The generated types live in:

```
apps/web/types/
```

If column names or types changed, regenerate types:

```bash
# From repo root
supabase gen types typescript --project-id <ref> > apps/web/types/supabase.ts
```

Or use the `generate_typescript_types` MCP tool. Then update any frontend files that destructure the old columns.

## Step 7: Vault log

Every view creation or revision is a P8 change. Log it at `docs/vault-logs/YYYY-MM-DD_slug.md`. Include:

- View name and what it computes
- Which source tables it joins
- Security model chosen (Path 1/2/3) and why
- Result of `get_advisors security` after the change
- Any downstream dependents found and how they were handled
- Frontend type impact

Use the `vault-log-writer` skill for the log structure.

## Self-check before declaring done

- [ ] View name follows `{entity}_{purpose}_js` convention
- [ ] S11 path selected and documented
- [ ] `WITH (security_invoker = true)` in CREATE statement
- [ ] `ALTER VIEW ... SET (security_invoker = true)` run after every `CREATE OR REPLACE`
- [ ] `get_advisors security` shows zero `0010_security_definer_view` for this view
- [ ] Downstream dependents checked before any DROP; recreated if needed
- [ ] Frontend types regenerated if column shape changed
- [ ] Vault log written

## Why this skill exists

On 2026-04-23 a `CREATE OR REPLACE VIEW` on `fd_access_js` silently dropped its `security_invoker` flag. The view reverted to SECURITY DEFINER behaviour for the rest of the session. On 2026-05-01 a `DROP VIEW ... CASCADE` on a view silently took out two downstream views — neither was listed in the migration plan. Both traps are 30-second checks that this skill makes habitual.
