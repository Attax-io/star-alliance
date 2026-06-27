---
type: Index
title: Arsenal model docs
description: Per-weapon pull + summon reference.
timestamp: 2026-06-27T00:00:00Z
---

# Arsenal — model docs

One file per weapon: backend, how to pull, how to summon, concurrency.
Dispatcher is [summon.py](../summon.py); cloud backend [ollama_cloud.py](../ollama_cloud.py).

| Weapon | Kind | Status |
|---|---|---|
| [opus](opus.md) | text | LIVE |
| [sonnet](sonnet.md) | text | LIVE |
| [haiku](haiku.md) | text | LIVE |
| [minimax-m3](minimax-m3.md) | text | LIVE |
| [glm-5.2](glm-5.2.md) | text | LIVE (reserve) |
| [kimi-k2.7](kimi-k2.7.md) | text | LIVE (reserve) |
| [deepseek-v4-pro](deepseek-v4-pro.md) | text | LIVE (reserve) |
| [nemotron-3-ultra](nemotron-3-ultra.md) | text | LIVE (reserve) |
| [qwen3.5](qwen3.5.md) | text | LIVE (reserve) |
| [gemma4](gemma4.md) | text | LIVE (reserve) |
| [gpt-5.5](gpt-5.5.md) | text | DEACTIVATED |
| [image-01](image-01.md) | media | LIVE |
| [minimax-video](minimax-video.md) | media | LIVE |
| [minimax-speech](minimax-speech.md) | media | LIVE |
| [minimax-music](minimax-music.md) | media | LIVE |

## Concurrency (cloud)

## Concurrency

Ollama Cloud caps **concurrent models** by plan — **Free = 1**, Pro = 3, Max = 10. Beyond the cap requests queue, then get **rejected** once the queue fills (a 429/503). A naive parallel fan-out loses the overflow models — they look dead when the account is just over its slot count. The arsenal guards this: `ollama_cloud.py` holds a cross-process slot semaphore (`OLLAMA_MAX_CONCURRENT`, default **1**) and retries on busy, so calls queue LOCALLY instead of being dropped. Set `OLLAMA_MAX_CONCURRENT` to your plan's number; keep it at 1 on Free.

