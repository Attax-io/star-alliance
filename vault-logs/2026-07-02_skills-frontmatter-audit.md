# 2026-07-02 — Skills Frontmatter Audit (AUDIT-mode)

**Mode:** AUDIT (read-only)
**Scope:** 126 skills under `star-alliance-skills/`
**Result:** 120 drift findings, 23 doc ghosts, 60 wikilink rot, 55/62 declared trigger phrases dead/orphan.

## Files

- `audit-campaigns/2026-07-02_skills-frontmatter/00-campaign-plan.md` — the audit plan (mode, scope, waves).
- `audit-campaigns/2026-07-02_skills-frontmatter/01-frontmatter-drift.md` — 120 drift findings, severity-tagged.
- `audit-campaigns/2026-07-02_skills-frontmatter/02-references-rot.md` — 23 doc ghosts + 60 wikilink rot.
- `audit-campaigns/2026-07-02_skills-frontmatter/03-trigger-coverage.md` — 62 declared trigger phrases with verdicts.
- `audit-campaigns/2026-07-02_skills-frontmatter/04-hook-coverage.md` — 45 hooks surveyed.
- `audit-campaigns/2026-07-02_skills-frontmatter/99-synthesis.md` — TL;DR + critical findings + bugs + open items + cadence.
- `audit-campaigns/2026-07-02_skills-frontmatter/_raw.json` — source-of-truth parsed findings.
- `audit-campaigns/2026-07-02_skills-frontmatter/_skill_summary.json` — per-skill rollup.

## Headline

The 500-char description cutoff affects 107/126 skills — single highest-leverage fix. 4 skills break `yaml.safe_load` on unescaped colons (high severity, trivial fix). Most "dead" trigger phrases reflect intentional natural-language routing, not dead code.

## Status

Audit complete. Open items filed. No skill was modified (AUDIT-mode is read-only).
