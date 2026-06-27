---
name: invariant-inference
description: "The Architect's craft for data-driven invariant and rule synthesis, distilled from LoopInvGen (SyGuS-Comp Inv-track winner). Learn a logical rule that holds on 'good' cases and fails on 'bad' ones, prove it against an oracle, refine on counterexamples — the CEGIS skeleton: sample → learn (predicates synthesized on demand) → check → refine → stop only when the oracle cannot break it. Transfers beyond loops: data-model / state-machine invariants, CHECK constraints, RLS predicates, regression oracles for migrations, and (with the-translator) pinning fuzzy statute boundaries. Use when you must infer a rule over a domain you can sample or check but not enumerate. Triggers: 'infer the invariant', 'what must always hold here', 'learn the rule that separates these cases', 'CEGIS this', 'derive a CHECK/RLS constraint from examples'. Differentiate from legal-rule-modeling (models a KNOWN statute's arithmetic; this infers an UNKNOWN rule) and schema-evolution (changes the schema; this finds what stays true across it)."
metadata:
  version: 1.0.0
type: Skill
---

# Invariant Inference — the Architect's craft

Some rules are written down; you model those with `legal-rule-modeling`. Other rules are *latent* — true of a working system but never stated, or hiding at a boundary the statute left fuzzy. This craft recovers them. It is distilled from **LoopInvGen**, the data-driven loop-invariant generator that won the SyGuS-Comp Inv track in 2017 and 2018, and it generalizes that tool's engine into a method you can run by hand on a data model, a state machine, or a legal edge case.

The core move is **CEGIS** — Counterexample-Guided Inductive Synthesis: fit the simplest rule that holds on the good examples and fails on the bad ones, then hand it to an oracle that tries to break it. A fitted rule is a *guess*; a rule the oracle cannot break is *proven*. Never confuse the two.

## What it is / is not

- **It IS** a method for *inferring* a logical rule (invariant / precondition / constraint) over a domain too large to enumerate, from concrete good/bad examples plus a checking oracle — with the rule's vocabulary grown on demand rather than fixed upfront.
- **It is NOT `legal-rule-modeling`** — that craft transcribes a *known* statute's arithmetic into `inputs → computation → output`. This craft *discovers* a rule you don't yet have a clean statement of. They meet at fuzzy boundaries: this skill finds the cut, `legal-rule-modeling` writes it into the model and flags the residue for review. See [[legal-rule-modeling]].
- **It is NOT `schema-evolution`** — that changes the schema; this discovers the invariant that must survive the change.
- **It is NOT a tool install.** You rarely run the OCaml binary. You steal its algorithm. (CLI is documented only for the case where you do — see [the-method.md](references/the-method.md).)

## The five-step skeleton (memorize this)

```
1. SAMPLE   good states (rule must hold) + bad states (rule must fail)
2. LEARN    simplest formula true on good / false on bad;
            if a good/bad pair is indistinguishable → SYNTHESIZE a new predicate
3. CHECK    oracle (solver / spec / test) tries to find a counterexample
4. REFINE   counterexample → add to sample → back to LEARN
5. STOP     oracle finds nothing → rule is PROVEN over the whole domain
```

Four load-bearing ideas: **data-driven not structure-driven**, **no fixed feature set** (mint predicates on demand), **likely-then-proven** (never ship the fitted rule unchecked), **strengthen then guard against overshoot** (don't over-fit past the precondition).

## How to use this skill

1. **Read [applying-the-method.md](references/applying-the-method.md) first** — it is the doctrine: when to reach for this, what the Architect does with it (data-model invariants, CHECK/RLS predicates, migration regression oracles), and how the Translator uses it on statute boundaries. This is the part you carry into work.
2. **Reach for [the-method.md](references/the-method.md)** when you need the exact algorithm — Process / Record / Infer, the PIE internals (BFL PAC-CNF learner + HEnum feature synthesis), the strengthening loop, the three sufficiency conditions, the tuning knobs, and the LoopInvGen CLI.

## The three sufficiency conditions (the original loop case)

A candidate `I` is a *sufficient* loop invariant iff it is, all at once:

- **weaker than the precondition** — `∀s. P(s) ⇒ I(s)`
- **inductive over the transition** — `∀s,t. I(s) ∧ T(s,t) ⇒ I(t)`
- **stronger than the postcondition** — `∀s. I(s) ⇒ Q(s)`

Every transfer of this skill is some renaming of these three: *covers the legitimate cases*, *survives the operation*, *implies the goal*. When you adapt the method, state your three conditions explicitly before you start sampling.

## Honest limits

The result is only as good as your **bad-state coverage** — thin negatives yield a vacuously-weak rule. The word "proven" is only earned when the **oracle is sound**; with a test suite (incomplete oracle), say "validated" instead. Synthesis can stall when the true rule is large — narrow the predicate vocabulary by hand when it does.

## Provenance

Distilled 2026-06-27 from the LoopInvGen source (SyGuS-Comp solver description + repository). Upstream papers: PIE (PLDI 2016) and Hybrid Enumeration (CAV 2019), Padhi–Sharma–Millstein. Repository: <https://github.com/SaswatPadhi/LoopInvGen>.
