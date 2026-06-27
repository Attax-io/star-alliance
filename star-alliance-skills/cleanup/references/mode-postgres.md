---
type: Document
timestamp: 2026-06-27T10:27:03Z
---

# Mode: postgres — full recipe

Check Supabase advisor output + pg health queries; auto-fix additive issues; flag schema-level
issues for a dedicated campaign. Script: `scripts/postgres_cleanup.py`.

**Why advisory-only auto-fix.** Only additive, non-destructive SQL is auto-applied (e.g.
`CREATE INDEX IF NOT EXISTS`). Anything requiring a destructive DDL change, an RLS rewrite,
or a trigger/function update is surfaced as a `schema-campaign` item — the user opens a
conquering-campaign session to handle it safely with the PDAAV pattern.

**MCP pre-flight contract.** This mode calls Supabase MCP tools before running the script.
Claude writes the raw JSON outputs to temp files; the script classifies and acts on them.
Always use `project_id bqgrpnsvplvicnmzxwkm` for every MCP call.

#### Step PG0 — Pre-flight

Confirm the Supabase MCP is reachable:

```bash
# Verify project is accessible
# (Claude calls get_project MCP with project_id=bqgrpnsvplvicnmzxwkm)
```

If MCP is unavailable, surface the error and abort — postgres mode cannot run without
Supabase MCP access.

#### Step PG1 — Detect

Run the two MCP calls and write their output:

```bash
# 1. Supabase security + performance advisors
# Claude: get_advisors(project_id='bqgrpnsvplvicnmzxwkm') → write to /tmp/pg_advisors.json

# 2. pg health queries (missing FK indexes, tables without RLS, high dead-tuple tables)
# Claude: execute_sql(project_id='bqgrpnsvplvicnmzxwkm', query=HEALTH_SQL) → write to /tmp/pg_health.json
```

Standard health SQL to run (matches what the health-checker skill uses):

```sql
-- Missing FK indexes
SELECT
    tc.table_schema, tc.table_name, kcu.column_name,
    ccu.table_name AS references_table
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
    AND tc.table_schema = kcu.table_schema
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
AND tc.table_schema = 'public'
AND NOT EXISTS (
    SELECT 1 FROM pg_indexes
    WHERE schemaname = tc.table_schema
    AND tablename = tc.table_name
    AND indexdef ILIKE '%' || kcu.column_name || '%'
);

-- Tables without RLS
SELECT schemaname, tablename
FROM pg_tables
WHERE schemaname = 'public'
AND NOT rowsecurity;

-- High dead-tuple tables (> 10 000 dead rows)
SELECT relname, n_dead_tup, n_live_tup,
    round(100.0 * n_dead_tup / NULLIF(n_live_tup + n_dead_tup, 0), 1) AS dead_pct
FROM pg_stat_user_tables
WHERE n_dead_tup > 10000
ORDER BY n_dead_tup DESC;
```

Then run the script's detect phase:

```bash
python3 ~/.claude/skills/cleanup/scripts/postgres_cleanup.py detect
```

Show the user the total issue count per source (advisors vs health queries) and ask whether to proceed.

#### Step PG2 — Classify

```bash
python3 ~/.claude/skills/cleanup/scripts/postgres_cleanup.py classify
```

Tier mapping:

| Tier | Signal | Action |
|---|---|---|
| **advisory-auto-fix** | Missing FK index, no-primary-key on empty table | Generate `CREATE INDEX IF NOT EXISTS` SQL |
| **advisory-surface** | Dead tuples, cache hit ratio, index bloat | Surface as informational — Atta decides if VACUUM/REINDEX needed |
| **schema-campaign** | RLS disabled on a table, SECURITY DEFINER view, unused index candidate for DROP, any policy rewrite | Flag as needing a conquering-campaign session |
| **noise** | Long-running queries (ephemeral), replication lag (not applicable for single-project) | Suppress |

Print the classification summary. Confirm auto-fix count before proceeding.

#### Step PG3 — Apply (advisory-auto-fix only)

```bash
python3 ~/.claude/skills/cleanup/scripts/postgres_cleanup.py apply
```

The script generates `/tmp/pg_apply.sql`. Review the SQL, then apply:

```
# Claude: apply_migration(project_id='bqgrpnsvplvicnmzxwkm', query=<contents of /tmp/pg_apply.sql>)
```

**Hard constraint:** Only `CREATE INDEX IF NOT EXISTS` is auto-applied. Any other DDL found in the
auto-fix tier (unexpected by the script) is escalated to `schema-campaign` instead. Never apply
`DROP`, `ALTER TABLE`, or `CREATE OR REPLACE FUNCTION` via auto-fix.

**Migration filename safety.** The project uses 14-digit timestamp format for migration names
(`YYYYMMDDHHMMSS`). Confirm the format matches before calling `apply_migration`. A mismatch
causes `MIGRATIONS_FAILED` on preview branches, leaving the DB empty and unresponsive.

#### Step PG4 — Verify

Re-run health queries and advisors; report delta:

```bash
# Claude: get_advisors + execute_sql again → overwrite /tmp/pg_advisors.json + /tmp/pg_health.json
python3 ~/.claude/skills/cleanup/scripts/postgres_cleanup.py verify
```

Expected: advisory-auto-fix count drops to 0. If any remain, surface them as needing manual review.

#### Step PG5 — Surface schema-campaign items

```bash
python3 ~/.claude/skills/cleanup/scripts/postgres_cleanup.py surface
```

Print the full triage list. For each `schema-campaign` item, suggest the conquering-campaign
trigger phrase the user would use (e.g., "add RLS to the `notifications` table").

#### Step PG6 — Vault log

Delegate to **vault-log-compliance** *only if a migration was applied*. For triage-only runs,
no vault log needed.

The entry should document: each auto-fixed index (table + column + `CREATE INDEX` SQL), advisor
delta (before → after count), and the schema-campaign checklist for the user.

**Key traps for postgres mode:**

- **`CREATE OR REPLACE VIEW` silently drops `security_invoker=true`** — if any view is touched
  during this pass (even incidentally), follow up with `ALTER VIEW <v> SET (security_invoker = true)`.
- **Intentional advisor warnings** — some advisories are expected (e.g. a public SECURITY DEFINER
  RPC is intentional per the v2 conventions). Document intentional exceptions in the vault log
  with a `// BR-NNN:` style comment so future postgres passes don't re-flag them.
- **`GROUP BY` + aggregate in views** — makes the view non-streamable to PostgREST (silently
  ignores `Range` headers on paginated queries). Classify as `advisory-surface`.
- **New trigger/RPC advisor warnings** — new trigger functions and RPCs almost always generate
  `search_path` + anon-EXECUTE advisor warnings. Fix inline when writing the object; don't
  defer to a cleanup pass.
