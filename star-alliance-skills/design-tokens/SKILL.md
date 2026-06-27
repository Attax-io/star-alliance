---
name: design-tokens
description: "The Designer's token-architecture craft — structure a design-token system that scales, themes, and ports across platforms. Modes: architect (three-tier layering — primitive tokens for raw palette/type/space, semantic tokens named by role, component-scoped tokens; components consume only semantic tokens, theming happens at the semantic layer); theme (light, dark, high-contrast from ONE semantic layer by remapping values; OKLCH for perceptually-uniform tonal ramps and accessible lightness); responsive (fluid type/space scales with clamp(), container queries, logical properties for RTL-safe layout); format (the W3C Design Tokens JSON spec so one source compiles to CSS/iOS/Android). Use to design a token system, set up theming, structure tokens, or build dark mode. Triggers: 'design tokens', 'token architecture', 'set up theming', 'dark mode tokens', 'semantic tokens', 'OKLCH palette', 'W3C design tokens'. Differentiate from design-unity (audits drift) and a11y-craft (the accessibility gate)."
metadata:
  version: 1.0.0
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

## Versioning

Own skill. Bump metadata.version on any change (PATCH: wording/refs · MINOR: new mode/coverage ·
MAJOR: method-contract change). Regenerate VERSIONS.md with
python3 star-alliance-skills/skillsmith/scripts/skill_registry.py write, then python3 build.py.

## Changelog
- **1.0.0** — Initial release. Token architecture as a designer craft. Four modes — architect
  (primitive/semantic/component layering), theme (multi-theme from one semantic layer + OKLCH),
  responsive (fluid scales + logical properties for RTL), format (W3C Design Tokens spec for
  cross-platform portability). Authored in the 2026-06-27 the-designer deep-audit follow-up.
