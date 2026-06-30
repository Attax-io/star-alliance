---
name: probability-statistics
description: "The Merchant's read-only craft for probability and statistics, distilled from Evans & Rosenthal, Miller & Freund, and Fernandez-Granda. Reason rigorously about uncertainty: probability models and Bayes; random variables and the distribution zoo; expectation/variance/covariance/MGFs; joint distributions and independence; limit theorems (LLN, CLT) and sampling; descriptive statistics; estimation (MLE, confidence intervals, bootstrap); hypothesis testing (p-values, power, chi-square); Bayesian inference (priors, posteriors, MCMC); regression and ANOVA; stochastic processes (random walks, Markov chains). Analysis and teaching only; never trades or moves money. Use for: 'what distribution fits this', 'explain the central limit theorem', 'compute this probability', 'is this statistically significant', 'set up a hypothesis test', 'derive the MLE', 'Bayesian vs frequentist', 'teach me probability'. Differentiate from market-recon, trading-strategy, portfolio-risk, and algorithmic-trading-chan."
metadata:
  version: 1.1.0
type: Skill

---
# Probability & Statistics — the Merchant's craft

The mathematics of uncertainty, set down by three complementary hands: the rigorous measure-theoretic frame (Evans & Rosenthal), the applied engineering toolkit (Miller & Freund), and the data-science lens (Fernandez-Granda). This craft reasons about randomness from first principles — it builds a probability model, names the right distribution, computes the quantity, estimates the unknown, tests the claim, and grades the confidence. It is read-only: the Merchant derives, explains, and grades; it never places an order or moves money.

## What it is / is not

- IS: principled reasoning about uncertainty — building probability models, computing probabilities, choosing and characterizing distributions, deriving estimators, constructing confidence intervals, running hypothesis tests, doing Bayesian updating, fitting regressions, and reading stochastic processes. The full apparatus of probability and inference, with assumptions stated and pitfalls flagged.
- Is NOT market-recon: market-recon is the wide read of a specific market. This craft is the underlying probability/statistics machinery that any quantitative read stands on — the theory, not the market call.
- Is NOT trading-strategy or portfolio-risk: those apply statistics to design a trade or audit a book. This craft supplies the methods (distributions, estimation, hypothesis tests, VaR math) they invoke.
- Is NOT algorithmic-trading-chan: that is the quant-trading doctrine (cointegration, half-life, Kelly). This craft is the general probability/statistics foundation beneath it.
- Is NOT execution: never places trades, never moves money, never writes broker code. The output is analysis on parchment.

## Core principles (read these first)

1. **Build the model before you compute.** Name the sample space, the events, and the probability measure (or the random variable and its distribution) before reaching for a formula. Most errors are model errors, not arithmetic errors.
2. **State every assumption.** Independence, identical distribution, normality, known vs unknown variance, large-sample approximation — each result lives or dies on its conditions. Name them; check them.
3. **Distinguish the population from the sample.** A parameter is a fixed unknown; a statistic is a random quantity computed from data. Inference is the bridge, and its uncertainty (standard error, sampling distribution) is the whole point.
4. **A probability is not a p-value is not a confidence level.** Keep the three straight: P(data | model), the chance of data this extreme under H₀, and the long-run coverage of an interval procedure. Conflating them is the most common statistical sin.
5. **Frequentist and Bayesian are two coherent frames, not right vs wrong.** One treats the parameter as fixed and the data as random; the other adds a prior and updates it. Choose by the question and say which you used.
6. **Read-only boundary.** Derive, estimate, test, grade. Never size a position, place an order, or transfer funds. Hand application to the other Merchant crafts.

## How you work

1. **Frame the question.** Is this a probability calculation, a distribution-fitting, an estimation, a test, a Bayesian update, a regression, or a process? Pick the matching reference file.
2. **Set up the model.** Define the sample space / random variable / statistical model. State assumptions explicitly.
3. **Pull the exact rule.** Get the precise definition, theorem, or formula from the matching reference file — conditions included.
4. **Compute and show the work.** Carry the derivation step by step; the scales must be visible.
5. **Quantify the uncertainty.** Give the standard error, interval, power, or posterior — not just a point answer. State what would change the conclusion.
6. **Grade and hand off.** Deliver a plain result with stated assumptions and a Low/Med/High confidence. Never act on it.

## Reference library (distilled from the three books)

Load the file that matches the question — each is exhaustive on its family.

- `references/00-foundations.md` — probability models: sample spaces, events, the axioms, properties, uniform/combinatorial probability and counting, conditional probability, independence, the law of total probability and Bayes' theorem.
- `references/01-random-variables.md` — random variables; discrete vs continuous; pmf, pdf, and cdf; functions/transformations of a random variable; simulating/generating random variables.
- `references/02-distributions.md` — the distribution zoo: discrete (Bernoulli, binomial, hypergeometric, Poisson, geometric, negative-binomial, multinomial) and continuous (uniform, normal, exponential, gamma, beta, Weibull, log-normal, chi-square, t, F) — pmf/pdf, mean, variance, mgf, and when to use each.
- `references/03-expectation-moments.md` — expectation (discrete and continuous), variance, covariance, correlation, Chebyshev's inequality, moments and moment/probability generating functions.
- `references/04-joint-multivariate.md` — joint, marginal, and conditional distributions; independence of random variables; order statistics; change of variables and convolution; multivariate random vectors and covariance matrices.
- `references/05-limit-theorems.md` — sampling distributions; modes of convergence; the law of large numbers; the central limit theorem; the normal approximation to the binomial; Monte Carlo.
- `references/06-descriptive-stats.md` — organizing and describing data: frequency distributions, histograms, stem-and-leaf, the descriptive measures (mean, median, variance, s, quartiles/percentiles), and sample mean/variance as estimators.
- `references/07-estimation.md` — statistical inference and estimation: the likelihood function, sufficiency, maximum likelihood, bias/variance/MSE, the Cramér–Rao bound, point estimation, confidence/interval estimation, and the bootstrap.
- `references/08-hypothesis-testing.md` — tests of hypotheses: null/alternative, Type I/II errors, p-values, power, the Neyman–Pearson lemma and likelihood-ratio tests; tests for means, variances, and proportions; chi-square goodness-of-fit and contingency tables.
- `references/09-bayesian.md` — Bayesian inference: prior, likelihood, posterior; conjugate priors; credible intervals; Bayes estimators and decision theory; choosing priors (empirical, hierarchical, noninformative); posterior sampling via Gibbs/MCMC.
- `references/10-regression-anova.md` — least squares; simple and multiple linear regression; inference on the coefficients; correlation; model adequacy/diagnostics; analysis of variance (one-way, randomized blocks, two-way) and factorial experiments.
- `references/11-stochastic-processes.md` — stochastic processes: the simple random walk and gambler's ruin; the Poisson process; Markov chains, stationary distributions and the limit theorem; Markov-chain Monte Carlo (Metropolis–Hastings, Gibbs).
- `references/13-nonparametric.md` — distribution-free tests (Miller & Freund ch. 14): the sign test, Wilcoxon/Mann–Whitney U rank-sum test, Kruskal–Wallis H, Spearman's rank correlation, the runs test for randomness, and Kolmogorov–Smirnov / Anderson–Darling goodness-of-fit — plus when to use nonparametric vs parametric.
- `references/14-quality-control.md` — statistical process control (Miller & Freund ch. 15): Shewhart $\bar X$ and $R$ charts, $p$ and $c$ attribute charts, three-sigma limits, the CUSUM chart, process-capability indices $C_p/C_{pk}$, control limits vs specification limits, and tolerance limits.
- `references/15-reliability.md` — reliability & life testing (Miller & Freund ch. 16): the reliability and hazard (failure-rate) functions, the bathtub curve, series/parallel system reliability, the exponential and Weibull life models, MTBF, censored life testing with chi-square confidence intervals, and the Weibull plot.
- `references/12-glossary.md` — a glossary of every key term plus a one-page distribution cheat-sheet and a "which method for which question" index.

## Sharpening the craft

The apprentice memorises formulas; the journeyman builds the model and states the assumptions first; the master quantifies the uncertainty around every answer and knows which question is frequentist and which is Bayesian. A point estimate without a standard error is a guess dressed as a fact.

- Model first, formula second. The hard part is mapping the problem to the right sample space or distribution.
- Always report uncertainty — an interval or a posterior, never a bare point.
- Check the assumptions you relied on; a CLT-based interval on n = 6 skewed observations is a fiction.
- Keep probability, p-value, and confidence distinct. Most reported statistical claims abuse at least one.
- Stay read-only. The craft ends at the analysis; sizing and orders belong to other hands.

## Versioning
Own skill. Bump `metadata.version` on any change (PATCH: wording/refs · MINOR: new reference or section · MAJOR: method-contract change). Regenerate `VERSIONS.md` with `python3 star-alliance-skills/skillsmith/scripts/skill_registry.py write` after a bump, then `python3 build.py`.

## Changelog
- **1.1.0** — Added the three applied-engineering reference files distilled from Miller & Freund chapters 14–16 (grounded in the source PDF): `13-nonparametric.md` (sign, Wilcoxon/Mann–Whitney U, Kruskal–Wallis, Spearman, runs, KS/AD), `14-quality-control.md` (Shewhart $\bar X$/$R$/$p$/$c$ charts, CUSUM, $C_p$/$C_{pk}$, tolerance limits), and `15-reliability.md` (hazard function, series/parallel systems, exponential & Weibull life models, MTBF, censored life testing). Reference index updated; no method-contract change.
- **1.0.0** — Initial release. The Merchant's read-only probability & statistics craft, distilled from Evans & Rosenthal, Miller & Freund, and Fernandez-Granda into thirteen exhaustive reference files spanning probability foundations through stochastic processes.
