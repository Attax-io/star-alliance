# file_access Table Migration SQL

## Overview

This migration creates the `file_access` table — the single source of truth for who can access a file. It replaces the legacy `fd_access` satellite table with a formally-typed model that stores roles and computes `users_access` at query time.

**Status:** Ready for approval
**Date:** 3 April 2026
**Total rows affected:** All files (backfill from fd_access required after table creation)

---

## Migration SQL

```sql
-- ═══════════════════════════════════════════════════════════════════════════════
-- file_access Table — Core Table Creation
-- ═══════════════════════════════════════════════════════════════════════════════
--
-- Purpose: Single source of truth for file access. Replaces fd_access.
--
-- Roles (stored):
--   • file_owner: council member (is_partner = true), default from ppl
--   • file_admin: any council member, defaults to owner at creation
--   • member_assistants: attorney council members, manually added
--   • external_assistants: pre-registered org_users, manually added
--   • customer_uuid: auto-resolved from ppl.user_ref, null if no account
--   • subers: opt-in notification subscribers (subset of users_access)
--   • branches_access: branch-level RLS (GIN indexed)
--
-- Virtual (computed in file_access_full view):
--   • users_access: deduplicated union of all roles, respects view_for_customer flag
--   • tasks_access: computed live from tasks table
--
-- RLS: Three-gate pattern (Gates 1-3 in views)
--   1. branches_access @> ARRAY[user's branch]
--   2. auth.uid() = ANY(users_access)
--   3. EXISTS on ancestor file_access rows (via fd.gfn_ref/mfn_ref/bfn_ref/sfn_ref)
--
-- ═══════════════════════════════════════════════════════════════════════════════

-- Create table
CREATE TABLE IF NOT EXISTS public.file_access (
  file_id                uuid NOT NULL PRIMARY KEY,
  file_owner             uuid NOT NULL,
  file_admin             uuid NOT NULL,
  member_assistants      uuid[] NOT NULL DEFAULT '{}',
  external_assistants    uuid[] NOT NULL DEFAULT '{}',
  customer_uuid          uuid,
  branches_access        uuid[] NOT NULL,
  subers                 uuid[] NOT NULL DEFAULT '{}',
  view_for_customer      boolean NOT NULL DEFAULT true,
  updated_at             timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT file_access_file_id_fk FOREIGN KEY (file_id) REFERENCES fd(file_id) ON DELETE CASCADE,
  CONSTRAINT file_access_owner_fk FOREIGN KEY (file_owner) REFERENCES council_members(id),
  CONSTRAINT file_access_admin_fk FOREIGN KEY (file_admin) REFERENCES council_members(id)
);

-- Create indexes
CREATE INDEX IF NOT EXISTS file_access_owner_idx ON file_access(file_owner);
CREATE INDEX IF NOT EXISTS file_access_admin_idx ON file_access(file_admin);
CREATE INDEX IF NOT EXISTS file_access_customer_uuid_idx ON file_access(customer_uuid);

-- GIN indexes for array columns (used by RLS Gate 2 and Gate 3)
CREATE INDEX IF NOT EXISTS file_access_branches_access_gin ON file_access USING gin(branches_access);
CREATE INDEX IF NOT EXISTS file_access_member_assistants_gin ON file_access USING gin(member_assistants);
CREATE INDEX IF NOT EXISTS file_access_external_assistants_gin ON file_access USING gin(external_assistants);
CREATE INDEX IF NOT EXISTS file_access_subers_gin ON file_access USING gin(subers);

-- ═══════════════════════════════════════════════════════════════════════════════
-- Row-Level Security (RLS)
-- ═══════════════════════════════════════════════════════════════════════════════
-- RLS is deferred to the file_access_full view and _js views that use it.
-- The table itself allows authenticated read; the view enforces the three-gate pattern.
-- ═══════════════════════════════════════════════════════════════════════════════

ALTER TABLE public.file_access ENABLE ROW LEVEL SECURITY;

-- Allow authenticated users to read (RLS enforcement happens at view layer)
CREATE POLICY file_access_select_authenticated ON public.file_access
  FOR SELECT
  USING (auth.role() = 'authenticated');

-- Only system / trigger can modify file_access directly
-- (Frontend changes go through _js views and API routes)
CREATE POLICY file_access_update_system_only ON public.file_access
  FOR UPDATE
  USING (false)  -- Fallback: never allow direct updates at table level
  WITH CHECK (false);

CREATE POLICY file_access_delete_system_only ON public.file_access
  FOR DELETE
  USING (false);  -- Fallback: never allow direct deletes

-- ═══════════════════════════════════════════════════════════════════════════════
-- Backfill from fd_access (if migrating from legacy fd_access table)
-- ═══════════════════════════════════════════════════════════════════════════════
-- This step assumes the legacy fd_access table exists and has been populated.
-- If fd_access does not exist or is already integrated into fd, skip this block.
--
-- INSERT INTO file_access (
--   file_id,
--   file_owner,
--   file_admin,
--   member_assistants,
--   external_assistants,
--   customer_uuid,
--   branches_access,
--   subers,
--   view_for_customer,
--   updated_at
-- )
-- SELECT
--   fa.file_id,
--   fa.file_owner,
--   fa.file_admin,
--   fa.member_assistants,
--   fa.external_assistants,
--   fa.customer_uuid,
--   fa.branches_access,
--   fa.subers,
--   true AS view_for_customer,  -- Default to true for legacy data
--   NOW()
-- FROM fd_access fa
-- ON CONFLICT (file_id) DO NOTHING;
--
-- ═══════════════════════════════════════════════════════════════════════════════

-- Grant permissions
GRANT SELECT ON public.file_access TO authenticated;
GRANT SELECT ON public.file_access TO anon;  -- For signed URLs via storage_check_doc_access

-- ═══════════════════════════════════════════════════════════════════════════════
-- Trigger Function: fa_on_fd_a_insert
-- ═══════════════════════════════════════════════════════════════════════════════
-- Fires: AFTER INSERT ON fd
-- Does: Creates file_access row; resolves defaults; sets branches_access
--
-- This is a TEMPLATE. To be implemented in a separate migration after this table
-- exists and the org_users table is created. The trigger must:
--   1. Resolve file_owner from ppl.user_ref (customer) → council_members (partner)
--   2. Set file_admin = file_owner
--   3. Resolve customer_uuid from ppl.user_ref if customer has an account
--   4. Set branches_access from the file's owner's primary branch
--
-- Note: external_assistants and member_assistants validation FK → org_users / council_members
--       will be enforced by constraint after org_users table is created.
-- ═══════════════════════════════════════════════════════════════════════════════

-- Template signature (implementation deferred):
-- CREATE OR REPLACE FUNCTION fa_on_fd_a_insert()
-- RETURNS TRIGGER AS $$
-- DECLARE
--   v_owner_id uuid;
--   v_owner_branch uuid;
--   v_customer_uuid uuid;
-- BEGIN
--   -- 1. Resolve file_owner from customer (ppl.user_ref → council_members)
--   SELECT cm.id INTO v_owner_id
--   FROM ppl p
--   JOIN council_members cm ON cm.id = p.partner_id
--   WHERE p.ppl_id = NEW.ppl_ref
--     AND cm.is_partner = true
--     AND cm.in_service = true
--   LIMIT 1;
--
--   IF v_owner_id IS NULL THEN
--     RAISE EXCEPTION 'Cannot resolve owner: no active partner for customer';
--   END IF;
--
--   -- 2. Get owner's primary branch
--   SELECT in_branch INTO v_owner_branch
--   FROM council_members
--   WHERE id = v_owner_id;
--
--   -- 3. Resolve customer_uuid from ppl.user_ref
--   SELECT p.user_ref INTO v_customer_uuid
--   FROM ppl p
--   WHERE p.ppl_id = NEW.ppl_ref;
--
--   -- 4. Create file_access row
--   INSERT INTO file_access (
--     file_id,
--     file_owner,
--     file_admin,
--     member_assistants,
--     external_assistants,
--     customer_uuid,
--     branches_access,
--     subers,
--     view_for_customer,
--     updated_at
--   ) VALUES (
--     NEW.file_id,
--     v_owner_id,
--     v_owner_id,
--     '{}',
--     '{}',
--     v_customer_uuid,
--     ARRAY[v_owner_branch],
--     '{}',
--     true,
--     NOW()
--   );
--
--   RETURN NEW;
-- END;
-- $$ LANGUAGE plpgsql SECURITY DEFINER;

-- ═══════════════════════════════════════════════════════════════════════════════
-- Trigger Function: fa_on_ppl_a_user_ref
-- ═══════════════════════════════════════════════════════════════════════════════
-- Fires: AFTER UPDATE OF user_ref ON ppl
-- Does: Updates customer_uuid on all linked file_access rows when customer gains/loses account
--
-- This is a TEMPLATE. To be implemented in a separate migration.
-- ═══════════════════════════════════════════════════════════════════════════════

-- Template signature (implementation deferred):
-- CREATE OR REPLACE FUNCTION fa_on_ppl_a_user_ref()
-- RETURNS TRIGGER AS $$
-- BEGIN
--   UPDATE file_access
--   SET customer_uuid = NEW.user_ref, updated_at = NOW()
--   WHERE file_id IN (
--     SELECT file_id FROM fd WHERE ppl_ref = NEW.ppl_id
--   );
--   RETURN NEW;
-- END;
-- $$ LANGUAGE plpgsql SECURITY DEFINER;

-- ═══════════════════════════════════════════════════════════════════════════════
-- Pending Items
-- ═══════════════════════════════════════════════════════════════════════════════
--
-- The following are defined in TABLE STRUCTURE but require separate migrations:
--
-- 1. org_users table — External user registry
--    Columns: id (uuid, PK), full_name (text), org_name (text), email (text),
--             is_active (boolean), created_at (timestamptz)
--    After creation, add FK constraint:
--      ALTER TABLE file_access
--      ADD CONSTRAINT file_access_external_assistants_fk
--      FOREIGN KEY (external_assistants) REFERENCES org_users(id);
--
-- 2. file_access_log table — Audit trail (AFTER UPDATE trigger required)
--    Columns: id (uuid, PK), file_id (uuid, FK), changed_at (timestamptz),
--             changed_by (uuid, FK), field (text), old_value (text), new_value (text)
--
-- 3. file_access_full view — Computes users_access + tasks_access
--    Uses:
--      array_distinct(
--        array_remove(
--          ARRAY[file_owner, file_admin] || member_assistants
--          || CASE WHEN view_for_customer = true
--               THEN external_assistants || COALESCE(ARRAY[customer_uuid], '{}')
--               ELSE '{}'
--             END
--          || (SELECT array_agg(DISTINCT assigned_uuid) FROM tasks
--              WHERE file_ref = fa.file_id AND NOT is_done),
--          NULL
--        )
--      ) AS users_access
--
-- 4. Rewrite 30+ _js views to use file_access_full instead of fd_access
--
-- 5. Update storage_check_doc_access() to read from file_access_full
--
-- 6. Trigger functions: fa_on_fd_a_insert, fa_on_ppl_a_user_ref
--
-- 7. Backfill from legacy fd_access (if applicable)
--
-- ═══════════════════════════════════════════════════════════════════════════════

```

---

## Constraints & Validation Rules

| Rule | Enforcement | Trigger/Function |
|---|---|---|
| Owner must be active partner | `is_partner = true AND in_service = true` | `fa_on_fd_a_insert` |
| Admin must be council member | FK → `council_members.id` | Table constraint |
| Member assistants must be attorneys | `is_attorney = true` for each UUID | Trigger validation (deferred) |
| External assistants must be pre-registered | FK → `org_users.id` (after org_users created) | Table constraint (deferred) |
| `subers` are soft constraint | Checked at notification dispatch time, not DB level | Application logic |
| `users_access` no NULLs/duplicates | `array_remove(..., NULL)` + `array_distinct(...)` | `file_access_full` view computation |

---

## Notes

1. **RLS is enforced at the view layer**, not the table. The `file_access` table itself allows authenticated SELECT; the three-gate predicate is implemented in `file_access_full` view and all `_js` views that consume it.

2. **`users_access` is never stored** — it is computed at query time in the `file_access_full` view. This avoids synchronization costs and keeps the table lean.

3. **Triggers are templates** — actual implementation deferred to separate migrations after dependencies (org_users table) are created.

4. **Backfill is optional** — only needed if migrating from legacy `fd_access`. If this is a fresh table, the trigger `fa_on_fd_a_insert` will populate new files automatically.

5. **Array constraints** — FK constraints on array columns (member_assistants → council_members, external_assistants → org_users) require triggers or application-level validation; they cannot be enforced directly at the DB level.

---

## Approval Required

Before applying this migration:

1. Confirm the `org_users` table exists or will be created separately
2. Confirm the backfill logic (or skip if starting fresh)
3. Confirm the trigger implementations (deferred)
4. Get approval from the team lead

**Once approved, apply via Supabase migrations directory:**

```bash
# File name: supabase/migrations/20260403_create_file_access_table.sql
# Then apply in Supabase dashboard or via CLI
```
