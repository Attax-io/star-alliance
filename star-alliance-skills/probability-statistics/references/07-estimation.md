---
type: Document
timestamp: 2026-07-02T12:28:13Z
---

# Statistical Inference: Estimation, Testing, and Optimal Theory

Statistical inference is the discipline of drawing conclusions about unknown characteristics of a probability distribution from observed data. Given a statistical model $\mathcal{P} = \{P_\theta : \theta \in \Theta\}$ (the set of candidate distributions indexed by parameter $\theta$), three principal types of inference are studied: (i) **point estimation** — a single value $T(s)$ proposed for an unknown characteristic $\theta$; (ii) **interval (region) estimation** — a set $C(s)$ that should contain $\theta$ with high probability; and (iii) **hypothesis assessment** — quantifying how surprising the data are when a hypothesized value $\theta_0$ is true. The unifying mathematical tools are the likelihood function, the sampling distribution, and the score function; the unifying optimality tools are mean-squared error minimization, bias control, and likelihood ratios.

## 1. The Statistical Model and Data

### 1.1 Statistical Model
A **statistical model** is a family of probability measures $\mathcal{P} = \{P_\theta : \theta \in \Theta\}$, where $\theta$ is the **parameter** and $\Theta$ the **parameter space**. The statistician asserts the true measure $P$ lies in $\mathcal{P}$ but does not know which. For parametric models indexed by a real parameter, densities (or probability functions) are written $f(x;\theta)$, and $f(s;\theta) = \prod_{i=1}^n f(x_i; \theta)$ is the joint density of an i.i.d. sample.

### 1.2 I.I.D. Sample and Sufficient Statistics
A **random sample** of size $n$ is a sequence $X_1, \dots, X_n$ of independent, identically distributed random variables with common distribution in the model. A statistic $T: \mathcal{S} \to \mathbb{R}$ is **sufficient** for the model if $T(s_1) = T(s_2)$ implies $L(s_1) = c(s_1,s_2) L(s_2)$ for some positive constant $c$ (likelihood functions are equivalent up to positive multiples).

**Factorization Theorem.** If the joint density factors as $f(s;\theta) = h(s)\, g(T(s);\theta)$ with $g, h \geq 0$, then $T$ is sufficient.

A sufficient statistic is **minimal sufficient** if its value can be recovered from the likelihood function (the likelihood is maximized at the observed value of $T$).

### 1.3 Common Sufficient Statistics
| Model | Density / PMF | Sufficient statistic |
|---|---|---|
| Bernoulli($\theta$) | $\theta^x (1-\theta)^{1-x}$ | $\bar{x}$ (or $\sum x_i$) |
| Binomial($n,\theta$) | $\binom{n}{x}\theta^x(1-\theta)^{n-x}$ | $x$ |
| Poisson($\theta$) | $e^{-\theta}\theta^x/x!$ | $\bar{x}$ |
| Exponential($\beta$) | $\beta^{-1}e^{-x/\beta}$ | $\bar{x}$ |
| $\mathcal{N}(\mu, \sigma_0^2)$, $\sigma_0^2$ known | normal | $\bar{x}$ |
| $\mathcal{N}(\mu, \sigma^2)$, both unknown | normal | $(\bar{x}, s^2)$ |
| Multinomial | $\prod p_i^{x_i}$ | $(x_1, \dots, x_k)$ |
| Uniform[0,$\theta$] | $\theta^{-1}\mathbf{1}\{0\le x\le\theta\}$ | $x_{(n)}$ (max) |

## 2. Point Estimation and the MLE

### 2.1 The Likelihood Function
The **likelihood function** is $L(\theta; s) = f(s; \theta)$, treated as a function of $\theta$ for fixed data $s$. The data support $\theta_1$ over $\theta_2$ whenever $L(\theta_1; s) > L(\theta_2; s)$. Equivalent likelihoods differ by a positive multiplicative constant.

**Likelihood Principle.** If two model/data combinations yield proportional likelihood functions, the inferences about $\theta$ must be the same.

A **likelihood region** at level $c$ is $C(s) = \{\theta : L(\theta; s) \geq c\}$.

### 2.2 Maximum Likelihood Estimator (MLE)
The MLE $\hat{\theta}(s)$ is any $\theta$ that maximizes $L(\theta; s)$. Equivalently, for a sample, $\hat{\theta} = \arg\max_\theta \prod_{i=1}^n f(x_i;\theta)$.

**Log-likelihood:** $\ell(\theta; s) = \log L(\theta; s) = \sum_{i=1}^n \log f(x_i; \theta)$.

**Score function:** $S(\theta; s) = \frac{\partial \ell}{\partial \theta}$. The MLE satisfies the **score equation** $S(\hat{\theta}; s) = 0$.

The MLE is the unique local maximum if the second derivative $\partial^2 \ell / \partial \theta^2 < 0$ at $\hat{\theta}$.

**Invariance (Reparameterization).** If $\hat{\theta}$ is the MLE and $\eta = g(\theta)$ is a one-to-one function, then $g(\hat{\theta})$ is the MLE of $\eta$.

### 2.3 MLEs for Common Models
| Model | MLE |
|---|---|
| Bernoulli($\theta$), sample of size $n$ | $\hat{\theta} = \bar{x}$ |
| Poisson($\theta$) | $\hat{\theta} = \bar{x}$ |
| Exponential($\beta$) | $\hat{\beta} = \bar{x}$ |
| $\mathcal{N}(\mu, \sigma_0^2)$, $\sigma_0^2$ known | $\hat{\mu} = \bar{x}$ |
| $\mathcal{N}(\mu, \sigma^2)$ | $\hat{\mu} = \bar{x},\; \hat{\sigma}^2 = \frac{1}{n}\sum(x_i-\bar{x})^2$ |
| Uniform[0,$\theta$] | $\hat{\theta} = x_{(n)} = \max_i x_i$ |
| Multinomial $(p_1, \dots, p_k)$ | $\hat{p}_i = x_i/n$ |
| Gamma($\alpha, \beta$), $\alpha$ known | $\hat{\beta} = \bar{x}/\alpha$ |

The MLE for $\sigma^2$ in the normal model divides by $n$ (not $n-1$); this is **biased** as an estimator of $\sigma^2$.

### 2.4 Mean-Squared Error, Bias, and Consistency
For an estimator $T(s)$ of $\theta$, the **mean-squared error (MSE)** is
$$
\operatorname{MSE}_\theta(T) = E_\theta\!\left[(T-\theta)^2\right] = \operatorname{Var}_\theta(T) + \big(\operatorname{Bias}_\theta(T)\big)^2,
$$
where $\operatorname{Bias}_\theta(T) = E_\theta[T] - \theta$. $T$ is **unbiased** if bias is zero for all $\theta$. The **standard error** of $T$ is $\sqrt{\operatorname{Var}_\theta(T)}$; when estimated, $\widehat{\operatorname{SE}}(T) = \sqrt{\widehat{\operatorname{Var}}(T)}$.

A sequence $T_1, T_2, \dots$ is **consistent** for $\theta$ if $T_n \xrightarrow{P} \theta$ for every $\theta \in \Theta$. The SLLN ensures the sample mean is consistent for the population mean under finite first moment. MLEs are consistent under regularity conditions (Theorem 6.5.2).

## 3. Interval Estimation (Confidence Intervals)

A random interval $C(s) = (L(s), U(s))$ is a $(1-\alpha)$ **confidence interval** for $\theta$ if
$$
P_\theta(\theta \in C(S)) \geq 1 - \alpha \quad \text{for all } \theta \in \Theta.
$$
After the data are observed, the fixed interval either contains $\theta$ or does not; the $1-\alpha$ is a property of the procedure, not of the realized interval.

### 3.1 z-Confidence Interval (Normal, $\sigma$ known)
For $X_i \overset{iid}{\sim} \mathcal{N}(\mu, \sigma^2)$, the pivotal quantity $Z = \frac{\sqrt{n}(\bar{X} - \mu)}{\sigma} \sim \mathcal{N}(0,1)$, giving
$$
\boxed{\;\bar{x} - z_{1-\alpha/2}\frac{\sigma}{\sqrt{n}} < \mu < \bar{x} + z_{1-\alpha/2}\frac{\sigma}{\sqrt{n}}\;}
$$
For large $n$ from any distribution with finite $\sigma^2$, the CLT justifies the approximate interval
$$
\bar{x} \pm z_{1-\alpha/2} \frac{s}{\sqrt{n}}.
$$

### 3.2 t-Confidence Interval (Normal, $\sigma$ unknown)
By Theorem 4.6.6, $T = \frac{\sqrt{n}(\bar{X}-\mu)}{S} \sim t_{n-1}$. Therefore,
$$
\boxed{\;\bar{x} - t_{1-\alpha/2,\,n-1}\frac{s}{\sqrt{n}} < \mu < \bar{x} + t_{1-\alpha/2,\,n-1}\frac{s}{\sqrt{n}}\;}
$$
is an exact $(1-\alpha)$ confidence interval for $\mu$.

### 3.3 Confidence Interval for a Proportion (Bernoulli)
Using the CLT approximation $\sqrt{n}(\bar{X} - \theta)/\sqrt{\bar{X}(1-\bar{X})} \xrightarrow{d} \mathcal{N}(0,1)$:
$$
\bar{x} \pm z_{1-\alpha/2}\sqrt{\frac{\bar{x}(1-\bar{x})}{n}}.
$$
The approximation requires $n$ large and $\theta$ not too close to 0 or 1. Always verify by simulation for the specific $\theta$ range of interest.

### 3.4 Confidence Interval for $\sigma^2$ (Normal)
For $X_i \overset{iid}{\sim} \mathcal{N}(\mu, \sigma^2)$, $\frac{(n-1)S^2}{\sigma^2} \sim \chi^2_{n-1}$. An exact $(1-\alpha)$ CI for $\sigma^2$ is
$$
\frac{(n-1)s^2}{\chi^2_{1-\alpha/2,\,n-1}} < \sigma^2 < \frac{(n-1)s^2}{\chi^2_{\alpha/2,\,n-1}}.
$$

### 3.5 Sample-Size Determination
For margin of error $E$ at level $1-\alpha$ with known $\sigma$:
$$
n = \left(\frac{z_{1-\alpha/2}\,\sigma}{E}\right)^2.
$$
For proportions, use $\sigma \leq 1/2$:
$$
n = \left(\frac{z_{1-\alpha/2}}{2E}\right)^2.
$$

## 4. Hypothesis Testing

### 4.1 Framework
**Null hypothesis** $H_0: \theta = \theta_0$ is the value to be tested; **alternative hypothesis** $H_1$ (or $H_A$) is the claim to be established. The test divides $\mathcal{S}$ into a rejection region $R$ and acceptance region $R^c$.

| | $H_0$ true | $H_0$ false |
|---|---|---|
| Reject $H_0$ | Type I error (prob $\alpha$) | Correct decision |
| Accept $H_0$ | Correct decision | Type II error (prob $\beta$) |

**Significance level** $\alpha$ = maximum probability of Type I error. The **power function** is $\gamma(\theta) = P_\theta(\text{reject } H_0)$.

### 4.2 z-Tests (Normal, $\sigma$ known)
Test statistic: $Z = \frac{\bar{X} - \theta_0}{\sigma/\sqrt{n}}$, with $Z \sim \mathcal{N}(0,1)$ under $H_0$.

| Alternative | Reject $H_0$ if | P-value (two-sided) |
|---|---|---|
| $H_1: \theta < \theta_0$ | $Z < -z_{1-\alpha}$ | $2(1 - \Phi(|z|))$ |
| $H_1: \theta > \theta_0$ | $Z > z_{1-\alpha}$ | $1 - \Phi(z)$ (one-sided) |
| $H_1: \theta \neq \theta_0$ | $|Z| > z_{1-\alpha/2}$ | $2(1 - \Phi(|z|))$ |

### 4.3 t-Tests (Normal, $\sigma$ unknown)
Test statistic: $t = \frac{\bar{X} - \theta_0}{S/\sqrt{n}}$, with $t \sim t_{n-1}$ under $H_0$.

| Alternative | Reject $H_0$ if |
|---|---|
| $H_1: \theta < \theta_0$ | $t < -t_{1-\alpha, n-1}$ |
| $H_1: \theta > \theta_0$ | $t > t_{1-\alpha, n-1}$ |
| $H_1: \theta \neq \theta_0$ | $|t| > t_{1-\alpha/2, n-1}$ |

### 4.4 Test for a Proportion
For large $n$, use $Z = \frac{\bar{X} - \theta_0}{\sqrt{\theta_0(1-\theta_0)/n}}$, asymptotically $\mathcal{N}(0,1)$ under $H_0$.

### 4.5 Test for $\sigma^2$ (Normal)
Test statistic: $\chi^2 = \frac{(n-1)S^2}{\sigma_0^2} \sim \chi^2_{n-1}$ under $H_0$.
- $H_1: \sigma^2 < \sigma_0^2$: reject if $\chi^2 < \chi^2_{\alpha, n-1}$.
- $H_1: \sigma^2 > \sigma_0^2$: reject if $\chi^2 > \chi^2_{1-\alpha, n-1}$.
- $H_1: \sigma^2 \neq \sigma_0^2$: two-sided form.

### 4.6 P-Value
The **P-value** is the probability, computed under $H_0$, of obtaining a test statistic as extreme or more extreme than the observed value. Small P-values are evidence against $H_0$. A P-value is **not** the probability that $H_0$ is true.

### 4.7 Statistical vs. Practical Significance
With large $n$, even practically negligible departures from $\theta_0$ yield tiny P-values. Always report the magnitude of the estimated effect alongside the P-value.

### 4.8 Equivalence of Confidence Intervals and Two-Sided Tests
$H_0: \theta = \theta_0$ is rejected at level $\alpha$ (two-sided) $\iff$ $\theta_0$ lies outside the $(1-\alpha)$ confidence interval for $\theta$.

## 5. Power Analysis and Sample Size

### 5.1 Power for the z-Test
For $H_0: \theta = \theta_0$ vs. $H_1: \theta = \theta_1$ (one-sided), the power is
$$
\gamma(\theta_1) = P\!\left(Z > z_{1-\alpha} + \frac{\sqrt{n}(\theta_0 - \theta_1)}{\sigma}\right).
$$
For two-sided:
$$
\gamma(\theta_1) = P\!\left(Z < -z_{1-\alpha/2} + \frac{\sqrt{n}(\theta_0-\theta_1)}{\sigma}\right) + P\!\left(Z > z_{1-\alpha/2} + \frac{\sqrt{n}(\theta_0-\theta_1)}{\sigma}\right).
$$

Properties of $\gamma(\theta)$:
- $\gamma(\theta_0) = \alpha$ (Type I error at the null value)
- $\gamma$ is nondecreasing in $n$ (for fixed $\theta_1$)
- $\gamma$ is nondecreasing in $|\theta_1 - \theta_0|$
- $\gamma \to 1$ as $|\theta_1 - \theta_0| \to \infty$
- $\gamma$ is nondecreasing in $\sigma$ for power loss direction; power **decreases** as $\sigma$ increases.

### 5.2 Sample Size for Specified Power (One-Sided z-test)
For $\gamma(\theta_1) = 1 - \beta$:
$$
n = \left[\frac{\sigma(z_{1-\alpha} + z_{1-\beta})}{|\theta_0 - \theta_1|}\right]^2.
$$

### 5.3 Operating Characteristic (OC) Curve
The OC curve plots $L(\mu) = 1 - \gamma(\mu)$ versus $\mu$. An ideal OC curve equals 1 for $\mu \leq \mu_0$ and 0 for $\mu > \mu_0$; actual OC curves approximate this as $n$ increases.

## 6. Descriptive Statistics and Data Summary

### 6.1 Sample Quantiles
Order statistics $x_{(1)} \leq x_{(2)} \leq \cdots \leq x_{(n)}$. The sample $p$-th quantile $x_{(p)}^*$ satisfies $\frac{i-1}{n} < p \leq \frac{i}{n}$ for some $i$, with linear interpolation
$$
x_{(p)}^* = x_{(i)} + (pn - (i-1))(x_{(i+1)} - x_{(i)}).
$$
The sample median is $x_{0.5}^*$; sample IQR is $x_{0.75}^* - x_{0.25}^*$.

### 6.2 Boxplot Components
- Box: Q1 to Q3 with median line
- Whiskers: extend to largest/smallest value within $Q3 + 1.5\cdot \text{IQR}$ and $Q1 - 1.5\cdot \text{IQR}$ respectively
- Outliers: points beyond the whisker limits

### 6.3 Histogram (Density Form)
For bins $(h_j, h_{j+1}]$,
$$
\hat{f}(x) = \frac{1}{n \cdot (h_{j+1}-h_j)} \cdot \#\{x_i \in (h_j, h_{j+1}]\} \quad \text{for } x \in (h_j, h_{j+1}].
$$
$\int_a^b \hat{f}(x)\,dx \approx F(b) - F(a)$.

### 6.4 Sample Mean and Variance
$$
\bar{x} = \frac{1}{n}\sum_{i=1}^n x_i, \quad s^2 = \frac{1}{n-1}\sum_{i=1}^n (x_i - \bar{x})^2.
$$
$\bar{x}$ is unbiased for $\mu$; $s^2$ is unbiased for $\sigma^2$. By Theorem 4.6.6, in normal samples $\bar{X} \perp\!\!\!\perp S^2$ and $\frac{(n-1)S^2}{\sigma^2} \sim \chi^2_{n-1}$.

## 7. Bayesian Inference

### 7.1 Posterior Distribution
Given prior $\pi(\theta)$ and likelihood $L(\theta; s)$, the posterior is
$$
\pi(\theta \mid s) = \frac{\pi(\theta) L(\theta; s)}{m(s)}, \quad m(s) = \int \pi(\theta) L(\theta; s)\,d\theta.
$$
For a parameter of interest $\eta = g(\theta)$ with nuisance $\xi$, integrate out: $\pi(\eta \mid s) = \int \pi(\eta, \xi \mid s)\,d\xi$.

### 7.2 Bayes Estimator
Under squared-error loss, the Bayes estimator is the posterior mean $\hat{\theta}_B = E[\theta \mid s]$.

### 7.3 Conjugate Priors
| Likelihood | Conjugate prior | Posterior form |
|---|---|---|
| Bernoulli($\theta$) | Beta($a,b$) | Beta($a + \sum x_i$, $b + n - \sum x_i$) |
| Poisson($\theta$) | Gamma($\alpha, \beta$) | Gamma($\alpha + \sum x_i$, $\beta/(1 + n\beta)$) |
| Exponential($\beta$) | Gamma($\alpha, \beta$) | Gamma($\alpha + n$, $\beta + \sum x_i$) |
| $\mathcal{N}(\mu, \sigma^2)$, $\sigma$ known | $\mathcal{N}(\mu_0, \tau^2)$ | $\mathcal{N}\!\left(\frac{\tau^{-2}\mu_0 + n\sigma^{-2}\bar{x}}{\tau^{-2} + n\sigma^{-2}}, \frac{1}{\tau^{-2}+n\sigma^{-2}}\right)$ |
| $\mathcal{N}(\mu, \sigma^2)$, both unknown ($\sigma^2 \sim$Inv-$\chi^2$) | Normal-inv-$\chi^2$ | Normal-inv-$\chi^2$ |

For Bernoulli with Beta prior, the prior mean is $a/(a+b)$ and the prior sample size is $a+b$. Posterior mean:
$$
\hat{\theta}_B = \frac{a + \sum x_i}{a + b + n} = \frac{a+b}{a+b+n}\cdot\frac{a}{a+b} + \frac{n}{a+b+n}\cdot\bar{x}.
$$

### 7.4 Credible Intervals
A $(1-\alpha)$ **credible region** is a set $C(s)$ with $P(\theta \in C(s) \mid s) \geq 1-\alpha$. The highest posterior density (HPD) region is shortest.

## 8. Optimal Estimation Theory

### 8.1 Mean-Squared Error Decomposition (Theorem)
For any estimator $T$ with $E[T^2] < \infty$,
$$
\operatorname{MSE}_\theta(T) = E_\theta[(T - \theta)^2] = \operatorname{Var}_\theta(T) + (E_\theta[T] - \theta)^2.
$$
A natural constraint is **unbiasedness** ($E_\theta[T] = \theta$ for all $\theta$); then MSE = Variance.

### 8.2 Uniformly Minimum Variance Unbiased (UMVU) Estimator
A **UMVU estimator** is an unbiased estimator with the smallest variance among all unbiased estimators, for every $\theta$.

### 8.3 Rao–Blackwell Theorem
**Theorem.** If $T(s)$ is an estimator with finite second moment and $U(s)$ is sufficient, then
$$
T^*(s) := E[T \mid U = U(s)]
$$
depends on data only through $U$, and $\operatorname{MSE}_\theta(T^*) \leq \operatorname{MSE}_\theta(T)$ for all $\theta$. Moreover, if $T$ is unbiased, so is $T^*$, and $\operatorname{Var}_\theta(T^*) \leq \operatorname{Var}_\theta(T)$.

This process is called **Rao–Blackwellization**.

### 8.4 Characterization of Sufficiency
**Theorem.** $U$ is sufficient $\iff$ the conditional distribution of the data $S$ given $U = u$ is the same for every $\theta$ (i.e., contains no information about $\theta$).

### 8.5 Completeness
A statistic $U$ is **complete** if $E_\theta[h(U)] = 0$ for all $\theta$ implies $P_\theta(h(U) = 0) = 1$ for all $\theta$.

### 8.6 Lehmann–Scheffé Theorem
**Theorem.** If $U$ is a complete sufficient statistic and $T^*(s) = h(U(s))$ is an unbiased estimator of $\theta$ with finite second moment, then $T^*$ is the **unique** UMVU estimator of $\theta$.

**Recipe for UMVU:** Find any unbiased estimator $T$, Rao–Blackwellize using a complete sufficient statistic $U$, and apply Lehmann–Scheffé.

### 8.7 Complete Sufficient Statistics for Common Models
| Model | Complete sufficient statistic |
|---|---|
| Bernoulli($\theta$) | $\sum X_i$ |
| Poisson($\theta$) | $\sum X_i$ |
| Exponential($\beta$) | $\sum X_i$ |
| $\mathcal{N}(\mu, \sigma^2)$, both unknown | $(\bar{X}, S^2)$ |
| Uniform[0,$\theta$] | $X_{(n)}$ |
| All continuous distributions on $\mathbb{R}$ | order statistics (with finite moment constraints) |

### 8.8 Cramér–Rao (Information) Inequality
Let $I(\theta) = \operatorname{Var}_\theta(S(\theta))$ be the Fisher information, where $S(\theta) = \partial \ell / \partial \theta$.

**Theorem (Cramér–Rao).** Under regularity conditions, for any unbiased estimator $T$ of $\theta$,
$$
\operatorname{Var}_\theta(T) \geq \frac{1}{I(\theta)},
$$
with equality iff $T(s) - \theta = c(\theta) S(\theta; s)$ for some function $c(\theta)$.

**Multiparameter version:** $\operatorname{Cov}_\theta(T) \succeq I(\theta)^{-1}$.

If an estimator attains the bound, it is UMVU. Otherwise, the bound is a benchmark.

### 8.9 Asymptotic Optimality of the MLE
Under regularity (Theorem 6.5.2), the MLE $\hat{\theta}_n$ is consistent and asymptotically normal:
$$
\sqrt{n}(\hat{\theta}_n - \theta) \xrightarrow{d} \mathcal{N}\!\left(0, \frac{1}{I(\theta)}\right).
$$
Thus the MLE attains the Cramér–Rao bound asymptotically.

### 8.10 Examples of UMVU via Rao–Blackwell + Lehmann–Scheffé
| Model | Target $\theta$ | UMVU estimator |
|---|---|---|
| Bernoulli($\theta$) | $\theta$ | $\bar{X}$ |
| $\mathcal{N}(\mu, \sigma^2)$ | $\mu$ | $\bar{X}$ |
| $\mathcal{N}(\mu, \sigma^2)$ | $\sigma^2$ | $S^2$ |
| $\mathcal{N}(\mu, \sigma^2)$ | $\sigma$ | $c_n S$ (where $c_n = \sqrt{2}\Gamma(n/2)/(\sqrt{n-1}\Gamma((n-1)/2))$) |
| Uniform[0,$\theta$] | $\theta$ | $\frac{n+1}{n} X_{(n)}$ |

## 9. Optimal Hypothesis Testing

### 9.1 Test Functions and Rejection Regions
A **rejection region** $R \subseteq \mathcal{S}$ specifies when to reject $H_0$. A **test function** $\phi: \mathcal{S} \to [0,1]$ generalizes this: $\phi(s) = P(\text{reject } H_0 \mid s)$, the conditional probability given the data. Rejection regions are test functions with $\phi \in \{0,1\}$.

### 9.2 Size and Power
The **size** of a test $\phi$ for $H_0: \theta \in \Theta_0$ is $\sup_{\theta \in \Theta_0} E_\theta[\phi]$. The **power function** is $\gamma(\theta) = E_\theta[\phi]$. A size-$\alpha$ test has $\sup_{\theta \in \Theta_0} \gamma(\theta) \leq \alpha$.

### 9.3 Uniformly Most Powerful (UMP) Test
A test $\phi^*$ is **UMP of size $\alpha$** for $H_0: \theta \in \Theta_0$ vs $H_1: \theta \in \Theta_1$ if:
1. $\sup_{\theta \in \Theta_0} E_\theta[\phi^*] \leq \alpha$, and
2. $E_\theta[\phi^*] \geq E_\theta[\phi]$ for all $\theta \in \Theta_1$ and all other size-$\alpha$ tests $\phi$.

### 9.4 Neyman–Pearson Lemma
**Theorem (Neyman–Pearson).** For simple $H_0: \theta = \theta_0$ vs simple $H_1: \theta = \theta_1$ with densities $f_0, f_1$ and level $\alpha$, the most powerful test of size $\alpha$ is the **likelihood ratio test**:
$$
\phi^*(s) = \begin{cases} 1 & \text{if } f_1(s) > k f_0(s) \\ \gamma & \text{if } f_1(s) = k f_0(s) \\ 0 & \text{if } f_1(s) < k f_0(s) \end{cases}
$$
where $k \geq 0$ and $\gamma \in [0,1]$ are chosen so that $E_{\theta_0}[\phi^*] = \alpha$.

The test rejects $H_0$ when the likelihood ratio $\Lambda(s) = f_1(s)/f_0(s)$ is large.

### 9.5 Karlin–Rubin Theorem
**Theorem.** For monotone likelihood ratio (MLR) families, the UMP test of $H_0: \theta \leq \theta_0$ vs $H_1: \theta > \theta_0$ is one-sided in the sufficient statistic, with critical value chosen to give size $\alpha$. The $\mathcal{N}(\mu, \sigma^2)$ family (with $\sigma$ known) has MLR in $\bar{X}$, and the UMP test rejects for large $\bar{X}$.

## 10. Common Sampling Distributions Reference

| Distribution | Density / PMF | Mean | Variance | Notes |
|---|---|---|---|---|
| $\chi^2_n$ | $\frac{1}{2^{n/2}\Gamma(n/2)} x^{n/2-1} e^{-x/2}$ | $n$ | $2n$ | Sum of $n$ squared $\mathcal{N}(0,1)$ |
| $t_n$ | $\frac{\Gamma((n+1)/2)}{\sqrt{n\pi}\Gamma(n/2)}(1 + x^2/n)^{-(n+1)/2}$ | $0$ (n>1) | $n/(n-2)$ (n>2) | Standard normal divided by $\sqrt{\chi^2_n/n}$ |
| $F_{m,n}$ | See standard tables | $\frac{n}{n-2}$ (n>2) | complex | Ratio of scaled $\chi^2$ |
| $\mathcal{N}(0,1)$ | $\frac{1}{\sqrt{2\pi}}e^{-x^2/2}$ | 0 | 1 | |
| $\text{Beta}(a,b)$ | $\frac{1}{B(a,b)}x^{a-1}(1-x)^{b-1}$ | $\frac{a}{a+b}$ | $\frac{ab}{(a+b)^2(a+b+1)}$ | |

## 11. Method of Moments and Distribution-Free Inference

### 11.1 Method of Moments
The $k$-th sample moment $M_k = \frac{1}{n}\sum X_i^k$ estimates the $k$-th population moment $\mu_k = E[X^k]$. By the law of large numbers, $M_k \to \mu_k$ a.s. For smooth functions $g$ of moments, the **delta method** gives asymptotic normality:
$$
\sqrt{n}\,(g(M_1, \dots, M_k) - g(\mu_1, \dots, \mu_k)) \xrightarrow{d} \mathcal{N}(0, \nabla g^\top \Sigma \nabla g),
$$
where $\Sigma$ is the asymptotic covariance of $\sqrt{n}(M_1-\mu_1, \dots, M_k-\mu_k)$.

### 11.2 Bootstrapping
The **empirical CDF** is $\hat{F}_n(x) = \frac{1}{n}\sum_{i=1}^n \mathbf{1}\{X_i \leq x\}$, an unbiased estimator of $F$. Resample with replacement from the data $m$ times, compute the statistic on each, and use the sample standard deviation of the bootstrap statistics as the estimated standard error.

**Bootstrap MSE estimate:** $\widehat{\operatorname{MSE}} = \widehat{\text{Bias}}^2 + \widehat{\text{Var}}_{\text{boot}}$.

## 12. Pivotal Quantities and Common CIs

| Target | Pivotal quantity | CI |
|---|---|---|
| $\mu$ ($\sigma$ known, normal) | $\frac{\bar{X}-\mu}{\sigma/\sqrt{n}} \sim \mathcal{N}(0,1)$ | $\bar{x} \pm z_{1-\alpha/2}\,\sigma/\sqrt{n}$ |
| $\mu$ ($\sigma$ unknown, normal) | $\frac{\bar{X}-\mu}{S/\sqrt{n}} \sim t_{n-1}$ | $\bar{x} \pm t_{1-\alpha/2,n-1}\,s/\sqrt{n}$ |
| $\sigma^2$ (normal) | $\frac{(n-1)S^2}{\sigma^2} \sim \chi^2_{n-1}$ | $\frac{(n-1)s^2}{\chi^2_{1-\alpha/2,n-1}} < \sigma^2 < \frac{(n-1)s^2}{\chi^2_{\alpha/2,n-1}}$ |
| $\sigma_1^2/\sigma_2^2$ (normal) | $F = S_1^2/S_2^2 \sim F_{n_1-1,n_2-1}$ | ratio CI using $F$ quantiles |
| Difference of means | $\frac{(\bar{X}_1-\bar{X}_2)-(\mu_1-\mu_2)}{S_p\sqrt{1/n_1+1/n_2}} \sim t_{n_1+n_2-2}$ | pooled-$t$ CI |
| $\theta$ (Poisson) | $\sum X_i \sim \text{Poisson}(n\theta)$ | exact CI via Poisson quantiles |

## 13. Decision Theory

### 13.1 Framework
A **decision problem** consists of:
- State space $\Theta$ (parameters)
- Action space $\mathcal{A}$ (decisions)
- Loss function $L(\theta, a)$ measuring cost of action $a$ when $\theta$ is true
- Data $S$ with distribution $P_\theta$

A **decision rule** is $\delta: \mathcal{S} \to \mathcal{A}$. The **risk** is $R(\theta, \delta) = E_\theta[L(\theta, \delta(S))]$.

### 13.2 Bayes Rule
With prior $\pi$ on $\Theta$, the **posterior risk** is $E[L(\theta, a) \mid s]$. The **Bayes rule** $\delta^*$ minimizes posterior risk for every $s$:
$$
\delta^*(s) = \arg\min_a E[L(\theta,a) \mid s].
$$
For squared-error loss $L(\theta,a) = (\theta - a)^2$, $\delta^*(s) = E[\theta \mid s]$ (posterior mean). For 0-1 loss, $\delta^*(s) = \arg\max_\theta \pi(\theta \mid s)$ (posterior mode).

### 13.3 Admissibility
A rule $\delta$ is **inadmissible** if there exists $\delta'$ with $R(\theta, \delta') \leq R(\theta, \delta)$ for all $\theta$ and strict inequality for some. Otherwise, $\delta$ is **admissible**.

### 13.4 Minimax Rules
A **minimax rule** minimizes the maximum risk: $\delta^* = \arg\min_\delta \sup_\theta R(\theta, \delta)$. Bayes rules with respect to least-favorable priors are minimax.

## 14. Sampling Theory Summary

| Sample from | Statistic | Distribution |
|---|---|---|
| $\mathcal{N}(\mu, \sigma^2)$ | $\bar{X}$ | $\mathcal{N}(\mu, \sigma^2/n)$ |
| $\mathcal{N}(\mu, \sigma^2)$ | $\frac{\bar{X}-\mu}{S/\sqrt{n}}$ | $t_{n-1}$ |
| $\mathcal{N}(\mu, \sigma^2)$ | $\frac{(n-1)S^2}{\sigma^2}$ | $\chi^2_{n-1}$ |
| Two normal samples | $\frac{(\bar{X}_1-\bar{X}_2)-(\mu_1-\mu_2)}{S_p\sqrt{1/n_1+1/n_2}}$ | $t_{n_1+n_2-2}$ |
| Two normal samples | $S_1^2/S_2^2$ | $F_{n_1-1,n_2-1}$ |
| Bernoulli($\theta$) | $\sum X_i$ | Binomial($n, \theta$) |
| Poisson($\theta$) | $\sum X_i$ | Poisson($n\theta$) |
| Exponential($\beta$) | $\sum X_i$ | Gamma($n, \beta$) |
| Any (CLT) | $\frac{\bar{X}-\mu}{\sigma/\sqrt{n}}$ | $\dot\sim \mathcal{N}(0,1)$ for large $n$ |

## 15. Core Formulas Quick Reference

| Quantity | Formula |
|---|---|
| Likelihood | $L(\theta; s) = \prod_{i=1}^n f(x_i; \theta)$ |
| Score | $S(\theta) = \partial \ell / \partial \theta$ |
| Fisher information | $I(\theta) = E_\theta[S(\theta)^2]$ |
| Bias | $\operatorname{Bias}_\theta(T) = E_\theta[T] - \theta$ |
| Variance | $\operatorname{Var}_\theta(T) = E_\theta[(T - E_\theta[T])^2]$ |
| MSE | $\operatorname{MSE}_\theta(T) = \operatorname{Var}_\theta(T) + \text{Bias}^2$ |
| Cramér–Rao bound | $\operatorname{Var}_\theta(T) \geq 1/I(\theta)$ for unbiased $T$ |
| z-CI half-width | $z_{1-\alpha/2}\,\sigma/\sqrt{n}$ |
| t-CI half-width | $t_{1-\alpha/2,n-1}\,s/\sqrt{n}$ |
| Power (one-sided z) | $\gamma(\theta_1) = \Phi\!\left(\frac{\sqrt{n}(\theta_1-\theta_0)}{\sigma} - z_{1-\alpha}\right)$ |
| Sample size (one-sided) | $n = \left[\frac{\sigma(z_{1-\alpha}+z_{1-\beta})}{|\theta_1-\theta_0|}\right]^2$ |
| Posterior | $\pi(\theta \mid s) \propto \pi(\theta) L(\theta; s)$ |
| Bayes estimator (squared loss) | $E[\theta \mid s]$ |
| Likelihood ratio test | reject if $f_1(s)/f_0(s) > k$ |
