---
type: Document
title: Adding a provider
description: Checklist and worked examples for wrapping a new model provider behind the shared base-class contract.
timestamp: 2026-06-28T00:00:00Z
---

# Adding a provider

The repeatable move: pick the base whose contract matches the modality, implement only `run`,
normalize at the edges, register the class, and choose one error contract. Everything else is
inherited.

## Checklist

1. **Pick the base by modality, not by provider.**
   - Text chat/completion → `BaseLLM` (return `str`).
   - Image-in, text-out (VLM) → `BaseMultiModalModel` (signature `run(task, img=None)`).
   - Text-to-speech → `BaseTTSModel` (return audio `bytes`).
   - Text-to-video → `BaseTextToVideo` (return video file path).
   - Embeddings → implement the `Embeddings` ABC (`embed_documents` + `embed_query`).
   - Image generation → its own small class is fine (see `dalle3.py`); it does not fit the
     text bases cleanly, so don't force it.

2. **Construct the native client in `__init__`.** Read keys from env with a sensible default
   (`os.getenv("OPENAI_API_KEY")`), store config, build the SDK client. Call
   `super().__init__(...)` so base state (history, retries, max_workers) exists. Validate
   required keys early and raise — don't defer to first call.

3. **Implement `run` and nothing else.** Inside `run`: marshal the input → call the native
   SDK → marshal the output back to the contract's promised return. Keep all provider dialect
   here.

4. **Normalize input.** Bare task + optional system prompt → the SDK's expected shape. For
   chat SDKs that is a `messages` list (factor it into `_prepare_messages`). For local VLMs it
   is a processor call over text + PIL image.

5. **Normalize output.** Convert the SDK response to the promised type: chat →
   `response.choices[0].message.content`; image-gen → download the URL, save, return the path;
   TTS → accumulate streamed bytes; HF generate → `processor.batch_decode(...)`.

6. **Choose the error contract (pick one, hold every provider to it).** Default:
   retry-with-backoff, log loudly, re-raise. Avoid the `TogetherLLM` anti-pattern of returning
   `"Error running model."` as a normal value — it hides failures from the caller.

7. **Register the class** in `swarm_models/__init__.py` (import + add to `__all__`) so it is
   importable as `from swarm_models import YourModel`. This is also where you keep heavy/
   optional deps commented out so the package imports without every backend installed.

8. **Provide an escape hatch.** Pass `*args, **kwargs` through to the native client so a caller
   can reach provider-specific knobs without you enumerating them. Optionally expose the raw
   `self.client`.

## Worked examples (all from the source)

**LLM via litellm (`LiteLLM`).** Construct nothing heavy; `run` builds messages and calls
`completion(...)`, then returns `response.choices[0].message.content`:

```python
def _prepare_messages(self, task):
    messages = []
    if self.system_prompt:
        messages.append({"role": "system", "content": self.system_prompt})
    messages.append({"role": "user", "content": task})
    return messages

def run(self, task, *args, **kwargs):
    response = completion(model=self.model_name, messages=self._prepare_messages(task),
                          stream=self.stream, temperature=self.temperature,
                          max_tokens=self.max_tokens, *args, **kwargs)
    return response.choices[0].message.content
```

**Aggregator wrapper (`AISuiteWrapper`).** One class fronts *many* providers via aisuite's
`provider:model` string (`"anthropic:claude-3-5-sonnet"`). Same `run` → `messages` →
`choices[0].message.content` shape. When a third party already unifies providers, wrap *it*
rather than re-implementing per-provider clients.

**TTS (`OpenAITTS`).** Subclasses `BaseLLM`; `run` POSTs to the speech endpoint and accumulates
streamed chunks into `bytes`; `run_and_save` writes a WAV. Return bytes — let the caller decide
to save.

**Image-gen (`Dalle3`).** Own dataclass. `__call__` is decorated `@backoff.on_exception(expo,
max_time=...)`, checks a `TTLCache`, calls `client.images.generate`, downloads the returned URL,
saves under `save_path`, returns the local path, and on `openai.OpenAIError` logs in red and
**re-raises**. This is the reference error/caching pattern.

**Local VLM (`Fuyu`).** Subclasses `BaseMultiModalModel`. `__init__` loads tokenizer +
image-processor + model from HuggingFace; `run(text, img)` opens the image to PIL, runs the
processor, moves tensors to device, `model.generate(...)`, then `processor.batch_decode(...)`.
Local-weights providers do their normalization through a HF processor instead of a remote SDK.

## Anti-patterns to avoid (seen in the source)

- Returning a sentinel error string instead of raising (`TogetherLLM`).
- A `run` that `print`s its result instead of returning it (`Fuyu`, `run_many`).
- Hoisting every provider's params into the shared constructor (`BaseLLM`) — most go unused.
- Module-level side effects: `ai_suite_wrapper.py` instantiates a client and prints at import
  time. Keep wrappers import-pure; gate demos behind `if __name__ == "__main__"`.
