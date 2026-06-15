# Skill Version Registry

Canonical version of every skill in this repo. The **source of truth is the top-level `version:`
field in each skill's `SKILL.md` frontmatter** — this table mirrors it for at-a-glance diffing.

**On any skill change:** bump its `version:` (SemVer — PATCH = fix/wording, MINOR = new
backward-compatible capability, MAJOR = breaking workflow change), then update the matching row
here in the same commit. See [`README.md`](README.md) for the full convention.

> `vendored` skills carry an upstream `metadata.version` (provenance); the top-level `version:`
> is *our* tracked version and is what this registry records.

| Skill | Version | Source | What it does |
|---|---|---|---|
| [`article-creator`](article-creator/SKILL.md) | 1.0.0 | own | End-to-end procedure for creating a public Insights article and pushing it to the Lex Council production DB… |
| [`brandkit`](brandkit/SKILL.md) | 1.0.0 | own | Premium brand-kit image generation skill for creating high-end brand-guidelines boards, logo systems, ident… |
| [`bug-fix-workflow`](bug-fix-workflow/SKILL.md) | 1.0.0 | own | The Lex Council end-to-end bug workflow — pull reports from the bug_reports table, triage their status, inv… |
| [`cleanup`](cleanup/SKILL.md) | 1.14.0 | own | Multi-mode hygiene skill for Lex Council |
| [`codex-law-translate`](codex-law-translate/SKILL.md) | 1.0.0 | own | End-to-end pipeline for loading a real-world law into the Lex Council legal codex, translated into all 5 no… |
| [`conquering-campaign`](conquering-campaign/SKILL.md) | 3.8.1 | own | Multi-wave campaign skill for work too big for one pass |
| [`db-rename-sweep`](db-rename-sweep/SKILL.md) | 1.0.0 | own | Loads the full surface inventory for any Lex Council table or column rename before the first migration line… |
| [`design-taste-frontend`](design-taste-frontend/SKILL.md) | 1.0.0 | own | Senior UI/UX Engineer |
| [`dev-server`](dev-server/SKILL.md) | 1.0.0 | own | Use this skill whenever the user says 'open dev server', 'run dev server', 'restart dev server', 'start the… |
| [`full-output-enforcement`](full-output-enforcement/SKILL.md) | 1.0.0 | own | Overrides default LLM truncation behavior |
| [`gpt-taste`](gpt-taste/SKILL.md) | 1.0.0 | own | Elite UX/UI & Advanced GSAP Motion Engineer |
| [`graphify`](graphify/SKILL.md) | 1.0.0 | own | any input (code, docs, papers, images, videos) to knowledge graph |
| [`high-end-visual-design`](high-end-visual-design/SKILL.md) | 1.0.0 | own | Teaches the AI to design like a high-end agency |
| [`image-to-code`](image-to-code/SKILL.md) | 1.0.0 | own | Elite website image-to-code skill for Codex |
| [`imagegen-frontend-mobile`](imagegen-frontend-mobile/SKILL.md) | 1.0.0 | own | Elite mobile app image-generation skill for creating premium, app-native screen concepts and flows |
| [`imagegen-frontend-web`](imagegen-frontend-web/SKILL.md) | 1.0.0 | own | Elite frontend image-direction skill for generating premium, conversion-aware website design references |
| [`impeccable`](impeccable/SKILL.md) | 3.0.7 | external (npx impeccable) | Use when the user wants to design, redesign, shape, critique, audit, polish, clarify, distill, harden, opti… |
| [`industrial-brutalist-ui`](industrial-brutalist-ui/SKILL.md) | 1.0.0 | own | Raw mechanical interfaces fusing Swiss typographic print with military terminal aesthetics |
| [`minimalist-ui`](minimalist-ui/SKILL.md) | 1.0.0 | own | Clean editorial-style interfaces |
| [`obsidian-markdown`](obsidian-markdown/SKILL.md) | 1.0.0 | own | Create and edit Obsidian Flavored Markdown with wikilinks, embeds, callouts, properties, and other Obsidian… |
| [`performance`](performance/SKILL.md) | 1.0.0 | vendored (web-quality-skills) | Optimize web performance for faster loading and better user experience |
| [`redesign-existing-projects`](redesign-existing-projects/SKILL.md) | 1.0.0 | own | Upgrades existing websites and apps to premium quality |
| [`stitch-design-taste`](stitch-design-taste/SKILL.md) | 1.0.0 | own | Semantic Design System Skill for Google Stitch |
| [`strategies-review`](strategies-review/SKILL.md) | 1.0.0 | own | Review pending strategies and move them to executed then check the docs. |
| [`supabase`](supabase/SKILL.md) | 0.1.2 | vendored (Supabase) | Use when doing ANY task involving Supabase |
| [`supabase-postgres-best-practices`](supabase-postgres-best-practices/SKILL.md) | 1.1.1 | vendored (Supabase) | Postgres performance optimization and best practices from Supabase |
| [`transactions-domain-model`](transactions-domain-model/SKILL.md) | 1.0.0 | own | Loads the complete Lex Council transactions domain model before any transaction-related work begins |
| [`vault-log-compliance`](vault-log-compliance/SKILL.md) | 1.0.0 | own | Enforces P8 vault-logging compliance for Lex Council |

_28 skills • last synced 2026-06-15._
