---
type: Document
title: Post-Production & Finishing Tools
description: The end-tag closing-card rendering contract and the finishing-tool catalog (reframe, grade, key, captions, silence, reference grounding).
timestamp: 2026-06-28T00:00:00Z
---

# Post-Production & Finishing Tools

The catalog of finishing tools the agent reaches for after assets exist — closing cards,
aspect conversion, color, keying, captions, dead-air removal, and reference grounding. Source:
`pipeline_defs/documentary-montage.yaml` (end-tag contract), `tools/video/*`,
`tools/enhancement/color_grade.py`, `tools/analysis/video_analyzer.py`,
`schemas/artifacts/video_analysis_brief.schema.json`.

## End-tag closing-card rendering contract

A **closing card** (the documentary "end-tag" — one philosophical line over the final scenes)
is a first-class, **MANDATORY** artifact on tone-poem / documentary work (absent only with an
explicit user opt-out recorded in the brief). The end-tag plan is set at `idea` (text, palette,
duration, mode), its timing is locked at `edit`, and it is rendered at `compose`. It has two
render modes:

- **`overlay` (default).** Rendered as a **ProRes 4444 clip with an alpha channel**, composited
  on top of the final scenes via the Remotion CinematicRenderer. The text appears *over the
  footage*, and **the overlay does not extend the timeline** — body duration is unchanged; the
  edit carries `end_tag.offset_seconds`. Verification: extract a frame from the overlay region
  and confirm the text is visible **over footage, not over black**.
- **`concat` (fallback).** An opaque end-tag card **appended after the body**, which *does* add
  its own duration to the total. Verification: the **last frame must be the end-tag card**.

The render report records `end_tag_rendered`, `end_tag_mode` (`overlay`|`concat`), and
`music_mixed`. Runtime constraint: on `documentary-montage` the overlay/concat end-tag stack
**depends on Remotion** CinematicRenderer components — the locked `render_runtime` must stay
`remotion` until HyperFrames end-tag parity lands; a silent swap to `hyperframes`/`ffmpeg` is a
CRITICAL governance violation.

## Finishing-tool catalog

Each tool is a single capability; reach for it by name, read its tool-layer doc before calling.

- **`auto_reframe`** — aspect-ratio conversion with **face tracking**. Converts e.g. 16:9 →
  9:16 for Reels/Shorts/TikTok while keeping the speaker's face centered (MediaPipe/OpenCV face
  detection → smoothed bounding-box trajectory → FFmpeg crop). No GPU. Primary use: landscape
  talking-head → vertical social. Don't naive-crop a talking head; reframe it.
- **`color_grade`** (`tools/enhancement/`) — cinematic grading via FFmpeg LUT + filter chains.
  Applies built-in profile presets **or an external `.cube` LUT** file. This is the tool that
  delivers the *uniform grade across mixed-era footage* the documentary-montage compose stage
  requires.
- **`green_screen_processor`** — chroma/blue-screen **keying**. Methods: `auto` (analyze frame
  histograms to choose), `chromakey` (FFmpeg, fast, clean screens), `rembg` (AI u2net
  segmentation, slower, any background). Pair with `green_screen_composite` to lay the keyed
  speaker over a Remotion background (news-anchor / behind / PiP / split layouts).
- **`remotion_caption_burn`** — **word-level / karaoke captions** burned onto a talking-head
  video via the Remotion CaptionOverlay component, driven by **WhisperX word-level transcript
  segments**. Runtime-specific (Remotion-only); falls back to FFmpeg `subtitles` burn-in if
  Remotion is unavailable. If a brief requires word-level captions, lock `render_runtime` to
  `remotion` (HyperFrames word-level parity is not yet there).
- **`silence_cutter`** — automatic jump cuts via FFmpeg `silencedetect`. Modes: `remove` (cut
  silent segments → tight jump cut), `speed_up` (speed silent segments instead — less jarring),
  `mark` (output silence timestamps for manual review only). No deps beyond FFmpeg.

## Reference grounding — the `video_analysis_brief` artifact

When starting from a reference video, `video_analyzer` (`tools/analysis/`) produces a
schema-validated **`video_analysis_brief`** (`schemas/artifacts/video_analysis_brief.schema.json`):
a structured analysis — transcript, scene detection, keyframes, pacing, style — run **entirely
locally with zero API keys** (yt-dlp download, youtube-transcript-api / faster-whisper for
captions, PySceneDetect/FFmpeg for scenes + frame extraction). The tool provides the structured
data; **the agent's own vision model interprets the keyframes** and enriches the brief. This
artifact is the grounding context that feeds reference-driven pipeline productions — it is what
turns "make me something like this" from a search request into a grounded plan.
