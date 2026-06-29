---
name: file-access-model
description: >
  Loads full context for the Lex Council file access model before any related work begins.
  Use this skill whenever the user mentions or asks about: file_access table, users_access,
  file_owner, file_admin, member_assistants, external_assistants, org_users, file_access_log,
  view_for_customer flag, RLS for files, file permissions, who can see a file, access inheritance,
  subers, subscriptions, the three-gate RLS pattern, or any migration related to file access.
  Also trigger when the user says "work on access", "build the access table", "write the access migration",
  "access model", "permission model", "who has access", or references anything about granting
  or revoking access to files. Load silently in the background — no need to announce the skill is running.
---

# File Access Model — Context Loader

This skill loads the full design context for the Lex Council `file_access` model so work can continue without re-explaining prior decisions.

## Step 1 — Load the reference docs immediately

Read both files in full before doing anything else:

- `lex_council/docs/references/FILE-ACCESS-MODEL.md` — table structure, roles, users_access composition, exclusion flag, RLS pattern, trigger definitions, org_users and file_access_log specs
- `lex_council/docs/references/FILE-HIERARCHY.md` — the 5-level hierarchy (GFN→AFN), ancestor ref columns, how Gate 3 RLS uses them for inheritance

These are the canonical source of truth for this domain. Everything below is a quick orientation — the docs have the full detail.

---

## Quick Orientation

### What has been decided and documented

**Table:** `file_access` — one row per file, replaces `fd_access`.

**Stored columns (explicit roles):**
- `file_owner` — partner only (`council_members.is_partner = true`), default from `ppl`
- `file_admin` — any council member, defaults to owner at creation
- `member_assistants` — attorney council members, manually added
- `external_assistants` — pre-registered org users (`org_users` table), manually added
- `customer_uuid` — auto-resolved from `ppl.user_ref`, null if no account
- `subers` — opt-in notification subscribers, subset of users_access
- `branches_access` — for branch-level RLS
- `view_for_customer` — exclusion flag: when false, both `customer_uuid` AND `external_assistants` are excluded from users_access

**Virtual (computed in `file_access_full` view, not stored):**
- `users_access` — deduped union of all stored roles, respects exclusion flag, includes task holders via subquery on `tasks`
- `tasks_access` — computed live from `tasks` table, no trigger needed

**RLS — three gates (short-circuit order):**
1. `branches_access @> ARRAY[user's branch]` — fast GIN, handles most council members
2. `auth.uid() = ANY(users_access)` — fast GIN, handles direct individual access
3. EXISTS on ancestor `file_access` rows via `fd.gfn_ref/mfn_ref/bfn_ref/sfn_ref` — handles inherited access, max 4 GIN lookups, no cascade triggers

**Constraints:**
- Owner must be active partner: `is_partner = true AND in_service = true`
- Member assistants must be attorneys: `is_attorney = true`
- External assistants must exist in `org_users`
- Stale subers are skipped at notification dispatch time (soft constraint)

### What is still pending (not yet built)

| Item | Status | Notes |
|---|---|---|
| `file_access` table — CREATE SQL | ⏳ Not written | Full migration SQL needed |
| `org_users` table | ⏳ Not written | External user registry; needed before external_assistants can be validated |
| `file_access_log` table | ⏳ Not written | Append-only audit trail; AFTER UPDATE trigger on file_access |
| `fa_on_fd_a_insert` trigger | ⏳ Not written | Creates file_access row on fd INSERT, resolves defaults |
| `fa_on_ppl_a_user_ref` trigger | ⏳ Not written | Updates customer_uuid when ppl.user_ref changes |
| `file_access_full` view | ⏳ Not written | Computes users_access + tasks_access; replaces fd_access in all _js views |
| Rewrite all 30+ `_js` views | ⏳ Not written | JOIN file_access_full instead of fd_access |
| Update storage function | ⏳ Not written | `storage_check_doc_access` reads from file_access_full |
| Backfill from fd_access | ⏳ Not written | Map existing columns; split file_assisstants → member_assistants + external_assistants |

---

## Rules when working in this domain

1. **All access reads come from `file_access` / `file_access_full`** — never from `fd` directly.
2. **`users_access` is virtual** — never store it as a column; always compute it in the view.
3. **No cascade triggers** — hierarchy inheritance is handled by Gate 3 of the RLS, not by propagating data downward.
4. **Show SQL and get approval before applying** — this is a RULES.md requirement for all migrations.
5. **The exclusion flag is one flag** (`view_for_customer`) — it covers both customer and external assistants together. Do not introduce separate flags.
6. **Subers are a soft constraint** — enforce at notification dispatch time, not at DB level.
