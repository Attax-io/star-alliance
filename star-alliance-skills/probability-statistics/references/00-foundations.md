---
type: Document
timestamp: 2026-07-02T12:28:13Z
---

# Probability Models, Random Variables, and Discrete Distributions

A probability model pairs a sample space (the set of all possible outcomes) with a probability measure that assigns numbers in [0,1] to events. Random variables are functions from that sample space into the reals, allowing probability to describe numerical quantities of interest. Together these three primitives — sample space, measure, and random variable — form the foundation of every statistical and data‑science model studied later.

---

## 1. Probability Spaces

### 1.1 Sample Space Ω
The sample space Ω (or S) is the set of all possible outcomes of an experiment. Classification:

| Type | Cardinality | Examples |
|---|---|---|
| Finite | n < ∞ | Roll of a die: {1,2,3,4,5,6}; coin: {H,T} |
| Countably infinite | ℵ₀ | Number of trials until first success; number of heads in n flips as n→∞ |
| Continuous (uncountable) | continuum | Arrival time on [0,∞); cholesterol level on (0,∞); position of a particle in ℝ³ |

A sample space is **discrete** if finite or countably infinite; otherwise it is **continuous**.

### 1.2 σ‑Algebra (Set of Events) F
A **σ‑algebra** F over Ω is a collection of subsets satisfying:
1. If A ∈ F then Aᶜ ∈ F.
2. If A₁, A₂, … ∈ F then ∪ᵢ Aᵢ ∈ F (closure under countable unions).
3. Ω ∈ F (equivalently, ∅ ∈ F).

For discrete Ω the power set 2^Ω is a valid σ‑algebra. For continuous Ω one typically uses the **Borel σ‑algebra** — the smallest σ‑algebra containing all open intervals — so any explicitly described interval, half‑line, or finite/computable set is an event.

### 1.3 Probability Measure P
A **probability measure** P : F → [0,1] satisfies three axioms (Kolmogorov):

| Axiom | Statement |
|---|---|
| Non‑negativity | P(A) ≥ 0 for all A ∈ F |
| Normalization | P(Ω) = 1 |
| Countable additivity | For disjoint A₁, A₂, … ∈ F: P(∪ᵢAᵢ) = ΣᵢP(Aᵢ) |

Equivalent compact form: 0 ≤ P(·) ≤ 1, P(Ω)=1, additive on disjoint events.

**A probability space is the triple (Ω, F, P).**

### 1.4 Direct Consequences
- P(∅) = 0.
- A ⊆ B ⇒ P(A) ≤ P(B) (monotonicity).
- P(Aᶜ) = 1 − P(A) (complement rule).
- Finite additivity follows from countable additivity by padding the sequence with empty sets.

### 1.5 Discrete Assignments
If Ω is discrete and arranged in a sequence, assign pᵢ = P({ωᵢ}) with pᵢ ≥ 0 and Σ pᵢ = 1. Then for any event A, P(A) = Σᵢ∈A pᵢ. The axioms are automatically satisfied.

---

## 2. Events and Set Operations

### 2.1 Definitions
For A, B ⊆ Ω:

| Operation | Notation | Definition |
|---|---|---|
| Union | A ∪ B | outcomes in A or B (or both) |
| Intersection | A ∩ B | outcomes in both A and B |
| Difference | A \ B or A ∩ Bᶜ | in A but not in B |
| Complement | Aᶜ | outcomes not in A |
| Empty set | ∅ | no outcomes |
| Sample space | Ω | all outcomes |

Two events are **disjoint (mutually exclusive)** if A ∩ B = ∅, equivalently P(A ∩ B) = 0. A family {Aᵢ} is a **partition** of Ω when the Aᵢ are pairwise disjoint and ∪ᵢAᵢ = Ω.

### 2.2 Algebraic Identities
- A ∪ ∅ = A, A ∩ Ω = A, A ∩ Aᶜ = ∅, A ∪ Aᶜ = Ω.
- Commutativity / associativity / distributivity of ∪ and ∩ (as in set algebra).
- **De Morgan's laws**: (A ∪ B)ᶜ = Aᶜ ∩ Bᶜ; (A ∩ B)ᶜ = Aᶜ ∪ Bᶜ.
- (A ∪ B)ᶜ ∩ (A ∪ Bᶜ)ᶜ = A ∩ Bᶜ, etc.

### 2.3 Venn Diagrams
A Venn diagram represents Ω as a rectangle and events as regions (typically circles) inside it. The overlap is A ∩ B, the union is the area covered by both circles, and the complement is everything outside the circle but inside the rectangle. They verify identities visually.

---

## 3. Interpretations of Probability

| Interpretation | Meaning | Typical Use |
|---|---|---|
| **Classical** | For m equally likely outcomes with s favorable: P = s/m | Games of chance, fair dice, random sampling without replacement |
| **Relative frequency** | Long‑run fraction of trials on which A occurs | Estimating probability from data; basis of frequentist statistics |
| **Subjective (personal)** | Strength of belief; elicited via betting odds or coherent judgment | One‑off events (election, weather, business risk) |
| **Axiomatic** | Any P satisfying Kolmogorov's axioms | Rigorous foundation; unifies the other three |

A probability assignment is **permissible** iff it satisfies the three axioms. The axioms do not tell you *how* to assign probabilities; they restrict the assignments that are valid.

---

## 4. Properties of Probability

### 4.1 Complement Rule
P(Aᶜ) = 1 − P(A). In particular, P(∅) = 0 and P(Ω) = 1.

### 4.2 Monotonicity
A ⊆ B ⟹ P(A) ≤ P(B).

### 4.3 Law of Total Probability (unconditioned form)
If {A₁, A₂, …, Aₖ} partitions Ω, then for any event B:
P(B) = Σᵢ P(Aᵢ ∩ B).

### 4.4 Inclusion–Exclusion
For two events:
P(A ∪ B) = P(A) + P(B) − P(A ∩ B).

For three events:
P(A ∪ B ∪ C) = P(A) + P(B) + P(C)
              − P(A ∩ B) − P(A ∩ C) − P(B ∩ C)
              + P(A ∩ B ∩ C).

For n events, alternate sums of probabilities of k‑fold intersections (sgn = (−1)^(k+1)). Proof by induction.

### 4.5 Subadditivity (Union Bound)
For any (countable) family A₁, A₂, …:
P(∪ᵢ Aᵢ) ≤ Σᵢ P(Aᵢ).
Equality holds iff the Aᵢ are pairwise disjoint.

### 4.6 Continuity of P
A sequence of events (Aₙ) is **increasing** (written Aₙ ↑ A) if A₁ ⊆ A₂ ⊆ … and ∪ₙ Aₙ = A; it is **decreasing** (Aₙ ↓ A) if A₁ ⊇ A₂ ⊇ … and ∩ₙ Aₙ = A. Then
P(Aₙ ↑ A) or Aₙ ↓ A  ⇒  limₙ P(Aₙ) = P(A).

**Theorem (continuity ⇔ countable additivity):** Assuming finite additivity and P(Ω)=1, countable additivity is equivalent to continuity from above and below. This justifies the use of limit arguments in computing probabilities of infinite unions/intersections.

---

## 5. Counting and Combinatorics

### 5.1 Multiplication Principle (Fundamental Theorem of Counting)
If a task has k stages with n₁ choices at stage 1, n₂ at stage 2, …, nₖ at stage k, the total number of distinct outcomes is n₁ n₂ ⋯ nₖ. Equivalent to counting sequences (s₁, s₂, …, sₖ) with sᵢ ∈ Sᵢ, giving |S₁ × S₂ × ⋯ × Sₖ| = Π|Sᵢ|.

### 5.2 Permutations
A **permutation** is an ordered arrangement of r distinct objects chosen from n. The number of such arrangements is
_nPᵣ = n!/(n − r)! = n(n − 1)(n − 2) ⋯ (n − r + 1).
When r = n this is n! (full permutations).

### 5.3 Combinations and the Binomial Coefficient
The number of unordered subsets of size r chosen from n distinct objects is
C(n, r) = ₙCᵣ = n!/(r! (n − r)!).

**Key identity:** Σ_{r=0}^{n} C(n, r) = 2ⁿ (binomial theorem with x = y = 1).

### 5.4 Ordered Sequences of Subsets (Multinomial)
The number of ways to choose an ordered family of disjoint subsets of sizes k₁, k₂, …, k_l (with Σ kᵢ ≤ n) from an n‑set is
n! / (k₁! k₂! ⋯ k_l! (n − Σkᵢ)!).

When the family is an **ordered partition** with Σkᵢ = n, this reduces to the **multinomial coefficient**
n! / (k₁! k₂! ⋯ k_l!).
C(n; k₁, …, k_l) = C(n, k₁) C(n − k₁, k₂) ⋯ C(k_{l−1}+k_l, k_{l−1}).

### 5.5 Useful Special Cases
- Number of bridge hands (4 ordered 13‑card hands from 52): 52!/(13!)⁴.
- Probability of exactly k heads in n fair‑coin flips: C(n, k)/2ⁿ.

---

## 6. Conditional Probability

### 6.1 Definition
For events A, B ∈ F with P(B) > 0,
P(A | B) = P(A ∩ B) / P(B).

**Interpretation:** restrict attention to the reduced sample space B; within B, the probability of A is the fraction of probability mass that also lies in A.

**Sanity checks:** P(A | Ω) = P(A); P(Ω | B) = 1; if A, B disjoint with P(B)>0 then P(A | B) = 0; P(B | B) = 1.

### 6.2 Multiplication Rule (Chain Rule)
P(A ∩ B) = P(A) P(B | A) = P(B) P(A | B)   (whenever P(A), P(B) > 0).

For multiple events, **chain rule**:
P(A₁ ∩ A₂ ∩ ⋯ ∩ Aₙ) = P(A₁) P(A₂ | A₁) P(A₃ | A₁∩A₂) ⋯ P(Aₙ | A₁ ∩ ⋯ ∩ A_{n−1}).

### 6.3 Law of Total Probability (conditioned form)
If {A₁, …, Aₖ} partitions Ω with each P(Aᵢ) > 0, then for any B:
P(B) = Σᵢ P(Aᵢ) P(B | Aᵢ).

This is the workhorse for two‑stage (or multi‑stage) experiments: marginalize out the first stage.

### 6.4 Bayes' Theorem
For events A, B with P(A), P(B) > 0:
P(A | B) = P(B | A) P(A) / P(B)
       = P(B | A) P(A) / [ Σᵢ P(B | Aᵢ) P(Aᵢ) ]   (using total probability with partition {Aᵢ}).

**Interpretation:** P(A) is the **prior**; P(A | B) is the **posterior**; the factor P(B | A)/P(B) is the **likelihood ratio** that updates belief after observing B.

For a partition {A₁, …, Aₙ} and evidence B:
P(Aᵣ | B) = P(Aᵣ) P(B | Aᵣ) / Σᵢ P(Aᵢ) P(B | Aᵢ),   r = 1, …, n.

**Pitfalls:**
- P(A | B) ≠ P(B | A) in general (the "prosecutor's fallacy"). Symmetry holds only when priors are equal.
- Bayesian assignments are **consistent** when they satisfy the axioms; subjective probabilities violating additivity should be rejected.
- Zero prior: if P(A) = 0, no amount of evidence (with positive likelihood) can make P(A | B) > 0.

### 6.5 Independence
Two events A, B ∈ F are **independent** if
P(A ∩ B) = P(A) P(B).

Equivalent (when P(A), P(B) > 0) to P(A | B) = P(A) and P(B | A) = P(B). Independence is symmetric: A ⊥ B iff B ⊥ A; if P(B) = 0 the product rule still defines independence.

**Pairwise vs. mutual independence.** For {A₁, …, Aₙ}:
- **Pairwise independent:** every pair is independent.
- **Mutually independent:** for any subcollection {Aᵢ₁, …, Aᵢₖ}, P(∩ⱼ Aᵢⱼ) = Πⱼ P(Aᵢⱼ).
- Mutual independence is strictly stronger than pairwise.

### 6.6 Conditional Independence
Events A, B are **conditionally independent given C** (with P(C) > 0) if
P(A ∩ B | C) = P(A | C) P(B | C),
equivalently P(A | B, C) = P(A | C).

**Neither implies the other:** independence does not imply conditional independence (events may become dependent once a common cause is known), and vice versa (events may be independent marginally but become coupled once conditioning reveals a confounder).

---

## 7. Random Variables

### 7.1 Definition
Given a probability space (Ω, F, P), a **random variable** is a measurable function X : Ω → ℝ. "Measurable" means that for every Borel set B, X⁻¹(B) ∈ F, so P(X ∈ B) is well defined.

If ω is the realized outcome, x = X(ω) is a **realization**. We write random variables in upper case (X, Y, Z) and their values in lower case (x, y, z).

**Standard shorthand:**
P(X ∈ S) := P({ω : X(ω) ∈ S}),  P(X = x) := P({ω : X(ω) = x}).

### 7.2 Special Constructions
- **Constant random variable:** X(ω) = c for all ω. Then P(X = c) = 1. Useful for centering.
- **Indicator of an event A:** 1_A(ω) = 1 if ω ∈ A, 0 otherwise. By construction, 1_A ~ Bernoulli(P(A)). Indicators convert events into numbers and are invaluable for proofs.
- **Arithmetic combinations:** if X, Y are RVs on the same space, so are X + Y, XY, g(X) for any measurable g, X ∧ Y, X ∨ Y, X⁺, X⁻, |X|, etc. Random variables are closed under pointwise operations.

### 7.3 Distribution of a Random Variable
The **distribution** of X is the push‑forward measure μ_X(B) = P(X ∈ B) for Borel sets B. Specifying the distribution is usually easier than specifying (Ω, F, P) explicitly. Two random variables are **identically distributed** if μ_X = μ_Y; they are **equal** (X = Y) if X(ω) = Y(ω) for all ω, which is stronger.

---

## 8. Discrete Random Variables and Their Distributions

A random variable X is **discrete** if it takes at most countably many values. It is fully described by its **probability mass function (pmf)**
p_X(x) = P(X = x).

The pmf satisfies p_X(x) ≥ 0 and Σ_x p_X(x) = 1. Conversely, any such function defines a valid distribution on the support D = {x : p_X(x) > 0}. For any event S ⊆ D,
P(X ∈ S) = Σ_{x ∈ S} p_X(x).

### 8.1 Bernoulli (Indicator)
Models a single yes/no trial.
- Support: {0, 1}.  pmf: p_X(1) = p, p_X(0) = 1 − p, where p ∈ [0, 1].
- Mean: p.  Variance: p(1 − p).  MGF: 1 − p + p e^t.
- The indicator 1_A is Bernoulli with parameter P(A). Used to encode any event as a number and to build more complex RVs by summing indicators.

### 8.2 Binomial (n, p)
Number of successes in n independent Bernoulli(p) trials.
- Support: k = 0, 1, …, n.
- pmf: P(X = k) = C(n, k) pᵏ (1 − p)^{n − k}.
- Mean: np.  Variance: np(1 − p).
- MGF: (1 − p + p e^t)ⁿ.
- **Use when:** you have a fixed number of independent trials with the same success probability, no other stopping rule. (Pólya's urn, hypergeometric, or negative‑binomial setup ⇒ don't use Binomial.)

### 8.3 Geometric (p)
Number of trials until (and including) the first success in independent Bernoulli(p) trials.
- Support: k = 1, 2, 3, …
- pmf: P(X = k) = (1 − p)^{k − 1} p.
- Mean: 1/p.  Variance: (1 − p)/p².
- **Memoryless property:** P(X > m + n | X > m) = P(X > n). This is the only discrete memoryless distribution.
- **Use when:** trials are i.i.d. and you stop at the first success; e.g. number of calls until a sale, number of Bernoulli trials until a defect appears.

### 8.4 Negative Binomial (r, p)
Number of trials until the r‑th success, with independent Bernoulli(p) trials.
- Support: k = r, r+1, r+2, …
- pmf: P(X = k) = C(k − 1, r − 1) pʳ (1 − p)^{k − r}.
- Mean: r/p.  Variance: r(1 − p)/p².
- Reduces to Geometric when r = 1.

### 8.5 Hypergeometric (N, K, n)
Number of "successes" in n draws **without replacement** from a finite population of N items containing K successes.
- Support: k = max(0, n − (N − K)), …, min(n, K).
- pmf: P(X = k) = C(K, k) C(N − K, n − k) / C(N, n).
- Mean: nK/N.  Variance: n (K/N) (1 − K/N) · (N − n)/(N − 1).
- **Use when:** sampling without replacement from a finite, known population; e.g. defective items in a batch, spades in a bridge hand.
- **Approximation:** when n/N is small (rule of thumb n ≤ N/10), Hypergeometric ≈ Binomial(n, p = K/N).

### 8.6 Poisson (λ)
Number of events in a fixed interval when events occur independently at constant rate λ > 0.
- Support: k = 0, 1, 2, …
- pmf: P(X = k) = e^{−λ} λᵏ / k!.
- Mean: λ.  Variance: λ.  MGF: exp(λ(e^t − 1)).
- **Use when:** events are independent, occur at a constant average rate, and the probability of two events at exactly the same instant is zero. Approximates Binomial(n, p) when n is large and p is small with np = λ.

### 8.7 Multinomial (n; p₁, …, p_k)
A generalization of the Binomial: counts in k categories with n independent trials and category probabilities p₁, …, p_k (Σ pᵢ = 1).
- Joint pmf: P(X₁ = n₁, …, X_k = n_k) = n!/(n₁! ⋯ n_k!) p₁^{n₁} ⋯ p_k^{n_k}, with Σ nᵢ = n.
- Marginals: each Xᵢ ~ Binomial(n, pᵢ); pairs have a multinomial‑derived covariance Cov(Xᵢ, Xⱼ) = −n pᵢ pⱼ for i ≠ j.
- **Use when:** classifying each of n independent trials into one of k ≥ 2 categories.

### 8.8 Discrete Uniform on {a, a+1, …, b}
- pmf: p_X(x) = 1/(b − a + 1) for each integer x in [a, b].
- Mean: (a + b)/2.  Variance: ((b − a + 1)² − 1)/12.
- **Use when:** each integer in a finite range is equally likely (a fair die is Uniform{1, …, 6}).

### 8.9 Family Summary Table

| Distribution | Support | pmf P(X = x) | Mean | Variance |
|---|---|---|---|---|
| Bernoulli(p) | {0,1} | pˣ (1−p)^{1−x} | p | p(1−p) |
| Binomial(n,p) | 0…n | C(n,x) pˣ (1−p)^{n−x} | np | np(1−p) |
| Geometric(p) | 1,2,… | (1−p)^{x−1} p | 1/p | (1−p)/p² |
| NegBin(r,p) | r, r+1,… | C(x−1, r−1) pʳ (1−p)^{x−r} | r/p | r(1−p)/p² |
| Hypergeom(N,K,n) | 0…min(n,K) | C(K,x)C(N−K,n−x)/C(N,n) | nK/N | n K/N · (1−K/N) · (N−n)/(N−1) |
| Poisson(λ) | 0,1,2,… | e^{−λ} λˣ/x! | λ | λ |
| Multinomial(n; p₁…p_k) | nᵢ with Σnᵢ=n | n!/(n₁!⋯n_k!) Πpᵢ^{nᵢ} | npᵢ (marginal) | npᵢ(1−pᵢ); Cov=−npᵢpⱼ |
| Discrete Unif{a..b} | integers a…b | 1/(b−a+1) | (a+b)/2 | ((b−a+1)²−1)/12 |

---

## 9. Cumulative Distribution Functions

The **CDF** of any real‑valued RV X is
F_X(x) = P(X ≤ x),   x ∈ ℝ.

### 9.1 Properties (any RV)
1. F is non‑decreasing.
2. lim_{x → −∞} F(x) = 0;  lim_{x → +∞} F(x) = 1.
3. F is right‑continuous (lim_{y ↓ x} F(y) = F(x)); for discrete RVs it is right‑continuous with jumps of size p_X(k) at each atom k.
4. P(a < X ≤ b) = F(b) − F(a).
5. P(X = x) = F(x) − lim_{y ↑ x} F(y) (the jump at x).

For a discrete RV with pmf p_X,
F(x) = Σ_{k ≤ x} p_X(k).
For a continuous RV with pdf f, F(x) = ∫_{−∞}^x f(t) dt and f(x) = F′(x) wherever F is differentiable.

The CDF completely determines the distribution: any F satisfying properties 1–3 is a valid CDF of some RV.

---

## 10. Operations and Functions of Random Variables

If X is a discrete RV with pmf p_X and g : ℝ → ℝ is any function, then Y = g(X) is a RV with pmf
p_Y(y) = Σ_{x : g(x) = y} p_X(x).

If g is injective, this simplifies to p_Y(y) = p_X(g⁻¹(y)). For sums of independent discrete RVs use convolution: p_{X+Y}(k) = Σ_x p_X(x) p_Y(k − x).

**Pitfalls:**
- Do not confuse g(X)'s pmf with g evaluated at expected values: E[g(X)] ≠ g(E[X]) in general (Jensen's inequality).
- When inverting a non‑monotonic g, sum probabilities over all preimages.

---

## 11. Practical Computation Tips

| Situation | Use this rule / tool |
|---|---|
| "At least one" of many independent events | Complement: 1 − Π(1 − pᵢ) |
| "All of" several independent events | Multiplication: Π pᵢ |
| Probability of union of many events | Union bound ≤ Σ; exact via inclusion–exclusion |
| Sequential sampling without replacement | Multiplication rule updating denominator (e.g. 4/52 · 3/51 · …) |
| Geometric / waiting‑time problem | Geometric(p); check independence and constant p |
| Fixed n, constant p, count successes | Binomial(n, p) |
| Finite batch inspection | Hypergeometric |
| Independent rare events over interval/time | Poisson with rate λ = (rate) × (length) |
| Stage‑1 prior, stage‑2 likelihood given stage‑1 | Law of total probability, then Bayes to invert |
| Probability depends on who/what is acting | Check independence carefully; otherwise condition |

---

## 12. Common Modeling Pitfalls

1. **Conflating mutually exclusive with independent.** If A ∩ B = ∅ with P(A), P(B) > 0, they are *negatively maximally dependent* — seeing A rules out B, so P(B | A) = 0 ≠ P(B). Independence is the opposite end: learning one tells you nothing about the other.
2. **Confusing P(A | B) with P(B | A).** Use Bayes' rule; the asymmetry comes from the priors.
3. **Adding probabilities of overlapping events.** P(A ∪ B) = P(A) + P(B) only when A, B are disjoint; otherwise subtract the intersection (inclusion–exclusion).
4. **Treating draws as independent when sampling without replacement.** Use conditional probabilities; only with replacement (or infinite population) is independence valid.
5. **Assigning P(X = x) > 0 to uncountably many x with total 1.** Impossible — by countable additivity, a discrete RV can have at most countably many atoms.
6. **Forgetting to renormalize after conditioning.** P(· | B) is itself a probability measure with P(B | B) = 1.
7. **Equating "P = 0" with "impossible."** P(A) = 0 implies A is *almost surely* impossible (a.s.), but for continuous RVs the atom is still a possible outcome of the experiment.

Probability models, conditional rules, and the discrete distributions above form a self‑contained toolkit for representing uncertainty, computing with it, and updating it in light of new evidence.
