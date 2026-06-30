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

## "Find the code that does X" (by behavior, not name)

When you can describe *what the code does* but not what it's called, skip regex and
go semantic:

```
semantic_query(query="where do we verify/decode JWT access tokens?")
semantic_query(query="exponential backoff retry on a failed HTTP request")
```
`semantic_query` is vector search over the whole graph (bundled `nomic-embed-code`,
768d int8, no API key / Ollama / Docker). Each hit comes with an **11-signal scoring
breakdown** — TF-IDF, RRI, API/Type/Decorator signatures, AST profiles, data flow,
Halstead-lite, MinHash, module proximity, graph diffusion. **Read the breakdown
before trusting a borderline hit:** strong hits show agreement across several
independent signals (API + AST + data-flow); a hit carried only by module proximity
or a single signal is weak. Then pivot to the exact name with `search_graph` /
`get_code_snippet` to read the body.

Contrast: `search_graph` = known name (regex/BM25), `semantic_query` = known behavior,
`search_code` = known literal.

## "Find near-duplicates / cloned functions"

```
query_graph(query="MATCH (a:Function)-[s:SIMILAR_TO]->(b:Function) RETURN a.name, b.name, s.score ORDER BY s.score DESC LIMIT 50")
```
`SIMILAR_TO` edges come from **MinHash + LSH near-clone detection**, Jaccard-scored —
structural near-duplicates worth consolidating. For clones that *do the same thing in
different vocabulary* (e.g. `getUser` vs `fetchAccount`), use the meaning-level edge:

```
query_graph(query="MATCH (a:Function)-[r:SEMANTICALLY_RELATED]->(b:Function) RETURN a.name, b.name, r.score ORDER BY r.score DESC")
```
`SEMANTICALLY_RELATED` is same-language, vocabulary-mismatch, score ≥ 0.80. Use either
to drive a dedup / DRY pass; spot-check both bodies with `get_code_snippet` before
merging.

## Infrastructure-as-code queries (Docker / K8s / Kustomize)

Dockerfiles, Kubernetes manifests, and Kustomize overlays are indexed as graph nodes:
K8s kinds (and Dockerfile-derived resources) become `Resource` nodes, Kustomize
overlays become `Module` nodes with `IMPORTS` edges to the resources they reference.

```
query_graph(query="MATCH (r:Resource) RETURN r.name, r.kind LIMIT 50")                 # what infra resources exist
query_graph(query="MATCH (m:Module)-[:IMPORTS]->(r:Resource) RETURN m.name, r.name")   # which overlay pulls in which resource
```
Answers "what does this Kustomize overlay deploy?" / "which manifest defines this
resource?" without grepping YAML by hand.

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
```
`Route` is a first-class node. Route detection spans **REST, gRPC, GraphQL, and tRPC**
(protobuf Route extraction included), so the same `HTTP_CALLS` / `Route` patterns find
service links regardless of transport.

## Pub-sub / event channels

```
query_graph(query="MATCH (p)-[:EMITS]->(c) RETURN p.name, c.name")          # who publishes which channel/event
query_graph(query="MATCH (c)<-[:LISTENS_ON]-(h) RETURN c.name, h.name")     # who subscribes / handles it
```
`EMITS` / `LISTENS_ON` model pub-sub channels for Socket.IO, EventEmitter, and generic
pub-sub patterns across ~8 languages, with constant resolution (so a channel named by a
`const` is linked, not lost). Use them to trace event-driven flows that have no direct
call edge.

## Validate cross-service edges with runtime traces (`ingest_traces`)

Inferred `HTTP_CALLS` edges are static guesses; runtime telemetry confirms them.

```
ingest_traces(...)    # feed observability traces; matched edges get validated / strengthened
```
Workflow: (1) capture HTTP traces from your observability stack (each entry pairs a
caller with the route/endpoint actually hit), (2) `ingest_traces` to reconcile them
against the graph — real traffic validates true `HTTP_CALLS` edges and surfaces links
the static pass missed or got wrong, (3) re-query the `Route` / `HTTP_CALLS` patterns
above with higher confidence. Reach for this when a cross-service answer is
load-bearing (an incident, a contract change) and static inference alone isn't enough.

## Cross-repo questions (multi-repo / `project` scoping)

When several repos are indexed under the same store, `CROSS_*` edges link nodes across
them — so you can answer questions that span service boundaries:

```
list_projects()                                                      # see every indexed repo + its name
search_graph(name_pattern=".*PaymentClient.*", project="billing")    # scope a search to one repo
query_graph(query="MATCH (a)-[x]->(b) WHERE type(x) STARTS WITH 'CROSS_' RETURN a.name, b.name")  # cross-repo links
```
- **Scope with `project="name"`** whenever results from the wrong repo leak in
  (`list_projects` shows the names) — this is also the standard fix for "wrong
  project's results".
- The multi-galaxy 3D UI renders these cross-repo links visually (see install-and-setup).
- **Share the index, skip the reindex**: commit `.codebase-memory/graph.db.zst` and a
  teammate's first `index_repository` **bootstraps** from the artifact, then
  incremental-indexes only their local diff (see install-and-setup for the two-tier
  export and `merge=ours` no-conflict detail).

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
MATCH (f:File)-[:FILE_CHANGES_WITH]->(g:File) RETURN f.name, g.name        # co-change coupling
MATCH (a:Function)-[s:SIMILAR_TO]->(b:Function) RETURN a.name, b.name, s.score  # near-clones
MATCH (m:Module)-[:IMPORTS]->(r:Resource) RETURN m.name, r.name           # Kustomize → K8s resource
MATCH (p)-[:EMITS]->(c) RETURN p.name, c.name                             # pub-sub channels
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
