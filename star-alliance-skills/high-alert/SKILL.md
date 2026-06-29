---
name: high-alert
description: "The guild's deployment brief. The Butler (the voice persona) opens every working turn with a short, professional, plain-English brief so the Guild Master always knows what is running: the workflow, which agents are deployed, how many, and each agent's model slots. One planning slot is always shown; execution and critic slots appear only when a doer call or critic gate actually fired — never a placeholder. Always report the model that truly answered this turn, never stamp a template. Three announcements: the Workflow line names the workflows.json procedure that begins, the Skill line names any Skill tool that fires (hook-enforced via high-alert.py), and the Agent-deployed line names the member dispatched and its model. Always on, every session, no toggle. Triggers automatically — this skill documents the standing announcement contract and its hook."
metadata:
  version: 2.4.0
type: Skill

---
# High-Alert — the guild's deployment brief

You exist so the Guild Master always knows what is running — in clean, professional, plain language. The Butler opens every working turn with a short deployment brief, then proceeds. Brief first, prose after. No insider jargon, no game-y wording, no clutter.

## The deployment brief (open every working turn)

```
▸ Workflow — <workflow name>
Deploying <N> agents:
  • The <Member> — <planning model> (planning)
  • The <Member> — <planning model> (planning) [· <doer model> (execution)] [· <critic model> (critic)]
```

- The **`▸ Workflow — <name>`** line is mandatory — it names a real `workflows.json` entry and is the gate key (no workflow line → tools are blocked).
- List **one bullet per agent** the workflow deploys. Keep the **`<N>` count** accurate.
- **Model slots — transparency rule (three slots, conditional)**: report only what actually ran this turn. Never stamp a template — a slot naming a model that did not run is a hallucination, not a formality.
  - **planning (brain)** — always present. On a Butler voice-only turn, the session model that actually answered this turn (for example Opus). On a dispatched-specialist turn, the member Hermes profile brain — its DEFAULT seat chain — name the model that actually answered if known, otherwise say profile-default rather than guessing. Do NOT pin a specific model.
  - **execution (doer)** — name the doer model ONLY if a doer call actually ran this turn. Otherwise omit the slot entirely. Do not write a placeholder doer.
  - **critic** — name the critic model ONLY if the verify or critic gate actually fired this turn. Otherwise omit the slot entirely. Do not hardcode any critic model.
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

## Who chooses the workflow (the banner contract)

The deployment brief names ONE workflow — the one actually running this turn. Three roles, three jobs, no swaps:

- **The Butler** opens the *Routing* intake banner on every intake turn. He does not pick the real workflow — he voices, translates, holds the approval gate, and reports.
- **The Strategist** picks the real workflow. He reads the cleared brief, selects the right entry from `workflows.json` (Quick Fix · Standard Mission · Architecture Build · Design Sprint · Legal Codex · Market Recon · Skill Forge · …), and the turn continues under that banner. If none fits, the Strategist opens *Workflow Forge* — not the Butler.
- **The Guild Master** approves. The Butler restates; the Strategist chooses; the Guild Master says go.

So: Butler voices, Strategist picks, Guild Master approves. The division is fixed.

## Changelog

- **2.4.0** — Truthfulness fix: the brief now reports only models that actually ran this turn. The agent line shows ONE planning slot always; execution and critic slots are conditional and appear only when a doer call or critic gate truly fired (brackets in the template mark them as optional). The brain slot reports the profile default that answered (voice-only → session model; dispatched specialist → the member Hermes profile brain seat) instead of pinning a specific model. A slot naming a model that did not run is a hallucination — never stamp a template.
- **2.3.0** — Transparency fix: replaced ALWAYS minimax-m3 / ALWAYS glm-5.2 with when-invoked / none-if-not-called language. Model slots now reflect what actually ran. Aligns with the transparency rule in CLAUDE.md.
- **2.2.0** — Added the "Who chooses the workflow (the banner contract)" section: **the Butler OPENS Routing on intake; the Strategist PICKS the real lane; the Guild Master APPROVES.** The Butler never selects the actual workflow from `workflows.json` — that is the Strategist's job. Routing exists as the universal intake banner so workflow-gate always has a valid key while the Strategist is still deciding.
- **2.1.0** — Brief gains a third model slot: the **critic** (`glm-5.2`) is now shown for every agent. Execution is pinned to the `minimax-m3` doer. Both fixed slots are mechanically enforced at turn-end by `workflow-banner-enforcer.py` (a brief with a wrong execution/critic slot is bounced back). Planning stays the live thinker. Reflects the uniform Sonnet-thinker / MiniMax-doer / GLM-critic loadout.
- **2.0.1** — Rephrased the `description:` frontmatter to remove angle-bracket placeholders (Agent Skills validator rejects `<`/`>`); restored Cowork-installability. No behavior change.
- **2.0.0** — Deployment-brief format: workflow line, agent list with models, two auto-announcements.
