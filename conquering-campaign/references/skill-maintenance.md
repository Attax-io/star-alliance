# Skill Maintenance

Deploy sync procedures and self-health checks for the conquering-campaign skill.

---

## Deploy & sync (added v3.0.0 — #84)

This skill exists in multiple locations that drift. After ANY edit to SKILL.md or references/, sync every copy and verify:

| Copy | Path | Role |
|---|---|---|
| Project-local (canonical) | `<project>/.claude/skills/conquering-campaign/` | what runs in this project's Claude Code |
| Slash-command pointer | `<project>/.claude/commands/conquering-campaign.md` | the `/conquering-campaign` entry point — must point at `.claude/skills/conquering-campaign/SKILL.md` (NOT a stale `_skill-updates/` path) |
| Source repo | `~/Documents/Claude/Projects/claude-skills/conquering-campaign/` | distribution source (git) |
| Cowork customize page | (web) | Cowork sessions — paste the full text |

Sync step: `diff -rq <canonical>/SKILL.md+references <source>` — must be empty (source keeps its own `evals/`). Confirm the slash-command pointer path resolves. When pasting into Cowork, paste the WHOLE file (a partial `cp` once produced duplicate frontmatter). The canonical copy is project-local; propagate FROM it.

---

## Skill self-health (run at every reflection pass — #84)

```bash
SK=.claude/skills/conquering-campaign
# every referenced file exists
grep -oE "references/[a-z0-9-]+\.md" $SK/SKILL.md | sort -u | while read f; do test -f "$SK/$f" || echo "MISSING $f"; done
# every #N has a catalog row
# every §X and [[link]] resolves (manual scan)
wc -l $SK/SKILL.md   # track core size — investigate if it climbs back toward 700
```

A dangling `references/<file>` / `#N` / `§X`, or a core ballooning past ~700 lines, is a self-health failure — fix in the same pass.
