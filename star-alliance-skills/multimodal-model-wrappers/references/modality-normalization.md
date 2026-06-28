---
type: Document
title: Modality normalization
description: Input/output normalization patterns per modality, the typed MultimodalData envelope, and the escape-hatch rule.
timestamp: 2026-06-28T00:00:00Z
---

# Modality normalization

The wrapper's value is that the caller hands you the **simplest possible input** and receives
the **simplest possible output**. Everything in between — SDK message shapes, base64 encoding,
URL downloads, tensor decoding, file writes — is the subclass's private business.

## Input normalization patterns

| Input the caller gives | What the subclass turns it into | Source |
|------------------------|----------------------------------|--------|
| `task: str` (+ optional `system_prompt`) | `messages=[{"role":"system",...},{"role":"user",...}]` | `LiteLLM._prepare_messages`, `TogetherLLM`, `AISuiteWrapper` |
| `img: str` (local path) | base64 string for an API, or PIL `Image` for local models | `BaseMultiModalModel.encode_img`, `get_img` |
| `img: str` (URL) | downloaded PIL `Image` (`requests.get` → `BytesIO` → `Image.open`) | `BaseMultiModalModel.get_img_from_web` |
| `text + img` (local VLM) | one processor call producing model tensors on `device` | `Fuyu.run` |

Factor the message-building into a small private helper (`_prepare_messages`) so system-prompt
handling and role shaping are written once per provider and tested in isolation.

## Output normalization patterns

| Provider returns | Promised contract return | How |
|------------------|--------------------------|-----|
| `response.choices[0].message.content` | `str` (LLM) | direct extraction |
| image **URL** | local file **path** (image-gen) | download via `requests`, save under `save_path`, return path |
| streamed audio chunks | audio `bytes` (TTS) | accumulate `response.iter_content(...)` into one `bytes` |
| token tensors | decoded `str` (VLM) | `processor.batch_decode(output, skip_special_tokens=True)` |
| generated frames | video **path** (TTV) | `export_to_video(...)`, return path |

**Rule:** the contract's return type is a promise. If a provider hands back something else (a
URL when the contract promises a path, a tensor when it promises a string), the subclass — not
the caller — does the conversion. The caller must never branch on which provider it got.

## The typed modality envelope (`model_types.py`)

When a call needs more than "a string and maybe one image," stop passing positional args and
pass a typed envelope. The source defines pydantic models:

```python
class TextModality(BaseModel):   content: str
class ImageModality(BaseModel):  url: str; alt_text: Optional[str] = None
class AudioModality(BaseModel):  url: str; transcript: Optional[str] = None
class VideoModality(BaseModel):  url: str; transcript: Optional[str] = None

class MultimodalData(BaseModel):
    text:   Optional[List[TextModality]]  = None
    images: Optional[List[ImageModality]] = None
    audio:  Optional[List[AudioModality]] = None
    video:  Optional[List[VideoModality]] = None
```

Why it earns its place:
- **Self-describing** — each item carries its own metadata (`alt_text`, `transcript`), so one
  interface carries mixed media without an explosion of positional arguments.
- **Validated + serializable** — pydantic gives you type-checking, defaults, and JSON in/out
  for free, which matters when the envelope crosses a process or wire boundary.
- **Extensible** — add a modality by adding a field, not by re-signing every `run`.

Reach for it when the abstraction must carry several media at once or round-trip structured
multimodal data; for a plain LLM call, `run(task)` is still the right, lighter surface.

## The escape-hatch rule (so the wrapper doesn't become lossy)

A unified wrapper turns net-negative the moment it forces every provider through a
string-in/string-out hole and silently drops streaming, tool-calls, vision detail, or
provider-specific knobs. Two mitigations, both present in the source:

1. **`*args, **kwargs` passthrough.** Every `run` forwards extra args straight to the native
   client (`completion(..., *args, **kwargs)`, `client.chat.completions.create(..., **kwargs)`).
   A caller who needs a provider-only parameter passes it through without you enumerating it.
2. **Expose the raw client.** Keep `self.client` (or the underlying SDK object) reachable so a
   power user can drop down to the native API for the 20% the abstraction can't model — while
   the 80% common path stays unified.

When a modality genuinely cannot honor the shared contract without lying about its return type
(embeddings need two verbs, not one), **give it its own base** rather than distorting the
shared one. A clean second contract beats a leaky single one.
