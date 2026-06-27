---
type: Document
timestamp: 2026-06-27T10:27:03Z
---

# Skill Maintenance

Deploy/sync procedures + self-health checks for the conquering-campaign skill. (Extracted from SKILL.md at v3.7.1 — the lean-core-v2 move continued; SKILL.md keeps stub headings that point here.)

---

## Deploy & sync (added v3.0.0 — #84)

This skill exists in multiple locations that drift. After ANY edit to SKILL.md or references/, sync every copy and verify:

| Copy | Path | Role |
|---|---|---|
| Project-local (canonical) | `<project>/.claude/skills/conquering-campaign/` | what runs in this project's Claude Code |
| Slash-command pointer | `<project>/.claude/commands/conquering-campaign.md` | the `/conquering-campaign` entry point — must point at `.claude/skills/conquering-campaign/SKILL.md` (NOT a stale `_skill-updates/` path) |
| Source repo | `~/Documents/Claude/Projects/star-alliance/conquering-campaign/` | distribution source (git: `Attax-io/star-alliance`, branch `main`) |
| Cowork customize page | (web) | Cowork sessions — paste the full text |

Sync step: `diff -rq <canonical>/SKILL.md+references <source>` — must be empty (source keeps its own `evals/`). Confirm the slash-command pointer path resolves. When pasting into Cowork, paste the WHOLE file (a partial `cp` once produced duplicate frontmatter). **The canonical copy is project-local; propagate FROM it.**

**The G0 hook is project-local, NOT part of the portable skill (v3.8.0).** `.claude/scripts/g0-campaign-guard.sh` + its `PreToolUse` registration in `.claude/settings.json` are harness enforcement for THIS project — they do NOT travel with the skill copies (a Cowork/headless run has no settings.json hook; G0 falls back to the in-skill prose + description under-match there). So: don't expect `diff -rq` to cover the hook, and when standing the skill up in a new project that wants mechanical G0, copy the hook script + add the settings.json `PreToolUse` block separately. The skill functions correctly without it (the hook is a backstop, not a dependency — #103).

---

## Skill self-health (run at every reflection pass — #84)

```bash
SK=.claude/skills/conquering-campaign
# every referenced file exists
grep -oE "references/[a-z0-9-]+\.md" $SK/SKILL.md | sort -u | while read f; do test -f "$SK/$f" || echo "MISSING $f"; done   # [a-z0-9-] so fe-i18n-playbook.md (digit) isn't silently skipped
# every #N has a catalog row · every §X and [[link]] resolves (manual scan)
# v3.8.0 sprawl + COHERENCE metric (G0 health) — run from project root; sums all *-campaigns roots, PRUNES node_modules/.next/.git/worktrees (monorepo has nested doc roots + #95 worktree copies → never `head -1`, never unpruned — an unpruned find triple-counts via the worktrees).
# v3.8.0 added INFLATED/LOOSE/BADSTATUS: presence-of-scope was a weak signal — agents now write `scope: full` on 1-file folders to pass the declaration gate (#103/M2), so measure COHERENCE, not just presence.
T=0; THIN=0; NOSCOPE=0; INFLATED=0; LOOSE=0; BADSTATUS=0
for R in $(find . -type d \( -name node_modules -o -name .next -o -name .git -o -name worktrees \) -prune -o -type d -name '*-campaigns' -print 2>/dev/null); do
  LOOSE=$((LOOSE + $(find "$R" -maxdepth 1 -type f -name '*.md' ! -name README.md 2>/dev/null | wc -l)))   # M4: an audit/plan as a loose file, not a folder. `find` not a glob — a `for f in "$R"/*.md` ABORTS under zsh on no-match (the #32/#102 artifact)
  for d in "$R"/*/; do [ -d "$d" ] || continue; T=$((T+1)); n=$(ls "$d" | wc -l)
    [ "$n" -le 3 ] && THIN=$((THIN+1)); P="$d/00-campaign-plan.md"; [ -f "$P" ] || continue
    grep -q "^scope:" "$P" || NOSCOPE=$((NOSCOPE+1))
    sc=$(grep "^scope:" "$P" | head -1 | sed 's/scope: *//;s/["[:space:]]*$//')
    # M2 scope-inflation: medium/full tier on a ≤2-file folder that isn't content-authoring
    { [ "$n" -le 2 ] && { [ "$sc" = "full" ] || [ "$sc" = "medium" ]; } && ! grep -q "^generation_strategy:.*content" "$P"; } && INFLATED=$((INFLATED+1))
    # M4 off-enum status (enum = planning|in-progress|completed|superseded)
    grep -qE "^status: (planning|in-progress|completed|superseded)" "$P" || BADSTATUS=$((BADSTATUS+1))
  done
done
echo "folders=$T thin(≤3)=$THIN missing-scope=$NOSCOPE scope-INFLATED=$INFLATED loose-files=$LOOSE off-enum-status=$BADSTATUS"
echo "# baseline 2026-06-04 (all roots, pruned): folders=180 thin=127 (71%) missing-scope=49 INFLATED=53 loose=1 off-enum-status=20"
echo "# G0-PROSE ALONE FAILED: 161→180 folders (+19) in the 2 days after v3.7.0, thin% flat at 71%, and scope-INFLATED=53 (the dominant pathology the old presence-only metric was blind to — agents wrote a higher tier to pass the declaration gate). The v3.8.0 PreToolUse hook is the first mechanical brake ⇒ folder-growth-rate + thin% + INFLATED should fall from 2026-06-04 forward. (An earlier 156 read was a lex-submodule-cwd undercount — run from PROJECT ROOT, an #32 trap.)"
wc -l $SK/SKILL.md   # track core size — investigate if it climbs back toward ~700
```

A dangling `references/<file>` / `#N` / `§X`, or a core ballooning past ~700 lines, is a self-health failure — fix in the same pass. A rising thin-folder% or no-scope-declaration% in the sprawl metric means G0 isn't firing (over-invocation regressing — #101/#102); the cure is enforcement at G0, not deleting folders after the fact.
