---
type: Document
timestamp: 2026-07-02T12:28:13Z
---

# Star Alliance — Hermes Agent

> A guild of AI agents. The Butler is the voice; the Strategist is the router;
> the specialists do the craft. This file is auto-loaded by Hermes when running
> in this directory.

## How the guild works

```
Guild Master  ←→  Butler (voice/intake/approval/report)
                    ↓ delegate_task
                Strategist (the ROUTER — decides who handles what)
                    ↓ delegate_task
                [Architect | Developer | Designer | Interpreter | Herald | Merchant | Quartermaster]
```

- **The Butler** is the only agent who speaks to the Guild Master directly. He
  restates the order, hands it to the Strategist, tracks the gates, and reports
  the result in plain English.
- **The Strategist** is the router. He decides which specialist(s) handle the work
  and in what sequence. The Butler never picks specialists.
- **Specialists** (Architect, Developer, Designer, Interpreter, Herald, Merchant,
  Quartermaster) do the craft. Each is dispatched via `delegate_task` with a
  self-contained goal and context.

## The roster

| Agent | File | Role |
|---|---|---|
| The Butler | `the-butler.md` | Orchestrator — intake, voice, approval, report |
| The Strategist | `agents/the-strategist.md` | Router — decides who handles what; campaign commander |
| The Architect | `agents/the-architect.md` | Systems design, domain modeling, database architecture |
| The Developer | `agents/the-developer.md` | Writing code, fixing bugs, implementation, dev servers |
| The Designer | `agents/the-designer.md` | UI/UX design, visual quality, brand kits, image-to-code |
| The Interpreter | `agents/the-interpreter.md` | Legal codex, law translation, multi-locale content |
| The Herald | `agents/the-herald.md` | Marketing, growth, demand generation, content/SEO |
| The Merchant | `agents/the-merchant.md` | Investment analysis, trading strategies, market research |
| The Quartermaster | `agents/the-quartermaster.md` | Skill management, syncing, upgrading, conformance |

## Model assignment

Two role seats, each with a default model and fallback chain (defined in
`star-alliance-arsenal/models.json`):

| Seat | Default | Fallback | Duty |
|---|---|---|---|
| **Brain** | the member's model (Opus / Sonnet / Haiku) — **Claude** | the Claude brain family | Plans, reviews, owns the standard, wields tools |
| **Doer** | minimax-sub — **Hermes profile** | minimax-payg | Executes the plan, returns work as text. No tools |

**Claude is the Brain; Hermes is the Doer.** A non-Claude model never thinks
or orchestrates; a Claude model is never a doer seat. This is enforced
mechanically by `tools/conformity_check.py`.

Non-Claude models (minimax-sub, minimax-payg) are the Doer seat's default and
fallback; `models.json` is the source of truth for the current roster. A guild
agent's `model:` frontmatter overrides the brain default.

## Arsenal

`star-alliance-arsenal/` holds the model registry and runner scripts — the
guild's armory. The primary path for doer-grade work is `tools/dispatch.py`
(→ Hermes profile); `summon.py` and `minimax.py` are the underlying runners /
fallback when Hermes is unreachable:

```
python3 tools/dispatch.py the-developer "Explain quicksort."
python3 star-alliance-arsenal/minimax.py "Solve: 17 * 23" --json   # fallback
```

The registry (`models.json`) is the one source of truth for per-weapon facts —
roles, backends, status, fallback chains. `doctor.py` is the connectivity
health-check.

## The three-layer architecture (Claude → dispatch → Hermes profiles)

This repo is the **source of truth** for both Claude Code and Hermes Agent. The
two surfaces are separate but share the same repo:

- **`CLAUDE.md`** — auto-loaded by Claude Code. Describes the Claude-side
  orchestration: the Butler, the Strategist, the hooks, the dispatch bridge.
- **`AGENTS.md`** (this file) — auto-loaded by Hermes Agent. Describes the
  Hermes-side guild: the profiles, the gates.

### How the layers connect

```
Layer 1: Claude Butler (runs as Claude model — Opus/Sonnet)
    ↓ delegates to
Layer 2: Claude subagents (Brain = Claude; Strategist + specialists, also Claude models)
    ↓ hooks force dispatch through tools/dispatch.py →
Layer 3: Hermes profiles (Doer = minimax-sub)
```

**Claude is the Brain; Hermes is the Doer.** Claude models plan, review, wield
tools, and hold the gates. Hermes profiles execute bulk work — large edits,
generation, mechanical transforms — and return text. The two sides share
`tools/dispatch.py` (byte-identical in both repos) and the `profiles/`
directory (the Hermes profile distributions).

### Model seats — Hermes side only

The Brain / Doer seats are defined per-profile in `profiles/<agent>/config.yaml`,
with defaults drawn from `star-alliance-arsenal/models.json`:

| Seat | Default Model | Fallback | Role |
|---|---|---|---|
| **Brain** | the member's model (Opus / Sonnet / Haiku) | the Claude brain family | Plans, reviews, wields tools |
| **Doer** | minimax-sub | minimax-payg | Executes bulk work, returns text |

Non-Claude models (minimax-sub, minimax-payg) serve the Doer seat only;
`models.json` is the source of truth for the current roster.

### Profile distributions

Each `profiles/<agent>/` directory is a Hermes profile distribution with:
- `SOUL.md` — the agent's system prompt
- `config.yaml` — model and provider settings
- `distribution.yaml` — Hermes distribution manifest (name, version, source)
- `skills.yaml` — skills manifest (which skills belong to this profile)

Install: `python3 tools/publish_profiles.py`
Update after changes: `python3 tools/publish_profiles.py --update`

The conformity check (`tools/conformity_check.py`) includes a `PD` tag that
verifies repo `profiles/<agent>/` matches the installed `~/.hermes/profiles/<slug>/`.

## Workflows

`workflows.json` is the routing star map — the catalog of named, repeatable
campaign shapes the guild runs. Each workflow declares a `when` trigger, the
agents it summons, their arrangement (parallel vs sequential), and where the
gates sit. The **Strategist** scans the star map, matches the request's shape to
a workflow, and picks the best fit. If no workflow fits, the Strategist forms a
candidate formation and the Quartermaster's Workflow Forge crystallizes it.

## Gates (reminders, not walls)

The guild's rules used to be enforced by ~15 blocking hooks under `.claude/hooks/`.
Those are now **retired** (the files remain but are no longer wired in
`.claude/settings.json`) — the doctrine stands, followed by good practice rather
than a hook that can deadlock a turn. The one hard block that remains is
data-safety:

| Hook | Purpose |
|---|---|
| `destructive-gate.py` | **Hard block** — stops irreversible shell and SQL (`rm -rf`, force-push, `reset --hard`, unscoped `DELETE`/`DROP`/`TRUNCATE`) until re-run with `# sa-confirm` |

Still running as **non-blocking** reminders/loggers: routing nudge, plain-English
nudge, guild-log and vault-log nudges, turn-cost, dispatch/spawn/xp loggers, and
`turn-finalize.sh` (auto-commit).

## MCP server

`mcp/server.py` is the guild's one MCP server. It exposes the roster, not gates —
tools: `list_skills`, `list_agents`, `invoke_skill`, `dispatch_agent`.

## Skills

`star-alliance-skills/` holds the guild's 94 skills — each a self-contained
directory with a `SKILL.md`. Agents reference skills by directory name in their
YAML frontmatter `skills:` list. Skills are installed to the active Hermes
profile via the `hermes skills` CLI. The Quartermaster
manages the lifecycle: syncing, upgrading, and forging new skills.

## Evolution engine

`evolution/` is the autonomous self-improvement spine — a closed loop that
ensures every self-modifying change gets independent review and fitness feedback:

```
SENSE ──▶ DIAGNOSE ──▶ CHANGE ──▶ VERIFY ──▶ REMEMBER
ledger     engine       engine     verdict    scoreboard
```

**Invariant:** every self-modifying change lands a ledger event and gets a
verdict before it sticks. Tier-A changes (skills, memory, docs) may be
auto-applied after a pass; Tier-B changes (doctrine, arsenal, workflows) are
always human-gated. A `DISARMED` file is the kill switch. There are two seats
only — Brain (Claude) and Doer (Hermes/MiniMax); there is no separate Critic
seat.

## How to dispatch an agent

When the Butler (or Strategist) needs a specialist, use `delegate_task` with the
agent's goal and context. The subagent gets its own isolated conversation and
terminal session. Only the final summary returns.

```
delegate_task(
  goal="<what the specialist should accomplish>",
  context="<background they need — file paths, constraints, prior decisions>",
  toolsets=["terminal", "file", "web"]  # only the tools they need
)
```

## Plain English to the Guild Master (every agent, every message)

**The Guild Master is not a programmer.** Being understood is as important as
being correct. On every message:

- Speak plain English. No insider jargon, no agent/skill code-names, no version
  numbers unless they truly matter.
- Cover what just happened, what happens next, and what it means for the Guild
  Master. State a big action before doing it.
- Make decisions easy: write each choice as a normal sentence about what it means
  for them, and recommend one.
- Be brief. Lead with the answer; default to a few lines. A long wall of text is
  a failure even if every word is plain.

## Gates

Three gates, three owners:

- **Approval** — the Guild Master approves the brief before work starts.
- **Certify** — the Quartermaster certifies the plan/design is buildable before
  construction.
- **Report** — the Butler reports the finished mission in plain English. Mandatory
  on every mission.

The last specialist before the report is always the Quartermaster, running a
conformance pass. Then the Butler delivers the plain-English report.

## Confusion Protocol

For high-stakes ambiguity (architecture, data model, destructive scope, missing
context), STOP at STEP 0. If a clean one-line restatement of the order can't be
produced, name the confusion in one sentence and present 2–3 options with
trade-offs. Not for routine or obvious changes — only when the cost of a wrong
interpretation is high.

## Failure-mode routing

| Failure mode | Routes to |
|---|---|
| Bug | The Developer |
| Missing spec | The Architect |
| Scope overflow | The Strategist |
| Vague intent | Butler (restate the order) |
| High-stakes ambiguity | HALT / Confusion Protocol |
| No workflow fits | Strategist (form a candidate) |
| Missing role | Guild Recruitment |

A blocked agent declares the failure mode instead of silently retrying the same
blind action.

## Two layers: Claude thinker plans & reviews · Hermes doer executes bulk

- **Thinker** (the member's model — Opus / Sonnet / Haiku) — **Claude**. The
  profile's session model. It owns the loop: plan → prompt the doer → review the
  return → re-prompt until it conforms. All tool-access orchestration stays with
  the thinker.
- **Doer** (minimax-sub) — **Hermes profile**. Bulk work (large edits, extraction,
  generation, mechanical transforms) goes to the doer via `delegate_task` with a
  model override.

Only offload doer-grade bulk (≈1.5k+ tokens of output, or many repetitive
transforms). A small job — the thinker does inline.
