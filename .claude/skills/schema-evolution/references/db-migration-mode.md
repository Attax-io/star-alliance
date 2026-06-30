---
name: db-migration-mode
type: Reference
---
# DB-Migration Mode — when the "field" is a Postgres table or column

The five additive moves in `SKILL.md` assume the model is a JSON record shape: absence is safe,
the default lives in the reader, the proof is a green gate over old data. When the thing you are
evolving is an actual **Postgres table or column** — not a JSON field — additivity is necessary
but not sufficient. A new table that reads green in your test can still be a **silent data leak**:
without Row-Level Security every row is visible to every tenant, and the additive instinct ("it
doesn't break existing readers") says nothing about who is now allowed to read it.

This mode complements the additive-JSON guidance; it does not replace it. Use it the moment the
field being added is a column on, or the whole of, a tenant-scoped Postgres table. The discipline
below is the database-migration safety contract: security ships **in the same migration file** as
the structure, or it does not ship.

## The contract — RLS lives in the same migration file as the table

A `CREATE TABLE` and the security that scopes it are **one atomic change**, in **one migration
file**. Splitting the policies into a separate RLS file is **forbidden**: a migration can land,
and the table can go live serving rows, before the second file ever runs — that gap is the leak.
The same file that creates the table must, in order:

1. `CREATE TABLE …` — the structure.
2. `ALTER TABLE … ENABLE ROW LEVEL SECURITY` — turn the guard on. A table without this line is a
   stop-the-line condition (see below); RLS-off means every row is world-readable to the app role.
3. The **policies** — one per access path the role legitimately has (user SELECT, user INSERT,
   user UPDATE, admin, system/background-job as needed). A policy missing for a path that the
   GRANT then opens is the bug; a path GRANTed but unpolicied is a leak.
4. `CREATE INDEX … ON tbl(user_id)` — **Index for RLS performance — MANDATORY.** Every RLS
   predicate filters on the scoping column (`user_id`), so every query the policy touches is a
   scan without this index. The index is part of the security change, not a later optimization.
5. The **GRANTs** — the role's table privileges, last, after the guard and the policies are in
   place so no window exists where the role can read an unpoliced table.

```sql
-- one migration file, in this order
CREATE TABLE user_data (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id    TEXT NOT NULL,
  data       JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE user_data ENABLE ROW LEVEL SECURITY;                 -- guard ON, same file

CREATE POLICY user_data_user_select ON user_data                 -- policy, same file
  FOR SELECT TO app_user
  USING (user_id = current_setting('app.current_user_id', true));

CREATE INDEX idx_user_data_user_id ON user_data(user_id);        -- Index for RLS perf — MANDATORY

GRANT SELECT, INSERT, UPDATE ON user_data TO app_user;           -- GRANTs last
```

## The mandatory user_id index

Every RLS-scoped table carries an index on its scoping column. The RLS policy's `USING` clause
runs on **every** read of the table, and it filters on `user_id`; with no index that predicate is
a sequential scan on every query, and the cost grows with the table. Treat the `user_id` index as
a structural requirement of enabling RLS — it is created in the same file, never deferred to a
follow-up "perf" migration that may never come.

## Migration checklist (run in order)

1. **RLS in the same file** — `ENABLE ROW LEVEL SECURITY` + all policies live in the very file
   that `CREATE TABLE`s. No separate RLS file. (Stop-the-line if split.)
2. **user_id index** — `CREATE INDEX … ON tbl(user_id)` present in that same file, one per scoped
   table.
3. **GRANTs** — the role's privileges declared, after the guard and policies, never before.
4. **Data-dictionary update** — record the new table/column, its RLS policies, and its scoping
   column in the project's data dictionary in the same pass. An undocumented table is a table the
   next author re-discovers by reading the schema (the same failure mode as the additive mode's
   "forgot the authoring skill").

## Stop-the-line — policies absent

If a migration creates or alters a tenant-scoped table and the RLS policies are **absent** — no
`ENABLE ROW LEVEL SECURITY`, or the guard is on but no policy covers a GRANTed path, or the RLS
sits in a separate file — **stop the line.** Do not thread the change through consumers, do not
hand off, do not let the build proceed on the additive-is-enough reasoning. A new RLS-scoped table
without its policies in-file is a security defect, not a backward-compatibility one, and the
additive proof (old readers still work) is silent about it. Fix the migration so structure +
RLS + index + GRANTs are one atomic file, then continue.

## How this maps onto the five moves

- **Optional + safe default** still holds for an added *column*: add it nullable / with a default
  so existing rows remain valid — the additive move is unchanged.
- **Validate at the source / at the gate** becomes: the migration file itself is the source, and
  the stop-the-line check (RLS-in-file → user_id index → GRANTs → data-dictionary) is the gate.
  The "when present, consistent" rule grows a sibling: "when a scoped table, RLS-complete."
- **Prove old data passes** still applies — and now also: prove the policy actually scopes (a row
  for tenant A is invisible to tenant B), not merely that the table reads green.

Grounded in the SAW `migration-patterns` discipline (RLS in the same migration file as the table,
mandatory `user_id` index for RLS performance, the before-PR migration checklist, and ARCHitect
approval before any schema change), adapted to the guild's additive-evolution voice.
