---
name: view-registry
description: "Gate every Supabase view query in the frontend through a typed registry (VIEWS dot key) so names are refactor-safe, discoverable, and never drift between the DB and the frontend. A new view = +1 registry key + 1 migration in the same commit. Every page gets its own dedicated view — no shared views, even when the SELECT body is identical. Append-only column rule: new columns go at the END of the SELECT list (Postgres error 42P16 on reorder). Use for: 'add a new view', 'rename a view', 'find which page reads this view', 'avoid view drift', 'wire a page to a view', 'list our views'. Pairs with add-new-view, supabase, supabase-postgres-best-practices, frontend-react-engineering."
metadata:
  version: 1.0.0
type: Skill
---

# View Registry — typed constants for every Supabase SELECT

As a Supabase project grows, views get renamed, deleted, or split — and raw SQL string
literals scattered across the frontend silently break. `from('admin_files_tasks_list')`
in twelve different pages means twelve different files to grep when the view is renamed
or split. The error is loud only if the rename was *recent*; old renames just show up
as "this page has been broken for three weeks."

A view registry centralizes **every view name as a typed constant**. `VIEWS.adminFilesTasksList`
is a TypeScript-level indirection: a rename is a one-line edit, TypeScript catches every
stale reference at compile time, and the registry doubles as the project's view catalog.

## The rule

**ALL Supabase SELECT queries in the frontend must reference a view name via `VIEWS.<key>`,
never a raw string literal.** A new view means **one migration + one registry key + at least
one frontend call site**, all in the same commit. Three moves, always together:

1. The migration (`CREATE OR REPLACE VIEW public.view_name AS …`)
2. The registry entry (`newKeyName: 'view_name'`)
3. The frontend call (`supabase.from(VIEWS.newKeyName).select(…)`)

Never a view without a registry key. Never a registry key without a migration. Never a
registry key without at least one call site.

## Registry pattern (TypeScript)

```ts
// apps/web/lib/view-registry.ts
export const VIEWS = {
  // Admin portal
  adminFilesTasksList:          'admin_files_tasks_list',
  adminFinancesTransactionsPending: 'admin_finances_transactions_pending',
  adminUsersActivityStream:     'admin_users_activity_stream',

  // Members portal
  membersFilesTasksList:        'members_files_tasks_list',
  membersAttendanceDaily:       'members_attendance_daily',

  // Clients portal
  clientsFilesDetail:           'clients_files_detail',

  // Foundation views (cross-cutting)
  folderAccess:                 'folder_access',
  notificationLog:              'notification_log',
} as const;

export type ViewKey  = keyof typeof VIEWS;
export type ViewName = (typeof VIEWS)[ViewKey];
```

The `as const` is not decoration — it gives every value the literal-string type, so
`supabase.from(VIEWS.adminFilesTasksList)` is type-checked end-to-end. Drop `as const`
and the whole indirection silently degrades to `string`.

## Query pattern

```ts
// CORRECT — view name is typed, refactor-safe, greppable from the registry
const { data } = await supabase.from(VIEWS.adminFilesTasksList).select('*');

// WRONG — raw string literal, breaks silently on rename
const { data } = await supabase.from('admin_files_tasks_list').select('*');
```

The wrong form is the bug the registry exists to prevent. If you find a raw view-name
string in a frontend file, treat it as a defect: register the view, replace the string,
ship in the same PR. There is no halfway.

## Naming convention for view names (the *values* in VIEWS)

**Page-specific views** — one per page, named for the page that consumes them:

```
{portal}_{section}_{entity}_{purpose}
```

- `portal` ∈ `{admin, members, clients}`
- Example: `admin_files_tasks_list`, `members_attendance_daily`, `clients_files_detail`

**Foundation views** — cross-cutting reads with no portal, named for the entity and role:

```
{entity}_{role}
```

- Example: `folder_access`, `notification_log`, `activity_stream`

The portal prefix is the *primary routing signal* for a new developer: "this view is for
the admin portal" is a stronger claim than "this view contains files." Don't drop the
prefix on shared-looking views; if a page needs cross-portal reads, give it a foundation
view of its own.

## No shared views rule

**Every frontend page gets its own dedicated view, even if the SELECT body is identical
to a sibling.** A page that adds one column tomorrow should not silently break a sibling
page that uses the same shared view. The pain of writing `CREATE OR REPLACE VIEW public.admin_files_X`
next to `members_files_X` is the protection: the two views can now diverge safely.

The two cases that *feel* like exceptions but aren't:

- **"Both pages just `SELECT *`."** Until the day one page wants `*, is_pinned` and the
  other page doesn't. The shared view becomes the change that breaks both.
- **"It's just one row of joins."** Then the cost of writing a second view is five minutes.
  The cost of debugging a shared-view regression is an afternoon.

If a shared view already exists, the fix is to split it: one migration per new view,
one registry key per view, each page rewires to its own. The split is mechanical.

## Sync discipline

When creating a new view, three steps in **one commit**:

1. **Migration:** `CREATE OR REPLACE VIEW public.view_name AS …` with the full SELECT,
   `security_invoker = true` pinned via `ALTER VIEW` immediately after.
2. **Registry:** add `newKeyName: 'view_name'` to `VIEWS` in `apps/web/lib/view-registry.ts`.
3. **Consumer:** at least one page or component reads via `VIEWS.newKeyName`.

All three steps go in the same commit — never a view without a registry key, never a
registry key without a migration, never a registry key without a call site. The PR
review checklist for any new view is literally these three lines.

## Append-only column rule

**When adding columns to an existing view: always add at the END of the SELECT list.
Never reorder existing columns.** Reordering triggers Postgres error 42P16 on
`CREATE OR REPLACE VIEW` when downstream objects depend on column order:

```
ERROR:  cannot drop column X of view ... because other objects depend on it
DETAIL: ... depends on column X of view ...
HINT:   Use DROP ... CASCADE if you really want to drop the column.
```

This is not a hint you follow on a Friday afternoon. The fix is to **append**:

```sql
-- WRONG — inserting a column mid-list breaks dependents
CREATE OR REPLACE VIEW public.admin_files_tasks_list AS
  SELECT f.id, f.title,            -- existing
         f.is_pinned,              -- new column in the middle = 42P16
         f.created_at, … ;

-- RIGHT — new columns go at the END
CREATE OR REPLACE VIEW public.admin_files_tasks_list AS
  SELECT f.id, f.title, f.created_at, … ,
         f.is_pinned;              -- appended, no reorder, no 42P16
```

If a reordering is genuinely required (a UI wants columns in a specific order), change
the **consumer's column selection**, not the view's SELECT order. `select('id, title,
is_pinned, created_at')` in the page does the reordering safely.

## Audit queries the registry enables

The registry is also a **discoverability tool**:

- "Which pages read this view?" — `grep VIEWS.<key>` across `apps/`.
- "What views does this page read?" — open the file, every view is a typed constant.
- "Which views exist?" — open the registry. No `pg_catalog` archaeology, no rummaging
  through `_js` view definitions.
- "Is anyone still reading the old view name?" — before a rename, `grep` for the
  string in the registry (which surfaces the value side), then update both ends.

## When to break the rules

There is **no sanctioned exception** to the `VIEWS.<key>` rule. Every raw view-name
string in the frontend is a defect to be fixed, not a tradeoff to be weighed. The cost
of the indirection is one extra identifier lookup; the cost of the bug it prevents is
a silent production page.

The append-only column rule has one exception: a view that's known to have no
downstream dependents and the reordering is part of an explicit deprecation — but in
that case, write the new view, migrate the consumers, drop the old one. The discipline
is the same.