---
type: Document
title: Providers, Selection & Composition Runtimes
description: Scored provider selection, the free-first ladder, and the Remotion/HyperFrames/FFmpeg runtime choice.
timestamp: 2026-06-28T00:00:00Z
---

# Providers, Selection & Composition Runtimes

How to choose *which* tool produces each asset, and *which* engine composes the final
timeline — without vendor lock-in and without silent swaps. Sources: README ("Scored Provider
Selection", "Supported Providers"), `docs/PROVIDERS.md`, `AGENT_GUIDE.md` ("Composition
Runtimes", "Capability Discovery").

## Discover capability at runtime — never from memory

Capability is read from the live registry, not assumed. At preflight, run
`provider_menu_summary()` (the human-ready rollup) — not the raw `support_envelope()`
firehose. It returns: `composition_runtimes` (ffmpeg/remotion/hyperframes booleans),
`capabilities[]` (configured/total counts + provider lists), `setup_offers[]` (1-minute
env-var fixes), `runtime_warnings[]` (silent-failure signals — surface verbatim).

Present this as a **capability menu**, never a flat tool list:

```
Video Generation: 0/13 configured    Image Generation: 1/7 configured
Text-to-Speech:   1/3 configured     Composition:      3/3 (FFmpeg, stitch, trim)
You can produce videos now with images + TTS + FFmpeg.
```

Always show the "X of Y configured" ratio so breadth is visible. Group by capability, not by
tool. Show what they can do *now*, then what they could *unlock*. Don't hardcode provider
names, key names, or setup URLs — read them from each tool's `install_instructions` and
`dependencies` fields. If the user declines setup, proceed with the best available path — no
nagging.

## Dual-provider rule: every capability has a free/local path

Every capability must support both **API providers** (cloud, paid) and **local/open-source
alternatives** (free, GPU- or local-dependent). The free-first ladder (from `PROVIDERS.md`):
Pexels/Pixabay stock ($0) → Google TTS / ElevenLabs / Piper offline TTS ($0) → fal.ai for
broad image+video coverage (~$0.03/img) → premium video (Runway/Veo/Kling) and Suno music
(pay-as-you-go) → local GPU video (WAN, Hunyuan, CogVideo, LTX) and local diffusion ($0+GPU).

**With zero keys you can still ship real video:** Piper narrates, stock/open archives supply
visuals, and Remotion (or FFmpeg) composes. The "no keys" path is a feature, not a fallback
apology.

## Scored provider selection (7 dimensions)

Route multi-provider capabilities through the **selectors** (`tts_selector`,
`image_selector`, `video_selector`), which auto-discover providers from the registry — adding
a provider tool makes it available with no selector change. Each selection runs a scoring
engine: task fit (30%), output quality (20%), control features (15%), reliability (15%), cost
efficiency (10%), latency (5%), continuity (5%). The winning provider and its score are logged
in the decision trail with all alternatives considered. Selectors normalize loose brief
context ("Pixar-style with character consistency") into scorer-friendly intent before ranking,
and surface the chosen provider's Layer-3 `agent_skills` so the agent reads the right
prompting guide before writing a prompt.

User preference, when explicitly given and available, wins over the score — surface the
vendor directly, don't hide provider choice.

## The three-layer knowledge architecture

Read in this order; do not write prompts from memory:

- **Layer 1 — `tools/` + `pipeline_defs/`:** *what exists* — capabilities, runtime, cost,
  fallback chain, related skills.
- **Layer 2 — `skills/`:** *how OpenMontage wants it used* — pipeline integration, quality
  bars, artifact mappings.
- **Layer 3 — `.agents/skills/`:** *how the technology works* — vendor-specific prompt
  engineering, parameter tuning, quality keywords.

**Layer 3 is mandatory before any generation call.** Every generation tool declares an
`agent_skills` field; read it first. The difference between a generic prompt and a
skill-informed one is the difference between "usable" and "cinematic" (e.g. read `ai-video-gen`
before calling `kling_video` for camera-direction syntax). Prefer skills over source for usage;
read source only to debug, audit, or verify the governance contract.

## Composition runtimes — present both, swap neither

`video_compose` has three parallel engines. The choice is made at proposal, locked in
`edit_decisions.render_runtime`, and carried unchanged through compose:

| Engine | Best for | Requires |
|--------|----------|----------|
| **Remotion** (React) | data-driven explainers, still-image→animated scenes, charts, stat/text cards, word-level captions, TalkingHead | Node.js + `remotion-composer/` |
| **HyperFrames** (HTML/CSS/GSAP) | kinetic typography, product promos, launch reels, website-to-video, registry blocks, SVG character rigs | Node ≥ 22 + FFmpeg + `npx hyperframes` |
| **FFmpeg** | pure concat/trim, subtitle burn-in, simple cuts | `ffmpeg` binary (always present) |

**Present both runtimes (HARD RULE).** When both Remotion and HyperFrames are available,
present both to the user before locking `render_runtime` — one-line "best at" + one-line
honest tradeoff + a recommendation tied to the brief's delivery promise. Silently picking a
"default" is forbidden even when a manifest suggests one; logging only one runtime as
considered is a critical reviewer finding. If only one is installed, say so explicitly and
record the other as `rejected_because: runtime not available`.

**Silent runtime swap is forbidden.** If `render_runtime="hyperframes"` was locked and
HyperFrames is unavailable, do *not* reroute to Remotion — surface a structured blocker, get
approval, log a `render_runtime_selection` decision, then proceed.

## Templated vs Atelier (authoring mode)

Orthogonal to *which engine* is *how* the composition is built — log it as its own
`composition_mode` decision:

- **Templated** — assemble the stock scene-types (`text_card`, `stat_card`, `bar_chart`, …)
  into the existing Explainer/Cinematic compositions. Fast, cheap, reliable — and *the reason
  most videos look alike*. Right for batch output, localization variants, drafts, low-stakes
  clips.
- **Atelier** — hand-author the composition from scratch: bespoke scenes, a one-off theme,
  motion written for this piece. **Default to atelier for hero work** (marketing, launches,
  brand films, any single deliverable that must impress). The deciding rule: *reuse engine
  knowledge, never creative components* — in atelier mode the stock catalog and registry
  blocks are off-limits because they are frozen looks that reintroduce sameness. Close with a
  distinctness review: *could this be any other product's video?* Atelier costs more
  tokens/iteration than templated — say so at proposal so the user opts in knowingly.

## Style playbooks & platform profiles

Visual language is controlled by **style playbooks** (`clean-professional`,
`flat-motion-graphics`, `minimalist-diagram`) governing typography, palette, motion, audio,
and quality rules — the agent applies them consistently across every generated asset.
**Platform output profiles** (YouTube 16:9/4K/Shorts, Reels, TikTok 9:16, LinkedIn,
Cinematic 21:9) set resolution, codec, CRF, max duration, and caption format per target.
