---
type: findings
campaign: audit-campaigns/2026-07-02_skills-frontmatter
section: 4
title: Hook ↔ Skill Coverage (45 hooks surveyed)
---

# Hook ↔ Skill Coverage — 45 hooks

| Of those | Count |
|---|---|
| mention "skill" | 18 |
| reference explicit skill names | 13 |

## Coverage table

| Hook | Validates against | Mentions skill? | Size |
|---|---|---|---|
| devserver-gate.py | — | no | 5950 B |
| unity-gate.py | cleanup, code-unity | yes | 4279 B |
| hermes-upgrade-notify.py | — | yes | 4464 B |
| guild-routing-gate.sh | high-alert, image-to-code, members-formation, performance, supabase, weapon-utility | yes | 18313 B |
| guild-log-nudge.py | — | no | 2265 B |
| unity-skill-gate.py | code-unity, design-unity, high-alert | yes | 3504 B |
| connector-gate.py | — | no | 6735 B |
| test_dispatch_enforce.py | high-alert | yes | 5910 B |
| delegation-gate.py | — | no | 12169 B |
| routing-enforce.py | — | no | 8072 B |
| safe-read-gate.py | — | no | 3868 B |
| turn-start.py | — | no | 4167 B |
| verify-gate.py | — | yes | 10615 B |
| vault-log-nudge.py | — | no | 2917 B |
| conformity-precommit-gate.py | — | no | 5870 B |
| workflow-gate.py | high-alert, skillsmith | yes | 11616 B |
| approval-gate.py | — | no | 5615 B |
| thinker-gate.py | — | no | 7830 B |
| build-mark.py | guild-log | yes | 2245 B |
| precompact-snapshot.py | — | no | 2481 B |
| _test_executor_enforce.sh | — | no | 12990 B |
| verify_hash.py | — | yes | 4062 B |
| version-auto-bump.py | guild-log | yes | 4850 B |
| approval-detect.py | — | no | 7659 B |
| stop-line-gate.py | — | no | 4811 B |
| xp-log.py | — | yes | 2034 B |
| _saroot.py | — | no | 2661 B |
| weapon-gate.py | ultra-brainstorming, weapon-utility | yes | 7268 B |
| spawn-log.py | — | no | 1641 B |
| prove-it.py | — | no | 13523 B |
| dispatch-log.py | — | no | 1698 B |
| member-skill-lint-gate.py | backend-auditor, db-rename-sweep, frontend-auditor, okf | yes | 10861 B |
| turn-finalize.sh | — | no | 6606 B |
| workflow-banner-enforcer.py | — | no | 14165 B |
| executor-enforce.py | — | no | 23323 B |
| plain-english-nudge.py | — | no | 5649 B |
| turn-cost.py | — | yes | 6388 B |
| destructive-gate.py | — | no | 5480 B |
| sa-pretool.py | high-alert, okf | yes | 4185 B |
| butler-skill-gate.py | butler-voice, helpless, star-alliance-language | yes | 10911 B |
| thinker-attest.py | — | no | 4381 B |
| high-alert.py | high-alert | yes | 3612 B |
| dispatch-enforce.py | — | no | 33158 B |
| okf-gate.py | impeccable, okf, star-alliance-language | yes | 5716 B |
| conformance-gate.py | — | no | 6383 B |

## Observation

Hook coverage is **narrow by design**. Most hooks consult 1–4 specific skills because each hook enforces one gate's doctrine. Mass coverage gaps are expected — a hook that tried to cover all 126 skills would be a coupling nightmare.

## No-action verdict

The coverage shape is correct. Do not broaden hooks to "fix" gaps; instead, when a NEW skill ships, the skill should declare which hook (if any) is responsible for its gate, and that hook should be updated.
