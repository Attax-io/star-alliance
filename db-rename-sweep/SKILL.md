---
name: db-rename-sweep
description: >
  Loads the full surface inventory for any Lex Council table or column rename before
  the first migration line is written. Use this skill whenever the user asks to rename
  a table, rename a column, rename a view, do a naming sweep, migrate a prefix (e.g.
  attendance_* → atnd_*), unify naming, or fix an inconsistent name. Also trigger on
  "rename", "rename sweep", "rename checklist", "naming cleanup", "change table name",
  "rename this view", "prefix the tables", "sweep the old name", "unify the naming",
  or any request that implies a SQL `ALTER TABLE ... RENAME` / `RENAME COLUMN`. The
  skill exists because a rename in this codebase touches ~14 surfaces (migrations,
  trigger bodies, view defs, RLS policy bodies, edge functions, frontend types,
  markdown docs, auto-memory, scheduled tasks, etc.) and the single most common failure
  mode is forgetting one. Load silently — no need to announce the skill is running.
---

# DB Rename Sweep — Context Loader

This skill's only job is to auto-trigger on rename keywords and point you at the authoritative checklist in the vault before you touch anything.

## Step 1 — Load the canonical checklist

Read this file in full before doing anything else:

- `lex_council/docs/architecture/backend/DB-RENAME-CHECKLIST.md` — the 14-surface inventory, per-surface grep/SQL commands, verification queries, anti-patterns, canonical example.

If the rename touches a money-feeding column (wages, credits, transactions), also read:

- `lex_council/docs/architecture/backend/DB-REFACTOR-PHASED-PLAN.md` — the phased-plan framework. A money-adjacent rename must run as Phase N of a phased refactor, not a naive rename.

## Step 2 — Follow the checklist in order

The checklist is numbered 1 through 14. **Do not skip a surface** — run every grep/SQL command, even the ones you believe don't apply. The whole point of the checklist is to verify, not to assume.

## Step 3 — Build the migration after the sweep

Only once the sweep is complete do you write the rename migration. Batch all related renames into a single migration for atomicity. Never drop-and-recreate — always `ALTER ... RENAME`.

## Step 4 — Verification pass

Before calling the rename done, run the sentinel INSERT, the `pg_views` scan, and the `pg_policies` scan from the checklist's "Verification" section. These catch the #1 missed surface (trigger bodies referencing old names) before it reaches prod.

## Step 5 — Vault log

Per P8, write one vault-log entry covering the rename. Name every surface touched. Name every surface confirmed clean. Include the old→new mapping so future readers can reconcile past vault logs.

---

**Related docs:** `lex_council/docs/architecture/backend/DB-RENAME-CHECKLIST.md` · `lex_council/docs/architecture/backend/DB-REFACTOR-PHASED-PLAN.md` · `lex_council/docs/architecture/backend/MIGRATION-LOG.md` · `lex_council/docs/GENERAL-GUIDELINES.md` §P8
