---
type: Document
timestamp: 2026-07-02T12:28:13Z
---

# Responsive + RTL tokens — fluid scales and logical properties

Tokens that compose across viewport sizes and writing directions without per-breakpoint overrides.

## Fluid scales with `clamp()`

**Rule:** Express fluid type and space tokens as `clamp(MIN, PREFERRED, MAX)`. MIN and MAX are the floor and ceiling. PREFERRED is `vw` (or `vi`, `svw`) with a `rem` floor.

**Why:** A single token interpolates continuously between MIN (smallest viewport) and MAX (largest). No `@media` blocks, no JS, no layout shift between breakpoints.

**Example — fluid body type:**
```css
--font-size-body: clamp(1rem, 0.875rem + 0.5vw, 1.125rem);
```
- At 320px viewport: 0.875 + 0.5*3.2 = 0.875 + 0.16 = 1.036rem → clamped to MIN `1rem`.
- At 1024px: 0.875 + 0.5*10.24 = 0.875 + 5.12 = ~6rem → clamped to MAX `1.125rem`.

**Why include a `rem` term in PREFERRED:** A pure `vw` value can become unreadable on tiny or huge viewports. The `rem` component keeps it within a sane range before the clamp kicks in.

## Modular scale ratios

**Rule:** Pick one base size and one ratio. Compute scale stops as `base * ratio^n`. Common ratios (real, from music theory / type tradition):

| Ratio | Value | Use |
|---|---|---|
| Minor second | 1.067 | Dense UI, data tables |
| Major second | 1.125 | Default body-dense |
| Minor third | 1.200 | Default body |
| Major third | 1.250 | Editorial, marketing |
| Perfect fourth | 1.333 | Headlines + body |
| Perfect fifth | 1.500 | Display, marketing |
| Golden ratio | 1.618 | Decorative only |

**Why:** A consistent ratio is a visual system. Eyeballed scales look random and break hierarchy.

**Example — minor third (1.2) from `1rem` base:**
```
font-size-xs:   0.694rem   (1 / 1.2^2)
font-size-sm:   0.833rem   (1 / 1.2)
font-size-md:   1.000rem   (base)
font-size-lg:   1.200rem
font-size-xl:   1.440rem
font-size-2xl:  1.728rem
font-size-3xl:  2.074rem
```

## Fluid vs stepped breakpoints

**Rule:** Use **fluid** tokens for type, space, radius. Use **stepped** `@media` only for layout: column count, sidebar visibility, navigation collapse.

**Why:** Type and space have continuous perceptual impact — fluid is the right tool. Layout is discrete — a 3-column grid does not interpolate; it switches. Hybrid is correct.

**When NOT to use fluid:** Icons, borders, and shadow blur (use stepped — small sizes round to zero otherwise).

## Container queries vs media queries

**Rule:** Use `@container` for **component-internal** responsiveness (a card reflowing inside a sidebar). Use `@media` for **page-level** layout (overall grid, navigation).

**Why:** A media query knows the viewport, not the component. A card in a 300px sidebar and a card on a 1400px page both see the same viewport but need different layouts. Container queries solve this.

**Example:**
```css
.card {
  container-type: inline-size;
  container-name: card;
}
@container card (min-width: 400px) {
  .card { grid-template-columns: 1fr 2fr; }
}
```

## Logical properties — the RTL rule

**Rule:** Use **logical properties** for every directional value. `margin-inline-start`, `padding-block-end`, `inset-inline-start`, `border-start-start-radius`, `text-align: start`. Reserve `left` / `right` / `top` / `bottom` for true physical cases (a fixed-position tooltip arrow, a map marker).

**Why:** Logical properties are written-direction-aware. A token using `margin-inline-start: 1rem` becomes `margin-right: 1rem` in LTR and `margin-left: 1rem` in RTL automatically. No `[dir="rtl"]` overrides, no duplicated CSS, no bugs where the LTR fix wasn't mirrored.

| Physical | Logical |
|---|---|
| `margin-left` | `margin-inline-start` |
| `margin-right` | `margin-inline-end` |
| `padding-top` | `padding-block-start` |
| `padding-bottom` | `padding-block-end` |
| `left` | `inset-inline-start` |
| `right` | `inset-inline-end` |
| `border-top-left-radius` | `border-start-start-radius` |
| `border-top-right-radius` | `border-start-end-radius` |
| `width` | `inline-size` |
| `height` | `block-size` |

## Logical tokens

**Rule:** Name spacing tokens by **logical role**, not physical side: `space-inset-inline-start`, `space-stack`, `space-inset-block`, `space-gutter-inline`. Never `space-left`.

**Why:** A physical token name in RTL is a lie. "Left padding 16px" in an RTL document is the right edge. Logical names compose with logical CSS properties and survive direction changes.

**Example:**
```json
{
  "space": {
    "inset": { "sm": { "$value": "0.5rem" } },
    "inset-inline": { "md": { "$value": "1rem" } },
    "stack": { "lg": { "$value": "2rem" } }
  }
}
```
```css
.card {
  padding-inline: var(--space-inset-inline-md);
  padding-block: var(--space-inset-sm);
  margin-block-end: var(--space-stack-lg);
}
```

## Text expansion headroom

**Rule:** Reserve **20–30% extra inline space** for translated text in components with fixed inline dimensions (buttons, nav items, table cells, badges). Use `min-inline-size` and `max-inline-size` instead of fixed `width`.

**Why:** English text grows on translation — German ~30% longer, French ~20%, Finnish up to 60% longer in UIs. A button sized to "Submit" hard-codes its content.

**Example:**
```css
.button {
  min-inline-size: 4rem;
  max-inline-size: 12rem; /* caps runaway in untranslated locales */
  white-space: normal;     /* allow wrap for long translations */
}
```

## Bidirectional text (bidi)

**Rule:** Wrap user-generated strings that may mix scripts in `<bdi>` (or set `unicode-bidi: isolate`). Never insert visual bidi controls in tokens.

**Why:** A username "David2024" embedded in an RTL paragraph renders LTR digits correctly inside an RTL run if isolated. Without `bdi`, digits and punctuation attach to the wrong base direction and break reading order.

**Example:**
```html
<p lang="ar">مرحبا <bdi>User_2024</bdi>، شكرا</p>
```

**Rule:** For mixed-direction component layout (RTL app with a numeric badge in a leading position), use logical properties — do not hardcode the badge side.

**Why:** `padding-inline-start` mirrors with the document, keeping the badge visually leading in both directions.

## Container query units (`cqw`, `cqh`, `cqi`, `cqb`)

**Rule:** Use container query units (`cqi`, `cqb`) for **component-scoped** fluid sizing. Reserve `vw`/`vh` for page-level sizing.

**Why:** `1cqi` = 1% of the containing block's inline size. A card sized by `cqi` responds to its parent, not the viewport — a card inside a narrow sidebar scales down, a card in a wide main column scales up. This is the missing link between fluid tokens and container queries.

**Example:**
```css
.card {
  container-type: inline-size;
  padding: clamp(0.5rem, 2cqi, 1.5rem);
  font-size: clamp(0.875rem, 3cqi + 0.5rem, 1.25rem);
}
```
