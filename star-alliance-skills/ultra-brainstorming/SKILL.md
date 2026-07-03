---
name: ultra-brainstorming
description: "An ASSIGNABLE multi-thinker method — any member who carries it fires ALL his available Claude models at once on the same material, then his strongest model reviews every output and synthesizes one opinion. Use to deepen one member's thinking across model diversity, or at a fan-in to fuse several members' inputs into one build-ready plan. Triggers: 'ultra-brainstorm this', 'super-plan this', 'think this across all models', 'use all my thinkers', 'synthesize the members' work', 'merge these proposals into one plan', 'plan this deeply before we build'. Distinct from storm-investigation (five persona minds on one topic) and members-formation (the Butler's routing): this is a MODEL ensemble — several thinking models, each a different mind — converging into one ranked, peer-reviewed result. It is the model fan-out exception named in weapon-utility."
metadata:
  version: 1.3.1
type: Skill

---
# Ultra-Brainstorming — the assignable multi-thinker skill

This skill gives **any member who carries it** one extra power: instead of thinking a problem
through in a single pass, the member **fans out several parallel Claude subagents at once** on the
same material — each an independent mind — then **reviews every output and synthesizes one
opinion**. This is exactly the *thinker fan-out exception* named in [[weapon-utility]] — assign
this skill to a member and that member gains it.

It serves two shapes: **deepen one member's own thinking** across reasoning diversity, or sit at a
**fan-in** where several members' outputs **converge** and leave as **one plan** for the builder. The
Strategist carries it for campaign planning, but it rides any member you add it to.

Know what it is *not*:

- Not **`members-formation`** (the Butler's routing — *who* works and in what arrangement). The
  Butler routes the inputs *to* this synthesis node; here the member holding this skill fuses them.
- Not **`storm-investigation`** (five *persona* minds researching one topic). This is a **model
  ensemble** — five *thinking models*, each a genuinely different mind, brainstorming the same
  combined material. Personas vary the viewpoint; models vary the reasoning engine.
- Not **`conquering-campaign`** (multi-wave *execution*). This produces the **plan** the campaign
  then executes. The **builder** below is the member (a Claude subagent) that receives this plan and
  does the work.

## When to run it — MANDATORY for carriers

**Carrying this skill is an obligation, not an option.** If a member carries `ultra-brainstorming`
and the task in front of it is **plan-grade or hard-problem work**, the member **must** fan out its
subagent panel — it may not quietly think it through in a single pass. The skill rides these
carriers today: **the-strategist · the-architect · the-developer · the-herald · the-merchant**.
Each must use it whenever it does the kind of thinking below.

**"Plan-grade / hard-problem work" — the panel is required when the task is any of:**
- planning before a build, refactor, or campaign (sequencing, trade-offs, dependency order)
- architecture or data-model decisions; structural choices with more than one defensible answer
- a **fan-in** — two or more members' outputs (schema sketch · UX notes · risk read) must become
  **one coherent plan** before a builder starts
- risk / investment / go-to-market calls where being wrong is expensive
- anything where the carrier would otherwise reach for its single prime thinker to *decide*, not
  just *look up*

**Two tiers — scale the fire to the stakes (both still count as "using it"):**
- **Quick brainstorm** (the default for everyday hard calls): the panel runs, all five phases run,
  but lightly — short candidates, fast convergence. The point is *more than one mind touched it*.
- **Full panel** (high-stakes — architecture, irreversible scope, multi-member fan-in, money/risk):
  the full five-phase treatment with the parallel subagent fan-out, the convergence map, and the
  peer-review grade.

**The only legitimate skip is a lookup.** Single-input retrieval, a mechanical/obvious change, or a
question with one correct answer is **not** plan-grade work — think it through in a single pass,
that's the Butler's formation. But the skip is **on the record**: a carrier that declines the panel
on something that *looks* plan-grade states the reason in one line — `single-thinker: <why this is a
lookup, not a decision>` — exactly as [[weapon-utility]] requires an exception to be justified out
loud. Silent single-pass thinking on plan-grade work is a conformity failure, not a shortcut.

Ultra-brainstorming is for *fusion across minds*. A member without the skill thinks a problem
through in a single pass; a member **with** it owes the panel on every real decision.

## In / out

- **In:** the outputs of several members + the mission brief, constraints, success criteria, and
  the name of the **builder** (the member) who will receive the plan.
- **Out:** one synthesized, **ranked, build-ready plan** + a confidence grade + the dissent preserved
  for audit.

## The five phases — run in order

Phases 2–5 each consume the prior output.

### Phase 1 — Gather & frame
Collect every member's output. State the mission, the hard constraints, the success criteria, and
who the builder is. Normalize each input into a common shape — **claim · proposal · risk · open
question** — so the subagents brainstorm the same material, not different formats.

### Phase 2 — Divergent brainstorm (parallel subagents — the heart)
Fan out **several parallel Claude subagents** on the same combined inputs, each as an **independent
mind**. Vary the reasoning engine by giving each subagent a different Claude model (`opus`, `sonnet`,
`haiku`) and/or a different framing, so the panel genuinely covers different blind spots. The example
below is the Strategist's; another member composes its own panel:

| Subagent | The mind it brings | How it runs |
|---|---|---|
| **opus** | Deepest structural reasoning — is the plan *sound*? | Task tool, `subagent_type` + `model=opus` |
| **sonnet (frame A)** | Frontier multi-step reasoning — the long dependency chains. | Task tool, `model=sonnet` |
| **sonnet (frame B)** | A different analytical frame — where the others over-fit. | Task tool, `model=sonnet`, contrarian brief |
| **haiku** | Fast, wide coverage — surfaces the obvious the deep minds skip. | Task tool, `model=haiku` |

The panel is **only what is actually reachable** — never name a mind that can't run. Each is a Claude
subagent spawned by the live session via the Task tool; the three available models
(`opus`/`sonnet`/`haiku`) live in [`star-alliance-arsenal/models.json`](../../star-alliance-arsenal/models.json).

**Quorum floor — two distinct minds or it is not a brainstorm.** The value is *reasoning diversity*, so a
panel needs **at least two genuinely different subagents** (different model or different framing) to count.
If only one mind is reachable, the brainstorm has **failed to form** — do not pass single-subagent output
off as a synthesis. Say so explicitly (`degraded: 1 mind reachable — X`), **cap the Phase 5 confidence**
accordingly, and either wait for a second mind or hand back a single-pass plan *labelled as such* so the
receiver knows it was never cross-checked. A fake panel that quietly ran one subagent is worse than an
honest single pass.

Each subagent returns exactly three things: its **best plan** (3–5 steps) · the **one risk** it weighs
heaviest · the **one idea no other subagent would propose**. Diversity is the entire value — different
minds, different blind spots.

**Execution — actually spawn the subagents, don't hand-wave it.** Phase 2 is where this skill quietly
*fails*: an orchestrator can "synthesize" in its own single head and the panel never runs. Make it real by
spawning each panel member as a separate Claude subagent **via the Task tool** in one message (so they run
in parallel), on the same brief, then folding their candidates into the same panel:

```
# One message, several Task calls — each a different Claude mind on the same brief:
Task(subagent_type="the-architect", model="opus",   prompt="<brief> — return best plan, top risk, unique idea")
Task(subagent_type="the-strategist", model="sonnet", prompt="<brief> — same, from a dependency-order frame")
Task(subagent_type="the-strategist", model="sonnet", prompt="<brief> — same, argue the contrarian case")
Task(subagent_type="the-developer",  model="haiku",  prompt="<brief> — same, fast wide coverage")
```

**Only the live top session spawns the panel** — parallel sibling subagents are the Butler's swarm
carve-out. Fire them in a single message so they run concurrently, then collect every candidate.
**Never collapse the panel to a single subagent** — the point here is *reasoning diversity*; one mind
is not a brainstorm.

### Phase 3 — Convergence map
Across the candidate plans: (1) where do **two+ models agree** — the high-confidence spine;
(2) where do they **contradict** — the real decisions, each with its trade-off; (3) which plan has
the **strongest** reasoning, which the **weakest**, and why; (4) the best **orphan idea** — proposed
by one model, adopted by none (often the gem); (5) what did **all models miss** — the panel's shared
blind spot.

### Phase 4 — Synthesis (the one plan)
Build the plan no single subagent wrote: take the agreed spine, **resolve each contradiction with an
explicit call + the reason**, graft the best orphan ideas, and close the blind spot. Output is
**one ordered, build-ready plan** — numbered steps, each with *action · produces · the decision and
why behind it* — ranked by dependency (what must come first).

### Phase 5 — Peer-review gate (the honesty gate)
Grade the plan before it leaves: (1) **confidence 1–10 per step** + the reason; (2) the **weakest
link** + exactly what check would harden it; (3) **model-bias check** — did one model dominate the
synthesis?; (4) the **missing sixth model/angle** that would change conclusions; (5) **overall
grade** a senior planner would give + what to fix first.

## Handoff to the builder

Deliver the **Phase 4 plan** as the headline with **Phase 5 confidence** attached. Keep the Phase 2
candidates and Phase 3 map collapsed/appended so the work is auditable. **Never hand a plan without
its grade** — the grade is what makes it trustworthy. The plan goes to the **member doing the job**
(the builder the Butler routed), scoped and ranked, ready to execute.

## Where it sits in a formation

The natural shape: **members brainstorm in parallel (fan-out) → Strategist ultra-brainstorm (fan-in
/ synthesis) → builder builds.** In a `members-formation`, this is one member step owned by
the member holding the skill (e.g. `the-strategist`) that *produces* a "synthesized plan." When that pattern recurs, the Butler hands
the formation to the Quartermaster to crystallize into a star-map workflow.

## Assignment

This skill is **assignable**. Add `ultra-brainstorming` to a member's `skills:` list and that
member gains the all-minds-at-once power — it then reviews every subagent's output and forms the
final opinion. A member without it thinks a problem through in a single pass (see [[weapon-utility]]).
Assign it where parallel-subagent depth earns its cost; leave it off members who only ever need one mind.

## Versioning

Own skill. Bump `metadata.version` on any change (PATCH: wording/refs · MINOR: new phase/panel
member · MAJOR: method contract change). Regenerate `VERSIONS.md` with
`python3 skillsmith/scripts/skill_registry.py write`, then `python3 build.py`.

## Changelog
- **1.3.1** — Trimmed the panel table to the reachable Claude minds (opus · sonnet · haiku via the
  Task tool); dropped a retired non-Claude row. Refs → PATCH.
- **1.3.0** — **Made the panel MANDATORY for carriers + hardened against fake runs.** "When to run
  it" flipped from discretionary to an obligation: a member that carries this skill **must** fan out
  its subagent panel on plan-grade / hard-problem work (planning, architecture/data-model, fan-in,
  risk/GTM calls), naming the five current carriers (strategist · architect · developer · herald ·
  merchant). Added two tiers — **quick brainstorm** (everyday) vs **full panel** (high-stakes) — so
  the mandate scales to cost and stays adoptable. The only legal skip is a genuine *lookup*, and it
  now leaves a one-line `single-thinker: <why>` trail per [[weapon-utility]]'s exception-out-loud
  doctrine. Phase 2 gains a **quorum floor**: <2 distinct reachable minds = the brainstorm failed to
  form — label it `degraded`, cap Phase 5 confidence, never pass one subagent off as a synthesis.
- **1.2.0** — **Made Phase 2 real, not hand-waved.** Phase 2 now spells out spawning each panel
  member as a separate Claude subagent via the Task tool in one message (so they run in parallel),
  closing the gap where an orchestrator could "synthesize" in one head and the panel never ran.
  Panel table now names each mind's Claude model (opus/sonnet/haiku) and how it runs (Task tool).
- **1.1.0** — **Generalized into an assignable multi-mind skill.** Reframed from "the Strategist's" method to a power any member gains by carrying it: the holding member fans out several parallel Claude subagents at once and then synthesizes one opinion. Added the within-member use (not just cross-member fan-in), an Assignment section, and tied it explicitly to the thinker fan-out exception in [[weapon-utility]]. Panel is now the holding member's own composed set of subagents rather than a fixed Strategist panel.
- **1.0.0** — Initial release. Five-phase multi-mind synthesis: gather & frame, divergent
  parallel-subagent brainstorm, convergence map, one-plan synthesis, peer-review gate,
  builder handoff. Differentiated from storm-investigation (persona ensemble) and members-formation
  (routing); positioned as the fan-in synthesis node in a formation.
