---
type: Document
title: Penpot MCP — the agent-driven surface
---

# Penpot MCP — what an agent can read and do

Penpot ships its **own** official MCP server (`@penpot/mcp`, npm). It is not a
third-party bridge — it is Penpot's own LLM layer, built on top of the Penpot
**Plugin API**. This file lists the real tools and how the surface is wired, so
an agent uses the actual capability instead of inventing one.

## Architecture (read this before reasoning about latency or trust)

The chain is: **MCP client (the agent) → MCP server → WebSocket → Penpot MCP
Plugin → Penpot Plugin API → the live design file in the browser.**

- The server exposes MCP tools to the agent. The **plugin** (loaded inside an
  open Penpot file) connects back to the server over WebSocket and actually runs
  the work against the file.
- Therefore **a design file must be open in Penpot with the MCP plugin connected**
  for any tool to do anything. The plugin UI must stay open and the tab stay
  active; closing the UI or a suspended tab drops the connection and the server
  rejects tasks.
- The LLM writes and runs **arbitrary JS** in the plugin sandbox. The model's
  power over the file is the Plugin API's power — nothing more, nothing less.

## Transport / connection facts

- Server default port **4401**: Streamable HTTP at `http://localhost:4401/mcp`,
  legacy SSE at `http://localhost:4401/sse`. WebSocket (plugin) default **4402**.
- Launch released: `npx -y @penpot/mcp@latest` (or `@beta` for the test server).
- stdio-only clients need a proxy: `npx -y mcp-remote http://localhost:4401/mcp --allow-http`.
- Claude Code: `claude mcp add penpot -t http http://localhost:4401/mcp`.
- Remote mode (`PENPOT_MCP_REMOTE_MODE=true`) **disables local file-system
  access** — which removes the file-backed tools (see tiers below).
- Use a **capable, vision-capable** model: many design tasks require visually
  inspecting an exported image, and weak/local models produce unusable results.

## The tools (real names, from the server source)

### Always registered (core surface)

- **`high_level_overview`** — returns the base usage instructions + the Penpot
  design model (shapes, boards, layouts, components, tokens). **Read this first,
  once**, before any other tool. Do not call it again in the same session.
- **`penpot_api_info`** — retrieves Penpot Plugin API documentation for specific
  types and their members. The lookup you reach for before writing code that
  touches an unfamiliar type.
- **`execute_code`** — the workhorse. Runs JavaScript in the Penpot plugin
  context with `penpot` (the API), `penpotUtils` (helpers — prefer these over
  re-implementing search/layout logic), and `storage` (a persistent object that
  survives across calls — stash selections and intermediate results here, never
  trust the live selection to stay put). The body is treated as a function body;
  whatever you `return` comes back (no `JSON.stringify` needed). **Never `console.log`
  data you are also returning — you receive it twice.** Try the simple approach
  first; add error-handling/logging only when it fails.
- **`export_shape`** — exports a shape (or a shape's image fill) to PNG or SVG so
  the agent can **visually inspect** what it looks like. The eyes of the loop —
  use it to verify a generated/modified design actually renders correctly.

### File-system mode only (off in remote mode)

- **`import_image`** — imports a local pixel image (JPEG/PNG/GIF/WEBP) into Penpot
  as a Rectangle whose fill is that image; keeps aspect ratio by default; optional
  x/y/width/height.

### Penpot devenv only (`PENPOT_MCP_DEVENV=true`, for Penpot's own contributors)

Not part of a normal design session — these target Penpot's own codebase:

- **`cljs_repl`** — persistent ClojureScript REPL in the Penpot frontend runtime
  (shadow-cljs nREPL); state persists across calls.
- **`cljs_compiler_output`** — status of the most recent shadow-cljs `:main` build.
- **`clj_check_parentheses`** — finds unclosed delimiters in a Clojure/CLJS file.
- **`import_penpot_file`** — imports a `.penpot` file from a URL into the user's
  Drafts project; returns the imported file name(s).
- **`read_taiga_issue`** — reads a Penpot issue from the Taiga tracker.

## The execute_code loop (the doctrine that makes it work)

1. Read `high_level_overview` once.
2. Inspect before you mutate: `penpotUtils.shapeStructure(page.root, 3)` for a
   page overview; `penpotUtils.findShape(s)` with predicates to locate elements;
   copy `penpot.selection` into `storage` immediately.
3. Look up unknown types with `penpot_api_info` before writing against them.
4. Mutate in small `execute_code` steps, building helpers up in `storage`.
5. **Verify visually** with `export_shape` — don't declare a design done you
   haven't looked at.

Generation shortcuts already in the API: `penpot.generateStyle(shapes, {type:"css",
withChildren:true})` for CSS, `penpot.generateMarkup(...)` for HTML/SVG — this is
the design→code direction the MCP advertises.
