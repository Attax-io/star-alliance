---
title: Audit Campaigns — Re-run Protocol
description: How to run a doc-sync audit campaign when docs and code drift visibly
created: <YYYY-MM-DD>
referenced_by: GENERAL-GUIDELINES.md (P14 or equivalent), CLAUDE.md, primary_instructions.md
---

# Audit Campaigns

This directory holds **doc-sync audit campaigns** — the systematic process for reconciling the project's source-of-truth docs (Backend, Frontend, Integration, Guidelines) with code and DB reality. Per the project's audit-campaign rule, a campaign should run:

- After every major version (e.g. 1.6.x → 1.7.0)
- Whenever a `/graphify` (or equivalent dependency-graph) run shows community cohesion < 0.2 or > 30% of communities labelled as "stale"
- Quarterly at minimum
- Whenever doc drift is suspected by the maintainer or surfaces in a vault-log review

Each campaign produces an evidence trail (numbered findings files) and a final synthesis (`99-synthesis.md`) that drives a staged doc rewrite.

---

## Convention

```
docs/audit-campaigns/<YYYY-MM-DD>_<topic>/
├── 00-campaign-plan.md        # wave structure + agent/model assignments
├── 01-backend-reality.md      # W1.1
├── 01a-edge-functions-live.md # any per-task partials (W1.1a, etc.)
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
```

Frontmatter for every findings file:

```yaml
---
task: WX.Y - Task Name
agent: subagent-type
model: opus|sonnet|haiku
date: YYYY-MM-DD
status: complete|partial|blocked
---
```

Body sections (in this order): **Method · Findings · Drift table · Recommendations · Open questions**.

---

## Wave structure

| Wave | Tasks | Run mode | Why |
|---|---|---|---|
| **W1 — Foundation reality** | Backend, Frontend, Integration, Rule compliance | parallel | Cheap independent reads; produces the evidence base |
| **W2 — Deep structural** | Dead code, API routes, Permission system, Hierarchy/scoping | parallel (some need W1.1 RLS data) | Goes deeper on the structural layer; uncovers bugs |
| **W3 — Domain depth** | God objects (if any), Realtime, Mutation layer | parallel | Targeted depth on patterns that span multiple communities |
| **W4 — Synthesis** | Master synthesis → staged doc rewrites → promotion → vault-log | sequential | Single coherent narrative; one promotion gate |

A typical campaign runs ~11 audit tasks producing ~10 findings files. Each task is a single subagent invocation (or two if the first attempt is blocked).

---

## Model recommendations

| Task type | Model | Reason |
|---|---|---|
| Schema reasoning, RLS parity, security audits | opus | needs deep cross-table reasoning |
| Architecture reality (god objects, dead code) | opus | needs to weigh evidence and overturn graph hypotheses |
| Pattern compliance (grep-driven counting) | sonnet | mechanical, fast, accurate at scale |
| API route mapping, realtime channel tracing | sonnet | well-defined surface area |
| File-system inventory, dead code verification | sonnet | mechanical |
| Master synthesis | opus | reads all findings, distils a coherent rewrite brief |
| Doc rewrites (Backend, Frontend) | opus | longest, most cross-cutting |
| Doc rewrites (Integration, Guidelines) | sonnet | smaller scope |

Haiku is intentionally not used — every task in this domain needs nuanced understanding of the project's context.

---

## When external resources are unreachable

The DB pooler / MCP / third-party API can time out independently of the campaign. If a query is blocked:

1. **Don't abort.** Fall back to migration files / git history / AST output as ground truth. They're delta-only — solid for some surfaces, partial for others.
2. **Mark every unverified claim** with `<!-- CHECKPOINT: CHK-<id> · description · expected: <value> -->` markers in the staged docs.
3. **Write CHECKPOINTS.md** in the campaign folder with the SQL queries / commands to run when the blocker clears.
4. **Promote staged docs that don't depend on the blocker** — keep BACKEND.md (or whichever is affected) staged.
5. **When the blocker clears**, run the CHECKPOINTS.md §1 queries, walk §2 row by row, replace placeholder values, drop checkpoint markers, then promote the held-back docs and emit a follow-up vault-log.

---

## Re-run trigger checklist

Before launching a new campaign:

- [ ] Confirm a graphify run is recent (< 7 days) — if not, run `/graphify <path>` first
- [ ] Read the previous campaign's `99-synthesis.md` and `CHECKPOINTS.md` (if any) — pick up unfinished items
- [ ] Confirm external resources (DB, MCP) are reachable. If not, plan the fallback path.
- [ ] Confirm BACKEND, FRONTEND, INTEGRATION, GUIDELINES are at known-good state in git
- [ ] Allocate 30–60 min of wall time per wave (4 waves ≈ 2–4 hours total)

---

## Promotion gate

Before staged → live promotion:

1. All checkpoints clear (or are explicitly accepted as "ship with marker visible")
2. `git diff docs/staged/ docs/{BACKEND,FRONTEND,INTEGRATION,GENERAL-GUIDELINES}.md` reviewed
3. Meta-doc surgical edits applied (CLAUDE.md / primary_instructions.md so they're internally consistent)
4. Vault-log entry written referencing the campaign folder
5. New `/graphify` run confirms docs match new graph reality (community cohesion ≥ 0.2 on documented surfaces)

---

## Past campaigns

| Campaign | Trigger | Outcome |
|---|---|---|
| <Date> <topic> | <trigger> | <one-line outcome> |

(Append a row per campaign.)
