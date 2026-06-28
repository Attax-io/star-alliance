---
type: Document
title: Auth and Cookies
description: Cookie export/extraction, local-only storage, burner accounts, proxies, and browser-session reuse for agent-web-reach.
timestamp: 2026-06-28T00:00:00Z
---

# Auth & Cookies — unlocking login-walled platforms

Login-required platforms (Reddit, Xiaohongshu, Twitter search, Xueqiu full data,
Bilibili subtitles) are unlocked by a **cookie that proves a logged-in session**.
The technique is uniform across platforms; only the cookie names differ.

## The standard cookie flow (preferred over QR scan)

1. Log into the site in a normal browser (e.g. `x.com`, `xiaohongshu.com`).
2. Install **Cookie-Editor** (Chrome/Firefox/Edge).
3. Click it → **Export → Header String**.
4. Hand the string to the agent. It runs e.g.
   `agent-reach configure twitter-cookies <string>`.

This is simpler and more reliable than QR-scan login. For a server agent that
can't see your browser, this is the *only* path — export locally, paste over.

### Per-platform cookie specs

| Platform | Domain(s) | Cookies that matter |
|---|---|---|
| Twitter/X | `.x.com`, `.twitter.com` | `auth_token`, `ct0` |
| Xiaohongshu | `.xiaohongshu.com` | all (grabbed as one header string) |
| Bilibili | `.bilibili.com` | `SESSDATA`, `bili_jct` |
| Xueqiu | `.xueqiu.com` | all — `xq_a_token` + session cookies |
| Reddit | `reddit.com` | `reddit_session` (manual-write path for Chrome 127+) |

## Auto-extraction from the local browser

On a desktop, cookies can be lifted silently from Chrome/Firefox/Edge/Brave/Opera
via `rookiepy` (Rust, more stable) with a `browser_cookie3` fallback:
`agent-reach configure --from-browser chrome`. Extraction *only* succeeds when the
session token is present (e.g. Xueqiu's `xq_a_token`); failures are swallowed so an
agent without a local browser keeps working on the public path.

## OpenCLI — cookies you never touch

OpenCLI drives the user's *real* Chrome through a bridge extension + local daemon,
reusing whatever sessions are already logged in. If you've browsed Reddit /
Xiaohongshu / Twitter in that Chrome, the agent can read them with **zero**
per-platform cookie work. Desktop-only (no headless); on a server it never probes
alive, so the channel falls through to its headless/cookie backend (e.g.
xiaohongshu-mcp). One nuance: `opencli doctor` *auto-starts* the daemon (a side
effect) — health checks must use `opencli daemon status` (a pure query) instead.
A "disconnected" extension is not dead: its service worker sleeps and wakes on the
first real command.

## Two non-negotiable safety rules

1. **Credentials stay local.** Cookies/tokens live only in
   `~/.agent-reach/config.yaml` with file mode **600** (owner-only). `doctor` flags
   the file when group/other can read it (`chmod 600 ~/.agent-reach/config.yaml`).
   Never upload, never echo into logs.
2. **Use a burner account, never the main one.** Scripted/API-shaped calls with a
   cookie can be detected and **get the account banned or limited**. A dedicated
   throwaway also caps the blast radius if the cookie leaks (a cookie equals full
   login rights). This applies to every cookie-auth platform (Twitter, Xiaohongshu…).

## Proxies — for IP-blocked, not login-blocked, platforms

Some platforms block by server IP / region rather than by login. From a blocked
network (e.g. mainland China reaching Reddit or Twitter), add a residential proxy
(~$1/month). This is orthogonal to cookies: you may need *both* a logged-in cookie
*and* a proxy. Local desktops usually need neither a proxy nor much config.

## Auth state is a spectrum, not a boolean

A tool can be **installed-and-authed** (`ok`), **installed-but-unauthed** (`warn` —
twitter-cli `not_authenticated`, gh unauthenticated, rdt-cli not logged in), or
**not installed** (`off`). Treat *unauthed* as a fixable warn with a login
prescription — not a failure, and never as a reason to block a different backend
that is fully working. (See `health-probing.md` for the resolution order.)
