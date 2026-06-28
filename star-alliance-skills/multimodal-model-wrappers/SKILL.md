---
name: multimodal-model-wrappers
type: Skill
metadata:
  version: 1.0.0
description: "Craft for building a unified, multi-provider model abstraction — one stable call surface (run / __call__) over many LLM, vision-language (VLM), TTS, text-to-video, image-gen, and embedding providers. Use when you need to wrap a new model provider behind a shared interface, unify several model APIs (OpenAI, Anthropic, Together, Ollama, HuggingFace) under one class hierarchy, add a provider to an existing abstraction, normalize inputs and outputs across modalities, or design retry, batch, and async behavior in the base class. Differs from arsenal-forge (that wires a runner into the Star Alliance arsenal/registry, not designing the provider abstraction itself) and from mcp-builder (that exposes tools over the MCP protocol, not a Python model class hierarchy). Distilled from the swarm-models repo."
---

# Multimodal Model Wrappers

The craft of putting **one stable call surface over many model providers and modalities**.
A caller writes `model.run(task)` or `model(task)` and does not care whether the model is
OpenAI chat, an Anthropic call routed through aisuite, a local HuggingFace VLM, a DALL·E-3
image generator, an OpenAI TTS endpoint, or a text-to-video diffusion model. The wrapper
absorbs the differences; the caller keeps one mental model.

Distilled from `swarm-models` (`base_llm.py`, `base_multimodal_model.py`, `base_tts.py`,
`base_ttv.py`, `embeddings_base.py`, `model_types.py`, and concrete wrappers like `dalle3.py`,
`openai_tts.py`, `lite_llm_model.py`, `fuyu.py`).

## What it is

- A **base-class contract per modality** (text LLM, vision-language, TTS, text-to-video,
  embeddings) that fixes the call shape — `run` / `__call__` — and provides the shared
  machinery (async, batch, retries, metrics) once, so each provider subclass writes only its
  own API call.
- A discipline for **normalizing inputs and outputs** so heterogeneous provider SDKs present
  the same shape to callers: a task string in, a typed result out.
- A set of judgment calls about **when a unified wrapper earns its keep** versus when it
  becomes a lossy lowest-common-denominator that hides the very features you wanted.

## What it is not

- **Not arsenal-forge.** Arsenal-forge registers a finished runner into the Star Alliance
  arsenal/registry (`models.json`, dashboard wiring). This skill is about *designing the
  provider abstraction* — the class hierarchy and contract — that a runner sits behind.
- **Not mcp-builder.** mcp-builder exposes capabilities over the MCP wire protocol to an
  agent host. This is an in-process Python class hierarchy callers import and instantiate.
- **Not a model zoo or a router.** Routing/selection (`model_router.py`) is a *consumer* of
  these wrappers; the wrappers themselves are dumb, single-provider adapters.
- **Not a place to leak provider quirks.** If `gpt-4o` and `claude` need different message
  shaping, that lives *inside* each subclass, never in the caller.

## Principles

### 1. The base class fixes the verb; the subclass fills the call.
Every modality base declares one abstract entry point and implements everything reusable
around it. In `BaseLLM` and `BaseMultiModalModel` that verb is `run(...)` (abstract), with
`__call__` delegating to it so `model(task)` and `model.run(task)` are identical. A new
provider overrides only `run`; it inherits `arun`, `batch_run`, `chat`, metrics, history, and
setters for free. **Define the contract once as the narrowest thing every provider must do
(produce a result from a task), and hang the shared scaffolding off it.**

### 2. One verb, modality-shaped signature.
The call surface stays `run` across modalities, but its *arguments* match the modality:
`BaseLLM.run(task)`; `BaseMultiModalModel.run(task, img=None)`; TTS `run(task) -> bytes`;
text-to-video `run(task, img=None) -> video_path`; embeddings split into `embed_documents`
and `embed_query`. **Keep the verb constant so callers recognize it everywhere; vary the
signature only as the modality genuinely demands** (an image input, an audio-bytes output, a
file path). Resist adding a brand-new method name when an extra optional arg would do.

### 3. Normalize at the edges — provider SDK shape stays inside the subclass.
Each provider speaks its own dialect: OpenAI/Together/aisuite return
`response.choices[0].message.content`; litellm wraps the same; DALL·E returns a URL you must
download; HuggingFace VLMs return decoded token tensors. The subclass's job is to **convert
that dialect into the contract's promised return** — a plain string for LLMs, audio bytes for
TTS, a saved file path for image/video. Inbound, do the same: `_prepare_messages` turns a bare
task + optional system prompt into the `messages` list; `encode_img` / `get_img_from_web` turn
a path or URL into base64 or a PIL image. **The caller hands you the simplest possible input
and receives the simplest possible output; all marshalling is hidden.**

### 4. Put cross-cutting machinery in the base, not in every provider.
Async (`arun` via `run_in_executor`), batching (`batch_run`, `run_batch`, `run_concurrently`,
`run_many` over a `ThreadPoolExecutor`), retries (`run_with_retries` looping `self.retries`),
metrics/timing, and history all live in the base class and call down to the one `run` each
subclass implements. **Write fan-out, async, and retry once against the abstract verb** so
every provider gains them the day it subclasses — and so a bug fix lands everywhere at once.

### 5. Make failure visible and bounded; never swallow silently.
Concrete wrappers show a spectrum: `dalle3` uses `@backoff.on_exception(expo, max_time=...)`
plus a typed-and-logged re-raise; `BaseMultiModalModel.run_with_retries` loops a fixed count;
`TogetherLLM` logs and returns a sentinel string. The right default is **retry with backoff,
log loudly, then re-raise** so the caller can decide — returning `"Error running model."` as a
normal value is a trap that hides failures downstream (guild doctrine: log errors loudly,
never silently swallow). Pick one error contract for the abstraction and hold every provider
to it; don't let each subclass invent its own.

### 6. Type the modality envelope so multimodal data is self-describing.
`model_types.py` defines pydantic `TextModality`, `ImageModality` (url + alt_text),
`AudioModality`, `VideoModality`, and a `MultimodalData` container. **A typed envelope per
modality lets one interface carry mixed media without positional-argument soup** and gives
validation, defaults, and serialization for free. Reach for it the moment a call needs more
than "a string and maybe one image."

### 7. A unified wrapper helps until it costs more than it saves.
It *helps* when callers swap providers often, when you fan out the same task across models,
and when the shared machinery (retries/async/batch) is the real value. It *hurts* when it
becomes a lossy lowest common denominator — flattening streaming, tool-calls, vision detail,
or provider-specific knobs into a string-in/string-out box. Note the `sampling_params` /
per-provider kwarg sprawl in `BaseLLM.__init__`: every provider's params got hoisted into one
giant constructor, much of it ignored per provider. **Wrap to stabilize the 80% common path;
expose an escape hatch (`*args, **kwargs` passthrough to the native client, or direct access
to the underlying SDK object) for the 20% that needs the raw provider.** When a modality can't
honor the shared contract without lying, give it its own base rather than forcing it.

## References

- `references/base-contracts.md` — the per-modality base classes, their abstract verbs,
  shared machinery (async/batch/retry/metrics), and the `run` ↔ `__call__` delegation.
- `references/adding-a-provider.md` — the checklist for wrapping a new provider: subclass the
  right base, implement `run`, normalize in/out, register in `__init__.py`, choose the error
  contract; worked examples (LLM, TTS, image-gen, local VLM).
- `references/modality-normalization.md` — input/output normalization patterns per modality,
  the typed `MultimodalData` envelope, and the escape-hatch rule for provider-specific power.
