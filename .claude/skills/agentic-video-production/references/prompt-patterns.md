---
type: Document
title: Brief & Prompt Patterns
description: How a plain-language brief should be shaped to route the right pipeline, path, and cost.
timestamp: 2026-06-28T00:00:00Z
---

# Brief & Prompt Patterns

How to read (and how to help a user shape) a plain-language brief so it routes to the right
pipeline, the right visual path, and a known cost. Source: README "Try These Prompts",
`PROMPT_GALLERY.md`, `AGENT_GUIDE.md` onboarding.

## A brief carries five routing signals

Before pipeline selection, extract these from the brief — ask only for the ones that
materially change the plan:

1. **Duration** — the agent sizes content density to length (≈110 words narration for 45s,
   ≈225 for 90s). Always pin it.
2. **Visual path** — image-based, generated-motion, or real-footage (see corpus-and-footage).
   Phrases like "use real footage only" / "no paid APIs" hard-select the free real-footage or
   zero-key path.
3. **Audience** — "for junior developers" / "for 8th graders" changes script, pacing, and
   visual style as much as the topic does.
4. **Named visual components** — "bar chart for the comparison, donut for the breakdown,
   stat cards for the key numbers." The system has bar/line/pie/donut charts, KPI grids,
   progress bars, comparison cards, callouts — name them and they get used.
5. **Style & tone** — "Ghibli-style," "elegiac," "modern and minimal," "Adam-Curtis archival."
   Style explicitness routes the playbook and (for anime) the Animation pipeline.

## Pipeline triggers by brief shape

| Brief shape | Routes to | Path / cost signal |
|-------------|-----------|--------------------|
| "explainer about X, narration + captions" | `animated-explainer` | zero-key with Piper+Remotion; ~$0 |
| "data-driven video, charts comparing …" | `animated-explainer` (templated) | charts/stat cards; ~$0 |
| "Ghibli/anime-style 30s of …" | `animation` (image_animation) | FLUX stills + crossfade/particles; ~$0.15 |
| "documentary montage / tone poem, real footage only" | `documentary-montage` | CLIP corpus retrieval; ~$0 |
| "cinematic trailer / teaser, motion clips" | `cinematic` | Veo/Kling motion; ~$1–3, motion required |
| "kinetic typography / product launch reel" | `animation` via HyperFrames | HTML/GSAP; ~$0 |
| "make me something like this <video>" | reference entry → best-fit pipeline | analyze first, 2–3 concepts |
| "edit / cut up this footage" | `talking-head` / `clip-factory` / `hybrid` | source-media inspection first |
| "avatar announcing X" | `avatar-spokesperson` | HeyGen + TTS; ~$1.50 |
| "turn this 2h podcast into clips" | `podcast-repurpose` / `clip-factory` | batch ranked clips |

## Onboarding a vague brief

When the first message is vague ("make me a video," "what can you do?"), don't guess. Run
capability discovery, classify the user's setup, present capabilities in plain language, and
offer **4–5 starter concepts** tailored to their *available* tools. The goal: curious →
making a video in under 60 seconds. Skip onboarding when the brief is specific and actionable.

## The proposal is where cost and look get committed

Before any asset generation, the user sees: 4–5 concept directions (when open), recommended
pipeline, recommended + alternative *available* tool paths, the **music plan** (mandatory for
any audio pipeline — library track / drop-in / generate / none, surfaced at proposal not
deferred to the expensive asset stage), a cost estimate with quality tradeoffs, and the
stage-by-stage plan. Approval gates asset generation.

## Specificity is the lever

The single biggest quality lever is brief specificity. Coach the user (or self-correct):
instead of "make it look good," say "bar charts for the comparison, a donut for the breakdown,
stat cards for the numbers." Instead of "a video about coffee," say "60s, bar charts comparing
countries, a pie chart of coffee types, conversational narrator, 9:16 for TikTok." Name the
components, the audience, the duration, the tone — vagueness is what produces generic output.
