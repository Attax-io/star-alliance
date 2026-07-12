---
name: guild-reflection
description: "Guild health review on the Supabase spine (v2.1 — restores the automation the retired evolution engine lost, without its stall). Runs manual OR on an external schedule: query the guild.* views (dead_skills, turn_cost_daily, member_levels, skill_usage) via `bin/sa` or the Supabase MCP, run each candidate through a critic gate, then record the survivors as guild.findings rows (status='open'). Acting on a finding is ordinary session work — do the change, then flip status to applied or rejected. The schedule lives OUTSIDE the skill (the harness scheduler); every fire runs a fresh stateless pass, so the skill still holds no state and cannot stall. Triggers: 'reflect on the guild', 'guild self-audit', 'run a reflection', 'weed the skills', 'what did we learn', 'review guild health', 'check for dead skills', or a scheduled reflection fire."
metadata:
  version: 2.1.0
type: Skill

---

# guild-reflection

**Trigger: manual OR scheduled.** Someone asks for a reflection, or the harness
scheduler fires one on a cadence. Either way the skill does the same thing.

The old evolution engine (retired 2026-07, see
`.retired/2026-07-supabase-migration/evolution/`) stalled silently because it held
its own state and ran its own in-process heartbeat. v2.0.0 over-corrected by banning
automation entirely — which is why reflection went idle after ~July 4 once nothing
called it by hand. v2.1 splits the difference the safe way:

- The **schedule lives outside the skill**, in the harness scheduler (the
  `schedule` / scheduled-tasks capability), not a bespoke daemon inside the guild.
- Every fire — manual or scheduled — runs a **fresh stateless pass** that reads the
  live views and leaves only `guild.findings` rows behind.
- The skill itself still holds **no state**, so it still **cannot stall**. External
  scheduling is safe precisely because each run starts clean; that hard-won lesson
  is now the *reason* automation is allowed, not a reason to forbid it.

## Scheduling (set up once, outside this skill)

To make reflection run on its own, register a recurring job with the harness
scheduler that invokes this skill (e.g. weekly). Do this as a deliberate, separate
act — not from inside a reflection run. Nothing here installs a schedule for you;
this section documents how one is wired. If no schedule exists, the skill still runs
fine on manual trigger — that is the fallback, never a failure.

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

## The critic gate (restored — runs before anything is filed)

The old engine had a critic that culled weak suggestions; it went missing in the
migration. Restore it as an adversarial pass over the raw candidates the loop
produced. Before writing a single row, challenge each candidate and **drop** it if:

- **No view-evidence** — it isn't backed by a concrete result from one of the four
  views above. No vibes, no introspective claims. (This extends v2's
  "no suggestion without evidence" rule into an explicit gate.)
- **Duplicate** — an equivalent finding is already open (`bin/sa findings`).
- **Vague** — the title isn't a concrete imperative action the Guild Master could
  approve as-is.

Only the survivors become findings. A pass that produces zero survivors is a valid,
healthy outcome — file nothing.

## Output: findings rows, one per surviving suggestion

For each candidate that clears the critic gate, insert ONE row into `guild.findings`
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
- Evidence = the query result that justifies it, as compact jsonb. Enforced by the
  critic gate above — a row without view-evidence should never reach this step.

## Acting on a finding

Ordinary session work — no special machinery. Do the change (edit the skill,
retire the member, fix the hook), then flip the row:

```sql
update guild.findings set status = 'applied', decided_at = now() where id = <id>;
-- or status = 'rejected' with the reason appended to body
```

A reflection run is complete when the surviving suggestions are filed — not when
they are acted on. Acting is a separate, deliberate choice by the Guild Master.

## Changelog

| Version | Date | Summary |
|---|---|---|
| **2.1.0** | 2026-07-12 | Restore automation the retired engine lost, without its stall: the skill now runs on an EXTERNAL harness schedule as well as by hand, and a critic gate again culls evidence-less / duplicate / vague candidates before any finding is filed. Each fire is still a fresh stateless pass, so the skill holds no state and cannot stall. |
| **2.0.0** | 2026-07-12 | Rewritten for the Supabase spine: manual-trigger-only, stateless. Queries guild.dead_skills / turn_cost_daily / member_levels / skill_usage and files guild.findings rows. Replaces the retired evolution engine and the old CYCLE/AUDIT journal machinery. |
| **1.1.0** | 2026-06-28 | Four TIER-3 self-learning audits (superseded by 2.0.0). |
| **1.0.1** | 2026-06-27 | Description trimmed under the 1024-char limit. |
