---
type: Reference
---
# Reliability & Life Testing

**Reliability** is the probability that a unit functions within specified limits for at least a specified period under specified environmental conditions. Because it is a probability, the whole apparatus of probability applies: system reliability is built from component reliabilities by the rules of multiplication, and component reliabilities are estimated from life tests. This reference covers the reliability function and the hazard (failure-rate) function, the bathtub curve, series and parallel system reliability, the exponential and Weibull life models, MTBF, censored (truncated) life testing with chi-square confidence intervals, and the Weibull plot. Grounded in Miller & Freund's *Probability and Statistics for Engineers*, Chapter 16.

---

## 1. Reliability is a probability — and depends on conditions

A unit's reliability is defined *relative to* purpose, time, and environment: a microchip perfectly reliable in a home audio system may be useless in a missile guidance system. So reliability is always quoted as "probability of functioning for at least time $t$ under stated conditions." This framing lets us compute complex-system reliability from component reliabilities (Section 2) and estimate component reliabilities from life tests (Sections 4–5).

---

## 2. System Reliability: Series and Parallel

Model a system as series, parallel, or a combination, assuming **independent** components.

### 2.1 Series system — product law of reliabilities

A series system fails if *any* component fails. With component reliabilities $R_i$,

$$R_S = \prod_{i=1}^{n} R_i.$$

Complexity is punishing: 5 components at $R=0.970$ give $R_S=0.970^5=0.859$; doubling to 10 components drops it to $0.970^{10}=0.737$. To hold the 5-component reliability with 10 components, each would need $R=0.985$.

### 2.2 Parallel system — product law of unreliabilities

A parallel system fails only if *all* components fail. With unreliabilities $F_i=1-R_i$,

$$F_P = \prod_{i=1}^{n} F_i, \qquad R_P = 1 - \prod_{i=1}^{n}(1-R_i).$$

Redundancy (replacing a component with several in parallel) is the standard way to raise reliability.

### 2.3 Mixed systems

Collapse parallel sub-assemblies to equivalent components, then apply the series law. *Example (M&F):* a parallel triple at $R=0.70$ becomes $1-(1-0.70)^3=0.973$; a parallel pair at $R=0.75$ becomes $1-(1-0.75)^2=0.9375$; the resulting series chain $(0.95)(0.99)(0.973)(0.9375)(0.90)=0.772$.

---

## 3. Failure-Time Distribution and the Hazard (Failure-Rate) Function

Let $f(t)$ be the density of time to failure, $F(t)=\int_0^t f(x)\,dx$ the CDF, and the **reliability function**

$$R(t) = 1 - F(t)$$

the probability of surviving past $t$. The **failure-rate** or **hazard function** $Z(t)$ is the instantaneous conditional failure rate given survival to $t$:

$$Z(t) = \frac{f(t)}{R(t)} = \frac{f(t)}{1-F(t)}.$$

Inverting this relationship (using $Z(t)=-\,d[\ln R(t)]/dt$) recovers the reliability and density from the hazard:

$$R(t) = e^{-\int_0^t Z(x)\,dx}, \qquad f(t) = Z(t)\, e^{-\int_0^t Z(x)\,dx}.$$

### 3.1 The bathtub curve

The typical hazard curve has three regimes:

1. **Infant mortality** — *decreasing* failure rate; poorly made units are weeded out (motivating "burn-in").
2. **Useful life** — roughly *constant* failure rate; only chance failures (the exponential regime).
3. **Wear-out** — *increasing* failure rate; units fail from age.

(The same shape describes human mortality.)

---

## 4. The Exponential Model (constant hazard)

If the failure rate is constant, $Z(t)=\alpha$ ($\alpha>0$), then

$$f(t) = \alpha\, e^{-\alpha t}, \quad t>0, \qquad R(t)=e^{-\alpha t}.$$

This is the **exponential failure-time distribution** — the "exponential assumption" of a constant hazard, appropriate to the useful-life regime. If a failed component is immediately replaced and failures follow a Poisson process, inter-failure waiting times are exactly exponential. The mean time between failures is the reciprocal of the rate:

$$\text{MTBF} = \mu = \frac{1}{\alpha}.$$

### 4.1 Life testing under the exponential model

Put $n$ components on test; stop after the $r$th failure ($r\le n$) — a **censored / truncated** test. Observed times $t_1\le\cdots\le t_r$. The **accumulated time on test** is

$$T_r = \sum_{i=1}^{r} t_i + (n-r)t_r \quad\text{(nonreplacement)}, \qquad T_r = n\,t_r \quad\text{(replacement)}.$$

An unbiased estimate of the mean life is $\hat\mu = T_r/r$ (so $\hat\alpha=1/\hat\mu$). The key fact: $2T_r/\mu$ is $\chi^2$ with $2r$ degrees of freedom (with or without replacement). Hence a two-sided $(1-\alpha)100\%$ confidence interval for the mean life:

$$\frac{2T_r}{\chi^2_{\alpha/2}} < \mu < \frac{2T_r}{\chi^2_{1-\alpha/2}} \quad (2r \text{ d.f.}).$$

To test $H_0:\mu=\mu_0$ against $H_1:\mu>\mu_0$ at level $\alpha$, reject when $T_r > \tfrac12\mu_0\,\chi^2_\alpha$ (with $2r$ d.f.).

**Worked example (M&F).** $n=50$, $r=10$, first 10 failure times summing appropriately give $T_{10}=43{,}410$ hours, $\hat\mu=4{,}341$ hours, $\hat\alpha=0.00023$/hr. With $\chi^2_{0.05}=31.410$, $\chi^2_{0.95}=10.851$ (20 d.f.), the 90% CI is $\frac{2(43{,}410)}{31.410}<\mu<\frac{2(43{,}410)}{10.851}$, i.e. $2{,}764<\mu<8{,}001$ hours.

### 4.2 Checking the exponential assumption — total-time-on-test plot

Plot $T_i/T_r$ (total time on test through the $i$th failure, scaled) against $i/r$. Exponential data follow the 45° line; a curve above it indicates an **increasing** hazard (wear-out), warning against the exponential model.

---

## 5. The Weibull Model (monotone hazard)

When the hazard rises or falls smoothly (initial or wear-out regimes), use a power-law hazard

$$Z(t) = \alpha\beta\, t^{\beta-1}, \quad t>0,$$

which gives the **Weibull distribution**

$$f(t) = \alpha\beta\, t^{\beta-1} e^{-\alpha t^{\beta}}, \qquad R(t) = e^{-\alpha t^{\beta}}.$$

The shape parameter $\beta$ governs the hazard: $\beta<1$ → decreasing (infant mortality), $\beta=1$ → constant (recovers the exponential), $\beta>1$ → increasing (wear-out). The density is right-skewed for $\beta<1$, exponential at $\beta=1$, and bell-ish (still skewed) for $\beta>1$.

Moments use the gamma function:

$$\mu = \alpha^{-1/\beta}\,\Gamma\!\left(1+\tfrac{1}{\beta}\right), \qquad \sigma^2 = \alpha^{-2/\beta}\left\{\Gamma\!\left(1+\tfrac{2}{\beta}\right) - \left[\Gamma\!\left(1+\tfrac{1}{\beta}\right)\right]^2\right\}.$$

### 5.1 Estimating $\alpha,\beta$ (MLE under censoring)

Maximum likelihood. With lifetimes censored at the $r$th failure (or uncensored, $r=n$), $\hat\beta$ solves (numerically)

$$\frac{\sum_{i=1}^{r} t_i^{\beta}\ln t_i + (n-r)t_r^{\beta}\ln t_r}{\sum_{i=1}^{r} t_i^{\beta} + (n-r)t_r^{\beta}} - \frac{1}{\beta} - \frac{1}{r}\sum_{i=1}^{r}\ln t_i = 0,$$

then

$$\hat\alpha = \frac{r}{\sum_{i=1}^{r} t_i^{\beta} + (n-r)t_r^{\beta}}.$$

For a time-truncated test at $T_0$, replace $t_r$ by $T_0$ in the $(n-r)$ terms.

### 5.2 The Weibull plot

Because $\ln\ln\frac{1}{R(t)} = \ln\alpha + \beta\ln t$ is linear in $\ln t$, plot $\ln t_i$ against $\ln\ln\frac{1}{1-\hat F(t_i)}$, estimating $\hat F(t_i)=i/(n+1)$. Points near a straight line support the Weibull model; the slope estimates $\beta$. *Example (M&F):* 12 failures out of 100 give $\hat\alpha=0.001505$, $\hat\beta=0.7148$ (so a decreasing hazard), $\hat\mu\approx11{,}000$ hours, and $\hat Z(t)=0.00108\,t^{-0.2852}$.

---

## 6. Do's and Don'ts

- **Do** fit a Weibull alongside any exponential model and check whether $\hat\beta\approx1$; the exponential is just Weibull with $\beta=1$.
- **Don't** trust an exponential reliability analysis when components have an increasing hazard — it is over-optimistic, because most real parts eventually age.
- **Don't** accept a system analysis that assumes component independence uncritically — external shocks can fail several components at once.
- **Do** verify the exponential assumption with a total-time-on-test plot (45° line) before quoting MTBF-based intervals.

---

## 7. Quick selector

| Situation | Model / tool |
|---|---|
| Series system | $R_S=\prod R_i$ |
| Parallel (redundant) system | $R_P=1-\prod(1-R_i)$ |
| Constant hazard (useful life) | exponential, $R(t)=e^{-\alpha t}$, MTBF $=1/\alpha$ |
| Mean-life CI from censored test | $\dfrac{2T_r}{\chi^2_{\alpha/2}}<\mu<\dfrac{2T_r}{\chi^2_{1-\alpha/2}}$, $2r$ d.f. |
| Monotone (increasing/decreasing) hazard | Weibull, $Z(t)=\alpha\beta t^{\beta-1}$ |
| Check exponential fit | total-time-on-test plot |
| Check Weibull fit / estimate $\beta$ | Weibull plot ($\ln\ln$ vs $\ln t$) |
