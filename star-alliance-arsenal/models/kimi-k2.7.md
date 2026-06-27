---
type: Reference
title: kimi-k2.7
description: How to pull and summon the kimi-k2.7 weapon.
timestamp: 2026-06-27T00:00:00Z
---

# kimi-k2.7

**Status:** LIVE (reserve) — pulled & reachable  
**Kind:** text

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
python3 star-alliance-arsenal/summon.py kimi-k2.7 "<prompt>" --max-tokens 4000
```
Flags: `-s <system>` · `--json` · `-f <file>` · `--timeout <s>`.

## Concurrency

Ollama Cloud caps **concurrent models** by plan — **Free = 1**, Pro = 3, Max = 10. Beyond the cap requests queue, then get **rejected** once the queue fills (a 429/503). A naive parallel fan-out loses the overflow models — they look dead when the account is just over its slot count. The arsenal guards this: `ollama_cloud.py` holds a cross-process slot semaphore (`OLLAMA_MAX_CONCURRENT`, default **1**) and retries on busy, so calls queue LOCALLY instead of being dropped. Set `OLLAMA_MAX_CONCURRENT` to your plan's number; keep it at 1 on Free.

> **Token trap:** reasoning models spend the budget on `<think>` first. Low `--max-tokens` returns **empty content** — keep it ≥ ~2000 (4000 for hard briefs). `ollama_cloud.py` strips `<think>…</think>` before returning.

> Index: [models/README.md](README.md) · dispatcher: [summon.py](../summon.py) · cloud backend: [ollama_cloud.py](../ollama_cloud.py)
