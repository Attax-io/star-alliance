---
name: strategies-review
description: Review pending strategies and move them to executed then check the docs.
metadata:
  version: 1.0.0
type: Skill

---
## Step 1 — Load the resolutions log first

Read `docs/strategy/auto_strategizing/RESOLUTIONS.md` before anything else. This file is the canonical record of every strategy decision (APPLIED, POSTPONED, or PROPOSED) with resolution IDs. Use it to pre-classify each pending strategy's real status before reading individual files.

## Step 2 — Scan all three strategy locations

Check execution status across:
- `docs/strategy/pending/` — named strategies and auto-generated proposals
- `docs/strategy/auto_strategizing/` — root-level strategy files
- `docs/strategy/auto_strategizing/plans/` — numbered PLAN files

For each strategy found, cross-reference its status against the resolutions log. Only read the full strategy file if the resolution is ambiguous or missing.

## Step 3 — Classify and report

For each strategy, determine one of:
- **Move to executed** — all phases applied per resolutions log; file should be relocated to `docs/strategy/executed/`
- **Update status** — partially executed or superseded; file status/frontmatter is stale
- **Genuinely pending** — no execution evidence; correctly in pending
- **Stale/duplicate** — file duplicates information already tracked elsewhere

## Step 4 — Verify documentation

For strategies classified as executed or partially executed, spot-check that the relevant docs (named in the strategy's "Docs Updates Required" section, if present) reflect the changes. Flag any doc that has not been updated.

## Step 5 — Flag inconsistencies

Identify contradictions, gaps, or conflicts within or between strategies — especially:
- Overlapping scope between pending strategies
- Dependency ordering issues
- Frontmatter status that contradicts the resolutions log

## Output format

For each finding, indicate the strategy name, affected document(s), and a one-line description.

Format as an Obsidian-compatible Markdown note with:
- YAML frontmatter: `date`, `type: strategy-review`, `tags: [strategy, pending, executed]`
- `[[wikilinks]]` for referenced documents and strategies
- Obsidian callouts (`> [!success]`, `> [!warning]`, `> [!bug]`, `> [!info]`) to distinguish action types

Save the file to: `docs/strategy/strategy_review_[DATE].md`
