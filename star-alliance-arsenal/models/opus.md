---
type: Reference
title: opus
description: How to pull and summon the opus weapon (generated from models.json).
timestamp: 2026-06-27T00:00:00Z
---

# opus

**Status:** LIVE  
**Role:** thinker · **Backend:** claude · **Kind:** text

Deepest structural reasoning — the prime thinker for hard plans.

## Backend

Claude-native. **No script, no pull.** The orchestrator IS this model.

## How to pull

_None._ Nothing to pull — Claude runs inside the harness.

## How to summon

Run via the **Task tool** with `model=opus`. `summon.py opus` only prints a reminder (exit 0) — it does NOT call a backend.

Counts against your **Claude plan** 5h window, not Ollama — a separate pool, safe to overlap with Ollama/MiniMax calls.

> Generated from [models.json](../models.json) by `gen_model_docs.py`. Edit the registry, not this file. Dispatcher: [summon.py](../summon.py) · cloud backend: [ollama_cloud.py](../ollama_cloud.py)
