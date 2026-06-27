---
name: okf
type: Skill
description: Keep the whole Star Alliance repo tidy and conformant to the Open Knowledge Format (OKF v0.1) — one concept per markdown file, each carrying a `type:` frontmatter, cross-linked, with non-knowledge files swept and placed by concept-path. The Quartermaster's repo-hygiene standard. Use when the user says 'tidy the repo', 'OKF', 'keep it clean', 'make it OKF-conformant', 'run the OKF audit', 'fix frontmatter', or after any campaign that left new files behind. Pairs with star-alliance-language (the reader half).
metadata:
  version: 1.0.0
---

# OKF — Open Knowledge Format hygiene

The **producer** half of the guild's knowledge standard. The Quartermaster runs
this to keep the *entire* repo tidy and conformant to the **Open Knowledge Format
(OKF v0.1)** — Google Cloud's vendor-neutral spec for representing knowledge as a
directory of markdown files. Its companion is **star-alliance-language**, the
*reader* half every other member uses to consume what this skill produces.

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
  orderly around it.

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
4. **Sweep non-md tidy.** Find orphaned/duplicate/dead files, place each under its
   concept-path, delete genuine dead code (confirm first), and `guild-log` the move.
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
