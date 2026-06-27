---
type: Reference
title: image-01
description: How to pull and summon the image-01 weapon.
timestamp: 2026-06-27T00:00:00Z
---

# image-01

**Status:** LIVE — MiniMax media (image)  
**Kind:** media

Text→image forge. Forged every `skill-art/*.png` tile.

## Backend

MiniMax DIRECT API `POST /v1/image_generation` (model `image-01`). **Not** routed by summon/minimax.py (text-only).

## How to pull

_None._ Direct API, same `~/.config/minimax/m3.key`.

## How to summon

Use the helper: `node star-alliance-arsenal/gen-skill-art.cjs` (or `imagegen.py`). Text dispatchers do NOT route media.

Forge SEQUENTIALLY — background bash has no API net. Verify the model tag before a run (MiniMax bumps them).

> Index: [models/README.md](README.md) · dispatcher: [summon.py](../summon.py) · cloud backend: [ollama_cloud.py](../ollama_cloud.py)
