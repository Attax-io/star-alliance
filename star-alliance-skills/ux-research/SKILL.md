---
name: ux-research
metadata:
  version: 1.0.0
type: Skill
description: "The Designer's UX research craft — learn from real users instead of guessing. Choose a method (interviews, surveys, usability tests, card/tree sorts, A/B) by matching it to the research question and the decision it moves; write unbiased questions and task scripts; recruit and sample the real population; moderate a usability test cleanly; synthesize raw sessions into findings via affinity mapping, severity rating, personas, and journey maps; turn findings into design decisions. Triggers: run user research, plan a usability test, write interview questions, map the user journey, synthesize this research, build a persona, recruit participants, rate finding severity. Differs from design-taste (visual judgment, not user evidence), a11y-craft (WCAG accessibility, not research), and storm-investigation (5-persona strategic recon, not a real-user study)."
---
# ux-research — learn from real users, then design from what you learned

This is the Designer's craft for **finding out what users actually need and whether a design
works** — by studying real people, not by guessing well. The Designer owns visual language, tokens,
and accessibility; this skill adds the missing **research** layer: the discipline of asking the
right people the right question the right way, and converting what they say and do into design
decisions you can defend.

Research is how taste earns the right to be confident. A premium surface that nobody can use, or
that solves a problem users don't have, is a beautiful wrong answer. This skill keeps the team
honest about which problem is real and whether the solution works.

## What it is / is not

- It **is** the user-evidence layer: choose a method, run a clean study, synthesize findings, and
  hand the team a decision. Generative (discover the problem) and evaluative (test the design) both.
- It is **not** [[design-taste]] — that is *visual judgment* about how an interface should look.
  Research tells you whether the look serves the user; taste decides the look. Research before taste
  in discovery; research after taste to validate.
- It is **not** [[a11y-craft]] — that proves a UI is operable against WCAG 2.2 AA. Accessibility is a
  *standard you apply*; research is a *question you ask of users*. Reach for a11y-craft for keyboard
  and contrast; reach here to learn what users are trying to do.
- It is **not** `storm-investigation` — that is a five-persona *strategic recon* of a topic by
  simulated expert minds. This skill studies **real users** with real methods and real consent. Don't
  substitute a persona-storm for talking to actual people.
- It may draw on `design:user-research` and `design:research-synthesis` plugin knowledge as deeper
  references, but the generative principles here are the spine.

## The references

| Reference | Covers |
|---|---|
| [references/choosing-a-method.md](references/choosing-a-method.md) | The two axes (attitudinal/behavioural, qual/quant), a method picker, generative vs evaluative, honest sample sizes, triangulation, when *not* to research |
| [references/running-studies.md](references/running-studies.md) | Unbiased questions & task scripts, recruiting & sampling, moderating a usability test, survey design, ethics & consent |
| [references/synthesis-and-artifacts.md](references/synthesis-and-artifacts.md) | The synthesis ladder, affinity mapping, severity rating, personas, journey maps, the findings report, closing the loop to a decision |

## Generative principles

1. **The question and the decision come before the method.** Write the research question in one
   sentence and name the decision it will move *before* recruiting. No decision in play → no study;
   "research as theatre to justify a made-up mind" is named and refused. The method is chosen to
   answer *that* question (see the picker), never by fashion or convenience.

2. **Behaviour over claims; the gap between them is the finding.** What people *do* outranks what they
   *say* — design from observed behaviour, weight stated preference lightly, and never ask the
   hypothetical ("would you use this?"). When attitudinal and behavioural data disagree (interviews
   praise a page analytics show people flee), that disagreement is itself the most valuable signal.

3. **Don't leak the answer into the instrument.** The fastest way to ruin a study is a leading
   question, a loaded adjective, a double-barrelled item, or a usability task that names the control
   you want clicked. Ask open and concrete, one idea per question, tasks-as-goals not steps; license
   honesty ("we're testing the design, not you"); pilot every instrument once before the real runs.

4. **Recruit the real population, and own who you missed.** Screen by behaviour to the actual segment,
   set quotas for segments that matter, and refuse the convenience-sample trap (friends, colleagues,
   power users are easy and unrepresentative). State who you could *not* reach — that absence bounds
   every claim you make.

5. **Match rigour to claim — small n for depth, powered n for numbers.** ~5 users per round surface
   most severe usability issues; run more *rounds*, not more users per round. Quantitative claims need
   a sample driven by margin of error and effect size, and an A/B test needs a pre-set power
   calculation — never "run it until it looks significant" (peeking manufactures false positives).

6. **Climb the synthesis ladder; never skip a rung.** Observation → pattern → insight → recommendation,
   each rung traceable to a quoted, sourced observation. Cluster bottom-up (affinity mapping), name
   clusters by the insight they carry, rate every usability issue by severity (impact × frequency)
   tied to a block/fix/backlog decision. A recommendation with no observation under it is an opinion.

7. **An artifact that moves no decision was waste — close the loop.** Personas, journey maps, and
   reports exist to *change a design choice*; if one could be deleted without changing any decision, it
   was decoration. Make findings decision-shaped ("so we should…"), state confidence and limitations
   honestly, separate observation from interpretation, and track which recommendations shipped and
   what changed.

## How you work

1. **Frame first.** Restate the research question and the decision in one line. If you can't, you're
   not ready — surface the ambiguity instead of recruiting.
2. **Pick the method from the question**, not the calendar — the picker in `choosing-a-method.md`.
3. **Build and pilot the instrument** (script / screener / tasks / survey) before any real session;
   strip every leak.
4. **Run clean** — observe behaviour without contaminating it; capture success, time, errors, and
   sourced verbatims.
5. **Synthesize up the ladder** to severity-rated findings and only the artifacts that move a decision.
6. **Hand the Designer and Developer a decision**, with evidence, confidence, and limitations stated.
