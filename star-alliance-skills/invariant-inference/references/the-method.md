---
type: Document
title: The method
description: Implementation-oriented reference for LoopInvGen's data-driven loop-invariant inference — Process, Record, Infer, PIE, BFL, HEnum, the CEGIS strengthening loop, and the CLI.
timestamp: 2026-06-27T00:00:00Z
---

# LoopInvGen — Reference

LoopInvGen is a data-driven generator of **provably sufficient** loop invariants for programs encoded in the **SyGuS-INV** format. It was the **Inv-track winner** at SyGuS-Comp 2017 and 2018. Its backbone is **PIE** (Precondition Inference Engine), which reduces loop-invariant inference to a sequence of precondition-inference problems solved by **CEGIS** with automatic feature synthesis.

This document is an implementation-oriented reference. It captures the exact algorithm, data flow, and configuration knobs so that the method can be re-implemented or reasoned about without the original paper.

---

## 1. Problem Statement

A **SyGuS-INV problem** is a tuple

$$
\Sigma \;=\; \langle P,\; Q,\; T,\; \Delta \rangle
$$

where

| Symbol | Meaning |
|--------|---------|
| $P(s)$ | precondition on the entry state $s$ |
| $Q(s)$ | postcondition on the exit state $s$ |
| $T(s, s')$ | state transition relation (one loop iteration, from $s$ to $s'$) |
| $\Delta$ | auxiliary relations (define–funs) referenced by $P$, $Q$, or $T$ |

A formula $I$ over the program variables is a **sufficient loop invariant** iff it satisfies all three of the following conditions simultaneously:

$$
\begin{aligned}
\text{(PRE) }    &\forall s.\; P(s) \Rightarrow I(s) \\
\text{(TRANS) }  &\forall s, t.\; I(s) \wedge T(s, t) \Rightarrow I(t) \\
\text{(POST) }   &\forall s.\; I(s) \Rightarrow Q(s)
\end{aligned}
$$

The goal of LoopInvGen is to synthesize some $I$ that satisfies all three, using a **data-driven** approach that begins with **no features** and synthesizes them on demand.

---

## 2. Architecture

```
                ┌──────────────────────────────────────────────────────┐
                │                       Process                         │
                │   (static simplification + early correctness checks) │
                └──────────────────────────┬───────────────────────────┘
                                           │  Σ′  (simplified SyGuS-INV)
                                           ▼
                ┌──────────────────────────────────────────────────────┐
                │                       Record                         │
                │  (sample reachable program states via constraint    │
                │   solving; merge from parallel instances)            │
                └──────────────────────────┬───────────────────────────┘
                                           │  𝒵  (set of states)
                                           ▼
                ┌──────────────────────────────────────────────────────┐
                │                       Infer                          │
                │  outer strengthening loop, with an inner CEGIS loop  │
                │   ┌──────────────┐    ┌──────────────┐               │
                │   │     PIE      │ ←→ │    Checker   │  (Z3)         │
                │   │ BFL + Synth  │    │ PRE/TRANS/POST               │
                │   └──────────────┘    └──────────────┘               │
                └──────────────────────────┬───────────────────────────┘
                                           │  I  (sufficient invariant)
                                           ▼
                                        Verifier
```

Three top-level components:

- **Process** — static analysis pass, plus an early postcondition check (`Q` itself is an invariant ⇒ done) and unsolvability check (`P ⇒ Q` fails ⇒ terminate with `PASS (NO SOLUTION)`).
- **Record** — collects a multiset of reachable program states $\mathcal{Z}$ using the SMT solver as an execution engine.
- **Infer** — iteratively refines a candidate invariant via an inner CEGIS loop that calls **PIE** + **Checker**.

The two off-the-shelf reasoning backends are:

- **Checker** = Z3 (used for both `GetModel` and verification of PRE / TRANS / POST).
- **PIE** = PAC boolean-function learner (**BFL**) + feature synthesizer (**Synth** = HEnum over LIA).

---

## 3. Component: `Process`

Performs two cheap pre-flights and one syntactic simplification.

### 3.1 Early checks

1. **Early postcondition check** — before sampling or learning anything, ask Z3 whether
   $$ \forall s.\; P(s) \wedge \bigwedge_{\text{defs in } \Delta} \Rightarrow Q(s). $$
   If this holds (and similarly $\forall s.\; P(s) \Rightarrow Q(s)$ after using $\Delta$), output `Q` and terminate.

2. **Unsolvability detection** — if $\exists s.\; P(s) \wedge \neg Q(s)$ is satisfiable, terminate immediately with `PASS (NO SOLUTION)`. LoopInvGen also keeps a running set of known states and terminates as soon as one of them is a **negative example** w.r.t. the specification.

### 3.2 Unused-variable elimination

Define a variable $v$ as *used* iff it appears in $P$, in $Q$, or in $T$ (as either $v$ or $v'$) after inlining all relations from $\Delta$.

Algorithm:

1. Build the call graph of all relations in $\Delta \cup \{P, Q, T\}$.
2. Perform **3 topological sorts** rooted at $P$, $Q$, and $T$.
3. From the leaves upward, label the *used* formal parameter set $V_R$ of every relation $R$ by unioning the labels of the actual arguments at each call site.
4. Compute
   $$ V \;=\; V_P \;\cup\; \{ v \mid v \in V_T \lor v' \in V_T \} \;\cup\; V_Q. $$

Only variables in $V$ are tracked during `Record` and `Infer`.

**Running example.** For `trex1_vars.sl` (variables $x, y$; precondition `x < y`; postcondition `x >= 1`):
$$ V_P = \{x\},\;\; V_T = \{x, y, x'\},\;\; V_Q = \{x, y\},\;\; V = \{x, y\}. $$

The simplified problem is then serialized to a binary form so the downstream components do not re-parse SyGuS.

---

## 4. Component: `Record`

A constraint solver is used as an interpreter: each "execution step" is a single call to the SMT solver.

### 4.1 Algorithm

```
Record(Σ = (P, Q, T, Δ), V, n):
    𝒵 ← ∅
    while True:
        m ← GetModel( Δ ∧ P(m) ∧ (⋀_{s ∈ 𝒵}  m ≠ s),  V )
        if m = NONE:  break
        𝒵 ← 𝒵 ∪ RecordStatesFrom(m, n − |𝒵|)
        if |𝒵| = n:  break
    return 𝒵

RecordStatesFrom(m, k):
    states ← ⟨m⟩
    while |states| < k:
        m ← GetModel( Δ ∧ T(m, m'),  { v′ | v ∈ V } )
        if m = NONE:  break
        states := states ⋅ ⟨m⟩
    return states
```

- `GetModel(φ, V)` returns a satisfying assignment to the variables in $V$ under $\varphi$, or `NONE` if unsatisfiable. Variables of $V$ not constrained by $\varphi$ are filled in by a **pseudo-random number generator (PRNG)**.
- Line 3 of `Record` requests an *unseen* model of $P$ so each new trajectory starts from a fresh initial state.
- `RecordStatesFrom` performs at most $k$ loop iterations from a given starting state; on early termination (loop guard becomes false, or no model exists) it returns the trajectory so far.
- The number of program states collected per problem is **512** (was 6400 in earlier versions; the better `Record` coverage allowed reducing it).

### 4.2 Parallel `Record`

By default **2** instances of `Record` run in parallel with **different PRNG seeds**; their collected states are merged (set-union, with duplicates removed) before being passed to `Infer`. The merge prefers variety because PIE/PIE's BFL is sensitive to redundancy in the sample.

### 4.3 On-demand extension

The inner phase of `Infer` (line 11, `RecordStatesFrom(c, NumStepsOnRestart)`) reuses the same routine to extend state coverage when an over-strong candidate is detected.

---

## 5. Component: `Infer`

The main algorithm. Pseudocode (faithful to the paper):

```
Infer(Σ, 𝒵, Θ):
    I ← Q                                       # weakest invariant satisfying POST
    while True:
        B ← ∅                                    # counterexample set
        while True:                              # ── inner CEGIS loop ──
            ρ ← PIE(𝒵, B, Θ)                     # likely precondition
            c ← Checker( ∀s, t.  ρ(s) ⇒ I(s) ∧ T(s, t) ⇒ I(t) )
            if c = NONE:  break
            B ← B ∪ { c }                        # add 32 counterexamples per round
        I ← I ∧ ρ
        c ← Checker( ∀s.  P(s) ⇒ I(s) )          # PRE check
        if c ≠ NONE:                             # I stronger than P ⇒ re-explore
            𝒮 ← RecordStatesFrom(c, Θ.NumStepsOnRestart)
            return Infer(Σ, 𝒵 ∪ 𝒮, Θ)
        elif ρ = ⊤:  break                       # no further strengthening needed
    return I
```

The structure is two nested loops:

- **Outer strengthening loop** (lines 2–12). At iteration $i$, the candidate is
  $$ I_i \;=\; Q \;\wedge\; \bigwedge_{j=1}^{i} \rho_j. $$
  Each $\rho_j$ is a precondition that, when conjoined, makes the new $I_j$ inductive.
- **Inner CEGIS loop** (lines 4–7). $\rho_j$ is a *likely* precondition learned by PIE; the Checker either confirms it is a provably sufficient strengthening of $I_{j-1}$, or produces a counterexample state that is added to the negative set $B$.

### 5.1 Why this shape?

- **Initialize $I \leftarrow Q$** — guarantees POST for free. (The original PIE paper initialized with a learned invariant for `{I} skip {Q}`; LoopInvGen found this initial value too strong in some benchmarks.)
- **Strengthening, not weakening** — for TRANS to fail on candidate $I$, we want the *smallest* additional constraint that, when conjoined, restores inductiveness. That constraint is itself a precondition-inference problem: find a formula $\rho$ s.t.
  $$ \forall s, t.\; I(s) \wedge \rho(s) \wedge T(s, t) \Rightarrow I(t). $$
  This is exactly what PIE does.
- **PRE check before terminating** — conjoining many $\rho_j$ may overshoot and make $I$ stronger than $P$. The PRE check guards against this. On failure we extend $\mathcal{Z}$ from the offending state and **recurse** with the augmented dataset.
- **Stop when $\rho = \top$** — if the strengthening needed is trivial, the current $I$ is already inductive; combined with PRE/POST, it is sufficient.

### 5.2 Multiple counterexamples per round

A key performance change since SyGuS-Comp 2018: **32** counterexamples are added to $B$ per round, not 1. This substantially reduces the number of CEGIS iterations needed.

### 5.3 Confluence of CEGIS rounds

Given a fixed $(\mathcal{Z}, B, \Theta)$ and a fixed internal seed, PIE is reproducible — re-running the same CEGIS round yields the same $\rho$. This matters for debugging: a non-terminating `Infer` is reproduced by replaying the recorded states, not by re-sampling.

---

## 6. Component: PIE (inside `Infer`)

`PIE(𝒵, B, Θ)` is the data-driven precondition learner from the PLDI 2016 paper. It takes

- $\mathcal{Z}$ — set of "good" program states (a precondition must be true here),
- $B$ — set of "bad" program states (a precondition must be false here),
- $\Theta$ — knobs (notably `conflict-group-size` = **64** in LoopInvGen),

and returns a boolean combination $I$ of *features* such that $I$ is true on all of $\mathcal{Z}$ and false on all of $B$. (Here "feature" means an atomic predicate over program variables — a synthesized LIA expression.)

### 6.1 Two subcomponents

- **BFL (Boolean Function Learner)** — a standard **PAC** algorithm that learns an arbitrary **CNF** formula, biased toward small formulas. It consumes a feature vocabulary and returns a candidate composition.
- **Synth (Feature Synthesizer)** — **HEnum** (Hybrid Enumeration), which synthesizes new LIA expressions from a grammar. HEnum *interleaves* exploration of subgrammars of different expressiveness, reducing overfitting and converging faster than uniform random or pure enumerative search.

### 6.2 Why no initial features?

LoopInvGen starts with an **empty** feature set. BFL cannot distinguish any pair of states until a feature is added that separates them. PIE detects these "conflicts" (pairs $(z \in \mathcal{Z}, b \in B)$ indistinguishable under the current feature vocabulary) and asks **Synth** to produce, for some **conflict group** of size `conflict-group-size = 64`, a new feature that separates at least one conflict. This is the on-demand feature growth that distinguishes LoopInvGen from fixed-feature tools such as **ICE-DT**.

### 6.3 Parallel `Infer` via `PLearn`

Since SyGuS-Comp 2018, LoopInvGen runs **several parallel instances of `Infer`**, each restricted to a different **subgrammar of the LIA / NIA grammar** (this is `PLearn`). The first one to return a sufficient invariant wins. This reduces overfitting because each subgrammar is biased toward a different shape of expression.

---

## 7. Configuration Parameters (Θ)

| Parameter | Default | Meaning |
|-----------|---------|---------|
| `NumStatesToRecord` | 512 | Target size of the state set $\mathcal{Z}$ collected by `Record`. |
| `NumStepsOnRestart` | (small) | Number of extra transitions recorded from a PRE counterexample before restarting `Infer`. |
| `ConflictGroupSize` | 64 | Number of states per group when PIE queries Synth for a new distinguishing feature. |
| `NumCexPerRound` | 32 | Number of counterexamples added to $B$ per CEGIS round. |
| `NumParallelInfer` | several | Number of parallel `Infer` instances with different subgrammars. |
| `NumParallelRecord` | 2 | Number of parallel `Record` instances with different PRNG seeds. |
| `Logic` | LIA | Synthesis theory (the Inv track of SyGuS-Comp uses LIA). |

---

## 8. Implementation Notes

- **Language:** OCaml (≥ 4.08, with `flambda` recommended). Build system: `dune`.
- **Backends:** Z3 4.8.7+ for both `GetModel` and `Checker`. A single Z3 subprocess is launched; LoopInvGen relies on Z3 **scopes** to cache assertions between calls and minimize query size.
- **AST pruning:** before invoking the theorem prover, a syntactic pass removes redundant ASTs (e.g. `_+ x - x`, `1 * _`).
- **SyGuS-IF support:** arbitrary auxiliary relations in $\Delta$ are supported (not just P/Q/T). Full SyGuS-IF syntax is parsed once in `Process` and serialized to an internal binary form.
- **Non-LIA:** experimental support for **NLIA** via `(set-logic NLIA)`.
- **External features:** the CLI flag `-F <file.smt2>` preseeds the feature vocabulary from an SMTLib2 file (used in CHI_InvGame benchmarks).

---

## 9. CLI

```
./loopinvgen.sh [options] <benchmark.sl>

  -t N     wall-clock timeout (seconds) for the inference algorithm
  -v       verify the generated invariant against the benchmark after inference
  -F FILE  preseed features from SMTLib2 file
  -h       full help
```

### 9.1 Verdicts (with `-v`)

| Verdict | Meaning |
|---------|---------|
| `PASS` | Generated invariant verifies PRE, TRANS, and POST. |
| `PASS (NO SOLUTION)` | Benchmark is invalid ($P \not\Rightarrow Q$); no invariant returned. |
| `FAIL {pre; trans; post; …}` | Generated invariant fails one or more of {PRE, TRANS, POST}. |
| `FAIL (NO SOLUTION)` | Benchmark is invalid AND a (non-`false`) invariant was nevertheless returned. |
| `[TIMEOUT] <verdict>` | Inference timed out; `<verdict>` is one of the above (using `false` as the candidate). |

### 9.2 Batch benchmarking

```
./scripts/test_all.sh -b benchmarks/LIA [-t N] [-l old_log_dir] [-T tool] [-- tool-args]
```

- Runs the solver on every `.sl` file under the benchmark tree, applies the verifier, and records the verdict.
- `-l <old_log_dir>` re-runs only the previously failing benchmarks.
- `-T <tool>` substitutes a different SyGuS-format solver for benchmarking.
- `[SKIPPED] PASS` indicates a benchmark that was already passing on a prior run.

---

## 10. End-to-End Data Flow (summary)

```
.sl file
  │
  ▼
Process ──► simplified Σ′  ──►  binary dump
  │                              │
  │                              ▼
  │                          Record (× 2 parallel) ──► 𝒵 (≈ 512 states)
  │                                                    │
  │                                                    ▼
  │                                                Infer (× N parallel via PLearn)
  │                                                  │    ┌──── PIE ────┐
  │                                                  └──► │ BFL + HEnum │ ─► ρ
  │                                                       └─────────────┘
  │                                                          ▲     │
  │                                                          │     ▼
  │                                                       Checker (Z3)
  │                                                          │
  ▼                                                          ▼
(optional) Verifier ◄──── I (sufficient invariant) ◄────── done?
```

LoopInvGen returns the first sufficient invariant produced by any of the parallel `Infer` instances. The verifier then independently checks PRE, TRANS, POST on that invariant and emits the verdict.

---

## 11. Key References

- **PLDI 2016** — Padhi, Sharma, Millstein. *Data-Driven Precondition Inference with Learned Features.* Original PIE technique.
- **CAV 2019** — Padhi et al. *A Hybrid Enumeration Algorithm for … overfitting in program synthesis.* Introduces HEnum, used as `Synth` inside PIE.
- **Alur et al. 2016** — *SyGuS-Comp 2016/2017/2018/2019 reports.* Defines the Inv-track input format.
- **Garg et al. 2016** — *ICE-DT.* Prior fixed-feature technique contrasted in the introduction.
- **Dillig et al. 2013** — *HOLA.* The strengthening-loop pattern in `Infer` is inspired by HOLA.

Repository: <https://github.com/SaswatPadhi/LoopInvGen>
