---
type: Readme
timestamp: 2026-06-27T10:27:03Z
---

# Star Alliance

A guild of AI agents — each member is a specialist with their own skill set, deployed to help
with specific kinds of work. Members share common skills and carry unique ones.

> **STOP RULE:** guild work is frozen after the 2026-07 Supabase migration until Lex Council
> ships. Bugfixes ≤30 minutes only; new ideas become `guild.findings` rows (`sa findings add`).

## How it works

The guild's **source of truth is a Supabase database** — the `guild` schema in the
"Lex Council Pro" project: 128 skills, 10 members, full activity history, findings, and the
device registry. This repo is the working copy and read cache Claude Code loads.

```
star-alliance/
├── star-alliance-members/  ← guild roster (member cards; pushed to guild.members)
├── star-alliance-skills/   ← shared skill pool (each dir a SKILL.md; pushed to guild.skills)
│   └── skillsmith/         ← the quartermaster's toolkit (manages skills + members)
├── bin/sa                  ← the bridge CLI: init/pull/push/seed/flush/log/list/findings/dash/doctor
├── workflows.json · data/domains.json · star-alliance-arsenal/models.json  ← file-truth configs
├── VERSIONS.md             ← skill version registry
├── docs/SECOND-MAC-SETUP.md ← day-1 card for a new device
└── README.md               ← this file
```

The bridge is **`bin/sa`**, a single-file stdlib Python CLI. It authenticates with the
publishable key (`~/.config/star-alliance/config.json`) plus a `guild_agent` JWT in the macOS
Keychain. The `guild_agent` role is fenced to the `guild` schema — it cannot touch the app's
`public` schema and cannot DELETE. The dashboard is generated live by `sa dash` (the old
`build.py`/`guild-data.js` pipeline is retired to `.retired/2026-07-supabase-migration/`).

**Skills** live in `star-alliance-skills/` — each subdirectory is one skill (a `SKILL.md` plus
optional `scripts/`, `references/`, `assets/`). All skills are shared property of the guild.
`sa pull` materializes them into `~/.claude/skills` and the repo dirs; `sa push` sends edits back.

**Members** live in `star-alliance-members/` — each `.md` file is a Claude Code agent definition
with a system prompt and a curated `skills` list. Consumer repos (like Lex Council) get members
materialized into their `.claude/agents/` via `sa pull` — no copying by hand, no MCP server.

## The Roster

| Member | Role | Skills | Deploy When |
|---|---|---|---|
| **The Butler** | Orchestrator — takes orders, routes work to other members | members-formation | Any request — The Butler decides who handles what |
| **The Architect** | Systems design, domain modeling, database architecture | transactions-domain-model, db-rename-sweep, supabase, supabase-postgres-best-practices | "design the system", "model the domain", "architect the database" |
| **The Developer** | Writing code, fixing bugs, implementation, dev servers, tooling, knowledge graphs | bug-fix-workflow, db-rename-sweep, dev-server, graphify, supabase, supabase-postgres-best-practices, full-output-enforcement, obsidian-markdown | "write the code", "fix this bug", "implement this feature", "open dev server", "generate a knowledge graph" |
| **The Designer** | UI/UX design, visual quality, brand kits, image-to-code | design-taste, design-language, motion-design, image-to-code, imagegen-frontend, impeccable | "design the UI", "make it look premium", "create a brand kit" |
| **The Strategist** | Multi-wave campaigns, deep multi-model planning, bug workflows, performance | ultra-brainstorming, conquering-campaign, storm-investigation, bug-fix-workflow, performance, strategies-review, vault-log-compliance | "plan the campaign", "break this into waves", "ultra-brainstorm this", "run the bug workflow" |
| **The Interpreter** | Legal codex, law translation, multi-locale content | codex-law-translate, article-creator, obsidian-markdown | "load this law", "translate this law", "add translations" |
| **The Herald** | Marketing, growth, demand generation — content/SEO, brand, email, social/paid | growth-marketing, article-creator, imagegen-frontend, storm-investigation | "plan our marketing", "we need leads", "fix our positioning", "go to market" |
| **The Merchant** | Investment analysis, trading strategies, market research, portfolio management | market-recon, trading-strategy, portfolio-risk, storm-investigation | "analyze this investment", "build a trading strategy", "research this market" |
| **The Quartermaster** | Skill management, syncing, upgrading, daily evolution | skillsmith, guild-log, cleanup, storm-investigation | "sync my skills", "upgrade a skill", "run the skill routine" |

### Member levels

Each member carries a **craft-depth level** — a meter of arsenal depth + specialty, **decoupled
from standing** (the Butler leads regardless of tier). It's *earned* by an objective checklist
computed from the guild database (XP/levels are DB views, surfaced by `sa dash`) and
*conferred* by the Quartermaster, recorded in the guild log.
The standard and the promotion procedure live in
[`docs/archive/STRATEGIST-MEMBER-LEVELING.md`](docs/archive/STRATEGIST-MEMBER-LEVELING.md) and the Quartermaster's manual
[`skillsmith/references/member-leveling.md`](star-alliance-skills/skillsmith/references/member-leveling.md);
operate it with `python3 member_level.py report | promote`.

| Tier | Members |
|---|---|
| **Master** | The Strategist |
| **Elite** | The Designer |
| **Advanced** | The Quartermaster · The Herald · The Developer · The Architect · The Merchant |
| **Intermediate** | The Interpreter |
| **Foundational** | The Butler |

The thinnest arsenal (the Butler) sits at Foundational by design — that's the "who's lagging"
signal. `member_level.py report` shows each member's exact gap to the next tier.

### Shared skills

These skills appear across multiple members — they're the guild's common toolkit:

- `weapon-utility` — carried by **every** member; teaches each how to wield their weapons (the AI models)
- `star-alliance-language` — carried by **every** member; the read side of the guild's knowledge language, **OKF** (the *Star Alliance Language*). Its producer half, `okf`, is the Quartermaster's alone.
- `supabase`, `supabase-postgres-best-practices`, `db-rename-sweep` — The Architect and The Developer
- `bug-fix-workflow` — The Developer and The Strategist
- `obsidian-markdown` — The Developer and The Interpreter
- `article-creator` — The Interpreter and The Herald
- `imagegen-frontend` — The Designer and The Herald (the Herald briefs its `brand` mode; the Designer forges)
- `storm-investigation` — The Strategist, The Merchant, The Quartermaster, and The Herald

> `cleanup` is no longer shared — hygiene is the Quartermaster's alone. A skill rides on a member
> only when it builds that member's craft; the universal `weapon-utility` is the one exception.

### Unique skills

These skills belong to one member only — they define the member's specialty:

- `members-formation` — The Butler's routing method: form the team, decide parallel vs. sequential
- `ultra-brainstorming` — The Strategist's multi-model super-planning hub: many minds in, one plan out
- `conquering-campaign` — The Strategist's campaign framework
- `codex-law-translate` — The Interpreter's legal pipeline
- `graphify` — The Developer's knowledge graph engine (folded in from the retired Engineer)
- `skillsmith` — The Quartermaster's management toolkit
- `growth-marketing` — The Herald's four-mode marketing engine (content/SEO, brand, email, social/paid)
- `market-recon`, `trading-strategy`, `portfolio-risk` — The Merchant's read-only trading crafts (the read, the plan, the book)
- `image-to-code`, `imagegen-frontend`, `impeccable`, etc. — The Designer's design arsenal (`imagegen-frontend`'s `brand` mode shared with The Herald)

## Deploying a member

```sh
# 1. From the consumer project (e.g. Lex Council), pull from the guild database
python3 bin/sa pull        # materializes members → .claude/agents/ and skills → ~/.claude/skills

# 2. Invoke in Claude Code
@the-architect model the transaction domain for this project
```

New device? See [`docs/SECOND-MAC-SETUP.md`](docs/SECOND-MAC-SETUP.md).

## Recruiting a new member

1. Create `star-alliance-members/<name>.md` with the agent definition (see `star-alliance-members/README.md` for format).
2. List the skills they should carry in the `skills` frontmatter field.
3. Install any new skills they need via `skillsmith create` (from `star-alliance-skills/skillsmith/`).
4. `python3 bin/sa push` so the new member lands in the guild database.
5. Update the roster table in this README.

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
4. `sa push` the change to the guild database, then `sa pull` on other devices — a stale
   device copy silently runs old code (the `cleanup` §L24 lesson).

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
status (129 skills).