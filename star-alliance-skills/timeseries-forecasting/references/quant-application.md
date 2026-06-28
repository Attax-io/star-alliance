---
type: Document
title: Quant and trading application
description: How a trading/quant member should and should not use TimesFM, why it is not alpha on liquid prices, and its honest uses.
timestamp: 2026-06-28T00:00:00Z
---

# Quant and trading application

The merchant carries this skill. The discipline is knowing what a public,
zero-shot forecaster can and cannot honestly do in a market context.

## The hard truth: TimesFM is not alpha on a liquid price

Feeding a stock/FX/crypto **price level** to TimesFM and trading the forecast is
a trap. A public foundation model holds no information the market lacks; on a
liquid, near-efficient instrument the price already embeds the consensus
expectation. The model will happily extrapolate trend and seasonality, but that
is *not edge* — it is a confident restatement of what is already priced. Treat
any "the model says it goes up" on a liquid price as **noise to be backtested
into the ground**, not a signal. If a naive forecast beat the market, everyone
running the same open weights would have arbitraged it away.

What *can* carry edge: a **proprietary** series the market does not price
(internal order flow, a private demand panel, a niche fundamental), or using the
forecast's *distribution* rather than its point (see below).

## Where it is genuinely useful

- **Operational / business forecasting.** Demand, sales, inventory, headcount,
  cash flow, capacity — the bread-and-butter "project this metric forward N
  periods". Here the merchant's value is real and TimesFM shines: batch, zero
  tuning, calibrated bands.
- **Volume and liquidity, not direction.** Forecasting *traded volume* or
  intraday volume curves (for VWAP scheduling, execution sizing) is a far more
  defensible target than price direction.
- **Realized-volatility / range forecasting.** Project a volatility proxy
  forward to size positions or set stops — direction-free, and the **interval**
  is the product.
- **Macro and fundamental series.** Project published macro prints (claims,
  inventories, a slow fundamental) where the series is genuinely autoregressive
  and not instantly arbitraged.
- **Anomaly / regime flags.** Use the quantile bands as a tripwire: an actual
  escaping the 90% interval is a statistically rare move worth a human look
  (`evaluation-and-pitfalls.md`).
- **Scenario bands for risk.** The q10/q50/q90 fan is a ready-made
  optimistic/base/pessimistic envelope to feed downstream sizing.

## Use the distribution, not the point

For a quant the *interval* is usually more valuable than the median. The q10–q90
spread is a model-implied uncertainty you can:

- turn into position sizing (wider band → smaller size),
- compare against option-implied ranges (cheap vs the model's view),
- backtest for coverage and only then trust for risk.

Always validate coverage on a rolling backtest before any sizing relies on the
bands; an overconfident band is worse than no band.

## Covariates that make sense in markets

Use XReg only with **known-future** drivers: an earnings/economic-release
calendar, a holiday/half-day schedule, day-of-week / month-end effects, a planned
auction or roll date. Do **not** stuff in another price you would also have to
forecast — that just moves the unknown.

## Process discipline (merchant)

1. Frame the target so it is *forecastable* (volume / vol / a proprietary series
   — not a liquid price direction you expect to beat the market on).
2. Backtest rolling-origin against seasonal-naive *and* an ARIMA/ETS baseline.
3. Score interval coverage, not just MAE.
4. Ship only if it beats the baseline on the relevant horizon; re-check on drift.
5. Never present a forecast without its interval and the backtest that earned it.

## Relation to neighbouring merchant skills

- **market-recon** — gathers and interprets market context (catalysts, sentiment,
  positioning). This skill turns a chosen *numeric series* into a forward
  distribution; it does not gather context.
- **trading-strategy** — builds the entry/exit/sizing rules. A TimesFM forecast +
  interval is an *input* to a strategy, never the strategy.
- **portfolio-risk** — aggregates exposure, drawdown, VaR across positions. This
  skill can hand it a forward distribution for one series but does not do
  portfolio aggregation.
- **probability-statistics** — the general inference/distribution toolkit
  (hypothesis tests, estimators, Monte Carlo). This skill is one applied
  instrument — a pretrained sequence forecaster — that lives inside it.
