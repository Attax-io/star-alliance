---
name: admin-page-fixer
description: >
  Fix bugs and warnings found by the admin-page-auditor skill (or manually identified) across Lex Council admin pages.
  Use this skill whenever the user asks to: fix audit findings, fix admin page bugs, apply fixes from an audit report,
  fix file hierarchy filter issues, fix branches_access scoping, fix page-reset dependencies, fix SELECT_COLS,
  extract filter bars, standardize thresholds, or resolve any compliance issues identified in admin pages.
  Also trigger when the user says "fix", "fix these", "apply fixes", "fix the bugs", "fix all issues",
  or references an audit report and wants the findings resolved. This is the companion to admin-page-auditor —
  the auditor finds issues, this skill fixes them.
version: 1.0.0
type: Skill

---
# Admin Page Fixer

Fix bugs, warnings, and compliance issues across Lex Council admin pages. This is the action companion to `admin-page-auditor` — it takes audit findings (from an HTML report or from conversation context) and applies the correct code fixes, verifies them, and optionally re-audits.

## When to use this skill

Trigger whenever the user wants to resolve issues found by an audit, or asks you to fix specific patterns across admin pages. The user might say "fix", "fix these", "apply the fixes", or reference a specific audit report. They might also describe a specific bug class (e.g., "add branches_access to all pages that are missing it").

## Prerequisites

Before fixing, you need findings. These come from one of three sources:

1. **An audit report** — the user ran `admin-page-auditor` and has an HTML report with a fix priority table
2. **Conversation context** — the user described specific issues in the current conversation
3. **Fresh audit** — if neither exists, suggest running the auditor first: "I should audit the pages first so I know exactly what to fix. Want me to run the auditor skill?"

## Fix workflow

The workflow has 5 phases: **Triage**, **Read**, **Fix**, **Verify**, **Confirm**.

---

## Phase 1: Triage

Organize the findings into a prioritized fix plan.

### 1.1 Extract findings

If working from an audit report, read the HTML file and extract the fix priority table. If from conversation, gather all mentioned issues. For each finding, capture:

- **Page** — which page file is affected
- **Category** — which pattern is violated (hierarchy filter, data layer, permissions, styling, state)
- **Severity** — P0 (data/security), P1 (UX/robustness), P2 (inconsistency)
- **Fix type** — what kind of code change is needed (see Fix Patterns below)

### 1.2 Group by fix type

Fixes that touch the same pattern across multiple pages should be done together for consistency. Common groupings:

| Fix type | Typical scope |
|----------|--------------|
| `branches_access` scoping | SELECT_COLS + type mapper + filter callback |
| Page-reset deps | Single useEffect in each page |
| Threshold standardization | All ref-ladder `if` conditions in each page |
| `isFilesFilterActive` gate | The hierarchy filter block in each page's query |
| `file_nature` addition | One line inside the hierarchy block |
| Filter bar extraction | Move inline JSX into new component file |
| `SELECT_COLS` replacement | Replace `select('*')` with explicit columns |
| Dual-store sync | FilePickerModal `onSelect` handler |

### 1.3 Present the fix plan

Before making any changes, present the plan to the user. Use a brief summary format:

```
Fix plan (X pages, Y changes):
  P0: [list of P0 fixes with affected pages]
  P1: [list of P1 fixes with affected pages]
  P2: [list of P2 fixes with affected pages]
```

Wait for the user to confirm before proceeding. They might say "fix all", "just P0", or "skip the filter bar extraction for now".

---

## Phase 2: Read

Read each affected page fully before making any changes. This phase matters because fixes interact with existing code in non-obvious ways — a page's fetch method (`usePaginatedQuery` vs custom `fetchData`) determines which fix pattern applies, and blindly applying a template leads to broken code.

### Identifying the fetch method

This is the single most important thing to determine before applying fixes, because the fix pattern differs between the two methods.

**Quick diagnostic:**
- If the page imports `usePaginatedQuery` from `hooks/use-paginated-query` → it uses the **hook pattern**. Filters are applied inside a callback function passed to the hook. Pages using this: Documents, POAs, IDs, People.
- If the page has `const fetchData = useCallback(async () => { ... })` and `const fetchIdRef = useRef(0)` → it uses the **custom fetch pattern**. Filters are applied inside the callback body. Pages using this: Tasks, Cases, Transactions.
- The Files page uses its own unique fetch pattern — treat it as a special case.

The distinction matters because:
- **Hook pattern**: filters go in the callback arg `(q) => { ... return q }`, and `usePaginatedQuery` handles pagination, count, and mapping internally
- **Custom fetch pattern**: filters go in the `fetchData` useCallback body, and the page manages state (`setRows`, `setTotalCount`, `setLoading`) manually

### What to look for in each page

For each page you're about to fix, note:

1. **Fetch method** — hook pattern or custom fetch (see diagnostic above)
2. **Store access** — which stores are imported, how `activeFilesState` is accessed
3. **Existing filter block** — where the hierarchy filters are applied (if any)
4. **Existing page-reset** — find the `useEffect(() => setPage(0), [...])` and read its current deps
5. **SELECT_COLS** — is it a string constant or `select('*')`?
6. **Type definitions** — where is the row interface? Does it need updating?

Use subagents to read multiple pages in parallel when fixing more than 2 pages.

---

## Phase 3: Fix

Apply fixes following the documented patterns below. Fix one page at a time, completing all changes for that page before moving to the next.

### Fix Patterns Reference

These are the exact code patterns to apply for each fix type, extracted from the Build Instructions and proven across all existing admin pages.

#### Fix: Add `branches_access` scoping

This is a multi-file fix. All three parts are required.

**Part 1: SELECT_COLS** — Add `'branches_access'` to the column list.

If SELECT_COLS is a string: add `, branches_access` to the comma-separated list.
If SELECT_COLS is an array: add `'branches_access'` to the array.

**Part 2: Type + Mapper** — Update the TypeScript interface and row mapper in `types/`.

```typescript
// In the interface:
branchesAccess: number[] | null

// In the mapper function:
branchesAccess: r.branches_access ?? null
```

**Part 3: Filter callback** — Add as the FIRST filter line, before any conditional filters:

For `usePaginatedQuery` pages (filter callback):
```typescript
(q) => {
  q = q.contains('branches_access', `{${activeFilesState.activeLexBranch}}`)
  // ... rest of filters
}
```

For custom `fetchData` pages:
```typescript
let q = supabase.from(VIEW_NAME).select(SELECT_COLS, { count: 'exact' })
q = q.contains('branches_access', `{${activeFilesState.activeLexBranch}}`)
// ... rest of filters
```

**Important**: The Files page does NOT use `branches_access` — it uses `default_branch = activeLexBranch` instead. Never add `branches_access` to the Files page.

#### Fix: Page-reset dependencies

Find the page-reset useEffect and ensure it includes ALL filter deps. The complete list depends on the page, but these are commonly missed:

```typescript
useEffect(() => { setPage(0) }, [
  // Domain-specific filters (varies per page):
  statusFilter, searchQuery, typeFilter, dateFrom, dateTo, memberFilter,
  // File hierarchy (MUST be present on every page with file filter):
  isFilesFilterActive, activeFilesState,
  // Pagination config:
  pageSize,
  // Setter (if used from store):
  setPage,
])
```

The key insight: `isFilesFilterActive` and `activeFilesState` are the most commonly missing deps because they come from the files store, not the domain store.

If a page has multiple page-reset useEffects, combine them into one. Multiple effects watching different subsets of filters can miss combinations.

**Page-type examples** — the actual deps vary by domain, but here's the pattern:
- **Minimal** (Cases): `[isFilesFilterActive, activeFilesState]` — Cases has few filters beyond hierarchy
- **Medium** (IDs): `[activeIdsState, isFilesFilterActive, activeFilesState, pageSize]` — domain state object captures most filters
- **Heavy** (Transactions): `[certFilter, agreedFilter, proofFilter, searchQuery, branchFilter, typeFilter, dateFrom, dateTo, memberFilter, pageSize, isFilesFilterActive, activeFilesState, viewMode, setPage]` — many independent filter variables

The rule: if changing a filter should reset to page 0, it must be in the deps array. Walk through every filter the page supports and verify each one is present.

#### Fix: Threshold standardization

The ref ladder must use consistent thresholds. The standard is `> 0` because the files store defaults are `0` for unset refs.

Find all ref-ladder conditions and standardize:

```typescript
// Before (inconsistent):
if (afs.activeFileClass >= 2 && afs.activeGFN > 1) ...  // wrong threshold
if (afs.activeFileClass >= 3 && afs.activeMFN > 0) ...  // correct

// After (standardized to > 0):
if (afs.activeFileClass >= 2 && afs.activeGFN > 0) q = q.eq('gfn_ref', afs.activeGFN)
if (afs.activeFileClass >= 3 && afs.activeMFN > 0) q = q.eq('mfn_ref', afs.activeMFN)
if (afs.activeFileClass >= 4 && afs.activeBFN > 0) q = q.eq('bfn_ref', afs.activeBFN)
if (afs.activeFileClass >= 5 && afs.activeSFN > 0) q = q.eq('sfn_ref', afs.activeSFN)
if (afs.activeFileClass >= 6 && afs.activeAFN > 0) q = q.eq('afn_ref', afs.activeAFN)
```

#### Fix: Add `isFilesFilterActive` gate

The entire hierarchy filter block must be wrapped in the gate:

```typescript
if (isFilesFilterActive) {
  q = q.eq('file_nature', afs.activeFileNature)
  if (afs.activeFileClass >= 2 && afs.activeGFN > 0) q = q.eq('gfn_ref', afs.activeGFN)
  if (afs.activeFileClass >= 3 && afs.activeMFN > 0) q = q.eq('mfn_ref', afs.activeMFN)
  if (afs.activeFileClass >= 4 && afs.activeBFN > 0) q = q.eq('bfn_ref', afs.activeBFN)
  if (afs.activeFileClass >= 5 && afs.activeSFN > 0) q = q.eq('sfn_ref', afs.activeSFN)
}
```

Note: `file_nature` goes FIRST inside the block, before any ref checks.

#### Fix: Add `file_nature` to hierarchy block

If the hierarchy block exists but is missing `file_nature`, add it as the first line:

```typescript
if (isFilesFilterActive) {
  q = q.eq('file_nature', afs.activeFileNature)  // ADD THIS LINE
  // existing ref ladder...
}
```

#### Fix: Replace `select('*')` with explicit `SELECT_COLS`

1. Identify all columns the page actually uses (check the row mapper, the table render, and any modals)
2. Create a `SELECT_COLS` constant with those columns as a comma-separated string
3. Replace `.select('*')` with `.select(SELECT_COLS, { count: 'exact' })`
4. If TypeScript complains about type inference after the change, use `(data as unknown as DomainRow[])` instead of `(data as DomainRow[])` — the double-cast is needed because Supabase can't infer column types from a string variable

#### Fix: Extract inline filter bar

1. Create a new file at `app/(admin)/admin/{domain}/components/{Domain}FilterBar.tsx`
2. Define a typed props interface for everything the filter bar needs:
   - Filter state values and their setters
   - Row count for display
   - Any callbacks (create, export, etc.)
3. Move the filter bar JSX from the page into the new component
4. Import and render `<DomainFilterBar {...props} />` in the page
5. The component must use `'use client'` since it has interactive state

#### Fix: Dual-store sync in FilePickerModal

The `onSelect` handler must write to BOTH stores. Check if the handler already updates both — if it only updates one, add the missing update. See the file hierarchy rules reference in the auditor skill for the exact dual-store pattern.

#### Fix: Custom fetch race-condition guard

This fix ONLY applies to pages using the custom fetch pattern (Tasks, Cases, Transactions). Pages using `usePaginatedQuery` get this protection from the hook itself — don't add a redundant guard.

If a page uses custom `fetchData`, it must have a `fetchIdRef` guard:

```typescript
const fetchIdRef = useRef(0)

const fetchData = useCallback(async () => {
  const fetchId = ++fetchIdRef.current
  // ... build query ...
  const { data, count, error } = await q
  if (fetchId !== fetchIdRef.current) return  // stale response, discard
  // ... process data ...
}, [deps])
```

---

## Phase 4: Verify

After applying all fixes, verify them.

### 4.1 TypeScript check

Run the TypeScript compiler to catch type errors:

```bash
cd apps/web && npx tsc --noEmit 2>&1 | head -60
```

If there are errors in files you edited, fix them. Common post-fix TS issues:

- **Missing property in interface** — you added a column to SELECT_COLS but not to the type
- **Type assertion failure** — after replacing `select('*')`, use `(data as unknown as Row[])`
- **Import not found** — you referenced a store or type that isn't imported

If there are pre-existing errors in files you didn't touch, note them but don't fix them — they're out of scope.

### 4.2 Sanity check

For each fixed page, quickly re-read the changed sections to verify:

- The fix is syntactically correct
- No accidentally deleted code
- Imports are present for any new dependencies
- The fix follows the exact pattern documented above

---

## Phase 5: Confirm

Summarize what was fixed and offer next steps.

### 5.1 Fix summary

Present a brief summary:

```
Fixed X issues across Y pages:
  - [Page]: [what was fixed]
  - [Page]: [what was fixed]

TypeScript: [clean / N pre-existing errors in unrelated files]
```

### 5.2 Offer re-audit

After fixes are applied, offer to re-run the auditor: "Want me to run a fresh audit to confirm everything is clean?"

---

## Important edge cases

- **The Files page is special.** It uses `default_branch` instead of `branches_access`, `file_class` in its query, and no `isFilesFilterActive` gate. Many fix patterns that apply to other pages do NOT apply to Files.
- **Cases page hierarchy is different.** The cases store deliberately has no hierarchy fields — it reads hierarchy directly from the files store. Don't flag missing dual-store sync as a bug on Cases.
- **Don't over-fix.** If the audit says WARN (not BUG), discuss with the user before changing it. Warnings mean the code works today but is fragile — the user might prefer to leave it.
- **TypeScript double-cast.** When replacing `select('*')` with `SELECT_COLS`, Supabase's type inference breaks because it can't parse a string variable. The fix is `(data as unknown as DomainRow[])` — this is expected and correct.
- **Always read before editing.** Never apply a fix pattern blindly — read the full page first to understand its fetch method, store usage, and existing patterns.

## Source code locations

- Admin pages: `apps/web/app/(admin)/admin/`
- Stores: `apps/web/store/`
- Types: `apps/web/types/`
- Shared hooks: `apps/web/hooks/`
- Constants: `apps/web/app/(admin)/admin/constants.ts`
- Build Instructions: `/mnt/Lex Council NextJS App/LEX_COUNCIL_BUILD_INSTRUCTIONS.html`
