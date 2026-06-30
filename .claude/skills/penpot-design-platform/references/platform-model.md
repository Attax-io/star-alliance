---
type: Document
title: Penpot platform model — shapes, boards, layouts, components, tokens
---

# The Penpot design model

Penpot is the open-source design + prototyping platform (a self-hostable Figma
alternative) built on **open standards** — SVG, CSS, HTML, JSON. "Design is
expressed as code," which is why an agent and a developer can both read it. This
file is the mental model an agent needs before driving the file via the MCP's
`execute_code` / Plugin API.

## Hierarchy

A design is ultimately a tree of **shapes**.

- A project has one or more **`Page`** objects; a page's root is `page.root`.
- A **`Board`** is the high-level grouping element (the Penpot equivalent of a
  frame/artboard). A **`Group`** is the lower-level logical grouping.
- Low-level shapes: `Rectangle`, `Path`, `Text`, `Ellipse`, `Image`, `Boolean`,
  `SvgRaw`. `ShapeBase` is the common base; `Shape` is the union of containers +
  low-level shapes.
- `penpot.root` is the **current** page only — to work across pages, resolve the
  page first (`penpotUtils.getPageByName / getPages`).

## Shape properties (the gotchas that bite generated code)

- `x`/`y` are the top-left in **absolute (page)** coords and are **writable**.
  `parentX`/`parentY`/`boardX`/`boardY` are **read-only** — to position relative
  to a parent use `penpotUtils.setParentXY(shape, px, py)`.
- `width`/`height`/`bounds` are **read-only** — change size with `resize(w, h)`.
- `fills`/`strokes`/`shadows` are arrays whose **contents are read-only**: replace
  the whole array, never mutate an element. No fill = `shape.fills = []`. Colors
  are caps hex (`#FF5533`).
- **Z-order = order in the parent's `children` array.** Add background shapes
  first. Adjust later with `bringToFront/sendToBack/bringForward/sendBackward` or
  `setParentIndex(i)`.
- Reparent with `newParent.appendChild(shape)` / `insertChild(i, shape)` (absolute
  position preserved). `remove()` is **deletion**, not reparenting. `clone()`
  duplicates.

## Layout systems (responsive, code-like)

Boards can carry a layout that controls children automatically — **always check
for one before setting child x/y**, because the layout overrides manual positions.

- **Flex** — `board.addFlexLayout()` (or `penpotUtils.addFlexLayout(board, dir)`
  when the board already has children, to preserve visual order). Props: `dir`,
  `rowGap`, `columnGap`, `alignItems`, `justifyContent`, padding. Adjust spacing
  via gaps/margins, not child coordinates.
- **Grid** — `board.addGridLayout()`; CSS-grid style with `rows`, `columns`,
  `rowGap`, `columnGap`; children placed by 1-based `appendChild(shape, row, col)`.
- Both have `verticalSizing`/`horizontalSizing`: `fix` | `auto` | `fill`. Set
  `auto` when the container should grow to its content.

This is the same Flex/Grid that makes Penpot designs "behave like real code from
the start" — lean on it instead of absolute positioning.

## Text

`Text.characters` is the rendered string. Change size via `fontSize` (NOT
`resize`, which only changes the box and forces `growType:"fixed"` — set it back
to `auto-width`/`auto-height` for auto-sizing). Style sub-ranges via
`getRange(start, end)`. Discover fonts in `penpot.fonts`; apply with
`font.applyToText(text, variant)`.

## Components, variants, and asset libraries

Penpot's design-systems layer — one source of truth shared across files.

- `penpot.library.local` is the file's own library; `penpot.library.connected`
  the connected externals; `availableLibraries()` / `connectLibrary(id)` to wire
  more. Each `Library` holds `components`, `colors`, `typographies`.
- Instantiate a component: `component.instance()` (returns a Shape, often a Board).
  `instance.component()` / `component.mainInstance()` to navigate back. Use
  `detach()` to break the link for independent edits.
- Create a component from shapes: `penpot.library.local.createComponent(shapes)`.
- **Variants** group related component versions along named property axes (Size,
  State…), powering the swap UI. Prefer the one-call helper
  `penpotUtils.createVariantContainer([{shape, properties}, ...])` over the
  lower-level `createVariantFromComponents` ordering dance.

## Design tokens (the native single source of truth)

Penpot has **best-in-class native Design Tokens** — reusable values that bridge
design and code. Catalog: `penpot.library.local.tokens` (type `TokenCatalog`).

- `sets: TokenSet[]` (order = precedence), `themes: TokenTheme[]` (presets that
  activate sets). Create with `addSet({name})` / `addTheme({group, name})`. Only
  **active** sets affect shapes (`set.toggleActive()`).
- `set.addToken({type, name, value})`. `TokenType` ∈ color | dimension | spacing |
  typography | shadow | opacity | borderRadius | borderWidth | fontWeights |
  fontSizes | fontFamilies | letterSpacing | textDecoration | textCase. Values can
  reference other tokens: `"{color.primary}"`; `token.resolvedValue` follows refs.
- Discover: `penpotUtils.tokenOverview()`, `findTokenByName`, `findTokensByName`.
- Apply: `shape.applyToken(token, properties)` or `token.applyToShapes(shapes,
  props)` — application is async (~100ms). Setting a property directly removes its
  token binding.

This token catalog is the natural thing to **export** when a request says "pull
the tokens from Penpot" — and it maps cleanly onto the guild's `design-tokens`
craft for downstream code use.

## Design ↔ code directions Penpot advertises

- **Inspect mode** gives ready-to-use SVG / CSS / HTML for any element.
- The MCP enables **design-to-design, code-to-design, and design-to-code**
  multi-directional workflows. The API equivalents are `penpot.generateStyle`
  (CSS) and `penpot.generateMarkup` (HTML/SVG).
- Webhooks + an access-token REST API exist for toolchain integration beyond the
  plugin/MCP surface.

## Authoring discipline (from Penpot's own instructions)

- When translating a design to code, **adhere strictly** — never invent missing
  values; fall back to non-creative defaults (white/black) when info is missing.
- When creating, apply flex/grid where appropriate and use **semantic naming**;
  don't add text layers that merely repeat a shape's name.
- Before a change, ask "would a designer consider this appropriate?" For
  containment issues, check whether the parent is too small or the child too large
  before resizing — container sizes are usually intentional.
