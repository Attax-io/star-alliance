---
type: Document
title: Health Probing
description: Classifying backend health (missing/broken/timeout/ok), the stale-venv trap, multi-backend resolution, and the doctor report in agent-web-reach.
timestamp: 2026-06-28T00:00:00Z
---

# Health Probing — proving a backend actually works

The discipline that keeps reach reliable: never trust that a tool is usable just
because it's on PATH. Really run a cheap probe and classify the result.

## Why `which()` lies

`shutil.which(cmd)` only proves a file exists at that name. The classic failure:
after a system Python upgrade, a pip/uv/pipx-installed CLI's venv shim still passes
`which()`, but executing it raises `FileNotFoundError` pointing at the now-missing
interpreter behind the shebang. The tool *looks* installed and is completely broken.
So probing executes a **side-effect-free** command (`--version` or `status`) and
reads the real outcome.

## The four states

| Status | Meaning | Right response |
|---|---|---|
| **missing** | not on PATH | install prescription (`pipx install …`) |
| **broken** | exists, can't exec (`FileNotFoundError`/`OSError`, or shell exit 126/127) | *reinstall* prescription — `uv tool install --force <pkg>` / `pipx reinstall <pkg>` (a stale-venv repair, not a fresh install) |
| **timeout** | runs but hangs past the limit | retry once for transient; then report timeout. Don't retry missing/broken — they won't heal |
| **ok** | exits 0 with healthy output | use it |
| **error** | runs, exits non-zero, but tool is alive | inspect output — often a normal *business* state, not a defect |

## Non-zero exit ≠ broken

A non-zero exit can be a healthy tool reporting normal state. Read the *output*:
- `twitter status` exits non-zero with `not_authenticated` → tool is fine, just
  needs login → **warn** + login prescription (never *error*).
- `gh auth status` exits non-zero when simply unauthenticated → **warn**.
- rdt-cli logs network retries to *stderr* even on success → capture stdout
  separately so JSON parsing of `status --json` doesn't choke on the noise.

Grading these as "broken" would wrongly bury a usable backend.

## Per-backend prescription nuances

The reinstall hint must match how the tool ships, or it sends the user down the
wrong path:
- pip/pipx/uv CLIs → `uv tool install --force` / `pipx reinstall`.
- `gh` (brew/binary) → `brew reinstall gh`, not pipx.
- mcporter (npm) → `npm install -g mcporter`.
- bird → npm package `@steipete/bird` → `npm install -g @steipete/bird`, not pipx.
- rdt-cli → **git-commit-pinned**, not PyPI (see below).

### git-pin a tool whose PyPI release lags (rdt-cli)

When a tool's PyPI release trails its fixed upstream, **pin a specific git commit**
in the prescription instead of `pipx install rdt-cli`. rdt-cli
(`channels/reddit.py`) does this: PyPI only ships 0.4.1 while the working state is a
0.4.2 commit (upstream issue #10), so both the install and the *reinstall*
prescriptions name the SHA, and the broken-state hint is custom (the generic
pipx/uv reinstall would re-pull the stale PyPI build):

```python
_RDT_GIT_SOURCE = ("git+https://github.com/public-clis/rdt-cli.git"
                   "@5e4fb3720d5c174e976cd425ccc3b879d52cac66")
_RDT_BROKEN_HINT = (
    "rdt 命令存在但无法执行——通常是系统 Python 升级后 venv 解释器丢失。\n"
    "PyPI 版本落后，推荐用固定 git 源强制重装：\n"
    f"  pipx install --force '{_RDT_GIT_SOURCE}'")
```

rdt-cli also can't go through the shared `probe_command`: `rdt status --json` logs
network-retry noise to **stderr even on success (rc=0)**, so a merged stdout+stderr
capture breaks the JSON parse. It keeps a hand-written `subprocess.run` that captures
stdout *separately*, while still classifying exceptions by `probe` semantics —
`OSError`/exit 126/127 → broken (the git-pin reinstall hint), `TimeoutExpired` →
timeout.

### env-var-first config (xiaoyuzhou / Groq key)

Read a secret from its **environment variable first, then fall back to the
agent-reach config file** — never config-only. `channels/xiaoyuzhou.py` checks
`os.environ["GROQ_API_KEY"]` before `Config().get("groq_api_key")`, so a key exported
in the shell wins without a config write and an unset key is a fixable *warn* (with
the "register at console.groq.com → configure groq-key" prescription), not an error.

## Resolving a multi-backend channel

For a channel with an ordered backend list, probe each candidate, collect
`(backend, status, message)`, then resolve:

1. First backend with `ok` wins → set it active.
2. No `ok`? First `warn` wins (a fixable state with a prescription).
3. Only broken/timeout left → return `error` with the repair note.
4. None installed → `off` with the install recommendation.

This is a **two-loop** resolution, and the loop separation is the whole point: you
must collect *all* candidates first, then pick — returning on the first non-`None`
result would let an installed-but-unauthed backend (warn) early-out ahead of a
fully-working one (ok) sitting later in the list. Every multi-backend channel
(`twitter.py`, `bilibili.py`, `reddit.py`, `xiaohongshu.py`) uses this identical
shape:

```python
def check(self, config=None):
    self.active_backend = None
    findings = []                                   # collect EVERY candidate first
    for backend in self.ordered_backends(config):
        result = self._check(backend)               # (status, message) or None
        if result is None:
            continue                                # not installed → not a candidate
        findings.append((backend, *result))

    for wanted in ("ok", "warn"):                   # ok beats warn regardless of order
        for backend, status, message in findings:
            if status == wanted:
                self.active_backend = backend        # set the one ACTUALLY serving now
                return status, message

    if findings:                                    # only broken/timeout left
        return "error", "\n".join(m for _, _, m in findings)
    return "off", _install_recommendation           # none installed
```

A candidate probe returns `None` for "not installed" (so it drops out of contention
entirely), or `(status, message)` where `message` for a `warn`/`error` **carries the
reinstall/login hint** — e.g. bird's "npm install -g @steipete/bird", twitter-cli's
`export TWITTER_AUTH_TOKEN=…`. When a fallback serves but the preferred backend is
down, surface the fallback *and* carry the preferred backend's repair note so the
user can restore the better route (the second of the two rules below).

Two rules that prevent the common bugs:
- **`ok` beats `warn` regardless of order.** An installed-but-unauthed twitter-cli
  (warn) must not block a fully-working OpenCLI (ok) sitting behind it. Collect all
  candidates first, *then* pick — don't return on the first non-None result.
- **Carry the broken preferred backend's prescription even when a fallback serves.**
  e.g. "served by search-API; [preferred backend down] reinstall bili-cli with…" —
  so the user can restore the better route.

A channel must also set `active_backend` to the one actually serving right now
(`None` when nothing works), and a single misbehaving channel must never crash the
whole report — per-channel exceptions degrade to `error`.

## `doctor` — the single source of truth

`agent-reach doctor` runs every channel's `check()` and renders: zero-config
channels (✅ / needs-config / not-installed), active optional channels, an
`N/total available` count, a one-line "you can still unlock X, Y, Z" nudge, and a
config-permission security warning. Crucially it names the **current backend** per
channel — so when reach misbehaves, run `doctor` *first*: it tells you what's live,
what's broken, and exactly how to fix it, instead of guessing.
