---
type: Reference
title: haiku
description: How to pull and summon the haiku weapon.
timestamp: 2026-06-27T00:00:00Z
---

# haiku

**Status:** LIVE — native to the orchestrator  
**Kind:** text

Fastest, cheapest Claude — quick mechanical reasoning.

## Backend

Claude-native. **No script, no pull.** The orchestrator IS this model.

## How to pull

_None._ Nothing to pull — Claude runs inside the harness.

## How to summon

Run via the **Task tool** with `model=haiku`. `summon.py haiku` only prints a reminder (exit 0) — it does NOT call a backend.
```
summon.py haiku   # -> "native — use the Task tool"
```

Counts against your **Claude plan** 5h window, not Ollama. Separate pool — safe to overlap with Ollama/MiniMax calls.

> Index: [models/README.md](README.md) · dispatcher: [summon.py](../summon.py) · cloud backend: [ollama_cloud.py](../ollama_cloud.py)
