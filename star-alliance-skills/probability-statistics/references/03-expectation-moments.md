---
type: Document
timestamp: 2026-07-02T12:28:13Z
---

# Expectation, Moments, and Related Quantities

Expected value is the long-run average value of a random variable, defined separately for discrete and absolutely continuous cases, and serves as the foundation for variance, covariance, correlation, and generating-function analyses. This reference consolidates definitions, theorems, properties, common distributions, and operational identities for expectation, dispersion, dependence, conditional expectation, and moment-generating functions, in a form usable for derivations, computation, and modeling decisions.

---

## 1. Expected Value — Discrete Case

### Definitions

**Definition 3.1.1** — For a discrete random variable $X$,
$$E[X] = \sum_{x \in \mathbb{R}} x \, P(X = x) = \sum_x x \, p_X(x).$$

**Definition 3.1.2** — If $X$ takes distinct values $x_1, x_2, \ldots$ with $p_i = P(X = x_i)$, then
$$E[X] = \sum_i x_i \, p_i.$$

Both definitions are equivalent; only $x$ with $P(X=x)>0$ contribute.

### Indicator / Bernoulli (Example 3.1.6)
For $X = I_A$, $E[I_A] = P(A)$. If $X \sim \text{Bernoulli}(p)$, then $E[X] = p$.

### Common Discrete Means (proof sketches in source)

| Distribution | $E[X]$ |
|---|---|
| Degenerate $X = c$ | $c$ |
| Bernoulli($p$) | $p$ |
| Binomial($n,p$) | $np$ |
| Geometric($p$) (counting failures before first success) | $(1-p)/p$ |
| Poisson($\lambda$) | $\lambda$ |
| Hypergeometric($N,M,n$) | $nM/N$ |
| Negative-Binomial($r,p$) | $r(1-p)/p$ |
| Multinomial($n;\pi_1,\pi_2,\pi_3$) | $E[X_i] = n\pi_i$ |

**Use** these as building blocks; combining indicator decompositions (e.g., Binomial = sum of i.i.d. Bernoullis) is faster than direct summation.

### Existence

**Example 3.1.10** — $p_X(2^k) = 2^{-k}$ for $k=1,2,\ldots$ gives $E[X] = \sum_{k\ge 1} 1 = \infty$.

**Example 3.1.11** — Symmetric $p_Y(\pm 2^k) = 2^{-(k+1)}$ gives $E[Y]$ undefined (each half diverges).

**St. Petersburg Paradox (Example 3.1.12)** — Award $2^Z$ pennies with $Z$ = # tails before first head, $P(Z=z) = 2^{-(z+1)}$. Then
$$E[\text{award}] = \sum_{z=0}^\infty 2^z \cdot 2^{-(z+1)} = \sum_{z=0}^\infty \tfrac{1}{2} = \infty.$$
Truncating at $2^{30}$ cents yields an expected value of only $15.5$ cents (Example 3.1.13); utility functions $U(x) = \min(x, 2^{30})$ reconcile "infinite" expected utility with rational pricing.

### Functions of Discrete Random Variables

**Theorem 3.1.1.** (a) $E[g(X)] = \sum_x g(x) \, P(X=x)$ when the sum exists.
(b) $E[h(X,Y)] = \sum_{x,y} h(x,y) \, P(X=x, Y=y)$ when the sum exists.

Proof for (b): sum over $z$ of $zP(Z=z)$ and substitute the indicator $\mathbf{1}\{h(x,y)=z\}$.

### Linearity of Expectation

**Theorem 3.1.2.** For discrete $X,Y$ and reals $a,b$, $E[aX+bY] = aE[X] + bE[Y]$.

The proof only requires the joint pmf, **not** independence. Use to compute $E[\text{Binomial}(n)]$ by summing $n$ i.i.d. Bernoullis (Example 3.1.15).

### Products and Independence

**Theorem 3.1.3.** If $X,Y$ discrete and independent, $E[XY] = E[X] E[Y]$.

**Example 3.1.16** (counterexample when dependent) — $E[XY] = 26 \neq 4 \cdot 19/3 \approx 25.33$, so without independence, $E[XY] \neq E[X]E[Y]$.

### Monotonicity

**Theorem 3.1.4.** If $X \le Y$ a.s. (i.e., $X(s) \le Y(s)$ for all $s \in S$), then $E[X] \le E[Y]$.

Proof: $Z = Y-X \ge 0$ a.s., so $E[Z] = \sum z_i P(Z=z_i) \ge 0$.

---

## 2. Expected Value — Absolutely Continuous Case

### Definition

**Definition 3.2.1.** For absolutely continuous $X$ with density $f_X$,
$$E[X] = \int_{-\infty}^\infty x \, f_X(x) \, dx.$$

**Derivation (Heuristic).** Approximate by Riemann sums over intervals $[i\varepsilon, (i+1)\varepsilon)$:
$$E[X] \approx \sum_i i\varepsilon \, P(i\varepsilon \le X < (i+1)\varepsilon) \to \int x f_X(x)\,dx \text{ as } \varepsilon \to 0.$$

### Common Continuous Means

| Distribution | $E[X]$ |
|---|---|
| Uniform[$0,1$] | $1/2$ |
| Uniform[$L,R$] | $(L+R)/2$ |
| Exponential($\lambda$) | $1/\lambda$ |
| $N(\mu,\sigma^2)$ | $\mu$ |
| Gamma($\alpha,\beta$) (shape $\alpha$, rate $\beta$) | $\alpha/\beta$ |
| Beta($a,b$) | $a/(a+b)$ |
| Weibull($\lambda,k$) | $\lambda \Gamma(1+1/k)$ |
| Pareto($\alpha, x_m$) (for $\alpha>1$) | $\alpha x_m/(\alpha-1)$ |
| Laplace($\mu,b$) | $\mu$ |
| Logistic($\mu,s$) | $\mu$ |

**Example 3.2.4 ($N(0,1)$).** The mean is $0$ because the integrand $z \cdot \phi(z)$ is odd.

### Existence in the Continuous Case

- **Infinite (Example 3.2.5):** $f_X(x) = 1/x^2$ on $[1,\infty)$ has $E[X] = \infty$.
- **Undefined (Example 3.2.6):** Symmetric density on $(-1,1)$ such that each tail contributes divergent but canceling integrals.
- **Cauchy:** $E[X]$ does not exist (Problem 3.2.20).

### Functions of Continuous Random Variables

**Theorem 3.2.1.** (a) $E[g(X)] = \int g(x) f_X(x)\,dx$ when the integral converges (absolutely or as a limit).
(b) $E[h(X,Y)] = \iint h(x,y) f_{X,Y}(x,y)\,dx\,dy$ when convergent.

### Linearity and Monotonicity

**Theorem 3.2.2 (Linearity).** $E[aX+bY] = aE[X] + bE[Y]$ for jointly absolutely continuous $X,Y$.

**Theorem 3.2.3 (Independence).** If $X,Y$ independent, $E[XY] = E[X]E[Y]$.

**Theorem 3.2.4 (Monotonicity).** If $X \le Y$ a.s., then $E[X] \le E[Y]$. (Uses the same trick as Theorem 3.1.4.)

### Shifting a Distribution

For any random variable $X$ and constant $c$, $E[X+c] = E[X] + c$ (mean is a location measure, shifts with the distribution). This requires either $X$ and $c$ both discrete/continuous treated jointly, or the general machinery of Section 3.7.

---

## 3. Variance

### Definition

**Definition 3.3.1.** The variance of $X$ is
$$\text{Var}(X) = E[(X - \mu_X)^2] = E[(X - E[X])^2].$$

**Definition 3.3.2.** The standard deviation is $\text{Sd}(X) = \sqrt{\text{Var}(X)}$.

**Why square?** $E[X - \mu_X] = 0$ identically. The squared quantity $E[(X-\mu_X)^2]$ is always non-negative, has a built-in weighting toward large deviations, and supports clean algebraic identities.

**Scale property:** $\text{Var}(aX+b) = a^2 \text{Var}(X)$ and $\text{Sd}(aX+b) = |a|\,\text{Sd}(X)$.

### Fundamental Properties

**Theorem 3.3.1.** For any $X$ with $E[X]=\mu$ and $\text{Var}(X)=\sigma^2$:
(a) $\text{Var}(X) \ge 0$ (and always defined, since $E[(X-\mu)^2]$ is a non-negative integral/sum).
(b) $\text{Var}(aX+b) = a^2 \text{Var}(X)$.
(c) $\text{Var}(X) = E[X^2] - (E[X])^2 = E[X^2] - \mu^2$. (Computing formula.)
(d) $\text{Var}(X) \le E[X^2]$.

**Proof of (c).** Expand $(X-\mu)^2 = X^2 - 2\mu X + \mu^2$ and use $E[\mu] = \mu$:
$$E[X^2 - 2\mu X + \mu^2] = E[X^2] - 2\mu E[X] + \mu^2 = E[X^2] - \mu^2.$$

### Common Variances

| Distribution | $\text{Var}(X)$ |
|---|---|
| Degenerate $X=c$ | $0$ |
| Bernoulli($p$) | $p(1-p)$ |
| Binomial($n,p$) | $np(1-p)$ |
| Geometric($p$) | $(1-p)/p^2$ |
| Poisson($\lambda$) | $\lambda$ |
| Hypergeometric($N,M,n$) | $n(M/N)(1 - M/N)(N-n)/(N-1)$ |
| Negative-Binomial($r,p$) | $r(1-p)/p^2$ |
| Uniform[$L,R$] | $(R-L)^2/12$ |
| Exponential($\lambda$) | $1/\lambda^2$ |
| $N(\mu,\sigma^2)$ | $\sigma^2$ |
| Gamma($\alpha,\beta$) (rate) | $\alpha/\beta^2$ |
| Beta($a,b$) | $ab/[(a+b)^2(a+b+1)]$ |
| Laplace($\mu,b$) | $2b^2$ |
| Weibull($\lambda,k$) | $\lambda^2[\Gamma(1+2/k) - \Gamma(1+1/k)^2]$ |
| Pareto($\alpha, x_m$), $\alpha>2$ | $x_m^2 \alpha/[(\alpha-1)^2(\alpha-2)]$ |

### Binomial Variance (Example 3.3.11 / Example 35)
Decompose $Y = X_1+\cdots+X_n$ with $X_i$ i.i.d. Bernoulli($p$), $\text{Var}(X_i) = p(1-p)$. Then $\text{Var}(Y) = np(1-p)$ by Corollary 3.3.3.

---

## 4. Covariance and Correlation

### Definition

**Definition 3.3.3.** The covariance of $X,Y$ is
$$\text{Cov}(X,Y) = E[(X - \mu_X)(Y - \mu_Y)].$$

**Definition 3.3.4.** The (Pearson) correlation is
$$\text{Corr}(X,Y) = \frac{\text{Cov}(X,Y)}{\text{Sd}(X)\,\text{Sd}(Y)} = \frac{\text{Cov}(X,Y)}{\sqrt{\text{Var}(X)\,\text{Var}(Y)}},$$
defined when both variances are strictly positive.

### Properties

**Theorem 3.3.2 (Linearity of Covariance in the First Argument).** 
$$\text{Cov}(aX + bY, Z) = a\,\text{Cov}(X,Z) + b\,\text{Cov}(Y,Z).$$

**Theorem 3.3.3 (Computing Formula).** 
$$\text{Cov}(X,Y) = E[XY] - E[X]E[Y].$$

**Corollary 3.3.2.** If $X,Y$ are independent, then $\text{Cov}(X,Y) = 0$.

**Caveat — the converse fails (Example 3.3.10):** Discrete $(X,Y)$ with $E[XY] - E[X]E[Y] = 0$ but $P(X=4,Y=5) \ne P(X=4)P(Y=5)$. Zero covariance does **not** imply independence.

**Theorem 3.3.4 (Variance of a Sum).**
(a) $\text{Var}(X+Y) = \text{Var}(X) + \text{Var}(Y) + 2\,\text{Cov}(X,Y).$
(b) $\text{Var}\left(\sum_i X_i\right) = \sum_i \text{Var}(X_i) + 2\sum_{i<j}\text{Cov}(X_i,X_j).$

**Corollary 3.3.3 (Independence Adds Variances).** If $X_1,\ldots,X_n$ are independent,
$$\text{Var}\!\left(\sum_i X_i\right) = \sum_i \text{Var}(X_i).$$

**Bounds (Section 3.6 preview).** Always $-1 \le \text{Corr}(X,Y) \le 1$ (Cauchy–Schwarz).

### Correlated Linear Combinations

For $X \sim$ any distribution with $\text{Var}(X) = \sigma^2$, $Y = cX$ has $\text{Cov}(X,Y) = c\sigma^2$, $\text{Sd}(Y) = |c|\sigma$, hence $\text{Corr}(X,Y) = \text{sign}(c)$.

For bivariate normal with parameters $(\mu_1,\mu_2,\sigma_1^2,\sigma_2^2,\rho)$, $\text{Corr}(X,Y) = \rho$ exactly.

---

## 5. Probability Generating Functions

### Definition

**Definition 3.4.1.** For a (typically discrete) random variable $X$,
$$r_X(t) = E[t^X], \quad t \in \mathbb{R}.$$

Examples:
- Binomial($n,p$): $r_X(t) = (1-p + pt)^n$.
- Poisson($\lambda$): $r_Y(t) = e^{\lambda(t-1)}$.

### Recovering Probabilities

**Theorem 3.4.1.** If $X$ is supported on $\{0,1,2,\ldots\}$ and $r_X$ is finite in a neighborhood of $0$, then
$$r_X^{(k)}(0) = k! \, P(X=k).$$

Thus $r_X$ uniquely determines the distribution on the non-negative integers.

---

## 6. Moments

**Definition 3.4.2.** The $k$-th moment of $X$ is $E[X^k]$, provided it exists.

If $E[X^k]$ exists and is finite, then $E[X^j]$ exists and is finite for all $0 \le j \le k$.

- First moment: location/mean.
- Second moment with the first moment: variance.
- Third moment about the mean: skewness ($\mu_3/\sigma^3$).
- Fourth moment about the mean: kurtosis ($\mu_4/\sigma^4$).

**Conversion formula (Miller §4.4):** 
$$\sigma^2 = \mu_2' - \mu^2, \quad \mu_3 = \mu_3' - 3\mu_2'\mu + 2\mu^3.$$

---

## 7. Moment Generating Functions

### Definition

**Definition 3.4.3.** The moment generating function (MGF) of $X$ is
$$m_X(s) = E[e^{sX}], \quad s \in \mathbb{R},$$
when finite.

**Connection to PGF (Theorem 3.4.2).** $m_X(s) = r_X(e^s)$ when $X$ is non-negative integer valued.

### Recovering Moments

**Theorem 3.4.3.** If $m_X(s)$ is finite in some neighborhood $(-\delta, \delta)$ of $0$, then
$$m_X^{(k)}(0) = E[X^k], \quad k = 0, 1, 2, \ldots$$

### Common MGFs

| Distribution | $m_X(s)$ | Domain |
|---|---|---|
| Bernoulli($p$) | $1-p+pe^s$ | all $s$ |
| Binomial($n,p$) | $(1-p+pe^s)^n$ | all $s$ |
| Poisson($\lambda$) | $\exp(\lambda(e^s-1))$ | all $s$ |
| Geometric($p$) | $pe^s/[1-(1-p)e^s]$ | $s < -\ln(1-p)$ |
| Uniform[$L,R$] | $(e^{sR}-e^{sL})/[s(R-L)]$ | $s\ne 0$; $1$ at $s=0$ |
| Exponential($\lambda$) | $\lambda/(\lambda-s)$ | $s < \lambda$ |
| $N(0,1)$ | $e^{s^2/2}$ | all $s$ |
| $N(\mu,\sigma^2)$ | $e^{\mu s + \sigma^2 s^2/2}$ | all $s$ |
| Gamma($\alpha,\beta$) rate $\beta$ | $(1-\beta s)^{-\alpha}$ | $s < 1/\beta$ |
| Chi-square($\nu$) | $(1-2s)^{-\nu/2}$ | $s < 1/2$ |
| Laplace($\mu,b$) | $e^{\mu s}/(1-b^2 s^2)$ | $|s|<1/b$ |
| Negative-Binomial($r,p$) | $[p/(1-(1-p)e^s)]^r$ | $s<-\ln(1-p)$ |

### MGF of a Linear Transformation

**Theorem 3.4.5 / Theorem 5.3.** For constants $a,b$ and r.v. $X$ with MGF $m_X$,
$$m_{a+bX}(s) = e^{as} \, m_X(bs).$$

**Example (Z = (X-μ)/σ).** Since $m_X(s) = e^{\mu s + \sigma^2 s^2/2}$ for $X \sim N(\mu,\sigma^2)$, we have $m_Z(s) = e^{-\mu s/\sigma} m_X(s/\sigma) = e^{s^2/2}$, so $Z \sim N(0,1)$.

### MGF of a Sum

**Theorem 3.4.5(b) / Theorem 5.4.** If $X,Y$ are independent with MGFs $m_X, m_Y$, then
$$m_{X+Y}(s) = m_X(s) \cdot m_Y(s).$$

**Sums of independent normals** are normal with additive means and additive variances. Sums of independent Poissons($\lambda_i$) are Poisson($\sum \lambda_i$); sums of independent Gammas with common rate are Gamma.

### Uniqueness

**Theorem 3.4.6 (Uniqueness).** If $m_X(s)$ is finite in a neighborhood of $0$, then $m_X$ uniquely determines the distribution of $X$.

**Use:** Recognize an MGF, then name the distribution; conversely, derive a distribution by finding an MGF and matching it to a known one.

---

## 8. Compound Distributions

**Definition 3.4.4.** Let $X_1, X_2, \ldots$ be i.i.d. and let $N$ be a non-negative integer-valued random variable independent of the $X_i$. Then
$$S = \sum_{i=1}^N X_i$$
is said to have a **compound distribution** (with $S=0$ when $N=0$).

**Modeling use:** Insurance claims ($X_i$ = claim size, $N$ = number of claims), total service time, particle multiplicities.

**Theorem 3.4.7.** 
(a) $E[S] = E[N] \, E[X_1]$.
(b) $m_S(s) = r_N(m_{X_1}(s))$.

**Proof sketch for (a):** $E[S] = E[E[S|N]] = E[N \cdot E[X_1]] = E[N]E[X_1]$.

**Examples.**
- $X_i$ i.i.d. Exponential($\lambda$), $N$ independent Poisson($\mu$): $S$ is compound Poisson. $E[S] = \mu/\lambda$.
- $N$ Geometric, $X_i$ i.i.d. Exponential: similar formulas via the geometric PGF.

---

## 9. Characteristic Functions

**Definition 3.4.5.** The characteristic function of $X$ is
$$c_X(s) = E[e^{isX}], \quad s \in \mathbb{R},$$
where $i = \sqrt{-1}$. Equivalently, $c_X(s) = E[\cos(sX)] + i E[\sin(sX)]$.

**Theorem 3.4.8.** $c_X(s)$ is finite for **every** real $s$ (since $|e^{isX}|=1$).

**Theorem 3.4.9.** If the first $k$ moments of $X$ exist, then
$$c_X^{(k)}(0) = i^k E[X^k].$$

**Theorem 3.4.10.** If $X,Y$ are independent, $c_{X+Y}(s) = c_X(s) \, c_Y(s)$.

**Cauchy sample mean (Problem 3.4.28):** $c_{\bar X}(s) = c_X(s/n) = e^{-|s|/n}$, so $\bar X$ is again Cauchy — distributions without a mean can be "averaged" without becoming normal.

**Use when MGF is infinite** (Example 3.4.12): characteristic functions always exist and provide a substitute for MGF-based reasoning.

---

## 10. Conditional Expectation

### Discrete Case

**Definition 3.5.1.** $E[X \mid A] = \sum_x x \, P(X=x \mid A) = \sum_x x \, P(X=x, A)/P(A)$ when $P(A)>0$.

**Definition 3.5.2.** For discrete $X,Y$ with $P(Y=y) > 0$,
$$E[X \mid Y=y] = \sum_x x \, P(X=x \mid Y=y) = \frac{\sum_x x \, p_{X,Y}(x,y)}{p_Y(y)}.$$

**Definition 3.5.3.** $E[X \mid Y]$ is the random variable equal to $E[X \mid Y=y]$ when $Y=y$.

### Continuous Case

**Definition 3.5.4.** For jointly absolutely continuous $(X,Y)$ with joint density $f_{X,Y}$ and marginal $f_Y$,
$$E[X \mid Y=y] = \int_{-\infty}^\infty x \, f_{X\mid Y}(x \mid y) \, dx = \int_{-\infty}^\infty x \, \frac{f_{X,Y}(x,y)}{f_Y(y)} \, dx.$$

**Definition 3.5.5.** $E[X \mid Y]$ is the random variable with value $E[X \mid Y=y]$ when $Y=y$.

### Linearity

**Theorem 3.5.1.** For constants $a,b$, r.v.s $X_1, X_2, Y$, and event $A$:
(a) $E[aX_1 + bX_2 \mid A] = a E[X_1 \mid A] + b E[X_2 \mid A]$.
(b) $E[aX_1 + bX_2 \mid Y=y] = a E[X_1 \mid Y=y] + b E[X_2 \mid Y=y]$.
(c) $E[aX_1 + bX_2 \mid Y] = a E[X_1 \mid Y] + b E[X_2 \mid Y]$.

### Double Expectation and "Taking Out What Is Known"

**Theorem 3.5.2 (Tower / Total Expectation).** $E[E[X \mid Y]] = E[X]$.

**Theorem 3.5.3 (Defining Property).** For any $g$,
$$E[g(Y) \cdot E[X \mid Y]] = E[g(Y) X].$$
This **characterizes** $E[X \mid Y]$: it is the (a.s.-unique) function of $Y$ whose covariance against any $g(Y)$ equals that of $X$.

**Theorem 3.5.4 (Factoring Functions of $Y$).** $E[g(Y) X \mid Y] = g(Y) \cdot E[X \mid Y]$ a.s.

**Theorem 3.5.5 (Idempotence).** $E[E[X \mid Y] \mid Y] = E[X \mid Y]$.

### Conditional Variance

**Definition 3.5.6.** 
$$\text{Var}(X \mid A) = E[(X - E[X \mid A])^2 \mid A] = E[X^2 \mid A] - (E[X \mid A])^2,$$
$$\text{Var}(X \mid Y=y) = E[X^2 \mid Y=y] - (E[X \mid Y=y])^2,$$
$$\text{Var}(X \mid Y) = E[X^2 \mid Y] - (E[X \mid Y])^2.$$

**Theorem 3.5.6 (Law of Total Variance).** 
$$\text{Var}(X) = \text{Var}\!\big(E[X \mid Y]\big) + E\!\big[\text{Var}(X \mid Y)\big].$$
"Total variance = variance of conditional mean + mean of conditional variance." Always non-negative, and useful for hierarchical/mixture models.

---

## 11. Chebyshev's Theorem

**Theorem 4.1 (Chebyshev's Inequality).** For any random variable $X$ with mean $\mu$ and standard deviation $\sigma$,
$$P(|X - \mu| \ge k\sigma) \le \frac{1}{k^2}, \quad k > 0.$$

**Equivalent form:** $P(|X-\mu| < k\sigma) \ge 1 - 1/k^2$.

**Proof outline.** Split $\sigma^2 = \sum (x-\mu)^2 f(x)$ into three regions: $|x-\mu|<k\sigma$ (drop — non-negative) and $|x-\mu|\ge k\sigma$ (replace $(x-\mu)^2$ by $k^2\sigma^2$):
$$\sigma^2 \ge k^2 \sigma^2 \sum_{|x-\mu|\ge k\sigma} f(x),$$
giving $P(|X-\mu|\ge k\sigma) \le 1/k^2$.

**Use:** Distribution-free, requires only $\mu,\sigma$; gives (often loose) bounds for any distribution. Sharpest at large $k$ (at most $1/k^2$); useless at $k\le 1$.

**Application to sample proportions (Law of Large Numbers preview).** For $\bar p_n$ = proportion of successes in $n$ i.i.d. Bernoulli($p$) trials, $\mu=p$, $\sigma = \sqrt{p(1-p)/n}$, and Chebyshev implies $\bar p_n \to p$ in probability.

**Practical caveat:** Tight for two-point and many symmetric unimodal distributions; weak for heavy-tailed ones; e.g., binomial ($n=16$, $p=1/2$) has $P(|X-8|\ge 2\cdot 4)=0.077$, much less than Chebyshev's $1/4$.

---

## 12. Sample Mean and Variance

For $X_1, \ldots, X_n$ i.i.d. with mean $\mu$ and variance $\sigma^2$:

**Sample mean** $\bar X = (X_1+\cdots+X_n)/n$:
- $E[\bar X] = \mu$.
- $\text{Var}(\bar X) = \sigma^2/n$.
- $\text{Sd}(\bar X) = \sigma/\sqrt{n}$.

**Sample variance** $S^2 = \sum_{i=1}^n (X_i - \bar X)^2 / (n-1)$:
- $E[S^2] = \sigma^2$ (unbiased).

**Derivation for $E[S^2]$.** Use the identity 
$$\sum_i (X_i - \bar X)^2 = \sum_i (X_i - \mu)^2 - n(\bar X - \mu)^2.$$
Then $E[\sum(X_i-\mu)^2] = n\sigma^2$ and $E[n(\bar X-\mu)^2] = n \cdot \sigma^2/n = \sigma^2$, so $E[\sum(X_i-\bar X)^2] = (n-1)\sigma^2$, giving $E[S^2]=\sigma^2$.

**Use:** $\text{Var}(\bar X) = \sigma^2/n$ explains why the sample mean concentrates around $\mu$ as $n$ grows; the unbiased factor $(n-1)$ in $S^2$ corrects for using $\bar X$ in place of $\mu$.

---

## 13. Mixed Discrete/Continuous and Joint Operations

**Variance of $aX_1 + a_2X_2$ when independent** (Example 30–33):
- $E[a_1 X_1 + a_2 X_2] = a_1\mu_1 + a_2\mu_2$.
- $\text{Var}(a_1 X_1 + a_2 X_2) = a_1^2 \sigma_1^2 + a_2^2 \sigma_2^2$.

Constants added to a sum contribute to the mean but not the variance.

**Joint density examples (Miller §5.10, Exercises 5.73, 5.76, 5.81):** Use $f_1(x) = \int f(x,y) dy$, $f_2(y) = \int f(x,y) dx$, then $f_1(x \mid y) = f(x,y)/f_2(y)$ when $f_2(y)>0$, and integrate for $E[\text{anything}]$.

---

## 14. Decision Checklist

| If you need to… | Use this… | Caveat |
|---|---|---|
| Compute $E[X]$ for a single discrete r.v. | Sum $x p_X(x)$ | Sum may diverge; check $\sum |x| p(x) < \infty$ |
| Compute $E[X]$ for a single continuous r.v. | $\int x f_X(x) dx$ | Need absolute convergence or principal value |
| Compute $E[aX+b]$ | $aE[X]+b$ | No independence needed |
| Compute $E[XY]$ | $E[X]E[Y]$ **iff** $X,Y$ independent | Use Theorem 3.1.3 / 3.2.3, else joint |
| Compute $\text{Var}(aX+b)$ | $a^2 \text{Var}(X)$ | Always |
| Compute $\text{Var}(X+Y)$ | $\text{Var}(X)+\text{Var}(Y)+2\text{Cov}(X,Y)$ | Use Cor 3.3.3 if independent |
| Compute $\text{Cov}(X,Y)$ from a joint table | $E[XY]-E[X]E[Y]$ | Zero covariance $\not\Rightarrow$ independence |
| Get all moments | Differentiate MGF at $0$ | Need MGF finite in a neighborhood of $0$ |
| Identify the distribution of a sum | MGF / PGF / characteristic function, then match | Use uniqueness |
| Bound tail probability | Chebyshev: $P(\lvert X-\mu\rvert\ge k\sigma)\le 1/k^2$ | Distribution-free but loose |
| Compute $E[X \mid Y]$ | Definition 3.5.2 / 3.5.4 | $P(Y=y)>0$ (discrete) or $f_Y(y)>0$ (continuous) |
| Total variance | $\text{Var}(X)=\text{Var}(E[X\mid Y])+E[\text{Var}(X\mid Y)]$ | Always non-negative |
| Average in a hierarchical model | $E[X]=E[E[X\mid Y]]$ | Use to build mixture distributions |

End of reference.
