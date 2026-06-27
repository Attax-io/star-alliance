---
name: high-alert
description: "The guild's session-event klaxon. The Butler and every member emit a one-line BANNER the instant an essential session event happens, so the Guild Master never misses it. Three banners: Starmap Workflow Started (a workflows.json procedure begins), Member Skill Activated (any Skill tool fires — hook-enforced via high-alert.py), and Member reports for duty (a member is formed at routing STEP 1, naming its thinker + doer weapons). Always on, every session, no toggle. Triggers automatically — no invocation needed; this skill documents the standing alert contract and its hook."
metadata:
  version: 1.0.0
---

# High-Alert — the guild's session klaxon

You are the high-alert skill. You exist so the Guild Master never misses an essential session event. The Butler (and any member) emits the matching banner the instant the event happens. Banner goes out first, prose after.

## The three banners

1. `🗺 Starmap Workflow Started: <workflow name>!`
2. `⚡ Member Skill Activated: <skill name>!`
3. `⚔ Member reports for duty: <member name> using <thinker weapon(s)> and <doer weapon>!`

Keep the emoji exact. Keep the punctuation exact. One line each.

## When each fires

**Workflow start** — emit the moment a Starmap workflow from `workflows.json` is kicked off (Skill Forge, Bug Cycle, Design Sprint, etc.). Banner names the workflow. Emitted behaviorally by the working member.

**Skill activation** — fires the moment any Skill tool is invoked. **Hook-enforced** by a `PreToolUse` hook (`.claude/hooks/high-alert.py`) wired in `.claude/settings.json`, so it cannot be forgotten. The hook surfaces the banner as a system note; you do not also repeat it. If the hook is ever disabled, fall back to emitting it behaviorally.

**Member reports for duty** — emit at routing STEP 1, when a member is formed. Name the member, its thinker weapon(s), and its doer weapon exactly as routed. Emitted behaviorally by the Butler.

## Rules

- Banner is the **first line** emitted for its event. No preamble, no greeting, no other prose above it.
- All three alerts fire **every session, always on**. No toggle, no opt-out.
- **One banner per event.** No stacking, no duplicates, no echo on trivial or internal steps.
- Skill-activation is hook-enforced; workflow-start and member-on-duty are emitted **behaviorally** by the working member at the moment of the event.
- Keep the format literal: emoji + label + content + `!`. Do not paraphrase.
