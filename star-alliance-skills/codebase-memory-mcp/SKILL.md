---
name: codebase-memory-mcp
description: "Use this MCP code-intelligence engine to answer structural questions about a real repository: 'index this codebase', 'where is X defined', 'what calls Y', 'trace this call chain', 'impact of changing Z', 'find dead code', 'find near-duplicate code', 'map this repo's architecture', semantic by-behavior search, infrastructure-as-code (Docker/K8s/Kustomize) queries, cross-service gRPC/GraphQL/tRPC and pub-sub linking, cross-repo questions, and Cypher over a knowledge graph of functions, classes, routes, and resources. A fast external MCP server (single static binary, 158 languages via tree-sitter plus Hybrid LSP, 14 tools, semantic_query vector search, optional 3D graph UI at localhost:9749, ~120x fewer tokens than grep) that indexes a repo into a persistent graph the agent queries. Reach for it before fanning out greps/reads on any structural question. Differs from graphify, the guild's graph-building craft over arbitrary inputs; codebase-memory-mcp is code intelligence over one or many indexed repos."
metadata:
  version: 1.1.0
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
   - "where is X defined" (known name) → `search_graph` (→ `get_code_snippet` for the body)
   - "find the code that does X" (known behavior, not name) → `semantic_query` (vector
     search; read its **11-signal scoring breakdown** before trusting a borderline hit)
   - "what calls Y / what does Y call / trace the chain" → `trace_path`
   - "impact of changing Z / blast radius of my diff" → `detect_changes`
   - "map the architecture" → `get_architecture`; "what's queryable" → `get_graph_schema`
   - "find dead code / near-duplicates / custom multi-hop" → `query_graph` (Cypher subset;
     `SIMILAR_TO` for MinHash/LSH near-clones)
   - "Docker/K8s/Kustomize infra" → `query_graph` over `Resource` / `Module` nodes
   - "cross-service (REST/gRPC/GraphQL/tRPC) or pub-sub link" → `query_graph` over
     `HTTP_CALLS`/`Route`/`EMITS`/`LISTENS_ON`, validated by `ingest_traces` (runtime traces)
   - "cross-repo question" → `list_projects` + `project="name"` scoping + `CROSS_*` edges
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
"trace this call chain", "impact of changing Z", "find dead code", "find near-duplicate
code", "map this repo's architecture", "find the code that does X" (semantic), "what
HTTP/gRPC/GraphQL route handles this", "which K8s/Docker resource configures this",
"cross-repo / which service calls which", "set up codebase-memory-mcp", "open the graph
UI". Any structural code-intelligence question over one or more real repositories you
can index.

## References

- `references/mcp-tools.md` — the 14 tools, each mapped to the question it answers,
  the question→tool cheat sheet, the **three search modes** (`search_graph` exact /
  `semantic_query` by-behavior with 11-signal scoring / `search_code` literal), and the
  graph data model incl. IaC `Resource`/`Module` nodes, `SIMILAR_TO`/`SEMANTICALLY_RELATED`,
  pub-sub `EMITS`/`LISTENS_ON`, and cross-repo `CROSS_*` edges.
- `references/install-and-setup.md` — install (one-line / 11-agent auto-config / `--ui`),
  operating it (auto-index, watcher, CLI), persistence, ignores, IaC indexing, cross-repo
  shared store + multi-galaxy UI, team-shared artifact bootstrap, troubleshooting.
- `references/query-recipes.md` — recipes from real questions to tool calls: semantic
  by-behavior search, near-duplicate detection, infra-as-code queries, cross-service /
  pub-sub linking, `ingest_traces` validation, cross-repo patterns, Cypher examples, and
  the token-economy rationale.

## Changelog

- **1.1.0** — Added the capabilities the skill omitted (grounded in the source README):
  `semantic_query` vector search as a distinct mode with the 11-signal scoring breakdown;
  `SIMILAR_TO` (MinHash/LSH) near-duplicate detection recipe; infrastructure-as-code
  (`Resource`/`Module`) indexing + infra-query section; cross-repo `CROSS_*` edges,
  `project` scoping, multi-galaxy UI, and the `graph.db.zst` bootstrap; gRPC/GraphQL/tRPC
  route detection and `EMITS`/`LISTENS_ON` pub-sub recipes; `ingest_traces` workflow; and
  a "when to use" note for the 3D UI at localhost:9749.
- **1.0.0** — Initial usage skill: 14 MCP tools, principles, install/setup, query recipes.
</content>
