---
name: admin-page-builder
description: Build a new admin page for the Lex Council app under apps/web/app/(admin)/admin/. Use this skill whenever the user asks to create an admin page, build a management UI, add a page under the Files/Users/Finances tab, scaffold a new page inside (admin)/admin/, build a kind/list/grid/table admin screen, add an admin tool, or create a dashboard for admins. Also trigger on "new admin page for X", "admin management UI", "build an admin panel for Y", "admin screen that lets me edit Z", even if design tokens aren't mentioned. This skill exists because without it Claude tends to invent hex colors, miss the navy page frame, and skip the KpiStrip pattern — resulting in pages that read as foreign against every other admin page.
metadata:
  version: 1.1.0
type: Skill

---
# Lex Council admin-page builder

Build new admin pages that match the rest of the admin surface (Files, Users, Finances tabs). This skill encodes the design language established by the Advance Management page (`finances/advances/page.tsx`, shipped 2026-04-23), which is the canonical reference.

## Step 1: Read the canonical reference — do not skip

Before writing any code, open these three files and skim them:

1. `apps/web/app/(admin)/admin/finances/advances/page.tsx` — the outer-page pattern (pageStyle, filter bar, KpiStrip, card grid, PermissionGate)
2. `apps/web/app/(admin)/admin/finances/advances/components/MemberCard.tsx` — the canonical card style (`C.rowOdd` fill, `C.border`, `borderRadius: 12`, subtle shadow)
3. `apps/web/app/(admin)/admin/constants.ts` — the `C` object + all `filterBar*` style tokens + `modal*` style tokens

This is non-negotiable. The wrong instinct is "I already know the design." Admin pages look foreign when built from design instinct alone because they miss small tokens like `C.rowEven`, `filterBarDividerStyle`, and the `C.teal` active-chip color. Always skim `advances/page.tsx` even if you built a similar page yesterday.

## Step 2: Three-layer scaffold

Every admin page in this codebase is a three-layer flex column:

```
┌─ Filter bar (navy shell, filterBarShellStyle) ─────────┐
├─ KPI strip (navy horizontal metric grid, optional) ────┤
└─ Scrollable body (C.rowEven background, cardGridStyle) ┘
     └─ Cards (C.rowOdd background, C.border, radius 12)
```

Outer wrapper:

```typescript
const pageStyle: CSSProperties = {
  display: 'flex', flexDirection: 'column', flex: 1, minHeight: 0,
  background: C.navy, overflow: 'hidden', height: '100%',
}
```

It's a scrollable work surface, NOT a centered document with page padding. Never wrap the page in a `<main style={{ maxWidth: 800, margin: '0 auto', padding: '24px 28px' }}>` — that's the signature of a foreign page.

## Page chrome conventions — back button, Views, and detail panels

Three structural conventions are easy to get wrong, and they were re-directed on repeatedly across sessions. Treat them as defaults, not options — like every other step here, each is a specific thing that got built wrong first.

### Back navigation lives in a "Page Actions" card

A page you can navigate back from does NOT put a bare back arrow in the filter bar or float it over the grid. The top row is two side-by-side elements:

- **left: a "Page Actions" card** holding the back button (and any nav-level controls), and
- **right: a separate named-button panel** holding the page's primary named actions (e.g. "New Advance", "Export").

Left = navigation, right = named actions — two distinct siblings in the top row, not one merged bar. Don't scatter the back button into the filter/search bar.

### Tab views get their own "Views" card — never the filter bar

Two controls look similar but belong in different places:

- **Filter chips** (status, level, type) narrow the *current* list — these live in the filter bar (Step 4).
- **View tabs** switch between whole views of the page ("Active / Archived / All", or per-section tabs) — these get their own dedicated **Views** card, separate from the search-and-filter card.

Never put view tabs inside the filter/search bar. The Views card is its own row; the filter bar stays about searching and filtering one view.

### Row detail opens the shared PortalSidebar

For viewing or editing a single list row, open the shared **PortalSidebar** (the app's right-side detail panel) — not a bespoke per-page drawer. PortalSidebar keeps width, stacking, and close behavior consistent across the admin surface. (The `modalOverlayStyle`/`modalPanelStyle` tokens in Step 10 are for genuine modals and one-off drawers, not list-row detail.)

## Required pattern: Two Zustand stores + file hierarchy filter

Every admin page reads from **two** Zustand stores — never just one, never more than two:

```typescript
// 1. Shared store — always present
const { cmAp, activeFilesState } = useFilesStore()

// 2. Page-specific store — one per page
const { items, loading, error, refetch } = useMyPageStore()
```

`useFilesStore` supplies `cmAp` (permissions), `activeFilesState.activeLexBranch` (the branch filter), and the file hierarchy context. `useMyPageStore` supplies the page's own data and actions.

### File hierarchy filter hook (C5 step 4)

Most admin pages let the user filter by file level (GFN/MFN/BFN/etc.). Always wire this up:

```typescript
const { filterComponent, selectedLevel } = useFileHierarchyFilter()
// Render filterComponent inside the filter bar
// Pass selectedLevel into your data-fetch function as a WHERE clause filter
```

`useFileHierarchyFilter` lives in `apps/web/hooks/useFileHierarchyFilter.ts`. Read it before building a custom level-picker — it handles the display names, resets, and URL-sync for you.

### Branch scoping — every entity query (S2)

**Every** query that returns branch-scoped data must include the `branches_access` filter:

```typescript
.contains('branches_access', `{${activeFilesState.activeLexBranch}}`)
```

This is not optional. Omitting it means a branch-A admin sees branch-B data. `activeLexBranch` comes from `useFilesStore` → `activeFilesState.activeLexBranch`.

### Member picker filter — active members only

Any dropdown or picker that lets the user choose a council member must filter:

```typescript
.eq('in_service', true)
.eq('has_left', false)
```

Both filters are required together. `in_service=true` without `has_left=false` leaks leaver accounts into assignment dropdowns (leavers can have `in_service=true` until the flag is flipped). Do NOT apply this filter to display-only surfaces (history, logs, attribution) — leavers must remain visible in historical records.

## Step 3: Use the C object — never raw colors

Import:

```typescript
import {
  C,
  filterBarShellStyle,
  filterBarCountStyle,
  filterBarSearchContainerStyle,
  filterBarSearchInputStyle,
  filterChipBaseStyle,
  filterBarDividerStyle,
  filterBarActionBtnStyle,
  modalOverlayStyle,
  modalPanelStyle,
} from '../../constants'
import { borderRadius, typography } from '@repo/md'
```

Color mapping:

| Role | Token |
|---|---|
| Page frame / nav chrome | `C.navy` |
| Scrollable grid background | `C.rowEven` (#F1F4F8, pale blueish) |
| Card fill | `C.rowOdd` (#E0E3E7, slightly darker blueish) |
| Default border | `C.border` |
| Soft / divider border | `C.borderLight` |
| Primary text on light surfaces | `C.textDark` (navy) |
| Muted text | `C.textMid` |
| Primary accent / primary CTA | `C.teal` |
| Error / destructive | `C.red` |
| Success | `C.green` |
| Warning | `C.orange` |

If a color need doesn't map to a token, stop and ask the user. **Do not invent hex colors.** When users iterate on color ("darker", "bluer"), that means the existing token was wrong — not that you should pick a new hex. Go re-read the canonical page.

## Step 4: Filter bar — always use the tokens

```typescript
<div style={filterBarShellStyle}>
  <span style={filterBarCountStyle}>
    {filtered.length} of {total}
  </span>
  <div style={{ display: 'flex', alignItems: 'center', gap: 4, color: C.teal, fontSize: 11, fontWeight: 700, letterSpacing: 0.5 }}>
    <MIcon name="section_icon" size={16} color={C.teal} />
    SECTION LABEL
  </div>
  <div style={filterBarDividerStyle} />
  {CHIPS.map((chip) => {
    const on = filter === chip.key
    return (
      <button
        key={chip.key}
        type="button"
        onClick={() => setFilter(chip.key)}
        style={{
          ...filterChipBaseStyle,
          padding: '0 10px',
          fontSize: 11,
          fontWeight: 700,
          fontFamily: 'inherit',
          background: on ? C.teal : 'rgba(255,255,255,0.08)',
          color: '#fff',
          border: on ? 'none' : '1px solid rgba(255,255,255,0.15)',
        }}
      >
        <MIcon name={chip.icon} size={12} color="#fff" />
        {chip.label}
      </button>
    )
  })}
  <div style={filterBarSearchContainerStyle}>
    <MIcon name="search" size={14} color="rgba(255,255,255,0.5)"
           style={{ marginLeft: 8, pointerEvents: 'none' } as any} />
    <input style={filterBarSearchInputStyle} placeholder="Search..."
           value={query} onChange={(e) => setQuery(e.target.value)} />
  </div>
</div>
```

Never build a custom light-background filter bar. It breaks every other admin page's visual rhythm. The chips here are **filter chips** (narrow the current list) — if you instead need to switch between whole views, that's a Views card, not the filter bar (see Page chrome conventions).

## Step 5: KPI strip (when the page has summary metrics)

A horizontal strip of metric cells — NOT a grid of floating cards. Navy background, N equal columns, divider lines between cells.

```typescript
const kpiStripStyle: CSSProperties = {
  display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)',
  background: C.navy,
  borderBottom: '1px solid rgba(255,255,255,0.06)',
  flexShrink: 0,
}
const kpiCellStyle: CSSProperties = {
  padding: '12px 20px',
  borderRight: '1px solid rgba(255,255,255,0.06)',
  display: 'flex', flexDirection: 'column', gap: 2,
}
```

Cell content: colored icon + `UPPERCASE LABEL` (10.5px, muted white) + big value (20px white, `fontVariantNumeric: 'tabular-nums'`) + small sub-caption (10.5px, very muted white).

## Step 6: Scrollable card grid

```typescript
const cardGridStyle: CSSProperties = {
  padding: '20px 24px',
  display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 12,
  overflowY: 'auto', flex: 1, minHeight: 0,
  alignContent: 'start', background: C.rowEven,
}
```

`flex: 1` plus `minHeight: 0` is load-bearing — it makes this the scrollable region inside the flex-column page. Without both, the grid won't scroll.

## Step 7: Card style

```typescript
const cardStyle: CSSProperties = {
  background: C.rowOdd,
  border: `1px solid ${C.border}`,
  borderRadius: 12,
  padding: '14px 16px',
  display: 'flex', flexDirection: 'column', gap: 10,
  boxShadow: '0 1px 3px rgba(10,26,59,0.06)',
  transition: 'box-shadow 0.2s, border-color 0.2s',
}
```

For primary identifiers inside cards (like a file name or transaction title), use:

```typescript
<code style={{
  fontSize: 12.5, fontWeight: 700, color: C.navy,
  fontFamily: "'Source Code Pro', monospace",
  wordBreak: 'break-all', lineHeight: 1.3,
}}>
```

## Step 8: Permission gate

Wrap the exported page component:

```typescript
import PermissionGate from '.../components/permissions/PermissionGate'

function MyPageInner() { /* ... */ }

export default function MyPage() {
  return (
    <PermissionGate perm="your_perm_vap" mode="page">
      <MyPageInner />
    </PermissionGate>
  )
}
```

If the permission doesn't exist yet, invoke the `add-admin-permission` skill to create it — do not inline the column add.

## Step 9: Nav entry

Edit `apps/web/app/(admin)/admin/components/AdminNavPanel.tsx` — two changes:

(a) Top of the component, with the other `canXxx` consts:
```typescript
const canMyPage = cmAp.your_perm_vap === true
```

(b) Inside the matching `{activeTab === N && (...)}` block:
```typescript
<WithHelp helpKey="nav.myPage">
  <NavButton
    label="My Page"
    iconBg={TAB_ICON_BG}
    hoverBorderColor={colors.navy}
    onClick={() => router.push('/admin/section/my-page')}
    disabled={!canMyPage}
    disabledReason="Requires your_perm_vap"
    icon={<MIcon name="icon_name" size={24} color={colors.navy} />}
  />
</WithHelp>
```

The button is **disabled** (not hidden) when the user lacks the permission — admin convention. The nav entry shows users the capability exists and how to gain access.

Tab numbers (from `AdminNavPanel.tsx`): 0 = Home/Quick, 1 = Files, 2 = Users, 3 = Finances. Verify in the file.

## Step 10: Modals and side drawers — use the tokens

```typescript
// Backdrop
<div style={modalOverlayStyle as any} onClick={onClose} />

// Right-side drawer
<div
  style={{
    ...modalPanelStyle,
    position: 'fixed',
    top: 0, right: 0, bottom: 0, left: 'auto',
    width: 'min(480px, 100vw)', height: '100vh',
    maxHeight: 'none', borderRadius: 0,
    zIndex: 10000,
  }}
>
  ...
</div>
```

Never hand-roll a backdrop RGBA or a custom border-radius-per-modal — the tokens keep stacking and backdrop opacity consistent across the app. These tokens are for genuine modals and one-off drawers only; for **list-row detail/edit**, use the shared **PortalSidebar** instead (see Page chrome conventions).

## Step 11: Data fetching

For pages with real pagination (>50 rows), use the `usePaginatedQuery` hook — see `advances/page.tsx` for the canonical invocation.

For small catalogs (~20 rows like `n_kinds`), a plain `supabase.from(view).select('*')` inside a `useEffect` + `useCallback(load)` is fine. Use `createClient()` from `@repo/supabase/client`, not the server client. Views are preferred over tables (project convention).

## Step 12: Realtime subscriptions

If the page shows live data, subscribe via `supabase.channel(...)` inside a `useEffect` with a 2500ms debounce before refetching. Pattern from `advances/page.tsx`:

```typescript
useEffect(() => {
  const channel = supabase
    .channel('my-page-realtime')
    .on('postgres_changes',
        { event: '*', schema: 'public', table: 'the_table' },
        () => {
          if (debounceRef.current) clearTimeout(debounceRef.current)
          debounceRef.current = setTimeout(() => refetch(), 2500)
        })
    .subscribe()
  return () => { supabase.removeChannel(channel) }
}, [refetch])
```

## Layout variant: List rows (for list/management pages)

Not all admin pages use the card-grid layout. Many pages — tasks, documents, transactions, cases, bugs — are lists. **Default to `ListRowBase` rows, not a hand-rolled `<table>`.** `ListRowBase` gives you the shared row chrome (fixed columns, hover, selection, sticky navy header) that every other list page already uses, and its rows open the shared **PortalSidebar** for detail/edit. This is a convention the user re-directed on repeatedly: raw tables read as foreign — convert them to `ListRowBase` cards with `PortalSidebar`.

Reach for a raw `<table>` only when you need dense multi-column comparison that `ListRowBase` genuinely can't express — and even then, keep the sticky navy `<thead>`, `TableShell`, and `PaginationBar` shown below. Read the canonical list page before building a custom row; do not invent a bespoke drawer for row detail.

### Raw-table fallback scaffold

```typescript
// Wrap table in TableShell (handles loading skeleton, error state, empty state)
<TableShell loading={loading} error={error} empty={rows.length === 0} emptyMessage="No results">
  <table style={{ width: '100%', borderCollapse: 'collapse', tableLayout: 'fixed' }}>
    <colgroup>
      <col style={{ width: '40%' }} />
      <col style={{ width: '20%' }} />
      <col style={{ width: '20%' }} />
      <col style={{ width: '20%' }} />
    </colgroup>
    <thead style={{
      position: 'sticky', top: 0, zIndex: 1,
      background: C.navy,
    }}>
      <tr>
        <th style={thStyle}>Column A</th>
        <th style={thStyle}>Column B</th>
        <th style={thStyle}>Column C</th>
        <th style={thStyle}>Actions</th>
      </tr>
    </thead>
    <tbody>
      {rows.map((row) => (
        <tr key={row.id} style={rowStyle}>
          <td style={tdStyle}>{row.name}</td>
          <td style={tdStyle}>{row.value}</td>
          <td style={tdStyle}>{row.status}</td>
          <td style={tdStyle}>
            {/* action buttons */}
          </td>
        </tr>
      ))}
    </tbody>
  </table>
</TableShell>
<PaginationBar
  currentPage={currentPage}
  totalPages={totalPages}
  onPageChange={setCurrentPage}
/>
```

Key style constants for table pages:

```typescript
const thStyle: CSSProperties = {
  padding: '10px 16px', textAlign: 'left',
  fontSize: 11, fontWeight: 700, letterSpacing: 0.5,
  color: 'rgba(255,255,255,0.7)',
  borderBottom: '1px solid rgba(255,255,255,0.08)',
}
const tdStyle: CSSProperties = {
  padding: '12px 16px', fontSize: 13,
  color: C.textDark,
  borderBottom: `1px solid ${C.borderLight}`,
  verticalAlign: 'middle',
}
const rowStyle: CSSProperties = {
  background: '#fff',
  transition: 'background 0.12s',
}
// Hover: swap background to C.rowOdd inline via onMouseEnter/Leave
```

The scrollable wrapper for a table page uses the same `flex: 1, minHeight: 0, overflowY: 'auto'` container as the card grid, just with `background: '#fff'` instead of `C.rowEven`.

`tableLayout: 'fixed'` is required — without it, columns resize to content and the table jumps on every data change. Always pair it with `<colgroup>` to set explicit widths.

**When to use card grid vs list rows vs raw table:**
- **Card grid** — when each entity has rich metadata to show at a glance (advances, members, transactions). Cards work well for ≤ ~50 visible items.
- **ListRowBase rows** (default for lists) — when you need to scan many rows quickly and compare a few columns (tasks, documents, cases). Row detail opens the shared PortalSidebar.
- **Raw table** — only for dense multi-column comparison ListRowBase can't express; keep sticky navy `<thead>`, `TableShell`, `PaginationBar`.

## Step 13: Before you ship — self-check

Do all of these pass?

- [ ] Outer div uses `pageStyle` (navy, flex column, overflow hidden, height 100%) — not a max-width centered layout
- [ ] Every color comes from `C.*` or the filter-bar/modal style tokens — no hand-picked hex
- [ ] Back navigation sits in a left "Page Actions" card with a separate right named-button panel — not floated over the grid or dropped into the filter bar
- [ ] View tabs live in a dedicated "Views" card — the filter/search bar holds only search + filter chips
- [ ] Filter bar uses `filterBarShellStyle` + `filterBarCountStyle` + `filterBarSearchContainerStyle` + `filterBarSearchInputStyle` + `filterChipBaseStyle` — no custom light container
- [ ] Grid uses `cardGridStyle` — `C.rowEven` background, `flex: 1` + `minHeight: 0`
- [ ] Cards use `C.rowOdd` background, `C.border`, `borderRadius: 12`, the `0 1px 3px rgba(10,26,59,0.06)` shadow
- [ ] Page wrapped in `<PermissionGate perm="..." mode="page">`
- [ ] Nav entry added in `AdminNavPanel.tsx` under the correct tab, gated by the `canXxx` const
- [ ] Modals/one-off drawers use `modalOverlayStyle` + `modalPanelStyle`; list-row detail uses the shared `PortalSidebar` (not a bespoke drawer)
- [ ] Every entity query filters by `.contains('branches_access', ...)` using `activeFilesState.activeLexBranch`
- [ ] Member pickers filter `.eq('in_service', true).eq('has_left', false)` (display surfaces exempt)
- [ ] `useFilesStore` (shared) + page-specific store both wired — never one store alone
- [ ] List/management pages default to `ListRowBase` rows (raw `<table>` only for dense comparison, and then with `tableLayout: 'fixed'` + `<colgroup>` + sticky navy `<thead>` + `TableShell` + `PaginationBar`)

If any of these is missing, fix it before declaring the page done — it will stand out as foreign otherwise.

## Why this skill exists

On 2026-04-24 I built `/admin/files/notifications-management` without reading `advances/page.tsx` first. I invented container colors (`#E6EDF4`, `#EFEBDC`), invented a border (`#C4CAD3`), built a centered-document layout with page-level padding, and made floating KPI cards instead of a strip. Atta pushed back three times on color tone ("darker", "blueish not yellowish", "revert") before saying "why is it so inconsistent with the design language we use? check the last made advances page and make it like it." A full rewrite followed.

The page-chrome conventions (Page Actions card, Views card, ListRowBase + PortalSidebar over raw tables) were added later for the same reason — they were re-directed on across several members/admin panel sessions until they became the standing default.

Every step in this skill is a specific thing I got wrong. Follow the skill the first time and save the rewrite.