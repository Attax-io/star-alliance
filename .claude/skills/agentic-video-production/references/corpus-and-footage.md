---
type: Document
title: Corpus & Footage — Real Video, Not Animated Stills
description: Retrieval-first b-roll, building a CLIP-searchable corpus, and reference-video entry.
timestamp: 2026-06-28T00:00:00Z
---

# Corpus & Footage — Real Video, Not Animated Stills

The distinguishing doctrine of OpenMontage: it can produce a real **video video** — actual
motion footage edited into a timeline — not only the usual "animate a handful of stills and
call it video" trick. Sources: README ("Start From A Video You Already Love", "What You Get
With Zero API Keys"), `AGENT_GUIDE.md` ("Reference Video Entry Point", "Critical Rule:
Motion-Required Requests").

## Three paths to the visuals — name them honestly

Most "free AI video" stacks quietly mean "Ken Burns over still images." Be explicit about
which path a brief is taking, because they look different and the user is owed the truth:

1. **Image-based video.** Generate (or fetch) still images, then a composition engine
   (Remotion, HyperFrames) animates them — crossfade, parallax, camera motion (zoom/pan/Ken
   Burns), particle overlays. Cheapest path, looks animated, but it is *not motion footage*.
2. **Generated motion video.** A video model (Veo, Kling, Runway, MiniMax, WAN-local, …)
   produces actual moving clips. Cinematic, costs more.
3. **Real-footage / documentary montage.** Build a corpus of **actual motion clips** from
   free stock + open archives, rank them semantically, and cut them into a timeline. No paid
   video model required — and the result is genuine footage, not animated frames.

When the user says "use real footage only," path 3 is mandatory and paths 1–2 are off the
table for the body of the video. When the brief's promise depends on motion (sci-fi trailer,
hype edit, cinematic teaser), **still-image fallback is forbidden** — do not quietly downgrade
a motion-led job into an animatic without explicit approval.

## Corpus building — retrieval-first b-roll

The documentary-montage pipeline builds a **CLIP-searchable corpus** of free/open motion
footage, then retrieves clips by semantic match to each beat of the script:

- **Open archives (no key):** Archive.org, NASA, Wikimedia Commons — archival footage,
  educational media, documentary texture, public-domain video.
- **Free stock (free dev key):** Pexels, Pixabay (footage + images), Unsplash (images).
- **Index, then retrieve.** Ingest candidates, embed with CLIP/BLIP-2, and search the corpus
  by meaning ("rain on a city street at night") rather than by filename. This is a
  retrieval problem, not a generation problem — the b-roll already exists, you find it.

Trigger words that route here: *documentary montage*, *tone poem*, *stock-footage collage*,
*archival collage*, *b-roll corpus*, plus an explicit "real footage only." Tone poems and
mood pieces (no narration, music yes) are the sweet spot.

### The build→retrieve workflow, with the real tool names

The `documentary-montage` pipeline's `assets` stage has two paths; pick by whether you need
semantic ranking over a large pool or just fast acquisition of known clips:

- **Standard path (semantic) — `corpus_builder` → `clip_search`.** `corpus_builder` is the one
  place adapters + embedding + the `Corpus` meet: it fans out across the stock sources,
  downloads candidates, thumbnails them, embeds with CLIP, and indexes. `clip_search` then
  loads that corpus and exposes retrieval (`rank_for_slot` embeds a slot's text description and
  ranks the corpus by meaning, plus diversify/dedupe). Use when the brief needs the best clip
  per beat from a broad pool. The asset-director's quality bar: **corpus size ≥ 8× slot count,
  per-pick scores ≥ 0.22, diversify ran clean, every pick has provenance** (provider,
  original_url, license) and a `rejected_picks` log. Emits `metadata.corpus_stats`.
- **Fast path — `direct_clip_search`.** Same `StockSource` adapter protocol (Pexels,
  Archive.org, NASA, Wikimedia, Unsplash, …) but **skips CLIP embedding** — it downloads
  matching clips directly when you already know what you want. Use for quick fills or when the
  corpus overhead isn't worth it. Inspect thumbnails, note cross-act reuse, fill gaps. Emits
  `metadata.search_stats`.

Both paths must satisfy the same contract downstream: exactly one picked clip per scene slot,
no `clip_id` reused across two slots.

## Starting from a reference video

Starting from a video the user already loves is often faster than starting from a blank
prompt. This is a **first-class workflow**, not a generic web-search request — treat
"make me something like this" as the reference entry point.

The workflow (read `skills/meta/video-reference-analyst.md` in the source for the full
recipe):

1. **Analyze the reference** with local analysis tools — transcript extraction, scene
   detection, keyframe/frame sampling, pacing, style. Works from a YouTube video, Short,
   Reel, TikTok, or a local clip.
2. **Produce a grounded summary**: what the reference is doing — content, pacing, structure,
   style, and *what makes it work*.
3. **Present 2–3 differentiated concepts**, never a carbon copy. For each, be explicit about:
   - **what it keeps** from the reference (pacing, hook style, structure, tone),
   - **what it changes** (topic, visual treatment, angle, narration),
   - **what it will cost** at the target duration before assets are generated,
   - **what it will actually look like** with the user's currently available tools.

Distinguish the two reference shapes:

- **Reference-driven** ("make me something *like* this") → analyze, then create a new,
  differentiated piece.
- **Source-footage** ("edit *this* footage" / "cut this into clips") → inspect the supplied
  media and run a footage-led pipeline (talking-head, clip-factory, hybrid). Do not confuse
  the two — missing this distinction makes a model fall back to search + guesswork.

## Source media inspection — never guess from filenames

When the user brings their own footage, **probe every file** before any creative decision:
resolution, codec, audio channels, duration. Derive planning implications from what the files
*actually contain*. Hallucinating content from a filename is a banned shortcut.
