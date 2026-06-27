---
type: Reference
title: gpt-5.5
description: How to pull and summon the gpt-5.5 weapon.
timestamp: 2026-06-27T00:00:00Z
---

# gpt-5.5

**Status:** DEACTIVATED — no OpenAI key on device (Atta, 2026-06-26)  
**Kind:** text

OpenAI-direct second opinion. Kept in loadouts on purpose; reactivate with a key.

## Backend

OpenAI-direct. **Not provisioned** — `summon.py gpt-5.5` exits **69**.

## How to pull

_None._ Set an OpenAI API key on the device and wire the OpenAI-direct backend in `summon.py` to reactivate. Do NOT strip from loadouts.

## How to summon

```
summon.py gpt-5.5   # -> "DEACTIVATED", exit 69
```

> Index: [models/README.md](README.md) · dispatcher: [summon.py](../summon.py) · cloud backend: [ollama_cloud.py](../ollama_cloud.py)
