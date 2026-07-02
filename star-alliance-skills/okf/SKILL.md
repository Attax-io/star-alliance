---
name: okf
type: Skill
description: Keep the whole Star Alliance repo tidy and conformant to the Open Knowledge Format (OKF v0.1) — one concept per markdown file, each carrying a `type:` frontmatter, cross-linked, with non-knowledge files swept and placed by concept-path. The Quartermaster's repo-hygiene standard. Use when the user says 'tidy the repo', 'OKF', 'keep it clean', 'make it OKF-conformant', 'run the OKF audit', 'fix frontmatter', or after any campaign that left new files behind. Pairs with star-alliance-language (the reader half).
metadata:
  version: 1.4.0
---

# OKF — Open Knowledge Format hygiene

The **producer** half of the guild's knowledge standard. The Quartermaster runs
this to keep the *entire* repo tidy and conformant to the **Open Knowledge Format
(OKF v0.1)** — Google Cloud's vendor-neutral spec for representing knowledge as a
directory of markdown files. Its companion is **star-alliance-language**, the
*reader* half every other member uses to consume what this skill produces.

> **OKF *is* the Star Alliance Language** — the guild's one knowledge standard from here
> on. The Quartermaster **produces** in it (this skill); every member **reads** it back via
> [[star-alliance-language]]. One format spoken across every member, skill, and doc.

> The OKF graph here is for **hand-tidied repo knowledge** — one concept per file,
> curated cross-links. For **auto-building a graph from non-OKF or raw inputs**
> (raw code, papers, images, video), see [[graphify]] to construct the first map,
> then hand it off to OKF for curation.

## What OKF requires (the whole spec, one screen)

1. **One concept per file.** A markdown file = one concept (a member, a skill, a
   workflow, a doc, a log entry, a runbook). The **file path is the concept's
   identity** — `star-alliance-members/the-quartermaster.md` *is* the Quartermaster
   concept.
2. **YAML frontmatter, one required field — `type:`.** Everything else is optional
   but recommended: `title`, `description`, `resource`, `tags`, `timestamp`.
   ```yaml
   ---
   type: Member
   title: The Quartermaster
   description: Keeper of the arsenal — skills, versions, guild log.
   tags: [member, skills]
   timestamp: 2026-06-27T00:00:00Z
   ---
   ```
3. **Markdown body for everything else.** Plain GFM. No new runtime, no SDK.
4. **Cross-link with normal markdown links.** `[the customers table](/tables/customers.md)`
   turns the directory into a graph richer than the parent/child tree. Wikilinks
   (`[[name]]`) are honoured too (the guild already uses them in memory).
5. **Optional `index.md` and `log.md`.** `index.md` gives progressive disclosure
   as an agent walks a hierarchy; `log.md` carries chronological history.

> OKF is **minimally opinionated**: it defines the *interoperability surface*
> (the `type:` contract), not the content model. The guild decides what types
> exist (Member, Skill, Workflow, Document, Index, Log, Readme, …).

## The standard, applied to THIS repo

- **Every governed `.md` opens with frontmatter carrying `type:`.** Enforced
  mechanically by the `okf-gate` PreToolUse hook — a Write/Edit that would leave a
  governed file non-conformant is blocked with the exact fix line.
- **Governance scope = the whole repo**, minus: `node_modules/`, `.git/`,
  `__pycache__/`, virtualenvs, `scratchpad/`, routine-log dumps, and the vendored
  `impeccable/` skill (a fork that carries its own multi-agent mirrors). The single
  source of truth for scope lives in `scripts/okf_audit.py` (`EXCLUDE_*`); the hook
  mirrors it.
- **Non-markdown files are tidied too** — not by frontmatter (you can't put YAML in
  a `.py`), but by *placement and pruning*: files live under the concept-path they
  belong to, orphans/dead artifacts are swept, and the move is recorded in the
  guild log. The markdown is the knowledge surface; the rest of the repo is kept
  orderly around it. **This is no longer prose-only — `okf_audit.py --layout`
  enforces it** (see the layout taxonomy below).

## Layout taxonomy — where each kind of file belongs

The frontmatter audit governs markdown *content*; the **`--layout`** audit governs
*placement* of every loose file at the repo **root**. A file is classified one of
three ways:

- **Pinned** — legitimately at root: `README.md`, `CLAUDE.md`, `VERSIONS.md` (the
  registry), and the dashboard trio `index.html` / `app.js` / `app.css` (served from
  root). Never flagged.
- **Concept-path target** — belongs under a folder by kind:
  | matches | → concept-path | base tag |
  |---|---|---|
  | `STRATEGIST-*.md`, `AUDIT-*.md` | `docs/` | safe |
  | `gen-*.cjs` / `gen-*.py` | `tools/generators/` | review |
  | `build.py`, `conformity_check.py`, `log_event.py`, `member_level.py`, `build_guild_log.py` | `tools/` | review |
  | `*.json` data, `guild-data.js` | `data/` | review |
- **Unclassified** — no rule; left alone (advisory only).

**Safety is computed, never guessed.** The table's *base tag* is only a ceiling: the
audit runs `git grep` to count inbound references (markdown links, `see X.md`
pointers, code comments, JSON detail strings) and a file is **safe** only when its
base tag is `safe` *and* it has **zero** inbound refs. Any reference — or a `review`
base tag — yields **review**: relocation would strand a link or a hardcoded path, so
it needs a **path/link-rewrite sweep**, a gated Architecture Build, never a blind
`git mv`. (This is why a referenced `STRATEGIST-*.md` shows up as review, not safe.)
`--layout --fix` moves the **safe** class only and defers the rest.
The single source of truth for the taxonomy is `LAYOUT_PINNED` + `LAYOUT_RULES` in
`scripts/okf_audit.py`.

## Output-path convention — where a skill's generated artifacts belong

Skills that write reports, state, diagnostics, or generated files were each
inventing their own output location by hand. The layout taxonomy above covers
where a *root file* belongs; this section extends it to where a **skill's own
generated output** belongs, reusing the exact same `LAYOUT_RULES`
target-directory taxonomy so the two conventions never diverge — one taxonomy
for placement, one for output, sourced from the same constants.

### What `tools/resolve_output.py` does

`resolve(skill, kind, cwd=None)` resolves the correct folder for a given
**skill name** + **output kind** via a 4-step order (mirrors
`tools/resolve_vault.py`'s env → config → convention → scaffold shape):

1. **`OUTPUT_DIR` env override** — wins outright if set.
2. **Nearest `.claude/output.json`** walking up — a per-kind override; if the
   config has an entry for the requested kind, that wins.
3. **OKF layout convention** — imports `LAYOUT_RULES` directly from
   `star-alliance-skills/okf/scripts/okf_audit.py` (adds its `scripts/` dir to
   `sys.path` and imports live) rather than duplicating it, so `report` and
   `diagnostic` resolve to `docs/`, `generated-script` resolves to
   `tools/generators/`, and `data`/`log` resolve to `data/` — all read live
   from `LAYOUT_RULES`'s `target_dir` values. One genuinely new kind, `state`,
   resolves to `.claude/state/` (no `LAYOUT_RULES` equivalent, since `.claude/`
   is dotfile-excluded from the root layout audit).
4. **Unclassified kind** — falls back to a proposed `.claude/output/<kind>/`
   scratch path; `--scaffold` writes (or merges into) `.claude/output.json`.

### Resolved folders for the six known kinds

| kind | resolved folder |
|---|---|
| `report` | `docs/` |
| `diagnostic` | `docs/` |
| `generated-script` | `tools/generators/` |
| `data` | `data/` |
| `state` | `.claude/state/` |
| `log` | `data/` |

### How `.claude/output.json` is structured

```json
{
  "kinds": {
    "report": "docs/",
    "diagnostic": "docs/",
    "generated-script": "tools/generators/",
    "data": "data/",
    "state": ".claude/state/",
    "log": "data/"
  },
  "default_kind": "data",
  "notes": "..."
}
```

A `kinds` sub-dict (kind → relative folder), an optional `default_kind`
(fallback kind when the requested one is missing but a generic default is
acceptable), an optional `default_folder`, and a `notes` field. Mirrors
`.claude/vault.json`'s per-target-project override shape but for output
routing instead of vault-log routing.

### Which skills use it

As of this pass, `tools/resolve_output.py` and `.claude/output.json` exist as
the shared convention and reference implementation, but **no skill script has
been wired to call it yet** — six candidates were audited and each was found
already conformant by its own existing convention, so none were changed:

- `cleanup/scripts/errors_cleanup.py` and `cleanup/scripts/consolidate_code.py`
  write ephemeral scratch to `/tmp/*` (a live Lex Council dev-server session
  artifact, correctly scoped outside this repo) plus already-correctly-placed
  durable outputs (`CONSOLIDATION-CANDIDATES.md`,
  `references/routine-ledger/99-synthesis.md`).
- `skillsmith/scripts/routine_watchdog.py` writes its log to the
  already-correct `star-alliance-skills/skillsmith/routine-logs/watchdog.log`.
- `skillsmith/scripts/routine_scan.py` is read-only and writes only to its
  explicit `--out FILE` flag or stdout — never a hardcoded convention path.
- `session-mining/scripts/session_map.py` and
  `session-mining/scripts/mine_sessions.py` both follow the same `--out
  FILE`-or-stdout pattern.
- `law-harvest` is prose-only (no script) instructing the Architect/Translator
  to write `logs/harvests/YYYY-MM-DD.md` inside the TARGET project (e.g. Lex
  Council), not this repo — a future candidate for a `resolve_output`-style
  per-project resolver mirroring `resolve_vault.py`'s pattern, but out of
  scope for a mechanical wiring pass since there is no script to edit.

### Already-conformant reference examples (exempt, left as-is)

Two systems are explicitly out of scope for this convention — they are the
pattern this file mirrors, not systems to migrate onto it:

- **`guild-log`** — `data/guild-log.json` is the fixed, correct, single
  source of truth; never touch it.
- **`vault-log-writer`** — its `tools/resolve_vault.py` is already the
  correct per-target-project resolution pattern that `tools/resolve_output.py`
  was modeled on.

## How you work

1. **Audit.** `python3 star-alliance-skills/okf/scripts/okf_audit.py`
   — reports every governed `.md` that lacks frontmatter or a `type:` field.
   Add `--json` for a machine report, `--staged` for a pre-commit pass, `--path P`
   to scope to one file/subtree.
   **Scaffold a new concept file** with
   `python3 star-alliance-skills/okf/scripts/okf_new.py PATH --type TYPE
   [--title T] [--description D] [--tags a,b,c] [--force]`. Writes the
   frontmatter (type, optional title/description/tags, ISO-8601 UTC timestamp)
   plus a level-1 heading derived from `--title` or the filename stem, so
   nobody has to hand-type the opening. Refuses non-`.md` paths and existing
   files unless `--force` is set; refuses paths inside an excluded scope
   (e.g. `.claude/`).
2. **Fix (migrate-first).** `okf_audit.py --fix` rewrites non-conformant files to
   baseline: injects a `type:` derived from the path (`SKILL.md`→Skill,
   `star-alliance-members/*`→Member, `index.md`→Index, `log.md`→Log,
   `README.md`→Readme, else Document) and a `timestamp:` when it has to create a
   fresh block. **Idempotent** — safe to re-run. Always run this *before* arming
   the gate so it can never lock the guild out of its own docs.
3. **Enrich (by hand or by doer).** Baseline conformance is just `type:`. Raise
   value by adding `title`, `description`, `tags`, and **cross-links** between
   related concepts. **Find the backlog first** with
   `python3 star-alliance-skills/okf/scripts/okf_enrich.py` (or `--json` for
   machine output, `--missing title,description,tags` to narrow the subset) —
   it reports every governed `.md` that passes the baseline but is missing any
   of those three enrichment keys. Read-only by design and exits 0 always;
   never fails a build over missing metadata, only points at the work. Once
   the backlog is in hand, hand bulk enrichment to a doer weapon
   (`summon.py minimax-m3`) — drafting a one-line `description` for 50 files
   is doer-grade.
4. **Sweep non-md tidy (placement).** Run `okf_audit.py --layout` to list root files
   off their concept-path. `--layout --fix` relocates the **safe** class (via
   `git mv`); the **review** class is reported for a path-rewrite sweep (Architecture
   Build), never moved blind. Then prune orphaned/dead files (confirm first) and
   `guild-log` the moves.
5. **Verify the gate.** The `okf-gate` hook blocks any future non-conformant write.
   Confirm it's registered in `.claude/settings.json` under `PreToolUse`.
6. **Close out.** Run `dashboard-parity` if the change should show on the dashboard,
   then `guild-log` the work (a `chore`/`skill-upgrade` entry).

## Conformance contract (what `type:` lets the reader assume)

Because every governed file *guarantees* a `type:`, the reader skill
(**star-alliance-language**) never has to blind-read: it lists concepts by
frontmatter, filters by `type`, and walks cross-links. The gate is what makes that
guarantee real — producer and consumer share one contract, exactly as OKF intends
(producer/consumer independence: who writes ≠ who reads, the format is the bond).

## Don't

- Don't arm the gate before `--fix` migrates the baseline.
- Don't put frontmatter in non-markdown files — tidy those by placement, not YAML.
- Don't widen scope into `impeccable/` or `node_modules/` — they're vendored.
- Don't hand-bump the project version; `guild-log` the work and `build.py` does it.

## Changelog
- **1.4.0** — New shared output-path convention extending the layout taxonomy —
  `tools/resolve_output.py`'s `resolve()` (env -> `.claude/output.json`
  config -> OKF `LAYOUT_RULES` convention -> scaffold fallback, mirroring
  `resolve_vault.py`) + `.claude/output.json` (six kinds:
  report/diagnostic->`docs/`, generated-script->`tools/generators/`,
  data/log->`data/`, state->`.claude/state/`); audited six candidate skill
  scripts (cleanup's errors_cleanup.py/consolidate_code.py, skillsmith's
  routine_watchdog.py/routine_scan.py, session-mining's
  session_map.py/mine_sessions.py, law-harvest prose), found all already
  conformant by their own existing convention, wired none (documented why in
  the new §Output-path convention section); guild-log and vault-log-writer
  explicitly exempt as the reference patterns this convention mirrors; new
  capability, no breaking change -> MINOR.
- **1.3.0** — Two new helper scripts to ease day-to-day work, sitting alongside
  `okf_audit.py` and reusing its governance scope (drift-proof by construction):
  - **`scripts/okf_new.py`** — scaffolds a new OKF-conformant `.md` with
    frontmatter (`type`, optional `title`/`description`/`tags`, ISO-8601 UTC
    `timestamp`) and a level-1 heading derived from `--title` or the filename.
    Refuses non-`.md` paths, refuses existing files without `--force`, and
    refuses paths inside an excluded scope (`.claude/`, `node_modules/`, …).
    Wire it into step 1 (next to Audit) as the way to start a new concept.
  - **`scripts/okf_enrich.py`** — read-only enrichment backlog report: every
    governed `.md` that passes the baseline (has `type:`) but is missing any
    of `title` / `description` / `tags`. Imports `is_governed`, `iter_md`,
    `split_frontmatter`, `fm_has_type`, and the `EXCLUDE_*` constants from
    `okf_audit.py` so scope never drifts. `--json` for machine output,
    `--missing` to narrow the subset, exits 0 always (advisory — never fails
    a build). Wire it into step 3 (Enrich) as the way to **find** the backlog
    before drafting descriptions.
- **1.2.0** — **Placement is now enforced, not just promised.** Added the `--layout`
  audit + a declared layout taxonomy (`LAYOUT_PINNED` / `LAYOUT_RULES`) to
  `okf_audit.py`: it classifies every loose root file as pinned / concept-path-target
  / unclassified, with a **safe vs review** safety tag. `--layout --fix` relocates the
  safe class via `git mv`; the review class (path-referenced files) is deferred to a
  gated Architecture Build. Closes the long-standing gap where OKF claimed repo-wide
  tidiness but the tool only checked markdown frontmatter. The default frontmatter
  audit and the `okf-gate` hook are unchanged.
- **1.1.0** — Declared canonical: **OKF is the Star Alliance Language**, the guild's single knowledge format — Quartermaster-produced, read by every member via [[star-alliance-language]]. The `skill_registry.py` generator now emits OKF frontmatter on `VERSIONS.md`, so the whole repo (members, skills, docs, registries) audits 100% conformant.
- **1.0.0** — Initial release. The producer half of the guild knowledge standard (OKF v0.1): one concept per file, `type:` frontmatter, cross-links, audit + `--fix`.

