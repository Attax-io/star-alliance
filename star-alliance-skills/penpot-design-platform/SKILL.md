---
name: penpot-design-platform
metadata:
  version: 1.0.0
type: Skill
description: "Drive Penpot, the open-source design and prototyping platform (a self-hostable Figma alternative built on open SVG/CSS/HTML/JSON), for real design work. Covers the platform model (pages, boards, flex/grid layouts, components, variants, native design tokens, inspect-mode SVG/CSS/HTML), Penpot's own official MCP server and its real tools (high_level_overview, penpot_api_info, execute_code, export_shape, import_image) for agent-driven inspect/generate/modify, and the plugin API plus manifest/permissions for shippable plugins. Use when asked to open this in penpot, pull the components or tokens from penpot, use the penpot MCP, design this in penpot, export penpot tokens, or write a penpot plugin. Differs from design-tokens, design-language, image-to-code, imagegen-frontend (the guild's own token/brand/codegen crafts): this drives the Penpot platform and its MCP/plugin surface."
---

# Penpot Design Platform

The Designer's craft for **driving Penpot** — the open-source design and
prototyping platform teams use to build digital products at scale (a
self-hostable Figma alternative). Penpot is built on **open standards** — SVG,
CSS, HTML, JSON — so a design is, in effect, readable code. It ships two surfaces
an agent can drive: its **own official MCP server** and a **plugin system**. This
skill teaches *when and how* to reach for Penpot and how to operate those two
surfaces well. It is a tool-usage craft, not a re-implementation of Penpot.

## What it is / is not

**Is:**
- A guide to the **Penpot platform model**: pages, boards, flex/grid layouts,
  shapes, components, variants, native design tokens, inspect-mode SVG/CSS/HTML.
- A guide to **Penpot's own MCP server** (`@penpot/mcp`) and its *real* tools —
  what an agent can inspect, generate, and modify in a live file.
- A guide to the **plugin API + manifest/permissions** for building shippable
  Penpot plugins.

**Is not:**
- Not a clone of any guild design pipeline. **`design-tokens`** is the guild's own
  token modeling/codegen; **`design-language`** its brand/voice system;
  **`image-to-code`** turns a *picture* into markup; **`imagegen-frontend`**
  generates UI imagery. This skill instead **drives the Penpot platform** and its
  MCP/plugin surface. (Once tokens are pulled *out* of Penpot, hand them to
  `design-tokens` for downstream code use — the seam is clean.)
- Not a self-hosting/ops guide and not a re-spec of the Penpot API; for exact type
  members, the MCP's `penpot_api_info` tool is the source of truth.

## Principles

1. **Penpot is open code, not an opaque canvas — exploit that.** Designs are SVG/
   CSS/HTML/JSON; inspect-mode and `penpot.generateStyle` / `generateMarkup` give
   ready-to-use code for any element. Prefer reading the real structure over
   guessing; when translating design→code, **adhere strictly** and never invent
   missing values (fall back to white/black, not creativity).

2. **The MCP is the agent's hands; a design file must be open and the plugin
   connected.** Penpot's MCP server reaches the file only through the MCP **plugin**
   running in an open, active browser tab over WebSocket. No open file + connected
   plugin → no capability. Use a **capable, vision-capable** model: many tasks
   require visually inspecting an exported image.

3. **Inspect before you mutate; verify by looking.** Read `high_level_overview`
   once, overview the tree (`penpotUtils.shapeStructure`), stash the selection in
   `storage` immediately, look up unknown types with `penpot_api_info`, mutate in
   small `execute_code` steps, then **`export_shape` to actually see the result**.
   Never declare a design done you haven't viewed.

4. **Build with the platform's structure, not against it.** Use components +
   variants for a real design system, native **design tokens** as the single
   source of truth, and **flex/grid layouts** for responsive structure — boards
   with a layout override manual child x/y, so check for one first. Semantic
   naming over decorative layers.

5. **Plugin vs MCP — same API, different front-end.** Write a **plugin** when the
   user wants a durable, shippable tool in Penpot's Plugins menu (palette
   generator, token exporter, linter); request least-privilege `permissions` in
   the manifest. Drive the **MCP** when an agent should do a specific task in a
   conversation now. Both terminate at the same Plugin API, so the model rules
   apply identically.

6. **Reach for Penpot — not a guild pipeline — when the work lives *in* a Penpot
   file.** "Open/inspect/design this in Penpot", "pull the components/tokens from
   Penpot", "export Penpot tokens", "write a Penpot plugin" → this skill. Modeling
   our own tokens, brand language, or converting a flat image to code → the
   guild's own crafts.

## Quickstart (MCP)

```
npx -y @penpot/mcp@latest                       # run server (port 4401)
claude mcp add penpot -t http http://localhost:4401/mcp
```

Then in Penpot: open a file → Plugins menu → load the MCP plugin → "Connect to
MCP server" (keep the plugin UI open and the tab active). stdio-only clients
proxy via `npx -y mcp-remote http://localhost:4401/mcp --allow-http`.

## References

- **`references/mcp-surface.md`** — Penpot's MCP architecture, transport/connection
  facts, and every real tool (core: `high_level_overview`, `penpot_api_info`,
  `execute_code`, `export_shape`; file-mode: `import_image`; devenv-only Clojure/
  Taiga tools) + the inspect→mutate→verify loop.
- **`references/platform-model.md`** — the design model: pages/boards/shapes, the
  read-only-property gotchas, flex/grid layouts, text, components, variants, native
  design tokens, and the design↔code directions.
- **`references/plugin-api.md`** — plugin anatomy, `manifest.json` + permissions,
  runtime page/file/selection hooks, sample plugins to mirror, the access-token /
  webhook REST API, and plugin-vs-MCP selection.
