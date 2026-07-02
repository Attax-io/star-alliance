---
type: Document
timestamp: 2026-07-02T12:28:13Z
---

# Random Variables and Probability Distributions

A random variable is a numerical quantity whose value is determined by the outcome of a random experiment; its distribution captures all probabilities associated with that value. Probability distributions come in two principal forms — discrete (governed by a probability mass function on a countable set) and absolutely continuous (governed by a probability density function) — and every distribution can be summarized by a cumulative distribution function (cdf) that uniquely determines it. This reference covers the formal foundations, the major named families, the cdf machinery, conditional and joint structures, and the simulation algorithms used to draw samples from these distributions.

---

## 1. Random Variables

### 1.1 Definition

A **random variable** $X$ on a sample space $\Omega$ is a function $X : \Omega \to \mathbb{R}$. The value $X(\omega)$ is called a *realization* of $X$. Random variables are written in uppercase ($X, Y, Z$); realizations in lowercase ($x, y, z$).

For any Borel set $S \subseteq \mathbb{R}$,
$$P(X \in S) = P(\{\omega : X(\omega) \in S\}).$$

Every Borel-set event $\{X \in S\}$ is well-defined provided $S$ lies in the Borel $\sigma$-algebra (the smallest $\sigma$-algebra on $\mathbb{R}$ containing all open intervals). Any set constructible from countable unions/intersections/complements of intervals is Borel.

### 1.2 Special Types

- **Constant random variable**: $X(\omega) = c$ for all $\omega$. Notation: $X = c$.
- **Indicator function** $\mathbf{1}_A$ of an event $A$:
$$\mathbf{1}_A(\omega) = \begin{cases} 1 & \omega \in A \\ 0 & \omega \notin A. \end{cases}$$
This is always a Bernoulli random variable with parameter $P(A)$.

### 1.3 Operations

For random variables $X, Y$ and outcome $\omega$, define $(X+Y)(\omega) = X(\omega) + Y(\omega)$, $(XY)(\omega) = X(\omega)Y(\omega)$, and so on. Any measurable function $g : \mathbb{R} \to \mathbb{R}$ produces a new random variable $g(X)$.

---

## 2. The Distribution of a Random Variable

### 2.1 Definition

The **distribution** of $X$ is the collection $\{P(X \in B) : B \subseteq \mathbb{R}, B \text{ Borel}\}$. Knowledge of this collection is equivalent to knowledge of the underlying probability model restricted to $X$.

### 2.2 Computing Probabilities of Events

For $B \subseteq \mathbb{R}$,
$$P(X \in B) = P(\{s \in S : X(s) \in B\}).$$

---

## 3. Discrete Random Variables

### 3.1 Definition

$X$ is **discrete** if its entire probability mass concentrates on a countable set:
$$\sum_{x \in \mathbb{R}} P(X = x) = 1.$$
Equivalently, $X$ takes values in a finite or countably infinite set $\{x_1, x_2, \ldots\}$ with $p_i = P(X = x_i) \ge 0$ and $\sum_i p_i = 1$.

### 3.2 Probability Mass Function (pmf)

The **probability mass function** is $p_X(x) = P(X = x)$, satisfying:
- $p_X(x) \ge 0$ for all $x$
- $\sum_x p_X(x) = 1$

For any set $S$,
$$P(X \in S) = \sum_{x \in S} p_X(x).$$

### 3.3 Law of Total Probability (discrete form)

For any event $A$,
$$P(A) = \sum_{x \in \mathbb{R}} P(X = x)\, P(A \mid X = x).$$

### 3.4 Important Discrete Distributions

| Name | Notation | pmf $p_X(x)$ | Support | Mean | Variance | When to use |
|------|----------|--------------|---------|------|----------|-------------|
| Degenerate | $X = c$ | $1$ at $x=c$, else $0$ | $\{c\}$ | $c$ | $0$ | Modeling a known constant |
| Bernoulli$(p)$ | $\text{Bernoulli}(p)$ | $p^x (1-p)^{1-x}$ | $\{0,1\}$ | $p$ | $p(1-p)$ | One binary trial |
| Binomial$(n,p)$ | $\text{Bin}(n,p)$ | $\binom{n}{x} p^x (1-p)^{n-x}$ | $\{0,\ldots,n\}$ | $np$ | $np(1-p)$ | Number of successes in $n$ i.i.d. Bernoulli trials |
| Geometric$(p)$ (count of failures) | $\text{Geom}(p)$ | $(1-p)^k p$ | $\{0,1,2,\ldots\}$ | $\frac{1-p}{p}$ | $\frac{1-p}{p^2}$ | Failures before first success |
| Geometric$(p)$ (count of trials) | $\text{Geom}(p)$ | $(1-p)^{k-1} p$ | $\{1,2,\ldots\}$ | $1/p$ | $(1-p)/p^2$ | Trials up to and including first success |
| Negative-Binomial$(r,p)$ | $\text{NegBin}(r,p)$ | $\binom{r+k-1}{k} p^r (1-p)^k$ | $\{0,1,2,\ldots\}$ | $\frac{r(1-p)}{p}$ | $\frac{r(1-p)}{p^2}$ | Failures before $r$-th success |
| Poisson$(\lambda)$ | $\text{Poi}(\lambda)$ | $\dfrac{\lambda^x e^{-\lambda}}{x!}$ | $\{0,1,2,\ldots\}$ | $\lambda$ | $\lambda$ | Counts of rare independent events |
| Hypergeometric$(N,M,n)$ | $\text{Hyp}(N,M,n)$ | $\dfrac{\binom{M}{x}\binom{N-M}{n-x}}{\binom{N}{n}}$ | $\{\max(0,n-N+M), \ldots, \min(n,M)\}$ | $\frac{nM}{N}$ | $\frac{nM(N-M)(N-n)}{N^2(N-1)}$ | Sampling without replacement |
| Multinomial$(n, p_1,\ldots,p_k)$ | $\text{Mult}(n,\vec p)$ | $\frac{n!}{x_1!\cdots x_k!}\prod p_i^{x_i}$ | $\sum x_i = n$ | $n p_i$ | $n p_i(1-p_i)$ | Categorical counts in $n$ trials |

### 3.5 Key Properties and Approximations

- **Binomial sum of Bernoullis**: If $X_1, \ldots, X_n$ are i.i.d. $\text{Bernoulli}(p)$, then $Y = \sum X_i \sim \text{Bin}(n,p)$.
- **Binomial sum**: If $X \sim \text{Bin}(n_1, p)$ and $Y \sim \text{Bin}(n_2, p)$ independent, then $X+Y \sim \text{Bin}(n_1+n_2, p)$.
- **Negative-Binomial sum**: If $X \sim \text{NegBin}(r_1, p)$ and $Y \sim \text{NegBin}(r_2, p)$ independent, then $X+Y \sim \text{NegBin}(r_1+r_2, p)$.
- **Poisson limit (Law of Rare Events)**: If $X \sim \text{Bin}(n, p_n)$ with $n p_n \to \lambda$, then for each fixed $x$,
$$\lim_{n\to\infty} P(X = x) = \frac{\lambda^x e^{-\lambda}}{x!}.$$
Use Poisson$(\lambda = np)$ as an approximation when $n \ge 20$ and $p \le 0.05$ (or $n \ge 100$ and $np \le 10$).
- **Hypergeometric vs Binomial**: With-replacement sampling from $N$ objects with $M$ "successes" gives Binomial$(n, M/N)$; without-replacement gives Hypergeometric$(N,M,n)$. The two are close when $n \ll N$.
- **Memoryless property (Geometric)**: $P(X > k_0 + k \mid X > k_0) = P(X > k)$; equivalently, the conditional distribution of $X - k_0$ given $X > k_0$ is again $\text{Geom}(p)$.

### 3.6 Motive for the Poisson Distribution

If we flip $n$ coins, each with tiny head probability $p_n = \lambda/n$, and let $n \to \infty$ with $n p_n = \lambda$ fixed, the count of heads converges in distribution to $\text{Poi}(\lambda)$. This is the standard derivation; the limit identity $\lim_{n \to \infty}(1-\lambda/n)^n = e^{-\lambda}$ and $\frac{n!}{(n-k)!(n-\lambda)^k} \to 1$ together yield the pmf.

---

## 4. Continuous Random Variables

### 4.1 Definition

$X$ is **continuous** if $P(X = x) = 0$ for every $x \in \mathbb{R}$. $X$ is **absolutely continuous** if there exists a non-negative integrable function $f_X$ (a **density**) with
$$\int_{-\infty}^{\infty} f_X(x)\,dx = 1, \qquad P(a \le X \le b) = \int_a^b f_X(x)\,dx.$$
Every absolutely continuous random variable is continuous; the converse fails (singular continuous measures exist but are not needed in standard practice).

### 4.2 Properties of a Density

- $f_X(x) \ge 0$ everywhere.
- $\int f_X(x)\,dx = 1$ (total probability).
- For small $\Delta$, $P(X \in [a, a+\Delta]) \approx f_X(a)\Delta$ (local probability per unit length).
- Densities are not unique: changing $f$ on a finite (or measure-zero) set yields the same distribution. The "best" version is the one that is continuous/piecewise-continuous.

### 4.3 Important Absolutely Continuous Distributions

| Name | Notation | pdf $f_X(x)$ | Support | Mean | Variance | When to use |
|------|----------|--------------|---------|------|----------|-------------|
| Uniform$[a,b]$ | $U[a,b]$ | $\frac{1}{b-a}$ on $[a,b]$ | $[a,b]$ | $\frac{a+b}{2}$ | $\frac{(b-a)^2}{12}$ | Equal likelihood over an interval |
| Exponential$(\lambda)$ | $\text{Exp}(\lambda)$ | $\lambda e^{-\lambda x}$ | $x \ge 0$ | $1/\lambda$ | $1/\lambda^2$ | Waiting time to a memoryless event |
| Gamma$(\alpha,\lambda)$ | $\text{Gamma}(\alpha,\lambda)$ | $\frac{\lambda^\alpha}{\Gamma(\alpha)} x^{\alpha-1} e^{-\lambda x}$ | $x > 0$ | $\alpha/\lambda$ | $\alpha/\lambda^2$ | Sum of $\alpha$ i.i.d. exponentials (if $\alpha$ integer) |
| Normal$(\mu,\sigma^2)$ | $N(\mu,\sigma^2)$ | $\frac{1}{\sigma\sqrt{2\pi}} e^{-(x-\mu)^2/(2\sigma^2)}$ | $\mathbb{R}$ | $\mu$ | $\sigma^2$ | Bell-shaped, sums of many i.i.d. variables (CLT) |
| Standard Normal | $N(0,1)$ | $\phi(x) = \frac{1}{\sqrt{2\pi}} e^{-x^2/2}$ | $\mathbb{R}$ | $0$ | $1$ | Standardized reference; use $\Phi$ for cdf |
| Beta$(a,b)$ | $\text{Beta}(a,b)$ | $\frac{x^{a-1}(1-x)^{b-1}}{B(a,b)}$, $B(a,b)=\frac{\Gamma(a)\Gamma(b)}{\Gamma(a+b)}$ | $(0,1)$ | $\frac{a}{a+b}$ | $\frac{ab}{(a+b)^2(a+b+1)}$ | Probabilities, proportions |
| Logistic | $\text{Logistic}$ | $\frac{e^{-x}}{(1+e^{-x})^2}$ | $\mathbb{R}$ | $0$ | $\pi^2/3$ | Symmetric heavy-tail alternative to Normal |
| Weibull$(\lambda, k)$ | $\text{Weib}$ | $k\lambda(\lambda x)^{k-1}e^{-(\lambda x)^k}$ | $x \ge 0$ | varies | varies | Reliability/lifetime modeling |
| Pareto$(\alpha)$ | $\text{Pareto}(\alpha)$ | $\alpha / x^{\alpha+1}$ | $x \ge 1$ | $\alpha/(\alpha-1)$ ($\alpha>1$) | $\alpha/((\alpha-1)^2(\alpha-2))$ ($\alpha>2$) | Heavy-tailed incomes, file sizes |
| Cauchy | $\text{Cauchy}$ | $\frac{1}{\pi(1+x^2)}$ | $\mathbb{R}$ | undefined | undefined | Ratio of i.i.d. standard normals |
| Laplace$(\mu,b)$ | $\text{Laplace}$ | $\frac{1}{2b}e^{-|x-\mu|/b}$ | $\mathbb{R}$ | $\mu$ | $2b^2$ | Double-exponential tails |

### 4.4 Gamma Function

$$\Gamma(\alpha) = \int_0^\infty t^{\alpha-1} e^{-t}\,dt, \quad \alpha > 0.$$
Key identities: $\Gamma(1)=1$, $\Gamma(1/2)=\sqrt{\pi}$, $\Gamma(\alpha+1) = \alpha \Gamma(\alpha)$, $\Gamma(n) = (n-1)!$ for positive integer $n$.

### 4.5 The Exponential Distribution and Memorylessness

For $X \sim \text{Exp}(\lambda)$: $P(X > t) = e^{-\lambda t}$, $P(a \le X \le b) = e^{-\lambda a} - e^{-\lambda b}$.

**Memoryless property**: For $s, t > 0$,
$$P(X > s + t \mid X > s) = P(X > t), \quad \text{equivalently} \quad P(X - s > t \mid X > s) = P(X > t).$$
Conditional on $X > s$, the residual $X - s$ is again $\text{Exp}(\lambda)$. The only continuous memoryless distribution on $[0,\infty)$ is Exponential; the only discrete memoryless distribution on $\{0,1,\ldots\}$ is Geometric.

### 4.6 The Normal Distribution

If $X \sim N(\mu, \sigma^2)$, then $Z = (X-\mu)/\sigma \sim N(0,1)$ (standardization). For any $a \le b$,
$$P(a \le X \le b) = \Phi\!\left(\frac{b-\mu}{\sigma}\right) - \Phi\!\left(\frac{a-\mu}{\sigma}\right),$$
where $\Phi$ is the cdf of the standard normal. Numerical values are obtained from tables or software; no closed form exists.

---

## 5. Cumulative Distribution Functions

### 5.1 Definition

The **cumulative distribution function (cdf)** of $X$ is
$$F_X(x) = P(X \le x), \quad x \in \mathbb{R}.$$
Notation: $F$ when context is clear.

### 5.2 Properties (any cdf)

- $0 \le F(x) \le 1$ for all $x$.
- $F$ is non-decreasing: $x \le y \Rightarrow F(x) \le F(y)$.
- $F$ is right-continuous.
- $\lim_{x \to -\infty} F(x) = 0$ and $\lim_{x \to \infty} F(x) = 1$.

Conversely, any function satisfying these conditions is the cdf of some random variable.

### 5.3 Recovering Event Probabilities from the cdf

| Event | Formula |
|-------|---------|
| $P(a < X \le b)$ | $F(b) - F(a)$ |
| $P(a \le X \le b)$ | $F(b) - F(a^-)$ |
| $P(a < X < b)$ | $F(b^-) - F(a)$ |
| $P(a \le X < b)$ | $F(b^-) - F(a^-)$ |
| $P(X = a)$ | $F(a) - F(a^-)$ |

For continuous $X$, $F(a^-) = F(a)$, so all four interval formulas give the same answer. For absolutely continuous $X$, the pdf is $f_X(x) = \frac{d}{dx} F_X(x)$ a.e., and $F_X(x) = \int_{-\infty}^x f_X(t)\,dt$.

### 5.4 Cdf of a Discrete Random Variable

If $X$ takes values $x_1 < x_2 < \cdots$ with $P(X = x_i) = p_i$, then
$$F(x) = \sum_{x_i \le x} p_i.$$
$F$ is a step function with jump of size $p_i$ at $x_i$, right-continuous.

### 5.5 Standard Normal cdf

$$\Phi(x) = \int_{-\infty}^x \frac{1}{\sqrt{2\pi}} e^{-t^2/2}\,dt,$$
with $\Phi(0) = 1/2$, $\Phi(-x) = 1 - \Phi(x)$, and $\lim_{x \to \infty}\Phi(x) = 1$. General normal probabilities are computed by standardization.

---

## 6. Mixture Distributions

### 6.1 Definition

If $F_1, \ldots, F_k$ are cdfs and $p_1, \ldots, p_k \ge 0$ with $\sum p_i = 1$, then
$$G(x) = \sum_{i=1}^k p_i F_i(x)$$
is a cdf. The distribution with cdf $G$ is a **(finite) mixture** with mixing weights $p_i$.

### 6.2 Generative Interpretation

A two-stage mechanism produces mixtures: first draw $Z$ with $P(Z=i) = p_i$, then draw $Y$ with conditional cdf $F_i$. The marginal cdf of $Y$ is $G$. Discrete location/scale mixtures shift or scale a base distribution $F$ by random parameters; continuous location mixtures integrate $F(x-y)$ against a mixing density $g(y)$:
$$H(x) = \int F(x - y)\, g(y)\,dy, \quad \int g(y)\,dy = 1.$$

### 6.3 Properties

- Mixtures of discrete distributions are discrete; mixtures of absolutely continuous distributions are absolutely continuous.
- A mixture can be **neither** discrete nor continuous when its components are mixed across types (e.g., $\tfrac{1}{5}F_{\text{Poi}} + \tfrac{4}{5}\Phi$), creating a cdf with both jumps and smooth parts. In this case, $P(X = y) = \tfrac{1}{5}P(\text{Poi} = y) \ne 0$ for the discrete part while $f_X(y) = \tfrac{4}{5}\phi(y)$ contributes continuous mass.

---

## 7. Conditioning on Events

### 7.1 Conditional pmf

For discrete $X$ and event $S$ with $P(X \in S) > 0$:
$$p_{X \mid X \in S}(x) = \begin{cases} \dfrac{p_X(x)}{\sum_{s \in S} p_X(s)}, & x \in S \\ 0, & x \notin S. \end{cases}$$

### 7.2 Conditional pdf

For continuous $X$ with pdf $f_X$ and event $S$ with $P(X \in S) > 0$:
$$f_{X \mid X \in S}(x) = \begin{cases} \dfrac{f_X(x)}{\int_S f_X(u)\,du}, & x \in S \\ 0, & x \notin S. \end{cases}$$

### 7.3 Memorylessness via Conditioning

For $\text{Geom}(p)$ on $\{0,1,\ldots\}$ and integer $k_0 \ge 0$:
$$P(X = k \mid X > k_0) = (1-p)^{k - k_0 - 1} p, \quad k > k_0,$$
which is again $\text{Geom}(p)$ shifted by $k_0$.

For $\text{Exp}(\lambda)$ and $t_0 > 0$:
$$F_{X \mid X > t_0}(t) = 1 - e^{-\lambda(t - t_0)}, \quad t \ge t_0,$$
which is again $\text{Exp}(\lambda)$ shifted by $t_0$.

---

## 8. Functions of Random Variables

### 8.1 Discrete Case

For $Y = g(X)$ with $X$ discrete:
$$p_Y(y) = \sum_{\{x : g(x) = y\}} p_X(x).$$

### 8.2 Continuous Case — Change of Variable

For $Y = g(X)$ with $X$ continuous, first compute the cdf:
$$F_Y(y) = P(g(X) \le y) = \int_{\{x : g(x) \le y\}} f_X(x)\,dx,$$
then differentiate to obtain $f_Y$ when differentiable.

### 8.3 Monotone Transformation Theorem

If $g$ is strictly monotone and differentiable on the support of $X$, and $Y = g(X)$, then
$$f_Y(y) = f_X(g^{-1}(y)) \left|\frac{d}{dy} g^{-1}(y)\right|.$$
Equivalent form: if $x = h(y)$ is the inverse, $f_Y(y) = f_X(h(y))\,|h'(y)|$.

### 8.4 Important Consequences

- **Standardization**: $X \sim N(\mu,\sigma^2) \Rightarrow Z = (X-\mu)/\sigma \sim N(0,1)$.
- **Log of Uniform**: If $U \sim U[0,1]$ then $-\log U / \lambda \sim \text{Exp}(\lambda)$ (since $F_X(x) = 1 - e^{-\lambda x}$ is the inverse-transform formula).
- **Sum of independent Gammas with common rate**: If $X_i \sim \text{Gamma}(\alpha_i, \lambda)$ independent, then $\sum X_i \sim \text{Gamma}(\sum \alpha_i, \lambda)$.

---

## 9. Multivariate (Joint) Random Variables

### 9.1 Joint pmf (Discrete)

For discrete $X, Y$ on ranges $R_X, R_Y$:
$$p_{X,Y}(x,y) = P(X = x, Y = y),$$
satisfying $p_{X,Y} \ge 0$ and $\sum_{x \in R_X}\sum_{y \in R_Y} p_{X,Y}(x,y) = 1$. For any set $S \subseteq R_X \times R_Y$,
$$P((X,Y) \in S) = \sum_{(x,y) \in S} p_{X,Y}(x,y).$$

### 9.2 Joint pdf (Continuous)

For continuous $(X,Y)$ with joint density $f_{X,Y}$:
$$P((X,Y) \in S) = \iint_S f_{X,Y}(x,y)\,dx\,dy,$$
with $f_{X,Y}(x,y) \ge 0$ and $\iint f_{X,Y} = 1$.

### 9.3 Marginalization

To obtain the marginal distribution of one variable, sum/integrate over the others:
$$p_X(x) = \sum_{y \in R_Y} p_{X,Y}(x,y), \qquad f_X(x) = \int f_{X,Y}(x,y)\,dy.$$
This generalizes: for any subset $I$ of a random vector $\vec X$,
$$p_{\vec X_I}(\vec x_I) = \sum_{\vec x_{J} : J = \{1,\ldots,n\}\setminus I} p_{\vec X}(\vec x).$$

### 9.4 Conditional Distributions

For discrete $X, Y$ with $p_X(x) > 0$:
$$p_{Y \mid X}(y \mid x) = \frac{p_{X,Y}(x,y)}{p_X(x)}.$$
For continuous $X, Y$ with $f_X(x) > 0$:
$$f_{Y \mid X}(y \mid x) = \frac{f_{X,Y}(x,y)}{f_X(x)}.$$

### 9.5 Chain Rule

$$p_{X,Y}(x,y) = p_X(x)\, p_{Y \mid X}(y \mid x) = p_Y(y)\, p_{X \mid Y}(x \mid y).$$
For vectors, in any order:
$$p_{\vec X}(\vec x) = \prod_{i=1}^n p_{X_i \mid \vec X_{1:i-1}}(x_i \mid \vec x_{1:i-1}).$$

### 9.6 Independence

$X$ and $Y$ are **independent** iff $p_{X,Y}(x,y) = p_X(x) p_Y(y)$ (discrete) or $f_{X,Y}(x,y) = f_X(x) f_Y(y)$ (continuous), equivalently $F_{X,Y}(x,y) = F_X(x) F_Y(y)$ for all $x,y$.

- **Conditional independence** of $A, B$ given $C$: $P(A \cap B \mid C) = P(A \mid C) P(B \mid C)$.
- Independence does **not** imply conditional independence, and vice versa; the relationship depends on whether the conditioning event screens off dependence or creates spurious correlation through mixing.

---

## 10. Independence (Events)

### 10.1 Definition

Events $A, B$ are independent iff $P(A \cap B) = P(A) P(B)$.

### 10.2 Equivalent Form

If $P(B) > 0$, $A \perp B$ iff $P(A \mid B) = P(A)$.

### 10.3 Mutual Independence

Events $A_1, \ldots, A_n$ are mutually independent iff for every sub-collection,
$$P\!\left(\bigcap_{i \in S} A_i\right) = \prod_{i \in S} P(A_i).$$
Pairwise independence alone is not sufficient.

### 10.4 Independence of Random Variables

A family $\{X_i\}$ is independent iff for all Borel sets $B_i$,
$$P(X_1 \in B_1, \ldots, X_n \in B_n) = \prod_i P(X_i \in B_i).$$

### 10.5 Common Pitfalls

- Independence $\ne$ mutual exclusivity. If $A, B$ are mutually exclusive with $P(A), P(B) > 0$, then $P(A \cap B) = 0 \ne P(A)P(B) > 0$, so they are dependent.
- Marginal independence does not imply joint independence (a Gaussian example) and vice versa.
- Conditional independence can reverse marginal dependence (simpson's-paradox-style mixing).

---

## 11. Generating Random Variables

### 11.1 Inverse-Transform Sampling (Continuous)

**Algorithm**: Given a continuous cdf $F_X$:
1. Sample $U \sim U[0,1]$.
2. Return $X = F_X^{-1}(U)$, where $F_X^{-1}(u) = \inf\{x : F_X(x) \ge u\}$ is the generalized inverse.

**Theorem**: The output $X$ has cdf $F_X$. Proof sketch: $P(F_X^{-1}(U) \le x) = P(U \le F_X(x)) = F_X(x)$.

**Example (Exponential)**: $F_X(x) = 1 - e^{-\lambda x}$ gives $F_X^{-1}(u) = -\log(1-u)/\lambda$. Using $1 - U \stackrel{d}{=} U$, can simplify to $-\log U/\lambda$.

### 11.2 Sampling from a Discrete Distribution

**Algorithm** (cdf partitioning): List values $x_1, x_2, \ldots$ with cumulative probabilities $F(x_i)$. Sample $U \sim U[0,1]$; return $x_i$ for the unique $i$ with $F(x_{i-1}) < U \le F(x_i)$.

### 11.3 Strategy

For any target distribution:
1. Sample $U \sim U[0,1]$ from a uniform RNG.
2. Apply a deterministic transformation (inverse cdf) to obtain a sample with the target distribution.

Uniform random number generation is itself a non-trivial problem (Mersenne Twister, etc.) but is assumed available.

---

## 12. Summary Tables of Key Identities

### 12.1 Cdf Identities

| Identity | Statement |
|----------|-----------|
| Range | $0 \le F(x) \le 1$ |
| Monotonicity | $x \le y \Rightarrow F(x) \le F(y)$ |
| Right continuity | $\lim_{y \downarrow x} F(y) = F(x)$ |
| Limits at infinity | $\lim_{x\to-\infty} F(x) = 0$, $\lim_{x\to\infty} F(x) = 1$ |
| Interval | $P(a < X \le b) = F(b) - F(a)$ |
| Point mass | $P(X = a) = F(a) - F(a^-)$ |
| Tail | $P(X > x) = 1 - F(x)$ |

### 12.2 Pdf/pmf Identities

| Identity | Discrete | Continuous |
|----------|----------|------------|
| Nonnegativity | $p(x) \ge 0$ | $f(x) \ge 0$ |
| Normalization | $\sum p(x) = 1$ | $\int f(x)\,dx = 1$ |
| From cdf | $p(x) = F(x) - F(x^-)$ | $f(x) = F'(x)$ a.e. |
| To cdf | $F(x) = \sum_{y \le x} p(y)$ | $F(x) = \int_{-\infty}^x f(t)\,dt$ |
| Event probability | $P(X \in S) = \sum_{x \in S} p(x)$ | $P(X \in S) = \int_S f(x)\,dx$ |

### 12.3 Convergence of Binomial to Poisson

For $X_n \sim \text{Bin}(n, \lambda/n)$ and fixed $x \in \{0, 1, 2, \ldots\}$:
$$\lim_{n \to \infty} P(X_n = x) = \frac{\lambda^x e^{-\lambda}}{x!}.$$
The convergence is fast when $n$ is large and $p = \lambda/n$ is small; in practice Poisson$(\lambda)$ is a good approximation to $\text{Bin}(n, p)$ when $n \ge 20, p \le 0.05$ (or $np \le 10$).

### 12.4 Gaussian Integration

The Gaussian integral evaluates to $\sqrt{\pi}$:
$$\int_{-\infty}^{\infty} e^{-t^2}\,dt = \sqrt{\pi}.$$
Proof: square the integral, change to polar coordinates, integrate radially. This establishes $\int \phi(x)\,dx = 1$ after the substitution $t = (x-\mu)/(\sigma\sqrt{2})$.

The full machinery of random variables — from the function-from-$\Omega$-to-$\mathbb{R}$ definition, through discrete and absolutely continuous distributions, to cdf manipulation, joint/conditional structures, and inverse-transform sampling — provides a unified language for representing uncertainty about numerical quantities and computing any probability expressible as a countable combination of events.
