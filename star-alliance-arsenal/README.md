---
type: Readme
timestamp: 2026-07-03T00:00:00Z
---

# Star Alliance — Arsenal

The guild's model registry and small support tools. The Star Alliance is a
**Claude-only** harness: every member runs as one of three Claude models, and the
guild is exposed to projects as an **MCP server**. There is no external doer,
Hermes, or non-Claude bench layer — that machinery has been removed.

## The three Claude models

| Model | Role | Use it for |
|---|---|---|
| **opus** | thinker | Deepest reasoning — hard plans, architecture, review. |
| **sonnet** | both | Balanced daily driver — fast, reliable, near-Opus quality. |
| **haiku** | both | Fastest and cheapest — bulk classification, routing, mechanical transforms. |

The session persona (the Butler) is itself a Claude model. Bulk or parallel work
is handled by **spawning Claude subagents** with the Task/Agent tool — not by
dispatching to an outside model.

## Files

| File | Purpose |
|---|---|
| `models.json` | **Canonical registry** — the ONE source of truth for the three Claude models (`role · backend · status · summary` + UI fields). Consumers DERIVE from it. |
| `models_registry.py` | Stdlib loader for `models.json`. Import from here (`role_map`, `claude_ids`, `known_ids`, `status_map`, `seats`) — never hand-copy model facts. |
| `arsenal_usage.py` | Best-effort per-model usage logger → `usage-log.jsonl` (feeds the dashboard's `/api/arsenal`). |
| `doctor.py` | Health-check: parses `models.json` (asserts every model is Claude-backed) and `.mcp.json`. `--json` for machine output. |
| `ultra_brainstorm.py` | Deprecated. Ultra-brainstorming now runs as parallel Claude subagents; the script only prints that explanation. |
| `install.sh` | Installs a member + skills (and optionally hooks + the Claude-only arsenal + `.mcp.json`) into a target project. See tiers below. |
| `models/` | Per-model docs — one md each for opus/sonnet/haiku. [Index](models/README.md). |
| `supabase.py` | Read-only Supabase helper (SELECT/WITH only) for scripts that need to read the DB. |

## Canonical registry — `models.json`

**[`models.json`](models.json) is the ONE source of truth** for per-model facts.
Everything else DERIVES from it — `models_registry.py`, `conformity_check.py`
(roles), `serve.cjs` (dashboard), `build.py` (guild-data), and the per-model docs
under [`models/`](models/README.md). **Edit the registry, never hand-copy** into
those consumers.

The registry also carries the role `seats` block: `brain.default` is the model a
member runs on unless its own `model:` frontmatter or a `memberOverrides` entry
says otherwise.

## Installer tiers (`install.sh`)

```
./star-alliance-arsenal/install.sh <member-name> <target-project-path> [--tier 1|2|3]
```

- **Tier 1** (default) — syncs the member's skills into the target's `.claude/skills/`.
- **Tier 2** — Tier 1 + the member agent file + `STAR_ALLIANCE_ROOT` in the target's `settings.json`.
- **Tier 3** — Tier 2 + hooks + hook wiring + `workflows.json` + the full agent
  roster + the Claude-only arsenal + `.mcp.json`, so the target runs the guild as
  an MCP server. Self-contained.

## Dashboard

The Arsenal page in the dashboard reads this folder: `serve.cjs`'s `/api/arsenal`
reads `usage-log.jsonl`, and the model cards render from `models.json`.
