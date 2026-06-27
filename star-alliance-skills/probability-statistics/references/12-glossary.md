# Glossary & Quick Reference

## Glossary

- **Acceptance rate** — In MCMC, the fraction of proposed moves that are accepted; tuning target depends on algorithm (e.g., ~0.234 for random-walk MH in high dim, ~0.7 for HMC).
- **Ancillarity** — A statistic whose distribution does not depend on the parameter θ; complements sufficient statistics in Basu's theorem.
- **Anderson–Darling test** — A goodness-of-fit test based on a weighted Cramér–von Mises statistic, giving more weight to the tails than KS.
- **ANOVA (Analysis of variance)** — A method that partitions total variability into between-group and within-group components to compare k ≥ 3 group means; F = MSB/MSW.
- **Bayes' theorem** — P(A|B) = P(B|A)P(A) / P(B); the engine of Bayesian updating.
- **Bayesian information criterion (BIC)** — BIC = k ln n − 2ℓ; an asymptotic approximation to 2·log marginal likelihood; lower is better, heavier penalty than AIC.
- **Beta distribution** — A continuous distribution on (0,1) with PDF f(x)=x^{α−1}(1−x)^{β−1}/B(α,β); the conjugate prior for a Bernoulli/Binomial probability.
- **Bias** — Bias(θ̂) = E[θ̂] − θ; systematic deviation of an estimator from the target.
- **Bonferroni correction** — Family-wise error control by testing each hypothesis at level α/m.
- **Bootstrap** — Resample with replacement from the data B times to approximate the sampling distribution of a statistic; gives SE, percentile, or BCa intervals.
- **CDF (Cumulative distribution function)** — F(x) = P(X ≤ x); non-decreasing, right-continuous, F(−∞)=0, F(+∞)=1.
- **Central limit theorem (CLT)** — √n(X̄_n − μ) →ᵈ N(0, σ²) when X_i are iid with finite σ²; the basis for large-sample inference.
- **Characteristic function** — φ_X(t) = E[e^{itX}]; uniquely determines the distribution of X.
- **Chi-square (χ²) test** — Test based on the statistic Σ (O−E)²/E; used for goodness of fit, independence in contingency tables, and variance inference.
- **Chi-square distribution** — The distribution of the sum of squares of ν iid standard normals; χ²(ν) = Gamma(ν/2, 1/2).
- **Conditional probability** — P(A|B) = P(A∩B)/P(B), defined for P(B)>0.
- **Conjugate prior** — A prior family p(θ) such that the posterior p(θ|x) is in the same family (e.g., Beta–Binomial, Normal–Normal, Gamma–Poisson).
- **Consistent estimator** — θ̂_n →ᵖ θ as n→∞.
- **Convergence in distribution** — X_n →ᵈ X iff F_{X_n}(x)→F_X(x) at every continuity point of F_X (denoted →ᵈ or ⇀).
- **Convergence in probability** — X_n →ᵖ X iff ∀ε>0, P(|X_n−X|>ε)→0; the mode used in the WLLN.
- **Correlation (ρ)** — Cov(X,Y)/(σ_X σ_Y); scale-free measure of linear association on [−1, 1].
- **Counting process** — A stochastic process {N(t):t≥0} that is non-decreasing, right-continuous, integer-valued with N(0)=0.
- **Covariance** — Cov(X,Y) = E[(X−E[X])(Y−E[Y])] = E[XY] − E[X]E[Y].
- **Coverage probability** — P(θ ∈ CI_α) over repeated sampling; equals 1−α for a valid level-α CI.
- **Cramér–Rao bound (CRLB)** — Var(θ̂) ≥ 1 / [n·I(θ)] for unbiased estimators, where I(θ) = E[(∂ℓ/∂θ)²] is Fisher information.
- **Credible interval** — A posterior interval containing θ with a given probability (e.g., 95% credible interval: 0.95 = P(a ≤ θ ≤ b | x)).
- **Cross-validation** — Hold out part of the data to estimate out-of-sample error; k-fold averages over k partitions.
- **Density (PDF)** — f(x)≥0 with ∫f(x)dx=1; P(a≤X≤b)=∫_a^b f(x)dx.
- **Distribution function** — See CDF; sometimes the term refers to the PMF/PDF/CDF collectively.
- **Effective sample size (ESS)** — n_eff = n / (1 + 2 Σ_{k≥1} ρ_k); the number of iid-equivalent draws given MCMC autocorrelation.
- **Efficiency (relative)** — Eff(θ̂_1, θ̂_2) = Var(θ̂_2) / Var(θ̂_1); ≥ 1 means θ̂_1 is better.
- **Empirical CDF (ECDF)** — F̂_n(x) = (1/n) Σ 1{X_i ≤ x}; converges uniformly to F by the Glivenko–Cantelli theorem.
- **Estimate** — The realized numerical value θ̂(x) of an estimator on observed data.
- **Estimator** — A function θ̂(X) of the data; a random variable before data are seen.
- **Event** — A subset of the sample space; an element of the σ-algebra.
- **Expectation (E[X])** — E[X] = Σ x p(x) (discrete) or ∫x f(x)dx (continuous); the first moment and the mean μ.
- **Exponential distribution** — Memoryless continuous distribution on [0,∞) with PDF f(x)=λe^{−λx}; mean 1/λ, rate λ.
- **Exponential family** — f(x|θ) = h(x) exp{η(θ)ᵀT(x) − A(θ)}; the family for which MLEs and standard errors have clean forms.
- **F-distribution** — Distribution of (χ²(d_1)/d_1) / (χ²(d_2)/d_2); arises in ANOVA and variance-ratio tests.
- **F-test** — Any test whose statistic has an F distribution; e.g., overall regression significance, ANOVA, comparison of nested models.
- **False discovery rate (FDR)** — Expected proportion of false rejections among rejections; controlled by Benjamini–Hochberg.
- **Fisher information** — I(θ) = E[(∂ℓ/∂θ)²] = −E[∂²ℓ/∂θ²]; measures how much information data carry about θ.
- **Frequentist vs Bayesian** — Frameworks treating θ as fixed vs random; inference via sampling behavior vs posterior.
- **Gamma distribution** — Sum of α iid Exponential(β) variables; PDF β^α x^{α−1}e^{−βx}/Γ(α); conjugate prior for Poisson rate.
- **Gaussian** — Synonym for Normal.
- **Gelman–Rubin (R̂)** — Convergence diagnostic comparing within-chain and between-chain variance; values near 1 indicate convergence.
- **Generalized linear model (GLM)** — Regression with response from an exponential family and link g; E[Y|X] = g⁻¹(Xβ).
- **Geometric distribution** — Number of trials until first success; PMF (1−p)^{k−1}p on k=1,2,…; memoryless.
- **Goodness of fit** — Tests whether observed data are consistent with a proposed distribution; χ², KS, Anderson–Darling.
- **Hazard function** — h(t) = f(t)/S(t); instantaneous failure rate in survival analysis.
- **Hypergeometric distribution** — Sampling without replacement: P(X=k) = C(K,k) C(N−K, n−k) / C(N,n).
- **Hypothesis test** — Decision rule rejecting H_0 based on a statistic with known null distribution.
- **iid (independent and identically distributed)** — Observations drawn independently from the same distribution.
- **Importance sampling** — Monte Carlo method using weights w_i = f(x_i)/(g(x_i)·M) under a proposal g; reduces variance when g is well-chosen.
- **Independence** — X,Y independent iff P(X∈A, Y∈B)=P(X∈A)P(Y∈B) for all A,B; equivalently, the joint density factors.
- **Jackknife** — Leave-one-out resampling; bias ≈ (n−1)(θ̂_(·) − θ̂); variance of θ̂ ≈ ((n−1)/n) Σ (θ̂_(i) − θ̂_(·))².
- **Joint distribution** — Distribution of a random vector (X,Y,…); determined by joint PMF/PDF or CDF.
- **Kolmogorov–Smirnov (KS) test** — Sup-norm distance between ECDF and a reference (1-sample) or two ECDFs (2-sample); D = sup|F̂−F|.
- **Kurtosis** — E[(X−μ)⁴/σ⁴]; excess kurtosis = kurtosis − 3 (0 for Normal).
- **Law of large numbers (LLN)** — X̄_n → μ in probability (weak) or almost surely (strong) as n→∞; X_i iid with E|X|<∞.
- **Least squares** — β̂ = argmin_β ‖y − Xβ‖²; closed form β̂ = (XᵀX)⁻¹Xᵀy (when XᵀX is invertible).
- **Likelihood** — L(θ; x) = f(x|θ), regarded as a function of θ for fixed data x.
- **Likelihood ratio (Λ)** — Λ = sup_{θ∈Θ_0} L(θ) / sup_{θ∈Θ} L(θ); small values reject H_0 (Neyman–Pearson).
- **Linear regression** — Model y_i = x_iᵀβ + ε_i with ε iid N(0,σ²); inference via t-tests, F-tests, and CIs for coefficients.
- **Logistic function** — σ(x) = 1/(1+e^{−x}) ∈ (0,1); the inverse logit link for binary GLMs.
- **Logit** — log(p/(1−p)); the canonical link for binomial GLMs.
- **Log-likelihood** — ℓ(θ) = log L(θ); easier to maximize, and ∇ℓ is the score.
- **Log-normal distribution** — exp(Y) for Y ~ N(μ,σ²); right-skewed positive support; multiplicative-process model.
- **Marginal distribution** — Distribution of a subset of a random vector, obtained by summing/integrating the others out.
- **Markov chain** — {X_n} satisfying P(X_{n+1}|X_n, X_{n-1},…) = P(X_{n+1}|X_n); the past is summarized by the present.
- **Markov chain Monte Carlo (MCMC)** — Algorithms (Metropolis–Hastings, Gibbs, HMC/NUTS) that draw from complex distributions by constructing a chain with the target as its stationary distribution.
- **Maximum likelihood estimate (MLE)** — θ̂ = argmax_θ L(θ; x); under regularity, asymptotically Normal and efficient.
- **Mean** — Synonym for E[X].
- **Mean squared error (MSE)** — E[(θ̂−θ)²] = Var(θ̂) + Bias(θ̂)²; standard risk measure.
- **Median** — Any m with P(X ≤ m) ≥ 1/2 and P(X ≥ m) ≥ 1/2; robust to outliers.
- **Metropolis–Hastings** — MCMC algorithm accepting moves x→x′ with prob min{1, [f(x′)q(x|x′)] / [f(x)q(x′|x)]}.
- **Mode** — Value(s) maximizing the PMF/PDF; the peak of the distribution.
- **Moment** — E[X^k] (raw) or E[(X−μ)^k] (central); mean = first raw, variance = second central.
- **Moment generating function (MGF)** — M_X(t) = E[e^{tX}], defined where finite; uniquely determines the distribution and E[X^k] = M^{(k)}(0).
- **Monte Carlo** — Estimation by repeated random sampling; MC error scales as σ/√n_sim.
- **MSE** — See Mean squared error.
- **Multinomial** — Counts in k categories from n trials with cell probabilities p_1,…,p_k; PMF n!/(x_1!…x_k!) Π p_i^{x_i}.
- **Negative binomial** — Number of trials until the r-th success; PMF C(k−1, r−1) p^r (1−p)^{k−r}; mean r/p, variance r(1−p)/p².
- **Neyman–Pearson lemma** — The most powerful test of H_0:θ=θ_0 vs H_1:θ=θ_1 rejects when likelihood ratio Λ ≤ k.
- **Normal distribution** — f(x) = (1/(σ√(2π))) exp(−(x−μ)²/(2σ²)); the CLT limit distribution; MGF exp(μt+σ²t²/2).
- **Odds** — p/(1−p); log-odds is the logit.
- **One-sided / Two-sided test** — H_1 specifies a direction (e.g., μ>μ_0) or both (μ≠μ_0); critical regions differ.
- **p-value** — Smallest α at which H_0 would be rejected given the observed data; equivalently, P(T ≥ t_obs | H_0).
- **Parameter** — A quantity θ indexing a family of distributions (e.g., μ, σ², p).
- **Pareto distribution** — Heavy-tailed distribution on [x_m,∞); P(X>x) = (x_m/x)^α.
- **Permutation test** — Significance test using the exact or simulated distribution of a statistic under all rearrangements of the data.
- **PMF (Probability mass function)** — p(x) = P(X=x) for discrete X; Σ p(x)=1.
- **Poisson distribution** — PMF e^{−λ} λ^k / k!; mean = variance = λ; counts of rare events.
- **Poisson process** — Counting process with N(0)=0, independent increments, and P(N(t+h)−N(t)=1) ≈ λh; inter-arrivals iid Exp(λ).
- **Posterior** — p(θ|x) ∝ p(x|θ) p(θ); updated belief after data.
- **Power** — 1 − β = P(reject H_0 | H_1 true); increases with n, effect size, and α.
- **Predictive distribution** — p(x_new | x) = ∫ p(x_new|θ) p(θ|x) dθ; incorporates parameter uncertainty.
- **Prior** — p(θ); the distribution of θ before observing data; can be informative or non-informative.
- **Probability generating function (PGF)** — G_X(s) = E[s^X] for X ∈ {0,1,2,…}; G'(1) = E[X].
- **Quantile** — q_p such that F(q_p) = p; e.g., the 0.975-quantile for the upper 2.5% tail.
- **Random variable (X)** — A measurable function X: Ω → ℝ mapping outcomes to real numbers.
- **Random walk** — X_n = X_{n-1} + Z_n with iid increments Z_n; simple symmetric walk has Z_n ∈ {±1}.
- **R² (coefficient of determination)** — 1 − SS_res/SS_tot; proportion of variance in y explained by the model.
- **Regression** — Modeling E[Y|X] as a function of X; linear when linear in parameters.
- **Residual** — e_i = y_i − ŷ_i; in OLS, Σe_i = 0 and Σx_i e_i = 0 by construction.
- **Ridge / Lasso** — Penalized regression adding λΣβ_j² (L2 / Ridge) or λΣ|β_j| (L1 / Lasso) to the loss; shrinks or zeroes coefficients.
- **Sample** — A realization x_1,…,x_n of iid random variables.
- **Sample space (Ω)** — The set of all possible outcomes of a random experiment.
- **Sampling distribution** — The distribution of a statistic over hypothetical replications of the experiment.
- **Score function** — U(θ) = ∂ℓ/∂θ; satisfies E[U]=0 and Var[U]=I(θ).
- **Shapiro–Wilk test** — Test of normality based on the ratio of squared OLS coefficient of ordered sample to sample variance; powerful for n ≤ 50.
- **σ-algebra (σ-field)** — A collection of events closed under complementation and countable unions; the collection on which a probability measure is defined.
- **Significance level (α)** — Type I error rate; the threshold below which a p-value triggers rejection of H_0.
- **Skewness** — E[(X−μ)³/σ³]; 0 for symmetric distributions.
- **Slutsky's theorem** — If X_n →ᵈ X and Y_n →ᵈ a (constant), then X_n + Y_n →ᵈ X + a and X_n/Y_n →ᵈ X/a.
- **Standard error (SE)** — The standard deviation of an estimator; e.g., SE(X̄) = σ/√n.
- **Stationary distribution (π)** — A distribution satisfying π = πP for a transition matrix P; the long-run distribution of the chain.
- **Statistic** — Any function of the data, e.g., X̄, s²; random before data, fixed after.
- **Student's t-distribution** — Distribution of (Z/√(U/ν)) with Z~N(0,1), U~χ²(ν) independent; heavier tails than Normal.
- **Sufficiency** — T(X) is sufficient for θ if the conditional distribution of X|T does not depend on θ; characterized by the factorization theorem: f(x|θ) = g(T(x),θ) h(x).
- **Survival function** — S(t) = P(T > t) = 1 − F(t); foundation of survival analysis.
- **Test statistic** — A scalar T(X) summarizing evidence against H_0; compared to its null distribution to get a p-value.
- **Time-to-event / Survival data** — Data with censoring; analyzed via hazard, KM, Cox, or parametric models.
- **t-test (one-sample)** — T = (X̄ − μ_0)/(S/√n) ~ t_{n−1} under H_0 if data are Normal.
- **t-test (two-sample, independent)** — T = (X̄_1 − X̄_2)/SE_pooled, using t_{n_1+n_2−2} (equal variance) or Welch's t (unequal).
- **t-test (paired)** — Applied to the differences d_i = x_i − y_i; reduces to one-sample t on d.
- **Type I error** — Rejecting H_0 when H_0 is true; probability α by construction.
- **Type II error** — Failing to reject H_0 when H_1 is true; probability β; 1−β is power.
- **Unbiased estimator** — E[θ̂] = θ; bias is zero.
- **Uniform distribution (continuous)** — U(a,b); PDF 1/(b−a) on [a,b]; mean (a+b)/2, variance (b−a)²/12.
- **Uniform distribution (discrete)** — PMF 1/N on {1,…,N}; mean (N+1)/2, variance (N²−1)/12.
- **UMVUE** — Uniformly minimum-variance unbiased estimator; obtained from a complete sufficient statistic via Rao–Blackwell.
- **Variance** — Var(X) = E[(X−μ)²] = E[X²]−μ²; the second central moment.
- **Wald test** — Z = (θ̂−θ_0)/SE(θ̂) compared to N(0,1); uses the MLE and its SE.
- **Weibull distribution** — f(x) = (k/λ)(x/λ)^{k−1} exp(−(x/λ)^k); flexible time-to-failure model; k=1 ⇒ Exponential.
- **Welch's t-test** — Two-sample t allowing unequal variances; uses Satterthwaite degrees of freedom.
- **White noise** — Strictly stationary sequence with zero mean and constant finite variance and no serial correlation; the error process in many models.
- **Wishart distribution** — Multivariate analogue of χ²: distribution of sample covariance matrix from multivariate Normal.
- **z-test** — Test using Z = (X̄−μ_0)/(σ/√n) ~ N(0,1); used when σ is known (or large n).

## Distribution Cheat-Sheet

| Distribution | Support | PMF / PDF | Mean | Variance | MGF | When to use |
|---|---|---|---|---|---|---|
| **Bernoulli(p)** | {0, 1} | p^x (1−p)^{1−x} | p | p(1−p) | 1 − p + p e^t | Single binary trial (success/failure) |
| **Binomial(n, p)** | {0, 1, …, n} | C(n,k) p^k (1−p)^{n−k} | np | np(1−p) | (1 − p + p e^t)^n | # successes in n independent Bernoulli trials |
| **Geometric(p)** | {1, 2, …} | p (1−p)^{k−1} | 1/p | (1−p)/p² | p e^t / [1 − (1−p) e^t], t < −ln(1−p) | # trials until first success; only discrete distribution with memoryless property |
| **Negative Binomial(r, p)** | {r, r+1, …} | C(k−1, r−1) p^r (1−p)^{k−r} | r/p | r(1−p)/p² | [p e^t / (1 − (1−p) e^t)]^r | # trials until r-th success; overdispersed counts |
| **Hypergeometric(N, K, n)** | {max(0, n+K−N), …, min(n, K)} | C(K,k) C(N−K, n−k) / C(N, n) | nK/N | nK(N−K)(N−n) / [N²(N−1)] | complicated (hypergeometric fn) | Sampling without replacement from a finite population |
| **Poisson(λ)** | {0, 1, 2, …} | e^{−λ} λ^k / k! | λ | λ | exp(λ(e^t − 1)) | Counts of rare/independent events in a fixed interval; mean = variance |
| **Multinomial(n, p_1,…,p_k)** | {x_i ≥ 0, Σx_i = n} | (n! / Π x_i!) Π p_i^{x_i} | (np_1, …, np_k) | diag(np_i) with Cov = −np_i p_j | complicated | Counts of outcomes across k categories from n trials |
| **Uniform disc.** U{1,…,N} | {1, …, N} | 1/N | (N+1)/2 | (N² − 1)/12 | (e^t (e^{Nt} − 1)) / (N (e^t − 1)) | Equally likely integer outcomes (e.g., dice) |
| **Uniform cont. U(a, b)** | [a, b] | 1/(b − a) | (a + b)/2 | (b − a)²/12 | (e^{tb} − e^{ta}) / (t (b − a)) | Equally likely values in an interval; baseline for non-informative priors |
| **Normal(μ, σ²)** | (−∞, ∞) | (1 / (σ√(2π))) exp(−(x−μ)² / (2σ²)) | μ | σ² | exp(μ t + σ² t²/2) | Default continuous model; CLT limit; errors in linear models |
| **Exponential(λ)** | [0, ∞) | λ e^{−λ x} | 1/λ | 1/λ² | λ / (λ − t), t < λ | Waiting time; memoryless; inter-arrival times in Poisson process |
| **Gamma(α, β)** shape α, rate β | (0, ∞) | β^α x^{α−1} e^{−β x} / Γ(α) | α/β | α/β² | (β / (β − t))^α, t < β | Sum of α exponentials; waiting for α events; conjugate prior for Poisson rate |
| **Beta(α, β)** | (0, 1) | x^{α−1} (1−x)^{β−1} / B(α,β) | α/(α+β) | αβ / [(α+β)² (α+β+1)] | ₁F₁(α; α+β; t) (hypergeometric) | Proportions and probabilities; conjugate prior for Bernoulli/Binomial p |
| **Weibull(k, λ)** shape k, scale λ | [0, ∞) | (k/λ)(x/λ)^{k−1} exp(−(x/λ)^k) | λ Γ(1 + 1/k) | λ² [Γ(1 + 2/k) − Γ(1 + 1/k)²] | complicated (incomplete gamma) | Time-to-failure; reliability; flexible hazard (k>1 increasing, k<1 decreasing) |
| **Log-normal(μ, σ²)** | (0, ∞) | (1 / (x σ √(2π))) exp(−(ln x − μ)² / (2σ²)) | exp(μ + σ²/2) | (e^{σ²} − 1) e^{2μ + σ²} | no closed form | Multiplicative-process positive quantities; right-skewed data |
| **Chi-square(ν)** | (0, ∞) | x^{ν/2−1} e^{−x/2} / [2^{ν/2} Γ(ν/2)] | ν | 2ν | (1 − 2t)^{−ν/2}, t < 1/2 | Sum of ν squared standard normals; variance inference, goodness of fit |
| **Student-t(ν)** | (−∞, ∞) | Γ((ν+1)/2) [1 + x²/ν]^{−(ν+1)/2} / (√(νπ) Γ(ν/2)) | 0 (ν > 1) | ν/(ν−2) (ν > 2) | undefined (finite only for |t| < some r) | Inference with unknown σ; fat-tailed data; regression coefficients |
| **F(d₁, d₂)** | (0, ∞) | complicated (Beta-type) | d₂/(d₂ − 2) (d₂>2) | 2 d₂² (d₁ + d₂ − 2) / [d₁ (d₂ − 2)² (d₂ − 4)] (d₂>4) | complicated | Ratio of variances; ANOVA; overall F-test in regression |

## Which method for which question

| Question / Goal | Method / Test | Key assumption(s) |
|---|---|---|
| Estimate a mean (σ known) | z-interval: X̄ ± z_{α/2} σ/√n | Normality (or large n by CLT) |
| Estimate a mean (σ unknown) | One-sample t-interval: X̄ ± t_{α/2, n−1} S/√n | Approx. normality; iid |
| Compare two independent means | Two-sample t-test (Student if equal variances; Welch otherwise) | Indep., approx. normality; Welch does not require equal variance |
| Compare two paired means | Paired t-test on differences d_i = x_i − y_i | Differences approx. Normal; pairs independent |
| Test a single proportion | One-sample z-test on p̂; exact binomial CI for small n | n p ≥ 5 and n(1−p) ≥ 5 for z; independence |
| Compare two proportions | Two-sample z-test or 2×2 χ² test | Large n, expected counts ≥ 5, independent samples |
| Compare k ≥ 3 means | One-way ANOVA → F-test | Normality, equal variances (homoscedasticity), independence |
| Compare k ≥ 3 means, robust | Kruskal–Wallis (non-parametric ANOVA) | Same shape distributions; ordinal responses |
| Compare two or more variances | F-test (Normal), Levene's, or Bartlett's | Normality for F; Levene is robust |
| Test independence in a contingency table | Pearson χ² test of independence | Expected cell counts ≥ 5; random sample |
| Goodness of fit (categorical) | Pearson χ² GOF | Expected counts ≥ 5 |
| Goodness of fit (continuous, fully specified) | Kolmogorov–Smirnov; Anderson–Darling (more tail weight) | Continuous, fully specified null distribution |
| Test normality | Shapiro–Wilk (n ≤ 50); KS / Lilliefors / Anderson–Darling otherwise | — |
| Fit a linear relationship | OLS linear regression; t-tests for coefficients; F-test overall | Linearity, indep. errors, homoscedasticity, normality of errors (for inference) |
| Fit a relationship with many predictors | Ridge / Lasso / Elastic Net; PCA; partial least squares | Same as OLS plus the penalty choice (L1, L2, mix) |
| Predict a binary outcome | Logistic regression (GLM, logit link); Wald, LR, or score tests | Independence, no perfect separation, large n |
| Predict a count | Poisson GLM with log link; check for overdispersion → Negative Binomial GLM | Independence, correct mean–variance relationship |
| Predict a count with excess zeros | Zero-inflated Poisson / NB; hurdle model | Two-process data-generating mechanism |
| Predict time-to-event | Cox proportional hazards; parametric (Exponential, Weibull) regression | PH assumption (Cox); non-informative censoring |
| Compare two survival curves | Log-rank test; KM estimator | Non-informative censoring; PH for some extensions |
| Update a belief about θ given data | Bayes' theorem → posterior p(θ\|x) ∝ p(x\|θ) p(θ) | Model correctness; appropriate prior |
| Compute posterior with no closed form | MCMC: Gibbs (conjugate structure), Metropolis–Hastings, HMC/NUTS (Stan, PyMC) | Chain has converged (R̂ ≈ 1, high ESS); sufficient mixing |
| Summarize MCMC output | Trace plots, R̂, ESS, posterior summaries (mean, median, HDI) | Adequate burn-in and thinning |
| Reduce MC estimator variance | Importance sampling, control variates, antithetic variates, stratified sampling | Known proposal / control; bounded moments |
| Estimate SE without distributional assumptions | Bootstrap (percentile, BCa) | Data ≈ iid; resamples ≈ draws from F̂ |
| Test H_0 with small n or non-Normal | Permutation test; exact test; randomization test | Exchangeability under H_0 |
| Choose among competing models | AIC, BIC, cross-validation (k-fold, LOOCV) | Same model class for AIC/BIC; out-of-sample for CV |
| Test H_0 in nested models | Likelihood ratio test (or Wald, Score — asymptotically equivalent) | Large n, regular models |
| Multiple testing | Bonferroni (FWER); Benjamini–Hochberg (FDR) | Independence for Bonferroni; PRDS for BH |
| Time-series forecasting with trend / seasonality | ARIMA / SARIMA; exponential smoothing (ETS) | Stationarity after differencing; no structural breaks |
| Time-series with dependence, dynamic regression | ARIMAX; state-space / Kalman filter | Gaussian errors; correct lag structure |
| Sequential / continuous monitoring | SPRT; alpha-spending (Pocock, O'Brien–Fleming) | iid observations; prespecified design |
| Hierarchical / grouped data | Mixed-effects (random intercepts/slopes); hierarchical Bayesian model | Partial-pooling justified; exchangeable groups |
| A/B test with binary metric | Two-proportion z-test or Bayesian Beta–Binomial model | SUTVA; stable assignment probability |
| A/B test with hierarchical structure (e.g., users within sites) | Mixed logistic; hierarchical Beta–Binomial | Independence conditional on group effects |
| Best-arm identification | Multi-armed bandits: UCB, Thompson sampling | Stationary reward distribution; sub-Gaussian rewards |
| Compute optimal test for two simple hypotheses | Likelihood-ratio test (Neyman–Pearson) | Both H_0 and H_1 are simple |
| Construct optimal test for composite H_0 vs composite H_1 | UMP (when it exists), UMP-unbiased, or LR-based tests | Monotone likelihood ratio family (for UMP) |
| High-dimensional regression (p > n) | Lasso / Elastic Net; ridge; sure independence screening | Sparsity; approximate linearity |
| Variable importance | Permutation importance; SHAP values; drop-one analysis | Exchangeable features; no severe dependence |
| Causal effect estimation | Randomized experiment; propensity-score matching; IV; DiD; RDD | Random assignment, ignorability, exclusion (IV), parallel trends (DiD), continuity (RDD) |
| Treatment effect heterogeneity | Causal forest; interaction terms; subgroup analyses | Honest estimation; sufficient sample in leaves |
| Data with spatial structure | Spatial autoregression (SAR); GWR; kriging | Stationarity; neighborhood structure |
| Network / graph data | Stochastic block model; ERGM; spectral methods | Exchangeability under the model |
| Reliability / survival with covariates | Accelerated failure time; Cox; AFT with log-normal or Weibull | Correct distributional form; PH or AFT assumption |
| Quality control (process monitoring) | Control charts: X̄-R, X̄-S, p, c, EWMA, CUSUM | In-control process stable; independent measurements |
| Survey inference under complex design | Design-based estimation with survey weights; cluster-robust SE | Probability sampling; known inclusion probabilities |
| Missing data | Multiple imputation (joint or chained equations); IPW; EM | MAR (for valid MI); correct model specification (EM) |
| High-dimensional posterior | Variational inference; normalizing flows; HMC with mass matrix tuning | Continuous, differentiable target; tuning of mass matrix / step size |
| Convergence of MCMC (informal) | Trace plots; autocorrelation plots; effective sample size | Multiple chains from overdispersed starts |
| Convergence of MCMC (formal) | Gelman–Rubin R̂; Geweke; Heidelberg–Welch | Single chain or multiple chains as required |
