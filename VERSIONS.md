# Skill Version Registry

Canonical version + Cowork-compliance status of every skill. **Source of truth is
`metadata.version`** in each skill's `SKILL.md` frontmatter (a top-level `version:` is rejected by
the Agent Skills frontmatter validator — only `name, description, license, allowed-tools, metadata,
compatibility` are allowed). This table mirrors it. Regenerate with
`python3 skillsmith/scripts/skill_registry.py write`.

## Cowork limits

| Limit | Rule | Source |
|---|---|---|
| **description** | **≤ 1024 characters** (hard — frontmatter validation reject above it) | Anthropic Agent Skills frontmatter spec |
| **SKILL.md body** | **< 500 lines ideal** (soft — add hierarchy + `references/` pointers as you approach it) | `skill-creator` authoring guidance |
| **SKILL.md body** | **keep well under ~10k words** for the Cowork installer (a 15,342-word file is known to fail; references/ bundled files do NOT count) | empirical (`cleanup` §1.9.0) |

**Status:** `✓ lean` = within all · `○ large` = installable but over the 500-line ideal or 5k+ words (trim candidate) · `⚠ body>10k` = near/over the empirical Cowork word ceiling — lean-pass candidate · `✗ desc>1024` / `✗ desc<>` = hard violations (too long / contains angle brackets), will reject.

**On any change:** bump the skill's `version:`, regenerate this file, keep the description ≤1024 chars, and prefer pushing detail into `references/` over growing SKILL.md. See [`README.md`](README.md).

> Every skill records its version under `metadata.version`. Vendored/external skills came with one
> upstream; our own skills set it explicitly. `impeccable` is external (npx-managed) and still ships a
> top-level `version:` — the reader falls back to it; don't hand-edit it to satisfy the validator.

| Skill | Ver | Src | Desc (words / chars) | Body (words / lines) | Cowork | What it does |
|---|---|---|---|---|---|---|---|
| [`article-creator`](star-alliance-skills/article-creator/SKILL.md) | 1.0.1 | own | 138 / 923 | 839 / 112 | ✓ lean | End-to-end procedure for creating a public Insights article and pushing it to the Lex Coun… |
| [`brandkit`](star-alliance-skills/brandkit/SKILL.md) | 1.0.0 | own | 52 / 464 | 2543 / 796 | ○ large | Premium brand-kit image generation skill for creating high-end brand-guidelines boards, lo… |
| [`bug-fix-workflow`](star-alliance-skills/bug-fix-workflow/SKILL.md) | 1.1.3 | own | 151 / 934 | 1939 / 226 | ✓ lean | The Lex Council end-to-end bug workflow — pull reports from the bug_reports table, triage … |
| [`cleanup`](star-alliance-skills/cleanup/SKILL.md) | 1.20.0 | own | 135 / 991 | 5594 / 331 | ○ large | Multi-mode hygiene skill for Lex Council |
| [`codex-law-translate`](star-alliance-skills/codex-law-translate/SKILL.md) | 1.1.0 | own | 134 / 908 | 2112 / 229 | ✓ lean | End-to-end pipeline for loading a real-world law into the Lex Council legal codex, transla… |
| [`conquering-campaign`](star-alliance-skills/conquering-campaign/SKILL.md) | 3.8.3 | own | 140 / 1001 | 10351 / 467 | ⚠ body>10k | Multi-wave campaign skill for work too big for one pass |
| [`db-rename-sweep`](star-alliance-skills/db-rename-sweep/SKILL.md) | 1.1.0 | own | 146 / 910 | 542 / 49 | ✓ lean | Loads the full surface inventory for any Lex Council table or column rename before the fir… |
| [`design-taste-frontend`](star-alliance-skills/design-taste-frontend/SKILL.md) | 1.0.0 | own | 23 / 202 | 2896 / 224 | ✓ lean | Senior UI/UX Engineer |
| [`dev-server`](star-alliance-skills/dev-server/SKILL.md) | 1.1.0 | own | 46 / 303 | 645 / 74 | ✓ lean | Use this skill whenever the user says 'open dev server', 'run dev server', 'restart dev se… |
| [`fallen-sword-design-language`](star-alliance-skills/fallen-sword-design-language/SKILL.md) | — | own | 52 / 329 | 1976 / 286 | ✓ lean | The vocabulary, mechanics, and lore of Fallen Sword — a classic browser-based MMORPG set i… |
| [`full-output-enforcement`](star-alliance-skills/full-output-enforcement/SKILL.md) | 1.0.0 | own | 25 / 203 | 382 / 47 | ✓ lean | Overrides default LLM truncation behavior |
| [`gpt-taste`](star-alliance-skills/gpt-taste/SKILL.md) | 1.0.0 | own | 39 / 312 | 1090 / 72 | ✓ lean | Elite UX/UI & Advanced GSAP Motion Engineer |
| [`graphify`](star-alliance-skills/graphify/SKILL.md) | 1.0.0 | own | 35 / 225 | 5904 / 1026 | ○ large | any input (code, docs, papers, images, videos) to knowledge graph |
| [`growth-marketing`](star-alliance-skills/growth-marketing/SKILL.md) | 1.0.0 | own | 108 / 829 | 2490 / 98 | ✓ lean | The Herald's marketing craft — turn a business's invisibility into a repeatable demand eng… |
| [`guild-log`](star-alliance-skills/guild-log/SKILL.md) | 1.2.1 | own | 118 / 801 | 2454 / 232 | ✓ lean | Enforce logging of non-git-visible changes to the Star Alliance guild log |
| [`high-end-visual-design`](star-alliance-skills/high-end-visual-design/SKILL.md) | 1.0.0 | own | 38 / 234 | 1413 / 96 | ✓ lean | Teaches the AI to design like a high-end agency |
| [`image-to-code`](star-alliance-skills/image-to-code/SKILL.md) | 1.0.0 | own | 80 / 555 | 5735 / 1226 | ○ large | Elite website image-to-code skill for Codex |
| [`imagegen-frontend-mobile`](star-alliance-skills/imagegen-frontend-mobile/SKILL.md) | 1.0.0 | own | 87 / 638 | 6460 / 1463 | ○ large | Elite mobile app image-generation skill for creating premium, app-native screen concepts a… |
| [`imagegen-frontend-web`](star-alliance-skills/imagegen-frontend-web/SKILL.md) | 1.0.0 | own | 90 / 661 | 5724 / 985 | ○ large | Elite frontend image-direction skill for generating premium, conversion-aware website desi… |
| [`impeccable`](star-alliance-skills/impeccable/SKILL.md) | 3.0.7 | external | 118 / 895 | 1793 / 173 | ✓ lean | Use when the user wants to design, redesign, shape, critique, audit, polish, clarify, dist… |
| [`industrial-brutalist-ui`](star-alliance-skills/industrial-brutalist-ui/SKILL.md) | 1.0.0 | own | 36 / 286 | 1034 / 90 | ✓ lean | Raw mechanical interfaces fusing Swiss typographic print with military terminal aesthetics |
| [`members-formation`](star-alliance-skills/members-formation/SKILL.md) | 1.0.2 | own | 132 / 825 | 1356 / 152 | ✓ lean | The Butler's routing method — turn any mission into a formation: which member owns each sl… |
| [`minimalist-ui`](star-alliance-skills/minimalist-ui/SKILL.md) | 1.0.0 | own | 18 / 145 | 1066 / 83 | ✓ lean | Clean editorial-style interfaces |
| [`obsidian-markdown`](star-alliance-skills/obsidian-markdown/SKILL.md) | 1.0.0 | own | 36 / 262 | 610 / 164 | ✓ lean | Create and edit Obsidian Flavored Markdown with wikilinks, embeds, callouts, properties, a… |
| [`performance`](star-alliance-skills/performance/SKILL.md) | 1.0.3 | vendored | 32 / 219 | 1418 / 372 | ✓ lean | Optimize web performance for faster loading and better user experience |
| [`redesign-existing-projects`](star-alliance-skills/redesign-existing-projects/SKILL.md) | 1.0.0 | own | 31 / 225 | 2174 / 176 | ✓ lean | Upgrades existing websites and apps to premium quality |
| [`skillsmith`](star-alliance-skills/skillsmith/SKILL.md) | 1.2.0 | own | 132 / 987 | 3768 / 139 | ✓ lean | Manage, sync, upgrade, create, and auto-evolve Star Alliance skills across the star-allian… |
| [`stitch-design-taste`](star-alliance-skills/stitch-design-taste/SKILL.md) | 1.0.0 | own | 29 / 257 | 1628 / 182 | ✓ lean | Semantic Design System Skill for Google Stitch |
| [`storm-investigation`](star-alliance-skills/storm-investigation/SKILL.md) | 1.0.0 | own | 113 / 866 | 919 / 95 | ✓ lean | Multi-perspective deep-research method (Stanford STORM, NAACL 2024) for any topic — run fi… |
| [`strategies-review`](star-alliance-skills/strategies-review/SKILL.md) | 1.0.0 | own | 12 / 72 | 297 / 45 | ✓ lean | Review pending strategies and move them to executed then check the docs. |
| [`supabase`](star-alliance-skills/supabase/SKILL.md) | 0.1.2 | vendored | 58 / 475 | 1184 / 107 | ✓ lean | Use when doing ANY task involving Supabase |
| [`supabase-postgres-best-practices`](star-alliance-skills/supabase-postgres-best-practices/SKILL.md) | 1.1.1 | vendored | 23 / 183 | 242 / 55 | ✓ lean | Postgres performance optimization and best practices from Supabase |
| [`transactions-domain-model`](star-alliance-skills/transactions-domain-model/SKILL.md) | 1.3.1 | own | 108 / 951 | 3263 / 400 | ✓ lean | Loads the complete Lex Council transactions domain model before any transaction-related wo… |
| [`ultra-brainstorming`](star-alliance-skills/ultra-brainstorming/SKILL.md) | 1.0.0 | own | 128 / 865 | 926 / 109 | ✓ lean | The Strategist's super-planning method — fuse the outputs of several members into one doer… |
| [`vault-log-compliance`](star-alliance-skills/vault-log-compliance/SKILL.md) | 1.1.0 | own | 128 / 807 | 1445 / 120 | ✓ lean | Enforces P8 vault-logging compliance for Lex Council |
| [`weapon-utility`](star-alliance-skills/weapon-utility/SKILL.md) | 1.0.0 | own | 152 / 922 | 926 / 110 | ✓ lean | Every member's rule for which weapon (model) to draw and how thinker and doer weapons work… |

_36 skills — 29 lean · 6 large (installable, over the 500-line ideal) · 1 near the word ceiling · 0 hard violations._
