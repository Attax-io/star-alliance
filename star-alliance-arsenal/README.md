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

## MiniMax media models (image · video · speech · music)

Beyond M3 (text), the MiniMax DIRECT API — same `~/.config/minimax/m3.key` — also forges media.
These are **not** chat models: `summon.py`/`minimax.py` are text-only and do not route them. Hit the
media endpoints directly (or use `gen-skill-art.cjs` for image). All four are registered as Arsenal
weapons in `../app.js` (`MODELS`, tier **Forge**), so they appear on the dashboard.

| Weapon id | API model | Endpoint | Helper |
|---|---|---|---|
| `image-01` | `image-01` | `POST /v1/image_generation` | **`node ../gen-skill-art.cjs`** — forged every `skill-art/*.png` |
| `minimax-video` | `MiniMax-Hailuo-02` | `POST /v1/video_generation` (async → poll `/v1/query/video_generation` → fetch `/v1/files/retrieve`) | none yet |
| `minimax-speech` | `speech-02-hd` | `POST /v1/t2a_v2` | none yet |
| `minimax-music` | `music-1.5` | `POST /v1/music_generation` | none yet |

Auth for all: `Authorization: Bearer $(cat ~/.config/minimax/m3.key)`. **Verify the exact model tag
before a run** — MiniMax bumps them. Only `image-01` has a helper today. Set real caps in
`models-usage.json`.

## Re: the dashboard

The Arsenal page's per-model "How to summon" recipes (in `../app.js`, the `MODELS` map)
point at these scripts. The dev server's `/api/arsenal` (`../.claude/serve.cjs`) reads
`models-usage.json` from this folder.
