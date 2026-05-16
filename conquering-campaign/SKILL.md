---
name: conquering-campaign
description: "Multi-wave deep audit campaign for large codebases — typically used to reconcile out-of-date documentation with reality, audit a project before a major release, or systematically map an unfamiliar large system. Use this skill whenever the user mentions a deep audit, doc-sync, reconcile docs with code, campaign, deep dive on the whole app, or expresses any of these symptoms — docs citing contradictory counts of the same thing, headline numbers that feel stale, a graphify/dependency-graph run revealing structural drift, or the project being too big to walk in one pass. Also use it when the user wants to coordinate many parallel subagents on a multi-task investigation with a synthesis at the end. The skill structures the work into 4 waves (foundation reality, deep structural, domain depth, synthesis and doc rewrite), assigns Claude models per task complexity, makes every subagent emit a numbered findings file, then drives a master synthesis and staged doc rewrites with a clear promotion gate."
---

# Conquering Campaign

A campaign turns a one-shot "audit this big thing" prompt into a structured, parallelizable, evidence-trail-producing workflow that ends with concrete updates to the source-of-truth docs (or an equivalent staged deliverable).

The core idea: you cannot reliably reason about a 700-file, 100-table system in one pass. Instead, you split the work into **four waves** of independent subagent tasks, each writing to a numbered findings file, then synthesise everything into a master changelog and rewrite the affected docs against staged paths before promotion.

## When this skill triggers

- "Audit my whole app", "deep dive on the codebase", "reconcile our docs with the code"
- After a graphify / dependency-graph run shows weakly-connected nodes, god-objects, or doc-vs-code drift
- Pre-release readiness check on a system the user cannot mentally hold in one piece
- Symptoms: same doc cites 4 different counts of the same thing; "headline X" claims contradict reality; ghost references to functions that don't exist; "we have 32 rules" but the rule list has 39 items
- User wants to coordinate many parallel subagents and end with a single synthesis + concrete doc updates

If the user only wants a quick check on one file or one rule, this skill is overkill — say so and offer a lighter-weight pass instead.

## What "good" looks like at the end

By the end of a campaign:

1. There's a `docs/audit-campaigns/<YYYY-MM-DD>_<topic>/` directory containing 8–12 numbered findings files plus `99-synthesis.md`.
2. Every doc that needed to change has been **rewritten to a staged path** (`docs/staged/<doc>.md`), reviewed, then promoted.
3. Anything that couldn't be verified at audit time is captured as `<!-- CHECKPOINT: CHK-<id> -->` markers with a CHECKPOINTS.md registry of queries to run when the blocker clears.
4. A vault-log (or equivalent project changelog) entry exists per the project's P8-style rule.
5. The user has a clear "what's left" list — usually a code-cleanup PR with concrete file/line targets, separate from the doc work.

The campaign is **not** a code-fix campaign. It produces evidence and doc updates. Code fixes are a follow-up task with the campaign's findings as their input.

## Step 1 — Capture the target and scope

Before launching anything, get explicit alignment on:

- **What artefact / system?** A monorepo? One app? A subfolder? The current dir is fine if the user confirms.
- **What's the trigger?** Drift from a graphify run, pre-release, refactor, etc. Write this down — it shapes what the synthesis emphasises.
- **Are there docs to reconcile against?** Most projects have something. If there are none, the campaign produces them from scratch instead of reconciling.
- **Are external resources (DB, MCP, APIs) reachable?** Probe early. If the DB pooler is down, you'll fall back to migration files and use the CHECKPOINT pattern for anything you can't verify directly.
- **Size pre-flight.** If the codebase is over 1,500 files or 1.5M words, ask which subfolder to start with — running on the whole thing dilutes findings and burns tokens. The point of the campaign isn't to crawl every file; it's to find the structural truth.

If the user has just done a graphify (or similar) run and the findings are visible, mine that output for hypotheses **before** designing the campaign — the hypotheses become specific tasks for the wave-1 subagents to verify.

## Step 2 — Design the campaign plan

Always write a campaign plan as the first artefact. Save it at:

`docs/audit-campaigns/<YYYY-MM-DD>_<topic>/00-campaign-plan.md`

Use the template in [references/templates.md](references/templates.md#campaign-plan). The plan must include:

- **Trigger / context** — why this campaign, what it's reconciling against
- **Wave structure** — 4 waves with task lists
- **Per-task agent + model assignment** (see [model assignment](#model-assignment) below)
- **Logging convention** — the numbered findings file format
- **Success criteria** — what "done" looks like for this specific run

Show the plan to the user and get explicit approval before dispatching subagents. The plan is cheap to revise; a wave of 5 subagents is not.

## Step 3 — Run the four waves

The full wave-by-wave playbook (including prompt templates for each subagent type) lives in [references/wave-playbook.md](references/wave-playbook.md). Read it when you're ready to dispatch subagents.

Headline structure:

| Wave | Mode | What it does | Typical task count |
|------|------|--------------|---|
| **W1 — Foundation reality** | parallel | Reconciles each major doc (Backend, Frontend, Integration, Rules) against actual code/DB | 4 |
| **W2 — Deep structural** | parallel (some depend on W1.1) | Dead code, API route mapping, permission/RLS parity, hierarchy/scoping | 4 |
| **W3 — Domain depth** | parallel | God-object decomposition, realtime/subscription map, mutation layer, anything domain-specific | 2–4 |
| **W4 — Synthesis** | sequential | Master synthesis → staged doc rewrites → promotion → vault-log | 1 (or 1+N if you parallelise the rewrites) |

Each wave's findings file is numbered: `01-backend-reality.md`, `02-frontend-reality.md`, etc., with `99-synthesis.md` last. See [references/templates.md](references/templates.md#findings-file) for the canonical findings-file shape.

**Critical**: wait for the previous wave's hard dependencies before launching the next. W2.3 (permission audit) and W2.4 (hierarchy audit) typically benefit from W1.1 (backend reality) data. W4 always waits for everything.

If a subagent comes back blocked (DB unreachable, MCP timing out, missing input), don't abandon the wave — fall back to a tractable proxy (migration files, git history, AST output) and emit `<!-- CHECKPOINT: CHK-<id> -->` markers for anything that can't be verified now. See [references/checkpoint-pattern.md](references/checkpoint-pattern.md).

## Step 4 — Synthesise

Read every findings file. Write `99-synthesis.md` yourself (don't delegate this to a subagent — synthesis benefits from reading all the evidence with a single mind). The synthesis is structured as:

1. **TL;DR** — drift one-liner, real bugs, security findings, latent design gaps, architecture facts the graph misled you on
2. **Critical findings** (security & defence-in-depth)
3. **Real bugs** (worth fixing soon)
4. **Doc ghosts** (referenced but don't exist)
5. **Doc orphans** (in doc but not in reality)
6. **Undocumented reality** (in code but not in doc)
7. **Architecture patterns to document**
8. **Per-doc rewrite checklist** (this is the brief for Step 5)
9. **Code cleanup checklist** (separate PR; not your job in this campaign)
10. **Open questions for the user** (must be answered before promotion)
11. **Re-audit cadence**

See [references/templates.md](references/templates.md#synthesis) for the exact shape.

## Step 5 — Staged doc rewrites + promotion

Create `docs/staged/` and write each rewritten doc there first, never directly over the live doc. This gives the user a diff to review before promotion.

If the rewrites are large, you can parallelise — one subagent per doc, each given the synthesis + their target doc. Use [references/wave-playbook.md](references/wave-playbook.md#w4-doc-rewrites) for the briefs.

Promotion gate (all of these must hold before `mv staged/X.md X.md`):

- [ ] All checkpoint markers either resolved or explicitly accepted as "ship with marker visible"
- [ ] Diff (`git diff staged/ live/`) reviewed by the user
- [ ] Surgical edits applied to meta-docs (CLAUDE.md, primary instructions) so they're consistent with the new doc state
- [ ] Vault-log entry drafted per the project's logging rule (P8 in this codebase)
- [ ] Empty `staged/` directory removed

If a doc is blocked by an unresolved external check (e.g., DB pooler down), promote everything else and keep that doc staged. When the blocker clears, run the CHECKPOINTS.md queries, resolve markers, then promote.

## Step 6 — Re-run protocol & docs for future runs

Add a short `docs/audit-campaigns/README.md` that explains the convention so the next run is self-bootstrapping. The boilerplate lives in [assets/campaign-readme-template.md](assets/campaign-readme-template.md). Reference it from the project's general guidelines under a new rule (P14 or equivalent: "audit-campaign convention").

The template includes the wave structure, model assignments, the checkpoint pattern, the promotion gate, and a placeholder past-campaigns table. The next campaign appends a row and produces a new dated folder.

## Model assignment

Pick the model based on what each task actually requires. Wrong assignments waste tokens on routine work or under-think security-critical work.

| Task type | Model | Why |
|---|---|---|
| Schema reasoning, RLS parity, security audits | **opus** | Cross-table reasoning, weighing evidence across many migrations |
| Architecture reality (god objects, dead code, refactor risk) | **opus** | Must overturn graph hypotheses with code evidence |
| Master synthesis (you, not a subagent) | **opus** | Coherent narrative across 8+ findings files |
| Doc rewrites (Backend.md, Frontend.md — biggest scope) | **opus** | Cross-cutting; precision matters |
| Pattern compliance (grep-driven counting) | **sonnet** | Mechanical, fast, accurate at scale |
| API route / fetch-callsite mapping | **sonnet** | Well-defined surface area |
| File-system inventory, dead-code verification | **sonnet** | Mechanical |
| Realtime channel / subscription mapping | **sonnet** | Well-defined surface |
| Mutation-module compliance per file | **sonnet** | Per-module checklist |
| Doc rewrites (Integration.md, Guidelines.md — smaller scope) | **sonnet** | Less cross-cutting |
| Mass file-listing, trivial extractions | **haiku** | Cheap, fast |

**Avoid haiku for anything that requires nuance or domain context.** A campaign is not the place to save tokens at the cost of getting the analysis wrong.

## Subagent dispatch best practices

- **Use `general-purpose` as the subagent type by default.** Specialized auditors (`backend-auditor`, `frontend-auditor`) often have constrained contracts — they may only return diffs, not full findings files. If a specialized auditor exists and matches the task scope, use it; otherwise default to general-purpose so the agent can write findings to disk freely.
- **Hand each subagent a self-contained brief** that includes: pre-existing findings to read first (so they don't redo work), exact output path, frontmatter to use, sections expected. The wave playbook has these briefs.
- **Tell every subagent to write a single findings file**, not to modify code or other docs. The campaign is a read-only audit until W4.
- **Run waves in parallel within a wave** — same message, multiple Agent calls. Sequential dispatch defeats the parallelism that makes the campaign tractable.
- **Track agent IDs** — when a subagent gets blocked or returns partial work, you'll need to relaunch with corrected scope.
- **If you said you dispatched something, verify it actually ran.** Look at the agent transcript directory or the findings file's existence on disk before claiming done. (This is how we burned a wave once.)

## The checkpoint pattern (when external data is unreachable)

If a subagent can't verify something at audit time (DB pooler down, third-party API throttled, MCP unavailable), don't guess. Insert a marker:

```
<!-- CHECKPOINT: CHK-<id> · short description · expected: <migration-derived value or "unknown"> -->
```

Then add a row to `CHECKPOINTS.md` in the campaign folder, with the exact query/command to run when the blocker clears. The doc can ship with the marker visible — readers see "we don't know yet" rather than a false claim.

When the blocker clears: run all queries, resolve every marker, promote any held-back staged docs, and emit a follow-up vault-log entry referencing the original.

Full pattern in [references/checkpoint-pattern.md](references/checkpoint-pattern.md).

## Common failure modes

1. **Trusting a graph hypothesis without code verification.** Graphify-style outputs surface candidates; they don't prove. The 91-edge "god object" in the inspiring run turned out to be a 95-line file with 3 fields and 5 actions — high fan-in, narrow API. Always verify before recommending a refactor.
2. **Skipping the synthesis step.** Without `99-synthesis.md`, the doc rewrites drift from the evidence. The synthesis is the bridge.
3. **Promoting docs without staged review.** The user must see the diff before live docs change. Skip this and you risk overwriting `[!atta]`-style sacred blocks or losing context the doc carried.
4. **Letting "running tally" footers proliferate.** If the previous version of the docs has per-pass housekeeping footers, retire them — they're the source of every "doc cites 4 different counts of the same thing" finding.
5. **Forgetting to remove the empty staged/ dir.** Cosmetic but indicates the promotion is complete.

## Output conventions

Every campaign produces:

- `docs/audit-campaigns/<YYYY-MM-DD>_<topic>/00-campaign-plan.md` — the plan
- `docs/audit-campaigns/<YYYY-MM-DD>_<topic>/NN-<task>.md` — one per audit task (typically 8–12 files)
- `docs/audit-campaigns/<YYYY-MM-DD>_<topic>/99-synthesis.md` — the master changelog
- `docs/audit-campaigns/<YYYY-MM-DD>_<topic>/CHECKPOINTS.md` — only if external blockers existed
- `docs/audit-campaigns/<YYYY-MM-DD>_<topic>/01b-pooler-snapshot.md` (or similar) — only if a follow-up reconciliation ran
- Updated live docs (Backend, Frontend, Integration, Guidelines, etc.)
- Updated meta-docs (CLAUDE.md / project root instructions)
- One vault-log entry per the project's logging rule
- `docs/audit-campaigns/README.md` (first run only) — re-run protocol

## Reference files

- [references/wave-playbook.md](references/wave-playbook.md) — full wave-by-wave playbook with subagent prompt templates for each task
- [references/templates.md](references/templates.md) — campaign-plan, findings-file, synthesis, checkpoint-registry, vault-log templates
- [references/checkpoint-pattern.md](references/checkpoint-pattern.md) — when and how to use CHECKPOINT markers
- [assets/campaign-readme-template.md](assets/campaign-readme-template.md) — boilerplate for the project's audit-campaigns/README.md
