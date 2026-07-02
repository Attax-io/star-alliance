---
type: Document
timestamp: 2026-07-02T12:28:13Z
---

# File Access Model: Roles and Exclusion Flag

## What Roles Can Be on a File

Every file in Lex Council has five distinct role types, all of which feed into the computed `users_access` list:

| Role | Column | Type | Who Can Have It | Details |
|---|---|---|---|---|
| **Owner** | `file_owner` | `uuid` | Council member with `is_partner = true` | Financial/monetary ownership only. No operational responsibility. Auto-resolved from the customer (`ppl`) at file creation. |
| **Admin** | `file_admin` | `uuid` | Any council member | Manages and follows up the file day-to-day. Can differ from owner. Defaults to same as `file_owner` at creation. |
| **Member Assistants** | `member_assistants` | `uuid[]` | Council members with `is_attorney = true` | Internal attorneys from the same branch surface first in the picker. Array allows multiple. |
| **External Assistants** | `external_assistants` | `uuid[]` | Registered org users (`org_users` table) | Users from organizations Lex Council is contracted with. Must be pre-registered in `org_users` before they can be added. Array allows multiple. |
| **Customer** | `customer_uuid` | `uuid \| null` | Customer with an account (`ppl.user_ref`) | Automatically included if the customer has a user account; NULL if they don't. Auto-resolved from `ppl` at file creation. |

### Additional Access Derived at Query Time

**Task Holders** — Users assigned to active (non-completed) tasks on the file are automatically included in `users_access` at query time. These are derived from the `tasks` table (where `is_done = false`), not stored in `file_access`.

---

## How the Exclusion Flag Works

The **`view_for_customer`** boolean flag controls all external party visibility. It is stored in the `file_access` table with a default value of `true`.

### Behavior

**When `view_for_customer = true` (default):**
- External parties have access to the file
- Both `external_assistants` and `customer_uuid` are included in the computed `users_access`

**When `view_for_customer = false` (internal-only mode):**
- The file is hidden from all external parties
- Both `customer_uuid` **and** `external_assistants` are **excluded** from `users_access`
- They are **not removed** from the table — the roles remain stored unchanged
- If the flag is re-enabled later, they regain access automatically with no additional work

### Key Points

- **Single flag, comprehensive control** — There is no separate flag for external assistants; `view_for_customer` gates both customer and external assistant visibility
- **Non-destructive** — Excluded parties are simply not added to the computed access list, not deleted from the table
- **Reversible** — Re-enabling the flag restores access immediately without re-entry of contact information

### Computation in `file_access_full` View

The `users_access` is computed in the `file_access_full` view using this logic (pseudocode):

```sql
array_distinct(
  array_remove(
    ARRAY[file_owner, file_admin]
    || member_assistants
    || CASE WHEN view_for_customer = true
         THEN external_assistants || COALESCE(ARRAY[customer_uuid], '{}')
         ELSE '{}'
       END
    || (SELECT array_agg(DISTINCT assigned_uuid)
        FROM tasks
        WHERE file_ref = fa.file_id AND NOT is_done),
    NULL
  )
)
```

The result is always deduplicated (no duplicates) and NULL-free. A user holding multiple roles (e.g., admin who also has a task) appears exactly once in `users_access`.

---

## Summary

- **Five stored roles** + **task-derived access** = the complete access set
- **`view_for_customer` flag** provides single-toggle control over all external visibility
- **No destructive exclusion** — external parties are simply filtered out of `users_access` when the flag is off, not removed from the table
- **Inherited hierarchy access** — Access on parent files is automatically inherited by descendant files via RLS predicates, not via cascade triggers
