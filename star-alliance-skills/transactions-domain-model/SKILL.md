---
name: transactions-domain-model
description: >
  Loads the complete Lex Council transactions domain model before any transaction-related work begins.
  Use this skill whenever the user mentions or asks about: transactions, transaction types, safe transactions,
  normal transactions, advances, deposits, withdrawals, expenses, income, transaction form, batch transactions,
  agree/agreement, certify/certification, action_required_user_inquestion, done_by, transaction_to,
  transaction views, transaction tabs (Personal, Pending, Approval, Certification, Safe, History),
  TransactionFormModal, BatchTransactionModal, TransactionContainerV8, TransactionActionBar,
  tr_on_tr_b_iu trigger, transaction templates, or any transaction-related bug, feature, or refactor.
  Also trigger when the user says "work on transactions", "fix a transaction bug", "add a transaction feature",
  "transaction page", or references any file under finances/. Load silently in the background — no need to
  announce the skill is running.
metadata:
  version: 1.3.0
---

# Transactions Domain Model

> ⚠️ **Schema-name staleness (this model was written ~April 2026, BEFORE the 2026-05-24 v2 DB-naming
> overhaul).** The *concepts* below — 13 types, the three-gate Create→Agree→Certify lifecycle, the
> trigger-owns-derived-fields rule, the tab views, the two form modals — are still accurate. The
> **table / view names were pre-v2 and GONE on current `main`; as of 2026-06-21 they have been
> verified against the live `information_schema` and corrected in §5/§6 below.** Mapping (live-checked
> 2026-06-21, project `bqgrpnsvplvicnmzxwkm`):
> - the `_js` view suffix is **retired** — all six `transactions_*_js` views are DROPPED. v2 splits the
>   old single page across the **admin** and **members** portals, each with its own `{portal}_{section}_{entity}_{purpose}` view:
>   `transactions_approval_js` → `admin_finances_transactions_approval`,
>   `transactions_certification_js` → `admin_finances_transactions_certification`,
>   `transactions_safe_js` → `admin_finances_transactions_safe`,
>   `transactions_history_js` → `admin_finances_transactions_history`,
>   `transactions_pending_js` → `admin_finances_transactions_pending`,
>   `transactions_personal_js` → `members_finances_transactions_personal`,
>   `transactions_container_js` → `admin_files_transactions_detail`.
> - `council_members` → `users` (member identity); `n_name` columns → resolve via the v2 member view
> - `fd` / `fd_access` / `fd_access_js` → `folders` / `folder_access`
> - `admin_perms` / `cm_ap` → v2 permission model (`user_permissions`, `has_perm`); `branches_js` → `branches`
> - `transaction_templates` table → DROPPED; templates live in the generic `templates` table (admin list view `admin_templates_list`)
> - **Still live & verified-correct:** the `tr_on_tr_b_iu` trigger, and the columns
>   `action_required_user_inquestion`, `done_by`, `transaction_to`, `payment_for_fees`, `on_customer_by_agreement`.
> - **Writes:** as of 2026-06-19 the app routes ALL writes through `callServerRpc → /api/rpc` (server
>   cookie client) to dodge the Safari `navigator.locks` wedge — not the per-route `createAdminClient()`
>   pattern §9 describes. Treat §9's routes as the historical shape; confirm the current transport.
>
> The view *names* are now live-corrected; the per-view **column lists and exact WHERE semantics** were
> NOT re-verified (the old "45-column, zero-drift" claim in §5 is pre-v2 and no longer holds now that
> admin/members views diverged). **Trust the model, trust the corrected names, re-check column shapes.**

This skill provides the complete mental model of the Lex Council transactions subsystem. Read this
before touching any transaction-related code, view, trigger, or API route. The system is non-trivial —
there are 13 transaction types, a three-gate lifecycle, six tab views with permission-tier gating,
a BEFORE INSERT/UPDATE trigger that owns several derived fields, and two form modals (single + batch)
with multi-phase wizards.

When you need deeper detail on a specific area, read the relevant reference file in `references/`.

---

## 1. Transaction Types

There are 13 transaction types, divided into two modes:

**Normal types** (tied to a specific file via `file_ref`):

| ID | Arabic | English | Notes |
|----|--------|---------|-------|
| 1 | مصروف | Expense | |
| 2 | وارد | Income | |
| 6 | تسوية | Settlement | |
| 7 | أمر دفع | Payment Order | |
| 8 | مرتجعات | Returns | |
| 10 | أتعاب متعاقد عليها | Contracted Fees | |
| 13 | استرداد مصروفات | Expense Refund | |

**Safe types** (tied to the branch safe via `safe` column; `file_ref` is auto-set to the branch's GFN file):

| ID | Arabic | English | Notes |
|----|--------|---------|-------|
| 3 | إيداع بحسابي بالشركة | Deposit | |
| 4 | سحب من حسابي بالشركة | Withdrawal | |
| 5 | أخذ عهدة | Advance Added | Advance type |
| 9 | إرجاع عهدة | Advance Returned | Advance type |

Constants in code:
- `NORMAL_TYPE_IDS = [1, 2, 10, 8, 7, 13, 6]` — used by TransactionFormModal, BatchTransactionModal, template validation
- `SAFE_TYPE_IDS = [3, 4, 5, 9]` — same consumers; also `view-modes.ts` for the Safe tab filter
- `ADVANCE_TX_TYPES = [5, 9]` — subset of safe; these are the advance types with special `transaction_to` semantics

**Terminology:** The project uses "safe" (not "wallet") for these types. A rename from wallet→safe
was completed on 2026-04-24 across all code, types, constants, and UI strings. The only surviving
"wallet" reference is the Material Icon name `account_balance_wallet` used for the Safe tab icon.

---

## 2. Three-Gate Lifecycle

Every transaction passes through three gates in order: **Create → Agree → Certify**.

### Gate 1: Create
- Any user with file access can create a transaction via `TransactionFormModal` or `BatchTransactionModal`.
- Payload goes to `POST /api/transactions/create` which uses `createAdminClient()` (service-role) because
  the `transactions` table has no INSERT RLS policy for `authenticated`.
- The API validates `transactionType`, `amount`, `fileRef`, and checks file access via `checkFileAccess()`.
- `is_agreed_on` defaults to `true` on INSERT (legacy Flutter behavior). The only exception is admin-created
  safe advances (types 5/9) where the admin acts on behalf — these set `is_agreed_on = false` because
  the recipient must confirm they received the advance.
- `is_certified` always starts `false` — certification is never at-create (as of April 2026; inline
  certify-at-create is planned but not yet shipped).
- `created_by` is always `auth.uid()` (the logged-in user).

### Gate 2: Agree
- Agreement means "the person whose real-world action is recorded confirms it happened."
- `action_required_user_inquestion` identifies who must agree. Enforced by the DB trigger (see §4).
- **Self-agree:** The action-required user agrees on their own transaction.
- **Admin agree on behalf:** An admin with `cmAp.tr_agree_on_transactions` can agree for another member.
  The bulk-agree route (`/api/transactions/agree`) additionally checks `council_members.allow_admin_conscent`.
  The single-transaction agree path (`agreeOnTransaction` → `/api/transactions/update`) does NOT check
  consent (Model A from Phase 0 vault log). This inconsistency is documented and deliberate.
- One-way only — once agreed, cannot be un-agreed.
- Mutation: `agreeOnTransaction(id)` → sets `is_agreed_on = true`, `is_agreed_on_at = now()`.
  The trigger backfills `agreed_on_by_n_name`.

### Gate 3: Certify
- Certification is the final seal — an admin with `cmAp.tr_certify` marks the transaction as verified.
- **Prerequisite:** `is_agreed_on` must be `true` before certification. Enforced server-side in
  `/api/transactions/certify`.
- Mutation: `certifyTransactions(ids)` → sets `is_certified = true`, `certified_at = now()`,
  `certified_by = auth.uid()`. Trigger backfills `certified_by_n_name`.
- Bulk certify is supported via `useTransactionsBulkCertify` hook + `TransactionsBulkActionBar`.

---

## 3. Key Actors in a Transaction

A transaction has up to four actor roles:

| Role | Column | Meaning |
|------|--------|---------|
| **Creator** | `created_by` | The user who entered the transaction into the system |
| **Doer** | `done_by` | The person who performed the real-world action (e.g., spent money) |
| **Recipient** | `transaction_to` | The person on the other end (e.g., received an advance) |
| **Action-Required** | `action_required_user_inquestion` | The person who must confirm the transaction happened (DB-enforced) |

For most types, `done_by = action_required_user_inquestion` (the doer confirms their own action).
For safe advance types (5, 9), `transaction_to = action_required_user_inquestion` (the recipient
confirms they received/returned the advance).

**Admin-on-behalf pattern:** When an admin creates a transaction for another member:
- `created_by` = admin's UUID
- `done_by` = the member's UUID (for normal types) OR admin's UUID (for safe advances, since the
  admin hands out/receives cash)
- `transaction_to` = the member's UUID (for safe advances)
- `action_required_user_inquestion` = DB-enforced (see §4)

---

## 4. The `tr_on_tr_b_iu` Trigger

`private.tr_on_tr_b_iu()` is a BEFORE INSERT/UPDATE trigger on `public.transactions`. It is the single
source of truth for several derived fields. The frontend should NOT send these fields — the trigger
overrides whatever the client provides.

**What the trigger does (in order):**

1. **Action-required user guard** (added 2026-04-24):
   - Types 5, 9 → `NEW.action_required_user_inquestion := NEW.transaction_to`
   - All other types → `NEW.action_required_user_inquestion := NEW.done_by`
   - This is authoritative. No matter what the client sends, the DB enforces the correct value.

2. **Flag derivation:**
   - `action_required` = `NOT NEW.is_agreed_on` (true when agreement is still pending)
   - Other boolean flags as needed

3. **Name lookups:**
   - `done_by_n_name` from the v2 member identity (`users` / the v2 member view) where `id = NEW.done_by`
   - `to_n_name` from the v2 member identity where `id = NEW.transaction_to`
   - `created_by_n_name` from the v2 member identity where `id = NEW.created_by`
   - `agreed_on_by_n_name` (on UPDATE when `is_agreed_on` flips to true)
   - `certified_by_n_name` (on UPDATE when `is_certified` flips to true)
   - *Source note:* pre-v2 these read `council_members.n_name` (table + column now gone); the `*_n_name` output columns persist — verify the exact v2 source column against live schema.

4. **Aggregation updates:**
   - `tr_update_counter` increment
   - Other counters as needed

**Key implication for frontend developers:** Never include `action_required_user_inquestion`,
`action_required`, or any `*_n_name` field in create/update payloads. The trigger handles them.
The create route still accepts `action_required_user_inquestion` for backward compatibility but
the trigger immediately overwrites it.

---

## 5. Six-Tab View Architecture

The transactions page uses six tabs, each backed by its own Supabase view with permission-tier
filtering baked into the WHERE clause (defense-in-depth).

> **View names below are v2-live (verified 2026-06-21).** The Filter/Special columns describe the
> *pre-v2 concept* and were not re-verified against the new view bodies — treat them as the intent,
> not a column-level guarantee.

| Tab | View (v2-live) | Permission | Filter | Special |
|-----|------|-----------|--------|---------|
| **Personal** | `members_finances_transactions_personal` | Always permitted | `auth.uid() = ANY(user_concerned)` + `is_certified = true` | Certified-only for the current user (members portal) |
| **Pending** | `admin_finances_transactions_pending` | Always permitted | `auth.uid() = ANY(user_concerned)` + `(NOT is_agreed_on OR NOT is_certified)` | User's own unfinished transactions |
| **Approval** | `admin_finances_transactions_approval` | `tr_agree_on_transactions` | `is_agreed_on = false` | Has extra `allow_admin_conscent` column |
| **Certification** | `admin_finances_transactions_certification` | `tr_certification_vap` | `is_certified = false` | Shows bulk-certify tickboxes |
| **Safe** | `admin_finances_transactions_safe` | `tr_safe_vap` | `transaction_type IN (3,4,5,6,9)` | Safe types only |
| **History** | `admin_finances_transactions_history` | `tr_history_vap` | None (all transactions) | Full unfiltered view |

**Container view:** `admin_files_transactions_detail` is used by `TransactionContainerV8` (the detail popup)
and the activity timeline. It has a wider WHERE clause: `(tr_history_vap OR tr_safe_vap OR tr_certification_vap OR user_concerned OR ar_owner)`.

**Tab order:** Personal → Pending → Approval → Certification → Safe → History

**Column shapes diverged in v2.** The pre-v2 "all views share one 45-column SELECT, zero drift" claim
no longer holds — the admin and members views are now distinct surfaces. Re-read the live view body
before relying on any specific column.

**Default view mode on refresh:** `personal` (hardcoded in `transactions-store.ts`). This ensures
every user lands on their own transactions after a browser refresh, not on a permission-gated tab
they may not have access to. Changing this default to `safe` caused a bug (see vault log
`2026-04-17_transactions-default-tab-sticks-to-safe-on-refresh.md`).

**File-access base gate** (pre-v2 shape — `council_members`→`users`, `fd_access_js`→`folder_access`
in v2; the v2 canonical path is the `user_can_see_file` helper, see V2-CONVENTIONS.md):
```
branches_access @> ARRAY[(SELECT u.in_branch FROM users u WHERE u.id = auth.uid())]
OR auth.uid() = ANY(users_access)
OR EXISTS (
  SELECT 1 FROM folder_access anc
  WHERE anc.file_id = ANY(ARRAY[gfn_ref, mfn_ref, bfn_ref, sfn_ref])
    AND auth.uid() = ANY(anc.users_access)
)
```

---

## 6. Frontend Architecture

### TransactionFormModal (single transaction create/edit)
- Location: `apps/web/app/(admin)/admin/finances/components/TransactionFormModal.tsx`
- 8-phase wizard: Recipient → Type → Title → Amount → Description → Date → Branch/File → Review
- Modes: `'normal' | 'safe'` (controlled by `TransactionFormMode` in `transactions-store.ts`)
- Safe mode auto-sets `fileRef` to the branch's GFN file (`safeFileRef` from `useTransactionLookups`)
- For safe advances (types 5, 9), `done_by` = admin, `transaction_to` = selected member,
  `is_agreed_on = false`
- Does NOT send `action_required_user_inquestion` — trigger is authoritative
- Opened via `useTransactionsStore.openSlideOver(mode, editingTransaction?, prefill?)`

### BatchTransactionModal (multi-row batch create)
- Location: `apps/web/app/(admin)/admin/finances/components/BatchTransactionModal.tsx`
- 4-phase wizard: Titles+Amounts → Mode+Type per row → Date+Branch+People → File+Review
- Per-row mode: each row independently picks Normal or Safe (v2 refactor, 2026-04-17)
- Mode flip resets type on that row (different type lists per mode)
- Safe rows auto-get `safeFileRef`; normal rows need manual file pick
- Submit calls `createTransactionsBatch()` which sequentially POSTs each row

### TransactionContainerV8 (detail popup)
- Location: `apps/web/app/(admin)/admin/finances/components/TransactionContainerV8.tsx`
- Three-layer layout: Header (navy) → Tab strip (white) → Action bar (bottom icons)
- 5 tabs: Details, Agreement, Proof, Comments[n], Audit[n]
- Header ToggleChips for: Agreed/Pending, Certified, Proof, Action Required, On Customer
- Agreement tab has inline Agree button (Model A — no consent check)
- `ConfirmAgreePopup` for one-way agree confirmation

### TransactionActionBar (per-row actions in table)
- Location: `apps/web/app/(admin)/admin/finances/components/TransactionActionBar.tsx`
- 6 buttons: Edit, Agree, Certify, Open File, Share, View Container
- Edit gated by `canEdit` (creator-only; `r.createdBy === currentUserUid`)
- Agree shown when `canAgreeOnRow && !r.isAgreedOn && r.actionRequired`
- Certify shown when `canCertify && !r.isCertified && r.isAgreedOn`

### Transaction Templates
- Stored in the generic `public.templates` table (DB) — per-user, max 200; the pre-v2
  `transaction_templates` table is DROPPED. Admin list view: `admin_templates_list`.
- Template ref 1 = transaction template; refs 2-4 reserved for other kinds
- Validation in `apps/web/app/api/templates/_helpers.ts`:
  - Each row needs `title`, `amount > 0`, `txMode` ('normal'|'safe'), `transactionType`
  - Normal rows require non-null `fileRef`; safe rows require null `fileRef`
  - Safe advance types (5, 9) with `asAdmin=true` require `transactionTo`
- UI: `TemplatesModal.tsx` for save/load/delete

---

## 7. Permissions Map

| Permission Key | What It Gates |
|---|---|
| `tr_create_transactions` | Can create transactions (currently not enforced in create route — access is file-access-gated only) |
| `tr_agree_on_transactions` | Can agree on behalf of another member (admin agree) |
| `tr_certify` | Can certify transactions |
| `tr_safe_vap` | Can view the Safe tab |
| `tr_certification_vap` | Can view the Certification tab |
| `tr_history_vap` | Can view the History tab |
| `tr_summary_vap` | Can view the KPI summary bar |

Personal and Pending tabs are `alwaysPermitted` — every authenticated user sees them.

The Approval tab is gated by `tr_agree_on_transactions` (same permission as the agree action).

---

## 8. Common Pitfalls and Gotchas

1. **Never set `action_required_user_inquestion` from the frontend.** The trigger is the single
   source of truth. The create route still accepts it for backward compatibility but the trigger
   immediately overwrites it. This was the root cause of the "blacked-out approval buttons" bug
   (2026-04-24).

2. **`is_agreed_on` defaults to `true`.** Most transactions land already agreed. The only exception
   is admin-created safe advances where the recipient must confirm. If you add new transaction types,
   think carefully about whether they need the agree gate.

3. **Safe file resolution is branch-of-user, not branch-of-row.** `safeFileRef` is fetched once
   for `cmAp.in_branch`. If a batch row is overridden to a different branch, it still uses the
   user's current branch's GFN file. Known limitation.

4. **View mode default must be `personal`.** Changing it to any permission-gated tab (like `safe`)
   causes users without that permission to see an empty/broken page after refresh.

5. **The Approval tab has an extra column.** `admin_finances_transactions_approval` exposes
   `allow_admin_conscent` — other views do NOT. The history page uses `APPROVAL_SELECT_COLS`
   (which appends this column) only when `viewMode === 'approval'`.

6. **`fileRef` is required for all transactions** including safe types. For safe types, the
   form auto-resolves `fileRef` to the branch's GFN file (pre-v2: `branches_js.b_gfn_link`;
   v2: the `branches` table — verify the current GFN-link column). The create route validates
   `fileRef` is present and rejects without it.

7. **Mode flip resets type.** In both modals, switching between Normal and Safe clears the
   selected `transactionType` because the type lists are disjoint.

8. **Model A vs Model C inconsistency.** The single-transaction agree path (via
   `agreeOnTransaction` → `/api/transactions/update`) uses Model A (admin power alone, no consent
   check). The bulk-agree path (`/api/transactions/agree`) uses Model C (checks
   `allow_admin_conscent`). This is documented as deliberate; reconciliation is a future task.

9. **Consent-dimming in the Approval tab.** Rows where `allow_admin_conscent !== true` are rendered
   at 65% opacity (`isRowConsentBlocked`). The admin can still see them but cannot tick/agree.
   This is NOT a bug — it's the visual signal that the member hasn't opted in.

10. **`user_concerned` array.** Each transaction has a `user_concerned` UUID array (populated by
    the trigger) containing all relevant parties. Personal and Pending tabs filter on
    `auth.uid() = ANY(user_concerned)`.

---

## 9. API Routes

| Route | Method | Purpose |
|-------|--------|---------|
| `/api/transactions/create` | POST | Create a single transaction |
| `/api/transactions/update` | POST | Update a transaction (edit, single agree) |
| `/api/transactions/certify` | POST | Bulk certify (accepts `{ ids: number[] }`) |
| `/api/transactions/agree` | POST | Bulk agree (accepts `{ ids: number[] }`) — checks consent |
| `/api/transactions/comment` | POST | Add/delete transaction comments |

As of 2026-06-19, all write routes go through `callServerRpc` → `/api/rpc` (server cookie client) to
dodge the Safari `navigator.locks` wedge; the per-route `requireAuth()` + `createAdminClient()`
(service-role) shape is the historical pre-2026-06-19 transport. The route paths and methods in the
table above are unchanged. File access is checked via `checkFileAccess()` on the transaction's `file_ref`.

---

## 10. Store

`useTransactionsStore` (Zustand, `apps/web/store/transactions-store.ts`) manages:
- `viewMode: ViewMode` — current tab (default: `'personal'`)
- Filter state: `typeFilter`, `certFilter`, `agreedFilter`, `proofFilter`, `branchFilter`,
  `searchQuery`, `dateFrom`, `dateTo`, `memberFilter`
- Pagination: `currentPage`, `pageSize` (25)
- Slide-over state: `slideOverOpen`, `slideOverMode`, `editingTransaction`, `prefill`
- Batch selection: `selectedRows` for bulk certify/approve
- Saved views and templates (localStorage-backed)
- `setViewMode(m)` resets `currentPage`, `certFilter`, and `typeFilter`
- `resetFilters()` clears all filters and resets page

---

## 11. Key Vault Logs (Chronological)

For deep context on past decisions, read these vault logs:

| Date | File | Topic |
|------|------|-------|
| 2026-04-17 | `batch-transaction-per-row-mode` | Per-row Normal/Safe in BatchTransactionModal |
| 2026-04-17 | `transactions-default-tab-sticks-to-safe-on-refresh` | Why default viewMode must be personal |
| 2026-04-17 | `transaction-type-reset-on-edit-mode` | Type reset when switching modes |
| 2026-04-18 | `templates-phase-0-migration` through `phase-7-docs` | Transaction templates system |
| 2026-04-18 | `transaction-title-default-by-type` | Default titles per transaction type |
| 2026-04-19 | `tr-agree-on-transactions-phase0` | Model A decision for admin agree |
| 2026-04-19 | `tr-agree-on-transactions-phases-1-3` | Agree UI wiring in container + action bar |
| 2026-04-19 | `phase-1-per-tab-transaction-views` | Six per-tab views (defense-in-depth) |
| 2026-04-19 | `transaction-container-v8` | Container redesign to v8 language |
| 2026-04-19 | `transactions-bulk-certify` | Bulk certification flow |
| 2026-04-24 | `action-required-user-guard` | Trigger guard + 186-row data fix |
| 2026-04-24 | `transactions-approval-tab` | Approval tab with consent gating |
| 2026-04-24 | `wallet-to-safe-rename` | Terminology rename across codebase |
| 2026-04-24 | `legacy-data-consistency-fix` | 464 legacy rows fixed for consistency |

---

## Changelog

| Version | Change |
|---|---|
| 1.3.0 | §4 name-lookup source rewritten from `council_members.n_name` → v2 member identity (`users` / v2 member view); the `*_n_name` output columns persist, exact v2 source column flagged for live re-check. §9 write transport corrected to `callServerRpc` → `/api/rpc` (2026-06-19); per-route `requireAuth()` + `createAdminClient()` service-role shape marked historical. Route paths and methods unchanged. |
| 1.2.0 | **Per-name v2 rewrite (the deferred 1.1.0 follow-up), now done — names verified live against `information_schema` 2026-06-21 (project `bqgrpnsvplvicnmzxwkm`).** Proven DEAD and corrected in-body: all six `transactions_*_js` views + `transactions_container_js` (→ `admin_finances_transactions_{approval,certification,safe,history,pending}` / `members_finances_transactions_personal` / `admin_files_transactions_detail`), `fd_access_js` (→ `folder_access`), `branches_js` (→ `branches`), `transaction_templates` table (→ generic `templates` / `admin_templates_list`). Proven STILL-LIVE (kept): `tr_on_tr_b_iu` trigger + the 5 transaction columns. Retired the false "all views = one 45-column SELECT, zero drift" claim (admin/members views diverged in v2). Column shapes + exact WHERE semantics still flagged for re-check. |
| 1.1.0 | Added the **v2 schema-name staleness banner** at the top: the domain *concepts* remain accurate but table/view/column names (`council_members`, `n_name`, `fd_access_js`, the `_js` view suffix, `admin_perms`, `branches_js`) are pre-v2 (2026-05-24 overhaul) and GONE on `main`; lists v2 successors + the 2026-06-19 server-transport write change, and routes name-verification to V2-CONVENTIONS.md. Full per-name rewrite deferred (needs live DB read). |
| 1.0.0 | Initial — complete pre-v2 transactions domain model. |
