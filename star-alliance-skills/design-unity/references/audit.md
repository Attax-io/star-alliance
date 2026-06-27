---
type: Document
title: design-unity — audit phase
description: Scan every UI surface for divergence from the source of truth and rank it by blast radius.
timestamp: 2026-06-27T00:00:00Z
---

# Phase 2 — audit every surface against the source of truth

Goal: a ranked, `file:line` report of every place a surface diverges from the `DESIGN.md` + token SoT.
Precondition: the SoT exists (run `establish` first). Auditing without a SoT measures chaos against chaos.

## The divergence taxonomy (what counts)

| Class | Signal | Example |
|---|---|---|
| **Hardcoded value** | a raw hex/rgb/px/rem where a token names the same thing | `color: #3B82F6` while `--color-primary` is that blue |
| **Off-scale value** | a number not on the canonical scale | `gap: 7px`, `font-size: 13px`, `border-radius: 5px` |
| **Duplicate component** | a second implementation of a component already in the inventory | a local `<button class=...>` instead of the `Button` |
| **Inconsistent treatment** | same role, different look | two "primary" CTAs with different radius / weight / height |
| **Orphan pattern** | a one-off that should be a token/component or be deleted | a bespoke card shadow used in exactly one file |
| **Doc↔token drift** | `DESIGN.md` and the token file disagree | doc says 8px base, tokens ship a 6px step |

The last class is checked first — if the two SoT artifacts disagree, every downstream audit is unreliable.

## The scan recipe (hand the bulk to the doer)

The thinker frames the patterns and makes the keep/kill calls; `minimax-m3` (or `rg`) does the grepping.

1. **Colours.** Grep every `#hex`, `rgb(/rgba(`, `hsl(`, `oklch(` in component/style files. Any literal that
   equals (or is a near-cluster of) a token value is a **hardcoded** divergence. Any literal with no token at
   all is either an orphan (promote to a token) or genuine drift.
2. **Spacing / sizing.** Grep margin/padding/gap/width/height literals. Flag any value not on the spacing scale.
   Watch for unit-mixing (`px` where the system is `rem`).
3. **Type.** Grep `font-size` / `font-weight` / `line-height`. Flag anything off the type scale or any ad-hoc
   pairing the scale doesn't sanction.
4. **Radius / shadow / border / z-index.** Grep each; flag off-scale steps and one-off shadows.
5. **Components.** List component definitions; find inline re-implementations of inventory components (a raw
   `<button>`/`<input>`/modal markup where a canonical component exists). Flag duplicates and near-duplicates.
6. **Motion.** Grep `transition` / `animation` / `@keyframes`; flag durations/easings off the motion tokens.

Exclude vendored/generated dirs (`node_modules`, build output, third-party). On macOS prefer `rg` or
`LC_ALL=C grep` — plain `grep` silently misses matches in UTF-8/multibyte files.

## Rank by blast radius

Sort findings so the highest-leverage fixes surface first:

1. **Frequency** — a hardcoded colour in 40 files outranks one in 2. Fixing the common one unifies the most.
2. **Visibility** — shared primitives (buttons, headers, the global shell) outrank a buried admin corner.
3. **Class severity** — duplicate components and doc↔token drift outrank a single off-scale gap.

Each finding: `path:line` · class · the offending value · the canonical token/component it should use ·
the count (how many sites share it).

## Output

A `design-unity-audit.md` report: a ranked table of divergences + a one-line headline
("N divergences across M files; top offender: raw `#3B82F6` in 41 sites → `--color-primary`"). This report is
the input to `reconcile`. Do not fix during the audit — measure first, fix in the next phase by blast radius.

## Standing-guard mode

For a recurring check (the Master level), run a thinned audit on just the changed files of a diff and treat any
**new** divergence as a failing test — the UI stays one-handed because drift never lands in the first place.
