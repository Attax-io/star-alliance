---
name: supabase-postgres-best-practices
description: Postgres performance optimization and best practices from Supabase. Use this skill when writing, reviewing, or optimizing Postgres queries, schema designs, or database configurations.
license: MIT
metadata:
  author: supabase
  version: "1.2.0"
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

## Changelog

| Version | Date | Change |
|---|---|---|
| 1.2.0 | 2026-06-30 | Lex Council additions: initplan `(SELECT auth.uid())`, `SET search_path TO ''`, RPC REVOKE/GRANT, security_invoker mandatory, one FOR ALL RLS bundle, RPC auth-guard incantation, FK naming `{table}_{col}_fkey`. Source: W6 + 287-migration audit. |
| 1.1.1 | Jan 2026 | Upstream Supabase content (unchanged). |

