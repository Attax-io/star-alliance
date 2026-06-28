---
type: Document
title: Query recipes — common code-intelligence questions to tool calls
---

# Query recipes

Each recipe maps a real developer question to the tool call(s) that answer it with
the fewest tokens. Discovery before traversal: most chains start by finding an exact
name with `search_graph`, then act on it.

## Orient on an unfamiliar repo

```
get_graph_schema()        # node/edge counts, what's queryable — run first
get_architecture()        # languages, packages, entry points, routes, hotspots, clusters
```
Answers "map this repo's architecture" / "where do I start?" in two calls instead of
reading dozens of files.

## "Where is X defined?"

```
search_graph(name_pattern=".*X.*", label="Function")   # or Class / Method / Type
get_code_snippet(name="<project>.<path>.X")            # body, once you have the qualified name
```
Qualified-name format is `<project>.<path_parts>.<name>`; always discover it via
`search_graph` first.

## "What calls Y?" / "What does Y call?"

```
trace_path(function_name="Y", direction="inbound")     # callers
trace_path(function_name="Y", direction="outbound")    # callees
trace_path(function_name="Y", direction="both", depth=5)  # full local call chain
```
Import-aware and type-inferred (Hybrid LSP), so calls resolve across files, packages,
and inheritance — not just same-file textual matches. If it returns 0, the name is
wrong; `search_graph` first.

## "Impact of changing Z" / "blast radius of my diff"

```
detect_changes()    # maps the current git diff to affected symbols + risk-classified blast radius
```
Use before a refactor or to scope re-testing. Pairs well with
`trace_path(direction="inbound")` on each flagged symbol to see who downstream breaks.

## "Find dead code"

```
query_graph(query="MATCH (f:Function) WHERE NOT EXISTS { (f)<-[:CALLS]-() } RETURN f.name")
```
`EXISTS { … }` single-hop existence is the idiom; exclude legitimate entry points
(`main`, route handlers, test fns) in the `WHERE`.

## Cross-service / HTTP linking

```
query_graph(query="MATCH (:Route)-[:HTTP_CALLS]->(f) RETURN f.name")   # who a route reaches
ingest_traces(...)    # feed runtime traces to validate / strengthen HTTP_CALLS edges
```
`Route` is a first-class node. Also detects gRPC / GraphQL / tRPC services and
`EMITS` / `LISTENS_ON` channels (Socket.IO, EventEmitter, pub-sub).

## Custom traversals with Cypher (`query_graph`)

Read-only openCypher subset. Supported: `MATCH`, `OPTIONAL MATCH`, `WHERE`, `WITH`,
`RETURN`, `ORDER BY`, `SKIP`, `LIMIT`, `DISTINCT`, `UNWIND`, `UNION`(`ALL`), `CASE`;
label alternation `(n:A|B)`; variable-length paths `[*1..3]`; aggregates (`count`,
`sum`, `avg`, `min`, `max`, `collect`); string/cast functions. Anything outside the
subset (writes, `MERGE`, `CALL`, comprehensions, params) **fails with a clear
`unsupported …` error** — never a silently-empty result. Examples:

```cypher
MATCH (f:Function)-[:CALLS]->(g) WHERE f.name = 'main' RETURN g.name
MATCH (c:Class)-[:IMPLEMENTS]->(i:Interface) RETURN c.name, i.name
MATCH (f:File)-[:FILE_CHANGES_WITH]->(g:File) RETURN f.name, g.name   # co-change coupling
```

## Architecture Decision Records

```
manage_adr(...)   # CRUD — record "why we chose X", recall across sessions
```
Persists architectural rationale in the graph so it survives context resets.

## Token economy — why this beats grep

Five structural queries cost **~3,400 tokens** vs **~412,000** via file-by-file grep
exploration (claimed ~99% / "120x" reduction; arXiv eval: 10x fewer tokens, 2.1x
fewer tool calls, 83% answer quality across 31 repos). One graph query replaces dozens
of grep→read cycles. Reach for a graph tool **before** fanning out reads on any
structural ("where/what-calls/impact/architecture") question over an indexed repo.
</content>
