---
name: add-new-trigger
description: "End-to-end procedure for creating or modifying a database trigger and its backing function in the Lex Council Supabase backend. Use whenever the user asks to add a trigger, create a trigger function, modify trigger logic, wire a BEFORE/AFTER trigger, fire on INSERT/UPDATE/DELETE, add a transition guard, or write a PL/pgSQL function. Also trigger on mentions of CREATE OR REPLACE FUNCTION in private schema, pg_trigger, FOR EACH ROW, AFTER UPDATE, NEW.col IS DISTINCT FROM OLD.col, S7 hardening, S8 privilege lockdown, or SECURITY DEFINER in a trigger context. This skill exists because trigger bugs have caused three separate production incidents: duplicate notifications from missing transition guards, broken INSERT flows from stale column refs in function bodies after renames, and privilege escalation from missing S7 search_path pinning."
version: 1.1.0
---

# Adding or Modifying a Trigger in Lex Council

## Step 1: Read SUPABASE-FUNCTIONS.md first

```
lex_council/docs/architecture/backend/SUPABASE-FUNCTIONS.md
```

Confirm:
1. Does a function with the name you're about to use already exist in `private`? If so, alter it in place with `CREATE OR REPLACE FUNCTION` — never create a second one.
2. Does an existing trigger on this table already handle adjacent logic? If so, consider extending it rather than adding a parallel trigger.

## Step 2: Naming convention

Functions and triggers share the same name. Every trigger must follow:

```
{source}_on_{target}_{timing}_{events}
```

| Segment | Meaning | Examples |
|---|---|---|
| `{source}` | Table where the trigger fires (no schema prefix) | `fd`, `tasks`, `council_members` |
| `on` | Literal separator | — |
| `{target}` | Table the function reads from or writes to | `access`, `notifications`, `cm` |
| `{timing}` | `a` = AFTER · `b` = BEFORE | `a`, `b` |
| `{events}` | Events in `iud` order, omit unused | `iud`, `iu`, `u`, `i` |

Examples: `fd_on_cm_a_iud`, `td_on_tsl_a_iu`, `cm_on_cm_b_main_iu`

**One function = one relationship.** If you need to touch two target tables from one source event, create two separate functions and two triggers — one per target.

## Step 3: S7 hardening — mandatory on every SECURITY DEFINER function

All trigger functions run as SECURITY DEFINER (they fire as the `postgres` owner). Three rules are non-negotiable:

### 3a. Pin search_path

```sql
CREATE OR REPLACE FUNCTION private.my_trigger_fn()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO 'public', 'private'
AS $$
```

Without this, an attacker can shadow `public` functions in a temp schema and hijack the definer's elevated privileges.

### 3b. Verify authentication at the top

```sql
BEGIN
  IF auth.uid() IS NULL THEN
    RAISE EXCEPTION 'Not authenticated';
  END IF;
  ...
```

SECURITY DEFINER functions bypass RLS. An unauthenticated call executes with full owner-level access.

### 3c. Check caller permissions before acting

Before performing any write, verify the caller holds the relevant `admin_perms` flag:

```sql
IF NOT EXISTS (
  SELECT 1 FROM public.admin_perms
  WHERE ap_uuid = auth.uid()
    AND relevant_flag = true
) THEN
  RAISE EXCEPTION 'Permission denied';
END IF;
```

Only required for functions that gate admin actions. Triggers fired by system events (crons, cascade chains) may skip this check — use judgment.

## Step 4: S8 privilege lockdown — always

PostgreSQL grants `EXECUTE` to `PUBLIC` by default on every new function. In Supabase, `anon` inherits from `PUBLIC`. Every function in the `public` schema needs an explicit revoke.

For `private` schema functions this is less critical (anon/authenticated can't access the private schema by default), but if you expose a public wrapper:

```sql
-- After CREATE FUNCTION, always include:
REVOKE EXECUTE ON FUNCTION public.my_function(args) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.my_function(args) TO authenticated;
GRANT EXECUTE ON FUNCTION public.my_function(args) TO service_role;
```

## Step 5: Transition guards on AFTER UPDATE branches

Every `AFTER UPDATE` trigger branch that cares about a specific column change **must** include a transition guard:

```sql
IF NOT (
  NEW.some_status = target_value
  AND OLD.some_status IS DISTINCT FROM NEW.some_status
) THEN
  RETURN NEW;
END IF;
```

Use `IS DISTINCT FROM` — not `<>` — because `<>` returns NULL when either operand is NULL, which means the guard silently fails on rows where the column transitions from NULL.

**Why this matters:** On 2026-04-24, `td_on_tsl_a_iu` Branch 1 lacked a transition guard. A nightly `update_task_counter` cron incremented a counter on every overdue task, re-firing the trigger on every row each night. 189 duplicate notifications in one batch.

Never use "is the column non-null" as a proxy for "did the column change". Always use `IS DISTINCT FROM`.

## Step 6: Multiple branches — use explicit branch IDs

If a trigger function handles more than one case, label each branch for observability:

```sql
-- Branch 1: status transitions to X
IF NEW.task_status = 7 AND OLD.task_status IS DISTINCT FROM NEW.task_status THEN
  PERFORM private.notify_many(
    ...
    p_source => 'trigger:td_on_tsl_a_iu:b1',
    ...
  );
  RETURN NEW;
END IF;

-- Branch 2: some other condition
IF NEW.other_col IS DISTINCT FROM OLD.other_col THEN
  ...
  RETURN NEW;
END IF;
```

The `p_source` tag (for notification triggers) or a comment label (for others) makes `n_events.source` useful when debugging which branch produced a side effect.

## Step 7: Full canonical template

```sql
CREATE OR REPLACE FUNCTION private.{source}_on_{target}_{timing}_{events}()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO 'public', 'private'
AS $$
DECLARE
  v_some_var uuid[];
BEGIN
  -- Auth check (for admin-action triggers)
  IF auth.uid() IS NULL THEN
    RAISE EXCEPTION 'Not authenticated';
  END IF;

  -- Branch 1 — with transition guard (AFTER UPDATE triggers)
  IF NOT (
    NEW.some_col = target_value
    AND OLD.some_col IS DISTINCT FROM NEW.some_col
  ) THEN
    RETURN NEW;
  END IF;

  -- Do the work
  SELECT array_agg(DISTINCT user_id)
    INTO v_some_var
    FROM public.some_table
   WHERE file_id = NEW.file_id;

  -- Example: notify (for notification triggers)
  PERFORM private.notify_many(
    p_kind_key       => 'entity.event.qualifier',
    p_recipient_ids  => v_some_var,
    p_recipient_type => 'member',
    p_subject_refs   => jsonb_build_object(
      'file_id',  NEW.file_id,
      'all_ref',  NEW.id,
      'n_table',  2
    ),
    p_vars           => jsonb_build_object(
      'entity_title',  NEW.title,
      'all_ref_info',  NEW.title
    ),
    p_actor_id       => auth.uid(),
    p_source         => 'trigger:{fn_name}:b1',
    p_channels       => NULL
  );

  RETURN NEW;
END;
$$;

-- Create or replace the trigger
DROP TRIGGER IF EXISTS {trigger_name} ON public.{source_table};
CREATE TRIGGER {trigger_name}
  AFTER UPDATE ON public.{source_table}
  FOR EACH ROW
  EXECUTE FUNCTION private.{source}_on_{target}_{timing}_{events}();
```

Note: `DROP TRIGGER IF EXISTS ... CREATE TRIGGER` is idempotent — preferred over conditional creation.

## Step 8: Scan pg_proc before future renames

Renaming a column or table does **not** rewrite PL/pgSQL function bodies. The stale `NEW.old_col` reference compiles silently but fails at runtime, and PostgREST masks the resulting `42703 column does not exist` as a `42501 RLS violation` when the trigger fires inside an `INSERT...RETURNING` CTE.

Whenever a rename is planned on any table or column that has triggers, grep the function bodies:

```sql
SELECT n.nspname, p.proname
FROM pg_proc p
JOIN pg_namespace n ON n.oid = p.pronamespace
WHERE n.nspname IN ('public', 'private')
  AND pg_get_functiondef(p.oid) ILIKE '%old_column_name%';
```

This is also documented in the `db-rename-sweep` skill.

## Step 9: Vault log

Every new trigger is a P8 change. Log at `docs/vault-logs/YYYY-MM-DD_slug.md`:

- Function name and what it does
- Trigger timing (BEFORE/AFTER), events (IUO), and table
- Branch logic and transition guards
- S7/S8 compliance notes
- Test evidence (row counts, notification delivery state, etc.)

Use the `vault-log-writer` skill for the log structure.

## Self-check before declaring done

- [ ] Function name follows `{source}_on_{target}_{timing}_{events}` convention
- [ ] Function lives in `private` schema
- [ ] Function and trigger share the same name
- [ ] `SET search_path TO 'public', 'private'` in function definition
- [ ] `auth.uid() IS NULL` guard at top (for admin-action functions)
- [ ] Transition guard present on every AFTER UPDATE branch: `OLD.col IS DISTINCT FROM NEW.col`
- [ ] S8: REVOKE/GRANT block for any public-schema wrappers
- [ ] No stale column references (verified with pg_proc grep after any rename)
- [ ] Vault log written

## Why this skill exists

Three production incidents from trigger bugs:
1. **Missing transition guard** — 189 duplicate notifications from a nightly cron re-firing (2026-04-24).
2. **Stale column ref after rename** — trigger body referenced a dropped column; PostgREST masked the 42703 as a 42501 RLS violation (2026-05-03, twice).
3. **Missing search_path pin** — SECURITY DEFINER function callable via shadowed schema (caught during April 2026 security audit).

Every step in this skill addresses one of these failure modes.
