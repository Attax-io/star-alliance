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
| [opus](opus.md) | thinker | claude | reserve |
| [sonnet](sonnet.md) | both | claude | reserve |
| [haiku](haiku.md) | both | claude | reserve |
| [minimax-sub](minimax-sub.md) | doer | minimax-direct | live |
| [minimax-payg](minimax-payg.md) | doer | minimax-direct | live |
| [glm-5.2](glm-5.2.md) | doer | ollama-cloud | live |
| [kimi-k2.7](kimi-k2.7.md) | doer | ollama-cloud | live |
| [image-01](image-01.md) | media | minimax-media | live |
| [minimax-video](minimax-video.md) | media | minimax-media | live |
| [minimax-speech](minimax-speech.md) | media | minimax-media | live |
| [minimax-music](minimax-music.md) | media | minimax-media | live |

## Concurrency (cloud)

## Concurrency

Ollama Cloud caps **concurrent models** by plan — **Free = 1**, Pro = 3, Max = 10. Beyond the cap requests queue, then get **rejected** once the queue fills (a 429/503). A naive parallel fan-out loses the overflow models — they look dead when the account is just over its slot count. The arsenal guards this: `ollama_cloud.py` holds a cross-process slot semaphore (`OLLAMA_MAX_CONCURRENT`, default **1**) and retries on busy, so calls queue LOCALLY instead of being dropped. Set `OLLAMA_MAX_CONCURRENT` to your plan's number; keep it at 1 on Free.


## Findings (for future runs)

- **Ollama Cloud Free = 1 concurrent model** (Pro=3, Max=10). A parallel fan-out **rejects** the overflow — it is NOT a dead model. Run sequentially or set `OLLAMA_MAX_CONCURRENT` to your plan number.
- **Default `--max-tokens` = 16000.** Reasoning models return empty if the budget is too small (eaten by `<think>`). Verified 2026-06-27: a 60-token call returns empty; 800+ returns content.
- **`minimax-sub` (direct API) is the prime DOER**; the Ollama bench (incl. `kimi-k2.7` since weapon-utility 1.7.0) is read as **thinkers**. Separate pools — Claude (Task) + MiniMax-direct overlap the Ollama panel freely.
- **glm-5.2 confirmed alive** 2026-06-27 (returned `GLM_ALIVE`). A 'glm missing' scare was a truncated `ollama list | head` — it is pulled.

