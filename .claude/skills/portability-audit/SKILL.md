---
name: portability-audit
description: "Audit how portable a Claude Code project is — maps every layer (skills, members, hooks, env vars, hardcoded paths, arsenal tools), assigns tier gaps, and produces a ranked install plan. Run before deploying Star Alliance members to a new project, or when a project feels 'stuck here'. Triggers: 'audit portability', 'can I use this in another project', 'how do I deploy this elsewhere', 'portability audit', 'what needs to move', 'install plan for project X', '/portability-audit'."
metadata:
  version: 1.0.0
type: Skill

---
# portability-audit — map what's portable, what's broken, what's missing

Answers: **can this project's AI setup move to another project, and what's the gap?**

Mined from the 2026-06-27 Star Alliance portability audit. Reusable on any Claude Code project —
not just Star Alliance.

## The 6 portability layers

Audit each layer in order. Each one can independently block a deployment.

| # | Layer | What to check | Common break |
|---|---|---|---|
| 1 | **Skills** | Are skills in `~/.claude/skills` (global) or `.claude/skills` (project)? Are versions current vs source repo? | Stale version silently runs old code |
| 2 | **Members** | Are `.md` files in `.claude/agents/`? Do they reference any path that only exists here? | Member present but arsenal calls fail |
| 3 | **Arsenal tools** | Does any script reference a relative path that only resolves from one directory? | Silent path failure in target project |
| 4 | **Env vars** | Is `STAR_ALLIANCE_ROOT` (or equivalent) set in `.claude/settings.json`? | Arsenal calls resolve to nothing |
| 5 | **Hooks** | Are `.claude/hooks/*.py` present? Are they wired in `settings.json`? | Gate hooks silently absent; no routing enforcement |
| 6 | **Workflows** | Is `workflows.json` present? Does it have the workflows the members reference? | Workflow-gate blocks every turn |

## Procedure

### Step 1 — Identify what's installed

```sh
ls .claude/agents/
ls .claude/skills/
ls ~/.claude/skills/
ls .claude/hooks/
cat .claude/settings.json
ls workflows.json 2>/dev/null && echo "present" || echo "MISSING"
```

### Step 2 — Check arsenal path resolution

```sh
grep -n "python3\|STAR_ALLIANCE_ROOT\|arsenal" .claude/agents/*.md
```

Fails = any bare `python3 minimax.py` or `python3 star-alliance-arsenal/` without `$STAR_ALLIANCE_ROOT`.

### Step 3 — Check skill versions

```sh
for d in .claude/skills/*/; do
  skill=$(basename "$d")
  local_ver=$(grep 'version:' "$d/SKILL.md" | head -1 | awk '{print $2}')
  repo_ver=$(grep 'version:' "$STAR_ALLIANCE_ROOT/star-alliance-skills/$skill/SKILL.md" 2>/dev/null | head -1 | awk '{print $2}')
  [[ "$local_ver" != "$repo_ver" ]] && echo "STALE: $skill local=$local_ver repo=$repo_ver"
done
```

### Step 4 — Assign tiers + gaps

| Finding | Tier gap | Fix |
|---|---|---|
| Skills stale or missing | Tier 1 | `install.sh <member> . --tier 1` |
| Member .md absent | Tier 2 | `install.sh <member> . --tier 2` |
| `STAR_ALLIANCE_ROOT` missing | Tier 2 | Add env block to `.claude/settings.json` |
| Arsenal paths hardcoded | Tier 2 | Replace with `$STAR_ALLIANCE_ROOT/star-alliance-arsenal/` |
| Hooks absent | Tier 3 | `install.sh <member> . --tier 3` |
| `workflows.json` missing | Tier 3 | Copy `workflows-lite.json` from arsenal |

### Step 5 — Produce the install plan

Output format:

```
PORTABILITY AUDIT — <project-name>
Date: <today>

LAYER STATUS:
  Skills      : <N current> / <N total> — <N stale>
  Members     : <present|missing>
  Arsenal     : <STAR_ALLIANCE_ROOT set|MISSING>
  Hooks       : <N hooks present|MISSING>
  Workflows   : <present|MISSING>

GAPS (ranked by impact):
  1. [CRITICAL] ...
  2. [HIGH] ...
  3. [LOW] ...

INSTALL PLAN:
  bash "$STAR_ALLIANCE_ROOT/star-alliance-arsenal/install.sh" <member> . --tier <N>
```

## Tier definitions (quick ref)

| Tier | What you get | Command |
|---|---|---|
| 1 | Skills only | `install.sh <member> <project> --tier 1` |
| 2 | + member agent + `STAR_ALLIANCE_ROOT` env | `install.sh <member> <project> --tier 2` |
| 3 | + hooks + routing gate + `workflows-lite.json` | `install.sh <member> <project> --tier 3` |

## After the audit

Run `/project-start` in the target project to verify the install resolved all gaps.

## Versioning

Bump `metadata.version` on any change — PATCH for wording, MINOR for new layer or step.
