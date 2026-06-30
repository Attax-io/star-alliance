# Chapter 4 — Mean Reversion of Stocks and ETFs

The stock market is the most fertile ground for finding mean-reverting instruments, but stock pairs trading is plagued by fundamental-valuation instability, short-sale constraints, and tiny intraday quote sizes. ETF pairs cointegrate more robustly, and ETFs can also be paired with producer stocks or used as the "spread" leg against a basket of their own component stocks. Beyond traditional time-series mean reversion, intraday/seasonal patterns and cross-sectional relative-return reversals open additional, simpler, and historically more profitable strategies.

---

## Difficulties of Trading Stock Pairs

**Idea:** Pair-trade individual stocks using standard cointegration tests.

**Rationale:** Although it is intuitively appealing to pair stocks in the same sector (Exxon vs. Chevron, Citibank vs. Bank of America), the fortunes of one company can change abruptly through management decisions, competition, or idiosyncratic news, so two "similar" companies are often not subject to the same shocks. Even when cointegration is found in-sample, it frequently breaks out-of-sample, so the expected out-of-sample return of an individual stock pair is often non-positive. Aggregating many bad pairs does not save the strategy, because the law of large numbers only helps when the per-pair expected return is positive.

**Pitfalls:**
- **Cointegration instability.** Pairs that cointegrate in one period routinely lose cointegration in the next.
- **Short-sale constraint and short squeezes.** Shorting a hard-to-borrow stock can force liquidation at the worst moment, especially when lenders recall shares after unexpected good news. The 2010 U.S. alternative uptick rule adds further uncertainty to backtesting and live execution by forbidding short market orders once the circuit breaker is triggered.
- **Tiny intraday NBBO sizes.** Quoted size at the NBBO for popular names like AAPL is often only 100 shares, because iceberg orders, dark pools, smart-execution child orders, HFT cancellations, and risk-averse market makers suppress displayed size. Backtests that assume fills at the NBBO are therefore unrealistic; live traders must post limit orders and manage partial fills.
- **Structural reasons for past profits.** Spreads used to be wider before decimalization, and the market used to be less efficient, both of which made stock pairs historically profitable (per Serge, 2008). Those tailwinds are largely gone in U.S. equities.
- **Survivorship bias.** Stock backtests in this chapter are performed on an S&P 500 universe with survivorship bias; index composition itself changes through history, and primary-exchange vs. consolidated open/close prices also create a fill-price gap for MOO/LOO/MOC/LOC orders.

**Takeaway:** Single-name stock-pair trading requires fundamental understanding of each company to avoid being blindsided by idiosyncratic news; without it, the strategy is not reliably profitable in U.S. markets.

---

## Trading ETF Pairs (and Triplets)

**Idea:** Form cointegrated pairs (or triplets) of ETFs that share common economic exposures.

**Rationale:** A basket of stocks is a far more stable economic unit than a single company, so once two ETFs are found to cointegrate, the relationship is far more likely to persist out-of-sample. ETF pair selection is therefore easier and more durable than stock pair selection.

**Method:**
1. Choose ETFs exposed to common economic factors (country ETFs with similar economies, sector ETFs, commodity vs. producer ETFs).
2. Run a cointegration test (e.g., Johansen) on historical price series.
3. Re-test the relationship on subsequent out-of-sample data before going live.

**Findings / Examples:**
- **EWA vs. EWC** (Australia and Canada country ETFs): Confirmed cointegrating; Chan notes the relationship held from his 2009 mention through November 2012.
- **RTH vs. XLP** (retail and consumer staples sector ETFs): Cointegrating.
- **GLD vs. GDX** (gold spot vs. gold miners): Cointegrated at the 99% level over May 23, 2006 – July 14, 2008, but lost cointegration over July 15, 2008 – April 9, 2009. The break coincides with the WTI oil price peaking near $145/barrel on July 14, 2008.
- **GLD + GDX + USO** (adding the oil futures ETF USO): The Johansen test indicates one cointegrating relationship at 99% probability over the full 2006–2012 period.
- **USO vs. XLE** is *not* a clean substitute: USO holds oil futures, not oil spot, and because futures price ≠ spot price, XLE may cointegrate with spot oil but not with USO. The same caveat applies to any commodity-futures fund paired with a producer fund — pairs are far less risky when the commodity fund holds the actual commodity.
- **NBBO sizes** for ETFs are much larger than for stocks (e.g., typical EWC NBBO size ≈ 5,000 shares vs. 100 for AAPL).

**Pitfalls:**
- The post-2010 alternative uptick rule covers ETFs (unlike the old uptick rule), constraining short-market-order execution.
- Cointegration can break for economically meaningful reasons (here, oil price); traders should monitor the latent factor and either substitute a triplet or impose a rule to stop trading the pair when the factor breaches a threshold.

**Takeaway:** When a cointegrating ETF pair stops working, hypothesize the cause and test it — for example, add USO to GLD/GDX and trade the triplet — rather than abandoning the idea.

---

## Intraday Mean Reversion: Buy-on-Gap Model

**Idea:** Buy stocks that gap down at the open, provided they are still in a longer-term uptrend, and liquidate at the close.

**Rationale:** On days when index futures are weak pre-open, panic selling at the open pushes certain stocks down disproportionately; once the panic exhausts, the stock tends to recover over the day. Stacking a momentum filter on top (open above the 20-day MA of closes) sharpens the signal: stocks that dropped "just a little" mean-revert more reliably than stocks that dropped "a lot," because the latter often carry negative fundamental news (e.g., poor earnings) that is less likely to revert. Stocks above their long-term moving average attract liquidity-providing selling pressure from longer-horizon players (e.g., long-only funds), and price moves driven by liquidity demand are more likely to revert than those driven by fundamental shifts.

**Method:**
1. At the open, select stocks whose return from the previous day's low to today's open is more than one standard deviation below zero. The standard deviation is computed from 90 days of daily close-to-close returns.
2. Restrict to those whose open price is above the 20-day moving average of closing prices (momentum filter).
3. Buy the 10 stocks in the filtered set with the most negative previous-low-to-open returns (or all of them if fewer than 10).
4. Liquidate all positions at the market close.

**Findings:** Backtest on S&P 500 (with survivorship bias), May 11, 2006 – April 24, 2012: **APR 8.7%, Sharpe ratio 1.5.** Chan notes a version without the MA filter (rule 2) is what he has traded personally and in a fund, but that version suffered diminishing returns from 2009 onward.

**Pitfalls:**
- The strategy is long-only and has small capacity (only 10 names per day).
- Signal prices come from official opens, but the trader cannot actually fill at those prices; pre-open feeds (e.g., ARCA) must be used to generate signals, creating "signal noise."
- Consolidated vs. primary-exchange open prices can produce different signals, as discussed in Chapter 1.
- Survivorship bias in the S&P 500 universe inflates historical performance.
- Transaction costs are not included in the backtest.

**Takeaway:** Even price series that fail stationarity tests on daily bars can exhibit strong mean reversion at specific intraday windows — seasonal mean reversion at short time scales is real and tradable, and a momentum filter (open > 20-day MA) layered on a mean-reversion signal typically improves consistency.

---

## Short-on-Gap Model (Mirror Image)

**Idea:** Short stocks that gap up by more than one standard deviation yet remain below their 20-day moving average, liquidated at the close.

**Rationale:** Mirror logic of the Buy-on-Gap model — an upside gap that is still below a longer-term trend is treated as a temporary overshoot likely to revert.

**Findings:** Same backtest period as Buy-on-Gap: **APR 46%, Sharpe ratio 1.27.**

**Pitfalls:** Higher returns come with a steeper drawdown than the long-only version, and the strategy is exposed to the same short-sale constraints (hard-to-borrow names, short squeezes, alternative uptick rule) as any short-equity strategy.

**Takeaway:** The gap reversal signal works on both sides, but shorting adds structural risks (short squeezes, uptick rule) that limit realistic implementation.

---

## Index Arbitrage: ETF vs. Component-Stock Subset

**Idea:** Re-create the ETF/arbitrage spread using only a subset of the ETF's constituent stocks, which widens the exploitable mispricing.

**Rationale:** Traditional index arbitrage (full basket of stocks vs. futures/ETF) is so competitive that the spread is almost too small to trade, especially intraday/high-frequency. By deliberately holding only a subset of the constituents, the spread is enlarged to a tradable magnitude. Cointegration is the framework that keeps the strategy a *stationary* (mean-reverting) portfolio rather than a directional bet on the index.

**Method:**
1. Pick a training window (e.g., January 1, 2007 – December 31, 2007).
2. For each stock in the universe, run a Johansen test against the ETF (e.g., SPY) and keep those that cointegrate with at least 90% probability.
3. Form a long-only portfolio of the surviving stocks with equal dollar capital per stock.
4. Confirm on the training set, using the Johansen test on log prices, that this long-only portfolio cointegrates with the ETF. (Equal capital weights do *not* guarantee cointegration even if every constituent cointegrates individually.)
5. From the Johansen output, take the largest-eigenvalue eigenvector as the hedge-ratio vector between the stock portfolio and the ETF.
6. Trade the resulting long-short stationary portfolio using the linear mean-reversion rule (z-score on log market value with a 5-day look-back for MA and std, fixed with hindsight in the example) over a separate out-of-sample test period (e.g., January 2, 2008 – April 9, 2012).

**Findings:** SPY example, 98 of the SPX stocks cointegrated individually with SPY in 2007. The long-only portfolio's log market value cointegrated with SPY at >95% probability. Out-of-sample (2008-01-02 to 2012-04-09) **APR 4.5%, Sharpe ratio 1.3**, with performance decaying over time because the model was not periodically retrained.

**Pitfalls:**
- **Decay without retraining.** The selected constituents and hedge ratios drift out of date; a more complete backtest would retrain periodically.
- **Short-sale constraint.** Mitigated here because the stock portfolio is well-diversified (≈98 names).
- **Primary vs. consolidated closes.** If trading MOC/LOC orders, the primary-exchange close will likely be worse than the consolidated close used in the backtest.
- **Futures substitution.** A futures contract on the index can be used in place of the ETF, but the futures prices used in backtesting must be contemporaneous with the stock closes (Chapter 1 pitfall).
- **Why not Johansen on all 500 stocks + SPY at once?** Chan's Johansen implementation caps at ~12 symbols, and the resulting eigenvectors typically require both long and short stock positions, leading to double-short exposure on some names.
- **Alternative: constrained optimization.** Instead of equal capital weights, use a genetic algorithm or simulated annealing to minimize the average absolute difference between the stock portfolio and the ETF, subject to positive hedge ratios.

**Takeaway:** Index arbitrage is "dead" only at full basket; trading a Johansen- or optimization-selected subset of components against the ETF (or futures) restores a tradable spread, provided hedge ratios and constituents are refreshed over time.

---

## Cross-Sectional Mean Reversion: Linear Long-Short Model (Khandani & Lo)

**Idea:** Every day, weight every stock in a universe by the *negative* of its return relative to the cross-sectional mean return, normalized to a fixed gross capital of $1.

**Rationale:** Cross-sectional mean reversion is the analog of time-series mean reversion: the cumulative returns of instruments in a basket revert to the cumulative return of the basket, not to each instrument's own past. Standard stationarity/cointegration tests largely do not capture this; what matters is the serial anti-correlation of *relative* returns. Stocks that outperformed the average today tend to underperform tomorrow, and vice versa, regardless of whether the absolute return was positive or negative. The strategy is "dollar neutral" (equal long and short capital), parameter-free, and requires no estimation of betas or factor loadings.

**Formula / rule:**

$$
w_i = -\frac{r_i - \langle r_j \rangle}{\sum_k |r_k - \langle r_j \rangle|}
$$

where $r_i$ is the daily return of stock $i$ and $\langle r_j \rangle$ is the equal-weighted average daily return of the index/universe. The denominator ensures total gross capital is $1 every day.

**Method (close-to-close):**
1. Compute daily stock returns from closing prices.
2. Compute the equal-weighted market return (mean of stock returns).
3. Compute weights per the formula above.
4. PnL is the previous-day weights multiplied by today's returns, divided by gross capital (1).

**Findings:** SPX universe, January 2, 2007 – December 30, 2011: **APR 13.7%, Sharpe ratio 1.3.** Notable sub-periods: **2008 APR ≈ 30%** (Lehman year), **2011 APR ≈ 11%** (debt downgrade/Greek default). Performance from 2008 onward is a true out-of-sample test, because the original Khandani & Lo paper was published in 2007.

**Takeaways and extensions:**
- "Profits come in the aggregate, not per name" — some individual stocks serve as hedges on any given day.
- Smaller-cap universes historically generated higher returns than the SPX.
- **Ranking factor choice.** Relative return is the default, but the cross-sectional signal can also be ranked on fundamental factors such as P/E ratio (using trailing or analyst-projected earnings). The reasoning: if a stock's outperformance is justified by a positive earnings-revision, mean reversion is less likely, so filtering on P/E can avoid false-positive shorts.

**Pitfalls:**
- Backtest universe has survivorship bias.
- Using the official close to compute weights and then filling at that exact close is unrealistic; pre-close prints are usually close enough for the close-to-close version, but intraday variants add signal noise.
- Decay as more traders crowd the trade — Khandani & Lo's original edge has shrunk since publication.

---

## Intraday Linear Long-Short Model

**Idea:** Use the return from the previous close to today's open to set the weights, enter at the open, and liquidate at the close.

**Rationale:** Same cross-sectional mean-reversion logic as the close-to-close version, but using the more volatile overnight/overnight-to-open return as the signal, and capturing the open-to-close reversal as the PnL.

**Method:**
1. Compute the "overnight" return as `(open - previous close) / previous close`.
2. Compute the equal-weighted market overnight return.
3. Compute weights via the cross-sectional formula.
4. PnL for the day is the weight times `(close - open) / open`, divided by gross capital.

**Findings:** Same period as the close-to-close version: **APR 73%, Sharpe ratio 4.7.**

**Pitfalls:**
- Transaction costs are roughly doubled relative to the close-to-close version (two-way trading).
- Inherits the "open signal noise" pitfall: weights must be computed off pre-open prints, not the actual official open at which fills occur.
- Apparent outperformance is partly an artifact of the (untested in this chapter) assumption that the signal can be acted on cleanly at the open.

**Takeaway:** The cross-sectional reversal is strong enough that switching from close-to-close to open-to-close roughly quintuples the headline Sharpe — but only if the trader accepts the doubled trading costs and the additional signal noise inherent in using opens.

---

## General Pitfalls and Pointers (Chapter-Wide)

- **No transaction costs in the backtests.** Costs depend on execution method and universe; stated returns should be read as upper bounds.
- **Survivorship bias** in the S&P 500 stock universe; a proper replication needs a survivorship-bias-free database *and* a record of the index's changing composition.
- **Consolidated vs. primary-exchange prices.** Backtests use consolidated opens/closes; MOO/LOO/MOC/LOC orders will fill at the primary exchange, generally producing lower realized returns.
- **Short-sale constraints** (hard-to-borrow, short squeezes, 2010 alternative uptick rule) affect any short-leg strategy.
- **Tiny NBBO quote sizes** make intraday backtesting unrealistic unless trading just ~100 shares or assuming large transaction costs.
- **Decimalization** permanently narrowed spreads and squeezed the market-making profits that used to fund stock-pair returns.
- **Commodity ETFs that hold futures** (e.g., USO) cannot be treated as the spot price; the spread between futures and spot contaminates any commodity-vs-producer pair.
- **Time-series vs. cross-sectional.** Cross-sectional reversal is not detected by standard stationarity/cointegration tests, so testing frameworks must match the type of mean reversion targeted.
- **When a cointegration breaks, hypothesize, don't quit.** The GLD/GDX → GLD/GDX/USO story is the template: a broken pair often becomes a working triplet.
- **Momentum filter on a mean-reversion signal** is a recurring, consistently useful enhancement.
