---
mode: AUDIT
status: completed
date: 2026-07-02
topic: skills-frontmatter
scope: 126 skills under star-alliance-skills/
approval_cadence: hybrid
current_phase: w4-synthesis
phases_completed: [w0-prescan, w1-recon, w2-classify, w3-synthesize, w4-close]
phases_remaining: []
predecessor: null
---

# Audit Campaign — Skills Frontmatter Drift Recon

## TL;DR

Reconciled **126 skill SKILL.md files** against (a) the filesystem (refs + wikilinks + anchors), (b) the hooks under `.claude/hooks/`, (c) `workflows.json` `trigger_phrases`, and (d) `evolution/ledger.jsonl` skill-fire history.

**120 drift findings** · **23 doc ghosts** · **60 wikilink rot** · **62 declared triggers (7 active / 0 dead-or-orphan)** · **45 hooks surveyed**.

One systemic class of finding dominates: **description fields averaging 807 chars** — well past the 500-char loader cutoff. This is a single fix (raise the limit OR trim the descriptions), not 107 individual bugs.

## Waves

### W0 — Prescan
Listed `star-alliance-skills/` (128 entries: 126 skill dirs + `index.md` + `_impeccable-upstream-source/` excluded). Confirmed 142 `SKILL.md` files (some skills ship nested variants).

### W1 — Recon (parallel)
Streamed all SKILL.md frontmatter via YAML + regex fallback. Built per-skill index: `{name, dir, description, version, type, refs[], triggers[], drift[]}`.

### W2 — Classify (parallel)
- Frontmatter drift: parsed + severity-tagged (high / med / low).
- Doc ghosts: every markdown link target checked against filesystem.
- Wikilink rot: every `[[link]]` resolved; anchor check skipped (none found in this corpus).
- Trigger phrases: each declared phrase grepped against hooks + workflows.json + ledger.

### W3 — Synthesize (parallel)
Top-5 critical findings cross-cut (see `99-synthesis.md`). Classified `obsidian-markdown` and `vault-log-writer` wikilink findings as **syntax-example false positives**, not real rot.

### W4 — Close
Wrote this plan + 4 numbered findings + synthesis + vault-log entry.

## Surfaced patterns

1. **Systemic description bloat** (107/126 skills over 500 chars).
2. **YAML-quoting fragility** (4 skills break `safe_load` on unescaped colons).
3. **Natural-language routing is real** — most trigger phrases have never fired a hook because routing happens via description matching, not phrase interception. This is intentional, not dead code.
4. **Wikilink-rot is over-counted by ~30** (syntax examples in `obsidian-markdown` / `vault-log-writer`). A classifier is needed, not more rot.

## Open items

See `99-synthesis.md` §Open Items.

## Reference files

- `_raw.json` — parsed findings (source of truth)
- `_skill_summary.json` — per-skill rollup
- `vault-logs/2026-07-02_skills-frontmatter-audit.md`
