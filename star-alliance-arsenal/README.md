# Star Alliance — Arsenal

The guild's model-calling toolkit. Stdlib-only Python CLIs that let any session (or
skill) **offload text generation off Opus** to a cheaper model. All three were
authored by MiniMax M3 itself (`minimax.py` wrote the other two).

Run from the repo root (paths below assume that), e.g. `python3 star-alliance-arsenal/summon.py …`.

## Scripts

| Script | Purpose |
|---|---|
| `summon.py <model-id> "<prompt>"` | **One dispatcher.** Routes to the right backend by model id. Start here. |
| `minimax.py "<prompt>"` | MiniMax M3 — **direct** cloud sub (`api.minimax.io`). |
| `ollama_cloud.py <tag>:cloud "<prompt>"` | Any Ollama Cloud model (`/api/chat`). |
| `models-usage.json` | Parked hand-edited caps (was the consumption gauge; gauge removed, file kept). |

## summon.py routing

```
summon.py minimax-m3 …     → minimax.py
summon.py glm-5.2 …        → ollama_cloud.py glm-5.2:cloud
summon.py kimi-k2.7 …      → ollama_cloud.py kimi-k2:cloud        (pull first)
summon.py deepseek-v4-pro… → ollama_cloud.py deepseek-v3.1:cloud (pull first)
summon.py nemotron-3-ultra…→ ollama_cloud.py nemotron:cloud      (pull first)
summon.py qwen3.5 …        → ollama_cloud.py qwen3-coder:cloud    (pull first)
summon.py gemma4 …         → ollama_cloud.py gemma3:cloud         (pull first)
summon.py opus|sonnet|haiku→ "native — use the Task tool" (exit 0)
summon.py gpt-5.5          → "not provisioned" (exit 69)
```

## Shared flags

`-s <system>` · `--json` (strips ```fences + validates) · `-f <file>` · reads **stdin** if no prompt arg.

- `minimax.py` — key from `$MINIMAX_API_KEY` else `~/.config/minimax/m3.key`; `--max-tokens` default **16000** (never low — reasoning eats the budget → empty output).
- `ollama_cloud.py` — `--num-predict` default **4096** (same trap); strips `<think>…</think>`. Only `glm-5.2:cloud` is pulled today; other bench tags need `ollama pull` + tag verify.

Token usage prints to **stderr**, content to **stdout** — pipe-friendly.

## Re: the dashboard

The Arsenal page's per-model "How to summon" recipes (in `../app.js`, the `MODELS` map)
point at these scripts. The dev server's `/api/arsenal` (`../.claude/serve.cjs`) reads
`models-usage.json` from this folder.
