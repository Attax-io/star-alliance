---
title: The Strategist's Merge Review — 24 Workflows
author: the-strategist
date: 2026-06-26
status: proposal (no changes applied)
scope: workflows.json (version 1, 24 entries)
---

# The Strategist's Merge Review

> Guild Master's order: *"Review all the workflows — are any worth merging? Pros and cons."*
> I read all 24 by **actor topology + purpose + skill set**, not by name. Verdict below.

## Bottom line

There are **no slam-dunk merges**. The catalogue is mostly well-factored — most
"overlaps" are deliberate *shaped paths* (the whole point of a star-map: one
discoverable lane per intent, each with its own art tile). But I found:

- **2 arguable merges** (same engine, different payload) — judgement calls, I lean *keep*.
- **1 pipeline to document, not merge** (Law Harvest → Legal Codex).
- **1 rename, not a merge** (Market Recon vs Marketing Recon — a name collision, highest-value fix here).
- **1 philosophical collapse I recommend against** (Mission-family into modes).

Net: **keep 24 as-is**, do the rename, and document the Law pipeline. Merge only if you
want a leaner roster more than you want discoverable lanes.

---

## The merge candidates, graded

### A. Architecture Build ⊕ Security Sweep — *same engine* · merge-confidence 5/10
Both run the identical chain: `strategist → architect → [certify] → developer → QM`.
Security Sweep *is* Architecture Build pointed at the DB security surface.

**Pros of merging**
- Identical actor topology — they're twins, not cousins.
- Both **Build & Fix**; one fewer near-duplicate to maintain.
- Security becomes a documented *mode* of structural work rather than a parallel path.

**Cons of merging**
- Different **posture**: Security Sweep is audit → **propose first, apply on sign-off** (read-only-first, safety-critical). Architecture Build is greenfield construction. Burying a safety posture inside a generic build is how leaks ship.
- Different **triggers** ("seal every leak" vs "design the schema") — users find them by intent.
- Specialized skill set (Supabase advisors, RLS bundles) that doesn't belong on the generic lane.

**Verdict:** **Keep separate.** This is the closest pair in the catalogue, but the safety
posture earns its own lane. If you ever do merge, make Security a named mode, never the default.

---

### B. Guild Log Sync ⊕ Hygiene Rotation — *both QM hygiene* · merge-confidence 5/10
Hygiene Rotation: `butler → [approval] → QM → QM → [report]`.
Guild Log Sync: `butler → [approval] → butler → [certify] → QM → QM → [report]`.

**Pros of merging**
- Both **Hygiene & Release**, both end in QM sweeps, both run at the same cadence (pre-release).
- Guild Log Sync could be one more *mode* in the rotation alongside the other hygiene modes.

**Cons of merging**
- Guild Log Sync is **Butler-led** (he sweeps recent sessions and backfills) with its own mid-flow **certify** gate; Hygiene Rotation is QM-only with no mid-gates. Different lead actor + different gate shape.
- Distinct deliverable: a *backfilled log* vs *clean code*. They fail differently and are run for different reasons.

**Verdict:** **Keep separate**, but they're adjacent enough to **chain** (run Guild Log Sync,
then Hygiene Rotation, then Release Train as a standard closeout sequence). Document the chain
rather than collapsing the entries.

---

### C. Law Harvest → Legal Codex — *a pipeline, not a duplication* · merge-confidence 4/10
Law Harvest explicitly calls itself *"the feed for the codex."* It's stage 1 (ingest law
PDFs → verified source-law library); Legal Codex is stage 2 (source → multilingual codex).

**Pros of merging**
- Sequential halves of one process; Harvest's output is literally Codex's input.
- Both **Legal**, both translator-heavy.

**Cons of merging**
- They're **stages with independent re-run cadence**: you re-run Codex (re-translate, re-publish) far more often than you re-harvest source PDFs. Merging forces the heavy ingest every time.
- Harvest pulls in the Architect + its own certify gate; Codex doesn't need either.

**Verdict:** **Keep separate; document the chain.** Optionally add a thin "Law → Codex"
express path for first-time end-to-end runs, but don't destroy the ability to run each stage alone.

---

### D. Market Recon vs Marketing Recon — *NOT a merge, a rename* · action 9/10
Near-identical names, **completely different work**: Market Recon = the Merchant doing
financial/trading/investment intel; Marketing Recon = the Herald auditing the public site
& brand. Same name-stem, opposite domains.

**Pros of acting** — kills the single worst discoverability hazard in the catalogue; one will
be picked by mistake eventually.
**Cons** — none worth noting; this is pure upside.

**Verdict:** **Rename, don't merge.** Suggest `Market Recon` → keep; `Marketing Recon` →
`Brand Audit` or `Site & Brand Recon`. Highest-value change on this page.

---

### E. The Mission family (Standard / Quick Fix / Design Sprint / Architecture Build) — *collapse to modes?* · merge-confidence 3/10
All four are "build something" at different depths. One could imagine a single parameterized
`Mission(depth: quick | standard | design | arch)`.

**Pros** — one entry instead of four; the depth ladder becomes explicit.
**Cons** — this **defeats the star-map**. The product value is four shaped, discoverable lanes
with distinct art and distinct entry points. Quick Fix's entire worth is *being lean and skipping
the Strategist/Designer*; folding it into a mode of the big pipeline hides exactly the thing that
makes it useful.

**Verdict:** **Keep separate.** Reject the collapse.

---

## Why the catalogue is already well-factored — the merges are *on record*
This isn't an opinion; the consolidation happened when the 24 were built. Per
`STRATEGIST-WORKFLOWS.md` §10 ("Merged-not-split"), these were *deliberately* folded
rather than given their own entry:
- schema-drift fixes → **Quick Fix / Bug Cycle**
- performance + finance-critical migration → **Architecture Build**
- i18n / hardcoded-text extraction → **Hygiene Rotation** (cleanup)
- deploys → **Release Train**
- Flutter → Next migration → **Standard Mission**

So the obvious merges are already done. What remains (Section A–E) is the residue — the
pairs that survived that pass on purpose.

## Adjacent pairs I checked and cleared (no merge)
- **Skill Forge vs Arsenal Forge** — same "parallel forge of a guild asset" shape, but different asset: a *skill* (forge/sync) vs a *weapon* (forge/reskin + thinker/doer wiring). Same reasoning as Design Sprint/Art Forge. Keep.
- **Comms Triage vs Relationship Intel** — both touch email, but one produces *action items*, the other *CRM intelligence*. Different actors emphasis, different output. Keep.
- **Design Sprint vs Art Forge** — same topology, different domain (product UI vs Fallen-Sword game art). Keep.
- **Conformity Sweep** — a *proof of self-agreement*, not a fix. Stands alone. Keep.
- **Quick Fix vs Bug Cycle** — Quick Fix is a known small change; Bug Cycle is root-cause hunt + certify. Keep.

## Project-specific con that applies to *every* merge here
Each workflow owns a **workflow-art tile** and a star-map node (`workflow-art/`,
`gen-workflow-art.cjs`, the dashboard). Merging shrinks the visual roster and orphans art.
In a normal repo, fewer-entries is a clean win; here the catalogue *is* the product surface.
That tilts the default toward **keep + document the chains** rather than physically merge.

## Recommended actions, in order
1. **Rename Marketing Recon → Brand Audit** to remove the Market Recon collision. ✅ **DONE 2026-06-26** — display name changed in `workflows.json` (id `marketing-audit` kept, so the art tile is untouched), Market Recon's cross-ref updated, guild-data rebuilt.
2. **Document two chains** in the star-map `when` copy: Law Harvest → Legal Codex; and Guild Log Sync → Hygiene Rotation → Release Train. ✅ **DONE 2026-06-26** — chain notes appended to the relevant `when` fields, guild-data rebuilt.
3. **Leave all 24 entries intact.** Revisit Architecture Build ↔ Security Sweep only if the roster is later judged too large. *(no action — standing recommendation)*
