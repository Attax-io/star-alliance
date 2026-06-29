---
type: Reference
title: haiku
description: How to pull and summon the haiku weapon (generated from models.json).
timestamp: 2026-06-27T00:00:00Z
---

# haiku

**Status:** LIVE (reserve) — pulled & reachable  
**Role:** doer · **Backend:** claude · **Kind:** text

Fastest, cheapest Claude — quick mechanical reasoning.

## Backend

Claude-native. **No script, no pull.** Reserve model — dispatched via delegate_task.

## How to pull

_None._ Nothing to pull — Claude runs inside the harness.

## How to summon

Run via **delegate_task** with `model=haiku`. `summon.py haiku` only prints a reminder (exit 0) — it does NOT call a backend.

Counts against your **Claude plan** 5h window, not Ollama — a separate pool, safe to overlap with Ollama/MiniMax calls.

> Generated from [models.json](../models.json) by `gen_model_docs.py`. Edit the registry, not this file. Dispatcher: [summon.py](../summon.py) · cloud backend: [ollama_cloud.py](../ollama_cloud.py)
