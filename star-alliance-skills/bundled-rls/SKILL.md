---
name: bundled-rls
description: "Write Postgres Row-Level Security as composable named bundles, not ad-hoc inline policies. One FOR ALL policy per table (USING for read, WITH CHECK for write) composed from a named bundle catalog (is_self, has_perm, can_see_file, not_deleted, trash_visible, parent_visible). Bundles are reusable, indexed, and (SELECT auth.uid())-cached. Change one bundle, every table that uses it inherits the fix — no more 199 inline policies to audit. Use for: 'write a new RLS policy', 'standardize our policies', 'compose a bundle', 'replace inline EXISTS', 'audit RLS coverage', 'add FOR SELECT visibility'. Pairs with add-admin-permission, add-new-view, schema-evolution, supabase-postgres-best-practices."
metadata:
  version: 1.0.0
type: Skill
---

# Bundled RLS — composable Row-Level Security

Raw RLS policies inline in migrations become unmaintainable fast. One project reached 199
policies on 100 tables — 199 different security rules to audit, 199 chances for an inline
`EXISTS(SELECT 1 FROM user_permissions …)` to drift from the equivalent check on the next
table, 199 chances for `auth.uid()` to be re-evaluated per row instead of once per query.

Bundled RLS replaces this with a **named catalog of reusable predicates**. Every policy
composes from the catalog; every table gets one `FOR ALL` policy by default; changing a
bundle changes every table that uses it. The security model lives in **one doc**, not
199 migrations.

## What it solves

- **Drift:** Inline policies on 100 tables re-implement the same "is owner" or "has admin"
  predicate with subtle variations. The catalog eliminates the duplication.
- **Audit:** "What does our RLS actually do?" has a one-document answer instead of a
  migration archaeology expedition.
- **Performance:** The `(SELECT auth.uid())` initplan cache trick and the indexed-join
  convention are written once in the bundle doc, not decided 199 times.
- **Refactors:** Renaming a column used by an RLS predicate is one migration; every policy
  in the catalog picks up the change automatically on the next `CREATE OR REPLACE`.

## The golden rules

1. **One `FOR ALL` policy per table, by default.** The `USING` clause is the **read**
   predicate; the `WITH CHECK` clause is the **write** predicate. Same composition both
   sides unless the table genuinely needs different visibility for SELECT.
2. **The only sanctioned exception: a table whose SELECT visibility genuinely differs from
   UPDATE/DELETE visibility** (e.g., an audit table you can read but never write) gets a
   minimal, documented second `FOR SELECT` policy — **listed by name in the central bundle
   catalog doc**. No undocumented second policies, ever.
3. **Never inline `EXISTS(SELECT 1 FROM user_permissions …)` directly in a policy body.**
   If no existing bundle fits the predicate you need, **propose a new bundle first** —
   add it to the catalog, then compose from it. Inline predicates are exactly the drift
   the catalog exists to prevent.
4. **Always `(SELECT auth.uid())`, never bare `auth.uid()`.** Postgres evaluates the
   `SELECT` subquery **once per query** (the *initplan cache*), not once per row.
   `auth.uid()` re-evaluates per row and silently tanks performance.

## Bundle catalog pattern

Define named predicates in **one central doc** (e.g. `docs/RLS-BUNDLES.md`). The catalog
is the single source of truth for what every RLS policy in the project does.

```
- is_self:                   (SELECT auth.uid()) = user_id
- has_perm(domain):          EXISTS(SELECT 1 FROM user_permissions
                                WHERE uid = (SELECT auth.uid())
                                  AND domain = domain AND active)
- can_see_file(file_id):     EXISTS(SELECT 1 FROM file_access
                                WHERE uid = (SELECT auth.uid())
                                  AND file_id = file_id)
- not_deleted:               deleted_at IS NULL
- trash_visible:             not_deleted
                           OR (SELECT is_admin FROM profiles
                                WHERE id = (SELECT auth.uid()))
- parent_visible(parent_id): parent_id IN (SELECT id FROM parent_table
                                WHERE [can_see_parent_predicate])
```

Every bundle name is a verb — the read of the policy reads like English:
`is_self AND not_deleted`, `can_see_file(file_id) AND has_perm('tasks.write')`.

## Policy composition examples

```sql
-- Simple: only the owner can see/write their own records.
ALTER TABLE public.user_notes ENABLE ROW LEVEL SECURITY;
CREATE POLICY rls ON public.user_notes FOR ALL
  USING       (is_self)
  WITH CHECK  (is_self);

-- File-scoped: visibility through file_access, write additionally needs tasks.write.
CREATE POLICY rls ON public.file_tasks FOR ALL
  USING       (can_see_file(file_id) AND not_deleted)
  WITH CHECK  (can_see_file(file_id) AND has_perm('tasks.write'));

-- Admin override: admins see everything, including trash.
CREATE POLICY rls ON public.documents FOR ALL
  USING       (can_see_file(file_id) AND trash_visible)
  WITH CHECK  (can_see_file(file_id));
```

Every policy is named `rls` on the table. There is only one policy per table. The
predicate is the bundle composition; the doc is the catalog. That's the whole model.

## Rolling out to existing tables

A four-phase migration, never a big-bang rewrite:

1. **Audit all existing policies.** Categorize each by which bundle(s) it matches. Build
   a coverage table: *table · current policy · equivalent bundle composition · action*.
2. **Per-table migration:** Replace each inline policy with bundle composition. Drop the
   old policy, `CREATE POLICY rls …` with the composed predicate. Test against an
   authenticated user, another user, anon, and the `service_role` (which bypasses RLS —
   confirm this is the intended behaviour).
3. **Track coverage in the central catalog.** A checked list grows with the rollout:
   `[x] user_notes   [x] file_tasks   [x] documents   [ ] invoices`. Every new table
   lands checked.
4. **Test per migration.** After each table is migrated, run the four-user test (auth /
   other / anon / service_role). The catalog's coverage list is the to-do.

## Performance notes

- `(SELECT auth.uid())` is evaluated **once per query** via the Postgres initplan cache,
  not once per row. Bare `auth.uid()` re-evaluates per row — silent perf killer.
- `EXISTS` predicates with indexed columns are fast. Every bundle's join column
  (`uid`, `file_id`, `parent_id`) must have an index. Bundles that call other tables
  must have those tables indexed on the join key.
- The `(SELECT is_admin FROM profiles WHERE id = (SELECT auth.uid()))` form inside
  `trash_visible` is safe because `profiles.id` is the PK — index lookup, not scan.
- Avoid `IN (SELECT … FROM large_table …)` without an index on the inner table's
  filter column. `parent_visible` only scales if `parent_table`'s predicate is indexed.

## Security checklist before enabling RLS on a new table

Every new `ENABLE ROW LEVEL SECURITY` migration MUST clear this list before commit:

- [ ] `ALTER TABLE public.<t> ENABLE ROW LEVEL SECURITY;`
- [ ] One `FOR ALL` policy named `rls` using bundle composition from the catalog
- [ ] Tested with: authenticated owner (should see own rows), other authenticated user
      (should see nothing), `anon` (should see nothing), `service_role` (bypasses RLS —
      verify this is intentional and documented)
- [ ] Each bundle referenced by the policy has its join column indexed
- [ ] Policy added to the central catalog's coverage list (`[x] <table>`)
- [ ] No raw `auth.uid()` — every call wrapped in `(SELECT auth.uid())`
- [ ] No inline `EXISTS` that could have been a bundle — if a new predicate was needed,
      the bundle is in the catalog first, the policy second

## When to break the rules

- **Auditing / append-only tables** legitimately need a second `FOR SELECT` policy (read
  broadly, write narrowly). Document it in the catalog's *Exceptions* section.
- **Tables with no concept of a current user** (cron-driven, system-managed) may bypass
  RLS entirely — but only if the `service_role` is the only writer, and only with an
  explicit comment in the migration explaining why.
- **Always `WITH CHECK = true` and `USING = false`** are not shortcuts — they are bugs
  wearing a costume. A policy that allows everything and checks nothing is not a policy.

## Reference doc

The bundle catalog is **one Markdown file** at the repo root or under `docs/` (project
convention). It lists every bundle, every table that uses it, and the per-table coverage
status. Treat it like a schema migration log — append-only, reviewed in PRs, audited
alongside the RLS advisor.