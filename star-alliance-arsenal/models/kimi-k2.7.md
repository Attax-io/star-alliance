---
type: Reference
title: kimi-k2.7
description: How to pull and summon the kimi-k2.7 weapon (generated from models.json).
timestamp: 2026-06-27T00:00:00Z
---

# kimi-k2.7

**Status:** LIVE  
**Role:** thinker · **Backend:** ollama-cloud · **Kind:** text

Long-context coherence across large inputs.

## Backend

Ollama Cloud via `ollama_cloud.py` (local daemon `/api/chat`, tag `kimi-k2.7-code:cloud`).

## How to pull

```
ollama pull kimi-k2.7-code:cloud
```
Verify: `ollama list | grep kimi-k2.7-code`

## How to summon

```
python3 star-alliance-arsenal/summon.py kimi-k2.7 "<prompt>" --max-tokens 16000
```
Flags: `-s <system>` · `--json` · `-f <file>` · `--timeout <s>`.

## Concurrency

Ollama Cloud caps **concurrent models** by plan — **Free = 1**, Pro = 3, Max = 10. Beyond the cap requests queue, then get **rejected** once the queue fills (a 429/503). A naive parallel fan-out loses the overflow models — they look dead when the account is just over its slot count. The arsenal guards this: `ollama_cloud.py` holds a cross-process slot semaphore (`OLLAMA_MAX_CONCURRENT`, default **1**) and retries on busy, so calls queue LOCALLY instead of being dropped. Set `OLLAMA_MAX_CONCURRENT` to your plan's number; keep it at 1 on Free.

> **Token trap:** reasoning models spend the budget on `<think>` first. Low `--max-tokens` returns **empty content** — the arsenal default is now **16000**; never drop below ~2000. `ollama_cloud.py` strips `<think>…</think>` before returning.

## Findings (for future runs)

- **Ollama Cloud Free = 1 concurrent model** (Pro=3, Max=10). A parallel fan-out **rejects** the overflow — it is NOT a dead model. Run sequentially or set `OLLAMA_MAX_CONCURRENT` to your plan number.
- **Default `--max-tokens` = 16000.** Reasoning models return empty if the budget is too small (eaten by `<think>`). Verified 2026-06-27: a 60-token call returns empty; 800+ returns content.
- **`minimax-m3` (direct API) is the prime DOER**; the Ollama bench (incl. `gemma4` since weapon-utility 1.7.0) is read as **thinkers**. Separate pools — Claude (Task) + MiniMax-direct overlap the Ollama panel freely.
- **glm-5.2 confirmed alive** 2026-06-27 (returned `GLM_ALIVE`). A 'glm missing' scare was a truncated `ollama list | head` — it is pulled.

> Generated from [models.json](../models.json) by `gen_model_docs.py`. Edit the registry, not this file. Dispatcher: [summon.py](../summon.py) · cloud backend: [ollama_cloud.py](../ollama_cloud.py)
