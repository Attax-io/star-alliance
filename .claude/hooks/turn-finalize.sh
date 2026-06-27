#!/bin/sh
# ─────────────────────────────────────────────────────────────────────────────
# Star Alliance — TURN FINALIZE  (Stop hook, Phase 3 upkeep cap)
#
# Why this exists: the harness's own cost used to SCALE WITH ITS EDIT COUNT. Three
# bookkeeping jobs ran on the PostToolUse-per-edit path — member-table regen
# (build.py) and a fresh git commit FOR EVERY SINGLE FILE WRITE — producing the
# `auto: Edit app.css` / `auto: Edit app.js` commit storm and a build.py spawn per
# edit. None of that is on the critical path: the dashboard and the table are
# VIEWS; the commit only needs to be one-per-logical-change.
#
# This Stop hook moves that work to ONCE PER TURN:
#   1. Regenerate member tables (build.py) ONLY if a loadout source actually
#      changed this turn (a member .md or members-meta.json) — not on every edit.
#   2. Coalesce ALL of the turn's working-tree changes into ONE commit. Commit
#      only; never push (push still needs an explicit ask, per the standing rule).
#
# Fails OPEN (exit 0) on everything — a broken finalize must never block Stop.
# ─────────────────────────────────────────────────────────────────────────────

repo=$(git rev-parse --show-toplevel 2>/dev/null) || exit 0

# 1. Regenerate member tables only when a loadout source changed this turn.
if git -C "$repo" status --porcelain 2>/dev/null \
     | grep -qE 'star-alliance-members/.*\.md|data/members-meta\.json'; then
  [ -f "$repo/build.py" ] && python3 "$repo/build.py" >/dev/null 2>&1
fi

# 2. One coalesced commit for the whole turn (commit-only, never push).
if [ -n "$(git -C "$repo" status --porcelain 2>/dev/null)" ]; then
  git -C "$repo" add -A 2>/dev/null
  if ! git -C "$repo" diff --cached --quiet 2>/dev/null; then
    git -C "$repo" commit -q \
      -m "auto: session turn" \
      -m "Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>" \
      >/dev/null 2>&1
  fi
fi

exit 0
