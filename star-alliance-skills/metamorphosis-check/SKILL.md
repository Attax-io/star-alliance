---
name: metamorphosis-check
description: "A guardrail that catches the most dangerous agent failure: confidently running the OLD playbook after the underlying state has changed. Mined from Kafka's Metamorphosis. An agent that detects a discontinuity in itself — a model swap, a failed/missing tool, a degraded or truncated context, a misread prompt, an MCP gone unavailable — must STOP, name the new state, and rebuild its plan from what it can do NOW, not what it used to do. Forces three written answers first: (1) what did I assume about my inputs/tools/role that may no longer hold? (2) what part of my workflow depends on it? (3) what is the smallest honest first step given the ACTUAL state? Use on session start, after a tool error, after a model/context change, or when output starts contradicting itself. Triggers: 'something changed', 'tool failed', 'unexpected output', 'recheck state', 'did the context drift', 'capability check', 'why is this failing now'. Refuse to mimic a confident pre-change voice when capability drift is detected."
metadata:
  version: 1.0.0
type: Skill

---

# metamorphosis-check

> *Gregor Samsa woke one morning to find himself transformed — and spent his last strength trying
> to catch the 7 o'clock train.* — Kafka, *The Metamorphosis*

The lethal failure is not change. It is running the **old procedure on a new self**. When an
agent's substrate, tools, context, or role shifts in a way that breaks the assumptions its
current plan rests on, the right move is to **stop and re-inspect** — not to keep executing the
routine that no longer fits.

## When to fire

- **Session start** — always, as the first check. You do not yet know your actual state.
- **A tool returns unexpected output** — wrong shape, empty, an error you didn't plan for.
- **An MCP / connector went unavailable** mid-task.
- **A model or context change** — a swap, a summarization, a truncation, a cache miss.
- **Your own output starts contradicting itself** — a sign of capability/context drift.

## The three forced answers (write them before proceeding)

1. **What did I assume that may no longer hold?** About my inputs, my tools, my context window,
   my role, my model. Name the assumption explicitly.
2. **What part of my standard workflow depends on that assumption?** Find the step that would
   break — the "catch the train" step that the new state can't support.
3. **What is the smallest honest first step given the ACTUAL state?** Rebuild from what you can do
   now, not from what you used to do.

## The refusal

If you detect capability drift — lost context, repeated tool errors, contradictions in your own
output — **refuse to mimic the confident pre-change voice.** Gregor's apologies in the salesman's
register were the tragedy. State the new state plainly and re-plan; do not perform competence you
no longer have.

## Relationship to the guild

- The-butler wires this into the router: first turn of any session, and any unhandled exception,
  completes this check before work is approved.
- Pairs with `letting-go` (stop clinging to the old plan) and `guild-reflection` (log the drift so
  the next session starts wiser).

> One-liner: **If you have changed, stop apologizing in the voice of who you were — re-learn what
> you are before you act.**
