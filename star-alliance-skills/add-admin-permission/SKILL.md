---
name: add-admin-permission
description: Add a new granular permission flag to admin_perms in the Lex Council app and wire it through every file that must stay in sync. Use this skill whenever the user asks to add a new permission, gate a page with a new flag, add an X_vap boolean, create an admin capability, restrict a feature to certain admins, or add a column to admin_perms. Also trigger on "make this admin-only", "grant X access to Y", "only these admins can see this", "add permission for Z", "lock this behind a permission". This skill exists because adding a permission requires 6 files in lock-step — if you miss any (especially the cm_ap_js view), the permission silently fails to hydrate in the Zustand store and the UI behaves as if the flag is always false.
---

# Lex Council: add an admin_perms permission

Adding a new granular permission — e.g., `notifications_vap`, `td_manual_advance`, `reports_vap` — requires **6 files in lock-step**. Missing any one causes silent failures because the admin UI hydrates permissions from a view, not from the underlying table, and several non-obvious parts of the frontend have to learn the new key too.

This skill is a checklist. Follow every step.

## Naming convention

- **`X_vap`** — gates "view / access the page" (most common). E.g., `td_vap`, `docs_vap`, `fd_vap`, `notifications_vap`.
- **`X_action`** — gates a specific action. E.g., `td_delete`, `fd_can_close_file`, `tr_certify`, `ppl_insert`.
- Prefix the permission with the module or feature short-code. See `apps/web/lib/permissions.ts` for the existing conventions before inventing a new prefix.

## Step 1: DB migration — add the column

```sql
ALTER TABLE public.admin_perms
  ADD COLUMN IF NOT EXISTS your_perm_vap boolean NOT NULL DEFAULT false;

COMMENT ON COLUMN public.admin_perms.your_perm_vap IS
  'Grants access to /admin/... — describes the capability in one line.';
```

Seed trusted users in the same migration if you know them:

```sql
UPDATE public.admin_perms
   SET your_perm_vap = true
 WHERE ap_uuid IN (
   SELECT id FROM public.council_members WHERE cm_email = 'atta@lexcouncil.com' LIMIT 1
 );
```

## Step 2: DB migration — rebuild cm_ap_js to surface the new column

**This is the single most commonly-missed step — it causes silent failures.** `cm_ap_js` is a view with an explicit column list; `SELECT * FROM admin_perms` does not auto-propagate. The frontend Zustand store (`useFilesStore`) hydrates from this view — if the column isn't listed, the permission reads as `undefined` / `false` in the UI, even though the DB value is `true`. Symptom: the nav entry stays disabled and the `PermissionGate` lock screen shows, with no error anywhere.

Get the current view definition:

```sql
SELECT pg_get_viewdef('public.cm_ap_js'::regclass, true);
```

Then `CREATE OR REPLACE VIEW public.cm_ap_js AS` with the full SELECT, adding `ap.your_perm_vap` to the column list before the `FROM public.council_members cm` clause. Preserve everything else.

Immediately after, pin SECURITY INVOKER (the advisor lints `SECURITY DEFINER` views as ERROR, and `CREATE OR REPLACE` can drop the option):

```sql
ALTER VIEW public.cm_ap_js SET (security_invoker = true);
```

Run `get_advisors type=security` after — expect zero lints. A `security_definer_view` ERROR on `cm_ap_js` means the `security_invoker` didn't survive — re-run the ALTER VIEW.

## Step 3: DB migration — rebuild cm_perms_js to surface the new column

**This step is as critical as Step 2 and is missed just as often.** `cm_perms_js` powers the `/admin/users/permissions` grid — the page where admins grant permissions to other admins. It has its own explicit column list. If you skip this step, the new permission column is invisible on that page and any attempt to grant the permission via the UI silently does nothing. Symptom: the column is simply absent from the permissions matrix — no error, no log.

Get the current view definition:

```sql
SELECT pg_get_viewdef('public.cm_perms_js'::regclass, true);
```

Then `CREATE OR REPLACE VIEW public.cm_perms_js AS` with the full SELECT, adding `ap.your_perm_vap` to the column list. Preserve everything else.

Immediately after, pin SECURITY INVOKER (`CREATE OR REPLACE` silently drops it):

```sql
ALTER VIEW public.cm_perms_js SET (security_invoker = true);
```

> **Why this is a separate step from Step 2:** `cm_ap_js` drives the Zustand store that gates UI access. `cm_perms_js` drives the permissions management page where admins grant each other access. They have different consumers and different column lists. Rebuilding one does not rebuild the other. This exact trap has caused two production incidents (2026-04-26 and 2026-05-01); both times `cm_ap_js` was updated and `cm_perms_js` was forgotten, resulting in `column ... does not exist` errors on the permissions page.


## Step 4: TypeScript — update CmAp interface

Edit `apps/web/types/cm-ap.ts`. Two changes:

(a) Add the new field to the `CmAp` interface in the appropriate grouped section:

```typescript
/* ── Your Module ── */
your_perm_vap: boolean  // brief one-line description
```

(b) Add the default in `DEFAULT_CM_AP`, in the same grouping:

```typescript
your_perm_vap: false,
```

Both are required. Missing the default means Zustand's initial state has `undefined` for this key, and truthiness checks like `cmAp.your_perm_vap === true` will behave unpredictably during first render.

## Step 5: permissions.ts — the registry

Edit `apps/web/lib/permissions.ts`. Four updates:

(a) Add to the `PermKey` union under the appropriate module comment:

```typescript
/* Your Module */
| 'your_perm_vap'
```

(b) If introducing a new module group, add it to the `PermModule` union and to the right module-list (`CORE_MODULES` for multi-perm cores, `STANDALONE_MODULES` for single-perm modules, `META_MODULES` for meta). Also add it to `ALL_MODULES` in display order.

(c) Add the `PERM_META` entry:

```typescript
your_perm_vap: {
  label: 'View Your Page',
  module: 'YourModule',
  denied_message: 'You need your_perm_vap permission to view this page.',
  description: 'Access to /admin/section/page. Can do X, Y, Z.',
},
```

The `label` is what admins see on the permissions management page. The `description` is the fuller explanation. The `denied_message` is what a user without the permission sees on the lock screen.

## Step 6: AdminNavPanel.tsx — the nav entry

Edit `apps/web/app/(admin)/admin/components/AdminNavPanel.tsx`. Two changes:

(a) Top of the component body, with the other `canXxx` consts, add:

```typescript
const canYourPage = cmAp.your_perm_vap === true
```

(b) Inside the matching `{activeTab === N && (...)}` block (0 = Home/Quick, 1 = Files, 2 = Users, 3 = Finances — verify in the file), add the `NavButton`:

```typescript
<WithHelp helpKey="nav.yourPage">
  <NavButton
    label="Your Page"
    iconBg={TAB_ICON_BG}
    hoverBorderColor={colors.navy}
    onClick={() => router.push('/admin/section/page')}
    disabled={!canYourPage}
    disabledReason="Requires your_perm_vap"
    icon={<MIcon name="material_icon_name" size={24} color={colors.navy} />}
  />
</WithHelp>
```

The button is **disabled**, not hidden, when the permission is missing. The entry shows users the capability exists and how to gain access. This is the admin UX convention.

## Step 7: The page itself — PermissionGate wrapper

Wrap the target page's default export:

```typescript
import PermissionGate from '.../components/permissions/PermissionGate'

function YourPageInner() { /* the real page content */ }

export default function YourPage() {
  return (
    <PermissionGate perm="your_perm_vap" mode="page">
      <YourPageInner />
    </PermissionGate>
  )
}
```

`mode="page"` renders a full-page lock screen when the user lacks the permission.

For action-level gating (e.g., a "Delete" button on an existing allowed page), use `mode="action"` — it disables or hides the element with a tooltip:

```typescript
<PermissionGate perm="your_perm_delete" mode="action">
  <button onClick={handleDelete}>Delete</button>
</PermissionGate>
```

## Step 8: RLS + column-level grants (if the page edits data)

If users with the new permission need to INSERT or UPDATE rows, add an RLS policy and column-level grants:

```sql
DROP POLICY IF EXISTS p_your_table_update_your_perm ON public.your_table;
CREATE POLICY p_your_table_update_your_perm ON public.your_table
  FOR UPDATE TO authenticated
  USING (EXISTS (
    SELECT 1 FROM public.admin_perms
    WHERE ap_uuid = (select auth.uid()) AND your_perm_vap = true
  ))
  WITH CHECK (EXISTS (
    SELECT 1 FROM public.admin_perms
    WHERE ap_uuid = (select auth.uid()) AND your_perm_vap = true
  ));

-- Column-level GRANT — narrow to just the columns that should be editable.
GRANT UPDATE (col1, col2, col3) ON public.your_table TO authenticated;
```

Prefer column-level grants over table-level. They prevent accidental edits to FK columns or audit fields even if the RLS policy is permissive.

For SECURITY DEFINER RPCs that wrap restricted operations, check the permission inside the function body rather than relying only on grants:

```sql
CREATE OR REPLACE FUNCTION public.your_action_rpc(p_arg text)
RETURNS bigint
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = 'public', 'private'
AS $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM public.admin_perms
    WHERE ap_uuid = auth.uid() AND your_perm_vap = true
  ) THEN
    RAISE EXCEPTION 'Insufficient permissions: your_perm_vap required';
  END IF;

  -- do the thing
END;
$$;

REVOKE EXECUTE ON FUNCTION public.your_action_rpc(text) FROM PUBLIC;
GRANT  EXECUTE ON FUNCTION public.your_action_rpc(text) TO authenticated;
```

Always pin `SET search_path` on SECURITY DEFINER functions. The advisor lints mutable search_path as a WARN.

## Step 9: Audit trail (optional, recommended for editable perms)

If the permission grants edit capability, add an audit table and AFTER UPDATE trigger on the target table:

```sql
CREATE TABLE IF NOT EXISTS public.your_table_audit (
  audit_id   bigserial PRIMARY KEY,
  at         timestamptz NOT NULL DEFAULT now(),
  actor_id   uuid NOT NULL,
  row_key    text NOT NULL,  -- PK of the changed row
  field      text NOT NULL,  -- column name
  old_value  jsonb,
  new_value  jsonb
);

CREATE OR REPLACE FUNCTION public.your_table_audit_on_update()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = 'public'
AS $$
DECLARE v_actor uuid := auth.uid();
BEGIN
  IF v_actor IS NULL THEN RETURN NEW; END IF;
  IF NEW.col1 IS DISTINCT FROM OLD.col1 THEN
    INSERT INTO public.your_table_audit (actor_id, row_key, field, old_value, new_value)
    VALUES (v_actor, NEW.pk::text, 'col1', to_jsonb(OLD.col1), to_jsonb(NEW.col1));
  END IF;
  -- repeat per editable column
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_your_table_audit ON public.your_table;
CREATE TRIGGER trg_your_table_audit
  AFTER UPDATE ON public.your_table
  FOR EACH ROW EXECUTE FUNCTION public.your_table_audit_on_update();
```

RLS-read the audit table to the same permission holders.

## Step 10: Run the advisor

```
get_advisors type=security
```

Common lints after a permission add:

- **`security_definer_view` on `cm_ap_js`** — the `security_invoker` got dropped. Re-run `ALTER VIEW public.cm_ap_js SET (security_invoker = true)`.
- **`function_search_path_mutable`** on any new SECURITY DEFINER function — add `SET search_path = '...'` to the function.
- **`policy_exists_rls_disabled`** — RLS wasn't enabled. Run `ALTER TABLE public.your_table ENABLE ROW LEVEL SECURITY`.

Fix before shipping.

## Step 11: Regenerate TypeScript types

Run the Supabase type generator (via the MCP or `supabase gen types typescript`) so `packages/supabase/src/types.ts` picks up the new column. The admin page's direct `.from('admin_perms')` queries (if any) need the new type to compile.

## Final checklist

Every one of these must be done:

- [ ] Migration added the column with `NOT NULL DEFAULT false`
- [ ] `cm_ap_js` view rebuilt to include `ap.your_perm_vap`
- [ ] `ALTER VIEW public.cm_ap_js SET (security_invoker = true)` ran
- [ ] `cm_perms_js` view rebuilt to include `ap.your_perm_vap`
- [ ] `ALTER VIEW public.cm_perms_js SET (security_invoker = true)` ran
- [ ] `CmAp` interface updated in `apps/web/types/cm-ap.ts`
- [ ] `DEFAULT_CM_AP` has the new key with `false`
- [ ] `PermKey` union has `'your_perm_vap'` in `apps/web/lib/permissions.ts`
- [ ] `PERM_META` has the full entry (label, module, denied_message, description)
- [ ] `ALL_MODULES` includes the module (and the right sub-list: `CORE_`, `STANDALONE_`, or `META_MODULES`) if it's new
- [ ] `AdminNavPanel.tsx` has `canYourPage` const + `NavButton` in the right tab
- [ ] Target page wrapped in `<PermissionGate perm="your_perm_vap" mode="page">`
- [ ] RLS policy + column grants + RPC permission checks added (if the permission grants edit capability)
- [ ] Audit trail added (recommended for edit permissions)
- [ ] Supabase advisor clean
- [ ] TypeScript types regenerated

Missing items 2–7 is a silent failure — the DB knows the user has the permission, but the UI never hears about it.

## Why this skill exists

On 2026-04-24 I added `notifications_vap` and forgot that `cm_ap_js` has an explicit column list, not `SELECT *`. The DB column was `true` for Atta, but the admin page kept locking him out because the view didn't surface the new column — Zustand hydrated `notifications_vap` as `undefined`, and `cmAp.notifications_vap === true` returned `false`. The only symptom was "the nav entry is disabled." No error, no log. 5 minutes of hunt through the render chain before the view omission clicked. Every step in this skill is a specific thing that has burned me or that I almost missed.
