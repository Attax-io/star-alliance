#!/usr/bin/env bash
# Prove a hook blocks the bad case AND allows the good case before wiring it live.
#
# Usage:
#   test_hook.sh <hook.py> '<should-BLOCK event json>' '<should-ALLOW event json>'
#
# Example:
#   test_hook.sh .claude/hooks/your-gate.py \
#     '{"tool_name":"Bash","tool_input":{"command":"rm -rf /"}}' \
#     '{"tool_name":"Bash","tool_input":{"command":"ls"}}'
#
# An untested hook is a guess. The dangerous bug is one that blocks the GOOD
# case, so both branches are checked. A block is exit 2 with a reason on stderr.
set -u

HOOK="${1:?path to hook script}"
BLOCK_EVENT="${2:?should-block event JSON}"
ALLOW_EVENT="${3:?should-allow event JSON}"

run() { printf '%s' "$2" | python3 "$HOOK"; printf '%s' "$?"; }

echo "── should BLOCK ─────────────────────────────"
ec_block="$(run "$HOOK" "$BLOCK_EVENT")"
echo "  exit=$ec_block  (want 2)"
[ "$ec_block" = "2" ] && echo "  ✓ blocked" || echo "  ✗ did NOT block"

echo "── should ALLOW ─────────────────────────────"
ec_allow="$(run "$HOOK" "$ALLOW_EVENT")"
echo "  exit=$ec_allow  (want 0)"
[ "$ec_allow" = "0" ] && echo "  ✓ allowed" || echo "  ✗ wrongly blocked the good case"

echo "── fail-open ────────────────────────────────"
ec_garbage="$(printf 'not json' | python3 "$HOOK"; printf '%s' "$?")"
echo "  garbage payload exit=$ec_garbage  (want 0 — must fail open)"
[ "$ec_garbage" = "0" ] && echo "  ✓ fails open" || echo "  ✗ crashes/blocks on bad input"

[ "$ec_block" = "2" ] && [ "$ec_allow" = "0" ] && [ "$ec_garbage" = "0" ] \
  && { echo "ALL GREEN"; exit 0; } || { echo "FIX BEFORE WIRING"; exit 1; }
