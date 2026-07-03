---
name: design-taste
description: "The Designer's core taste engine — one multi-mode skill replacing the guild's scattered style skills. Pick and enforce a premium, anti-generic visual language for any interface, then hold the line against AI-slop defaults. Modes: engineer (metric dials, component architecture, the AI-tells ban list); agency (Awwwards-tier 'expensive' aesthetic + motion choreography); minimal (warm editorial monochrome); brutalist (Swiss industrial + tactical terminal); motion (GSAP scroll, AIDA, true-randomized layout); encode (emit a DESIGN.md the whole team follows); redesign (audit and upgrade an existing UI without breaking it). Each mode's full playbook lives in references/. Use for any visual-design, styling, taste, or redesign work. Triggers: 'design the UI', 'make it premium', 'pick a style', 'minimalist', 'brutalist', 'add motion', 'write a DESIGN.md', 'redesign this', 'anti-slop'. Differentiate from imagegen-frontend brand mode (identity/logo), image-to-code (generate+build), and impeccable (npx polish)."
metadata:
  version: 1.0.0
type: Skill

---
# Design Taste — the Designer's core taste engine

This is the Designer's one craft for **deciding and enforcing how an interface looks and feels.**
It replaces seven scattered style skills with a single multi-mode engine: you pick the archetype the
work needs, run that mode's playbook, and hold the line against the generic defaults that make AI
design look cheap. One skill, seven modes — pick one, ship the surface, prove it against the slop test.

## What it is / is not

- It **is** the aesthetic decision + enforcement layer: pick a visual language, apply it, defend it.
- It is **not** `imagegen-frontend`'s `brand` mode — that builds the identity system (logo, palette, brand
  decks). Taste dresses a product; `brand` mode defines who the product *is*. Taste consumes its tokens, it
  doesn't set them.
- It is **not** `image-to-code` / `imagegen-*` — those *generate* assets and screens. Taste decides the
  language those generators must obey.
- It is **not** `impeccable` — that is the external npx polish/critique tool, kept separate. Reach for it
  to audit a finished surface; reach for `design-taste` to set the direction first.

## When to run which mode

| Mode | Pick it when | Full playbook |
|---|---|---|
| `engineer` | Default. Any build that needs strict, metric-driven frontend taste + anti-slop guardrails | `references/engineer.md` |
| `agency` | The surface must feel *expensive* — Awwwards-tier, hero-led marketing sites, premium product pages | `references/agency.md` |
| `minimal` | Editorial, content-first, warm monochrome; calm utilities and dashboards that must feel quiet | `references/minimal.md` |
| `brutalist` | Data-heavy dashboards, portfolios, dev tools that should read like declassified blueprints | `references/brutalist.md` |
| `motion` | Motion is the point — GSAP scroll choreography, AIDA narrative pages, true-randomized layout | `references/motion.md` |
| `encode` | The whole team needs one written design system — emit a `DESIGN.md` other agents follow | `references/encode.md` |
| `redesign` | An existing UI is generic or dated — audit it and lift it without breaking functionality | `references/redesign.md` |

## The modes

- **`engineer`** — the baseline taste any build inherits. Three metric dials you set per project —
  `DESIGN_VARIANCE`, `MOTION_INTENSITY`, `VISUAL_DENSITY` (1–10) — plus strict component architecture,
  hardware-accelerated CSS, and the **AI-tells ban list** (forbidden visual/typographic/layout/content
  patterns). Start here; layer an archetype on top.
- **`agency`** — the "expensive" aesthetic. The Absolute-Zero anti-pattern rules, a creative variance
  engine (pick one vibe/texture archetype + one layout archetype), haptic micro-aesthetics (nested
  "double-bezel" architecture, island buttons, spatial tension) and fluid motion choreography.
- **`minimal`** — premium utilitarian minimalism. Banned: gradients, heavy shadows, decoration for its
  own sake. Warm monochrome + spot pastels, typographic contrast, flat bento grids, restrained micro-motion.
- **`brutalist`** — Swiss industrial print fused with tactical-telemetry/CRT terminal. Rigid grids, extreme
  type-scale contrast, utilitarian colour, analog degradation. For surfaces that should feel engineered.
- **`motion`** — Python-driven true randomization to break the template loop, strict AIDA page structure,
  the hero 2-line iron rule, gapless bento, GSAP ScrollTriggers (pinning, stacking, scrubbing), a mandatory
  `<design_plan>` pre-flight before any code.
- **`encode`** — turn a chosen language into an agent-readable `DESIGN.md` (atmosphere, palette, type,
  hero, components, layout, responsive, motion, anti-patterns) so every other member builds in one voice.
- **`redesign`** — audit an existing surface for generic AI patterns, then upgrade typography, colour,
  layout, and motion to premium standard **without breaking the existing functionality or framework.**

## Shared design laws (every mode obeys)

- **Type:** one expressive type pairing, real scale contrast (don't ship everything at 16px). No 6-line wraps.
- **Colour:** a deliberate palette from `imagegen-frontend` (`brand` mode) tokens — never raw framework defaults, never a rainbow.
- **Layout:** intentional asymmetry and rhythm over centered-everything. Whitespace is structure, not filler.
- **Motion:** purposeful and hardware-accelerated (`transform`/`opacity`), never decorative jank.
- **The AI-slop test:** before shipping, ask — *does this look like a default Tailwind/Bootstrap template?*
  generic gradient hero, three equal cards, lucide icons everywhere, `#3B82F6` blue, centered everything,
  "Jane Doe" placeholder copy? If yes, it failed. Push a dial, change an archetype, re-run.

## How the Designer works

1. **Pick the mode** from the table — default `engineer`, then layer an archetype (`agency`/`minimal`/
   `brutalist`/`motion`) if the surface has a clear character.
2. **Load that mode's `references/*.md`** for the full playbook — the dispatcher above is the index, the
   detail lives in the reference so this file stays lean.
3. **Set the dials** (`engineer` mode) and pull tokens from `imagegen-frontend` (`brand` mode); never invent identity here.
4. **Build, then run the slop test.** The Designer (a Claude model) plans and critiques; spawn Claude
   subagents via the Task tool to generate variants in parallel. Nothing ships until it passes the slop test.
5. **Encode it** when more than one surface or member is involved — run `encode` to emit a `DESIGN.md`
   so the whole guild builds to one language.

## Sharpening the craft

- **Apprentice** — runs one archetype literally, ships the reference verbatim. Measure: slop-test pass rate.
  Outgrow: shipping the template; centered-everything; default blue.
- **Journeyman** — sets the dials per project and blends two archetypes cleanly (agency hero + minimal body).
  Measure: how few revisions to a "feels premium" sign-off. Outgrow: motion for its own sake; dial maxing.
- **Artisan** — encodes the language into a `DESIGN.md` other members build against, and keeps the
  reference playbooks current as taste shifts. Measure: cross-member visual consistency. Outgrow: hoarding
  taste in your head instead of writing it down.
- **Master** — invents a coherent new archetype when none fit, adds it as an eighth `references/*.md`, and
  the guild's look levels up. Measure: archetypes promoted into the engine. Outgrow: novelty without rigor.

## Gotchas

- Don't merge `impeccable` in — it is external/npx-managed and synced from upstream; keep it standalone.
- `minimal` and `brutalist` are *mutually exclusive* archetypes — pick one per surface, never blend them.
- The detail is in `references/`; resist re-inflating this SKILL.md back toward the seven originals — that
  re-creates the bloat the merge removed and risks the Cowork word ceiling.
- Taste without identity tokens drifts. If the identity isn't set, run `imagegen-frontend` (`brand` mode) first.

## Versioning
Own skill (consolidates seven prior style skills). Bump `metadata.version` on any change (PATCH: wording/refs · MINOR: new mode/reference · MAJOR: method contract change). Regenerate `VERSIONS.md` with `python3 star-alliance-skills/skillsmith/scripts/skill_registry.py write` after a bump, then `python3 build.py`.

## Changelog
- **1.0.0** — Initial release. Consolidates `design-taste-frontend`, `high-end-visual-design`, `minimalist-ui`, `industrial-brutalist-ui`, `gpt-taste`, `stitch-design-taste`, and `redesign-existing-projects` into one seven-mode taste engine; each original playbook preserved verbatim under `references/`. `impeccable` (external) kept separate.
