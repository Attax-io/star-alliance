---
type: Document
title: Evaluation and pitfalls
description: Rolling-origin backtest, interval-coverage scoring, quantile-based anomaly detection, and the recurring TimesFM mistakes.
timestamp: 2026-06-28T00:00:00Z
---

# Evaluation and pitfalls

A forecast you have not backtested is a hope. Score both the point and the
interval, and watch for the handful of mistakes that bite every time.

## Rolling-origin backtest

A single train/test split overfits to one window. Roll the origin: forecast from
several cut points and average the scores. This is how you decide TimesFM vs a
classical baseline (`foundation-vs-classical.md`) and how you tune `max_context`.

```python
H = 24
errs, covs = [], []
for cut in range(len(values) - 5 * H, len(values) - H, H):   # 5 rolling origins
    train, actual = values[:cut], values[cut:cut + H]
    point, q = model.forecast(horizon=H, inputs=[train])
    pred = point[0]
    errs.append(np.mean(np.abs(actual - pred)))                       # MAE
    inside = (actual >= q[0, :, 1]) & (actual <= q[0, :, 9])          # in 80% band
    covs.append(inside.mean())
mae      = float(np.mean(errs))
coverage = float(np.mean(covs)) * 100   # should be ≈ 80
```

## Metrics — and why coverage matters

- **MAE / RMSE**: point error in the series' own units. RMSE punishes large
  misses harder.
- **MAPE**: percent error — undefined / explosive near zero; avoid for series
  that cross or sit near 0 (returns, spreads).
- **Interval coverage**: fraction of actuals inside the 80% band (q10–q90). It
  should be ≈ 80%. **Far below** → bands too tight, model overconfident, do not
  use them for sizing. **Far above** → bands too wide, intervals uninformative.

A model with slightly worse MAE but *honest* coverage beats a tighter,
overconfident one — the second lies about its own risk.

## Anomaly detection falls out of the quantiles

No separate model. Forecast, then flag actuals that escape the band:

```python
point, q = model.forecast(horizon=H, inputs=[history])
lower, upper = q[0, :, 1], q[0, :, 9]          # 80% band (q10, q90)
anomalies = (actual < lower) | (actual > upper)
```

| Severity | Condition | Meaning |
| --- | --- | --- |
| Normal | inside 80% band | expected |
| Warning | outside 80% band | unusual but possible |
| Critical | outside the 90% band | rare (<10% probability) |

For **in-context** anomaly scanning of trending data, detrend first: fit a linear
trend, take residuals, z-score the residuals (critical at |z| ≥ 3, warning ≥ 2).
Raw z-scores on a trending series flag the trend itself as a wall of anomalies.

## Recurring mistakes

1. **Quantile off-by-one.** `quantiles[..., 0]` is the **mean, not q0**. q10 =
   index 1, q90 = index 9, median = index 5. Name them: `IDX_Q10, IDX_Q90 = 1, 9`.
2. **Forgot to compile.** `forecast()` before `compile()` raises
   `RuntimeError: Model is not compiled`.
3. **Passed an array, not a list.** `inputs` must be `[array]`, not `array`.
4. **Trailing NaNs.** Leading/internal NaNs are handled; trailing are **not** —
   strip them or the tail corrupts the context.
5. **Wrong sign clamp.** `infer_is_positive=True` (default) clamps the forecast
   ≥ 0 — silently wrong for returns, temperature, PnL, spreads. Set it False.
6. **Covariate horizon span.** Dynamic covariates must cover the full
   `context + horizon`; a covariate you do not know into the future cannot be
   used without first forecasting it.
7. **`forecast_with_covariates()` on TimesFM 1.0** — does not exist; needs 2.5.
8. **Wrong column name / unnormalized inputs** — print `df.columns` first; keep
   `normalize_inputs=True` so disparate scales do not destabilize the forecast.
9. **Headless plotting** — call `matplotlib.use("Agg")` before importing pyplot
   when running without a display.

## Quality checklist (run before declaring success)

- [ ] `point` is `(n_series, horizon)`; `quantiles` is `(n_series, horizon, 10)`.
- [ ] Quantile indices by name (0 = mean, 1 = q10, 5 = q50, 9 = q90).
- [ ] No NaN in output: `np.isnan(point).any()` is False.
- [ ] Context ≥ ~32 points per series.
- [ ] `infer_is_positive` matches the sign domain of the series.
- [ ] Backtest reports both point error AND interval coverage (≈ nominal).
- [ ] TimesFM 1.0/2.0: `freq=[0]` for monthly. TimesFM 2.5: omit.
