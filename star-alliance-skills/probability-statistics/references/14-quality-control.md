---
type: Reference
---
# Statistical Quality Control & Process Capability

Any manufacturing process, however good, carries a certain irreducible **chance variation**. The statistical job of quality control is to separate that natural, random variation from **assignable variation** — the trouble caused by worn parts, faulty settings, poor materials, or untrained operators — and to flag the latter quickly, ideally before defects are produced. This reference covers Shewhart control charts for measurements ($\bar X$ and $R$ charts) and for attributes ($p$ and $c$ charts), three-sigma limits, the CUSUM chart for small shifts, process-capability indices ($C_p$, $C_{pk}$), the distinction between control limits and specification limits, and tolerance limits. Grounded in Miller & Freund's *Probability and Statistics for Engineers*, Chapter 15.

---

## 1. Statistical control and the logic of a control chart

A process is in a state of **statistical control** when its variability is confined to chance variation. Achieving that state means finding and eliminating **assignable causes**. A **control chart** is a sequential, time-ordered set of hypothesis tests:

- a **central line** at the average quality the process should hold,
- **upper and lower control limits (UCL, LCL)** chosen so that points inside are attributable to chance, points outside indicate loss of control.

A point beyond the limits is read like rejecting $H_0:\mu=\mu_0$ — a signal to look for trouble. But even inside the limits, **trends and patterns** carry information; the chart is read for runs and drifts as well as out-of-limit points.

**Three-sigma limits.** If a characteristic is roughly normal, virtually all of it lies within $\mu\pm3\sigma$. Rather than use a chosen $\alpha$ (whose $z_{\alpha/2}$ would require trusting normality), industrial practice substitutes 3 for $z_{\alpha/2}$ — **three-sigma limits** — so the process is rarely declared out of control when it is actually in control.

---

## 2. Control Charts for Measurements ($\bar X$ and $R$)

When the data are measurements, control both the **average** (with an $\bar X$ chart) and the **variability** (with an $R$ chart on sample ranges, or a $\sigma$ chart on sample standard deviations). Take $k\approx20$–25 consecutive samples each of size $n$ while the process is in control.

Let $\bar x_i$ be the mean and $R_i$ the range of sample $i$. The grand mean and mean range are

$$\bar{\bar x} = \frac{1}{k}\sum_{i=1}^{k}\bar x_i, \qquad \bar R = \frac{1}{k}\sum_{i=1}^{k}R_i.$$

### 2.1 $\bar X$ chart

With $\mu,\sigma$ estimated from past data, the constant $A_2$ (tabulated by $n$, assuming normal measurements) turns $\bar R$ into an unbiased estimate of $3\sigma/\sqrt{n}$:

$$\text{central line} = \bar{\bar x}, \qquad \text{UCL} = \bar{\bar x} + A_2 \bar R, \qquad \text{LCL} = \bar{\bar x} - A_2 \bar R.$$

(If $\mu,\sigma$ are *known* from specifications, use central line $\mu$ and limits $\mu \pm A\sigma$ with $A=3/\sqrt{n}$.)

### 2.2 $R$ chart

The control-chart constants $d_2, d_3$ give the mean and SD of the sample range from a normal population. With $\sigma$ **unknown** (estimated from $\bar R$):

$$\text{central line} = \bar R, \qquad \text{UCL} = D_4 \bar R, \qquad \text{LCL} = D_3 \bar R,$$

where $D_3=D_1/d_2$, $D_4=D_2/d_2$, $D_1=d_2-3d_3$, $D_2=d_2+3d_3$. With $\sigma$ **known**: central line $d_2\sigma$, UCL $D_2\sigma$, LCL $D_1\sigma$. (If sample standard deviations are used instead of ranges, the $\bar X$ limits become $\bar{\bar x}\pm A_1\bar s$ and the $\sigma$ chart uses central line $c_2 s$ with limits $B_3 s$, $B_4 s$.)

**Constants for common $n$** (from M&F Table 8W): $n=2$: $A_2=1.880, D_3=0, D_4=3.267$. $n=4$: $A_2=0.729, D_3=0, D_4=2.282$. $n=5$: $A_2=0.577, D_3=0, D_4=2.114$. (For small $n$ the lower range limit is 0.)

**Reading the charts.** A point out of limits, a run of points on one side of the central line, or a steady drift signals a shift in level (on the $\bar X$ chart) or in spread (on the $R$ chart). Always pair the $\bar X$ chart with an $R$ (or $\sigma$) chart — a stable mean over rising variability is still an out-of-control process.

---

## 3. CUSUM Chart — for small, sustained shifts

The Shewhart chart is slow to catch a *small* persistent shift in the mean. The **cumulative-sum (CUSUM)** chart accumulates deviations from a target value $a$ and is far more sensitive to small shifts:

$$S_t = \sum_{j=1}^{t}(x_j - a).$$

A sustained slope in the plotted $S_t$ reveals that the process level sits a fixed amount off target. **Crosier's two-sided CUSUM** (which reduces false alarms) starts at $S_0=0$, computes $C_n=|S_{n-1}+(X_n-a)|$, and updates

$$S_n = \begin{cases} 0, & C_n \le ks \\ (S_{n-1}+X_n-a)\left(1-\dfrac{ks}{C_n}\right), & \text{otherwise} \end{cases}$$

with $k=\tfrac12(\mu_1-\mu_0)/\sigma$ set to half the mean-shift (in SD units) you want to detect quickly. It signals a shift when $S_n\ge hs$ (increase) or $S_n\le -hs$ (decrease).

---

## 4. Control Charts for Attributes ($p$ and $c$)

When inspection is "go / no-go" rather than measured, use attribute charts. Note the distinction: a unit is **defective** (it has $\ge1$ defect) or not; a single unit may carry several **defects**.

### 4.1 $p$ chart (fraction defective)

Built on the normal approximation to the binomial. If a standard $p$ is given, central line $p$ with

$$p \pm 3\sqrt{\frac{p(1-p)}{n}}.$$

If no standard, estimate $p$ from $k$ samples as the pooled proportion

$$\bar p = \frac{d_1+d_2+\cdots+d_k}{n_1+n_2+\cdots+n_k},$$

then

$$\text{central line} = \bar p, \qquad \text{UCL/LCL} = \bar p \pm 3\sqrt{\frac{\bar p(1-\bar p)}{n}}.$$

If the LCL comes out negative, set it to 0 and use the upper limit only. When $np$ is small the normal approximation fails — use exact binomial or Poisson limits instead. (The equivalent **number-of-defectives** chart multiplies the central line and limits by $n$: central line $n\bar p$, limits $n\bar p \pm 3\sqrt{n\bar p(1-\bar p)}$.)

### 4.2 $c$ chart (number of defects per unit)

When counting defects per unit (per 100 yards of carpet, per roll of newsprint), $c$ is modeled as Poisson, whose SD is $\sqrt{\lambda}$. Estimate $\lambda$ from $\ge20$ units as $\bar c=\frac{1}{k}\sum c_i$:

$$\text{central line} = \bar c, \qquad \text{UCL} = \bar c + 3\sqrt{\bar c}, \qquad \text{LCL} = \bar c - 3\sqrt{\bar c}.$$

### 4.3 Extra sensitivity tests

Beyond "one point outside the limits," signal a special cause if either:

1. **9 points in a row** on the same side of the central line, or
2. **6 points in a row** all increasing or all decreasing.

---

## 5. Process Capability ($C_p$, $C_{pk}$) — control limits vs spec limits

**Control limits and specification limits are different things.** Control limits come from the *process's own* variation (where points fall by chance); **specification limits** $\text{LSL}, \text{USL}$ come from *engineering requirements* (what the customer accepts). A process can be in perfect statistical control yet incapable of meeting spec — and capability is only meaningful once the process is stable.

If a characteristic is nearly normal, its natural spread is $6\sigma$. The **process capability index** compares that spread to the spec width:

$$\hat C_p = \frac{\text{USL}-\text{LSL}}{6s}.$$

Practitioners require $\hat C_p \ge 1.33$ before deeming an ongoing process capable. $C_p$ ignores **centering**; when the mean is off-center, the closest spec limit dominates, so use

$$\hat C_{pk} = \frac{\min(\bar x - \text{LSL},\; \text{USL} - \bar x)}{3s}.$$

**Worked example (M&F, valve).** $\text{LSL}=10.98$, $\text{USL}=11.01$, $\bar x=10.991$, $s=0.0035$. Then $\hat C_p=\frac{0.03}{6(0.0035)}=1.43$ (judged capable), but $\hat C_{pk}=\frac{\min(0.011,\,0.019)}{3(0.0035)}=1.048$ — much smaller, because the mean is off-center toward the LSL.

---

## 6. Tolerance Limits — vs confidence limits

A **tolerance interval** locates a stated proportion $P$ of the *population*, distinct from a confidence interval (which locates a *parameter*). As $n\to\infty$ a confidence interval shrinks to zero length, but tolerance limits approach the population values.

For a normal population with unknown $\mu,\sigma$, two-sided tolerance limits are

$$\bar x \pm K s,$$

where $K$ (from tolerance-factor tables, depending on $n$, the confidence level $1-\alpha$, and $P$) is chosen so that with $(1-\alpha)100\%$ confidence the interval contains at least proportion $P$ of the population. As $n$ grows, $K\to z$ for the chosen $P$ (e.g. $K\to1.96$ for $P=0.95$).

**One-sided tolerance bound.** For strength work it is the weak tail that matters; specify a lower percentile rather than the mean. A lower bound $L=\bar x - Ks$ (with $K$ from the one-sided table) gives $(1-\alpha)100\%$ confidence that at least proportion $P$ of the population exceeds $L$ — equivalently, a one-sided confidence bound on the lower percentile.

**Worked example (M&F, springs).** $n=100$, $\bar x=1.507$, $s=0.004$, $1-\alpha=0.99$, $P=0.95$ gives $K=2.335$, so $\bar x\pm Ks = (1.497,\,1.517)$: with 99% confidence, at least 95% of springs have free length in that interval. (Round lower limits down, upper limits up.)

---

## 7. Do's and Don'ts

- **Do** confirm the process is stable — no trends in level or spread — before computing a central line and limits.
- **Do** keep improving by reducing variation even after the process is in control; getting $6\sigma$ inside spec is only the first step.
- **Don't** confuse control limits (from process variation) with specification limits (from engineering): a controlled process may still be incapable.
- **Don't** ignore dependence between adjacent plotted points — even moderate autocorrelation badly degrades chart performance; check pairs $(\bar x_i, \bar x_{i-1})$.
- **Do** use a CUSUM (or the 9-in-a-row / 6-trending rules) to catch small sustained shifts the basic Shewhart limits miss.
