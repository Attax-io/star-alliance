# Transactions Domain — File Map

Quick reference for locating transaction-related code. Read the relevant file before modifying it.

## Frontend Components

| File | Purpose |
|------|---------|
| `apps/web/app/(admin)/admin/finances/components/TransactionFormModal.tsx` | Single transaction create/edit (8-phase wizard) |
| `apps/web/app/(admin)/admin/finances/components/BatchTransactionModal.tsx` | Batch transaction create (4-phase wizard) |
| `apps/web/app/(admin)/admin/finances/components/TransactionContainerV8.tsx` | Transaction detail popup (v8 design) |
| `apps/web/app/(admin)/admin/finances/components/TransactionActionBar.tsx` | Per-row action buttons in table |
| `apps/web/app/(admin)/admin/finances/components/TransactionsSummaryBar.tsx` | KPI summary strip |
| `apps/web/app/(admin)/admin/finances/components/TransactionCell.tsx` | Table cell renderer |
| `apps/web/app/(admin)/admin/finances/components/TransactionTypeIcon.tsx` | Type icon/badge |
| `apps/web/app/(admin)/admin/finances/components/SmartMovementCell.tsx` | Movement (done_by → to) cell |
| `apps/web/app/(admin)/admin/finances/components/CompoundTransactionStatus.tsx` | Compound status display |
| `apps/web/app/(admin)/admin/finances/components/TransactionModeChooser.tsx` | Normal/Safe mode picker |
| `apps/web/app/(admin)/admin/finances/components/ConfirmAgreePopup.tsx` | One-way agree confirmation modal |
| `apps/web/app/(admin)/admin/finances/components/TemplatesModal.tsx` | Template save/load/delete UI |
| `apps/web/app/(admin)/admin/finances/components/DensityToggle.tsx` | Table density switcher |
| `apps/web/app/(admin)/admin/finances/components/transactionTitleDefaults.ts` | Default title per type (Arabic) |
| `apps/web/app/(admin)/admin/finances/components/primitives.tsx` | Shared primitives (AmountCell, etc.) |

## Pages

| File | Purpose |
|------|---------|
| `apps/web/app/(admin)/admin/finances/history/page.tsx` | Main transactions page (all 6 tabs) |
| `apps/web/app/(admin)/admin/finances/advances/page.tsx` | Advance management page (member cards) |
| `apps/web/app/(admin)/admin/finances/revenue/page.tsx` | Revenue page |
| `apps/web/app/(admin)/admin/finances/expenses/page.tsx` | Expenses page |
| `apps/web/app/(admin)/admin/finances/credits/page.tsx` | Credits page |
| `apps/web/app/(admin)/admin/finances/wages/page.tsx` | Wages page |

## Hooks

| File | Purpose |
|------|---------|
| `apps/web/app/(admin)/admin/finances/hooks/useTransactionLookups.ts` | Loads types, members, branches, safeFileRef for form modals |
| `apps/web/app/(admin)/admin/finances/hooks/useTransactionsRealtime.ts` | Realtime subscription for transaction changes |
| `apps/web/app/(admin)/admin/finances/hooks/useTransactionsBulkCertify.ts` | Bulk certify logic |
| `apps/web/app/(admin)/admin/finances/hooks/useTransactionsBulkApprove.ts` | Bulk approve logic |
| `apps/web/app/(admin)/admin/finances/components/useTransactionContainerData.ts` | Data hook for ContainerV8 |

## View Modes & Config

| File | Purpose |
|------|---------|
| `apps/web/app/(admin)/admin/finances/history/view-modes.ts` | ViewMode type, VIEW_MODE_CONFIG, TAB_ORDER, SAFE_TYPE_IDS |
| `apps/web/app/(admin)/admin/finances/history/components/ViewModeTabBar.tsx` | Tab bar component |
| `apps/web/app/(admin)/admin/finances/history/components/TransactionsFilterBar.tsx` | Filter bar |
| `apps/web/app/(admin)/admin/finances/history/components/TransactionsBulkActionBar.tsx` | Bulk action bar |

## Store & Types

| File | Purpose |
|------|---------|
| `apps/web/store/transactions-store.ts` | Zustand store (filters, pagination, slide-over, selection) |
| `apps/web/types/transaction-row.ts` | TransactionRow interface + mapTransactionRow |
| `apps/web/lib/query-configs/transactions-columns.ts` | SELECT column list for queries |

## Mutations & API Routes

| File | Purpose |
|------|---------|
| `apps/web/lib/mutations/transactions.ts` | Client-side mutation helpers |
| `apps/web/app/api/transactions/create/route.ts` | Create transaction (POST) |
| `apps/web/app/api/transactions/update/route.ts` | Update transaction (POST) |
| `apps/web/app/api/transactions/certify/route.ts` | Bulk certify (POST) |
| `apps/web/app/api/transactions/agree/route.ts` | Bulk agree (POST) |
| `apps/web/app/api/transactions/comment/route.ts` | Add/delete comments (POST) |

## Templates

| File | Purpose |
|------|---------|
| `apps/web/app/api/templates/_helpers.ts` | Template validation (type checks, mode enforcement) |
| `apps/web/lib/mutations/templates.ts` | Template mutation helpers |

## Database

| Object | Type | Purpose |
|--------|------|---------|
| `public.transactions` | Table | Main transactions table |
| `public.transaction_types` | Table | Type reference (13 rows) |
| `public.transaction_templates` | Table | Per-user templates |
| `private.tr_on_tr_b_iu()` | Trigger function | BEFORE INSERT/UPDATE — action-required guard, name lookups, flags |
| `transactions_personal_js` | View | Personal tab |
| `transactions_pending_js` | View | Pending tab |
| `transactions_approval_js` | View | Approval tab (includes `allow_admin_conscent`) |
| `transactions_certification_js` | View | Certification tab |
| `transactions_safe_js` | View | Safe tab |
| `transactions_history_js` | View | History tab |
| `transactions_container_js` | View | Container detail + activity timeline |
