---
type: Reference
title: gemma4
description: How to pull and summon the gemma4 weapon.
timestamp: 2026-06-27T00:00:00Z
---

# gemma4

**Status:** LIVE (reserve) — pulled & reachable  
**Kind:** text

Google open-weight bench — light, fast **thinker** (cheap second mind, esp. content/marketing; carried by the-herald).

## Backend

Ollama Cloud via `ollama_cloud.py` (local daemon `/api/chat`, tag `gemma4:cloud`).

## How to pull

```
ollama pull gemma4:cloud
```
Verify: `ollama list | grep gemma4`

## How to summon

```
python3 star-alliance-arsenal/summon.py gemma4 "<prompt>" --max-tokens 4000
```
Flags: `-s <system>` · `--json` · `-f <file>` · `--timeout <s>`.

## Concurrency

Ollama Cloud caps **concurrent models** by plan — **Free = 1**, Pro = 3, Max = 10. Beyond the cap requests queue, then get **rejected** once the queue fills (a 429/503). A naive parallel fan-out loses the overflow models — they look dead when the account is just over its slot count. The arsenal guards this: `ollama_cloud.py` holds a cross-process slot semaphore (`OLLAMA_MAX_CONCURRENT`, default **1**) and retries on busy, so calls queue LOCALLY instead of being dropped. Set `OLLAMA_MAX_CONCURRENT` to your plan's number; keep it at 1 on Free.

## Findings (for future runs)

- **Ollama Cloud Free = 1 concurrent model** (Pro=3, Max=10). A parallel fan-out **rejects** the overflow — it is NOT a dead model. Run sequentially or set `OLLAMA_MAX_CONCURRENT` to your plan number.
- **Default `--max-tokens` = 16000.** Reasoning models return empty if the budget is too small (eaten by `<think>`). Verified 2026-06-27: a 60-token call returns empty; 800+ returns content.
- **`minimax-m3` (direct API) is the prime DOER**; the Ollama bench (incl. `gemma4` since weapon-utility 1.7.0) is read as **thinkers**. Separate pools — Claude (Task) + MiniMax-direct overlap the Ollama panel freely.
- **glm-5.2 confirmed alive** 2026-06-27 (returned `GLM_ALIVE`). A 'glm missing' scare was a truncated `ollama list | head` — it is pulled.

> Index: [models/README.md](README.md) · dispatcher: [summon.py](../summon.py) · cloud backend: [ollama_cloud.py](../ollama_cloud.py)
