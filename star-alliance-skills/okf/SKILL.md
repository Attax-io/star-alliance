---
name: okf
type: Skill
description: Keep the whole Star Alliance repo tidy and conformant to the Open Knowledge Format (OKF v0.1) — one concept per markdown file, each carrying a `type:` frontmatter, cross-linked, with non-knowledge files swept and placed by concept-path. The Quartermaster's repo-hygiene standard. Use when the user says 'tidy the repo', 'OKF', 'keep it clean', 'make it OKF-conformant', 'run the OKF audit', 'fix frontmatter', or after any campaign that left new files behind. Pairs with star-alliance-language (the reader half).
metadata:
  version: 1.2.0
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
  | matches | → concept-path | safety |
  |---|---|---|
  | `STRATEGIST-*.md`, `AUDIT-*.md` | `docs/` | **safe** (inert, free to move) |
  | `gen-*.cjs` / `gen-*.py` | `tools/generators/` | review |
  | `build.py`, `conformity_check.py`, `install.py`, `log_event.py`, `member_level.py`, `build_guild_log.py` | `tools/` | review |
  | `*.json` data, `guild-data.js` | `data/` | review |
- **Unclassified** — no rule; left alone (advisory only).

`safety` is the upgrade's safety contract: **safe** = nothing references it, a mover
relocates it freely; **review** = reached by hardcoded paths (hooks in
`.claude/settings.json`, `build.py`, `serve.cjs`, the dashboard, sibling generators),
so relocation demands a **path-rewrite sweep** — a gated Architecture Build, never a
blind `git mv`. `--layout --fix` moves the **safe** class only and defers the rest.
The single source of truth for the taxonomy is `LAYOUT_PINNED` + `LAYOUT_RULES` in
`scripts/okf_audit.py`.

## How you work

1. **Audit.** `python3 star-alliance-skills/okf/scripts/okf_audit.py`
   — reports every governed `.md` that lacks frontmatter or a `type:` field.
   Add `--json` for a machine report, `--staged` for a pre-commit pass, `--path P`
   to scope to one file/subtree.
2. **Fix (migrate-first).** `okf_audit.py --fix` rewrites non-conformant files to
   baseline: injects a `type:` derived from the path (`SKILL.md`→Skill,
   `star-alliance-members/*`→Member, `index.md`→Index, `log.md`→Log,
   `README.md`→Readme, else Document) and a `timestamp:` when it has to create a
   fresh block. **Idempotent** — safe to re-run. Always run this *before* arming
   the gate so it can never lock the guild out of its own docs.
3. **Enrich (by hand or by doer).** Baseline conformance is just `type:`. Raise
   value by adding `title`, `description`, `tags`, and **cross-links** between
   related concepts. Hand bulk enrichment to a doer weapon (`summon.py minimax-m3`)
   — drafting a one-line `description` for 50 files is doer-grade.
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
- **1.1.0** — Declared canonical: **OKF is the Star Alliance Language**, the guild's single knowledge format — Quartermaster-produced, read by every member via [[star-alliance-language]]. The `skill_registry.py` generator now emits OKF frontmatter on `VERSIONS.md`, so the whole repo (members, skills, docs, registries) audits 100% conformant.
- **1.0.0** — Initial release. The producer half of the guild knowledge standard (OKF v0.1): one concept per file, `type:` frontmatter, cross-links, audit + `--fix`.

