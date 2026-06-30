# Chapter 1 — Backtesting and Automated Execution

This chapter lays the foundation for all subsequent strategy work in the book by addressing cross-cutting issues that can make or break any backtest. Chan systematically catalogs the common pitfalls (look-ahead bias, data-snooping, survivorship bias, primary-vs-consolidated prices, short-sale constraints, futures roll-adjustment issues, etc.), then walks through three flavors of statistical-significance testing on a TU futures momentum example, warns which strategies are not worth backtesting at all, and closes with criteria for choosing a backtesting and automated-execution platform.

## The Importance of Backtesting

**Idea:** Backtesting = feeding historical data to a strategy to see how it would have performed, in hopes that past performance informs future performance.

**Rationale:** Backtesting is essential even for published strategies because (a) profitability depends sensitively on implementation details that authors gloss over (market-on-open vs. market-on-close, bid vs. ask vs. last to trigger, futures close time, etc.), (b) it surfaces pitfalls specific to each market and strategy, and (c) it allows the trader to conduct true out-of-sample testing starting only after publication. Backtesting should follow the scientific method: hypothesis → backtest → modify → re-test.

**Method:** 
1. Backtest every published strategy yourself, even if you trust the author.
2. Pin down every implementation detail (order type, venue, trigger price, timing).
3. Audit for market- and strategy-specific pitfalls.
4. Conduct genuine out-of-sample testing only after publication, so the out-of-sample data cannot be re-used for parameter tweaking.
5. Use backtesting as an experimentation tool to refine parameters (e.g., look-back windows, order timing).

**Takeaway:** The right backtest is a vehicle for hypothesis-driven experimentation, not a one-shot number. A backtest whose only function is to confirm what the author wrote is no backtest at all.

## Common Pitfalls of Backtesting

Chan groups pitfalls into named categories. Most pitfalls tend to **inflate** backtest performance relative to realized performance.

### Look-Ahead Bias

**Idea:** The backtest inadvertently uses future information unavailable at the time of a "decision."

**Rationale:** Look-ahead bias is essentially a programming error. It can infect a backtest program but cannot exist in a live program, because a live program has no access to the future. The cleanest cure is to make backtest and live programs the *same* program, with the only difference being the data feed (historical vs. live).

**Method:** 
- Never use a day's high or low (known only after the close) to make an entry decision for the same day.
- Use an event-driven architecture that feeds data one tick or one bar at a time, identical to the live program.

**Takeaway:** A single source code for backtest and live execution is the surest cure.

### Data-Snooping Bias and the Beauty of Linearity

**Idea:** Fitting too many parameters to historical noise produces a model that looks great in-sample but predicts nothing.

**Rationale:** A model trained on a fixed out-of-sample set can be quietly re-tuned until it "passes" — at which point the out-of-sample is no longer out-of-sample. Cross-validation and walk-forward testing are the standard defenses, but the best structural defense is simplicity: linear models with few parameters are far less susceptible than nonlinear ones, even when parameter counts are matched (every nonlinear model has a simpler Taylor-series linear approximation that should be preferred unless there is a good reason not to). For return distributions, Occam's razor favors Gaussian unless non-Gaussian is strongly motivated. For the linear capital-allocation extreme, a mean-reverting model implies "averaging-in" (scaling-in): position size proportional to deviation from the mean at every price increment.

**Method:** 
1. Use cross-validation: train and test on multiple distinct subsets.
2. Prefer high-Sharpe, short-drawdown models — they pass cross-validation almost automatically.
3. Keep the model linear in prediction and in capital allocation.
4. Run a final walk-forward test (paper trading, ideally with real money at minimal leverage).
5. Accept that a live Sharpe as low as **half** of the backtest Sharpe is a reasonable outcome.

**Formula / rule:** 
- Equal-weight factor combination (after Z-scoring each factor in-sample):

  z^(i) = (f^(i) − mean(f))/std(f)

  predicted R = mean(R) + std(R) · (Σ sign(i) · z^(i)) / n

  where sign(i) is the sign of the historical correlation between factor i and R.

- Rank-only version (no expected-return calculation needed):

  rank(s) = Σ sign(i) · rank(s, f^(i))

- Greenblatt's "magic formula" two-factor example: f^(1) = return on capital, f^(2) = earnings yield; buy top-30 ranked stocks, hold one year. Reported **APR 30.8% (1988–2004) vs. 12.4% for S&P 500.**

**Findings:** Greenblatt's "magic formula" produced **30.8% APR (1988–2004)** vs. **12.4% for the S&P 500** over the same period.

**Takeaway:** Linearity is not a constraint — it is a defense against your own overfitting.

### Stock Splits and Dividend Adjustments

**Idea:** A backtest price series must be back-adjusted for splits and dividends, otherwise ex-dates create phantom price drops that trigger spurious signals.

**Rationale:** A stock's market value does not change on a split or dividend ex-date, but a naive price series does. The same adjustment must be made in both backtest and live systems (apply just before the open on the ex-date).

**Method:** 
- N-to-1 split: divide all historical prices *before* the ex-date by N.
- 1-to-N reverse split: multiply all historical prices *before* the ex-date by N.
- Cash dividend $d: subtract $d from all historical prices *before* the ex-date.
- A slightly more complicated adjustment is needed for options prices; the same applies to ETFs.

**Takeaway:** earnings.com is recommended for historical and forward split/dividend data; csidata.com is recommended for pre-adjusted historical prices.

### Survivorship Bias in Stock Database

**Idea:** If the stock database only contains currently-listed stocks, the backtest quietly excludes the names that went bankrupt — exactly the names a long-only "buy-the-losers" strategy would have been forced to own.

**Rationale:** Survivorship bias inflates long-only mean-reverting strategies most (they buy beaten-down names that *survived*). It deflates short-only mean-reverting strategies. For long-short, the two effects partially offset, but the long-side inflation tends to dominate. Momentum models are less affected.

**Method:** 
- Use a survivorship-bias-free database: csidata.com (provides a delisted list), kibot.com, tickdata.com, crsp.com.
- Or build your own by saving daily prices for every name in an index.
- Or restrict the backtest to the most recent ~three years to reduce damage.

**Takeaway:** If the published backtest does not explicitly say the data includes delisted stocks, assume it does not — and assume the return is inflated.

### Primary versus Consolidated Stock Prices

**Idea:** For strategies that fire on the open or close, you need historical prices from the *primary* exchange, not the consolidated tape.

**Rationale:** MOC and MOO orders are routed to a single primary exchange (NYSE for IBM, NYSE Arca for SPY, Nasdaq for MSFT). Consolidated open/close prices can reflect small prints on other venues whose prices are unachievable at the auction, especially the close. The same issue applies to consolidated highs and lows: they often reflect small prints on secondary exchanges and are unrepresentative.

**Method:** 
- Source primary-exchange open and close prices (Bloomberg subscription or direct feed from the primary exchange).
- Be aware that the close and open on U.S. primary exchanges are determined by auction; secondary-venue prints are not.
- If primary-exchange data is unavailable, treat backtest results with skepticism.

**Takeaway:** Consolidated-tape backtests of mean-reverting models are systematically optimistic.

### Venue Dependence of Currency Quotes

**Idea:** FX is even more fragmented than equities; the same currency pair can have very different bid-ask spreads across venues, and there is no requirement that a print on one venue be at the best cross-venue price.

**Rationale:** A backtest is realistic only if the historical data is from the same venue(s) the strategy will trade on. Aggregators like Streambase consolidate across venues and are valid only if execution can occur against that consolidated book. Trade prints in FX are often proprietary and unavailable in real time; bid-ask quotes are the appropriate backtest input and also capture the venue-dependent transaction cost.

**Takeaway:** Use bid-ask quotes (not trade prints) for FX backtests, and match the data source to the execution venue.

### Short-Sale Constraints

**Idea:** A backtest that freely shorts any name assumes a liquidity that the real world often does not provide.

**Rationale:** Stocks can be "hard to borrow" — your broker must locate shares to lend you; if short interest is already high or the float is limited, you may pay borrow interest, receive fewer shares than wanted, or be unable to borrow at all. After Lehman Brothers' collapse in the 2008–2009 crisis, the SEC banned short sales in financial-sector stocks for several months, and even SPY itself was unborrowable for the author during that period. Hard-to-borrow lists are broker-specific and not historically reconstructible; small-caps are far more affected than large-caps. ETF borrow can fail too.

The original **uptick rule (1938–2007)** required short sales at a price higher than the last trade, or at the last trade if higher than the prior trade; for Nasdaq, the reference was the last bid. The **Alternative Uptick Rule (effective 2010)** requires the trade price to exceed the national best bid only when a circuit breaker is triggered (a 10% drop from prior close, in effect for the triggering day and the following day). Either rule being in effect at the historical trade time must be modeled, or short-side backtest returns will be inflated.

**Method:** 
- Reduce exposure to small-cap shorts.
- Maintain a broker-specific hard-to-borrow list.
- Apply the uptick rule to any historical short entry.

**Takeaway:** A backtest that shorts freely is, in nearly every realistic case, an optimistic backtest.

### Futures Continuous Contracts

**Idea:** A futures strategy that uses front-month contracts needs a "continuous contract" series stitched across roll dates, and the choice of back-adjustment method has consequences that cannot be made invisible.

**Rationale:** Front-month rolls create artificial price gaps (front close p(T+1) vs. back close q(T+1) on the roll day). Two back-adjustment choices exist:
- **Price back-adjustment:** add (q(T+1) − p(T+1)) to every price p(t) on or before T. Correct P&L on the roll day; incorrect return on the roll day because the denominator becomes p(T) + (q(T+1) − p(T+1)).
- **Return back-adjustment:** multiply every price p(t) on or before T by q(T+1)/p(T+1). Correct return on the roll day; incorrect P&L.

You cannot have both correct simultaneously in a single continuous series. For a strategy that trades the **price difference** between two contracts (e.g., calendar spreads), you must use the price back-adjustment; otherwise the spread is wrong and the signal is wrong. For a strategy that trades the **ratio** of two contracts, you must use the return back-adjustment. Calendar spreads are especially sensitive because the spread is small relative to the underlying price, so the roll error is a large percentage of the signal.

A further problem with price back-adjustment: distant-past prices can go negative. The standard workaround is to add a constant to make all prices positive.

**Findings:** csidata.com uses only price back-adjustment (with optional additive constant to prevent negative prices); tickdata.com lets the user choose price vs. return back-adjustment (no constant option).

**Takeaway:** When choosing a futures data vendor, you must know which adjustment they use; when backtesting a spread model, the wrong adjustment will produce wrong signals both in backtest and live.

### Futures Close versus Settlement Prices

**Idea:** Most vendors label the "daily close" as the exchange **settlement** price, not the last trade; tick vendors may give you the last trade instead. Choose deliberately.

**Rationale:** A settlement price exists every day even if no trade occurred, and in general differs from the last trade. For most strategies, settlement is the right choice because it is closest to what you would have actually transacted at near the close. For pairs/spreads, settlement is doubly important because the two prices are guaranteed contemporaneous, provided the two contracts share an underlying and closing time. Last-trade prices can be from very different intraday moments, generating a fictitious spread that mean-reverts later for spurious profit.

For **intraday** spread strategies, the last printed price of each leg inside a bar can also be asynchronous; the proper input is the spread's own historical prints (and quote) data, where available. For **intermarket** spreads or ETF-vs-future spreads where closing times differ (e.g., gold future GC settles at 1:30 p.m. ET, gold-miners ETF GDX at 4:00 p.m. ET), the remedy is intraday bid-ask data, or to substitute a same-venue pair that closes together (e.g., GLD vs. GDX, both on Arca, both at 4:00 p.m. ET).

**Findings:** cqgdatafactory.com is cited as a vendor of intraday calendar-spread quote and trade data.

**Takeaway:** A spread backtest built from last-trade leg prices is essentially always optimistic.

## Statistical Significance of Backtesting: Hypothesis Testing

**Idea:** Any backtest performance number is a finite-sample estimate and could be due to luck. Hypothesis testing quantifies how confident we should be that the true expected return is nonzero.

**Rationale:** The general procedure tests whether the observed return is so far from zero that it would be unlikely under a specified null distribution. Three different null distributions lead to three different significance tests, and they generally give different answers — which is a feature, not a bug: each null compares the strategy to a different benchmark of randomness. Hypothesis testing's classical weakness is that it reports P(R | H₀) when we actually want P(H₀ | R), but failures to reject the null can still be informative about which features of the data the strategy is actually exploiting.

**Method:** 
1. Compute the test statistic (e.g., average daily return) from the backtest.
2. State the null hypothesis: the true average return is zero.
3. Specify a probability distribution for returns under H₀.
4. Compute the p-value: the probability of observing a statistic at least as extreme under H₀.
5. Reject H₀ (declare the result statistically significant) if p is below a threshold (e.g., 0.01).

**Formula / rule (Gaussian null, standard test):**
- Test statistic = mean(ret) / std(ret) · √(length(ret)) = daily Sharpe × √n
- Critical values for rejecting H₀ at the given p-value:

| p-value | Critical value of Sharpe·√n |
|---|---|
| 0.10 | 1.282 |
| 0.05 | 1.645 |
| 0.01 | 2.326 |
| 0.001 | 3.091 |

(Source cited: Berntson 2002.)

**Three null-distribution approaches compared:**
- **Version 1 (Gaussian):** assume daily returns are Gaussian with sample mean zero and sample standard deviation. Test statistic is Sharpe·√n. High-Sharpe strategies reject easily.
- **Version 2 (Monte Carlo on returns):** generate many (e.g., 10,000) random return series matching the observed mean, standard deviation, skewness, and kurtosis (using `pearsrnd` in MATLAB), reconstruct a price path, run the strategy on it, and ask what fraction of simulated paths produce an average return ≥ the observed one. Tests whether the strategy's profitability comes from serial correlations / patterns rather than from the first four moments.
- **Version 3 (randomized trade entries, Lo-Mamaysky-Wang 2000):** keep the actual return series, but randomly permute the entry dates of the long and short trades (preserving the count of long and short entries and the holding period). Ask what fraction of permuted trade sets match or beat the observed average return. Tests whether the trade *timing* matters, not just the moment shape.

## Example 1.1: Hypothesis Testing on a TU Futures Momentum Strategy

**Idea:** Apply all three hypothesis tests to a single 12-month-lookback, 1-month-hold momentum strategy on the TU (2-year Treasury note) future.

**Rationale:** TU is chosen because it has a fixed holding period, which simplifies Version 3 (only the entry date needs randomizing, not the hold period). The three tests deliberately stress different null hypotheses and are expected to disagree.

**Method:** 
1. Compute daily returns `ret` of the TU momentum strategy from the backtest.
2. Version 1: compute Sharpe·√n; compare to Table 1.1.
3. Version 2: draw 10,000 simulated return series of the same length with the same first four moments as the observed TU returns; build a price path; run the strategy; count fraction of simulations with average strategy return ≥ observed.
4. Version 3: draw 100,000 random permutations of the entry dates of the long and short trades; keep the actual return series; run the strategy; count fraction of permutations with average strategy return ≥ observed.

**Findings (TU momentum backtest, as reported):**
- Version 1 test statistic = **2.93**, allowing rejection of H₀ with **>99% confidence.**
- Version 2 (10,000 simulations): **1,166 simulations** produced an average return ≥ observed, so H₀ can be rejected with only **88% confidence.** (In other words, ~11.66% of random-shape distributions produced the observed result, much higher than the 1% bar.)
- Version 3 (100,000 permutations): **zero** permutations produced an average return ≥ observed, so H₀ is rejected with much greater confidence than Version 2.

**Takeaway:** The much weaker Version 2 versus much stronger Version 3 indicates that the strategy's success is not driven by the moments of the return distribution (Version 2 matched all four) but by the *timing* of trades (Version 3 destroyed performance by permuting timing). It also reveals that **any random return distribution with high kurtosis is favorable to momentum strategies** — the shape, not the timing, can be the source of the edge.

## When Not to Backtest a Strategy

**Idea:** Not every published strategy deserves the time cost of a backtest. Some should be rejected on the face of their reported numbers.

**Rationale:** Awareness of common backtest pitfalls lets a reader screen strategies before coding. Each example below illustrates a different screening heuristic.

**Five screening rules (with illustrative examples from the text):**

1. **Long drawdown, low Sharpe.** A backtest of 30% annualized return, Sharpe 0.3, with a two-year maximum drawdown is inconsistent. Few traders can stomach two years underwater; the long drawdown is also a tell that the strategy will not pass cross-validation. Skip it.

2. **No useful benchmark.** A long-only crude oil futures strategy that returned 20% in 2007 with a Sharpe of 1.5 is not superior to a buy-and-hold of the front-month contract, which returned **47%** with a Sharpe of **1.7** in the same year. The right benchmark for a long-only strategy is the buy-and-hold, and the right performance measure is the information ratio, not the standalone Sharpe.

3. **Suspect survivorship treatment.** A "buy the 10 cheapest stocks" strategy that returned **388% in 2001** is almost certainly a survivorship-bias artifact. A database that includes delisted names would have loaded the portfolio with imminent bankruptcies (near-100% loss). If the author does not state that the data includes delisted names, assume the return is inflated.

4. **Parameter explosion.** A neural-network trading model with ~100 nodes has a parameter count proportional to its nodes — at least 100. With that many knobs, the model can fit anything in-sample and predict nothing out-of-sample. The "neural net" label alone is treated by Chan as a yellow flag.

5. **Implausible high-frequency backtest.** A high-frequency E-mini S&P 500 strategy claiming 200% annualized return, Sharpe 6, with a 50-second average hold depends critically on order type, execution method, and market microstructure, and a "Heisenberg" effect may apply: your own orders change the behavior of other participants. Be deeply skeptical of any high-frequency backtest.

**Takeaway:** The first test of a strategy is the numbers on the page. If they fail any of the five screens above, do not waste time coding them.

## Will a Backtest Be Predictive of Future Returns?

**Idea:** Even a pitfall-free, statistically significant backtest is predictive only under the unstated assumption that the statistical properties of the price series are unchanging. They are not.

**Rationale:** Regime shifts (regulatory, structural, macroeconomic) can invalidate the historical relationship on which the strategy rests. Chan lists specific recent examples of regime shifts that altered which strategies were profitable.

**Method:** Maintain awareness of the following kinds of structural change, and re-evaluate any backtest that spans them:

- **Decimalization of U.S. stock quotes on April 9, 2001** (from 1/8 or 1/16 to $0.01). Effects: lower bid-ask spreads, lower displayed liquidity at the best bid/ask, lower statistical-arbitrage profitability, higher high-frequency profitability.
- **2008 financial crisis** and the subsequent **~50% drop in average daily trading volumes.** Retail participation in common stocks fell. Average market volatility decreased but the frequency of sudden outbursts increased (flash crash of May 2010, U.S. federal-debt credit-rating downgrade of August 2011). Net effect: **decreased profitability of mean-reverting strategies** that thrive on a high and constant volatility level.
- **The same 2008 crisis initiated a multi-year bear market in momentum strategies** (relevant to Chapter 6).
- **SEC Regulation NMS, implemented July 2007,** drove down average trade sizes and made the NYSE block trade obsolete.
- **Removal of the old uptick rule in June 2007** and **replacement with the Alternative Uptick Rule in 2010.**

**Takeaway:** Backtesting is not just algorithms and statistics. Awareness of the regulatory and market-structure regime is part of the job; a backtest done entirely in a pre-regime-shift data window is essentially worthless.

## Choosing a Backtesting and Automated Execution Platform

**Idea:** Platform choice determines which strategies you can express, how fast you can iterate, and which pitfalls you can structurally avoid.

**Rationale:** Chan's preferred approach uses one program for both backtest and live execution; this requires either a special-purpose platform or an institutional-grade open-source IDE. Platform choice is then driven by programming skill, asset-class coverage, latency needs, and event-processing needs.

**Method (decision flow):**
1. Choose between a special-purpose GUI/platform and a general-purpose language (with or without an IDE).
2. If choosing a general-purpose language, decide whether to use a scripting REPL language (MATLAB, R, Python) or a compiled language (C++, C#, Java).
3. Prefer a platform where the same code runs in backtest and live.
4. Confirm that the platform supports the asset classes you need.
5. Confirm that the platform supports your latency budget and strategy type (high-frequency, news-driven, CEP, etc.).
6. Confirm that the platform supports true multithreading if you will trade many symbols.

### Criterion 1 — Programming Skill

- **Little programming skill:** pick a special-purpose GUI platform (Deltix, Progress Apama, MetaTrader, NinjaTrader, Trading Blox, TradeStation Easy Language). GUI platforms limit strategy expressiveness in the long run.
- **Scripting-language comfort (MATLAB / R / Python):** the best balance of debugging ease, strategy expressiveness, and library access. MATLAB can call Java/C++/C# libraries and APIs. Excel (with or without VBA) is the historical favorite but is hard to debug, low-performance, and inefficient for execution; FXone is cited as an "Excel on steroids" — Excel-look, C++ engine, true tick-driven, true multithreaded at two levels.
- **Hard-core programming ability (C++/C#/Java):** the most flexible, efficient, and robust path. Most institutional brokers and exchanges provide APIs in these languages, or accept FIX messages generated by them (e.g., QuickFIX).

**Findings (third-party bridges for MATLAB):** Datafeed Toolbox → Trading Technologies X_TRADER; undocumentedmatlab.com IB-Matlab → Interactive Brokers; exchangeapi.com quant2ib → Interactive Brokers, quant2tt → Trading Technologies; pracplay.com → bridge to 15+ brokers; agoratron.com MATFIX → FIX protocol; QuickFIX in Java/.NET callable from MATLAB; Jev Kuznetsov's open-source IB-Matlab on MATLAB Central File Exchange; IbPy (open source) for Python → Interactive Brokers.

### Criterion 2 — Same Program for Backtest and Execution

**Rationale:** Sharing the program eliminates transcription errors between backtest and live, and structurally prevents look-ahead bias (the engine sees one bar or one tick at a time, identical to live). It is the only way to backtest true tick-based / event-driven / high-frequency strategies faithfully.

**Method:** Factor trading logic into a function that takes data and an order sink as inputs; switch the data source (historical vs. live) and order sink (simulated vs. broker) by a flag or button.

**Findings (open-source IDEs with backtest + live in one program, with various language, broker, and tick/CEP support):** ActiveQuant (Java/MATLAB/R; CTS/FIX/TT; tick-based; no CEP); AlgoTrader (Java; IB/FIX; tick-based; CEP); Marketcetera (Java/Python/Ruby; various/FIX; tick-based; CEP); OpenQuant (.NET; various/FIX; CEP status unclear); TradeLink (.NET/Java/Pascal/Python; various/FIX; tick-based; no CEP). Chan notes that institutional special-purpose platforms typically have all of these features.

### Criterion 3 — Asset Classes and Strategy Types Supported

**Rationale:** Few special-purpose platforms cover every asset class; cross-asset arbitrage is especially hard in them. MetaTrader is currencies-only. Pairs trading often needs a special module. Portfolio / statistical-arbitrage strategies with many symbols typically exceed lower-end platforms. Open-source IDEs handle all of these.

**High-frequency caveat:** Execution latency is dominated by (a) live market data latency (need colocation at the exchange or broker, and a direct exchange feed — not a consolidated feed like SIAC CTS; Interactive Brokers' feed gives only 250 ms snapshots) and (b) brokerage order-confirmation latency (some retail brokers take up to **6 seconds**; sub-10 ms requires direct market access and colocation). The software itself adds little latency (typically <10 ms) unless it has to monitor thousands of symbols. Backtesting a high-frequency strategy, however, requires many months of tick data (and possibly level-2 quotes) that overwhelm most platforms' memory, and a Heisenberg-uncertainty concern remains: the strategy's own orders change other participants' behavior.

**News-driven caveat:** Requires a machine-readable news feed as input. Most special-purpose platforms and most open-source IDEs do not have one. Exceptions cited: Progress Apama (Dow Jones + Reuters), Deltix (Ravenpack News Sentiment), Marketcetera (benzinga.com). Higher-end API feeds (Dow Jones, Thomson Reuters) are needed for high-frequency news trading; Newsware is offered as a more affordable option for slower news trading.

### Criterion 4 — Complex Event Processing (CEP)

**Idea:** CEP is event-driven (not bar-driven) execution: the program responds to the arrival of a tick or a news item, with no polling delay.

**Rationale:** A simple callback function (provided by most broker APIs) is enough for "moving average of the price over the last hour." A CEP language is more expressive for compound, sequenced, time-relative rules like "sell when order flow in the last 30 minutes is positive, price is above the moving average, volatility is low, and an important news item just arrived." CEP vendors argue that trading rules should be simple to avoid data-snooping but CEP is just expressing rules the trader already knows are profitable. Chan is not fully convinced, but flags Progress Apama and several open-source CEP-enabled IDEs (Marketcetera, AlgoTrader) for those who are.

## Colocation and Multithreading (Boxes 1.2 and 1.3)

**Idea (colocation):** Placing the trading program in a data center — VPS, broker data center, or exchange — reduces data and order-confirmation latency and reduces the risk of home power/internet outages.

**Rationale:** Reported round-trip ping times in the text: **~55 ms** to Interactive Brokers' quote server from the author's home desktop, **~25 ms** from Amazon EC2, and **~16–34 ms** from various VPSs near Interactive Brokers. Cloud/VPS does not automatically reduce latency — only a nearby, backbone-connected data center does. In-house data centers and extranet providers (BT Radianz, Savvis, TNS) provide a fast guaranteed link. The ultimate step is colocation inside the broker's data center (Lime Brokerage, FXCM) or at the exchange itself (typically requires a prime-broker relationship with sponsored access and multimillion-dollar accounts; more accessible at forex ECNs such as Currenex, EBS, FXall, Hotspot, often within Equinix NY4).

**IP-protection note:** Run executables (.p files in MATLAB, compiled binaries) on the remote server rather than source code; optionally require a time-varying password to start the program.

**Idea (multithreading):** A multithreaded platform can respond to ticks on multiple symbols simultaneously.

**Rationale:** Without multithreading, a busy listener on one symbol delays all other listeners. Java and Python have native multithreading. MATLAB requires the Parallel Computing Toolbox, which is **limited to 12 independent threads** — insufficient for trading the full SPX 500 simultaneously. Critically, lack of multithreading in MATLAB is not the same as losing ticks: a busy listener A does not make a non-busy listener B "deaf"; B processes all queued events once A finishes (cited to Kuznetsov 2010).

**Takeaway:** Colocation and multithreading are separate decisions from platform choice, but they set the achievable latency and concurrency floor. Plan the hardware tier in the same step as the software tier.

## Summary of Key Takeaways

- **Eliminating pitfalls:** A single code base for backtest and live execution eliminates look-ahead bias. Out-of-sample testing, cross-validation, high Sharpe ratios, and simplicity all help against data-snooping; walk-forward testing is the final defense.
- **Statistical significance:** Three null distributions give three answers. Version 1 (Gaussian) → Sharpe·√n. Version 2 (Monte Carlo) tests whether the *shape* of returns explains the strategy. Version 3 (randomized entries) tests whether the *timing* does.
- **Regime shifts:** Decimalization (April 9, 2001), Regulation NMS (July 2007), old uptick rule removal (June 2007), Alternative Uptick Rule (2010), and the 2008 financial crisis (with its volume collapse and multi-year momentum bear market) all invalidated backtests that crossed them.
- **Platform choice:** Match platform to programming skill (special-purpose GUI for non-programmers, scripting language for quants, compiled language for hard-core programmers). Prefer one program for backtest and live. Confirm asset-class coverage, latency support, and CEP support. Plan colocation and multithreading in the same step.
