---
title: Campaigns — Re-run Protocol (audit & build)
description: How to run a doc-sync audit campaign or a multi-phase build campaign on this project
created: <YYYY-MM-DD>
referenced_by: GENERAL-GUIDELINES.md (P14 or equivalent), CLAUDE.md, primary_instructions.md
---

# Campaigns

This convention covers **two kinds of campaign** that run on this project:

- **Audit campaigns** — systematic doc-sync runs that reconcile source-of-truth docs (Backend, Frontend, Integration, Guidelines) with code and DB reality. They produce an evidence trail and staged doc rewrites.
- **Build campaigns** — multi-phase feature builds and refactors that must remain deployable at every step. They produce per-phase plans + change logs and a post-rollout risk sweep.

Both modes share the same wave skeleton, the same model heuristics, the same checkpoint pattern, the same vault-log convention. They differ in subagent contracts (audit subagents are read-only; build subagents are read-only in W1/W2 and execute under user-approved gates in W3) and final artefacts (promoted docs vs shipped feature + memory entries).

---

## When to run each

### Audit campaign

- After every major version (e.g. 1.6.x → 1.7.0)
- Whenever a `/graphify` (or equivalent dependency-graph) run shows community cohesion < 0.2 or > 30% of communities labelled as "stale"
- Quarterly at minimum
- Whenever doc drift is suspected by the maintainer or surfaces in a vault-log review

### Build campaign

- Whenever a feature is going to touch ≥3 surfaces (schema, RLS, views, triggers, types, FE, admin, mutations, docs)
- Anything money-adjacent, anything that must remain deployable at every step, anything where rollback would mean restoring from backup
- Whenever the user has drafted a multi-phase plan and now wants the execution wrapped in the same parallel/numbered/evidence-trail discipline an audit gets

---

## Directory convention

```
docs/audit-campaigns/<YYYY-MM-DD>_<topic>/    # audit campaigns
├── 00-campaign-plan.md
├── 01-backend-reality.md      # W1.1
├── 02-frontend-reality.md     # W1.2
├── 03-integration-reality.md  # W1.3
├── 04-rule-compliance.md      # W1.4
├── 05-dead-code.md            # W2.1
├── 06-api-routes.md           # W2.2
├── 07-permissions.md          # W2.3
├── 08-file-hierarchy.md       # W2.4
├── 09-...                     # W3 tasks (project-specific)
├── 10-realtime.md             # W3.2 (etc.)
├── 11-mutations.md            # W3.3
├── 99-synthesis.md            # W4 step 1 — master changelog
└── CHECKPOINTS.md             # only if external blockers existed at audit time

docs/build-campaigns/<YYYY-MM-DD>_<topic>/    # build campaigns
├── 00-campaign-plan.md
├── 01-w1-discovery-schema.md   # W1.1
├── 02-w1-discovery-frontend.md # W1.2
├── 03-w1-discovery-admin.md    # W1.3
├── 04-w1-discovery-docs.md     # W1.4 (optional)
├── 05-phase-0-safety-net.md    # W2/W3 phase 0
├── 06-phase-1-schema.md        # W2/W3 phase 1
├── 07-phase-2-backfill.md      # W2/W3 phase 2
├── 08-phase-3-views.md         # W2/W3 phase 3
├── 09-phase-4-frontend.md      # W2/W3 phase 4
├── ...
├── 99-risk-sweep.md            # W4 — post-rollout sweep
└── CHECKPOINTS.md              # only if post-deploy probes are still pending
```

Frontmatter for every file:

```yaml
---
task: WX.Y - Task Name
agent: subagent-type
model: opus|sonnet|haiku
mode: audit|build
phase: N        # build mode only
date: YYYY-MM-DD
status: complete|partial|blocked
gate: ...       # build mode only — pending-user-approval|approved-YYYY-MM-DD-HHMM
---
```

Audit body sections: **Method · Findings · Drift table · Recommendations · Open questions**.
Build phase body sections: **Goal · Inputs · SQL drafts · Type drafts · Code sketches · Validation · Advisor expectations · Rollback · Risks · Approval gate · What actually ran**.

---

## Wave structure

| Wave | Audit tasks | Build tasks | Run mode |
|---|---|---|---|
| **W1 — Foundation / Discovery** | Backend, Frontend, Integration, Rule compliance reality | Per-surface discovery (schema, FE, admin, docs) — read-only | parallel |
| **W2 — Deep structural / Phase plans** | Dead code, API routes, Permission system, Hierarchy/scoping | One subagent per phase — read-only drafts | parallel |
| **W3 — Domain depth / Implementation** | God objects (if any), Realtime, Mutation layer | Main-agent execution of each phase, sub-agent parallelism inside | parallel (audit) / sequential per phase (build) |
| **W4 — Synthesis / Verification** | Master synthesis → staged doc rewrites → promotion → vault-log | Risk sweep + vault log + memory entries | sequential |

A typical audit campaign runs ~11 audit tasks producing ~10 findings files.
A typical build campaign runs 3–5 W1 discovery files + 4–8 phase files + 1 risk sweep.

---

## Model recommendations

| Task type | Mode | Model | Reason |
|---|---|---|---|
| Schema reasoning, RLS parity, security audits | audit | opus | needs deep cross-table reasoning |
| Architecture reality (god objects, dead code) | audit | opus | needs to weigh evidence and overturn graph hypotheses |
| Pattern compliance (grep-driven counting) | audit | sonnet | mechanical, fast, accurate at scale |
| API route mapping, realtime channel tracing | audit | sonnet | well-defined surface area |
| File-system inventory, dead code verification | audit | sonnet | mechanical |
| Master synthesis | audit | opus | reads all findings, distils a coherent rewrite brief |
| Doc rewrites (Backend, Frontend) | audit | opus | longest, most cross-cutting |
| Doc rewrites (Integration, Guidelines) | audit | sonnet | smaller scope |
| Surface discovery — schema/RLS/views | build | opus | cross-table reasoning |
| Surface discovery — types/FE/admin | build | sonnet | well-defined surface |
| Phase plan drafting — DDL/RLS/triggers | build | opus | RLS interactions, trigger order, money-adjacent risk |
| Phase plan drafting — types/FE/mutations | build | sonnet | pattern-following |
| Implementation — schema/RLS/triggers | build | opus (main agent) | one-shot migrations; mistakes are expensive |
| Implementation — types/FE/mutations | build | sonnet (sub-agents under main) | pattern-following |
| Risk sweep & vault log | build | opus (main agent) | surfaces adjacent-feature regression risks |

Haiku is intentionally not used — every task in this domain needs nuanced understanding of the project's context.

---

## When external resources are unreachable or probes are pending

The DB pooler / MCP / third-party API can time out independently of the campaign. Build campaigns also have post-deploy probes that can only be answered after prod traffic. Either way:

1. **Don't abort.** Fall back to migration files / git history / AST output as ground truth (audit). Fall back to a deferred phase or a CHECKPOINT-tracked probe (build). They're partial but solid.
2. **Mark every unverified claim** with `<!-- CHECKPOINT: CHK-<id> · description · expected: <value> -->` markers in the staged docs / phase logs.
3. **Write CHECKPOINTS.md** in the campaign folder with the SQL queries / probes to run when the blocker clears.
4. **Promote staged docs / close the phase that don't depend on the blocker** — keep BACKEND.md (or whichever phase is affected) staged.
5. **When the blocker clears**, run the `CHECKPOINTS.md` §1 queries, walk §2 row by row, replace placeholder values, drop checkpoint markers, then promote the held-back docs / mark the deferred phase verified and emit a follow-up vault-log.

---

## Re-run trigger checklist

### Audit campaign

- [ ] Confirm a graphify run is recent (< 7 days) — if not, run `/graphify <path>` first
- [ ] Read the previous campaign's `99-synthesis.md` and `CHECKPOINTS.md` (if any) — pick up unfinished items
- [ ] Confirm external resources (DB, MCP) are reachable. If not, plan the fallback path.
- [ ] Confirm BACKEND, FRONTEND, INTEGRATION, GUIDELINES are at known-good state in git
- [ ] Allocate 30–60 min of wall time per wave (4 waves ≈ 2–4 hours total)

### Build campaign

- [ ] User has drafted (or approved) a phased plan with phase titles and dependencies
- [ ] Surface count is ≥3 — confirm the campaign discipline is justified vs. a single-file change
- [ ] DB is reachable for `apply_migration`; advisors are available for post-phase checks
- [ ] No active audit campaign or unrelated multi-phase build is running on the same surface — campaigns don't interleave well
- [ ] Allocate ~30 min per phase plan in W2 + actual implementation time per phase in W3 + 30 min for risk sweep in W4

---

## Promotion gate

### Audit campaign (staged → live)

1. All checkpoints clear (or are explicitly accepted as "ship with marker visible")
2. `git diff docs/staged/ docs/{BACKEND,FRONTEND,INTEGRATION,GENERAL-GUIDELINES}.md` reviewed
3. Meta-doc surgical edits applied (CLAUDE.md / primary_instructions.md so they're internally consistent)
4. Vault-log entry written referencing the campaign folder
5. New `/graphify` run confirms docs match new graph reality (community cohesion ≥ 0.2 on documented surfaces)

### Build campaign (per-phase + campaign-close)

Per phase (in W3, before next phase begins):

1. Phase plan was approved by the user before execution
2. Validation queries from the plan ran and passed
3. Advisor / lint / check-types delta is acceptable
4. Phase change-log section was filled in with what actually ran
5. Tests added or updated for the new surface

Campaign-close (after the last phase):

1. `99-risk-sweep.md` written with post-rollout watch items
2. Single vault-log entry written, covering all phases, linking the campaign folder
3. Memory entries created for any surprise discoveries
4. Open items (deferred phases, post-deploy probes) explicitly listed in the risk sweep
5. User confirms the feature is live and observable

---

## Past campaigns

| Date | Mode | Campaign | Trigger | Outcome |
|---|---|---|---|---|
| <Date> | audit \| build | <topic> | <trigger> | <one-line outcome> |

(Append a row per campaign.)
