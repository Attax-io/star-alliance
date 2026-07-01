#!/usr/bin/env bash
# star-alliance/install.sh — deploy a member + skills into a target project
#
# Usage:
#   ./star-alliance-arsenal/install.sh <member-name> <target-project-path> [--tier 1|2|3]
#
# Tiers:
#   1  Skills only (default) — syncs this member's skills to target .claude/skills/
#   2  Tier 1 + member agent file + STAR_ALLIANCE_ROOT in target settings.json
#   3  Tier 2 + hooks + hook wiring + workflows-lite.json + the dispatch
#      substrate the gates route to (tools/dispatch.py + arsenal + evolution)
#      + an idempotent Hermes worker bootstrap with a dispatch-path preflight
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

# Write a managed doctrine block into a target markdown file, idempotently.
# $1 = target file, $2 = marker label (e.g. "STAR-ALLIANCE DOCTRINE"), $3 = source file to embed
write_managed_block() {
  local target="$1" label="$2" src="$3"
  local open="<!-- ${label} (managed) -->"
  local close="<!-- /${label} -->"
  ensure_dir "$(dirname "$target")"
  [[ -f "$target" ]] || : > "$target"
  # Strip any existing managed block (open..close inclusive), leaving the operator's own content intact.
  awk -v o="$open" -v c="$close" '
    $0==o {skip=1; next}
    $0==c {skip=0; next}
    !skip {print}
  ' "$target" > "${target}.sa_tmp"
  # Drop trailing blank lines, then append a fresh block.
  awk 'NF{last=NR} {lines[NR]=$0} END{for(i=1;i<=last;i++)print lines[i]}' "${target}.sa_tmp" > "$target"
  {
    # ensure one blank separator if file already had content
    [[ -s "$target" ]] && printf '\n'
    printf '%s\n' "$open"
    printf '%s\n' "<!-- AUTO-GENERATED by star-alliance install.sh — do not edit inside this block; re-run install to update. -->"
    cat "$src"
    printf '%s\n' "$close"
  } >> "$target"
  rm -f "${target}.sa_tmp"
}

# Copy a directory tree into the target, then strip dead weight so a Tier-3 target
# stays lean and never inherits transient state: caches (__pycache__/*.pyc), backups
# (*.bak/*.orig/*~), test scaffolding (_test_*/test_*), OS cruft (.DS_Store), archived
# history (archive/), and heavy append-only logs (ledger.jsonl, usage-log.jsonl,
# models-usage.json) that must start EMPTY on a fresh target.
copy_pruned() {
  local src="$1" dst="$2"
  ensure_dir "$(dirname "$dst")"
  rm -rf "$dst"
  cp -r "$src" "$dst"
  find "$dst" \( \
      -name '__pycache__' -o -name '*.pyc' -o -name '*.bak' -o -name '*.orig' \
      -o -name '*~' -o -name '_test_*' -o -name 'test_*' -o -name '.DS_Store' \
      -o -name 'archive' \
    \) -exec rm -rf {} + 2>/dev/null || true
  find "$dst" \( -name 'ledger.jsonl' -o -name 'usage-log.jsonl' \
      -o -name 'models-usage.json' \) -delete 2>/dev/null || true
}

# Provision each installed Hermes profile's .env with the doer keys (idempotent).
# Upserts the KEY=VALUE lines from the machine key files without clobbering any
# other keys already present in the profile .env.
provision_profile_envs() {
  local pdir="$HOME/.hermes/profiles"
  [[ -d "$pdir" ]] || { echo "    - no installed profiles yet (skip .env provisioning)"; return 0; }
  local sub="" payg=""
  [[ -f "$HOME/.config/minimax/m3-sub.key"  ]] && sub="$(tr -d '[:space:]'  < "$HOME/.config/minimax/m3-sub.key")"
  [[ -f "$HOME/.config/minimax/m3-payg.key" ]] && payg="$(tr -d '[:space:]' < "$HOME/.config/minimax/m3-payg.key")"
  if [[ -z "$sub" ]]; then echo "    - doer key absent; cannot provision .env (skip)"; return 0; fi
  local count=0 prof env
  for prof in "$pdir"/*/; do
    [[ -d "$prof" ]] || continue
    env="${prof}.env"
    python3 - "$env" "$sub" "$payg" <<'PYENV'
import sys, pathlib
env, sub, payg = sys.argv[1], sys.argv[2], sys.argv[3]
p = pathlib.Path(env)
lines = p.read_text().splitlines() if p.exists() else []
def upsert(lines, key, val):
    if not val:
        return lines
    out, seen = [], False
    for ln in lines:
        if ln.strip().startswith(key + "="):
            out.append(key + "=" + val); seen = True
        else:
            out.append(ln)
    if not seen:
        out.append(key + "=" + val)
    return out
lines = upsert(lines, "MINIMAX_SUB_KEY", sub)
lines = upsert(lines, "MINIMAX_PAYG_KEY", payg)
p.write_text("\n".join(lines) + "\n")
PYENV
    count=$((count + 1))
  done
  echo "    OK provisioned doer keys into $count profile .env file(s)"
}

# Preflight: is the full dispatch path live? Prints one line per check and returns
# the number of problems (0 = dispatch path live, safe to arm gates).
hermes_preflight() {
  local problems=0
  if command -v hermes >/dev/null 2>&1; then
    echo "    OK hermes on PATH: $(command -v hermes)"
    if [[ -d "$HOME/.hermes/profiles" && -n "$(ls -A "$HOME/.hermes/profiles" 2>/dev/null)" ]]; then
      echo "    OK hermes profiles published"
    else
      echo "    XX hermes profiles not published - run: python3 \"$SA_ROOT/tools/publish_profiles.py\""
      problems=$((problems + 1))
    fi
  else
    echo "    XX hermes not found on PATH - install Hermes, then re-run this installer"
    problems=$((problems + 1))
  fi
  if [[ -f "$HOME/.config/minimax/m3-sub.key" ]]; then
    echo "    OK doer key present (~/.config/minimax/m3-sub.key)"
  else
    echo "    XX doer key missing - place the MiniMax sub key at ~/.config/minimax/m3-sub.key"
    problems=$((problems + 1))
  fi
  return "$problems"
}

# Idempotent Hermes worker bootstrap. Verifies/publishes profiles, provisions the
# per-profile .env, then runs the preflight. NEVER requires the network: every
# sub-step degrades to a printed instruction when a tool or key is absent. Leaves
# evolution/DISARMED in place (gates stay OFF) and prints the exact arm command -
# it never silently arms enforcement on someone's project.
bootstrap_hermes() {
  echo ""
  echo "-- Tier 3: Hermes worker bootstrap"
  if command -v hermes >/dev/null 2>&1 && [[ -f "$SA_ROOT/tools/publish_profiles.py" ]]; then
    echo "  - publishing Hermes profiles (idempotent; --update preserves auth/memories)"
    if python3 "$SA_ROOT/tools/publish_profiles.py" --update >/dev/null 2>&1; then
      echo "    OK profiles published/updated"
    else
      echo "    WARN publish_profiles.py returned nonzero (network or hermes issue) - re-run manually"
    fi
  else
    echo "  - skipping profile publish (hermes not on PATH or publisher missing)"
  fi
  echo "  - provisioning per-profile .env (doer keys)"
  provision_profile_envs
  echo "  - preflight: dispatch path"
  if hermes_preflight; then
    echo "  OK dispatch path LIVE - to arm enforcement on the target:"
    echo "      rm \"$TARGET/evolution/DISARMED\""
  else
    echo "  WARN dispatch path incomplete - evolution/DISARMED stays in place (gates OFF, no brick)."
    echo "     Fix the XX items above, then re-run this installer or: rm \"$TARGET/evolution/DISARMED\""
  fi
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
  # Skip dead weight: the blind *.py/*.sh glob would otherwise ship backups,
  # disabled hooks, test scaffolding (_test_*, test_*, *.bak), and Finder-copy
  # duplicates ("name 2.py") into a target.
  case "$hook_name" in
    *.bak|*.orig|*~|*.disabled|_test_*|test_*|*\ [0-9].py|*\ [0-9].sh) continue ;;
  esac
  cp "$hook" "$TARGET_HOOKS/$hook_name"
  echo "  + hook: $hook_name"
done

# -- ship the dispatch substrate the gates route to --------------------------
# The Tier-3 gate hooks (executor-enforce, delegation-gate, verify-gate, ...)
# route every write through tools/dispatch.py -> the arsenal -> the evolution
# ledger. Shipping the hooks WITHOUT that substrate is the self-brick: the gates
# fire but have nothing to route to. Ship the minimum WORKING dispatch path.
echo "  - dispatch substrate"
ensure_dir "$TARGET/tools"
cp "$SA_ROOT/tools/dispatch.py" "$TARGET/tools/dispatch.py"
echo "    OK tools/dispatch.py"
copy_pruned "$SA_ROOT/star-alliance-arsenal" "$TARGET/star-alliance-arsenal"
echo "    OK star-alliance-arsenal/ (models.json + runners, pruned)"
copy_pruned "$SA_ROOT/evolution" "$TARGET/evolution"
echo "    OK evolution/ (engine + ledger organs, pruned)"

# Pre-seed the evolution kill-switch so a fresh Tier-3 target cannot lock its
# main session with no unlock path. The dispatch substrate now ships (above),
# but the gates also need a reachable Hermes worker + doer key. Until the
# Hermes bootstrap preflight passes, evolution/DISARMED keeps the gates off.
# Mirror the printf style used to seed DEPLOY_LEDGER.
ensure_dir "$TARGET/evolution"
if [[ ! -f "$TARGET/evolution/DISARMED" ]]; then
  printf '%s\n' \
    '# DISARMED — evolution engine gates are OFF on this target.' \
    'The dispatch substrate (dispatch.py + arsenal + evolution) now ships with Tier-3, but the gates also need a reachable Hermes worker and the doer key. Until the Hermes preflight passes, the gates stay OFF so the main session cannot be locked with no unlock path.' \
    'Remove this file ONLY once the Hermes preflight passes (hermes reachable + profiles published + doer key present) - the installer prints the exact command.' \
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

# ── ship the doctrine the gates enforce ──────────────────────────────────────
# The Tier-3 hooks encode doctrine BY REFERENCE (banner-or-block, routing-or-block);
# the rulebook they enforce must actually travel. Copy it merge-safe so a target's
# own CLAUDE.md/AGENTS.md is never clobbered — only our managed block is updated.
SA_CLAUDE_MD="$SA_ROOT/CLAUDE.md"
SA_AGENTS_MD="$SA_ROOT/AGENTS.md"

if [[ -f "$SA_CLAUDE_MD" ]]; then
  write_managed_block "$TARGET/CLAUDE.md" "STAR-ALLIANCE DOCTRINE" "$SA_CLAUDE_MD"
  echo "  ✓ doctrine → $TARGET/CLAUDE.md (managed block)"
else
  echo "  ⚠  $SA_CLAUDE_MD not found — copy guild doctrine into $TARGET/CLAUDE.md manually"
fi

if [[ -f "$SA_AGENTS_MD" ]]; then
  if [[ -f "$TARGET/AGENTS.md" ]]; then
    write_managed_block "$TARGET/AGENTS.md" "STAR-ALLIANCE AGENTS" "$SA_AGENTS_MD"
    echo "  ✓ agents doctrine → $TARGET/AGENTS.md (managed block)"
  else
    cp "$SA_AGENTS_MD" "$TARGET/AGENTS.md"
    echo "  ✓ agents doctrine → $TARGET/AGENTS.md (copied whole)"
  fi
else
  echo "  ⚠  $SA_AGENTS_MD not found — copy AGENTS.md into $TARGET manually"
fi

bootstrap_hermes

echo ""
echo "✅ Tier 3 complete."
