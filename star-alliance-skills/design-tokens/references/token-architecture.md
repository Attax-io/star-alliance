# Token architecture — primitive, semantic, component

A three-tier model where each layer has exactly one job, references flow downward, and the layer you reference is decided by *who consumes the token*, not by taste.

## Layer 1 — Primitive tokens (global, value-bearing)

**Definition:** Raw values named for **what they are**, not what they do. Also called "global", "base", or "reference" tokens.

**Rule:** Primitives are the only layer that may hold raw hex, oklch(), px, ms, or bezier values. Every other layer references them by `{group.token}`.

**Why:** A single source of truth for raw values lets you rebalance the entire system by editing primitives. Without primitives, dark mode and rebrands become search-and-replace.

**Example:**
```json
{
  "color": {
    "blue": { "500": { "$value": "oklch(0.62 0.18 255)" } },
    "neutral": { "900": { "$value": "oklch(0.18 0.01 255)" } }
  },
  "space": { "4": { "$value": "1rem" }, "8": { "$value": "2rem" } },
  "radius": { "sm": { "$value": "0.25rem" } }
}
```

## Layer 2 — Semantic tokens (alias, role-bearing)

**Definition:** Tokens named for **role/intent** that alias primitives. The theming seam lives here.

**Rule:** Semantic token names describe purpose — `color-bg-surface`, `color-text-default`, `color-action-primary`, `space-inset-md`, `radius-control`. Never name them by value (`color-blue-500` is not semantic).

**Why:** This layer is what gets remapped per theme. One semantic name, many primitive values. Components stay theme-agnostic.

**Example:**
```json
{
  "color": {
    "bg": {
      "surface":   { "$value": "{color.neutral.50}"  },
      "default":   { "$value": "{color.neutral.100}" }
    },
    "text": {
      "default":   { "$value": "{color.neutral.900}" }
    },
    "action": {
      "primary":   { "$value": "{color.blue.500}"   }
    }
  }
}
```

## Layer 3 — Component tokens (scoped, optional)

**Definition:** Tokens scoped to a single component or pattern. Aliases to semantic tokens.

**Rule:** Only create a component token when a specific component needs a value that diverges from the system default, or when the same semantic token is used inconsistently across components and you want to lock in intent per component.

**Why:** Lets you tweak one component without re-skinning the system. Without this layer, ad-hoc overrides leak into component CSS.

**Example:**
```json
{
  "button": {
    "bg":        { "$value": "{color.action.primary}" },
    "bg-hover":  { "$value": "{color.action.primary-hover}" },
    "padding-x": { "$value": "{space.4}" },
    "radius":    { "$value": "{radius.sm}" }
  }
}
```

## Consumption rules

**Rule:** Components consume **semantic or component tokens only**. Never reference a primitive directly from a component.

**Why:** A component that uses `{color.blue.500}` directly is locked to that primitive forever; switching to semantic `{color.action.primary}` makes it theme-portable for free.

**Rule:** Add a new tier level only when a real consumer needs it. Do not pre-build a fourth tier ("application tokens") unless you have evidence.

**Why:** Empty tiers are maintenance debt. Most systems stop at three.

## Naming convention — `category-concept-property[-state]`

**Rule:** `<group>.<role>.<property>[.<state>]`, all kebab-case.

**Why:** Predictable names compose, search, and lint. Designers and engineers guess the name without reading docs.

**Example:**
- `color.bg.surface`
- `color.text.muted`
- `color.action.primary.hover`
- `color.action.primary.disabled`
- `space.inset.md`
- `space.stack.lg`
- `radius.control`
- `font.body.default`

## When to split vs merge tokens

**Rule:** Split a token when its value diverges across themes, brands, or components. Merge when two roles always share a value — splitting them invites accidental drift.

**Why:** Token count grows non-linearly with carelessness. A token per role is correct; a token per pixel is not.

**Example:** `color.action.primary` and `color.action.danger` are two roles; keep separate. `color.bg.surface` and `color.bg.canvas` only split if you actually need them to differ in dark mode.

## Required JSON fields per tier

| Field | Primitive | Semantic | Component |
|---|---|---|---|
| `$value` | literal | `{ref}` | `{ref}` |
| `$type` | required | required | required |
| `$description` | recommended | required | required |
| `$extensions` | optional | optional | optional |

**Why:** `$type` is what Style Dictionary and Tokens Studio use to transform values per platform. Missing `$type` = silent fallback to string.
