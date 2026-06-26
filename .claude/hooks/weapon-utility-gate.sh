#!/bin/sh
# ─────────────────────────────────────────────────────────────────────────────
# Star Alliance — WEAPON-UTILITY ENFORCEMENT HOOK  (UserPromptSubmit)
#
# Why this exists: the guild DESCRIBED delegation (weapon-utility skill, CLAUDE.md
# "MiniMax first") but never ENFORCED it — the orchestrator kept doing doer-grade
# work inline on Opus, burning premium tokens the cheap bench was meant to absorb.
# A doc line proved non-binding. This hook is harness-executed: it injects the
# delegate-first rule into context on EVERY task, so the rule is unmissable at the
# exact moment a decision is made — regardless of what the orchestrator "remembers."
#
# Output on stdout (exit 0) is added to the model's context by Claude Code.
# Keep it terse: a ~60-token nudge per turn is trivial against the Opus tokens
# saved by delegating even one task to a doer.
# ─────────────────────────────────────────────────────────────────────────────
cat <<'EOF'
⚔ WEAPON-UTILITY GATE (Star Alliance harness — harness-injected, binding):
Delegate doer-grade work — bulk edits, extraction, generation, mechanical transforms,
large reads/summaries — to a DOER. This is the default; inline Opus execution of
doer-grade work is the exception and must be justified out loud.
  Fire:  python3 star-alliance-arsenal/summon.py <model> "<prompt>"   (-s sys · --json · -f file)
  Order: doers first, cheapest left→right — minimax-m3, gemma4, kimi-k2.7 — then thinkers; sonnet last-resort.
  Availability: skip any weapon not pulled/reachable (Ollama bench needs `ollama list` to show it).
Opus stays the mind: orchestrate, plan, prompt the doer, review the result against the plan, re-prompt until it conforms.
EOF
exit 0
