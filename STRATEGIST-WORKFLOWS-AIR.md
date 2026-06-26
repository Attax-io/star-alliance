---
title: Star Alliance — Strategist's Workflow Catalogue (MacBook Air pass)
author: The Strategist (Air session mine; MiniMax doer, Strategist gate)
date: 2026-06-26
project_version_at_scan: 6.49.42
method: read-only mine of the Air's local session stores → MiniMax cluster → Strategist differential gate
companion: STRATEGIST-WORKFLOWS.md (the Mac-mini pass — the canonical 546+562-session catalogue)
---

# Star Alliance — The Air Pass (differential)

> The Guild Master asked the Strategist to run the Mac-mini workflow-investigation + skill-smith
> routine again on the **MacBook Air**. Crucially, both machines share the same git repo on
> `main`: the mini run already forged the **24-workflow star map** and the **41-skill roster**.
> So the Air pass is a **differential**, not a re-run — the Air contributes new *input* (its own
> local sessions), but the *output targets are already populated*. The Strategist's job here is to
> find only what the existing map does **not** already cover, and to refuse minting duplicate
> constellations (the `workflow-forge` discipline: *a healthy star map is edited, not just appended to*).

## What was scanned (this machine)

| Store | Location | Volume |
|---|---|---|
| **Claude Code sessions** | `~/.claude/projects/*` | **693 transcripts** (653 Lex Council App, 36 star-alliance, 3 claude-skills, 1 worktree) |
| **Cowork sessions (metadata)** | `…/Claude/claude-code-sessions/**/local_*.json` | **319 sessions** (titles + cwd), Apr 19 – Jun 26 |
| **Cowork agent transcripts** | `…/Claude/local-agent-mode-sessions/**/*.jsonl` | **1,607 transcripts** (excl. subagents) |

- Harvest tool: skillsmith `routine_scan.py` (CC store, `--days 130`) + a dedicated Cowork harvester (`cowork_harvest.py`) for the two Cowork stores routine_scan does not reach.
- **305 unique** Cowork session titles after near-dup collapse.
- **cwd distribution: 309 / 319 sessions = Lex Council App.** The Air is, operationally, a Lex Council machine.

## Verdict at a glance

| Question | Answer |
|---|---|
| Net-new workflows the Air corpus proves but the 24-map lacks | **0** |
| MiniMax candidate workflows proposed | 7 |
| …surviving the Strategist's differential gate | **0** (all covered or already-referenced — see below) |
| Genuine skill **defects** (real user-turn friction text) found | **0** |
| "Frictionful" skill flags that were product-name false positives | all of them (`supabase` ×176 = the product, not the skill) |
| Outcome | **The 24-workflow / 41-skill map already saturates the Air's corpus.** The Air pass *validates* the mini run. |

## The differential gate — why each MiniMax candidate was rejected

The doer (MiniMax M3, per `CLAUDE.md`) clustered the 305 titles and proposed 7 net-new workflows.
The Strategist gated each against `workflows.json`:

| Candidate | Closest existing | Verdict | Why |
|---|---|---|---|
| performance-optimization-quest | `architecture-build` | **covered** | architecture-build's `when` literally reads *"including performance tuning"*. |
| schema-migration-campaign | `architecture-build` + `conquering-campaign` | **covered** | architecture-build's `when` reads *"finance-critical data migrations (plan, dry-run with BEGIN/ROLLBACK, reconcile)"*; renames owned by the `db-rename-sweep` skill. |
| public-calculator-build | `tool-forge` | **covered** | tool-forge's `when` reads *"wages, social-insurance, severance, inheritance, customs, land"* — the exact calculator titles. (MiniMax missed tool-forge.) |
| i18n-localization-quest | `legal-codex` / `cleanup-rotation` | **covered** | `i18n`, `locale`, `translat` already appear in workflows.json; missing-key leaks are owned by the `cleanup` skill's `leaks` mode. |
| impeccable-ui-audit | `design-sprint` | **covered** | `audit`/`polish` already in the map; the `impeccable` skill owns the aesthetic-bar review. |
| bulk-data-operation-quest | `quick-fix` / `bug-cycle` | **covered** | A Lex domain feature area, not a reusable cross-mission guild pattern. workflow-forge rule: *refuse the forge when it's a skill gap (or domain feature) in disguise.* |
| dev-environment-bootstrap | the `dev-server` skill | **covered** | Machine setup, owned by a skill — not a multi-member workflow. |

## What the Air corpus *did* prove (the value of the pass)

1. **The star map holds.** Every one of 305 operational sessions maps onto an existing workflow id. No constellation was minted; none needed to be. This is the intended result of a second-machine pass.
2. **Lex Council is the centre of gravity.** 309/319 Cowork sessions and 653/693 CC sessions are Lex Council App work — confirming the mini run's finding that this is "a personal, mostly-Lex-Council agent OS in guild costume."
3. **No skill is broken.** Zero genuine user-turn friction text surfaced against any guild skill. The harvest's "frictionful" flags were all product-name collisions (`supabase`, `performance`, `cleanup` as topic words), exactly the over-count `routine_scan.py` documents.

## Recurring operational themes (already-owned, logged for the record)

These are the dominant Air work patterns — each already has a home, listed for the next Butler:

- **Fix-X bug hotfixes** (missing DB column, missing i18n message key, RLS permission-denied, hydration mismatch) → `bug-cycle` / `quick-fix`.
- **Cleanup + version-bump + push** → `cleanup-rotation` / `release-train`.
- **Admin/members panel layout redesigns** → `design-sprint`.
- **Column/RLS audits, phased migrations, renames** → `architecture-build` / `conquering-campaign` / `db-rename-sweep`.
- **Public calculators (severance, social-security, GES)** → `tool-forge`.
- **Legal memos / bilingual drafts** → `legal-draft`.
- **Skill sync/upgrade, taste-skill installs** → `skill-forge` / `skillsmith`.

## Method note

- Harvest is read-only; it wrote only its digest files under `/tmp`. No session store was modified.
- The doer drafted; the Strategist gated; nothing was forged. This *is* the gate working — phantoms (here, duplicate constellations) caught at the stub cost nothing.
