---
type: Index
title: Star Alliance Arsenal
description: The guild's Claude-only model registry (opus/sonnet/haiku) and support tools.
timestamp: 2026-07-03T00:00:00Z
---

# Star Alliance Arsenal

The guild's Claude-only model registry (opus / sonnet / haiku) and support tools.
The Star Alliance runs entirely on Claude and is exposed to projects as an MCP
server — there is no external doer or non-Claude bench layer.

## Contents

<!-- okf:generated-contents:start -->
- `models/` — folder (per-model docs: opus, sonnet, haiku)
- `arsenal_usage.py` — file (per-model usage logger)
- `doctor.py` — file (registry + MCP health-check)
- `index.md` — file
- `install.sh` — file (member/skills/arsenal installer)
- `models-usage.json` — file
- `models.json` — file (canonical registry — single source of truth)
- `models_registry.py` — file (stdlib loader for models.json)
- `README.md` — file
- `supabase.py` — file (read-only Supabase helper)
- `ultra_brainstorm.py` — file (deprecated; brainstorming is now parallel Claude subagents)
- `usage-log.jsonl` — file
- `workflows-lite.json` — file
<!-- okf:generated-contents:end -->
