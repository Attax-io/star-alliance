---
type: Document
title: The 14 MCP tools — which to reach for per question
---

# The 14 MCP tools

codebase-memory-mcp exposes exactly **14 MCP tools**, split into Indexing (4) and
Querying (10). The agent (you) is the intelligence layer; the server is the
structural backend. There is **no built-in LLM** — you translate the question into
a tool call and narrate the structured result back in plain English.

Verify the surface after install with `/mcp` — you should see `codebase-memory-mcp`
with 14 tools.

## Indexing tools (4)

| Tool | What it does | Reach for it when |
|------|--------------|-------------------|
| `index_repository` | Full-index a repo into the graph (auto-sync keeps it fresh after). Bootstraps from a committed `.codebase-memory/graph.db.zst` artifact if present, then incremental-fills the diff. | "index this project", "index this codebase", first contact with a new repo, or `trace_path` returns 0 because nothing is indexed yet. **Pass an absolute `repo_path`.** |
| `list_projects` | List all indexed projects with node / edge counts. | You need the exact project name to scope a query, or to confirm an index exists. |
| `index_status` | Check indexing status of a project. | Index is large/slow (e.g. monorepo, kernel-scale) and you want to confirm it finished before querying. |
| `delete_project` | Remove a project and all its graph data. | Cleanup, or forcing a clean re-index. |

## Querying tools (10)

| Tool | What it does | The question it answers |
|------|--------------|------------------------|
| `get_graph_schema` | Node/edge counts, relationship patterns, property defs per label. **Run this first** on an unfamiliar graph. | "what's actually in this graph / what can I query?" — orient before writing Cypher. |
| `get_architecture` | One-call overview: languages, packages, entry points, routes, hotspots, boundaries, layers, clusters, ADRs. | "map this repo's architecture", "give me the lay of the land", "what are the entry points / hotspots?" |
| `search_graph` | Structured search by label, name pattern (regex), file pattern, min/max degree; paginated. Also the BM25 / semantic search surface. | "where is X defined?", "find all `.*Handler.*` functions", "list the classes in this file". **Use this to discover exact qualified names before `trace_path` / `get_code_snippet`.** |
| `trace_path` | BFS call-chain traversal, inbound / outbound / both, depth 1–5 (alias `trace_call_path`). | "what calls Y?" (inbound), "what does Y call?" (outbound), "trace this call chain", "show the path from A to B". |
| `detect_changes` | Map a git diff to affected symbols + blast radius, with risk classification. | "impact of changing Z", "what does my uncommitted diff touch?", "what's the blast radius of this PR?", "what should I re-test?" |
| `query_graph` | Execute a read-only openCypher subset (`MATCH … RETURN …`). | Anything the structured tools don't express directly — dead-code (`WHERE NOT EXISTS { (f)<-[:CALLS]-() }`), custom multi-hop traversals, aggregates. See query-recipes.md. |
| `get_code_snippet` | Read the source of a function by **qualified name** (`<project>.<path>.<name>`). | "show me the body of function X" once you have its qualified name (find it via `search_graph`). |
| `search_code` | Graph-augmented grep over indexed project files only. | "find this literal / text", "where does this string appear?" — text search that stays inside the indexed set. |
| `manage_adr` | CRUD for Architecture Decision Records, persisted across sessions. | "record this architectural decision", "what ADRs exist?", "why was X chosen?" |
| `ingest_traces` | Ingest runtime traces to validate `HTTP_CALLS` (cross-service) edges. | You have runtime/observability traces and want to confirm or strengthen inferred cross-service links. |

## Question → tool cheat sheet

- "index this codebase / project" → `index_repository`
- "where is X defined?" → `search_graph` (then `get_code_snippet` for the body)
- "what calls Y?" / "what does Y call?" → `trace_path` (inbound / outbound)
- "trace this call chain" → `trace_path` direction=both, depth up to 5
- "impact of changing Z" / "blast radius of my diff" → `detect_changes`
- "map this repo's architecture" → `get_architecture`
- "find dead code" → `query_graph` with a `NOT EXISTS { (f)<-[:CALLS]-() }` pattern
- "what HTTP route handles this call / cross-service link?" → `query_graph` over `HTTP_CALLS` / `Route` (validate with `ingest_traces`)
- "show me the source of X" → `get_code_snippet` (qualified name)
- "what's in this graph?" → `get_graph_schema`
- "record / recall an architecture decision" → `manage_adr`

## Note on semantic search

The search layer also offers **semantic / vector search** (bundled `nomic-embed-code`
embeddings, 11-signal scoring) and **BM25 full-text** with a camelCase/snake_case-aware
tokenizer. These are reached through the search surface (`search_graph` / `search_code`)
— useful when you know *what a thing does* but not its exact name. No API key, no Ollama,
no Docker; embeddings are compiled into the binary.

## Graph data model (for `query_graph`)

- **Node labels**: `Project`, `Package`, `Folder`, `File`, `Module`, `Class`,
  `Function`, `Method`, `Interface`, `Enum`, `Type`, `Route`, `Resource`.
- **Edge types**: `CONTAINS_PACKAGE`, `CONTAINS_FOLDER`, `CONTAINS_FILE`, `DEFINES`,
  `DEFINES_METHOD`, `IMPORTS`, `CALLS`, `HTTP_CALLS`, `ASYNC_CALLS`, `IMPLEMENTS`,
  `HANDLES`, `USAGE`, `CONFIGURES`, `WRITES`, `MEMBER_OF`, `TESTS`, `USES_TYPE`,
  `FILE_CHANGES_WITH`.
</content>
</invoke>
