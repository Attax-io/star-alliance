---
type: Document
timestamp: 2026-07-02T12:28:13Z
---

# Star Alliance — Hermes

A guild of AI agents. The Butler is the single Hermes profile the Guild Master
talks to; every other agent is a specialist dispatched as a subagent via
`delegate_task`. Each agent is defined as a `.md` file in this project directory
— not a separate Hermes profile.

## Structure

```
star-alliance-hermes/
├── AGENTS.md                ← guild charter; auto-loaded by Hermes
├── IDEA.md                  ← this file
├── the-butler.md            ← the Butler's identity (the voice the Guild Master talks to)
├── agents/                  ← source-of-truth agent definitions
│   ├── the-architect.md
│   ├── the-developer.md
│   ├── the-designer.md
│   ├── the-strategist.md
│   ├── the-interpreter.md
│   ├── the-herald.md
│   ├── the-merchant.md
│   └── the-quartermaster.md
├── star-alliance-skills/    ← 94 guild skills
├── star-alliance-arsenal/   ← model registry + summon scripts
├── workflows.json           ← the routing star map
├── server/                  ← MCP gate server
├── guild/                   ← guild Python scripts
├── tools/                   ← build and utility scripts
├── evolution/               ← autonomous skill evolution engine
├── data/                    ← guild data files
└── state/                   ← runtime state
```

## The Roster

| Agent | File | Role | Model seat |
|---|---|---|---|
| The Butler | `the-butler.md` | Orchestrator — intake, voice, approval, report | Thinker (GLM-5.2) |
| The Strategist | `agents/the-strategist.md` | Router — decides who handles what | Thinker (GLM-5.2) |
| The Architect | `agents/the-architect.md` | Systems design, domain modeling, databases | Thinker (GLM-5.2) |
| The Developer | `agents/the-developer.md` | Code, bugs, implementation, dev servers | Thinker (GLM-5.2) + Doer (MiniMax M3) |
| The Designer | `agents/the-designer.md` | UI/UX, visual quality, brand kits | Thinker (GLM-5.2) + Doer (MiniMax M3) |
| The Interpreter | `agents/the-interpreter.md` | Legal codex, law translation, locales | Thinker (GLM-5.2) + Doer (MiniMax M3) |
| The Herald | `agents/the-herald.md` | Marketing, growth, demand generation | Thinker (GLM-5.2) + Doer (MiniMax M3) |
| The Merchant | `agents/the-merchant.md` | Investment analysis, trading, markets | Thinker (GLM-5.2) + Doer (MiniMax M3) |
| The Quartermaster | `agents/the-quartermaster.md` | Skills, syncing, conformance | Thinker (GLM-5.2) |

**Model assignment:** Thinker (Brain) = GLM-5.2 · Doer = MiniMax M3 · Critic = Kimi K2.7.
Claude models remain in the arsenal as reserve, never as default seats.

## How it works

The Guild Master talks to the Butler — the single Hermes profile in this project.
The Butler restates the order, hands it to the Strategist, and the Strategist
scans **`workflows.json`** (the routing star map) to match the request's shape to
a named workflow — each declaring its agents, arrangement, and gates. If no
workflow fits, the Strategist forms a candidate and the Quartermaster's Workflow
Forge crystallizes it.

Each specialist is dispatched via `delegate_task` as a subagent: its own isolated
conversation, terminal session, and tool context — but not a separate Hermes
profile. The Butler tracks the work through its **gates**, which run automatically as
Claude Code hook scripts (`.claude/hooks/*.py`, on `PreToolUse` and `Stop`) — the
verify-gate (runs the Critic on the diff), the destructive-command gate, and the
delegation gate fire at the right points in the loop with no explicit call. The
guild's one MCP server, `mcp/server.py`, exposes the roster (`list_skills`,
`list_agents`, `invoke_skill`, `dispatch_agent`) — it is not a gate server.

Agents draw weapons (models) from the **arsenal** (`star-alliance-arsenal/`) via
`summon.py`, and wield skills from `star-alliance-skills/` (94 guild skills,
referenced by name in each agent's frontmatter). The **evolution engine**
(`evolution/`) runs a closed SENSE → DIAGNOSE → CHANGE → VERIFY → REMEMBER loop
that autonomously improves skills — every change gets an independent Critic
verdict (Kimi K2.7) and a fitness score before it sticks.

The Butler reports the result back to the Guild Master in plain English.