---
type: Reference
title: minimax-video
description: How to pull and summon the minimax-video weapon.
timestamp: 2026-06-27T00:00:00Z
---

# minimax-video

**Status:** LIVE — MiniMax media (video), no helper yet  
**Kind:** media

Text→video. Async: submit → poll → fetch file.

## Backend

MiniMax DIRECT API `POST /v1/video_generation` (model `MiniMax-Hailuo-02`), async → poll `/v1/query/video_generation` → `/v1/files/retrieve`.

## How to pull

_None._ Direct API, `~/.config/minimax/m3.key`.

## How to summon

No helper yet — hit the endpoint directly with the bearer key.

> Index: [models/README.md](README.md) · dispatcher: [summon.py](../summon.py) · cloud backend: [ollama_cloud.py](../ollama_cloud.py)
