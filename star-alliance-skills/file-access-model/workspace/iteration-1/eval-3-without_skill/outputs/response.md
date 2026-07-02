---
type: Document
timestamp: 2026-07-02T12:28:13Z
---

# Adding File Access for an External Lawyer from a Partner Firm

## Overview

To grant a file to an external lawyer from a partner firm, there are **two prerequisites** that must be met before you can add them to any file:

1. **Their organization must be registered** in the system
2. **They must have a user account** (be registered in `org_users`)

Once these prerequisites are in place, you then add them to the specific file.

---

## Step-by-Step Workflow

### Step 1: Verify the External Lawyer is Pre-Registered in `org_users`

Before you can add an external lawyer to a file, they must exist in the `org_users` table. This is a **one-time setup** per external lawyer.

**What is `org_users`?**
- It's the registry of external users from organizations Lex Council is contracted with
- Each external user needs a UUID entry here before they can be added to any file
- Minimum required data per user:
  - `id` (UUID) — unique identifier
  - `full_name` — their name
  - `org_name` — their organization/firm name
  - `email` — contact email
  - `is_active` — boolean flag (should be `true`)
  - `created_at` — timestamp

**What to do:**
- If the external lawyer's firm/organization is new, confirm they have been registered in `org_users` first
- If they already have an entry there, you're ready to proceed to Step 2
- If they don't exist yet, contact your admin to create an `org_users` entry for them

---

### Step 2: Navigate to the File and Open Access Settings

Once the external lawyer is registered in `org_users`:

1. Find the file you want to share (navigate to the specific General File Node, Main File Node, Branch File Node, Sub File Node, or Atomic File Node)
2. Open the file's **access management interface** (typically a "Share", "Access", or "Permissions" button/panel — exact UI location depends on the page you're on)
3. Look for the **"External Assistants"** field or section

---

### Step 3: Add the External Lawyer as an External Assistant

In the file access settings:

1. **Locate the "External Assistants" field** — this is specifically for external users from partner firms
2. **Search or select** the external lawyer's name from the dropdown
   - The picker will display names from `org_users`
   - You can search by name or organization
   - Only active (`is_active = true`) users appear in the picker
3. **Confirm the selection** to add them to the `external_assistants` array for that file

**Important:** External lawyers are only added to `external_assistants` — not to `member_assistants` (which are for internal council members who are attorneys).

---

### Step 4: Verify the `view_for_customer` Flag (if applicable)

**What is this flag?**
- When `view_for_customer = false`, the file is marked as **internal-only**
- This exclusion automatically hides the file from:
  - All external assistants (including your newly added external lawyer)
  - The customer (if they have an account)
- When `view_for_customer = true` (the default), external assistants can see the file

**What to check:**
- If you want the external lawyer to see the file: **ensure `view_for_customer = true`** (this is the default)
- If the file should remain internal-only: leave `view_for_customer = false` (the external lawyer will not have access, even if added to `external_assistants`)

---

## Access Inheritance: Automatic Coverage of Sub-Files

**Key benefit:** If you add an external lawyer to a **parent file** (e.g., a Main File Node), they automatically inherit access to **all descendant files** (Branch File Nodes, Sub File Nodes, Atomic File Nodes) without needing to add them individually.

**How it works:**
- The system checks three access gates in order:
  1. **Branch access** — does the user belong to the right branch?
  2. **Direct access** — are they listed in `users_access` for this specific file?
  3. **Inherited access** — are they listed in `users_access` for any ancestor file?
- If the external lawyer appears in any ancestor's `users_access`, they can see all descendants

**Practical example:**
- If you add the external lawyer to a General File Node (GFN) level, they will automatically see all Main File Nodes, Branch File Nodes, Sub File Nodes, and Atomic Files under it
- If you add them to a lower level (e.g., Branch File Node), they only see that branch and its descendants, not siblings or parents

---

## User Roles Explained

When managing file access, there are **five distinct roles**. External lawyers from partner firms can only hold one role:

| Role | Who | Can Add | Notes |
|---|---|---|---|
| **Owner** | Council member with `is_partner = true` | No — for external lawyers | Controls financial/monetary ownership only |
| **Admin** | Any council member | No — for external lawyers | Day-to-day management; can differ from owner |
| **Member Assistants** | Council members who are attorneys (`is_attorney = true`) | No — for external lawyers | For internal team members only |
| **External Assistants** | Pre-registered org users from partner firms | **Yes — use this for external lawyers** | Can view files (unless `view_for_customer = false`) |
| **Customer** | The customer (`ppl.user_ref`) | No — automatic if they have an account | Auto-included if customer is a registered user |

---

## Common Scenarios

### Scenario 1: Share a Specific File with an External Lawyer
1. Verify the lawyer is in `org_users`
2. Open the file's access settings
3. Add them to `external_assistants`
4. Ensure `view_for_customer = true`
5. **Done** — they have access to that file

### Scenario 2: Share a Matter (GFN) and All Sub-Files
1. Verify the lawyer is in `org_users`
2. Open the General File Node (GFN) access settings
3. Add them to `external_assistants` on the GFN
4. Ensure `view_for_customer = true`
5. **Done** — they automatically inherit access to all MFN, BFN, SFN, and AFN files under it

### Scenario 3: Keep a File Internal-Only (Hide from External Lawyers)
1. If the file already has external assistants added
2. Set `view_for_customer = false`
3. **Done** — the file is now hidden from external assistants (they remain in the record but cannot view it)
4. When you're ready to share again, set `view_for_customer = true`

### Scenario 4: Multiple External Lawyers from the Same Firm
1. Each lawyer needs their own `org_users` entry (unique UUID, email, etc.)
2. Add each lawyer individually to the `external_assistants` array
3. Both will appear in the file's access list and can view the file (if `view_for_customer = true`)

---

## Important Constraints & Safeguards

**Before adding an external lawyer, confirm:**

| Check | Requirement | Why |
|---|---|---|
| **Pre-registered in `org_users`?** | UUID must exist in the `org_users` table | External assistants have a foreign key constraint to `org_users.id` |
| **`is_active = true`?** | The user record must have `is_active` set to `true` | Inactive users do not appear in the picker and cannot be added |
| **Correct role?** | They must be added to `external_assistants`, not `member_assistants` | Member assistants must be internal attorneys (`is_attorney = true`); external lawyers cannot hold this role |
| **Correct file level?** | Choose the right level (GFN vs. MFN vs. BFN, etc.) to add them | Think about inheritance: adding at GFN is simpler than adding at each BFN individually |
| **Visibility flag?** | Verify `view_for_customer = true` if you want them to see the file | Setting `view_for_customer = false` hides the file from all external assistants, regardless of the list |

---

## Technical Details (For Reference)

**How external lawyers are stored:**
- They are stored as a **UUID array** in the `file_access.external_assistants` column
- The file access system computes a virtual column called `users_access` (in the `file_access_full` view) that includes:
  - `file_owner`
  - `file_admin`
  - All members in `member_assistants`
  - All members in `external_assistants` (if `view_for_customer = true`)
  - The customer (if they have an account and `view_for_customer = true`)
  - Any task assignees for open tasks on the file

**Audit trail:**
- Every change to `external_assistants` is logged in the `file_access_log` table (append-only audit trail)
- The log records: which file, what changed, old value, new value, who made the change, and when

**Row-level security (RLS):**
- The system enforces access via RLS policies on the `file_access` table
- External lawyers can only view files where they appear in the computed `users_access` (or in an ancestor's `users_access`)
- The system automatically checks inheritance up to 4 levels (GFN → MFN → BFN → SFN)

---

## Summary

To add file access for an external lawyer:

1. **Check prerequisites** — Lawyer must be registered in `org_users` (contact your admin if not)
2. **Navigate to the file** — Open the file you want to share
3. **Add to External Assistants** — Select the lawyer from the picker and add them
4. **Verify visibility** — Confirm `view_for_customer = true` (default)
5. **Inheritance is automatic** — If you add them at a parent level, all sub-files are covered

**No additional steps needed.** The system automatically applies RLS and ensures they can only see files they're assigned to.

