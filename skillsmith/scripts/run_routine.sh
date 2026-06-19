#!/bin/bash
# skillsmith — daily routine runner (called by the LaunchAgent, or by hand).
# Invokes Claude Code headless on `routine` mode with full perms + a cost cap, and
# tees everything to a dated log you can tail. See references/routine-playbook.md §R7.
#
# Run by hand:   bash scripts/run_routine.sh
# Watch it:      tail -f routine-logs/$(date +%F).log
set -uo pipefail

# ── config (tune here) ───────────────────────────────────────────────
REPO="${CLAUDE_SKILLS_REPO:-$HOME/Documents/Claude/Projects/claude-skills}"
CLAUDE_BIN="/opt/homebrew/bin/claude"
MODEL="opus"
MAX_BUDGET_USD="10"          # hard ceiling per run (§R5)
# ─────────────────────────────────────────────────────────────────────

export PATH="/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"
cd "$REPO" || { echo "skillsmith routine: repo not found at $REPO" >&2; exit 1; }

DATE="$(date +%F)"
LOGDIR="$REPO/skillsmith/routine-logs"
mkdir -p "$LOGDIR"
LOG="$LOGDIR/$DATE.log"

read -r -d '' PROMPT <<'EOF'
Run the skillsmith `routine` mode now, fully autonomously, end to end.

Invoke the skillsmith skill and follow references/routine-playbook.md exactly:
Stage A harvest (scripts/routine_scan.py) → Stage B STORM research per active skill
(references/storm-method.md) → Stage C write today's ledger entry incrementally as you
go → Stage D execute every finding with peer-review confidence >= 8/10 that clears the
§R4 guards (upgrade existing skills, create genuinely new ones, fix bugs — skillsmith
itself last, per §R6) → Stage E commit each change separately and `git push origin main`,
then write the Run Summary at the top of today's ledger entry.

You are unattended. Do not ask questions; apply the autonomy contract as written (fully
autonomous, >=8/10 gate, forks/externals never auto-edited, everything a revertible
commit). Respect the per-run budget in §R5 (top ~3 actions, ~8 skills STORMed). Narrate
each stage to the ledger so the run is watchable. If you cannot finish a stage, write what
you learned to the ledger and stop cleanly.
EOF

{
  echo "═══ skillsmith routine $DATE $(date +%T) ═══"
  echo "repo=$REPO model=$MODEL budget=\$$MAX_BUDGET_USD"
  "$CLAUDE_BIN" -p "$PROMPT" \
    --model "$MODEL" \
    --permission-mode bypassPermissions \
    --max-budget-usd "$MAX_BUDGET_USD" \
    --verbose
  echo "═══ done $(date +%T) (exit $?) ═══"
} 2>&1 | tee -a "$LOG"
