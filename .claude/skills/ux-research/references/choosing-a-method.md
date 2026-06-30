---
title: Choosing a UX research method
type: reference
---

# Choosing a method — match the question, not the fashion

A method is a tool for answering a *kind* of question. Pick by what you need to learn and what
decision the finding will move, never by what is fashionable or easiest to schedule. The first
move in any study is to write the **research question** in one sentence and name the **decision**
it will inform. If you cannot, you are not ready to recruit.

## The two axes that pick a method

1. **Attitudinal vs behavioural** — *what people say* vs *what people do*. The two diverge
   constantly; design from behaviour, weight stated preference lightly.
2. **Qualitative vs quantitative** — *why / how* (small n, depth, generative) vs *how many / how
   much* (large n, measurement, evaluative). Qual finds the problem; quant sizes it.

## Method picker

| You need to learn | Method | Axis | Typical n |
|---|---|---|---|
| Why users behave this way; unmet needs; mental models | **In-depth interview** | attitudinal · qual | 5–8 per segment |
| Whether a design is usable; where people fail a task | **Usability test** (moderated) | behavioural · qual | 5 per round |
| How big a problem is; satisfaction; preference at scale | **Survey** | attitudinal · quant | 100+ for stable % |
| How people group/label concepts (IA, navigation) | **Card sort** (open/closed) | behavioural · qual→quant | 15–30 |
| Whether labels/structure let people find things | **Tree test** | behavioural · quant | 30+ |
| Which of two live variants performs better | **A/B test** | behavioural · quant | powered by effect size |
| What real users do in context, over time | **Diary study / field study** | behavioural · qual | 8–15 |
| Where users click / drop on a live flow | **Analytics + session replay** | behavioural · quant | all traffic |

## Generative vs evaluative

- **Generative (discovery)** research runs *before* you have a design — interviews, field studies,
  diary studies, open card sorts. Output: needs, jobs, opportunities, a problem worth solving.
- **Evaluative** research runs *on a design* — usability tests, tree tests, A/B, surveys of an
  existing experience. Output: does this design work, and where does it fail.

Most teams over-invest in evaluative and starve generative — they polish solutions to the wrong
problem. If you do not yet know the problem, do not run a usability test; run interviews.

## Sample size, honestly

- **Qual usability:** ~5 users surface ~85% of severe issues *per round*; run **more rounds**, not
  more users per round (test 5, fix, test 5 again).
- **Quant:** sample is driven by the **margin of error and effect size you need**, not a round
  number. A survey reporting a proportion needs ~100+ for a usable confidence interval; an A/B test
  needs a power calculation from baseline rate and minimum detectable effect — running it "until it
  looks significant" manufactures false positives (peeking).
- **Saturation** is the qual stop rule: stop when new sessions stop producing new themes.

## Triangulate

No single method is ground truth. A strong finding is one the same conclusion reaches from two
methods — e.g. interviews say users distrust the pricing page (qual *why*) and analytics show a
drop at that step (quant *how many*). When methods disagree, that gap is itself the finding.

## When NOT to run research

- The decision is already made and research is theatre to justify it — say so, don't run it.
- The question is a known best practice (a 3px focus ring, a standard date picker) — apply the
  standard, save the budget for the genuinely uncertain.
- You need the answer faster than a study can run — ship a reversible bet and instrument it.
