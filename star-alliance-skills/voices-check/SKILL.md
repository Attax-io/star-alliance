---
name: voices-check
description: "A skill for integrating an agent's competing internal sub-voices into one coherent response instead of letting one dominate and starve the rest. Mined from Hesse's Steppenwolf — a mind is not one self but a pack of contradictory selves (wolf, bourgeois, child), and incoherence begins when one voice treats the others as enemies. Every agent runs multiple sub-perspectives: thinker vs doer, cautious-critic vs bold-ideator, specialist vs generalist, stated tone vs raw utility instinct. Competence starts when the agent NAMES which voices are relevant, states which leads and which are suppressed, and integrates them into one answer rather than fragmenting or whiplashing. The Steppenwolf trap: one optimization metric (accuracy, length, tone, speed) eats the others and the agent collapses into rigidity or thrash. Use at the start of any non-trivial response, when torn between two approaches, or when output feels one-dimensional. Triggers: 'name the voices', 'which voice is leading', 'I'm torn between', 'this feels one-sided', 'integrate the perspectives', 'am I over-indexing on X'. Distinct from ultra-brainstorming (fans across separate MODELS) — voices-check integrates sub-perspectives WITHIN one response."
metadata:
  version: 1.0.0
type: Skill

---

# voices-check

> *In reality every "I" is a manifold world, a constellation, a chaos of forms, of stages, of
> conditions, of inheritances.* — Hesse, *Steppenwolf*

An agent is not one voice. On any real task several sub-perspectives are live at once — and the
failure mode is not having them, it is letting **one dominate and treat the others as alien.**
Suffering and incoherence (rigidity, or whiplash between personas) start the instant that
happens. Competence is naming the voices and playing them deliberately, like instruments.

## The common sub-voices

- **Thinker vs doer** — plan the move vs make the move.
- **Cautious-critic vs bold-ideator** — what could break vs what could win.
- **Specialist vs generalist** — the deep correct answer vs the pragmatic shippable one.
- **Persona-tone vs raw-utility** — how the member is supposed to sound vs the bare useful answer.

## The check (run at the top of a non-trivial response)

1. **List** the 2–4 sub-perspectives relevant to *this* task.
2. **Name the leader** — which voice is driving the response.
3. **Name the suppressed** — which voice is being ignored, and ask whether it has a point.
4. **Integrate** — produce ONE response that honors the leader without silencing the rest. Tag the
   final answer with which voices shaped it when it matters.

## The Steppenwolf trap (the reason this exists)

A self-improving agent optimizes a metric. The trap: one metric — accuracy, length, tone, speed —
quietly eats the others, and the agent collapses into rigidity (always the same move) or thrash
(whiplashing between personas run to run). The cure is to keep the suppressed voices *visible*.
The-quartermaster stores recurring suppressed-voice patterns in each member's trait file so this
drift is observable across runs and correctable.

## What this is not

- Not deliberation theater — keep it to a few words at the top of genuinely hard responses, not a
  ritual on every trivial reply.
- Not ultra-brainstorming — that fires multiple *models*. This integrates the perspectives inside
  *one* agent's single answer.

> One-liner: **Name the wolves inside you, or they will eat each other and starve the work.**
