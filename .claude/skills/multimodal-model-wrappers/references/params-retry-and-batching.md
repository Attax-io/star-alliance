---
type: Document
title: Typed params, decorated retry, and batch concurrency
description: Three positive reference implementations from the source — a validated SamplingParams object that replaces the fat constructor, the dalle3 @backoff+re-raise retry, and the run_concurrent_batched vs run_batched contrast.
timestamp: 2026-06-28T00:00:00Z
---

# Typed params, decorated retry, and batch concurrency

`base-contracts.md` names three weaknesses in the source — the kitchen-sink `BaseLLM.__init__`,
the swallow-on-exhaustion retry loop, and a `run_many` that prints instead of returning. This
reference points at the parts of the *same* repo that already do each of those right, so you
copy the good version instead of inheriting the bad one.

## 1. Typed params object (`SamplingParams`) — the positive form of the fat constructor

`BaseLLM.__init__` hoists ~25 generation knobs into one signature, most ignored by any given
provider, with a real `frequency_penalty`/`freq_penalty` overwrite bug. The cure is in the
same package: `sampling_params.py::SamplingParams` collects the generation knobs into **one
validated value object** instead of smearing them across a constructor:

```python
class SamplingParams:
    def __init__(self, n=1, temperature=1.0, top_p=1.0, top_k=-1,
                 max_tokens=16, logprobs=None, prompt_logprobs=None,
                 presence_penalty=0.0, frequency_penalty=0.0,
                 use_beam_search=False, stop=None, ...):
        ...
        self._verify_args()                 # raises on out-of-range values
        if self.use_beam_search:
            self._verify_beam_search()
        else:
            self._verify_non_beam_search()
```

Why this beats the fat constructor:

- **One param bag, passed by value.** `run(task, params: SamplingParams)` (or
  `SamplingParams` as a single constructor arg) replaces 25 positional kwargs. A provider
  reads the fields it supports and ignores the rest — but the *caller's* call site stays one
  argument wide.
- **Validation at construction, not at the API 400.** `_verify_args` enforces the ranges the
  provider would otherwise reject (`top_p in (0,1]`, `presence_penalty in [-2,2]`,
  `temperature >= 0`, `logprobs >= 0`). Bad params fail loudly where they were set, not deep
  in the SDK.
- **Mode coherence.** `use_beam_search` flips a whole validation regime
  (`_verify_beam_search` vs `_verify_non_beam_search`) and a derived `sampling_type`
  (`GREEDY` / `RANDOM` / `BEAM` via `@cached_property`). The object keeps interdependent knobs
  consistent; 25 loose constructor args cannot.
- **`logprobs` / `prompt_logprobs` are first-class.** The fat constructor never modeled
  log-probability output. The typed object carries `logprobs` (per-output-token) and
  `prompt_logprobs` (per-prompt-token), so a wrapper that needs confidence scores has a
  field to request them through instead of a raw kwarg.

**Rule.** Generation knobs belong in a validated params object the caller constructs once and
hands in, not in the wrapper's constructor. The object validates itself, keeps mode-dependent
fields coherent, and gives advanced outputs (`logprobs`) a typed home. This is the concrete
"typed params object" the base-contracts caveat points to.

## 2. Decorated-retry reference impl (`dalle3`) — backoff + re-raise, never silent `None`

`BaseMultiModalModel.run_with_retries` loops a fixed count, prints, and returns `None` on
exhaustion — the failure vanishes. `OpenAIFunctionCaller.run` does the same (catch-all →
`return None`). The reference *positive* impl is `dalle3.py`:

```python
@backoff.on_exception(backoff.expo, Exception, max_time=max_time_seconds)
def __call__(self, task: str):
    if task in self.cache:                  # TTLCache short-circuit
        return self.cache[task]
    try:
        response = self.client.images.generate(model=self.model, prompt=task, ...)
        img_path = self._download_and_save(response.data[0].url)
        self.cache[task] = img_path
        return img_path
    except openai.OpenAIError as error:
        print(colored(f"Error running Dalle3: {error} ...", "red"))
        raise error                         # log loudly, then RE-RAISE
```

What makes it the model to copy:

- **Backoff is a decorator, not a hand-rolled loop.** `@backoff.on_exception(backoff.expo,
  Exception, max_time=...)` gives exponential backoff with a wall-clock ceiling, declaratively.
  No `for i in range(self.retries): try/except/continue` to get subtly wrong.
- **It re-raises on the terminal failure.** The caller learns the call failed and decides what
  to do — the opposite of returning `None` or `"Error running model."`. This is the single
  error contract the skill mandates: retry → log loudly → re-raise.
- **Idempotent short-circuit via `TTLCache`.** A repeated prompt within the TTL returns the
  cached path without a second API hit — retry-safe and cost-safe.

Adopt the decorator + re-raise shape for *every* provider, including the structured-output and
TTS paths, so the error contract is uniform across the abstraction.

## 3. TTV batching contrast — `run_concurrent_batched` vs `run_batched`

`base_ttv.py` ships two batch methods, and the difference is the whole point of putting
fan-out in the base class:

```python
def run_batched(self, tasks=None, imgs=None, *a, **k):
    # serial: one run() after another
    return [self.run(t, i, *a, **k) for t, i in zip(tasks, imgs)]

def run_concurrent_batched(self, tasks=None, imgs=None, *a, **k):
    with ThreadPoolExecutor(max_workers=4) as executor:
        loop = asyncio.get_event_loop()
        futs = [loop.run_in_executor(executor, self.run, t, i, *a, **k)
                for t, i in zip(tasks, imgs)]
        return loop.run_until_complete(asyncio.gather(*futs))
```

Both validate `len(tasks) == len(imgs)` and **return** their results (unlike the
`run_many`-prints anti-pattern). The contrast is the rationale:

- **`run_batched` is serial** — a plain list comprehension over `run`. Use it when the
  provider is a local GPU model where concurrency just thrashes one device, when ordering and
  back-pressure matter, or for trivially small batches where a thread pool's overhead isn't
  worth it. Latency is the sum of the calls.
- **`run_concurrent_batched` overlaps the calls** — it offloads each blocking `run` to a
  `ThreadPoolExecutor` via `loop.run_in_executor` and `asyncio.gather`s them. Use it when
  `run` is **I/O-bound** (a remote diffusion API, an HTTP video endpoint): the wall-clock
  collapses toward the slowest single call instead of their sum. The `max_workers=4` cap is
  the politeness knob — it bounds concurrent provider load so you don't trip rate limits
  (mirror the provider's concurrency ceiling here).

**Rule.** Offer both and let the caller choose by workload: serial for device-bound or
order-sensitive runs, concurrent for I/O-bound remote calls. Bounding the pool
(`max_workers`) is mandatory — unbounded `gather` over a rate-limited provider is a
self-inflicted 429. This is the batch-side expression of "put cross-cutting machinery in the
base": both variants are written once against the abstract `run` and inherited by every TTV
provider.
