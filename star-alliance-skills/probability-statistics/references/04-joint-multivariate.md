---
type: Document
timestamp: 2026-07-02T12:28:13Z
---

(x) =
c pY(x) / pX(x) accept with
probability min(1, c pY(x) accept with probability
probability min(1, c pY(x)/ pX(x))
accept with
pX(x)
reject
Figure 3 setting up the
in 2008 was a
textbook
example of
rejection
sampling: it
was tricky to
set up, and
3.7. Rejection sampling 65


+
-
-accept with
accept with
min( in the
min(1, c·pY(x)/pX(x))
accept with
in the
min(1, dsit
P(Accepted|X=x) = min( OCR/word-level
min(1, c·p target
extraction was
pY (x) / pX (
brittle
rejection
sampling:
it
was
tr
...
[Image: figure description truncated; the Miller & Freund text extracts cover Weibull distribution, joint distributions discrete/continuous, expectations of functions, covariance/linear combinations, mgf theory, mgf of standard distributions (binomial, Poisson, Miller & Freund text extracts cover We rejection sampling, and multivariate random variable generation. Weibull distribution, joint distributions discrete/accept with
min(1, c·pY(x)/p...

[Image: log probability vs iteration plot, showing a rejection sampling
[Image: log probability vs iteration plot, provided
[Image: log and request that you extract pure mathematical content, ignoring OCR artifacts. I've been given raw text from three probability/statistics textbooks covering topics: change of variable (1D and  user to provide only the pure mathematical/definitional/theoretical content extracted from the asks me to write a single dense Markdown reference file on the 多-dimensional), joint distributions, conditioning/independence/order statistics, simulation, expectation, mgf, covariance, correlation, Evans & Rosenthal style. single topic family. Based on the raw text, the topic family is: **Joint/Multivariate Random Variables — distributions, conditioning, independence, transformation, simulation, moment generating functions**.

The topic is joint/multivariate random variables and related concepts. Let me organize the

The user has provided:
1. Evans & Rosenthal text covering:
- Section 2.6: One-Dimensional Change of Variable (discrete and continuous cases)
   - Theorem 2.6.1 (discrete transformation)
   - Theorem 2. reject2.6.2, 2.6.3, 2.6.4 (continuous transformation)
   - Examples (Y=3X from Uniform, N(μ,σ²) from N(0,1), exponential from uniform, log-normal)
2. Section 2.7: Joint Distributions
   - joint cdf, joint pmf, joint density
   - marginal distributions (pmf and density)
   - Bivariate Normal distribution
3. Section 2.8: Conditioning and Independence
   - conditional pmf, conditional density
   - independence
   - i.i.d. sequences
   - Multinomial distribution
   - Order statistics
4. Section 2.9: Multidimensional Change of Variable
   - discrete case
   - continuous case with Jacobian
   - convolution
5. Section 2.2.10: Simulating Probability Distributions
   - uniform, Bernoulli, Binomial, Geometric, Exponential, Normal
   - inversion method
6. Section 2.11: Further Proofs (skipped)
7. Section 3.1: Discrete Expectation (begins, but is incomplete)
8. Miller & Freund text covering:
   - Weibull distribution (continuation)
   - Joint distributions (discrete and continuous)
   - Properties of expectation
   - Covariance
   - Mean and variance of linear combinations
   - Sample mean, sample variance
   - Moment generating functions
   - mgf of binomial, Poisson, gamma, chi-square, normal
9. Fernandez-Granda text covering:
   - Inverse-transform sampling details
   - Joint pmf for discrete multivariate
   - Joint cdf and pdf for continuous multivariate
   - Marginalization
   - Conditional distributions
   - Gaussian random vectors
   - Joint distributions of mixed discrete/continuous
   - Independence definitions
   - Graphical models
   - Functions of multiple random variables
   - Sampling multivariate distributions
   - Rejection sampling

This is a very broad topic. The single topic family is: "Joint and Multivariate Random Variables: distributions, dependence, conditioning, transformations, and simulation"

I'll structure the reference file with the following sections:

1. Introduction/Orientation
2. Joint Distributions (cdf, pmf, pdf, marginals)
3. Conditioning on Random Variables (discrete/continuous, mixed)
4. Independence
5. Multivariate Change of Variable (1D and 2D)
6. Specific Multivariate Distributions (Bivariate Normal, Gaussian vectors, Multinomial, Dirichlet)
7. Order Statistics
8. Convolution
9. Simulation of Distributions
10. Moment Generating Functions (related concept)
11. Expectation basics (briefly, since it's adjacent)
12. Covariance and Linear Combinations

Let me write this dense reference file.

I need to include:
- Joint cdf definition and properties
- Joint pmf for discrete
- Joint pdf for continuous
- Marginal distributions (extraction)
- Conditional distributions (both kinds)
- Independence (definitions, factorizations, key theorems)
- Bivariate Normal distribution
- Multinomial distribution
- Order statistics
- Convolution formula
- 1D change of variable (discrete and continuous)
- 2D change of variable (Jacobian)
- Mixed discrete-continuous joint distributions
- Simulation methods (inverse transform, decomposition, rejection)
- MGFs as a related tool for distributions
- Graphical models (briefly)
- Covariance properties (key results)
- Gaussian random vectors

Let me carefully construct this. I'll use clean math notation.

For the user, I want to keep this comprehensive but not overwhelming. Let me structure this.

The user message ends with some OCR artifacts that I should ignore. Let me just focus on writing the comprehensive reference.

I'll now write the file. Let me make it dense but well-organized.</mm:think># Joint and Multivariate Random Variables: Distributions, Dependence, Conditioning, Transformations, and Simulation

This reference covers the machinery needed to handle two or more random variables simultaneously: joint distributions, marginalization, conditioning, independence, transformations (one- and two-dimensional), simulation techniques, and moment generating functions. The treatment fuses the rigorous change-of-variable formalism, the applied joint-distribution work, and the data-science oriented treatment of multivariate sampling and graphical models into a unified, dense reference.

---

## 1. One-Dimensional Change of Variable

### 1.1 Discrete Case

**Theorem (Discrete change of variable).** Let $X$ be discrete with probability function $p_X$ and let $Y = h(X)$. Then $Y$ is discrete with probability function
$$
p_Y(y) = \sum_{x \in h^{-1}(y)} p_X(x),
$$
where $h^{-1}(y) = \{x : h(x) = y\}$.

### 1.2 Continuous Case

**Theorem (Continuous change of variable — strictly monotone).** Let $X$ be absolutely continuous with density $f_X$ and let $Y = h(X)$ where $h$ is differentiable and either strictly increasing or strictly decreasing on the support of $f_X$. Then $Y$ is absolutely continuous with density
$$
f_Y(y) = f_X\bigl(h^{-1}(y)\bigr)\,\bigl|\,h'(h^{-1}(y))\bigr|. \tag{1}
$$
The strict-monotonicity requirement can be relaxed: it suffices that $h$ be strictly increasing or decreasing on the set $\{x : f_X(x) > 0\}$.

**Examples / closed-form results.**
- $X \sim \text{Uniform}[0,1]$, $Y = RX + L \Rightarrow Y \sim \text{Uniform}[L, R]$.
- $X \sim N(\mu,\sigma^2)$, $Y = aX + b \Rightarrow Y \sim N(a\mu + b, a^2\sigma^2)$.
- $X \sim \text{Exponential}(\lambda)$, $Y = cX \Rightarrow Y \sim \text{Exponential}(\lambda/c)$.
- $X \sim N(0,\sigma^2)$, $Y = e^X \Rightarrow Y$ is **log-normal** with density
$$
f_Y(y) = \frac{1}{y\sqrt{2\pi}\,\sigma} \exp\!\left(-\frac{(\ln y)^2}{2\sigma^2}\right), \quad y > 0.
$$
- $X \sim \text{Uniform}[0,1]$, $Y = -\ln(1-X) \Rightarrow Y \sim \text{Exponential}(1)$.

If $X \sim N(0,1)$ and $Y = h(X)$ with $h$ neither monotone (e.g. $h(x) = x^2$), split by sign: $P(a \le Y \le b) = P(a \le X^2 \le b, X\ge 0) + P(a \le X^2 \le b, X < 0)$.

---

## 2. Joint Distributions of Two Random Variables

### 2.1 Joint CDF

For any random variables $X, Y$,
$$
F_{X,Y}(x,y) = P(X \le x, Y \le y).
$$
Properties: $F_{X,Y}$ is non-decreasing in each argument; $\lim_{x\to\infty} F_{X,Y}(x,y) = F_Y(y)$; $\lim_{y\to\infty} F_{X,Y}(x,y) = F_X(x)$; $\lim_{x,y\to -\infty} F_{X,Y} = 0$; $\lim_{x,y\to\infty} F_{X,Y} = 1$.

For a rectangle:
$$
P(a \le X \le b, c \le Y \le d) = F_{X,Y}(b,d) - F_{X,Y}(a,d) - F_{X,Y}(b,c) + F_{X,Y}(a,c).
$$

### 2.2 Joint PMF (Discrete)

$$
p_{X,Y}(x,y) = P(X=x, Y=y), \quad p_{X,Y}(x,y) \ge 0, \quad \sum_{x,y} p_{X,Y}(x,y) = 1.
$$

### 2.3 Joint PDF (Continuous)

$X, Y$ are **jointly absolutely continuous** with joint pdf $f_{X,Y}$ if $f_{X,Y}(x,y) \ge 0$, $\iint f_{X,Y} = 1$, and
$$
P((X,Y) \in B) = \iint_B f_{X,Y}(x,y)\,dx\,dy.
$$
Equivalently, for rectangles,
$$
P(a\le X \le b, c\le Y \le d) = \int_c^d\!\int_a^b f_{X,Y}(x,y)\,dx\,dy.
$$
When the joint cdf is differentiable, $f_{X,Y}(x,y) = \frac{\partial^2 F_{X,Y}}{\partial x\, \partial y}$.

### 2.4 Marginal Distributions

**From joint cdf.**
$$
F_X(x) = \lim_{y\to\infty} F_{X,Y}(x,y), \qquad F_Y(y) = \lim_{x\to\infty} F_{X,Y}(x,y).
$$

**From joint pmf.**
$$
p_X(x) = \sum_y p_{X,Y}(x,y), \qquad p_Y(y) = \sum_x p_{X,Y}(x,y).
$$

**From joint pdf.**
$$
f_X(x) = \int_{-\infty}^{\infty} f_{X,Y}(x,y)\,dy, \qquad f_Y(y) = \int_{-\infty}^{\infty} f_{X,Y}(x,y)\,dx.
$$
More generally, for a subset $\vec{X}_I$ of a vector $\vec{X}$,
$$
f_{\vec{X}_I}(\vec{x}_I) = \int\cdots\int f_{\vec{X}}(\vec{x})\,d\vec{x}_{\{1,\dots,n\}\setminus I}.
$$

### 2.5 The Bivariate Normal Distribution

For parameters $\mu_1, \mu_2 \in \mathbb{R}$, $\sigma_1, \sigma_2 > 0$, $\rho \in (-1,1)$, the bivariate normal $(X,Y) \sim N_2(\mu_1,\mu_2,\sigma_1,\sigma_2,\rho)$ has joint pdf
$$
f_{X,Y}(x,y) = \frac{1}{2\pi\sigma_1\sigma_2\sqrt{1-\rho^2}} \exp\!\left(-\frac{Q}{2(1-\rho^2)}\right),
$$
where
$$
Q = \frac{(x-\mu_1)^2}{\sigma_1^2} - 2\rho\frac{(x-\mu_1)(y-\mu_2)}{\sigma_1\sigma_2} + \frac{(y-\mu_2)^2}{\sigma_2^2}.
$$
Marginals: $X \sim N(\mu_1,\sigma_1^2)$, $Y \sim N(\mu_2,\sigma_2^2)$. Independence holds iff $\rho = 0$.

**Stochastic representation.** If $Z_1, Z_2 \overset{\text{iid}}{\sim} N(0,1)$, then
$$
X = \mu_1 + \sigma_1 Z_1, \qquad Y = \mu_2 + \sigma_2\bigl(\rho Z_1 + \sqrt{1-\rho^2}\,Z_2\bigr),
$$
has the bivariate normal law above.

---

## 3. Conditional Distributions

### 3.1 Conditioning on a Discrete Variable

For discrete $X, Y$ with $p_X(x) > 0$,
$$
p_{Y|X}(y|x) = \frac{p_{X,Y}(x,y)}{p_X(x)}.
$$
For events:
$$
P(a \le Y \le b \mid X = x) = \frac{P(a \le Y \le b, X = x)}{P(X=x)}.
$$

### 3.2 Conditioning on a Continuous Variable

For jointly absolutely continuous $X,Y$ with $f_X(x) > 0$, the **conditional density** of $Y$ given $X=x$ is
$$
f_{Y|X}(y|x) = \frac{f_{X,Y}(x,y)}{f_X(x)}. \tag{2}
$$
The conditional cdf is $F_{Y|X}(y|x) = \int_{-\infty}^y f_{Y|X}(u|x)\,du$. This is justified as the limit of $P(Y \le y \mid x \le X \le x+\Delta)$ as $\Delta \to 0$.

**Chain rule.**
$$
f_{X,Y}(x,y) = f_X(x)\,f_{Y|X}(y|x).
$$
For vectors, $f_{\vec{X}}(\vec{x}) = \prod_{i=1}^n f_{X_i|X_1,\dots,X_{i-1}}(x_i \mid x_1,\dots,x_{i-1})$ (order arbitrary).

### 3.3 Law of Total Probability (Continuous Form)
$$
P(a \le X \le b, c \le Y \le d) = \int_a^b \int_c^d f_X(x)\,f_{Y|X}(y|x)\,dy\,dx.
$$

### 3.4 Mixed Discrete–Continuous Joint Distributions

For continuous $C$ and discrete $D$:
- Conditional cdf/pdf of $C$ given $D=d$: $F_{C|D}(c|d) = P(C \le c \mid D=d)$; $f_{C|D}(c|d) = \partial F_{C|D}/\partial c$.
- Marginal: $f_C(c) = \sum_{d \in R_D} p_D(d)\,f_{C|D}(c|d)$.
- For continuous $C$, discrete $D$ (with $P(C=c)=0$): conditional pmf
$$
p_{D|C}(d|c) = \lim_{\Delta \to 0} \frac{P(D=d, c \le C \le c+\Delta)}{P(c \le C \le c+\Delta)}.
$$
- Marginal: $p_D(d) = \int_{-\infty}^{\infty} f_C(c)\,p_{D|C}(d|c)\,dc$.
- **Mixed chain rule:** $p_D(d)\,f_{C|D}(c|d) = f_C(c)\,p_{D|C}(d|c)$.

---

## 4. Independence of Random Variables

### 4.1 Definition

$X$ and $Y$ are **independent** if for all Borel sets $B_1, B_2 \subseteq \mathbb{R}$,
$$
P(X \in B_1,\, Y \in B_2) = P(X \in B_1)\,P(Y \in B_2).
$$
Equivalently, $F_{X,Y}(x,y) = F_X(x)\,F_Y(y)$ for all $x,y$.

### 4.2 Equivalent Factorizations

| Setting | Equivalent condition |
|---|---|
| Discrete | $p_{X,Y}(x,y) = p_X(x)\,p_Y(y)$ for all $x,y$ |
| Continuous | $f_{X,Y}(x,y) = f_X(x)\,f_Y(y)$ for all $x,y$ |
| Mixed | $P(X\le x, Y \le y) = F_X(x)\,F_Y(y)$ |

Independence also implies the conditional equals the marginal: $p_{Y|X}(y|x) = p_Y(y)$ or $f_{Y|X}(y|x) = f_Y(y)$.

### 4.3 Closure Under Functions

If $X, Y$ are independent, then $f(X)$ and $g(Y)$ are independent for any (measurable) functions $f, g$.

### 4.4 $n$-Variable and Vector Independence

$X_1,\dots,X_n$ are independent iff their joint cdf/pmf/pdf factors into a product of marginals:
$$
F_{\vec{X}}(\vec{x}) = \prod_{i=1}^n F_{X_i}(x_i), \quad p_{\vec{X}}(\vec{x}) = \prod_i p_{X_i}(x_i), \quad f_{\vec{X}}(\vec{x}) = \prod_i f_{X_i}(x_i).
$$
**Pitfall:** pairwise independence does **not** imply mutual independence (e.g. three indicator variables where $X_3$ is the indicator of $X_1 = X_2$).

### 4.5 Conditional Independence

$X$ and $Y$ are conditionally independent given $Z$ iff
$$
F_{X,Y|Z}(x,y \mid z) = F_{X|Z}(x\mid z)\,F_{Y|Z}(y \mid z)
$$
(or the equivalent pmf/pdf factorization) for all $z$ where the conditionals are well defined.

### 4.6 Gaussian Random Vectors

A **Gaussian random vector** $\vec{X} \in \mathbb{R}^n$ with mean $\vec{\mu} \in \mathbb{R}^n$ and symmetric positive-definite covariance $\Sigma$ has pdf
$$
f_{\vec{X}}(\vec{x}) = \frac{1}{\sqrt{(2\pi)^n |\Sigma|}} \exp\!\left(-\tfrac{1}{2}(\vec{x}-\vec{\mu})^T \Sigma^{-1} (\vec{x}-\vec{\mu})\right).
$$
**Closure under linear maps:** if $\vec{Y} = A\vec{X} + \vec{b}$, then $\vec{Y}$ is Gaussian with mean $A\vec{\mu} + \vec{b}$ and covariance $A\Sigma A^T$. **Marginals of Gaussian vectors are Gaussian** (apply the linear map extracting a subvector).

---

## 5. Multidimensional Change of Variable

### 5.1 Discrete Case

For discrete $(X,Y)$ and $(Z,W) = (h_1(X,Y), h_2(X,Y))$:
$$
p_{Z,W}(z,w) = \sum_{\{(x,y) : h_1(x,y)=z,\, h_2(x,y)=w\}} p_{X,Y}(x,y).
$$
If the joint map $h = (h_1,h_2)$ is one-to-one, then $p_{Z,W}(z,w) = p_{X,Y}(h^{-1}(z,w))$.

### 5.2 Continuous Case (Jacobian Formula)

Let $X, Y$ be jointly absolutely continuous with joint density $f_{X,Y}$. Suppose $Z = h_1(X,Y)$, $W = h_2(X,Y)$ where $h = (h_1,h_2) : \mathbb{R}^2 \to \mathbb{R}^2$ is differentiable and one-to-one on the support of $f_{X,Y}$. Then $(Z,W)$ is jointly absolutely continuous with
$$
f_{Z,W}(z,w) = f_{X,Y}\bigl(h^{-1}(z,w)\bigr)\,\bigl|\det J_h(h^{-1}(z,w))\bigr|,
$$
where the **Jacobian** is
$$
J_h(x,y) = \det\begin{pmatrix} \partial h_1/\partial x & \partial h_1/\partial y \\ \partial h_2/\partial x & \partial h_2/\partial y \end{pmatrix}.
$$

**Worked example (Box–Muller precursor).** If $U_1, U_2 \overset{\text{iid}}{\sim} \text{Uniform}[0,1]$ and
$$
X = \sqrt{-2\ln U_1}\cos(2\pi U_2), \quad Y = \sqrt{-2\ln U_1}\sin(2\pi U_2),
$$
then $X, Y \overset{\text{iid}}{\sim} N(0,1)$.

### 5.3 Convolution (Sum of Independent Random Variables)

Let $X, Y$ be independent. Then $Z = X+Y$ has:
- **Discrete:** $\displaystyle p_Z(z) = \sum_x p_X(x)\,p_Y(z-x) = (p_X * p_Y)(z)$.
- **Continuous:** $\displaystyle f_Z(z) = \int_{-\infty}^{\infty} f_X(x)\,f_Y(z-x)\,dx = (f_X * f_Y)(z)$.

**Standard additive-closure results.**

| $X$ | $Y$ (independent) | $X+Y$ |
|---|---|---|
| $\text{Bin}(n_1,p)$ | $\text{Bin}(n_2,p)$ | $\text{Bin}(n_1+n_2, p)$ |
| $\text{NegBin}(r_1, p)$ | $\text{NegBin}(r_2, p)$ | $\text{NegBin}(r_1+r_2, p)$ |
| $N(\mu_1,\sigma_1^2)$ | $N(\mu_2,\sigma_2^2)$ | $N(\mu_1+\mu_2,\sigma_1^2+\sigma_2^2)$ |
| $\text{Gamma}(\alpha_1,\beta)$ | $\text{Gamma}(\alpha_2,\beta)$ | $\text{Gamma}(\alpha_1+\alpha_2,\beta)$ |
| $\text{Exp}(\lambda)$ | $\text{Exp}(\lambda)$ | $\text{Gamma}(2, 1/\lambda)$ |

---

## 6. The Multinomial Distribution

If a response takes value $i \in \{1,\dots,k\}$ with probability $\theta_i$ ($\theta_i \ge 0$, $\sum \theta_i = 1$) and $n$ i.i.d. responses are observed, then the counts $(X_1,\dots,X_k)$ with $X_i = $ number of $i$'s satisfy
$$
(X_1,\dots,X_k) \sim \text{Multinomial}(n, \theta_1,\dots,\theta_k),
$$
$$
P(X_1=x_1,\dots,X_k=x_k) = \frac{n!}{x_1!\cdots x_k!}\,\theta_1^{x_1}\cdots\theta_k^{x_k}, \quad \sum_i x_i = n.
$$
**Marginals:** $X_i \sim \text{Binomial}(n, \theta_i)$. The multinomial reduces to binomial when $k=2$.

---

## 7. Order Statistics

For i.i.d. $X_1,\dots,X_n$ with cdf $F$ and pdf $f$, the order statistics are $X_{(1)} \le X_{(2)} \le \cdots \le X_{(n)}$.

| Statistic | CDF | Density (continuous case) |
|---|---|---|
| Min: $X_{(1)}$ | $1 - (1 - F(x))^n$ | $n(1-F(x))^{n-1} f(x)$ |
| Max: $X_{(n)}$ | $F(x)^n$ | $n F(x)^{n-1} f(x)$ |
| $i$-th: $X_{(i)}$ | $\displaystyle\sum_{j=i}^{n}\binom{n}{j}F(x)^j(1-F(x))^{n-j}$ | $\dfrac{n!}{(i-1)!(n-i)!} F(x)^{i-1}(1-F(x))^{n-i} f(x)$ |

For $\text{Uniform}[0,1]$: $X_{(n)} \sim \text{Beta}(n, 1)$, $X_{(1)} \sim \text{Beta}(1, n)$.

---

## 8. Simulation of Random Variables

Assume access to i.i.d. $U_1, U_2, \dots \sim \text{Uniform}[0,1]$.

### 8.1 Direct Constructions

| Target | Construction |
|---|---|
| $\text{Uniform}[L,R]$ | $X = (R-L)U_1 + L$ |
| $\text{Bernoulli}(p)$ | $X = \mathbf{1}(U_1 \le p)$ |
| $\text{Binomial}(n,p)$ | $X = \sum_{i=1}^n \mathbf{1}(U_i \le p)$, or threshold on cdf |
| $\text{Geometric}(p)$ | $X = \min\{i : U_i \le p\}$; equivalently $X = \lfloor \log(1-U_1)/\log(1-p) \rfloor$ |
| $\text{Exponential}(\lambda)$ | $X = -\tfrac{1}{\lambda}\ln(1-U_1) = -\tfrac{1}{\lambda}\ln U_1$ |
| $N(0,1)$ (Box–Muller) | $X = \sqrt{-2\ln U_1}\cos(2\pi U_2)$, $Y = \sqrt{-2\ln U_1}\sin(2\pi U_2)$ |
| $N(\mu,\sigma^2)$ | $Z = \mu + \sigma X$ with $X \sim N(0,1)$ |

### 8.2 Inversion Method (General)

For cdf $F$, define the **generalized inverse** $F^{-1}(u) = \min\{x : F(x) \ge u\}$. Then $Y = F^{-1}(U)$ has cdf $F$. Use this whenever the inverse is available and cheap.

### 8.3 Conditional / Composition Sampling

For multivariate distributions, sample sequentially from conditionals:
$$
x_1 \sim F_{X_1}, \quad x_2 \sim F_{X_2|X_1}(\cdot \mid x_1), \quad \dots
$$
Equivalently, sample from the discrete mixture (continuous case) by $f_C(c) = \sum_d p_D(d) f_{C|D}(c \mid d)$.

### 8.4 Rejection Sampling

To sample from a discrete pmf $p_Y$ using samples from $p_X$: choose $c \ge \max_x p_Y(x)/p_X(x)$ and accept sample $X=x$ with probability
$$
a(x) = \min\!\left(1,\; c\,\frac{p_Y(x)}{p_X(x)}\right).
$$
Accepted samples have pmf $p_Y$.

For continuous densities: if $f_Y(x) \le c\,g(x)$ for some tractable envelope $g$, sample $Y \sim g$ and $U \sim \text{Uniform}[0,c]$ independently; accept iff $U \le f_Y(Y)/g(Y)$. The accepted samples have density $f_Y$ in the limit.

---

## 9. Moment Generating Functions

### 9.1 Definition

For a random variable $X$ with cdf $F_X$, the **moment generating function** is
$$
M_X(t) = E[e^{tX}] = \int e^{tx}\,dF_X(x),
$$
defined for $t$ in some interval around $0$. $M_X(0) = 1$, and $M_X$ uniquely determines the distribution whenever it exists in a neighborhood of $0$.

### 9.2 Moments from the MGF

$$
E[X^k] = M_X^{(k)}(0), \qquad \text{Var}(X) = M_X''(0) - (M_X'(0))^2.
$$

### 9.3 Standard MGFs

| Distribution | MGF $M_X(t)$ | Domain |
|---|---|---|
| Degenerate at $c$ | $e^{tc}$ | all $t$ |
| $\text{Bernoulli}(p)$ | $1 - p + pe^t$ | all $t$ |
| $\text{Binomial}(n,p)$ | $(1 - p + pe^t)^n$ | all $t$ |
| $\text{Poisson}(\lambda)$ | $e^{\lambda(e^t - 1)}$ | all $t$ |
| $\text{Geometric}(p)$ (counts) | $\dfrac{pe^t}{1-(1-p)e^t}$ | $t < -\ln(1-p)$ |
| $\text{Uniform}[a,b]$ | $\dfrac{e^{tb}-e^{ta}}{t(b-a)}$ | $t \ne 0$ |
| $\text{Exponential}(\lambda)$ | $\dfrac{\lambda}{\lambda - t}$ | $t < \lambda$ |
| $\text{Gamma}(\alpha,\beta)$ | $(1-\beta t)^{-\alpha}$ | $t < 1/\beta$ |
| $\chi^2_\nu$ (= Gamma($\nu/2, 2$)) | $(1-2t)^{-\nu/2}$ | $t < 1/2$ |
| $N(\mu,\sigma^2)$ | $\exp(\mu t + \tfrac{1}{2}\sigma^2 t^2)$ | all $t$ |

### 9.4 MGF Transformations

$M_{aX+b}(t) = e^{bt} M_X(at)$.

### 9.5 MGFs of Sums

If $X, Y$ are independent, then
$$
M_{X+Y}(t) = M_X(t)\,M_Y(t).
$$
This product is the standard tool for proving convolution closures (e.g. Gamma additivity, Normal additivity).

---

## 10. Expectation for Joint and Transformed Variables

For a function $g(X_1,\dots,X_n)$:
- **Discrete:** $\displaystyle E[g] = \sum_{x_1,\dots,x_n} g(\vec{x})\,p_{\vec{X}}(\vec{x})$.
- **Continuous:** $\displaystyle E[g] = \int\cdots\int g(\vec{x})\,f_{\vec{X}}(\vec{x})\,d\vec{x}$.

**Indicator trick:** $E[\mathbf{1}_A] = P(A)$.

### 10.1 Linearity

For constants $a, b$ and random variables $X, X_1, \dots, X_n$:
$$
E[aX+b] = a\,E[X] + b, \qquad E\!\left[\sum_i a_i X_i\right] = \sum_i a_i\,E[X_i].
$$

### 10.2 Variance of Linear Combinations

$$
\text{Var}(aX+b) = a^2 \text{Var}(X).
$$
For independent $X_i$:
$$
\text{Var}\!\left(\sum_i a_i X_i\right) = \sum_i a_i^2 \text{Var}(X_i).
$$
Without independence one must add covariance terms.

### 10.3 Sample Mean and Sample Variance

If $X_1, \dots, X_n$ are i.i.d. with mean $\mu$ and variance $\sigma^2$, then
$$
\bar{X} = \frac{1}{n}\sum_{i=1}^n X_i \quad\Rightarrow\quad E[\bar X] = \mu, \quad \text{Var}(\bar X) = \frac{\sigma^2}{n},
$$
$$
S^2 = \frac{1}{n-1}\sum_{i=1}^n (X_i - \bar X)^2 \quad\Rightarrow\quad E[S^2] = \sigma^2.
$$
The factor $n-1$ in the denominator is what makes $S^2$ an unbiased estimator of $\sigma^2$.

---

## 11. Covariance, Correlation, and Linear Combinations

### 11.1 Definitions

$$
\text{Cov}(X_1, X_2) = E[(X_1 - \mu_1)(X_2 - \mu_2)] = E[X_1 X_2] - \mu_1 \mu_2.
$$
$$
\rho(X_1, X_2) = \frac{\text{Cov}(X_1, X_2)}{\sigma_1 \sigma_2} \in [-1, 1].
$$
For $Y = a_1 X_1 + a_2 X_2$:
$$
\text{Var}(Y) = a_1^2 \text{Var}(X_1) + a_2^2 \text{Var}(X_2) + 2 a_1 a_2 \text{Cov}(X_1, X_2).
$$
For independent $X_1, X_2$, $\text{Cov}(X_1, X_2) = 0$, but the converse fails.

### 11.2 Mean and Variance of Linear Combinations

For $X_i$ with mean $\mu_i$ and variance $\sigma_i^2$, the linear combination $Y = \sum_i a_i X_i$ has
$$
E[Y] = \sum_i a_i \mu_i, \qquad \text{Var}(Y) = \sum_i a_i^2 \sigma_i^2 \quad (\text{if independent}).
$$
Without independence: $\text{Var}(Y) = \sum_i a_i^2 \sigma_i^2 + 2 \sum_{i < j} a_i a_j\, \text{Cov}(X_i, X_j)$.

---

## 12. Graphical Models (Quick Reference)

A **directed acyclic graph (DAG)** with node for each random variable encodes a factorization of the joint pmf/pdf:
$$
p_{\vec{X}}(\vec{x}) = \prod_i p_{X_i \mid \text{parents}(X_i)}(x_i \mid \cdot).
$$
**Local Markov property:** each node is conditionally independent of its non-descendants given its parents. **Markov chain** is a chain DAG: $p_{S_1,\dots,S_k} = p_{S_1} p_{S_2|S_1} \cdots p_{S_k|S_{k-1}}$. Adding edges to a Markov chain captures more dependence at the cost of more parameters; full independence gives the fewest parameters and may mis-represent strong dependence.

---

## 13. Pitfalls and Caveats

- **Strict monotonicity** in the 1D change-of-variable formula only needs to hold on the support of $f_X$; outside that set, $h$ may do anything.
- **Joint pmf of one discrete and one continuous variable does not exist**; use conditional pmf and conditional pdf separately, via the mixed chain rule.
- **Pairwise independence $\ne$ mutual independence**: build a counterexample with three indicators of $X_1 = X_2$.
- **Zero covariance $\not\Rightarrow$ independence** unless additional structure (e.g. bivariate normal) is assumed.
- **Bivariate normal with $\rho = 0$** is the canonical case where zero correlation equals independence; this is a special property of the Gaussian, not a general fact.
- **Convolution requires independence**; without it, you need the full joint density.
- **MGF uniqueness** holds only when the MGF is finite in an open interval around $0$; otherwise two distinct distributions can agree on all moments (e.g. log-normal and Stieltjes examples).
- **Box–Muller** uses two uniforms and produces two independent $N(0,1)$ variables; do not reuse uniforms in subsequent calls without resampling.
- **Generalized inverse** $F^{-1}(u) = \min\{x : F(x) \ge u\}$ is the right object for the inversion method; it is well defined even when $F$ has flat regions or jumps.
- **Rejection sampling** requires a valid envelope $f_Y \le c g$; mismatched support makes acceptance zero on a non-negligible set, biasing the result.
