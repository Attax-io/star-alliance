---
type: Document
timestamp: 2026-06-28T00:00:00Z
---

# Postgres Performance Best Practices

Apply these rules whenever writing queries, designing schema, or debugging slow operations. They represent the most common Postgres performance traps in Supabase applications.

## RLS Performance (CRITICAL — up to 100x speedup)

Auth functions like `auth.uid()` are called **once per row** by default. Wrapping them in a `SELECT` subquery makes Postgres evaluate them once and cache the result.

```sql
-- WRONG: auth.uid() called for every row in the table
create policy orders_policy on orders
  using (auth.uid() = user_id);

-- CORRECT: evaluated once, result cached for the query
create policy orders_policy on orders
  using ((select auth.uid()) = user_id);
```

For complex multi-table checks, use a `SECURITY DEFINER` helper function so the inner lookup is an indexed seek, not a per-row join:

```sql
create or replace function is_team_member(team_id bigint)
returns boolean
language sql
security definer
set search_path = ''
as $$
  select exists (
    select 1 from public.team_members
    where team_id = $1 and user_id = (select auth.uid())
  );
$$;

create policy team_orders_policy on orders
  using ((select is_team_member(team_id)));
```

> Keep `security definer` helper functions in a private (unexposed) schema — see the Security Checklist in `SKILL.md`.

**Always index the columns used in RLS policy predicates:**

```sql
create index orders_user_id_idx on orders (user_id);
```

## Connection Pooling (CRITICAL)

Postgres connections are expensive (~1–3 MB RAM each). Direct connections are fine for migrations and admin tooling, but application traffic must always go through Supabase's built-in **PgBouncer** pooler. Supabase provides two connection strings in the dashboard — use the **pooler URL** (port 6543) for your app server, never the direct URL (port 5432).

- Use **transaction mode** for stateless apps and serverless functions.
- Use **session mode** only if your code relies on prepared statements or temporary tables.

## Indexes on WHERE / JOIN / RLS Columns (CRITICAL)

Every column used in a `WHERE` filter, a `JOIN` condition, or an RLS policy predicate should have an index unless the table is tiny.

```sql
-- Add index on frequently filtered column
create index orders_customer_id_idx on orders (customer_id);

-- Partial index for high-cardinality filtered queries (much smaller, faster)
create index active_orders_idx on orders (created_at)
  where status = 'active';
```

Run `EXPLAIN (ANALYZE, BUFFERS)` to confirm an index is being used. A `Seq Scan` on a large table is almost always a missing index.

## N+1 / Nested-Select Queries (MEDIUM)

Fetching related rows in a loop (one query per parent row) causes latency that scales linearly with result size. Batch with a single JOIN or use Supabase's nested-select syntax instead:

```sql
-- WRONG: N+1 — one query per order
for order in orders:
    fetch customer where id = order.customer_id

-- CORRECT: single JOIN
select o.id, c.name
from orders o
join customers c on c.id = o.customer_id;
```

## Schema Design Reminders

- **Use `bigint` (not `int`) for primary keys** on tables expected to grow large; use `uuid` when row IDs are exposed externally.
- **Always define foreign key constraints** — Postgres does not index FK columns automatically; add an index on the referencing side.
- **Avoid storing JSON where structured columns would do** — JSONB is powerful but defeats the query planner for simple lookups.

## Deeper Reference

The full rule catalogue with SQL examples and `EXPLAIN` output lives in the companion skill `supabase-postgres-best-practices`:

| Category | Reference files |
|---|---|
| Query performance & indexes | `references/query-*.md` |
| Connection management | `references/conn-*.md` |
| RLS performance | `references/security-rls-performance.md` |
| Schema design | `references/schema-*.md` |
| Concurrency & locking | `references/lock-*.md` |
| Data access patterns | `references/data-*.md` |
| Monitoring & diagnostics | `references/monitor-*.md` |
| Advanced features | `references/advanced-*.md` |

These files are in `../supabase-postgres-best-practices/references/` relative to this skill.
