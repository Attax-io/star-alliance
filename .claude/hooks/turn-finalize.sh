#!/bin/sh
# ─────────────────────────────────────────────────────────────────────────────
# Star Alliance — TURN FINALIZE  (Stop hook, Phase 3 upkeep cap)
#
# Why this exists: the harness's own cost used to SCALE WITH ITS EDIT COUNT — a
# build.py spawn and a git commit fired on the PostToolUse-per-edit path. None of
# that is on the critical path: the dashboard and the member table are VIEWS; the
# commit only needs to be one-per-logical-change. This Stop hook caps it at ONCE
# PER TURN:
#
#   1. Regenerate generated outputs (build.py) ONCE — but only if build-mark.py
#      flagged that a build-source actually changed this turn (.claude/state/
#      build-pending). Any source (member / skill / workflow / art / guild-log)
#      arms it; we build a single time regardless of how many edits there were.
#   2. Coalesce ALL of the turn's working-tree changes into ONE commit, with a
#      MEANINGFUL subject derived from the changed paths — not the old opaque
#      "auto: session turn" that buried git history (183/200 commits were that
#      one string, defeating the "read git log before continuing" discipline).
#      Commit only; never push (push still needs an explicit ask).
#
# Fails OPEN (exit 0) on everything — a broken finalize must never block Stop.
# ─────────────────────────────────────────────────────────────────────────────

repo=$(git rev-parse --show-toplevel 2>/dev/null) || exit 0
state="$repo/.claude/state"
pending="$state/build-pending"

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
    # Meaningful subject: top changed paths + total count.
    n=$(git -C "$repo" diff --cached --name-only 2>/dev/null | wc -l | tr -d ' ')
    top=$(git -C "$repo" diff --cached --name-only 2>/dev/null \
            | sed 's#^\([^/]*/[^/]*\).*#\1#' | sort -u | head -3 \
            | tr '\n' ',' | sed 's/,$//; s/,/, /g')
    [ -z "$top" ] && top="working tree"
    if [ "$n" -gt 3 ]; then
      subject="auto: ${top} (+$((n-3)) more, ${n} files)"
    else
      subject="auto: ${top} (${n} file$( [ "$n" -eq 1 ] || echo s ))"
    fi
    git -C "$repo" commit -q \
      -m "$subject" \
      -m "Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>" \
      >/dev/null 2>&1
  fi
fi

exit 0
