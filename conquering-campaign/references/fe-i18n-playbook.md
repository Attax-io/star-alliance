# FE + i18n playbook — conquering-campaign

Load this for any FE / theme / i18n / codemod phase. SKILL.md keeps the gates (G1 reuse-before-build) + the named-pattern index; the procedures, code samples, and the new lessons live here.

---

## Conformity extraction (the G1 procedure in full)

Before writing ANY component/style/button (P9, failure modes #4 #22 #26 #27 #49 #83):

1. **Grep the current + sibling surfaces for an existing primitive FIRST.** If one exists, use it. Hand-rolling a primitive that exists is a campaign failure. The highest-frequency violation: a `<button>` inside `<SidebarCard>` — use the canonical nav-row primitive (`PortalNavRow`), never a raw button, even in "dev-only" panels (a hand-rolled active state ships `background:<active>` + `color:<same-family>` = invisible label).
2. **Name the EXACT leaf file** the design language lives in — it is usually 2 hops below the page row: `Row → ActionBar → GhostIconButton`, not the row. "Match the files page" is ambiguous until you name `…/FileActionBar.tsx` (failure mode #83).
3. **Read the reference's full render function** (not its imports/types/signature) and extract the render hierarchy as labelled lines ("Line 1: rowNum + headline + actions | Line 2: status chip + meta | Line 3: chips"). Put this in the plan's `## Reference render structure` block — empty block ⇒ plan can't be approved (#26).
4. **Extract every token explicitly before writing** — approximating one causes serial revert round-trips (`c013271e`: 3 reverts before the icon buttons matched):
   - Button: `background`, `border` (thickness + color token), `borderRadius` (the token name e.g. `borderRadius.lg`, never the px), icon `size`, icon `color` token, `transition`, `flexShrink`, `padding`
   - Wrapper: `display`, `gap`, `alignItems`
   - Hover: CSS transition or `useState` (not inline `onMouseEnter` mutation)
   - Tooltip: `<Tooltip>` component vs bare `title=`
5. **Re-read the reference immediately before writing** — it may have changed this session.

**Single-instance fix → sibling scan (#77):** after fixing a structural/layout bug on one panel, grep all siblings in the same directory for the identical pattern before "done" — structural bugs are almost always replicated (`BugsPanel` fixed, `LanguagesPanel`/`ActionsTable` left broken).

**Stale-default sweep (#23):** when a phase changes a shared primitive's visual default, grep every consumer override of that property and reclassify (still-correct / stale-against-old-default → fix now / newly-redundant → remove). Also grep stale header comments describing the old design fact.

**Layout direction:** Arabic DB content in an English admin panel → the CONTAINER is `ltr`, even if the text is Arabic. Don't inherit `direction:rtl` from old table-column patterns or from the content's origin language (#56). **Per-row actions** (N rows × N edit/delete buttons) are a legitimate strict-zone exception — document accepted exceptions in the risk sweep so future campaigns don't reopen them.

---

## Named FE patterns

### RIBS — rename-incidental-body-shrink (single file, #60)
Rename a public component + delete >40% of its body. Declare `fe_pattern: RIBS`.
1. **R** — `git mv old.tsx new.tsx` (keeps version control, restamps path).
2. **I** — Read the new path once (satisfies the Edit pre-invariant after the path change).
3. **B** — single atomic `Write` over the whole new file: imports trimmed to the survivor branch, helpers deleted, dead render branches removed, dropped union values gone from the type, default export renamed. NOT chained Edits (a >40% shrink leaves lint-dirty intermediates — #28).
4. **S** — update the barrel; grep-prove zero remaining imports of the old name before consumer updates: `grep -rln "<OldName>" apps/web/ --include=*.tsx --include=*.ts`.
Used on `FilesStackHorizontal.tsx → FilesStack.tsx` (962 → 374 lines, −61%).

### RIBS-N — multi-file lockstep rename (#60 generalised)
When the rename touches companions (`Foo.tsx` + `Foo.test.tsx` + `Foo.stories.tsx` + `Foo.types.ts`, or hook + consumers + test). Declare `fe_pattern: RIBS-N`. Batch `git mv` all companions → Read each → atomic `Write` per file → barrel + grep-proof → companion-consistency grep (no test file still importing the old type module). N=1 ⇒ use plain RIBS.

---

## Environment hazards (FE)

### Aggressive PostToolUse hooks
- **"File modified since read"** mid-Edit — the hook touched the file between Read and Edit. Prefer `Write` over `Edit` for files you just refactored; or re-Read the smallest slice then Edit. After any wait >30s (subagent / Monitor / MCP), re-Read before the next Edit (#41).
- **Design-token rewrites mid-flight** (`colors.X` → `var(--color-X)`, unused-import strips) are expected, not regressions — accept the linter's output as source of truth; run lint at every phase exit to catch cascades in batches.
- **Multi-Edit atomicity trap (#28):** `Edit #1` adds a helper, `Edit #2` adds its call site → linter strips the "unused" helper between them. When the intermediate state would be lint-dirty, single `Write` over the whole file.
- **JSX structural pivot (#51):** wrapping N>3 same-shape JSX siblings with a conditional via chained Edits → mis-anchors + inconsistent intermediate + fragmented diff. `N>3 same-shape wraps in one file ⇒ single Write` (or one `replace_all`).
- **Defensive `?? '#hex'` fallback** is dead code (canonical tokens never resolve undefined under `as const`) and violates the raw-hex rule — drop the fallback half. Grep `C\.[a-zA-Z]+\s*\?\?\s*['\"]#`.

### Runtime module caches that don't HMR (#48)
- **Next.js dev-server JSON imports:** a key added to `messages/<locale>/<ns>.json` mid-session is NOT picked up (the dynamic import was evaluated at startup). Runtime renders the raw key path. Detection trio: (a) raw key path renders, (b) `git blame` shows `00000000 (Not Committed Yet)`, (c) sibling keys render fine ⇒ **restart the dev server**, don't chase the DB/config/namespace.
- **SWC stale parse:** a removed symbol still produces a parse error at a line that no longer contains it + `git diff HEAD` clean ⇒ clear `.next/` + restart.
- **Umbrella:** *if the runtime symptom contradicts the current file on disk, restart the dev server FIRST, diagnose only if it persists.*

### Mass-edit / codemod safety (#73)
Inline `python3 << 'PY'` with `re.sub` is 10× faster than per-file Edits for ≥10 same-shape files, but:
- **JSX double-quote escapes:** use raw strings `r'…'`; match `r'className="x"'`, never `'className=\"x\"'`.
- **Multiline-aware scanning:** single-line regex undercounts multi-line JSX (`<input …>` over lines) and arrow `=>` defeats element-close detection — use brace-aware scanners or per-file Edits; never trust a single-line occurrence count for scope (#76).
- **`\b` doesn't guard decimals:** `12.5` → `typography.size.xs.5`; add a negative-lookahead after the digit in numeric-token codemods.
- **Import insertion** targets the LAST top-level import line, never mid-multiline-import.
- **`\uXXXX` double-escape:** bash-heredoc + Python literal double-consume backslashes → the needle matches nothing (reported subs >> grep count is the tell); build it via `bytes.fromhex(...).decode('latin1')`.
- **Exclude canon/doc files** that intentionally contain the banned pattern as `✗ FORBIDDEN` examples — a blind sweep corrupts the canon itself.
- **No Read precondition on Bash writes** = no "modified since read" safety net → run `tsc --noEmit` within seconds of the batch.

### SSR / client hydration mismatch with module-level state (#20)
Recurs in any campaign touching client state that persists across reloads (theme, auth, locale, flags, role). A store that reads `localStorage` at MODULE LOAD returns the SSR fallback (`typeof window==='undefined'`) and bakes it into the client bundle, so the real stored value never applies. Symptoms: storage has the right value, the visual reflects the fallback, the `useEffect` fires once with the stale value, `tsc + lint` green. **Two-layer fix:** (1) a synchronous inline `<script>` in the root layout `<head>` that sets the attribute before first paint (no hardcoded `data-theme="light"` on `<html>`); (2) a mount-time re-sync `useEffect` in the client provider. Promoting a provider UP a layout level without (1) causes a FOUC (#E6). Step 1.2 Q9 must include a reload-with-non-default-storage browser recipe for these campaigns.

---

## New FE lessons (v3.0.0 mine)

- **Z-index numeric fix is structurally wrong (#64).** Root cause of "dropdown behind widget" = ancestor stacking-context containment, not the number. Cure: `createPortal` to `document.body` + fixed positioning via `getBoundingClientRect()`; adopt a canonical Z scale (`base:0, sticky:100, sidebar:200, topbar:300, overlay:8000, modal:9000, dropdown:9500, toast:9999`).
- **Sidebar `overflow:hidden` clips portal children (#65).** Any popover inside a scrollable/overflow container must `createPortal` to body; a higher z-index does nothing.
- **Stepper collapse by step-count is insufficient (#66).** Overflow = f(steps, panel width, label length, locale). Measure (`scrollWidth` vs `clientWidth`) in a `ResizeObserver`; never a hardcoded `labelWindow` threshold.
- **DB placeholder/sentinel leakage.** Conditional-render text guards must check known sentinels (`null`, empty, locale placeholders like `N/A` / `لا يوجد`), not just null/undefined — a row rendering a DB-default placeholder is a visual-noise bug.
- **Stale spatial hints.** After moving tabs/controls, grep inline hint copy for old locations ("above", "at the top", "in the left panel") and update in the same phase.
- **Inline-style architecture ceiling.** A project setting every color via `style={{background:'#hex'}}` cannot switch to CSS-var theming without a multi-campaign sweep — acknowledge the ceiling in the plan; ship layout-level + highest-visibility components first.
- **`redirect()` is 200 in dev, 307 in prod (#E10).** RSC streaming serves the destination at the source URL in dev — redirect correctness can only be verified in a production build. CHK-tag redirect server calls for prod verification.
- **Pagination indexing convention (0- vs 1-indexed)** must be checked before sharing a pagination primitive; add a live last-page count check to verification (`row_count == page_size` interior, `< page_size` last).
- **Navigation intent default:** "home page" / "landing page" in a dev/admin tool means the LOCAL app root (`router.push('/')`), never the production public URL — external navigation requires explicit "open lexcouncil.com" language.

---

## i18n lessons

- **`useTranslations()` no-arg + bare keys renders the raw key path (#71).** Use `useTranslations('namespace')` + `t('key')`. Grep for no-arg `useTranslations()` during i18n campaigns; `tsc + lint` don't catch the literal-string render.
- **JSON hygiene (#72):** (a) deleting the alphabetically-last key leaves a trailing comma → canonicalize the JSON after any key delete; (b) renaming an EN key orphans DB `key_path` overrides silently — cross-reference key_path vs live JSON before saving; (c) reordered interpolation needs NAMED params `t('key',{month,day})`, never positional; (d) register a locale in `routing.ts` only AFTER its message files exist; (e) re-run the dead-key grep after any phase that ADDS `t()` calls (a P1-purged key can resurrect in P2).
- **`@/i18n/navigation` with `pathnames:{}`:** `useRouter().push` / `<Link>` types compute to `never` — use `next/navigation` for `push`, `next/link` for `<Link>`; only `usePathname` from `@/i18n/navigation` is safe. Lex memory `[[discovery_i18n-navigation-pathnames-empty]]`.

### Translation generation (extends `generation_strategy: deferred-parallel-subagents`)
- Plan must list **intentionally-EN values** (brand names, numeric stats, abbreviations CSV/ID/MFN, URLs) as an exclude list AND **valid cognates per locale** (FR: Finances, Documents; ES: Error, No) so the EN=locale check doesn't false-alarm.
- **Locale anchor protocol:** each translation subagent reads 5–10 existing translated values in the target locale before generating, to anchor tone/register.
- **Ollama contamination scan:** qwen3:8b intermittently injects wrong-script chars (Korean into Arabic) — run a unicode script-range scan (`unicodedata`) before writing locale JSON; flag contaminated keys for manual correction.
- **Unicode normalization:** normalize both sides to NFC before EN→translated lookups (a file written `ensure_ascii=True` may hold literal `…` where Ollama emitted U+2026); always write locale JSON `ensure_ascii=False`.
