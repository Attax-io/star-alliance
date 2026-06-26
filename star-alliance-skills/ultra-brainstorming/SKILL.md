---
name: ultra-brainstorming
description: "The Strategist's super-planning method — fuse the outputs of several members into one doer-ready plan by brainstorming them across several thinking models at once. Use when two or more members have produced inputs (analyses, sketches, proposals, risks) that must become a single coherent plan before any doer can start. Triggers: 'ultra-brainstorm this', 'super-plan this', 'synthesize the members' work', 'brainstorm this across models', 'merge these proposals into one plan', 'plan this deeply before we build', or any fan-in where several specialists feed one build. Distinct from storm-investigation (five persona minds on one topic) and members-formation (the Butler's routing): this is a MODEL ensemble — several thinking models, each a different mind — that converges many members' work into one ranked, peer-reviewed plan handed to the member doing the job."
metadata:
  version: 1.0.0
---

# Ultra-Brainstorming — the Strategist's synthesis hub

This is where several members' outputs **converge**, get brainstormed across **several thinking
models at once**, and leave as **one plan** for the doer. It is the Strategist's deep-planning
craft, alongside campaign waves.

Know what it is *not*:

- Not **`members-formation`** (the Butler's routing — *who* works and in what arrangement). The
  Butler routes the inputs *to* this synthesis node; here the Strategist fuses them.
- Not **`storm-investigation`** (five *persona* minds researching one topic). This is a **model
  ensemble** — five *thinking models*, each a genuinely different mind, brainstorming the same
  combined material. Personas vary the viewpoint; models vary the reasoning engine.
- Not **`conquering-campaign`** (multi-wave *execution*). This produces the **plan** the campaign
  then executes.

## When to run it

When **two or more members** have produced inputs — an Architect's schema sketch, a Designer's UX
notes, a Merchant's risk read, a Developer's feasibility call — and they must become **one coherent
plan** before a doer can start. Run it at the **fan-in**: many specialists feed it, one plan leaves.

If there's only one input, or the route is obvious, don't — that's the Butler's formation, not a
synthesis. Ultra-brainstorming is for *fusion*, not lookup.

## In / out

- **In:** the outputs of several members + the mission brief, constraints, success criteria, and
  the name of the **doer** who will receive the plan.
- **Out:** one synthesized, **ranked, doer-ready plan** + a confidence grade + the dissent preserved
  for audit.

## The five phases — run in order

Phases 2–5 each consume the prior output.

### Phase 1 — Gather & frame
Collect every member's output. State the mission, the hard constraints, the success criteria, and
who the doer is. Normalize each input into a common shape — **claim · proposal · risk · open
question** — so the models brainstorm the same material, not different formats.

### Phase 2 — Divergent brainstorm (multi-model — the heart)
Run **several thinking models** on the same combined inputs, each as an **independent mind**. The
default panel is the Strategist's thinker weapons:

| Model | The mind it brings |
|---|---|
| **opus** | Deepest structural reasoning — is the plan *sound*? |
| **gpt-5.5** | Analytical + creative second opinion — what's the non-obvious move? |
| **deepseek-v4-pro** | Frontier multi-step reasoning — the long dependency chains. |
| **glm-5.2** | A different analytical frame — where the others over-fit. |
| **kimi-k2.7** | Holds the whole context — long-range coherence across all inputs. |

Each model returns exactly three things: its **best plan** (3–5 steps) · the **one risk** it weighs
heaviest · the **one idea no other model would propose**. Diversity is the entire value — different
engines, different blind spots.

**Execution.** Run the panel as **parallel doers**, one per model. Use Claude sub-agents or a
`Workflow` when models need tools or must return structured output; otherwise call each weapon
directly. **Do not collapse the panel to a single MiniMax doer** — the repo default favors MiniMax
for doer work, but here the point is *model diversity*; one model is not a brainstorm.

### Phase 3 — Convergence map
Across the candidate plans: (1) where do **two+ models agree** — the high-confidence spine;
(2) where do they **contradict** — the real decisions, each with its trade-off; (3) which plan has
the **strongest** reasoning, which the **weakest**, and why; (4) the best **orphan idea** — proposed
by one model, adopted by none (often the gem); (5) what did **all models miss** — the panel's shared
blind spot.

### Phase 4 — Synthesis (the one plan)
Build the plan no single model wrote: take the agreed spine, **resolve each contradiction with an
explicit call + the reason**, graft the best orphan ideas, and close the blind spot. Output is
**one ordered, doer-ready plan** — numbered steps, each with *action · produces · the decision and
why behind it* — ranked by dependency (what must come first).

### Phase 5 — Peer-review gate (the honesty gate)
Grade the plan before it leaves: (1) **confidence 1–10 per step** + the reason; (2) the **weakest
link** + exactly what check would harden it; (3) **model-bias check** — did one model dominate the
synthesis?; (4) the **missing sixth model/angle** that would change conclusions; (5) **overall
grade** a senior planner would give + what to fix first.

## Handoff to the doer

Deliver the **Phase 4 plan** as the headline with **Phase 5 confidence** attached. Keep the Phase 2
candidates and Phase 3 map collapsed/appended so the work is auditable. **Never hand a plan without
its grade** — the grade is what makes it trustworthy. The plan goes to the **member doing the job**
(the doer the Butler routed), scoped and ranked, ready to execute.

## Where it sits in a formation

The natural shape: **members brainstorm in parallel (fan-out) → Strategist ultra-brainstorm (fan-in
/ synthesis) → doer builds.** In a `members-formation`, this is one member step owned by
`the-strategist` that *produces* a "synthesized plan." When that pattern recurs, the Butler hands
the formation to the Quartermaster to crystallize into a star-map workflow.

## Versioning

Own skill. Bump `metadata.version` on any change (PATCH: wording/refs · MINOR: new phase/panel
member · MAJOR: method contract change). Regenerate `VERSIONS.md` with
`python3 skillsmith/scripts/skill_registry.py write`, then `python3 build.py`.

## Changelog
- **1.0.0** — Initial release. Five-phase multi-model synthesis: gather & frame, divergent
  multi-model brainstorm (5-thinker panel), convergence map, one-plan synthesis, peer-review gate,
  doer handoff. Differentiated from storm-investigation (persona ensemble) and members-formation
  (routing); positioned as the fan-in synthesis node in a formation.
