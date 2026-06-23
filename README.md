# Star Alliance

A guild of AI agents — each member is a specialist with their own skill set, deployed to help
with specific kinds of work. Members share common skills and carry unique ones.

## How it works

```
star-alliance/
├── members/           ← guild roster (agent definitions)
│   ├── the-architect.md
│   ├── the-designer.md
│   ├── the-strategist.md
│   ├── the-translator.md
│   ├── the-engineer.md
│   └── the-quartermaster.md
├── <skill-name>/      ← shared skill pool (29 skills, each a directory with SKILL.md)
├── skillsmith/        ← the quartermaster's toolkit (manages skills + members)
├── VERSIONS.md        ← skill version registry
└── README.md          ← this file
```

**Skills** live at the repo root — each directory is one skill (a `SKILL.md` plus optional
`scripts/`, `references/`, `assets/`). All skills are shared property of the guild.

**Members** live in `members/` — each `.md` file is a Claude Code agent definition with a
system prompt and a curated `skills` list. Deploy a member by copying their file into your
project's `.claude/agents/` and installing their skills.

## The Roster

| Member | Role | Skills | Deploy When |
|---|---|---|---|
| **the Architect** | Systems design, domain modeling, database architecture | transactions-domain-model, db-rename-sweep, supabase, supabase-postgres-best-practices, cleanup | "design the system", "model the domain", "architect the database" |
| **the Designer** | UI/UX design, visual quality, brand kits, image-to-code | design-taste-frontend, high-end-visual-design, image-to-code, imagegen-frontend-web, imagegen-frontend-mobile, brandkit, minimalist-ui, industrial-brutalist-ui, impeccable, stitch-design-taste, gpt-taste, redesign-existing-projects | "design the UI", "make it look premium", "create a brand kit" |
| **the Strategist** | Multi-wave campaigns, bug workflows, performance | conquering-campaign, bug-fix-workflow, performance, strategies-review, vault-log-compliance, cleanup | "plan the campaign", "break this into waves", "run the bug workflow" |
| **the Translator** | Legal codex, law translation, multi-locale content | codex-law-translate, article-creator, obsidian-markdown | "load this law", "translate this law", "add translations" |
| **the Engineer** | Dev servers, knowledge graphs, tooling, output enforcement | dev-server, graphify, full-output-enforcement, cleanup | "open dev server", "generate a knowledge graph", "full output mode" |
| **the Quartermaster** | Skill management, syncing, upgrading, daily evolution | skillsmith, cleanup | "sync my skills", "upgrade a skill", "run the skill routine" |

### Shared skills

These skills appear across multiple members — they're the guild's common toolkit:

- `cleanup` — used by the Architect, Strategist, Engineer, and Quartermaster

### Unique skills

These skills belong to one member only — they define the member's specialty:

- `conquering-campaign` — the Strategist's campaign framework
- `codex-law-translate` — the Translator's legal pipeline
- `graphify` — the Engineer's knowledge graph engine
- `skillsmith` — the Quartermaster's management toolkit
- `brandkit`, `image-to-code`, `imagegen-*`, `impeccable`, etc. — the Designer's design arsenal

## Deploying a member

```sh
# 1. Copy the member's agent file into your project
cp members/the-architect.md ~/my-project/.claude/agents/

# 2. Install the member's skills to the device
python3 skillsmith/scripts/skill_sync.py apply --skill transactions-domain-model
python3 skillsmith/scripts/skill_sync.py apply --skill supabase
# ... or sync all at once

# 3. Invoke in Claude Code
@the-architect model the transaction domain for this project
```

## Recruiting a new member

1. Create `members/<name>.md` with the agent definition (see `members/README.md` for format).
2. List the skills they should carry in the `skills` frontmatter field.
3. Install any new skills they need via `skillsmith create`.
4. Update the roster table in this README.

## Skill versioning — every skill is upgradable

Every skill carries a **canonical version** under **`metadata.version`** in its `SKILL.md`
frontmatter. That field is the single source of truth; [`VERSIONS.md`](VERSIONS.md) is the
at-a-glance registry that mirrors it.

```yaml
---
name: my-skill
description: ...
metadata:
  version: 1.2.0      # ← canonical. Bump on every change.
---
```

**SemVer contract:**

| Bump | When |
|---|---|
| **PATCH** (`x.y.Z`) | Bugfix, wording tweak, doc clarification, script fix. No behavior change for the user. |
| **MINOR** (`x.Y.0`) | New mode / capability / flag, backward-compatible. Existing invocations keep working. |
| **MAJOR** (`X.0.0`) | Breaking workflow change. Rare. |

**On any skill change, in the same commit:**

1. Bump the skill's `metadata.version`.
2. Regenerate [`VERSIONS.md`](VERSIONS.md) (`python3 skillsmith/scripts/skill_registry.py write`).
3. If the skill keeps its own changelog (e.g. `cleanup`, `conquering-campaign`), add an entry there too.
4. Re-sync the on-device copy if the skill runs from `~/.claude/skills/` (a stale device copy
   silently runs old code — the `cleanup` §L24 lesson).

The **`skillsmith`** skill (the Quartermaster's toolkit) automates all of this —
`/skillsmith` sync / upgrade / create. See its `SKILL.md`.

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
| **frontmatter keys** | only `name`, `description`, `license`, `allowed-tools`, `metadata`, `compatibility` at the top level — hard. Put `version` (and any custom field) under `metadata`. |
| **description** | **≤ 1024 characters and no `<`/`>`** — hard. The validator rejects both. Keep it tight and trigger-focused. |
| **name** | kebab-case, ≤ 64 chars — hard. |
| **SKILL.md body** | **< 500 lines ideal** — soft. As you approach it, add a layer of hierarchy and push detail into `references/` with clear pointers rather than growing the body. |
| **SKILL.md body** | **keep well under ~10k words** — the Cowork installer rejects very large bodies. Bundled `references/`, `scripts/`, and `assets/` do **not** count toward this. |

The authoritative gate is **`skill-creator`'s `quick_validate.py` green** on every skill.
`skillsmith` runs it as part of `sync`/`create`; the one sanctioned failure is the external
`impeccable` (npx-managed).

## Registry

See [`VERSIONS.md`](VERSIONS.md) for the full skill → version table with word counts and Cowork
status (29 skills).