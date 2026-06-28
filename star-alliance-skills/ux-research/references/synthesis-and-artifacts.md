---
title: Synthesis and artifacts — from raw sessions to design decisions
type: reference
---

# Synthesis — turn observations into a decision, not a deck

Raw notes are not findings. Synthesis is the disciplined move from *what we saw* to *what it means*
to *what we'll do* — and it is where most research dies, because teams stop at a pretty artifact and
never reach a decision. An artifact that changes no decision was waste; close that loop.

## The synthesis ladder

1. **Observations** — atomic, quoted, sourced facts ("P3 abandoned checkout at the coupon field").
2. **Patterns** — observations that recur across participants (grouped via affinity mapping).
3. **Insights** — the *why* behind a pattern, stated as a tension or need ("users expect the coupon
   field to be optional and read its prominence as 'a code is required to proceed'").
4. **Recommendations** — a design move the insight implies, with a rationale and a confidence level.

Never skip a rung. A "recommendation" with no traceable observation under it is an opinion wearing
research's clothes.

## Affinity mapping

- One observation per sticky/card, in the participant's words, tagged with the source (P-id).
- Cluster **bottom-up** — let groups emerge from similarity; do not pre-build the buckets you expect,
  or you will only confirm your bias.
- Name each cluster with the *insight* it carries (a sentence), not a topic label ("Coupon field
  reads as mandatory" beats "Coupons").
- Count support per cluster — 1 mention is a signal to watch; 5 of 6 participants is a finding.

## Severity rating (usability findings)

Rate every issue so the team fixes the right things first. A common scale combines:

- **Impact** — cosmetic (0) · minor (1) · major (2) · catastrophic (3, blocks task completion).
- **Frequency** — how many participants hit it / how often in real traffic.
- **Persistence** — one-time stumble vs repeated even after learning.

Severity ≈ impact × frequency. A catastrophic issue 5 of 5 users hit is a launch blocker; a cosmetic
one-off goes to the backlog. Tie severity to a decision (block / fix-this-sprint / backlog), not just
a number.

## Artifacts — built to be used, not admired

- **Personas** — *behavioural archetypes grounded in research*, not demographic cartoons. A useful
  persona captures goals, mental model, context, and pain — the things that change a design decision.
  If a persona could be deleted without changing any design choice, it was decoration. Build them
  from real segments you observed; never invent them to rationalise a design.
- **Journey map** — the end-to-end path across stages, with the user's *actions, thoughts, emotions,
  and pain points* per stage, and the *opportunities* each pain implies. Its value is locating where
  the worst friction sits so effort goes there. Anchor every emotional low and every pain to a real
  observation.
- **Empathy map / service blueprint** — when the experience spans channels or backstage actors, a
  blueprint exposes the seams (handoffs, systems, support) the journey map hides.
- **Findings report** — the deliverable that actually moves work: research question → method & sample
  (with limitations stated honestly) → key findings ranked by severity, each with evidence (quote +
  source) → recommendations with confidence. Lead with the decision the reader must make.

## From research to design decision

- **Make findings decision-shaped.** End every finding with "so we should…" — if you can't, the
  finding isn't actionable yet; dig for the *why*.
- **State confidence and limitations.** "5 of 6 power users, desktop only" is honest; "users hate
  it" over-claims. Quant gives you a confidence interval — report it, don't launder an estimate into a
  fact.
- **Separate observation from interpretation** in every write-up, so a reader can disagree with your
  reading without losing the data.
- **Close the loop.** Track which recommendations shipped and what changed. Research that never
  re-checks its own impact is a one-way data dump, not a practice.
