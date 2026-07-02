# Proposal: Mode-aware Standard Mission (closes the AUDIT-mode gap)

**Status:** Tier-B · pending human GO
**Author:** the-butler (auto-generated from evolution engine + first real AUDIT-mode campaign)
**Date:** 2026-07-02
**Evidence:** `audit-campaigns/2026-07-02_skills-frontmatter/` (126 skills audited, 7 deliverables + vault-log)
**Closes signal:** phantom-workflow `Conquering Campaign (AUDIT mode)` declared 3× but not registered.

## Why

The evolution engine flagged a recurring phantom workflow: every time the guild reaches for
the **Conquering Campaign in AUDIT mode**, it gets declared as an unregistered workflow.
AUDIT-mode is a real, distinct shape from BUILD-mode (read-only — no Designer/Developer
write phases), but the star map doesn't currently let the Strategist say "run it as AUDIT
vs BUILD" — so the same `standard-mission` workflow is invoked under both names.

The fix is **mode-aware standard-mission**: keep the current build-mode intact, add an
audit-mode branch that trims the pipeline to read-only recon + synthesis + vault-log.
No new top-level workflow is needed — the gap is a parameter, not a missing lane.

## Diff sketch

### `workflows.json` — `standard-mission` entry

```diff
   {
     "id": "standard-mission",
-    "version": "1.0.0",
+    "version": "1.1.0",
     "name": "Standard Mission",
     "icon": "🛰️",
     "accent": "cyan",
     "category": "Build & Fix",
     "class": "mutating",
+    "modes": ["build", "audit"],
     "tagline": "The full guild pipeline for serious, multi-step missions.",
-    "when": "Use this when the work is large, multi-disciplinary, or needs several specialists coordinated in waves — the guild's conquering-campaign, planned and driven to completion.",
+    "when": "Use this when the work is large, multi-disciplinary, or needs several specialists coordinated in waves — the guild's conquering-campaign, planned and driven to completion. Pass mode=audit for read-only doc-vs-reality reconciliation (replaces the 'Conquering Campaign (AUDIT mode)' phantom workflow).",
     "steps": [
       { /* Place the Order — unchanged */ },
       { /* approval gate — unchanged */ },
-      { /* Strategist forms the campaign plan — template: campaign */ },
-      { /* Designer shapes the visuals */ },
-      { /* certify gate */ },
-      { /* Developer implements */ },
-      { /* Quartermaster clean up and verify */ },
-      { /* Quartermaster confirm guild conformance */ },
+      { /* Strategist forms the plan — args.template: { build: 'campaign', audit: 'audit' }[mode] */ },
+      { /* mode=build: Designer shapes the visuals */
+        "skip_when": "mode=audit" },
+      { /* certify gate — runs only in build mode */ },
+      { /* mode=build: Developer implements */
+        "skip_when": "mode=audit" },
+      { /* mode=build: Quartermaster clean up and verify */
+        "skip_when": "mode=audit" },
+      { /* mode=build: Quartermaster confirm guild conformance */
+        "skip_when": "mode=audit" },
+      { /* mode=audit: parallel read-only recon wave (Architect + Interpreter + Herald, findings only) */ },
+      { /* mode=audit: synthesis step (Quartermaster writes 99-synthesis.md + vault-log) */ },
       { /* report gate — unchanged */ }
     ],
     "trigger_phrases": [
       "standard mission",
       "full guild pipeline",
       "conquering campaign",
       "multi-disciplinary mission",
       "big coordinated campaign",
       "wave of specialists",
+      "conquering campaign (audit mode)",
+      "audit this",
+      "reconcile docs with code"
     ]
   }
```

### `guild/plan.py`

Add an `audit` template that mirrors the campaign template but with `mode: AUDIT` and
read-only waves. The first real audit (skills-frontmatter) is the reference shape.

### Ledger event

A `verdict: pass` event is already filed under `surface=workflows` referencing this
proposal as evidence.

## Safety envelope

- **Additive only.** The build-mode path is untouched. `mode=build` (the default) behaves
  identically to v1.0.0.
- **No auto-apply.** This proposal is human-gated per Tier-B doctrine. Even if a future
  nightly reflector proposes the same change, it cannot land without your GO.
- **Reversible.** A one-commit revert restores v1.0.0.
- **No new surface.** `standard-mission` is already Tier-A's load-bearing entry; this is
  a parameter, not a new lane.

## What this DOES NOT do

- Does not invent a recipe. The recipe is mined from the real audit just completed —
  `audit-campaigns/2026-07-02_skills-frontmatter/`.
- Does not touch any other workflow entry.
- Does not change hook behavior.

## Verification after apply

1. Re-run `evolution/engine.py` — phantom-workflow signal should drop to 0.
2. Trigger `conquering campaign (audit mode)` — should now resolve to
   `standard-mission[mode=audit]` instead of declaring as unknown.
3. Run one more AUDIT-mode campaign end-to-end as smoke test.

## Estimated reviewer effort

~15 min: read the diff, skim the audit deliverables, approve or reject.

## Open question for the reviewer

Should `mode` be a hard enum (`build` | `audit`) or extensible (e.g. `extension` later)?
Default in this proposal: hard enum. Deferring `extension` keeps the star map clean.
