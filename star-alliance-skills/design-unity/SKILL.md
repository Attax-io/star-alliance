---
name: design-unity
description: "The Designer's UI-unity guardian — make ONE design language the single source of truth and hold every surface to it. Three phases: establish (define or extract the canonical DESIGN.md plus a real code token file — CSS custom properties / theme — doc describes, tokens enforce); audit (scan every surface and flag divergence from the source of truth — hardcoded hex, off-scale spacing / type / radius / shadow, duplicate components, inconsistent motion — ranked by blast radius, file:line); reconcile (fix the drift — raw values to tokens, duplicate components to the canonical one, strays to the scale, without breaking functionality). Use to unify a UI, kill design drift, enforce a design system, or stand up a single source of truth. Triggers: 'make the UI consistent', 'one source of truth for the UI', 'enforce the design system', 'kill the design drift', 'unify the look', 'audit UI conformity', 'design tokens'. Differentiate from design-taste (decides the language) and imagegen-frontend (generates imagery)."
metadata:
  version: 1.1.0
type: Skill

---
# design-unity — one source of truth, every surface in one language

This is the Designer's craft for **UI conformity and unity.** A product looks designed-by-one-hand only
when every surface obeys **one** visual language, written down **once** and enforced everywhere. This skill
stands up that single source of truth and holds the whole UI to it — so a button, a card, a heading, a
spacing step never get re-invented in five slightly-different ways across five files.

It is a three-phase loop. Run them in order on a drifting UI, or enter at the phase you need.

## The one principle

**One source of truth, two artifacts that must agree:**
- **`DESIGN.md`** — the *language*: palette roles, type scale, spacing scale, radius/elevation, motion, the
  component inventory, and the anti-patterns. Human- and agent-readable. The *why* and the *vocabulary*.
- **A code tokens file** — the *enforcement*: CSS custom properties / a theme file / Tailwind config that
  every component consumes. The *what*, machine-checkable. No surface hardcodes a value the tokens already name.

The doc **describes**, the tokens **enforce**. If they disagree, the UI has two sources of truth and unity is
already lost. Keeping them in lockstep is the whole job.

## The three phases

| Phase | What it does | Playbook |
|---|---|---|
| `establish` | Define or **extract** the single source of truth: write `DESIGN.md`, mint the token set (dedupe the de-facto values already in the code into one canonical scale), wire the token contract | `references/establish.md` |
| `audit` | Scan every surface for **divergence** from the SoT and report it ranked by blast radius, `file:line` | `references/audit.md` |
| `reconcile` | **Fix** the drift — raw values to tokens, duplicate components to the canonical one, strays to the scale — without breaking functionality | `references/reconcile.md` |

## When to run which

- **No design system yet, or it lives only in someone's head** → `establish`. Bootstrap from `design-taste`'s
  `encode` mode (it emits a first `DESIGN.md`); this skill hardens it into the SoT + the token contract.
- **A system exists but surfaces drift from it** → `audit`, then `reconcile` the findings.
- **Recurring guard** → `audit` on every design-touching change; treat a new divergence like a failing test.

## The divergence taxonomy (what "drift" means)

A surface is **non-conformant** when it does any of these instead of consuming the SoT:
- **Hardcoded value** — a raw hex/rgb/px the tokens already name (`#3B82F6` where `--color-primary` exists).
- **Off-scale value** — a spacing/type/radius/shadow step not on the canonical scale (`13px`, `7px` gap).
- **Duplicate component** — a second Button/Card/Modal that re-implements one that already exists.
- **Inconsistent treatment** — same role, different look (two "primary" buttons with different radius/weight).
- **Orphan pattern** — a one-off that should be promoted into the system or deleted, not left to multiply.

**Not drift:** an *annotated intentional lock* — a hardcode kept on purpose (dark-mode contrast where the token
flips, a fixed brand mark, a PDF/email/canvas context where CSS vars don't resolve, a token definition itself).
The `audit` phase **subtracts these first** (its Step 0); a sweep that converts them is a regression, not a fix.

Full detection recipe + ranking in `references/audit.md`.

## How the Designer works

1. **Find or forge the SoT first.** Never audit against nothing. If there is no `DESIGN.md` + token file,
   run `establish` (bootstrapping from `design-taste encode`). One canonical file each — not per-feature copies.
2. **Audit the surfaces.** Fan the bulk scan/extraction out to parallel Claude subagents (Task tool) when the
   surface is large; the Designer (running as sonnet) sets the taste calls — which value is canonical, which
   duplicate is the keeper. Output a ranked divergence report.
3. **Reconcile by blast radius.** Fix the value used in 40 files before the one used twice. Replace raw values
   with tokens, collapse duplicates to the canonical component, align strays to the scale. Re-run `audit` to zero.
4. **Keep doc and tokens in lockstep.** Every token change updates `DESIGN.md`; every `DESIGN.md` rule has a
   token (or a documented exception). A drift between the two artifacts is itself a divergence — fix it first.
5. **Make it a standing guard, not a one-time sweep.** Conformity decays; re-audit on every UI change.

## Boundaries — what it is not

- It is **not** `design-taste` — that *decides* the visual language (archetype, dials, anti-slop). design-unity
  takes a decided language, makes it the **single** source of truth, and **enforces** it. Taste authors; unity guards.
- It is **not** `imagegen-frontend` — that *generates* imagery/screens. Unity governs the shipped code's tokens.
- It is **not** `impeccable` — that is the external npx polish/critique tool. design-unity is the guild-native
  conformity sweep against a token SoT.
- It is **not** `guild-conformity` / `dashboard-parity` — those audit the *repo's* cross-references and render
  state. design-unity audits the *visual* language of a product's UI.

## Sharpening the craft

- **Apprentice** — extracts a token file and replaces obvious hardcoded hex. Measure: % of raw values tokenized.
  Outgrow: tokenizing colour only while spacing/type still drift.
- **Journeyman** — runs the full taxonomy, collapses duplicate components, ranks fixes by blast radius. Measure:
  divergences per 1000 lines, trending down. Outgrow: auto-aligning a stray that was *intentionally* off-scale.
- **Artisan** — keeps `DESIGN.md` and tokens in perfect lockstep and promotes recurring orphans into the system.
  Measure: time-to-conformance after a new feature lands. Outgrow: a SoT so rigid the product can't evolve.
- **Master** — bakes the audit into the team's loop so drift is caught at write time, and the UI stays
  one-handed as it scales. Measure: zero net new divergence across releases. Outgrow: enforcing uniformity where
  deliberate contrast was the point.

## Gotchas

- **Audit needs a SoT.** Running `audit`/`reconcile` with no canonical token file just measures chaos against
  chaos. `establish` is the gate.
- **Raw match count ≠ drift count.** Always subtract intentional locks / token definitions / tests / no-var
  contexts (audit Step 0) before reporting or reconciling. Headlining the raw count over-reports and makes the
  sweep dangerous. Discover the project's lock annotation (e.g. `theme-flat`) by READING the comments around a
  sample of hardcodes first.
- **Colour locks need both themes verified.** Never convert a colour you can't view in light AND dark mode — a
  flipping token is exactly why the lock exists.
- **Reconcile never breaks functionality.** A token swap is a value change, not a refactor — verify the surface
  still renders and behaves before moving on.
- **Two token files = no source of truth.** If you find competing theme files, merging them to one IS the task.
- **The detail lives in `references/`;** resist re-inflating this SKILL.md back toward the playbooks.

## Versioning
Own skill. Bump `metadata.version` on any change (PATCH: wording/refs · MINOR: new phase/reference · MAJOR: method-contract change). Regenerate `VERSIONS.md` with `python3 star-alliance-skills/skillsmith/scripts/skill_registry.py write`, then `python3 build.py`.

## Changelog
- **1.1.0** — Added **intentional-lock detection** (audit Step 0): the audit now subtracts annotated locks (e.g. `theme-flat`), token definitions, test fixtures, and no-var (PDF/email/canvas) contexts BEFORE counting drift, and reports the genuine-drift count rather than the raw match count. Reconcile now mandates verifying BOTH light and dark mode after every batch (a flipping token is why the lock exists) and never converting a lock. Mined from a real run on the Lex Council App where 97/408 raw-hex hits were intentional dark-mode-contrast locks — a naive hex→token sweep would have regressed dark mode. SKILL.md taxonomy + gotchas, `references/audit.md` (Step 0 + output split), `references/reconcile.md` (dark-mode safety).
- **1.0.0** — Initial release. The Designer's UI-unity / conformity engine: three-phase loop (establish → audit → reconcile) over a single source of truth (`DESIGN.md` + a code token file). Playbooks under `references/`. Pairs with `design-taste` (encode mode bootstraps the SoT) and `impeccable`.
