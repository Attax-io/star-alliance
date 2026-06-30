---
name: strategies-review
description: Review and housekeep strategies. Walks the static strategy docs (pending / auto_strategizing / plans) against the resolutions log to classify each as executed, stale, or genuinely pending, then audits two LIVE review surfaces — the alert-rule roster (price_cross and volume_spike trigger plus cooldown semantics) and the DecisionSignal status queue (active to expired / invalidated / closed). The skill audits and reports only; it never creates rules, fires triggers, mutates signal status, or executes trades.
metadata:
  version: 1.1.0
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

## Step 6 — Audit the live review surfaces

Static docs capture *intent*; two **live** surfaces hold standing state that drifts between
reviews. Audit them as housekeeping — confirm the live state still matches declared strategy
intent and flag stale or contradictory entries. **This is review only: never create a rule,
force a trigger, mutate a signal status, or place an order.** Full field tables, trigger /
cooldown semantics, and the review traps are in
[references/live-review-surfaces.md](references/live-review-surfaces.md).

- **Alert-rule roster.** For each live `alert_rule`, confirm the type is still
  runtime-executable (the core two are `price_cross` — `direction` `above`/`below` at a
  fixed `price` — and `volume_spike` — latest volume over the ~20-day average by
  `multiplier`×), the `target` still resolves, thresholds are plausible vs. the current
  range, and `enabled`/`severity` are intentional. Do not misread an active **cooldown**
  (`cooldown_until` in the future) as a dead rule, and remember a normal not-triggered poll
  writes no history — absence of triggers is not a defect.
- **Signal status queue.** Scan the `DecisionSignal` queue (default view `status=active`)
  for `active` signals well past a sane TTL (possible missed expiry), two opposing `active`
  signals on one instrument (missed invalidation), and any terminal signal
  (`expired`/`invalidated`/`closed`/`archived`) someone expects to be live — terminal
  statuses are one-way and cannot be reactivated. Record discrepancies as findings only.

## Output format

For each finding, indicate the strategy name, affected document(s), and a one-line description.

Format as an Obsidian-compatible Markdown note with:
- YAML frontmatter: `date`, `type: strategy-review`, `tags: [strategy, pending, executed]`
- `[[wikilinks]]` for referenced documents and strategies
- Obsidian callouts (`> [!success]`, `> [!warning]`, `> [!bug]`, `> [!info]`) to distinguish action types

Include live-surface findings (Step 6) in the same note: `> [!warning]` for a stale rule /
over-far `price_cross` / missed-expiry signal, `> [!bug]` for a genuine contradiction (two
opposing active signals, or a runtime-rejected rule type still enabled), `> [!info]` for
housekeeping notes, and `> [!success]` for a surface that is clean.

Save the file to: `docs/strategy/strategy_review_[DATE].md`

## Changelog

- **1.1.0** — Added live review surfaces (Step 6 + `references/live-review-surfaces.md`): alert-rule lifecycle (`price_cross` / `volume_spike` trigger and cooldown semantics) and the DecisionSignal status queue (`active` → `expired` / `invalidated` / `closed`). Framed as audit/housekeeping — the skill reports, it never executes. Source spec (Chinese) translated to English. Description expanded to cover the live surfaces.
- **1.0.0** — Initial: static strategy-doc review against the resolutions log.
