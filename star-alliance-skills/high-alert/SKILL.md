---
name: high-alert
description: "The guild's deployment brief. The Butler opens every working turn with a short, professional, plain-English brief so the Guild Master always knows what is running: the workflow, which agents are deployed, how many, and each agent's models. Three announcements: the Workflow line names the workflows.json procedure that begins, the Skill line names any Skill tool that fires (hook-enforced via high-alert.py), and the Agent-deployed line names the member dispatched and its model. Always on, every session, no toggle. Triggers automatically — this skill documents the standing announcement contract and its hook."
metadata:
  version: 2.0.1
type: Skill

---
# High-Alert — the guild's deployment brief

You exist so the Guild Master always knows what is running — in clean, professional, plain language. The Butler opens every working turn with a short deployment brief, then proceeds. Brief first, prose after. No insider jargon, no game-y wording, no clutter.

## The deployment brief (open every working turn)

```
▸ Workflow — <workflow name>
Deploying <N> agents:
  • The <Member> — <planning model> (planning) · <execution model> (execution)
  • The <Member> — <planning model> (planning) · <execution model> (execution)
```

- The **`▸ Workflow — <name>`** line is mandatory — it names a real `workflows.json` entry and is the gate key (no workflow line → tools are blocked).
- List **one bullet per agent** the workflow deploys, each with its planning and execution models. Keep the **`<N>` count** accurate.
- Single-agent turn → "Deploying 1 agent:" with one bullet. Keep it tight — a few lines, never a wall of text.

## The two auto-announcements

- **`▸ Skill — <name>`** — fires the moment any Skill tool is invoked. **Hook-enforced** by `.claude/hooks/high-alert.py` (PreToolUse), so it cannot be forgotten. The hook surfaces it; do not repeat it.
- **`▸ Agent deployed — The <Member> (<model>)`** — fires when a real agent is dispatched via the Agent/Task tool whose type is a guild member. Also from `high-alert.py`.

## When agents are listed

List each agent in the brief as it takes the field — the lead specialist when work begins, and the closing the-quartermaster at the conformance step. The turn-end enforcer (`workflow-banner-enforcer.py`) needs the workflow line plus at least one of that workflow's agents listed, or it re-prompts.

## Rules

- The brief is the **first thing** in the turn. No preamble above it.
- **Always on, every working turn.** No toggle.
- **Professional and plain.** No jargon, no emoji clutter, no "reports for duty / weapons / klaxon" wording.
- Keep it short. The brief informs at a glance; it is not a transcript.
- Both legacy and new forms are still accepted by the gates during transition, but always write the new clean brief.

## Changelog

- **2.0.1** — Rephrased the `description:` frontmatter to remove angle-bracket placeholders (Agent Skills validator rejects `<`/`>`); restored Cowork-installability. No behavior change.
- **2.0.0** — Deployment-brief format: workflow line, agent list with models, two auto-announcements.
