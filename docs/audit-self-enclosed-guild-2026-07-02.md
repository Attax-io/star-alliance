---
type: Document
title: "Self-Enclosed Guild — Intent Audit (2026-07-02)"
description: "14-architect Strategic Audit verdict on whether Star Alliance achieves its intent of a self-enclosed, self-enforcing, self-installing guild; scorecard across 7 intent pillars, ranked gaps, and fix-first shortlist."
tags: [audit, strategic-audit, self-enclosed, lex-council, okf, portability]
---

# Self-Enclosed Guild — Intent Audit

**Date:** 2026-07-02
**Method:** Strategic Audit workflow — 14 read-only Architect slices across 3 waves, ground-truthed against the live repo, merged by the Strategist. No source was modified.

## 1. Verdict

The guild has built a genuinely self-reliant body of skills and workflows (P1), but it is **not yet self-enclosed**: the mechanisms that would make it refuse global craft (P4), telemeter its own use honestly (P2), propagate itself onto new ground (P3/P6), and pull outside craft inward (P5) are either **absent, written-but-disarmed, or scoped to star-alliance so they don't travel** — and the flagship landing (Lex Council, P7) is stalled on four concrete blockers.

## 2. Intent Scorecard

| Pillar | Slice | Status | Evidence pointer |
|---|---|---|---|
| **P1 — Self-reliant agents** | Members carry own skills | MET | 10 members, real skills[] 6-34, 0 dangling/128; conformity SEC/K/PS clean (S1) |
| | Members run own workflows | MET | 30 workflows all categories; workflow-gate.py:234-239 + banner-enforcer; no SoT drift (S2) |
| **P2 — Telemetry** | Agent invocation | PARTLY | dispatch-log 476 (Hermes only) + thinker-attest 496 (main only); Claude subagent spawns unlogged — no PostToolUse on Task/Agent (S5) |
| | Skill invocation | PARTLY | xp-log fires only on tool_name==Skill -> 2 rows / 128 skills (~1.6%); stopped 2026-07-01 (S6) |
| | Workflow invocation | PARTLY | writer real (38 rows) but once_per_turn sentinel never re-armed + dir mismatch -> once-per-name-for-life undercount (S7) |
| **P3 — Install via MCP** | Portability (does it install) | MET | install-star-alliance.command + deploy_device.py real/working (S8a) |
| | MCP as the install channel | NOT-MET | MCP is the payload (4 tools, no deploy tool); shell installs MCP, not vice-versa — "install via MCP" literally false (S8b) |
| **P4 — Refuse global craft** | Refuse global SKILLS | NOT-MET | No mechanism, no doctrine; harness merges ~/.claude/skills (127>114); butler-skill-gate gates name/role not provenance (S3) |
| | Refuse global AGENTS | PARTLY | Butler->specialist gated via Strategist; BUT non-guild subagents waved through (routing-enforce:144-145), thinker-gate fails open (77-79); no allowlist (S4) |
| **P5 — Absorb on landing** | Absorb SKILLS | PARTLY | skill_sync detects add-to-repo (181-182) but display-only, no apply/watcher -> manual; once absorbed, wired correctly (S9) |
| | Absorb WORKFLOWS | NOT-MET | absorb.py skills-only; no import/adopt path (grep=0); structural asymmetry vs skills (S10) |
| **P6 — Force new project under protocol** | Copy protocol + enforce | NOT-MET | star-alliance-deploy is prose, no script; never copies CLAUDE.md; gates fail OPEN in foreign repo (S11) |
| **P7 — Land in Lex under QM OKF** | OKF enforced in target | PARTLY | okf-gate:89-124 blocks but not armed (absent from settings.json) + doesn't travel (okf_audit anchors to star-alliance's workflows.json) (S12) |
| | star-alliance-language reads OKF | MET | okf_read.py parsed 119 live OKF files; producer+consumer share OKF v0.1 + identical frontmatter regex (S13) |
| | Lex Council operational | PARTLY | deployed (CLAUDE.md, .harness-version, growing ledger) BUT 4 blockers: no dispatch.py, STAR_ALLIANCE_ROOT unset, .claude/agents EMPTY, dead hook mirror + stale sha (S14) |

## 3. Ranked Gap List (by Lex-landing impact)

### Tier 1 — Lex is landed but broken
1. **Lex .claude/agents/ is EMPTY (P7/S14).** Members unspawnable -> routing gate never satisfied -> high-stakes turns deadlock. *Fix:* run guild/install_agents.py (or install.sh) inside Lex.
2. **Lex has no tools/dispatch.py (P7/S14).** executor-enforce blocks the Butler's write path with no delegate. *Fix:* ship the dispatch substrate to Lex (Tier-3 portability installer, pointed at Lex).
3. **STAR_ALLIANCE_ROOT unset in Lex settings (P7/S14).** Path-resolving tools no-op. *Fix:* add the env block to Lex .claude/settings.json.

### Tier 2 — isolation claimed but unenforced
4. **No refusal of global SKILLS (P4/S3).** "FORBIDDEN" has zero backing; harness merges 127 global skills over 114 own. *Fix:* provenance check in the skill-load gate — reject skills outside the repo's star-alliance-skills/.
5. **Non-guild subagents waved through + thinker-gate fails open (P4/S4).** *Fix:* flip routing-enforce:144-145 to deny-unknown against the roster; make thinker-gate fail closed.
6. **Gates fail OPEN in a foreign repo (P6/S11).** Config resolves to foreign path, models.json missing, gates no-op. *Fix:* gates detect "config not found" and fail closed.

### Tier 3 — self-propagation and absorption missing
7. **"Install via MCP" is literally false (P3/S8b).** *Fix:* add a deploy_to_project tool to the MCP server, OR revise the intent wording.
8. **No workflow absorb path (P5/S10).** *Fix:* extend absorb.py with a workflow-adopt branch mirroring the skill branch.
9. **Skill absorb is manual (P5/S9).** *Fix:* add an --apply action to skill_sync for the add-to-repo it already detects.
10. **okf-gate not armed + doesn't travel (P7/S12).** *Fix:* add okf-gate to settings; make okf_audit resolve its anchor to the target repo root.

### Tier 4 — telemetry fidelity (logs exist but lie)
11. **Skill telemetry near-blind (P2/S6).** *Fix:* widen the seam to log skill activation at prompt/dispatch time, not just tool-name match.
12. **Agent-spawn telemetry hole (P2/S5).** *Fix:* PostToolUse hook on Task/Agent appending to dispatch-log.
13. **Workflow undercount (P2/S7).** *Fix:* re-arm the sentinel in turn-start and fix the .claude/state vs state dir mismatch (~2 lines).

## 4. Fix-First Shortlist

| # | Fix | Effort | Owner |
|---|---|---|---|
| 1 | Populate Lex .claude/agents/ via install_agents.py | ~10 min, one command | Quartermaster |
| 2 | Ship dispatch.py + set STAR_ALLIANCE_ROOT in Lex (bundle gaps 2+3) | ~30 min, point Tier-3 installer at Lex | Developer |
| 3 | Provenance refusal in the skill-load gate (P4 core mechanism) | ~half day, one gate + doctrine line | Architect + Developer |
| 4 | Gates fail-CLOSED on missing config in a foreign repo | ~half day, shared guard in all gates | Developer |
| 5 | Fix workflow-telemetry sentinel + dir mismatch (cheapest P2 win) | ~2 lines | Developer |

Fixes 1-2 make Lex actually run; 3-4 make "self-enclosed" real; 5 is the cheapest honesty win.

## 5. Honest Tally

- **Genuinely MET (mechanism exists AND enforced/proven): 5 slices** — own skills (P1), own workflows (P1), portability installer (P3a), star-alliance-language reads OKF (P7), OKF-format sharing between producer/consumer.
- **Doctrine/mechanism WITHOUT enforcement (written-but-disarmed, scoped-so-it-can't-travel, or logs-but-lies): 8 slices** — all three telemetry slices (P2), refuse-agents (P4), absorb-skills (P5), okf-gate-in-target (P7), Lex-operational (P7), plus refuse-skills which has neither doctrine nor mechanism.
- **Structurally absent (no mechanism at all): 3 slices** — refuse global skills (P4), absorb workflows (P5), force-new-project (P6). MCP-as-channel (P3b) is a fourth if read literally.

**Pattern:** P1 is strong and real. Everything that makes the guild *self-enclosed* rather than merely *self-equipped* — isolation-enforcement (P4), telemetry fidelity (P2), self-propagation (P3/P6), inward absorption (P5) — is weak in the same way every time: the mechanism was built for star-alliance's own repo and does not travel, was written but never armed, or logs without telling the truth. Roughly one-third of the intent is genuinely met; the rest is doctrine waiting for enforcement.
