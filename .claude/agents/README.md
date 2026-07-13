---
type: Readme
timestamp: 2026-06-27T10:27:03Z
---

# Guild Members

Each member is a Claude Code agent definition — a markdown file with a system prompt and a curated list of skills from the shared pool at `../star-alliance-skills/`.

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

- **Shared skills** appear in multiple members' `skills` lists (e.g. `supabase`, `dev-server`) —
  allowed only when the skill builds that member's craft
- **`weapon-utility`** is the one universal skill — every member carries it (the
  numeric usage-level meter: every skill, workflow, and member has a level derived
  from append-only invocation logs; surfaces unused craft and load-bearing craft.
  It does NOT select weapons — model selection lives in `star-alliance-arsenal/`.)
- **Unique skills** appear in only one member's list (e.g. `conquering-campaign` for the strategist,
  `cleanup` for the quartermaster — hygiene is his alone)
- All skills live in `../star-alliance-skills/` — members just reference them by name

## Current roster

See `../README.md` for the full guild roster.

## Location

This directory (`star-alliance-members/`) holds the guild roster. It was previously
`members/`, then `star-alliance-agents/`, and renamed to `star-alliance-members/` on
2026-06-26 — every agent definition is unchanged across the renames.