---
name: imagegen-frontend
description: "The Designer's image-generation engine — generate premium design imagery with image-01, one multi-mode skill for every visual surface. Generates IMAGES ONLY (reference art a developer or coding model recreates), never production code — for code use image-to-code. Modes: web (landing / marketing sites / product comps — one separate horizontal image PER section, varied hero scales, anti-AI-slop, one consistent palette); mobile (iOS / Android / cross-platform app screens and flows — screen-first in a premium phone mockup, multi-screen); brand (the identity system — brand-guideline boards, logo systems, identity decks, the brand mark). Each mode's playbook lives in references/. Use when design imagery is needed. Triggers: 'generate website design references', 'mock the landing page', 'design the app screens', 'create a brand kit', 'design the logo / identity', 'imagegen'. Differentiate from image-to-code (build production code) and design-taste (decides the visual language)."
metadata:
  version: 1.0.0
type: Skill

---
# imagegen-frontend — the Designer's image-generation engine

One craft for **generating premium design imagery** with whatever image-generation tool the session
has to hand. You pick the surface the work needs, run that mode's full playbook, and ship imagery a
developer (or a coding model) can recreate faithfully — or a brand-identity board ready to present.
One skill, three modes — pick one, generate the frames, hold the line against generic AI-image
defaults.

## What it is / is not

- It **is** the image-generation layer: art-direct and generate the design *images* (screens or identity).
- It is **not** `image-to-code` — that turns a reference image into production frontend. This skill stops
  at the image; `image-to-code` builds from it. They pair: imagegen-frontend → image-to-code.
- It is **not** `design-taste` — that *decides* the visual language (archetype, dials, anti-slop laws).
  This skill *renders* in that language; run `design-taste` first when the direction is unset.
- `brand` mode **is** the identity system (logo, palette, brand decks, the brand mark) — formerly the
  standalone `brandkit` skill, folded in here. `design-taste` and `design-language` consume its tokens.

## When to run which mode

| Mode | Pick it when | Full playbook |
|---|---|---|
| `web` | Website / landing / marketing-site / product-comp references — desktop-led, section-by-section | `references/web.md` |
| `mobile` | iOS / Android / cross-platform app screen + flow concepts — phone-mockup-framed, multi-screen | `references/mobile.md` |
| `brand` | The identity system — brand-guideline boards, logo systems, identity decks, the brand mark | `references/brand.md` |

## The modes

- **`web`** — elite Awwwards-level website art direction. The **hard output rule**: generate ONE separate
  horizontal image PER section (8 sections → 8 images, never one tall page). Combinatorial variation engine,
  hero-composition bias (the left-text/right-image hero is the overused default — earn it), varied hero
  scales (giant / mid / mini minimalist), anti-AI-slop rules, typography-first discipline, and a single
  consistent palette across every frame. For landing pages, marketing sites, and product comps.
- **`mobile`** — premium app-native screen direction for iOS / Android / cross-platform. Screen-first inside
  a subtle premium phone mockup, multi-screen + screen-to-screen consistency, platform-mode awareness, safe-
  area discipline, comfortably readable type, custom iconography, textured surfaces, and a style-variation
  engine. For onboarding, auth, dashboards, profile, settings, chat, ecommerce, fintech, health, social.
- **`brand`** — premium brand-identity art direction (formerly the `brandkit` skill). Brand-guideline boards,
  logo systems (monogram, product-action, metaphor-fusion, negative-space, construction-geometry), the default
  3×3 panel system, identity decks, premium mockups, and visual-world presentations. Strategy-first: a
  complete brand world in one image. The Herald briefs what it must *say*; the Designer forges it.

## Shared laws (both modes obey)

- **Images only.** This skill never writes code. Reference art out; `image-to-code` builds from it.
- **One consistent palette** across every frame of a set — pick it once, hold it.
- **Anti-AI-slop.** No centered-dark-hero + purple/blue glow reflex; no generic stock-mockup defaults.
  If the frame could be guessed from the category alone, re-direct it.
- **Recreatable.** Frames must be believable real-product concepts a developer can rebuild — not abstract art.
- **Consume the direction, don't invent it.** In `web`/`mobile`, pull the archetype/palette from
  `design-taste` when it's set; `brand` mode is where the identity itself gets forged.

## How the Designer works

1. **Set the direction first** — if the visual language isn't decided, run `design-taste`. If the *identity*
   isn't set, run this skill's `brand` mode first; `web`/`mobile` then render inside that identity.
2. **Pick the mode** — `web` for sites, `mobile` for app screens, `brand` for the identity system. Load that
   mode's `references/*.md` for the full playbook; this file is the index, the detail lives in the reference.
3. **Generate the frames.** The Designer (a Sonnet subagent) holds the art-direction brief and drives
   whatever image-generation tool the session has available. Generate sequentially when the tool is
   one-at-a-time, announcing each frame ("Section 3 of 8: Pricing").
4. **Run the slop test** on every frame before handing off. Re-direct any frame that reads as generic.
5. **Hand off to `image-to-code`** when the references are approved and production code must mirror them.

## Gotchas

- **`web` mode's one-image-per-section rule is non-negotiable** — never collapse a page into one tall image.
- Don't reach here for production code (→ `image-to-code`) or to *decide* the visual language (→ `design-taste`).
- `brand` mode owns identity tokens; `design-taste` / `design-language` consume them, never set them.
- The detail lives in `references/`; resist re-inflating this SKILL.md — that re-creates the bloat the merge
  removed and risks the Cowork word ceiling.

## Versioning
Own skill (consolidates `imagegen-frontend-web` + `imagegen-frontend-mobile` + `brandkit`). Bump `metadata.version` on any change (PATCH: wording/refs · MINOR: new mode/reference · MAJOR: method-contract change). Regenerate `VERSIONS.md` with `python3 star-alliance-skills/skillsmith/scripts/skill_registry.py write`, then `python3 build.py`.

## Changelog
- **1.0.0** — Initial release. Merges `imagegen-frontend-web`, `imagegen-frontend-mobile`, and `brandkit` into one three-mode image-generation engine (`web` / `mobile` / `brand`); each original playbook preserved verbatim under `references/` (`web.md`, `mobile.md`, `brand.md`). `brand` mode (formerly `brandkit`) stays shared with the Herald, who briefs the identity the Designer forges.
