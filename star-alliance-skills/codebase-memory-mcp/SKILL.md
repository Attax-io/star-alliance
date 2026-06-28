---
name: codebase-memory-mcp
description: "Use this MCP code-intelligence engine to answer structural questions about a real repository: 'index this codebase', 'where is X defined', 'what calls Y', 'trace this call chain', 'impact of changing Z', 'find dead code', 'map this repo's architecture', or cross-service HTTP linking and Cypher queries over a knowledge graph of functions, classes, call chains, and routes. It is a fast external MCP server (single static binary, 158 languages via tree-sitter plus Hybrid LSP type resolution, 14 tools, ~120x fewer tokens than file-by-file grep) that indexes a repo into a persistent graph the agent queries. Reach for it before fanning out greps/reads on any where/what-calls/impact/architecture question. Differs from graphify, the guild's own graph-building craft over arbitrary inputs (code, docs, papers, media); codebase-memory-mcp is purpose-built code intelligence over one indexed repo."
metadata:
  version: 1.0.0
type: Skill
---

# codebase-memory-mcp

A fast, external **MCP code-intelligence engine**. It full-indexes a repository into
a persistent knowledge graph — functions, classes, call chains, HTTP routes,
cross-service links — and exposes **14 MCP tools** that answer structural questions
in under a millisecond and at a fraction of the token cost of reading files. This
skill teaches **when** to reach for it and **which tool** answers which question. It
is a usage skill (like the Supabase skill teaches using Supabase), not a
re-implementation.

## What it is

- A **single static binary** (macOS / Linux / Windows), zero dependencies, no API
  keys, no Docker. Runs 100% locally; code never leaves the machine.
- **158 languages** parsed via vendored tree-sitter grammars, with **Hybrid LSP**
  semantic type resolution for ~11 languages (Python, TS/JS/JSX/TSX, PHP, C#, Go,
  C, C++, Java, Kotlin, Rust) — so calls resolve across files, imports, generics,
  and inheritance, not just same-file text.
- A **structural backend with no built-in LLM**: the agent *is* the intelligence
  layer. You translate the user's question into a tool call and narrate the
  structured result back.
- Persists to SQLite (`~/.cache/codebase-memory-mcp/`), auto-syncs on git changes,
  ships an optional 3D graph-visualization UI at `localhost:9749`, and one `install`
  command auto-configures Claude Code plus 10 other agents.

## What it is not

- **Not graphify.** `graphify` is the guild's own craft that turns *arbitrary
  inputs* (code, docs, papers, images, video) into a knowledge graph with community
  detection and an HTML/JSON/report bundle in `graphify-out/`. codebase-memory-mcp is
  a **purpose-built, external code-intelligence engine over one real indexed repo**,
  queried live through MCP tools. Use **codebase-memory-mcp** for structural code
  questions about a codebase you can index; use **graphify** to build a graph over
  mixed or non-code inputs, or when you want the portable `graphify-out/` artifact and
  guild-controlled pipeline. They overlap only in spirit (the team-shared
  `.codebase-memory/graph.db.zst` artifact resembles `graphify-out/`).
- **Not a grep replacement for content edits.** It augments search; you still `Read`
  before you `Edit`. Its Claude hook never gates `Read`.
- **Not an LLM.** No NL→query model bundled — that is your job as the MCP client.

## Principles

1. **Index once, then ask the graph.** First contact with a repo → `index_repository`
   (absolute path). After that the background watcher keeps it fresh. A `trace_path`
   that returns 0 usually means *nothing is indexed yet* or *the name is wrong* — not
   that the answer is empty.

2. **Graph-first on structural questions.** For any "where is X / what calls Y / what
   does Z touch / what's the architecture" question over an indexed repo, reach for a
   graph tool **before** fanning out greps and reads. Five structural queries cost
   ~3,400 tokens versus ~412,000 for file-by-file exploration — the whole point is to
   *not* read dozens of files to learn structure.

3. **Discover the exact name, then traverse.** Names are load-bearing.
   `search_graph(name_pattern=".*X.*")` to find the exact (qualified) name, *then*
   `trace_path` / `get_code_snippet`. Skipping discovery is the #1 cause of empty
   results.

4. **One tool per question class.** Match the question to the right tool rather than
   forcing everything through Cypher:
   - "where is X defined" → `search_graph` (→ `get_code_snippet` for the body)
   - "what calls Y / what does Y call / trace the chain" → `trace_path`
   - "impact of changing Z / blast radius of my diff" → `detect_changes`
   - "map the architecture" → `get_architecture`; "what's queryable" → `get_graph_schema`
   - "find dead code / custom multi-hop" → `query_graph` (Cypher subset)
   - "cross-service / HTTP route linking" → `query_graph` over `HTTP_CALLS`/`Route`,
     validated by `ingest_traces`
   - "record/recall an architecture decision" → `manage_adr`

   Full mapping in `references/mcp-tools.md`.

5. **The graph is a source of truth, but a derived one.** It mirrors what an IDE
   "Go to Definition" resolves (Hybrid LSP), but languages without a Hybrid LSP pass
   fall back to textual resolution. Trust it for structure; spot-check load-bearing
   claims with `get_code_snippet` before acting destructively.

6. **Stay inside MCP; degrade gracefully.** Drive it through its MCP tools (or CLI
   mode for scripting). If the server isn't connected, fix the install (`/mcp` should
   show 14 tools, absolute `command` path) rather than fabricating a structural
   answer.

## When to reach for this skill

Trigger phrases: "index this codebase/project", "where is X defined", "what calls Y",
"trace this call chain", "impact of changing Z", "find dead code", "map this repo's
architecture", "what HTTP route handles this", "set up codebase-memory-mcp". Any
structural code-intelligence question over a real repository you can index.

## References

- `references/mcp-tools.md` — the 14 tools, each mapped to the question it answers,
  the question→tool cheat sheet, semantic-search note, and the graph data model.
- `references/install-and-setup.md` — install (one-line / 11-agent auto-config / UI),
  operating it (auto-index, watcher, CLI), persistence, ignores, team-shared artifact,
  troubleshooting.
- `references/query-recipes.md` — recipes from real questions to tool calls, Cypher
  examples (dead code, co-change, cross-service), and the token-economy rationale.
</content>
