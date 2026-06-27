---
name: guild-sync
description: "The Quartermaster's device-parity craft — one sweep that proves every surface where the on-device install can fall behind the repo source of truth still matches, then reconciles what drifted. Covers four surfaces: skills (repo vs ~/.claude/skills, delegating the compare + install to skillsmith, never re-implementing it), scheduled-tasks (every entry points at the canonical repo path, not a stale rename), members (roster committed), and config (repo .claude tracked, runtime state ignored). Runs guild/device_sync.py read-only by default and only flags HARD drift; --reconcile installs repo-ahead skills via skillsmith. Use to answer 'is the device current' or to close the Sync Rotation workflow. Triggers: 'sync the repo with claude', 'is the device up to date', 'what needs syncing', 'device parity', 'sync rotation', 'check for drift'. Differentiate from skillsmith (skills-only versioning, delegated to here) and guild-conformity (repo-internal cross-reference agreement, not repo-to-device install state)."
metadata:
  version: 1.0.0
type: Skill

---
# Guild Sync — the Quartermaster's device-parity craft

You are the keeper of parity. The repo is the source of truth; the device is what
actually runs. A skill, a scheduled task, or a config that has drifted on the device
silently runs old behaviour — the most dangerous kind of bug, because nothing errors.
This craft is one disciplined sweep across every surface where that drift can hide,
and the reconciliation that closes it.

It is **not** `skillsmith` and **not** `guild-conformity` — it sits between them:

- `skillsmith sync` reconciles **skills only** (repo ↔ `~/.claude/skills`). Guild-sync
  **delegates** the skill surface straight to it — it never re-implements the version
  compare or the install.
- `guild-conformity` proves the repo agrees **with itself** (cross-references between
  members, skills, domains, workflows, the log, and the generated `guild-data`). It says
  nothing about whether the **device** matches the repo.
- Guild-sync owns the **repo → device** axis across **all** surfaces, and reports drift
  as one board.

## The four surfaces

| Surface | Source of truth | Device target | Drift class |
|---|---|---|---|
| **skills** | `star-alliance-skills/<id>/` | `~/.claude/skills/<id>/` | HARD — repo-ahead silently runs old code |
| **scheduled-tasks** | repo path is canonical | `~/.claude/scheduled-tasks/*` | HARD — a stale-rename path kills the daily routine |
| **members** | `star-alliance-members/*.md` | (repo-only roster → dashboard; no device agents) | INFO — uncommitted roster drift |
| **config** | repo `.claude/` hooks + settings | (project-local; not copied to global) | INFO — runtime `state/*` ignored |

Only **skills** and **scheduled-tasks** are HARD: they are the surfaces that actually
install to a global device location and can run stale. Members and config are
**repo-local** — they render to the dashboard or load in-place, so their only "drift"
is being uncommitted, which is informational, not a stale-runtime risk.

## Run it

```sh
python3 guild/device_sync.py --check       # read-only sweep, parity board (default)
python3 guild/device_sync.py --reconcile   # + install repo-ahead skills to device via skillsmith
```

`--check` exits non-zero **only** on HARD drift (skills repo-ahead, or a scheduled-task
pointing at a dead `claude-skills` path). `--reconcile` runs the skillsmith install for
each repo-ahead skill, then re-reports clean.

## Workflow

1. **Sweep** — run `guild/device_sync.py --check`. Read the board: each surface is `OK`,
   `DRIFT` (HARD), `INFO`, or `SKIP`.
2. **Reconcile skills** — if the skills row is `DRIFT`, run `--reconcile` (delegates to
   `skillsmith skill_sync.py apply --direction install`). **Never blind-overwrite** a
   documented fork (`cleanup`, `conquering-campaign`) or external (`impeccable`) — the
   skillsmith plan already buckets those as `FORK`; handle them per `skillsmith`'s
   `sync-playbook.md`, not here.
3. **Repoint stale tasks** — if the scheduled row is `DRIFT`, edit the offending
   `~/.claude/scheduled-tasks/*` entry to the canonical repo path (this is a device-config
   edit, not a repo commit). The 1.1.8 rename class — `claude-skills → star-alliance` —
   is exactly what this catches.
4. **Surface INFO rows** — uncommitted members/config are reported, not auto-committed;
   the operator decides whether they are in-flight work or real drift.
5. **Close** — re-run `--check`; on `✓ PARITY`, hand to **`guild-conformity`** for the
   repo-internal close, then the Butler reports. This is the **Sync Rotation** workflow.

## Invariants

1. **Delegate skills to skillsmith.** This skill orchestrates the *sweep*; the skill
   install itself is always `skillsmith`'s `skill_sync.py`. Do not duplicate version logic.
2. **Forks + externals are never blind-overwritten.** `--reconcile` only installs the
   plan's `INSTALL` bucket; `FORK`/external skills are skillsmith's manual flow.
3. **HARD vs INFO is fixed.** Only skills + scheduled-tasks (global-device install
   surfaces) gate the exit code. Repo-local surfaces report but never fail the sweep.
4. **Runtime state is not drift.** `.claude/state/*` is ignored — it is per-turn runtime,
   not config.
5. **Read-only by default.** `--check` writes nothing; only `--reconcile` mutates the
   device, and only via skillsmith.

## Changelog

| Version | Date | Summary |
|---|---|---|
| **1.0.0** | 2026-06-27 | Initial release. Device-parity orchestrator over four surfaces (skills/scheduled-tasks/members/config), `guild/device_sync.py` primitive (read-only `--check`, `--reconcile` delegates skill install to skillsmith), and the `Sync Rotation` workflow it closes. Owned by the-quartermaster. Sits between `skillsmith` (skills-only, delegated to) and `guild-conformity` (repo-internal). |
