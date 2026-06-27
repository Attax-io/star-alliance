---
type: Reference
title: deepseek-v4-pro
description: How to pull and summon the deepseek-v4-pro weapon.
timestamp: 2026-06-27T00:00:00Z
---

# deepseek-v4-pro

**Status:** LIVE (reserve) — pulled & reachable  
**Kind:** text

Frontier multi-step reasoning — long dependency chains.

## Backend

Ollama Cloud via `ollama_cloud.py` (local daemon `/api/chat`, tag `deepseek-v4-pro:cloud`).

## How to pull

```
ollama pull deepseek-v4-pro:cloud
```
Verify: `ollama list | grep deepseek-v4-pro`

## How to summon

```
python3 star-alliance-arsenal/summon.py deepseek-v4-pro "<prompt>" --max-tokens 4000
```
Flags: `-s <system>` · `--json` · `-f <file>` · `--timeout <s>`.

## Concurrency

Ollama Cloud caps **concurrent models** by plan — **Free = 1**, Pro = 3, Max = 10. Beyond the cap requests queue, then get **rejected** once the queue fills (a 429/503). A naive parallel fan-out loses the overflow models — they look dead when the account is just over its slot count. The arsenal guards this: `ollama_cloud.py` holds a cross-process slot semaphore (`OLLAMA_MAX_CONCURRENT`, default **1**) and retries on busy, so calls queue LOCALLY instead of being dropped. Set `OLLAMA_MAX_CONCURRENT` to your plan's number; keep it at 1 on Free.

> **Token trap:** reasoning models spend the budget on `<think>` first. Low `--max-tokens` returns **empty content** — keep it ≥ ~2000 (4000 for hard briefs). `ollama_cloud.py` strips `<think>…</think>` before returning.

> Index: [models/README.md](README.md) · dispatcher: [summon.py](../summon.py) · cloud backend: [ollama_cloud.py](../ollama_cloud.py)
