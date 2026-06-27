---
type: Document
timestamp: 2026-06-27T10:27:03Z
---

# STORM Investigation — paste-ready prompt pack

The four verbatim prompts. Replace `[TOPIC]` (and `[ROLE]` in Prompt 3) before running. Run in
order; each prompt assumes the previous output is in context.

---

## Prompt 1 — Multi-perspective scan

```text
I need to research [TOPIC].
Simulate 5 different expert perspectives on this topic:
1. THE PRACTITIONER: works with this daily.
   What do they know that academics miss?
   What practical realities are usually ignored?
2. THE ACADEMIC: has studied this for years.
   What does the peer reviewed evidence actually say?
   Where does the evidence contradict popular belief?
3. THE SKEPTIC: thinks the mainstream view is wrong.
   What is the strongest counterargument?
   What evidence do proponents conveniently ignore?
4. THE ECONOMIST: follows the money.
   Who profits from the current narrative?
   What financial incentives shape the research?
5. THE HISTORIAN: has seen similar patterns before.
   What historical parallels exist?
   What can we learn from how those played out?
For each perspective give me:
- Their core position in 2 sentences
- The strongest evidence supporting their view
- The one thing they would tell me that no other perspective would
```

## Prompt 2 — Contradiction map

```text
Based on the 5 perspectives above, map the contradictions:
1. Where do two or more perspectives directly contradict each other?
   List each conflict with the specific claims that clash.
2. Which perspective has the strongest evidence?
   Which has the weakest? Why?
3. What is the one question that, if answered, would resolve the biggest contradiction?
4. What does EVERY perspective agree on? (This is likely true. Even opponents confirm it.)
5. What topic did NONE of the perspectives address?
   (This is the blind spot in the whole field. Often the most valuable finding.)
```

## Prompt 3 — Synthesis

```text
Synthesize everything from the 5 perspectives and the contradiction map into a research briefing:
1. THE ONE PARAGRAPH SUMMARY: explain this topic as if briefing a CEO who has 60 seconds
   and needs nuance, not just the headline.
2. THE 5 KEY FINDINGS: most important things I now know, ranked by reliability.
   For each, note which perspectives support it and which challenge it.
3. THE HIDDEN CONNECTION: one non obvious link between findings that only shows up
   when you look at all 5 perspectives together.
4. THE ACTIONABLE INSIGHT: based on all the evidence, what should someone in [ROLE]
   actually DO differently? Be specific.
5. THE FRONTIER QUESTION: the one question that, if answered, would change everything
   about how we understand this topic.
```

## Prompt 4 — Peer review

```text
Now peer review your own research briefing:
1. CONFIDENCE SCORES: rate each of the 5 key findings on a 1 to 10 scale for reliability.
   Explain each score.
2. WEAKEST LINK: which claim are you least confident in?
   What specific info would you need to verify it?
3. BIAS CHECK: which perspective might be overrepresented in your synthesis?
   Did one voice dominate?
4. MISSING PERSPECTIVE: is there a 6th angle I should have included
   that would change the conclusions?
5. OVERALL GRADE: if a domain expert reviewed this briefing, what grade would they give
   and why? What would they tell me to fix?
```

---

## Swappable persona sets

Keep five, keep them contrasting. Swap the Prompt 1 roles to fit the domain:

| Domain | Five personas |
|---|---|
| **General** (default) | Practitioner · Academic · Skeptic · Economist · Historian |
| **Investment** | Bull · Bear · Macro analyst · Quant · Contrarian |
| **Legal / dispute** | Plaintiff · Defense · Judge · Regulator · Historian |
| **Product / feature** | Power user · Engineer · PM · Support · Competitor |
| **Hiring / org** | Hiring manager · IC on the team · Skeptic peer · Finance · Ex-employee |
| **Go-to-market** | Buyer · Seller · Analyst · Skeptic customer · Incumbent |

## Fan-out execution (parallel personas)

For high-stakes or sourced research, run one doer per persona instead of inline.

- **Default doer = MiniMax M3** (repo `CLAUDE.md`): each persona is one call —
  `python3 minimax.py "<persona prompt for TOPIC>" -s "You are THE <PERSONA>. <lens>." --json`.
  Collect the five JSON verdicts, then run Prompts 2–4 over them.
- **Use Claude sub-agents / a Workflow** when personas must use tools (WebSearch, WebFetch, an MCP
  data source, file reads) or must return schema-validated output. Natural shape: one sub-agent per
  persona in phase 1 (parallel), then the parent runs contradiction-map → synthesis → peer-review
  sequentially. A `pipeline`/`parallel` Workflow fits when each persona should also fetch its own
  sources.
- **Grounding:** when sourced, require every persona to put a citation (URL / doc / data point) in its
  "strongest evidence" slot. If unsourced, say so in Prompt 4's bias check — reasoning-only briefings
  are still useful but must be labeled.

## Provenance
- Method: Stanford OVAL Lab, *STORM*, NAACL 2024 · github.com/stanford-oval/storm · storm.genie.stanford.edu
- Adapted from the write-up saved at `~/Downloads/The Stanford STORM Method ….md` (2026-06-19).
- Related: `skillsmith` `routine` mode uses a STORM recast for skill evolution (see
  `skillsmith/references/storm-method.md`); `deep-research` is the web-search-fan-out complement.
