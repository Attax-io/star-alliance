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
- rdt-cli → pinned git commit (`pipx install --force 'git+…@<sha>'`); PyPI lags.

## Resolving a multi-backend channel

For a channel with an ordered backend list, probe each candidate, collect
`(backend, status, message)`, then resolve:

1. First backend with `ok` wins → set it active.
2. No `ok`? First `warn` wins (a fixable state with a prescription).
3. Only broken/timeout left → return `error` with the repair note.
4. None installed → `off` with the install recommendation.

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
