---
type: Document
timestamp: 2026-06-27T10:27:03Z
---

# Consolidation candidates registry

Unconsolidated-but-should-be instances across the Lex Council app, mined from 146 archived
sessions (2026-05-29) + cross-checked against the live codebase. Seeds the `consolidate-code`
DRAFT mode (see SKILL.md). Each entry: **what** is duplicated, **where**, **tier**, **status**.

**Tiers:**
- **T1 extract-now** — mechanical, low behavior-parity risk, ≤ codemod or a few files. Safe under autonomous cadence.
- **T2 needs-campaign** — cross-cutting, behavior-parity risk (§L2 byte-compare rule applies), or >15 sites. Open a conquering-campaign.
- **T3 resolved/historical** — already consolidated; kept for the record so re-mining doesn't re-flag.

**Verification key:** `[live]` = grep-confirmed in the codebase this session · `[audit]` = cited from a
persisted audit synthesis · `[session]` = from a session transcript, not re-verified.

> Biggest single existing source: [`docs/audit-campaigns/2026-05-22_db-wide-consolidation-audit/99-synthesis.md`](../../../lex_council/docs/audit-campaigns/2026-05-22_db-wide-consolidation-audit/99-synthesis.md)
> — a 74-finding staged DB consolidation plan. The DB rows below are lifted from it; read it before any DB consolidation campaign.

---

## T1 — extract-now (mechanical, low-risk)

| # | What | Where | Verify | Action |
|---|---|---|---|---|
| C1 | `const PANEL_WIDTH = 332` copy-declared instead of importing canonical `PORTAL_SIDEBAR_WIDTH` | **44 files** vs canonical `components/portal/PortalSidebar.tsx:30` | `[live]` | Codemod: replace local `PANEL_WIDTH` decl + usages with `import { PORTAL_SIDEBAR_WIDTH }`. Single biggest mechanical win. |
| C2 | `PAGE_SIZE_OPTIONS = [25, 100, 250]` duplicated | `components/portal/SidebarPaginationCard.tsx:10` + `components/data-table/PaginationBar.tsx:20` | `[live]` | Extract to one shared const (e.g. `lib/pagination.ts`); both import it. |
| C3 | Deprecated `insights/articles.ts` — `export {}` tombstone, 0 importers since 1.6.52 | `apps/web/app/[locale]/(public)/insights/articles.ts` | `[session]` | `git rm` (grep-verified zero importers 2026-05-01). |
| C4 | Two Finder-duplicate API dirs (`end 2/`, `start 2/`) | `apps/web/app/api/impersonation/{end,start} 2/` | `[session]` | `git rm -r` the ` 2/` copies. |
| C5 | Identical `UtilBtn` icon-button helper inlined in two containers | `DocumentContainerV8.tsx` + `FileContainerV8.tsx` | `[session]` | Already has target `components/ui/TableActionBtn.tsx` — compose it, delete inline copies. |
| C6 | Orphan page-keys with no live `<PortalSidebar pageKey>` consumer + missing `hooks/` barrel | `lib/page-keys.ts` | `[session]` | Drop dead keys; add a `hooks/index.ts` barrel. |

## T2 — needs-campaign (cross-cutting / parity risk)

### FE primitives + patterns

| # | What | Where | Verify | Notes |
|---|---|---|---|---|
| C43 | **C4 raw component writes bypass `lib/mutations`** — ~72 raw `supabase.from().insert/update` sites; mutations wrap SECURITY DEFINER RPCs, so routing needs new RPCs (MCP-applied) | ~25 files; **priority-1: `ShareHubCreate`** 5 entity inserts (tasks/documents/poas/ids/cases) | `[live]` | Priority-10 BR-documented 2026-06-02 (BR-239…248, 20 sites). T2: route through RPC-backed mutations. See [[2026-06-02_security-fixes-followups]]. |
| C7 | **EntityContainerHeader dark-mode glyph bug duplicated across all 9 V9 containers** — same `C.navy` (themable) vs `colors.navy` (flat) mistake, pale-on-gold in every adapter | 9 container adapters | `[audit]` | One shared header fix; HIGH-band. Maps to the C.alwaysWhite/colors.navy canon rule. |
| C8 | `entity-container/shared.ts` style module imported by only **1 of 8** V9 containers; other 7 duplicate style constants | `components/entity-container/shared.ts` | `[audit]` | Rule C5b already mandates importing it. Migrate the 7. |
| C9 | **8 portal panels hand-roll `<aside>` sidebar chrome** instead of `<PortalSidebar>` (the 33-page sweep missed these) | 8 panels | `[audit]` | `position:fixed/top:64/insetInlineEnd:16` chrome that `<PortalSidebar pageKey>` (v1.7.7) owns. |
| C10 | **6 per-page KPI-strip implementations** should collapse to one `<KpiStrip>` | advances, cases, wages, branches, insights, notifications-mgmt | `[session]` | Partly addressed (generic `MdKpiStrip` retired 2026-05-19 canon §2.4 → SidebarCard rows). Surviving page-specific `*KpiStrip` (e.g. `CasesKpiStrip`) allowed by canon; audit the 6 for a shared base. `[live]` confirmed only 3 imports + 5 render sites remain. |
| C11 | **3 sibling `*ListRow` components drift** instead of composing one `ListRowBase` | files/tasks/transactions list rows | `[session]` | The N=3 clone that drove conquering-campaign v1.4.0's render-extraction gate. Back-fit `FileListRow` etc. onto `ListRowBase` was explicitly deferred. |
| C12 | **`DocActionBar`/`PplActionBar`/`IdActionBar`** near-duplicate per-row action bars (thin wrappers around `TableActionBtn`) | 3 files, identical `32×32 navy` design-language comment | `[session]` | Collapse to one parameterized action-bar. |
| C13 | **36 button visual signatures for ~7 button roles** | app-wide; `modal_cta` alone = 10 sigs / 52 surfaces | `[session]` | The button-style standardization pass. Two near-identical save buttons differ only in `borderRadius md vs lg` + `fontWeight 600 vs 700`. |
| C14 | **13 bespoke `*FilterBar` impls** (~1000 LOC) → shared `Sidebar*` primitives | TransactionsFilterBar (743 LOC), TasksFilterBar (~680), CasesFilterBar, Activity/Attendance/Bugs/Task FilterBar | `[session]` | Mostly resolved page-by-page but recurred; `MIGRATION-NOTES-TRACKER.md` H5. Confirm remaining survivors. |
| C42 | **Team-response progress bar + name-pills markup duplicated** (progress bar + N/N + ✓ name pills) | `members/tasks/.../MemberTaskListRow.tsx` (line3) + `admin/files/tasks/components/TaskListRow.tsx` (line3) | `[live]` | **N=2 — DEFER until a 3rd consumer.** Parity risk (§L2): the two rows resolve "responded" **differently** — admin by ID (`done_by.includes(id)`), members by name (`doneByNames.includes(name)`). A `TeamResponseProgress` primitive must accept a **precomputed responded-set** (or both `{requiredIds,requiredNames,doneIds}` and `{requiredNames,doneNames}` shapes) — never assume one. Extracting now means touching `MemberTaskListRow` (the keeper reference), risking a regression to the reference for only a 2nd consumer. Logged by the 2026-05-29 admin-task-row-members-parity campaign (P5). |
| C15 | **9 public-marketing section patterns** repeated across 3-7 files (~420-520 LOC copy-paste) | IconRowCard, FAQAccordion, verbatim 6-prop `h2` style ×5 | `[session]` | Extract the 7 highest-value into shared section components. |
| C16 | Two oversized monolith pages | compliance-check (1,298 lines), contact (955 lines) | `[session]` | Decompose into section components + hook (target ~107 / ~48 lines). |
| C17 | Placeholder-option idiom `{ key: '', label: '- Select -' }` copy-pasted across ~6 form components | CalendarEventForm, ShareHubCreate, DocCreateModal ×2, OrphanedFpPanel | `[session]` | Root of the React duplicate-empty-key bug; only the symptom (composite keys) was fixed, not the duplication. |
| C18 | Tier-3 CASCADE-AUDIT promotion/merge targets | `StatCard`→@repo/md, `FormModalWrapper`/`ModalShell` merge, `PaginationBar`, `TableShell`, overlay primitives (`Modal`/`ContainerPopup`/`ConfirmDialog`) | `[session]` | 9 components named for promotion or merger. |
| C44 | **`PortalListPane` centering-wrapper inlined ~25× — NOT byte-identical** (`<div padding/maxWidth/margin:'0 auto'/width:'100%'>`) | 25 sites across `(admin)`/`(members)`/`(clients)` list components + pages (Docs/Ids/Tasks/Poas/Branches/Files/Library/Insights/Points×3/Balances/Users×5/finances-history/members-tasks/members-attendance/clients×3) | `[live]` byte-compared 2026-06-04 | **DEFER — parity variation (§L2/§L4).** maxWidth 1400 (20×) / 1200 (2×: clients home, Branches) / 1100 (2×: members tasks+attendance); padding `16` vs `'24px'` (clients home) vs `'16px 16px 0'` (Balances); trailing `flex:1` / `flex:1,minHeight:0` (activity) / none — and the two **reference** lists disagree (`DocsList` has `flex:1`, `IdsList` doesn't). A `<PortalListPane maxWidth padding fill?>` API needs 3 knobs; the canonical reference **inlines** it, so extracting diverges from canon for low (cosmetic-structural) value. From the 2026-06-03 portal-scrollbar-alignment risk-sweep open item #1. |
| C45 | **N=3 hand-rolled "search input + scrollable select-list" picker body** (search `<input>` + radio/checkbox rows + `searchInputStyle`/`listStyle`/`rowStyle` consts) inside the shared `EditorialFormShell`/`Modal` chrome | `ShareToChatModal.tsx`, `files/components/MoveFileModal.tsx`, `docs-table/DocMergeModal.tsx` | `[live]` byte-compared 2026-06-04 | **DEFER — look-alike-but-different (§L2/§L4).** Chrome is already shared (all compose `EditorialFormShell`/`Modal` — **not** a forked primitive). Only the inner list body is copy-pasted and the 3 diverge: **select-model** ShareToChat = *multi* (Set/`.has`/`.add`) vs MoveFile + DocMerge = *single* (`selectedId`); **shell** picker (DocMerge) vs standard (other 2); **searchInputStyle** MoveFile has no fixed height + no 30px search-icon inset (DocMerge mirrors ShareToChat's). An `<EditorialPickerList>` API would need single|multi select + optional search-icon + per-row render — extracting now silently risks collapsing multi↔single. DocMergeModal (Bug #244) correctly **conformed** to the sibling pattern; it incremented a pre-existing N=2 dup to N=3, did not introduce a new shape. Surfaced by the 2026-06-03_doc-version-merge followups sweep. |

### Config / tokens

| # | What | Where | Verify | Notes |
|---|---|---|---|---|
| C19 | **141 `// Token gap:` annotations** mark hardcoded hex/pastel with no token | 77 files (chat/status/entity-type pastels) | `[session]` | Needs ~N new design tokens then a sweep. Themes dev-tools panel built to monitor this. |
| C20 | `admin/constants.ts` back-compat re-export shim (re-exports `C` + `FILTER_CHIP` from `lib/design-tokens.ts`) | `app/[locale]/(admin)/admin/constants.ts` | `[session]` | Migrate importers to the single source, delete shim. |
| C21 | Hardcoded `#FFFFFF` → `C.alwaysWhite`, `#0A1A3B` → `colors.navy`; 107 hardcoded hex (not theme-flat-annotated) | app-wide (792 TS/TSX) | `[session]` | Round-cleanup audit list; pairs with the `lint` mode hex-grep bonus scan (L13). |
| C22 | Unnamed modal-width / icon-size magic numbers (C15 "No Magic Values" rule) | app-wide | `[session]` | `REALTIME_DEBOUNCE_MS`/`DEFAULT_PAGE_SIZE` are named; widths/icon-sizes aren't. |

### DB (from 2026-05-22 db-wide-consolidation-audit — 74 findings)

| # | What | Where | Audit ref | Notes |
|---|---|---|---|---|
| C23 | **7 near-byte-identical transaction views** differ only in WHERE → 1 base view + FE tab filter | transactions_{personal,pending,history,safe,certification,approval,...}_js | C-05 | §L2 byte-compare before merge. |
| C24 | **3 advance views** share a ~200-line CTE differing only in `WHERE is_in_service` → 1 view exposing the column | advance views | C-06 | |
| C25 | `cm_ap_js` (71 cols) + `cm_perms_js` (67 cols) are 95% identical drifted projections → 1 canonical | cm_ap_js / cm_perms_js / admin_perms_js | C-07/08 | |
| C26 | **Duplicated RLS predicates inlined across many policies** → private helper fns | attendance-admin ×11, insights-admin, etc. | B-14..B-19 | `private.attendance_admin()` etc. Predates `private.has_vap()` precedent. |
| C27 | **11 orphan views (0 FE + 0 RPC refs)** + orphan tables → DROP | atnd_monthly_js, cm_dashboard_js, credit_ledger_*_js, … | B-05 | |
| C28 | **138 legacy `_js` base views** remain after v2 per-portal-wrapper rename → DROP after FE rewire confirmed | branch-wide | `[session]` c7f0e567 | Open work; FE now uses `VIEWS.*` registry keys. |
| C29 | **~100 views across 13 soft-deletable entities** missing `AND [entity].deleted_at IS NULL` | ~50 fixed, ~46 migrations pending | `[session]` ec17e29f | Systemic missing-convention. |
| C30 | `admin_perms` = 67-column column-as-permission god-table → normalize to junction `admin_perms_grants(ap_uuid, perm_key, granted)` | admin_perms | D-03 | Rewrites ~40 RLS policies; XL campaign. |
| C31 | Duplicate sources of truth: `reason_code` text col AND `metadata->>reason_code` JSON; `file_type` text vs FK | task_events, file_events | B-23 | |
| C32 | Locale defined in **3 places** for the same 6 locales → 1 enum | article_locale (enum), app_translations.locale (CHECK), source_law_translations.locale (CHECK) | C-09 | |
| C33 | 14 empty FK-target lookup tables → enums or seed-once | file_status, file_types, task_types, … | C-10/B-25 | |
| C34 | Multi-hop passthrough view chains (violate S12.2 2-view depth) | n_customer_feed→_js, n_kinds_stats→_js (3-hop) | B-07/C-13 | |
| C35 | **2 ghost views referenced by 6 live FE callsites but absent on prod** — CRITICAL | `ppl_picker_js` (4 callsites), `customer_requests_js` | A-16/17 | Silent failures on ID/Case/POA forms + client dashboard. Fix FIRST. |
| C36 | ~18 mutation fns in API routes SOLELY to get admin client (2 competing write transports) | lib/mutations + api routes | `[session]` | RPC audit recommended SECURITY DEFINER; ~37hr migration not run. Needs the single canonical write-transport rule the user keeps asking for. |
| C37 | 33 mutation callsites violate Rule C4 (writes not through `lib/mutations/`) | app-wide | `[audit]` | Direct `db()` writes, no `MutationResult<T>`/`BR-NNN`. |

### i18n

| # | What | Where | Verify | Notes |
|---|---|---|---|---|
| C38 | **294 duplicate EN translation groups / 695 keys** (~401 reclaimable = ~2005 cells × 5 locales) | admin NS worst: 191 groups | `[session]` | Needs a codemod (the `consolidate` mode's map-callsites engine). Worst single backlog. |
| C39 | `MyTaskCard` + `MemberTaskListRow` duplicate identical `STATUS_CONFIG` + `SECTION_CONFIG` | 2 files | `[session]` | Extract to one shared config module. |
| C40 | Same wrong `t()` call-path (spurious `clients.` prefix) copy-pasted | FileCasesPanel, FilePoaPanel, FileHearingsPanel | `[session]` | Maps to L16 namespace-scope trap. |
| C41 | Customer-bundle wizard re-collects fields already in standalone form modals + a parallel orchestration RPC | CustomerBundleModal + `create_customer_bundle` RPC | `[session]` | Wizard form-parity debt; should compose the real form modals. |

## T3 — resolved / historical (do not re-flag)

- `mapAuthError` copied ×4 auth pages → `getAuthErrorKey` `[live]` confirmed 0 hits now
- 90 native `<select>` ×46 files → one `<Dropdown>`; `SharePicker` orphan deleted
- canon 150→31 tokens; 3 palette exports → 1 `PALETTE`
- `FilesStackHorizontal` 3 render branches → 1 (−61%)
- dual bulk surfaces → `BulkActionCard` (−382 lines)
- 26 stacked public CTAs → 1 `CTABanner`; `ConsultationCtaSection` deleted
- `AdminDataTable` + `AdminFilterBar` deleted (v1.7.3)
- 18 hand-rolled `PermissionGate`+navy wrappers → `AdminPageShell`
- `C.teal` → gold across 344 sites
- `private.has_vap()` helper killed inlined RLS predicate copy-paste
- 7 button variants → one `useButtonInteraction` hook
- orphan views `msts_js`, `ppl_op_js` + 6 backup tables dropped (v2 P9)

---

## Priority order for a consolidation campaign

1. **C35** (ghost views, CRITICAL — 6 live broken callsites) — fix immediately, not a campaign
2. **C1** (PANEL_WIDTH ×44) — single biggest mechanical win, codemod
3. **C38** (294 i18n dup groups) — run the `consolidate` mode's codemod
4. **C28 + C29** (138 legacy `_js` views + 100 soft-delete-filter-missing views) — DB hygiene campaign
5. **C7 + C8 + C11** (V9 container dark-mode glyph + shared.ts + ListRow drift) — FE primitive campaign
6. **C23–C27** (DB view/RLS consolidation) — the 74-finding audit's staged plan
7. **C30** (admin_perms god-table) — XL, schedule separately
