# Probability Distributions

## Orientation
A random variable is a real-valued function defined on a sample space; its distribution specifies how probability is spread across the values it can take. Discrete random variables take countably many values and are described by probability mass functions (pmf) with probabilities assigned directly to each value, while continuous random variables are described by probability density functions (pdf) with probabilities obtained by integration. This reference collects every standard distribution family, the machinery of expectations, variances, moment generating functions, joint/conditional/marginal distributions, approximation results, and key inequalities used throughout applied probability and statistics.

---

## Random Variables and Their Distributions

### Random Variables

A **random variable** is a function that assigns a numerical value to each outcome in a sample space. Random variables are typically denoted by uppercase letters $X, Y, Z, \ldots$ and their realized values by lowercase $x, y, z, \ldots$.

Two broad classes:
- **Discrete random variable**: takes only a finite or countably infinite set of values; all probability comes from being equal to specific values, i.e., $\sum_x P(X=x) = 1$.
- **Continuous random variable**: $P(X=x)=0$ for every $x$; probabilities are obtained by integrating a density over intervals.

### Probability Mass Function (Discrete)

The **probability distribution** of a discrete random variable $X$ is
$$f(x) = P(X=x)$$
which must satisfy $f(x)\ge 0$ for all $x$ and $\sum_{\text{all }x} f(x) = 1$.

### Probability Density Function (Continuous)

A **probability density** $f$ satisfies $f(x)\ge 0$ and $\int_{-\infty}^{\infty} f(x)\,dx = 1$, with probabilities given by
$$P(a\le X\le b) = \int_a^b f(x)\,dx.$$
In the continuous case, $P(X=x)=0$ for every point $x$, and whether or not the endpoints are included does not matter:
$$P(a\le X\le b) = P(a\le X<b) = P(a<X\le b) = P(a<X<b).$$

### Cumulative Distribution Function

The **cumulative distribution function (cdf)** is
$$F(x) = P(X\le x).$$
For discrete variables, $F(x) = \sum_{y\le x} f(y)$ (right-continuous, piecewise constant with jumps of size $f(x)$ at points with positive mass). For continuous variables, $F(x) = \int_{-\infty}^x f(t)\,dt$ and $F'(x) = f(x)$ wherever the derivative exists.

### Axiom (countable additivity)

Axiom 3′ (extension to countably infinite disjoint unions): if $A_1, A_2, \ldots$ are mutually exclusive, then
$$P\!\left(\bigcup_{i=1}^\infty A_i\right) = \sum_{i=1}^\infty P(A_i).$$
This is needed for distributions (Poisson, geometric, etc.) on countably infinite supports.

### Properties of any cdf $F$

- $0 \le F(x) \le 1$ for all $x$.
- $F$ is non-decreasing.
- $\lim_{x\to-\infty} F(x) = 0$ and $\lim_{x\to\infty} F(x) = 1$.
- $F$ is right-continuous.

For any interval $[a,b]$: $P(a\le X\le b) = F(b) - F(a^-)$; for any $a$, $P(X=a) = F(a) - F(a^-)$.

---

## Common Discrete Distributions

### Bernoulli (Bernoulli($p$))

| Item | Formula |
|---|---|
| Support | $x\in\{0,1\}$ |
| pmf | $P(X=1)=p,\ P(X=0)=1-p$ |
| Mean | $p$ |
| Variance | $p(1-p)$ |
| mgf | $M(t) = 1-p + p e^{t}$ |

Models a single trial with two outcomes. **When used:** building block for binomial, geometric, negative binomial.

### Binomial (Binomial($n,p$))

Number of successes in $n$ independent Bernoulli trials each with success probability $p$.

$$P(X=x) = \binom{n}{x} p^x (1-p)^{n-x}, \quad x=0,1,\ldots,n.$$

| Item | Value |
|---|---|
| Mean | $\mu = np$ |
| Variance | $\sigma^2 = np(1-p)$ |
| mgf | $M(t) = (1-p+pe^t)^n$ |
| Mode | $\lfloor (n+1)p\rfloor$ |

Cumulative: $B(x;n,p) = \sum_{k=0}^x \binom{n}{k}p^k(1-p)^{n-k}$. Useful identity: $P(a\le X\le b) = B(b;n,p) - B(a-1;n,p)$ and $b(x;n,p) = B(x;n,p) - B(x-1;n,p)$.

**When to use:** counts of successes in a fixed number of independent, identical trials. **Caveat:** always check the four Bernoulli assumptions (two outcomes, constant $p$, independence, fixed $n$). **Shape:** symmetric at $p=1/2$, positively skewed when $p<1/2$, negatively skewed when $p>1/2$.

### Hypergeometric (Hypergeometric($N, a, n$))

Number of "successes" in a sample of $n$ drawn **without replacement** from a finite population of $N$ items containing $a$ successes.

$$P(X=x) = \frac{\binom{a}{x}\binom{N-a}{n-x}}{\binom{N}{n}}, \quad x=\max(0, n-(N-a)),\ldots,\min(n,a).$$

| Item | Value |
|---|---|
| Mean | $\mu = n\cdot \dfrac{a}{N}$ |
| Variance | $\sigma^2 = n\cdot\dfrac{a}{N}\!\left(1-\dfrac{a}{N}\right)\!\dfrac{N-n}{N-1}$ |

The factor $\frac{N-n}{N-1}$ is the **finite population correction**. **When to use:** sampling without replacement from a small finite batch. **Rule of thumb:** the binomial with $p = a/N$ is a good approximation when $n \le N/10$; the two agree exactly in the limit $N\to\infty$.

### Geometric (Geometric($p$))

Number of trials until the first success (counting from 1), in independent Bernoulli trials with success probability $p$:

$$P(X=x) = p(1-p)^{x-1}, \quad x=1,2,3,\ldots$$

| Item | Value |
|---|---|
| Mean | $\mu = 1/p$ |
| Variance | $\sigma^2 = (1-p)/p^2$ |
| mgf | $M(t) = \dfrac{pe^t}{1-(1-p)e^t}$ for $t<-\ln(1-p)$ |

A **memoryless** distribution: $P(X>s+t \mid X>s) = P(X>t)$. The convention "number of failures before first success" uses $P(X=x)=(1-p)^x p$ for $x=0,1,2,\ldots$ with mean $(1-p)/p$.

### Negative-Binomial (Negative-Binomial($r,p$))

Number of trials required to obtain the $r$-th success:

$$P(X=x) = \binom{x-1}{r-1} p^r (1-p)^{x-r}, \quad x=r, r+1, r+2, \ldots$$

| Item | Value |
|---|---|
| Mean | $\mu = r/p$ |
| Variance | $\sigma^2 = r(1-p)/p^2$ |
| mgf | $M(t) = \left(\dfrac{pe^t}{1-(1-p)e^t}\right)^r$ for $t<-\ln(1-p)$ |

Reduces to the geometric when $r=1$. **When to use:** counts of trials needed to achieve $r$ successes, especially for overdispersed counts.

### Poisson (Poisson($\lambda$))

Counts of rare events over a fixed interval of time or space:

$$P(X=x) = \frac{\lambda^x e^{-\lambda}}{x!}, \quad x = 0,1,2,\ldots,\quad \lambda>0.$$

| Item | Value |
|---|---|
| Mean | $\mu = \lambda$ |
| Variance | $\sigma^2 = \lambda$ |
| mgf | $M(t) = \exp(\lambda(e^t-1))$ |
| Mode | $\lfloor \lambda\rfloor$ (the two adjacent integers when $\lambda$ is integer) |
| Recursion | $P(X=x+1) = \dfrac{\lambda}{x+1}\,P(X=x)$ |

**When to use:** rare events in continuous time/space; events arising from a Poisson process. **As Poisson limit of the binomial:** when $n\to\infty$ and $p\to 0$ with $np=\lambda$ fixed, $\text{Binomial}(n,p) \to \text{Poisson}(\lambda)$. **Rule of thumb for approximation:** $n\ge 20$ and $p\le 0.05$ acceptable; excellent when $n\ge 100$ and $np\le 10$.

### Multinomial (Multinomial($n; p_1, \ldots, p_k$))

Each of $n$ independent trials yields one of $k$ outcomes with probabilities $p_1, \ldots, p_k$ ($\sum p_i = 1$). Let $X_i$ = number of trials of type $i$:

$$P(X_1=x_1,\ldots,X_k=x_k) = \frac{n!}{x_1!\,x_2!\,\cdots x_k!}\, p_1^{x_1} p_2^{x_2}\cdots p_k^{x_k}, \quad \sum_i x_i = n,\ x_i\ge 0.$$

| Item | Value |
|---|---|
| $E[X_i]$ | $n p_i$ |
| $\text{Var}(X_i)$ | $n p_i(1-p_i)$ |
| $\text{Cov}(X_i, X_j)$ | $-n p_i p_j$ for $i\ne j$ |

**When to use:** classification into $k\ge 2$ categories. Reduces to the binomial when $k=2$.

### Summary Table: Discrete Distributions

| Distribution | pmf $P(X=x)$ | Mean | Variance | mgf |
|---|---|---|---|---|
| Bernoulli($p$) | $p^x(1-p)^{1-x}$ | $p$ | $p(1-p)$ | $1-p+pe^t$ |
| Binomial($n,p$) | $\binom{n}{x}p^x(1-p)^{n-x}$ | $np$ | $np(1-p)$ | $(1-p+pe^t)^n$ |
| Hypergeometric($N,a,n$) | $\binom{a}{x}\binom{N-a}{n-x}/\binom{N}{n}$ | $na/N$ | $\frac{na}{N}\!\left(1-\frac{a}{N}\right)\!\frac{N-n}{N-1}$ | — |
| Geometric($p$) | $p(1-p)^{x-1}$ | $1/p$ | $(1-p)/p^2$ | $pe^t/(1-(1-p)e^t)$ |
| Negative-Binomial($r,p$) | $\binom{x-1}{r-1}p^r(1-p)^{x-r}$ | $r/p$ | $r(1-p)/p^2$ | $(pe^t/(1-(1-p)e^t))^r$ |
| Poisson($\lambda$) | $\lambda^x e^{-\lambda}/x!$ | $\lambda$ | $\lambda$ | $\exp(\lambda(e^t-1))$ |
| Multinomial($n;p_i$) | $n!\prod p_i^{x_i}/\prod x_i!$ | $np_i$ | $np_i(1-p_i)$ | $\left(\sum p_i e^{t_i}\right)^n$ |

---

## Common Continuous Distributions

### Uniform (Uniform($\alpha,\beta$))

$$f(x) = \frac{1}{\beta-\alpha}, \quad \alpha<x<\beta.$$

| Item | Value |
|---|---|
| cdf | $F(x) = (x-\alpha)/(\beta-\alpha)$ for $\alpha\le x\le\beta$ |
| Mean | $\mu = (\alpha+\beta)/2$ |
| Variance | $\sigma^2 = (\beta-\alpha)^2/12$ |
| mgf | $M(t) = (e^{\beta t} - e^{\alpha t})/((\beta-\alpha)t)$ |

**When used:** equal likelihood over an interval, modeling lack of information on a bounded range, generating random variates via inversion.

### Normal / Gaussian (Normal($\mu,\sigma^2$))

$$f(x) = \frac{1}{\sigma\sqrt{2\pi}} \exp\!\left(-\frac{(x-\mu)^2}{2\sigma^2}\right), \quad -\infty<x<\infty.$$

| Item | Value |
|---|---|
| Mean | $\mu$ |
| Variance | $\sigma^2$ |
| mgf | $M(t) = \exp(\mu t + \tfrac{1}{2}\sigma^2 t^2)$ |
| cdf | No closed form; use tables/$\Phi(z)$ |

**Standardization:** if $X\sim N(\mu,\sigma^2)$, then $Z = (X-\mu)/\sigma \sim N(0,1)$. The standard normal cdf is $\Phi(z) = P(Z\le z) = \int_{-\infty}^z \frac{1}{\sqrt{2\pi}}e^{-t^2/2}dt$, with $\Phi(-z) = 1 - \Phi(z)$.

For $a<b$:
$$P(a<X<b) = \Phi\!\left(\frac{b-\mu}{\sigma}\right) - \Phi\!\left(\frac{a-\mu}{\sigma}\right).$$

**When used:** symmetric, bell-shaped variation; errors of measurement; the limiting distribution of standardized sums (CLT). **The notation** $z_\alpha$ denotes the value such that $P(Z > z_\alpha) = \alpha$, e.g., $z_{0.05} = 1.645$, $z_{0.025} = 1.96$, $z_{0.01} = 2.33$, $z_{0.005} = 2.575$.

### Log-Normal (Log-Normal($\alpha,\beta^2$))

$X$ has the log-normal distribution if $\ln X \sim \text{Normal}(\alpha, \beta^2)$:

$$f(x) = \frac{1}{x\beta\sqrt{2\pi}} \exp\!\left(-\frac{(\ln x - \alpha)^2}{2\beta^2}\right), \quad x>0.$$

| Item | Value |
|---|---|
| cdf | $F(x) = \Phi\!\left(\dfrac{\ln x - \alpha}{\beta}\right)$ |
| Mean | $\mu = e^{\alpha + \beta^2/2}$ |
| Variance | $\sigma^2 = e^{2\alpha + \beta^2}(e^{\beta^2} - 1)$ |

**When used:** quantities that arise as products of many small multiplicative effects (failure times, incomes, particle sizes, gold concentrations). Positively skewed; cannot be negative.

### Exponential (Exponential($\beta$) or Exp($\lambda$))

$$f(x) = \frac{1}{\beta}e^{-x/\beta}, \quad x>0, \quad \beta>0 \quad \text{(rate form: } f(x)=\lambda e^{-\lambda x}\text{)}.$$

| Item | Value (scale $\beta$) | Value (rate $\lambda$) |
|---|---|---|
| Mean | $\beta$ | $1/\lambda$ |
| Variance | $\beta^2$ | $1/\lambda^2$ |
| mgf | $M(t) = (1-\beta t)^{-1}$ | $M(t) = \lambda/(\lambda-t)$ |
| cdf | $1-e^{-x/\beta}$ | $1-e^{-\lambda x}$ |

**Memoryless property:** $P(X > s+t \mid X > s) = P(X > t)$. **Connection to Poisson processes:** interarrival times in a Poisson($\alpha$) process are Exponential with mean $1/\alpha$ (scale form $\beta = 1/\alpha$). **When used:** lifetimes of components with constant hazard; waiting times.

### Gamma (Gamma($\alpha,\beta$))

$$f(x) = \frac{1}{\beta^{\alpha}\Gamma(\alpha)} x^{\alpha-1} e^{-x/\beta}, \quad x>0, \quad \alpha>0,\ \beta>0.$$

The **gamma function** $\Gamma(\alpha) = \int_0^\infty t^{\alpha-1}e^{-t}dt$ satisfies $\Gamma(\alpha)=(\alpha-1)\Gamma(\alpha-1)$ and $\Gamma(n)=(n-1)!$ for positive integers $n$.

| Item | Value |
|---|---|
| Mean | $\mu = \alpha\beta$ |
| Variance | $\sigma^2 = \alpha\beta^2$ |
| mgf | $M(t) = (1-\beta t)^{-\alpha}$ for $t<1/\beta$ |
| Special case | $\alpha=1$ reduces to Exponential($\beta$) |
| Sum property | Sum of $n$ i.i.d. Exp($\beta$) is Gamma($n,\beta$) |

**Shape:** positively skewed; skewness decreases as $\alpha$ grows. The Gamma($k/2, 2$) family gives the **chi-square distribution** with $k$ degrees of freedom.

### Beta (Beta($\alpha,\beta$))

$$f(x) = \frac{\Gamma(\alpha+\beta)}{\Gamma(\alpha)\Gamma(\beta)}\, x^{\alpha-1}(1-x)^{\beta-1}, \quad 0<x<1, \quad \alpha>0,\ \beta>0.$$

| Item | Value |
|---|---|
| Mean | $\mu = \alpha/(\alpha+\beta)$ |
| Variance | $\sigma^2 = \alpha\beta/[(\alpha+\beta)^2(\alpha+\beta+1)]$ |
| Special case | $\alpha=\beta=1$ gives Uniform(0,1) |
| Mode | $(\alpha-1)/(\alpha+\beta-2)$ for $\alpha,\beta>1$ |

**When used:** model a random variable confined to $(0,1)$ (proportions, percentages, probabilities), Bayesian prior for a binomial probability.

### Weibull (Weibull($\alpha,\beta$))

$$f(x) = \alpha\beta x^{\beta-1} e^{-\alpha x^{\beta}}, \quad x>0,\ \alpha>0,\ \beta>0.$$

| Item | Value |
|---|---|
| cdf | $F(x) = 1 - e^{-\alpha x^{\beta}}$ |
| Mean | $\mu = \alpha^{-1/\beta}\,\Gamma(1+1/\beta)$ |
| Variance | $\sigma^2 = \alpha^{-2/\beta}\left[\Gamma(1+2/\beta) - \Gamma(1+1/\beta)^2\right]$ |
| Special case | $\beta=1$ gives Exponential with mean $1/\alpha$ |

**When used:** lifetime/reliability modeling; flexible shape parameter $\beta$ (decreasing failure rate when $\beta<1$, increasing when $\beta>1$).

### Chi-Square ($\chi^2_k$)

Same as Gamma($k/2, 2$):

$$f(x) = \frac{1}{2^{k/2}\Gamma(k/2)} x^{k/2-1} e^{-x/2}, \quad x>0.$$

| Item | Value |
|---|---|
| Mean | $k$ |
| Variance | $2k$ |
| mgf | $M(t) = (1-2t)^{-k/2}$ for $t<1/2$ |

**When used:** sample variances, goodness-of-fit, likelihood-ratio tests, sum of squares of $k$ i.i.d. standard normals.

### Student's $t$ ($t_\nu$)

$$f(x) = \frac{\Gamma((\nu+1)/2)}{\sqrt{\nu\pi}\,\Gamma(\nu/2)}\left(1+\frac{x^2}{\nu}\right)^{-(\nu+1)/2}, \quad -\infty<x<\infty.$$

| Item | Value |
|---|---|
| Mean | $0$ for $\nu>1$ |
| Variance | $\nu/(\nu-2)$ for $\nu>2$ |
| mgf | does not exist |
| Special case | $\nu=1$ gives Cauchy; $\nu\to\infty$ gives $N(0,1)$ |

**When used:** inference about means with unknown variance; $t$ distribution with $\nu$ df arises as $Z/\sqrt{V/\nu}$ for independent $Z\sim N(0,1)$ and $V\sim\chi^2_\nu$.

### $F$ Distribution (F($d_1,d_2$))

$$f(x) = \frac{1}{B(d_1/2,d_2/2)}\left(\frac{d_1}{d_2}\right)^{d_1/2} \frac{x^{d_1/2-1}}{(1+d_1 x/d_2)^{(d_1+d_2)/2}}, \quad x>0.$$

| Item | Value |
|---|---|
| Mean | $d_2/(d_2-2)$ for $d_2>2$ |
| Variance | $\frac{2 d_2^2 (d_1+d_2-2)}{d_1(d_2-2)^2(d_2-4)}$ for $d_2>4$ |

**When used:** ratio of chi-square variables (scaled); ANOVA, regression, comparing variances.

### Other Named Continuous Families (one-line summaries)

- **Cauchy:** $f(x)=\frac{1}{\pi(1+x^2)}$; symmetric, heavy tails; mean and variance undefined; arises as $Z_1/Z_2$ for i.i.d. standard normals.
- **Laplace (double exponential):** $f(x)=\tfrac{1}{2}e^{-|x|}$; symmetric, exponential tails; mean $0$, variance $2$.
- **Pareto:** $f(x) = \alpha x_m^{\alpha}/x^{\alpha+1}$ for $x\ge x_m$; heavy-tailed, used for income, file size, insurance claims.
- **Logistic / extreme value / Gumbel:** appear in growth models, regression, max/min of samples.
- **Dirichlet:** multivariate generalization of Beta on the simplex.

### Summary Table: Continuous Distributions

| Distribution | pdf $f(x)$ | Mean | Variance |
|---|---|---|---|
| Uniform($\alpha,\beta$) | $1/(\beta-\alpha)$ on $(\alpha,\beta)$ | $(\alpha+\beta)/2$ | $(\beta-\alpha)^2/12$ |
| Normal($\mu,\sigma^2$) | $\frac{1}{\sigma\sqrt{2\pi}}e^{-(x-\mu)^2/2\sigma^2}$ | $\mu$ | $\sigma^2$ |
| Log-Normal($\alpha,\beta^2$) | $\frac{1}{x\beta\sqrt{2\pi}}e^{-(\ln x-\alpha)^2/2\beta^2}$ | $e^{\alpha+\beta^2/2}$ | $e^{2\alpha+\beta^2}(e^{\beta^2}-1)$ |
| Exponential($\beta$) | $\frac{1}{\beta}e^{-x/\beta}$ for $x>0$ | $\beta$ | $\beta^2$ |
| Gamma($\alpha,\beta$) | $\frac{x^{\alpha-1}e^{-x/\beta}}{\beta^\alpha\Gamma(\alpha)}$ | $\alpha\beta$ | $\alpha\beta^2$ |
| Beta($\alpha,\beta$) | $\frac{\Gamma(\alpha+\beta)}{\Gamma(\alpha)\Gamma(\beta)}x^{\alpha-1}(1-x)^{\beta-1}$ on $(0,1)$ | $\alpha/(\alpha+\beta)$ | $\alpha\beta/[(\alpha+\beta)^2(\alpha+\beta+1)]$ |
| Weibull($\alpha,\beta$) | $\alpha\beta x^{\beta-1}e^{-\alpha x^\beta}$ | $\alpha^{-1/\beta}\Gamma(1+1/\beta)$ | $\alpha^{-2/\beta}[\Gamma(1+2/\beta)-\Gamma(1+1/\beta)^2]$ |
| $\chi^2_k$ | $\frac{x^{k/2-1}e^{-x/2}}{2^{k/2}\Gamma(k/2)}$ | $k$ | $2k$ |
| $t_\nu$ | $\propto(1+x^2/\nu)^{-(\nu+1)/2}$ | $0$ ($\nu>1$) | $\nu/(\nu-2)$ ($\nu>2$) |
| F($d_1,d_2$) | see above | $d_2/(d_2-2)$ | see above |

---

## Expectation, Variance, and Moments

### Mean (Expected Value)

For a discrete random variable: $\mu = E(X) = \sum_x x\,f(x)$.

For a continuous random variable: $\mu = E(X) = \int_{-\infty}^{\infty} x\,f(x)\,dx$.

The mean is the long-run average value; in physics, the center of gravity of the probability mass.

### Variance and Standard Deviation

$$\sigma^2 = \text{Var}(X) = E\!\left[(X-\mu)^2\right].$$
**Computing (shortcut) formula:** $\sigma^2 = E(X^2) - \mu^2$.

**Discrete:** $\sigma^2 = \sum_x (x-\mu)^2 f(x)$. **Continuous:** $\sigma^2 = \int (x-\mu)^2 f(x)\,dx$.

**Standard deviation:** $\sigma = \sqrt{\sigma^2}$, in the same units as $X$.

### Higher Moments

- **$k$-th moment about the origin:** $\mu'_k = E(X^k) = \sum_x x^k f(x)$ (integral in the continuous case).
- **$k$-th moment about the mean:** $\mu_k = E[(X-\mu)^k]$.
- **Skewness:** $\mu_3/\sigma^3$ (positive skew $\Rightarrow$ long right tail; negative skew $\Rightarrow$ long left tail).
- **Kurtosis:** $\mu_4/\sigma^4$ (peakedness/tail weight).
- **Variance relation:** $\sigma^2 = \mu'_2 - \mu^2$.

### Moment Generating Function

$$M(t) = E(e^{tX}) = \sum_x e^{tx} f(x) \quad \text{(discrete)}, \qquad M(t) = \int_{-\infty}^{\infty} e^{tx} f(x)\,dx \quad \text{(continuous)}.$$

If $M$ exists in a neighborhood of $0$, then $E(X^k) = M^{(k)}(0)$.

**Key facts:**
- $M_X(t)$ uniquely determines the distribution of $X$.
- For independent $X, Y$: $M_{X+Y}(t) = M_X(t) M_Y(t)$.
- The mgf of a sum of i.i.d. random variables yields the distribution of the sum.

### Expectation Rules

For constants $a, b$ and random variable $X$:
- $E(aX + b) = a E(X) + b$.
- $\text{Var}(aX + b) = a^2 \text{Var}(X)$.
- $E(X+Y) = E(X) + E(Y)$ (linearity, no independence needed).
- $\text{Var}(X+Y) = \text{Var}(X) + \text{Var}(Y) + 2\,\text{Cov}(X,Y)$; if $X, Y$ independent, the covariance term is $0$.

---

## Joint, Marginal, and Conditional Distributions

### Discrete Case

The **joint pmf** of two discrete random variables $X_1, X_2$ is $f(x_1, x_2) = P(X_1 = x_1, X_2 = x_2)$. The **marginal** of $X_1$ is
$$f_1(x_1) = \sum_{x_2} f(x_1, x_2).$$
The **conditional pmf** of $X_1$ given $X_2 = x_2$ is
$$f_1(x_1 \mid x_2) = \frac{f(x_1, x_2)}{f_2(x_2)}, \quad f_2(x_2) > 0.$$

**Independence:** $X_1, X_2$ are independent iff $f(x_1, x_2) = f_1(x_1) f_2(x_2)$ for all $(x_1, x_2)$ (equivalently, $f_1(x_1\mid x_2) = f_1(x_1)$).

For $k$ random variables, the joint pmf is $f(x_1, \ldots, x_k)$, and the marginal of the $i$-th variable is obtained by summing over all other coordinates.

### Continuous Case

The **joint pdf** $f(x_1, \ldots, x_k)$ satisfies $f\ge 0$ and
$$\int_{-\infty}^{\infty}\!\!\cdots\int_{-\infty}^{\infty} f(x_1,\ldots,x_k)\,dx_1\cdots dx_k = 1.$$
Probabilities over rectangular regions are obtained by multiple integration. The **joint cdf** is
$$F(x_1,\ldots,x_k) = P(X_1\le x_1, \ldots, X_k \le x_k),$$
with $f = \dfrac{\partial^k F}{\partial x_1\cdots\partial x_k}$.

**Marginal:** $f_1(x_1) = \int \cdots \int f(x_1,\ldots,x_k)\,dx_2\cdots dx_k$.

**Conditional density:** $f(x_1, x_2) = f_1(x_1)\, f(x_2 \mid x_1)$, with $f(x_2\mid x_1) = f(x_1,x_2)/f_1(x_1)$.

**Independence:** $f(x_1, \ldots, x_k) = f_1(x_1)\cdots f_k(x_k)$ iff the variables are independent.

### Covariance and Correlation

$$\text{Cov}(X, Y) = E[(X-\mu_X)(Y-\mu_Y)] = E(XY) - \mu_X\mu_Y,$$
$$\rho(X,Y) = \frac{\text{Cov}(X,Y)}{\sigma_X \sigma_Y} \in [-1, 1].$$
Independent $\Rightarrow$ $\text{Cov}=0$, but not conversely. $\rho = \pm 1$ iff $X$ and $Y$ are perfectly linearly related.

---

## Inequalities and Approximations

### Chebyshev's Theorem

**Theorem.** If a random variable $X$ has mean $\mu$ and standard deviation $\sigma$, then for any $k>0$,
$$P(|X-\mu| \ge k\sigma) \le \frac{1}{k^2}, \quad \text{equivalently} \quad P(|X-\mu| < k\sigma) \ge 1 - \frac{1}{k^2}.$$
**When to use:** distribution-free bound on tail probability; works for any distribution with finite variance. **Caveat:** the bound is loose for specific families (e.g., the normal).

### Law of Large Numbers

**Theorem.** As $n\to\infty$, the sample mean $\bar X_n = (X_1 + \cdots + X_n)/n$ converges in probability to $E(X)$ for i.i.d. observations with finite mean. **Consequence:** the sample proportion converges to the success probability. **Use:** empirical frequencies stabilize in the long run.

### Normal Approximation to the Binomial

If $X \sim \text{Binomial}(n, p)$, then for large $n$, $X$ is approximately $N(np, np(1-p))$. **Standardization:**
$$Z = \frac{X - np}{\sqrt{np(1-p)}} \;\dot\sim\; N(0,1).$$

**Rule of thumb:** use the approximation only when $np > 15$ **and** $n(1-p) > 15$. **Continuity correction:** approximate $P(a \le X \le b)$ for integer $a, b$ by $P(a - 1/2 < Y < b + 1/2)$ where $Y \sim N(np, np(1-p))$.

### Poisson Approximation to the Binomial

When $n$ is large and $p$ is small, $\text{Binomial}(n, p) \approx \text{Poisson}(\lambda)$ with $\lambda = np$. **Rule of thumb:** $n \ge 20$ and $p \le 0.05$; excellent when $n \ge 100$ and $np \le 10$.

### Other Useful Approximations

- **Poisson to normal:** when $\lambda$ is large, $\text{Poisson}(\lambda) \approx N(\lambda, \lambda)$.
- **Binomial to Poisson (alternative form):** sample without replacement from a large batch behaves like binomial with $p = a/N$.

---

## Transformations of Random Variables

### Linear Transformation

If $Y = aX + b$ with $a\ne 0$:
$$f_Y(y) = \frac{1}{|a|} f_X\!\left(\frac{y-b}{a}\right), \quad E(Y) = aE(X) + b, \quad \text{Var}(Y) = a^2 \text{Var}(X).$$

### General Monotone Transformation

If $Y = g(X)$ with $g$ strictly monotone, then
$$f_Y(y) = f_X(g^{-1}(y))\,\left|\frac{d}{dy}g^{-1}(y)\right|.$$

### Sums of Independent Random Variables (Convolution)

If $X, Y$ are independent, the cdf of $Z = X+Y$ is $F_Z(z) = \int F_X(z-y)\,f_Y(y)\,dy$; equivalently, the mgf is $M_Z(t) = M_X(t) M_Y(t)$.

| Sum | Distribution |
|---|---|
| $n$ i.i.d. Bernoulli($p$) | Binomial($n, p$) |
| Sum of $n$ i.i.d. Exp($\beta$) | Gamma($n, \beta$) |
| $n$ i.i.d. $N(\mu, \sigma^2)$ | $N(n\mu, n\sigma^2)$ |
| $\chi^2_a + \chi^2_b$ (independent) | $\chi^2_{a+b}$ |
| Binomial($n_1,p$) + Binomial($n_2,p$) (independent) | Binomial($n_1+n_2, p$) |
| $a \chi^2_d$ | Gamma($d/2, 2a$) |

---

## Special Processes and Models

### Bernoulli Trials

Four conditions for a sequence of trials to qualify as Bernoulli trials:
1. Each trial has exactly two outcomes (success/failure).
2. The success probability $p$ is the same for every trial.
3. Outcomes on different trials are independent.
4. (For binomial) the number of trials $n$ is fixed in advance.

A violation of (2) or (3) rules out the binomial distribution. If (3) fails (e.g., sampling without replacement from a small batch), use the hypergeometric.

### Poisson Processes

A random process producing events in continuous time (or space) is a **Poisson process with rate $\alpha > 0$** if:
- The number of events in any interval of length $T$ is $\text{Poisson}(\lambda)$ with $\lambda = \alpha T$.
- The numbers of events in disjoint intervals are independent.
- At most one event occurs in any sufficiently small interval.

Consequences:
- **Interarrival times** are i.i.d. Exponential with mean $1/\alpha$.
- **Time of the $r$-th event** is Gamma($r, 1/\alpha$).
- **Conditional on a count** $N(t) = n$, the $n$ event times are i.i.d. Uniform on $[0, t]$.

### Simulation and Monte Carlo Methods

To generate samples from a discrete distribution, use the **inverse cdf method**: partition $(0,1)$ into intervals whose lengths equal the probabilities, and assign each uniform $U\in(0,1)$ to the value whose interval contains $U$. Random number tables and software-generated pseudo-random numbers (uniform on $\{0,1,\ldots,9\}$ or $(0,1)$) drive this. To simulate a random variable with given pmf $f$:
- Compute cumulative probabilities $F(x_i)$.
- Assign ranges of random numbers in proportion to $F(x_i) - F(x_{i-1})$.

**Buffon's needle** (classic Monte Carlo): probability that a needle of length $a$ crosses one of parallel lines spaced $b$ apart is $2a/(\pi b)$, enabling probabilistic estimation of $\pi$.

---

## Distribution Selection Guide

| Setting | Distribution |
|---|---|
| Counts of successes in $n$ independent trials | Binomial($n, p$) |
| Counts of successes in $n$ draws without replacement | Hypergeometric($N, a, n$) |
| Counts of rare events per unit time/space | Poisson($\lambda$) |
| Number of trials until first success | Geometric($p$) |
| Number of trials until $r$-th success | Negative-Binomial($r, p$) |
| Single success/failure trial | Bernoulli($p$) |
| Equally likely over an interval | Uniform($\alpha, \beta$) |
| Bell-shaped, symmetric, mean-centered data | Normal($\mu, \sigma^2$) |
| Right-skewed positive values, multiplicative effects | Log-Normal |
| Lifetimes, waiting times, constant hazard | Exponential |
| Sum of exponentials, general right skew | Gamma |
| Proportion on $(0,1)$, Bayesian prior for $p$ | Beta |
| Reliability, flexible failure rate | Weibull |
| Sample variance, sums of squares | $\chi^2_k$ |
| Mean with estimated variance, small $n$ | $t_\nu$ |
| Ratio of variances, ANOVA, $F$-tests | F($d_1, d_2$) |
| Classification into $k$ categories | Multinomial |

---

## Common Pitfalls and Caveats

- **Binomial requires four conditions**; check independence, equal $p$, and fixed $n$ before applying. A counterexample: sampling without replacement from a small batch needs the hypergeometric.
- **Hypergeometric vs. binomial:** use the hypergeometric when sampling without replacement; approximate with binomial only when $n \le N/10$.
- **Poisson requires rare-event structure**, not just small $p$; verify that the event rate is constant and intervals are independent.
- **Normal approximation to the binomial** is poor when $p$ is near $0$ or $1$; use the Poisson approximation instead.
- **Continuity correction** improves the normal approximation to a discrete count; replace $k$ with the interval $(k-1/2, k+1/2)$.
- **Log-normal mean** is not $e^{\mu}$ where $\mu$ is the mean of $\ln X$; it is $e^{\alpha + \beta^2/2}$.
- **Exponential memorylessness** is unique to the exponential among continuous distributions on $[0,\infty)$.
- **Chebyshev's bound** is universal but typically loose; use exact distributions or sharper bounds (Cantelli, Chernoff) when available.
- **Density values are not probabilities**; $f(x)$ can exceed 1 for a continuous distribution. Only $\int f = $ probability over a region.
- **Independent variables have zero covariance, but the converse fails**: zero covariance does not imply independence.
- **mgf may not exist** (e.g., $t$ distribution, log-normal tail behavior); check before using mgf methods.
- **Law of large numbers** is a statement about convergence, not a guarantee for any specific sample.
- **Sample mean = population mean is rarely true in practice**; LLN describes the long-run tendency.
