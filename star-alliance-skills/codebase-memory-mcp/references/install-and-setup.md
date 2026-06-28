---
type: Document
title: Install, setup, and operating the engine
---

# Install and setup

codebase-memory-mcp ships as a **single static binary** (macOS arm64/amd64, Linux
arm64/amd64, Windows amd64). No Docker, no runtime deps, no API keys, zero vendored
infrastructure. Everything runs **100% locally** — code never leaves the machine.

## One-line install (macOS / Linux)

```bash
curl -fsSL https://raw.githubusercontent.com/DeusData/codebase-memory-mcp/main/install.sh | bash
```

With the 3D graph-visualization UI:

```bash
curl -fsSL https://raw.githubusercontent.com/DeusData/codebase-memory-mcp/main/install.sh | bash -s -- --ui
```

Windows (PowerShell): download `install.ps1`, inspect it, then run `.\install.ps1`.

Install options: `--ui` (graph UI), `--skip-config` (binary only, no agent setup),
`--dir=<path>` (custom location).

**After install: restart your coding agent, then say "Index this project".**

Also distributed via npm, PyPI, Homebrew, Scoop, Winget, Chocolatey, AUR
(`yay -S codebase-memory-mcp-bin`), and `go install`.

## What `install` configures — 11 agents, one command

`install` auto-detects every installed agent and writes MCP entries, instruction
files, skills, and pre-tool hooks for each: **Claude Code, Codex CLI, Gemini CLI,
Zed, OpenCode, Antigravity, Aider, KiloCode, VS Code, OpenClaw, Kiro.**

- **Claude Code** gets `.claude/.mcp.json`, 4 Skills, and a **non-blocking**
  `PreToolUse` hook that intercepts `Grep`/`Glob` (never `Read`) and, when the
  search token matches indexed symbols, injects them as `additionalContext` via
  `search_graph` — so a normal grep also returns structured graph context. The shim
  is named `cbm-code-discovery-gate` for backward compatibility; despite the legacy
  name it **never gates and never blocks** (exit 0 on every path).
- **Codex / Gemini CLI / Antigravity** get a `SessionStart` code-discovery reminder.

The `install` command auto-strips macOS quarantine and ad-hoc signs the binary — no
manual `xattr` / `codesign`.

## Manual MCP config (if you skip `install`)

Add to `~/.claude/.mcp.json` (global) or project `.mcp.json`:

```json
{
  "mcpServers": {
    "codebase-memory-mcp": {
      "command": "/path/to/codebase-memory-mcp",
      "args": []
    }
  }
}
```

Restart, then verify with `/mcp` → `codebase-memory-mcp` with **14 tools**.

## Graph visualization UI (3D, localhost:9749)

The UI is a **separate binary variant** — install with `--ui` (one-line: `… | bash
-s -- --ui`; manual: download the `codebase-memory-mcp-ui-<os>-<arch>` archive). Then
launch it:

```bash
codebase-memory-mcp --ui=true --port=9749
```

Open `http://localhost:9749`. The UI runs as a background thread alongside the MCP
server — a 3D interactive knowledge-graph explorer, available whenever the agent is
connected. A **multi-galaxy layout** renders each indexed repo as its own galaxy and
draws the `CROSS_*` edges between them, so cross-repo architecture is visible at a
glance.

**When to use it:** the agent answers structural questions far more cheaply via the
MCP tools — reach for the UI for *human* exploration, not agent queries: eyeballing
overall shape, spotting clusters/hotspots `get_architecture` summarizes, presenting a
cross-repo map to a teammate, or sanity-checking that an index looks complete. It is
not required for any tool to work; skip the `--ui` variant entirely if you only drive
the engine through the agent.

## Operating it

- **Auto-index on session start**: `codebase-memory-mcp config set auto_index true`
  (limit via `config set auto_index_limit 50000`). New projects index on first
  connection; known projects register with the background watcher for git-based
  change detection.
- **Background auto-sync**: a watcher polls git and re-indexes changed files so the
  graph stays fresh without manual re-runs.
- **Update**: `codebase-memory-mcp update` (also auto-checks on startup).
- **Uninstall**: `codebase-memory-mcp uninstall` removes agent configs/skills/hooks
  (leaves the binary and the SQLite DBs).
- **CLI mode** — every tool is callable headless:
  `codebase-memory-mcp cli search_graph '{"name_pattern": ".*Handler.*"}'`,
  add `--raw … | jq` for scripting.

## Persistence, ignores, config

- **Storage**: SQLite at `~/.cache/codebase-memory-mcp/` (WAL, ACID, survives
  restarts). Override with `CBM_CACHE_DIR`. Reset with
  `rm -rf ~/.cache/codebase-memory-mcp/`.
- **Ignore layering**: hardcoded patterns (`.git`, `node_modules`) → `.gitignore`
  hierarchy → `.cbmignore` (gitignore syntax). Symlinks always skipped.
- **Custom extensions**: map extra extensions to languages per-project
  (`.codebase-memory.json`) or globally — e.g. `{"extra_extensions": {".blade.php": "php"}}`.
- **Env vars**: `CBM_CACHE_DIR`, `CBM_WORKERS`, `CBM_LOG_LEVEL`, `CBM_DIAGNOSTICS`,
  `CBM_DUMP_VERIFY_MIN_RATIO` (indexing returns `status:"degraded"` if persisted
  nodes fall below this fraction of committed nodes).

## What gets indexed beyond code (infrastructure-as-code)

The pipeline indexes **infrastructure-as-code** alongside source: **Dockerfiles,
Kubernetes manifests, and Kustomize overlays** become first-class graph nodes —
`Resource` nodes for K8s kinds (and Dockerfile-derived resources), `Module` nodes for
Kustomize overlays, with `IMPORTS` edges from an overlay to the resources it
references. No extra config; it happens on a normal `index_repository`. Query it like
any other part of the graph (see the infra-query recipes in query-recipes.md) — e.g.
"which overlay deploys this resource?" without grepping YAML.

## Cross-repo intelligence (shared store + multi-galaxy)

Index multiple repos under the **same store** (the default `~/.cache/codebase-memory-mcp/`,
or a shared `CBM_CACHE_DIR`) and the engine links them with `CROSS_*` edges, exposing a
cross-repo architecture view (services, routes, dependencies across the fleet).

- **Scope queries** to one repo with `project="name"` (`list_projects` lists them); this
  is also the fix when results from the wrong repo leak in.
- **Visualize** the fleet with the multi-galaxy 3D UI (above).
- **Share the index** via the team artifact below — the recommended way to bootstrap a
  teammate or a second machine into the same graph without a full reindex.

## Team-shared graph artifact

Commit `.codebase-memory/graph.db.zst` (a zstd-compressed graph snapshot, 8–13:1) next
to the source and teammates skip the reindex. Two export tiers: **Best** (`zstd -9` +
index strip + `VACUUM INTO`) on an explicit `index_repository`, **Fast** (`zstd -3`)
written by the watcher for low-latency incremental updates.

**Bootstrap path:** when no local DB exists but the artifact is present,
`index_repository` **imports the artifact first**, then runs incremental indexing to
fill only the local diff — avoiding the full reindex cost on a fresh clone or machine.
A `merge=ours` `.gitattributes` line is auto-created on first export so the binary
artifact never produces merge conflicts. Optional — gitignore `.codebase-memory/` if you
prefer everyone reindex from scratch. (Similar in spirit to graphify's `graphify-out/`,
but a single integrity-checked compressed file.)

## Troubleshooting (high-signal)

- `/mcp` doesn't show the server → make the `.mcp.json` `command` path **absolute**,
  restart. Smoke test: `echo '{}' | /path/to/binary` should print JSON.
- `index_repository` fails → pass an **absolute** `repo_path`.
- `trace_path` returns 0 → the name is wrong or the repo is unindexed; run
  `search_graph(name_pattern=".*Partial.*")` first to get the exact qualified name.
- Wrong project's results → add `project="name"` (`list_projects` shows names).
</content>
