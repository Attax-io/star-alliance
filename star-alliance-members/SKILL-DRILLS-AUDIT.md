---
type: Audit
timestamp: 2026-06-27T16:00:00Z
workflow: Strategic Audit
scope: member skill-invocation instructions (when/how to fire each carried skill)
---

# Skill-Invocation Audit — Guild Members

Audit of the **do / do-not** guidance on *when* and *how* every member invokes the
skills it carries. Source of truth for each skill's WHEN is its own `SKILL.md`
`description`. One row per member × skill.

## Standard (the contract every member must meet)

Each member file gains a **`## Skill Drills`** section: a table with four columns —

| Column | Means |
|---|---|
| **Skill** | the carried skill name |
| **Invoke WHEN** | the precise trigger — the situation that *should* fire it |
| **Do NOT invoke for** | the anti-trigger — the adjacent task that wrongly pulls it |
| **Pairs with** | the skill it chains to (or the member it hands off to) |

The existing **`## How you work`** prose stays, but is corrected (dedupe numbering,
name every listed skill) so the narrative and the table agree. Two universal skills —
`weapon-utility` and `star-alliance-language` — get one shared drill block, identical
across all members, since they ride every member.

## Findings

### F1 — Universal skills are orphaned in all 9 members
`weapon-utility` and `star-alliance-language` appear in every `skills:` list but are
**never drilled** in any member's prose. A member reading its own file gets no
point-of-use cue to (a) consult `weapon-utility` before picking a model, or (b) run
`star-alliance-language` to orient in the repo before blind-reading. **Fix:** shared
universal drill block in every file.

### F2 — Listed-but-undrilled skills (per member)
Skills present in `skills:` frontmatter with no prose drill — a member can carry a
blade it was never taught to draw:

- **developer:** `supabase` (only `supabase-postgres-best-practices` is drilled)
- **architect:** `legal-rule-modeling`, `law-harvest`, `supabase`
- **designer:** `image-to-code` (prose conflates it with `imagegen-*`; they are distinct)
- **herald:** `relationship-intel`
- **strategist:** `workflow-forge`, `arsenal-forge`, `scheduled-watch`
- **translator:** `legal-drafting`, `law-harvest`
- **quartermaster:** `release-train`, `okf`
- **butler:** `high-alert` (mentioned only in a frontmatter comment, never in prose)

### F3 — No anti-triggers anywhere
Not one member states when *not* to fire a skill. Adjacent tasks misfire: e.g. designer's
`image-to-code` (production code from a mock) vs `imagegen-frontend-web` (reference imagery
only) have no boundary; developer's `supabase` (app/client/auth) vs
`supabase-postgres-best-practices` (query/schema tuning) are undivided. **Fix:** the
Do-NOT column.

### F4 — Numbering / label defects
- developer: two `7.` steps ([the-developer.md:61-62](the-developer.md))
- architect: two `4.` steps ([the-architect.md:54-57](the-architect.md))
- designer: step 3 labels the `imagegen-*` skills as "image-to-code", masking the real
  `image-to-code` skill

### F5 — Format drift
`the-merchant` already carries a per-skill `## Skills` block (the strongest current
pattern); the other eight do not. No shared template means depth and shape vary file to
file. The Skill Drills table normalizes all nine.

## Cross-member overlap (same skill, must not conflict)
- `supabase` / `supabase-postgres-best-practices` — developer **and** architect
- `db-rename-sweep` — developer **and** architect
- `storm-investigation` — herald, merchant, strategist, quartermaster
- `brandkit` — designer (forges) **and** herald (briefs only — must say "brief, don't forge")
- `article-creator` — herald **and** translator
- `law-harvest` — architect **and** translator
- `bug-fix-workflow` — developer **and** strategist
- `obsidian-markdown` — developer **and** translator

Each member's drill for a shared skill must state *its* slice so two members don't claim
the same act (e.g. herald **briefs** `brandkit`; designer **forges** it).

## Remediation (this run)
1. Add `## Skill Drills` table to all 9 working members (butler included).
2. Append the shared universal drill block (`weapon-utility`, `star-alliance-language`).
3. Correct `## How you work` prose: dedupe numbering, name every listed skill, fix the
   designer image-to-code mislabel.
4. Verify: `guild-conformity` (every `skills:` entry drilled, no dead refs) + `dashboard-parity`.
5. Log: `guild-log` entry (`type: member-upgrade`) → version pumps.
