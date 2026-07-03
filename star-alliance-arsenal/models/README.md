---
type: Index
title: Arsenal model docs
description: Per-model reference for the three Claude models (generated from models.json).
timestamp: 2026-07-03T00:00:00Z
---

# Arsenal — model docs

One file per model, describing the three Claude models the guild runs on. Facts
come from the canonical registry [models.json](../models.json) — edit the registry,
not these docs.

| Model | Role | Backend | Status |
|---|---|---|---|
| [opus](opus.md) | thinker | claude | live |
| [sonnet](sonnet.md) | both | claude | live |
| [haiku](haiku.md) | both | claude | live |

The guild is **Claude-only**: there is no external doer, Hermes, or non-Claude
bench. The session persona is a Claude model, and bulk or parallel work is handled
by spawning Claude subagents (the Task/Agent tool), not by dispatching to an
outside model.

## Choosing a model

- **opus** — the master brain. Deepest reasoning; use it for hard plans,
  architecture, and final review.
- **sonnet** — the reliable daily driver. Fast and balanced, near-Opus quality;
  the default for most work.
- **haiku** — the stiletto. Fastest and cheapest; use it for bulk classification,
  routing, summarization, and mechanical transforms — not deep reasoning.

Each member's `model:` frontmatter (or a `memberOverrides` entry in
`models.json`) picks which of these it runs on; otherwise the `seats.brain.default`
applies.
