---
name: guild-reflection
description: "Manual-trigger guild health review on the Supabase spine (v2 — replaces the retired evolution engine). When asked to reflect, run a guild self-audit, weed skills, or review guild health: query the guild.* views (dead_skills, turn_cost_daily, member_levels, skill_usage) via `bin/sa` or the Supabase MCP, and record each concrete suggestion as one guild.findings row (status='open'). Acting on a finding is ordinary session work — do the change, then flip the finding's status to applied or rejected. No cron, no heartbeat, no state machine: this skill holds no state, so it cannot stall. Triggers: 'reflect on the guild', 'guild self-audit', 'run a reflection', 'weed the skills', 'what did we learn', 'review guild health', 'check for dead skills'."
metadata:
  version: 2.0.0
type: Skill

---

# guild-reflection

**Manual trigger only.** Someone asks for a reflection; nothing runs on its own.
The old evolution engine (retired 2026-07, see `.retired/2026-07-supabase-migration/evolution/`)
stalled silently because it held state. This skill holds none: every run reads the
live views fresh and leaves only `guild.findings` rows behind.

## The loop (one pass, ~4 queries)

Read the DB spine — via the Supabase MCP (`execute_sql`, schema `guild`) or through
PostgREST the way `bin/sa` does (never print the JWT):

1. **`guild.dead_skills`** — skills with no `skill_fire` event. Candidates for
   retirement or for a better trigger phrase in their description.
2. **`guild.turn_cost_daily`** — token/wall-time trend per project per day.
   Spikes = a workflow or hook wasting turns; flag it.
3. **`guild.member_levels`** — spawn counts per member. A member never spawned
   may be mis-described or redundant; a member absorbing everything may need
   its load split.
4. **`guild.skill_usage`** — fires per skill. The head (top ~10) is doctrine
   that works; the long tail is weeding ground.

Also read the findings already open — `bin/sa findings` — so a run never
re-files a suggestion that is already on the board.

## Output: findings rows, one per suggestion

For each concrete, actionable suggestion, insert ONE row into `guild.findings`
with `status='open'`:

```sql
insert into guild.findings (kind, status, title, body, evidence, device_id)
values (
  'reflection',            -- kind: reflection | dead-skill | cost | load
  'open',
  'Retire skill X — zero fires since seed',
  'What to do and why, in plain English the Guild Master can read.',
  '{"skill_id": "x", "last_fired_at": null}'::jsonb,
  'mac-atta'
);
```

Rules:
- One row per suggestion — never a batch dumped into one body.
- Title = imperative action phrase; body = plain English, no jargon.
- Evidence = the query result that justifies it, as compact jsonb. No
  suggestion without evidence from a view — no vibes, no introspective claims.

## Acting on a finding

Ordinary session work — no special machinery. Do the change (edit the skill,
retire the member, fix the hook), then flip the row:

```sql
update guild.findings set status = 'applied', decided_at = now() where id = <id>;
-- or status = 'rejected' with the reason appended to body
```

A reflection run is complete when the suggestions are filed — not when they are
acted on. Acting is a separate, deliberate choice by the Guild Master.

## Changelog

| Version | Date | Summary |
|---|---|---|
| **2.0.0** | 2026-07-12 | Rewritten for the Supabase spine: manual-trigger-only, stateless. Queries guild.dead_skills / turn_cost_daily / member_levels / skill_usage and files guild.findings rows. Replaces the retired evolution engine and the old CYCLE/AUDIT journal machinery. |
| **1.1.0** | 2026-06-28 | Four TIER-3 self-learning audits (superseded by 2.0.0). |
| **1.0.1** | 2026-06-27 | Description trimmed under the 1024-char limit. |
