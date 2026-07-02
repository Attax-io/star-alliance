---
type: findings
campaign: audit-campaigns/2026-07-02_skills-frontmatter
section: 3
title: Trigger Coverage (62 declared phrases · 7 active, 55 dead/orphan)
---

# Trigger Coverage — 62 declared phrases

| Verdict | Count |
|---|---|
| active | 7 |
| dead/orphan | 55 |

## Per-phrase table

| Skill | Declared phrase | Hook fires? | Workflow trigger? | Ledger fired? | Verdict |
|---|---|---|---|---|---|
| a11y-craft | is this accessible | no | no | no | dead-or-orphan |
| agentic-video-production | make a video about X | no | no | no | dead-or-orphan |
| api-integration-design | design the API for X | no | no | no | dead-or-orphan |
| arsenal-forge | add a weapon | no | no | no | dead-or-orphan |
| backend-auditor | audit the backend | no | no | no | dead-or-orphan |
| butler-onboarding | what can you do | no | no | no | dead-or-orphan |
| claude-code-hooks | write a hook | no | no | no | dead-or-orphan |
| cleanup | run cleanup | no | no | no | dead-or-orphan |
| code-unity | one source of truth | yes | no | no | active |
| cold-doc-rotator | rotate cold docs | no | no | no | dead-or-orphan |
| comms-triage | triage my inbox | no | yes | no | active |
| contract-review | review this contract | no | no | no | dead-or-orphan |
| dashboard-parity | is it on the dashboard | no | no | no | dead-or-orphan |
| decompose-and-swarm | swarm this | no | yes | no | active |
| design-language | use the X voice | no | no | no | dead-or-orphan |
| design-taste | design the UI | no | no | no | dead-or-orphan |
| design-tokens | design tokens | no | no | no | dead-or-orphan |
| design-unity | make the UI consistent | no | no | no | dead-or-orphan |
| dev-ops-command-pack | start work on this | no | no | no | dead-or-orphan |
| dual-model-review | dual review | no | no | no | dead-or-orphan |
| financial-data-reach | pull the fundamentals for X | no | no | no | dead-or-orphan |
| frontend-auditor | audit the frontend | no | no | no | dead-or-orphan |
| frontend-react-engineering | build this React component | no | no | no | dead-or-orphan |
| growth-marketing | plan our marketing | no | no | no | dead-or-orphan |
| guild-conformity | run the conformity check | no | no | no | dead-or-orphan |
| guild-reflection | reflect on this | no | yes | no | active |
| harness-efficiency | efficiency report | no | no | no | dead-or-orphan |
| health-checker | db health check | no | no | no | dead-or-orphan |
| heat-map-analyst | heat map | no | no | no | dead-or-orphan |
| imagegen-frontend | generate website design references | no | no | no | dead-or-orphan |
| invariant-inference | infer the invariant | no | no | no | dead-or-orphan |
| law-harvest | harvest the laws | no | no | no | dead-or-orphan |
| leaders-command | command the team | no | no | no | dead-or-orphan |
| legal-drafting | draft a client email | no | yes | no | active |
| legal-rule-modeling | model the law for this calculator | no | no | no | dead-or-orphan |
| market-recon | analyze this investment | no | no | no | dead-or-orphan |
| members-formation | route this | no | yes | no | active |
| metamorphosis-check | something changed | no | no | no | dead-or-orphan |
| motion-design | animate this | no | no | no | dead-or-orphan |
| negotiation-deal-strategy | prep this negotiation | no | no | no | dead-or-orphan |
| obedience | don't over-do it | no | no | no | dead-or-orphan |
| observability-incident-response | the app is down | no | no | no | dead-or-orphan |
| pattern-detector | detect patterns | no | no | no | dead-or-orphan |
| pattern-library-discovery | find a pattern for X | no | no | no | dead-or-orphan |
| portability-audit | audit portability | no | no | no | dead-or-orphan |
| portfolio-risk | review my portfolio | no | no | no | dead-or-orphan |
| project-start | start session | no | no | no | dead-or-orphan |
| python-master | set up a python library | no | no | no | dead-or-orphan |
| relationship-intel | sweep my email for relationship intel | no | no | no | dead-or-orphan |
| release-train | cut a release | no | no | no | dead-or-orphan |
| safe-agentic-orchestration | orchestrate this team | no | no | no | dead-or-orphan |
| scheduled-watch | schedule this | no | no | no | dead-or-orphan |
| schema-evolution | add a field to | no | no | no | dead-or-orphan |
| skillsmith | sync my skills | no | no | no | dead-or-orphan |
| spec-driven-development | spec this out | no | no | no | dead-or-orphan |
| trading-strategy | build a trading strategy | no | no | no | dead-or-orphan |
| ultra-brainstorming | ultra-brainstorm this | no | no | no | dead-or-orphan |
| ux-copywriting | write the error message | no | no | no | dead-or-orphan |
| voices-check | name the voices | no | no | no | dead-or-orphan |
| weapon-utility | what | yes | no | no | active |
| workflow-forge | save this as a workflow | no | no | no | dead-or-orphan |
| workflow-runner | run the X workflow | no | no | no | dead-or-orphan |

## Interpretation

Most "dead/orphan" verdicts are **not bugs**. The guild routes skills by **description matching**, not by hook-firing on a phrase. A skill is alive when a member agent invokes it because the request fits the description — not when a hook intercepts a magic phrase.

Some "dead" phrases are demonstrably intentional workflow-triggers re-used as skill-trigger phrasing (e.g. `comms-triage → 'triage my inbox'` matches the Comms Triage workflow's `trigger_phrases`).

## Recommended action

Do NOT add hooks to "wake up" dead phrases. Instead:

1. **Prune the dead phrases from skill descriptions** if they're not used as routing keywords by any member agent.
2. **Document the natural-language-routing convention** in `star-alliance-language` SKILL.md so members don't expect phrase hooks.
