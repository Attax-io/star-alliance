#!/bin/sh
# ─────────────────────────────────────────────────────────────────────────────
# Star Alliance — WEAPON-UTILITY ENFORCEMENT HOOK  (UserPromptSubmit)
#
# Why this exists: the guild DESCRIBED delegation (weapon-utility skill, CLAUDE.md
# "MiniMax first") but never ENFORCED it — a member (the Butler included) kept doing
# doer-grade work itself instead of handing it to its own doer weapons, burning
# premium thinker tokens the cheap bench was meant to absorb. A doc line proved
# non-binding. This hook is harness-executed: it injects the draw-your-weapons rule
# into context on EVERY task, so the rule is unmissable at the exact moment a
# decision is made — regardless of what the member "remembers."
#
# Output on stdout (exit 0) is added to the model's context by Claude Code.
# Keep it terse: a ~60-token nudge per turn is trivial against the premium tokens
# saved by handing even one task to a doer weapon.
# ─────────────────────────────────────────────────────────────────────────────
cat <<'EOF'
⚔ WEAPON-UTILITY GATE (Star Alliance harness — harness-injected, binding):
Every member — the Butler included — draws from his OWN arsenal per weapon-utility.
Hand doer-grade work — bulk edits, extraction, generation, mechanical transforms,
large reads/summaries — to one of the member's DOER weapons. This is the default;
doing it yourself in the thinker is the exception and must be justified out loud.
  Fire:  python3 star-alliance-arsenal/summon.py <model> "<prompt>"   (-s sys · --json · -f file)
  Order: scan the member's own arsenal left→right — doers before thinkers, cheapest doer first; skip any weapon not pulled/reachable (Ollama bench needs `ollama list` to show it).
The member's THINKER weapon stays the mind: plan, prompt the doer, review the result against the plan, re-prompt until it conforms. The thinker need NOT be Opus — it is whichever thinker-capable weapon the member carries.
EOF
exit 0
