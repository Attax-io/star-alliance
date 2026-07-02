---
type: synthesis
campaign: audit-campaigns/2026-07-02_skills-frontmatter
section: 99
title: Skills Frontmatter Audit — Synthesis
---

# Skills Frontmatter Audit — Synthesis

## TL;DR

| Metric | Value |
|---|---|
| Skills audited | 126 |
| Skills clean | 19 |
| Skills with drift | 107 |
| Total drift findings | 120 |
| High severity | 4 |
| Doc ghosts | 23 |
| Wikilink rot | 60 |
| Dead/orphan triggers | 55 |
| Hooks surveyed | 45 |

**Verdict: REGRESSION-LIKELY.** The 500-char description cutoff is the single highest-leverage fix — one decision affects 107 skills.

## Critical findings

1. **Description bloat is systemic (med, universal).** 107/126 skills exceed 500 chars. Decision needed: raise loader limit OR trim descriptions. Pick one path.

2. **4 skills break `yaml.safe_load` (high).** Unescaped `:` in `description:` field. Quotes fix them.

3. **Trigger-phrase coverage is intentionally sparse (informational).** 55/62 declared phrases don't fire a hook. Natural-language routing, not dead code. Document the convention.

4. **Wikilink rot is over-counted by ~30 (informational).** `obsidian-markdown` (21) and `vault-log-writer` (10) are syntax-example false positives. Need a classifier, not more rot.

5. **Doc ghosts are concentrated in 2 skills (med).** `obsidian-markdown` (13) has a relative-path bug. `supabase` (6) has placeholder deep-links.

## Real bugs

- **B1** — 4 YAML-parse-break skills. Fix by quoting `description:` field. Trivial.
- **B2** — `obsidian-markdown` cites `skills/obsidian-markdown/references/...` but files are at `references/...`. Relative-path bug.

## Doc ghosts

23 — see `02-references-rot.md`. Top 2 sources: `obsidian-markdown` (13), `supabase` (6).

## Doc orphans

None — every file under `star-alliance-skills/` is reachable. (No `_orphan.md` files found outside the `_impeccable-upstream-source/` carve-out.)

## Patterns to document

- **Description truncation policy** — codify the 500-char cutoff or raise it. Currently the loader behavior is implicit.
- **Natural-language routing** — most skills are "alive" via description matching, not via hook interception. The trigger-phrase field is advisory metadata, not a dispatch contract.
- **Wikilink classifier needed** — `[[link]]` matches inside code blocks / quoted examples should be excluded from rot scans.

## Re-audit cadence

Quarterly. Next sweep: 2026-10-02.

## Open items

- **OI-1** — Decide description-length policy (loader limit vs trim). Owner: Quartermaster.
- **OI-2** — Quote the 4 unquoted descriptions. Trivial; safe for direct edit.
- **OI-3** — Add wikilink-classifier to the audit script (skip code blocks).
- **OI-4** — Fix `obsidian-markdown` relative-path bug in the skill's reference links.
- **OI-5** — Document natural-language routing convention in `star-alliance-language`.

## Appendix — what this run teaches the AUDIT-mode workflow

- **W0 prescan** is fast and worth keeping.
- **W1 recon via streaming parse** is the right primitive — yaml + regex fallback handled every edge case.
- **W2 classify** needs a "syntax example" classifier for wikilinks; otherwise rot is over-counted.
- **W3 synthesize** produces the same shape every run: TL;DR + critical findings + bugs + ghosts + patterns + open items + cadence.
- **W4 close** = plan + 4 numbered findings + synthesis + vault-log. Standard recipe confirmed.

This shape becomes the recipe for the future AUDIT branch of `standard-mission` workflow.
