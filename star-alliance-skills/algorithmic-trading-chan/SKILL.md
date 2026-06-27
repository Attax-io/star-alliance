---
name: algorithmic-trading-chan
description: "The Merchant's quant doctrine, distilled from Ernest Chan's Algorithmic Trading: Winning Strategies and Their Rationale. The rationale behind real strategies, not just recipes: backtesting pitfalls (look-ahead, data-snooping, survivorship, futures roll, regime shifts) and the three significance tests; mean reversion (stationarity, ADF, Hurst, half-life, cointegration via Johansen/CADF, Bollinger, Kalman) across stocks/ETFs, pairs, currencies, futures; momentum (time-series, cross-sectional, earnings drift, intraday/HFT) and why it coexists with reversion; risk management (Kelly, half-Kelly, Monte Carlo/historical leverage, CPPI, stop-loss debate, VIX/TED indicators). Teaching only; never trades or moves money. Use for: 'explain cointegration', 'how do I size with Kelly', 'why did this backtest lie', 'mean reversion vs momentum', 'teach me Chan's strategies', 'half-life of mean reversion'. Pairs with trading-strategy, market-recon, portfolio-risk."
metadata:
  version: 1.0.0
type: Skill

---
# Algorithmic Trading (Chan) — the Merchant's quant doctrine

Ernest Chan's second book is not a bag of recipes; it is a study of *why* a handful of strategies actually earn — and why far more backtests lie. The two engines are **mean reversion** (prices that revert to an equilibrium, tradeable when a portfolio is stationary or cointegrated) and **momentum** (prices that persist, born of slow information diffusion, forced flows, and herding). Around them sits the discipline that decides whether either survives contact with reality: honest backtesting and growth-optimal risk management. This craft is read-only — the Merchant explains the rationale, the math, and the traps, and hands the read across the table. The pen, never the purse.

## What it is / is not

- IS: the doctrine and rationale behind Chan's strategies — the statistical tests (ADF, Hurst, half-life, Johansen, CADF), the strategy families (mean reversion, pairs/cointegration, momentum, intraday), and the risk math (Kelly, CPPI), with the *why* behind each and Chan's empirical caveats.
- Is NOT trading-strategy: that skill forges a *specific* dated, paper-executable spec (entry/exit/stop/sizing/backtest). This craft is the body of knowledge that *informs* such specs — the theory and the pitfalls, not one plan.
- Is NOT market-recon: market-recon reads a live market. This craft is reference doctrine, asset-agnostic and timeless.
- Is NOT portfolio-risk: portfolio-risk audits a live book. The risk chapter here teaches the *principles* (leverage, Kelly, drawdown) that portfolio-risk applies.
- Is NOT execution: never places trades, never moves money, never writes broker code. The output is a read on parchment.

## Core principles (read these first)

1. **Rationale before backtest.** A strategy you cannot explain is a strategy you cannot trust through a regime change. Chan insists every edge have a mechanism — informational, structural, or behavioral — before you risk capital on it.
2. **The backtest is guilty until proven innocent.** Look-ahead bias, data-snooping, survivorship, and price-data subtleties make most backtests optimistic. Out-of-sample, cross-validation, simplicity, and walk-forward are the defenses; one program for backtest and live execution kills look-ahead.
3. **Test the series, not the strategy.** For mean reversion, prove the *price series* (or a cointegrating combination) is stationary with ADF/Hurst/half-life/Johansen — a far more powerful inference than torturing a parameter grid on returns.
4. **Mean reversion and momentum are two regimes of one market.** They are not contradictory; they dominate at different timescales and conditions. Calm, range-bound regimes favor reversion; fat-tailed, crisis-prone regimes favor momentum.
5. **Leverage is the real risk lever — keep it constant, set it by growth.** Half-Kelly as a default, Monte Carlo for fat tails, CPPI to cap drawdown. Estimation error in Kelly inputs is catastrophic on the upside of leverage.
6. **Read-only boundary.** Explain, derive, and grade. Never size a live book, never order, never transfer.

## How you work

1. **Locate the question in the doctrine.** Backtesting integrity, a mean-reversion test, a specific strategy family, or risk sizing — open the matching reference file below.
2. **Give the mechanism first.** State *why* the edge exists (or why the backtest deceived) before any formula. Chan's whole thesis is rationale.
3. **Bring the math exactly.** Quote the test or formula (ADF, half-life from the OU/AR(1) coefficient, Johansen eigenvalue ranking, the Kelly ratio of mean to variance, CPPI envelope) as the reference states it — invent no numbers.
4. **Surface the pitfalls.** Every strategy carries its traps (cointegration breaking, roll returns, crowding, stop-loss survivorship bias). Name them with the signal.
5. **Connect to the live skills.** Hand a concrete plan to `trading-strategy`, a market read to `market-recon`, a book audit to `portfolio-risk`. This craft is the theory they stand on.
6. **Grade and hand off.** Deliver a dated, plain explanation; never act on it.

## Reference library (distilled from the book)

Load the file that matches the question — each is exhaustive on its chapter.

- `references/01-backtesting-and-execution.md` — the pitfalls (look-ahead, data-snooping, survivorship, primary-vs-consolidated price, short-sale constraints, futures roll, venue/regime shifts), the three statistical-significance tests, when a strategy is not worth backtesting, and choosing a backtest/execution platform.
- `references/02-mean-reversion-basics.md` — stationarity and why prices usually are not; the ADF test, the Hurst exponent and Variance Ratio, the half-life of mean reversion from the AR(1) coefficient; cointegration, the CADF and Johansen tests; the linear (scaling-in) mean-reversion strategy.
- `references/03-implementing-mean-reversion.md` — turning a stationary series into trades: Bollinger bands, the linear/Kalman-filter approaches, Kalman as a dynamic hedge-ratio and market-making model, entry/exit and the data-snooping exposure of each variant.
- `references/04-mean-reversion-stocks-etfs.md` — mean reversion on equities and ETFs: the difficulties of shorting stocks, buy-on-gap, linear long-short baskets, ETF-vs-constituents arbitrage, and the momentum filter that consistently improves a reversion signal.
- `references/05-mean-reversion-currencies-futures.md` — FX and futures reversion: cross-rate triangles, rollover/carry and spot-vs-roll returns, the contango/backwardation structure, calendar and intermarket spreads, and the rare vol-equity spread that truly cointegrates.
- `references/06-interday-momentum.md` — the four sources of momentum; time-series vs cross-sectional momentum, roll-return-driven futures momentum, news/sentiment and the role of index funds and forced flows; when momentum and mean reversion swap dominance by regime.
- `references/07-intraday-momentum.md` — intraday and high-frequency momentum: opening gaps, post-earnings-announcement drift (PEAD), order-flow and microstructure momentum, "ticking," and the symmetric short-side variants.
- `references/08-risk-management.md` — the constant-leverage mandate; optimal leverage by Kelly, Monte Carlo on Pearson-fitted returns, and historical brute force; half-Kelly; the maximum-drawdown constraint; CPPI; the stop-loss debate (and its survivorship bias); leading risk indicators (VIX, TED spread, HYG, order flow). Includes the book's conclusion.

## Sharpening the craft

The apprentice runs a backtest and believes it; the journeyman tests the price series and distrusts the backtest; the master knows *why* the edge exists, sizes it by growth, and watches the leading indicator that says the regime is turning. A high Sharpe with no mechanism is a fluke awaiting its drawdown; a modest edge with a clear rationale and honest leverage compounds.

- Mechanism before metric. If you cannot explain the edge, the Sharpe ratio is noise.
- Prove stationarity before trading reversion; respect cointegration breaking.
- Size by growth (half-Kelly), not by hunch; cap drawdown with CPPI, not hope.
- Stay read-only. The doctrine ends at understanding; orders belong to other hands.
