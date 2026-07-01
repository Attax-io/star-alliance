#!/usr/bin/env bash
# star-alliance/install.sh — deploy a member + skills into a target project
#
# Usage:
#   ./star-alliance-arsenal/install.sh <member-name> <target-project-path> [--tier 1|2|3]
#
# Tiers:
#   1  Skills only (default) — syncs this member's skills to target .claude/skills/
#   2  Tier 1 + member agent file + STAR_ALLIANCE_ROOT in target settings.json
#   3  Tier 2 + hooks + hook wiring + workflows-lite.json
#
# Example:
#   ./star-alliance-arsenal/install.sh the-developer /path/to/my-project --tier 2

set -euo pipefail

SA_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MEMBERS_DIR="$SA_ROOT/star-alliance-members"
SKILLS_DIR="$SA_ROOT/star-alliance-skills"
HOOKS_DIR="$SA_ROOT/.claude/hooks"

# ── args ────────────────────────────────────────────────────────────────────
MEMBER_NAME=""
TARGET=""
TIER=1

while [[ $# -gt 0 ]]; do
  case "$1" in
    --tier) TIER="$2"; shift 2 ;;
    --tier=*) TIER="${1#--tier=}"; shift ;;
    -*) echo "Unknown flag: $1"; exit 1 ;;
    *) if [[ -z "$MEMBER_NAME" ]]; then MEMBER_NAME="$1";
       elif [[ -z "$TARGET" ]]; then TARGET="$1";
       fi; shift ;;
  esac
done

if [[ -z "$MEMBER_NAME" || -z "$TARGET" ]]; then
  echo "Usage: $0 <member-name> <target-project-path> [--tier 1|2|3]"
  exit 1
fi

MEMBER_FILE="$MEMBERS_DIR/${MEMBER_NAME}.md"
if [[ ! -f "$MEMBER_FILE" ]]; then
  echo "❌ Member not found: $MEMBER_FILE"
  echo "   Available: $(ls "$MEMBERS_DIR"/*.md | xargs -n1 basename | sed 's/\.md//' | tr '\n' ' ')"
  exit 1
fi

if [[ ! -d "$TARGET" ]]; then
  echo "❌ Target project not found: $TARGET"
  exit 1
fi

echo "⚔  Star Alliance Install"
echo "   Member  : $MEMBER_NAME"
echo "   Target  : $TARGET"
echo "   Tier    : $TIER"
echo ""

# ── deploy ledger (append-only; the deployment-frequency axis for member-leveling Wave 6) ─────
DEPLOY_LEDGER="$SA_ROOT/star-alliance-skills/skillsmith/references/deploy-ledger.md"
if [[ ! -f "$DEPLOY_LEDGER" ]]; then
  printf '%s\n' '# Deploy Ledger' '' 'Append-only record of every `install.sh` deploy. Consumed by member-leveling Wave 6 (the usage/reach axis). Do not hand-prune.' '' '| Date | Member | Tier | Target |' '|---|---|---|---|' > "$DEPLOY_LEDGER"
fi
printf '| %s | `%s` | %s | `%s` |\n' "$(date +%Y-%m-%d)" "$MEMBER_NAME" "$TIER" "$TARGET" >> "$DEPLOY_LEDGER"

# ── helpers ─────────────────────────────────────────────────────────────────

ensure_dir() { mkdir -p "$1"; }

merge_env_to_settings() {
  local settings_file="$1"
  local key="$2"
  local value="$3"

  ensure_dir "$(dirname "$settings_file")"
  if [[ ! -f "$settings_file" ]]; then
    echo '{}' > "$settings_file"
  fi

  # Use python3 to safely merge the env key into settings.json
  python3 - "$settings_file" "$key" "$value" <<'PYEOF'
import sys, json
path, key, value = sys.argv[1], sys.argv[2], sys.argv[3]
with open(path) as f:
    data = json.load(f)
data.setdefault("env", {})[key] = value
with open(path, "w") as f:
    json.dump(data, f, indent=2)
    f.write("\n")
print(f"  ✓ env.{key} = {value}")
PYEOF
}

merge_hooks_to_settings() {
  local settings_file="$1"
  local hooks_src="$SA_ROOT/.claude/settings.json"

  python3 - "$settings_file" "$hooks_src" <<'PYEOF'
import sys, json
target_path, src_path = sys.argv[1], sys.argv[2]

with open(target_path) as f:
    target = json.load(f)
with open(src_path) as f:
    src = json.load(f)

# Merge hooks: append SA hooks that aren't already present
src_hooks = src.get("hooks", {})
tgt_hooks = target.setdefault("hooks", {})

for event, entries in src_hooks.items():
    tgt_event = tgt_hooks.setdefault(event, [])
    for entry in entries:
        # entry is either a hook object or a list-of-hooks object
        cmds = [h.get("command","") for block in (entry if isinstance(entry, list) else [entry])
                for h in (block.get("hooks",[]) if "hooks" in block else [block])]
        # skip if any command from this entry already present
        existing_cmds = [h.get("command","") for block in tgt_event
                         for h in (block.get("hooks",[]) if "hooks" in block else [block])]
        if not any(c in existing_cmds for c in cmds if c):
            tgt_event.append(entry)

with open(target_path, "w") as f:
    json.dump(target, f, indent=2)
    f.write("\n")
print("  ✓ hooks merged into target settings.json")
PYEOF
}

# ── extract member's skill list ──────────────────────────────────────────────

MEMBER_SKILLS=$(python3 - "$MEMBER_FILE" <<'PYEOF'
import sys, re
with open(sys.argv[1]) as f:
    content = f.read()
m = re.search(r'^skills:\s*\[([^\]]+)\]', content, re.MULTILINE)
if m:
    skills = [s.strip() for s in m.group(1).split(',')]
    print('\n'.join(skills))
PYEOF
)

# ── tier 1: install skills ───────────────────────────────────────────────────

echo "── Tier 1: Skills"
TARGET_SKILLS="$TARGET/.claude/skills"
ensure_dir "$TARGET_SKILLS"

INSTALLED=0
SKIPPED=0
while IFS= read -r skill; do
  [[ -z "$skill" ]] && continue
  skill_src="$SKILLS_DIR/$skill"
  skill_dst="$TARGET_SKILLS/$skill"
  if [[ ! -d "$skill_src" ]]; then
    echo "  ⚠  skill not found in repo: $skill (skipped)"
    ((SKIPPED++)) || true
    continue
  fi
  if [[ -d "$skill_dst" ]]; then
    # Check version
    src_ver=$(python3 -c "import re,sys; m=re.search(r'version:\s*(\S+)', open(sys.argv[1]).read()); print(m.group(1) if m else '?')" "$skill_src/SKILL.md" 2>/dev/null || echo "?")
    dst_ver=$(python3 -c "import re,sys; m=re.search(r'version:\s*(\S+)', open(sys.argv[1]).read()); print(m.group(1) if m else '?')" "$skill_dst/SKILL.md" 2>/dev/null || echo "?")
    if [[ "$src_ver" == "$dst_ver" ]]; then
      echo "  ✓ $skill v$src_ver (already current)"
      ((SKIPPED++)) || true
      continue
    fi
    echo "  ↑ $skill $dst_ver → $src_ver"
  else
    echo "  + $skill"
  fi
  cp -r "$skill_src" "$TARGET_SKILLS/"
  ((INSTALLED++)) || true
done <<< "$MEMBER_SKILLS"

echo "  Skills: $INSTALLED installed/updated, $SKIPPED already current"
echo ""

if [[ "$TIER" -lt 2 ]]; then
  echo "✅ Tier 1 complete."
  exit 0
fi

# ── tier 2: member agent + env var ──────────────────────────────────────────

echo "── Tier 2: Member agent"
AGENTS_DIR="$TARGET/.claude/agents"
ensure_dir "$AGENTS_DIR"

cp "$MEMBER_FILE" "$AGENTS_DIR/${MEMBER_NAME}.md"
echo "  ✓ $MEMBER_NAME.md → $AGENTS_DIR/"

TARGET_SETTINGS="$TARGET/.claude/settings.json"
merge_env_to_settings "$TARGET_SETTINGS" "STAR_ALLIANCE_ROOT" "$SA_ROOT"
echo ""

if [[ "$TIER" -lt 3 ]]; then
  echo "✅ Tier 2 complete."
  echo ""
  echo "   Next: add to your project CLAUDE.md:"
  echo "   'Arsenal tools path: \$STAR_ALLIANCE_ROOT/star-alliance-arsenal/'"
  exit 0
fi

# ── tier 3: hooks + workflows-lite ──────────────────────────────────────────

echo "── Tier 3: Hooks + workflows"
TARGET_HOOKS="$TARGET/.claude/hooks"
ensure_dir "$TARGET_HOOKS"

# Copy hooks
for hook in "$HOOKS_DIR"/*.py "$HOOKS_DIR"/*.sh; do
  [[ -f "$hook" ]] || continue
  hook_name=$(basename "$hook")
  cp "$hook" "$TARGET_HOOKS/$hook_name"
  echo "  + hook: $hook_name"
done

# Pre-seed the evolution kill-switch so a fresh Tier-3 target cannot lock
# its main session with no unlock path. The Tier-3 wiring copies the gate
# hooks but not the dispatch substrate they route around (dispatch.py,
# the arsenal, the evolution engine itself). Until that substrate lands,
# `evolution/DISARMED` keeps the gates off. Once dispatch.py + arsenal +
# evolution are present and working, the operator removes the file to
# arm enforcement. Mirror the printf style used to seed DEPLOY_LEDGER.
ensure_dir "$TARGET/evolution"
if [[ ! -f "$TARGET/evolution/DISARMED" ]]; then
  printf '%s\n' \
    '# DISARMED — evolution engine gates are OFF on this target.' \
    'A fresh Tier-3 install copies the enforcement hooks without the dispatch substrate they route around (dispatch.py, arsenal, evolution engine). Until that substrate is in place, gates would lock the main session with no unlock path.' \
    'Remove this file ONLY once dispatch.py + arsenal + evolution are present and working.' \
    > "$TARGET/evolution/DISARMED"
fi
echo "  ✓ pre-seeded evolution/DISARMED (safety kill-switch)"

# Merge hook wiring into target settings.json
# Rewrite hook paths to use CLAUDE_PROJECT_DIR (they already do — just merge)
merge_hooks_to_settings "$TARGET_SETTINGS"

# Copy workflows-lite.json
WORKFLOWS_LITE="$SA_ROOT/star-alliance-arsenal/workflows-lite.json"
if [[ -f "$WORKFLOWS_LITE" ]]; then
  cp "$WORKFLOWS_LITE" "$TARGET/workflows.json"
  echo "  ✓ workflows-lite.json → $TARGET/workflows.json"
else
  echo "  ⚠  workflows-lite.json not yet created — copy $SA_ROOT/workflows.json manually"
fi

echo ""
echo "✅ Tier 3 complete."
echo ""
echo "   Remaining manual step:"
echo "   Copy the relevant CLAUDE.md sections (reading discipline, guild conduct)"
echo "   into $TARGET/CLAUDE.md"
