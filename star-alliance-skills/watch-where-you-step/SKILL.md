---
name: watch-where-you-step
description: "Use when about to run a direct write (UPDATE/DELETE/INSERT or DDL) against a database or via the Supabase MCP (execute_sql, apply_migration). Triggers: 'update this row', 'delete from this table', 'insert into', 'run this migration', 'truncate', 'drop column', 'apply this DDL', 'execute this SQL'. Teaches the cascade-check doctrine — walk FK ON DELETE/UPDATE CASCADE chains, dependent views, and triggers on the target table BEFORE the write runs, and stop if the blast radius is non-empty."
metadata:
  author: Hermes Agent
  version: 1.0.0
  hermes:
    tags: [databases, postgresql, supabase, cascades, safety, doctrine, data-integrity]
    related_skills: [supabase, supabase-postgres-best-practices, schema-evolution, db-rename-sweep, bundled-rls, code-crime-scene, destructive-gate]
type: Skill
---

# Watch Where You Step — the cascade-check doctrine

The guild has been bitten by cascade deletes that nobody mapped, and by
`UPDATE` cascades that propagated through three layers of dependent views.
The doctrine: **no direct write to a production-shape database without
first walking what the write would touch.** This skill is the procedure
and the rationale. The companion PreToolUse hook
(`.claude/hooks/cascade-check-gate.py`) is the mechanical enforcer; the
doctrine is the *why* you don't try to bypass it.

## The doctrine in one breath

Before any direct write to a database — raw Postgres or via the
Supabase MCP — **map what the write would touch.** Identify the target
table, the operation, the filter / WHERE / row-set. Then walk every
foreign-key relationship (ON DELETE CASCADE / ON UPDATE CASCADE /
ON DELETE SET NULL), every dependent view, and every trigger on the
target. If the blast radius is empty, proceed. If it isn't, stop and
ask the Guild Master — name the affected tables, the row counts, and
the nature of the cascade.

## When to use

Use this skill **every** time you are about to run, or about to call a
tool that runs, any of:

- `UPDATE <table> SET …` (any UPDATE; cascades on PK changes are silent)
- `DELETE FROM <table> …` (rows you delete can cascade to child rows)
- `INSERT INTO <table> …` (rarely cascades, but the inverse — a row
  that fails to insert because of a parent FK — is also a foot-gun
  when the parent has its own cascade behaviour)
- `TRUNCATE TABLE` (truncate is the nuclear option: cascades through
  every FK; no triggers fire unless you add `TRUNCATE` triggers)
- DDL that restructures: `ALTER TABLE … DROP COLUMN`, `ALTER TABLE …
  RENAME`, `ALTER TABLE … ALTER COLUMN … TYPE`, `DROP TABLE … CASCADE`
- The Supabase MCP equivalents: `execute_sql` (when its argument
  contains any of the above verbs) and `apply_migration` (migrations
  are DDL/DML batches — same doctrine applies to the whole migration)
- A raw `psql` / `pgcli` / `psql -c "…"` shell call against a
  non-test database

**Don't use for:** read-only `SELECT`s, `EXPLAIN`, `VACUUM`, `ANALYZE`,
or anything that doesn't change rows. Also don't use for **app-layer
writes** that go through a service which already mediates the cascade
(Lex Council's typed Supabase client, RLS-gated admin pages, the
`view-registry` VIEWS interface). Those paths are already audited.

## The procedure — eight steps

For every direct write, run the full procedure. The tool call happens
in step 8; steps 1–7 are the gate.

### 1. Name the write explicitly

State, in plain English, three facts before touching anything:

- **Target table** — the table the write lands in. `users`,
  `transactions`, `auth.uid()`'s resolved user, etc.
- **Operation** — UPDATE / DELETE / INSERT / TRUNCATE / DDL
- **Filter / row-set** — the WHERE clause, the PK list, the
  migration's affected surface

If you can't fill in all three, the write is not yet specified. Don't
run it.

### 2. Run the cascade-check queries (read-only)

The full SQL reference is in
[`references/cascade-check-sql.md`](references/cascade-check-sql.md).
Always include at least these four:

```sql
-- 2a. FKs WHERE THIS TABLE IS THE PARENT (cascades fire on this table's writes)
SELECT conname, conrelid::regclass AS child_table,
       confdeltype, confupdtype
FROM   pg_constraint
WHERE  contype = 'f'
  AND  confrelid = '<TARGET_TABLE>'::regclass;

-- 2b. FKs WHERE THIS TABLE IS THE CHILD (its writes depend on parents)
SELECT conname, confrelid::regclass AS parent_table,
       conrelid::regclass AS child_table,
       confdeltype, confupdtype
FROM   pg_constraint
WHERE  contype = 'f'
  AND  conrelid = '<TARGET_TABLE>'::regclass;

-- 2c. Triggers on the target
SELECT tgname, tgtype, tgenabled
FROM   pg_trigger
WHERE  tgrelid = '<TARGET_TABLE>'::regclass
  AND  NOT tgisinternal;

-- 2d. Views / mat-views that reference the target
SELECT dependent_view.relname AS view_name,
       source_table.relname   AS source_table
FROM   pg_depend
JOIN   pg_rewrite  ON pg_rewrite.oid = pg_depend.objid
JOIN   pg_class    AS dependent_view ON dependent_view.oid = pg_rewrite.ev_class
JOIN   pg_depend   AS refd ON refd.objid = dependent_view.oid
JOIN   pg_class    AS source_table ON source_table.oid = refd.refobjid
WHERE  source_table.relname = '<TARGET_TABLE>';
```

For Supabase specifically, the MCP exposes:

- `list_tables` — gives the schema, FK summary, and RLS posture
- `get_advisors` — surfaces missing-index / performance advisories that
  hint at hot FK columns

Run those as a cross-check against the raw `pg_constraint` walk; they
agree in the steady state and the disagreement is the bug.

### 3. Compute the blast radius

Translate the cascade-check output into a plain-English list:

- **CASCADE DELETE** — child rows disappear silently. The number
  matters: a `DELETE FROM users WHERE id = 1` that fans out to
  12,000 `transactions` rows is a different problem than the same
  delete with 3 rows.
- **CASCADE UPDATE** — PK changes propagate. A user-id rename on a
  parent table that fans out to ten child tables is a write-fan, not
  a single update.
- **SET NULL / SET DEFAULT** — orphan rows become nullable. Surfaces
  as NULL-poisoning in any downstream view that didn't `COALESCE`.
- **Dependent views** — `REFRESH MATERIALIZED VIEW` cost; or a
  read-only view that starts returning NULL because the underlying
  row disappeared.
- **Triggers** — `BEFORE/AFTER DELETE/UPDATE` handlers, audit
  triggers, replication-out. Triggers can themselves issue writes;
  see what the trigger function does before you trust the count.

**Get the row count first.** Never assume. A `SELECT count(*) FROM
<child> WHERE <parent_fk> IN (<candidates>)` or a `SELECT count(*) FROM
<target> WHERE <filter>` is the only honest number.

```sql
-- Approximate blast radius — the rows that will be touched / orphaned
SELECT count(*) AS cascade_fanout
FROM   <child_table>
WHERE  <parent_fk> IN (SELECT <pk> FROM <target_table> WHERE <filter>);
```

### 4. If blast radius is empty — proceed

- The cascade-check returned no FK fanout, no dependent views, no
  triggers of consequence.
- A single row UPDATE on a leaf table with no children.
- An INSERT into a table with no triggers and a self-resolving FK.

State the empty result in one sentence ("0 children, 0 dependent
views, 0 row-firing triggers") and proceed. **Do not proceed in
silence** — the doctrine is verbal, not just mechanical; the Guild
Master should be able to read the cascade-check transcript and see
"empty → proceed."

### 5. If blast radius is non-empty — STOP

This is the doctrine's load-bearing step. State plainly, in a single
message, four facts:

- **Target table** + **operation** + **filter** (echoed from step 1)
- **Tables affected** — the child / view list, with row counts
- **Nature of cascade** — DELETE / UPDATE / SET NULL / trigger fan
- **Recommended next step** — usually one of: scope the WHERE tighter,
  do the cascade in a single transaction with a savepoint, or stop
  and ask for explicit Guild Master approval

Wait for explicit, textual permission. "Sure" / "yes" / "go" — anything
shorter than "yes, I understand <X> rows will be deleted, proceed" —
is not yet permission. Re-state the blast radius; the operator
re-confirms; then you run.

### 6. The two paths — raw Postgres AND Supabase MCP

The doctrine applies to both. The only differences are the tools:

- **Raw Postgres** (psql, pgcli, `psql -c "…"` in a Bash call) — the
  cascade-check is one `psql -c "…"` invocation against the same
  connection; the destructive-gate covers the unwrap.
- **Supabase MCP** — `execute_sql` and `apply_migration` are the
  primary write surface. The cascade-check is a separate
  `execute_sql` call (read-only SELECT) that must be recorded in the
  same turn BEFORE the write call. The companion hook
  `cascade-check-gate.py` enforces this — see below.

### 7. Log the cascade-check

Every cascade-check is an audit event. Two channels, both required:

- **Vault log** — the cascade-check result, the affected tables, and
  the disposition (proceed / stop-and-confirm). Mined from
  `references/cascade-check-sql.md` examples; written via the
  `vault-log-writer` skill.
- **Evolution ledger** — the gate's auto-ledger entry (kind=verdict,
  surface=databases, verdict=pass | block) when the companion hook is
  armed. This is the durable record that the doctrine was followed.

A write that didn't log a cascade-check, on inspection, was a
write-shaped incident.

### 8. Execute the write — only now

Single transaction, savepoint-first if the cascade is non-empty. Read
back the affected row count and compare against the predicted blast
radius. If the numbers disagree, the cascade-check was wrong; reverse
the transaction (`ROLLBACK TO SAVEPOINT`) and re-do step 2.

## Common pitfalls

1. **Forgetting UPDATE cascades.** `UPDATE users SET id = …` is not
   the same operation as `UPDATE users SET email = …`. The PK
   change fans out; the column change doesn't. The cascade-check is
   for the **specific write**, not the table.
2. **Trusting `list_tables` over `pg_constraint`.** The Supabase
   `list_tables` view is human-oriented; the `pg_constraint` walk is
   authoritative. When they disagree, `pg_constraint` wins.
3. **Missing `ON DELETE CASCADE` on a soft-delete column.** Many
   production schemas have `deleted_at` + `WHERE deleted_at IS NULL`
   on every read; the `ON DELETE` clause still fires for hard
   deletes that bypass the soft layer. The cascade-check doesn't
   care about your ORM's `WHERE`.
4. **Triggers that call other tables.** A `BEFORE DELETE` trigger
   on `users` that inserts into `audit_log` doesn't cascade, but it
   is a write fan. Walk the trigger function.
5. **Views built on views built on the target.** The
   `pg_depend` walk only shows direct dependents; if the target
   table is reachable through a 3-deep view chain, chase it.
6. **Bypassing via RLS-gated client.** The doctrine applies even when
   the client is `anon`-role and "shouldn't" be able to see the
   cascade. The cascade is a Postgres behaviour, not an RLS
   behaviour; RLS only filters rows, it does not stop cascades.
7. **Stating the empty result, then proceeding silently.** State the
   empty result *out loud* so the operator sees the doctrine was
   run. "0 children → proceeding" is the right shape; just running
   the write is not.
8. **Asking permission in jargon.** "Want me to cascade this?" is
   not yet permission. "12,400 transactions rows will be deleted
   along with these 3 user rows. Proceed?" is.

## The enforcement half — the cascade-check gate

A new PreToolUse hook
(`.claude/hooks/cascade-check-gate.py`) is registered alongside this
skill. It mirrors the pattern of `destructive-gate.py` and
`verify-gate.py`:

- **PreToolUse on `Bash` and the Supabase MCP write tools**
  (`execute_sql`, `apply_migration`).
- **Detection** — scans the tool call for the cascade-triggering
  patterns: `UPDATE/DELETE/INSERT INTO …`, `TRUNCATE`, the
  DDL-DROP/RENAME verbs, and the `apply_migration` call itself.
- **State** — `.claude/state/cascade-check-pass` holds the
  fingerprint of the most recent cascade-check on this turn; the
  gate reads it to know the doctrine was followed.
- **Kill switch** — `evolution/DISARMED` OR
  `.claude/state/cascade-check-gate-disarmed` stands the gate
  down (one file, same pattern as the other gates).
- **Default state — REGISTERED BUT NOT ARMED.** The gate ships in
  the catalog but is off by default; arming requires explicit
  Guild Master confirmation (mirrors Tier-B hooks per the
  Evolution Engine invariant: hooks and gates are human-gated).
  See "How to arm" below.
- **Fails OPEN on infrastructure errors.** A broken safety hook
  must never trap a session.

### Current arming state (as of v1.0.0)

The hook is **REGISTERED** in `.claude/settings.json` (added under
`hooks.PreToolUse[*]` alongside `sa-pretool.py` and
`executor-enforce.py`) AND **NOT ARMED** (the disarmed sentinel
`.claude/state/cascade-check-gate-disarmed` is present, so the gate
short-circuits on every tool call). Mirrors the Tier-B invariant in
`evolution/ENFORCEMENT-MODEL`: hooks and gates are human-gated, so
they ship in the catalog but require explicit Guild Master
confirmation before they enforce.

This is the v1.0.0 default. **Arming the gate is a one-line decision,
not an architecture change** — the hook already exists and is wired;
deleting the sentinel is enough to flip enforcement on.

```sh
# Arm: gate begins blocking Supabase MCP writes and raw-Postgres
# writes that don't have a cascade-check on record for this turn.
rm -f .claude/state/cascade-check-gate-disarmed

# Disarm: same as the other gates — one file stands the gate down.
touch .claude/state/cascade-check-gate-disarmed
```

The hook also honors `SA_CASCADE_SKIP=1` for a one-turn bypass
(same pattern as the other gates' `SA_SKIP_*` env vars), so an
agent can override a single write when the operator has signed
off out-of-band.

## Verification checklist

Before you close a turn that ran a direct DB write, confirm:

- [ ] The target table, operation, and filter are named in the
  conversation (step 1).
- [ ] The cascade-check ran — `pg_constraint` walk + dependent
  views + triggers + child-table row count (steps 2–3).
- [ ] If blast radius was non-empty, the operator explicitly
  confirmed the row count and the cascade shape (step 5).
- [ ] A vault log entry records the cascade-check and disposition
  (step 7).
- [ ] If the gate is armed, the evolution ledger shows
  `verdict=pass` for this turn (step 7).
- [ ] The write was wrapped in a transaction with a savepoint
  (step 8).
- [ ] The post-write row count matches the pre-write prediction
  (step 8); if not, the write was rolled back and re-done.

## Related skills

- `supabase` — the structural Supabase doctrine; the platform
  surface that hosts the cascades.
- `supabase-postgres-best-practices` — query/index/tuning craft;
  pairs with this one for the read-side questions.
- `schema-evolution` — the **additive** path (optional columns,
  safe defaults). The cascade doctrine is the **destructive**
  mirror.
- `db-rename-sweep` — the surface-inventory pattern; runs BEFORE a
  rename so the rename's cascade is known.
- `bundled-rls` — RLS-shape decisions; the doctrine applies to
  writes that *should* be blocked by RLS, not just by cascade.
- `code-crime-scene` — open-ended system investigation; surfaces
  the kind of cascade foot-guns this doctrine prevents.
- `destructive-gate` — the sibling hook that catches
  `rm -rf`-class shell patterns; this gate is the
  database-shape mirror.

## Versioning

Own skill. Current: **1.0.0**. Bump `metadata.version` on any
change (PATCH: wording/refs · MINOR: new step or doctrine
expansion · MAJOR: a different safety contract). Regenerate
`VERSIONS.md` via
`python3 star-alliance-skills/skillsmith/scripts/skill_registry.py write`
after a bump, then `python3 build.py` and
`python3 tools/conformity_check.py`.
