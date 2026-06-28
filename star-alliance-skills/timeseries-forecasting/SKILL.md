---
name: timeseries-forecasting
metadata:
  version: 1.0.0
type: Skill
description: "Project a numeric time series forward with Google's TimesFM zero-shot foundation model, returning a point forecast plus calibrated quantile prediction intervals — no per-series training. Triggers on 'forecast this series', 'predict the next N periods', 'time-series forecast', 'project this metric forward', 'forecast demand/volume/price'. Adds uncertainty bands, quantile-based anomaly flags, batch-forecasting many series, and covariate (XReg) forecasting with known-future drivers. Covers when a foundation model beats classical ARIMA/Prophet, context/horizon framing, and rolling backtest evaluation. Differs from market-recon (gathers market context), trading-strategy (entry/exit rules), portfolio-risk (exposure/VaR), and probability-statistics (general inference toolkit) — this projects one series forward."
---

# Time-Series Forecasting (TimesFM foundation model)

Forecasting a series forward is a craft of **framing**, not a button. The model
returns numbers no matter what you feed it — the skill is choosing context,
horizon, covariates, and uncertainty handling so those numbers mean something,
and knowing when a foundation model beats a fitted classical one.

This skill distils the craft of **zero-shot foundation-model forecasting** with
Google's TimesFM (decoder-only, pretrained on a large time-series corpus). You
hand it a univariate series and it returns a point forecast plus calibrated
quantile bands — no per-series training. The merchant uses it to project a
metric forward (demand, volume, a price level, a macro print) when fitting and
maintaining a bespoke ARIMA/Prophet per series is not worth it.

## What it is / is not

**It is:** a way to get a *distributional* forecast (median + quantiles) for
many series cheaply and instantly; a strong default when you have hundreds of
series or no time to tune; a probabilistic source you can turn into prediction
intervals, anomaly flags, or scenario bands.

**It is not:** a coefficient model you can interpret ("a 1% rate cut moves
sales 0.3%"); a multivariate / Granger-causality engine; an alpha signal by
itself — a public foundation model has no edge over the market's own
expectations on a liquid price (see `references/quant-application.md`); a
classifier or clustering tool; a substitute for the offline backtest that tells
you whether it actually helps *your* series.

## When TimesFM vs classical (the first decision)

- **Many series, no time to tune, decent history** → foundation model. One
  compiled model batch-forecasts hundreds of series in one call; no per-series
  fitting.
- **One series, want interpretable coefficients / explicit seasonality terms**
  → classical (`statsmodels` ARIMA/ETS, Prophet). You can read the model.
- **Need exogenous drivers** (price, promo, holidays, weather) → TimesFM 2.5
  *with covariates (XReg)*, or a classical regression-with-ARIMA-errors. Decide
  by whether the driver's future values are known over the horizon.
- **Always**: settle it with a rolling-origin backtest on held-out windows, not
  by reputation. TimesFM is a strong *default*, not a guaranteed winner.
  Full decision logic: `references/foundation-vs-classical.md`.

## Generative principles

**1. Forecasting is framing — context and horizon are the real knobs.**
Before any code, decide the *context* (how much history the model sees) and the
*horizon* (how far ahead). Give at least 3–5 full cycles of the dominant pattern
(weekly seasonality on daily data → ≥ 21–35 days of context). Longer horizons
degrade; trust the near term more than the tail. `max_context`/`max_horizon` are
set once at `compile()`; you can still call `forecast(horizon=M)` for any
`M ≤ max_horizon`. Match context to data frequency, not to "more is better"
(table in `references/api-and-usage.md`).

**2. Always forecast a distribution, never just a point.** TimesFM returns
`(point, quantiles)` where `quantiles` is `(batch, horizon, 10)`:
index 0 = mean, 1 = q10, 5 = q50 (= the point), 9 = q90. The off-by-one here is
the single most common bug — `quantiles[..., 0]` is the **mean, not q0**. The
spread between q10 and q90 *is* your risk estimate; a forecast quoted without it
is a guess dressed as a number. Set `use_continuous_quantile_head=True` and
`fix_quantile_crossing=True` so the bands are calibrated and monotone.

**3. Normalize, and tell the model the sign domain.** Set
`normalize_inputs=True` always (z-norms each series; prevents scale blow-ups).
Set `infer_is_positive=True` for inherently non-negative series (demand,
volume, counts, price *levels*) so the floor stays at 0 — but set it **False**
for anything that can go negative: temperature, *returns*, PnL, spreads. Getting
this wrong silently clips half your distribution.

**4. Covariates earn their place only when their future is known.** A dynamic
covariate must be supplied over the **full `context + horizon`** window — so it
only helps if you *know* its future values (a published holiday calendar, a
scheduled promotion, a planned price). An unknown-future driver (next month's
weather you don't have) cannot be a covariate without first forecasting it.
Three kinds: dynamic-numerical (price, temp), dynamic-categorical (day-of-week,
holiday flag), static-categorical (region, store id). Requires TimesFM 2.5 +
`timesfm[xreg]`. Detail: `references/api-and-usage.md`.

**5. Evaluate with a rolling backtest, score the interval too.** Hold out the
last H points, forecast from the truncated history, compare to actuals — then
roll the origin forward several times. Report point error (MAE / RMSE / MAPE)
**and interval coverage**: the fraction of actuals that land inside the 80% band
should be ≈ 80%. Coverage far from nominal means the bands are mis-calibrated
and you should not trust them for sizing. A model with worse MAE but honest
coverage can beat a tighter, overconfident one.

**6. Anomaly detection falls out of the quantiles — it is not a separate
model.** An actual value below q10 or above q90 is statistically unusual
(outside the 80% band); outside q10/q90 of the *90% interval* is rare (<10%).
For trending series, detrend first (linear fit → residuals → z-score) before
flagging, or the trend itself reads as a string of anomalies. Pattern in
`references/evaluation-and-pitfalls.md`.

**7. Preflight the machine and the dataset before you load.** TimesFM 2.5 (200M)
needs ~1.5 GB RAM on CPU / ~1 GB VRAM and downloads ~800 MB of weights on first
use. The archived 500M v2.0 needs ≥ 16 GB RAM — prefer 2.5. Estimate batch RAM
as `0.8 + 0.5 + 0.0002 × num_series × context_length` GB and chunk large
batches rather than OOM mid-run. Sizing tiers: `references/api-and-usage.md`.

## Quick shape (orientation, not a tutorial)

```python
import torch, numpy as np, timesfm
torch.set_float32_matmul_precision("high")

model = timesfm.TimesFM_2p5_200M_torch.from_pretrained("google/timesfm-2.5-200m-pytorch")
model.compile(timesfm.ForecastConfig(
    max_context=1024, max_horizon=256, normalize_inputs=True,
    use_continuous_quantile_head=True, fix_quantile_crossing=True,
    infer_is_positive=False,   # series can go negative (returns, temp, spreads)
))
point, q = model.forecast(horizon=24, inputs=[series_a, series_b])  # list of 1-D arrays
# point: (2, 24)   q: (2, 24, 10)  -> q[...,1]=q10, q[...,5]=median, q[...,9]=q90
```

Model variants: TimesFM **2.5** (latest, 200M, 16k context, no `freq` flag) is
the default. **2.0** (500M) and **1.0** (200M, 2k context) are archived and
require `freq=[0]` for monthly data. Always prefer 2.5.

## References

- `references/foundation-vs-classical.md` — the decision: foundation model vs
  ARIMA/ETS/Prophet; what zero-shot buys and costs; how to settle it empirically.
- `references/api-and-usage.md` — model classes, `ForecastConfig` every flag,
  output shapes, covariates (XReg), data prep / NaN handling, hardware sizing.
- `references/evaluation-and-pitfalls.md` — rolling backtest, coverage scoring,
  anomaly detection, and the recurring mistakes (quantile off-by-one, trailing
  NaNs, covariate horizon span, sign clamp).
- `references/quant-application.md` — how a trading/quant member should and
  should not use it; why it is not alpha on liquid prices; volume/vol/macro
  uses; relation to market-recon, trading-strategy, portfolio-risk,
  probability-statistics.

## How this differs from neighbouring skills

- **market-recon** gathers and reads the market context (what is happening, why);
  this skill *projects a numeric series forward* with calibrated uncertainty.
- **trading-strategy** designs entries/exits/sizing rules; this skill is an input
  to one (a forecast + interval), never the strategy itself.
- **portfolio-risk** measures exposure/drawdown/VaR across positions; this skill
  can *feed* it a forward distribution but does not aggregate portfolio risk.
- **probability-statistics** is the general inference/distribution toolkit; this
  skill is one applied instrument — a pretrained sequence model — within it.
