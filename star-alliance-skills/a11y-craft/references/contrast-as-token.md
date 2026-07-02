---
type: Document
timestamp: 2026-07-02T12:28:13Z
---

# Contrast-as-token — make AA structurally un-violatable

Goal: bind an on-color to every surface token at build time so a designer can ship `--surface-purple-500` and an accessible foreground is auto-emitted with it. No human can produce an inaccessible pairing because the pairing is not a decision.

## WCAG 2 relative luminance

**Rule.** Convert each sRGB channel (0–255 → 0–1) to linear, then combine with the ITU-R BT.709 coefficients.

**Why.** sRGB values are gamma-encoded; perceived brightness is not linear in channel value. AA contrast is defined against *luminance*, not channel value, so all ratio math must run on the linearized form.

**How to check.**

```
For each channel value `c` in [0, 1]:
  if c <= 0.04045:  c_lin = c / 12.92
  else:             c_lin = ((c + 0.055) / 1.055) ** 2.4

L = 0.2126 * R_lin + 0.7152 * G_lin + 0.0722 * B_lin
```

G is weighted 3.36× more than B; R 2.96× more than B. Green-dominant colors read lighter than blue-dominant at the same channel value.

## Contrast ratio

**Rule.** `(L1 + 0.05) / (L2 + 0.05)`, where L1 is the lighter of the two. Round only for display; never round before ratio computation. Pass thresholds: 4.5 normal text, 3.0 large text / UI / non-text.

**Why.** The 0.05 offset models ambient screen flare and prevents the ratio from going infinite on identical colors.

**How to check.**

```
ratio = (max(L1, L2) + 0.05) / (min(L1, L2) + 0.05)
pass  = ratio >= 4.5  # normal text
```

## Black-vs-white on-color picker

**Rule.** Given a surface luminance `Ls`, compute `ratio(white, Ls)` and `ratio(black, Ls)`. Pick whichever yields the *higher* ratio *as long as it meets the target*. If both pass, prefer the higher ratio. If neither passes 4.5:1, the surface is unusable as a normal-text background — darken or lighten the surface, do not paper over with a colored on-token.

**Why.** Black-on-yellow is the maximum-contrast pair in practice. The picker is a deterministic fallback: any surface, any theme, one answer.

**How to check.** Implement in the token build step. The function takes a surface color and a target ratio (4.5 or 3) and returns a hex. Verify with a contrast grid for 16+ swatches spanning the palette.

## Tonal palette with on-color

**Rule.** A tonal scale (e.g., 50/100/200/…/900) is generated as a single hue with systematic lightness steps. Each step has a pre-computed `--on-{step}` token bound at generation. Designers pick a step + use its `on` token — they cannot pick a foreground independently.

**Why.** A scale where the designer also picks the foreground is a scale that will produce failures. Coupling eliminates the choice.

**How to check.** Token build script reads a single source-of-truth (e.g., `colors.json` with `scale: "blue"`, `min_l: 0.95`, `max_l: 0.10`, `steps: 11`) and emits `surface`, `on-surface`, `border`, `on-border` for each step. Fail the build if any on-surface pair < 4.5:1.

## APCA (WCAG 3 draft) — perceptual alternative

**Rule.** APCA (`Lc` value) is a perceptual contrast method in the WCAG 3 working draft, intended to replace the A/AA ratio. It models perceived lightness difference and uses use-case-dependent thresholds rather than a single 4.5:1. Approximate draft thresholds for body text: `Lc ≥ 75` (use `75` for body, `60` for content text, `45` for large/headline, `30` for non-text/UI).

**Why.** AA ratios over-approve low-lightness-on-low-lightness pairs that read poorly, and under-approve yellow-on-white that reads well. APCA tracks perception more linearly.

**How to check.** Use APCA-W3 (the `apca-w3` npm package) for token validation in parallel with WCAG 2 ratios. APCA is *not* AA-conformant — treat it as a future-looking sanity check, not a replacement for 4.5:1 today. Adopting APCA as the gating metric today creates audit risk until WCAG 3 is a published recommendation.

## Doing it in CSS

**Rule.** Three CSS features make on-tokens automatic:
1. `color-contrast()` (CSS Color 5) — `color: color-contrast(var(--surface) vs black, white to 4.5)`. The browser picks the better pair against a target ratio. Browser support is partial (Safari 15+, Chrome 111+ behind flag, Firefox 112+); use as a progressive enhancement.
2. Relative color syntax (CSS Color 5) — derive an on-color from a base: `color: rgb(from var(--surface) calc(255 - r) calc(255 - g) calc(255 - b))`. Stable in all modern engines.
3. `light-dark()` (CSS Color 5) — bind a property to both schemes: `color: light-dark(#1a1a1a, #f5f5f5)`. The browser picks by `color-scheme`. Use to ship one rule per token that adapts to the theme.

**Why.** Static token files cannot react to runtime conditions; CSS functions can. The build emits the surface; CSS handles the on-color.

**How to check.** Use `color-contrast()` where supported; fall back to the build-step on-color elsewhere via `@supports`. Use `light-dark()` to avoid duplicating rules for each theme.

## Doing it in the token build step

**Rule.** A build step (Style Dictionary, Theo, Theemo, or a custom script) ingests raw color values, runs the luminance pipeline, and emits a JSON/Style Dictionary output where each surface has a paired on-color. The build fails on a ratio < 4.5:1 (or 3.0 for non-text).

**Why.** Designers do not have to think about foreground. The system fails closed. A new theme ships as one file: raw swatches. The output is the full token set, vetted.

**How to check.** Add a unit test: feed the build step 20 surfaces across the spectrum; assert all on-colors meet 4.5:1 against their surface. Wire the test into CI.

## Pitfalls

**Rule.**

- **Large-text exception (1.4.3):** ≥ 18pt regular or ≥ 14pt bold gets the 3:1 threshold, not 4.5:1. If a step is meant for headline/display only, set its on-color to pass 3:1, not 4.5:1. Otherwise, do not exploit the exception to ship low-contrast body text.
- **Disabled-state exemption:** WCAG 2 explicitly exempts inactive UI components. But "disabled-looking" is not the same as "disabled" — the `disabled` attribute or `aria-disabled="true"` must be set, otherwise the component is active and must meet contrast.
- **Brand-color overrides:** marketing/brand teams will request a primary that fails contrast. The system must surface the failure (ratio + alternatives) rather than silently accept. Provide 2–3 brand variants pre-computed: a dark theme, a light theme, and an on-tinted-brand variant — all meeting AA.
- **Gradient backgrounds and images:** compute contrast against the *worst* local background color, not the average. Treat the component as failing if any pixel-area large enough to read text fails the ratio.
- **Focus rings and shadows:** not "decoration" — these are UI components under 1.4.11, need 3:1 against the surface they sit on.
