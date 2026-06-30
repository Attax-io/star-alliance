---
type: Document
title: design-unity — establish phase
description: Build or extract the single source of truth — DESIGN.md plus a canonical code token file.
timestamp: 2026-06-27T00:00:00Z
---

# Phase 1 — establish the single source of truth

Goal: one `DESIGN.md` (the language) and one code token file (the enforcement) that every surface consumes.
Two artifacts, kept in lockstep. Nothing downstream is meaningful until this exists.

## Step 1 — decide: author or extract?

- **Greenfield / language already decided** → run `design-taste`'s `encode` mode first; it emits a starting
  `DESIGN.md` (atmosphere, palette, type, components, motion, anti-patterns). Harden that into the SoT below.
- **Existing UI with no system** → *extract* the de-facto system from the code. The values are already there,
  scattered and inconsistent — your job is to find them, dedupe to a canonical scale, and name them once.

## Step 2 — extract the de-facto values (existing UI)

Hand the bulk scan to the doer (`minimax-m3`); the thinker makes the canonical calls.

- **Colours** — every hex/rgb/hsl/oklch in the codebase, with frequency. Cluster near-duplicates (`#3b82f6`,
  `#3c83f7`, `rgb(59,130,246)` are one colour). The most-used member of a cluster is the canonical candidate.
- **Spacing** — every margin/padding/gap value. Most UIs cluster around a 4px or 8px base; surface the real steps.
- **Type** — font-size / line-height / weight pairs in use. Collapse to a scale (e.g. 12/14/16/20/24/32/48).
- **Radius, shadow, border, z-index, motion (duration/easing)** — same: list, cluster, pick the canonical step.

Output a raw inventory (value → count → files). High count = load-bearing, keep it; low count + near a cluster =
drift, fold it in.

## Step 3 — mint the canonical token set

Reduce each inventory to a **small, named, intentional scale**. Fewer tokens than raw values — that reduction
IS the unification. Name by **role, not value** (`--color-primary`, not `--color-blue-500`; `--space-3`, not
`--space-12px`) so the value can change without renaming every call site.

Write them into **one** token file in the project's idiom:
- CSS custom properties in a `:root` (and a dark scope if themed) — the most portable.
- Tailwind: the `theme.extend` in `tailwind.config`.
- A JS/TS theme object if the stack consumes tokens that way.

One file. If you find two competing theme files, merging them to one is part of this phase.

## Step 4 — write DESIGN.md (the language)

The canonical narrative. Keep it tight; it describes the tokens and the rules, it does not duplicate code.
Sections:

1. **Atmosphere** — one paragraph: what this product should feel like, who uses it, the anti-references.
2. **Colour** — the role tokens, when each applies, the contrast rules, the "never raw hex" rule.
3. **Type** — the scale, the pairing, hierarchy rules (weight/size contrast), max line length.
4. **Spacing & layout** — the scale, the grid/rhythm rules, density.
5. **Radius / elevation / border** — the steps and when each is used.
6. **Motion** — duration + easing tokens, what may animate, `prefers-reduced-motion`.
7. **Component inventory** — the canonical components (Button, Card, Input, Modal…), each with its variants.
   This is the dedup contract: a new component must reuse one of these or earn a new entry here.
8. **Anti-patterns** — the banned moves (hardcoded hex, off-scale values, duplicate components, side-stripe
   borders, gradient text, etc.). This is what `audit` checks against.

## Step 5 — wire the token contract

- Components import from the token file; **no raw values** in component code.
- Add a short rule to the project's contributor docs (or `DESIGN.md` itself): "new UI consumes tokens; a value
  not in the tokens needs a token added (and a `DESIGN.md` line), not a hardcode."
- If the project has a linter, a `no-hardcoded-color` / scale-enforcement rule makes the contract bite at write
  time — note it as a follow-up; it is the Master-level standing guard.

## Done when

- One `DESIGN.md` + one token file exist, agree, and live at a known canonical path.
- Every token has a role name and a `DESIGN.md` line; every `DESIGN.md` rule has a token or a stated exception.
- You can now run `audit` against a real source of truth.
