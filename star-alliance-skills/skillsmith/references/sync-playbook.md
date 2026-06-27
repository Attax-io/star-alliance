---
type: Document
timestamp: 2026-06-27T10:27:03Z
---

# Mode: sync — reconcile the repo with the on-device copies

Goal: the git repo (`Attax-io/star-alliance`) and the on-device copies (`~/.claude/skills` global,
`<cwd>/.claude/skills` project) agree — newer versions are installed where they run, device-ahead
work flows back to the repo, and intentional divergences are left alone.

## Step S1 — Survey

```sh
python3 skillsmith/scripts/skill_sync.py status   # versions across repo / global / project
python3 skillsmith/scripts/skill_sync.py plan     # bucketed recommendations
```

`plan` sorts every skill into a bucket:

| Bucket | Meaning | Action |
|---|---|---|
| **INSTALL** | in repo, absent (or older) on device | `apply --skill NAME --direction install` (repo→global) |
| **STAMP** | present on device but **unversioned**; repo carries the version | install repo→global so the device copy carries the stamp (safe — repo was seeded from the device + a version line) |
| **PUSH** | device version > repo version | the **upgrade flow** — review the diff, then push device→repo. Do NOT blind-overwrite; device may be a localized fork. |
| **ADD-TO-REPO** | on device, absent in repo | copy the device skill into the repo, then version it (`version: 1.0.0`) |
| **FORK** | intentional divergence | manual — see Step S3 |
| **OK** | same version both sides | nothing |

## Step S2 — Apply the clean cases

For INSTALL + STAMP (repo is the source of truth and content matches except the version line):

```sh
python3 skillsmith/scripts/skill_sync.py apply --skill NAME --dry   # preview the rsync
python3 skillsmith/scripts/skill_sync.py apply --skill NAME         # rsync -a --delete repo→global
```

`apply` mirrors the whole skill dir (excluding `.git`, `__pycache__`, `*.pyc`). Before a bulk STAMP
sweep, spot-check one: `diff -r repo/NAME global/NAME` should differ only by the `version:` line.

PUSH (device-ahead) is **not** a blind apply — the device copy may have diverged in content. Diff it,
decide whether it's a real upstream improvement or a local-only tweak (like a `dev-server` that
hardcodes a project name), and only then `apply --direction push` or hand-merge.

## Step S3 — Forks & externals (never blind-sync)

The `EXCEPTIONS` set in `skill_sync.py` (kept in step with this list):

| Skill | Why | How to update |
|---|---|---|
| **cleanup** | repo is a slim **Cowork stub** (`SKILL.md` + `references/mode-*.md`); device is the full **monolith** | "guts only": sync `scripts/`, re-extract each `### Mode:` section into `references/mode-*.md`, refresh `landmines.md`, surgically update the stub's tables. Never replace the stub with the monolith. |
| **conquering-campaign** | repo is the **Cowork-packaged edition** (lean description, version-history/anti-pattern in `references/`); device keeps the rich canonical | re-apply the lean packaging on top of the new device content; bump the repo PATCH |
| **impeccable** | **external**, self-updates via `npx impeccable` (~37 MB, own `.gitignore`) | refresh the repo copy *from the device* copy (`rsync` global→repo); never hand-edit; let its nested `.gitignore` drop generated/`node_modules` |

When adding a new fork/external, add it to `EXCEPTIONS` in the script **and** this table.

## Step S4 — Refresh the registry, conformity-close, commit

```sh
python3 skillsmith/scripts/skill_registry.py write   # regenerate VERSIONS.md
python3 skillsmith/scripts/skill_registry.py check   # confirm 0 hard violations
# Conformity-close (Invariant #8) — the Quartermaster's final gate. MUST pass before commit.
python3 build.py                                     # regenerate guild-data.* from all sources
python3 tools/conformity_check.py                          # FULL CONFORMITY (exit 0) or fix + re-run
git -C <repo> commit <scoped paths> && git -C <repo> push origin main   # scope to the skill + its regen; never blind `add -A` a co-mingled tree (§L27)
```

**Conformity-close (Invariant #8).** `tools/conformity_check.py` is read-only; it audits the whole repo for internal agreement + conformity with every logged `decision` (guild-data↔json parity, `meta.counts`, workflow gates/actors, member arsenal order, and the **K-invariant** skill dirs == `skills-meta.json` == generated skill ids). A sync that **added a skill to the repo** (ADD-TO-REPO) MUST also add its `skills-meta.json` entry + run `build.py`, or the K-check FAILS. Fix any contradiction before committing — never ship one.

## Notes / landmines

- **Unversioned ≠ absent.** A device skill can exist without a `version:` field (the STAMP bucket). The
  scripts distinguish these; don't read "STAMP" as "missing."
- **Version lives in `metadata.version`** (a top-level `version:` fails frontmatter validation). Vendored
  skills already carry `metadata.version`; `impeccable` is the external exception (top-level `version:`, the
  reader falls back to it). If a device skill arrives with a stray top-level `version:`, relocate it with
  `migrate_version.py` before registering.
- **The device copy is what `/<skill>` loads.** A repo-only edit does nothing until installed (the
  `cleanup` §L24 drift lesson — a stale global silently runs old code).
