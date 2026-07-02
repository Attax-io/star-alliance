---
type: Document
timestamp: 2026-07-02T12:28:13Z
---

# Chapter 2 — The Basics of Mean Reversion

This chapter lays the conceptual and statistical foundation for trading strategies that bet on prices reverting to a historical mean. It distinguishes mean reversion from trending behavior, introduces three formal tests (ADF, Hurst/Variance Ratio) for identifying stationary price series, extends those ideas to cointegrated portfolios via the CADF and Johansen tests, and presents a "parameterless" linear mean-reversion strategy as a benchmark.

## Mean Reversion vs. Returns

**Idea:** Most asset prices are not mean-reverting — they follow geometric random walks. What is mean-reverting (around zero) is the *return* series, but that is not directly tradable.

**Rationale:** There is a crucial distinction between mean reversion of *prices* (tradable) and mean reversion of *returns* (not directly tradable). Anti-serial-correlation of returns is equivalent to mean reversion of prices and is the basis for every mean-reversion strategy in the book. Misidentifying the stationary object — confusing "price comes back to its mean" with "next-day return is the opposite of today's" — is a common error that must be avoided.

**Method:** Always test and trade on the *price* (or, more commonly, the spread/portfolio) level, not the raw return series.

**Takeaway:** Trade the mean reversion of price levels, not the mean reversion of returns.

## Stationarity and Mean Reversion — Two Lenses, Same Object

**Idea:** A price series that is mean-reverting and a price series that is stationary are the same thing, viewed from two angles, giving rise to two families of tests.

**Rationale:** The two viewpoints are mathematically equivalent: if the next-period price change is proportional to the gap between the current price and its long-run mean, prices must diffuse more slowly than a geometric random walk. Both viewpoints must be exploited because no single test dominates the other.

**Method:**
- **Mean-reversion lens:** Δy(t) is proportional to (mean − y(t−1)). Tested by the ADF test on λ.
- **Stationarity lens:** Var(log y) grows sublinearly in time, of the form τ^(2H), with H < 0.5 (vs. H = 0.5 for a random walk). Tested by the Hurst exponent and Variance Ratio test.

**Formula / rule:** For a stationary (log) price, ⟨|z(t+τ) − z(t)|²⟩ ∼ τ^(2H), with H < 0.5. For a geometric random walk, H = 0.5. "Stationary" does *not* mean range-bound; it means the variance grows more slowly than linearly with time.

**Takeaway:** H < 0.5 is the single most useful scalar to summarize how strongly a series reverts to its mean; H > 0.5 indicates trending and rules out a mean-reversion strategy.

## Augmented Dickey-Fuller (ADF) Test

**Idea:** A regression-based test that asks whether the next period's price change depends on the current price level.

**Rationale:** If the next move is proportional to (mean − current price), then a negative λ in the regression is the signature of mean reversion; λ = 0 is the random-walk null. The test is the most direct statistical expression of the "buy low, sell high" intuition and is the workhorse for declaring a single price series stationary.

**Method:**
1. Run the regression Δy(t) = λ y(t−1) + μ + βt + α₁Δy(t−1) + … + αₖΔy(t−k) + εₜ.
2. For simplicity, set β = 0 (price drift is negligible vs. daily fluctuation in practice); keep μ ≠ 0.
3. Test the t-statistic λ/SE(λ) against Dickey–Fuller critical values (these depend on sample size and whether a non-zero mean / drift is allowed).
4. The hypothesis λ = 0 can be rejected only if λ/SE(λ) is *more negative* than the critical value.

**Formula / rule:** Δy(t) = λ y(t−1) + μ + α₁Δy(t−1) + … + αₖΔy(t−k) + εₜ, with β = 0 in practice. Reject random-walk null when λ/SE(λ) is sufficiently negative.

**Findings (USD.CAD example):**
- Lag k = 1 chosen (often necessary to reject the null).
- ADF t-statistic ≈ −1.84; AR(1) estimate ≈ 0.994.
- Critical values: 1% = −3.458, 5% = −2.871, 10% = −2.594.
- λ is negative, so USD.CAD is at least not trending, but the null cannot be rejected at the 90% level.

**Pitfalls:**
- Tests at intraday frequency do not increase statistical significance — sample at the cadence appropriate to your trading horizon.
- In practice, μ ≠ 0 and β = 0 are the right modeling choices for prices.

**Takeaway:** A negative but statistically insignificant λ is still useful information: it tells you the series is at least not trending.

## Hurst Exponent

**Idea:** A scalar H summarizing how fast the variance of log prices grows with the time lag τ.

**Rationale:** A geometric random walk has H = 0.5. Mean reversion is H < 0.5, and trending is H > 0.5. H therefore gives a *graded* measure of mean-reversion strength — the smaller H, the stronger the reversion — which is more informative than a binary ADF reject/fail-to-reject.

**Method:**
1. Take log prices z = log(y).
2. For several lags τ, compute ⟨|z(t+τ) − z(t)|²⟩.
3. Fit H from ⟨|z(t+τ) − z(t)|²⟩ ∼ τ^(2H). (Equivalently, regress log variance on log τ.)
4. Decision rule: H < 0.5 ⇒ mean-reverting; H > 0.5 ⇒ trending; H = 0.5 ⇒ random walk.

**Findings (USD.CAD):** H ≈ 0.49 — weakly mean-reverting.

**Pitfalls:** H alone has no confidence attached; the Variance Ratio test is needed to determine if H is statistically distinguishable from 0.5.

**Takeaway:** Use H as a continuous diagnostic of mean-reversion strength; pair it with the Variance Ratio test for statistical significance.

## Variance Ratio Test

**Idea:** A formal significance test for the null hypothesis that the Hurst exponent equals 0.5 (i.e., the series is a random walk).

**Rationale:** Because H is estimated from a finite sample, "H = 0.49" is not by itself evidence of mean reversion. The Variance Ratio test converts the H measurement into a proper hypothesis test, allowing a 90% (or higher) confidence rejection of the random-walk null.

**Method:** Test whether the ratio Var(z(t) − z(t−τ)) / [τ · Var(z(t) − z(t−1))] equals 1. Reject the random-walk null at 90% if the test's binary flag h = 1; pValue is the probability the null is true.

**Findings (USD.CAD):** h = 0, pValue ≈ 0.367 — cannot reject the random-walk null.

**Takeaway:** The Variance Ratio test is the formal significance companion to the Hurst exponent estimate.

## Half-Life of Mean Reversion

**Idea:** The λ coefficient from the ADF-style regression, reinterpreted as the exponential decay rate of the expected price toward its mean, gives a "half-life" — a time scale on which the mean reversion operates.

**Rationale:** Stationarity tests demand ≥ 90% confidence, but most profitable strategies do not need that level of certainty. The half-life is a more practical diagnostic: it tells you (a) whether mean reversion is fast enough to trade within your horizon, and (b) what natural time scale to use for look-back windows and holding periods — eliminating most parameter-optimization choices. It is the bridge between a statistical property of the series and a parameter choice for a strategy.

**Method:**
1. Run the regression Δy(t) = λ y(t−1) + μ + εₜ (ignoring drift and lagged differences).
2. Compute half-life = −log(2) / λ. This is the time for the expected price to halve its distance to the long-run mean −μ/λ.
3. Interpretation:
   - λ > 0 ⇒ do not run a mean-reversion strategy.
   - λ ≈ 0 ⇒ half-life too long to be profitable.
   - Set look-back and expected holding period to a small multiple of the half-life.

**Formula / rule:** E[y(t)] = y₀ exp(λt) − (μ/λ)(1 − exp(λt)); half-life = −log(2)/λ. This is the continuous-time Ornstein–Uhlenbeck form of the discrete ADF regression.

**Findings:**
- USD.CAD: half-life ≈ 115 days — possibly too long depending on horizon.
- EWA–EWC–IGE portfolio (best Johansen eigenvector): half-life = 23 days.

**Takeaway:** Trade mean reversion only if half-life is short relative to your horizon, and use a small multiple of the half-life as the natural look-back.

## Linear Mean-Reverting Trading Strategy (Single Asset)

**Idea:** A truly parameterless benchmark: at each bar, hold a number of units equal to the *negative Z-Score* of the price relative to its moving average, using a look-back equal to the half-life.

**Rationale:** This strategy has *no fitted parameters* — even the look-back is set from a property of the price series itself (the half-life), not by curve-fitting to backtest performance. This eliminates data-snooping bias and provides an honest lower bound on the extractable signal: any reasonable refinement should beat it. It is the cleanest possible proof-of-concept that a series with a short enough half-life is tradable.

**Method:**
1. Compute half-life λ; set lookback = round(half-life).
2. Compute market value: mktVal = −(y − movingAvg(y, lookback)) / movingStd(y, lookback) — the negative Z-Score.
3. Daily P&L: pnl = lag(mktVal,1) · (y − lag(y,1)) / lag(y,1).
4. (Caveat: a moving window is needed even for "stationary" prices, because both the mean and the variance can drift slowly — variance grows as τ^(2H) with H > 0 even when H < 0.5.)

**Findings (USD.CAD):** Cumulative P&L is positive despite the long half-life, but with a large drawdown. No transaction costs are assumed.

**Pitfalls:**
- Look-ahead bias: the half-life is fit on the same in-sample data used for the backtest.
- Unlimited capital may be required; no max market value is imposed.
- No transaction costs.
- Not a practical strategy as stated.

**Takeaway:** The linear Z-Score strategy is a parameterless *benchmark*, not a production strategy. Use it to validate that a series has real mean-reversion signal; refine it (e.g., as in Chapter 5) before going live.

## Cointegration

**Idea:** Non-stationary assets can be combined linearly into a portfolio whose net market value *is* stationary. Such assets are called *cointegrating*.

**Rationale:** Almost no individual asset is stationary, but by shorting one asset against another we can synthesize a stationary spread. This is the foundation of pairs trading and its generalizations — and the source of most of the mean-reversion opportunities available to a trader. Pairs are not arbitrary: they are typically linked by a real economic link (e.g., two commodity-driven economies, or miners and the metal they produce), which both makes the cointegration more durable *and* allows the trader to anticipate when the relation will break.

**Method:** Construct the portfolio's net market value as the linear combination y_port = Σ wᵢ · yᵢ (weights = hedge ratios). Test whether y_port is stationary. The hedge ratios are not given a priori — they are estimated from the data.

**Pitfalls:** A set of price series being cointegrating does *not* mean that *any* random linear combination is stationary. Hedge ratios matter.

**Takeaway:** Cointegration manufactures stationarity from non-stationary ingredients, vastly expanding the tradable universe beyond the small set of intrinsically stationary series.

## CADF (Cointegrated ADF) Test

**Idea:** For a pair of assets, the Engle–Granger two-step procedure: regress one price on the other to estimate the hedge ratio, then ADF-test the regression residuals for stationarity.

**Rationale:** For a pair we don't know the hedge ratio in advance. The CADF test combines hedge-ratio estimation and stationarity testing in one routine.

**Method:**
1. Choose an independent variable (say EWA) and a dependent variable (EWC).
2. Regress y on x; take the slope as the hedge ratio.
3. Form the residual spread and ADF-test it.
4. Compare t-statistic to CADF critical values (not the same as ADF critical values, since the residual is estimated).

**Findings (EWA–EWC):**
- Hedge ratio from OLS of EWC on EWA.
- CADF t-statistic ≈ −3.64; critical values: 1% = −3.880, 5% = −3.359, 10% = −3.038.
- Reject the null at 95% — EWA and EWC are cointegrating.

**Pitfalls (the central pitfall of CADF):**
- The test is **order-dependent**. The hedge ratio obtained by regressing EWC on EWA is not the exact reciprocal of the one obtained by regressing EWA on EWC. In many cases, only one ordering yields a stationary spread.
- Workaround: try each asset as the independent variable, and use the ordering that gives the most negative t-statistic.
- The Johansen test removes this order-dependence entirely.

**Takeaway:** CADF is fine for pairs but forces a trial of both orderings; the Johansen test is the order-independent generalization.

## Johansen Test

**Idea:** A multivariate test for cointegration across any number of price series, which simultaneously estimates the number of cointegrating relations *and* the hedge ratios (eigenvectors) that form them.

**Rationale:** CADF is order-dependent and limited to pairs. Johansen expresses the regression in matrix form and performs an eigen-decomposition, yielding (a) the count of independent stationary spreads that can be formed and (b) the optimal hedge ratios for each — all in one shot. As a by-product, the eigenvectors give the trader ready-made portfolio weights.

**Method:**
1. Stack the price series as columns of a matrix Y.
2. Fit the vector AR model ΔY(t) = Λ Y(t−1) + M + A₁ ΔY(t−1) + … + Aₖ ΔY(t−k) + εₜ, with β = 0.
3. Eigen-decompose Λ. The rank r of Λ equals the number of independent cointegrating relations.
4. Test r = 0, r ≤ 1, …, r ≤ n−1 using two statistics (Trace and Eigen) with tabulated critical values.
5. The eigenvectors (columns of evec, ordered by decreasing eigenvalue) are the hedge ratios. Pick the eigenvector with the largest eigenvalue for the strongest (shortest half-life) stationary portfolio.
6. Compute y_port = eigenvector · Y elementwise, summed across assets; then compute its half-life via the same OLS regression as in the single-asset case.

**Findings (EWA–EWC):**
- Trace: r ≤ 0 statistic 19.983 vs. 99% crit 19.935 (rejected at 99%); r ≤ 1 statistic 3.983 vs. 95% crit 3.841 (rejected at 95%).
- Eigen: r ≤ 0 statistic 16.000 vs. 95% crit 14.264 (rejected); r ≤ 1 statistic 3.983 vs. 95% crit 3.841 (rejected).
- Conclusion: two cointegrating relations from two price series — a consequence of CADF's order-dependence, both relations are stationary.

**Findings (EWA–EWC–IGE):**
- Trace: r ≤ 0 = 34.429 (95% crit 29.796, reject); r ≤ 1 = 17.532 (95% crit 15.494, reject); r ≤ 2 = 4.471 (95% crit 3.841, reject).
- Eigen: r ≤ 0 = 16.897 (fail at 95%); r ≤ 1 = 13.061 (reject at 95%); r ≤ 2 = 4.471 (reject at 95%).
- Net: three cointegrating relations across three series.
- Eigenvalues: 0.0112, 0.0087, 0.0030; the largest corresponds to the strongest (shortest half-life) relation.
- Best-eigenvector portfolio: half-life = 23 days.

**Takeaway:** Use the Johansen test whenever you have more than two candidate assets, and use the largest-eigenvalue eigenvector as your hedge ratio — it is the stationary portfolio with the shortest half-life.

## Linear Mean-Reverting Strategy on a Portfolio (Spread)

**Idea:** Apply the same negative-Z-Score rule as the single-asset strategy, but to the *unit portfolio's* price (the eigenvector-weighted combination of the underlying assets).

**Rationale:** Once the Johansen test has yielded a short-half-life stationary spread, the same parameterless linear strategy is a clean, data-snooping-free benchmark. The strategy's "linearity" refers to the number of *units* (proportional to negative Z-Score), not the dollar market value. Continuously entering and exiting small positions gives more statistical observations than a backtest with discrete entry/exit rules, increasing the reliability of the measured Sharpe.

**Method:**
1. Set lookback = round(half-life of the spread).
2. numUnits = −(y_port − movingAvg(y_port, lookback)) / movingStd(y_port, lookback).
3. Compute per-asset dollar positions: positions = numUnits · eigenvector · Y (broadcast).
4. Daily P&L: pnl = Σ lag(positions) · (Y − lag(Y)) / lag(Y).
5. Return: pnl / Σ |lag(positions)|.

**Findings (EWA–EWC–IGE):** APR = 12.6%, Sharpe ratio = 1.4. (No transaction costs; in-sample look-back for the half-life.)

**Pitfalls:**
- Look-ahead bias from in-sample half-life estimation.
- No cap on capital required.
- The strategy is not directly tradeable (fractional shares, infinite position sizes), but it is the *honest* benchmark for the signal strength of the spread.

**Takeaway:** Run this parameterless linear strategy on every short-half-life spread you find; it is the cleanest unbiased way to confirm that the signal is real.

## Pros and Cons of Mean-Reverting Strategies

**Pros:**
- **Wide universe:** You are not limited to intrinsically stationary assets — you can synthesize stationarity via cointegration, dramatically expanding the opportunity set. Each year's new, marginally differentiated ETFs add further candidates.
- **Fundamental grounding:** Cointegrating pairs usually have a real economic link (e.g., two commodity-driven economies, or a gold miner and gold itself), giving the trader both prior conviction and a way to anticipate *when* a relation will break. This stands in contrast to momentum strategies, which require belief in "greater fools."
- **Wide range of time scales:** From sub-second market-making to multi-year fundamental value investing, mean reversion spans every horizon. Shorter time scales imply more trades, higher statistical confidence, and higher compounded Sharpe.

**Cons / Pitfalls:**
- **Consistency breeds overconfidence and overleverage.** A long string of small wins encourages maximum leverage right before the regime change.
- **The rare loss is catastrophic.** When the mean-reversion relation breaks, it typically does so abruptly and after a long winning streak — exactly when positions are largest. The canonical example is Long-Term Capital Management.
- **Stop losses are hard to deploy logically.** A mean-reversion strategy is *designed* to buy more as the price moves further from the mean; placing a stop loss on the spread conflicts with the model's logic. Risk management for mean-reverting strategies is therefore a specialized topic (deferred to Chapter 8).
- **Cointegration can quietly fail.** Even pairs with strong fundamental links can decouple (e.g., GDX/GLD around early 2008 when high energy prices made gold mining abnormally expensive). Recognizing the breakdown often requires hindsight.

**Takeaway:** Mean reversion offers the cleanest statistical opportunities in algorithmic trading, but its very consistency makes it dangerous at maximum leverage; risk management, not signal discovery, is the binding constraint.

## Why Test Stationarity Before Backtesting?

**Idea:** Stationarity tests are a higher-statistical-power gate on a candidate series than a backtest of any specific strategy.

**Rationale:** A stationarity test uses every bar of the price series, whereas a backtest generates a much smaller number of round-trip trades and is contingent on the specific parameters and rules chosen. If the series itself fails the stationarity test, no strategy on it is likely to be robust. If it passes (or has a short enough half-life), the trader is assured that *some* parameterless strategy (the linear Z-Score rule) is profitable, even if the specific backtested strategy isn't.

**Method:** Always run ADF / Variance Ratio / half-life diagnostics before any backtest, as a pre-filter and as the source of natural parameter choices (e.g., look-back).

**Takeaway:** The statistical tests are not bureaucratic; they replace fragile backtest-based signal discovery with a more powerful inference on the price series itself.
