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

## Graph visualization UI

If you installed the `ui` variant:

```bash
codebase-memory-mcp --ui=true --port=9749
```

Open `http://localhost:9749`. The UI runs as a background thread alongside the MCP
server — a 3D interactive knowledge-graph explorer, available whenever the agent is
connected. Multi-galaxy layout for cross-repo views.

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

## Team-shared graph artifact

Commit `.codebase-memory/graph.db.zst` (a zstd-compressed graph snapshot, 8–13:1)
next to the source and teammates skip the reindex: on first run the artifact is
imported, then incremental indexing fills their local diff. A `merge=ours`
`.gitattributes` line is auto-created so the binary artifact never conflicts.
Optional — gitignore `.codebase-memory/` if you prefer everyone reindex from scratch.

## Troubleshooting (high-signal)

- `/mcp` doesn't show the server → make the `.mcp.json` `command` path **absolute**,
  restart. Smoke test: `echo '{}' | /path/to/binary` should print JSON.
- `index_repository` fails → pass an **absolute** `repo_path`.
- `trace_path` returns 0 → the name is wrong or the repo is unindexed; run
  `search_graph(name_pattern=".*Partial.*")` first to get the exact qualified name.
- Wrong project's results → add `project="name"` (`list_projects` shows names).
</content>
