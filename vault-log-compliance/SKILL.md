---
name: vault-log-compliance
description: Enforces P8 vault-logging compliance for Lex Council. Use this skill whenever a session has touched backend code (migrations, views, triggers, RPC functions, RLS policies, edge functions, cron jobs), frontend code (components, pages, hooks, mutations, stores), schema changes, or bug fixes — even if the user doesn't explicitly ask for a vault log. Also use when the user says phrases like "vault log this", "does this need a vault log?", "log what I did", "P8", "write a vault-log entry", or when finishing up work and unsure whether it qualifies. Skill audits what was touched, checks whether a covering vault-log entry already exists, drafts one in the project's established format if missing, and updates the INDEX.md and affected docs' Last Synced footers. Ask Atta to approve the draft before writing.
metadata:
  version: 1.0.0
---

# Vault-Log Compliance (P8)

Per lex_council/docs/primary_instructions.md §4 and GENERAL-GUIDELINES.md §P8, **every code or backend change gets a wikilinked vault-log entry in lex_council/docs/vault-logs/ before the session ends**. This is the input pipeline for the housekeeper — if a change isn't logged, the housekeeper can't find it on its next run, and the docs silently drift.

This skill's job is to prevent that drift by catching the log requirement at the right moment and drafting compliant entries.

## When this skill applies

Applies when **any** of the following happened in the current session:

- A migration was applied (via Supabase MCP apply_migration or execute_sql with DDL).
- A view, trigger, RPC function, RLS policy, cron job, or edge function was added, modified, or dropped.
- A .tsx, .ts, .jsx, or .js file in lex_council/app/, lex_council/lib/, or lex_council/components/ was created, modified, or deleted.
- A component, store, hook, mutation, or page was added or refactored.
- A bug was fixed in any of the above.
- The user explicitly requested logging ("vault log this", "does this need a vault log?", "P8", etc.).

Does **not** apply when:

- The session only touched .md files in lex_council/docs/ (documentation-only changes are tracked via the "Last Synced" footer, not via vault logs).
- The session only read files / ran queries without changing anything.
- The user is already mid-task and the work isn't finished — defer until the code/backend change is actually complete.
- A matching vault-log entry already exists for today covering this work (check before drafting).

## Workflow

### Step 1 — Enumerate what changed

Compile a list of the work done in this session:

1. Run git status and git diff --stat to see modified/new files.
2. Check the session's migration history (Supabase MCP list_migrations sorted by timestamp, compare against the last entry pre-session).
3. Note any edge function deploys (deploy_edge_function calls).
4. Note any RLS policy changes (they're migrations, but flag them separately — they go through the RLS sensitivity gate downstream).

Produce a short structured list: what was created, modified, or dropped, with file paths / entity names and a one-line reason.

### Step 2 — Check if a vault log already covers this

Before drafting, grep lex_council/docs/vault-logs/ for entries dated today that mention the affected entities. If a covering entry exists, extend it rather than creating a duplicate. The pattern — one log per coherent unit of work — is the norm.

If partial coverage exists (e.g., an earlier log covers phase 1 of a multi-phase change), create a new entry for the new phase and reference the prior one via wikilink.

### Step 3 — Draft the vault-log entry

Follow the project's established format. File path: lex_council/docs/vault-logs/YYYY-MM-DD_short-kebab-description.md where the description captures the essence in 3–6 words. Examples of good filenames from the project:

- 2026-04-24_attendance-v2-phase-5-shrink-trigger.md
- 2026-04-24_notification-event-delivery-migration-p0-to-p4.md
- 2026-04-22_security-audit-critical-fixes.md

The canonical structure (fenced code block intentionally omitted here — see reference examples below):

Frontmatter at top:
- claude_hits: 0
- housekeeper_passes: 0
- last_housekeeper_pass: null
- tags: [vault-log, <domain>, <area>, <feature>]

Then H1 title with date, then a `> ` quote-block one-sentence summary, then sections as applicable:

- **Context** — 2–4 sentences on why the change was needed. Reference driving concern (audit finding, user bug, phase gate, prior vault log).
- **Changes — Backend** — a `# | Type | Target | What Changed | Why` table. Types: CREATE/ALTER/DROP TABLE, CREATE OR REPLACE VIEW, CREATE/ALTER TRIGGER, CREATE OR REPLACE FUNCTION, POLICY (for RLS), CREATE/DROP INDEX, COMMENT. Follow with **Migration name:** on its own line if applicable.
- **Changes — Frontend** — `# | File | What Changed | Why` table.
- **Verification** — what you did to verify. Keep short.
- **What did NOT change** — bullets on scope boundaries. Helps the housekeeper understand what isn't affected.
- **Related** — wikilinks to prior phases, follow-ups, affected planet hubs.

Adapt sections to the actual work. Not every entry needs every section — use judgment. A simple bug fix might be Context + Changes — Frontend + Verification. A large migration might add Rollback and What did NOT change.

### Step 4 — Present the draft for approval

Before writing to disk, show the user the full draft in the chat. Ask:

> Here's the vault-log draft for what we did. Anything to add or change before I write it?

Wait for approval. If the user says "looks good" or similar, proceed. If they request changes, apply them and re-present. Do not write silently.

### Step 5 — Write the vault log, update the index, footers

Once approved:

1. Write the .md file to lex_council/docs/vault-logs/.
2. Append a row to lex_council/docs/vault-logs/INDEX.md. Format: `| DD Mon YYYY | [[wikilink]] | one-line summary |`. Insert after the most recent entry, preserving the table structure. Read the last 10 lines of INDEX.md to confirm the format before editing.
3. For each domain doc the change affects (BACKEND.md, FRONTEND.md, MIGRATION-LOG.md, a specific planet hub leaf doc, etc.), append a "Last Synced" footer entry with today's date and a wikilink to the new vault log. If the doc already has a Last Synced section, prepend today's entry above the prior ones; if not, add a new section at the bottom.

### Step 6 — Handle the edge cases

**RLS changes.** Flag loudly in the vault log with a dedicated section `## RLS Sensitivity`. Include the exact policy body diff (old vs new). Tag the log with `rls` in frontmatter. This primes the housekeeper's RLS sensitivity gate to create a 🔴 in OPEN-ITEMS.md on its next run.

**[!atta] blocks.** If your change touches a section inside or adjacent to a `> [!atta]` block in any doc, **stop**. Do not edit that doc. Flag this in the vault log under a `## [!atta] Review Needed` section with the exact block quoted and a description of what would need to change. Route to OPEN-ITEMS.md as a 🔴. This is the inviolable rule from primary_instructions.md §1.

**Ambiguous intent.** If the work could be interpreted multiple ways (e.g., "renamed column" without saying the old name, or a partial refactor where you're not sure what's final), write the vault log but mark ambiguous sections with `⚠️ INTENT UNCLEAR:` prefix and explain what's unresolved. The housekeeper will route these to OPEN-ITEMS rather than editing docs based on a guess.

**No backend change, but a new vault-logged event happened.** Some events worth logging even without code changes: scheduled-task creation (like housekeeping v2 going live), outage/incident narratives, major decisions. These get a simpler vault log — just context + what happened + related links.

## Why the approval gate matters

The housekeeper runs autonomously on vault logs, and anything you write here becomes durable project memory that future Claude sessions (and the bot) treat as ground truth. A misleading log poisons downstream doc-reconciliation. Make the user confirm the draft reflects reality before it becomes canon.

## Related

- lex_council/docs/primary_instructions.md §4 — the mandatory P8 rule.
- lex_council/docs/GENERAL-GUIDELINES.md §P8 — full rule text.
- lex_council/docs/housekeeping/README.md — how the housekeeper consumes these logs.
- lex_council/docs/vault-logs/INDEX.md — the chronological index this skill updates.
- Example logs to study for format: 2026-04-24_attendance-v2-phase-5-shrink-trigger.md, 2026-04-22_housekeeping-run1.md, 2026-04-24_housekeeping-v2-scheduled-and-live.md.
