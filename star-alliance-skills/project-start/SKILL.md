---
name: project-start
description: "Start-of-session health check for projects that have Star Alliance members deployed. Verifies STAR_ALLIANCE_ROOT resolves, checks for stale skills (version diff vs repo), and reports any updates available. Run at the top of any session in a project using SA members. Triggers: 'start session', 'session start', '/project-start', 'check my skills', 'are my skills up to date'."
metadata:
  version: 1.0.0
type: Skill

---
# project-start — session health check for Star Alliance-equipped projects

Run at the top of any working session in a project that has Star Alliance members deployed.
Takes ~5 seconds. Never auto-installs — only reports.

## What it checks

1. **`STAR_ALLIANCE_ROOT` resolves** — the env var must point to a readable directory. If missing or broken, arsenal tools won't work and all weapon calls will fail silently.
2. **Skill versions** — compares `metadata.version` in each `.claude/skills/<skill>/SKILL.md` against the repo copy at `$STAR_ALLIANCE_ROOT/star-alliance-skills/<skill>/SKILL.md`. Reports stale skills with a one-line fix command.
3. **Member file present** — verifies `.claude/agents/<member>.md` exists for each deployed member.

## Procedure

```
Step 1 — Check STAR_ALLIANCE_ROOT
  bash: echo "$STAR_ALLIANCE_ROOT"
  If empty or path not found → STOP and warn. Fix: add env.STAR_ALLIANCE_ROOT to .claude/settings.json.

Step 2 — Diff skill versions
  python3 "$STAR_ALLIANCE_ROOT/star-alliance-arsenal/install.sh" --check-only <project-path>
  (or manual: compare metadata.version in .claude/skills/*/SKILL.md vs repo)

Step 3 — Report
  If all current  → "✅ Skills up to date. Ready."
  If stale skills  → list each with repo version and fix command:
    bash "$STAR_ALLIANCE_ROOT/star-alliance-arsenal/install.sh" <member> . --tier 1
```

## Fix commands (copy-paste)

**Stale skills (Tier 1 update):**
```sh
bash "$STAR_ALLIANCE_ROOT/star-alliance-arsenal/install.sh" <member-name> . --tier 1
```

**STAR_ALLIANCE_ROOT missing — add to .claude/settings.json:**
```json
{
  "env": {
    "STAR_ALLIANCE_ROOT": "/Users/attaselim/Documents/Claude/Projects/star-alliance"
  }
}
```

**Member file missing — reinstall at Tier 2:**
```sh
bash "$STAR_ALLIANCE_ROOT/star-alliance-arsenal/install.sh" <member-name> . --tier 2
```

## When to skip

- Working inside the star-alliance repo itself (SA is the source of truth there)
- Quick one-liner sessions where staleness doesn't matter
- You just ran an install in this session
