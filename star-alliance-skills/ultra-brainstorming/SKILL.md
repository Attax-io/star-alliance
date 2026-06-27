---
name: ultra-brainstorming
description: "An ASSIGNABLE multi-thinker method — any member who carries it fires ALL his available thinker models at once on the same material, then his prime (highest-priority) thinker reviews every output and synthesizes one opinion. Use to deepen one member's thinking across model diversity, or at a fan-in to fuse several members' inputs into one doer-ready plan. Triggers: 'ultra-brainstorm this', 'super-plan this', 'think this across all models', 'use all my thinkers', 'synthesize the members' work', 'merge these proposals into one plan', 'plan this deeply before we build'. Distinct from storm-investigation (five persona minds on one topic) and members-formation (the Butler's routing): this is a MODEL ensemble — several thinking models, each a different mind — converging into one ranked, peer-reviewed result. It is the thinker fan-out exception named in weapon-utility."
metadata:
  version: 1.3.0
type: Skill

---
# Ultra-Brainstorming — the assignable multi-thinker skill

This skill gives **any member who carries it** one extra power: instead of running a single
prime thinker, the member fires **all of its available thinker weapons at once** on the same
material, then its **prime (highest-priority) thinker reviews every output and synthesizes one
opinion**. This is exactly the *thinker fan-out exception* named in [[weapon-utility]] — assign
this skill to a member and that member gains it.

It serves two shapes: **deepen one member's own thinking** across model diversity, or sit at a
**fan-in** where several members' outputs **converge** and leave as **one plan** for the doer. The
Strategist carries it for campaign planning, but it rides any member you add it to.

Know what it is *not*:

- Not **`members-formation`** (the Butler's routing — *who* works and in what arrangement). The
  Butler routes the inputs *to* this synthesis node; here the member holding this skill fuses them.
- Not **`storm-investigation`** (five *persona* minds researching one topic). This is a **model
  ensemble** — five *thinking models*, each a genuinely different mind, brainstorming the same
  combined material. Personas vary the viewpoint; models vary the reasoning engine.
- Not **`conquering-campaign`** (multi-wave *execution*). This produces the **plan** the campaign
  then executes.

## When to run it — MANDATORY for carriers

**Carrying this skill is an obligation, not an option.** If a member carries `ultra-brainstorming`
and the task in front of it is **plan-grade or hard-problem work**, the member **must** fire its
thinker panel — it may not quietly fall back to a single prime thinker. The skill rides these
carriers today: **the-strategist · the-architect · the-developer · the-herald · the-merchant**.
Each must use it whenever it does the kind of thinking below.

**"Plan-grade / hard-problem work" — the panel is required when the task is any of:**
- planning before a build, refactor, or campaign (sequencing, trade-offs, dependency order)
- architecture or data-model decisions; structural choices with more than one defensible answer
- a **fan-in** — two or more members' outputs (schema sketch · UX notes · risk read) must become
  **one coherent plan** before a doer starts
- risk / investment / go-to-market calls where being wrong is expensive
- anything where the carrier would otherwise reach for its single prime thinker to *decide*, not
  just *look up*

**Two tiers — scale the fire to the stakes (both still count as "using it"):**
- **Quick brainstorm** (the default for everyday hard calls): the panel runs, all five phases run,
  but lightly — short candidates, fast convergence. The point is *more than one mind touched it*.
- **Full panel** (high-stakes — architecture, irreversible scope, multi-member fan-in, money/risk):
  the full five-phase treatment with the runner, the convergence map, and the peer-review grade.

**The only legitimate skip is a lookup.** Single-input retrieval, a mechanical/obvious change, or a
question with one correct answer is **not** plan-grade work — run the single prime thinker, that's
the Butler's formation. But the skip is **on the record**: a carrier that declines the panel on
something that *looks* plan-grade states the reason in one line — `single-thinker: <why this is a
lookup, not a decision>` — exactly as [[weapon-utility]] requires an exception to be justified out
loud. Silent single-thinking on plan-grade work is a conformity failure, not a shortcut.

Ultra-brainstorming is for *fusion across minds*. A member without the skill runs the default single
prime thinker; a member **with** it owes the panel on every real decision.

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
Run **all of the holding member's available thinker weapons** on the same combined inputs, each as
an **independent mind**. The panel is therefore the member's own arsenal — the example below is the
Strategist's; another member runs its own thinkers:

| Model | The mind it brings | Backend |
|---|---|---|
| **opus** | Deepest structural reasoning — is the plan *sound*? | Claude-native → **Task tool**, not a script |
| **gpt-5.5** | Analytical + creative second opinion — what's the non-obvious move? | OpenAI-direct — **DEACTIVATED** (no key); skip until reactivated |
| **deepseek-v4-pro** | Frontier multi-step reasoning — the long dependency chains. | Ollama cloud |
| **glm-5.2** | A different analytical frame — where the others over-fit. | Ollama cloud |
| **kimi-k2.7** | Holds the whole context — long-range coherence across all inputs. | Ollama cloud |

The panel is **only what is actually reachable** — never name a mind that can't run. Each weapon has a
doc under [`star-alliance-arsenal/models/`](../../star-alliance-arsenal/models/README.md) (backend ·
how to pull · how to summon · concurrency). Confirm cloud thinkers with `ollama list` first.

**Quorum floor — two distinct minds or it is not a brainstorm.** The value is *model diversity*, so a
panel needs **at least two genuinely different reasoning engines** to count. If only one thinker is
reachable (Free plan with cloud down, every other model unpulled), the brainstorm has **failed to
form** — do not pass single-model output off as a synthesis. Say so explicitly (`degraded: 1 mind
reachable — X`), **cap the Phase 5 confidence** accordingly, and either wait for a second mind or hand
back a single-thinker plan *labelled as such* so the doer knows it was never cross-checked. A fake
panel that quietly ran one model is worse than an honest single thinker.

Each model returns exactly three things: its **best plan** (3–5 steps) · the **one risk** it weighs
heaviest · the **one idea no other model would propose**. Diversity is the entire value — different
engines, different blind spots.

**Execution — use the runner, don't hand-wave it.** Phase 2 is where this skill quietly *fails*: an
orchestrator can "synthesize" in its own single head and the panel never runs. Make it real with the
mechanical runner, which fires every reachable thinker and returns their candidates as JSON:

```
python3 "$STAR_ALLIANCE_ROOT/star-alliance-arsenal/ultra_brainstorm.py" "<brief>" --max-tokens 16000
# or: -f brief.txt ; --models glm-5.2,kimi-k2.7,deepseek-v4-pro,gemma4
```

Then add the **Claude minds** the runner lists in `run_via_task` (e.g. `opus`) by spawning them with
the **Task tool** (`model=opus`) on the same brief, and fold those candidates into the same panel.

**Concurrency is a hard limit, not a style choice.** Ollama Cloud caps *concurrent models* by plan —
**Free = 1**, Pro = 3, Max = 10 — and **rejects** overflow once the queue fills. That is the real
reason a 5-model parallel fan-out drops models: they look dead when the account is just over its slot
count. So the runner goes **sequential** for cloud thinkers (correct on Free), and `ollama_cloud.py`
holds a slot semaphore (`OLLAMA_MAX_CONCURRENT`, default 1) that queues locally + retries on busy. On
Pro/Max raise `OLLAMA_MAX_CONCURRENT` to the plan's number. Claude (Task) and MiniMax-direct are
*separate* pools — they overlap freely with the Ollama panel. **Never collapse the panel to a single
MiniMax doer** — the repo default favors MiniMax for doer work, but here the point is *model
diversity*; one model is not a brainstorm.

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
the member holding the skill (e.g. `the-strategist`) that *produces* a "synthesized plan." When that pattern recurs, the Butler hands
the formation to the Quartermaster to crystallize into a star-map workflow.

## Assignment

This skill is **assignable**. Add `ultra-brainstorming` to a member's `skills:` list and that
member gains the all-thinkers-at-once power — its prime thinker then reviews and forms the final
opinion. A member without it runs the default single prime thinker (see [[weapon-utility]]). Assign
it where multi-model depth earns its cost; leave it off members who only ever need one mind.

## Versioning

Own skill. Bump `metadata.version` on any change (PATCH: wording/refs · MINOR: new phase/panel
member · MAJOR: method contract change). Regenerate `VERSIONS.md` with
`python3 skillsmith/scripts/skill_registry.py write`, then `python3 build.py`.

## Changelog
- **1.3.0** — **Made the panel MANDATORY for carriers + hardened against fake runs.** "When to run
  it" flipped from discretionary to an obligation: a member that carries this skill **must** fire its
  thinker panel on plan-grade / hard-problem work (planning, architecture/data-model, fan-in,
  risk/GTM calls), naming the five current carriers (strategist · architect · developer · herald ·
  merchant). Added two tiers — **quick brainstorm** (everyday) vs **full panel** (high-stakes) — so
  the mandate scales to cost and stays adoptable. The only legal skip is a genuine *lookup*, and it
  now leaves a one-line `single-thinker: <why>` trail per [[weapon-utility]]'s exception-out-loud
  doctrine. Phase 2 gains a **quorum floor**: <2 distinct reachable minds = the brainstorm failed to
  form — label it `degraded`, cap Phase 5 confidence, never pass one model off as a synthesis.
- **1.2.0** — **Made Phase 2 mechanical + concurrency-aware.** Added the `ultra_brainstorm.py`
  runner so the fan-out actually fires (was prose the orchestrator could skip, synthesizing in one
  head). Documented the Ollama Cloud concurrency cap (Free=1/Pro=3/Max=10) as the real cause of
  dropped panel models, tied to the new `OLLAMA_MAX_CONCURRENT` slot guard in `ollama_cloud.py`.
  Panel table now tags each mind's backend (opus → Task tool; gpt-5.5 deactivated) and links the new
  per-weapon docs under `star-alliance-arsenal/models/`. Execution is sequential for cloud thinkers.
- **1.1.0** — **Generalized into an assignable multi-thinker skill.** Reframed from "the Strategist's" method to a power any member gains by carrying it: the holding member fires ALL its own available thinker weapons at once and its prime thinker synthesizes one opinion. Added the within-member use (not just cross-member fan-in), an Assignment section, and tied it explicitly to the thinker fan-out exception in [[weapon-utility]]. Panel is now the holding member's own arsenal rather than a fixed Strategist panel.
- **1.0.0** — Initial release. Five-phase multi-model synthesis: gather & frame, divergent
  multi-model brainstorm (5-thinker panel), convergence map, one-plan synthesis, peer-review gate,
  doer handoff. Differentiated from storm-investigation (persona ensemble) and members-formation
  (routing); positioned as the fan-in synthesis node in a formation.
