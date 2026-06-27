---
type: Document
title: Skill Version Registry
description: Canonical version + Cowork-compliance status of every Star Alliance skill.
---
# Skill Version Registry

Canonical version + Cowork-compliance status of every skill. **Source of truth is
`metadata.version`** in each skill's `SKILL.md` frontmatter (a top-level `version:` is rejected by
the Agent Skills frontmatter validator — only `name, description, license, allowed-tools, metadata,
compatibility` are allowed). This table mirrors it. Regenerate with
`python3 star-alliance-skills/skillsmith/scripts/skill_registry.py write`.

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
| [`algorithmic-trading-chan`](star-alliance-skills/algorithmic-trading-chan/SKILL.md) | 1.0.0 | own | 116 / 960 | 1016 / 53 | ✓ lean | The Merchant's quant doctrine, distilled from Ernest Chan's Algorithmic Trading: Winning S… |
| [`arsenal-forge`](star-alliance-skills/arsenal-forge/SKILL.md) | 1.0.0 | own | 147 / 949 | 1106 / 58 | ✓ lean | The Strategist's craft for recruiting a new weapon (AI model) into the guild arsenal, or r… |
| [`article-creator`](star-alliance-skills/article-creator/SKILL.md) | 1.0.1 | own | 138 / 923 | 839 / 111 | ✓ lean | End-to-end procedure for creating a public Insights article and pushing it to the Lex Coun… |
| [`bug-fix-workflow`](star-alliance-skills/bug-fix-workflow/SKILL.md) | 1.2.0 | own | 151 / 934 | 2388 / 255 | ✓ lean | The Lex Council end-to-end bug workflow — pull reports from the bug_reports table, triage … |
| [`claude-code-hooks`](star-alliance-skills/claude-code-hooks/SKILL.md) | 1.1.0 | own | 146 / 962 | 1920 / 134 | ✓ lean | The Developer's craft for authoring Claude Code hooks — the shell scripts the harness fire… |
| [`cleanup`](star-alliance-skills/cleanup/SKILL.md) | 1.20.0 | own | 135 / 991 | 5594 / 330 | ○ large | Multi-mode hygiene skill for Lex Council |
| [`codex-law-translate`](star-alliance-skills/codex-law-translate/SKILL.md) | 1.1.0 | own | 134 / 908 | 2112 / 228 | ✓ lean | End-to-end pipeline for loading a real-world law into the Lex Council legal codex, transla… |
| [`comms-triage`](star-alliance-skills/comms-triage/SKILL.md) | 1.0.0 | own | 151 / 945 | 1052 / 60 | ✓ lean | The Butler's one hands-on craft beside routing — sweep email, calendar, and WhatsApp into … |
| [`conquering-campaign`](star-alliance-skills/conquering-campaign/SKILL.md) | 3.8.3 | own | 140 / 1001 | 10351 / 466 | ⚠ body>10k | Multi-wave campaign skill for work too big for one pass |
| [`dashboard-parity`](star-alliance-skills/dashboard-parity/SKILL.md) | 1.1.0 | own | 159 / 1008 | 1521 / 76 | ✓ lean | The Quartermaster's craft for proving a change actually reaches the rendered dashboard at … |
| [`db-rename-sweep`](star-alliance-skills/db-rename-sweep/SKILL.md) | 1.1.0 | own | 146 / 910 | 542 / 48 | ✓ lean | Loads the full surface inventory for any Lex Council table or column rename before the fir… |
| [`design-language`](star-alliance-skills/design-language/SKILL.md) | 1.0.0 | own | 152 / 1011 | 921 / 93 | ✓ lean | Pick and enforce a project's NARRATIVE VOICE — its vocabulary, lore, naming conventions, a… |
| [`design-taste`](star-alliance-skills/design-taste/SKILL.md) | 1.0.0 | own | 132 / 1012 | 1077 / 100 | ✓ lean | The Designer's core taste engine — one multi-mode skill replacing the guild's scattered st… |
| [`design-unity`](star-alliance-skills/design-unity/SKILL.md) | 1.1.0 | own | 159 / 1016 | 1274 / 107 | ✓ lean | The Designer's UI-unity guardian — make ONE design language the single source of truth and… |
| [`dev-server`](star-alliance-skills/dev-server/SKILL.md) | 1.1.0 | own | 46 / 303 | 645 / 73 | ✓ lean | Use this skill whenever the user says 'open dev server', 'run dev server', 'restart dev se… |
| [`full-output-enforcement`](star-alliance-skills/full-output-enforcement/SKILL.md) | 1.0.0 | own | 25 / 203 | 382 / 46 | ✓ lean | Overrides default LLM truncation behavior |
| [`graphify`](star-alliance-skills/graphify/SKILL.md) | 1.0.0 | own | 35 / 225 | 5904 / 1025 | ○ large | any input (code, docs, papers, images, videos) to knowledge graph |
| [`growth-marketing`](star-alliance-skills/growth-marketing/SKILL.md) | 1.0.0 | own | 110 / 851 | 2506 / 97 | ✓ lean | The Herald's marketing craft — turn a business's invisibility into a repeatable demand eng… |
| [`guild-conformity`](star-alliance-skills/guild-conformity/SKILL.md) | 1.4.1 | own | 131 / 916 | 2167 / 139 | ✓ lean | The Quartermaster's craft for proving the whole guild repo agrees with itself and with eve… |
| [`guild-log`](star-alliance-skills/guild-log/SKILL.md) | 1.2.1 | own | 118 / 801 | 2454 / 231 | ✓ lean | Enforce logging of non-git-visible changes to the Star Alliance guild log |
| [`guild-sync`](star-alliance-skills/guild-sync/SKILL.md) | 1.0.0 | own | 139 / 1014 | 671 / 82 | ✓ lean | The Quartermaster's device-parity craft — one sweep that proves every surface where the on… |
| [`harness-efficiency`](star-alliance-skills/harness-efficiency/SKILL.md) | 1.2.0 | own | 150 / 1010 | 1303 / 143 | ✓ lean | The Strategist's craft for proving the Star Alliance harness actually saves tokens and tim… |
| [`high-alert`](star-alliance-skills/high-alert/SKILL.md) | 1.0.0 | own | 88 / 577 | 292 / 29 | ✓ lean | The guild's session-event klaxon |
| [`image-to-code`](star-alliance-skills/image-to-code/SKILL.md) | 1.0.0 | own | 80 / 555 | 5735 / 1225 | ○ large | Elite website image-to-code skill for Codex |
| [`imagegen-frontend`](star-alliance-skills/imagegen-frontend/SKILL.md) | 1.0.0 | own | 139 / 985 | 819 / 77 | ✓ lean | The Designer's image-generation engine — generate premium design imagery with image-01, on… |
| [`impeccable`](star-alliance-skills/impeccable/SKILL.md) | 3.0.7 | external | 118 / 895 | 1793 / 173 | ✓ lean | Use when the user wants to design, redesign, shape, critique, audit, polish, clarify, dist… |
| [`invariant-inference`](star-alliance-skills/invariant-inference/SKILL.md) | 1.0.0 | own | 163 / 1125 | 672 / 51 | ✗ desc>1024 | The Architect's craft for data-driven invariant and rule synthesis, distilled from LoopInv… |
| [`japanese-candlesticks`](star-alliance-skills/japanese-candlesticks/SKILL.md) | 1.0.0 | own | 128 / 1012 | 965 / 60 | ✓ lean | The Merchant's read-only craft for reading Japanese candlestick charts, distilled from Ste… |
| [`law-harvest`](star-alliance-skills/law-harvest/SKILL.md) | 1.0.0 | own | 149 / 979 | 1152 / 63 | ✓ lean | The shared Architect + Translator craft for ingesting real law PDFs into a clean, verified… |
| [`legal-drafting`](star-alliance-skills/legal-drafting/SKILL.md) | 1.0.0 | own | 122 / 935 | 1156 / 54 | ✓ lean | The Translator's craft for drafting client correspondence and bilingual (Arabic/French/Eng… |
| [`legal-rule-modeling`](star-alliance-skills/legal-rule-modeling/SKILL.md) | 1.0.0 | own | 133 / 931 | 1447 / 64 | ✓ lean | The Architect's craft for modelling a governing law into the exact calculation rules and i… |
| [`market-recon`](star-alliance-skills/market-recon/SKILL.md) | 1.0.0 | own | 127 / 914 | 1115 / 55 | ✓ lean | The Merchant's craft for read-only market, investment, and risk analysis that ships a writ… |
| [`members-formation`](star-alliance-skills/members-formation/SKILL.md) | 1.1.1 | own | 141 / 883 | 1805 / 179 | ✓ lean | The Butler's routing method — match an incoming request to the right star-map workflow in … |
| [`motion-design`](star-alliance-skills/motion-design/SKILL.md) | 2.0.0 | own | 135 / 1018 | 1307 / 180 | ✓ lean | Two-mode motion & interaction design specialist for product UI |
| [`obsidian-markdown`](star-alliance-skills/obsidian-markdown/SKILL.md) | 1.0.0 | own | 36 / 262 | 610 / 163 | ✓ lean | Create and edit Obsidian Flavored Markdown with wikilinks, embeds, callouts, properties, a… |
| [`okf`](star-alliance-skills/okf/SKILL.md) | 1.2.0 | own | 76 / 512 | 1204 / 142 | ✓ lean | Keep the whole Star Alliance repo tidy and conformant to the Open Knowledge Format (OKF v0… |
| [`performance`](star-alliance-skills/performance/SKILL.md) | 1.0.3 | vendored | 32 / 219 | 1418 / 371 | ✓ lean | Optimize web performance for faster loading and better user experience |
| [`portability-audit`](star-alliance-skills/portability-audit/SKILL.md) | 1.0.0 | own | 75 / 481 | 578 / 104 | ✓ lean | Audit how portable a Claude Code project is — maps every layer (skills, members, hooks, en… |
| [`portfolio-risk`](star-alliance-skills/portfolio-risk/SKILL.md) | 0.1.0 | own | 129 / 1005 | 834 / 55 | ✓ lean | The Merchant's craft for read-only, book-level portfolio construction and risk measurement… |
| [`probability-statistics`](star-alliance-skills/probability-statistics/SKILL.md) | 1.0.0 | own | 171 / 1453 | 1139 / 65 | ✗ desc>1024 | The Merchant's read-only craft for probability and statistics, distilled from Evans & Rose… |
| [`project-start`](star-alliance-skills/project-start/SKILL.md) | 1.0.0 | own | 55 / 375 | 262 / 56 | ✓ lean | Start-of-session health check for projects that have Star Alliance members deployed |
| [`python-master`](star-alliance-skills/python-master/SKILL.md) | 1.0.0 | own | 134 / 1020 | 431 / 47 | ✓ lean | The Developer's craft for building production-grade Python libraries and web apps end to e… |
| [`relationship-intel`](star-alliance-skills/relationship-intel/SKILL.md) | 1.0.0 | own | 136 / 961 | 1072 / 55 | ✓ lean | The Herald's craft for turning email traffic into living relationship intelligence so the … |
| [`release-train`](star-alliance-skills/release-train/SKILL.md) | 1.0.1 | own | 135 / 902 | 1146 / 62 | ✓ lean | The Quartermaster's craft for closing out a body of work — merge every outstanding branch … |
| [`scheduled-watch`](star-alliance-skills/scheduled-watch/SKILL.md) | 1.0.0 | own | 134 / 909 | 1030 / 48 | ✓ lean | The Strategist's craft for defining an unattended task that runs on a cron cadence and res… |
| [`schema-evolution`](star-alliance-skills/schema-evolution/SKILL.md) | 1.1.0 | own | 152 / 1013 | 1750 / 139 | ✓ lean | The Architect's craft for evolving a structured data model without breaking what already r… |
| [`session-mining`](star-alliance-skills/session-mining/SKILL.md) | 1.3.0 | own | 144 / 1012 | 1439 / 169 | ✓ lean | Mine your own Claude session history for lessons, then turn them into ranked, verified upg… |
| [`skillsmith`](star-alliance-skills/skillsmith/SKILL.md) | 1.5.1 | own | 132 / 987 | 5253 / 165 | ○ large | Manage, sync, upgrade, create, and auto-evolve Star Alliance skills across the star-allian… |
| [`spec-driven-development`](star-alliance-skills/spec-driven-development/SKILL.md) | 1.0.0 | own | 135 / 993 | 1005 / 121 | ✓ lean | The Architect's discipline for building from an executable specification instead of vibe-c… |
| [`star-alliance-language`](star-alliance-skills/star-alliance-language/SKILL.md) | 1.2.0 | own | 84 / 522 | 912 / 111 | ✓ lean | The guild's shared reading protocol for OKF-tidied repos — how every member quickly, cheap… |
| [`storm-investigation`](star-alliance-skills/storm-investigation/SKILL.md) | 1.0.0 | own | 113 / 866 | 919 / 94 | ✓ lean | Multi-perspective deep-research method (Stanford STORM, NAACL 2024) for any topic — run fi… |
| [`strategies-review`](star-alliance-skills/strategies-review/SKILL.md) | 1.0.0 | own | 12 / 72 | 297 / 44 | ✓ lean | Review pending strategies and move them to executed then check the docs. |
| [`supabase`](star-alliance-skills/supabase/SKILL.md) | 0.1.2 | vendored | 58 / 475 | 1184 / 106 | ✓ lean | Use when doing ANY task involving Supabase |
| [`supabase-postgres-best-practices`](star-alliance-skills/supabase-postgres-best-practices/SKILL.md) | 1.1.1 | vendored | 23 / 183 | 242 / 54 | ✓ lean | Postgres performance optimization and best practices from Supabase |
| [`trading-strategy`](star-alliance-skills/trading-strategy/SKILL.md) | 0.1.0 | own | 139 / 1009 | 901 / 55 | ✓ lean | The Merchant's craft for read-only trading-strategy design that ships a written, dated str… |
| [`transactions-domain-model`](star-alliance-skills/transactions-domain-model/SKILL.md) | 1.3.1 | own | 108 / 951 | 3263 / 399 | ✓ lean | Loads the complete Lex Council transactions domain model before any transaction-related wo… |
| [`ultra-brainstorming`](star-alliance-skills/ultra-brainstorming/SKILL.md) | 1.3.0 | own | 129 / 873 | 2028 / 191 | ✓ lean | An ASSIGNABLE multi-thinker method — any member who carries it fires ALL his available thi… |
| [`vault-log-compliance`](star-alliance-skills/vault-log-compliance/SKILL.md) | 1.1.0 | own | 128 / 807 | 1445 / 119 | ✓ lean | Enforces P8 vault-logging compliance for Lex Council |
| [`volume-price-analysis`](star-alliance-skills/volume-price-analysis/SKILL.md) | 1.0.0 | own | 137 / 1020 | 1067 / 55 | ✓ lean | The Merchant's read-only craft for Volume Price Analysis, distilled from Anna Coulling's A… |
| [`weapon-utility`](star-alliance-skills/weapon-utility/SKILL.md) | 2.1.0 | own | 166 / 1009 | 3516 / 256 | ✓ lean | Every member's rule for which weapon (model) to draw and how thinker and doer weapons work… |
| [`workflow-forge`](star-alliance-skills/workflow-forge/SKILL.md) | 1.3.0 | own | 153 / 997 | 1701 / 102 | ✓ lean | The Strategist's craft for distilling a finished run into a reusable star-map workflow in … |

_61 skills — 54 lean · 4 large (installable, over the 500-line ideal) · 1 near the word ceiling · 2 hard violations._
