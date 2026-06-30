# File Roles and the Exclusion Flag

## What Roles Can Be On a File?

Every file has **five role types** in the `file_access` table. All of them feed into the computed `users_access` virtual column.

| Role | Column | Type | Who Can Hold It | Default |
|---|---|---|---|---|
| **Owner** | `file_owner` | `uuid` | Council member with `is_partner = true` | Partner linked to the customer in `ppl` |
| **Admin** | `file_admin` | `uuid` | Any council member | Same as `file_owner` at creation |
| **Member Assistants** | `member_assistants` | `uuid[]` | Council members with `is_attorney = true` | `{}` (empty) |
| **External Assistants** | `external_assistants` | `uuid[]` | Pre-registered org users (`org_users` table) | `{}` (empty) |
| **Customer** | `customer_uuid` | `uuid` or `null` | The customer (if they have a user account) | Auto-resolved from `ppl.user_ref` |

Additionally, **task holders** are automatically derived at query time from the `tasks` table — they are not stored in `file_access` but are included in the computed `users_access`.

### Role Distinctions

- **Owner** = holds financial/monetary ownership only; no operational responsibility.
- **Admin** = manages the file day-to-day and can differ from the owner.
- **Member Assistants** = internal attorneys from the council; same-branch members surface first in the picker UI.
- **External Assistants** = users from organizations Lex Council is contracted with; must be pre-registered in the `org_users` table before they can be added.
- **Customer** = automatically included if the customer has a user account; NULL if they don't.

---

## How Does the Exclusion Flag Work?

The exclusion flag is a single boolean column called **`view_for_customer`** (default: `true`).

### When `view_for_customer = true` (default)

All roles are included in the computed `users_access`:
- File owner
- File admin
- Member assistants
- External assistants
- Customer (if they have an account)
- Task holders (auto-derived)

### When `view_for_customer = false`

The file is treated as **internal-only**. Both the customer and external assistants are **excluded** from `users_access`. More specifically:

- File owner, admin, member assistants, and task holders **remain** in access
- **Customer is excluded** from `users_access`
- **External assistants are excluded** from `users_access`

### Important Characteristics

1. **Single flag, dual effect** — There is no separate flag for external assistants. The one `view_for_customer` flag controls visibility for both customer and external parties together.

2. **Non-destructive exclusion** — When the flag is `false`, customer and external assistants are not removed from the table. Their UUIDs remain stored in those columns. If the flag is later re-enabled to `true`, they automatically regain access.

3. **Applied at query time** — The exclusion happens during computation of `users_access` in the `file_access_full` view, not at storage time.

4. **Per-file setting** — The flag is set independently on each file. A customer excluded on a child file does not inherit access even if included on the parent file.

### Pseudocode for `users_access` Computation

```sql
-- Simplified; see FILE-ACCESS-MODEL.md for full details
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

The result is always deduplicated and NULL-free. A user holding multiple roles appears exactly once.

---

## Soft Constraint on Subscribers

The `subers` column is an opt-in list of notification subscribers — a subset of `users_access`. If a user loses access (e.g., the flag changes or a role is revoked), they are not automatically removed from `subers`. Instead, **notification dispatch checks `subers ∩ users_access` at send time**, so stale entries are harmlessly skipped.

---

**References:**
- `FILE-ACCESS-MODEL.md` § 2 (Access Roles), § 4 (The Exclusion Flag), § 5 (`users_access` Composition)
- `FILE-HIERARCHY.md` § 5 (Access Inheritance and per-file flag behavior)
