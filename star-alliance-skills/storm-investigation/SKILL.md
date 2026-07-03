---
name: storm-investigation
description: >-
  Multi-perspective deep-research method (Stanford STORM, NAACL 2024) for any topic — run five contrasting expert personas, map where they contradict, synthesize a ranked briefing, then peer-review it for confidence. Use when the user wants real understanding fast, not a surface summary: 'research this topic', 'run STORM', 'STORM this', 'investigate X deeply', 'deep dive on X', 'multi-perspective research', '5 expert perspectives', 'contradiction map', 'give me a research briefing', 'red-team this idea', or research before a decision — before writing/investing/negotiating/interviewing/presenting/learning. Distinct from deep-research (which is web-search fan-out): STORM is persona-simulation reasoning that catches blind spots a single prompt misses, optionally grounded with sources. Produces a briefing with confidence scores a single expert could not write.
metadata:
  version: 1.0.0
type: Skill

---
# STORM Investigation

A way of *thinking*, not a tool. **STORM** — *Synthesis of Topic Outlines through Retrieval and
Multi-perspective Question Asking* (Stanford OVAL Lab, NAACL 2024) — beats single-prompt research
because **one prompt returns the majority view; five contrasting personas catch the blind spots.**
Stanford measured multi-perspective articles ~25% more organized and ~10% broader than single-prompt
ones. This skill runs that method on any topic in four phases.

> Repo note: `skillsmith`'s `routine` mode already uses a STORM *recast for skill-evolution*. This
> skill is the **general-purpose** version — research any topic, not just skills. Same four phases.

## When to run it

Any time the stakes beat a 60-second answer: before an article/report, a business or investment
decision, a negotiation, an interview, a presentation, or learning a new field. If the user just
wants a quick fact, don't — STORM is for understanding, not lookup.

## The four phases — run in order

Run all four in sequence. Phases 2–4 each consume the prior output. Verbatim prompt templates live in
[`references/prompt-pack.md`](references/prompt-pack.md) — paste-ready, swap `[TOPIC]`/`[ROLE]`.

### Phase 1 — Multi-perspective scan (the heart)
Simulate **five contrasting expert personas** on the topic. The default set:

| # | Persona | Lens | The question only it asks |
|---|---|---|---|
| 1 | **Practitioner** | Works with this daily. | What do practitioners know that academics miss? What practical reality is usually ignored? |
| 2 | **Academic** | Has studied it for years. | What does peer-reviewed evidence actually say? Where does it contradict popular belief? |
| 3 | **Skeptic** | Thinks the mainstream view is wrong. | What is the strongest counterargument? What evidence do proponents conveniently ignore? |
| 4 | **Economist** | Follows the money. | Who profits from the current narrative? What incentives shape the research? |
| 5 | **Historian** | Has seen the pattern before. | What historical parallels exist? How did those play out? |

For **each** persona capture exactly three things: **core position** (2 sentences) · **strongest
supporting evidence** · **the one thing it would tell you that no other persona would.**

**Swap personas to fit the domain.** Investment → Bull / Bear / Macro / Quant / Contrarian.
Legal → Plaintiff / Defense / Judge / Regulator / Historian. Product → User / Engineer / PM /
Support / Competitor. Keep five, keep them *contrasting* — diversity is the whole point.

### Phase 2 — Contradiction map
From the five verdicts: (1) where do two+ personas **directly contradict** — list each clash with the
specific claims; (2) which has the **strongest** evidence, which the **weakest**, and why; (3) the
**one question** that, if answered, resolves the biggest contradiction; (4) what do **ALL five agree**
on (likely true — even opponents confirm it); (5) what did **NO persona address** (the blind spot in
the whole field — often the most valuable finding).

### Phase 3 — Synthesis (the briefing)
Pull scan + map into a briefing no single expert could write: (1) **one-paragraph summary** as if
briefing a CEO who has 60 seconds and needs nuance; (2) **5 key findings ranked by reliability**, each
noting which personas support and which challenge it; (3) the **hidden connection** — one non-obvious
link visible only across all five; (4) the **actionable insight** — what should someone in `[ROLE]`
actually do differently, specifically; (5) the **frontier question** — the one unknown that would
change everything.

### Phase 4 — Peer review (the honesty gate)
STORM's known weakness: it doesn't self-critique, so source bias and fact-misassociation sneak in.
Force it to grade its own briefing: (1) **confidence 1–10** per finding, with the reason; (2) the
**weakest link** + exactly what evidence would verify it; (3) **bias check** — did one persona
dominate the synthesis?; (4) **missing 6th perspective** that would change conclusions; (5) **overall
grade** a domain expert would give + what to fix first.

## How to execute (two modes)

- **Inline (default, fast).** Run the four prompts in sequence in the conversation. ~5 minutes,
  one expert briefing. Best for most requests.
- **Fan-out (heavier, parallel).** One Claude subagent per persona, then the parent runs phases 2–4.
  Use for high-stakes topics or when you want sourced evidence per persona.
  - **Spawn one Claude subagent per persona** via the Task tool, briefing each with its lens; fan all
    five out in a single message so they run concurrently.
  - Reach for subagents / a `Workflow` especially when personas must use tools (web search, MCP,
    file reads) or return validated structured output. See `references/prompt-pack.md` §Fan-out.

## Grounding with sources (optional)
STORM is reasoning, not retrieval — but it's stronger grounded. To source it: give each persona real
evidence (WebSearch/WebFetch, an MCP data tool, or pasted material) and require citations in the
"strongest evidence" slot. Without sources, label the briefing as reasoning-only in Phase 4's bias
check. For pure web-search fan-out research, prefer the `deep-research` skill instead — or chain it
*before* STORM to supply the corpus.

## Output contract
Deliver the **Phase 3 briefing** as the headline, with **Phase 4 confidence scores** attached. Keep
the Phase 1 persona verdicts and Phase 2 map available (collapsed/appended) so the user can audit the
reasoning. Never present the synthesis without the peer-review grade — the grade is what makes it
trustworthy.

## Versioning
Own skill. Bump `metadata.version` on any change (PATCH: wording/refs · MINOR: new phase/mode ·
MAJOR: workflow contract change). Regenerate `VERSIONS.md` with
`python3 skillsmith/scripts/skill_registry.py write` after a bump.

## Changelog
- **1.0.0** — Initial release. Vanilla 5-persona STORM, four phases, inline + fan-out modes, swappable persona sets, optional source-grounding.
