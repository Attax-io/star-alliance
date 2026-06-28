---
type: Document
title: Foundation model vs classical forecasting
description: When to use TimesFM zero-shot vs ARIMA/ETS/Prophet, and how to settle it empirically.
timestamp: 2026-06-28T00:00:00Z
---

# Foundation model vs classical forecasting

The first decision in any forecasting task is *which kind of model*. TimesFM is a
strong default, not a universal winner. Choose deliberately.

## What a foundation model is

TimesFM is a decoder-only transformer pretrained by Google Research on a large
corpus of time series (paper: "A decoder-only foundation model for time-series
forecasting", ICML 2024). It forecasts **zero-shot**: you feed one univariate
series and it returns a forecast *without training on that series*. The pattern
recognition that ARIMA/ETS learn by fitting coefficients to *your* data, TimesFM
brings pre-learned from the corpus.

## What zero-shot buys you

- **No fitting, no maintenance.** One compiled model serves every series. No
  per-series order selection, no seasonality specification, no refit-on-drift.
- **Scale.** A single `forecast()` call batch-forecasts hundreds/thousands of
  series of *different lengths* at once.
- **Cold start.** Works on a brand-new series with no history to fit on (down to
  a handful of points, though more context = better).
- **Calibrated uncertainty out of the box** via the quantile head — you get
  prediction intervals without bootstrapping residuals.

## What it costs you

- **No interpretability.** You cannot read "the AR(1) coefficient" or "the
  holiday effect is +12%". If the question is *why*, classical wins.
- **No native multivariate / causality.** No VAR, no Granger causality. Exogenous
  drivers come only through XReg covariates, and only if their future is known.
- **A black box you must validate.** Pretraining bias may or may not match your
  domain. The only honest answer to "is it better here?" is a backtest.
- **It is univariate per call** — the target is one series; covariates assist but
  the model forecasts one target at a time.

## Decision guide

| Situation | Prefer |
| --- | --- |
| Hundreds of series, no time to tune each | **TimesFM** (one model, batch) |
| Brand-new series, little/no history to fit | **TimesFM** (zero-shot) |
| Need interpretable coefficients / effect sizes | Classical (ARIMA/ETS, Prophet) |
| Strong known-future driver (holiday, planned promo, scheduled price) | TimesFM **+ XReg** or regression-with-ARIMA-errors |
| Multivariate dynamics / lead-lag / causality | VAR / `statsmodels` (not TimesFM) |
| One series, explicit seasonality you want to declare | Prophet / ETS |
| Classification / clustering of series | not forecasting — `aeon`, `scikit-learn` |
| Tabular, non-temporal | `scikit-learn` (not a forecaster) |

## Settle it empirically — never by reputation

Reputation ("foundation models are SOTA") does not tell you whether TimesFM beats
a 3-line ETS on *your* series. Run a **rolling-origin backtest** (see
`evaluation-and-pitfalls.md`): hold out the last H points, forecast, score; roll
the origin back several windows; compare TimesFM against at least one cheap
classical baseline (seasonal-naive is the honest floor — if you cannot beat
"repeat last season", stop). Report both point error and interval coverage. Pick
the model that wins on *your* metric for *your* horizon, and re-check on drift.

## Hybrid stance

The two are not exclusive. A common pattern: TimesFM for the bulk of a large
series panel where tuning each is infeasible, and a hand-built classical model on
the few high-value series that justify the attention. Or TimesFM as the baseline
that any bespoke model must beat before it ships.
