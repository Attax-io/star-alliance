# W3C Design Tokens format — portable, tool-agnostic source of truth

The W3C Design Tokens Community Group format is a JSON document model for declaring design tokens. It is the lingua franca between Figma, Tokens Studio, Style Dictionary, Specify, and any custom consumer.

## Why a standard format

**Rule:** Store the source of truth in **W3C Design Tokens format** (a JSON object), not in CSS variables, not in Figma variables export, not in a custom YAML.

**Why:** A standardized JSON format is **portable** (every tool reads it), **declarative** (no behavior baked in), **typed** (each token carries a `$type`), and **composable** (aliasing via references). When your tool changes, the source does not. When you switch a build pipeline, the source does not.

**Interop today:** Style Dictionary (Amazon open-source), Tokens Studio (Figma plugin), Specify, Supernova, and the official `@design-tokens/community-group` parser all consume the same JSON.

## Required structure

**Rule:** A token is an object with at minimum `$value`. A typed token has `$type`. A group is a plain object containing tokens or sub-groups.

**Why:** Groups give structure (`color`, `space`, `typography`). The `$` prefix distinguishes token fields from arbitrary user fields.

**Example — minimal valid tokens file:**
```json
{
  "color": {
    "primary": { "$value": "#2255ff" }
  }
}
```

## `$type` — the required type tag

**Rule:** Declare `$type` on every token. The type drives transforms in Style Dictionary, type-checking in editors, and platform-specific output (iOS `CGFloat`, Android `dp`, CSS `rem`).

**Why:** Without `$type`, a token's value is just a string. A `dimension` of `"1rem"` cannot be safely converted to `"16px"` or `"16dp"` without knowing it is a length.

**Valid types per the W3C spec:**
- `color`
- `dimension` (lengths — px, rem, em, %)
- `fontFamily`
- `fontWeight`
- `duration` (ms, s)
- `cubicBezier`
- `number`
- `string`
- `boolean`
- `shadow`
- `border`
- `typography` (composite)
- `transition` (composite)
- `gradient`
- `strokeStyle`

**Example:**
```json
{
  "space": {
    "4": { "$value": "1rem", "$type": "dimension" }
  },
  "duration": {
    "fast": { "$value": "150ms", "$type": "duration" }
  }
}
```

## `$description` — required for non-trivial tokens

**Rule:** Every semantic and component token MUST have a `$description` field. Primitives SHOULD.

**Why:** `$description` is shown in editor tooltips, exported to code comments, and read by LLMs / future contributors. "What is `color.action.danger.hover` for?" is unanswerable from the name alone.

**Example:**
```json
{
  "color": {
    "action": {
      "danger": {
        "hover": {
          "$value": "{color.red.600}",
          "$type": "color",
          "$description": "Background of destructive action button on hover. AA against white text."
        }
      }
    }
  }
}
```

## Aliasing — `{group.token}` references

**Rule:** Reference another token's value with the `{path.to.token}` syntax. References resolve at build time, not runtime.

**Why:** Aliases are what enables a three-tier architecture in JSON. Editing the primitive updates every semantic that points at it, transitively.

**Example:**
```json
{
  "color": {
    "blue": { "500": { "$value": "#2255ff", "$type": "color" } },
    "bg": {
      "surface": { "$value": "{color.blue.500}", "$type": "color" }
    }
  }
}
```

**Rule:** Aliases may chain (semantic → primitive, or component → semantic → primitive). Self-references and forward references are forbidden by the spec.

**Why:** Cycles break resolution. Forward refs break parsing.

## Composite types

**Rule:** Use composite `$type` (`typography`, `shadow`, `border`, `transition`, `gradient`) for tokens that are bundles of atomic values. Each leaf of the composite references atomic tokens.

**Why:** A `typography` token that bundles font-size, line-height, font-weight, font-family is one token in your system — easier to consume, easier to audit.

**Example — typography composite:**
```json
{
  "typography": {
    "body": {
      "$value": {
        "fontFamily": "{font.family.sans}",
        "fontWeight": "{font.weight.regular}",
        "fontSize": "{font.size.md}",
        "lineHeight": "{font.lineHeight.normal}",
        "letterSpacing": "{font.tracking.normal}"
      },
      "$type": "typography"
    }
  }
}
```

**Example — shadow composite:**
```json
{
  "shadow": {
    "raised": {
      "$value": {
        "color": "{color.shadow.default}",
        "offsetX": "0px",
        "offsetY": "2px",
        "blur": "8px",
        "spread": "0px"
      },
      "$type": "shadow"
    }
  }
}
```

## Groups — nested objects

**Rule:** Group tokens by **category first, concept second, property/state third**. Group names are not tokens; they have no `$value`.

**Why:** Consistent grouping makes the file navigable, lets tools generate menus, and enables prefix-based subsetting (export only `color.*`).

**Example structure:**
```
color
├── blue / red / neutral       (primitive ramps)
├── bg / text / border / icon  (semantic role groups)
└── action / status            (semantic role groups)
space
├── 0–24                        (primitive scale)
├── inset / stack / inline      (semantic roles)
radius
font
├── family / weight / size / lineHeight
duration
```

## `$extensions` — tool-specific metadata

**Rule:** Use `$extensions` for data that is not part of the W3C spec but is needed by your tools (Figma variable IDs, mode bindings, custom metadata).

**Why:** The spec is a baseline. Real pipelines need hooks. `$extensions` is the escape hatch that keeps vendor data out of `$value` and `$type`.

**Example:**
```json
{
  "color": {
    "brand": {
      "$value": "#2255ff",
      "$type": "color",
      "$extensions": {
        "figma.variableId": "VariableID:1:2"
      }
    }
  }
}
```

## Worked example — full file

```json
{
  "color": {
    "blue":   { "500": { "$value": "oklch(0.62 0.18 255)", "$type": "color" } },
    "red":    { "500": { "$value": "oklch(0.62 0.22 25)",  "$type": "color" } },
    "neutral": {
      "50":  { "$value": "oklch(0.98 0.005 255)", "$type": "color" },
      "900": { "$value": "oklch(0.18 0.01  255)", "$type": "color" }
    },
    "bg": {
      "surface": { "$value": "{color.neutral.50}", "$type": "color" },
      "raised":  { "$value": "{color.neutral.100}", "$type": "color" }
    },
    "text": {
      "default": { "$value": "{color.neutral.900}", "$type": "color" }
    },
    "action": {
      "primary": { "$value": "{color.blue.500}", "$type": "color" },
      "danger":  { "$value": "{color.red.500}",  "$type": "color" }
    }
  },
  "space": {
    "1": { "$value": "0.25rem", "$type": "dimension" },
    "2": { "$value": "0.5rem",  "$type": "dimension" },
    "4": { "$value": "1rem",    "$type": "dimension" }
  },
  "radius": {
    "sm": { "$value": "0.25rem", "$type": "dimension" }
  },
  "typography": {
    "body": {
      "$value": {
        "fontFamily": "system-ui",
        "fontWeight": 400,
        "fontSize":   "{space.4}",
        "lineHeight": 1.5
      },
      "$type": "typography"
    }
  }
}
```

## Build pipeline — Style Dictionary

**Rule:** Compile W3C-format JSON into platform-specific outputs via Style Dictionary (or equivalent). The JSON is the source; CSS / iOS / Android / Tailwind config are generated.

**Why:** A single source of truth compiled to many targets. The moment you hand-edit generated CSS, the source and the build drift.

**Example pipeline:**
```js
// build.js
import StyleDictionary from 'style-dictionary';

const sd = new StyleDictionary({
  source: ['tokens/**/*.json'],
  platforms: {
    css: {
      transformGroup: 'css',
      buildPath: 'dist/css/',
      files: [{ destination: 'tokens.css', format: 'css/variables' }]
    },
    ios: {
      transformGroup: 'ios-swift',
      buildPath: 'dist/ios/',
      files: [{ destination: 'Tokens.swift', format: 'ios-swift/class.swift' }]
    },
    android: {
      transformGroup: 'android',
      buildPath: 'dist/android/',
      files: [{ destination: 'tokens.xml', format: 'android/resources' }]
    }
  }
});

await sd.buildAllPlatforms();
```

**Why Style Dictionary is the default choice:** It is open-source, ships transforms for CSS / SCSS / Less / iOS Swift / iOS Objective-C / Android XML / Flutter / Compose / Tailwind / JS, supports per-theme builds (`themes: [light, dark]`), and is what the W3C spec examples target.

## Resolution rules to remember

**Rule:** Aliases are **static** — they resolve at build time. A CSS variable referencing another CSS variable at runtime is fine, but in the W3C JSON source, `{color.blue.500}` must resolve during the build.

**Rule:** `$type` is **inherited** from group context only if explicitly set by a tool. Safer: declare `$type` on every token.

**Why:** The W3C spec does not mandate type inheritance; tools vary. Explicit typing is portable.

**Rule:** Reference paths are dot-separated and case-sensitive. `{color.Action.Primary}` ≠ `{color.action.primary}`.

**Why:** A typo in a reference is a silent broken alias. Most tools fail the build, but JSON linters in editors will not.
