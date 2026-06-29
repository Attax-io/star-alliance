---
name: vault-log-writer
description: Write and file a correct Lex Council vault log entry per the P8 mandatory change logging rule. Use whenever any code or backend change has been made in a session — every migration, trigger, view, RLS policy, component, page, edge function, bug fix, or doc update. Also use when the session called any Supabase MCP tool (execute_sql, apply_migration, get_advisors, etc.) to produce the required P13 self-audit section. Trigger on phrases like "write the vault log", "log this change", "P8 log", "session log", "what do I need to log", "vault log entry", or any time a session is about to end and no vault log has been written. This skill exists because P8 is non-negotiable and the P13 self-audit section is frequently omitted or malformed.
---

# Writing a Vault Log Entry

## Where it lives

```
lex_council/docs/vault-logs/YYYY-MM-DD_short-description.md
```

Use today's date in `YYYY-MM-DD` format. Slug: lowercase, hyphens, 3–6 words that describe the change (`adds-n-kinds-suspended-task`, `fix-fd-insert-returning`, `rewrite-attendance-daily-js`).

For changes from late April 2026 onward, some logs use the format `YYYYMMDD_slug.md` (no hyphens in date) — use this if recent logs in the directory use it. Check the INDEX to see which format is current.

## Frontmatter

```yaml
---
claude_hits: 0
housekeeper_passes: 0
last_housekeeper_pass: null
tags: [vault-log, backend, rls]   # add relevant domain tags
date: YYYY-MM-DD
applied: true                      # true if migrations were applied; omit for doc-only changes
author: Claude + Atta
---
```

Tag vocabulary (use what fits): `vault-log`, `backend`, `frontend`, `rls`, `triggers`, `views`, `security`, `permissions`, `notifications`, `access-control`, `schema`, `migration`, `edge-function`, `cron`, `performance`, `bug-fix`, `refactor`, `docs`.

## Title and summary

```markdown
# YYYY-MM-DD — Short imperative title describing the change

Brief one-paragraph summary: what problem was solved, what approach was taken, and why.
Quote Atta's instruction if it drove the work.
```

## Changes table

Every file touched gets a row:

```markdown
## Changes

| # | Type | Target | What Changed | Why |
|---|------|--------|-------------|-----|
| 1 | Schema | [[table_name]] | Added column `X boolean DEFAULT false NOT NULL` | Gate for new feature Y |
| 2 | View | [[view_name]] | Added column `X` to SELECT list; re-ran `ALTER VIEW SET (security_invoker=true)` | Expose X to frontend |
| 3 | Trigger | `private.fn_name` | Added Branch 3: transition guard on `col IS DISTINCT FROM OLD.col` | Prevent duplicate notifications |
| 4 | RLS | `table_name.policy_name` | Rewrote USING to call `private.user_can_see_file()` | Align write policy with SELECT |
| 5 | Frontend | `apps/web/app/.../page.tsx` | Added column to SELECT_COLS and card display | Reflect new schema column |
| 6 | Docs | [[VIEWS-CATALOG]] | Added entry for `[[new_view_js]]` | P8 doc update |
```

**Type vocabulary:** `Schema`, `View`, `Trigger`, `Function`, `RLS`, `Edge Function`, `Cron`, `Frontend`, `Docs`, `Data`, `Index`, `Migration`.

**Wikilink rule:** every Supabase object (table, view, trigger, function) and every doc file referenced gets `[[double-bracket]]` wikilink syntax. Frontend files use the path in backticks.

## Verification section

Include the SQL or UI check that proves the change shipped correctly:

```markdown
## Verification

```sql
-- Confirm view is security_invoker
SELECT relname, reloptions
FROM pg_class
WHERE relname = 'my_view_js';
-- Expect: reloptions = {security_invoker=true}

-- Confirm policy was rewritten
SELECT policyname, (qual ILIKE '%user_can_see_file%') AS uses_helper
FROM pg_policies
WHERE tablename = 'my_table';
```

`get_advisors security` result: 0 new errors.

UI smoke: opened Admin → [page] → data loaded, filter works, mutation succeeds.
```

## Lessons section (when something non-obvious was discovered)

```markdown
## Lessons

1. **PostgREST masks trigger errors as 42501.** A stale column ref inside a trigger body inside `INSERT...RETURNING` surfaces as "new row violates row-level security policy" — not the underlying 42703. Always grep `pg_proc.prosrc` for old column names before assuming a policy is broken.

2. **`CREATE OR REPLACE VIEW` drops `security_invoker`.** Always follow with `ALTER VIEW SET (security_invoker=true)`.
```

Add a lesson for every non-obvious failure mode encountered during this session. These become the raw material for memory and skill updates.

## P13 self-audit section

**Required if any Supabase MCP tool was called** (`execute_sql`, `apply_migration`, `list_tables`, `list_migrations`, `get_advisors`, `list_extensions`, `generate_typescript_types`, `get_logs`, `deploy_edge_function`, or any introspection/mutation tool).

```markdown
## P13 Self-Audit

### MCP calls made

| Tool | Call | Purpose |
|---|---|---|
| `execute_sql` | `SELECT * FROM pg_policies WHERE tablename = 'fd'` | Verify existing INSERT policy before rewrite |
| `apply_migration` | `my_migration_name` | Apply the RLS rewrite |
| `get_advisors` | security run | Confirm zero new advisor errors |

### Docs consulted

| Doc | Read? | Notes |
|---|---|---|
| `primary_instructions.md` | ✓ | |
| `Vault Core.md` | ✓ | |
| `BACKEND.md` (Planet Hub) | ✓ | §S11 for view security model decision |
| `FILE-ACCESS-MODEL.md` (leaf) | ✓ | Current path A/B model |
| `RLS-POLICY-REFERENCE.md` (sibling) | ✓ | Existing policy patterns |

### P13 compliance verdict

✅ COMPLIANT — all required docs read before first MCP call.

*or*

⚠️ PARTIAL — [name the gap and what compensated for it]
```

## Footer links

```markdown
---
**Related:** [[BACKEND]] · [[primary_instructions]] · [[affected_view]] · [[affected_table]]
```

Link the planet hub, primary_instructions, and every object name mentioned in the changes table.

## Updating INDEX.md

After writing the vault log file, add a row to `docs/vault-logs/INDEX.md`:

```markdown
| [[YYYY-MM-DD_slug]] | YYYY-MM-DD | Short one-line description |
```

Keep the index in reverse-chronological order (newest at top of the table body).

## Common mistakes to avoid

- **Missing wikilinks** — every table, view, trigger, function, or doc file touched must be wikilinked
- **"Updated X" without "because Y"** — always state the reason
- **Skipping verification** — include at least one SQL check or UI smoke test
- **Skipping P13 self-audit** — if any MCP tool was called, the audit is mandatory
- **Writing the log after the session ends** — P8 requires the log before the session closes; if Atta asks to stop mid-work, log what was completed and what remains as a follow-up item
- **Missing INDEX.md row** — every vault log needs an entry in the index
