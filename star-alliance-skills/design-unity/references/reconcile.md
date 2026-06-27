---
type: Document
title: design-unity — reconcile phase
description: Fix UI drift — raw values to tokens, duplicate components to the canonical one, strays to the scale — without breaking functionality.
timestamp: 2026-06-27T00:00:00Z
---

# Phase 3 — reconcile the drift

Goal: drive the audit report to zero divergences without breaking a single surface. Input: the ranked
`design-unity-audit.md`. Work top-down by blast radius — the common offender first.

## The order of operations

1. **Fix doc↔token drift first.** If `DESIGN.md` and the token file disagreed, reconcile them to one truth
   before touching any surface — otherwise you fix toward a moving target.
2. **Tokenize the highest-frequency raw values.** Replace the literal used in 40 files before the one used
   twice. One token swap unifies every call site at once.
3. **Align off-scale values to the nearest canonical step** — unless the stray was *intentional* (a deliberate
   one-off the designer wants); confirm intent before flattening it. Document a sanctioned exception in `DESIGN.md`.
4. **Collapse duplicate components.** Replace inline re-implementations with the canonical inventory component;
   migrate props/variants. If a duplicate has a genuinely new variant, promote that variant into the canonical
   component (and `DESIGN.md`), don't keep a fork.
5. **Resolve orphans.** Promote a recurring one-off into a token/component, or delete a true one-off. Never
   leave it to multiply.

## How to apply the fixes (doer + thinker)

- The **doer** (`minimax-m3`) does the mechanical sweep: raw `#3B82F6` → `var(--color-primary)`, `gap: 7px` →
  `gap: var(--space-2)`, etc., across the flagged sites. Bulk find-and-replace is its job.
- The **thinker** (sonnet) owns the judgement calls the doer can't make: which value is canonical when two
  compete, which duplicate component is the keeper, whether a stray is intentional, whether an orphan is
  promoted or deleted. Plan → dispatch the doer per finding-cluster → review the diff against the SoT → re-run.

## The non-negotiable: don't break functionality

A token swap is a **value change, not a refactor.** After each cluster of fixes:

- Verify the surface still **renders** (it loads, no console/CSS errors) and **behaves** (the button still
  clicks, the modal still opens). A wrong token can silently change a colour to transparent or a size to zero.
- Prefer reversible, scoped edits over a sweeping regex that also hits strings, comments, or test fixtures.
- Keep changes in reviewable batches (one divergence class or one component at a time), not one giant diff.

## Close the loop

- **Re-run `audit`.** The report must trend to zero. Surviving findings are either fixed-this-pass or a
  documented exception — nothing silently ignored.
- **Update the SoT for anything new.** A promoted variant or a new token means a `DESIGN.md` line + a token in
  the same change; the two artifacts never drift apart.
- **Report.** What was tokenized, what components collapsed, the before/after divergence count, and any
  sanctioned exceptions. That report is the proof the UI is now one-handed.

## Safety

- **No mass auto-fix without the audit.** Reconcile only what the ranked report flagged; don't freelance.
- **Confirm before flattening intentional contrast** — uniformity is the goal, but a deliberate accent surface
  or a one-off hero is not "drift." Unity is one *language*, not one *look-for-everything*.
