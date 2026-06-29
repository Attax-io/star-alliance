---
name: phased-db-refactor
description: Decision framework and execution guide for multi-phase database refactors in Lex Council. Use whenever the user asks to refactor a table or column that touches ≥3 downstream surfaces, involves a money-adjacent column (wages, credits, transactions), must remain deployable at every step, or where rolling back would require a backup restore. Also trigger on phrases like "phased refactor", "phase plan", "multi-phase migration", "attendance v2 style", "frontend-first", "Phase 0 safety net", "dual-write window", or "byte-identical". Do NOT use this for pure cosmetic renames with no semantic change — use the db-rename-sweep skill for those. This skill exists because rushing a multi-surface refactor into a single migration has caused wage recompute bugs, broken trigger bodies, and post-rollback data loss in past sessions.
---

# Phased DB Refactor — Framework

Full reference doc: `lex_council/docs/architecture/backend/DB-REFACTOR-PHASED-PLAN.md`

This skill is the procedural shortcut; that doc is the authoritative reference.

## When to use this framework

Use a phased plan when **any one** of these is true:

- The change touches **≥3 downstream surfaces** (view defs, trigger bodies, edge functions, frontend types, etc.)
- A column being renamed, dropped, or restructured **feeds into money** — wages, credits, transactions, customer billing
- The app must remain **deployable at every phase boundary** (no maintenance window available)
- Rolling back past Phase 2+ would require restoring from backup

If none apply, do the change in a single migration with a single vault log. Don't over-engineer.

**Distinguishing this from a rename sweep:** A rename with no semantic change goes through `db-rename-sweep`. A refactor that changes semantics, restructures columns, or touches money-adjacent data uses this framework.

## The 8 principles

### Principle 1 — Phase 0 is the safety net, not the first real phase

Create a **rollback archive table** (same shape as the target, keyed by `archived_at`) plus a snapshot of current rows. No behavior changes in Phase 0. The app runs exactly as before.

Without Phase 0, rollback = "restore from yesterday's backup" — which loses everything between the backup and the rollback.

```sql
-- Example Phase 0
CREATE TABLE public._backup_old_table_YYYYMMDD (LIKE public.old_table INCLUDING ALL);
INSERT INTO public._backup_old_table_YYYYMMDD SELECT * FROM public.old_table;
```

Move the backup to the `private` schema or ensure it has RLS (S10 — backup tables in `public` without RLS are a security regression).

### Principle 2 — Frontend-first, schema last

Order phases from cheapest-to-revert to most-expensive-to-revert:

1. Frontend type slimming → reversible with `git revert`
2. Repoint components to new views while old views still exist → reversible with `git revert`
3. Add new views/tables in parallel to old ones → drop with a migration
4. Populate + dual-write window → stop with a migration
5. Drop old columns / old views / old triggers → requires restore

If you discover mid-refactor that the plan is wrong, the pivot is cheap when the schema side is still untouched.

### Principle 3 — Prefer live-derived over stored columns

Default: derive classification (e.g., `is_late`, `is_ok`) in **views** off raw columns. Do not write the classification into a trigger-populated stored column unless you have a concrete query-cost reason.

Convert to stored only when all three hold:
- The view is the hottest path in the app
- The computation is measurably expensive
- The rule behind it is frozen for ≥6 months

### Principle 4 — Byte-identical preservation for money-adjacent columns

If the column feeds wages, credits, or any money formula: **do not touch the value** during the rename or restructure. Copy byte-identical.

**Test:** before and after the refactor, run `SELECT SUM(target_column) FROM target_table` and confirm totals match exactly.

### Principle 5 — Mid-plan re-evaluation at ~50%

At roughly halfway through the phase list, stop and re-read the plan. Ask:
- Did an earlier phase reveal a surface the plan missed?
- Is the remaining plan still the right shape, or should phases be re-ordered / merged / split?
- Did a dependency become obsolete?

If re-evaluation produces a non-trivial plan change, write a **revised plan section** in the original plan doc — don't mutate the phase list in place. Keep the original visible so future readers see the divergence and its reason.

### Principle 6 — One visible behavior change per phase

Each phase must end with the app still deployable and behaviorally equivalent — or with exactly one user-visible change described in the vault log.

Anti-pattern: a phase that drops three columns, rewrites a view, and deploys an edge function. If one piece breaks, bisection covers the whole phase.

### Principle 7 — Vault-log every phase before moving to the next

Not at session end — **before** Phase N+1 starts. The vault log is a contract with the next session that the phase completed cleanly.

Per-phase vault log must include: what changed, which surfaces were touched, rollback recipe, and what the next phase assumes.

### Principle 8 — Strategy reassessment is a first-class phase

If the re-evaluation (Principle 5) changes the plan significantly, that reassessment is itself a phase — numbered and vault-logged as such.

## Phase template

For each phase, document:

| Field | Content |
|---|---|
| **Phase N name** | Imperative, short — "Repoint AttendanceDashboard", not "Frontend changes" |
| **Goal** | User-visible behavior this phase achieves (or invariant it preserves) |
| **Surfaces touched** | Files, views, triggers, edge functions — exhaustive list |
| **Rollback recipe** | Exact commands to undo this phase |
| **Invariants** | What must remain byte-identical (money columns, etc.) |
| **Verification** | SQL + UI check that proves the phase shipped cleanly |
| **Vault log** | Path to the per-phase vault log, written before Phase N+1 |

## Starting a new phased refactor

1. Read `DB-REFACTOR-PHASED-PLAN.md` and `DB-RENAME-CHECKLIST.md` in full
2. List every downstream surface using the 14-surface checklist from `db-rename-sweep`
3. Decide if a Phase 0 safety net is needed (it almost always is)
4. Order phases frontend-first → parallel additions → dual-write → drops
5. Write the plan doc at `docs/proposals/YYYY-MM-DD_refactor-plan-name.md` before writing any SQL
6. Get Atta's confirmation on the plan before starting Phase 1

Atta must approve the full phase plan before any SQL migration is written — this is the P3 implementation approval protocol from GENERAL-GUIDELINES.md.

## Canonical reference

**Attendance v2 refactor** (April 2026) — 8 phases + Phase 4.5 (inserted post-re-eval), 5 tables, 4 views, 3 triggers, 1 edge function, ~40 frontend files.

Key moves:
- Phase 0: `attendance_rollback_archive` — no behavior change, pure safety net
- Phases 1–3: all frontend (repoint, toggle, type slim) — reversible with git revert
- Phase 4: enriched `attendance_daily_js` with live-derived classification — old columns still present in parallel
- Phase 4.5: inserted post-re-eval to slim `cm_hr_js` before the view depended on it
- Phase 5: shrunk the BEFORE trigger; `worked_hours_raw` preserved byte-identical (money-adjacent)
- Phase 6: dropped old derived columns — first destructive phase, after 5 reversible ones

## When NOT to use this framework

- Single-table, single-column change with no derived consumers → one migration, one vault log
- Time-boxed spike/experiment on a dev branch → branch, iterate, throw away
- Emergency hotfix → fastest safe path first, vault log after
- Pure cosmetic rename with no semantic change → `db-rename-sweep` skill
