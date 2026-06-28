---
type: Readme
timestamp: 2026-06-27T10:27:03Z
---

# Star Alliance

A guild of AI agents — each member is a specialist with their own skill set, deployed to help
with specific kinds of work. Members share common skills and carry unique ones.

## How it works

```
star-alliance/
├── star-alliance-members/  ← guild roster (agent definitions)
│   ├── the-architect.md
│   ├── the-butler.md
│   ├── the-designer.md
│   ├── the-developer.md
│   ├── the-herald.md
│   ├── the-merchant.md
│   ├── the-quartermaster.md
│   ├── the-strategist.md
│   └── the-translator.md
├── star-alliance-skills/  ← shared skill pool (95 skills, each a directory with SKILL.md)
│   ├── algorithmic-trading-chan/
│   ├── article-creator/
│   ├── bug-fix-workflow/
│   ├── ...
│   └── skillsmith/        ← the quartermaster's toolkit (manages skills + members)
├── build.py              ← one generator: skills + agents + *-meta.json → guild-data.js
├── skills-meta.json      ← hand-edited per-skill icon/blurb/level/triggers
├── members-meta.json     ← hand-edited per-member presentation (color, avatar, weapons, …)
├── domains.json          ← hand-edited project domains (linked skills + members)
├── guild-data.js         ← auto-generated data (const GUILD), loaded by index.html
├── index.html · app.css · app.js  ← the cosmic "command center" dashboard (buildless)
├── build_guild_log.py · log_event.py · guild-log.json  ← the guild-log pipeline
├── VERSIONS.md            ← skill version registry
└── README.md              ← this file
```

The dashboard is **buildless** — open `index.html` directly in a browser (or serve the folder).
It loads one generated file, `guild-data.js`, which `build.py` regenerates from the sources above.

**Skills** live in `star-alliance-skills/` — each subdirectory is one skill (a `SKILL.md` plus
optional `scripts/`, `references/`, `assets/`). All skills are shared property of the guild.

**Members** live in `star-alliance-members/` — each `.md` file is a Claude Code agent definition
with a system prompt and a curated `skills` list. Deploy a member by copying their file into
your project's `.claude/agents/` and installing their skills.

## The Roster

| Member | Role | Skills | Deploy When |
|---|---|---|---|
| **The Butler** | Orchestrator — takes orders, routes work to other members | members-formation | Any request — The Butler decides who handles what |
| **The Architect** | Systems design, domain modeling, database architecture | transactions-domain-model, db-rename-sweep, supabase, supabase-postgres-best-practices | "design the system", "model the domain", "architect the database" |
| **The Developer** | Writing code, fixing bugs, implementation, dev servers, tooling, knowledge graphs | bug-fix-workflow, db-rename-sweep, dev-server, graphify, supabase, supabase-postgres-best-practices, full-output-enforcement, obsidian-markdown | "write the code", "fix this bug", "implement this feature", "open dev server", "generate a knowledge graph" |
| **The Designer** | UI/UX design, visual quality, brand kits, image-to-code | design-taste, design-language, motion-design, image-to-code, imagegen-frontend, impeccable | "design the UI", "make it look premium", "create a brand kit" |
| **The Strategist** | Multi-wave campaigns, deep multi-model planning, bug workflows, performance | ultra-brainstorming, conquering-campaign, storm-investigation, bug-fix-workflow, performance, strategies-review, vault-log-compliance | "plan the campaign", "break this into waves", "ultra-brainstorm this", "run the bug workflow" |
| **The Translator** | Legal codex, law translation, multi-locale content | codex-law-translate, article-creator, obsidian-markdown | "load this law", "translate this law", "add translations" |
| **The Herald** | Marketing, growth, demand generation — content/SEO, brand, email, social/paid | growth-marketing, article-creator, imagegen-frontend, storm-investigation | "plan our marketing", "we need leads", "fix our positioning", "go to market" |
| **The Merchant** | Investment analysis, trading strategies, market research, portfolio management | market-recon, trading-strategy, portfolio-risk, storm-investigation | "analyze this investment", "build a trading strategy", "research this market" |
| **The Quartermaster** | Skill management, syncing, upgrading, daily evolution | skillsmith, guild-log, cleanup, storm-investigation | "sync my skills", "upgrade a skill", "run the skill routine" |

### Member levels

Each member carries a **craft-depth level** — a meter of arsenal depth + specialty, **decoupled
from standing** (the Butler leads regardless of tier). It's *earned* by an objective checklist
`build.py` computes from the repo and *conferred* by the Quartermaster, recorded in the guild log.
The standard and the promotion procedure live in
[`docs/STRATEGIST-MEMBER-LEVELING.md`](docs/STRATEGIST-MEMBER-LEVELING.md) and the Quartermaster's manual
[`skillsmith/references/member-leveling.md`](star-alliance-skills/skillsmith/references/member-leveling.md);
operate it with `python3 member_level.py report | promote`.

| Tier | Members |
|---|---|
| **Master** | The Strategist |
| **Elite** | The Designer |
| **Advanced** | The Quartermaster · The Herald · The Developer · The Architect · The Merchant |
| **Intermediate** | The Translator |
| **Foundational** | The Butler |

The thinnest arsenal (the Butler) sits at Foundational by design — that's the "who's lagging"
signal. `member_level.py report` shows each member's exact gap to the next tier.

### Shared skills

These skills appear across multiple members — they're the guild's common toolkit:

- `weapon-utility` — carried by **every** member; teaches each how to wield their weapons (the AI models)
- `star-alliance-language` — carried by **every** member; the read side of the guild's knowledge language, **OKF** (the *Star Alliance Language*). Its producer half, `okf`, is the Quartermaster's alone.
- `supabase`, `supabase-postgres-best-practices`, `db-rename-sweep` — The Architect and The Developer
- `bug-fix-workflow` — The Developer and The Strategist
- `obsidian-markdown` — The Developer and The Translator
- `article-creator` — The Translator and The Herald
- `imagegen-frontend` — The Designer and The Herald (the Herald briefs its `brand` mode; the Designer forges)
- `storm-investigation` — The Strategist, The Merchant, The Quartermaster, and The Herald

> `cleanup` is no longer shared — hygiene is the Quartermaster's alone. A skill rides on a member
> only when it builds that member's craft; the universal `weapon-utility` is the one exception.

### Unique skills

These skills belong to one member only — they define the member's specialty:

- `members-formation` — The Butler's routing method: form the team, decide parallel vs. sequential
- `ultra-brainstorming` — The Strategist's multi-model super-planning hub: many minds in, one plan out
- `conquering-campaign` — The Strategist's campaign framework
- `codex-law-translate` — The Translator's legal pipeline
- `graphify` — The Developer's knowledge graph engine (folded in from the retired Engineer)
- `skillsmith` — The Quartermaster's management toolkit
- `growth-marketing` — The Herald's four-mode marketing engine (content/SEO, brand, email, social/paid)
- `market-recon`, `trading-strategy`, `portfolio-risk` — The Merchant's read-only trading crafts (the read, the plan, the book)
- `image-to-code`, `imagegen-frontend`, `impeccable`, etc. — The Designer's design arsenal (`imagegen-frontend`'s `brand` mode shared with The Herald)

## Deploying a member

```sh
# 1. Copy the member's agent file into your project
cp star-alliance-members/the-architect.md ~/my-project/.claude/agents/

# 2. Install the member's skills to the device
python3 star-alliance-skills/skillsmith/scripts/skill_sync.py apply --skill transactions-domain-model
python3 star-alliance-skills/skillsmith/scripts/skill_sync.py apply --skill supabase
# ... or sync all at once

# 3. Invoke in Claude Code
@the-architect model the transaction domain for this project
```

## Recruiting a new member

1. Create `star-alliance-members/<name>.md` with the agent definition (see `star-alliance-members/README.md` for format).
2. List the skills they should carry in the `skills` frontmatter field.
3. Install any new skills they need via `skillsmith create` (from `star-alliance-skills/skillsmith/`).
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

The **`skillsmith`** skill (The Quartermaster's toolkit) automates all of this —
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
status (95 skills).