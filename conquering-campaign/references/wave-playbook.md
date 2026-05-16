# Wave Playbook

Full wave-by-wave brief templates for subagent dispatch. Read this before launching each wave.

## Conventions used in every brief

Every subagent gets this scaffolding:

1. **Pre-existing findings to read first** (paths, with one-line descriptions of what each contains). This stops the agent from redoing work earlier waves already did.
2. **Exact output path** — `lex_council/docs/audit-campaigns/<DATE>_<topic>/NN-<task>.md` or equivalent for the project.
3. **Frontmatter to use** (task / agent / model / date / status).
4. **Section structure expected** in the body (Method, Findings, Drift table, Recommendations, Open questions).
5. **"Read-only audit; do not modify code or other docs; only write the findings file."**

If a subagent type is `general-purpose`, it can write to disk freely. If it's a specialized auditor (e.g., `backend-auditor`, `frontend-auditor`), it may have a contract that constrains what it can return — re-dispatch with `general-purpose` if the brief needs the agent to write a findings file.

---

## W1 — Foundation reality (parallel, ~4 tasks)

### W1.1 — Backend Reality Audit
**Subagent:** `general-purpose` (or `backend-auditor` if its contract permits writing findings files)
**Model:** opus
**Output:** `01-backend-reality.md`

Compare live DB (via MCP / direct SQL) against the project's backend doc. If the DB is unreachable, fall back to migration files as ground truth and use the CHECKPOINT pattern.

Cover:
- Tables, columns, FKs, CHECK constraints
- Views (especially the `*_js` view convention)
- RLS policies (every table — flag tables with RLS-on-no-policies, RLS disabled in `public`)
- Triggers (per-table, retired vs live)
- Cron / scheduled jobs
- Edge functions (deployed vs documented)
- Extensions enabled
- Internal contradictions in the doc (the same count cited at different values inside one doc — the "running-tally footer" smell)

Output sections: Method · Authoritative counts (with evidence) · Drift table · Internal contradictions · RLS coverage map · Critical findings · Undocumented entities · Orphan documentation · Recommendations · Open questions.

### W1.2 — Frontend Reality Audit
**Subagent:** `general-purpose`
**Model:** opus
**Output:** `02-frontend-reality.md`

Compare actual code in the web/app folder against the frontend doc. Inventory routes, components, stores, hooks, mutations, type files, design tokens. Verify pattern compliance for all C-rules (component structure, no Tailwind, no hex literals outside the token system, MIcon-only, header conventions, etc.).

Verify graph-derived hypotheses (god objects, super-bridges, dead-code candidates) by reading the actual files. Most "god objects" turn out to be high-fan-in narrow-API singletons; recommend splitting only when the file is genuinely doing too much.

Output sections: Method · Route inventory · Store reality · Mutation foundation · Hooks inventory · Pattern compliance · Dead code verification · God-object reality · Recommendations · Open questions.

### W1.3 — Integration Reality Audit
**Subagent:** `general-purpose`
**Model:** sonnet
**Output:** `03-integration-reality.md`

Auth flow, Supabase / API client setup, realtime subscriptions, storage buckets, signed URL flow, edge function contracts. Compare to the project's integration doc.

Read the actual `packages/auth`, `packages/supabase`, middleware, login page, layout guards, every `useRealtime*` hook. Don't trust diagram-style docs — read the code.

Output sections: Method · Clients (browser/server/admin/middleware) · Auth flow step-by-step with file:line refs · Realtime inventory · Storage inventory · Edge functions inventory · Drift markers · Recommendations · Open questions.

### W1.4 — Rule Compliance Audit
**Subagent:** `general-purpose`
**Model:** sonnet
**Output:** `04-rule-compliance.md`

Walk every rule in the project's general-guidelines doc. For each rule, sample-check or grep-count compliance. The goal is a compliance scorecard: per-rule % + sample size + status, plus top-N violations per rule with `file:line`.

Watch for rules whose specification doesn't match practice (e.g., a type-naming convention nobody uses). Those rules need to be rewritten to match reality, not enforced.

Output sections: Method · Compliance scorecard · Top violations per rule · Rules that should be retired or rewritten · Recommendations · Open questions.

---

## W2 — Deep structural (parallel, ~4 tasks)

### W2.1 — Dead code & islands
**Subagent:** `general-purpose`
**Model:** sonnet
**Output:** `05-dead-code.md`

Take the graphify "isolates" + "small island clusters" output. For each candidate: grep for imports, check `import()` dynamic loads, look at git log, classify as DEAD / DYNAMIC / MISSING-EDGE / CONFIG.

Every project has barrel-`index.ts` blindness — files exported through a barrel show up as graph isolates because the edge runs through the barrel. Don't classify those as dead.

Output sections: Method · Kill list (with evidence) · Verify-then-delete list · Decision-needed list · Dynamic / re-export shims · API routes (string-fetch is an AST blind spot by design) · Config-file isolates · Recommendations · Open questions.

### W2.2 — API route map
**Subagent:** `general-purpose`
**Model:** sonnet
**Output:** `06-api-routes.md`

Inventory every route handler. For each, find every `fetch(...)` callsite or equivalent and reconstruct the runtime call graph the AST cannot see. Classify orphan routes (no callers) and ghost calls (fetches to URLs without a route).

Document the conventions: HTTP method patterns (POST-only command-style is common), shared `_helpers.ts` modules, mutation-wrapper indirection (`post(route, body)` helpers), direct-fetch bypasses (worth flagging as code-cleanup).

Output sections: Method · Route inventory · Caller map · Orphan routes · Ghost calls · Conventions · Recommendations · Open questions.

### W2.3 — Permission system reality
**Subagent:** `general-purpose`
**Model:** opus
**Output:** `07-permissions.md`

Build the missing permission/RLS parity matrix. Every `<PermissionGate>` callsite, every `cmAp` / permission-key value, every role flag (read the actual auth types — minimal projection vs full identity often diverge), every RLS policy that should match each gate.

Watch for "VAP-bypass" or equivalent patterns where a flag should appear in both UI gate and as a 4th-OR clause in RLS. Surface gaps where the gate exists but RLS doesn't enforce defence-in-depth.

Output sections: Method · Role flags inventory (real flags vs doc ghosts) · Permission registry decoded · Gate inventory (page → perm → tables) · RLS-by-table map · Parity matrix (gate ↔ RLS) · Critical gaps · Recommendations · Open questions.

### W2.4 — File hierarchy / scoping audit
**Subagent:** `general-purpose`
**Model:** sonnet
**Output:** `08-file-hierarchy.md`

If the project has a hierarchical entity (e.g., GFN→MFN→BFN→SFN→AFN file class), document where it's enforced (DB constraints? trigger? client-side?), where it's displayed (breadcrumb component? tree view?), and where it might be inconsistently applied across pages.

Branch / tenant / org scoping: every entity query that filters by branch / tenant. Find queries missing that filter (potential data leak).

Output sections: Method · Schema model · UI navigation · Scoping callsite inventory · Cross-tenant entities · Current-tenant session state · Possible leaks · Recommendations · Open questions.

---

## W3 — Domain depth (parallel, 2–4 tasks)

The exact tasks depend on what the project has. Common ones:

### W3.1 — God-object decomposition (only if W1.2 confirms a true god object)
**Subagent:** `Plan` or `general-purpose`
**Model:** opus
**Output:** `09-god-object.md`

If W1.2 found a real god object (large file with broad responsibility, not just high fan-in), produce a decomposition plan: identify natural splits, blast radius per split option, recommendation. Skip this task if W1.2 disproved the premise.

### W3.2 — Realtime / subscription map
**Subagent:** `general-purpose`
**Model:** sonnet
**Output:** `10-realtime.md`

Every `.subscribe()`, every `useRealtime*` hook, every channel name and table target. Check for `REPLICA IDENTITY` mismatches (non-PK filters on tables with DEFAULT replica identity will silently drop UPDATE events). Audit cleanup: every `useEffect` channel must `removeChannel` on unmount.

Common bug: `return () => clearTimeout(t)` placed inside a Supabase `.on()` callback. The `.on()` callback's return value is discarded — the timer is uncancellable. Hoist the timer to the outer `useEffect` scope.

Output sections: Method · Channel inventory · Hook patterns · Cleanup audit · Risks · Recommendations · Open questions.

### W3.3 — Mutation layer audit
**Subagent:** `general-purpose`
**Model:** sonnet
**Output:** `11-mutations.md`

Per-module compliance: returns the project's standard result type? Uses the shared error helper? Uses the shared client factory? Auth-checked? Branch/tenant scoping?

Catalog direct-write violations (components that bypass `lib/mutations/`). Classify as intentional-documented (has a `// BR-NNN:` comment), intentional-undocumented, or accidental. The first two stay; the third is a refactor target.

Output sections: Method · Module compliance table · Reference pattern (the cleanest exemplar) · Deviation list · Direct-write violations · Auth coverage · Recommendations · Open questions.

---

## W4 — Synthesis & doc rewrites (sequential)

### W4 step 1 — Master synthesis (you do this, not a subagent)

Read every findings file. Write `99-synthesis.md` per the template in [templates.md#synthesis](templates.md#synthesis). Don't delegate — synthesis benefits from a single mind reading all the evidence.

### W4 step 2 — Staged doc rewrites (parallel subagents)

One agent per doc. Each gets the synthesis + their target doc + instructions to:

- Write to `docs/staged/<DOC>.md`, NOT over the live file
- Use `<!-- CHECKPOINT: CHK-<id> -->` markers for unverified claims
- List all checkpoint markers in a "Pending Checkpoints" section at the bottom
- Fill in a frontmatter with `last_full_audit`, `counts_verified`, etc.

#### W4.A — Backend doc rewrite
**Model:** opus (heaviest scope: counts reconciliation, undocumented entities, RLS coverage)

#### W4.B — Frontend doc rewrite
**Model:** opus (cross-cutting: pattern updates, store/hook/route counts, new sections for hierarchy/permissions/realtime)

#### W4.C — Integration doc rewrite
**Model:** sonnet (well-defined: 3 clients, 7-step auth, realtime channels, API routes)

#### W4.D — Guidelines doc rewrite
**Model:** sonnet (rule-by-rule)

### W4 step 3 — Promotion gate

Before `mv staged/X.md X.md`:

- Diff the staged vs live (`git diff` if both are tracked)
- Show the user the major changes
- Get explicit "promote" or "promote these but hold that one"
- Apply surgical edits to meta-docs (CLAUDE.md, primary instructions) so they're internally consistent
- Draft the vault-log
- Promote
- Remove the empty `staged/` directory

### W4 step 4 — Re-run docs (only if first campaign on this project)

Create `docs/audit-campaigns/README.md` from [assets/campaign-readme-template.md](../assets/campaign-readme-template.md) so future runs know the convention. Add a rule (e.g., P14) to the project's general guidelines pointing at it.

---

## Subagent prompt skeleton

When dispatching a subagent, this is the shape of every brief:

```
You are <task ID> of a <campaign topic> campaign.

## Pre-existing findings to read first

- <path-1> — <one-line description>
- <path-2> — <one-line description>
- ...

## Your task

<concrete description of what to produce, with verifiable scope>

<key context the subagent needs — file paths, expected counts, hypotheses to verify>

## Output

Write findings to `<absolute path to NN-<task>.md>` with this header:

\`\`\`
---
task: <wave>.<num> - <Task Name>
agent: <subagent-type>
model: <opus|sonnet|haiku>
date: <YYYY-MM-DD>
status: complete|partial|blocked
---
\`\`\`

Sections:
1. **Method**
2. **<task-specific section>**
...
N. **Recommendations**
N+1. **Open questions**

Read-only audit. Do not modify code or other docs — only write the findings file.
```
