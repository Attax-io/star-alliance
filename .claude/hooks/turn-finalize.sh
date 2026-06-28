#!/bin/sh
# ─────────────────────────────────────────────────────────────────────────────
# Star Alliance — TURN FINALIZE  (Stop hook, Phase 3 upkeep cap)
#
# Caps the harness's own per-turn cost at ONCE PER TURN:
#   1. Regenerate generated outputs (build.py) ONCE — only if build-mark.py
#      flagged a build-source change this turn (.claude/state/build-pending).
#   2. Coalesce ALL of the turn's working-tree changes into ONE commit, with a
#      MEANINGFUL subject. The subject leads with the turn's declared workflow
#      (state/last-workflow) when known, then the top changed paths + count — so
#      git log reads as a ledger of WHAT each turn did, not "auto: session turn".
#      Commit only; never push (push still needs an explicit ask).
#
# It ALSO honors the independent-verification gate, which is now ARMED BY DEFAULT
# (the old opt-in .claude/state/verify-gate-armed touch-file is retired). This hook
# is a SIBLING Stop command and would commit even while verify-gate blocked (exit 2
# stops the Stop event but does NOT abort sibling hooks — git log proved it committed
# mid-block). So unless the gate is disarmed (mirror verify-gate.py's own conditions:
# evolution/DISARMED, .claude/state/verify-gate-disarmed, or SA_SKIP_VERIFY=1) we
# re-run the SAME source-changed check; if source changed this turn + unverified, we
# skip the commit, making the gate's "nothing is committed while blocked" guarantee
# actually true.
#
# Fails OPEN (exit 0) on everything — a broken finalize must never block Stop.
# ─────────────────────────────────────────────────────────────────────────────

repo=$(git rev-parse --show-toplevel 2>/dev/null) || exit 0
state="$repo/.claude/state"
pending="$state/build-pending"

# 0. Honor the verify-gate (armed by default). Mirror verify-gate.py's allow
#    condition so a blocked turn commits NOTHING. The gate auto-records a pass
#    (writes verify-pass) on pass/concerns; on BLOCK it writes no pass, so a turn
#    whose fingerprint matches a real baseline but neither that baseline nor the
#    recorded pass is a blocked turn — stand down. This re-implements verify-gate.py's
#    disarm conditions + baseline-absent fail-open in sh; the two are maintained in
#    lock-step (keep this block in sync when the gate's disarm set changes).
#    NOTE: SA_AUTO_CRITIC=0 is deliberately NOT a disarm — in that mode the gate takes
#    the manual path and BLOCKS until a human records verify-pass, so skipping the
#    commit here is correct (work stays in the tree, nothing is lost).
disarmed=0
[ -f "$repo/evolution/DISARMED" ] && disarmed=1
[ -f "$state/verify-gate-disarmed" ] && disarmed=1
[ "${SA_SKIP_VERIFY:-}" = "1" ] && disarmed=1
if [ "$disarmed" != "1" ]; then
  cur=$(python3 "$repo/.claude/hooks/verify_hash.py" 2>/dev/null)
  case "$cur" in
    CLEAN|NOREPO|"") : ;;                       # no source change → safe to commit
    *)
      base=$(cat "$state/verify-baseline" 2>/dev/null)
      pass=$(cat "$state/verify-pass" 2>/dev/null)
      # base empty → gate fails open (no turn-start baseline); don't skip the commit.
      if [ -n "$base" ] && [ "$cur" != "$base" ] && [ "$cur" != "$pass" ]; then
        echo "[turn-finalize] verify-gate armed + source changed this turn and unverified — commit skipped" >&2
        exit 0
      fi ;;
  esac
fi

# 0b. Honor the executor (delegation) gate. Like verify-gate, delegation-gate.py is
#     a SIBLING Stop hook whose exit 2 does NOT abort this hook — so it drops a
#     sentinel on BLOCK that we mirror here to skip the commit. It clears the
#     sentinel on pass / SA_SOLO override, so its presence means "blocked this turn."
if [ ! -f "$repo/evolution/DISARMED" ] && [ ! -f "$state/delegation-gate-disarmed" ] \
   && [ "${SA_SOLO:-}" != "1" ] && [ -f "$state/delegation-block" ]; then
  echo "[turn-finalize] delegation-gate blocked this turn (doer-grade bulk, no doer call) — commit skipped" >&2
  exit 0
fi

# 1. Single rebuild if any build-source changed this turn (flag set by build-mark.py).
#    Build output is kept in a state log (not /dev/null) so a regression is
#    diagnosable from the next session — an independent-review finding.
if [ -f "$pending" ]; then
  if [ -f "$repo/build.py" ]; then
    python3 "$repo/build.py" >"$state/last-build.log" 2>&1 \
      || echo "[turn-finalize] build.py FAILED — see .claude/state/last-build.log" >&2
  fi
  rm -f "$pending" 2>/dev/null
fi

# 2. One coalesced commit for the whole turn (commit-only, never push).
if [ -n "$(git -C "$repo" status --porcelain 2>/dev/null)" ]; then
  git -C "$repo" add -A 2>/dev/null
  if ! git -C "$repo" diff --cached --quiet 2>/dev/null; then
    # Meaningful subject: <workflow>: top changed paths + total count.
    n=$(git -C "$repo" diff --cached --name-only 2>/dev/null | wc -l | tr -d ' ')
    top=$(git -C "$repo" diff --cached --name-only 2>/dev/null \
            | sed 's#^\([^/]*/[^/]*\).*#\1#' | sort -u | head -3 \
            | tr '\n' ',' | sed 's/,$//; s/,/, /g')
    [ -z "$top" ] && top="working tree"
    if [ "$n" -gt 3 ]; then
      paths="${top} (+$((n-3)) more, ${n} files)"
    else
      paths="${top} (${n} file$( [ "$n" -eq 1 ] || echo s ))"
    fi
    wf=$(cat "$state/last-workflow" 2>/dev/null | tr -d '\n')
    if [ -n "$wf" ]; then
      subject="${wf}: ${paths}"
    else
      subject="auto: ${paths}"
    fi
    git -C "$repo" commit -q \
      -m "$subject" \
      -m "Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>" \
      >/dev/null 2>&1
  fi
fi

exit 0
