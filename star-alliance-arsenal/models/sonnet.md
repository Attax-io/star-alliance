---
type: Reference
title: sonnet
description: How to pull and summon the sonnet weapon (generated from models.json).
timestamp: 2026-06-27T00:00:00Z
---

# sonnet

**Status:** LIVE  
**Role:** both · **Backend:** claude · **Kind:** text

Balanced thinker + Claude-capable fallback — last in every arsenal.

## Backend

Claude-native. **No script, no pull.** The orchestrator IS this model.

## How to pull

_None._ Nothing to pull — Claude runs inside the harness.

## How to summon

Run via the **Task tool** with `model=sonnet`. `summon.py sonnet` only prints a reminder (exit 0) — it does NOT call a backend.

Counts against your **Claude plan** 5h window, not Ollama — a separate pool, safe to overlap with Ollama/MiniMax calls.

> Generated from [models.json](../models.json) by `gen_model_docs.py`. Edit the registry, not this file. Dispatcher: [summon.py](../summon.py) · cloud backend: [ollama_cloud.py](../ollama_cloud.py)
