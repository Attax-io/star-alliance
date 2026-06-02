# Skill Maintenance

Deploy/sync procedures + self-health checks for the conquering-campaign skill. (Extracted from SKILL.md at v3.7.1 — the lean-core-v2 move continued; SKILL.md keeps stub headings that point here.)

---

## Deploy & sync (added v3.0.0 — #84)

This skill exists in multiple locations that drift. After ANY edit to SKILL.md or references/, sync every copy and verify:

| Copy | Path | Role |
|---|---|---|
| Project-local (canonical) | `<project>/.claude/skills/conquering-campaign/` | what runs in this project's Claude Code |
| Slash-command pointer | `<project>/.claude/commands/conquering-campaign.md` | the `/conquering-campaign` entry point — must point at `.claude/skills/conquering-campaign/SKILL.md` (NOT a stale `_skill-updates/` path) |
| Source repo | `~/Documents/Claude/Projects/claude-skills/conquering-campaign/` | distribution source (git: `Attax-io/claude-skills`, branch `main`) |
| Cowork customize page | (web) | Cowork sessions — paste the full text |

Sync step: `diff -rq <canonical>/SKILL.md+references <source>` — must be empty (source keeps its own `evals/`). Confirm the slash-command pointer path resolves. When pasting into Cowork, paste the WHOLE file (a partial `cp` once produced duplicate frontmatter). **The canonical copy is project-local; propagate FROM it.**

---

## Skill self-health (run at every reflection pass — #84)

```bash
SK=.claude/skills/conquering-campaign
# every referenced file exists
grep -oE "references/[a-z0-9-]+\.md" $SK/SKILL.md | sort -u | while read f; do test -f "$SK/$f" || echo "MISSING $f"; done   # [a-z0-9-] so fe-i18n-playbook.md (digit) isn't silently skipped
# every #N has a catalog row · every §X and [[link]] resolves (manual scan)
# v3.7.0 over-invocation sprawl metric (G0 health) — run from project root; sums all *-campaigns roots, PRUNES node_modules/.next/.git/worktrees (monorepo has nested doc roots + #95 worktree copies → never `head -1`, never unpruned — an unpruned find triple-counts via the worktrees)
T=0; THIN=0; NOSCOPE=0
for R in $(find . -type d \( -name node_modules -o -name .next -o -name .git -o -name worktrees \) -prune -o -type d -name '*-campaigns' -print 2>/dev/null); do for d in "$R"/*/; do [ -d "$d" ] || continue; T=$((T+1)); [ "$(ls "$d" | wc -l)" -le 3 ] && THIN=$((THIN+1)); P="$d/00-campaign-plan.md"; { [ -f "$P" ] && ! grep -q "^scope:" "$P"; } && NOSCOPE=$((NOSCOPE+1)); done; done
echo "campaign-folders=$T thin(≤3 files)=$THIN plans-missing-scope=$NOSCOPE  # baseline 2026-06-02 (pruned, all roots): 161 / 115 (71%) / 49-of-153 (so 68% DO declare scope) — G0 working ⇒ thin% + missing-scope% trend DOWN"
wc -l $SK/SKILL.md   # track core size — investigate if it climbs back toward ~700
```

A dangling `references/<file>` / `#N` / `§X`, or a core ballooning past ~700 lines, is a self-health failure — fix in the same pass. A rising thin-folder% or no-scope-declaration% in the sprawl metric means G0 isn't firing (over-invocation regressing — #101/#102); the cure is enforcement at G0, not deleting folders after the fact.
