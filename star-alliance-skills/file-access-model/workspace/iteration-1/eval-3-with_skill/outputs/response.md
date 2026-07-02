---
type: Document
timestamp: 2026-07-02T12:28:13Z
---

# How to Add File Access for an External Lawyer

## Overview

In Lex Council, when you need to grant a file to an external lawyer from a partner firm, you're assigning them as an **external assistant**. This is one of five access roles in the file access model.

The process has two parts:
1. **Pre-registration** — The external lawyer must exist in the `org_users` registry
2. **File assignment** — Add them to the file via the external assistants picker

---

## The Five Access Roles (Background)

Every file in Lex Council has five role types. External lawyers fit into one of them:

| Role | Who | How They're Added |
|---|---|---|
| **File Owner** | Partner (financial/monetary ownership) | Set automatically from the customer contact in the matter |
| **File Admin** | Council member (day-to-day manager) | Manually selected, usually same as owner at creation |
| **Member Assistants** | Internal attorneys from your firm | Manually selected from the picker |
| **External Assistants** | Users from partner firms (like your external lawyer) | Manually selected from the pre-registered `org_users` list |
| **Customer** | The client/customer with a user account | Automatically included if they have signed up |

---

## How It Works: Three Key Rules

### 1. Pre-Registration Requirement

Before an external lawyer can be assigned to **any** file, they must exist in the **`org_users`** registry. This is a secure allowlist maintained by your administrator.

**What this means:**
- Your organization/partner firm manages who is pre-registered
- Once registered, that person can be added to any file
- Registration includes: full name, email, organization, and active status
- Only active users (`is_active = true`) can be assigned

**Who handles this:** Contact your administrator to register the external lawyer (usually a one-time setup per person per partner firm).

### 2. The Exclusion Flag: `view_for_customer`

Every file has an **exclusion flag** called `view_for_customer`. This controls whether external parties can see the file.

**When it's ON (`true`):**
- External assistants CAN access the file
- The customer CAN access the file (if they have an account)

**When it's OFF (`false`):**
- File is internal only
- External assistants and customers are blocked, even if listed
- Other roles (owner, admin, member assistants) still have access

**What this means:** Even if an external lawyer is added to the external assistants list, they can only see the file if the `view_for_customer` flag is enabled. This is a safety valve for internal-only work.

### 3. Access Inheritance Down the Hierarchy

Files in Lex Council are organized in a 5-level hierarchy:

```
GFN  (root matter)
 ├── MFN  (major division)
 │    ├── BFN  (branch-scoped work)
 │    │    ├── SFN  (sub-task)
 │    │    │    └── AFN  (leaf task)
```

**Inheritance rule:** When you add an external lawyer to a **parent file** (e.g., a GFN or MFN), they automatically inherit access to all **child files** below it — without needing to add them separately.

**Example:** If you add an external lawyer as an external assistant on the main MFN (level 2), they can access all BFN, SFN, and AFN files under it automatically.

---

## The Workflow: Step-by-Step

### Step 1: Ensure Pre-Registration

1. Confirm with your administrator that the external lawyer exists in `org_users`
   - If they're not yet registered, ask your admin to register them
   - This includes their full name, email, firm name, and confirmation of active status
2. Once registered, their UUID is in the system and ready to use

### Step 2: Navigate to the File

1. Open the Lex Council app
2. Navigate to the file you want to grant access to (GFN, MFN, BFN, SFN, or AFN)
3. Look for the **file settings** or **access management** section (usually in a sidebar or drawer)

### Step 3: Add the External Assistant

1. In the file's access settings, find the **External Assistants** field
2. Click the picker/dropdown
3. Select the external lawyer from the `org_users` list
4. Their UUID is added to the `external_assistants` array for that file
5. Save the change

### Step 4: Check the Exclusion Flag (Optional but Recommended)

1. While you're in the access settings, verify the **`view_for_customer`** flag
2. Make sure it's set to **ON (`true`)** if you want the external lawyer to actually see the file
3. If it's OFF, they won't have access even though they're listed as an external assistant

### Step 5: Consider Inheritance

1. Think about the file hierarchy level you're granting access on
2. **If granting on a parent file (GFN or MFN):** The external lawyer automatically inherits access to all child files
3. **If granting on a leaf file (AFN):** Access is only to that specific file; other files in the hierarchy are not affected
4. Choose the level that matches your intent

---

## What the External Lawyer Sees

Once added with the exclusion flag enabled, the external lawyer will:

1. **See the file** in their file list (if using the Lex Council client)
2. **Access documents** associated with that file and child files (via inheritance)
3. **Participate in discussions** or task work linked to the file (depending on app features)
4. **NOT see** internal-only files where the exclusion flag is OFF

---

## Safety Notes

### Audit Trail
Every change to file access is logged in the **`file_access_log`** audit table. This records:
- Who made the change
- When it was made
- Which role was modified (e.g., `external_assistants`)
- The old and new values

### Remove Access
To revoke access, simply remove the external lawyer's UUID from the `external_assistants` array on that file. The change is logged immediately.

### Access Via Tasks
Files can also be accessed via **task assignment**. If an external lawyer is assigned a task on a file, they gain access to that file even without being listed as an external assistant (as long as the exclusion flag is ON). This is automatic.

---

## Common Scenarios

### Scenario 1: Grant Access to One File
- Pre-register the lawyer (if needed)
- Navigate to the file
- Add them to external assistants
- Verify `view_for_customer = true`

### Scenario 2: Grant Access to an Entire Matter Branch
- Pre-register the lawyer (if needed)
- Navigate to the **MFN** (main file node) at the top of that branch
- Add them to external assistants on the MFN
- **They automatically inherit access to all BFN/SFN/AFN files below it**
- Verify `view_for_customer = true` on the MFN (and any child files where you want them blocked can have the flag turned OFF individually)

### Scenario 3: Block the Client But Allow External Lawyer
- Add the lawyer to external assistants
- Set `view_for_customer = true` (so they can see)
- The customer will NOT see the file (they have a separate `customer_uuid` role)
- (This requires the customer to also NOT be assigned directly, or the exclusion applies to both customer and external assistants together)

### Scenario 4: Revoke Access
- Remove the lawyer's UUID from the `external_assistants` array
- Change is logged immediately
- They lose access (inheritance still applies upward to parent files they have direct access to)

---

## Technical Details (For Reference)

### How Access Is Computed
The system computes a virtual `users_access` list for each file by combining:
- File owner
- File admin
- Member assistants (internal attorneys)
- **External assistants** (if `view_for_customer = true`)
- Customer (if they have an account and `view_for_customer = true`)
- Task holders (anyone assigned a non-completed task on the file)

**Result:** The external lawyer sees the file if:
1. They're in the `external_assistants` list, **AND**
2. `view_for_customer = true`, **OR**
3. They're assigned a task on the file (regardless of the flag)

### RLS Protection
All file queries use **Row-Level Security (RLS)** to enforce access. The system checks:
1. **Gate 1 (Fast):** Is the user's branch in the file's `branches_access`?
2. **Gate 2 (Fast):** Is the user in the file's `users_access`?
3. **Gate 3 (Bounded):** Is the user in the `users_access` of any ancestor file? (max 4 lookups)

If any gate passes, access is granted.

---

## Questions to Ask Before Proceeding

- Is the external lawyer already registered in `org_users`? If not, contact your admin to register them first.
- Should they see the entire matter (assign at GFN/MFN level) or just a specific file?
- Should they see all files, or should some be blocked (check `view_for_customer` per file)?
- Do you need to audit the change later? (All changes are logged automatically.)

---

*Last updated: 3 April 2026 — based on FILE-ACCESS-MODEL.md and FILE-HIERARCHY.md*
