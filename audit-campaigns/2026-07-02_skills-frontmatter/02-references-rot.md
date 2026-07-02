---
type: findings
campaign: audit-campaigns/2026-07-02_skills-frontmatter
section: 2
title: References Rot (23 doc ghosts, 60 wikilink rot)
---

# References Rot — 23 doc ghosts, 60 wikilink rot

> Anchor rot: **0** (no `#section` references found in corpus).

## Doc ghosts (23)

Markdown links whose target file doesn't exist on disk.

| Source skill | Ghost target | Kind |
|---|---|---|
| daily-stock-analysis | https://github.com/ZhuLinsen/daily_stock_analysis | doc ghost |
| obsidian-markdown | skills/obsidian-markdown/references/PROPERTIES.md | doc ghost |
| obsidian-markdown | skills/obsidian-markdown/references/EMBEDS.md | doc ghost |
| obsidian-markdown | skills/obsidian-markdown/references/CALLOUTS.md | doc ghost |
| obsidian-markdown | url | doc ghost |
| obsidian-markdown | skills/obsidian-markdown/references/EMBEDS.md | doc ghost |
| obsidian-markdown | skills/obsidian-markdown/references/CALLOUTS.md | doc ghost |
| obsidian-markdown | skills/obsidian-markdown/references/PROPERTIES.md | doc ghost |
| obsidian-markdown | skills/obsidian-markdown/references/adr-template.md | doc ghost |
| obsidian-markdown | https://help.obsidian.md/obsidian-flavored-markdown | doc ghost |
| obsidian-markdown | https://help.obsidian.md/links | doc ghost |
| obsidian-markdown | https://help.obsidian.md/embeds | doc ghost |
| obsidian-markdown | https://help.obsidian.md/callouts | doc ghost |
| obsidian-markdown | https://help.obsidian.md/properties | doc ghost |
| okf | /tables/customers.md | doc ghost |
| performance | https://web.dev/articles/vitals | doc ghost |
| python-master | https://github.com/wdm0006/python-skills | doc ghost |
| supabase | https://supabase.com/dashboard/project/<ref>/integrations/data_api/settings | doc ghost |
| supabase | https://supabase.com/docs/guides/api/securing-your-api.md | doc ghost |
| supabase | https://supabase.com/docs/guides/api/securing-your-api.md | doc ghost |
| supabase | https://supabase.com/docs/reference/cli/introduction | doc ghost |
| supabase | https://github.com/supabase/cli/releases | doc ghost |
| supabase | https://supabase.com/docs/guides/getting-started/mcp | doc ghost |

## Wikilink rot (60)

`[[wikilink]]` references that don't resolve.

| Source skill | Rot target |
|---|---|
| cleanup | 2026-06-02_cleanup-skill-lessons-l25-l31 |
| cleanup | 2026-05-22_db-wide-consolidation-audit |
| cleanup | 2026-05-29_cleanup-skill-upgrade |
| cleanup | 2026-05-28_translation-pass-non-en-locales |
| codex-law-translate | wikilinks |
| conquering-campaign | … |
| conquering-campaign | core-swarm |
| conquering-campaign | link |
| conquering-campaign | core-swarm |
| conquering-campaign | link |
| conquering-campaign | core-swarm |
| decompose-and-swarm | core-swarm |
| financial-data-reach | source-landscape |
| financial-data-reach | point-in-time-correctness |
| financial-data-reach | normalization-and-caching |
| financial-data-reach | normalization-and-caching |
| financial-data-reach | source-landscape |
| financial-data-reach | source-landscape |
| financial-data-reach | point-in-time-correctness |
| financial-data-reach | normalization-and-caching |
| head-of-department | core-swarm |
| head-of-department | core-swarm |
| helpless | butler-lockout |
| lex-system-audit | Vault Core |
| obsidian-markdown | Note |
| obsidian-markdown | embed |
| obsidian-markdown | wikilinks |
| obsidian-markdown | Note Name |
| obsidian-markdown | Note Name\|Display Text |
| obsidian-markdown | Note Name#Heading |
| obsidian-markdown | Note Name#^block-id |
| obsidian-markdown | #Heading in same note |
| obsidian-markdown | Note Name |
| obsidian-markdown | Note Name#Heading |
| obsidian-markdown | image.png |
| obsidian-markdown | image.png\|300 |
| obsidian-markdown | document.pdf#page=3 |
| obsidian-markdown | improve workflow |
| obsidian-markdown | Algorithm Notes#Sorting |
| obsidian-markdown | Architecture Diagram.png\|600 |
| obsidian-markdown | Meeting Notes 2024-01-10#Decisions |
| obsidian-markdown | wikilinks |
| obsidian-markdown | ADR-YYY Related Decision |
| obsidian-markdown | ADR-014 |
| obsidian-markdown | ADR-YYY Title |
| okf | name |
| portability-audit |  "$local_ver" != "$repo_ver"  |
| schema-evolution | verify-multiagent-audit |
| strategies-review | wikilinks |
| vault-log-compliance | wikilink |
| vault-log-writer | table_name |
| vault-log-writer | view_name |
| vault-log-writer | VIEWS-CATALOG |
| vault-log-writer | new_view_js |
| vault-log-writer | double-bracket |
| vault-log-writer | BACKEND |
| vault-log-writer | primary_instructions |
| vault-log-writer | affected_view |
| vault-log-writer | affected_table |
| vault-log-writer | YYYY-MM-DD_slug |

## Classification note

~30 of the wikilink-rot findings are **syntax examples** inside `obsidian-markdown/SKILL.md` (21) and `vault-log-writer/SKILL.md` (10) — those skills *document* the `[[wikilink]]` convention with literal placeholder names. They are not rot.

**Real rot, after filtering:**

- `cleanup` (4) — lesson-log note links
- `conquering-campaign` (6) — `[[core-swarm]]`, `[[decompose-and-swarm]]`, `[[weapon-utility]]`
- `financial-data-reach` (8)
- `helpless` (1)

Doc-ghost concentration:

- `obsidian-markdown` (13) — relative-path bug: skill cites `skills/obsidian-markdown/references/...` but files live at `references/...`
- `supabase` (6) — Supabase dashboard deep links with placeholder project refs
