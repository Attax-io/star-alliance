---
type: Index
title: Arsenal model docs
description: Per-weapon pull + summon reference (generated from models.json).
timestamp: 2026-06-27T00:00:00Z
---

# Arsenal — model docs

One file per weapon, **generated from [models.json](../models.json)** — the canonical registry. Edit the registry, run `gen_model_docs.py`. Dispatcher: [summon.py](../summon.py).

| Weapon | Role | Backend | Status |
|---|---|---|---|
| [opus](opus.md) | thinker | claude | live |
| [haiku](haiku.md) | both | claude | live |
| [minimax-m3](minimax-m3.md) | doer | minimax-direct | live |

## Concurrency (cloud)

## Concurrency

Ollama Cloud caps **concurrent models** by plan — **Free = 1**, Pro = 3, Max = 10. Beyond the cap requests queue, then get **rejected** once the queue fills (a 429/503). A naive parallel fan-out loses the overflow models — they look dead when the account is just over its slot count. The arsenal guards this: `ollama_cloud.py` holds a cross-process slot semaphore (`OLLAMA_MAX_CONCURRENT`, default **1**) and retries on busy, so calls queue LOCALLY instead of being dropped. Set `OLLAMA_MAX_CONCURRENT` to your plan's number; keep it at 1 on Free.


## Findings (for future runs)

- **Ollama Cloud Free = 1 concurrent model** (Pro=3, Max=10). A parallel fan-out **rejects** the overflow — it is NOT a dead model. Run sequentially or set `OLLAMA_MAX_CONCURRENT` to your plan number.
- **Default `--max-tokens` = 16000.** Reasoning models return empty if the budget is too small (eaten by `<think>`). Verified 2026-06-27: a 60-token call returns empty; 800+ returns content.
- **`minimax-m3` (direct API) is the prime DOER**; the Ollama bench (incl. `gemma4` since weapon-utility 1.7.0) is read as **thinkers**. Separate pools — Claude (Task) + MiniMax-direct overlap the Ollama panel freely.
- **glm-5.2 confirmed alive** 2026-06-27 (returned `GLM_ALIVE`). A 'glm missing' scare was a truncated `ollama list | head` — it is pulled.

