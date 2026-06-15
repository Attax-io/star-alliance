# claude-skills

Atta's personal Claude Code / Claude Agent skill library. Each top-level directory is one skill
(a `SKILL.md` plus optional `scripts/`, `references/`, `assets/`). Some are distributed onward
through the Cowork skill installer; all are kept in sync with the on-device copies under
`~/.claude/skills/` (global) and per-project `.claude/skills/`.

## Versioning — every skill is upgradable

Every skill carries a **canonical version** in the top-level `version:` field of its `SKILL.md`
frontmatter. That field is the single source of truth; [`VERSIONS.md`](VERSIONS.md) is the
at-a-glance registry that mirrors it.

```yaml
---
name: my-skill
version: 1.2.0      # ← canonical, top-level. Bump on every change.
description: ...
---
```

**SemVer contract:**

| Bump | When |
|---|---|
| **PATCH** (`x.y.Z`) | Bugfix, wording tweak, doc clarification, script fix. No behavior change for the user. |
| **MINOR** (`x.Y.0`) | New mode / capability / flag, backward-compatible. Existing invocations keep working. |
| **MAJOR** (`X.0.0`) | Breaking workflow change. Rare. |

**On any skill change, in the same commit:**

1. Bump the skill's top-level `version:`.
2. Update its row in [`VERSIONS.md`](VERSIONS.md).
3. If the skill keeps its own changelog (e.g. `cleanup`, `conquering-campaign`), add an entry there too.
4. Re-sync the on-device copy if the skill runs from `~/.claude/skills/` (a stale device copy
   silently runs old code — the `cleanup` §L24 lesson).

## `vendored` / `external` skills

A few skills come from upstream and carry an extra `metadata.version` (the upstream author's
version) for provenance:

- `performance`, `supabase`, `supabase-postgres-best-practices` — **vendored**; the top-level
  `version:` is *our* tracked version, seeded from the upstream `metadata.version`.
- `impeccable` — **external**, self-updates via `npx impeccable`; we vendor a working copy but do
  not hand-edit it. Refresh from the device copy rather than editing in place.

When refreshing a vendored skill from upstream, reconcile both versions and update `VERSIONS.md`.

## Cowork-friendly & installable

Every skill is kept installable through the Cowork skill installer. The constraints (and each
skill's measured word/line counts + status) live in [`VERSIONS.md`](VERSIONS.md):

| Limit | Rule |
|---|---|
| **description** | **≤ 1024 characters** — hard. Frontmatter validation rejects anything longer, so keep the description tight and trigger-focused (the authoring guidance is ~100 words anyway). |
| **SKILL.md body** | **< 500 lines ideal** — soft. As you approach it, add a layer of hierarchy and push detail into `references/` with clear pointers rather than growing the body. |
| **SKILL.md body** | **keep well under ~10k words** — the Cowork installer rejects very large bodies (a 15,342-word file is known to fail). Bundled `references/`, `scripts/`, and `assets/` do **not** count toward this — that's why the stub pattern (slim `SKILL.md` + `references/mode-*.md`) works (see `cleanup`). |

**Keeping a skill installable as it grows:** when the body gets large, extract the verbose recipes
into `references/*.md` and leave a one-line `Read references/X.md` pointer in `SKILL.md`. The model
loads them on demand; the installer only weighs the slim body. `cleanup` and `conquering-campaign`
are the worked examples.

Current status: 0 hard violations. `conquering-campaign` sits just over the ~10k-word figure
(within the 500-line spec) — flagged in `VERSIONS.md` as a lean-pass candidate. The image/design
skills (`graphify`, `image-to-code`, `imagegen-*`, `brandkit`) are over the 500-line ideal but well
under the word ceiling — installable, trim-when-convenient.

## Registry

See [`VERSIONS.md`](VERSIONS.md) for the full skill → version table with word counts and Cowork
status (28 skills).
