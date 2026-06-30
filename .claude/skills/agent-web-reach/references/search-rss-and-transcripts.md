---
type: Document
title: Search, RSS, and Transcripts
description: Choosing a search surface, reading RSS, and extracting video/podcast transcripts in agent-web-reach.
timestamp: 2026-06-28T00:00:00Z
---

# Search, RSS & Transcripts

Three reach modes that aren't "read this one URL": searching, subscribing, and
turning audio/video into text.

## Search — pick the surface, then the tool

There is no single "search the internet." Choose by *where* the answer lives:

| You want… | Use | How |
|---|---|---|
| Whole-web, semantic ("compare LLM frameworks") | **Exa** | MCP via mcporter, free, no key. `mcporter call exa...` |
| Results inside one platform | that platform's own search | `twitter search "q"`, `bili search "q"`, `opencli reddit search "q"`, Xueqiu `search_stock` |
| A site with **no** search API | Exa with a site filter | `site:v2ex.com <query>` |

Key rule: **don't fake a search a platform doesn't offer.** V2EX's public API has no
full-text search endpoint, so its `search()` deliberately returns a pointer to Exa
`site:v2ex.com` (or the site's own `?q=` page) rather than inventing one. Exa is the
universal search fallback for any site whose own search is missing or blocked.

Exa is preferred over generic keyword search because it's *semantic* (AI-ranked),
free, and key-less via MCP — the cheapest good search available.

## RSS — the lowest-friction subscription

For "subscribe to this / tell me when it updates," RSS via **feedparser** is the
standard. Zero config, pure Python. The channel matches any URL containing `/feed`,
`/rss`, `.xml`, or `atom`. When a site offers a feed, prefer it over scraping the
HTML page — it's structured, stable, and cheap. (Agent-Reach health-checks
feedparser; the actual polling/notify loop is the agent's to build on top.)

## Video & podcast transcripts

The common ask "summarize this video/podcast" is really "get me the transcript,
then summarize." Two tiers:

### Subtitles (free, fast) — preferred when they exist
- **YouTube → yt-dlp.** `yt-dlp --dump-json URL` for metadata;
  `yt-dlp --write-sub --skip-download URL` for subtitles. Multi-language, no key.
  Requires a JS runtime (Deno out-of-the-box, or Node with `--js-runtimes`
  configured in yt-dlp's config).
- **Bilibili → OpenCLI** (`opencli bilibili subtitle …`). Note: **not yt-dlp** —
  Bilibili's risk-control 412-blocks yt-dlp. bili-cli covers search/detail without
  login; subtitles need the OpenCLI browser session.

### Audio → text (when no subtitles) — Whisper transcription
When a video/podcast has no usable subtitle track (e.g. Xiaoyuzhou podcasts),
transcribe the audio:
- Download audio, transcode/slice with **ffmpeg**, send to a **Whisper** provider
  (Groq — free key — or OpenAI).
- YouTube can also fall back to this path: yt-dlp pulls the audio, ffmpeg prepares
  it, Whisper transcribes. `doctor` surfaces transcription readiness (which Whisper
  providers are configured, whether ffmpeg is present).

Prefer subtitles when available — they're free and instant. Reach for Whisper only
when there's no subtitle track to pull.

## Clean the output

Whatever the mode, return signal not structure: transcripts as plain text, search
results trimmed to title + URL + snippet, feed items to title/link/summary. The raw
yt-dlp JSON or a 40-field search blob is mostly noise that burns tokens — strip it
before the model sees it (see Principle 5 in SKILL.md).
