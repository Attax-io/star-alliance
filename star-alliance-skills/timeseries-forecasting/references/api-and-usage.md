---
type: Document
title: TimesFM API, config, data prep, and sizing
description: Model lifecycle, every ForecastConfig flag, output shapes, covariates (XReg), data prep, and hardware sizing for TimesFM 2.5.
timestamp: 2026-06-28T00:00:00Z
---

# TimesFM API, config, data prep, and sizing

Source: TimesFM 2.5 (`google/timesfm-2.5-200m-pytorch`). Default to 2.5.

## Three-step lifecycle

```python
import torch, numpy as np, timesfm
torch.set_float32_matmul_precision("high")          # set on Ampere+ GPUs / always safe

# 1. load (downloads ~800 MB weights to ~/.cache/huggingface on first use)
model = timesfm.TimesFM_2p5_200M_torch.from_pretrained("google/timesfm-2.5-200m-pytorch")

# 2. compile with a ForecastConfig — REQUIRED before forecast(), or RuntimeError
model.compile(timesfm.ForecastConfig(
    max_context=1024, max_horizon=256,
    normalize_inputs=True,
    use_continuous_quantile_head=True,
    fix_quantile_crossing=True,
    infer_is_positive=True,
    per_core_batch_size=32,
))

# 3. forecast — inputs is a LIST of 1-D arrays (one per series), not a 2-D matrix
point, quantiles = model.forecast(horizon=24, inputs=[series_a, series_b])
```

`from_pretrained()` returns an *uncompiled* model. `compile()` must run first.
`forecast(horizon=M)` accepts any `M ≤ max_horizon`.

## ForecastConfig — every flag

| Flag | Default | Set to | Why |
| --- | --- | --- | --- |
| `max_context` | 0 (= model max, 16384) | longest window you need, or 512–2048 | more context = slower; match to data, not "more is better" |
| `max_horizon` | 0 (= model max) | your expected max forecast length | ceiling for any `forecast(horizon=...)` |
| `normalize_inputs` | False | **True** | z-norm each series; prevents scale instability |
| `use_continuous_quantile_head` | False | **True** | 30M head → calibrated intervals, esp. long horizon |
| `fix_quantile_crossing` | False | **True** | guarantees q10 ≤ q20 ≤ … ≤ q90 |
| `infer_is_positive` | True | **False for negatives** | clamps forecast ≥ 0; wrong for returns/temp/PnL/spreads |
| `force_flip_invariance` | True | leave True | enforces f(−x) = −f(x) |
| `per_core_batch_size` | 1 | tune to memory | throughput vs OOM |
| `return_backcast` | False | True for covariate diagnostics | reconstruction of input |

The config is a frozen dataclass; quantiles default to
`[0.1,0.2,…,0.9]`, `decode_index=5` (the median).

## Output shapes — and the off-by-one

`forecast()` returns `(point_forecast, quantile_forecast)`:

- `point_forecast`: `(B, H)` — the **median** (q50).
- `quantile_forecast`: `(B, H, 10)` — slice 0 = **mean**, 1 = q10, 2 = q20, …,
  5 = q50, …, 9 = q90.

`quantile_forecast[..., 0]` is the **mean, not q0**. Always define
`IDX_Q10, IDX_Q50, IDX_Q90 = 1, 5, 9` and index by name.

```python
lower_80 = quantiles[:, :, 1]   # q10
median   = quantiles[:, :, 5]   # q50 (== point_forecast)
upper_80 = quantiles[:, :, 9]   # q90
```

## Data prep

Input = **list of 1-D numpy arrays** (`np.float32`), one per series. Series may
have different lengths in the same batch; `horizon` is shared across the batch
(different horizons → separate calls).

NaN handling: leading NaNs are stripped, internal NaNs linearly interpolated,
but **trailing NaNs are NOT handled** — drop them yourself. Replace `inf` with
`nan` so it interpolates. Drop series with `std < 1e-10` (constant → flat/NaN
forecast). Practical minimum context ≈ 32 points for a meaningful forecast.

```python
def clean(arr):
    arr = np.asarray(arr, np.float32)
    while len(arr) and np.isnan(arr[-1]):   # strip trailing NaN
        arr = arr[:-1]
    arr[np.isinf(arr)] = np.nan             # inf -> interpolated
    return arr
```

Context length by frequency (provide ≥ 3–5 cycles of the dominant pattern):

| Context | Use |
| --- | --- |
| 64–256 | prototyping |
| 256–512 | daily, ~1 yr |
| 512–1024 | daily, ~2–3 yr (standard) |
| 1024–4096 | hourly with weekly pattern |
| 4096–16384 | high-frequency / long memory (2.5 max) |

## Covariates (XReg) — requires TimesFM 2.5 + `pip install timesfm[xreg]`

```python
point, q = model.forecast_with_covariates(
    inputs=[y1, y2],
    dynamic_numerical_covariates={"price": [p1, p2]},      # known over context+horizon
    dynamic_categorical_covariates={"holiday": [h1, h2]},
    static_categorical_covariates={"region": ["east", "west"]},  # one label per series
    xreg_mode="xreg + timesfm",   # or "timesfm + xreg"
)
```

Three covariate kinds: **dynamic-numerical** (price, temperature, promo spend),
**dynamic-categorical** (day-of-week, holiday flag), **static-categorical**
(region, store/product id). Every *dynamic* covariate must span the **full
`context + horizon`** length per series — so it only helps when its future is
known. `xreg_mode` orders whether covariate regression runs before or after the
TimesFM forecast. `forecast_with_covariates()` does not exist on TimesFM 1.0.

## Hardware sizing

| Model | Params | RAM (CPU) | VRAM | Disk | Context |
| --- | --- | --- | --- | --- | --- |
| **2.5** (default) | 200M | ~1.5 GB / ≥4 GB | ~1 GB / ≥2 GB | ~800 MB | 16384 |
| 2.0 (archived) | 500M | ≥16 GB | ≥8 GB | ~2 GB | 2048 |
| 1.0 (archived) | 200M | ≥8 GB | ≥4 GB | ~800 MB | 2048 |

Batch RAM estimate: `GB ≈ 0.8 + 0.5 + 0.0002 × num_series × context_length`.
If a batch will not fit, **chunk** it rather than OOM:

```python
CHUNK = 100
for i in range(0, len(inputs), CHUNK):
    p, q = model.forecast(horizon=H, inputs=inputs[i:i+CHUNK])
```

Batch-size rough guide: CPU 8 GB → 8; CPU 16 GB → 32; GPU 8 GB → 64; GPU 16 GB →
128. On OOM, lower `per_core_batch_size` first, then `max_context`.

## Model variants

| Version | Params | Context | Status | Checkpoint | Note |
| --- | --- | --- | --- | --- | --- |
| 2.5 | 200M | 16384 | latest | `google/timesfm-2.5-200m-pytorch` | no `freq` flag |
| 2.0 | 500M | 2048 | archived | `google/timesfm-2.0-500m-pytorch` | `freq=[0]` for monthly |
| 1.0 | 200M | 2048 | archived | `google/timesfm-1.0-200m-pytorch` | `freq=[0]` for monthly; no covariates |

Backends: `_torch`, `_flax` (JAX, faster on TPU/GPU), `_transformers`.
