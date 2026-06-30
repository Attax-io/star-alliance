---
type: Document
title: Penpot plugin API — writing a plugin vs. driving the MCP
---

# The Penpot plugin system

The plugin system makes the Penpot workspace **programmable**: a plugin is a small
web app, loaded into an open Penpot file, that drives the same **Plugin API** the
MCP server uses under the hood. Reach for a **plugin** when the user wants a
reusable, shippable tool living in Penpot's Plugins menu; reach for the **MCP**
(see `mcp-surface.md`) when an agent should drive a file conversationally,
one task at a time. They are two front-ends to the same API.

## Anatomy of a plugin

A plugin is two parts:

1. **Plugin code** — JS that runs in the Penpot plugin sandbox and talks to the
   `penpot` API (create/read/modify shapes, libraries, tokens). It can open a UI
   with `penpot.ui.open(...)` and exchange messages with that UI.
2. **UI** (optional) — an HTML/JS page (iframe) for user interaction; it
   `postMessage`s to the plugin code, which holds the API access.

### The manifest (`manifest.json`)

The contract Penpot loads. Real shape (from the sample plugins):

```json
{
  "name": "Example Plugin",
  "host": "http://localhost:4201",
  "code": "/plugin.js",
  "icon": "/icon.png",
  "permissions": [
    "content:write",
    "library:write",
    "user:read",
    "comment:read",
    "allow:downloads"
  ]
}
```

- `code` is the entry script; `host` is where it's served.
- **`permissions`** gate what the plugin may do — request the least it needs:
  `content:read` / `content:write` (the design), `library:read` / `library:write`
  (assets/tokens), `user:read`, `comment:read` / `comment:write`,
  `allow:downloads`.

### Loading a plugin

In Penpot: open a file → **Plugins** menu → load via the plugin's manifest URL
(dev default `http://localhost:4400/manifest.json`, sample plugins
`http://localhost:4202/assets/manifest.json`). For plugins outside the monorepo,
Penpot publishes a **Plugin Starter Template** and create-a-plugin docs.

## The runtime hooks

The plugins runtime sets listeners so a plugin reacts to context changes — when
the active **page**, **file**, or **selection** changes. The same `penpot` object
documented in `platform-model.md` is the full API: `penpot.selection`,
`penpot.root`/`currentPage`, `penpot.library`, `penpot.fonts`,
`penpot.generateStyle`, `penpot.generateMarkup`, plus the `penpotUtils` helpers.

## Sample plugins worth mirroring

These ship in the repo as patterns to copy:

| Plugin | What it demonstrates |
| --- | --- |
| contrast-plugin | reading shapes + color contrast (a11y) info |
| icons-plugin | inserting assets (Feather icons) into the design |
| create-palette-plugin | generating a board of palette colors |
| colors-to-tokens-plugin | exporting a **tokens JSON** file from colors |
| poc-tokens-plugin | exercising the tokens API |
| rename-layers-plugin | bulk layer operations |
| table-plugin | creating/importing structured content |
| lorem-ipsum-plugin | generating placeholder text |

`colors-to-tokens-plugin` is the canonical reference for "export Penpot tokens";
`contrast-plugin` for reading design state for an audit.

## Beyond plugins: the open API

Penpot also exposes a REST API reachable via **access tokens** and **webhooks**,
for integrating Penpot into a development toolchain without a UI plugin. The MCP
server's `import_penpot_file` (devenv) and the SaaS endpoints build on this same
open surface.

## Plugin vs MCP — when to pick which

- **Plugin** — a durable, user-facing tool that should live in the Plugins menu,
  ship to a team, and run on demand (palette generator, token exporter, linter).
- **MCP** — an agent performing a *specific* design task in a conversation now
  (inspect this file, build this layout, pull these components/tokens, translate
  this design to code). No packaging; the model writes `execute_code` directly.
- Both terminate at the **same Plugin API**, so the design-model rules in
  `platform-model.md` apply identically to each.
