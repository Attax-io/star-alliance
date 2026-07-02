---
type: Document
timestamp: 2026-07-02T12:28:13Z
---

# Sampling Distributions, Convergence, and Random Processes

A random process is a collection of random variables indexed by time, and the central questions of inferential probability concern how such processes behave in the limit and how summary statistics computed from samples are themselves distributed. This reference collects the machinery of sampling distributions, modes of convergence, the law of large numbers, the central limit theorem, normal-theory distributions, and Monte Carlo methodology, together with the foundational theory of iid sequences, Poisson processes, random walks, and discrete-time Markov chains.

## Random Processes: Definition and Classification

### Definition

A random process $\tilde{X}$ on a probability space $(\Omega, \mathcal{F}, P)$ is a function that maps each $\omega \in \Omega$ to a function $\tilde{X}(\omega, \cdot) : T \to \mathbb{R}$, where $T$ is a discrete or continuous set.

- If $\omega$ is fixed, $\tilde{X}(\omega, t)$ is a deterministic **realization** (sample path) of the process.
- If $t$ is fixed, $\tilde{X}(\omega, t)$ is a random variable, denoted $\tilde{X}(t)$.
- The set of possible values of $\tilde{X}(t)$ for fixed $t$ is the **state space**.

### Classification

| Axis | Type | Description |
|---|---|---|
| Index set | Continuous-time | $T \subset \mathbb{R}$ or semi-infinite interval |
| Index set | Discrete-time | $T \subset \mathbb{Z}$ (often $\mathbb{N}$), write $\tilde{X}(i)$ |
| State space | Continuous-state | $\tilde{X}(t)$ is continuous for all $t$ |
| State space | Discrete-state | $\tilde{X}(t)$ is discrete; **finite-state** if it takes finitely many values |

Any combination is possible (continuous-state discrete-time, etc.).

### nth-Order Distribution

The joint distribution of $(\tilde{X}(t_1), \tilde{X}(t_2), \ldots, \tilde{X}(t_n))$ for any $n$ indices $\{t_1, \ldots, t_n\}$. Specifying all nth-order distributions completely characterizes a random process.

## Mean and Autocovariance Functions

The mean function is $\mu_{\tilde{X}}(t) := E[\tilde{X}(t)]$. The autocovariance function is

$$R_{\tilde{X}}(t_1, t_2) := \mathrm{Cov}(\tilde{X}(t_1), \tilde{X}(t_2)) = E[\tilde{X}(t_1)\tilde{X}(t_2)] - \mu_{\tilde{X}}(t_1)\mu_{\tilde{X}}(t_2).$$

In particular $R_{\tilde{X}}(t, t) = \mathrm{Var}(\tilde{X}(t))$. The autocovariance quantifies the correlation between the process at two time points.

## Stationarity

**Strict (strong) stationarity.** A process is strictly stationary if for any $n \geq 1$ and any shift $\tau$, the joint distribution of $(\tilde{X}(t_1), \ldots, \tilde{X}(t_n))$ equals that of $(\tilde{X}(t_1+\tau), \ldots, \tilde{X}(t_n+\tau))$. Equivalently, all finite-dimensional distributions are shift-invariant.

**Wide-sense (weak) stationarity.** A process is weakly stationary if $\mu_{\tilde{X}}(t) = \mu$ is constant and $R_{\tilde{X}}(t_1, t_2) = R_{\tilde{X}}(t_1 - t_2)$ depends only on the lag $s = t_1 - t_2$. Strict stationarity implies weak stationarity; the converse fails.

The shape of $R_{\tilde{X}}(s)$ governs sample-path character: $R(s) = 0$ for $s \neq 0$ produces erratic uncorrelated noise; large $R(s)$ at small $s$ produces smooth paths; alternating sign produces periodic behavior.

## Independent Identically-Distributed (iid) Sequences

A discrete-time process $\tilde{X}$ is iid if (i) each $\tilde{X}(i)$ has the same distribution and (ii) for any $n$ and any distinct indices, $\tilde{X}(i_1), \ldots, \tilde{X}(i_n)$ are mutually independent. For continuous state:

$$f_{\tilde{X}(i_1), \ldots, \tilde{X}(i_n)}(x_1, \ldots, x_n) = \prod_{j=1}^n f_{\tilde{X}}(x_j).$$

iid sequences are **strictly stationary**. With $\mu = E[\tilde{X}(i)]$ and $\sigma^2 = \mathrm{Var}(\tilde{X}(i))$:

$$\mu_{\tilde{X}}(i) = \mu, \qquad R_{\tilde{X}}(i, j) = \begin{cases} \sigma^2, & i = j \\ 0, & i \neq j \end{cases}.$$

iid sequences are the canonical building block for sampling distributions, the laws of large numbers, and the central limit theorem.

## Random Walks

Let $\tilde{S}(i)$ be iid with $P(\tilde{S}(i) = +1) = P(\tilde{S}(i) = -1) = 1/2$. The simple symmetric random walk is

$$\tilde{X}(i) = \begin{cases} 0, & i = 0 \\ \sum_{j=1}^i \tilde{S}(j), & i = 1, 2, \ldots \end{cases}.$$

It has $\mu_{\tilde{X}}(i) = 0$ and $R_{\tilde{X}}(i, j) = \min\{i, j\}$. The first-order pmf (by counting positive steps) is

$$p_{\tilde{X}(i)}(x) = \binom{i}{(i+x)/2} \frac{1}{2^i}, \quad \text{if } i+x \text{ even, } -i \leq x \leq i.$$

The variance grows linearly: $\mathrm{Var}(\tilde{X}(i)) = i$, so the standard deviation scales as $\sqrt{i}$. The random walk satisfies the Markov property.

## Poisson Processes

A Poisson process with rate $\lambda$ is a discrete-state continuous-time process $\tilde{N}$ on $[0, \infty)$ satisfying:

1. $\tilde{N}(0) = 0$.
2. For $t_1 < t_2$, $\tilde{N}(t_2) - \tilde{N}(t_1) \sim \mathrm{Poisson}(\lambda(t_2 - t_1))$.
3. Increments over disjoint intervals are independent.

Joint pmf: with $p(\lambda, x) := \frac{\lambda^x e^{-\lambda}}{x!}$,

$$p_{\tilde{N}(t_1), \ldots, \tilde{N}(t_n)}(x_1, \ldots, x_n) = \prod_{k=1}^n p(\lambda(t_k - t_{k-1}),\, x_k - x_{k-1}).$$

**Interarrival times** between consecutive events are iid $\mathrm{Exponential}(\lambda)$. Mean and autocovariance:

$$E[\tilde{N}(t)] = \lambda t, \qquad R_{\tilde{N}}(t_1, t_2) = \lambda \min(t_1, t_2).$$

The Poisson process is **not** stationary in either sense.

**Simulation:** generate iid exponential interarrivals $T_1, T_2, \ldots \sim \mathrm{Exp}(\lambda)$ and place events at cumulative sums $T_1, T_1 + T_2, \ldots$

## Markov Property and Discrete-Time Markov Chains

A process satisfies the **Markov property** if, for any $t_1 < t_2 < \cdots < t_{i+1}$, the future is conditionally independent of the past given the present:

$$P(\tilde{X}(t_{i+1}) = x_{i+1} \mid \tilde{X}(t_1), \ldots, \tilde{X}(t_i)) = P(\tilde{X}(t_{i+1}) = x_{i+1} \mid \tilde{X}(t_i)).$$

A **Markov chain** is a process with the Markov property. For a discrete-time finite-state Markov chain, specify the initial state distribution $\vec{p}(0)$ and the transition matrix $T$ with entries

$$T_{jk} := P(\tilde{X}(i+1) = x_j \mid \tilde{X}(i) = x_k).$$

The process is **time-homogeneous** if $T$ does not depend on $i$. Joint pmf of any $n+1$ samples:

$$p_{\tilde{X}(0), \ldots, \tilde{X}(n)}(x_0, \ldots, x_n) = p_{\tilde{X}(0)}(x_0) \prod_{i=0}^{n-1} T_{x_{i+1}, x_i}.$$

Both iid sequences and random walks satisfy the Markov property (random walks have a transition matrix encoding $+1$ vs $-1$ steps).

## Modes of Convergence

### Convergence in Probability

$X_n \xrightarrow{P} Y$ iff for every $\varepsilon > 0$, $\lim_{n \to \infty} P(|X_n - Y| > \varepsilon) = 0$.

### Convergence with Probability 1 (Almost Sure)

$X_n \xrightarrow{a.s.} Y$ iff $P(\lim_{n \to \infty} X_n = Y) = 1$. Equivalently, for every $\varepsilon > 0$ there exists (random) $N$ such that $|X_n - Y| < \varepsilon$ for all $n \geq N$.

### Convergence in Mean Square

$X_n \xrightarrow{m.s.} Y$ iff $\lim_{n \to \infty} E[(X_n - Y)^2] = 0$.

### Convergence in Distribution

$X_n \xrightarrow{d} X$ iff $\lim_{n \to \infty} F_{X_n}(x) = F_X(x)$ at every $x$ where $F_X$ is continuous.

### Implications

The implications form a strict hierarchy:

$$\text{a.s. convergence} \;\Rightarrow\; \text{convergence in probability} \;\Rightarrow\; \text{convergence in distribution}.$$

$$\text{mean-square convergence} \;\Rightarrow\; \text{convergence in probability}$$

The converses fail in general. An iid Bernoulli(1/2) example: $X_n$ built as nested indicator windows converges in probability to 0 but not almost surely. A binomial$(n, \lambda/n)$ converges in distribution to Poisson$(\lambda)$ but the actual values need not be close.

A sufficient condition for convergence in distribution is convergence of moment-generating functions: if $m_{X_n}(t) \to m_X(t)$ on a neighborhood of 0, then $X_n \xrightarrow{d} X$.

## The Law of Large Numbers

### Weak Law (LLN)

Let $X_1, X_2, \ldots$ be independent with common mean $\mu$ and variances bounded by some $\sigma^2$. Let $\bar{M}_n = (X_1 + \cdots + X_n)/n$. Then for all $\varepsilon > 0$,

$$\lim_{n \to \infty} P(|\bar{M}_n - \mu| > \varepsilon) = 0, \quad \text{i.e., } \bar{M}_n \xrightarrow{P} \mu.$$

**Proof sketch:** $E[\bar{M}_n] = \mu$, $\mathrm{Var}(\bar{M}_n) = \sigma^2/n$, Chebyshev gives $P(|\bar{M}_n - \mu| \geq \varepsilon) \leq \sigma^2/(n\varepsilon^2) \to 0$.

If the $X_i$ are iid with finite mean (no variance assumption needed), the conclusion still holds. Intuition: averaging is variance-reducing, so the sample mean concentrates on $\mu$ regardless of the underlying distribution.

### Strong Law (SLLN)

Let $X_1, X_2, \ldots$ be iid with finite mean $\mu$. Then $\bar{M}_n \xrightarrow{a.s.} \mu$. This is strictly stronger than the weak law.

The LLN is the rigorous form of long-run relative frequency: if each trial of an event has probability $p$, the empirical frequency converges (a.s. and in probability) to $p$.

### Standard Error of the Mean

The standard deviation of $\bar{M}_n$ is $\sigma/\sqrt{n}$. This is the **standard error of the mean**; the corresponding plug-in $S/\sqrt{n}$ is the **estimated standard error**. Halving the standard error requires quadrupling $n$ — a "law of diminishing returns."

## The Central Limit Theorem

### Statement

Let $X_1, X_2, \ldots$ be iid with finite mean $\mu$ and finite variance $\sigma^2$. Let $S_n = X_1 + \cdots + X_n$ and define the standardized sum

$$Z_n = \frac{S_n - n\mu}{\sigma\sqrt{n}} = \frac{\bar{M}_n - \mu}{\sigma/\sqrt{n}}.$$

Then $Z_n \xrightarrow{d} Z \sim N(0, 1)$ as $n \to \infty$. Equivalently, $S_n$ is approximately $N(n\mu, n\sigma^2)$ and $\bar{M}_n$ is approximately $N(\mu, \sigma^2/n)$, with deviations of order $\sqrt{n}$ and $1/\sqrt{n}$ respectively.

**Proof sketch (via MGFs):** Assume $m_{X-\mu}(t)$ is finite near 0. Expand $m_{X-\mu}(t) = 1 + t^2/2 + o(t^2)$ to get $m_{X-\mu}(t/\sqrt{n})^n \to e^{t^2/2}$, the MGF of $N(0,1)$. By the MGF convergence theorem, $Z_n \xrightarrow{d} N(0,1)$.

**Corollary (Lyapunov/Slutsky style):** If $\hat{\sigma}_n \to \sigma$ in probability, then $\sqrt{n}(\bar{M}_n - \mu)/\hat{\sigma}_n \xrightarrow{d} N(0, 1)$.

### Practical Guidance

- For $n \geq 25$ or 30, the normal approximation is excellent for most unimodal light-tailed distributions.
- Heavier tails (and very skewed distributions) require larger $n$ for the approximation to be accurate in the tails.
- **Continuity correction:** when approximating a discrete distribution (e.g., binomial) by a continuous normal, replace $P(Y = y)$ by $P(y - 0.5 \leq Y \leq y + 0.5)$.

### Continuity Correction for Binomial

If $Y \sim \mathrm{Binomial}(n, p)$, then for integer $y$,

$$P(Y = y) \approx \Phi\!\left(\frac{y + 0.5 - np}{\sqrt{np(1-p)}}\right) - \Phi\!\left(\frac{y - 0.5 - np}{\sqrt{np(1-p)}}\right).$$

### Assessing Error in an Estimate

For iid $X_i$ with mean $\mu$, the estimate $\bar{M}_n$ has approximate $1 - \alpha$ confidence interval

$$\bar{M}_n \pm z_{\alpha/2}\,\sigma/\sqrt{n}.$$

If $\sigma$ is unknown and a consistent estimate $\hat{\sigma}_n$ is available (such as the sample standard deviation $S_n$), replace $\sigma$ by $\hat{\sigma}_n$. The quantity $S_n/\sqrt{n}$ is the estimated standard error. For $1 - \alpha = 0.9974$, $z_{0.0013} \approx 3$ gives the conventional $\pm 3\hat{\sigma}_n/\sqrt{n}$ "virtual certainty" interval.

## Sampling Distributions

A **sampling distribution** is the distribution of a statistic (function of a sample) viewed as a random variable over repeated samples. The sampling distribution of $\bar{M}_n$ has mean $\mu$ and variance $\sigma^2/n$ (for sampling from an infinite population with mean $\mu$ and variance $\sigma^2$).

For finite populations of size $N$ sampled without replacement, the variance of $\bar{M}_n$ is

$$\mathrm{Var}(\bar{M}_n) = \frac{\sigma^2}{n} \cdot \frac{N - n}{N - 1},$$

with the factor $(N-n)/(N-1)$ called the **finite population correction factor**. This is close to 1 unless the sample is a substantial fraction of the population.

### Random Sample Definitions

- **Finite population of size $N$:** a sample $X_1, \ldots, X_n$ is random if every subset of $n$ elements has equal probability of selection.
- **Infinite population:** a sample is random if (i) each $X_i$ has the same marginal distribution and (ii) the $X_i$ are independent.

## Normal Theory Distributions

### Standard Normal and Properties

Recall that if $X \sim N(\mu, \sigma^2)$ then $(X - \mu)/\sigma \sim N(0, 1)$. The MGF is $m(t) = \exp(\mu t + \sigma^2 t^2/2)$. Linear combinations of independent normals are normal:

If $X_i \sim N(\mu_i, \sigma_i^2)$ independent and $Y = \sum a_i X_i + b$, then $Y \sim N\!\left(\sum a_i \mu_i + b,\, \sum a_i^2 \sigma_i^2\right)$.

In particular, $\bar{M}_n \sim N(\mu, \sigma^2/n)$ when sampling from a normal population — no large-$n$ approximation needed.

### Covariance-Implies-Independence for Linear Combinations of Independent Normals

If $U = \sum a_i X_i$ and $V = \sum b_i X_i$ are linear combinations of independent normals, then

$$\mathrm{Cov}(U, V) = \sum_i a_i b_i \sigma_i^2,$$

and $\mathrm{Cov}(U, V) = 0$ iff $U$ and $V$ are independent. This zero-covariance-implies-independence property is special to the normal family and fails for general distributions (and even for joint normal pairs that are not formed as linear combinations of independent normals).

### Chi-Squared Distribution $\chi^2_n$

**Definition.** $Z \sim \chi^2_n$ has the distribution of $X_1^2 + \cdots + X_n^2$ where $X_1, \ldots, X_n$ are iid $N(0, 1)$. The parameter $n$ is the degrees of freedom.

**Key properties:**

- $E[Z] = n$, $\mathrm{Var}(Z) = 2n$.
- $Z \sim \mathrm{Gamma}(n/2, 1/2)$, i.e., density $f_Z(z) = \frac{1}{2^{n/2} \Gamma(n/2)} z^{n/2 - 1} e^{-z/2}$ for $z > 0$.
- $\chi^2_1$ density: $f(z) = \frac{1}{\sqrt{2\pi z}} e^{-z/2}$ for $z > 0$.
- $\chi^2_2$ coincides with $\mathrm{Exponential}(2)$.
- Sum of independent chi-squareds: $\chi^2_{n_1} + \chi^2_{n_2} \sim \chi^2_{n_1 + n_2}$.

**Sample variance identity.** If $X_1, \ldots, X_n$ are iid $N(\mu, \sigma^2)$, with $\bar{X}$ the sample mean and $S^2 = \frac{1}{n-1}\sum (X_i - \bar{X})^2$ the sample variance, then

$$\frac{(n-1)S^2}{\sigma^2} \sim \chi^2_{n-1}, \qquad \bar{X} \perp\!\!\!\perp S^2, \qquad \bar{X} \sim N(\mu, \sigma^2/n).$$

In particular $E[S^2] = \sigma^2$ (which is why the divisor is $n-1$ rather than $n$). This independence of $\bar{X}$ and $S^2$ holds for samples from a normal population, not in general.

### Student's $t$ Distribution $t_n$

**Definition.** $T \sim t_n$ has the distribution of $\frac{Z}{\sqrt{W/n}}$ where $Z \sim N(0,1)$ and $W \sim \chi^2_n$ are independent. Equivalently, for iid $N(\mu, \sigma^2)$ samples,

$$T = \frac{\bar{X} - \mu}{S/\sqrt{n}} \sim t_{n-1}.$$

**Density:**

$$f_T(t) = \frac{\Gamma((n+1)/2)}{\sqrt{n\pi}\,\Gamma(n/2)} \left(1 + \frac{t^2}{n}\right)^{-(n+1)/2}, \quad t \in \mathbb{R}.$$

**Properties:**

- Symmetric about 0, bell-shaped, with mean 0 (for $n \geq 2$) and heavier tails than $N(0,1)$.
- $t_1$ is the Cauchy distribution.
- $t_n \xrightarrow{d} N(0,1)$ as $n \to \infty$.
- If $T \sim t_n$, then $T^2 \sim F_{1, n}$.
- $\mathrm{Var}(T) = n/(n-2)$ for $n \geq 3$.

When sampling from a normal population, the $t$-distribution provides exact inference for $\mu$ when $\sigma$ is unknown, replacing the unknown $\sigma$ with the sample $S$ (a price paid in heavier tails).

### $F$ Distribution $F_{m, n}$

**Definition.** $U \sim F_{m, n}$ has the distribution of $\frac{W_1/m}{W_2/n}$ where $W_1 \sim \chi^2_m$ and $W_2 \sim \chi^2_n$ are independent. Equivalently, for two independent normal samples,

$$F = \frac{S_1^2}{S_2^2} \sim F_{n_1 - 1,\, n_2 - 1}$$

when the two populations share the same variance.

**Density:**

$$f_U(u) = \frac{\Gamma((m+n)/2)}{\Gamma(m/2)\Gamma(n/2)} \left(\frac{m}{n}\right)^{m/2} \frac{u^{m/2 - 1}}{(1 + mu/n)^{(m+n)/2}}, \quad u > 0.$$

**Reciprocal identity:** if $U \sim F_{m, n}$ then $1/U \sim F_{n, m}$. Useful for table lookups of left-tail probabilities.

**Asymptotic:** $m U \xrightarrow{d} \chi^2_m$ as $n \to \infty$.

### Summary Table of Normal-Theory Distributions

| Distribution | Definition | Mean | Variance | MGF | Use |
|---|---|---|---|---|---|
| $N(\mu, \sigma^2)$ | continuous, density $\frac{1}{\sigma\sqrt{2\pi}}e^{-(x-\mu)^2/(2\sigma^2)}$ | $\mu$ | $\sigma^2$ | $\exp(\mu t + \sigma^2 t^2/2)$ | sample mean inference; CLT limit |
| $\chi^2_n$ | sum of $n$ squared $N(0,1)$ | $n$ | $2n$ | $(1-2t)^{-n/2}$ for $t<1/2$ | sample variance inference |
| $t_n$ | $N(0,1)/\sqrt{\chi^2_n/n}$ | 0 (n≥2) | $n/(n-2)$ | — | $\mu$ inference with unknown $\sigma$ |
| $F_{m,n}$ | $(\chi^2_m/m)/(\chi^2_n/n)$ | $n/(n-2)$ (n>2) | complex | — | ratio of sample variances |

## Representations of Normal-Theory Distributions

Let $Z, Z_1, Z_2, \ldots$ be iid $N(0, 1)$. Then:

- **Chi-square:** $\chi^2_\nu = \sum_{i=1}^\nu Z_i^2$.
- **t:** $t_\nu = Z / \sqrt{\chi^2_\nu / \nu}$, with $Z \perp\!\!\!\perp \chi^2_\nu$.
- **F:** $F_{\nu_1, \nu_2} = \frac{\chi^2_{\nu_1}/\nu_1}{\chi^2_{\nu_2}/\nu_2}$, with $\chi^2_{\nu_1} \perp\!\!\!\perp \chi^2_{\nu_2}$.

For iid $N(\mu, \sigma^2)$ samples, defining $Z_i = (X_i - \mu)/\sigma$:

- $\sqrt{n}\,\bar{Z} = \sqrt{n}(\bar{X} - \mu)/\sigma \sim N(0, 1)$.
- $\sum_{i=1}^n Z_i^2 = \sum_{i=1}^n (Z_i - \bar{Z})^2 + n\bar{Z}^2$, with the two right-hand terms independent and distributed $\chi^2_{n-1}$ and $\chi^2_1$ respectively.

From these representations, $T = \frac{\bar{X} - \mu}{S/\sqrt{n}} \sim t_{n-1}$ and $\frac{(n-1)S^2}{\sigma^2} \sim \chi^2_{n-1}$ follow.

## Deriving Sampling Distributions

### Moment-Generating Function Method

If $X_1, \ldots, X_n$ are independent with MGFs $M_{X_i}(t)$ and all MGFs exist on a common interval around 0, then

$$M_{X_1 + \cdots + X_n}(t) = \prod_{i=1}^n M_{X_i}(t).$$

The product is then identified as a known MGF. Key examples:

- Sum of independent $N(\mu_i, \sigma_i^2)$ is $N\!\left(\sum \mu_i, \sum \sigma_i^2\right)$.
- Sum of independent $\mathrm{Poisson}(\lambda_i)$ is $\mathrm{Poisson}\!\left(\sum \lambda_i\right)$.
- Sum of independent $\chi^2_{\nu_i}$ is $\chi^2_{\sum \nu_i}$.
- Sum of iid geometric($p$) gives the negative binomial.

The MGF method is the canonical tool for sums of independent random variables when the components share a common distribution family.

### Convolution Formula

For independent $X, Y$ with densities $f_X, f_Y$:

$$f_{X+Y}(z) = \int_{-\infty}^\infty f_X(x) f_Y(z - x)\,dx, \qquad f_{Y/X}(z) = \int_{-\infty}^\infty |x|\, f_X(x) f_Y(xz)\,dx.$$

For discrete, non-negative integer-valued independent $X, Y$:

$$P(X + Y = z) = \sum_{x=0}^z P(X = x) P(Y = z - x).$$

### Distribution Function Method

For $Y = h(X)$ with $h$ strictly increasing, $G(y) = F_X(w(y))$ where $w = h^{-1}$.

### Transformation Method

For $Y = h(X)$ with $h$ differentiable and strictly monotonic on the support of $X$:

$$g(y) = f_X(w(y))\,|w'(y)|, \qquad w = h^{-1}.$$

For multivariate: with $Y = h(X)$ invertible, $g(y) = f_X(w(y))\,|J|$ where $J = \det(\partial x / \partial y)$.

### Probability Integral Transform

If $X$ has continuous distribution function $F_X$, then $Y = F_X(X) \sim \mathrm{Uniform}(0, 1)$. Conversely, if $U \sim \mathrm{Uniform}(0, 1)$ and $F^{-1}$ is the inverse CDF, $F^{-1}(U) \sim F_X$.

## Monte Carlo Methods

### Approximating Integrals and Sums

For any $\mu = E[g(X)]$ with iid $X_1, \ldots, X_n$ from the relevant distribution, the LLN guarantees $\bar{M}_n = \frac{1}{n}\sum g(X_i) \to \mu$. The estimated standard error is $S_n/\sqrt{n}$, giving the approximate confidence interval $\bar{M}_n \pm 3 S_n/\sqrt{n}$.

**Approximating definite integrals:** for $I = \int_a^b g(x)\,dx$, choose any density $f$ on $[a, b]$ from which one can sample, write $I = E[g(X)/f(X)]$, and average.

**Approximating sums:** for $S = \sum_j a_j$ with $a_j \geq 0$ and $\sum a_j = C$, let $p_j = a_j / C$ and view $S = C \cdot E[X^2]$ for $X \sim$ distribution with pmf $p_j$.

### Importance Sampling

To approximate $\int_a^b g(x)\,dx$, choose an **importance sampler** density $f$ on $[a, b]$ and estimate

$$\hat{I}_n = \frac{1}{n}\sum_{i=1}^n \frac{g(X_i)}{f(X_i)}, \qquad X_i \sim f.$$

Variance:

$$\mathrm{Var}(\hat{I}_n) = \frac{1}{n}\left[\int_a^b \frac{g(x)^2}{f(x)}\,dx - I^2\right].$$

The optimal importance sampler is $f^*(x) \propto g(x)$, but this is generally infeasible because it requires knowing $I$. In practice, choose $f$ that mimics the shape of $g$ (large where $g$ is large), which can dramatically reduce variance over uniform or naive choices.

**Standard error of importance sampling estimate:** $\sqrt{\mathrm{Var}(\hat{I}_n)/n}$, with $\mathrm{Var}(\hat{I}_n)$ itself estimated from the sample.

### Monte Carlo Algorithm for Sampling Distributions

To estimate $F_Y(y) = P(Y \leq y)$ where $Y = h(X_1, \ldots, X_n)$ with iid $X_i$ from $P$:

1. Generate $N$ independent samples of size $n$: $(X_{i1}, \ldots, X_{in})$ for $i = 1, \ldots, N$.
2. Compute $Y_i = h(X_{i1}, \ldots, X_{in})$.
3. Estimate $F_Y(y) \approx \frac{1}{N}\sum_{i=1}^N \mathbf{1}[Y_i \leq y]$.

The error shrinks as $1/\sqrt{N}$ (independent of $n$).

### Buffon's Needle

Drop a needle of length $\ell$ on a ruled surface with line spacing $d \geq \ell$. The probability of touching a line is $P = 2\ell/(\pi d)$, providing a Monte Carlo estimator for $\pi$: $\hat{\pi} = 2\ell N/(d \cdot K)$ where $K$ is the number of crossings in $N$ drops.

## Chi-Square Goodness-of-Fit Intuition

While detailed tests come later, the chi-squared distribution underlies classical goodness-of-fit testing. If $O_j$ are observed counts in $k$ categories and $E_j$ are expected counts under a hypothesized distribution, the statistic

$$\chi^2 = \sum_{j=1}^k \frac{(O_j - E_j)^2}{E_j}$$

is approximately $\chi^2_{k - 1 - p}$ where $p$ is the number of estimated parameters, when the hypothesis holds.

## Inference for a Single Mean

### Point Estimation

The sample mean $\bar{X}$ is the standard point estimator of $\mu$. Its standard error is $\sigma/\sqrt{n}$ (known $\sigma$) or $S/\sqrt{n}$ (estimated standard error, with $S^2 = \frac{1}{n-1}\sum (X_i - \bar{X})^2$).

### Maximum Error of Estimate

For known $\sigma$ and large $n$, $P(|\bar{X} - \mu| \leq z_{\alpha/2} \sigma/\sqrt{n}) \approx 1 - \alpha$, giving maximum error $E = z_{\alpha/2} \sigma/\sqrt{n}$. The probability statement applies to the **method**; once data are observed and $\bar{x}$ is computed, one makes a **confidence statement** about the parameter.

### Confidence Intervals (Classical Normal-Theory Summary)

| Setting | $(1-\alpha)$ Confidence Interval for $\mu$ |
|---|---|
| $\sigma$ known, normal or large $n$ | $\bar{X} \pm z_{\alpha/2}\,\sigma/\sqrt{n}$ |
| $\sigma$ unknown, normal population | $\bar{X} \pm t_{\alpha/2,\,n-1}\,S/\sqrt{n}$ |
| Large $n$, $\sigma$ unknown | $\bar{X} \pm z_{\alpha/2}\,S/\sqrt{n}$ (t approx) |

The width of the CI is the **maximum error**; halving it requires quadrupling $n$.

### Hypothesis Testing for a Mean

To test $H_0: \mu = \mu_0$ against $H_1: \mu \neq \mu_0$ (two-sided):

- Known $\sigma$: reject $H_0$ at level $\alpha$ if $|Z| = |\bar{X} - \mu_0|/(\sigma/\sqrt{n}) > z_{\alpha/2}$.
- Unknown $\sigma$, normal population: reject $H_0$ if $|T| = |\bar{X} - \mu_0|/(S/\sqrt{n}) > t_{\alpha/2,\,n-1}$.

One-sided tests replace $z_{\alpha/2}$ by $z_\alpha$ or $t_{\alpha, n-1}$ and use a one-sided rejection region.

### Power, Sample Size, and Operating Characteristics

The **power function** $\beta(\mu) = P(\text{reject } H_0 \mid \mu)$ depends on the true mean. For the two-sided $z$-test at level $\alpha$ with true mean $\mu \neq \mu_0$,

$$\beta(\mu) = \Phi\!\left(z_{\alpha/2} - \frac{\mu - \mu_0}{\sigma/\sqrt{n}}\right) + \Phi\!\left(-z_{\alpha/2} - \frac{\mu - \mu_0}{\sigma/\sqrt{n}}\right).$$

**Sample size for given power $1 - \beta$ at effect $\delta = \mu - \mu_0$:** solve $\sqrt{n} |\delta|/\sigma = z_{\alpha/2} + z_\beta$, giving

$$n = \frac{(z_{\alpha/2} + z_\beta)^2 \sigma^2}{\delta^2}.$$

**Operating characteristic curve** plots $1 - \beta(\mu)$ against $\mu$ and is read alongside the type-I error $\alpha$ to assess test quality.

### Connection Between Tests and Confidence Intervals

A two-sided level-$\alpha$ test of $H_0: \mu = \mu_0$ rejects iff $\mu_0$ lies outside the corresponding $(1-\alpha)$ CI. The set of $\mu_0$ values **not** rejected at level $\alpha$ forms the $(1-\alpha)$ CI. This duality holds generally.

## Worked Examples of Standard Normal Computations

**Example 1 (CLT for proportion).** A coin has unknown $P(\text{head}) = p$. With $\bar{M}_n$ the sample proportion, $\sqrt{n}(\bar{M}_n - p)/\sqrt{p(1-p)} \xrightarrow{d} N(0, 1)$. Estimating $p$ by $\bar{M}_n$ in the standard error gives a plug-in CI for $p$.

**Example 2 (Continuity-corrected normal approximation).** $Y \sim \mathrm{Binomial}(1000, 0.6)$. Then $E[Y] = 600$, $\mathrm{Var}(Y) = 240$. For $P(550 \leq Y \leq 625)$ with continuity correction:

$$P(549.5 \leq Y \leq 625.5) \approx \Phi\!\left(\frac{625.5 - 600}{\sqrt{240}}\right) - \Phi\!\left(\frac{549.5 - 600}{\sqrt{240}}\right) = \Phi(1.646) - \Phi(-3.259) \approx 0.9501.$$

**Example 3 (One-sided t-test).** With $n = 14$, $\bar{x} = 46$, $s = 9.4$, $H_0: \mu = 40$: $T = (46 - 40)/(9.4/\sqrt{14}) = 2.388$. Comparing to $t_{0.025, 13} = 2.160$ (two-sided) or $t_{0.05, 13} = 1.771$ (one-sided 5%), the data refute the claim that $\mu \leq 40$.

## Practical Pitfalls and Caveats

- **Do not confuse** the population distribution (variation in a single observation) with the sampling distribution of a statistic (variation of the statistic over samples).
- **Finite population correction:** when sampling a non-negligible fraction of a finite population, multiply the variance of $\bar{M}_n$ by $(N-n)/(N-1)$.
- **Nonnormal populations:** the CLT gives normal approximations for the sampling distribution of $\bar{M}_n$ when $n \geq 25$–$30$ for most unimodal light-tailed populations, but heavier tails demand larger $n$.
- **Selecting random samples:** watch for selection bias, sampling from the wrong population, and human-judgment non-randomness; use random-number generators or mechanical devices.
- **Zero-covariance-implies-independence** is not generally true; it holds for linear combinations of independent normals and for joint normals (with care).
- **Simulating Poisson processes** requires exponential interarrivals, not Poisson counts over fixed intervals.
- **iid is stronger than independent:** the LLN/CLT require (at least) independent with common mean for LLN and iid with finite mean and variance for CLT.
- **Standard error vs. standard deviation:** the SE of $\bar{M}_n$ is $\sigma/\sqrt{n}$, not $\sigma$.
- **Confidence vs. probability:** the $1-\alpha$ refers to the procedure, not to the parameter; once the interval is computed, one makes a confidence statement.
- **Independence of $\bar{X}$ and $S^2$** is a special property of samples from a normal distribution, not a general fact.
- **Independence of Poisson increments over disjoint intervals** is the defining property of the Poisson process and underlies all its calculations.
