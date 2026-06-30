---
type: Reference
---
# Nonparametric (Distribution-Free) Tests

Most of the standard tests — the one- and two-sample t tests, the F tests, ANOVA — assume the observations come from normal populations. When that assumption is doubtful, especially at small sample sizes where normality cannot be checked, **nonparametric** (distribution-free) tests give exact inferences from far weaker assumptions. They depend only on *order relationships* among the observations, so asymmetry or other departures from normality leave the null sampling distribution untouched and the significance level stays exact. The price is power: when normality *does* hold, the parametric test is more efficient. This reference covers the sign test, the rank-sum (Wilcoxon/Mann–Whitney U) test, the Kruskal–Wallis H test, Spearman's rank correlation, the runs test for randomness, and the Kolmogorov–Smirnov / Anderson–Darling goodness-of-fit tests, with the rule for choosing nonparametric vs parametric. Grounded in Miller & Freund's *Probability and Statistics for Engineers*, Chapter 14.

---

## 1. When to use a nonparametric test

Reach for a distribution-free test when **any** of these hold:

- The normality assumption is doubtful and the sample is too small to verify it.
- The data are ranks or ordinal scores, or the numerical measurement scale is arbitrary.
- You want an **exact** level of significance regardless of the population shape.
- The quantity of interest is a **median** (robust to outliers) rather than a mean.

Stay parametric (t, F, ANOVA) when the population is plausibly normal and you want maximum power, or when the question is genuinely about means/variances of a known model. **Rule of thumb:** nonparametric tests sacrifice some power for robustness; their power is usually still satisfactory even under mild non-normality, and they win outright under heavy-tailed or skewed populations.

**Caution (independence).** Rank tests are distribution-free only for *independent* observations. Even moderate time dependence can seriously distort the actual significance level. Confirm independence before applying any rank test, and account for finite-population dependence when the sample is 5–10% of the population.

---

## 2. The Sign Test

A nonparametric alternative to the one-sample t test and the paired-sample t test. It applies to a continuous, (roughly) symmetric population and is framed in terms of the population **median** $\tilde\mu$.

### 2.1 One-sample sign test

To test $H_0:\tilde\mu=\tilde\mu_0$, replace each observation greater than $\tilde\mu_0$ with a **plus** sign and each less than $\tilde\mu_0$ with a **minus** sign; discard any value exactly equal to $\tilde\mu_0$ (continuous variates are virtually always rounded, so ties occur). Under $H_0$ the plus and minus signs are outcomes of binomial trials with $p=\tfrac12$.

- **Small sample:** refer the number of plus signs $x$ directly to the binomial table with $p=0.5$ and the reduced $n$ (after discards). Reject if $P(X\ge x)$ (or the appropriate tail) $\le \alpha$.
- **Large sample:** use the normal approximation to the binomial (the large-sample test for a proportion).

**Worked example (M&F).** 15 octane ratings, test $H_0:\tilde\mu=98.0$ vs $H_1:\tilde\mu>98.0$ at $\alpha=0.01$. One value equals 98.0 and is discarded, so $n=14$; the signs give $x=12$ plus signs. From the binomial table, $P(X\ge 12)=1-0.9935=0.0065<0.01$, so reject $H_0$: the median octane rating exceeds 98.0.

### 2.2 Paired-sample sign test

For paired data, replace each pair with a **plus** if the first value exceeds the second, a **minus** if it is smaller, discard ties, and test the median of the differences $\tilde\mu_D$ against 0 exactly as above. A clean nonparametric replacement for the paired t test.

---

## 3. Rank-Sum Tests

Rank-sum tests rank the pooled data and compare the rank sums between groups. **Ties:** assign each tied observation the average of the ranks they jointly occupy (e.g. a tie for ranks 3 and 4 gets 3.5).

### 3.1 The U test (Wilcoxon / Mann–Whitney) — two independent samples

A nonparametric alternative to the two-sample t test. It tests whether two samples come from identical populations, with one-sided alternatives phrased in terms of **stochastic order** (one population tends to produce larger values).

Rank all $n_1+n_2$ observations jointly in increasing order. Let $W_1$ be the sum of the ranks held by sample 1. Define

$$U_1 = W_1 - \frac{n_1(n_1+1)}{2}, \qquad U_2 = W_2 - \frac{n_2(n_2+1)}{2},$$

with $U_1+U_2 = n_1 n_2$. Under $H_0$ (identical populations), the sampling distribution of $U_1$ has

$$\mu_{U_1}=\frac{n_1 n_2}{2}, \qquad \sigma^2_{U_1}=\frac{n_1 n_2 (n_1+n_2+1)}{12}.$$

For $n_1, n_2 > 8$ the distribution is well approximated by the normal, so test with

$$Z = \frac{U_1 - \mu_{U_1}}{\sigma_{U_1}}.$$

Reject $H_0$ for $Z<-z_\alpha$ if the alternative is "population 2 stochastically larger," for $Z>z_\alpha$ if "population 1 stochastically larger," or two-sided against $\pm z_{\alpha/2}$. For small samples use special U tables. (Ties make the variance formula approximate; with few ties the approximation is good.)

**Worked example (M&F, grain size).** $n_1=15$, $n_2=14$, $W_1=162$. Then $U_1=162-\tfrac{15\cdot16}{2}=42$, $\mu_{U_1}=105$, $\sigma^2_{U_1}=525$, so $z=(42-105)/\sqrt{525}=-2.75$. At $\alpha=0.01$ (two-sided, $\pm2.575$) reject: the two grain-size populations differ.

### 3.2 The H test (Kruskal–Wallis) — k independent samples

The rank-based generalization of one-way ANOVA: tests whether $k$ independent samples come from identical populations. Rank all observations jointly; let $R_i$ be the rank sum of the $n_i$ observations in sample $i$, with $n=\sum n_i$. The statistic is

$$H = \frac{12}{n(n+1)} \sum_{i=1}^{k} \frac{R_i^2}{n_i} - 3(n+1).$$

When every $n_i>5$ and $H_0$ is true, $H$ is approximately $\chi^2$ with $k-1$ degrees of freedom; reject for large $H$. Use special tables for small $n_i$.

**Worked example (M&F, corrosion methods).** Three methods, $H=6.7$, compared with $\chi^2_{0.05}=5.991$ at 2 d.f.; since $6.7>5.991$, reject $H_0$ — the methods are not equally effective ($P\approx0.035$).

---

## 4. Correlation Based on Ranks — Spearman's $r_S$

Spearman's rank-correlation coefficient is Pearson's $r$ computed on ranks. With $R_i$ the rank of $x_i$ and $S_i$ the rank of $y_i$,

$$r_S = \frac{\sum_{i=1}^{n}\left(R_i-\frac{n+1}{2}\right)\left(S_i-\frac{n+1}{2}\right)}{n(n^2-1)/12} = \frac{\sum_{i=1}^{n} R_i S_i - n(n+1)^2/4}{n(n^2-1)/12}.$$

Properties: $-1\le r_S\le 1$; values near $+1$ indicate large $X$ and $Y$ tend to pair together, near $-1$ the opposite; $r_S$ measures a **monotone** (not necessarily linear) association. Average tied ranks. For large $n$, if $X$ and $Y$ are independent, $Z=\sqrt{n}\,r_S$ is approximately standard normal — use it to test independence.

---

## 5. Tests of Randomness — the Runs Test

When you cannot control how data are collected, test whether the *order* in which they arrived is random. A **run** is a maximal succession of identical symbols. Too few runs suggests clustering / non-constant probability; too many suggests negative dependence (over-alternation).

For a sequence of $n_1$ symbols of one kind and $n_2$ of another (each $\ge 10$), the total number of runs $u$ is approximately normal with

$$\mu_u = \frac{2 n_1 n_2}{n_1+n_2}+1, \qquad \sigma_u = \sqrt{\frac{2 n_1 n_2 (2 n_1 n_2 - n_1 - n_2)}{(n_1+n_2)^2 (n_1+n_2-1)}}.$$

Test with $Z=(u-\mu_u)/\sigma_u$. Use special tables when $n_1$ or $n_2$ is small.

**Runs above and below the median.** For numerical data, label each value $a$ if above the sample median and $b$ if below, then apply the runs test to the $a$/$b$ sequence. This is a frequent quality-control check: plotting successive small-sample means in time order and counting runs reveals trends or over-frequent machine adjustments before serious damage occurs.

**Worked example (M&F, lathe).** Runs above/below the median 0.250 of 40 shaft diameters give $n_1=19$, $n_2=16$, $u=27$; $\mu_u=18.37$, $\sigma_u=2.89$, $z=2.98>2.33$ — reject randomness: the lathe is being adjusted too often (too many runs).

---

## 6. Goodness-of-Fit: Kolmogorov–Smirnov and Anderson–Darling

These test agreement between an empirical and a specified **continuous** cumulative distribution (or between two empirical CDFs). Unlike the chi-square goodness-of-fit test they need no binning and work for very small samples — but they apply only to continuous distributions (use chi-square for discrete).

### 6.1 Kolmogorov–Smirnov (KS)

Based on the maximum absolute difference between the empirical CDF $F_n(x)$ and the hypothesized $F(x)$:

$$D = \max_x |F_n(x) - F(x)|.$$

Reject for large $D$ (obtain the $P$-value from software or KS tables). KS is generally more efficient than chi-square for small samples and is sensitive to differences in location, dispersion, and skewness. Its weakness is poor power in the **tails**.

### 6.2 Anderson–Darling (AD)

Weights the discrepancy by $1/\sqrt{F(x)(1-F(x))}$, giving more weight to the tails:

$$A^2 = n\int_{-\infty}^{\infty} \frac{[F_n(x)-F(x)]^2}{F(x)(1-F(x))}\,f(x)\,dx.$$

For continuous $F$ with $u_i = F(x_{(i)})$ (the $i$th smallest observation),

$$A^2 = -\frac{1}{n}\sum_{i=1}^{n}(2i-1)\big[\ln u_i + \ln(1-u_{n+1-i})\big] - n.$$

Reject for large $A^2$. Large-sample critical values (accurate even for $n$ as small as 10): 1.933 (10%), 2.492 (5%), 3.878 (1%). Prefer AD over KS when tail behavior matters.

---

## 7. Do's and Don'ts

- **Do** prefer the Wilcoxon U test for comparing two locations at small sample sizes — it does not require normality, which is hard to check with little data.
- **Don't** apply the U test when the two dot diagrams show very different spreads as well as different locations: a location test won't tell the whole story.
- **Don't** apply rank tests without confirming the observations are independent — rank tests are *not* distribution-free under dependence.
- **Do** match the test to the question: median → sign; two groups → U; $k$ groups → H; monotone association → $r_S$; order/randomness → runs; continuous goodness-of-fit → KS/AD (AD for tails).

---

## 8. Quick selector

| Question | Parametric | Nonparametric |
|---|---|---|
| One median / one mean | one-sample t | sign test |
| Paired difference | paired t | paired sign test |
| Two independent groups | two-sample t | Wilcoxon / Mann–Whitney U |
| $k\ge3$ independent groups | one-way ANOVA (F) | Kruskal–Wallis H |
| Association between two variables | Pearson $r$ | Spearman $r_S$ |
| Is the sequence random? | — | runs test (incl. above/below median) |
| Does data fit a continuous distribution? | — | Kolmogorov–Smirnov, Anderson–Darling |
