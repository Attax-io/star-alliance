---
type: Document
timestamp: 2026-07-02T12:28:13Z
---

# Chapter 8 — Risk Management

Risk management here is not about loss aversion per se; it is the prudent use of leverage to maximize long-term compounded growth, with optional constraints on maximum drawdown and proactive avoidance of high-risk regimes. The unifying theme is that leverage should be kept constant at all times, and the chapter surveys three ways to set that constant (Kelly, Monte Carlo, historical), then layers on drawdown-control techniques (CPPI, stop loss) and leading risk indicators.

## The Constant-Leverage Mandate

**Idea:** Regardless of which method is used to set leverage, it must be held constant period-over-period, forcing position-size adjustments after every P&L.

**Rationale:** Constant leverage is mathematically required to optimize the growth rate whether or not a drawdown constraint is imposed. It is also the only way to make leverage estimates (Kelly, Monte Carlo, etc.) internally consistent with the objective of compounded growth.

**Method:** After every period, rebalance the portfolio market value to `leverage × current equity`. If equity rises from $90K to $110K at leverage 5, portfolio must grow from $450K to $550K (add $80K of securities). If equity falls to $90K, portfolio must shrink to $450K (liquidate $40K).

**Pitfalls:** "Selling into losses" can cause contagion across funds holding similar positions — cited as a cause of the August 2007 quant-fund meltdown (Khandani and Lo, 2007). Self-preservation by one fund can become a tragedy of the commons.

**Takeaway:** Constant leverage is the universal prerequisite for growth-rate optimization; accept the counterintuitive "sell losers, buy winners" rebalancing as a feature, not a bug, but recognize its systemic risk.

## Optimal Leverage: Three Methods

**Idea:** Three methods of differing restrictiveness can each be used to find the leverage that maximizes compounded growth rate, with progressively fewer distributional assumptions.

**Rationale:** No method is "right" — each trades elegance for realism. All three share the assumption that future return distributions resemble the past, which is usually wrong but unavoidable. The choice depends on the strategy's return distribution (Gaussian vs. fat-tailed) and on whether the trader can tolerate potential ruin.

**Method (overview):**
1. **Kelly formula** — closed-form under Gaussian assumption.
2. **Monte Carlo on Pearson-system simulated returns** — relaxes Gaussian, uses first four moments (mean, std, skewness, kurtosis) to generate 100,000 random returns, then maximizes expected `g(f) = ⟨log(1 + fR)⟩` numerically.
3. **Historical brute-force optimization** — directly maximizes the realized compounded growth rate of the backtest returns with respect to `f`.

## Kelly Formula (Gaussian)

**Idea:** Under the Gaussian assumption, optimal leverage is a simple ratio of mean to variance of excess returns.

**Formula / rule:** `f = m / s²`, where `m` is mean excess return and `s²` is variance of excess returns. For multiple strategies sharing a common equity pool: **F** = `C⁻¹ M`, where **C** is the covariance matrix of portfolio returns and **M** is the vector of mean excess returns.

**Rationale:** Thorp (1997) proves this maximizes the compounded growth rate when the Gaussian approximation holds. Beyond single-strategy sizing, the vector form gives the optimal allocation of buying power across portfolios.

**Pitfalls:** Estimation errors in mean and variance are catastrophic in one direction — overestimated `m` or underestimated `s²` inflates leverage and can lead to ruin. Underestimated leverage only costs growth rate. The formula is dangerously sensitive to input error.

**Takeaway:** Treat Kelly as an upper bound, not a target; many traders use **half-Kelly** as a practical compromise. Chan reports that Russell 1000 and 2000 have Kelly leverage ≈ 1.8, making Direxion's triple-leveraged ETFs BGU and TNA (leverage = 3) structurally prone to NAV going to zero.

**Method (multiple strategies under leverage cap):** If the broker's `Fmax` is binding, the standard rescaling `Fi × Fmax / Σ|Fi|` is suboptimal. When `Fmax` is much smaller than the unconstrained total gross leverage, it is often growth-rate-optimal to invest all buying power into the single strategy with the highest mean excess return / lowest variance ratio.

## Monte Carlo Optimization on Simulated Returns

**Idea:** Replace the Gaussian assumption with a Pearson-system distribution fit to the first four empirical moments, draw 100,000 simulated returns, and numerically maximize the expected log-growth.

**Formula / rule:** `g(f) = ⟨log(1 + fR)⟩`, averaged over sampled `R`. For a non-Gaussian `R` this is not analytic, so Monte Carlo plus `fminbnd`-style numerical search is used.

**Rationale:** Captures skewness and kurtosis (fat tails) that the Kelly formula ignores, giving a more realistic optimal leverage. For some distributions no analytic answer exists, making simulation the only practical option.

**Method:**
1. Compute `{mean, std, skewness, kurtosis}` of strategy's daily returns.
2. Sample 100,000 returns from the corresponding Pearson distribution (e.g., via `pearsrnd`).
3. Numerically minimize `−g(f)` over `f` using the simulated series.

**Findings (Example 5.1 mean-reversion strategy):**
- Kelly leverage (from test set): 18.4.
- Monte Carlo optimal `f`: ≈ 19 (close to Kelly, but not identical).
- At `f = 31` the growth rate becomes −1 (ruin), because the most negative daily return was −0.0331, giving ruin threshold `1/0.0331 = 30.2`.

**Pitfalls:** Pearson captures only four moments — higher moments (e.g., infinite-variance Pareto–Levy) are missed. Capturing more moments invites data-snooping bias from limited data. Different random seeds give slightly different optimal `f`.

**Takeaway:** Monte Carlo gives a sanity check on Kelly and a more honest answer for fat-tailed strategies; ruin happens well before Kelly's "infinite" answer if any single period's loss exceeds `1/f`.

## Historical Brute-Force Optimization

**Idea:** Skip distributional assumptions entirely and just maximize the realized compounded growth rate of the backtest with respect to leverage.

**Method:** Feed the actual backtest return series into the same `g(f)` function and minimize `−g(f)`.

**Findings (same mean-reversion strategy):** Optimal `f` = 18.4, identical to Kelly on this dataset.

**Pitfalls:** Suffers from data-snooping bias — the optimal `f` for this one historical realization is unlikely to be optimal for future realizations. Insufficient data for robust worst-case sizing.

**Takeaway:** Useful as a quick cross-check; in Chan's example it agreed exactly with Kelly. Reasonable as a third opinion alongside Kelly and Monte Carlo, not as a standalone answer.

## Maximum-Drawdown Constraint

**Idea:** When an external constraint caps the allowable drawdown (e.g., client mandate, risk manager, spouse), that cap becomes an additional constraint on the leverage optimization.

**Rationale:** Drawdown limits and growth-rate maximization often conflict; the drawdown bound is non-negotiable when managing other people's money.

**Findings (mean-reversion example):** With unconstrained optimal `f` ≈ 19.2, simulated max drawdown was −0.999. Halving `f` to 9.6 still gave max DD of −0.963. To bring DD down to ≈ 0.5, `f` had to be lowered by a factor of 7 (to ≈ 2.7). Using historical returns instead, halving `f` (to 13) brought max DD below −0.49 — a 1.5× reduction sufficed there.

**Pitfalls:** Reducing leverage proportionally to the drawdown ratio is wrong — the relationship is highly nonlinear and must be found by trial-and-error (or numerical search). The two methods (simulated vs. historical) can give very different answers.

**Takeaway:** A good compromise is a leverage between the historical-fit and simulation-fit values. Simulated max DD is a VaR-like statistic that may correspond to a once-in-a-million-years event; historical max DD covers a realistic strategy lifespan but undersamples tail risk. Neither alone is sufficient.

## Constant Proportion Portfolio Insurance (CPPI)

**Idea:** Allocate only a fraction `D` of total equity to a "trading subaccount," apply the strategy's full Kelly leverage to that subaccount, and leave `(1 − D)` in cash; reset the subaccount upward at new high-water marks only.

**Rationale:** Simultaneously caps drawdown at `−D` (by construction the subaccount cannot be fully lost) and preserves Kelly-leverage upside on the active portion. The cash buffer grows with profits, locking in gains without the choppiness of stop-loss exits.

**Method:**
- Set `subaccount_equity = D × total_equity`; trade with leverage `f` on the subaccount.
- After each period, if total equity hits a new high, transfer cash so subaccount is again `D × total_equity`.
- If losses deplete the subaccount, the strategy is wound down — a graceful, principled exit replacing the emotional one.

**Findings:** On 100,000 simulated days with `D = 0.5`, CPPI's growth rate was 0.002484/day vs. 0.002525/day for the alternative (`fD` leverage on full account) — essentially the same. But CPPI's max DD was < 0.5 (by design) vs. 0.9 for the no-stop-loss alternative at half Kelly.

**Pitfalls:**
- CPPI is **not** equivalent to running leverage `fD` on the full account — CPPI shrinks position size much faster on drawdowns and so will underperform the simple-rescale approach in any period with losses.
- If multiple strategies share one CPPI envelope, profitable strategies subsidize losers and the combined drawdown may never reach `−D`, preventing the natural shutdown of bad strategies.
- Cannot prevent gap/overnight drawdowns or losses during market closures — must be hedged with out-of-the-money options for known downtime.

**Takeaway:** CPPI is the only technique that meaningfully reconciles growth-rate maximization with a hard drawdown cap, and is preferred over a stop-loss-based drawdown limit because the stop-loss can only trigger once in a strategy's life.

## Stop Loss

**Idea:** Two distinct usages exist: (1) exit an individual position when its unrealized loss exceeds a threshold, then re-enter later; (2) shut the strategy down entirely on a cumulative drawdown threshold (rare, awkward, only triggers once).

**Rationale (momentum):** If momentum is reversing, exiting is the logically correct response — a continuously updated momentum signal is itself a de facto stop loss, so momentum strategies do not face the same tail risk as mean-reverting ones.

**Rationale (mean reversion) — and why it is controversial:** Stop loss appears to contradict the central premise of mean reversion. Chan has never backtested a mean-reverting strategy whose APR or Sharpe improved with a stop loss imposed — but this conclusion is contaminated by survivorship bias, because failed mean-reverting strategies that would have benefited from stops were already excluded from the profitable backtest pool.

**Pitfalls:**
- Ineffective against overnight gaps and market closures; requires option hedges for known downtime.
- Useless when liquidity providers withdraw simultaneously — flash crash of May 6, 2010, where stop-loss sell orders on Accenture executed at $0.01 (stub quote) (Arnuk and Saluzzi, 2012).
- On a "turncoat" price series that regime-changes from mean-reverting to trending, no stop loss in the original backtest would have triggered, yet a real stop loss would have prevented catastrophic losses.

**Takeaway:** Set the stop loss for a mean-reverting strategy at a level **greater than** the backtest's maximum intraday drawdown, so it never triggers in-sample but still provides black-swan protection. For momentum, the trading signal itself is the stop.

## Leading Risk Indicators

**Idea:** Rather than react to losses after the fact, use indicators that predict whether the next period will be risky for a given strategy.

**Rationale:** No single indicator works for all strategies — what is risky for one may be profitable for another. A leading indicator must be tested against the specific strategy, not in isolation.

**Findings (VIX as strategy-specific indicator):**
- **Buy-on-gap stocks (Ch. 4, May 2006–Apr 2012):** Baseline annualized return ≈ 8.7%, Sharpe ≈ 1.5. When prior-day VIX > 35, next-day annualized return jumps to **17.2%** (Sharpe 1.4) — high VIX is *favorable* for this strategy.
- **FSTX opening gap (Ch. 7, Jul 2004–May 2012):** Baseline annualized return ≈ 13%, Sharpe ≈ 1.4. When prior-day VIX > 35, next-day return collapses to **2.6%** with Sharpe **0.16** — VIX > 35 is a clear "don't trade today" signal.

**Other indicators discussed:**
- **TED spread** (3M LIBOR − 3M T-bill): measures bank default risk; peaked at 457 bps in 2008. Useful as a relative-time-series signal despite known LIBOR manipulation (Snider & Youle, 2010).
- **HYG** (high-yield bond ETF), **MXN** (Mexican peso — used as a risky-asset proxy during the 2011 European debt crisis), and **ONN/OFF** (at time of writing only ~7 months of history; unproven).
- **Order flow** (short-horizon): a sudden negative shift in order flow on a risky asset is a short-term leading risk indicator, often reflecting informed institutional flow (Lyons, 2001); it works at higher frequency than any other indicator.
- **Strategy-specific:** oil price as a leading risk indicator for GLD/GDX pair trading (Ch. 4); gold price for gold-producer pairs; Baltic Dry Index for export-country ETFs/currencies.

**Pitfalls:** Financial panics are rare, so backtesting the efficacy of any leading indicator is highly susceptible to data-snooping bias. No financial indicator can predict non-financial disasters (Rumsfeld's "unknown unknowns").

**Takeaway:** Use a leading risk indicator matched to the specific strategy — VIX > 35 is a profitable filter for one gap strategy and a stop-trading signal for another. Order flow is the most promising high-frequency leading indicator. Always discount backtests of risk indicators for data-snooping bias.

## Chapter Key Points (Chan's own summary)

- **Growth-rate maximization:** For long-term net-worth maximization, start with **half-Kelly**. For fat-tailed returns, prefer **Monte Carlo** over the Kelly formula. As a coarse check, brute-force the **historical backtest** growth rate. To cap drawdown while keeping upside, use **CPPI**.
- **Stop loss:** Will usually *hurt* the backtest performance of mean-reverting strategies (survivorship bias), but prevents black swans; set the level **outside** the backtest's max intraday DD. For momentum strategies, the signal itself is the stop.
- **Risk indicators:** Candidate leading indicators — VIX, TED spread, HYG, ONN/OFF, MXN, plus order flow. Beware data-snooping bias when backtesting.
