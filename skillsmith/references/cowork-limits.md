# Cowork limits — the always-on invariant

Every skill in the repo is kept installable through the Cowork skill installer. Three limits:

| Limit | Rule | Hardness | Source |
|---|---|---|---|
| **frontmatter keys** | only **`name`, `description`, `license`, `allowed-tools`, `metadata`, `compatibility`** at the top level. Anything else (`version`, `trigger`, `argument-hint`, `user-invocable`, …) is rejected as an unexpected key. **Version goes in `metadata.version`; put any other custom field under `metadata` too.** | **HARD** | `skill-creator/scripts/quick_validate.py` (the Agent Skills spec validator) |
| **description** | **≤ 1024 characters** AND **no `<` or `>`** (angle brackets are rejected outright) | **HARD** — the validator rejects both. The local Claude Code loader is lenient, but Cowork/upload runs the validator. | same |
| **name** | kebab-case (`^[a-z0-9-]+$`, no leading/trailing/double hyphen), **≤ 64 chars** | HARD | same |
| **SKILL.md body** | **< 500 lines ideal** ("go longer if needed", but add hierarchy + `references/` pointers as you approach it) | soft | `skill-creator` authoring guidance |
| **SKILL.md body** | **keep well under ~10k words** | soft (empirical) — the Cowork installer rejects very large bodies; a **15,342-word** file is *known* to fail. Exact threshold unverified. | `cleanup` §1.9.0 field data |

**The acceptance gate is `quick_validate.py` green**, not any single limit. Run it across the repo
(`skillsmith` sync/upgrade do this) and read every failure — a "version moved" pass that still trips
on a stray `trigger:` or a `<` in the description is not done. The one sanctioned exception is the
external `impeccable` (npx-managed, ships top-level `version:`/`argument-hint`/`user-invocable`) —
don't hand-edit it; treat its validator failure as expected.

## What does NOT count

Bundled **`references/`, `scripts/`, `assets/`** files do **not** count toward the body limits —
they load on demand. **This is the escape hatch:** when a `SKILL.md` gets large, move the verbose
recipes into `references/*.md` and leave a one-line `Read references/X.md` pointer in the body. The
installer only weighs the slim body; the model pulls the detail when it needs it.

Worked examples in this repo: `cleanup` (slim stub + `references/mode-*.md`), `conquering-campaign`
(core router + `references/*-playbook.md`).

## Status classification (used by `skill_registry.py`)

| Status | Meaning |
|---|---|
| `✓ lean` | within all limits |
| `○ large` | over the 500-line ideal or >5k words — installable, trim-when-convenient |
| `⚠ body>10k` | near/over the empirical Cowork word ceiling — lean-pass candidate (extract to references/) |
| `✗ desc>1024` | **HARD violation** — description too long. Trim now. |
| `✗ desc<>` | **HARD violation** — description contains `<` or `>`. Replace them (e.g. `>=3` → `3+`, `<500` → `under 500`). |

## Fixing violations

- **`✗ desc>1024`** — trim the description to ≤1024 chars. Keep the trigger phrases and the "when to
  use" essence (authoring guidance says ~100 words and a little "pushy"); drop mechanics prose that
  already lives in the body. Validate with `skill_registry.py check NAME`.
- **`✗ desc<>`** — replace every `<`/`>` in the description (`>=3` → `3+`, `<500 lines` → `under 500
  lines`, `<Component>` → `Component`). The validator rejects angle brackets outright.
- **`⚠ body>10k`** — extract verbose recipe sections into `references/*.md`, leaving `Read
  references/X.md` pointers. **Never cut routing/decision logic to hit a number** — if safe
  extraction doesn't get under, stop and flag it as a lean-pass candidate.
- **`○ large`** — optional. Same extraction technique when convenient.
