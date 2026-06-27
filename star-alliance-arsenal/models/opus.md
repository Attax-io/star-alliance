---
type: Reference
title: opus
description: How to pull and summon the opus weapon.
timestamp: 2026-06-27T00:00:00Z
---

# opus

**Status:** LIVE — native to the orchestrator  
**Kind:** text

Deepest structural reasoning — the prime thinker for hard plans.

## Backend

Claude-native. **No script, no pull.** The orchestrator IS this model.

## How to pull

_None._ Nothing to pull — Claude runs inside the harness.

## How to summon

Run via the **Task tool** with `model=opus`. `summon.py opus` only prints a reminder (exit 0) — it does NOT call a backend.
```
summon.py opus   # -> "native — use the Task tool"
```

Counts against your **Claude plan** 5h window, not Ollama. Separate pool — safe to overlap with Ollama/MiniMax calls.

> Index: [models/README.md](README.md) · dispatcher: [summon.py](../summon.py) · cloud backend: [ollama_cloud.py](../ollama_cloud.py)
