---
type: Document
title: Applying the method
description: How the Architect and Interpreter transfer LoopInvGen's CEGIS skeleton to data-model invariants and legal rule boundaries.
timestamp: 2026-06-27T00:00:00Z
---

# Applying the method — the transfer

LoopInvGen solves loop invariants. But the *shape* of its algorithm is a general recipe for a much larger class of problems the guild meets every week: **learn a logical rule that separates good cases from bad cases, prove it, and refine it on counterexamples.** This file is the part a member actually carries into work. The mechanics live in [the-method.md](the-method.md); this is the doctrine.

## The reusable skeleton (CEGIS)

Strip LoopInvGen down and you get **Counterexample-Guided Inductive Synthesis**:

```
1. SAMPLE    collect concrete good states (must satisfy) and bad states (must not)
2. LEARN     fit the simplest formula that holds on good, fails on bad
             — and if no existing vocabulary separates a good/bad pair (a CONFLICT),
               SYNTHESIZE a new predicate on demand instead of giving up
3. CHECK     ask an oracle (solver / spec / test) whether the formula is actually correct
4. REFINE    if the oracle returns a counterexample, add it to the sample and go to 2
5. STOP      when the oracle finds no counterexample → the rule is proven, not just fitted
```

Four ideas carry the weight, and each is independently stealable:

- **Data-driven, not structure-driven.** When the artifact (a statute, a schema, a transition relation, a contract) is too tangled to reason about top-down, reason about its *behavior* — concrete examples — instead.
- **No fixed feature set.** Do not commit upfront to the vocabulary of predicates. Start empty; mint a new predicate only when two cases you must separate are currently indistinguishable. This is the single biggest win over template-based tools (ICE-DT etc.).
- **Likely-then-proven.** Learning gives you a *likely* rule fast (it only fits the sample). Never ship the likely rule — pass it to a checker that can produce a counterexample. The loop converges to a rule that is *provably* right on the whole domain, not just the sample.
- **Strengthen monotonically, then guard against overshoot.** Start from the weakest thing that satisfies the goal (LoopInvGen starts `Inv = Q`), conjoin constraints to fix violations, and after each conjunction check you have not become *stronger than the precondition* — i.e. that you have not over-fit and excluded legitimate cases.

## When a member should reach for this

The trigger is a problem that smells like *"infer a rule that must hold over an unbounded/large domain, where I can generate or check examples but can't enumerate the domain."* Concretely:

### the-architect (primary owner)
- **Deriving an invariant for a data model or state machine** — "what must always be true across these rows / this status lifecycle?" Sample valid and invalid states, learn the constraint, check it against the schema and triggers, refine. Output a CHECK constraint, an RLS predicate, or a trigger guard that is *proven* against the examples, not eyeballed.
- **Reverse-engineering an implicit spec** from a working system whose rules were never written down: treat current data as good states, known-bad inputs as bad states, synthesize the predicate that separates them.
- **Migration safety**: an invariant that holds before *and* after a refactor is a regression oracle. Infer it on the old system, assert it on the new.

### the-interpreter (shared owner) — bridge to [[legal-rule-modeling]]
`legal-rule-modeling` turns a statute into `inputs → computation → output`. This skill sharpens its hardest step: **pinning down a boundary the text leaves fuzzy.** Where a bracket edge, an exemption, or an eligibility test is ambiguous, you have worked examples (cases that qualify, cases that don't). Treat them as good/bad states:
- Synthesize the predicate that separates qualifying from non-qualifying cases.
- The "no fixed features" idea = do not assume the statute's cut is on a variable you already named; the separating feature might be a *combination* (income − deductions ≥ cap), and you mint it on demand.
- The "likely-then-proven" loop = every candidate rule gets checked against the next worked example before you write it into the model; a failing example is a counterexample, not a nuisance.
- Whatever boundary refuses to be separated cleanly is a **genuine ambiguity** — exactly the thing `legal-rule-modeling` says to flag for the team-review disclaimer. This skill tells you *which* boundary, with evidence.

## What stays in the paper, what comes with you

- **Stays in LoopInvGen:** OCaml, Z3 wiring, the SyGuS-INV file format, the 512-states / 32-cex / conflict-group-64 tuning. Useful only if you are literally running the tool (see the CLI section of [the-method.md](the-method.md)).
- **Comes with you everywhere:** the five-step CEGIS skeleton, the four ideas above, and the discipline of *never trusting a fitted rule until an oracle has failed to break it.*

## Honest limits

- The method finds a rule **consistent with the examples and the oracle** — it is only as good as your bad-state coverage. Thin negative examples → an over-weak rule that passes the check vacuously. Push for adversarial bad cases.
- The checker must be sound for the claim to be "proven." A test suite is a weaker oracle than a solver; be explicit about which you have, and downgrade the word "proven" to "validated" when the oracle is incomplete.
- Synthesis can diverge or be slow when the true rule is large. LoopInvGen fights this with parallel subgrammars (PLearn); a member fights it by narrowing the predicate vocabulary by hand when the search stalls.
