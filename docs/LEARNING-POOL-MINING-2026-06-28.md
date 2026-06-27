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
- [ ] `agent-skills-main` — skills marketplace/structure
- [ ] `spec-kit-main` — spec-driven development
- [ ] `codebase-memory-mcp-main` — codebase memory MCP
- [ ] `Agent-Reach-main` — agent outreach tool
- [ ] `swarm-models-main` — multi-model swarm
- [ ] `system_prompts_leaks-main` — leaked system prompts (prompt-craft mining)
- [ ] `timesfm-master` — time-series foundation model (Merchant interest)
- [ ] `daily_stock_analysis-main` — stock analysis skill/MCP (Merchant)
- [ ] `OpenMontage-main` — video montage agent
- [ ] `penpot-develop` — open-source design tool (Designer interest)

### Final
- [ ] Synthesis: ranked upgrade routes table
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
