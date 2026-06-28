---
type: Readme
title: Star Alliance Desktop Installer
description: Prebuilt Tauri DMG and install steps for synced devices.
timestamp: 2026-06-28T00:00:00Z
---

# Star Alliance — Desktop Installer

Prebuilt Tauri desktop app, committed so any synced device can install without a build.

## Install (Apple Silicon Mac only)

1. `git pull`
2. Double-click `Star-Alliance_0.1.0_aarch64.dmg`
3. Drag **Star Alliance** to Applications
4. Launch from Launchpad / Spotlight

> **Architecture:** this DMG is `aarch64` (Apple Silicon, M1–M4). It will **not** run on
> Intel Macs, Windows, or Linux. For those, build from source:
> `cd desktop && npm install && npm run tauri build`
> — the fresh installer lands in `desktop/src-tauri/target/release/bundle/`.

## Updating this installer

After a new `npm run tauri build`, copy the regenerated DMG here and bump the filename
version so old/new don't collide:

```sh
cp "desktop/src-tauri/target/release/bundle/dmg/Star Alliance_<ver>_aarch64.dmg" \
   "desktop/installers/Star-Alliance_<ver>_aarch64.dmg"
```
