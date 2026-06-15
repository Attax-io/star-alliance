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

## Registry

See [`VERSIONS.md`](VERSIONS.md) for the full skill → version table (28 skills).
