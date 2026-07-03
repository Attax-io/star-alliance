---
type: Document
timestamp: 2026-07-02T12:28:13Z
---

# Star Alliance

A guild of AI agents — Claude-only. The Butler is the active session persona the
Guild Master talks to; every other member is a Claude specialist the session
routes to, and larger jobs fan out into Claude **subagents** (via the Task tool).
Each member is defined as a `.md` file in this project directory. The guild is
also published as an MCP server that other projects can draw skills and members
from.

## Structure

```
star-alliance/
├── AGENTS.md                ← guild charter
├── IDEA.md                  ← this file
├── the-butler.md            ← the Butler's identity (the voice the Guild Master talks to)
├── star-alliance-members/   ← source-of-truth member definitions
│   ├── the-architect.md
│   ├── the-developer.md
│   ├── the-designer.md
│   ├── the-strategist.md
│   ├── the-interpreter.md
│   ├── the-herald.md
│   ├── the-merchant.md
│   ├── the-steward.md
│   └── the-quartermaster.md
├── star-alliance-skills/    ← guild skills
├── workflows.json           ← the routing star map
├── server/                  ← MCP server (serves skills + members to other projects)
├── guild/                   ← guild Python scripts
├── tools/                   ← build and utility scripts
├── evolution/               ← autonomous skill evolution engine
├── data/                    ← guild data files
└── state/                   ← runtime state
```

## The Roster

Every member is a single Claude model. The Architect runs as **opus**; the
Quartermaster runs as **haiku**; every other member runs as **sonnet**. There is
no second worker behind a member — the same Claude mind that thinks does the work,
and spawns Claude subagents when a job needs many hands at once.

| Member | File | Role | Model |
|---|---|---|---|
| The Butler | `the-butler.md` | Orchestrator — intake, voice, approval, report | Claude |
| The Strategist | `star-alliance-members/the-strategist.md` | Router — decides who handles what | Claude (opus) |
| The Architect | `star-alliance-members/the-architect.md` | Systems design, domain modeling, databases | Claude (opus) |
| The Developer | `star-alliance-members/the-developer.md` | Code, bugs, implementation, dev servers | Claude (sonnet) |
| The Designer | `star-alliance-members/the-designer.md` | UI/UX, visual quality, brand kits | Claude (sonnet) |
| The Interpreter | `star-alliance-members/the-interpreter.md` | Legal codex, law translation, locales | Claude (sonnet) |
| The Herald | `star-alliance-members/the-herald.md` | Marketing, growth, demand generation | Claude (sonnet) |
| The Merchant | `star-alliance-members/the-merchant.md` | Investment analysis, trading, markets | Claude (sonnet) |
| The Steward | `star-alliance-members/the-steward.md` | Customer service, support triage, relationships | Claude (sonnet) |
| The Quartermaster | `star-alliance-members/the-quartermaster.md` | Skills, syncing, conformance | Claude (haiku) |

## How it works

The Guild Master talks to the Butler — the active Claude session persona. The
Butler restates the order, hands it to the Strategist, and the Strategist scans
**`workflows.json`** (the routing star map) to match the request's shape to a
named workflow — each declaring its members, arrangement, and gates. If no
workflow fits, the Strategist forms a candidate and the Quartermaster's Workflow
Forge crystallizes it.

Each specialist runs as a Claude subagent: its own isolated conversation and tool
context. When a job is big enough to need several helpers at once, the session
fans out multiple Claude subagents in parallel, then reviews and integrates their
returns. The Butler tracks the work through its **gates**. The one hard gate left
is the destructive-command gate (`.claude/hooks/destructive-gate.py`) that blocks
irreversible shell and SQL commands; the rest of the old blocking gates are
retired to non-blocking reminders and loggers.

Members wield skills from `star-alliance-skills/` (referenced by name in each
member's frontmatter). The guild's MCP server (`server/`) serves those skills and
members to other projects. The **evolution engine** (`evolution/`) runs a closed
SENSE → DIAGNOSE → CHANGE → VERIFY → REMEMBER loop that improves skills — every
change earns an independent review and a fitness score before it sticks.

The Butler reports the result back to the Guild Master in plain English.