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

### Cookie-extraction library order — rookiepy preferred, browser_cookie3 fallback

The extractor (`cookie_extract.py: extract_all`) imports **rookiepy first, then
`browser_cookie3`**, and the order is deliberate. `rookiepy` is Rust-backed and far
more stable against the moving target of browser cookie encryption (Chrome's
v10/v11 app-bound `Cipher` changes break the pure-Python `browser_cookie3`
repeatedly). The fallback is auto: a bare `import rookiepy` failure drops to
`import browser_cookie3`, and only if *both* are missing does it raise — with a
prescription that recommends `pip install rookiepy` first. The two libraries return
different shapes (rookiepy → `list[dict]` with `name`/`value`/`domain` keys;
browser_cookie3 → a cookiejar of objects), so the extractor normalizes rookiepy's
dicts into `.name`/`.value`/`.domain` objects before the shared per-platform
matching loop runs. Don't hardcode one library; keep the import-order fallback so a
single broken install doesn't kill extraction.

Per-platform, the extractor only **saves a cookie set when its session token is
present**: Xueqiu is written to config only if the header string contains
`xq_a_token` (anonymous cookies are useless and would falsely report "configured"),
Bilibili requires `SESSDATA`, Twitter requires both `auth_token` and `ct0`. A
platform whose token is missing returns a *fixable* message ("login to x.com in
chrome first"), never a silent success.

### Session-bootstrap / anti-DDoS token (Xueqiu pattern)

Some platforms front their **public** API with an anti-DDoS layer (e.g. Akamai/
Alibaba `acw_tc`) that 4xx-rejects a cold request carrying no session cookie — even
on endpoints that need no login. The fix is a **homepage-visit bootstrap**: before
the first public-API call, GET the site homepage through a cookie-jar-backed opener
so the response's `Set-Cookie` plants the anti-DDoS token, then make the real API
call on the same opener.

Xueqiu (`channels/xueqiu.py: _ensure_cookies`) does exactly this as the **last** of
three cookie sources, in priority order:

1. Saved cookie string in `~/.agent-reach/config.yaml` (`xueqiu_cookie`).
2. Live browser cookies via rookiepy/browser_cookie3 (only if `xq_a_token` present).
3. **Homepage-visit fallback** — `GET https://xueqiu.com` on the shared
   `HTTPCookieProcessor` opener to pick up the `acw_tc` anti-DDoS cookie.

```python
# build ONE opener with a cookie jar; reuse it for bootstrap AND the API call
_cookie_jar = http.cookiejar.CookieJar()
_opener = urllib.request.build_opener(
    urllib.request.HTTPCookieProcessor(_cookie_jar))

def _ensure_cookies():
    if _load_cookies_from_config():   return   # logged-in path
    if _load_cookies_from_browser():  return   # logged-in path
    # public path: visit homepage so acw_tc anti-DDoS cookie lands in the jar
    req = urllib.request.Request("https://xueqiu.com", headers={"User-Agent": _UA})
    _opener.open(req, timeout=10)              # discard body — we only want the cookie
```

Key points: the bootstrap only yields the anti-DDoS token, **not** auth — it
unlocks public quote/search/hot endpoints but not login-walled data; and it must
share the *same* opener/jar as the subsequent calls, or the freshly-set cookie is
lost. Run it once and memoize (`_cookies_initialized`).

### Localhost proxy-bypass for MCP service checks

When probing a **local** MCP backend (e.g. xiaohongshu-mcp on
`http://localhost:18060/mcp`), build the request opener with an **empty
`ProxyHandler`** so the check is never routed through `HTTP_PROXY`/`HTTPS_PROXY`. An
agent on a blocked network legitimately sets a residential proxy for Reddit/Twitter
(below) — but localhost must bypass it, or the health check dies on a proxy that
can't reach `127.0.0.1`. Any HTTP answer (even a 405 to a GET) counts as "service
alive":

```python
opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))  # bypass proxy
try:
    opener.open(urllib.request.Request(_MCP_ENDPOINT, method="GET"), timeout=3)
    return True
except urllib.error.HTTPError:
    return True   # 405/404 — the service answered, it's up
except Exception:
    return False

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
