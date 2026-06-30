---
type: Document
title: Channels
description: Platform-to-access-class map for agent-web-reach — which backend each platform needs and when.
timestamp: 2026-06-28T00:00:00Z
---

# Channels — platform → access class, backend, when

Each platform is a *channel*: a `can_handle(url)` matcher + an ordered backend list
+ a tier. Tier encodes setup cost: **0** = zero-config (works on install),
**1** = needs a free key or a login/cookie, **2** = optional complex setup.

Pick a channel by matching the URL/intent, then read down the backend list and use
the first one `doctor` reports as serving it.

## The four access classes

| Class | Why a special technique is needed | Platforms |
|---|---|---|
| **Open** | Free, unblocked, public — just read | web, RSS, YouTube, GitHub (public), V2EX, Xueqiu (public quotes), Exa |
| **Paid-API-avoided** | Official API costs money; ride a cookie CLI instead | Twitter/X |
| **Block-bypassed** | The obvious tool is actively blocked; use the one that still works | Bilibili (yt-dlp 412'd), Reddit (anon .json 403'd) |
| **Login-required** | No anonymous path exists; every backend rides a session | Reddit, Xiaohongshu, Twitter search, LinkedIn detail |

A platform can be in two classes at once (Reddit is both block-bypassed *and*
login-required). Misclassifying is the #1 failure: yt-dlp on Bilibili returns 412;
an anonymous Reddit `.json` returns 403.

## Channel table

| Channel | Tier | Backends (preferred ▸ fallback) | Unlocks | When / notes |
|---|---|---|---|---|
| **web** | 0 | Jina Reader | Read any URL as clean Markdown | Universal fallback (`can_handle` = always true). `curl https://r.jina.ai/URL`. No key. |
| **youtube** | 0 | yt-dlp | Video metadata + subtitles/transcript, search | Needs a JS runtime (Node or Deno) — Deno works out of the box, Node needs `--js-runtimes` in yt-dlp config. Audio→text needs ffmpeg + a Whisper key. |
| **rss** | 0 | feedparser | Read any RSS/Atom feed | `can_handle` matches `/feed`, `/rss`, `.xml`, `atom`. Pure Python. |
| **github** | 0 | gh CLI | Public repos + search; auth unlocks private/issues/PR/fork | Unauthenticated is a normal *warn*, not an error. `gh auth login` to unlock more. |
| **exa_search** | 0 | Exa via mcporter (MCP) | Whole-web semantic search | Search-only (`can_handle` = false). Free, no API key, auto-configured via MCP. |
| **v2ex** | 0 | V2EX public API | Hot topics, node browse, topic+replies, user info | No public *search* endpoint — route search through Exa `site:v2ex.com`. May need proxy. |
| **xueqiu** | 1 | Xueqiu API (login cookie) | Stock quotes, search, hot posts, hot stocks | Public quotes work anonymously; full data needs `xq_a_token` cookie. `agent-reach configure --from-browser chrome`. |
| **twitter** | 1 | twitter-cli ▸ OpenCLI ▸ bird (legacy) | Read tweet; search, timeline, long-form Article, user, thread | Paid-API-avoided. twitter-cli needs `auth_token`+`ct0` cookies (or browser login to x.com). `ok` only when `twitter status` says `ok: true`; `not_authenticated` is a *warn*. |
| **bilibili** | 1 | bili-cli ▸ OpenCLI ▸ search-API | Search/hot/ranking/video-detail (bili-cli, no login); subtitles (OpenCLI) | Block-bypassed: **yt-dlp removed** (risk-control 412 in every config tried, 2026-06). bili-cli works login-free; upstream unmaintained since 2026-03. |
| **reddit** | 1 | OpenCLI ▸ rdt-cli | Search, read posts + comments | **No zero-config path**: anon `.json` 403'd, official API approval-gated since 2025-11. Every backend needs login. rdt-cli pins a git commit (PyPI lags). China needs proxy. |
| **xiaohongshu** | 1 | OpenCLI ▸ xiaohongshu-mcp ▸ xhs-cli | Search, read notes, comments, feed | Login-required. Backend order auto-splits by environment: OpenCLI needs desktop Chrome (never probes alive on a server) → xiaohongshu-mcp (self-contained headless + QR) takes over there. xhs-cli unmaintained since 2026-03. |
| **xiaoyuzhou** | 1 | groq-whisper + ffmpeg | Podcast audio → transcript | Needs ffmpeg + a free Groq API key + the install-time transcribe script. |
| **linkedin** | 2 | linkedin-scraper-mcp ▸ Jina Reader | Profile / company / job search (MCP); public pages (Jina) | Jina Reader reads public pages with zero setup; full detail needs the MCP server + mcporter config. |

## Picking a channel

1. **Have a URL?** Find the channel whose `can_handle` matches the domain. Falls
   through to **web** (Jina Reader) for anything unmatched.
2. **Searching, not reading a URL?** Whole-web → **exa_search**; one platform →
   that platform's own search; a site with no search API (e.g. V2EX) → Exa with
   `site:`.
3. **Read which backend is live** from `agent-reach doctor` — it names the
   *current* backend per channel, since the list reorders over time.

## Why these backends (current selection, periodically re-verified)

- **web → Jina Reader**: free, no key, returns Markdown not HTML.
- **twitter → twitter-cli**: stable cookie-auth search; OpenCLI is the browser-
  session fallback. Avoids the paid X API entirely.
- **reddit → OpenCLI (desktop)**: anon blocked + API approval-gated leave only the
  logged-in route; rdt-cli imports cookies as the server/existing-install fallback.
- **bilibili → bili-cli**: yt-dlp is 412-blocked; bili-cli searches+reads without
  login. (yt-dlp still serves YouTube — it just no longer serves Bilibili.)
- **xiaohongshu → OpenCLI**: zero-friction reuse of an already-logged-in desktop
  Chrome; xiaohongshu-mcp covers servers via its own headless browser.
- **exa → Exa**: AI semantic search, MCP-mounted, free, no key.

These are *current* picks based on live testing. When a route dies, the list is
reordered; `doctor` always reports the route now in use.
