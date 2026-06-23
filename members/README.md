# Guild Members

Each member is a Claude Code agent definition — a markdown file with a system prompt and a curated list of skills from the shared pool at the repo root.

## Member file format

```markdown
# .claude/agents/<name>.md
---
name: <member-name>
description: <when to deploy this member>
model: sonnet
tools: [Read, Edit, Write, Bash]
skills: [skill-a, skill-b, skill-c]
---

You are <member-name>, a <role> in the Star Alliance.

<system prompt — personality, expertise, workflow style>
```

## Fields

| Field | Required | Description |
|---|---|---|
| `name` | yes | Kebab-case member name (e.g. `the-architect`) |
| `description` | yes | When to deploy this member (trigger phrase) |
| `model` | no | Claude model: `sonnet`, `opus`, `haiku` (default: `sonnet`) |
| `tools` | no | Allowed Claude Code tools (default: all) |
| `skills` | yes | List of skill names from the repo root this member can use |

## How members get deployed

1. Copy the member's `.md` file into your project's `.claude/agents/` directory
2. Install the member's skills into `~/.claude/skills/` (via `skillsmith sync` or manually)
3. Invoke the member in Claude Code: `@<member-name> <task>`

## Shared vs unique skills

- **Shared skills** appear in multiple members' `skills` lists (e.g. `cleanup`, `supabase`)
- **Unique skills** appear in only one member's list (e.g. `conquering-campaign` for the strategist)
- All skills live at the repo root — members just reference them by name

## Current roster

See `../README.md` for the full guild roster.