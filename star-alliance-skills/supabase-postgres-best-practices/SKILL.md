---
name: supabase-postgres-best-practices
description: Postgres performance optimization and best practices from Supabase. Use this skill when writing, reviewing, or optimizing Postgres queries, schema designs, or database configurations.
license: MIT
metadata:
  author: supabase
  version: "1.3.0"
  organization: Supabase
  date: January 2026
  abstract: Comprehensive Postgres performance optimization guide for developers using Supabase and Postgres. Contains performance rules across 8 categories, prioritized by impact from critical (query performance, connection management) to incremental (advanced features). Each rule includes detailed explanations, incorrect vs. correct SQL examples, query plan analysis, and specific performance metrics to guide automated optimization and code generation.
type: Skill

---
# Supabase Postgres Best Practices

Comprehensive performance optimization guide for Postgres, maintained by Supabase. Contains rules across 8 categories, prioritized by impact to guide automated query optimization and schema design.

## When to Apply

Reference these guidelines when:
- Writing SQL queries or designing schemas
- Implementing indexes or query optimization
- Reviewing database performance issues
- Configuring connection pooling or scaling
- Optimizing for Postgres-specific features
- Working with Row-Level Security (RLS)

## Rule Categories by Priority

| Priority | Category | Impact | Prefix |
|----------|----------|--------|--------|
| 1 | Query Performance | CRITICAL | `query-` |
| 2 | Connection Management | CRITICAL | `conn-` |
| 3 | Security & RLS | CRITICAL | `security-` |
| 4 | Schema Design | HIGH | `schema-` |
| 5 | Concurrency & Locking | MEDIUM-HIGH | `lock-` |
| 6 | Data Access Patterns | MEDIUM | `data-` |
| 7 | Monitoring & Diagnostics | LOW-MEDIUM | `monitor-` |
| 8 | Advanced Features | LOW | `advanced-` |

## How to Use

Read individual rule files for detailed explanations and SQL examples:

```
references/query-missing-indexes.md
references/query-partial-indexes.md
references/_sections.md
```

Each rule file contains:
- Brief explanation of why it matters
- Incorrect SQL example with explanation
- Correct SQL example with explanation
- Optional EXPLAIN output or metrics
- Additional context and references
- Supabase-specific notes (when applicable)

## References

- https://www.postgresql.org/docs/current/
- https://supabase.com/docs
- https://wiki.postgresql.org/wiki/Performance_Optimization
- https://supabase.com/docs/guides/database/overview
- https://supabase.com/docs/guides/auth/row-level-security

## Lex Council Additions

Rules harvested from Lex Council CLAUDE.md W6 and the 287-migration backend codebase. These are mandatory in the Lex Council Supabase project on top of (not instead of) the Supabase upstream practices above.

### security-rls-initplan-caching

Always wrap `auth.uid()` in a subquery — `(SELECT auth.uid())` — inside every RLS policy USING and WITH CHECK expression. Never write the bare `auth.uid()` call.

**Why:** the subquery form makes Postgres treat the auth lookup as an `initplan` — evaluated once per query, cached, and reused for every row. The bare form re-evaluates per row, which on large tables (notifications, fd_access, audit tables) becomes the dominant cost. Every policy in the W6 audit was migrated from bare → `(SELECT auth.uid())` form and the hot-path queries dropped from O(rows) auth calls to O(1).

```sql
-- WRONG — bare auth.uid(), per-row re-evaluation on large tables
CREATE POLICY read_own ON public.documents FOR SELECT
  USING user_id = auth.uid();

-- RIGHT — initplan, cached once per query
CREATE POLICY read_own ON public.documents FOR SELECT
  USING user_id = (SELECT auth.uid());
```

This rule applies to **every** RLS policy body in every migration, including new ones.

### security-definer-search-path-empty

Every `SECURITY DEFINER` function — RPC body, trigger function, helper — must pin `SET search_path TO ''` (empty string, not a schema list) and schema-qualify **every** reference.

**Why:** `SET search_path TO ''` forces schema-qualified names everywhere; without it an attacker who can create objects in a search-path schema can shadow `public` calls and hijack the definer's elevated privileges. Pinning to a list like `'public', 'private'` was the old convention and is now banned — empty is the only safe default.

```sql
CREATE OR REPLACE FUNCTION private.my_definer_fn()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO ''          -- empty, not 'public, private'
AS $$
BEGIN
  -- schema-qualify EVERY reference
  INSERT INTO public.notifications (n_user_id, n_kind)
  VALUES ((SELECT auth.uid()), 'entity.event.kind');
  RETURN NEW;
END;
$$;
```

`SET search_path TO 'public', 'private'` — the old S7 form — must be migrated to `SET search_path TO ''` on every existing SECURITY DEFINER object before the next security audit.

### rpc-privilege-lockdown

Every RPC (function callable from PostgREST / `.rpc()`) must end with an explicit REVOKE/GRANT block — no exception, including throwaway helpers.

```sql
REVOKE EXECUTE ON FUNCTION public.my_rpc(args) FROM PUBLIC;
REVOKE EXECUTE ON FUNCTION public.my_rpc(args) FROM anon;
GRANT EXECUTE ON FUNCTION public.my_rpc(args) TO authenticated;
GRANT EXECUTE ON FUNCTION public.my_rpc(args) TO service_role;
```

Postgres grants `EXECUTE` to `PUBLIC` by default, and Supabase's `anon` role inherits from `PUBLIC`. Without the revoke, an unauthenticated request can call any function in the `public` schema. Never skip this block — past audits found multiple functions reachable by `anon` because the revoke was omitted "temporarily".

### views-security-invoker-mandatory

Every CREATE VIEW statement — and every CREATE OR REPLACE VIEW follow-up — must set `security_invoker = true`. SECURITY DEFINER views are banned in Lex Council.

```sql
CREATE OR REPLACE VIEW public.foo_js
WITH (security_invoker = true)
AS SELECT ... FROM public.foo;

ALTER VIEW public.foo_js SET (security_invoker = true);  -- mandatory follow-up; see add-new-view skill
```

The `add-new-view` skill's Step 4 covers the `CREATE OR REPLACE` trap (reloptions silently dropped). This rule also covers the **initial** create — never ship a view without `security_invoker = true` baked in from the start.

### rls-policy-bundle-composition (one FOR ALL per table)

Every table gets **one** `FOR ALL` RLS policy that composes read + write + delete rules as a named bundle — not multiple `FOR SELECT` / `FOR INSERT` / `FOR UPDATE` / `FOR DELETE` policies with ad-hoc inline `EXISTS` checks scattered across migrations.

**Structure:**
- `USING` clause = read rule (used by SELECT and DELETE).
- `WITH CHECK` clause = write rule (used by INSERT and UPDATE).
- The policy name encodes the bundle — e.g. `readwrite_owner`, `read_admin_write_owner`, `read_members_write_self`.

```sql
-- RIGHT — one FOR ALL bundle, USING = read, WITH CHECK = write
CREATE POLICY readwrite_owner ON public.files
  FOR ALL
  TO authenticated
  USING       (file_owner_id = (SELECT auth.uid()))
  WITH CHECK  (file_owner_id = (SELECT auth.uid()));

-- WRONG — multiple per-op policies with inline EXISTS
-- (creates 0006_multiple_permissive_policies lint, leaks intent across migrations)
```

This keeps policy authoring legible in one place per table, makes auditing fast (one policy per table = one review point), and aligns with the principle that all access to a table — read or write — flows through the same authorization check.

### rpc-auth-guard-template

Every public RPC that acts on behalf of a user must begin with the exact auth-guard incantation as its **first executable line** — above any DECLARE, above any variable assignment:

```sql
IF (SELECT auth.uid()) IS NULL THEN RAISE EXCEPTION 'unauthorized'; END IF;
```

Notes:
- Use `(SELECT auth.uid())`, not bare `auth.uid()` — same initplan reasoning as the RLS rule above.
- Use the literal string `'unauthorized'` (lowercase, no punctuation) — it's greppable in pg_stat_statements and in notification `p_source` tags.
- This guard is for user-facing RPCs. Triggers fired by system events (crons, cascade chains) MAY skip the caller's `auth.uid()` check but must still pin `search_path TO ''` and run as `SECURITY DEFINER`.

### fk-constraint-names-reflect-current-table

Foreign-key constraint names must use the **current** table name, not a stale name from before a rename: `{table}_{col}_fkey`.

**Why this matters:** Postgres uses the constraint name as the FK's identity. After a rename, a constraint named `old_table_old_col_fkey` still works but breaks:
- pg_dump output (constraint names contradict the schema)
- future RENAME TABLE (the old name lingers in error messages)
- observability tools that key off constraint names
- the `db-rename-sweep` skill's surface inventory

Always:
1. Generate the FK with `{current_table_name}_{col_name}_fkey`.
2. After any RENAME TABLE migration, grep for FK names that don't match and rename them in a follow-up migration.
3. The `db-rename-sweep` skill's 14-surface checklist should include "all FK constraint names match current table+column names".

### data-resolve-display-values-live (never copy a name out of its source)

Never denormalize a human-readable value (an owner's name, a title, a label) into every row alongside its foreign key. Store **only** the FK; resolve the display value live in a view via JOIN.

**Why:** a copied-out value drifts the instant its source changes. In Lex Council an owner's display name was denormalized across ~870 rows/files. When the owner renamed, the `owner_id` UUID stayed correct everywhere but the copied name lagged in all ~870 places — a silent, app-wide inconsistency with no single fix-point. The UUID never drifts because it is the identity; the name drifts because it was a copy.

```sql
-- WRONG — owner_name copied into every row; drifts when the owner renames
CREATE TABLE public.files (
  id uuid PRIMARY KEY,
  owner_id uuid REFERENCES public.users(id),
  owner_name text          -- stale copy; ~870 rows lagged after one rename
);

-- RIGHT — store the FK only; resolve the name live in the JS view
CREATE OR REPLACE VIEW public.files_js
WITH (security_invoker = true)
AS SELECT f.*, u.display_name AS owner_name
   FROM public.files f
   JOIN public.users u ON u.id = f.owner_id;
```

The name is now always current because it is read, not stored. Under `security_invoker = true` (mandatory — see the views rule above) the joined source table must be readable by the invoker; that is the normal case for a display field the caller is already entitled to see.

### security-rls-delegation-via-definer-helper (don't delegate RLS through an EXISTS subquery)

When a child table's RLS check depends on access to a **parent** table that itself has RLS, do not delegate the check with an inline `EXISTS (SELECT 1 FROM parent WHERE …)`. Postgres re-applies the parent's RLS *inside* that subquery, so every child row triggers a second full RLS evaluation — a measured ~380ms/query on hot paths. Delegate instead through a `SECURITY DEFINER` helper in `private.`: one RLS-free lookup per row instead of a full RLS re-eval per row.

**Why the helper bypasses the parent's RLS:** a `SECURITY DEFINER` function runs as its **owning role**, and in the Supabase migration workflow that owner is `postgres`, which is not subject to a table's RLS unless the table has `FORCE ROW LEVEL SECURITY` set. So the helper reads the parent directly, without re-triggering that parent's policies. This only holds if the helper is owned by such a role and the parent is not `FORCE`-RLS — get either wrong and the check silently no-ops and the ~380ms never drops.

```sql
-- WRONG — EXISTS against an RLS-protected parent = double RLS eval (~380ms/query)
CREATE POLICY read_members ON public.documents
  FOR ALL TO authenticated
  USING (EXISTS (SELECT 1 FROM public.projects p
                 WHERE p.id = documents.project_id));   -- projects' RLS runs again here

-- RIGHT — a definer helper checks membership without re-triggering the parent's RLS
CREATE OR REPLACE FUNCTION private.can_access_project(p_project_id uuid)
RETURNS boolean
LANGUAGE sql
SECURITY DEFINER
SET search_path TO ''
STABLE
AS $$
  SELECT EXISTS (SELECT 1 FROM public.projects p
                 WHERE p.id = p_project_id
                   AND p.owner_id = (SELECT auth.uid()));
$$;

CREATE POLICY read_members ON public.documents
  FOR ALL TO authenticated
  USING (private.can_access_project(project_id));
```

This is the performance-and-mechanism companion to `rls-policy-bundle-composition` above (which bans inline `EXISTS` on legibility grounds and points at the `bundled-rls` skill): the *reason* the ban matters on parent-linked tables is the double RLS eval, and the *fix* is the definer helper — not a denormalized owner column (that would reintroduce the copy-out drift banned by the rule above). The helper still obeys every SECURITY DEFINER rule: `SET search_path TO ''`, schema-qualified references, `(SELECT auth.uid())`.

### rpc-private-engine-public-wrapper (the split agents keep reverse-engineering)

Business logic lives in a `private.` `SECURITY DEFINER` **engine** function; the `public.` RPC is a thin **wrapper** that applies the caller-facing rules and calls the engine. Agents rebuild this split from scratch every time it appears — it is the standing convention, document it once here.

- **`public.<name>` wrapper** — the only thing PostgREST/`.rpc()` reaches. It carries the auth guard (`rpc-auth-guard-template`) as its first executable line and ships with the REVOKE/GRANT block (`rpc-privilege-lockdown`). It validates inputs, then delegates.
- **`private.<name>_engine`** — the actual work: multi-table writes, cascades, computed effects. Unreachable from PostgREST (the `private` schema is not exposed), so it is trusted; it never repeats the caller's auth guard but still pins `search_path TO ''` and schema-qualifies everything.

```sql
-- private engine: does the work, trusted, not caller-reachable
CREATE OR REPLACE FUNCTION private.archive_file_engine(p_file_id uuid)
RETURNS void
LANGUAGE plpgsql SECURITY DEFINER SET search_path TO ''
AS $$
BEGIN
  UPDATE public.files SET archived_at = now() WHERE id = p_file_id;
  INSERT INTO public.audit (a_kind, a_file_id) VALUES ('file.archived', p_file_id);
END;
$$;

-- public wrapper: auth guard + delegate; REVOKE/GRANT block follows (see rpc-privilege-lockdown)
CREATE OR REPLACE FUNCTION public.archive_file(p_file_id uuid)
RETURNS void
LANGUAGE plpgsql SECURITY DEFINER SET search_path TO ''
AS $$
BEGIN
  IF (SELECT auth.uid()) IS NULL THEN RAISE EXCEPTION 'unauthorized'; END IF;
  PERFORM private.archive_file_engine(p_file_id);
END;
$$;
```

The wrapper is exactly where `rpc-auth-guard-template` and `rpc-privilege-lockdown` get applied; the engine is where they deliberately are not. Keeping the two in separate schemas makes "what is reachable by a caller" a schema-level fact, not a per-function audit.

## Lex Council Security Additions
Rules extracted from a 287-migration production Supabase codebase (2026).

### (SELECT auth.uid()) — always wrap, never bare
In RLS policy bodies, NEVER use bare auth.uid(). Always:
  USING ((SELECT auth.uid()) = owner_id)
Bare auth.uid() re-evaluates per row. The initplan form evaluates once per query. Critical performance difference on large tables.

### SECURITY DEFINER + search_path lock
Every SECURITY DEFINER object must include SET search_path TO '' and reference all tables fully-qualified: public.my_table, never bare my_table. Missing search_path allows schema injection.

### REVOKE anon execute on all RPCs
  REVOKE EXECUTE ON FUNCTION public.my_rpc FROM PUBLIC, anon;
  GRANT EXECUTE ON FUNCTION public.my_rpc TO authenticated, service_role;
First line of every RPC body: IF (SELECT auth.uid()) IS NULL THEN RAISE EXCEPTION 'unauthorized'; END IF;

### security_invoker = true on every view
  CREATE OR REPLACE VIEW public.my_view WITH (security_invoker = true) AS ...
SECURITY DEFINER views bypass RLS entirely — banned.

### One FOR ALL policy per table
USING = read predicate. WITH CHECK = write predicate. Raw inline EXISTS(...) in policy bodies is banned — use named bundle predicates (see bundled-rls skill).

### FK constraint naming after renames
{table}_{col}_fkey using the NEW table name — never stale names after a rename.

## Changelog

| Version | Date | Change |
|---|---|---|
| 1.3.0 | 2026-07-12 | Lex Council patterns (4-session evidence): `data-resolve-display-values-live` (denormalized copy-out drift — an owner name lagged its UUID across ~870 files; fix = resolve live in the view); `security-rls-delegation-via-definer-helper` (inline EXISTS against an RLS parent = double RLS eval ~380ms/query; fix = SECURITY DEFINER helper); `rpc-private-engine-public-wrapper` (private-engine/public-wrapper RPC convention). |
| 1.2.0 | 2026-06-30 | Lex Council additions: initplan `(SELECT auth.uid())`, `SET search_path TO ''`, RPC REVOKE/GRANT, security_invoker mandatory, one FOR ALL RLS bundle, RPC auth-guard incantation, FK naming `{table}_{col}_fkey`. Source: W6 + 287-migration audit. |
| 1.1.1 | Jan 2026 | Upstream Supabase content (unchanged). |
