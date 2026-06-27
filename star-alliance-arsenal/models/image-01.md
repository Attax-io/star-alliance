---
type: Reference
title: image-01
description: How to pull and summon the image-01 weapon (generated from models.json).
timestamp: 2026-06-27T00:00:00Z
---

# image-01

**Status:** LIVE  
**Role:** media · **Backend:** minimax-media · **Kind:** media

Text→image forge. Forged every skill-art/*.png tile.

## Backend

MiniMax DIRECT API media endpoint (model `image-01`). **Not** routed by summon/minimax.py (text-only).

## How to pull

_None._ Direct API, same `~/.config/minimax/m3.key`.

## How to summon

Use the helper: `node star-alliance-arsenal/gen-skill-art.cjs` (or `imagegen.py`). Text dispatchers do NOT route media.

> Generated from [models.json](../models.json) by `gen_model_docs.py`. Edit the registry, not this file. Dispatcher: [summon.py](../summon.py) · cloud backend: [ollama_cloud.py](../ollama_cloud.py)
