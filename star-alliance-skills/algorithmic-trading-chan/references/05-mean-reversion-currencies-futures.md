# Chapter 5 — Mean Reversion of Currencies and Futures

Most currencies and futures are momentum-dominated, and most cross-sectional currency/futures portfolios do not mean-revert. The exception is futures calendar spreads, where both legs track the same underlying and where the roll-return component creates a stationary signal. The chapter's second thread is mechanical: getting backtested currency returns right (quote-currency matching, rollover interest, settlement-day conventions) and understanding the spot-return + roll-return decomposition of futures total returns.

## The "Commodity Currencies" Cluster

**Idea:** Form stationary currency portfolios the same way you would for international stock-index ETF pairs: by selecting currencies whose issuing countries share similar economic fundamentals.

**Rationale:** The same macro drivers that make stock-index ETFs cointegrate (e.g., EWA/EWC for Australia/Canada) should also make the underlying currencies cointegrate. Resource-export economies especially share common shocks through commodity prices, so traders group AUD, CAD, NOK, and ZAR as "commodity currencies."

**Method:** Pick a cluster of countries with similar fundamentals; test the resulting currency basket for cointegration and trade mean reversion of the spread.

**Takeaway:** Liquidity, leverage, no short-sale constraints, and 24-hour trading make currencies a structurally better vehicle for pair trading than the corresponding national ETFs.

## Cross-Rate Mechanics: Why Quote-Currency Matching Matters

**Idea:** Before running a cointegration test on two currencies, force them onto a common quote currency so that a one-point move in each has the same dollar value.

**Rationale:** Johansen eigenvectors and hedge ratios are interpreted as capital weights. If the two legs have different quote currencies, point moves have different dollar values and the test is meaningless. The same logic means an "AUD.ZAR" trade is usually implemented synthetically via USD (e.g., USD.ZAR / USD.AUD), because few brokers offer exotic cross-rates directly.

**Method:**
1. Convert both legs so the quote currency is the local (account) currency — e.g., use AUD.USD and CAD.USD rather than USD.AUD and USD.CAD.
2. Run the cointegration/Johansen test on the converted series.
3. To execute live, map each synthetic "Buy 1 of B.USD" into "Sell 1/y of USD.B" where y is the current USD.B quote.
4. At every round-trip, convert realized P&L in B and Q back to local currency, otherwise the accumulated foreign balances will cause backtest and live results to diverge.

**Formula / rule:** Portfolio return with n₁ units of B₁.USD and n₂ units of B₂.USD is
$$r_{t+1} = \frac{n_1 y_{1,U}(t)\, r_{1}(t+1) + n_2 y_{2,U}(t)\, r_{2}(t+1)}{|n_1|\, y_{1,U}(t) + |n_2|\, y_{2,U}(t)}, \quad r_i(t+1) = \frac{y_{i,U}(t+1) - y_{i,U}(t)}{y_{i,U}(t)}.$$
If the legs are instead priced in USD.Q form (n′₁ of USD.Q₁, n′₂ of USD.Q₂), the simpler form applies because one unit of USD.Qᵢ is worth exactly one USD. For B₁.Q₁ vs B₂.Q₂ with neither leg using the local currency, the same Equation 5.1 holds but the return uses log price differences of y_{i,Qi}.

**Takeaway:** The hardest part of currency arbitrage is data preparation, not signal design. Quote-currency mismatch is a silent killer of backtests.

## Pair Trading USD.AUD vs USD.CAD with the Johansen Eigenvector

**Idea:** A linear mean-reversion strategy on AUD.USD vs CAD.USD using a Johansen-estimated hedge ratio and a z-score entry signal.

**Rationale:** Forcing both legs to the same quote currency makes the Johansen eigenvector interpretable as dollar capital weights and lets the strategy capture the mean reversion of the resource-economy currency pair.

**Method:**
1. Reconstruct price series as `aud = AUD.USD` and `cad = 1 / USD.CAD` so both are quoted in USD per unit of base currency.
2. For each day `t` after an initial window, fit a Johansen model on the prior 250 days of `log(y)` with zero lag and one cointegrating vector; take the first eigenvector as the hedge ratio.
3. Compute the z-score of the spread `yport = h'·y` over a 20-day lookback.
4. Set `numUnits = -zScore` (short the spread when above its mean, long when below).
5. Translate `numUnits` into dollar market values of each leg via `positions = numUnits · hedgeRatio · y`.
6. Daily P&L in USD = sum over legs of (yesterday's dollar position) × (today's simple return). Daily portfolio return = P&L divided by total gross dollar market value at yesterday's close.

**Findings:** APR ≈ 11%, Sharpe ≈ 1.6 over Dec 18 2009 – Apr 26 2012.

**Takeaway:** Using unequal hedge ratios on a properly quote-matched pair beats trading the ready-made cross-rate with a hedge ratio of one.

## Rollover Interest Mechanics

**Idea:** Holding a currency cross-rate past the 5:00 p.m. ET rollover earns (or pays) the interest differential between base and quote currencies, and the per-day accrual is multiplied by the number of closed-market days that follow.

**Rationale:** Currency trading is a "carry" instrument; the financing leg of total return matters whenever a position is held overnight, and an inaccurate rollover will bias Sharpe ratios of overnight strategies.

**Method / rule:**
- Long B.Q overnight accrues `i_B − i_Q` per day; if `i_Q > i_B` it is a debit.
- Standard T+2 settlement: a position held past 5 p.m. ET on Wednesday pays/collects three days of rollover (Saturday, Sunday).
- USD.CAD and USD.MXN settle T+1, so the triple accrual only applies when day T+2 is closed — i.e., only when held past 5 p.m. ET on Thursday.
- Financing cost is zero for intraday FX, equity long-short (roughly), and futures; for cross-rate positions held overnight, the correct excess return is
$$r_{t+1} = \log y_{B.Q}(t+1) - \log y_{B.Q}(t) + \log(1 + i_B(t)) - \log(1 + i_Q(t)).$$

**Takeaway:** Add rollover to the return formula — Sharpe of an FX strategy that misses a 5% annualized carry adjustment is misstated.

## AUD.CAD with Rollover Interest

**Idea:** A simpler mean-reversion variant that trades the ready-made AUD.CAD cross-rate rather than a synthetic pair, with rollover interest included.

**Rationale:** Demonstrates the magnitude of carry-driven error in practice: even with a single-digit-percent annualized carry, the Sharpe moves meaningfully when rollover is dropped.

**Method:**
1. Build the z-score from a 20-day lookback on `dailyCl`.
2. Apply the "triple-Wednesday" rule to AUD rates and the "triple-Thursday" rule to CAD rates.
3. Daily strategy return = `−sign(lagged z) × (log price change + log(1+aud rate) − log(1+cad rate))`.

**Findings:** APR 6.2%, Sharpe 0.54 over the tested period. Neglecting rollover bumps APR to 6.7% and Sharpe to 0.58, even though the annualized average rollover is ~5%.

**Takeaway:** A non-unity hedge ratio (Example 5.1) earned Sharpe 1.6 vs 0.54 here — the carry-aware, non-unity hedge structure was the real source of edge, not just the rollover fix.

## Roll Return, Backwardation, and Contango

**Idea:** A futures contract's total return decomposes into a spot return (driven by the underlying) and a roll return (driven by the slope of the forward curve as the contract approaches expiry).

**Rationale:** Both legs of a calendar spread share the same underlying, so any mean reversion of the spread must come from the roll-return component, not the spot component. Without this decomposition, a strategy based on a cointegrating spot relationship can be silently destroyed by the roll return.

**Method — the constant-returns model:**
$$F(t,T) = c\, e^{\alpha t}\, e^{\gamma (t-T)},$$
where α is the (compounded) spot return and γ is the (compounded) roll return. Total return = α + γ; roll return alone is γ.

**Definitions:**
- **Backwardation:** near contracts price above far contracts → upward-sloping log-price curve → γ > 0 (positive roll return).
- **Contango:** near contracts price below far contracts → downward-sloping log-price curve → γ < 0 (negative roll return).

**Mnemonic (Keynes/Hicks):** "Backwardation" is the "normal" state where hedgers (farmers, oil producers) short and speculators must be paid to go long, so futures price below expected future spot.

**Pitfalls:**
- The constant-returns model is a mnemonic, not a proof; real log price curves are not linear and far contracts often do not sit on the same line.
- A cointegrating relationship to the spot price (e.g., an ETF of commodity producers like XLE vs the spot commodity) does **not** imply cointegration to the futures price. Chan flags this as a $100,000 lesson from his first year of independent trading (2006).

## Estimating α and γ by Regression

**Idea:** Estimate the spot return α by regressing log spot prices on time, and the roll return γ by regressing the log prices of the five nearest futures contracts on their time-to-maturity each day.

**Rationale:** Linear regression gives a clean separation of the two return sources and lets you compare them across markets; it also diagnoses whether the model is even applicable to a given contract (the line should fit the first five contracts reasonably).

**Method:**
1. Spot return α: regress `log(spot)` on a time index (in trading days); annualize the slope by ×252.
2. Roll return γ: at each day, regress `log(prices of 5 nearest contracts)` on time-to-maturity in months; take −12 × the slope, and only when all five contracts are present and consecutive in maturity.
3. Validate by scatter-plotting log prices vs time-to-maturity at a single point in time (e.g., CL 2007 Jan–May); the points should fall on a straight line.

**Findings — Table 5.1, average annualized α and γ:**

| Symbol | α (spot) | γ (roll) |
|--------|----------|----------|
| BR (CME) | −2.7% | 10.8% |
| C (CBOT) | 2.8% | −12.8% |
| CL (NYMEX) | 7.3% | −7.1% |
| HG (CME) | 5.0% | 7.7% |
| TU (CBOT) | −0.0% | 3.2% |

Erb & Harvey (Dec 1982 – May 2004) report heating oil roll return 4.6% vs spot return 0.93%. The VX future has been in contango roughly three-quarters of the time with average annualized roll return of about −50% (Simon & Campasano, 2012).

**Takeaway:** Roll returns can dwarf spot returns; for BR, C, and TU the magnitude of γ exceeds α, which is why naive spot-based intuition about futures is so often wrong.

## Do Calendar Spreads Mean-Revert?

**Idea:** A long-far / short-near calendar spread's log market value equals γ·(T₂ − T₁), so the spread's trading signal depends only on the roll return γ, not on the spot price.

**Rationale:** Both legs move one-for-one with the underlying, so spot cancels out. The stationary quantity that drives the spread is γ itself, which is why calendar-spread mean reversion is plausible even when the outright futures does not mean-revert.

**Method:** Treat the time series of γ as the signal: compute its half-life (via AR(1) regression of Δγ on lagged γ), set the lookback equal to the half-life, then trade a z-score mean-reversion of γ with the spread held for ~3 months before rolling 10 days before the near-contract expiry.

**Pitfall — the VIX/VX trap:** The VIX *index* is stationary (ADF at 99%), but the back-adjusted front-month VX *future* is not, because the −50% roll return dominates. Mean-reverting VIX does not imply a mean-reverting VX trade.

## CL 12-Month Calendar Spread (Example 5.4)

**Idea:** Linear mean-reversion of γ on the 12-month CL calendar spread, with explicit contract selection, holding period, and roll rules.

**Rationale:** The roll return γ for CL is plausibly slow-moving around a stable mean; using γ directly as the signal isolates the only return component the spread actually carries.

**Method:**
1. Compute γ day-by-day as in Example 5.3; ADF-test it (here, 99% stationary) and estimate the half-life (here, 36 days).
2. Set lookback = round(half-life) for moving average and standard deviation of γ; form the z-score.
3. For each pair of contracts (c, c+12) on each historical day, hold a long-far / short-near spread for 61 trading days, rolling 10 days before the near contract's expiration. Require that the previous pair's end-date precedes the next pair's start-date (no overlap).
4. Flip the sign of the position when z > 0 (spread expensive → long near / short far).
5. Daily return = sum of lagged positions × contract simple returns, divided by 2 (two contracts).

**Findings:** Unlevered APR 8.3%, Sharpe 1.3, Jan 2 2008 – Aug 13 2012.

**Takeaway:** Calendar spreads of traded-asset futures can be reliable when the roll return itself is stationary; the signal is γ, not price.

## VX Calendar Spreads

**Idea:** Trade the ratio of the back-month to front-month VX contracts, since the underlying VIX is not a traded asset and Equation 5.7 fails for VX.

**Rationale:** The simple model F = S·e^{γ(t−T)} requires a tradeable underlying, and log VX prices do not fall on a straight line against time-to-maturity. Empirically, however, the back/front ratio is stationary at 99% confidence, and a z-score mean-reversion strategy works post-2008.

**Method:** Standard linear mean-reversion strategy on the back/front ratio, with a 15-day moving-average and standard-deviation lookback.

**Findings:** APR 17.7%, Sharpe 1.5, Oct 27 2008 – Apr 23 2012. Performance was materially worse before October 2008.

**Pitfall:** A regime change around the 2008 financial crisis splits the sample. A backtest that pools both regimes will understate post-crisis edge but overstate the pre-crisis Sharpe.

## Intermarket Spreads: Crack Spread and CL-BZ

**Idea:** Test the most obvious "same-complex" futures pairs for mean reversion before searching further afield.

**Rationale:** Energy-cracking economics and Brent-WTI substitution are textbook examples of economically tight links, so if any intermarket futures spreads are stationary, these should be.

**Findings — crack spread (long 3 CL, short 2 RB, short 1 HO):** ADF test from May 20 2002 – May 4 2012 is **not** stationary; a large jump Mar 9 2007 – Jul 3 2008 followed by a sharp reversal produced negative P&L under a linear-mean-reversion strategy. NYMEX offers this as a basket with lower margin than the components.

**Findings — CL vs BZ (1:1):** Not stationary. BZ has persistently outperformed CL, plausibly due to rising U.S. oil production, the Cushing pipeline bottleneck, and the 2012 Iran-embargo effect on European-priced BZ.

**Pitfalls:**
- Back-adjust continuous contracts using *prices*, not returns, when running price-spread tests — return-based adjustment creates a spurious jump at rollovers.
- Synchronize closing times across exchanges. BZ traded in London (different close) before NYMEX listing on Sep 5 2001, so pre-2001 BZ-CL closing-price backtests are contaminated.
- Convert points to dollars (multiply by contract multiplier) before computing a hedge ratio.

## VX vs ES: A Stationary Vol/Equity Intermarket Spread

**Idea:** Use the post-crisis inverse relationship between the S&P 500 E-mini (ES) and VIX future (VX) to form a stationary two-contract portfolio and trade deviations from a training-set mean.

**Rationale:** Vol and equity are reliably anti-correlated, and the post-Aug-2008 sample shows a clean linear relationship with a tighter volatility regime than the 2004–2008 sample. Pooling both regimes would mix two different regressions and destroy the trade.

**Method:**
1. Identify the second regime (Aug 2008 onward) by scatter-plotting ES vs VX; the cluster is visually distinct from the 2004–May 2008 cluster.
2. Convert to dollar units: multiply VX prices by 1,000 and ES prices by 50 so point moves are comparable.
3. Train on the first 500 days of the post-Aug-2008 sample; regress `ES × 50` on `VX × 1,000`. Result: ES × 50 = −0.3906 × VX × 1,000 + $77,150; residual std dev = $2,047.
4. Form the stationary portfolio: long 1 ES, long 0.3906 VX (per the regression). Short this portfolio whenever its market value exceeds the mean by one residual standard deviation (Bollinger-band style).

**Findings:** APR 12.3%, Sharpe 1.4, Jul 29 2010 – May 8 2012. Profitability picked up notably around the time of the S&P U.S. credit-rating downgrade.

**Takeaway:** This is the rare intermarket futures spread that actually mean-reverts, and it works because the vol-equity link is structural rather than a cointegration accident — but only within a single volatility regime.
