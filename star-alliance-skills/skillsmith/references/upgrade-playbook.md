---
type: Document
timestamp: 2026-06-27T10:27:03Z
---

# Mode: upgrade — bump a skill, keep it Cowork-installable

Goal: a change to a skill is shipped with its version bumped, the registry refreshed, the Cowork
limits still satisfied, and the device copy re-synced.

## Step U1 — Make the change

Edit the skill in the **repo** copy (the distribution source). If the skill is a documented fork
(`cleanup`, `conquering-campaign`), edit per its fork rules — see `sync-playbook.md` §S3.

## Step U2 — Bump the version (SemVer)

The canonical version is **`metadata.version`** in the frontmatter (a top-level `version:` is rejected by the frontmatter validator — see `cowork-limits.md`).

| Bump | When |
|---|---|
| **PATCH** `x.y.Z` | bugfix, wording, doc/relocation, description trim, packaging. No behavior change. |
| **MINOR** `x.Y.0` | new mode / capability / flag, backward-compatible. |
| **MAJOR** `X.0.0` | breaking workflow change. Rare. |

Also: if the body heading carries a `(vX.Y.Z)` stamp, update it. If the skill keeps a **§Changelog**
(like `cleanup`) or a **`references/version-history.md`** (like `conquering-campaign`), prepend an entry.

## Step U3 — Cowork-compliance check

```sh
python3 skillsmith/scripts/skill_registry.py check NAME
```

- **`✗ desc>1024`** (HARD) — trim the description to ≤1024 chars (keep triggers + "when to use"; drop
  mechanics that live in the body). Re-check.
- **`⚠ body>10k`** — extract verbose recipe sections to `references/*.md`, leaving `Read references/X.md`
  pointers in the body. **Never cut routing/decision logic to hit the number.** If safe extraction
  doesn't clear it, stop and leave it flagged — note it as a lean-pass candidate.
- **`○ large`** — optional trim; installable as-is.

See `cowork-limits.md` for the full rules and the extraction technique.

## Step U4 — Refresh the registry

```sh
python3 skillsmith/scripts/skill_registry.py write   # regenerate VERSIONS.md from live frontmatter
```

The registry row updates automatically from the new `version:` + measured counts.

## Step U5 — Re-sync the device, conformity-close, commit

```sh
python3 skillsmith/scripts/skill_sync.py apply --skill NAME --dry   # preview
python3 skillsmith/scripts/skill_sync.py apply --skill NAME         # install repo→global
# Conformity-close (Invariant #8) — the Quartermaster's final gate. MUST report FULL CONFORMITY before commit.
python3 build.py                                                    # regenerate guild-data.*
python3 tools/conformity_check.py                                         # exit 0, or fix the contradiction + re-run
git -C <repo> commit <scoped paths> && git -C <repo> push origin main   # scope to the skill + its regen; never blind `add -A` a co-mingled tree (§L27)
```

For a **fork** skill, the device copy is intentionally different — re-sync only the parts that should
flow (e.g. `cleanup` guts), not the whole dir. The script will `SKIP` forks; do them by hand.

## Quick recipes

- **"make X cowork-installable"** → `check X`; fix the reported violation (usually a desc trim or a
  references/ extraction); `write`; bump PATCH; re-sync.
- **"bump X to 2.0.0"** → set `version: 2.0.0` + changelog entry + `write` + re-sync. (MAJOR ⇒ confirm
  the change is genuinely breaking.)
- **"audit all skills"** → `skill_registry.py report` + `check` (no NAME) for the full picture.
