---
type: Document
title: TimesFM backends (Torch / Flax / Transformers) and LoRA fine-tuning
description: The three TimesFM 2.5 backends with install + load paths and the torch_compile flag, plus a LoRA/PEFT fine-tuning reference (random-window dataset, training and eval loop).
timestamp: 2026-06-28T00:00:00Z
---

# TimesFM backends and LoRA fine-tuning

Source: `timesfm/__init__.py`, `timesfm_2p5/timesfm_2p5_torch.py`,
`timesfm_2p5/timesfm_2p5_flax.py`, and
`timesfm-forecasting/examples/finetuning/finetune_lora.py`. TimesFM 2.5 only.

## Three backends, one forecast API

The same `compile()` / `forecast()` / `forecast_with_covariates()` surface is
exposed by three backends. Pick by accelerator and workflow:

| Backend | Class | Checkpoint | Install | Use |
| --- | --- | --- | --- | --- |
| Torch (default) | `timesfm.TimesFM_2p5_200M_torch` | `google/timesfm-2.5-200m-pytorch` | `pip install timesfm[torch]` | CPU + CUDA; the default everywhere in this skill |
| **Flax (JAX)** | `timesfm.TimesFM_2p5_200M_flax` | `google/timesfm-2.5-200m-flax` | `pip install timesfm[flax]` | **faster inference on TPU and GPU** (JAX/`nnx`) |
| Transformers | `transformers.TimesFm2_5ModelForPrediction` | `google/timesfm-2.5-200m-transformers` | `pip install transformers` | the HuggingFace path used for fine-tuning (LoRA below) |

The framing knobs (context, horizon, quantiles, sign domain, covariates) are
identical across Torch and Flax — switching backend is a speed/hardware choice,
not a behavior change.

### Flax / JAX path

```python
import timesfm

model = timesfm.TimesFM_2p5_200M_flax.from_pretrained(
    "google/timesfm-2.5-200m-flax"
)
model.compile(timesfm.ForecastConfig(
    max_context=1024, max_horizon=256,
    normalize_inputs=True,
    use_continuous_quantile_head=True,
    fix_quantile_crossing=True,
    infer_is_positive=False,
))
point, q = model.forecast(horizon=24, inputs=[series_a, series_b])
```

Install a JAX build matching your accelerator (CPU / CUDA GPU / TPU) per the JAX
install docs; Flax is the path to reach for when TimesFM inference is the
bottleneck on a TPU or GPU.

### `torch_compile=False` (Torch backend only)

The Torch backend wraps the model in `torch.compile` by default. The flag is a
**constructor argument**, so pass it through `from_pretrained`:

```python
model = timesfm.TimesFM_2p5_200M_torch.from_pretrained(
    "google/timesfm-2.5-200m-pytorch",
    torch_compile=False,        # default is True
)
```

Set `torch_compile=False` when the one-time compile cost outweighs the runtime
win (short-lived processes, many tiny ad-hoc forecasts), when running on a device
where `torch.compile` is flaky, or to remove a confound while debugging. It has
no effect on the Flax backend.

## LoRA / PEFT fine-tuning

Reach for fine-tuning **only after a rolling backtest shows zero-shot genuinely
underfits your domain** — it is the last resort, not a default. LoRA
(parameter-efficient) trains a small adapter (a few MB) on the frozen base model
via the HuggingFace Transformers checkpoint + the `peft` library. Reference
script: `timesfm-forecasting/examples/finetuning/finetune_lora.py` (retail demand,
weekly store sales, forecasting the next 13 weeks).

```
pip install transformers accelerate peft pandas pyarrow scikit-learn
python finetune_lora.py \
    --model_id google/timesfm-2.5-200m-transformers \
    --context_len 64 --horizon_len 13 \
    --epochs 10 --batch_size 32 --lr 1e-4 \
    --lora_r 4 --lora_alpha 8 --lora_dropout 0.05 \
    --num_samples 5000
```

`--context_len` must be a multiple of 32 (clamped to the model's max context).

### The pre-sampled random-window dataset (the load-bearing detail)

Training windows are **pre-sampled random (series, start-point) slices**, each a
**full `context_len` context with no zero-padding**. Zero-padding a short context
would corrupt TimesFM's internal RevIN instance-normalisation statistics — so the
dataset only keeps series with `len >= context_len + horizon_len` and draws a
random valid start per sample. No external normalisation is applied; TimesFM
normalises internally and the loss is computed in the original data scale.

```python
class TimeSeriesRandomWindowDataset(Dataset):
    def __init__(self, series_list, context_len, horizon_len, num_samples=5000, seed=42):
        rng = np.random.default_rng(seed)
        min_len = context_len + horizon_len
        valid = [i for i, s in enumerate(series_list) if len(s) >= min_len]
        self.samples = []
        for _ in range(num_samples):
            idx = rng.choice(valid)
            max_start = len(series_list[idx]) - min_len
            self.samples.append((idx, rng.integers(0, max_start + 1)))
    def __getitem__(self, i):
        idx, start = self.samples[i]
        s = self.series_list[idx]
        context = torch.tensor(s[start:start+self.context_len], dtype=torch.float32)
        target  = torch.tensor(s[start+self.context_len:start+self.context_len+self.horizon_len],
                               dtype=torch.float32)
        return context, target
```

Validation uses each series' **last** window (`TimeSeriesLastWindowDataset`), so
the held-out comparison is the most-recent quarter per series.

### Apply LoRA + train

```python
from peft import LoraConfig, get_peft_model
from transformers import TimesFm2_5ModelForPrediction

model = TimesFm2_5ModelForPrediction.from_pretrained(
    "google/timesfm-2.5-200m-transformers",
    torch_dtype=torch.bfloat16, device_map=device,
)
model = get_peft_model(model, LoraConfig(
    r=4, lora_alpha=8, target_modules="all-linear",
    lora_dropout=0.05, bias="none",
))

optimizer = torch.optim.AdamW(model.parameters(), lr=1e-4, weight_decay=0.01)
scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs*len(train_loader))

for context, target_vals in train_loader:
    out = model(past_values=context, future_values=target_vals,
                forecast_context_len=context_len)
    out.loss.backward()
    torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
    optimizer.step(); optimizer.zero_grad(); scheduler.step()
```

The training signal is `outputs.loss` from passing both `past_values` and
`future_values`; grads are clipped to norm 1.0 and the LR is cosine-annealed.
Save with `model.save_pretrained(output_dir)` whenever validation loss improves —
that writes only the **adapter**, not the full base weights.

### Evaluate zero-shot vs fine-tuned (keep the winner)

Load the base model, wrap it with the saved adapter via
`PeftModel.from_pretrained(base_model, adapter_dir)`, and compare held-out MAE per
series — forecasts come from `out.mean_predictions[0, :horizon_len]`. Keep the
LoRA adapter **only if it beats zero-shot on held-out MAE**; otherwise stay
zero-shot. Fine-tuning that does not win the backtest is a liability (extra
weights, drift risk) for no gain.
