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
type: Document

---
# Audit Campaign — Skills Frontmatter Drift Recon

## TL;DR

Reconciled **126 skill SKILL.md files** against (a) the filesystem (refs + wikilinks + anchors), (b) the hooks under `.claude/hooks/`, (c) `workflows.json` `trigger_phrases`, and (d) `evolution/ledger.jsonl` skill-fire history.

**120 drift findings** (4 high · 115 med · 1 low) · **23 doc ghosts** · **60 wikilink rot** · **62 declared triggers (7 active / 55 dead-or-orphan)** · **45 hooks surveyed**.

One systemic class of finding dominates: **description fields averaging ~807 chars** — well past the 500-char loader cutoff. Single highest-leverage fix.

## Waves

### W0 — Prescan
Listed `star-alliance-skills/` (126 entries = 126 skill dirs + `index.md` + `_impeccable-upstream-source/` excluded).

### W1 — Recon (parallel)
Streamed all SKILL.md frontmatter via YAML + regex fallback (4 YAML-parse-breaks recovered via fallback). Built per-skill index.

### W2 — Classify (parallel)
- Frontmatter drift: parsed + severity-tagged (high / med / low).
- Doc ghosts: every markdown link target checked against filesystem.
- Wikilink rot: every `[[link]]` resolved. Anchor rot: 0.
- Trigger phrases: each declared phrase grepped against hooks + workflows.json + ledger.

### W3 — Synthesize (parallel)
Top-5 critical findings cross-cut (see `99-synthesis.md`). Classified `obsidian-markdown` and `vault-log-writer` wikilink findings as **syntax-example false positives**, not real rot.

### W4 — Close
Wrote this plan + 4 numbered findings + synthesis + vault-log entry.

## Open items

See `99-synthesis.md` §Open Items.
