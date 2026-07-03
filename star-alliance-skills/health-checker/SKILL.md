---
name: health-checker
description: "Runs three read-only Supabase health queries (missing FK indexes, public tables without RLS, high dead-tuple tables) and returns findings as a short bulleted list per query, flagging any new finding not already in OPEN-ITEMS.md 👁. Use when worried about database health between scheduled housekeeping runs, or to seed 👁 items in OPEN-ITEMS.md. Triggers: 'db health check', 'check for missing FK indexes', 'tables without RLS', 'dead tuples'."
metadata:
  version: 1.0.0
type: Skill
---

# Health Checker

**Runtime:** this skill invokes the Lex Council Supabase MCP connector, so it must be run by the live Claude session (or a Claude subagent) that has that connector mounted.

The health-checker skill surfaces three classes of database-health concern from the live Lex Council Supabase project by running read-only SQL via the Supabase MCP (connector prefix `mcp__1ee3ddfd-27aa-4176-9539-d9a2081c163d__execute_sql`).

## Queries

### 1. Missing FK indexes

Use the `unnest(indkey)::smallint` array-containment pattern (per OI-06 — the older `indkey::int2[]` cast mismatched on this Postgres version):

```sql
SELECT c.conrelid::regclass AS table_name,
       a.attname AS fk_col
FROM pg_constraint c
JOIN pg_attribute a
  ON a.attrelid = c.conrelid
 AND a.attnum = ANY(c.conkey)
WHERE c.contype = 'f'
  AND c.connamespace = 'public'::regnamespace
  AND NOT EXISTS (
        SELECT 1
        FROM pg_index i
        WHERE i.indrelid = c.conrelid
          AND (a.attnum)::smallint = ANY(unnest(i.indkey)::smallint[])
      )
ORDER BY c.conrelid::regclass::text, a.attname;
```

### 2. Public tables without RLS policies

```sql
SELECT t.tablename
FROM pg_tables t
WHERE t.schemaname = 'public'
  AND NOT EXISTS (SELECT 1 FROM pg_policies p WHERE p.tablename = t.tablename AND p.schemaname = 'public')
ORDER BY t.tablename;
```

### 3. High dead-tuple tables

```sql
SELECT relname, n_dead_tup
FROM pg_stat_user_tables
WHERE schemaname = 'public' AND n_dead_tup > 10000
ORDER BY n_dead_tup DESC;
```

## Output

Return findings as a short bulleted list per query, under 250 words total. Flag any new finding that is NOT already in `lex_council/docs/OPEN-ITEMS.md` 👁 section — the orchestrator will add those as new 👁 items. Do not edit any files — return-only.