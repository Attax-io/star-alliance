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
| [`a11y-craft`](star-alliance-skills/a11y-craft/SKILL.md) | 1.0.0 | own | 146 / 981 | 519 / 56 | ✓ lean | The Designer's accessibility craft — make WCAG 2.2 AA a gate every surface clears before i… |
| [`add-admin-permission`](star-alliance-skills/add-admin-permission/SKILL.md) | 1.0.0 | own | 131 / 732 | 1819 / 312 | ✓ lean | Add a new granular permission flag to admin_perms in the Lex Council app and wire it throu… |
| [`add-new-trigger`](star-alliance-skills/add-new-trigger/SKILL.md) | 1.0.0 | own | 124 / 844 | 1209 / 248 | ✓ lean | End-to-end procedure for creating or modifying a database trigger and its backing function… |
| [`add-new-view`](star-alliance-skills/add-new-view/SKILL.md) | 1.0.0 | own | 131 / 842 | 957 / 154 | ✓ lean | End-to-end procedure for creating or revising a view in the Lex Council Supabase backend |
| [`admin-page-builder`](star-alliance-skills/admin-page-builder/SKILL.md) | 1.0.0 | own | 121 / 724 | 2112 / 425 | ✓ lean | Build a new admin page for the Lex Council app under apps/web/app/(admin)/admin/ |
| [`admin-page-fixer`](star-alliance-skills/admin-page-fixer/SKILL.md) | 1.0.0 | own | 107 / 706 | 2206 / 331 | ✓ lean | Fix bugs and warnings found by the admin-page-auditor skill (or manually identified) acros… |
| [`agent-web-reach`](star-alliance-skills/agent-web-reach/SKILL.md) | 1.1.0 | own | 113 / 813 | 1138 / 136 | ✓ lean | Give an agent reliable internet reach — pull content from platforms that normally block ag… |
| [`agentic-video-production`](star-alliance-skills/agentic-video-production/SKILL.md) | 1.1.0 | own | 113 / 895 | 942 / 112 | ✓ lean | Produce finished video agentically from a plain-language brief: the agent runs research, p… |
| [`algorithmic-trading-chan`](star-alliance-skills/algorithmic-trading-chan/SKILL.md) | 1.0.0 | own | 116 / 960 | 1016 / 53 | ✓ lean | The Merchant's quant doctrine, distilled from Ernest Chan's Algorithmic Trading: Winning S… |
| [`api-integration-design`](star-alliance-skills/api-integration-design/SKILL.md) | 1.0.0 | own | 114 / 895 | 1159 / 101 | ✓ lean | The Architect's craft for the API and integration boundary — designing the service contrac… |
| [`arsenal-forge`](star-alliance-skills/arsenal-forge/SKILL.md) | 1.0.0 | own | 147 / 949 | 1106 / 58 | ✓ lean | The Strategist's craft for recruiting a new weapon (AI model) into the guild arsenal, or r… |
| [`article-creator`](star-alliance-skills/article-creator/SKILL.md) | 1.0.1 | own | 138 / 923 | 839 / 111 | ✓ lean | End-to-end procedure for creating a public Insights article and pushing it to the Lex Coun… |
| [`automated-testing`](star-alliance-skills/automated-testing/SKILL.md) | 1.1.0 | own | 119 / 810 | 1868 / 206 | ✓ lean | Author automated tests for a modern web app — the JS/TS plus application layer, grounded i… |
| [`bug-fix-workflow`](star-alliance-skills/bug-fix-workflow/SKILL.md) | 1.2.0 | own | 151 / 934 | 2388 / 255 | ✓ lean | The Lex Council end-to-end bug workflow — pull reports from the bug_reports table, triage … |
| [`chart-patterns`](star-alliance-skills/chart-patterns/SKILL.md) | 1.0.0 | own | 130 / 1012 | 1106 / 66 | ✓ lean | The Merchant's read-only craft for identifying and interpreting chart patterns, distilled … |
| [`claude-code-hooks`](star-alliance-skills/claude-code-hooks/SKILL.md) | 1.1.0 | own | 146 / 962 | 1920 / 134 | ✓ lean | The Developer's craft for authoring Claude Code hooks — the shell scripts the harness fire… |
| [`cleanup`](star-alliance-skills/cleanup/SKILL.md) | 1.20.0 | own | 135 / 991 | 5594 / 330 | ○ large | Multi-mode hygiene skill for Lex Council |
| [`cn-market-strategy-pack`](star-alliance-skills/cn-market-strategy-pack/SKILL.md) | 1.1.0 | own | 111 / 898 | 1094 / 123 | ✓ lean | The Merchant's read-only pack of 15 named CN/HK/US/JP/KR-market stock strategies distilled… |
| [`code-review-craft`](star-alliance-skills/code-review-craft/SKILL.md) | 1.1.0 | own | 123 / 769 | 1178 / 134 | ✓ lean | A deliberate, member-invoked code review of a diff, PR, or file |
| [`codebase-memory-mcp`](star-alliance-skills/codebase-memory-mcp/SKILL.md) | 1.2.0 | own | 139 / 1014 | 1337 / 167 | ✓ lean | Use this MCP code-intelligence engine to answer structural questions about a real reposito… |
| [`codex-law-translate`](star-alliance-skills/codex-law-translate/SKILL.md) | 1.1.0 | own | 134 / 908 | 2112 / 228 | ✓ lean | End-to-end pipeline for loading a real-world law into the Lex Council legal codex, transla… |
| [`comms-triage`](star-alliance-skills/comms-triage/SKILL.md) | 1.0.0 | own | 151 / 945 | 1052 / 60 | ✓ lean | The Butler's one hands-on craft beside routing — sweep email, calendar, and WhatsApp into … |
| [`conquering-campaign`](star-alliance-skills/conquering-campaign/SKILL.md) | 3.9.0 | own | 143 / 1015 | 7346 / 389 | ○ large | Multi-wave campaign skill for work too big for one pass |
| [`contract-review`](star-alliance-skills/contract-review/SKILL.md) | 1.0.0 | own | 128 / 896 | 1103 / 113 | ✓ lean | The Translator's inbound-review craft: read a contract or NDA the other side drafted, find… |
| [`dashboard-parity`](star-alliance-skills/dashboard-parity/SKILL.md) | 1.1.0 | own | 159 / 1008 | 1521 / 76 | ✓ lean | The Quartermaster's craft for proving a change actually reaches the rendered dashboard at … |
| [`data-analysis-viz`](star-alliance-skills/data-analysis-viz/SKILL.md) | 1.0.0 | own | 132 / 886 | 1264 / 39 | ✓ lean | The Merchant's craft for turning a raw dataset — a CSV, a query result, a table — into an … |
| [`db-rename-sweep`](star-alliance-skills/db-rename-sweep/SKILL.md) | 1.1.0 | own | 146 / 910 | 542 / 48 | ✓ lean | Loads the full surface inventory for any Lex Council table or column rename before the fir… |
| [`decompose-and-swarm`](star-alliance-skills/decompose-and-swarm/SKILL.md) | 1.0.0 | own | 89 / 630 | 1740 / 165 | ✓ lean | The Butler's swarm craft — judge whether a task is worth parallelising, scout the codebase… |
| [`design-language`](star-alliance-skills/design-language/SKILL.md) | 1.0.0 | own | 152 / 1011 | 921 / 93 | ✓ lean | Pick and enforce a project's NARRATIVE VOICE — its vocabulary, lore, naming conventions, a… |
| [`design-taste`](star-alliance-skills/design-taste/SKILL.md) | 1.0.0 | own | 132 / 1012 | 1077 / 100 | ✓ lean | The Designer's core taste engine — one multi-mode skill replacing the guild's scattered st… |
| [`design-taste-frontend`](star-alliance-skills/design-taste-frontend/SKILL.md) | 1.0.0 | own | 23 / 202 | 2896 / 224 | ✓ lean | Senior UI/UX Engineer |
| [`design-tokens`](star-alliance-skills/design-tokens/SKILL.md) | 1.0.0 | own | 132 / 1003 | 532 / 58 | ✓ lean | The Designer's token-architecture craft — structure a design-token system that scales, the… |
| [`design-unity`](star-alliance-skills/design-unity/SKILL.md) | 1.1.0 | own | 159 / 1016 | 1274 / 107 | ✓ lean | The Designer's UI-unity guardian — make ONE design language the single source of truth and… |
| [`dev-ops-command-pack`](star-alliance-skills/dev-ops-command-pack/SKILL.md) | 1.0.0 | own | 107 / 768 | 816 / 90 | ✓ lean | Run a disciplined dev-ops command lifecycle as one gated loop: start work, validate before… |
| [`dev-server`](star-alliance-skills/dev-server/SKILL.md) | 1.1.0 | own | 46 / 303 | 645 / 73 | ✓ lean | Use this skill whenever the user says 'open dev server', 'run dev server', 'restart dev se… |
| [`dual-model-review`](star-alliance-skills/dual-model-review/SKILL.md) | 1.0.0 | own | 123 / 826 | 2431 / 370 | ✓ lean | The dual-review flow that backs the cross-system bridge |
| [`file-access-model`](star-alliance-skills/file-access-model/SKILL.md) | 1.0.0 | own | 109 / 762 | 616 / 73 | ✓ lean | Loads full context for the Lex Council file access model before any related work begins |
| [`financial-data-reach`](star-alliance-skills/financial-data-reach/SKILL.md) | 1.0.0 | own | 128 / 844 | 1412 / 66 | ✓ lean | The Merchant's data-layer craft: acquire and clean the financial data his read-only analys… |
| [`frontend-react-engineering`](star-alliance-skills/frontend-react-engineering/SKILL.md) | 1.1.0 | own | 101 / 842 | 1584 / 152 | ✓ lean | Production React / Next.js engineering craft for the-developer: component architecture, ho… |
| [`full-output-enforcement`](star-alliance-skills/full-output-enforcement/SKILL.md) | 1.0.0 | own | 25 / 203 | 382 / 46 | ✓ lean | Overrides default LLM truncation behavior |
| [`gpt-taste`](star-alliance-skills/gpt-taste/SKILL.md) | 1.0.0 | own | 39 / 312 | 1090 / 72 | ✓ lean | Elite UX/UI & Advanced GSAP Motion Engineer |
| [`graphify`](star-alliance-skills/graphify/SKILL.md) | 1.0.0 | own | 35 / 225 | 5904 / 1025 | ○ large | any input (code, docs, papers, images, videos) to knowledge graph |
| [`growth-marketing`](star-alliance-skills/growth-marketing/SKILL.md) | 1.0.0 | own | 110 / 851 | 2506 / 97 | ✓ lean | The Herald's marketing craft — turn a business's invisibility into a repeatable demand eng… |
| [`guild-conformity`](star-alliance-skills/guild-conformity/SKILL.md) | 1.6.0 | own | 131 / 916 | 2792 / 188 | ✓ lean | The Quartermaster's craft for proving the whole guild repo agrees with itself and with eve… |
| [`guild-log`](star-alliance-skills/guild-log/SKILL.md) | 1.2.1 | own | 118 / 801 | 2454 / 231 | ✓ lean | Enforce logging of non-git-visible changes to the Star Alliance guild log |
| [`guild-reflection`](star-alliance-skills/guild-reflection/SKILL.md) | 1.1.0 | own | 148 / 1020 | 1295 / 134 | ✓ lean | The Quartermaster's self-improvement engine — turn finished work into durable guild upgrad… |
| [`guild-sync`](star-alliance-skills/guild-sync/SKILL.md) | 1.0.1 | own | 139 / 1014 | 742 / 83 | ✓ lean | The Quartermaster's device-parity craft — one sweep that proves every surface where the on… |
| [`harness-efficiency`](star-alliance-skills/harness-efficiency/SKILL.md) | 1.3.0 | own | 150 / 1010 | 1505 / 161 | ✓ lean | The Strategist's craft for proving the Star Alliance harness actually saves tokens and tim… |
| [`high-alert`](star-alliance-skills/high-alert/SKILL.md) | 2.3.0 | own | 132 / 886 | 752 / 54 | ✓ lean | The guild's deployment brief |
| [`high-end-visual-design`](star-alliance-skills/high-end-visual-design/SKILL.md) | 1.0.0 | own | 38 / 234 | 1413 / 96 | ✓ lean | Teaches the AI to design like a high-end agency |
| [`image-to-code`](star-alliance-skills/image-to-code/SKILL.md) | 1.0.0 | own | 80 / 555 | 5735 / 1225 | ○ large | Elite website image-to-code skill for Codex |
| [`imagegen-frontend`](star-alliance-skills/imagegen-frontend/SKILL.md) | 1.0.0 | own | 139 / 985 | 819 / 77 | ✓ lean | The Designer's image-generation engine — generate premium design imagery with image-01, on… |
| [`impeccable`](star-alliance-skills/impeccable/SKILL.md) | 3.0.7 | external | 118 / 895 | 1793 / 173 | ✓ lean | Use when the user wants to design, redesign, shape, critique, audit, polish, clarify, dist… |
| [`industrial-brutalist-ui`](star-alliance-skills/industrial-brutalist-ui/SKILL.md) | 1.0.0 | own | 36 / 286 | 1034 / 90 | ✓ lean | Raw mechanical interfaces fusing Swiss typographic print with military terminal aesthetics |
| [`invariant-inference`](star-alliance-skills/invariant-inference/SKILL.md) | 1.0.0 | own | 150 / 1022 | 672 / 51 | ✓ lean | The Architect's craft for data-driven invariant and rule synthesis, distilled from LoopInv… |
| [`japanese-candlesticks`](star-alliance-skills/japanese-candlesticks/SKILL.md) | 1.0.0 | own | 128 / 1012 | 965 / 60 | ✓ lean | The Merchant's read-only craft for reading Japanese candlestick charts, distilled from Ste… |
| [`law-harvest`](star-alliance-skills/law-harvest/SKILL.md) | 1.0.0 | own | 149 / 979 | 1152 / 63 | ✓ lean | The shared Architect + Translator craft for ingesting real law PDFs into a clean, verified… |
| [`leaders-command`](star-alliance-skills/leaders-command/SKILL.md) | 1.0.0 | own | 130 / 967 | 898 / 105 | ✓ lean | The Butler's down-command craft — take the Guild Master's words and re-issue them to a mem… |
| [`legal-drafting`](star-alliance-skills/legal-drafting/SKILL.md) | 1.0.0 | own | 122 / 935 | 1156 / 54 | ✓ lean | The Translator's craft for drafting client correspondence and bilingual (Arabic/French/Eng… |
| [`legal-rule-modeling`](star-alliance-skills/legal-rule-modeling/SKILL.md) | 1.0.0 | own | 133 / 931 | 1447 / 64 | ✓ lean | The Architect's craft for modelling a governing law into the exact calculation rules and i… |
| [`letting-go`](star-alliance-skills/letting-go/SKILL.md) | 1.0.1 | own | 157 / 1005 | 444 / 52 | ✓ lean | A universal guardrail that kills retry-storms, perfectionism paralysis, and over-deliberat… |
| [`lex-system-audit`](star-alliance-skills/lex-system-audit/SKILL.md) | 1.0.0 | own | 146 / 1019 | 1967 / 251 | ✓ lean | Methodology for auditing any backend subsystem in Lex Council — surveys schema, RLS, trigg… |
| [`market-recon`](star-alliance-skills/market-recon/SKILL.md) | 1.0.0 | own | 127 / 914 | 1115 / 55 | ✓ lean | The Merchant's craft for read-only market, investment, and risk analysis that ships a writ… |
| [`members-formation`](star-alliance-skills/members-formation/SKILL.md) | 1.3.0 | own | 141 / 883 | 2318 / 228 | ✓ lean | The Butler's routing method — match an incoming request to the right star-map workflow in … |
| [`metamorphosis-check`](star-alliance-skills/metamorphosis-check/SKILL.md) | 1.0.1 | own | 163 / 1007 | 408 / 52 | ✓ lean | A guardrail that catches the most dangerous agent failure: confidently running the OLD pla… |
| [`minimalist-ui`](star-alliance-skills/minimalist-ui/SKILL.md) | 1.0.0 | own | 18 / 145 | 1066 / 83 | ✓ lean | Clean editorial-style interfaces |
| [`motion-design`](star-alliance-skills/motion-design/SKILL.md) | 2.0.0 | own | 135 / 1018 | 1307 / 180 | ✓ lean | Two-mode motion & interaction design specialist for product UI |
| [`multimodal-model-wrappers`](star-alliance-skills/multimodal-model-wrappers/SKILL.md) | 1.1.0 | own | 125 / 891 | 1470 / 154 | ✓ lean | Craft for building a unified, multi-provider model abstraction — one stable call surface (… |
| [`negotiation-deal-strategy`](star-alliance-skills/negotiation-deal-strategy/SKILL.md) | 1.0.0 | own | 116 / 861 | 1150 / 56 | ✓ lean | The Herald's deal craft — strategize and draft a business negotiation from prep to close, … |
| [`obedience`](star-alliance-skills/obedience/SKILL.md) | 1.0.0 | own | 202 / 1288 | 1886 / 218 | ✗ desc>1024 | A turn-level discipline skill that constrains an agent to the literal scope of the user's … |
| [`observability-incident-response`](star-alliance-skills/observability-incident-response/SKILL.md) | 1.1.0 | own | 118 / 856 | 1416 / 165 | ✓ lean | Keep a live service observable and respond when it breaks |
| [`obsidian-markdown`](star-alliance-skills/obsidian-markdown/SKILL.md) | 1.1.0 | own | 61 / 448 | 915 / 228 | ✓ lean | Create and edit Obsidian Flavored Markdown with wikilinks, embeds, callouts, properties, a… |
| [`okf`](star-alliance-skills/okf/SKILL.md) | 1.2.0 | own | 76 / 512 | 1204 / 142 | ✓ lean | Keep the whole Star Alliance repo tidy and conformant to the Open Knowledge Format (OKF v0… |
| [`pattern-library-discovery`](star-alliance-skills/pattern-library-discovery/SKILL.md) | 1.0.0 | own | 114 / 896 | 944 / 111 | ✓ lean | Build and query a reusable code-pattern library so agents reuse a proven, security-validat… |
| [`penpot-design-platform`](star-alliance-skills/penpot-design-platform/SKILL.md) | 1.0.0 | own | 112 / 885 | 711 / 95 | ✓ lean | Drive Penpot, the open-source design and prototyping platform (a self-hostable Figma alter… |
| [`performance`](star-alliance-skills/performance/SKILL.md) | 1.0.3 | vendored | 32 / 219 | 1418 / 371 | ✓ lean | Optimize web performance for faster loading and better user experience |
| [`phased-db-refactor`](star-alliance-skills/phased-db-refactor/SKILL.md) | 1.0.0 | own | 119 / 825 | 1070 / 133 | ✓ lean | Decision framework and execution guide for multi-phase database refactors in Lex Council |
| [`portability-audit`](star-alliance-skills/portability-audit/SKILL.md) | 1.0.0 | own | 75 / 481 | 578 / 104 | ✓ lean | Audit how portable a Claude Code project is — maps every layer (skills, members, hooks, en… |
| [`portfolio-risk`](star-alliance-skills/portfolio-risk/SKILL.md) | 0.1.0 | own | 129 / 1005 | 834 / 55 | ✓ lean | The Merchant's craft for read-only, book-level portfolio construction and risk measurement… |
| [`price-action`](star-alliance-skills/price-action/SKILL.md) | 1.0.0 | own | 141 / 1001 | 1084 / 63 | ✓ lean | The Merchant's read-only craft for reading price action and market structure, distilled fr… |
| [`probability-statistics`](star-alliance-skills/probability-statistics/SKILL.md) | 1.1.0 | own | 117 / 1000 | 1318 / 69 | ✓ lean | The Merchant's read-only craft for probability and statistics, distilled from Evans & Rose… |
| [`project-start`](star-alliance-skills/project-start/SKILL.md) | 1.0.0 | own | 55 / 375 | 262 / 56 | ✓ lean | Start-of-session health check for projects that have Star Alliance members deployed |
| [`python-master`](star-alliance-skills/python-master/SKILL.md) | 1.0.0 | own | 134 / 1020 | 431 / 47 | ✓ lean | The Developer's craft for building production-grade Python libraries and web apps end to e… |
| [`redesign-existing-projects`](star-alliance-skills/redesign-existing-projects/SKILL.md) | 1.0.0 | own | 31 / 225 | 2174 / 176 | ✓ lean | Upgrades existing websites and apps to premium quality |
| [`relationship-intel`](star-alliance-skills/relationship-intel/SKILL.md) | 1.0.0 | own | 136 / 961 | 1072 / 55 | ✓ lean | The Herald's craft for turning email traffic into living relationship intelligence so the … |
| [`release-train`](star-alliance-skills/release-train/SKILL.md) | 1.0.1 | own | 135 / 902 | 1146 / 62 | ✓ lean | The Quartermaster's craft for closing out a body of work — merge every outstanding branch … |
| [`safe-agentic-orchestration`](star-alliance-skills/safe-agentic-orchestration/SKILL.md) | 1.1.0 | own | 133 / 1017 | 1202 / 58 | ✓ lean | Orchestrate a coordinated multi-agent AI team using the SAFe-agentic doctrine distilled fr… |
| [`scheduled-watch`](star-alliance-skills/scheduled-watch/SKILL.md) | 1.0.0 | own | 134 / 909 | 1030 / 48 | ✓ lean | The Strategist's craft for defining an unattended task that runs on a cron cadence and res… |
| [`schema-evolution`](star-alliance-skills/schema-evolution/SKILL.md) | 1.2.0 | own | 152 / 1013 | 2264 / 173 | ✓ lean | The Architect's craft for evolving a structured data model without breaking what already r… |
| [`session-mining`](star-alliance-skills/session-mining/SKILL.md) | 1.3.0 | own | 144 / 1012 | 1439 / 169 | ✓ lean | Mine your own Claude session history for lessons, then turn them into ranked, verified upg… |
| [`skillsmith`](star-alliance-skills/skillsmith/SKILL.md) | 1.7.2 | own | 132 / 987 | 5674 / 169 | ○ large | Manage, sync, upgrade, create, and auto-evolve Star Alliance skills across the star-allian… |
| [`spec-driven-development`](star-alliance-skills/spec-driven-development/SKILL.md) | 1.1.0 | own | 138 / 1017 | 1396 / 158 | ✓ lean | The Architect's discipline for building from an executable specification instead of vibe-c… |
| [`star-alliance-language`](star-alliance-skills/star-alliance-language/SKILL.md) | 1.2.0 | own | 84 / 522 | 912 / 111 | ✓ lean | The guild's shared reading protocol for OKF-tidied repos — how every member quickly, cheap… |
| [`stitch-design-taste`](star-alliance-skills/stitch-design-taste/SKILL.md) | 1.0.0 | own | 29 / 257 | 1628 / 182 | ✓ lean | Semantic Design System Skill for Google Stitch |
| [`storm-investigation`](star-alliance-skills/storm-investigation/SKILL.md) | 1.0.0 | own | 113 / 866 | 919 / 94 | ✓ lean | Multi-perspective deep-research method (Stanford STORM, NAACL 2024) for any topic — run fi… |
| [`strategies-review`](star-alliance-skills/strategies-review/SKILL.md) | 1.1.0 | own | 74 / 510 | 631 / 76 | ✓ lean | Review and housekeep strategies |
| [`supabase`](star-alliance-skills/supabase/SKILL.md) | 0.1.3 | vendored | 58 / 475 | 1435 / 129 | ✓ lean | Use when doing ANY task involving Supabase |
| [`supabase-postgres-best-practices`](star-alliance-skills/supabase-postgres-best-practices/SKILL.md) | 1.1.1 | vendored | 23 / 183 | 242 / 54 | ✓ lean | Postgres performance optimization and best practices from Supabase |
| [`system-prompt-design-patterns`](star-alliance-skills/system-prompt-design-patterns/SKILL.md) | 1.1.0 | own | 104 / 921 | 1313 / 160 | ✓ lean | Distills the recurring design patterns of effective production system prompts (Anthropic, … |
| [`timeseries-forecasting`](star-alliance-skills/timeseries-forecasting/SKILL.md) | 1.1.0 | own | 118 / 1019 | 1579 / 182 | ✓ lean | Project a numeric time series forward with Google's TimesFM zero-shot foundation model, re… |
| [`trading-strategy`](star-alliance-skills/trading-strategy/SKILL.md) | 0.2.0 | own | 139 / 1009 | 1120 / 64 | ✓ lean | The Merchant's craft for read-only trading-strategy design that ships a written, dated str… |
| [`transactions-domain-model`](star-alliance-skills/transactions-domain-model/SKILL.md) | 1.3.1 | own | 108 / 951 | 3263 / 399 | ✓ lean | Loads the complete Lex Council transactions domain model before any transaction-related wo… |
| [`ultra-brainstorming`](star-alliance-skills/ultra-brainstorming/SKILL.md) | 1.3.1 | own | 129 / 873 | 2029 / 191 | ✓ lean | An ASSIGNABLE multi-thinker method — any member who carries it fires ALL his available thi… |
| [`ux-copywriting`](star-alliance-skills/ux-copywriting/SKILL.md) | 1.0.0 | own | 121 / 852 | 1223 / 128 | ✓ lean | Write functional in-product copy — the words a user reads while operating an interface |
| [`ux-research`](star-alliance-skills/ux-research/SKILL.md) | 1.0.0 | own | 119 / 857 | 915 / 87 | ✓ lean | The Designer's UX research craft — learn from real users instead of guessing |
| [`vault-log-compliance`](star-alliance-skills/vault-log-compliance/SKILL.md) | 1.1.0 | own | 128 / 807 | 1445 / 119 | ✓ lean | Enforces P8 vault-logging compliance for Lex Council |
| [`vault-log-writer`](star-alliance-skills/vault-log-writer/SKILL.md) | 1.0.0 | own | 124 / 739 | 868 / 159 | ✓ lean | Write and file a correct Lex Council vault log entry per the P8 mandatory change logging r… |
| [`voices-check`](star-alliance-skills/voices-check/SKILL.md) | 1.0.1 | own | 145 / 1013 | 392 / 50 | ✓ lean | Integrate an agent's competing internal sub-voices into one coherent response instead of l… |
| [`volume-price-analysis`](star-alliance-skills/volume-price-analysis/SKILL.md) | 1.0.0 | own | 137 / 1020 | 1067 / 55 | ✓ lean | The Merchant's read-only craft for Volume Price Analysis, distilled from Anna Coulling's A… |
| [`weapon-utility`](star-alliance-skills/weapon-utility/SKILL.md) | 3.1.0 | own | 166 / 1009 | 4392 / 324 | ✓ lean | Every member's rule for which weapon (model) to draw and how thinker and doer weapons work… |
| [`workflow-forge`](star-alliance-skills/workflow-forge/SKILL.md) | 1.4.0 | own | 153 / 997 | 2235 / 175 | ✓ lean | The Strategist's craft for distilling a finished run into a reusable star-map workflow in … |
| [`workflow-runner`](star-alliance-skills/workflow-runner/SKILL.md) | 1.0.0 | own | 123 / 875 | 1100 / 90 | ✓ lean | The Quartermaster's craft for operating the guild's own machinery — RUN a star-map workflo… |

_112 skills — 106 lean · 5 large (installable, over the 500-line ideal) · 0 near the word ceiling · 1 hard violations._
