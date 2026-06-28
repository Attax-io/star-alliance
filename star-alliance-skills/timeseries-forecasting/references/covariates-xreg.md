---
type: Document
title: TimesFM XReg covariates — kinds, modes, tuning, dual output
description: The full forecast_with_covariates surface for TimesFM 2.5 — four covariate kinds (incl. static-numerical), both xreg_mode residual orderings, tuning knobs, the return_backcast requirement, the continuous-quantile head, and the dual-output unpacking.
timestamp: 2026-06-28T00:00:00Z
---

# TimesFM XReg covariates — kinds, modes, tuning, dual output

Source: `timesfm.timesfm_2p5.timesfm_2p5_base.forecast_with_covariates` +
`timesfm.utils.xreg_lib`. Requires TimesFM **2.5** and `pip install timesfm[xreg]`.
XReg fits an in-context linear model over the covariates and combines it with the
TimesFM forecast — it is *not* a separate API surface for unknown-future drivers.

## Hard preconditions

- `forecast_with_covariates()` raises `ValueError` unless the model was compiled
  with **`return_backcast=True`**. The linear fit needs the model's backcast
  (reconstruction of the input), so recompile if you forgot:

  ```python
  model.compile(timesfm.ForecastConfig(
      max_context=1024, max_horizon=256,
      normalize_inputs=True,
      use_continuous_quantile_head=True,   # see "continuous head" below
      fix_quantile_crossing=True,
      infer_is_positive=False,
      return_backcast=True,                # REQUIRED for XReg
  ))
  ```

- At least one of the four covariate dicts must be non-empty, else `ValueError`.
- Every **dynamic** covariate must span the full `context + horizon` per series.
  The horizon length is *inferred* from `len(dynamic_cov[i]) - len(inputs[i])`;
  if that exceeds `max_horizon` it raises. Static covariates are one value per
  series (no horizon span).

## The four covariate kinds

| Kind | Arg | Shape | Spans horizon? | Example |
| --- | --- | --- | --- | --- |
| dynamic numerical | `dynamic_numerical_covariates` | `{name: [seq_per_series]}` each `len = context+horizon` | yes (future known) | price, temperature, promo spend |
| dynamic categorical | `dynamic_categorical_covariates` | `{name: [seq_per_series]}` each `len = context+horizon` | yes (future known) | day-of-week, holiday flag |
| **static numerical** | `static_numerical_covariates` | `{name: [one_float_per_series]}` | no — per-series invariant | store sq-footage, latitude, base price tier, store age |
| static categorical | `static_categorical_covariates` | `{name: [one_label_per_series]}` | no — per-series invariant | region, store id, product family |

**static_numerical_covariates** is the per-series *invariant numeric* feature the
earlier skill omitted: one number per series, fed to the linear model as a
constant column. Use it for series-level scalars that never change over time
(physical size, a fixed tier, a geographic coordinate). Contrast with a *dynamic*
numerical covariate, which is a full time series. To keep inference fast, prefer
numeric (static-numerical / dynamic-numerical) over string categoricals where the
feature is genuinely numeric.

```python
point, q_xreg = model.forecast_with_covariates(
    inputs=[y1, y2, y3],                                   # list of 1-D arrays
    dynamic_numerical_covariates={                         # len == context+horizon
        "price": [price1, price2, price3],
    },
    dynamic_categorical_covariates={
        "holiday": [hol1, hol2, hol3],
    },
    static_numerical_covariates={                          # one value per series
        "sqft": [12000.0, 8400.0, 15500.0],
        "latitude": [40.7, 34.0, 41.9],
    },
    static_categorical_covariates={
        "region": ["east", "west", "midwest"],             # one label per series
    },
    xreg_mode="xreg + timesfm",
    normalize_xreg_target_per_input=True,
    ridge=0.0,
    max_rows_per_col=0,
    force_on_cpu=False,
)
```

## xreg_mode — the two residual orderings

`xreg_mode` is `"xreg + timesfm"` (default) or `"timesfm + xreg"`. They differ in
*what gets regressed* and *what gets forecast*:

- **`"xreg + timesfm"`** — fit the linear XReg model on the **targets** first,
  subtract its in-context fit, then run **TimesFM on the residual**. The covariate
  relationship is removed up front; TimesFM models whatever structure the linear
  model could not. Prefer when the covariates carry a strong, roughly-linear share
  of the signal (a clean price/promo driver) and you want TimesFM to clean up the
  rest. (Trains on the full input length, `train_len = input_len`.)

- **`"timesfm + xreg"`** — run **TimesFM first** to get a forecast, then fit the
  linear XReg model on the **residuals** of that forecast and add the XReg
  contribution back. The temporal/seasonal pattern is captured by TimesFM up
  front; XReg explains the leftover covariate effect. Prefer when the series'
  own temporal dynamics dominate and the covariates are a secondary correction.
  (Residual fit skips the first patch, so `train_len = max(0, input_len - p)`.)

Selection guidance: if the covariates *are* the story (engineered drivers with
known futures), lead with **xreg + timesfm**; if the *series shape* is the story
and covariates only nudge it, lead with **timesfm + xreg**. When unsure, backtest
both and keep the one with better held-out MAE **and** honest interval coverage.

## Tuning knobs

| Knob | Default | Effect |
| --- | --- | --- |
| `normalize_xreg_target_per_input` | `True` | z-normalises the XReg regression target per series in the batch; renormalised back on output. Leave on for mixed-scale batches; turn off only if every series already shares a scale. |
| `ridge` | `0.0` | L2 penalty on the linear model. `>0` shrinks coefficients (use when covariates are many/collinear or series are short). Also switches one-hot encoding to keep all levels (`drop=None`) instead of dropping the first. |
| `max_rows_per_col` | `0` (= no cap) | caps rows-per-column in the in-context linear solve; bound it to keep the regression well-conditioned / cheaper on very long contexts. |
| `force_on_cpu` | `False` | forces the linear model onto CPU. Set `True` if the XReg solve contends with the model on a tight GPU, or to sidestep a device-placement issue — TimesFM still runs on its own device. |

## Dual output — and the unpacking

`forecast_with_covariates()` returns a **two-element tuple**, and each element is
a **list (one entry per series)**, not the stacked `(B, H)` arrays that plain
`forecast()` returns:

```python
new_point_outputs, new_quantile_outputs = model.forecast_with_covariates(...)
# new_point_outputs[i]    -> (test_len_i,)        point forecast for series i
# new_quantile_outputs[i] -> (test_len_i, 10)     quantiles for series i
```

Both already **combine the TimesFM forecast and the XReg contribution** (the
mode-specific addition of the linear part back onto the TimesFM part). The
per-series horizon `test_len_i` is the horizon inferred from that series'
covariate length, so series can end up with different horizons in one call. Index
the quantile axis by name exactly as for plain `forecast()`:

```python
IDX_Q10, IDX_Q50, IDX_Q90 = 1, 5, 9
for i, (pt, q) in enumerate(zip(new_point_outputs, new_quantile_outputs)):
    median   = q[:, IDX_Q50]     # == pt
    lower_80 = q[:, IDX_Q10]
    upper_80 = q[:, IDX_Q90]
```

(The method's docstring loosely calls the two returns "the outputs of the model"
and "the outputs of the xreg"; in the 2.5 code both returned lists are the
*combined* point and quantile forecasts — point first, quantile second.)

## Continuous-quantile head vs discrete buckets

Compile with **`use_continuous_quantile_head=True`** to attach the optional ~30M
continuous-quantile head, which produces calibrated continuous quantiles up to a
**1k horizon** — markedly better-calibrated long-horizon bands than the default
discrete quantile buckets. The discrete path (head off) is lighter but its bands
degrade and can crook at long horizons; pair `use_continuous_quantile_head=True`
with `fix_quantile_crossing=True` so the 10 returned quantiles stay monotone. The
continuous head matters most precisely when you also use XReg over long horizons,
since that is where discrete buckets fall apart.
