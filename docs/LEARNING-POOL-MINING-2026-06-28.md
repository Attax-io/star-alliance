---
type: Document
title: Learning Pool Mining
description: Lessons + upgrade routes distilled from the Downloads/Learning Pool repos and books
timestamp: 2026-06-28T00:00:00Z
---

# Learning Pool — Mining & Upgrade Routes (2026-06-28)

Source: `/Users/attaselim/Downloads/Learning Pool` (16,222 files; mostly cloned repos).
Goal: distill lessons from each item → flag concrete upgrade routes for Star Alliance
**workflows · members · skills · arsenal · hooks**.

Mining strategy: read the **docs** in each repo (README / AGENTS.md / CLAUDE.md / SKILL.md /
spec docs) — not the source tree. PDFs handled per source-distillation recipe where new.

**Coverage:** 15 top-level items. 11 new repos mined (docs-read, not benchmarked); 4 dirs
(`Archive`, `Self learning`, `probability skill`, `design-motion-principles`) skipped as
already-absorbed — confirmed vs MEMORY.md (self-learning-doctrine, probability-statistics-skill,
motion-design-two-mode; trading PDFs → existing trading skills). Nothing tested/measured — every
`[x] MINED` = documentation read only.
**Evidence note:** all performance numbers below (e.g. codebase-memory-mcp "10×/2.1×") are
**vendor-reported**, not independently measured — verify before adoption.
**Ranking criterion:** synthesis table ordered by the "prose-doctrine → enforced-mechanism" through-line
first, then effort-to-leverage; not pure ROI. Re-sort by ROI before committing a build slate.

**Independent review (different model):** MiniMax M3 reviewed this doc 2026-06-28 → *Accept*: fulfills
intent, no fabrication, no harmful instruction; flagged auditability gaps now addressed above.

---

## ✅ CHECKPOINT TRACKER (resume here if interrupted)

Status legend: `[ ]` todo · `[~]` in progress · `[x]` done · `[skip]` already absorbed

### Already absorbed (verified vs memory — light note only)
- [x] `Archive/` — trading PDFs + OKF webarchive → existing skills (algorithmic-trading-chan, volume-price-analysis, japanese-candlesticks, okf)
- [x] `Self learning/` — → self-learning-doctrine-2026-06 (guild-reflection + CLAUDE.md doctrine)
- [x] `probability skill/` — → probability-statistics skill v1.0.0
- [x] `design-motion-principles-main` — → motion-design 2.0.0 absorbed

### New targets
- [x] `safe-agentic-workflow-main` — agentic harness safety (HIGH interest: hooks/gates) ← MINED, top-value
- [x] `agent-skills-main` — UPSTREAM of our supabase skills; parity-check only
- [x] `spec-kit-main` — MINED, high value (constitution-gates)
- [x] `codebase-memory-mcp-main` — MINED, high value (token-saving code-graph MCP)
- [x] `Agent-Reach-main` — MINED, medium-high (doctor + fallback routing)
- [x] `swarm-models-main` — MINED, low (already have summon/minimax)
- [x] `system_prompts_leaks-main` — MINED, high (prompt-craft)
- [x] `timesfm-master` — MINED, medium (Merchant forecasting)
- [x] `daily_stock_analysis-main` — MINED, medium (Merchant output schema)
- [x] `OpenMontage-main` — MINED, low-med (onboarding pattern)
- [x] `penpot-develop` — MINED, high (memory-graph architecture)

### Final
- [x] Synthesis: ranked upgrade routes table
- [ ] Present to Guild Master for go on actual guild edits

---

## LESSONS & UPGRADE ROUTES

### 1. safe-agentic-workflow (SAW) — peer multi-agent harness ⭐ TOP VALUE
SAFe-methodology agent harness: 11 role agents, 18 model-invoked skills, 24 commands,
3 hooks, machine-readable manifest+changelog. ~60% transfers to Star Alliance.

**Core insight** — SAW separates 3 things we mush together:
- **Hooks = enforced** (PreToolUse/Stop gates) · **Workflows = requested** · **Skills = recognized** (model-invoked).
We already have all three; steal the explicit "who invokes" axis as doctrine so behavior doesn't all become workflows.

**Steal-now upgrade routes (ranked):**
1. **Stop-the-Line gate** (NEW hook) — block `Write`/`Edit` by a doer when the active task has no
   acceptance-criteria / Definition-of-Done. "You are NOT responsible for inventing AC." Kills the
   "agent invented requirements and shipped them" failure. → fits our PreToolUse gate stack.
2. **Exit states + handoff contracts** (member upgrade) — each member gets a canonical `exit_state`
   enum + templated handoff + `must_not[]`. Makes inter-member handoffs machine-checkable by hooks.
   → members-meta.json / member .md upgrade.
3. **Negative-permission boundaries** (`must_not[]` per member, enforced by Stop hook) — enforceable
   data, not prose. Maps to our weapon/role split.
4. **Independence gates** — some roles (QA/security/architect-review) CANNOT collapse into the
   implementer; orchestration must spawn a fresh instance. → our verify-gate already half-does this
   ("different member must review"); formalize as a member tier flag.
5. **Tiered validation commands** (`validation.command` + `success_marker` per member) — Stop hook runs
   it after "done" and only honors completion if marker appears. Evidence-based delivery, enforced.
6. **Routing/failure-mode table** (`routing_table.yml`) — every failure has a named owner
   (bug→developer, pattern violation→pattern-keeper, AC missing→architect, blocked→strategist).
   Converts "agent stuck" → "route to X". Maps onto Butler's members-formation routing.
7. **Three-stage PR review** (sequential specialist gates, each own exit-state) — pattern-check →
   security-audit → human-merge. We have Security Sweep; add the staged-gate composition.

**Skill ideas:** `pattern-discovery` ("search first, reuse always, create only when necessary" —
MANDATORY before implementing) → upgrade guild-conformity / new reuse-gate; SAW enforces it as a
skill, matching our CLAUDE.md "grep+reuse before creating component" rule (currently unenforced).

**Skills 2.0 frontmatter to adopt:** `context: fork` (skill runs isolated sub-context),
`agent:` (which specialist executes), `user-invocable: false` (model-only). → skillsmith skill schema.

**Manifest/changelog:** `.harness-manifest.yml` (identity/substitutions/protected/replaced/sync +
`conflict_strategy` enum) and `HARNESS_CHANGELOG.yml` (per-change `breaking:` flag). → upgrade
guild-sync / skill-fingerprints for "guild as a distributable package".

**AVOID from SAW:** multi-provider duplication, tmux "dark factory", 24 commands (project noise),
full SAFe ceremony. We already prune these instincts.

### 2. spec-kit (GitHub Spec-Driven Dev) ⭐ HIGH VALUE
We already carry `spec-driven-development` skill — but spec-kit has concepts we lack:

**Steal-now:**
1. **Constitution-as-gates** — a versioned, ratified `constitution.md` of non-negotiable articles that
   PLANS must pass at "Phase -1 gates" (or document an exception in a Complexity-Tracking section).
   We have CLAUDE.md (prose) + OKF gate; we lack a *machine-checkable doctrine→execution contract*.
   → UPGRADE spec-driven-development to emit a constitution + add a plan-time constitution-check;
   could become a real gate. Strongest single idea.
2. **`[NEEDS CLARIFICATION]` markers** — templates FORCE the model to flag ambiguity instead of
   guessing. Maps directly onto our Confusion Protocol — currently prose, make it a template primitive
   in spec-driven-development + project-start.
3. **`/analyze` cross-artifact consistency** — reads spec+plan+tasks together, surfaces contradictions
   non-destructively. → new step/mode in spec-driven-development (and conceptually in conquering-campaign).
4. **`/converge` self-heal** — assess codebase vs spec/plan, APPEND remaining unbuilt work as new tasks.
   → drift→task bridge; fits conquering-campaign AUDIT mode + dashboard-parity.
5. **`/checklist` = "unit tests for English"** — validates REQUIREMENTS quality, not implementation.
   Distinct discipline we conflate. → new checklist artifact in spec-driven-development.

**Template-as-LLM-constraint craft** — templates ban HOW (tech) and force WHAT/WHY; anti-speculation
("no 'might need' features"); test-first file order (contracts→tests→source). → skillsmith authoring doctrine.
**Lighter adopts:** command `handoffs:` in frontmatter (declarative next-step chaining — maps to our
member handoff idea from SAW), `research.md` as first-class artifact, `Assisted-by:` commit trailer.

### 3. agent-skills (official Supabase skills) — UPSTREAM, parity-check only
This repo IS the source of our installed `supabase` + `supabase-postgres-best-practices` skills
(marketplace v1.1.0). No new doctrine. ACTION: version-parity check our installed copies vs this
v1.1.0 via guild-sync/skillsmith; re-pull if upstream is ahead. Pattern worth noting: clean
`marketplace.json` plugin manifest (name/owner/description/skills[]) — a model for if we ever publish
Star Alliance skills externally (ties to SAW manifest idea + impeccable npm precedent).

### 4. codebase-memory-mcp ⭐ HIGH VALUE (tooling, not doctrine)
Single-binary MCP: tree-sitter AST knowledge graph over 158 languages, indexes Linux kernel (28M LOC)
in 3 min, structural queries <1ms, **10× fewer tokens / 2.1× fewer tool calls** vs file-by-file
exploration (arXiv 2603.27277, 31-repo eval). 14 MCP tools: search, trace call-chains, impact
analysis, dead-code detection, Cypher queries, ADR mgmt, cross-service HTTP linking. Zero deps,
100% local, `install` auto-configures Claude Code.

**Upgrade route:**
- Evaluate adopting it as a real MCP server for **the-developer** (and architect) — directly attacks
  our #1 logged lesson (token-bloated reads). Our `graphify` skill builds graphs; this is a faster,
  query-on-demand engine. → Arsenal Forge candidate: add as a developer weapon / MCP.
- Even if not adopted, its design validates our reading-discipline doctrine: "one graph query replaces
  dozens of grep/read cycles." Reinforces CLAUDE.md reading discipline.
- ACTION (needs go): trial `install.sh` in a sandbox on the Lex repo, measure token savings.

### 5. Agent-Reach — MEDIUM-HIGH (connectivity + doctor pattern)
Python "glue layer" giving agents read/search over 13 internet platforms (Twitter/X, Reddit, YouTube,
Bilibili, Xiaohongshu, LinkedIn, RSS, GitHub, web, **Xueqiu stocks**, podcasts). Positioned as
**installer + doctor + config, NOT a wrapper**.

**Lessons → upgrade routes:**
1. **`doctor` diagnostic command** — one command reports each capability: works / broken / how-to-fix.
   → STEAL as an arsenal-health command (`arsenal doctor`): probe each weapon/MCP (minimax key, ollama
   list, summon models, MCP reachability) and print a fix-list. Complements guild-sync (device parity)
   but for *runtime connectivity*. New Arsenal Forge / skillsmith script.
2. **Primary + fallback multi-backend routing per capability** (e.g. yt-dlp → bili-cli when blocked,
   zero user action). → mirrors weapon-utility left→right scan; formalize explicit fallback chains so a
   dead doer auto-routes to the next. Hardens our doer loop against a single tool failing.
3. **BaseChannel plugin contract** (`can_handle / read / search / check`) — clean uniform interface.
   → model for arsenal weapon adapters if we standardize.
4. Capability value: Xueqiu/stock + social listening → **the-merchant** (market sentiment) and
   **the-herald** (brand listening / social research). We have brand-listening via brightdata; Agent-Reach
   is a free local alternative worth a bake-off.

### 6. swarm-models — LOW (already covered)
litellm-style unified multi-provider LLM wrapper (`.run(task)`, concurrent/batch). Our
`star-alliance-arsenal/summon.py` + `minimax.py` already abstract this. No adoption. Only confirmation:
unified `.run()` + batch/concurrent is the right arsenal shape — we already have it.

### 7. system_prompts_leaks ⭐ HIGH VALUE (prompt-craft mining)
Curated leaked + official system prompts for ~all major AI products: Claude (Opus 4.8, Fable 5,
Claude Code, Cowork, claude-design w/ 48 tools+16 skills), GPT-5.5/Codex, Gemini, Cursor, Devin,
Warp, opencode, MiniMax M2.5, etc. Includes the Claude Code & Cowork prompts we run *inside*.

**Upgrade routes:**
1. **Prompt-craft distillation** — mine top products for member-prompt patterns: identity framing,
   tool-use discipline, refusal/safety structure, progressive-disclosure. Feeds **members-formation**
   + **skillsmith** authoring doctrine + reinforces our "spoken-word framing" axiom (CLAUDE.md).
2. **Steal harness patterns** from the Claude Code / Cowork / claude-design prompts directly — how
   Anthropic structures tool gating, skills, deferred tools. Direct mirror of our own harness.
3. Reference shelf — keep as a research source (like a skill `references/`), not a build target.
   ACTION (low effort): a one-pass MiniMax distillation of the Anthropic/* prompts → a "prompt-craft"
   reference for skillsmith.

### 8. timesfm — MEDIUM (Merchant capability)
Google TimesFM 2.5 — decoder-only time-series **foundation model** for forecasting (ICML 2024),
on HuggingFace + BigQuery ML. Ships AGENTS.md + SKILL.md. Heavy (torch + weights).
**Upgrade route:** Merchant forecasting weapon — a new `time-series-forecasting` skill or arsenal
tool wrapping timesfm (price/volume/indicator series → probabilistic forecast). Pairs with our
probability-statistics + trading skills. Flag: weight/runtime cost; consider BigQuery/HF-endpoint
call instead of local. Needs go + a bake-off vs simpler baselines.

### 9. daily_stock_analysis — MEDIUM (Merchant)
Chinese agentic stock analyzer: SKILL.md (`stock_analyzer`) + MCP server + web/desktop. Best steal
is the **output schema** — `AnalysisResult.dashboard` = {core_conclusion (one-liner+signal+sizing),
data_perspective (trend/price/volume/chip-structure), intelligence (news/risk/catalysts),
battle_plan (sniper buy/sell points, position strategy, risk-control checklist)}.
**Upgrade routes:**
1. Adopt the **battle_plan output template** for the-merchant's market-recon / trading-strategy
   deliverables — turns analysis into actionable, uniformly-structured reports.
2. Its **AGENTS.md doctrine gems** (also in timesfm/OpenMontage): "reuse existing modules, no parallel
   implementations"; **flat changelog `[Unreleased]` format to avoid concurrent-PR merge conflicts**
   (no `###` subheads) — steal for our guild-log / release-train; screenshots go in PR/artifacts, never
   committed to repo (we already lean this way).

### 10. OpenMontage — LOW-MEDIUM (new domain + onboarding pattern)
"First open-source agentic video production system" — agent does research→script→assets→edit→render;
builds a real-footage corpus, not just animated stills. AGPLv3.
**Lessons (capability is out-of-scope unless we want a media member):**
1. **Onboarding meta-skill** (`skills/meta/onboarding.md`) — when first msg is vague, run discovery,
   classify the user's setup, present capabilities in plain language, offer tailored starter prompts;
   "curious → producing in <60s". → STEAL for **the-butler**: a meta-onboarding skill for vague
   requests ("what can you do?") instead of guessing. Complements Confusion Protocol.
2. **Reference-X as a first-class workflow** ("make a video like this") — treat an exemplar as input,
   not a web-search. → generalizes to our image-to-code / design-taste (reference-driven build).
3. **"Rule Zero"** + explicit AGENT_GUIDE contract — clean agent-contract doc pattern.

### 11. penpot ⭐ HIGH VALUE (memory architecture — unexpected)
Open-source Figma/design platform (Clojure/ClojureScript, huge). The design tool itself is NOT the
steal (we have Designer skills + tokens). The steal is its **AGENTS.md memory system**:
- Memories are the **PRIMARY** project guidance (not docs/README) — dense, terse, invariant-focused.
- A **reference GRAPH, not a flat list**: `critical-info` (graph root) → `<section>/core` (per-module
  core memory) → `<topic>` focused memories → deeper `mem:` links. Progressive discovery.
- **Hard gate**: "Read the core memory of every affected module BEFORE planning/coding. STOP. Skipping
  is the #1 cause of incorrect work." (uses serena `read_memory`).

**Upgrade route (strong):** evolve our memory system from a flat `MEMORY.md` index + sibling files
into a **graph**: keep MEMORY.md as root, add module/domain `core` memories, lean harder on `[[wikilinks]]`
as the edge set, and add a "read the relevant core memory before working in that area" discipline (we
already say "read vault/memory logs before continuing prior work" — penpot makes it a structured,
mandatory pre-work gate). Mirrors codebase-memory-mcp (graph beats flat) at the doctrine layer.

---

## 🏆 SYNTHESIS — RANKED UPGRADE ROUTES (proposed; needs Guild Master go)

Effort: S=small (config/doctrine) · M=medium (new script/skill upgrade) · L=large (new MCP/build)

| # | Upgrade | Source | Target asset | Effort | Why |
|---|---------|--------|--------------|--------|-----|
| 1 | **Memory → graph** (root + module `core` + read-before-work gate) | penpot | memory system + CLAUDE.md | M | Fixes #1 failure: working without reading prior context |
| 2 | **Stop-the-Line gate** (no AC/DoD → block doer Write/Edit) | SAW | new PreToolUse hook | M | Kills "invented requirements & shipped" |
| 3 | **Constitution-as-gates** (ratified articles, plan-time check) | spec-kit | spec-driven-development + new gate | M | Machine-checkable doctrine→execution; OKF-style |
| 4 | **`arsenal doctor`** (probe every weapon/MCP, print fix-list) | Agent-Reach | new arsenal script (Arsenal Forge) | S | Runtime connectivity health (guild-sync = device parity only) |
| 5 | **Member exit-states + `must_not[]` + handoff templates** | SAW | members-meta.json / member .md | M | Machine-checkable handoffs; enforceable boundaries |
| 6 | **codebase-memory-mcp** trial as developer MCP | codebase-memory-mcp | arsenal / the-developer | L | 10× fewer tokens on code exploration |
| 7 | **Confusion Protocol → `[NEEDS CLARIFICATION]` primitive** | spec-kit | project-start + spec-driven-development | S | Make ambiguity-flagging structural, not prose |
| 8 | **Doer fallback chains** (primary→backup per capability) | Agent-Reach | weapon-utility / summon.py | S | Hardens doer loop vs single-tool failure |
| 9 | **Prompt-craft reference** (distill Anthropic/* prompts) | system_prompts_leaks | skillsmith + members-formation | S | Sharper member identity/tool-use framing |
| 10 | **`/analyze` + `/converge`** cross-artifact & self-heal | spec-kit | spec-driven-development / conquering-campaign | M | Drift detection + auto task-backfill |
| 11 | **`/checklist` "unit tests for English"** | spec-kit | spec-driven-development | S | Validate requirement quality separately |
| 12 | **Merchant `battle_plan` output schema** | daily_stock_analysis | market-recon / trading-strategy | S | Uniform, actionable analysis reports |
| 13 | **Routing/failure-mode table** (failure→named owner) | SAW | members-formation / Butler | S | "Stuck" → deterministic route |
| 14 | **Independence-gate member tier** (no self-review) | SAW | verify-gate + members-meta | S | Formalizes existing verify-gate intent |
| 15 | **Butler onboarding meta-skill** (vague req → discovery) | OpenMontage | new the-butler skill | M | Better than guessing on "what can you do?" |
| 16 | **Skills 2.0 frontmatter** (`context: fork`, `agent:`) | SAW | skillsmith schema | M | Isolated skill execution + explicit executor |
| 17 | **timesfm forecasting weapon** | timesfm | new Merchant skill/arsenal | L | Real time-series forecasting (bake-off first) |
| 18 | **Flat changelog `[Unreleased]`** (no `###`, merge-safe) | daily_stock_analysis | guild-log / release-train | S | Fewer concurrent-edit conflicts |
| 19 | **Distributable manifest + breaking-flag changelog** | SAW / agent-skills | guild-sync / skill-fingerprints | M | "Guild as a package" |
| 20 | **Supabase skills parity re-pull** (v1.1.0) | agent-skills | supabase skill | S | Stay current with upstream |

**Top 5 to do first:** #1 memory-graph · #2 stop-the-line gate · #3 constitution-gates · #4 arsenal doctor · #5 member exit-states.
These convert prose doctrine into enforced mechanism — the through-line of every high-value source (SAW, spec-kit, penpot).

## NEXT STEP
Awaiting Guild Master go to turn any of these rows into real guild edits (each = its own workflow:
Skill Forge / Arsenal Forge / Workflow Forge / a CLAUDE.md doctrine diff). No guild assets changed yet —
this doc is analysis only.

---

## ✅ SHIPPED 2026-06-28 (Top-5 build — "proceed as recommended")
- **#4 Arsenal doctor** — `star-alliance-arsenal/doctor.py` (probe weapons → PASS/WARN/FAIL+fix; `--ping`/`--json`). Tested: 6 pass.
- **#2 Stop-the-Line gate** — `.claude/hooks/stop-line-gate.py`, wired into `sa-pretool.py`. **Opt-in** (`touch .claude/state/stop-line-armed`); blocks SOURCE writes without `📋 Acceptance:` line. Unit-tested 4/4; disarmed by default.
- **#3 Constitution** — `docs/CONSTITUTION.md` v1.0.0 (10 ratified articles + plan-time check + amendment process).
- **#1 Memory-graph** — CLAUDE.md doctrine ("read the domain core before working"); MEMORY.md now graph root; seeded `core-hooks-gates` memory.
- **#5 Member exit-states + handoff** — `exit_state` + `handoff` added to all 9 members in `data/members-meta.json`; dashboard rebuilt clean.

Remaining rows (6–20) un-started — deferred for explicit go (esp. L-effort #6 codebase-memory-mcp trial, #17 timesfm: need sandbox install + bake-off).
