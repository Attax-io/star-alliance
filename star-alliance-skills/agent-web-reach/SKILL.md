---
name: agent-web-reach
metadata:
  version: 1.0.0
type: Skill
description: "Give an agent reliable internet reach — pull content from platforms that normally block agents. Channels: YouTube + Bilibili (subtitles/transcripts), Twitter/X, Reddit, LinkedIn, Xiaohongshu, Xueqiu, V2EX, RSS, GitHub, generic web, Exa semantic search, podcast (Whisper) transcription, plus browser cookie extraction. Trigger on 'get this youtube transcript', 'summarize this video', 'scrape this reddit thread', 'pull this tweet', 'search twitter without the API', 'read this blocked page', 'this page returns 403/login wall', 'subscribe to this RSS', 'what does this xiaohongshu note say', 'read this bilibili video'. This is the access layer: how to REACH and clean content. Use market-recon for financial-data synthesis and relationship-intel for people/account research — they consume reach, they are not it."
---

# Agent Web Reach

When an agent is asked to "go look at this," half the platforms it needs say no:
YouTube hides subtitles behind a JS runtime, Twitter's API is paid, Reddit 403s
anonymous requests, Xiaohongshu and Bilibili demand login or trip risk-control,
and the rest hand back a wall of HTML tags. Each platform has its own toll booth —
a paid API, a block to bypass, a login to ride, or noisy data to clean. This skill
is the doctrine for picking the right access technique per platform, getting in
cheaply, and returning clean text.

Distilled from Agent-Reach (Panniantong/agent-reach): a *capability layer*, not a
wrapper. It selects, installs, health-checks, and routes the backend; the agent
then calls the upstream tool directly. Backends change generation-to-generation
(yt-dlp was the Bilibili backend until risk-control 412-blocked it; it was swapped
for bili-cli with zero user action) — so the durable asset is the *strategy*, not
the command string.

## What this is

- A map of **which access technique each platform needs** and **when** (free vs
  paid, open vs blocked, anonymous vs login-required, raw vs needs-cleaning).
- A routing discipline: **ordered backends** (preferred ▸ fallback), real
  health-probing, cookie/auth handling, and graceful degradation.
- The cheap-and-clean path: free open-source backends, no API fees, token-frugal
  output.

## What this is not

- **Not a browser-automation / "operate the page" tool.** Reach is read-and-search.
  Logging in inside a flow, submitting forms, multi-account isolation, captcha/
  risk-control hand-off — that is browser automation (e.g. BrowserAct), out of scope.
- **Not the analysis layer.** Reach delivers clean content; market-recon synthesizes
  financial/market data and relationship-intel profiles people and accounts. They
  *consume* reach.
- **Not a paid-API integration.** The whole point is the free, open-source path.

## Principles

### 1. Match the platform to its access class, not to a habit
Every platform falls into one of four access classes, and the class dictates the
technique. **Open** (web→Jina Reader, RSS→feedparser, YouTube→yt-dlp, GitHub→gh,
V2EX/Xueqiu→public API) — just read. **Paid-API-avoided** (Twitter/X) — ride a
cookie-auth CLI instead of paying. **Block-bypassed** (Bilibili, Reddit) — the
obvious tool is actively blocked, so you need the one that still works.
**Login-required** (Reddit, Xiaohongshu, Twitter search, LinkedIn detail) — no
anonymous path exists; every backend rides a logged-in session. Misclassifying is
the root error: trying yt-dlp on Bilibili (412), or expecting an anonymous Reddit
`.json` (403). See `references/channels.md` for the full table.

### 2. Order backends preferred ▸ fallback; switching = reorder, not rewrite
A platform is an *ordered candidate list*, not a single tool: `twitter` =
twitter-cli ▸ OpenCLI ▸ bird; `bilibili` = bili-cli ▸ OpenCLI ▸ search-API;
`xiaohongshu` = OpenCLI ▸ xiaohongshu-mcp ▸ xhs-cli. Probe in order; the **first
fully-usable** backend wins. Critically, `ok` beats `warn`: an installed-but-
unauthenticated twitter-cli must not block a fully-working OpenCLI behind it. When
an access route dies, you reorder the list — you do not rewrite the caller.

### 3. Existence is not health — really execute the probe
`shutil.which()` finds a stale venv shim that cannot run (classic after a system
Python upgrade: pip/uv/pipx installs break, `which` passes, `exec` raises
FileNotFoundError pointing at the shim). Always run a side-effect-free probe
(`--version` / `status`) and classify into **missing** (not installed) / **broken**
(installed, won't exec → reinstall prescription) / **timeout-or-error** (runs but
misbehaves) / **ok**. A non-zero exit can still be a healthy tool reporting normal
business state — twitter-cli exits non-zero with `not_authenticated`, gh exits
non-zero when simply unauthenticated. Never grade those as broken. See
`references/health-probing.md`.

### 4. Cookies are the universal key — handle them locally and as a throwaway
Login-walled platforms are unlocked by cookies, and the doctrine is uniform:
browser login → Cookie-Editor "Export → Header String" → hand to the agent (simpler
and more reliable than QR scan). Or auto-extract from the local browser
(rookiepy/browser_cookie3). Two non-negotiables: **(a) store credentials only
locally** (`~/.agent-reach/config.yaml`, file mode 600 — doctor flags wider perms),
never upload; **(b) use a burner account** — scripted cookie calls risk detection
and a ban, so never the main account. Reddit/Twitter from blocked networks
(mainland China) also need a residential proxy (~$1/mo). See
`references/auth-and-cookies.md`.

### 5. Clean at the edge — return signal, not structure
A reached page is worthless as a tag-soup or a 40-field API blob. Read web through
Jina Reader (`https://r.jina.ai/URL`) to get Markdown, not HTML. For verbose JSON
APIs (Xiaohongshu, Xueqiu), strip to the load-bearing fields — id/title/body/author/
engagement/images-as-URLs/tags/comments — before it reaches the model; the raw
response is mostly structural redundancy that burns tokens. Truncate long bodies
(e.g. 200 chars for list previews). Clean output is part of "reach," not a later step.

### 6. Pick search by surface, not by reflex
Three different search surfaces: **whole-web semantic** → Exa (free via mcporter
MCP, no key); **inside one platform** → that platform's own search (twitter search,
bili search, opencli reddit search, Xueqiu stock search); **a site with no search
API** → fall back to Exa with `site:example.com`. V2EX, for instance, has no public
search endpoint — route it through Exa rather than faking one. See
`references/search-rss-and-transcripts.md`.

### 7. Degrade loudly with a prescription, never silently
When nothing is usable, say exactly what's wrong and the one command that fixes it —
not three half-relevant hints. Report the *first fixable* candidate's prescription.
Surface a working fallback while still carrying the broken preferred backend's repair
note (e.g. "served by search-API; [preferred backend down] reinstall bili-cli with…").
`agent-reach doctor` is the single source of truth for what's live and which backend
is currently serving each channel. Always run it first when reach misbehaves.

## References

- `references/channels.md` — every platform → access class, backend list, what it
  unlocks, and when each is needed. Start here to pick a channel.
- `references/auth-and-cookies.md` — cookie export/extraction flow, local-only
  storage + 600 perms, burner-account rule, proxies, OpenCLI browser-session reuse.
- `references/search-rss-and-transcripts.md` — Exa vs in-platform search, RSS,
  YouTube/Bilibili subtitles, podcast Whisper transcription.
- `references/health-probing.md` — missing/broken/timeout/ok classification, the
  stale-venv trap, multi-backend resolution, the doctor report.
