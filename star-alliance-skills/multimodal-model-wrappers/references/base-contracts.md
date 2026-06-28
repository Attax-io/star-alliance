---
type: Document
title: Base contracts
description: Per-modality base classes, their abstract verbs, and the shared async/batch/retry/metrics machinery.
timestamp: 2026-06-28T00:00:00Z
---

# Base contracts — one verb per modality

Source: `swarm_models/base_llm.py`, `base_multimodal_model.py`, `base_tts.py`, `base_ttv.py`,
`embeddings_base.py`.

Each base class fixes a **single abstract entry point** and provides shared machinery around
it. A provider subclass implements only its own API call; everything else is inherited.

## The shape: abstract `run`, concrete `__call__`

`BaseLLM` and `BaseMultiModalModel` declare `run` with `@abstractmethod` and make `__call__`
delegate to it:

```python
@abstractmethod
def run(self, task: Optional[str] = None, *args, **kwargs) -> str:
    """generate text using language model"""

def __call__(self, task: str) -> str:
    return self.run(task)
```

So `model(task)` and `model.run(task)` are always the same path. Callers learn one verb; you
implement one method. **Never override `__call__` to do real work — it exists only to forward.**

## Base class by modality

| Base | Abstract verb | Signature | Promised return | Notes |
|------|---------------|-----------|-----------------|-------|
| `BaseLLM` | `run` | `run(task)` | `str` | + `arun`, `batch_run`, `abatch_run`, `chat(task, history)`, metrics, history, ~25 `set_*` knobs |
| `BaseMultiModalModel` | `run` | `run(task, img=None)` | provider-defined (usually `str`) | + `run_many`, `run_batch`, `run_batch_async`, `run_with_retries`, image helpers, chat history |
| `BaseTTSModel(BaseLLM)` | `run` | `run(task)` | audio `bytes` | + `save`, `load`, `save_to_file(speech_data, filename)` writing a WAV |
| `BaseTextToVideo(BaseLLM)` | `run` | `run(task, img=None)` | video file path | + `save_video_path`, `run_batched`, `run_concurrent_batched`, `arun` |
| `Embeddings(ABC)` | `embed_documents`, `embed_query` | `(texts)` / `(text)` | `List[List[float]]` / `List[float]` | async variants `aembed_*` default to `NotImplementedError` |

Key reading: **TTS and TTV subclass `BaseLLM`** to inherit its scaffolding even though their
outputs are bytes/paths, not text. That is the pattern — reuse the base for its machinery, then
let the subclass's `run` return the modality-appropriate payload. Embeddings, whose call shape
genuinely differs (two verbs, not one), get their own `ABC` rather than being bent to fit.

## Shared machinery lives in the base (write it once)

Implemented in the base against the abstract `run`, inherited by every provider:

- **Async** — `arun` wraps the sync `run` in `loop.run_in_executor(None, self.run, task)`.
  `abatch_run` is `asyncio.gather(*(self.arun(t) for t in tasks))`.
- **Batch / fan-out** — `batch_run` (serial list comp), `run_many` / `run_batch`
  (`ThreadPoolExecutor(max_workers=self.max_workers)`), `run_batch_async`
  (`run_in_executor` per task), `run_concurrent_batched` (TTV).
- **Retries** — `run_with_retries` loops `self.retries`, catches `Exception`, prints, continues;
  `run_batch_with_retries` wraps the batch. (See caveat below.)
- **Metrics / timing** — `start_time`/`end_time`, `_tokens_per_second`, `generation_latency`,
  `throughput`, `time_to_first_token`, `get_generation_time`.
- **State** — `chat_history` / `history`, `clear_history`, `unique_chat_history`, plus
  `set_temperature`, `set_max_tokens`, `set_top_k/top_p`, `set_device`, etc.

The payoff: a provider that implements one method gets async + batch + retry + metrics for
free, and a fix to any of those lands in every provider at once.

## Caveats observed in the source (do better than the original)

- **`BaseLLM.__init__` is a kitchen-sink constructor** — ~25 generation params (`top_k`,
  `beam_width`, `num_beams`, `length_penalty`, `pad_token_id`…) hoisted into one signature,
  most ignored by any given provider. It also has a real bug: `self.frequency_penalty` is set
  from `frequency_penalty` and then **overwritten** by `freq_penalty`. Lesson: prefer a typed
  params object (see `sampling_params.py`) or `**kwargs` passthrough over a fat constructor
  that every provider half-ignores.
- **`run_with_retries` swallows on exhaustion** — after the loop it returns `None` with no
  raise. A bare-count retry that prints-and-continues hides the final failure. Pair retries
  with a final re-raise (the `dalle3` `@backoff` + re-raise pattern is the better model).
- **`run_many` prints instead of returning** — it maps over the executor but only prints
  results; a real fan-out should collect and return them. Return data; let the caller print.
