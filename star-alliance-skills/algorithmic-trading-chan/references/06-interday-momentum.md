# Chapter 6 — Interday Momentum Strategies

This chapter lays out a taxonomy of interday momentum strategies in futures and stocks, grounded in four causal hypotheses: (1) persistence of the sign of roll returns in futures, (2) slow diffusion/analysis/acceptance of new information, (3) forced asset sales or purchases by funds, and (4) high-frequency-trader market manipulation (the last is treated in the next chapter). Chan distinguishes time-series momentum (a single asset's past returns predict its own future returns) from cross-sectional momentum (an asset's past returns relative to peers predict its future relative returns), and shows how to detect, trade, and stress-test each, with particular attention to the post-2008 "momentum crash" risk.

## The Four Causes of Momentum

**Idea:** Chan attributes momentum to four mechanisms operating at different speeds and on different instruments.
**Rationale:** Different causes motivate different signals and different holding periods. Recognizing the cause tells you which test to use, which pitfall to expect, and which time horizon is appropriate.
**Method:** Map each observed momentum anomaly to one (or more) of the four causes before designing a strategy around it.
**Takeaway:** A momentum strategy is only as robust as the causal story behind it; persistence-of-roll-returns momentum is structural, while news-diffusion and fire-sale momentum are regime-dependent and degrade once crowded or after crises.

## Time-Series vs. Cross-Sectional Momentum

**Idea:** Two distinct statistical forms of momentum that require different test designs.
**Rationale:** Time-series momentum exploits a single instrument's autocorrelation; cross-sectional momentum exploits persistent relative performance across a universe. The causes differ, the holding periods differ, and the failure modes differ.
**Formula / rule:**
- Time-series momentum: past returns of a price series are positively correlated with its own future returns.
- Cross-sectional momentum: a series with returns that outperformed other series tends to keep outperforming, and vice versa.
**Takeaway:** Always specify which type you are testing — a Hurst exponent or variance-ratio test is a time-series test; a ranking-and-long/short portfolio is a cross-sectional test.

## Tests for Time Series Momentum

**Idea:** Three statistical tests to detect and characterize time-series momentum, applied to the 2-year Treasury note future (TU) on CME.
**Rationale:** Different tests answer different questions. Correlation with a chosen lag tells you the optimal look-back/holding pair; sign correlation is appropriate when only direction matters; Hurst and Variance Ratio tell you whether long-term trending behavior exists independent of any specific lag.
**Method:**
1. Compute the Pearson correlation coefficient and its p-value between lagged returns and forward returns across a grid of look-back and holding periods.
2. Optionally repeat the test using only the signs of the returns.
3. Compute the Hurst exponent and run a Variance Ratio test for the null of random walk.
4. When gridding look-back × holding, enforce non-overlapping samples: if look-back ≥ holding, shift forward by look-back to start a new independent returns pair; if holding > look-back, shift forward by holding.
**Findings (TU):**
- The best compromise pairs of (correlation, p-value) are (60,10), (60,25), (250,10), (250,25), (250,60), (250,120).
- Best pairs when correlating signs of returns: (60,10), (250,10), (250,25).
- The 250×25 pair shows correlation 0.27 with p-value 0.02.
- The Hurst exponent is 0.44 and the Variance Ratio test fails to reject the random-walk null — a contradiction with the grid result that Chan reconciles by noting the time series exhibits both momentum and mean reversion at different time frames, which the Variance Ratio test cannot localize.
**Pitfalls:** Choosing any single test in isolation is misleading when momentum and mean reversion coexist; the Variance Ratio test cannot localize the specific horizons where correlation is strongest. Always grid over look-back × holding.
**Takeaway:** Prefer the grid-search correlation test for actionable strategy design; use Hurst and Variance Ratio only as a sanity check for long-term trending, not as a stand-alone decision tool.

## Time-Series Momentum Strategy: TU Example

**Idea:** A long/short time-series momentum strategy on TU using a 250-day look-back and 25-day holding, allocating capital incrementally each day rather than rebalancing in one block.
**Rationale:** The Moskowitz–Yao–Pedersen (2012) "12-month return, hold 1 month" prescription is adapted for daily implementation. Holding the future for a long period averages out the noisy spot return; if the average roll return dominates the average total return (the structural situation for TU, BR, HG), serial correlation of total returns emerges.
**Method:**
1. Each day, set longs = 1 if today's close > close 250 days ago, shorts = 1 if today's close < close 250 days ago.
2. Over the next 25 trading days, sum the long and short signals at each lag h = 0 … 24 to build a position series, so each day only 1/25 of capital is committed.
3. Compute daily return as (previous-day position) × daily price change, divided by 25.
**Formula / rule:** Go long (short) on a positive (negative) 250-day return; hold 25 days; invest 1/25 of capital per decision day.
**Findings (TU, June 1, 2004 – May 11, 2012):** Sharpe ratio ≈ 1.0; APR = 1.7% on the notional ($200,000 contract) versus a margin of about $400 (so leverage boosts return); maximum drawdown = –2.5%.
**Findings (other futures, Table 6.2):**
- BR (CME): look-back 100, holding 10, APR 17.7%, Sharpe 1.09, max DD –14.8%.
- HG (CME): look-back 40, holding 40, APR 18.0%, Sharpe 1.05, max DD –24.0%.
- TU (CBOT): 250/25, APR 1.7%, Sharpe 1.04, max DD –2.5%.
**Rationale for why this works:** Futures stay in contango or backwardation over long periods (persistent sign of roll return), while spot returns oscillate quickly. The total return serial correlation emerges because over a long enough holding period, the slowly-varying roll return dominates the rapidly-varying spot return. BR, HG, and TU all have roll-return magnitudes larger than their spot-return averages.
**Pitfalls:** C (corn) has the largest roll-yield-to-spot-return ratio yet does not exhibit this momentum — the explanation does not generalize universally. Because of the long holding period and limited sample, data-snooping bias is a serious risk; out-of-sample validation is essential.
**Takeaway:** Time-series momentum in futures is fundamentally a roll-return persistence play; if a contract's roll-yield dominates its average spot return, you should expect exploitable serial correlation.

## Cleaner Signal: Lagged Roll Return as the Trigger

**Idea:** Replace the lagged total return with the lagged roll return itself as the entry signal.
**Rationale:** Because the structural source of the serial correlation is the roll return, a signal based directly on the roll return isolates the cause, should be cleaner, and should reduce drawdown.
**Method:** Go long when the lagged roll return exceeds a positive threshold, go short when it is below the negative threshold, and flatten otherwise.
**Findings (TU, January 2, 2009 – August 13, 2012):** With an annualized roll-return threshold of 3%, APR rises to 2.5% and Sharpe to 2.1 with max drawdown reduced to 1.1%.
**Takeaway:** When the economic cause of an edge is known, a direct signal on that cause typically beats an indirect proxy on the noisy total return.

## Alternative Entry Signals for Time-Series Momentum

**Idea:** A menu of non-return-based trend signals a momentum trader can use.
**Rationale:** Each captures a different facet of "trend" or "new information" and can be matched to instrument and time-frame.
**Method (list of signals):**
- Price makes a new N-day high.
- Price exceeds N-day moving average or exponential moving average.
- Price exceeds upper Bollinger band.
- Number of up days exceeds number of down days over a moving window.
- Alexander Filter: buy when daily return rises at least x%; then sell and go short if price subsequently falls at least x% from the most recent high (Fama and Blume, 1966).
**Takeaway:** There is no single "right" trend signal — the choice depends on the noise/signal ratio of the instrument.

## Hybrid: Mean-Reverting Filter Added to a Momentum Rule

**Idea:** Combine momentum and mean-reversion entry conditions to expand the tradable universe and improve risk-adjusted returns.
**Rationale:** Pure momentum misses opportunities that pass only a mean-reversion filter, and vice versa; some instruments trade more cleanly when both conditions must be satisfied.
**Method (CL example):** Buy at the close if price < close 30 days ago AND price > close 40 days ago; short symmetrically. Flatten if neither condition holds.
**Findings (CL):** APR = 12%, Sharpe = 1.1.
**Findings (additions):** Adding a mean-reverting filter to the TU-style momentum strategy extends the tradable set to include IBX (MEFF), KT (NYMEX), SXF (DE), US (CBOT), CD (CME), NG (NYMEX), and W (CME), and improves the metrics on the original contracts.
**Takeaway:** Hybrid rules can rescue a momentum strategy on instruments that fail the pure momentum screen.

## S&P Diversified Trends Indicator (DTI) as Off-the-Shelf Momentum

**Idea:** A pre-built 24-future trend-following index: long a future when above its EMA, short when below, monthly rebalancing. Tracked by RYMFX (mutual fund) and WDTI (ETF).
**Rationale:** Trend-following indices are an efficient way to get diversified momentum exposure without constructing a custom system.
**Findings (Dever, 2011; January 1988 – December 2010):** Sharpe = 1.3, max drawdown = –16.6%. By comparison, SPX over the same period: Sharpe = 0.61, max drawdown = –50.96%.
**Pitfalls:** Like most interday momentum strategies, DTI performance has been poor since the 2008 financial crisis — a recurring failure mode for trend-following.
**Takeaway:** DTI provides a free benchmark for any custom momentum system; underperformance vs. DTI in a momentum strategy should prompt a redesign.

## Extracting Roll Returns via Future-vs-ETF Arbitrage

**Idea:** Use the identity total return = spot return + roll return to isolate roll return by going long the spot proxy and short the future (under contango), or vice versa (under backwardation), whenever the sign of roll return is expected to persist.
**Rationale:** This isolates the structural source of the edge and avoids waiting for the noisy spot return to average out, so the holding period can be shorter and the risk lower than a buy-and-hold of the future.
**Method (GLD vs. GC):** Long GLD, short GC whenever GC is in contango; reverse when in backwardation. Position is held until the roll-return sign changes.
**Findings (GLD/GC, August 3, 2007 – August 2, 2010):** Annualized return 1.9%, max drawdown 0.8%. GC roll return = –4.9% annualized (Dec 1982 – May 2004).
**Pitfalls:**
- Owning GLD (a physical gold ETF) incurs financing cost ≈ 1.9% over the backtest, so the excess return is close to zero.
- Asynchronous settlement: GC closes at 1:30 p.m. ET, GLD at 4:00 p.m. ET — a pitfall flagged in Chapter 1, irrelevant here because signals are generated from GC alone.
- Outside precious metals, no ETF holds the physical commodity (storage costs are prohibitive), so direct arbitrage is unavailable.
**Takeaway:** Spot-vs-future roll-yield arbitrage is theoretically clean but practically available for very few instruments; the excess return is often consumed by financing cost.

## Cointegrated-Proxy Arbitrage: XLE vs. USO

**Idea:** When no ETF holds the physical commodity, find an ETF that cointegrates with the spot price and use it as a proxy to extract the roll return of the corresponding future.
**Rationale:** Energy-sector companies' equity values are substantially driven by the underlying commodity, so the XLE/CL pair (and the cleaner XLE/USO pair) is cointegrated. Trading on the sign of the CL roll return is then implementable via XLE vs. USO.
**Method:** Short USO and long XLE whenever CL is in contango; long USO and short XLE whenever CL is in backwardation.
**Findings (April 26, 2006 – April 9, 2012):** APR = 16%, Sharpe ≈ 1.0.
**Takeaway:** A high (or anti-) correlation between a tradable instrument and the spot price is sufficient; perfect cointegration is not required for roll-yield harvesting.

## Volatility vs. Equity Index Futures: VX/ES Roll-Return Momentum

**Idea:** A daily momentum strategy on the pair (VX, ES) that exploits the very large and persistent roll return of VX, the negligible roll return of ES, and the –75% correlation of their daily returns.
**Rationale:** VX is too expensive to replicate via a physical basket or ETF, but ES is a clean proxy for the equity-spot return, so the pair lets you isolate VX's roll yield. Unlike Chapter 5's mean-reverting pair trade, this is a momentum trade that follows the sign of VX's roll return.
**Method (Simon and Campasano, 2012):**
1. If the front VX price exceeds VIX by 0.1 × (trading days to settlement) → VX is in contango → short 0.3906 VX and short 1 ES; hold one day.
2. If the front VX price is below VIX by 0.1 × (trading days to settlement) → VX is in backwardation → long 0.3906 VX and long 1 ES; hold one day.
- Hedge ratio 0.3906 comes from the price-level regression of VX on ES (Equation 5.11), not the return regression used in the original paper.
- Equation 5.7 is unusable here because VX forward prices are not on a straight line.
**Findings (July 29, 2010 – May 7, 2012, out-of-sample to hedge-ratio determination):** APR = 6.9%, Sharpe = 1.0.
**Takeaway:** When you can find two futures with opposite-sign or asymmetric-magnitude roll returns and a stable hedge ratio, a daily pair momentum strategy is a clean way to harvest one of the roll yields.

## Cross-Sectional Futures Momentum

**Idea:** A cross-sectional analogue of the time-series strategy: rank a universe of futures by lagged return, go long the top and short the bottom.
**Rationale:** If commodities' spot returns are positively correlated with a common macro factor (e.g., economic growth), the spot component cancels in a long-short cross-sectional portfolio and the residual return is driven by the roll-yield spread between backwardated and contangoed contracts.
**Method (Daniel and Moskowitz, 2011):** Each day, rank 52 physical commodities by 252-day (12-month) return; long the highest and short the lowest for 25 trading days (1 month).
**Findings:** June 1, 2005 – December 31, 2007: APR 18%, Sharpe 1.37. January 2, 2008 – December 31, 2009: APR –33%. Performance recovered afterward.
**Pitfalls:** This strategy — and many other interday momentum strategies — collapsed during the 2008–2009 financial crisis. With limited sample, data-snooping bias is a real concern.
**Takeaway:** Cross-sectional futures momentum is essentially a roll-yield harvesting trade, but it remains exposed to the same "momentum crash" risk as time-series momentum.

## Cross-Sectional Stock Momentum (Daniel–Moskowitz / 12-1)

**Idea:** Apply the cross-sectional rank-and-trade framework to equities: each day, rank S&P 500 stocks by 252-day return; long the top 50, short the bottom 50; hold 25 days.
**Rationale:** Stocks also exhibit persistent relative performance; here the cause is no longer roll yields (which don't exist for stocks) but slow diffusion of new information plus flow-driven pressure.
**Method:**
1. Compute 252-day total return for each stock.
2. Each day, sort ascending; identify bottom 50 and top 50 by return (excluding missing data).
3. Spread entry across the next 25 trading days (1/25 of position per day) to mimic the original monthly rebalance while keeping capital continuously deployed.
4. Daily portfolio return = (prior-day position-weighted average of stock daily returns) divided by (2 × topN × holddays).
**Findings (Chan, May 15, 2007 – December 31, 2007):** APR = 37%, Sharpe = 4.1. (Daniel and Moskowitz, 1947–2007: average annualized return 16.7%, Sharpe 0.83.)
**Findings (January 2, 2008 – December 31, 2009):** APR = –30% — the financial crisis destroyed the strategy. Post-2009 performance stabilized but had not returned to its prior high by the time of writing.
**Takeaway:** Cross-sectional equity momentum is among the most spectacular pre-crisis Sharpe-ratio opportunities, but it is also among the strategies most damaged by the 2008–2009 crash; do not size it as if the pre-crisis Sharpe is stationary.

## Factors as Cross-Sectional Ranking Variables

**Idea:** Replace raw lagged return with a broader set of "factors" (fundamental, statistical, or sentiment-based) for ranking.
**Rationale:** Total return = market return + factor returns; a cross-sectional long-short portfolio cancels the market component, so the residual is driven entirely by the factor. Choosing slowly-changing factors (everything except PCA) preserves the long-holding-period character of these strategies.
**Method:**
- Fundamental factors: earnings growth, book-to-price, or any linear combination.
- Statistical factors: PCA-derived factors (see Chan's *Quantitative Trading*).
- For futures: macro factors such as GDP growth or inflation regressed on individual futures returns, or PCA.
**Takeaway:** The factor choice is the strategy. Once a cross-sectional portfolio neutralizes the market, only the factor's time-series properties matter.

## News Sentiment as a Cross-Sectional Factor

**Idea:** Use NLP-derived sentiment scores on elementized news feeds as the ranking variable for a stock long-short portfolio.
**Rationale:** If the sentiment score aggregates a company's recent news into a single predictive signal, and if news diffuses slowly, then stocks with rising positive sentiment should outperform, providing a cross-sectional momentum edge.
**Method:** Subscribe to an elementized news feed (e.g., Newsware, Bloomberg Event-Driven Trading, Dow Jones Elementized News Feeds, Thomson Reuters Machine Readable News). Compute a sentiment score per stock per period, or buy a vendor score (RavenPack Sentiment Index, Recorded Future, thestocksonar.com, Thomson Reuters News Analytics). Each period, long the most-improved-positive-sentiment stocks and short the most-improved-negative-sentiment stocks.
**Findings (Hafez and Xie, 2012, using RavenPack Sentiment Index):** Pre-cost APR 52%–156% and Sharpe 3.9–5.3, depending on portfolio breadth.
**Takeaway:** News-sentiment momentum is direct evidence that slow information diffusion drives stock momentum. The edge is real but pre-cost and likely capacity-limited.

## Twitter / Social-Media "Mood" as a Market Predictor

**Idea:** Aggregate Twitter sentiment ("calm", "happy", etc.) to predict the equity index itself, then trade the index.
**Rationale (claimed):** Bollen, Mao, and Zeng (2010) reported that the public mood extracted from tweets predicted the Dow.
**Pitfalls:** A multimillion-dollar hedge fund was launched on this idea (Bryant, 2010), but the original research was challenged ("Buy the Hype", 2012).
**Takeaway:** Treat market-level social-media signals as research curiosities, not tradable edges, until independently replicated with cost-aware out-of-sample evidence.

## Mutual Fund Fire Sales and Forced Purchases (Coval–Stafford)

**Idea:** Build a "pressure" factor measuring net selling/buying pressure on each stock from poorly performing funds facing redemptions (or winning funds receiving inflows).
**Rationale:** Mutual funds are typically fully invested with minimal cash. Funds hit by redemptions must sell pro rata across existing positions; funds hit by inflows add to existing positions rather than seeking new ideas. The resulting mechanical flow depresses (elevates) prices of commonly held stocks, igniting price momentum in both directions. The fire-sale is contagious because depressed stocks hurt the holdings of other funds, triggering more redemptions.
**Method:** Compute the PRESSURE factor at end of quarter t, where:
- Buy(j,i,t) = 1 if fund j increased its holding in stock i during quarter t AND fund j experienced inflows > 5% of NAV; else 0.
- Sell(j,i,t) = 1 if fund j decreased its holding in stock i during quarter t AND fund j experienced outflows < –5% of NAV; else 0.
- PRESSURE(i,t) = sum_j [ Buy(j,i,t) − Sell(j,i,t) ] × Own(j,i,t−1) / sum_j Own(j,i,t−1).
- Own(j,i,t−1) is an indicator that fund j held stock i at the start of quarter t.
**Pitfalls:**
- PRESSURE treats Buy and Sell as binary and does not weight by fund NAV; weighting by NAV may improve results.
- Holdings data arrive quarterly; the portfolio is updated only quarterly, leaving stale exposure.
- Slippage is likely to be significant because information arrives with a delay.
- Implementation requires CRSP mutual-fund holdings data, costing about $10,000 per year of data.
**Findings (Coval and Stafford, pre-cost):**
- Market-neutral long high-PRESSURE / short low-PRESSURE portfolio: ≈ 17% annualized.
- Front-running the predicted flows (forecasting fund flows from past performance and past flows, then trading ahead): another ≈ 17% annualized.
- Buying the stocks that suffered the most pressure over t−4 to t−1 quarters (a mean-reversion layer on the same forced-flow phenomenon): another ≈ 7% annualized.
- Combined momentum + front-running + mean-reversion: ≈ 41% annualized pre-cost.
**Takeaway:** Forced flow is a real, structural source of stock momentum and is followed by mean reversion once the flow exhausts itself; the three-layer combination is one of the highest-return documented factor portfolios, but the data and infrastructure cost are non-trivial.

## Pros of Momentum Strategies

**Idea:** Five structural advantages that make momentum strategies attractive as a portfolio building block.
**Rationale:** These properties are intrinsic to the trend-following design rather than to any specific signal.
**Method (list of advantages):**
- Risk management is straightforward: time-based exit (a fixed holding period) and/or a stop-loss are both consistent with momentum (a stop-loss is just a reverse-signal entry).
- Per-position loss is bounded by the stop-loss; a single position cannot produce an open-ended drawdown.
- Upside is unlimited (no profit cap), and momentum strategies thrive in fat-tailed (high-kurtosis) distributions and on "black swan" events.
- Most futures and currencies exhibit momentum, so a momentum sleeve is a powerful diversifier across asset classes and countries.
- A combined momentum + mean-reversion portfolio has higher Sharpe and smaller drawdown than either sleeve alone (Example 1.1's simulation: a returns series with the same kurtosis as TU but no serial autocorrelation reproduced the TU momentum strategy's return in 12% of random draws — kurtosis alone does significant work).
**Takeaway:** Use momentum as the asymmetric, fat-tailed complement to a mean-reverting book; together they cover different return regimes and reduce aggregate drawdown.

## Cons of Momentum Strategies

**Idea:** Three structural disadvantages that constrain the standalone appeal of interday momentum.
**Rationale:** These are the costs of the long look-back / long holding-period design and the known "momentum crash" phenomenon.
**Method (list of disadvantages):**
- Harder to construct profitably than mean reversion, and resulting Sharpe ratios are typically lower, because long holding periods generate few independent trading signals (daily rebalancing does not create more independent signals).
- Vulnerable to "momentum crashes" (Daniel and Moskowitz, 2011): futures and stock momentum strategies tend to perform miserably for years after a financial crisis. Cross-sectional equity momentum vanished 2008–2009, replaced by strong mean reversion. After the 1929 crash, a representative momentum strategy took more than 30 years to recover its high watermark. The S&P DTI was down –25.9% from December 5, 2008 as of writing.
- The duration of any given momentum effect tends to compress as more traders learn about it. Earnings-announcement momentum, for example, used to last several days and now often lasts only until the close. The decay is unpredictable in schedule.
**Takeaway:** Size interday momentum conservatively, expect a multi-year post-crisis drawdown, and plan to shorten holding periods as the effect compresses — but do not abandon the sleeve, because in calm/fat-tailed regimes it is a major diversifier.

## Momentum vs. Mean-Reversion: Asymmetric Risk Profile

**Idea:** The two strategy families have mirror-image risk profiles.
**Rationale:** The entry/exit logic of each is internally consistent in one regime and inconsistent in the other.
**Method (rules of thumb):**
- Stop-loss is consistent with momentum (a reverse signal is the new entry); it is inconsistent with mean reversion (it cuts the position just as the thesis is most likely correct).
- Momentum: unlimited upside, bounded per-position downside; benefits from thick tails and black swans.
- Mean reversion: limited upside (capped at "the mean"), open-ended downside (the price can keep running away); benefits from low-volatility, mean-reverting regimes.
- Per-position drawdown under mean reversion can be enormous; cumulative drawdown under a stream of momentum losses can also bankrupt the trader.
**Takeaway:** Allocate between the two by forecasting the prevailing regime: fat-tailed/crisis-prone regimes favor momentum; calm, range-bound regimes favor mean reversion.
