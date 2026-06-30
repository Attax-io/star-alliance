---
title: Running studies — scripts, recruiting, moderation
type: reference
---

# Running studies — unbiased questions, the right people, a clean session

A study is only as good as its instrument and its participants. A leading question or a wrong
sample poisons every finding downstream — and you will not see the poison in the results, only the
confident wrong conclusion. This is where rigour is cheapest to add and most expensive to skip.

## Writing unbiased questions and scripts

The single most common failure is the researcher leaking the desired answer into the question.

- **Open over closed, in discovery.** "Walk me through the last time you booked travel" beats "Do
  you find booking travel difficult?" The first elicits behaviour; the second hands them a frame.
- **Ban leading and loaded wording.** Not "How much did you love the new dashboard?" (assumes love)
  — instead "What was your reaction to the dashboard?" Strip adjectives that pre-judge.
- **One idea per question.** "Was the form fast and clear?" is two questions; a single answer hides
  which one failed. Split double-barrelled items.
- **Ask about the past and the concrete, not the hypothetical.** "Would you use this?" is worthless
  — people are terrible predictors of their own future behaviour. Ask what they did last time.
- **Avoid acquiescence and social-desirability bias.** People agree to please. Balance scales,
  permit "I didn't / I wouldn't," and explicitly license honesty ("there are no wrong answers; we're
  testing the design, not you").
- **In tests, give tasks, not instructions.** A usability task states a *goal and context* ("you
  want to expense last week's lunch") — never the *steps* ("click the green Add button"). The moment
  you name the control you want them to use, you have destroyed the test.

### Survey-specific

- Pilot every survey on 5 people and watch them take it — comprehension breaks you cannot predict.
- Offer balanced response scales (equal positive/negative anchors), a neutral midpoint only when it
  is meaningful, and an escape hatch ("Not applicable").
- Order matters: earlier questions prime later ones. Put sensitive/demographic items last.

## Recruiting and sampling

- **Screen to the real population.** Define the segment by *behaviour* ("books travel ≥3x/year"),
  not just demographics, and write a screener that rejects ill-fits — including professional
  survey-takers and competitors.
- **Beware the convenience-sample trap.** Friends, colleagues, and your most engaged power users are
  the easiest to recruit and the least representative. Note who you *cannot* reach; that absence is a
  limitation on every claim.
- **Quotas, not coincidence.** If a segment matters to the decision, set a quota and fill it; don't
  hope the sample happens to include it.
- **Incentivise fairly and disclose it** — under-incentivised studies select for the bored and the
  desperate.

## Moderating a usability test

The moderator's job is to *observe behaviour without contaminating it.*

1. **Set up:** warm-up, explain think-aloud, stress "we test the design, not you," get consent to
   record. Establish that silence is fine.
2. **Tasks one at a time**, each a realistic scenario with a clear success state defined *in advance*
   (so you grade behaviour, not vibes).
3. **Shut up and watch.** Resist rescuing a struggling user — the struggle *is* the data. Count to
   ten before intervening.
4. **Echo, don't lead.** When they ask "is this right?", reflect it back: "what would you expect to
   happen?" Never answer, never nod approval.
5. **Probe after, not during:** "you paused there — what were you thinking?" Retrospective probing
   avoids steering the live task.
6. **Capture:** task success (yes/partial/no), time, errors, and verbatim quotes with timestamps.

### Remote vs in-person, moderated vs unmoderated

- **Moderated** (live, you can probe) suits early/ambiguous designs and deep *why*.
- **Unmoderated** (tool-run, no facilitator) scales and removes moderator bias, but you cannot probe
  — reserve for mature flows and larger n.

## Ethics and logistics (non-negotiable)

- **Informed consent** before recording; explain use, storage, and the right to stop.
- **Privacy:** anonymise, minimise PII, scrub recordings of incidental sensitive data.
- **Pilot** every instrument once before the real runs — it always finds a broken task or question.
- **Log the protocol** (script, screener, tasks) so the study is repeatable and auditable.
