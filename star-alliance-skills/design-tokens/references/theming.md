# Theming — light, dark, high-contrast from one semantic layer

One semantic token set, many value sets. The seam is at Layer 2; primitives and components are theme-agnostic.

## How multi-theme works

**Rule:** Define **one** set of semantic token NAMES. Provide **N** sets of VALUES, one per theme. Primitives stay fixed.

**Why:** The semantic name is the API; the value is the implementation. Components reference names, never values, so themes are free.

**Example (Style Dictionary build pattern):**
```json
{
  "color": {
    "bg": { "surface": { "$value": "{color.neutral.50}" } }
  }
}
```
With `themes: [light, dark, hc]` producing:
- `tokens.color.bg.surface` → `light: #fafafa`, `dark: #0e0e0e`, `hc: #ffffff`

## Dark mode — not inversion

**Rule:** Dark mode is a **redesign of the tonal map**, not `invert()`. Lift elevation with *brighter* surfaces (more L in OKLCH), not darker. Dim large color areas; reserve high chroma for small accents and focus rings.

**Why:** A naive invert of a light theme inverts contrast *direction* — what was `bg=high L, text=low L` becomes `bg=low L, text=high L` which looks correct, but mid-tones, elevation cues, and saturated brand colors all break. The eye reads luminance differences as elevation; flipping the polarity inverts the depth illusion.

**Example — elevation via surface luminance:**
```
Light theme:
  canvas  L=0.98
  surface L=0.96   (one step lower than canvas)
  raised  L=0.93   (modals, popovers)

Dark theme:
  canvas  L=0.12
  surface L=0.16   (LIGHTER than canvas — elevated in dark)
  raised  L=0.22   (LIGHTER still — modal floats up)
```

**Why:** In dark mode, "elevation = lighter surface" is the convention (Material 3, Apple HIG, Fluent). Matches the real-world analogy of light falling on a stack of papers in a dark room.

## Desaturate large areas, saturate small

**Rule:** In dark themes, drop chroma on large surfaces (backgrounds, fills) by ~30–50%; keep or boost chroma on small interactive elements (focus rings, links, primary buttons).

**Why:** Saturated colors on dark backgrounds vibrate and fatigue the eye. A `blue-500` designed against a light background is too vivid against black.

**Example:**
```
Light primary:  oklch(0.62 0.18 255)   chroma 0.18
Dark  primary:  oklch(0.70 0.16 255)   chroma 0.16, L raised for contrast
Dark  focus:    oklch(0.78 0.22 255)   chroma 0.22, small target
```

## High-contrast theme

**Rule:** HC theme targets **WCAG AAA** (7:1 for text, 4.5:1 for large text + non-text UI) and uses the OS high-contrast palette where possible (`Canvas`, `CanvasText`, `Highlight`, `HighlightText` system colors in CSS).

**Why:** Low-vision users need boundaries, not just contrast. Borders that vanish in default mode must become explicit 1–2px outlines in HC.

**Example:**
```css
[data-theme="hc"] {
  --color-bg-surface: Canvas;          /* system color */
  --color-text-default: CanvasText;    /* system color */
  --color-border-default: LinkText;    /* explicit, never gray */
}
```

## CSS implementation

**Rule:** Apply themes via a `[data-theme]` attribute on `<html>` or `<body>`. Default to `light-dark()` for binary light/dark, fall back to `prefers-color-scheme` only when user choice is not offered.

**Why:** `data-theme` is overridable per-element (e.g. a section that stays light inside a dark app). `prefers-color-scheme` is OS-only and cannot be set by your app.

**Example — `light-dark()` (CSS Color Module Level 5):**
```css
:root {
  color-scheme: light dark;
  --color-bg-surface: light-dark(#fafafa, #0e0e0e);
  --color-text-default: light-dark(#1a1a1a, #ededed);
}
```
The browser picks the value based on the `color-scheme` of the element. Combine with `@media (prefers-color-scheme: dark)` as the default branch.

**Example — multi-theme via custom property cascade:**
```css
:root,
[data-theme="light"] {
  --color-bg-surface: #fafafa;
  --color-text-default: #1a1a1a;
}
[data-theme="dark"] {
  --color-bg-surface: #0e0e0e;
  --color-text-default: #ededed;
}
[data-theme="hc"] {
  --color-bg-surface: #ffffff;
  --color-text-default: #000000;
  --color-border-default: #000000; /* 2px explicit */
}
```

**Rule:** Set `color-scheme` on `:root` to control native form controls and scrollbars, independent of your tokens.

**Why:** `<input>`, scrollbar, and `<select>` adopt the OS chrome for the declared scheme. Mismatched chrome against a dark theme is a visible regression.

## Why OKLCH, not HSL/hex

**Rule:** Build tonal ramps in **OKLCH** (CSS Color Module Level 4). Use HSL only for legacy output if a target platform requires it.

**Why:** OKLCH is **perceptually uniform** — equal L deltas look like equal lightness deltas to the eye. HSL is not: in HSL, `hsl(50 100% 50%)` (yellow) and `hsl(240 100% 50%)` (blue) at the same L look like very different brightnesses. Hex has no perceptual axis at all.

**Consequence:** A 9-step ramp at L = 0.10, 0.20, … 0.90 in OKLCH looks like evenly graded steps. The same ramp in HSL looks like it has gaps and jumps.

**Why:** Accessibility work needs predictable lightness steps. WCAG contrast ratios are computed on relative luminance (Y), which correlates with OKLCH's L far better than with HSL's L. Pick lightness in OKLCH, get contrast roughly right; pick it in HSL, get surprises.

## Building a palette in OKLCH

**Rule:** Fix hue `H` and chroma `C` per ramp. Vary only `L` (lightness) for the ramp. Adjust `C` separately if needed for the lightest/darkest stop to stay in gamut.

**Why:** Holding H+C constant produces a *coherent* ramp — all steps look like the same color. Drifting H between steps is the most common ramp-design mistake.

**Example — neutral ramp:**
```
oklch(0.98 0.005 hue)   /* 50, almost white */
oklch(0.95 0.005 hue)   /* 100 */
oklch(0.90 0.005 hue)   /* 200 */
oklch(0.80 0.005 hue)   /* 300 */
oklch(0.70 0.005 hue)   /* 400 */
oklch(0.60 0.005 hue)   /* 500 */
oklch(0.50 0.005 hue)   /* 600 */
oklch(0.40 0.005 hue)   /* 700 */
oklch(0.30 0.005 hue)   /* 800 */
oklch(0.20 0.005 hue)   /* 900 */
```
Hue is irrelevant for neutrals; chroma is tiny (`~0.005`) so they stay gray but not flat.

**Example — brand ramp with chroma curve:**
```
oklch(0.95 0.04  hue)  /* lightest — low chroma, in-gamut */
oklch(0.80 0.12  hue)
oklch(0.65 0.18  hue)  /* peak chroma around L=0.6–0.7 */
oklch(0.50 0.15  hue)
oklch(0.35 0.10  hue)  /* darker stops lose chroma */
oklch(0.20 0.06  hue)
```
**Why chroma curves:** Perceptual color research (Munsell, CIECAM02) shows perceived chroma is not constant at constant C — it peaks at mid L. A flat `C=0.18` across all L would look oversaturated in mid-tones and washed out at extremes. A bell curve matches perception.

## Gamut — sRGB, P3, Rec.2020

**Rule:** Write tokens in **oklch()** (not sRGB-bound `oklab()`) and let the browser gamut-map. Specify `color(display-p3 …)` only when you have evidence the target is a wide-gamut display and the asset pipeline preserves it.

**Why:** `oklch()` values are device-independent. If you write `oklch(0.7 0.3 30)` on an sRGB display, the browser clamps chroma to in-gamut. The same value on a P3 display renders more vivid. One source, faithful on both.

**Why not always P3:** P3 hex / `display-p3()` values are **out of gamut** on most shipped sRGB monitors — colors get clipped, sometimes visibly. sRGB is the safe floor.

**Example — gamut check:**
```css
--brand-500: oklch(0.65 0.22 255);  /* in-gamut on sRGB and P3 */
--brand-accent: oklch(0.70 0.32 30); /* may clip on sRGB; vivid on P3 */
```

## Theme switching without flash (FOUT)

**Rule:** Set theme **before paint** — inline a tiny script in `<head>` that reads `localStorage` and applies `data-theme` to `<html>` synchronously.

**Why:** A theme set in CSS after first paint causes a visible flash from default to chosen theme. Inline pre-paint is the only path without flash.

**Example:**
```html
<script>
  (function () {
    var t = localStorage.getItem('theme') ||
      (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
    document.documentElement.setAttribute('data-theme', t);
  })();
</script>
```
