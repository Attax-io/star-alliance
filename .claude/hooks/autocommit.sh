#!/bin/sh
# ─────────────────────────────────────────────────────────────────────────────
# Star Alliance — AUTO-COMMIT  (PostToolUse: Edit | Write | MultiEdit)
#
# Why this exists: the Guild Master never wants to be asked "Commit?" again.
# Every successful file edit is committed on its own, immediately, by this hook —
# so the Butler (and every member) stops pausing to ask. Commit ONLY; never push
# (push still needs an explicit ask, per the standing rule).
#
# Behaviour:
#   • Reads PostToolUse JSON from stdin, pulls tool_input.file_path.
#   • Stages and commits ONLY that one file.
#   • No-ops silently when: no file_path, file outside the repo, or nothing staged
#     (e.g. the edit produced no net change). Never blocks the tool — always exit 0.
#   • Commit message is auto-generated from the path + tool name.
# Partial / mid-task states ARE committed by design — per-edit granularity is the
# point. History stays linear and revertable; nothing is pushed.
# ─────────────────────────────────────────────────────────────────────────────

payload=$(cat)

file_path=$(printf '%s' "$payload" | jq -r '.tool_input.file_path // empty' 2>/dev/null)
tool_name=$(printf '%s' "$payload" | jq -r '.tool_name // "edit"' 2>/dev/null)

# Nothing to commit if no path was provided.
[ -z "$file_path" ] && exit 0
# File must still exist (a Write that deleted/renamed could leave nothing).
[ -e "$file_path" ] || exit 0

# Resolve the repo root from the edited file's directory; bail if not in a repo.
file_dir=$(dirname "$file_path")
repo_root=$(git -C "$file_dir" rev-parse --show-toplevel 2>/dev/null) || exit 0

# Stage only this file.
git -C "$repo_root" add -- "$file_path" 2>/dev/null || exit 0

# Nothing actually staged (no net change) → no-op.
if git -C "$repo_root" diff --cached --quiet -- "$file_path" 2>/dev/null; then
  exit 0
fi

# Path relative to the repo root, for a readable commit subject.
rel=$(git -C "$repo_root" ls-files --full-name -- "$file_path" 2>/dev/null | head -1)
[ -z "$rel" ] && rel=$(basename "$file_path")

git -C "$repo_root" commit --only \
  -m "auto: ${tool_name} ${rel}" \
  -m "Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>" \
  -- "$file_path" \
  >/dev/null 2>&1

exit 0
