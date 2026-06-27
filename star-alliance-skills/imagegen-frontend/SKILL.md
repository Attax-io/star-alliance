---
name: imagegen-frontend
description: "The Designer's reference-imagery engine — generate premium, conversion-aware frontend design references with image-01. Generates IMAGES ONLY (reference art a developer or coding model recreates), never production code — for code use image-to-code. Modes: web (landing / marketing sites / product comps — one separate horizontal image PER section, composition variety, varied hero scales, anti-AI-slop, one consistent palette); mobile (iOS / Android / cross-platform app screens and flows — screen-first inside a premium phone mockup, multi-screen consistency, platform-aware, readable type, custom iconography). Each mode's playbook lives in references/. Use when reference imagery is needed before building a UI. Triggers: 'generate website design references', 'mock the landing page', 'design the app screens', 'show me onboarding screens', 'imagegen'. Differentiate from image-to-code (build production code), design-taste (decides the visual language), brandkit (logo / identity)."
metadata:
  version: 1.0.0
type: Skill

---
# imagegen-frontend — the Designer's reference-imagery engine

One craft for **generating premium frontend design reference images** with the `image-01` doer.
You pick the surface the work needs, run that mode's full playbook, and ship reference imagery a
developer (or a coding model) can recreate faithfully. One skill, two modes — pick one, generate the
frames, hold the line against generic AI-image defaults.

## What it is / is not

- It **is** the reference-imagery layer: art-direct and generate the design *images* before code exists.
- It is **not** `image-to-code` — that turns a reference image into production frontend. This skill stops
  at the image; `image-to-code` builds from it. They pair: imagegen-frontend → image-to-code.
- It is **not** `design-taste` — that *decides* the visual language (archetype, dials, anti-slop laws).
  This skill *renders* references in that language; run `design-taste` first when the direction is unset.
- It is **not** `brandkit` — that forges the identity system (logo, palette, brand decks). This renders
  product/marketing screens, not the brand mark.

## When to run which mode

| Mode | Pick it when | Full playbook |
|---|---|---|
| `web` | Website / landing / marketing-site / product-comp references — desktop-led, section-by-section | `references/web.md` |
| `mobile` | iOS / Android / cross-platform app screen + flow concepts — phone-mockup-framed, multi-screen | `references/mobile.md` |

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

## Shared laws (both modes obey)

- **Images only.** This skill never writes code. Reference art out; `image-to-code` builds from it.
- **One consistent palette** across every frame of a set — pick it once, hold it.
- **Anti-AI-slop.** No centered-dark-hero + purple/blue glow reflex; no generic stock-mockup defaults.
  If the frame could be guessed from the category alone, re-direct it.
- **Recreatable.** Frames must be believable real-product concepts a developer can rebuild — not abstract art.
- **Consume the direction, don't invent it.** Pull the archetype/palette from `design-taste` + `brandkit`
  tokens when they're set; only improvise when no direction exists yet.

## How the Designer works

1. **Set the direction first** — if the visual language isn't decided, run `design-taste`; if the identity
   isn't set, run `brandkit`. This skill renders inside their decisions.
2. **Pick the mode** — `web` for sites, `mobile` for app screens. Load that mode's `references/*.md` for the
   full playbook; this file is the index, the detail lives in the reference so it stays lean.
3. **Dispatch the doer.** The thinker (sonnet) holds the art-direction brief; the `image-01` doer generates.
   Generate sequentially when the runner is one-at-a-time, announcing each frame ("Section 3 of 8: Pricing").
4. **Run the slop test** on every frame before handing off. Re-direct any frame that reads as generic.
5. **Hand off to `image-to-code`** when the references are approved and production code must mirror them.

## Gotchas

- **`web` mode's one-image-per-section rule is non-negotiable** — never collapse a page into one tall image.
- Don't reach here for production code (→ `image-to-code`) or for the brand mark/identity (→ `brandkit`).
- The detail lives in `references/`; resist re-inflating this SKILL.md — that re-creates the bloat the merge
  removed and risks the Cowork word ceiling.

## Versioning
Own skill (consolidates `imagegen-frontend-web` + `imagegen-frontend-mobile`). Bump `metadata.version` on any change (PATCH: wording/refs · MINOR: new mode/reference · MAJOR: method-contract change). Regenerate `VERSIONS.md` with `python3 star-alliance-skills/skillsmith/scripts/skill_registry.py write`, then `python3 build.py`.

## Changelog
- **1.0.0** — Initial release. Merges `imagegen-frontend-web` and `imagegen-frontend-mobile` into one two-mode reference-imagery engine; each original playbook preserved verbatim under `references/` (`web.md`, `mobile.md`). `brandkit` (identity system, cross-referenced by the Herald + design-taste) deliberately kept separate.
