---
type: Reference
title: minimax-m3
description: How to pull and summon the minimax-m3 weapon (generated from models.json).
timestamp: 2026-06-27T00:00:00Z
---

# minimax-m3

**Status:** LIVE  
**Role:** doer · **Backend:** minimax-direct · **Kind:** text

The prime doer. Direct MiniMax cloud sub for bulk generation/transform.

## Backend

MiniMax DIRECT API (`api.minimax.io`) via `minimax.py` — **not** Ollama.

## How to pull

_None._ Direct API. Needs a key at `~/.config/minimax/m3.key` (or `$MINIMAX_API_KEY`).

## How to summon

```
python3 star-alliance-arsenal/summon.py minimax-m3 "<prompt>"
```
Default `--max-tokens` 16000. `minimax.py --batch <file.jsonl>` for one-connection fan-out.

Direct API — **not** subject to the Ollama concurrency cap; its own rate limits apply.

> Generated from [models.json](../models.json) by `gen_model_docs.py`. Edit the registry, not this file. Dispatcher: [summon.py](../summon.py) · cloud backend: [ollama_cloud.py](../ollama_cloud.py)
