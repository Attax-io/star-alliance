---
name: backend-auditor
description: "Audits the Lex Council Supabase schema (tables, views, triggers, RPC functions, cron jobs, RLS policies) against BACKEND.md by running seven read-only SQL queries through the Supabase MCP connector and returning a structured [NEW]/[REMOVED]/[CHANGED] delta per category. Use after migrations or whenever BACKEND.md feels out of sync with the live database. Triggers: 'audit the backend', 'is BACKEND.md current', 'schema drift', 'compare DB to BACKEND.md', 'RLS sensitivity gate'."
metadata:
  version: 1.0.0
type: Skill
---

# Backend Auditor

**Runtime:** this skill invokes the Lex Council Supabase MCP connector, so it must be run by a Claude-native runtime that has that connector mounted — not a Hermes doer.

The backend-auditor skill reconciles the live Supabase schema for the Lex Council codebase against the canonical inventory in `lex_council/docs/BACKEND.md`. It runs seven read-only queries via the Supabase MCP (connector prefix `mcp__1ee3ddfd-27aa-4176-9539-d9a2081c163d__execute_sql` for SELECTs; `mcp__1ee3ddfd-27aa-4176-9539-d9a2081c163d__list_migrations` and `list_tables` where applicable), compares each result to its corresponding section in BACKEND.md, and returns a structured delta.

## Queries

1. **Migrations** — call `list_migrations`. Compare count against the last daily run's recorded count.
2. **Tables** — call `list_tables` filtered to the `public` schema. Compare names against BACKEND.md §Tables Inventory.
3. **Views** — `SELECT viewname FROM pg_views WHERE schemaname = 'public' ORDER BY viewname`. Compare to BACKEND.md §Views Inventory.
4. **Triggers** — `SELECT tgname, tgrelid::regclass FROM pg_trigger WHERE NOT tgisinternal ORDER BY tgname`. Compare to BACKEND.md §Trigger Functions Inventory.
5. **RPC functions** — `SELECT proname FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace WHERE n.nspname = 'public' AND p.prokind = 'f' ORDER BY proname`. Compare to BACKEND.md §RPC Functions Inventory.
6. **Cron jobs** — `SELECT jobname FROM cron.job ORDER BY jobname`. Compare to BACKEND.md §Cron Functions Inventory.
7. **RLS policies** — `SELECT schemaname, tablename, policyname FROM pg_policies WHERE schemaname = 'public' ORDER BY tablename, policyname`. Count the total and list policy names.

## Output

Return a structured delta listing `[NEW]` / `[REMOVED]` / `[CHANGED]` items per category. No raw dumps — diffs only.

**RLS sensitivity gate.** If any RLS policy change is detected (new, modified, or dropped), flag it explicitly at the top of the response as `RLS-SENSITIVITY-GATE-TRIGGERED` so the orchestrator routes it to `OPEN-ITEMS.md` 🔴.

Keep the response under 400 words. Do not edit any files — return-only.