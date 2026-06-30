---
name: cognitive-bias-guard
description: >-
  A structured protocol to catch and neutralize cognitive and social biases before they
  corrupt a group decision, code review, investigation, or design session. Use when someone
  asks "are we reasoning clearly here?", "run the bias check", "am I falling for something?",
  before any group decision or vote, before finalizing a hotspot verdict, before accepting a
  root-cause analysis, or when a team's conclusion feels suspiciously unanimous. Also apply
  proactively any time groupthink, hindsight bias, anchoring, or pluralistic ignorance might
  be distorting the outcome. Based on the forensic psychology chapters of Adam Tornhill's
  *Your Code as a Crime Scene* and supporting research in behavioral psychology.
metadata:
  version: 1.0.0
type: Skill

---
# Cognitive Bias Guard

**The forensic psychologist's observation:** when programmers diagnose code problems, evaluate
designs, or conduct post-mortems, they are not reasoning machines — they are humans running on
the same cognitive hardware that our ancestors used to navigate social tribes. The same biases
that produce false confessions, groupthink in committees, and eyewitness misidentifications
silently corrupt software decisions.

This skill names the six most dangerous biases in technical and team contexts, and provides a
concrete countermeasure for each.

> "Expert intuition can lead to high-quality decisions. The problem is that we don't know up
> front whether this time is one of those expert intuitions." — Tornhill

## When to deploy the guard

Any of these signals warrant running the guard:

- A room reaches consensus suspiciously fast (no disagreement heard)
- A post-mortem produces "we all knew it would fail" conclusions
- The first person to estimate anchored everyone else
- A code review confirms what the reviewer expected to find
- A single authority's opinion closed the debate
- The team avoided challenging a bad idea because everyone assumed someone else would

## The Six Biases + Countermeasures

---

### 1 — Pluralistic Ignorance
**What it is:** Each member of a group privately doubts the consensus, but publicly goes along
because they believe everyone else agrees. The result: a room full of silent dissenters who
each think they're the only one. Bad decisions survive because no one speaks up.

**Classic example (Tornhill):** The Thomas Quick wrongful conviction — investigators, therapists,
and the public all had doubts but assumed the others were confident, so no one challenged it.

**In code:** "Everyone said the architecture was fine, so I didn't raise the coupling concern."

**Countermeasure: silent-ballot before discussion.**
Before any group assessment, have every participant write their independent verdict (thumbs
up/down/concern list) before anyone shares. Reveal simultaneously. If more than one person
marked a concern, open the floor — pluralistic ignorance requires the false belief that
*no one* disagrees.

---

### 2 — Groupthink
**What it is:** Social pressure toward consensus silences dissent. The group optimizes for
harmony, not truth. Warning signs: illusion of unanimity, self-censorship of doubt, mind-guarding
(members discourage challenges to the group's view), and pressure on dissenters.

**In code:** "We decided not to raise the database design concern because the tech lead seemed
committed and we didn't want to slow things down."

**Countermeasure: assigned devil's advocate.**
Before the decision meeting, assign one person the explicit role of finding the strongest
argument *against* the proposed approach. Rotate the role across sessions. The assigned
devil's advocate has social permission to challenge — which removes the social cost of dissent.

---

### 3 — Hindsight Bias
**What it is:** After an outcome, people believe they "knew it all along." This distorts
post-mortems and makes them useless for learning: "Of course the monolith would fail" (but you
didn't say that before). The bias inflates confidence in future predictions and blocks genuine
understanding of *why* something failed.

**In code:** Every post-mortem where "the signs were obvious" — but no one wrote them down before
the incident.

**Countermeasure: prospective prediction ledger.**
Before a decision is finalized, write down in one sentence: "We predict this will succeed/fail
because ___." Date it. Review it in the post-mortem alongside what actually happened. The
discrepancy between what you *actually predicted* and what you *remember predicting* is the
bias made visible.

For investigations: form the hypothesis before looking at the evidence, then check the evidence.
Don't form the hypothesis *after* seeing data that confirms it.

---

### 4 — Anchoring
**What it is:** The first number, estimate, or framing heard by a group becomes the reference
point for all subsequent reasoning — even when it was arbitrary. If the first engineer says
"this will take 2 weeks," the group negotiates around 2 weeks rather than re-estimating
independently.

**In code:** The first complexity estimate, the first defect count, the first "this module is
fine" assessment anchors everyone who reads it next.

**Countermeasure: independent estimates first.**
Before any estimation or assessment meeting, each participant writes their independent estimate
privately, then all reveal simultaneously. Don't let anyone share their number first. This
applies to: story points, bug severity, refactoring difficulty, risk rating, and code review
verdicts (✓ / ✗).

---

### 5 — Confirmation Bias
**What it is:** We seek, notice, and remember evidence that confirms what we already believe,
and discount evidence that contradicts it. In code reviews, this means we read the code to
confirm our mental model of how it works, not to find surprises.

**In code:** "I know this code is fine because I wrote it." Or: "I read through the auth module
and it looks clean." (The reader was looking for problems where they expected none.)

**Countermeasure: the assumption list + contradiction hunt.**
Before investigating a module, write down your top 3 beliefs about it ("I believe this module
is stateless / has no external dependencies / follows the single-responsibility principle").
Then read the code *specifically looking for evidence that contradicts each belief*. What you
find against your priors is more valuable than what confirms them.

For post-mortems: assign one person to find evidence that the "root cause" is *not* the one
the group converged on.

---

### 6 — Authority Bias + False Expertise Signals
**What it is:** We overweight the opinion of the most senior person, the person who speaks
most confidently, or the person who uses the most technical jargon — regardless of the actual
quality of their reasoning.

**In code:** "The architect said the service mesh was fine, so we shipped." (But the architect
hadn't looked at the actual coupling data.)

**Countermeasure: evidence-first, not authority-first.**
Any claim about the system's health must be backed by data from the version-control system,
logs, or metrics — not just the speaker's tenure or confidence. Apply the rule: "Show me the
commit history that supports that claim." If the data isn't available, the claim is a hypothesis,
not a finding. Treat it as such.

---

## Rapid Bias Check (1-minute version)

When you don't have time for the full guard, run this five-question checklist before finalizing
any group decision or investigation finding:

1. **Did everyone share before anyone else spoke?** (anchoring guard)
2. **Did anyone privately doubt but not say so?** (pluralistic ignorance guard)
3. **Did the most senior voice dominate?** (authority bias guard)
4. **Did we write down our prediction before seeing the outcome?** (hindsight guard)
5. **Did we look for evidence *against* our conclusion?** (confirmation bias guard)

If any answer is "no," pause and apply the matching countermeasure above before proceeding.

---

## Pairing with other skills

- **Before finalizing a `code-crime-scene` verdict** → run the 1-minute check; apply
  "confirmation bias" guard to the hotspot list (is the highest-ranked file there because
  the data says so, or because someone pointed there first?).
- **Before a `storm-investigation` synthesis** → run the "authority bias" and "anchoring"
  guards on the persona verdicts (did one persona dominate the synthesis?).
- **In any post-mortem or bug retrospective** → apply the "hindsight bias" guard first;
  read back the pre-incident predictions before discussing what "everyone knew."
- **Before any architectural decision vote** → run the silent-ballot countermeasure for
  pluralistic ignorance.

## Versioning

Bump `metadata.version` on any change. Regenerate `VERSIONS.md` with
`python3 skillsmith/scripts/skill_registry.py write` after a bump.

## Changelog

- **1.0.0** — Initial release. Six-bias framework derived from Adam Tornhill,
  *Your Code as a Crime Scene* (Pragmatic Bookshelf, 2015) Chapters 7, 11–13.