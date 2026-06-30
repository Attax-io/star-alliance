# Chapter 3 — Implementing Mean Reversion Strategies

This chapter moves from the stationarity/cointegration tests of Chapter 2 to practical, tradable mean reversion strategies. It covers signal construction via price spreads, log price spreads, and ratios; the Bollinger band strategy as a practical alternative to the linear mean reversion strategy; a theoretical critique of scaling-in; and the Kalman filter as a tool for dynamically estimating hedge ratios, mean prices, and variances. The chapter closes with a warning that data errors inflate mean reversion backtests and trigger losing live trades.

## Trading Pairs: Price Spread, Log Price Spread, or Ratio

**Idea:** Construct a stationary signal for pairs/portfolio mean reversion in one of three ways: (1) linear price spread with hedge ratios, (2) log price spread with hedge ratios, or (3) price ratio.

**Rationale:** Each construction gives a different interpretation of "stationary portfolio." Price spreads (with hedge ratio h) imply a fixed number of shares per asset; the portfolio has no implicit cash, and rebalancing is not required. Log price spreads (with capital weights h) imply fixed dollar capital allocation per asset, which forces an implicit cash component and constant rebalancing. Ratios are useful when the pair is not truly cointegrating: if A and B both scale (e.g., A = $10, B = $5 → A = $100, B = $50), the spread can drift to non-stationary territory while the ratio stays flat, so a ratio-based signal can still capture short-term mean reversion.

**Method — Price spread:** Regress y₂ on y₁ via OLS or Johansen eigenvector, set h = regression coefficient, form spread y = y₁ − h·y₂. The h's give the number of shares of each asset.

**Method — Log price spread:** Regress log(y₂) on log(y₁), form log(q) = h₁ log(y₁) + h₂ log(y₂) + … + hₙ log(yₙ). The h's are interpreted as fixed capital weights, which implies an implicit cash leg that must be rebalanced.

**Method — Ratio:** Form y₁/y₂. This is theoretically equivalent to log-price cointegration only if the hedge ratios are equal in magnitude (h₁ = −h₂), which is a special case. In general, the ratio is not a stationary series. However, it is a useful signal when the pair is not truly cointegrating but you believe the short-term spread mean reverts, and it eliminates the need for a dynamically changing hedge ratio.

**Special case — FX:** Trading EUR.GBP is exactly trading the ratio USD.EUR/USD.GBP, so FX pairs naturally use ratios. For cross rates not directly tradable (e.g., MXN.NOK), the ratio USD.NOK/USD.MXN may be a more effective signal than the price spread, but be aware the two approaches generate P&L in different currencies.

**Pitfalls:** Log-price spreads require constant rebalancing to maintain constant capital weights, generating higher transaction costs than price spreads. Ratios may not be optimal when the pair is cointegrating; in the GLD-USO example, price spreads with an adaptive hedge ratio dominate.

## Example 3.1: GLD-USO — Comparing the Three Signals

**Idea:** Test the linear mean reversion strategy on GLD (gold ETF) and USO (oil ETF) using each of the three signal types, even though GLD and USO are not cointegrated.

**Rationale:** GLD and USO are believed by some traders to be linked via inflation, but cointegration tests reject this. The example still tests for short-term mean reversion to see if a trading signal exists.

**Method:**
- **Price spread:** Recalculate hedge ratio daily via OLS over a 20-trading-day lookback. Spread = USO − h·GLD. Trade it as a linear mean reversion strategy (numUnits = −z-score of spread). Long GLD, short USO, or vice versa.
- **Log price spread:** Same procedure but regress log(USO) on log(GLD) over the 20-day lookback. Implied portfolio requires daily rebalancing to keep capital weights constant.
- **Ratio:** Form USO/GLD as the signal. Drop the first 20 observations to align test sets. Apply the same linear z-score strategy with equal dollar capital on the long and short side.

**Findings (no transaction costs, with look-ahead bias acknowledged):**
- Price spread with dynamic hedge ratio: APR ≈ 10.9%, Sharpe ≈ 0.59.
- Log price spread: APR = 9%, Sharpe = 0.5 (lower than price spread, and worse after accounting for the rebalancing costs).
- Ratio: negative APR (ratio does not look stationary).

**Takeaway:** For non-cointegrated ETF pairs in this example, price spreads with a short adaptive lookback beat log price spreads, and both beat the ratio.

## Bollinger Bands as a Practical Mean Reversion Strategy

**Idea:** Replace the linear strategy's "scale in proportion to z-score" with a discrete entry/exit band: enter long/short when the z-score crosses ±entryZscore, exit when it reverts to exitZscore.

**Rationale:** The linear strategy demands infinitesimal rebalancing and unbounded buying power, because deviations from the mean are unbounded. Bollinger bands cap capital exposure, holding at most one unit of the portfolio at any time, which makes risk and capital allocation manageable. Setting exitZscore lower than entryZscore (e.g., 0) realizes profits before full reversion, which is essential when the series is only short-term mean reverting rather than truly stationary.

**Method:**
1. Compute z-score of the spread (or log spread, or price series) using a moving mean and moving standard deviation over a lookback period (often set to the half-life of mean reversion).
2. Generate entry signals: long entry when z < −entryZscore, short entry when z > entryZscore.
3. Generate exit signals: long exit when z ≥ −exitZscore, short exit when z ≤ exitZscore.
4. Maintain numUnitsLong and numUnitsShort arrays, set to 1 (or −1) on entry, 0 on exit, and forward-fill between events.
5. Combine: numUnits = numUnitsLong + numUnitsShort; build positions and P&L as in the linear strategy.

**Formula / rule:**
- z(t) = (y(t) − MA_t) / SD_t, with MA and SD computed over a rolling lookback.
- Long entry if z < −entryZscore; exit when z ≥ −exitZscore, with exitZscore < entryZscore.
- If exitZscore = 0, exit at the moving average. If exitZscore = −entryZscore, exit only when the z-score crosses the opposite band (a "stop-and-reverse" pattern).

**Pitfalls:** Both entryZscore and the lookback are free parameters subject to optimization bias and data-snooping if not handled carefully with a separate training set. The strategy is sensitive to data errors (see below). Shorter lookbacks with small entry/exit z-scores yield more round trips and generally higher profits but also more transaction costs in live trading.

## Example 3.2: Bollinger Band on GLD-USO

**Idea:** Apply a Bollinger band strategy (entryZscore = 1, exitZscore = 0) to the GLD-USO price spread from Example 3.1.

**Method:** Identical spread construction to Example 3.1 (20-day OLS hedge ratio). Then apply the band logic with entryZscore = 1, exitZscore = 0, using a fillMissingData routine to carry positions forward on non-event days.

**Findings:** APR = 17.8%, Sharpe ratio = 0.96 — a substantial improvement over the linear mean reversion strategy on the same spread (10.9% / 0.59).

**Takeaway:** A discrete-entry Bollinger band is materially more profitable than the equivalent linear strategy on a non-cointegrated pair, supporting the book's preference for band-based execution over proportional scaling.

## Does Scaling-in Work?

**Idea:** "Average-in" / "scale-in" strategies add to a position as the price deviates further from its mean. Schoenber and Corwin (2010) prove this is never optimal under constant transition probabilities.

**Rationale:** Scaling-in is intuitive: deeper deviation = larger potential profit on reversion, plus reduced market impact for large orders. But the theoretical critique matters for strategy design.

**Method (Schoenberg-Corwin illustration):** A future drops to L1 and is expected to revert to F > L1, with probability p of going lower to L2 < L1 first. Compare three entry schemes, all with two contracts of capital:
- All-in at L1: expected profit = 2(F − L1).
- All-in at L2: expected profit = 2p(F − L2).
- Average-in (one at L1, one at L2): expected profit = (F − L1) + p(F − L2).

**Formula / rule:** Transition threshold p̂ = (F − L1) / (F − L2). If p < p̂, all-in-at-L1 wins. If p > p̂, all-in-at-L2 wins. The average-in strategy is never the unique optimum.

**Pitfalls:** The proof assumes p is constant over time. In practice, volatility (and hence p) is not constant, so scaling-in may produce a better realized out-of-sample Sharpe ratio even though it looks suboptimal in-sample. Scaling-in/averaging-out can also reduce market impact for large orders, which is not captured by backtest P&L.

**Takeaway:** Scaling-in is theoretically dominated under constant-volatility assumptions, but live volatility regimes shift, so it can still be useful — particularly as an execution tactic — even when it appears suboptimal in backtest.

## Kalman Filter as Dynamic Linear Regression

**Idea:** Replace the moving-window OLS hedge ratio with a Kalman filter that updates β(t) from β(t−1) plus noise, giving smooth time-varying weights and adaptive mean/volatility estimates.

**Rationale:** Moving-window regressions suffer from abrupt jumps when the oldest bar drops out and the newest bar enters. The Kalman filter avoids the arbitrary cutoff of a moving window by giving more weight to recent data without a hard cutoff, and it generates three quantities simultaneously: the dynamic hedge ratio, the dynamic mean of the spread (Kalman intercept), and the dynamic standard deviation of the forecast error (replacing the moving SD in a Bollinger band). It is optimal (minimum mean square error) under Gaussian noise assumptions.

**Method — Specification for a two-asset spread:**
- **Observable variable:** y(t), one of the two price series.
- **Hidden variable:** β(t) = [slope(t), intercept(t)]ᵀ, a 2×1 vector. The intercept doubles as the moving average of the spread.
- **Observation model:** x(t), the other price series, augmented with a column of ones to allow for nonzero intercept.
- **Measurement equation:** y(t) = x(t)·β(t) + ε(t), with ε ~ Gaussian(0, Vε).
- **State transition equation:** β(t) = β(t−1) + ω(t−1), with ω ~ Gaussian(0, Vω). State transition model is the identity matrix.
- **Initialization:** β̂(1|0) = 0, R(0|0) = 0.
- **Choice of Vω:** Following Montana et al. (2009), Vω = δ/(1−δ) · I, with δ ∈ (0,1). δ = 0 freezes β (ordinary OLS with offset); δ = 1 makes β chase the latest observation wildly. Vε is set by training (e.g., Vε = 0.001 in Example 3.3). Optimal δ and Vε can be estimated by autocovariance least squares (Rajamani & Rawlings, 2007, 2009).

**Box 3.1 — Iterative Kalman equations:**
- State prediction: β̂(t|t−1) = β̂(t−1|t−1).
- State covariance prediction: R(t|t−1) = R(t−1|t−1) + Vω.
- Measurement prediction: ŷ(t) = x(t)·β̂(t|t−1).
- Measurement variance prediction: Q(t) = x(t)·R(t|t−1)·x(t)ᵀ + Vε.
- Forecast error: e(t) = y(t) − ŷ(t).
- Kalman gain: K(t) = R(t|t−1)·x(t)ᵀ / Q(t).
- State update: β̂(t|t) = β̂(t|t−1) + K(t)·e(t).
- State covariance update: R(t|t) = R(t|t−1) − K(t)·x(t)·R(t|t−1).

**Trading application:** The forecast error e(t) is the deviation of the spread from its Kalman-predicted mean, and √Q(t) is its predicted standard deviation. Replace the Bollinger band z-score with e(t)/√Q(t) for entry and exit decisions.

**Pitfalls:** The four-quantity specification (observable, hidden, state model, observation model) is the only creative part; the rest is mechanical. Vω and Vε must be set or estimated, or results will be poor. δ = 0 collapses the filter to OLS; δ = 1 makes it over-fit. The Kalman filter is linear and Gaussian; departures (heavy tails, regime shifts) degrade it.

## Example 3.3: Kalman Filter on EWA-EWC

**Idea:** Apply the Kalman filter to estimate a dynamic hedge ratio between EWA and EWC, then trade the resulting spread with a Bollinger band on the forecast error.

**Method:** Set x = EWA prices (augmented with a column of ones), y = EWC prices. Use δ = 0.0001 and Vε = 0.001 (chosen with hindsight). Run the Kalman recursion of Box 3.1. Treat the slope β(1, t) as the hedge ratio, the forecast error e(t) as the spread deviation, and √Q(t) as its standard deviation. Long entry when e(t) < −√Q(t), exit when e(t) > −√Q(t); symmetric for shorts.

**Findings:** APR = 26.2%, Sharpe ratio = 2.4 on EWA-EWC. The Kalman slope oscillates around 1 (consistent with the two ETFs tracking similar markets), and the Kalman intercept grows monotonically over time.

**Pitfalls:** These results use a look-ahead-selected δ and Vε, and ignore transaction costs. The filter is sensitive to the choice of δ and Vε, which should be cross-validated out of sample.

## Kalman Filter as Market-Making / Fair-Value Model

**Idea:** Use the Kalman filter on a single mean-reverting price series to update an estimate of the fair value m(t) from trade prints, with measurement noise Vε that depends on trade size.

**Rationale:** Market makers continuously update their estimate of an asset's "true" price. Larger trades carry more information than smaller trades, so they should move the estimate more aggressively. The Kalman filter formalizes this.

**Method:**
- **Measurement equation:** y(t) = m(t) + ε(t).
- **State transition:** m(t) = m(t−1) + ω(t−1).
- **State update:** m(t|t) = m(t|t−1) + K(t)·(y(t) − m(t|t−1)).
- **Forecast variance:** Q(t) = R(t|t−1) + Vε.
- **Kalman gain:** K(t) = R(t|t−1) / (R(t|t−1) + Vε).
- **State variance update:** R(t|t) = (1 − K(t))·R(t|t−1).
- **Size-dependent measurement noise:** Vε = R(t|t−1) · (1 − T/T_max), where T is the trade size and T_max is a benchmark (e.g., a fraction of prior-day volume, to be optimized on training data). When T = T_max, Vε = 0 and the gain equals 1, so the new estimate m(t) = y(t) exactly.

**Takeaway:** This is a formalization of volume-and-time-weighted fair value, analogous to VWAP but with more weight on large and recent trades. It can be used by market makers to mark their book.

## The Danger of Data Errors

**Idea:** Erroneous price prints (outliers, bad ticks) are uniquely dangerous to mean reversion strategies, both in backtest and live trading.

**Rationale:** A bad print creates a fictitious mean reversion opportunity that a backtester can harvest. In live trading, the same bad print triggers a real order against a price that does not actually exist, often filling at a much worse level.

**Method:** None proposed — this section is a warning, not a strategy. The defensive is to use reputable data vendors that honor exchange cancel-and-correct codes (e.g., Bloomberg; a third-party real-time feed beat a broker feed in the author's own pair-trading experience).

**Pitfalls:**
- **Backtest inflation:** If true prices are $100, $100, $100 but data shows $100, $110, $100, a mean reversion backtest will short at 11:01 ($110) and cover at 11:02 ($100) for a fictitious $10 profit. The same error suppresses momentum backtest P&L (a momentum strategy buys the bad $110 and stops out at $100).
- **Live bad ticks:** A $110 bid that does not actually exist will trigger a market sell that fills at the true $100. The problem is amplified for pairs/arbitrage strategies because the spread (e.g., $5) is small relative to the underlying prices, so even a small absolute error in either leg becomes a large percentage error in the spread (a $1 error on a $5 spread is 20%). In the author's own equities pair trading, switching from a broker data feed to a third-party feed (Yahoo! real-time; later Bloomberg) eliminated unexplained losing trades.
- **Intraday data:** Particularly susceptible to such errors because of the density of prints; reputable vendors apply cancel-and-correct codes to mitigate.
- **Cross-asset arbitrage:** Most exposed because of the small relative magnitude of spreads.
