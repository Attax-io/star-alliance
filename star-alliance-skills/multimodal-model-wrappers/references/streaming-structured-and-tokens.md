---
type: Document
title: Streaming, structured output, and token counting
description: The three escape-hatch contracts a string-in/string-out wrapper must add — an async streaming return, a typed-JSON return, and a token/cost meter — each grounded in the swarm-models source.
timestamp: 2026-06-28T00:00:00Z
---

# Streaming, structured output, and token counting

The base contract (`run(task) -> str`) is the 80% path. The three things callers most
often need *beyond* a finished string — tokens as they arrive, a typed object instead of
prose, and a count of what a call costs — each deserve their own first-class contract rather
than being flattened into the string hole. All three are present in the source; the earlier
skill named the first two only as anti-patterns. They are also legitimate **positive
patterns** when given the right return type.

## 1. Streaming output contract — `AsyncIterator[str]`

A blocking `run(task) -> str` cannot surface partial output; a UI that wants tokens as they
generate needs a *second* verb whose return type is a stream, not a string. `LiteLLM`
provides the seam (`lite_llm_model.py::arun_streaming`):

```python
async def arun_streaming(self, task: str):
    messages = self._prepare_messages(task)
    async for part in acompletion(
        model=self.model_name, messages=messages, stream=True
    ):
        logger.info(part.choices[0].delta.content or "")
```

The source only *logs* each delta — that is the bug to fix when you adopt this. The positive
contract is to **yield** each chunk so a caller can consume the stream:

```python
async def arun_streaming(self, task: str) -> AsyncIterator[str]:
    messages = self._prepare_messages(task)
    async for part in acompletion(
        model=self.model_name, messages=messages, stream=True
    ):
        delta = part.choices[0].delta.content
        if delta:
            yield delta            # yield, don't log-and-drop
```

**Rule.** Streaming is a distinct return type (`AsyncIterator[str]`), so it lives in a
distinct method (`arun_streaming` / `stream`), never bolted onto `run`. The `stream=True`
flag belongs to the SDK call inside that method; the caller picks the verb that matches the
shape it wants (one string vs. a stream of fragments). Accumulate-to-string is the caller's
choice, not the wrapper's default. This is the streaming sibling of the "one verb per
modality" rule: when the *return shape* genuinely differs, give it its own entry point.

## 2. Structured / JSON output escape-hatch — `response_format=BaseModel`

When the caller needs a typed object (a parsed record, a routing decision) rather than free
text, force the provider into a schema instead of post-hoc-parsing prose. `OpenAIFunctionCaller`
(`openai_function_caller.py`) shows the pattern: pass a pydantic `BaseModel` as
`response_format` and read the structured arguments back out:

```python
completion = self.client.beta.chat.completions.parse(
    model=self.model_name,
    messages=[{"role": "system", "content": self.system_prompt},
              {"role": "user", "content": task}],
    response_format=self.base_model,                     # <- the schema
    tools=[openai.pydantic_function_tool(self.base_model)],
    parallel_tool_calls=self.parallel_tool_calls,
    *args, **kwargs,
)
out = completion.choices[0].message.tool_calls[0].function.arguments
return out
```

This reframes tool-calls: the base skill treats them only as a *lossy* thing a string
wrapper drops, and that is right for the **plain `run`** path. But a **dedicated structured
verb** — one whose promised return is a validated object, not a string — is a legitimate
escape hatch for the 20% that needs schema-shaped output. Keep it off `run` and on its own
caller (`OpenAIFunctionCaller.run -> dict`), so the common path stays string-simple while the
structured path stays typed.

Two corrections to make when adopting it:

- **Don't `eval(out)`.** The source does `out = eval(out)` to turn the JSON-string arguments
  into a dict — that executes arbitrary text. Use `json.loads(out)`, or better, hydrate the
  pydantic model: `self.base_model.model_validate_json(out)` so you return a *validated*
  instance, not a bare dict.
- **Pair it with backoff and re-raise, not `return None`.** The source catches every
  `Exception`, logs, and returns `None` — the same swallow-on-failure trap the error-contract
  principle warns against. A structured call that silently yields `None` is worse than a
  string one, because the caller expected a typed object. Wrap the call in
  `@backoff.on_exception` and re-raise on exhaustion (the `dalle3` pattern, below).

## 3. Token counting / cost tracking — `count_tokens`

A wrapper that hides the provider also hides *what a call costs*. Token counting is fully
absent from the base classes; `tiktoken_wrapper.py` supplies a standalone meter that any
wrapper can compose:

```python
class TikTokenizer:
    def __init__(self, model_name: str = "o200k_base"):
        self.encoding = tiktoken.get_encoding(model_name)

    def encode(self, string: str) -> List[int]:
        return self.encoding.encode(string)

    def count_tokens(self, string: str) -> int:
        # source chunks the string and counts chunks across a ThreadPool
        return len(self.encoding.encode(string))
```

The source parallelizes the count across a `ThreadPoolExecutor` (1000-char chunks, 10
workers). That is **over-engineering for the common case** — `len(encoding.encode(string))`
is already fast, and chunking risks miscounting tokens that straddle a chunk boundary. Treat
the threadpool as a curiosity, not a model; the load-bearing idea is *expose a token meter at
all*.

**Where it belongs in the abstraction.** Compose a tokenizer into the base (or a mixin) and
use it for three things the wrappers otherwise can't do:

- **Pre-flight budgeting** — count `task` (+ system prompt) before the call and refuse or
  trim if it exceeds the model's context window, instead of letting the provider 400.
- **Cost tracking** — multiply prompt + completion tokens by a per-model rate to attach a
  cost to each `run`, feeding the metrics the base already collects
  (`_tokens_per_second`, `throughput`).
- **Choosing a model by size** — a router (`model_router.py`) can pick a cheaper model when
  the counted prompt is small.

Counting is provider-relative: pick the encoding that matches the target model
(`o200k_base` for current OpenAI models), and for non-OpenAI providers prefer the provider's
own usage numbers from the response when present, falling back to tiktoken as an estimate.
