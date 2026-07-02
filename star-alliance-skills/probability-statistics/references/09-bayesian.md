---
type: Document
timestamp: 2026-07-02T12:28:13Z
---

# Statistical Inference: Distribution-Free Methods, Bayesian Inference, and Computational Approaches

This reference covers nonparametric and large-sample inference procedures, the asymptotic theory of maximum likelihood estimation, and the Bayesian approach to statistical inference. It unifies rigorous likelihood-based foundations, applied/engineering perspectives on methods, and data-science-flavored computational viewpoints, emphasizing when and why each method applies and the conditions needed for validity.

---

## 1. Distribution-Free Methods

### 1.1 Motivation and Scope

When the assumed model $\{P_\theta : \theta \in \Theta\}$ is misspecified, parametric methods (likelihood, MLE) can be very misleading. **Distribution-free methods** enlarge the model to be as broad as possible—often the set of all distributions on $\mathbb{R}$ having certain moments—so that valid inferences can be made with minimal assumptions.

- Finite sample spaces: easy to take the distribution-free view (e.g., Bernoulli on $\{0,1\}$ is already "free").
- Infinite sample spaces: restrictions (e.g., finite moments) are usually necessary.

**Trade-off:** Larger models make weaker assumptions, but typically yield less powerful inferences. Smaller (correctly specified) models extract more information.

### 1.2 Method of Moments

#### Estimator and Properties

Let $X_1, \ldots, X_n$ be i.i.d. with population moments $\mu_i = E[X_1^i]$. The $i$-th sample moment is
$$m_i = \frac{1}{n}\sum_{j=1}^n X_j^i.$$

- $E[m_i] = \mu_i$ (unbiased).
- By the WLLN/SLLN: $m_i \xrightarrow{P, a.s.} \mu_i$.
- By the CLT: $\sqrt{n}(m_i - \mu_i) \xrightarrow{D} N(0, \sigma_i^2)$ where
$$\sigma_i^2 = \text{Var}(X_1^i) = \mu_{2i} - \mu_i^2,$$
provided $i \le l$ and the $(2i)$-th moment exists.

An unbiased estimator of $\sigma_i^2$ is
$$s_i^2 = \frac{1}{n-1}\sum_{j=1}^n (X_j^i - m_i)^2.$$

**Approximate $1-\alpha$ confidence interval for $\mu_i$:**
$$m_i \pm z_{1-\alpha/2}\, \frac{s_i}{\sqrt{n}}.$$

**Method of moments principle:** A differentiable function $g(\mu_1, \ldots, \mu_k)$ is estimated by $g(m_1, \ldots, m_k)$, with asymptotic variance determined by the delta method.

#### Delta Theorem (One-Dimensional)

If $g$ is continuously differentiable at $(\mu_1)$ with $g'(\mu_1) \ne 0$, then
$$\sqrt{n}\bigl(g(m_1) - g(\mu_1)\bigr) \xrightarrow{D} N\bigl(0, [g'(\mu_1)]^2 \sigma_1^2\bigr).$$

**Worked example:** For $g(\mu) = 1/\mu^2$ with $\mu_2$ known, $g'(\mu) = -2/\mu^3$, so
$$\sqrt{n}\bigl(m_1^{-2} - \mu^{-2}\bigr) \xrightarrow{D} N\!\left(0, \frac{4\sigma_1^2}{\mu^6}\right).$$

**Caveat:** $g$ must be continuously differentiable at the true value; if $\mu_1 = 0$ (or near 0), the delta method is invalid.

### 1.3 Bootstrapping

#### Empirical Distribution Function

The empirical cdf is
$$\hat F_n(x) = \frac{1}{n}\sum_{i=1}^n \mathbf{1}\{X_i \le x\}.$$

- Unbiased: $E[\hat F_n(x)] = F(x)$.
- Consistent (WLLN/SLLN).
- Variance: $\text{Var}[\hat F_n(x)] = \frac{F(x)(1-F(x))}{n} \to 0$ (mean-square convergence).
- $n \cdot \hat F_n(x) \sim \text{Binomial}(n, F(x))$.

#### Bootstrap Procedure

Suppose interest is in $T(F)$, estimated by $\hat\theta = h(X_1, \ldots, X_n)$. The bootstrap:

1. Treat $\hat F_n$ as the true distribution; it puts mass $1/n$ on each distinct $X_i$ (or $f_i/n$ on $X_i$ if repeated, where $f_i$ is the frequency).
2. Draw $m$ i.i.d. **bootstrap (resample) samples** of size $n$ from $\hat F_n$ (sampling with replacement from $\{X_1, \ldots, X_n\}$).
3. Compute $\hat\theta^{*(b)} = h(\text{b-sample } b)$ for $b = 1, \ldots, m$.
4. **Bootstrap mean:** $\overline{\hat\theta^*} = \frac{1}{m}\sum_{b=1}^m \hat\theta^{*(b)}$.
5. **Bootstrap variance / standard error:**
$$s^{*2}_b = \frac{1}{m-1}\sum_{b=1}^m \bigl(\hat\theta^{*(b)} - \overline{\hat\theta^*}\bigr)^2.$$

The estimated MSE is
$$\widehat{\text{MSE}}(\hat\theta) = \bigl(T(\hat F_n) - \hat\theta\bigr)^2 + s^{*2}_b$$
(combining squared-bias estimate with bootstrap variance).

**Why it works:** With large $n$, $\hat F_n$ is close to $F$, so the bootstrap distribution approximates the sampling distribution of $\hat\theta$. Requires finite first two moments of $\hat\theta$.

**Computational scale:** The exact formula for the bootstrap variance requires $n^n$ evaluations—e.g., $n=15$ gives $\approx 4.4 \times 10^{17}$ terms. Resampling with $m$ draws (typically $m = 10^3$ to $10^5$) is essential.

#### Choosing $m$

Run for successively larger $m$ and stop when $s^*_b$ stabilizes. This is heuristic; very slow convergence can fool the practitioner.

#### Bootstrap Confidence Intervals

| Interval Type | Formula | Assumption |
|---|---|---|
| Bootstrap $t$ | $\hat\theta \pm t_{1-\alpha/2, n-1}\, s^*_b$ | Bootstrap distribution approximately normal |
| Bootstrap percentile | $[\hat q^*_{\alpha/2}, \hat q^*_{1-\alpha/2}]$ where $\hat q^*_p$ is the $p$-th empirical quantile of $\{\hat\theta^{*(b)}\}$ | Bootstrap distribution approximately normal and approximately unbiased |

**Pitfall:** These require approximate normality of the bootstrap distribution. The sample median and trimmed mean do **not** always have normal bootstrap distributions (skewed), so naive intervals may fail.

#### Trimmed Mean (Definition 6.4.1)

For $0 \le \alpha \le 1/2$, the $\alpha$-trimmed mean is
$$\bar X_\alpha = \frac{1}{n - 2\lfloor n\alpha \rfloor}\sum_{i = \lfloor n\alpha \rfloor + 1}^{n - \lfloor n\alpha \rfloor} X_{(i)},$$
where $X_{(i)}$ is the $i$-th order statistic. Special cases: $\alpha = 0$ gives the sample mean; $\alpha = 0.5$ gives the sample median (up to convention). Provides robustness to outliers while using more data than the median.

### 1.4 The Sign Statistic and Quantile Inference

#### Setup

Let $F$ be a continuous cdf on $\mathbb{R}$ and $x_p$ the $p$-th quantile: $p = F(x_p)$. The natural estimator is $X_{(\lceil np \rceil)}$ (or interpolation for non-integer $np$).

#### Sign Test Statistic

For testing $H_0: x_p = x_0$:
$$S = \sum_{i=1}^n \mathbf{1}\{X_i \le x_0\},$$
which is the number of observations $\le x_0$. Under $H_0$, $S \sim \text{Binomial}(n, p)$.

**P-value** (two-sided):
$$\text{P-value} = \sum_{i: \binom{n}{i}p^i(1-p)^{n-i} \le \binom{n}{S}p^S(1-p)^{n-S}} \binom{n}{i}p^i(1-p)^{n-i}.$$

For large $n$, the normal approximation (with continuity correction) is
$$\text{P-value} \approx 2\bigl[1 - \Phi\bigl(|S - 0.5 - np|/\sqrt{np(1-p)}\bigr)\bigr].$$

#### Confidence Interval for the Median ($p = 1/2$)

Let $j$ be the smallest integer $> n/2$ such that
$$P\bigl(\text{Bin}(n, 1/2) \in [n/2 - j, n/2 + j]\bigr) \le 1 - \alpha.$$
Then a $1-\alpha$ confidence interval is
$$C = [X_{(n - j + 1)}, X_{(j)}] = [x_{(n-j+1)}, x_{(j)}],$$
because $\sum_{i=1}^n \mathbf{1}\{X_i \le x_0\} \in [n-j, j]$ iff $x_0 \in [X_{(n-j+1)}, X_{(j)}]$.

#### When the Sign Test is Appropriate

- Distribution-free: holds for **any** continuous $F$.
- Robust to outliers and misspecification of shape.
- Less powerful than the $t$-test when the population is normal.
- Recommended when the boxplot or other diagnostics show non-normal features (heavy tails, outliers).

#### Fisher Signed Deviation Test (Randomization Test)

For testing $H_0: \tilde x = x_0$ under symmetry:
$$S = \sum_{i=1}^n (X_i - x_0)\,\text{sgn}(X_i - x_0) = \sum_{i=1}^n |X_i - x_0|.$$

- $S$ is observable from data and equals $n\bar X - n x_0$.
- Conditional on the absolute deviations $\{|X_i - x_0|\}$, the signs $\text{sgn}(X_i - x_0)$ are i.i.d. uniform on $\{-1, +1\}$ (under symmetry).
- Conditional mean of $S$ is 0; conditional distribution symmetric.
- P-value computed from the conditional distribution of $S$ (analogous to a permutation/randomization test).
- Equivalent to a randomized $t$-test: condition on absolute deviations, treat signs as random, compute conditional distribution of $T = (\bar X - x_0)/(\hat\sigma/\sqrt{n})$.

#### Symmetry Lemma (Challenge)

If $X$ is absolutely continuous on $\mathbb{R}$ with density $f$ symmetric about its median 0, then $X$ and $\text{sgn}(X)$ are independent, with $X$ having density $2f$ on $\mathbb{R}$ and $\text{sgn}(X) \sim \text{Uniform}\{-1, +1\}$.

---

## 2. Asymptotic Theory of the MLE

### 2.1 Score Function and Fisher Information

For a parametric model $\{f(x;\theta): \theta \in \Theta\}$ satisfying regularity:
- $\frac{\partial^2 \ln f(x;\theta)}{\partial \theta^2}$ exists for each $x$.
- $E_\theta\bigl[\frac{\partial}{\partial \theta} \ln f(X;\theta)\bigr] = 0$.
- $E_\theta\bigl[\bigl(\frac{\partial}{\partial \theta} \ln f(X;\theta)\bigr)^2\bigr] = -E_\theta\bigl[\frac{\partial^2}{\partial \theta^2} \ln f(X;\theta)\bigr]$.

The **score function** is $S(X;\theta) = \frac{\partial}{\partial \theta} \ln f(X;\theta)$.

The **Fisher information** is
$$I(\theta) = \text{Var}_\theta\bigl[S(X;\theta)\bigr] = E_\theta\bigl[\bigl(\tfrac{\partial}{\partial \theta}\ln f(X;\theta)\bigr)^2\bigr] = -E_\theta\bigl[\tfrac{\partial^2}{\partial \theta^2}\ln f(X;\theta)\bigr].$$

For an i.i.d. sample of size $n$, the Fisher information is $n I(\theta)$ (additive over i.i.d. terms).

### 2.2 Observed vs. Plug-In Fisher Information

- **Plug-in Fisher information:** $I(\hat\theta)$ (substitute MLE into the formula).
- **Observed Fisher information:**
$$I_{\text{obs}}(X_1, \ldots, X_n) = -\frac{\partial^2 \ell(X_1, \ldots, X_n; \theta)}{\partial \theta^2}\bigg|_{\theta = \hat\theta},$$
where $\ell$ is the log-likelihood.

When these are equal, the plug-in and observed information coincide (e.g., location normal, Bernoulli, Poisson).

### 2.3 Nonexistence of Fisher Information

For $X \sim \text{Uniform}[0, \theta]$, the density $f(x;\theta) = \frac{1}{\theta}\mathbf{1}_{[0,\theta]}(x)$ is **not differentiable at $x = \theta$**, so $I(\theta)$ is not defined. Models with support depending on $\theta$ typically fail the regularity conditions.

### 2.4 Asymptotic Theorems for the MLE

**Theorem (Consistency).** Under regularity, $\hat\theta_n \xrightarrow{a.s.} \theta$ as $n \to \infty$ (a strong law for the MLE).

**Theorem (Asymptotic Normality).** Under regularity,
$$\sqrt{n I(\theta)}\,(\hat\theta_n - \theta) \xrightarrow{D} N(0, 1).$$

**Corollary.** When $I(\theta)$ is continuous in $\theta$,
$$\sqrt{n I(\hat\theta_n)}\,(\hat\theta_n - \theta) \xrightarrow{D} N(0, 1).$$
If $I(\hat\theta_n)$ is hard to compute, replace by the observed Fisher information $I_{\text{obs}}$ and the result still holds.

### 2.5 Large-Sample Inferences Based on the MLE

| Quantity | Formula |
|---|---|
| Approximate SE of $\hat\theta_n$ | $1/\sqrt{n I(\hat\theta_n)}$ or $1/\sqrt{I_{\text{obs}}}$ |
| Approximate $1-\alpha$ CI for $\theta$ | $\hat\theta_n \pm z_{1-\alpha/2} \cdot 1/\sqrt{n I(\hat\theta_n)}$ |
| Two-sided P-value for $H_0: \theta = \theta_0$ | $2\bigl[1 - \Phi(\sqrt{n I(\theta_0)}\,|\hat\theta_n - \theta_0|)\bigr]$ |

**Key idea:** For hypothesis testing, use the Fisher information evaluated **at $\theta_0$** (not at the MLE) since under $H_0$ we know the true asymptotic variance $1/[n I(\theta_0)]$.

### 2.6 Examples of Fisher Information

| Model | $I(\theta)$ | Plug-in $I(\hat\theta)$ | Observed $I$ |
|---|---|---|---|
| $N(\theta, \sigma_0^2)$ (location, $\sigma_0$ known) | $1/\sigma_0^2$ | $1/\sigma_0^2$ | $n/\sigma_0^2$ |
| Bernoulli($\theta$) | $1/[\theta(1-\theta)]$ | $1/[\hat\theta(1-\hat\theta)]$ | $n/[\hat\theta(1-\hat\theta)]$ |
| Poisson($\theta$) | $1/\theta$ | $1/\hat\theta$ | $n/\hat\theta$ |
| Exponential($\theta$) | $1/\theta^2$ | $1/\hat\theta^2$ | $n/\hat\theta^2$ |
| Gamma($\alpha_0, \theta$) (shape known) | $\alpha_0/\theta^2$ | $\alpha_0/\hat\theta^2$ | $n\alpha_0/\hat\theta^2$ |
| Pareto($\theta, x_0$ known) | $1/\theta^2$ (for $x_0 = 1$) | $1/\hat\theta^2$ | — |

### 2.7 Multivariate Fisher Information (Definition)

For $\theta = (\theta_1, \theta_2) \in \mathbb{R}^2$, the Fisher information matrix is
$$I(\theta) = \begin{pmatrix} E\bigl[\bigl(\tfrac{\partial \ell}{\partial \theta_1}\bigr)^2\bigr] & E\bigl[\tfrac{\partial \ell}{\partial \theta_1}\tfrac{\partial \ell}{\partial \theta_2}\bigr] \\ E\bigl[\tfrac{\partial \ell}{\partial \theta_2}\tfrac{\partial \ell}{\partial \theta_1}\bigr] & E\bigl[\bigl(\tfrac{\partial \ell}{\partial \theta_2}\bigr)^2\bigr] \end{pmatrix}.$$

---

## 3. Bayesian Inference

### 3.1 The Bayesian Model

Components:
- **Sampling model:** $\{f(x;\theta): \theta \in \Theta\}$ for data $S$.
- **Prior distribution** $\pi(\theta)$ for the parameter (discrete probability function or density on $\Theta$).
- **Joint distribution:** $f_S(s)\,\pi(\theta)$ (or $p(s\mid\theta)\pi(\theta)$ in discrete form).
- **Prior predictive distribution** (marginal for $S$):
$$m(s) = \int_\Theta f(s;\theta)\,\pi(\theta)\,d\theta \quad (\text{or sum over discrete }\theta).$$

### 3.2 Posterior Distribution

By conditional probability / Bayes' theorem:
$$p(\theta \mid s) = \frac{f(s;\theta)\,\pi(\theta)}{m(s)}.$$

The denominator $m(s)$ is the **inverse normalizing constant**. Often the functional form of the posterior is recognized without computing $m(s)$.

The Bayesian approach is **axiomatic** (principle of conditional probability), not a theorem.

### 3.3 Standard Conjugate Pairs

| Sampling model | Conjugate prior | Posterior |
|---|---|---|
| Bernoulli($\theta$), $n$ trials with $\sum x_i = n\bar x$ | $\text{Beta}(\alpha, \beta)$ | $\text{Beta}(\alpha + n\bar x, \beta + n(1-\bar x))$ |
| Poisson($\theta$), $n$ observations, $\sum x_i = s$ | $\text{Gamma}(\alpha, \beta)$ | $\text{Gamma}(\alpha + s, \beta + n)$ |
| Exponential($\theta$), $n$ observations | $\text{Gamma}(\alpha, \beta)$ | $\text{Gamma}(\alpha + n, \beta + n\bar x)$ |
| $N(\theta, \sigma_0^2)$, $\sigma_0$ known | $N(\mu_0, \tau_0^2)$ | $N\!\left(\frac{\mu_0/\tau_0^2 + n\bar x/\sigma_0^2}{1/\tau_0^2 + n/\sigma_0^2}, \frac{1}{1/\tau_0^2 + n/\sigma_0^2}\right)$ |
| $N(\mu_0, \theta)$ (scale, $\mu_0$ known) | $1/\theta \sim \text{Gamma}(\alpha, \beta)$ | $1/\theta \sim \text{Gamma}(\alpha + n/2, \beta + \sum(x_i - \mu_0)^2/2)$ |
| Multinomial($n, \theta_1, \ldots, \theta_k$) | Dirichlet($\alpha_1, \ldots, \alpha_k$) | Dirichlet($\alpha_1 + x_1, \ldots, \alpha_k + x_k$) |
| Uniform($[0, \theta]$) | Pareto (Improper Jeffreys $1/\theta$) | Improper — see below |

**Location–scale normal conjugate prior (Normal–Inverse-Gamma):**
- Conditional: $\theta \mid \sigma^2 \sim N(\mu_0, \sigma^2/\kappa_0)$.
- $1/\sigma^2 \sim \text{Gamma}(\alpha_0, \beta_0)$.
- Posterior (from $n\bar x = \sum x_i$, $s^2 = $ sample variance):
  - $\mu_* = \frac{\kappa_0 \mu_0 + n\bar x}{\kappa_0 + n}$, $\kappa_* = \kappa_0 + n$.
  - $\theta \mid \sigma^2, \text{data} \sim N(\mu_*, \sigma^2/\kappa_*)$.
  - $1/\sigma^2 \mid \text{data} \sim \text{Gamma}(\alpha_*, \beta_*)$ where
    - $\alpha_* = \alpha_0 + n/2$.
    - $\beta_* = \beta_0 + \tfrac{1}{2}\sum(x_i - \bar x)^2 + \frac{\kappa_0 n(\bar x - \mu_0)^2}{2(\kappa_0 + n)}$.

**Multinomial–Dirichlet:** $\theta_i \mid \text{data} \sim \text{Beta}(\alpha_i + x_i, \alpha_0 + n - \alpha_i - x_i)$ marginally (where $\alpha_0 = \sum_j \alpha_j$).

### 3.4 Posterior-Based Inferences

#### Point Estimation

- **Posterior mode (MAP):** $\hat\theta_{MAP} = \arg\max_\theta p(\theta \mid s)$. Equivalent to maximizing any 1–1 increasing function of $p(\theta \mid s)$, so the inverse normalizing constant is not needed.
- **Posterior mean:** $\hat\theta_{PM} = E[\theta \mid s]$ (requires existence).

When the posterior is symmetric about its mode, these agree. For skewed posteriors, they can differ substantially.

**Posterior mean examples (for uniform prior, $\alpha = \beta = 1$):**
- Bernoulli: $E[\theta \mid s] = (n\bar x + 1)/(n + 2)$.
- Bernoulli MAP: $\hat\theta_{MAP} = n\bar x / n = \bar x$.

**Posterior variances (with uniform prior):**
- Bernoulli: $\text{Var}[\theta \mid s] = n\bar x(n - n\bar x) / [(n+2)^2(n+3)] \to 0$.
- Multinomial $\theta_i$: $\text{Var}[\theta_i \mid s] = x_i(n - x_i) / [(n+k-1)^2(n+k)]$.

#### Credible Intervals (Bayesian Analog of Confidence Intervals)

A $1-\alpha$ credible interval $C(s) = [l(s), u(s)]$ satisfies
$$P(\theta \in C(s) \mid S = s) = 1 - \alpha.$$

**Highest Posterior Density (HPD) interval:**
$$C(s) = \{\theta : p(\theta \mid s) \ge c\},$$
where $c$ is the largest value making the probability equal to $1-\alpha$. Shortest among all $1-\alpha$ intervals; always contains the mode.

**Quantile-based interval:** $[q_{\alpha/2}, q_{1-\alpha/2}]$ where $q_p$ is the $p$-th posterior quantile. Avoids HPD computation but may be longer.

**Worked example — location normal:** Posterior $\theta \mid s \sim N(\mu_*, \tau_*^2)$. HPD interval (also the equal-tailed interval due to symmetry) is
$$\mu_* \pm z_{1-\alpha/2} \cdot \tau_*.$$
As $\tau_0 \to \infty$ (diffuse prior), this reduces to the frequentist $z$-interval $\bar x \pm z_{1-\alpha/2} \sigma_0/\sqrt{n}$.

**Worked example — location–scale normal:** Posterior marginally for $\theta$ is (from the Normal–Inverse-Gamma):
$$\frac{\theta - \mu_*}{\sqrt{\beta_*/[\alpha_* \kappa_*]}} \sim t_{2\alpha_*},$$
giving the HPD interval
$$\mu_* \pm t_{1-\alpha/2, 2\alpha_*} \cdot \sqrt{\beta_*/[\alpha_* \kappa_*]}.$$

**Under diffuse prior ($\kappa_0, \beta_0 \to 0$):** $\alpha_* \to n/2$, $\beta_* \to \tfrac{1}{2}\sum(x_i - \bar x)^2$, $\mu_* \to \bar x$, $\kappa_* \to n$, and the interval converges to
$$\bar x \pm t_{1-\alpha/2, n-2} \cdot s/\sqrt{n},$$
matching the frequentist $t$-interval.

#### Hypothesis Testing — Three Approaches

**1. Posterior probability approach:**
$$\text{Evidence against }H_0 \text{ if } P(\theta \in H_0 \mid s) \text{ is small}.$$

**Pitfall:** When $\theta$ has a continuous prior and $H_0 = \{\theta_0\}$ is a point, $P(\theta_0 \mid s) = 0$ **always**, regardless of data. Cannot directly test a point null with continuous prior.

**2. Bayesian P-value:**
$$\text{P-value} = P(p(\Theta \mid s) \le p(\theta_0 \mid s) \mid s) = 1 - P(p(\Theta \mid s) > p(\theta_0 \mid s) \mid s).$$
For unimodal posteriors, equivalent to a tail probability. **Not invariant** to reparameterization (a serious flaw).

**3. Bayes factors (recommended for testing):**

**Odds in favor of $A$:** $O(A) = P(A)/P(A^c)$.

**Bayes factor in favor of $H_0$ (where $H_0 \cup H_0^c = \Theta$):**
$$B(s) = \frac{\text{posterior odds}}{\text{prior odds}} = \frac{P(H_0 \mid s)/P(H_0^c \mid s)}{P(H_0)/P(H_0^c)}.$$

When the prior is a mixture $\pi = p \pi_0 + (1-p)\pi_1$ (where $\pi_0$ is point mass at $\theta_0$ and $\pi_1$ is continuous away from $\theta_0$):
$$B(s) = \frac{m_0(s)}{m_1(s)},$$
where $m_i$ is the prior predictive under $\pi_i$. **Independent of $p$** (Theorem 7.2.1).

Posterior probability of $H_0$:
$$P(H_0 \mid s) = \frac{r \cdot B(s)}{1 + r \cdot B(s)}, \quad r = \text{prior odds} = P(H_0)/P(H_0^c).$$

**Calibration:** $B > 1$ favors $H_0$; $B < 1$ against. Scale: $B \in (0, \infty)$.

#### Prediction

For predicting a future observation $T$ with conditional density $q(t \mid s, \theta)$:

**Posterior predictive density:**
$$q(t \mid s) = \int q(t \mid s, \theta)\, p(\theta \mid s)\, d\theta.$$

**Posterior predictive mean:** $E[T \mid s] = E_\theta[E[T \mid s, \theta] \mid s]$.

**Posterior predictive variance (iterated expectation):**
$$\text{Var}(T \mid s) = E_\theta[\text{Var}(T \mid s, \theta) \mid s] + \text{Var}_\theta[E[T \mid s, \theta] \mid s].$$

**Posterior predictive distribution of $X_{n+1}$ under conjugate normal model** (i.i.d. $N(\theta, \sigma_0^2)$, $N(\mu_0, \tau_0^2)$ prior on $\theta$):
$$X_{n+1} \mid s \sim N\!\left(\mu_*, \tau_*^2 + \sigma_0^2\right).$$

**Predictive interval** for $X_{n+1}$: apply HPD to the posterior predictive.

### 3.5 Bayesian Computations

#### Asymptotic Normality of the Posterior

Under regularity, as $n \to \infty$:
$$\hat\theta_n \mid s \;\dot\sim\; N\!\left(\hat\theta_{MAP}, \frac{1}{I_{\text{obs}}(s)}\right).$$

This is essentially the same as the MLE asymptotic result; $\hat\theta_n$ can be replaced by $\hat\theta_{MLE}$ for practical computation.

#### Monte Carlo Approximation

If $X_1, \ldots, X_N$ are i.i.d. draws from the posterior $p(\theta \mid s)$:
- **Estimate** of $E[g(\theta) \mid s]$: $\bar g = \frac{1}{N}\sum_{i=1}^N g(X_i)$.
- **Variance estimate:** $s_g^2 = \frac{1}{N-1}\sum_{i=1}^N [g(X_i) - \bar g]^2$.
- **Approximate confidence interval** (when $E[g^2] < \infty$): $\bar g \pm z_{1-\alpha/2}\, s_g/\sqrt{N}$.

**Error monitoring:** Compute estimates and $s_g/\sqrt{N}$ for successive $N$; stop when the half-width is small enough and stable.

**Existence check:** Before estimating $E[g(\theta) \mid s]$, verify the posterior moment exists. For unbounded $g$ (e.g., $g(\theta) = 1/\theta$ for a normal model), the mean may be infinite.

#### Gibbs Sampling (MCMC)

For a joint distribution $\pi(\theta_1, \ldots, \theta_k)$ that is hard to sample from directly, but each **full conditional** $\pi(\theta_i \mid \theta_{-i})$ is tractable:

1. Initialize $\theta^{(0)} = (\theta_1^{(0)}, \ldots, \theta_k^{(0)})$.
2. For each iteration $t = 1, 2, \ldots, T$:
   - Draw $\theta_1^{(t)} \sim \pi(\theta_1 \mid \theta_2^{(t-1)}, \ldots, \theta_k^{(t-1)})$.
   - Draw $\theta_2^{(t)} \sim \pi(\theta_2 \mid \theta_1^{(t)}, \theta_3^{(t-1)}, \ldots, \theta_k^{(t-1)})$.
   - $\vdots$
   - Draw $\theta_k^{(t)} \sim \pi(\theta_k \mid \theta_1^{(t)}, \ldots, \theta_{k-1}^{(t)})$.
3. Under mild conditions, $\theta^{(T)} \xrightarrow{D} \pi$ as $T \to \infty$, and
$$\frac{1}{T}\sum_{t=1}^T g(\theta^{(t)}) \to E_\pi[g(\theta)].$$

**Latent variable augmentation:** When full conditionals are not tractable, augment with auxiliary variables $V_1, \ldots, V_l$ to obtain a joint distribution whose full conditionals are easy.

**Variance estimation with MCMC (batch means):** Divide $T$ iterations into $T/m$ non-overlapping batches of size $m$; let $\bar g_b$ be the within-batch mean. Estimate variance by
$$s^2_{\text{batch}} = \frac{m}{T/m - 1}\sum_{b=1}^{T/m} (\bar g_b - \bar g)^2,$$
where $m$ is large enough for adjacent batches to be approximately independent (typically $m \ge 10$).

#### Importance Sampling

To estimate $E_\pi[g]$ with a tractable proposal $q$:
$$E_\pi[g(\theta)] = \frac{E_q[g(\theta)\,w(\theta)]}{E_q[w(\theta)]}, \quad w(\theta) = \pi(\theta)/q(\theta).$$
Critical: $q$ must have heavier tails than $\pi$ where $g$ is large. **Prior importance sampling** (use prior as proposal) is generally weak because the prior is typically much more diffuse than the posterior, leading to high-variance weights.

### 3.6 Choosing Priors

#### Conjugate Priors (Definition 7.4.1)

A family $\{\pi_\eta : \eta \in H\}$ of priors is **conjugate** for a sampling model if, for every prior $\pi_\eta$ and every dataset, the posterior is also of the form $\pi_{\eta'}$ for some $\eta' \in H$. Conjugacy reduces the posterior computation to updating hyperparameters.

| Model | Conjugate family |
|---|---|
| Bernoulli / Binomial | Beta |
| Poisson | Gamma |
| Exponential | Gamma |
| Normal (known $\sigma^2$, unknown $\mu$) | Normal |
| Normal (known $\mu$, unknown $\sigma^2$) | Inverse-Gamma |
| Normal (both unknown) | Normal–Inverse-Gamma |
| Multinomial | Dirichlet |
| Uniform($[0, \theta]$) | Pareto |

#### Elicitation

Specifying a prior by translating expert beliefs into hyperparameters:
- Specify prior mean and variance (or two quantiles).
- For the location normal model with $N(\mu_0, \tau_0^2)$ prior, the prior mean is $\mu_0$ and prior variance is $\tau_0^2$.

For $1 - F_{\text{prior}}(\mu_0 + 3\tau_0) \approx 0.997$, "$\mu_0 \pm 3\tau_0$" gives a practical range.

#### Empirical Bayes

Choose the prior's hyperparameters $\eta$ by maximizing the prior predictive (marginal) likelihood:
$$\hat\eta = \arg\max_\eta\, m(s;\eta) = \arg\max_\eta \int p(s \mid \theta)\,\pi(\theta;\eta)\,d\theta.$$

**Justification:** $m(s;\eta)$ is the "likelihood for $\eta$" treating $s$ as data. Maximizing gives a principled (but data-dependent) choice of $\eta$.

**Violation:** Empirical Bayes technically violates the principle that the prior must be fixed before seeing data. In practice it often works well for moderate/large $n$.

#### Hierarchical Bayes

Place a hyperprior $\pi(\eta)$ on the prior hyperparameters $\eta$, then integrate out:
$$p(\theta \mid s) = \frac{\int p(s \mid \theta)\,\pi(\theta;\eta)\,\pi(\eta)\,d\eta}{\iint p(s \mid \theta)\,\pi(\theta;\eta)\,\pi(\eta)\,d\theta\,d\eta}.$$

Shifts the subjectivity from choosing $\pi(\theta)$ to choosing $\pi(\eta)$.

#### Improper / Non-informative Priors

A prior with $\int \pi(\theta)\,d\theta = \infty$ (e.g., $\pi(\theta) = 1$ on $\mathbb{R}$). The posterior may still be a proper density if the normalizing constant converges.

**Jeffreys' prior:**
$$\pi_J(\theta) \propto \sqrt{I(\theta)}.$$
Invariance: if $\eta = g(\theta)$ is a 1–1 transformation, then $\pi_J(\eta) = \pi_J(\theta)\,|d\theta/d\eta|$. This is a major advantage for invariance.

| Model | Jeffreys' prior |
|---|---|
| $N(\theta, \sigma_0^2)$ location | $1$ (uniform on $\mathbb{R}$) |
| Bernoulli($\theta$) | $\theta^{-1/2}(1-\theta)^{-1/2}$ (proper, $\text{Beta}(1/2, 1/2)$) |
| Exponential($\theta$) | $1/\theta$ on $(0, \infty)$ |
| Poisson($\theta$) | $1/\sqrt{\theta}$ |
| Normal scale $\sigma$ (location known) | $1/\sigma$ |

**Critical checks when using improper priors:**
1. Does the posterior exist as a proper density?
2. Posterior is invariant to multiplication of the prior by any positive constant $c$.
3. Do not interpret the prior as a probability distribution.

---

## 4. Point Estimation Theory (MSE Criterion)

### 4.1 Mean-Squared Error

For an estimator $T$ of $\theta$:
$$\text{MSE}(T) = E_\theta[(T - \theta)^2] = \text{Var}_\theta(T) + [E_\theta(T) - \theta]^2.$$

**Bias-variance decomposition:** MSE = Variance + (Bias)$^2$.

### 4.2 Bias–Variance Trade-off

**Theorem 8.1.1:** Among all constants $c$, the choice $c = E_\theta[T]$ minimizes $E_\theta[(T - c)^2]$. That is,
$$E_\theta[(T - c)^2] = \text{Var}_\theta(T) + [E_\theta(T) - c]^2 \ge \text{Var}_\theta(T),$$
with equality iff $c = E_\theta(T)$.

### 4.3 Unbiasedness

$T$ is **unbiased** for $\theta$ if $E_\theta[T] = \theta$ for all $\theta \in \Theta$.

Restricting to unbiased estimators: the optimal choice minimizes variance. In general, no single estimator has uniformly smallest MSE.

### 4.4 Posterior Mean Minimizes Bayes MSE

**Theorem 10.3.1:** Among all estimators $T(X)$ of $\Theta$ (with squared-error loss and joint prior $\pi$),
$$E[(\theta_{MMSE}(X) - \theta)^2] \le E[(T(X) - \theta)^2],$$
where
$$\theta_{MMSE}(X) = E[\theta \mid X].$$

**Proof sketch:** Condition on $X = x$, apply Theorem 8.1.1 to $E[(T(X) - \theta)^2 \mid X = x]$; then take outer expectation.

This justifies the posterior mean as the optimal point estimator (under squared-error loss and Bayesian framework).

### 4.5 MAP Minimizes Probability of Error (Discrete $\Theta$)

**Theorem 10.3.5:** If $\Theta$ takes finitely many values,
$$\theta_{MAP}(x) = \arg\max_\theta P(\Theta = \theta \mid X = x)$$
minimizes $P(\theta_{MAP}(X) \ne \Theta)$ over all estimators $T(X)$.

This is the **0–1 loss** counterpart to the MMSE result. Useful when the cost of an error is uniform regardless of magnitude.

---

## 5. Consistency of Estimators

### 5.1 Definition

An estimator $\hat\theta_n = h(X_1, \ldots, X_n)$ of $\gamma \in \mathbb{R}$ is **consistent** if it converges to $\gamma$ as $n \to \infty$ in mean square, with probability one, or in probability.

### 5.2 Sample Mean Consistency

**Theorem 9.3.2:** The sample mean $\bar X_n = \frac{1}{n}\sum_{i=1}^n X_i$ is consistent for $\mu = E[X_i]$ as long as $\text{Var}(X_i)$ is bounded. (This is a direct application of the WLLN or SLLN.)

### 5.3 Sample Median Consistency

**Theorem 9.3.4:** The sample median is consistent for the population median $\tilde\mu$ of an i.i.d. sequence — even if the mean is undefined or the variance is infinite. (Holds for any distribution with a unique median.)

**Key implication:** The sample median is more robust than the sample mean. For heavy-tailed distributions (e.g., Cauchy), only the median is consistent.

**Proof outline:** Let $\tilde\mu$ be the population median. For the event $\{\text{median}(X_1, \ldots, X_n) \ge \tilde\mu + \epsilon\}$ to occur, at least $(n+1)/2$ of the $X_i$ must exceed $\tilde\mu + \epsilon$. Under regularity, $P(X_i > \tilde\mu + \epsilon) = 1/2 - \epsilon'$. By Chebyshev on the Binomial($n$, $1/2 - \epsilon'$), this probability $\to 0$.

### 5.4 Other Consistent Estimators

- **Sample variance and covariance:** Consistent for population variance/covariance under bounded fourth moment.
- **Sample moments of order $i$:** Consistent under finite $(2i)$-th moment.
- **Empirical cdf:** $E[\hat F_n(x)] = F(x)$ (unbiased); $\text{Var}[\hat F_n(x)] = F(x)(1-F(x))/n \to 0$ (mean-square consistent).

### 5.5 MLE Consistency (Theorem 6.5.2)

Under regularity conditions, the MLE $\hat\theta_n$ is consistent: $\hat\theta_n \xrightarrow{a.s.} \theta$ as $n \to \infty$.

### 5.6 Convergence of Principal Components

If $\Sigma_n$ is the sample covariance matrix and $\Sigma$ is the population covariance matrix, then (under i.i.d. assumptions) the eigenvalues and eigenvectors of $\Sigma_n$ converge to those of $\Sigma$. This justifies PCA as a consistent estimator of the population principal directions.

---

## 6. Confidence Intervals (Frequentist)

### 6.1 Definition

A $1 - \alpha$ confidence interval $I$ for a deterministic $\gamma \in \mathbb{R}$ satisfies
$$P(\gamma \in I) \ge 1 - \alpha, \quad 0 < \alpha < 1.$$

### 6.2 Chebyshev-Based Interval (Conservative)

For an iid sequence with $\text{Var}(X_i) \le b^2$, the interval
$$I_n = \bigl[\bar X_n - b\sqrt{\alpha/n},\; \bar X_n + b\sqrt{\alpha/n}\bigr]$$
is an exact $1 - \alpha$ confidence interval for $\mu$.

**Disadvantage:** Very conservative; intervals are wide.

### 6.3 CLT-Based Approximate Interval

When $n$ is large and $E[X_i^4] < \infty$, the Studentized statistic
$$\sqrt{n}\cdot \frac{\bar X_n - \mu}{S_n}, \quad S_n = \sqrt{\tfrac{1}{n}\sum(X_i - \bar X_n)^2},$$
converges in distribution to $N(0, 1)$. Therefore,
$$I_n = \bar X_n \pm S_n \cdot Q^{-1}(\alpha/2) / \sqrt{n}$$
is an approximate $1 - \alpha$ confidence interval, where $Q(x) = P(N(0,1) > x)$ and $Q^{-1}$ is its inverse.

**Interpretation:** $P(\mu \in I_n) \approx 1 - \alpha$, with the randomness in $I_n$ (not in $\mu$). Repeated sampling interpretation: about $(1-\alpha) \cdot 100\%$ of such intervals will contain $\mu$.

### 6.4 Width Behavior

Width $\propto 1/\sqrt{n}$; quadrupling $n$ halves the width. The Chebyshev interval has width $\propto 1/\sqrt{n}$ as well but with a much larger constant.

---

## 7. Comparison Table: Frequentist vs. Bayesian

| Aspect | Frequentist | Bayesian |
|---|---|---|
| Parameter $\theta$ | Fixed, unknown | Random with prior $\pi(\theta)$ |
| Data $X$ | Random; parameter conditional | Random; joint with $\theta$ |
| Inference target | Sampling distribution of estimator | Posterior $p(\theta \mid x)$ |
| Interval | Confidence interval: $P(\theta \in I) \ge 1 - \alpha$ | Credible interval: $P(\theta \in C \mid x) = 1 - \alpha$ |
| Point estimator | $\hat\theta = h(X)$, e.g., MLE | Posterior mean / mode (MAP) |
| Hypothesis test | P-value; reject $H_0$ if P-value $< \alpha$ | Posterior probability; Bayes factor |
| Optimality | Restricted (e.g., unbiased, MSE) | Direct (posterior mean = MMSE) |
| Model assumptions | Sampling model | Sampling model + prior |
| Use of prior info | Often not used | Integral part |

---

## 8. Practical Guidelines and Pitfalls

### 8.1 When to Use Each Method

| Situation | Recommended method |
|---|---|
| Valid model, large $n$ | MLE with normal approximation |
| Valid model, small $n$, specific distribution | Exact procedures (e.g., $t$-test) |
| Unknown or non-normal distribution | Distribution-free (sign test, bootstrap) |
| Heavy tails, outliers | Trimmed mean, sample median, sign test |
| Strong prior information available | Bayesian with informative prior |
| Subjective element unavoidable | Bayesian with non-informative prior |
| Need for prediction intervals | Bayesian posterior predictive |
| Complex likelihood, no closed form | MCMC / Gibbs sampling |
| Hierarchical structure | Hierarchical Bayes |
| Need for fast, automatic prior | Jeffreys' prior / empirical Bayes |

### 8.2 Common Pitfalls

1. **Using the MLE's Fisher info for testing:** Use $I(\theta_0)$ not $I(\hat\theta_n)$ when testing $H_0: \theta = \theta_0$.
2. **Posterior probability of a point null with continuous prior:** Always 0. Use mixture prior and Bayes factor instead.
3. **Bayesian P-value depends on parameterization:** Use posterior probability or Bayes factor instead.
4. **Delta method fails at boundary** (e.g., $\mu = 0$ for $1/\mu$). Reparameterize.
5. **Variance-stabilizing transformation** (Box–Cox idea): choose $g$ so that $\text{Var}(g(X))$ is approximately constant.
   - Poisson: $g(x) = \sqrt{x}$ stabilizes.
   - Bernoulli: $g(x) = \arcsin(\sqrt{x})$.
   - Distribution with $\text{Var} \propto \mu^2$: $g(x) = \ln x$.
6. **Bootstrap assumes approximately unbiased estimator and approximately normal sampling distribution;** these can fail.
7. **Prior predictive maximization for empirical Bayes violates the principle of conditioning on data;** still often works.
8. **Improper priors must be checked for posterior propriety.**
9. **Trimmed mean / sample median break the normal bootstrap distribution assumption** for the standard bootstrap $t$ or percentile intervals.
10. **Gibbs sampling requires convergence diagnostics** (e.g., trace plots, batch means with multiple batch sizes).

### 8.3 Method of Moments — When to Use

- **Pros:** Simple, no optimization, distribution-free in validity, no likelihood specification.
- **Cons:** Less efficient than MLE under correct specification; doesn't use full information.
- **Required moment existence:** To estimate $\mu_k$ you need the $(2k)$-th moment finite.

### 8.4 Bootstrap — When to Use

- Distribution of the statistic is unknown or intractable.
- Want a standard error for a complex estimator.
- Want to validate a normal approximation.
- **Required:** $n$ large enough that $\hat F_n$ approximates $F$; the estimator's first two moments exist.

### 8.5 Sign Test — When to Use

- Continuous distribution, unknown shape.
- Suspected non-normality (heavy tails, outliers).
- Symmetric distribution; testing the median.
- **P-value computation:** Use Binomial tables or software; for large $n$, normal approximation with continuity correction.

---

## 9. Quick-Reference Formula Sheet

### 9.1 Method of Moments
$$m_i = \frac{1}{n}\sum_{j=1}^n X_j^i, \quad s_i^2 = \frac{1}{n-1}\sum_{j=1}^n (X_j^i - m_i)^2.$$
CI: $m_i \pm z_{1-\alpha/2} s_i/\sqrt{n}$.

### 9.2 Bootstrap
$$\hat\theta^{*(b)} = h(\text{resample}_b), \quad s^{*2}_b = \frac{1}{m-1}\sum_b (\hat\theta^{*(b)} - \bar\theta^*)^2.$$

### 9.3 Sign Test
$$S = \sum \mathbf{1}\{X_i \le x_0\} \sim \text{Bin}(n, p).$$

### 9.4 MLE Asymptotics
$$\sqrt{nI(\hat\theta)}(\hat\theta - \theta) \xrightarrow{D} N(0,1).$$
CI: $\hat\theta \pm z_{1-\alpha/2}/\sqrt{nI(\hat\theta)}$.

### 9.5 Bayes
$$p(\theta \mid x) \propto p(x \mid \theta)\,\pi(\theta).$$
MMSE: $\hat\theta = E[\theta \mid x]$.
MAP: $\hat\theta = \arg\max_\theta p(\theta \mid x)$.

### 9.6 Jeffreys' Prior
$$\pi_J(\theta) \propto \sqrt{I(\theta)}.$$

### 9.7 Bayes Factor
$$B = \frac{m_0(x)}{m_1(x)} = \frac{\text{posterior odds}}{\text{prior odds}}.$$

### 9.8 Confidence Interval (Normal Approximation)
$$I_n = \bar X_n \pm \frac{S_n}{\sqrt{n}}\, Q^{-1}(\alpha/2).$$

### 9.9 Posterior Predictive
$$q(t \mid x) = \int q(t \mid x, \theta)\, p(\theta \mid x)\, d\theta.$$

### 9.10 Mean-Squared Error
$$\text{MSE}(\hat\theta) = E[(\hat\theta - \theta)^2] = \text{Var}(\hat\theta) + \text{Bias}(\hat\theta)^2.$$
