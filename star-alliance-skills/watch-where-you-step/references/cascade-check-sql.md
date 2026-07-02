---
type: Reference
skill: watch-where-you-step
timestamp: 2026-07-03T00:00:00Z
---

# cascade-check SQL — the read-only probes

The doctrine asks: "what would this write touch?" These four queries
answer that question without touching any row. They are
**read-only** — they query the catalog, not your data — so they
are safe to run in production. The companion hook
`.claude/hooks/cascade-check-gate.py` reads the same catalog surface
to verify the doctrine was followed.

## 0. Replace `<TARGET_TABLE>` before running

Every snippet below has `<TARGET_TABLE>` as a placeholder.
Substitute the actual table name (schema-qualified if needed:
`public.users`, `auth.users`, `lex.transactions`). Schema
qualification matters — `pg_constraint` lives in the catalog, but
the FK fan-out crosses schema boundaries on Supabase, and a
missed `auth.users` parent on a public-schema child is the most
common cascade foot-gun.

---

## 1. The FK walk — this table as PARENT

> Cascades fire on writes to the parent. If the target is the
> parent, deletes/updates on it fan out to children.

```sql
SELECT  con.conname                                AS constraint_name,
         child.relname                              AS child_table,
         child_ns.nspname                           AS child_schema,
         parent.relname                             AS parent_table,
         parent_ns.nspname                          AS parent_schema,
         CASE con.confdeltype
              WHEN 'a' THEN 'NO ACTION'
              WHEN 'r' THEN 'RESTRICT'
              WHEN 'c' THEN 'CASCADE'
              WHEN 'n' THEN 'SET NULL'
              WHEN 'd' THEN 'SET DEFAULT'
         END                                       AS on_delete,
         CASE con.confupdtype
              WHEN 'a' THEN 'NO ACTION'
              WHEN 'r' THEN 'RESTRICT'
              WHEN 'c' THEN 'CASCADE'
              WHEN 'n' THEN 'SET NULL'
              WHEN 'd' THEN 'SET DEFAULT'
         END                                       AS on_update
FROM    pg_constraint   AS con
JOIN    pg_class        AS child  ON child.oid  = con.conrelid
JOIN    pg_namespace    AS child_ns  ON child_ns.oid = child.relnamespace
JOIN    pg_class        AS parent ON parent.oid = con.confrelid
JOIN    pg_namespace    AS parent_ns ON parent_ns.oid = parent.relnamespace
WHERE   con.contype = 'f'
  AND   parent.relname = '<TARGET_TABLE>'
ORDER BY child_schema, child_table;
```

What to look for: any `on_delete = CASCADE` or `on_update = CASCADE`
row. `SET NULL` and `SET DEFAULT` are also fan-outs (they
*change* child rows), just less dramatic ones.

## 2. The FK walk — this table as CHILD

> Cascades IN to this table on writes to its parents. If the target
> is the child, an UPDATE that touches the parent's PK will
> cascade to this table's FK column.

```sql
SELECT  con.conname                                AS constraint_name,
         child.relname                              AS child_table,
         child_ns.nspname                           AS child_schema,
         parent.relname                             AS parent_table,
         parent_ns.nspname                          AS parent_schema,
         CASE con.confdeltype
              WHEN 'a' THEN 'NO ACTION'
              WHEN 'r' THEN 'RESTRICT'
              WHEN 'c' THEN 'CASCADE'
              WHEN 'n' THEN 'SET NULL'
              WHEN 'd' THEN 'SET DEFAULT'
         END                                       AS on_delete,
         CASE con.confupdtype
              WHEN 'a' THEN 'NO ACTION'
              WHEN 'r' THEN 'RESTRICT'
              WHEN 'c' THEN 'CASCADE'
              WHEN 'n' THEN 'SET NULL'
              WHEN 'd' THEN 'SET DEFAULT'
         END                                       AS on_update
FROM    pg_constraint   AS con
JOIN    pg_class        AS child  ON child.oid  = con.conrelid
JOIN    pg_namespace    AS child_ns  ON child_ns.oid = child.relnamespace
JOIN    pg_class        AS parent ON parent.oid = con.confrelid
JOIN    pg_namespace    AS parent_ns ON parent_ns.oid = parent.relnamespace
WHERE   con.contype = 'f'
  AND   child.relname = '<TARGET_TABLE>'
ORDER BY parent_schema, parent_table;
```

What to look for: a parent with `on_delete = CASCADE` means a
delete on the parent will *take this table with it* — a common
surprise when the target is a leaf table the operator thought
was "safe."

## 3. Triggers on the target

> Triggers can issue writes of their own, replicating rows out,
> inserting audit log entries, or refusing the operation.

```sql
SELECT  t.tgname                                  AS trigger_name,
         CASE t.tgtype & 66
              WHEN  2 THEN 'BEFORE'
              WHEN 64 THEN 'INSTEAD OF'
              ELSE        'AFTER'
         END                                       AS timing,
         CASE t.tgtype & 28
              WHEN  4 THEN 'INSERT'
              WHEN  8 THEN 'DELETE'
              WHEN 16 THEN 'UPDATE'
              WHEN 20 THEN 'INSERT OR UPDATE'
              WHEN 28 THEN 'INSERT OR UPDATE OR DELETE'
              WHEN  0 THEN 'ROW-LEVEL (no DML event)'
              ELSE        t.tgtype::text
         END                                       AS event,
         t.tgenabled                               AS enabled,
         p.proname                                 AS function_name,
         n.nspname                                 AS function_schema
FROM    pg_trigger   AS t
JOIN    pg_proc      AS p   ON p.oid = t.tgfoid
JOIN    pg_namespace AS n   ON n.oid = p.pronamespace
WHERE   t.tgrelid = '<TARGET_TABLE>'::regclass
  AND   NOT t.tgisinternal
ORDER BY event, timing;
```

`tgisinternal = true` rows are constraint-enforcement internals
(skip them). Anything else is a real trigger — read the function
(`\df+ <function_schema>.<function_name>`) to see what it does.
A `BEFORE DELETE` trigger that inserts into `audit_log` is a
write fan; an `AFTER UPDATE` that publishes to a queue is a
side-effect fan.

## 4. Views / mat-views that reference the target

> A view referencing the target reads its rows; if the target
> rows change, the view's result changes. A materialized view
> must be REFRESH'd to reflect the change. A view built on
> another view is a 2-hop dependent.

```sql
-- 4a. Direct dependents
SELECT  v.relname                                 AS view_name,
         v.relkind                                 AS kind,
         ns.nspname                                AS schema
FROM    pg_depend       AS d
JOIN    pg_class        AS v   ON v.oid = d.objid
JOIN    pg_namespace    AS ns  ON ns.oid = v.relnamespace
WHERE   d.refobjid = '<TARGET_TABLE>'::regclass
  AND   d.deptype = 'n'              -- normal dependency
  AND   v.relkind IN ('v', 'm')      -- view, materialized view
ORDER BY schema, view_name;

-- 4b. Indirect dependents (chase one level)
WITH RECURSIVE deps AS (
    SELECT  d.objid,
            1                       AS depth,
            ARRAY[v.relname::text]  AS chain
    FROM    pg_depend AS d
    JOIN    pg_class  AS v ON v.oid = d.objid
    WHERE   d.refobjid = '<TARGET_TABLE>'::regclass
      AND   d.deptype = 'n'
      AND   v.relkind IN ('v', 'm')
    UNION ALL
    SELECT  d.objid,
            deps.depth + 1,
            deps.chain || v.relname
    FROM    pg_depend   AS d
    JOIN    deps        ON d.refobjid = deps.objid
    JOIN    pg_class    AS v ON v.oid = d.objid
    WHERE   d.deptype = 'n'
      AND   v.relkind IN ('v', 'm')
      AND   deps.depth < 3              -- bound the chase
)
SELECT  c.relname        AS view_name,
        c.relkind        AS kind,
        ns.nspname       AS schema,
        depth            AS hops,
        chain            AS path
FROM    deps
JOIN    pg_class     AS c   ON c.oid = deps.objid
JOIN    pg_namespace AS ns  ON ns.oid = c.relnamespace
ORDER BY depth, schema, view_name;
```

`m` = materialized view (must REFRESH; can be expensive).
`v` = ordinary view (re-computed on read; check whether any
read path is hot).

## 5. Approximate blast radius — row count

> Never assume. The catalog tells you *which* tables will be
> touched; the row count tells you *how much*.

```sql
-- 5a. Rows in the target set (the rows the WHERE filter hits)
SELECT count(*) AS target_rows
FROM   <TARGET_TABLE> [WHERE …];

-- 5b. Rows that will be cascade-deleted per child (for DELETE
--     on a parent). Run this for each row from query #1 that
--     had on_delete = CASCADE.
SELECT count(*) AS cascade_fanout
FROM   <CHILD_TABLE>
WHERE  <PARENT_FK> IN (SELECT <PK> FROM <TARGET_TABLE> [WHERE …]);

-- 5c. Rows that will be cascade-updated per child (for UPDATE
--     on a parent's PK). Same shape, different verb. Note:
--     this is rare in practice because changing a PK is rare;
--     the doctrine catches it, but the case is uncommon.

-- 5d. Distinct FKs in play — a quick read of "how many child
--     tables have any row pointing back to this target?"
SELECT count(DISTINCT <PARENT_FK>) AS distinct_parent_refs
FROM   <CHILD_TABLE>
WHERE  <PARENT_FK> IS NOT NULL;
```

## 6. The one-shot summary

> If you want a single query that summarizes the cascade
> posture, this is it. The hook reads an analogous shape
> from `information_schema`.

```sql
SELECT
    tc.table_name                                    AS target_table,
    rc.update_rule                                   AS on_update,
    rc.delete_rule                                   AS on_delete,
    kcu.column_name                                  AS child_fk_column,
    ccu.table_name                                   AS child_table,
    ccu.column_name                                  AS parent_pk_column
FROM
    information_schema.table_constraints             AS tc
JOIN information_schema.referential_constraints      AS rc
      ON tc.constraint_name = rc.constraint_name
JOIN information_schema.key_column_usage              AS kcu
      ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage       AS ccu
      ON ccu.constraint_name = tc.constraint_name
WHERE
    ccu.table_name = '<TARGET_TABLE>'
ORDER BY
    rc.delete_rule, rc.update_rule, ccu.table_name;
```

This is a flatter, friendlier view of the same catalog data.
The hook uses `information_schema` because it survives a
schema rename; `pg_catalog` queries need schema re-resolution.

## 7. Supabase MCP equivalents

When the cascade-check is on the **Supabase MCP** path (not raw
Postgres), the same questions have a different API:

- `list_tables` — returns `name`, `schema`, `rls_enabled`,
  `columns`, and a **truncated** `relationships` array (it
  surfaces the FK names but not the ON DELETE / ON UPDATE
  rules in the public MCP view).
  ⇒ **Always cross-check** with the `pg_constraint` walk;
  the MCP view is human-oriented, not authoritative.
- `get_advisors` — performance advisors that may surface a
  missing FK index, which is a hint that a FK column is hot
  (i.e. the cascade IS the workload).
- `execute_sql` with the queries above — the most direct path
  and what the gate accepts as a "cascade-check on record."

The gate's check is: was a read-only `execute_sql` call (or a
raw-psql call) made this turn that returned rows from
`pg_constraint` / `pg_depend` / `pg_trigger` /
`information_schema.referential_constraints` for the target
table? If yes, the doctrine is on record; if no, the gate
blocks the write.

## 8. Worked example — `DELETE FROM public.users WHERE id = 42`

Suppose you're about to delete one user row. The cascade-check:

```sql
-- Step 1: name the write
--   target = public.users
--   op     = DELETE
--   filter = id = 42
-- Step 2: walk children
SELECT  child.relname, con.confdeltype
FROM    pg_constraint AS con
JOIN    pg_class      AS child ON child.oid = con.conrelid
WHERE   con.contype = 'f'
  AND   con.confrelid = 'public.users'::regclass;
```

Typical return:

```
 child.relname  | confdeltype
----------------+------------
 sessions       | c
 transactions   | c
 user_roles     | c
 audit_log      | a   -- NO ACTION (good)
 file_access    | n   -- SET NULL (orphans the row)
```

Step 3 — count the cascade fan-out:

```sql
SELECT 'sessions'      AS child, count(*) FROM sessions      WHERE user_id = 42
UNION ALL
SELECT 'transactions'  AS child, count(*) FROM transactions  WHERE user_id = 42
UNION ALL
SELECT 'user_roles'    AS child, count(*) FROM user_roles    WHERE user_id = 42
UNION ALL
SELECT 'file_access'   AS child, count(*) FROM file_access   WHERE user_id = 42;
```

Hypothetical return:

```
 child         | count
---------------+-------
 sessions      |     3
 transactions  | 12 400
 user_roles    |     1
 file_access   |    47
```

Step 4 — the doctrine's load-bearing step. Blast radius is
**non-empty** (12,451 rows would be touched across four child
tables; one of them, `file_access`, will orphan 47 rows via
SET NULL). The doctrine says: **stop, state plainly, wait for
explicit confirmation.**

```
Target: public.users, DELETE WHERE id = 42
Affected:
  - sessions     3 rows → DELETE CASCADE
  - transactions 12,400 rows → DELETE CASCADE
  - user_roles   1 row → DELETE CASCADE
  - file_access  47 rows → SET NULL (orphans the rows, file_access.user_id becomes NULL)
Recommend: scope the WHERE tighter, or do the cascade in a
single transaction with a savepoint and the operator's explicit
acknowledgement that 12,400 transaction rows will be deleted.
```

## 9. When the cascade-check itself is hard

There are a few cases where the catalog walk isn't enough:

- **Polymorphic references** — a JSONB column that *implicitly*
  holds a FK reference (no constraint enforces it). The catalog
  has no row; you must `WHERE col->>'id' = '<PK>'` to count.
- **Soft-deletes** — the `deleted_at IS NULL` clause on every read
  means a "delete" may actually be an UPDATE. The cascade still
  fires for hard-deletes that bypass the soft layer.
- **Cross-database** — if you have multiple databases / schemas
  that talk to each other (dblink, FDW), the catalog walk is
  per-database. Run the cascade-check in each.
- **Replica / CDC pipelines** — the catalog is local; the
  replication target (Kafka, BigQuery, the audit warehouse) is
  remote. A 12,400-row cascade is a 12,400-event replication
  fan.

In all four cases, the doctrine is the same: name the surface
you can't see in the catalog, and treat that surface as
**non-empty** for blast-radius purposes until proven otherwise.

## 10. Cite and log

The cascade-check's result is a vault-log event. Include:

- The target table, operation, and filter
- The number of FKs (parent role / child role)
- The blast-radius row count per child
- The disposition (proceed / stop-and-confirm)
- The operator's confirmation, if the blast radius was non-empty
