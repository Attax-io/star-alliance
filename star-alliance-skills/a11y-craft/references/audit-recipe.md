---
type: Document
timestamp: 2026-07-02T12:28:13Z
---

# A11y audit recipe — how the designer runs the gate

A single repeatable pre-ship pass. Run it on the staging build with the real component library and the real data shapes. Designer is the gate; dev cannot self-certify. Six stages, in order; each stage is concrete.

## Stage 1 — Automated (axe-core / Lighthouse / Pa11y)

**Rule.** Run three automated tools in CI on every PR; treat them as a *floor*, not the audit. axe-core catches roughly 30–40% of WCAG issues; Lighthouse and Pa11y each catch a different subset. Never let a green automated run block release on its own.

**Why.** Automation finds the cheap, mechanical failures: missing alt, missing label, broken ARIA, contrast on default theme, broken heading order, missing form-field-programmatic-label, duplicate id, missing landmark. These are failures a human will miss because they are invisible to the eye.

**How to check.**
- axe-core via `@axe-core/playwright` or Storybook a11y addon. Fix every `violation` and every `incomplete` (incompletes need human review).
- Lighthouse CI: target ≥ 95 on Accessibility category; investigate any sub-90.
- Pa11y CI on the live staging URL set (home, primary task, primary form, primary error state).
- Run *twice*: once on light theme, once on dark theme. Toggle `color-scheme` at the test root.
- What automation misses (must be caught by Stages 2–6): logical focus order, keyboard traps, custom widget behavior, screen-reader announcement quality, content-under-zoom, motion-induced vestibular harm, dynamic ARIA state correctness, "label in name" mismatches.

## Stage 2 — Manual keyboard sweep

**Rule.** Unplug the mouse / disable the trackpad. Tab from page top to bottom on every page of the primary user journey. Then back-tab from bottom to top. For each tab stop, record: visible focus? logical order? stuck (trap)? operable with Space/Enter/arrows?

**Why.** ~50% of WCAG failures are keyboard-related. Automated tools check "is the element focusable" but not "does the focus indicator actually appear and is it usable".

**How to check.**
- Visible focus: at every stop, the focus ring is present, on top, ≥ 3:1 against its background, ≥ 2 CSS px (or the 2.4.12 area rule).
- Focus order: tabbing should follow visual/DOM order, no surprises, no skipped content.
- No trap: at every modal, menu, combobox, date picker, rich-text editor — Esc closes, Shift+Tab exits, focus returns to the trigger.
- Activation: every interactive element responds to Enter (and Space where appropriate: buttons, checkboxes, radios, menu items, tabs).
- Arrows: in radio groups, listboxes, menubars, tab lists, sliders, tree views — arrow keys traverse.
- Custom widgets: verify WAI-ARIA Authoring Practices keyboard contract is implemented.
- Forms: Tab order = visual order; Enter submits; Space toggles checkboxes.

## Stage 3 — Screen-reader spot check

**Rule.** VoiceOver (macOS/iOS) or NVDA (Windows). Pick three pages: the home, the primary form, the primary error state. Tab through with the screen reader active. For every interactive element, you should hear: role + name + state, in that order.

**Why.** The screen reader is the user. A "logically correct" page that announces badly is unusable. Automated tools do not evaluate announcement quality.

**How to check.**
- Rotor/quick-nav: list "Headings", "Form Controls", "Links", "Landmarks". Each list is sensible; no orphan items, no missing items.
- Names: every form control has a name; every link has descriptive text (not "click here"); every button announces its action.
- States: `aria-expanded` on disclosure widgets toggles audibly; `aria-selected` on tabs/listbox options toggles; `aria-invalid` and `aria-describedby` connect errors to fields.
- Live regions: `aria-live="polite"` on toast/snackbars; `assertive` only for errors that block.
- Landmarks: one `<main>`, one `<nav>` per region, `<header>` and `<footer>` per page; skip-to-main link present and works.

## Stage 4 — Zoom / reflow at 200% and 320 CSS px

**Rule.** Verify both: (a) 200% browser zoom on a 1280px-wide window — page is usable, no horizontal scroll, no content loss. (b) 320 CSS px width — no two-dimensional scrolling, all primary content reachable via vertical scroll only. Exempt content: maps, data tables, presentations.

**Why.** Low-vision users (the largest disability group) zoom 200–400%. Reflow failures are the single most common AA violation in production.

**How to check.**
- 200% zoom: zoom to 200% in Chrome; complete the primary task; no content is cut off, no controls are unreachable.
- 320 px: open devtools responsive mode at 320 × 2560; scroll only vertically; verify every CTA, form, and nav menu is reachable.
- Text-spacing override: also re-run the Stage-2 keyboard sweep with the four 1.4.12 overrides applied; no clipping, no overlap.

## Stage 5 — Contrast in both themes

**Rule.** Run the full Stage 1 + Stage 2 in *both* light and dark themes. A passing audit in light mode that fails in dark mode is a failing audit. Verify every token pair (text × surface, UI × surface, focus × surface) in each theme.

**Why.** Designers tune one theme and ship both. The dark theme is the most common source of late-stage contrast failures because brand colors are often chosen for light-mode use.

**How to check.**
- Toggle the theme mid-session in devtools (`prefers-color-scheme` + a manual override).
- Re-run axe; fix any new violations.
- Spot-check 10 representative screens in dark mode: text, icons, input borders, focus rings, data viz.
- Chart/data viz: verify in both themes, with simulated CVD (Stark, Sim Daltonism).

## Stage 6 — Reduced motion

**Rule.** Enable `prefers-reduced-motion: reduce` in OS settings. Reload every primary page. All non-essential motion stops or shrinks to ≤ 200ms with no large displacement. Essential motion (loading indicator that conveys progress, a focus-trap that animates) may continue but must be subtle.

**Why.** Vestibular disorders affect ~35% of adults at some level. Decorative parallax and scroll-driven animation are the most common offenders.

**How to check.**
- Chrome devtools → Rendering → Emulate CSS media feature `prefers-reduced-motion: reduce`.
- Walk each primary page; flag every animation, transition, transform, scroll-linked effect.
- Auto-playing video/audio: must be pausable; ideally paused.
- Carousels: must not auto-advance, or must respect reduced-motion.

## Report shape

**Rule.** Every finding is a record with these fields, in this order:

| Field | Value |
|---|---|
| **Criterion** | WCAG 2.2 number + name (e.g., `1.4.3 Contrast (Minimum)`) |
| **Location** | file:line *or* CSS selector *or* URL + section (e.g., `src/components/Button.tsx:42`, `.btn--primary`, `https://…/checkout#address`) |
| **Severity** | `Blocker` / `Major` / `Minor` / `Backlog` |
| **Affected users** | one-line "who" (e.g., "low-vision users", "keyboard-only", "screen-reader on Safari") |
| **Evidence** | screenshot, screen-reader transcript, contrast ratio value, or repro steps |
| **Fix** | concrete remediation (token, component, copy) + estimated effort (S/M/L) |

**Severity → launch gate.**

- **Blocker** = AA failure that blocks a primary task for a primary user group. Ship-stopping. Examples: keyboard trap, missing form label, no accessible name on primary CTA, contrast < 3:1 on primary text, focus ring invisible.
- **Major** = AA failure on a secondary task, *or* a primary-task failure for a smaller user group. Fix-before-ship but trackable. Examples: skip link missing, dark-theme contrast fail, modal focus return broken.
- **Minor** = AA-adjacent, AAA, or non-AA-criterion issue that materially affects experience. Ship-with-known-issue acceptable if filed. Examples: 1.4.12 focus area on tertiary control, color-only chart legend on a non-primary chart.
- **Backlog** = nice-to-have, future WCAG, or low-impact. Files in the next cycle.

**Tie severity to launch gate.** Any open `Blocker` = no launch. Any open `Major` on a primary path = no launch. `Minor` + `Backlog` ship with tickets assigned. Sign the report; attach it to the release; do not waive findings by chat — record the decision in the report.
