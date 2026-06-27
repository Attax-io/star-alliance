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
# It ALSO honors the independent-verification gate: when that gate is ARMED, this
# hook is a SIBLING Stop command and used to commit even while verify-gate blocked
# (exit 2 stops the Stop event but does NOT abort sibling hooks — git log proved
# it committed mid-block). So before committing we re-run the SAME source-changed
# check; if armed + source changed this turn + unverified, we skip the commit,
# making the gate's "nothing is committed while blocked" guarantee actually true.
#
# Fails OPEN (exit 0) on everything — a broken finalize must never block Stop.
# ─────────────────────────────────────────────────────────────────────────────

repo=$(git rev-parse --show-toplevel 2>/dev/null) || exit 0
state="$repo/.claude/state"
pending="$state/build-pending"

# 0. Honor the verify-gate (opt-in). Mirror verify-gate.py's allow condition so a
#    blocked turn commits NOTHING: stand down only when source changed this turn
#    (cur != baseline) AND it was not independently verified (cur != verify-pass).
if [ -f "$state/verify-gate-armed" ] && [ "${SA_SKIP_VERIFY:-}" != "1" ]; then
  cur=$(python3 "$repo/.claude/hooks/verify_hash.py" 2>/dev/null)
  case "$cur" in
    CLEAN|NOREPO|"") : ;;                       # no source change → safe to commit
    *)
      base=$(cat "$state/verify-baseline" 2>/dev/null)
      pass=$(cat "$state/verify-pass" 2>/dev/null)
      if [ "$cur" != "$base" ] && [ "$cur" != "$pass" ]; then
        echo "[turn-finalize] verify-gate armed + source changed this turn and unverified — commit skipped" >&2
        exit 0
      fi ;;
  esac
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
