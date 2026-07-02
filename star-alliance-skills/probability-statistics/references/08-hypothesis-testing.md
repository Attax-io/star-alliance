---
type: Document
timestamp: 2026-07-02T12:28:13Z
---

# Optimal Statistical Inference

This reference covers the theory and practice of optimal point estimation, hypothesis testing, confidence interval construction, and decision making, integrating the rigorous measure-theoretic treatment of optimal unbiased estimation and Bayesian decision theory with the applied, computational perspective used in engineering and data-science practice. Topics progress from foundational definitions (bias, MSE, sufficiency, completeness) through UMVUE construction, MLE properties, Neyman–Pearson testing, the Cramér–Rao bound, Bayesian optimal rules, and tests/intervals for means, variances, and proportions under both classical and Bayesian paradigms.

---

## 1. Foundational Concepts: Estimators, Bias, and Risk

### 1.1 Estimator and Estimate

An **estimator** $T = T(X_1, \dots, X_n)$ is a statistic used to approximate a parameter $\theta$; an **estimate** is its numerical value once data are observed. The estimator is a random variable; the estimate is a number.

### 1.2 Bias and Mean Squared Error

For a real-valued parameter $\theta$ estimated by $T$:

$$\mathrm{Bias}_\theta(T) = E_\theta[T] - \theta, \qquad \mathrm{MSE}_\theta(T) = E_\theta[(T-\theta)^2].$$

The classical bias–variance decomposition is

$$\mathrm{MSE}_\theta(T) = \mathrm{Var}_\theta(T) + \big(\mathrm{Bias}_\theta(T)\big)^2.$$

An estimator is **unbiased** for $\theta$ if $E_\theta[T] = \theta$ for every $\theta$ in the parameter space. The sample mean $\bar X$ is unbiased for $\mu$, but the MLE $\hat\sigma^2 = \frac{1}{n}\sum (X_i-\bar X)^2$ is biased for $\sigma^2$; the unbiased version is $S^2 = \frac{n}{n-1}\hat\sigma^2$.

### 1.3 Unbiasedness Minimizes MSE Among Unbiased Estimators

**Theorem (Unbiasedness is MSE-optimal within unbiased class).** Among all unbiased estimators of a parameter, the one with smallest variance minimizes the mean squared error. Hence, when restricting attention to unbiased estimators, only variances matter for comparison.

---

## 2. Sufficiency, Completeness, and the Rao–Blackwell Theorem

### 2.1 Sufficient Statistic

A statistic $T(X_1,\dots,X_n)$ is **sufficient** for $\theta$ if the conditional distribution of the data given $T=t$ does not depend on $\theta$. **Minimal sufficiency** is obtained by maximal data reduction without loss of information.

Common examples:
- $\bar X$ is sufficient for $\mu$ in $N(\mu,\sigma^2)$ with $\sigma^2$ known; $(\bar X, S^2)$ is sufficient for $(\mu,\sigma^2)$.
- $\sum X_i$ is sufficient for $\lambda$ in Poisson$(\lambda)$ and for $\beta$ in Gamma$(\alpha,\beta)$ with $\alpha$ known.
- $X_{(n)} = \max_i X_i$ is sufficient for $\theta$ in Uniform$[0,\theta]$.
- $\sum X_i$ is sufficient for $p$ in Bernoulli$(p)$ with $n$ fixed.
- $\bar X$ is complete sufficient in one-parameter exponential family distributions.

### 2.2 Complete Statistic

A statistic $T$ is **complete** for a model if $E_\theta[g(T)] = 0$ for all $\theta$ implies $P_\theta(g(T)=0) = 1$ for all $\theta$. Completeness depends on the model: a sufficient statistic for one model may not be complete for a submodel or a larger model.

**Examples of complete sufficient statistics:**
- $\bar X$ in $N(\mu,\sigma^2)$ with $\sigma^2$ known.
- $\sum X_i$ in Poisson$(\lambda)$; $\sum X_i$ in Gamma$(\alpha,\beta)$ with $\alpha$ known.
- $\sum X_i$ in Bernoulli$(p)$.
- $X_{(n)}$ in Uniform$[0,\theta]$.
- A 1–1 function of a complete statistic is also complete.

### 2.3 Rao–Blackwell Theorem

Let $T$ be a sufficient statistic and $W$ any unbiased estimator of $\theta$. Then

$$T^* = E_\theta[W \mid T]$$

is (a) a function only of $T$, (b) unbiased for $\theta$, and (c) has variance no larger than $W$ (and strictly smaller unless $W$ is already a function of $T$).

**Intuition.** Since $T$ captures all information about $\theta$, conditioning any estimator on $T$ can only sharpen it.

### 2.4 Lehmann–Scheffé Theorem

If $T$ is a **complete sufficient** statistic and $W$ is any unbiased estimator, then $T^* = E[W|T]$ is the **unique uniformly minimum-variance unbiased estimator (UMVUE)** of $\theta$. Uniqueness is almost-everywhere.

**Worked example: UMVUE for $P(X=0)$ in Poisson$(\lambda)$.** Given $T=\sum X_i \sim \mathrm{Poisson}(n\lambda)$, the indicator $I(X_1=0)$ is unbiased for $P(X=0)$ under the multinomial structure of $(X_1,\dots,X_n)\mid T$. The UMVUE is

$$T^* = P(X_1=0 \mid T) = \left(\frac{n-1}{n}\right)^T.$$

This is non-obvious from its functional form, illustrating that the theory often produces estimators that would not be guessed directly.

---

## 3. Information Inequality and the Cramér–Rao Lower Bound

### 3.1 Cramér–Rao Lower Bound (CRLB)

Assume the data are i.i.d. with density $f(x;\theta)$, the support does not depend on $\theta$, and differentiation under the integral sign is valid. Then for any unbiased estimator $T$ of a differentiable function $\tau(\theta)$,

$$\mathrm{Var}_\theta(T) \;\geq\; \frac{[\tau'(\theta)]^2}{n \cdot I(\theta)},$$

where the **Fisher information** is

$$I(\theta) = E_\theta\!\left[\left(\frac{\partial \log f(X;\theta)}{\partial \theta}\right)^2\right] = -E_\theta\!\left[\frac{\partial^2 \log f(X;\theta)}{\partial \theta^2}\right].$$

An unbiased estimator attaining the CRLB with equality is **efficient**.

### 3.2 Information for Common Families

| Family | Parameter | $I(\theta)$ (per observation) |
|---|---|---|
| $N(\mu,\sigma^2)$, $\sigma^2$ known | $\mu$ | $1/\sigma^2$ |
| $N(\mu,\sigma^2)$, $\mu$ known | $\sigma^2$ | $1/(2\sigma^4)$ |
| Bernoulli$(p)$ | $p$ | $1/[p(1-p)]$ |
| Poisson$(\lambda)$ | $\lambda$ | $1/\lambda$ |
| Exponential$(\beta)$ | $\beta$ | $1/\beta^2$ |
| Gamma$(\alpha,\beta)$, $\alpha$ known | $\beta$ | $\alpha/\beta^2$ |
| Uniform$[0,\theta]$ | $\theta$ | $1/\theta^2$ |

### 3.3 MLE Asymptotic Optimality

Under regularity conditions, the MLE $\hat\theta_n$ is asymptotically unbiased for $\theta$ and its asymptotic variance equals the information lower bound $1/[nI(\theta)]$. Thus, with large samples, $\hat\theta_n$ makes full use of the data's information about $\theta$.

---

## 4. Maximum Likelihood Estimation

### 4.1 Likelihood and Log-Likelihood

The **likelihood function** is the joint density (or mass) viewed as a function of $\theta$ with the data fixed:

$$L(\theta) = \prod_{i=1}^n f(x_i;\theta), \qquad \ell(\theta) = \log L(\theta) = \sum_{i=1}^n \log f(x_i;\theta).$$

The **maximum likelihood estimator (MLE)** is $\hat\theta = \arg\max_\theta L(\theta)$.

### 4.2 Score Equation and Fisher Information

Setting the **score function** to zero:

$$U(\theta) = \frac{\partial \ell(\theta)}{\partial \theta} = \sum_{i=1}^n \frac{\partial \log f(x_i;\theta)}{\partial \theta} = 0.$$

The Fisher information is $I_n(\theta) = \mathrm{Var}_\theta[U(\theta)] = -E_\theta[U'(\theta)]$.

### 4.3 Invariance Property

If $\hat\theta$ is the MLE of $\theta$ and $g$ is a one-to-one continuous function, then $g(\hat\theta)$ is the MLE of $g(\theta)$.

### 4.4 MLE for Standard Distributions

| Distribution | MLE of $\theta$ | Notes |
|---|---|---|
| Bernoulli$(p)$ | $\hat p = \bar X$ | |
| Poisson$(\lambda)$ | $\hat\lambda = \bar X$ | Special case $\sum x_i=0$ gives $\hat\lambda=0$ |
| Exponential$(\beta)$ | $\hat\beta = \bar X$ | |
| Gamma$(\alpha,\beta)$, $\alpha$ known | $\hat\beta = \bar X/\alpha$ | |
| Gamma$(\alpha,\beta)$, $\beta$ known | $\hat\alpha$ via log-equation | |
| $N(\mu,\sigma^2)$, both unknown | $\hat\mu=\bar X$, $\hat\sigma^2 = \frac{1}{n}\sum(X_i-\bar X)^2$ | MLE variance uses $n$, biased |
| Uniform$[0,\theta]$ | $\hat\theta = X_{(n)}$ | Biased low |
| Negative Binomial | $\hat p = r/\bar X$ | where $r$ is the number of successes defining the NB |

For the normal distribution with both parameters unknown, since $\hat\sigma^2$ uses divisor $n$ (not $n-1$), it is biased. The standard sample standard deviation $S = \sqrt{S^2}$ is the typical reported estimator.

### 4.5 MLE for Functions of Parameters (Example)

The probability of 0 or 1 defectives when $X\sim \mathrm{Poisson}(\lambda)$ is $p = e^{-\lambda}+\lambda e^{-\lambda}$. By invariance, $\hat p = e^{-\hat\lambda} + \hat\lambda e^{-\hat\lambda}$, with $\hat\lambda = \bar x$.

---

## 5. Hypothesis Testing: Framework

### 5.1 Null and Alternative Hypotheses

The **null hypothesis** $H_0$ specifies a value (or set of values) for the parameter; the **alternative hypothesis** $H_a$ or $H_1$ is the complement. The alternative may be:
- **Two-sided:** $H_a: \theta \ne \theta_0$
- **One-sided:** $H_a: \theta > \theta_0$ or $H_a: \theta < \theta_0$

A **simple hypothesis** fully specifies the distribution; a **composite hypothesis** leaves some parameters unspecified.

**Convention.** When the goal is to *establish* an assertion, that assertion is the alternative; its negation is the null. This guarantees that control of Type I error protects against false claims.

### 5.2 Type I and Type II Errors

| | Fail to reject $H_0$ | Reject $H_0$ |
|---|---|---|
| $H_0$ true | Correct | **Type I error** ($\alpha$) |
| $H_0$ false | **Type II error** ($\beta$) | Correct (power $= 1-\beta$) |

- **Level of significance** $\alpha$ = $P(\text{Type I error})$.
- **Power** at $\theta$ = $P(\text{reject } H_0 \mid \theta)$ = $1 - \beta$ when $\theta \in H_a$.

A test is **unbiased** if its power at any $\theta \in H_a$ is at least its size at any $\theta_0 \in H_0$. Any UMP size-$\alpha$ test is automatically unbiased.

### 5.3 P-value

The **P-value** is the probability, under $H_0$, of obtaining a value of the test statistic at least as extreme as that observed. Smaller P-values indicate stronger evidence against $H_0$.

For a two-sided test based on statistic $Z$ with observed value $z$:

$$\text{P-value} = 2 P(Z \ge |z|).$$

For one-sided alternatives, only the relevant tail enters.

### 5.4 Five-Step Procedure

1. State $H_0$ and $H_a$.
2. Specify significance level $\alpha$ (and Type II error targets if applicable).
3. Determine rejection region using the sampling distribution of the chosen test statistic.
4. Compute the observed test statistic from data.
5. Reject $H_0$ if the statistic lies in the rejection region; otherwise fail to reject.

### 5.5 Power Function and OC Curve

The **power function** $\gamma(\theta) = P_\theta(\text{reject } H_0)$ completely characterizes a test. The **operating characteristic (OC) curve** plots $1 - \gamma(\theta)$, the probability of *accepting* $H_0$, against $\theta$.

Power depends on:
1. Significance level $\alpha$ (larger $\alpha \Rightarrow$ larger power),
2. Distance between true $\theta$ and $H_0$ (larger $\Rightarrow$ larger power),
3. Population variability $\sigma$ (larger $\sigma \Rightarrow$ smaller power),
4. Sample size $n$ (larger $n \Rightarrow$ larger power).

---

## 6. Tests and Confidence Intervals for One Mean

### 6.1 Sampling Distribution

For i.i.d. observations $X_1, \dots, X_n$ with mean $\mu$ and variance $\sigma^2$:

$$E[\bar X] = \mu, \qquad \mathrm{Var}(\bar X) = \sigma^2/n.$$

### 6.2 One-Sample Z-Test ($\sigma$ known)

$$Z = \frac{\bar X - \mu_0}{\sigma/\sqrt{n}} \sim N(0,1) \text{ under } H_0: \mu = \mu_0.$$

Rejection regions at level $\alpha$:

| Alternative | Reject if |
|---|---|
| $\mu < \mu_0$ | $Z < -z_\alpha$ |
| $\mu > \mu_0$ | $Z > z_\alpha$ |
| $\mu \ne \mu_0$ | $|Z| > z_{\alpha/2}$ |

### 6.3 Large-Sample Z-Test ($\sigma$ unknown, $n \ge 30$)

$$Z = \frac{\bar X - \mu_0}{S/\sqrt{n}} \approx N(0,1) \text{ under } H_0.$$

Rejection regions identical in form to the known-$\sigma$ case.

### 6.4 One-Sample t-Test (normal population, $\sigma$ unknown, small $n$)

$$t = \frac{\bar X - \mu_0}{S/\sqrt{n}} \sim t_{n-1} \text{ under } H_0.$$

Rejection regions at level $\alpha$:

| Alternative | Reject if |
|---|---|
| $\mu < \mu_0$ | $t < -t_\alpha$ |
| $\mu > \mu_0$ | $t > t_\alpha$ |
| $\mu \ne \mu_0$ | $|t| > t_{\alpha/2}$ |

Quantiles $t_\alpha, t_{\alpha/2}$ use $n-1$ degrees of freedom.

### 6.5 Confidence Intervals for $\mu$

| Setting | $100(1-\alpha)\%$ CI for $\mu$ |
|---|---|
| $\sigma$ known | $\bar x \pm z_{\alpha/2}\dfrac{\sigma}{\sqrt{n}}$ |
| $\sigma$ unknown, $n \ge 30$ | $\bar x \pm z_{\alpha/2}\dfrac{s}{\sqrt{n}}$ |
| Normal, $\sigma$ unknown, $n$ small | $\bar x \pm t_{\alpha/2}\dfrac{s}{\sqrt{n}}$ |

### 6.6 Relation Between Tests and Confidence Intervals

For a two-sided test of $H_0: \mu = \mu_0$ at level $\alpha$, **$H_0$ is rejected if and only if $\mu_0$ lies outside the $100(1-\alpha)\%$ confidence interval** for $\mu$. A confidence interval is therefore equivalent to the family of all such two-sided tests, and conveys strictly more information than a single test.

### 6.7 Required Sample Size for One-Sided Z-Test

For $H_0: \mu = \mu_0$ vs $H_1: \mu > \mu_0$ (or the symmetric case), with power $1-\beta$ at $\mu_1$:

$$n = \left[\frac{\sigma(z_\alpha + z_\beta)}{\mu_0 - \mu_1}\right]^2.$$

For two-sided tests, sample-size calculation is best done with software.

---

## 7. Two-Sample Inferences for Means

### 7.1 Independent Samples Design

Two independent random samples: $X_1,\dots,X_{n_1}$ from population 1 with mean $\mu_1$, variance $\sigma_1^2$; $Y_1,\dots,Y_{n_2}$ from population 2 with mean $\mu_2$, variance $\sigma_2^2$.

$$E[\bar X - \bar Y] = \mu_1 - \mu_2 = \delta, \qquad \mathrm{Var}(\bar X - \bar Y) = \frac{\sigma_1^2}{n_1} + \frac{\sigma_2^2}{n_2}.$$

### 7.2 Test Statistic Variants

| Setting | Test statistic | Distribution |
|---|---|---|
| Large samples ($n_1,n_2 \ge 30$) | $Z = \dfrac{(\bar X - \bar Y) - \delta_0}{\sqrt{S_1^2/n_1 + S_2^2/n_2}}$ | $\approx N(0,1)$ |
| Normal, equal $\sigma_1 = \sigma_2 = \sigma$ (pooled) | $t = \dfrac{(\bar X - \bar Y) - \delta_0}{S_p\sqrt{1/n_1 + 1/n_2}}$ | $t_{n_1+n_2-2}$ |
| Normal, unequal $\sigma$ (Smith–Satterthwaite) | $t' = \dfrac{(\bar X - \bar Y) - \delta_0}{\sqrt{S_1^2/n_1 + S_2^2/n_2}}$ | approx. $t_\nu$ |

where the **pooled variance** is

$$S_p^2 = \frac{(n_1-1)S_1^2 + (n_2-1)S_2^2}{n_1 + n_2 - 2}.$$

**Smith–Satterthwaite degrees of freedom:**

$$\nu = \frac{(S_1^2/n_1 + S_2^2/n_2)^2}{\dfrac{(S_1^2/n_1)^2}{n_1-1} + \dfrac{(S_2^2/n_2)^2}{n_2-1}},$$

rounded down to an integer for table use. As a rule of thumb, do not pool when one variance exceeds four times the other; a transformation often helps.

### 7.3 Confidence Intervals for $\delta = \mu_1 - \mu_2$

| Setting | $100(1-\alpha)\%$ CI for $\mu_1-\mu_2$ |
|---|---|
| Large samples | $(\bar x - \bar y) \pm z_{\alpha/2}\sqrt{S_1^2/n_1 + S_2^2/n_2}$ |
| Pooled | $(\bar x - \bar y) \pm t_{\alpha/2}\, S_p\sqrt{1/n_1 + 1/n_2}$ |
| Unequal variances | $(\bar x - \bar y) \pm t_{\alpha/2,\nu}\sqrt{S_1^2/n_1 + S_2^2/n_2}$ |

### 7.4 Rejection Regions for $\delta_0$

| Alternative | Reject if (Z or t) |
|---|---|
| $\mu_1 - \mu_2 < \delta_0$ | statistic $< -c$ |
| $\mu_1 - \mu_2 > \delta_0$ | statistic $> c$ |
| $\mu_1 - \mu_2 \ne \delta_0$ | $\mid$statistic$\mid > c_{\alpha/2}$ |

with $c = z_\alpha$ or $t_\alpha$ as appropriate. When $\delta_0 = 0$, the test is the "two-sample test of no difference."

### 7.5 Matched Pairs Design

For naturally paired data (e.g., before/after measurements), form differences $D_i = X_i - Y_i$, $i = 1,\dots,n$, and apply the **one-sample t-test** to the $D_i$:

$$t = \frac{\bar D - \mu_{D,0}}{S_D/\sqrt{n}} \sim t_{n-1}.$$

Hypotheses about $\mu_D = 0$ test for equality of the two population means. The 95% CI for $\mu_D$ is $\bar d \pm t_{\alpha/2}\, s_D/\sqrt{n}$.

Pairing eliminates the between-pair variability from the comparison and is more powerful than independent samples when the pairing variable strongly predicts the response.

### 7.6 Power and Sample Size for Two-Sample Z-Test

For $H_0: \delta = 0$ vs $H_1: \delta = \delta'$, define the fictitious single sample with

$$\sigma^2 = \sigma_1^2 + \sigma_2^2, \qquad n = \frac{\sigma^2}{\sigma_1^2/n_1 + \sigma_2^2/n_2}.$$

Then power formulas mirror the one-sample case with $\mu_0 - \mu_1$ replaced by $\delta_0 - \delta'$.

---

## 8. Inferences Concerning Variances

### 8.1 Sampling Distribution

For $X_1,\dots,X_n$ i.i.d. from a normal population:

$$\frac{(n-1)S^2}{\sigma^2} \sim \chi^2_{n-1}.$$

Hence $E[S^2] = \sigma^2$ (unbiased). The sample standard deviation $S$ is **not** unbiased for $\sigma$ (it underestimates for small $n$).

For two independent samples from normal populations:

$$\frac{S_1^2/\sigma_1^2}{S_2^2/\sigma_2^2} \sim F_{n_1-1,\,n_2-1}.$$

### 8.2 Confidence Intervals for $\sigma^2$ and $\sigma$

$$P\!\left(\chi^2_{1-\alpha/2,\,n-1} < \frac{(n-1)S^2}{\sigma^2} < \chi^2_{\alpha/2,\,n-1}\right) = 1-\alpha,$$

giving

$$\frac{(n-1)s^2}{\chi^2_{\alpha/2,\,n-1}} < \sigma^2 < \frac{(n-1)s^2}{\chi^2_{1-\alpha/2,\,n-1}}.$$

Taking square roots gives the corresponding CI for $\sigma$. Equal-tail intervals are not shortest (chi-square is skewed) but are used in practice.

### 8.3 Test for a Single Variance

Test statistic: $\chi^2 = \dfrac{(n-1)S^2}{\sigma_0^2} \sim \chi^2_{n-1}$ under $H_0: \sigma^2 = \sigma_0^2$.

| Alternative | Reject if |
|---|---|
| $\sigma^2 < \sigma_0^2$ | $\chi^2 < \chi^2_{1-\alpha}$ |
| $\sigma^2 > \sigma_0^2$ | $\chi^2 > \chi^2_{\alpha}$ |
| $\sigma^2 \ne \sigma_0^2$ | $\chi^2 < \chi^2_{1-\alpha/2}$ or $\chi^2 > \chi^2_{\alpha/2}$ |

### 8.4 F-Test for Equality of Two Variances

Let $S_M^2, S_m^2$ be the larger and smaller sample variances with sample sizes $n_M, n_m$. Under $H_0: \sigma_1^2 = \sigma_2^2$:

$$F = \frac{S_M^2}{S_m^2} \sim F_{n_M-1,\,n_m-1}.$$

For one-sided alternatives, place the hypothesized-larger variance's sample in the numerator. For two-sided test, $F_\alpha/2$ uses $n_M-1$ numerator and $n_m-1$ denominator d.f.

**Reciprocal relation:** $F_{1-\alpha}(\nu_1,\nu_2) = 1/F_\alpha(\nu_2,\nu_1)$.

### 8.5 Confidence Interval for $\sigma_2^2/\sigma_1^2$

$$F_{1-\alpha/2}(n_1-1,n_2-1)\cdot\frac{S_2^2}{S_1^2} < \frac{\sigma_2^2}{\sigma_1^2} < F_{\alpha/2}(n_1-1,n_2-1)\cdot\frac{S_2^2}{S_1^2}.$$

### 8.6 Robustness Warning

Procedures for variances are **not robust** to departures from normality. The sampling variance of $S^2$ depends on third and fourth moments under non-normality and can be much larger than $2\sigma^4/(n-1)$. Always plot the data and consider transformations (e.g., log) before reporting variance CIs or tests.

### 8.7 Estimating $\sigma$ from the Range

For normal samples with $n \le 10$, the unbiased estimator $\hat\sigma = R/d_2$ is competitive with $S$. Constants $d_2, d_3$ for $n = 2$ to $10$:

| $n$ | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|
| $d_2$ | 1.128 | 1.693 | 2.059 | 2.326 | 2.534 | 2.704 | 2.847 | 2.970 | 3.078 |
| $d_3$ | 0.853 | 0.888 | 0.880 | 0.864 | 0.848 | 0.833 | 0.820 | 0.808 | 0.797 |

---

## 9. Inferences About Proportions

### 9.1 Single Proportion

Data: $X$ successes in $n$ Bernoulli trials. Estimator: $\hat p = X/n$, $E[\hat p] = p$, $\mathrm{Var}(\hat p) = p(1-p)/n$.

**Standard error estimate:** $\sqrt{\hat p(1-\hat p)/n}$.

### 9.2 Large-Sample Confidence Interval for $p$

When $n\hat p$ and $n(1-\hat p)$ both exceed about 15:

$$\hat p \pm z_{\alpha/2}\sqrt{\frac{\hat p(1-\hat p)}{n}}.$$

### 9.3 Sample-Size Formula for Estimating $p$

For maximum error $E$ at level $1-\alpha$:

$$n = \frac{p(1-p)}{(E/z_{\alpha/2})^2} \quad \text{(if prior info on } p \text{)},$$

or, conservatively without prior info, $n = \dfrac{1}{4}(z_{\alpha/2}/E)^2$ (using $\max p(1-p) = 1/4$).

### 9.4 Large-Sample Test of $p = p_0$

$$Z = \frac{\hat p - p_0}{\sqrt{p_0(1-p_0)/n}} \approx N(0,1) \text{ under } H_0.$$

Rejection regions mirror the one-mean Z-test.

### 9.5 Exact Binomial Test

For small $n$, use the binomial directly. To test $H_0: p = p_0$ with Type I error at most $\alpha_B$:

| Alternative | Rejection region |
|---|---|
| $p \le p_0$ | $X \le x_1$, $x_1$ largest with $B(x_1;n,p_0) \le \alpha_B$ |
| $p \ge p_0$ | $X \ge x_2$, $x_2$ smallest with $1-B(x_2-1;n,p_0) \le \alpha_B$ |
| $p \ne p_0$ | $X \le x_1$ or $X \ge x_2$ (each tail $\alpha_B/2$) |

Software yields exact P-values and conservative CIs for arbitrary $n$.

### 9.6 Difference of Two Proportions

With $\hat p_1 = X_1/n_1$, $\hat p_2 = X_2/n_2$, and **pooled** $\hat p = (X_1+X_2)/(n_1+n_2)$:

$$Z = \frac{\hat p_1 - \hat p_2}{\sqrt{\hat p(1-\hat p)\left(\frac{1}{n_1} + \frac{1}{n_2}\right)}} \approx N(0,1) \text{ under } H_0: p_1 = p_2.$$

For confidence intervals (unpooled standard error):

$$(\hat p_1 - \hat p_2) \pm z_{\alpha/2}\sqrt{\frac{\hat p_1(1-\hat p_1)}{n_1} + \frac{\hat p_2(1-\hat p_2)}{n_2}}.$$

For testing $H_0: p_1 - p_2 = \delta_0$, replace the numerator with $(\hat p_1 - \hat p_2) - \delta_0$.

---

## 10. Chi-Square Tests for Proportions and Tables

### 10.1 Test of Homogeneity Among $k$ Proportions

Organize $k$ samples into a $2 \times k$ table of successes and failures. Compute the pooled proportion $\hat p = \sum X_i / \sum n_i$, then expected cell frequencies:

$$e_{1j} = n_j \hat p, \qquad e_{2j} = n_j(1-\hat p).$$

Equivalently, $e_{ij}$ = (row total $\times$ column total)/grand total.

**Test statistic:**

$$\chi^2 = \sum_{i=1}^{2}\sum_{j=1}^{k}\frac{(o_{ij} - e_{ij})^2}{e_{ij}} \sim \chi^2_{k-1} \text{ approximately under } H_0.$$

Reject $H_0: p_1 = p_2 = \cdots = p_k$ if $\chi^2 > \chi^2_{\alpha,\,k-1}$. For $k=2$, $\chi^2 = Z^2$ where $Z$ is the two-proportion test statistic.

**Caution.** All expected frequencies should be at least 5; combine cells if needed.

### 10.2 Analysis of $r \times c$ Tables

For an $r \times c$ contingency table, expected frequencies are

$$e_{ij} = \frac{(\text{row}_i\text{ total})(\text{col}_j\text{ total})}{\text{grand total}}.$$

The chi-square statistic

$$\chi^2 = \sum_{i=1}^r\sum_{j=1}^c \frac{(o_{ij} - e_{ij})^2}{e_{ij}}$$

is approximately $\chi^2_{(r-1)(c-1)}$ under the null hypothesis.

**Two distinct null hypotheses** give the same test statistic:
- **Homogeneity** (column totals fixed): $H_0: p_{i1} = p_{i2} = \cdots = p_{ic}$ for each row.
- **Independence** (single sample, two classifications): $H_0: p_{ij} = p_{i\cdot} \cdot p_{\cdot j}$.

Examining the cells' individual contributions $\chi^2_{ij} = (o_{ij}-e_{ij})^2/e_{ij}$ reveals the pattern of dependence.

### 10.3 Goodness of Fit

To test whether data follow a hypothesized distribution with $m$ parameters estimated from data:

$$\chi^2 = \sum_{i=1}^k \frac{(o_i - e_i)^2}{e_i} \sim \chi^2_{k-m} \text{ approximately}.$$

Combine cells so that all $e_i \ge 5$. Special cases include Poisson, binomial, exponential, and normal fitting.

---

## 11. Optimal Hypothesis Testing (Neyman–Pearson Theory)

### 11.1 Test Functions and Power Functions

A **test function** $\phi: \mathcal{S} \to [0,1]$ gives the conditional probability of rejecting $H_0$ given data $s$. The **power function** is $\beta(\theta) = E_\theta[\phi(\mathbf{X})]$. A test is **size** $\alpha$ if $\sup_{\theta \in \Theta_0} \beta(\theta) \le \alpha$; **exact size** $\alpha$ if equality holds.

A test function $\phi^*$ is **uniformly most powerful (UMP) size $\alpha$** if it is size $\alpha$ and $\beta_{\phi^*}(\theta) \ge \beta_\phi(\theta)$ for all $\theta \in \Theta_a$ and every other size-$\alpha$ test $\phi$.

Randomized tests ($\phi(\mathbf{x}) \in (0,1)$) may be required when the rejection region cannot be chosen to make the size exactly $\alpha$ (e.g., discrete distributions).

### 11.2 Neyman–Pearson Theorem (Simple $H_0$ vs Simple $H_a$)

**Theorem (Neyman–Pearson).** For testing $H_0: \theta = \theta_0$ vs $H_a: \theta = \theta_1$ (both simple), an exact-size-$\alpha$ UMP test has the **likelihood ratio form**

$$\phi(\mathbf{x}) = \begin{cases} 1 & f_1(\mathbf{x})/f_0(\mathbf{x}) > c \\ \gamma & f_1(\mathbf{x})/f_0(\mathbf{x}) = c \\ 0 & f_1(\mathbf{x})/f_0(\mathbf{x}) < c \end{cases}$$

for some $\gamma \in [0,1]$ and $c > 0$, where $f_i$ is the density under $\theta_i$.

The constant $c$ is the smallest value such that $E_0[\phi] \le \alpha$:

$$E_0\!\left[\frac{f_1(\mathbf{x})}{f_0(\mathbf{x})} > c\right] + \gamma\, P_0\!\left[\frac{f_1(\mathbf{x})}{f_0(\mathbf{x})} = c\right] = \alpha.$$

A UMP size-$\alpha$ test is unique up to $\phi$-null sets (i.e., on the boundary $\partial B = \{\mathbf{x}: f_1(\mathbf{x})/f_0(\mathbf{x}) = c\}$).

### 11.3 Sufficiency Reduces the Search

**Theorem.** If $U$ is a sufficient statistic and $\phi$ is size $\alpha$, then $\phi'(\mathbf{x}) = E[\phi(\mathbf{x}) \mid U]$ is size $\alpha$, has the same power function as $\phi$, and depends on data only through $U$. Hence UMP search can be restricted to functions of a sufficient statistic.

### 11.4 UMP Tests in Exponential Families: One-Sided Normal

For $X_1,\dots,X_n$ from $N(\mu,\sigma_2)$ with $\sigma^2$ known, the UMP size-$\alpha$ test of $H_0: \mu = \mu_0$ vs $H_a: \mu > \mu_0$ is the nonrandomized test rejecting when

$$\frac{\bar X - \mu_0}{\sigma/\sqrt{n}} > z_\alpha.$$

Because the rejection region does not depend on the specific alternative $\mu_1 > \mu_0$, this test is UMP for $H_0: \mu = \mu_0$ vs $H_a: \mu > \mu_0$. Similarly for $H_a: \mu < \mu_0$.

The **power function** is

$$\beta(\mu) = P\!\left(Z > z_\alpha - \frac{\mu-\mu_0}{\sigma/\sqrt{n}}\right),$$

which is increasing in $\mu$ (for $H_a: \mu > \mu_0$), confirming the test is unbiased.

### 11.5 No UMP for Two-Sided Alternatives in One-Parameter Families

For $H_0: \mu = \mu_0$ vs $H_a: \mu \ne \mu_0$ in $N(\mu,\sigma^2)$, no UMP size-$\alpha$ test exists: any UMP test against $\mu > \mu_0$ would have to equal the corresponding UMP test against $\mu < \mu_0$, which leads to a contradiction.

A **UMP unbiased** size-$\alpha$ test exists and rejects when $|\bar X - \mu_0|/(\sigma/\sqrt{n}) > z_{\alpha/2}$. (The two-sided test is automatically unbiased.)

### 11.6 UMP Tests for Bernoulli and Discrete Data (Randomization Needed)

For $X_1,\dots,X_n \sim \mathrm{Bernoulli}(p)$, testing $H_0: p = p_0$ vs $H_a: p = p_1$ ($p_1 > p_0$): the likelihood ratio $\frac{f_1}{f_0}$ is monotone in $T = \sum X_i$. The UMP size-$\alpha$ test has rejection region

$$T \ge c_0 \quad \text{with randomization at } T = c_0 \text{ if needed}.$$

Because $T \sim \mathrm{Binomial}(n,p_0)$ is discrete, the exact size $\alpha$ may be unattainable; we use the largest $c_0$ with $P_0(T \ge c_0) \le \alpha$ and randomize on the boundary with probability $\gamma = (\alpha - P_0(T > c_0))/P_0(T = c_0)$.

The UMP property extends to $H_a: p > p_0$ (one-sided) and $H_a: p < p_0$ (symmetric argument). A UMP unbiased test exists for $H_a: p \ne p_0$.

### 11.7 Generalized Likelihood Ratio Tests

For composite $H_0: \theta \in \Theta_0$ vs $H_a: \theta \in \Theta_a$, the **generalized likelihood ratio** is

$$\Lambda(\mathbf{x}) = \frac{\sup_{\theta \in \Theta_0} L(\theta;\mathbf{x})}{\sup_{\theta \in \Theta} L(\theta;\mathbf{x})}.$$

Reject $H_0$ for small $\Lambda$. Under regularity and $H_0$ true,

$$-2\log\Lambda(\mathbf{x}) \xrightarrow{d} \chi^2_{\dim\Theta - \dim\Theta_0},$$

so a size-$\alpha$ test rejects when $-2\log\Lambda > \chi^2_{\alpha,\,\dim\Theta - \dim\Theta_0}$.

### 11.8 Optimal Confidence Sets from UMP Tests

For each $\theta_0$, let $\phi_{\theta_0}$ be a UMP size-$\alpha$ test of $H_0: \theta = \theta_0$ (nonrandomized, taking values in $\{0,1\}$). Then

$$C(\mathbf{x}) = \{\theta_0 : \phi_{\theta_0}(\mathbf{x}) = 0\}$$

is a $100(1-\alpha)\%$ confidence set, and among all such sets it is **uniformly most accurate (UMA)**: it minimizes $P_\theta(\theta_0 \in C)$ for every $\theta_0 \ne \theta$.

---

## 12. Optimal Bayesian Inference

### 12.1 Bayes Rule for Estimation (Squared-Error Loss)

With prior $\pi(\theta)$ on $\theta$ and data $s$, the posterior $\pi(\theta \mid s)$ has posterior risk (given $s$) for estimator $T(s)$ equal to $E_{\theta \mid s}[(T(s) - \theta)^2]$.

**Theorem.** When posterior variance is finite, the posterior mean

$$T^*(s) = E[\theta \mid s]$$

is the unique Bayes rule (minimizes prior expected MSE).

Because the problem has a solution, **no restriction to unbiased estimators is needed** in the Bayesian framework. As $n \to \infty$ under weak regularity, the posterior concentrates, and $T^*(s) \to \theta$.

### 12.2 Bayes Rule for Hypothesis Testing (0–1 Loss)

For testing $H_0: \theta = \theta_0$ vs $H_a: \theta \ne \theta_0$ under equal-weighted 0–1 loss (each error costs 1), the **Bayes rule** is

$$\phi^*(s) = \begin{cases} 1 & P(H_0 \mid s) \le P(H_a \mid s) \\ 0 & P(H_0 \mid s) > P(H_a \mid s) \end{cases}$$

i.e., reject $H_0$ whenever the posterior odds favor $H_a$. This minimizes the prior probability of error.

**Caveat.** The prior must place positive mass on $H_0$ (e.g., a mixture $\pi = p_0 \delta_{\theta_0} + (1-p_0)g$). If $\pi(\Theta_0) = 0$, the Bayes rule is $\phi \equiv 1$, always rejecting $H_0$.

### 12.3 Conjugate Bayesian Examples

| Likelihood | Conjugate prior | Posterior |
|---|---|---|
| $N(\mu,\sigma^2)$, $\sigma$ known | $N(\mu_0, \tau^2)$ | $N(\mu_n, \tau_n^2)$ with $\mu_n = w\bar x + (1-w)\mu_0$, $w = \sigma^2/(\sigma^2+n\tau^2)$ |
| Bernoulli$(p)$ | Beta$(\alpha,\beta)$ | Beta$(\alpha+X, \beta+n-X)$ |
| Poisson$(\lambda)$ | Gamma$(\alpha,\beta)$ | Gamma$(\alpha+\sum X_i, \beta/(1+n\beta))$ |
| Exponential$(\beta)$ | Inv-Gamma | Updated form |

For squared-error loss, the Bayes estimator is the posterior mean; for 0–1 testing loss, the Bayes rule uses posterior odds.

---

## 13. Design and Implementation

### 13.1 Randomization

**Independent samples.** Assign treatments to $n$ units using random numbers; all $\binom{n}{n_1}$ selections of $n_1$ units for treatment 1 should be equally likely. Equal sample sizes maximize power for a given $n$.

**Matched pairs.** After pairing, flip a coin (or use random numbers) within each pair to assign treatments. This prevents systematic effects from uncontrolled variables.

**Purpose.** Randomization prevents uncontrolled variation from systematically biasing the comparison, providing a basis for inference even when the strict "random sample" assumption cannot be verified.

### 13.2 Pairs vs. Independent Samples

Pairing is most valuable when the pairing variable strongly predicts the response (eliminating between-pair variability) and when both treatments can be applied to the same unit. Independent samples are simpler and necessary when pairing is impossible (different units, destructive testing, etc.).

### 13.3 Choice of Significance Level

Common levels are $\alpha = 0.05$ and $\alpha = 0.01$. The choice should reflect the cost asymmetry between Type I and Type II errors. Use the smaller $\alpha$ when Type I error is more serious (e.g., safety-critical decisions). The probability of Type I error should not be set so low that the test has negligible power for practically important alternatives.

### 13.4 Operating Characteristic Curves

The OC curve plots $L(\mu) = P(\text{accept } H_0)$ vs $\mu$. It is read alongside the power curve $\gamma(\mu) = 1 - L(\mu)$. A well-designed test has an OC curve that drops sharply near $\mu_0$.

---

## 14. Decision Theory (Advanced)

### 14.1 The Decision Framework

Components:
- **Action space** $\mathcal{A}$: set of possible decisions.
- **Correct action** $A(\theta)$: optimal action when $\theta$ is true.
- **Loss function** $L(a,\theta)$: loss incurred by taking action $a$ when $\theta$ is true.
- **Decision rule** $\delta(s)$: maps data to actions.

### 14.2 Frequentist Risk

$$R(\theta, \delta) = E_\theta[L(\delta(s), \theta)].$$

Common losses:
- **Squared error:** $L(a,\theta) = (a-\theta)^2$, leading to MSE.
- **Absolute error:** $L(a,\theta) = |a-\theta|$, leading to MAD; Bayes rule = posterior median.
- **0–1 loss:** $L(a,\theta) = 1\{a \ne \theta\}$, leading to misclassification rate.

### 14.3 Bayes Risk and Bayes Rule

$$r(\pi, \delta) = E_\pi[R(\theta, \delta)] = E_\pi E_\theta[L(\delta(s), \theta)].$$

A **Bayes rule** minimizes $r(\pi, \delta)$ over all decision rules. By the theorem of total expectation and minimization pointwise in $s$, the Bayes rule is determined by minimizing the posterior expected loss for each $s$:

$$\delta^*(s) = \arg\min_{a \in \mathcal{A}} E_\theta[L(a,\theta) \mid s].$$

### 14.4 Minimax Rules

A **minimax** rule minimizes $\sup_\theta R(\theta, \delta)$ over $\delta$. It guards against the worst-case parameter value and is appropriate when the prior is unavailable or unpalatable. Bayes rules that are also minimax (e.g., for symmetric, well-behaved families) provide a dual justification.

### 14.5 Admissibility

A decision rule $\delta_1$ **dominates** $\delta_2$ if $R(\theta,\delta_1) \le R(\theta,\delta_2)$ for all $\theta$ with strict inequality for some. A rule is **admissible** if no rule dominates it. Admissibility is generally harder to establish than optimality within a restricted class.

---

## 15. Master Summary Tables

### 15.1 Inferences for One Mean

| Setting | Statistic | Distribution | $100(1-\alpha)\%$ CI |
|---|---|---|---|
| $\sigma$ known | $Z=\dfrac{\bar X-\mu_0}{\sigma/\sqrt{n}}$ | $N(0,1)$ | $\bar x \pm z_{\alpha/2}\sigma/\sqrt{n}$ |
| $\sigma$ unknown, $n$ large | $Z=\dfrac{\bar X-\mu_0}{S/\sqrt{n}}$ | $\approx N(0,1)$ | $\bar x \pm z_{\alpha/2}s/\sqrt{n}$ |
| $\sigma$ unknown, normal | $t=\dfrac{\bar X-\mu_0}{S/\sqrt{n}}$ | $t_{n-1}$ | $\bar x \pm t_{\alpha/2}s/\sqrt{n}$ |

### 15.2 Inferences for Two Means

| Setting | Statistic | d.f. | CI for $\mu_1-\mu_2$ |
|---|---|---|---|
| Large samples | $Z=\dfrac{(\bar X-\bar Y)-\delta_0}{\sqrt{S_1^2/n_1+S_2^2/n_2}}$ | — | $(\bar x-\bar y) \pm z_{\alpha/2}\sqrt{S_1^2/n_1+S_2^2/n_2}$ |
| Pooled, normal | $t=\dfrac{(\bar X-\bar Y)-\delta_0}{S_p\sqrt{1/n_1+1/n_2}}$ | $n_1+n_2-2$ | $(\bar x-\bar y) \pm t_{\alpha/2}S_p\sqrt{1/n_1+1/n_2}$ |
| Smith–Satterthwaite | $t'=\dfrac{(\bar X-\bar Y)-\delta_0}{\sqrt{S_1^2/n_1+S_2^2/n_2}}$ | $\nu$ (Welch) | $(\bar x-\bar y) \pm t_{\alpha/2,\nu}\sqrt{S_1^2/n_1+S_2^2/n_2}$ |
| Matched pairs | $t=\dfrac{\bar D - \mu_{D,0}}{S_D/\sqrt{n}}$ | $n-1$ | $\bar d \pm t_{\alpha/2}s_D/\sqrt{n}$ |

### 15.3 Inferences for Variances

| Setting | Statistic | Distribution |
|---|---|---|
| Single $\sigma^2$ | $\chi^2=(n-1)S^2/\sigma_0^2$ | $\chi^2_{n-1}$ |
| Ratio $\sigma_2^2/\sigma_1^2$ | $F=S_1^2/S_2^2$ | $F_{n_1-1,\,n_2-1}$ |

### 15.4 Inferences for Proportions

| Setting | Statistic | Distribution |
|---|---|---|
| Single $p$ | $Z=(\hat p-p_0)/\sqrt{p_0(1-p_0)/n}$ | $\approx N(0,1)$ |
| Two $p$ (test) | $Z=(\hat p_1-\hat p_2)/\sqrt{\hat p(1-\hat p)(1/n_1+1/n_2)}$ | $\approx N(0,1)$ |
| $k$ proportions (homogeneity) | $\chi^2=\sum (o-e)^2/e$ | $\approx \chi^2_{k-1}$ |
| $r\times c$ table | $\chi^2=\sum (o-e)^2/e$ | $\approx \chi^2_{(r-1)(c-1)}$ |
| Goodness of fit | $\chi^2=\sum (o-e)^2/e$ | $\approx \chi^2_{k-m}$ |

### 15.5 UMVUE and MLE Quick Reference

| Parameter | UMVUE | MLE |
|---|---|---|
| $\mu$ in $N(\mu,\sigma^2)$ | $\bar X$ | $\bar X$ |
| $\sigma^2$ in $N(\mu,\sigma^2)$ | $S^2$ (if $\mu$ unknown) | $\frac{1}{n}\sum(X_i-\bar X)^2$ (biased) |
| $p$ in Bernoulli$(p)$ | $\bar X$ | $\bar X$ |
| $\lambda$ in Poisson$(\lambda)$ | $\bar X$ | $\bar X$ |
| $\beta$ in Gamma$(\alpha,\beta)$ | $\bar X/\alpha$ | $\bar X/\alpha$ |
| $\theta$ in Uniform$[0,\theta]$ | $\frac{n+1}{n}X_{(n)}$ | $X_{(n)}$ (biased) |
| $\theta^2$ in Uniform$[0,\theta]$ | $\frac{n+1}{n+2}\left(\frac{n+1}{n}\right)X_{(n)}^2$ | $X_{(n)}^2$ (biased) |

### 15.6 Bayes Rules Quick Reference

| Loss / Task | Bayes rule |
|---|---|
| Estimation, squared error | Posterior mean $E[\theta \mid s]$ |
| Estimation, absolute error | Posterior median |
| Testing, 0–1 loss | Reject if $P(H_0 \mid s) \le P(H_a \mid s)$ |
| Testing, asymmetric loss | Threshold on posterior odds = loss ratio |

---

## 16. Pitfalls, Caveats, and Best Practices

1. **Unbiasedness restriction is restrictive.** Restricting to unbiased estimators can exclude estimators with lower MSE (e.g., regularized or biased estimators).
2. **Information bound may not be attained.** In some families (e.g., Uniform$[0,\theta]$ for $\theta$), no unbiased estimator attains the CRLB; the UMVUE is preferred.
3. **MLE for variance is biased** by the factor $(n-1)/n$. The unbiased version $S^2$ is UMVUE under normality.
4. **UMVUE uniqueness** (a.e.) holds when the sufficient statistic is complete; otherwise multiple UMVUEs may exist.
5. **Two-sided UMP tests rarely exist** in one-parameter exponential families. UMP *unbiased* tests do exist and are recommended.
6. **Discrete distributions require randomization** for exact-size tests; otherwise the actual size is below the nominal level.
7. **Variance procedures are not robust** to non-normality. Plot data and consider transformations before applying chi-square or F tests.
8. **Equal-variance assumption in two-sample t-test** is sensitive to large variance ratios; as a rule of thumb, if one variance exceeds four times the other, do not pool and prefer Smith–Satterthwaite.
9. **Match-pair t-test requires independence of the differences**, not of the original measurements.
10. **P-values do not replace significance-level decisions.** Pre-specify $\alpha$; P-values complement, not replace, that threshold.
11. **Confidence intervals convey more information** than point hypothesis tests; the two-sided level-$\alpha$ test is equivalent to checking whether $\theta_0$ is in the $100(1-\alpha)\%$ CI.
12. **Bayesian analysis requires a defensible prior.** When prior information is weak, choose diffuse priors and report sensitivity to prior choice; in the limit, posterior inference approximates MLE-based inference.
13. **Randomization** (assigning treatments to units) is the design analog of random sampling and is essential for the validity of classical inference in experiments.

This reference unifies the rigorous Neyman–Pearson, Rao–Blackwell, Lehmann–Scheffé, and Bayesian decision-theoretic foundations with the applied z-, t-, chi-square, and F-test machinery used in engineering and data science, providing a self-contained map from optimality principles to the formulas, distributions, and procedures that operationalize them.
