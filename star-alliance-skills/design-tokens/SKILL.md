---
name: design-tokens
description: "The Designer's token-architecture craft — structure a design-token system that scales, themes, and ports across platforms. Modes: architect (three-tier layering — primitive tokens for raw palette/type/space, semantic tokens named by role, component-scoped tokens; components consume only semantic tokens, theming happens at the semantic layer); theme (light, dark, high-contrast from ONE semantic layer by remapping values; OKLCH for perceptually-uniform tonal ramps and accessible lightness); responsive (fluid type/space scales with clamp(), container queries, logical properties for RTL-safe layout); format (the W3C Design Tokens JSON spec so one source compiles to CSS/iOS/Android). Use to design a token system, set up theming, structure tokens, or build dark mode. Triggers: 'design tokens', 'token architecture', 'set up theming', 'dark mode tokens', 'semantic tokens', 'OKLCH palette', 'W3C design tokens'. Differentiate from design-unity (audits drift) and a11y-craft (the accessibility gate)."
metadata:
  version: 1.1.0
type: Skill

---
# design-tokens — primitive, semantic, component; one source, every platform

This is the Designer's craft for **token architecture**. The guild's doctrine names a code token
file as the single source of truth — this skill is *how that file is structured* so it scales,
themes, and ports. It does not audit drift (that is [[design-unity]]) and it does not decide the
visual language (that is design-taste); it builds the **token system** those crafts depend on.

A token system earns its keep when a designer can re-theme an entire product, add dark mode, or
ship to a second platform by editing *values at one layer* — never hunting hardcoded hex.

## Four modes

- **architect** — the three-tier layering in [references/token-architecture.md](references/token-architecture.md):
  **primitive** tokens (raw palette / type ramp / space scale / radii / shadows, named by what they
  ARE — blue-500, space-4), **semantic** tokens (named by ROLE — color-bg-surface,
  color-text-default, color-action-primary, referencing primitives), **component** tokens (scoped —
  button-bg, card-padding, referencing semantics). The rule: components consume **only** semantic /
  component tokens, never primitives; theming happens at the semantic layer.
- **theme** — light / dark / high-contrast from ONE semantic layer: keep the semantic token *names*,
  remap their *values* per theme. [references/theming.md](references/theming.md) covers real dark
  mode (elevation via lighter surfaces, desaturation — not a naive invert), high-contrast, the CSS
  (data-theme, light-dark(), prefers-color-scheme), and **OKLCH** for perceptually-uniform tonal
  ramps and accessible lightness steps.
- **responsive** — fluid type/space scales with clamp(), modular ratios, container vs media
  queries, and **logical properties** (margin-inline, inset-inline-start) so layout mirrors for RTL
  automatically. See [references/responsive-rtl.md](references/responsive-rtl.md).
- **format** — the **W3C Design Tokens** JSON spec (value / type / aliasing / composite tokens) so
  one source compiles to CSS / iOS / Android via Style Dictionary. See
  [references/w3c-format.md](references/w3c-format.md).

## How you work

1. **Tokens before pixels.** Establish (or inherit) the token contract first; every visual value
   derives from it. A hardcoded hex in a component is a bug, not a shortcut.
2. **Theme at the semantic layer, never the primitive.** Primitives are fixed facts; semantics
   carry intent and are what a theme remaps. If you find yourself theming a primitive, add a
   semantic token instead.
3. **Name by role, not by value.** color-text-default survives a rebrand; color-charcoal-900 does
   not. The semantic name is the stable contract the rest of the system codes against.
4. **Pair theming with the a11y gate.** Every theme's semantic colour pairs must clear AA in that
   theme — lean on [[a11y-craft]]'s contrast-as-token so the ramp can't emit an inaccessible step.
5. **Keep the source portable.** Author in the W3C format so the same tokens feed Figma, the web
   build, and native — one source of truth, many outputs. You specify the system; the Developer
   wires the build pipeline.
6. **Consolidate a raw hex onto the *nearest existing* token, not a new one.** When you replace a
   hardcoded colour, first map it to the closest semantic token already in the system and confirm
   the swap doesn't shift the rendered value (compare in OKLCH — an imperceptible delta is fine, a
   visible one is a mismatch). Mint a new token only when nothing existing is close; a near-duplicate
   token is drift you just authored.

## Modern CSS: you own the fallback

`color-mix()` and CSS nesting are the sharp edges of a token layer, and there is **no lint** that
catches a missing fallback — so it is the token author's job, not a scan you defer to a tool.

- **Every token whose *value* uses `color-mix()` needs an `@supports` fallback.** A token defined as
  `color-mix(in oklch, var(--color-action) 12%, transparent)` resolves to *nothing* in a browser
  that lacks `color-mix()` — the property is dropped, and with it the hover tint, the badge
  background, or the gradient stop that consumed it. Define a real static fallback value first, then
  override it inside `@supports (color: color-mix(in oklch, red, blue))`. The fallback must be a
  believable approximation of the mix (a pre-computed flat colour), never omitted.
- **The three silent-drop hotspots** to give a fallback: **hover / active state tints**, **badge and
  pill backgrounds**, and **gradient stops** — these are where a dropped `color-mix()` reads as an
  invisible element, not a graceful degrade.
- **Nesting needs the same guard when the build doesn't flatten it.** If nested selectors ship raw
  (no PostCSS/Lightning flatten step), gate them or provide a flat equivalent so the styles they
  carry don't vanish on older engines. When the build *does* flatten, nesting is safe — confirm which
  you're in before relying on it.

This is authoring discipline at the token layer, in the same spirit as rule 4's contrast gate: the
token is only correct if it renders its intended value in every browser you support. It is **not** a
codebase drift scan — that remains [[design-unity]]'s job.

## Versioning

Own skill. Bump metadata.version on any change (PATCH: wording/refs · MINOR: new mode/coverage ·
MAJOR: method-contract change). Regenerate VERSIONS.md with
python3 star-alliance-skills/skillsmith/scripts/skill_registry.py write, then python3 build.py.

## Changelog
- **1.1.0** — Added two token-authoring disciplines. `How you work` rule 6: consolidate a raw hex
  onto the nearest *existing* semantic token and verify the swap doesn't shift the rendered value
  (OKLCH compare), minting new only when nothing fits. New section `Modern CSS: you own the fallback`:
  every `color-mix()`-valued token needs an `@supports` fallback (no lint exists for it) so
  unsupported browsers don't silently drop hover tints, badge backgrounds, and gradient stops; same
  guard for un-flattened nesting. Framed as construction craft, explicitly not the drift audit that
  belongs to design-unity.
- **1.0.0** — Initial release. Token architecture as a designer craft. Four modes — architect
  (primitive/semantic/component layering), theme (multi-theme from one semantic layer + OKLCH),
  responsive (fluid scales + logical properties for RTL), format (W3C Design Tokens spec for
  cross-platform portability). Authored in the 2026-06-27 the-designer deep-audit follow-up.