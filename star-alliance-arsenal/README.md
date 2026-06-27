---
type: Readme
timestamp: 2026-06-27T10:27:03Z
---

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
| `ollama_cloud.py <tag>:cloud "<prompt>"` | Any Ollama Cloud model (`/api/chat`). Slot-guarded — see **Concurrency**. |
| `ultra_brainstorm.py "<brief>"` | **Multi-thinker fan-out** for the `ultra-brainstorming` skill — fires every reachable thinker sequentially, returns JSON candidates for synthesis. |
| `models/` | **Per-weapon docs** — one md each: backend · how to pull · how to summon · concurrency. [Index](models/README.md). |
| `models-usage.json` | Parked hand-edited caps (was the consumption gauge; gauge removed, file kept). |

## Concurrency (Ollama Cloud)

Ollama Cloud caps **concurrent models** by plan — **Free = 1**, Pro = 3, Max = 10.
Beyond the cap, requests queue, then get **rejected** (429/503) once the queue fills.
A naive parallel fan-out (e.g. firing 5 thinkers at once) therefore silently loses
the overflow models — they *look dead* when the account is just over its slot count.

`ollama_cloud.py` guards this with a cross-process **slot semaphore**
(`OLLAMA_MAX_CONCURRENT`, default **1**) + busy-retry, so calls queue **locally**
instead of being dropped. Keep it at `1` on Free; set it to your plan's number on
Pro/Max. MiniMax-direct and Claude (Task tool) are **separate pools** — they overlap
the Ollama panel freely.

```
OLLAMA_MAX_CONCURRENT=1 python3 star-alliance-arsenal/summon.py glm-5.2 "…"   # Free
OLLAMA_MAX_CONCURRENT=3 python3 star-alliance-arsenal/summon.py glm-5.2 "…"   # Pro
```

## summon.py routing

Tags below mirror summon.py's `CLOUD_TAG` exactly (the dispatcher is the source of
truth) and were verified against `ollama list` on 2026-06-27 — all six bench tags
are pulled and reachable. They are RESERVE (idle: ~0 ledger calls; minimax-m3 takes
99% of offload), not broken — kept available, just not advertised as the live doer.

```
summon.py minimax-m3 …     → minimax.py                              (LIVE — 99% of offload)
summon.py glm-5.2 …        → ollama_cloud.py glm-5.2:cloud           (reserve, pulled)
summon.py kimi-k2.7 …      → ollama_cloud.py kimi-k2.7-code:cloud    (reserve, pulled)
summon.py deepseek-v4-pro… → ollama_cloud.py deepseek-v4-pro:cloud   (reserve, pulled)
summon.py nemotron-3-ultra…→ ollama_cloud.py nemotron-3-super:cloud  (reserve, pulled)
summon.py qwen3.5 …        → ollama_cloud.py qwen3.5:cloud           (reserve, pulled)
summon.py gemma4 …         → ollama_cloud.py gemma4:cloud            (reserve, pulled)
summon.py opus|sonnet|haiku→ "native — use the Task tool" (exit 0)
summon.py gpt-5.5          → "not provisioned" (exit 69)
```

## Shared flags

`-s <system>` · `--json` (strips ```fences + validates) · `-f <file>` · reads **stdin** if no prompt arg.

- `minimax.py` — key from `$MINIMAX_API_KEY` else `~/.config/minimax/m3.key`; `--max-tokens` default **16000** (never low — reasoning eats the budget → empty output).
- `ollama_cloud.py` — `--num-predict` default **4096** (same trap); strips `<think>…</think>`. All six bench tags above are pulled (verified `ollama list`, 2026-06-27) but RESERVE — minimax-m3 carries ~99% of offload; reactivation is a one-line move back to a live loadout once a bench weapon is actually drawn.
- `minimax.py --batch <file.jsonl>` — process N prompts over ONE keep-alive connection (one spawn, one TLS handshake) and emit JSONL results in order; `guild/delegate.py:delegate_many()` wraps it. The time win for any fan-out step.

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
