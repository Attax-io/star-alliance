---
name: cold-doc-rotator
description: "Picks the N Lex Council docs with the oldest `last_housekeeper_pass` frontmatter field (treating `null` as oldest), reads each, ticks the counter via the doc-hit-counter script, and flags any that look stale (inconsistencies, broken wikilinks, references to dropped tables/views). Use to force coverage of cold docs outside the scheduled rotation. Triggers: 'rotate cold docs', 'housekeeper pass on cold docs', 'tick doc counters', 'force coverage'."
metadata:
  version: 1.0.0
type: Skill
---

# Cold-Doc Rotator

The cold-doc-rotator skill guarantees coverage of every `.md` doc under `lex_council/docs/` by force-rotating the oldest-passed subset and ticking their counters.

## Selection

Find the 17 `.md` files in `lex_council/docs/` with the oldest `last_housekeeper_pass` frontmatter field. Treat `null` as oldest (these are newly migrated and have never been passed).

**Exclude** these directories: `archived/`, `memory/archived/`, `vault-logs/`, `logs/`, `outputs/`.

## Pass

For each selected file, in order oldest-first:

1. Read the file.
2. Evaluate staleness — look for: obvious inconsistencies with primary_instructions / Vault Core / BACKEND / FRONTEND, broken wikilinks, references to dropped tables / views / policies, outdated counts.
3. Call `bash .claude/scripts/doc-hit-counter.sh --source housekeeper "<absolute-path>"` to tick the counter. The script also updates `last_housekeeper_pass` to today's ISO date.

## Output

Return a list of any docs flagged as looking stale (file path + 1-line reason each). Keep the response under 300 words. The skill MAY edit via the hit-counter script, but must NOT edit doc content — the orchestrator queues reconciler tasks for flagged docs.