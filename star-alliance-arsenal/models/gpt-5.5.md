---
type: Reference
title: gpt-5.5
description: How to pull and summon the gpt-5.5 weapon (generated from models.json).
timestamp: 2026-06-27T00:00:00Z
---

# gpt-5.5

**Status:** DEACTIVATED — no key on device (kept in loadouts on purpose)  
**Role:** thinker · **Backend:** openai-direct · **Kind:** text

OpenAI-direct second opinion. Deactivated — no key on device; kept in loadouts on purpose.

## Backend

OpenAI-direct. **Not provisioned** — `summon.py gpt-5.5` exits **69**.

## How to pull

_None._ Set an OpenAI API key on the device and wire the OpenAI-direct backend in `summon.py` to reactivate. Do NOT strip from loadouts.

## How to summon

```
summon.py gpt-5.5   # -> "DEACTIVATED", exit 69
```

> Generated from [models.json](../models.json) by `gen_model_docs.py`. Edit the registry, not this file. Dispatcher: [summon.py](../summon.py) · cloud backend: [ollama_cloud.py](../ollama_cloud.py)
