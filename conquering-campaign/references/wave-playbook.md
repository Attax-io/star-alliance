# Wave Playbook

Full wave-by-wave brief templates for subagent dispatch. Two top-level sections — one per mode. Read the right section before launching each wave.

## W0 — Offline pre-scan (both modes, main agent only)

W0 runs before any Claude subagent is dispatched. The main agent executes it directly via the Bash
tool — no subagent spawned, no Agent call. If Ollama is unavailable, skip to the W1 section for
the relevant mode.

### W0 execution checklist

```bash
# 1. Detect Ollama and list models
ollama list 2>/dev/null && echo "OLLAMA_OK" || echo "OLLAMA_UNAVAILABLE"

# 2. Check RAM (Mac)
sysctl -n hw.memsize | awk '{printf "Total RAM: %.0f GB\n", $1/1073741824}'
vm_stat | awk '/Pages free/ {printf "Free RAM (approx): %.1f GB\n", $3*16384/1073741824}'
```

**Auto-select models** (no user input needed):
- Code-pattern model: first `qwen2.5-coder` variant found in `ollama list` → fallback to any `qwen3` coder variant
- Summarisation model: `qwen3:8b` if free RAM ≥ 6 GB → `qwen3:14b` if free RAM ≥ 11 GB → fallback to code-pattern model
- Never select `deepseek-r1` for W0 (too slow for listing/grepping tasks)

### W0 for Audit mode

```bash
# Build the file list for the project
PROJ=<project_root>/apps/web
find "$PROJ" -type f \( -name "*.ts" -o -name "*.tsx" \) \
  | grep -v node_modules | grep -v .next \
  | xargs wc -l 2>/dev/null | sort -rn | head -60 \
  > /tmp/cc_prescan_files.txt

# Count key patterns separately (faster via bash than asking the model)
VIEW_COUNT=$(grep -rl "_js" "$PROJ/lib/query-configs/" 2>/dev/null | wc -l | tr -d ' ')
MUT_LIST=$(ls "$PROJ/lib/mutations/" 2>/dev/null | tr '\n' ', ')
ADMIN_COUNT=$(find "$PROJ/app/\(admin\)" -name "page.tsx" 2>/dev/null | wc -l | tr -d ' ')
TYPE_COUNT=$(find "$PROJ/types" -name "*.ts" 2>/dev/null | wc -l | tr -d ' ')

# Run the model
(echo "Pattern counts: views=$VIEW_COUNT mutations=$MUT_LIST admin_pages=$ADMIN_COUNT type_files=$TYPE_COUNT"; \
 echo "---"; cat /tmp/cc_prescan_files.txt) \
| ollama run <code-pattern-model> \
"You are analyzing a Next.js/Supabase codebase for an audit campaign.
You have been given pattern counts and a file list (by line count, largest first).
Produce ONLY these 4 sections in clean markdown — no preamble, no conclusion:

## 1. File inventory
Top 30 files — name, line count, one-line purpose guess.

## 2. Pattern counts (use the numbers provided above, do not re-count)
Restate the counts in a table: Views | Mutations | Admin pages | Type files.

## 3. Surface map
For each main entity (infer from file names), list which files read/write it.
Group by entity. Max 5 entities.

## 4. Gaps spotted
Anything obviously missing or inconsistent based on file names alone.
Max 5 items."
```

Write output to: `docs/audit-campaigns/<DATE>_<topic>/00-w0-offline-prescan.md`

Add this header to the file before the Ollama output:
```markdown
---
task: W0 - Offline Pre-scan
model: <ollama-model-name>
mode: audit
date: <YYYY-MM-DD>
w0_enabled: yes
code_pattern_model: <model>
summarisation_model: <model>
total_ram: <N>GB
free_ram_approx: <N>GB
---
```

### W0 for Build mode

```bash
PROJ=<project_root>
KEYWORD=<feature_keyword>   # e.g. "scoring", "insights", "attendance"

# Find files relevant to the feature
find "$PROJ" -type f \( -name "*.ts" -o -name "*.tsx" -o -name "*.sql" \) \
  | grep -v node_modules | grep -v .next \
  | xargs grep -l "$KEYWORD" 2>/dev/null \
  > /tmp/cc_prescan_feature_files.txt

FILE_COUNT=$(wc -l < /tmp/cc_prescan_feature_files.txt | tr -d ' ')

(echo "Files mentioning '$KEYWORD': $FILE_COUNT"; \
 echo "Feature to build: <feature description>"; \
 echo "---"; cat /tmp/cc_prescan_feature_files.txt) \
| ollama run <code-pattern-model> \
"You are analyzing a Next.js/Supabase codebase to help plan a feature build.
You have been given a list of files that mention the feature keyword.
Produce ONLY these 4 sections in clean markdown — no preamble, no conclusion:

## 1. Surface inventory
Every file likely touched by this feature — path and one-line reason.
Group by layer: DB/migrations | views | mutations | types | FE pages | components | admin.

## 2. Existing patterns to follow
Find 1-2 existing mutation modules, type files, or components to model new code after.
Include file path and the specific pattern it demonstrates.

## 3. Missing pieces
What clearly does not exist yet (inferred from feature description vs file list).
Be specific — 'no mutation module for X', 'no type file for Y row shape', etc.

## 4. Phase ordering hints
What must be created before what — so phase sequencing is correct.
List as: 'A before B because B depends on A'."
```

Write output to: `docs/build-campaigns/<DATE>_<topic>/00-w0-offline-prescan.md`

Same header format as audit mode but with `mode: build`.

### How W1 subagents use W0 output

Every W1 subagent brief must begin with:

```
## Pre-existing files to read first

- docs/<mode>-campaigns/<DATE>_<topic>/00-w0-offline-prescan.md — Ollama pre-scan:
  file inventory, pattern counts, surface map, gaps. Use this as your starting inventory.
  Verify claims that matter; don't re-derive what's already confirmed here.
```

W1 subagents **verify and deepen**, not re-explore from scratch. If the pre-scan says "23 views"
the subagent spot-checks a sample, not all 23. The token savings come from this compression.

---

## Conventions used in every brief (both modes)

Every subagent gets this scaffolding:

1. **Pre-existing files to read first** (paths, with one-line descriptions of what each contains). This stops the agent from redoing work earlier waves already did.
2. **Exact output path** — `docs/audit-campaigns/<DATE>_<topic>/NN-<task>.md` (audit) or `docs/build-campaigns/<DATE>_<topic>/NN-<task>.md` (build).
3. **Frontmatter to use** (task / agent / model / date / status, plus `mode: audit|build` and `phase: <N>` in build mode).
4. **Section structure expected** in the body.
5. **Explicit read-only vs may-write designation** — audit subagents are always read-only; build W1 and W2 subagents are read-only; build W3 subagents draft into their own phase-plan file only, the main agent does the actual execution.

If a subagent type is `general-purpose`, it can write to disk freely. If it's a specialised auditor or reviewer (e.g., `backend-auditor`, `frontend-auditor`, `code-reviewer`), it may have a contract that constrains what it can return — re-dispatch with `general-purpose` if the brief needs the agent to write a findings file.

---

# Wave Playbook — Audit Mode

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

### W4 step 4 — Re-run docs (only if first audit campaign on this project)

Create `docs/audit-campaigns/README.md` from [assets/campaign-readme-template.md](../assets/campaign-readme-template.md) so future runs know the convention. Add a rule (e.g., P14) to the project's general guidelines pointing at it.

---

# Wave Playbook — Build Mode

Build mode runs the same wave shape with different subagent contracts: W1 discovers the surfaces the feature touches, W2 drafts the per-phase plans, W3 executes phase-by-phase under approval gates, W4 verifies + logs.

## W1 — Discovery (parallel, ~3–5 tasks, READ-ONLY)

Inventory the surfaces this feature will touch. One subagent per surface. Every W1 subagent is **read-only** — they produce a findings file that becomes input for the W2 phase plans.

### W1.1 — Schema & DB surface
**Subagent:** `general-purpose` (or a domain-specific DB skill if available, e.g., the `file-access-model` or `phased-db-refactor` skills in this codebase)
**Model:** opus
**Output:** `01-w1-discovery-schema.md`

Inventory every DB surface the feature will touch:
- Tables that will be added, modified, or referenced
- Existing columns that will be dropped or renamed
- RLS policies on the affected tables (so phase plans know what the existing gates are)
- Triggers on the affected tables (so phase plans don't accidentally bypass a trigger's invariant)
- Views that read from the affected tables (the `_js` chain — every consumer)
- Indexes that may need rebuilding
- Realtime publication membership (so the feature can preserve live updates)
- Money-adjacent or audit-trail columns (extra caution — list them explicitly)

Output sections: Method · Tables in scope · RLS on each · Triggers on each · Downstream view dependents · Realtime members · Money-adjacent flags · Risks for phase planning · Open questions.

### W1.2 — Frontend surface
**Subagent:** `general-purpose`
**Model:** sonnet
**Output:** `02-w1-discovery-frontend.md`

Inventory every FE surface the feature will touch:
- Pages (route paths, layout files, server vs client component status)
- Components (the ones that will need new props, the ones that consume the affected stores)
- Stores (which Zustand stores hold related state — what will need new actions / new shape)
- Hooks (which `use*` hooks read from the affected stores / views)
- Type files (which `*-row.ts`, `*-form.ts`, `*-state.ts` files will need updates)
- Design tokens / i18n keys (which message namespaces will need new strings)

**Import-path trap — verify from a live consumer, not the file system.** When cataloguing shared primitives for reuse (sidebar components, row bases, shell wrappers), confirm the actual import path by reading an existing consumer of each primitive (e.g., the reference page file), not just by locating the file on disk. Component libraries sometimes migrate paths between versions (e.g., `@/components/admin/` → `@/components/portal/` in this codebase's v1.7.4). List the confirmed `import { X } from '...'` path next to each shared component in your findings — never the disk path alone.

**UI-consolidation extra — read the reference component's full render function.** When the campaign migrates a page/component to match an existing reference design, the subagent must read the reference component's *full render JSX* (not just its imports or prop types) and map out the visual hierarchy explicitly: e.g., "Line 1: row# + headline + actions | Line 2: icon-label metadata pairs with `paddingInlineStart: 40` | Line 3: status chips with `paddingInlineStart: 40`." Include this render-hierarchy map in the findings file. Phase 2 drafters cannot produce a conforming component sketch without it.

Output sections: Method · Page inventory · Component inventory (with confirmed import paths) · Store inventory · Hook inventory · Type-file inventory · i18n inventory · Render-hierarchy map (UI-consolidation only) · Risks for phase planning · Open questions.

### W1.3 — Admin & mutation surface
**Subagent:** `general-purpose`
**Model:** sonnet
**Output:** `03-w1-discovery-admin.md`

Inventory:
- Admin pages that will need new sections / new gates
- Existing permission flags (will any new ones be needed?)
- Mutation modules under `lib/mutations/` that will need new functions or modifications
- API routes that may need new endpoints (or extension)
- Edge functions that may need new endpoints (or extension)

Output sections: Method · Admin pages · Permission flags · Mutation modules · API routes · Edge functions · Risks for phase planning · Open questions.

### W1.4 — Docs & memory surface (optional)
**Subagent:** `general-purpose`
**Model:** sonnet
**Output:** `04-w1-discovery-docs.md`

Inventory which docs will need updates after the build ships (Backend, Frontend, Integration, Guidelines, leaf docs for each new entity), and which memory entries are likely to be created (surprise discoveries, traps, conventions).

Output sections: Method · Doc files to update · Memory entry candidates · Open questions.

---

## W2 — Phase plans (parallel, one subagent per phase, READ-ONLY)

Now that W1 mapped every surface, the user's high-level plan gets broken into per-phase plans. One subagent per phase. Each is **read-only** — they draft SQL / types / code into their own phase-plan file. The main agent will execute under the user's approval gate in W3.

Phase numbering follows the user's plan (P0 safety net, P1 schema, P2 backfill, …). Match it 1:1.

### W2.N — Phase N plan
**Subagent:** `general-purpose`
**Model:** opus for schema/RLS/trigger phases, sonnet for types/FE/mutation phases
**Output:** `0N-phase-N-<topic>.md` (e.g. `05-phase-1-schema.md`)

Each phase plan must include:

1. **Goal** — what this phase changes; what's deployable at the end of it
2. **Inputs** — which W1 discovery files are the source of truth; which prior phases must have shipped
3. **SQL drafts (if applicable)** — full DDL / DML, copy-paste ready, with comments explaining each statement
4. **Type drafts (if applicable)** — full type-file content, ready to write
5. **Code sketches (if applicable)** — diffs against existing files, with file paths and line anchors. For UI-consolidation phases (migrating a component to match a reference design), the sketch must open with the **render hierarchy** extracted from the W1.2 findings (or re-derived by reading the reference component's full render function): list each named line-level and its key style properties before showing the JSX sketch. A sketch that omits the hierarchy produces a component that reuses the correct tokens but misses the visual structure — visually flat instead of the reference's layered card layout.
6. **Validation** — exact SQL/queries to run after the phase to confirm it landed
7. **Advisor / lint expectations** — what `get_advisors`, `npm run lint`, `npm run check-types` should look like after
8. **Rollback** — how to undo this phase if the next phase fails
9. **Risks** — known traps (e.g., the project's `security_invoker` view trap, the trigger-rename body-update trap, the money-adjacent recompute trap)
10. **Approval gate** — what the user explicitly approves before the main agent proceeds

This file is also the change log: the main agent appends a "What actually ran" section to it during W3 execution, so the same file serves as plan-before and log-after.

### Phase plan dispatch brief (subagent prompt)

```
You are the phase-N planning subagent for the <feature> build campaign.

## Pre-existing files to read first

- docs/build-campaigns/<DATE>_<topic>/00-campaign-plan.md — the campaign plan + phase list
- docs/build-campaigns/<DATE>_<topic>/01-w1-discovery-schema.md — DB surface inventory
- docs/build-campaigns/<DATE>_<topic>/02-w1-discovery-frontend.md — FE surface inventory
- docs/build-campaigns/<DATE>_<topic>/03-w1-discovery-admin.md — admin/mutation surface inventory
- (any prior phase plan files that this phase depends on)

## Your task

Draft the full plan for phase N (<phase title>). Cover all 10 sections from the playbook
(goal, inputs, SQL, types, code, validation, advisor expectations, rollback, risks, gate).

Read-only — do NOT execute migrations, do NOT modify any code or doc outside your phase-plan
file. Your output is a plan that the main agent will review with the user before any execution.

## Output

Write to `docs/build-campaigns/<DATE>_<topic>/0N-phase-N-<topic>.md` with this header:

---
task: W2.N - Phase N Plan
agent: general-purpose
model: opus|sonnet
mode: build
phase: N
date: <YYYY-MM-DD>
status: complete|partial|blocked
gate: pending-user-approval
---
```

---

## W3 — Implementation (sequential per phase, parallel within a phase)

The main agent executes each phase. The user's approval gate must be honoured before any DB write / code merge.

### Per-phase execution loop

For each phase, in order:

1. **Present the phase plan** to the user — link the phase plan file. Highlight: SQL summary, files changed, expected validation output. Wait for explicit approval ("approve P1" or equivalent).
2. **Execute the writes** — `apply_migration` / file edits / type generation, in the order the plan specified.
3. **Run the validation queries** — copy-paste the validation block from the plan, capture output.
4. **Run advisors / lint / check-types** — capture output.
5. **Append "What actually ran" to the phase file** — full record of what was executed, what advisor/lint emitted, any deviations from the plan.
6. **Mark the phase file status** — `executed-ok` / `executed-with-deviations` / `blocked`.
7. **Pause for user confirmation** before proceeding to the next phase, especially for: money-adjacent phases, destructive phases (column drops), dual-write windows, anything the plan flagged as a risk.

### When parallelism inside a phase makes sense

Some phases have independent sub-tasks — e.g., updating 5 component files with the same pattern, or adding 5 typed row files in lockstep. The main agent can delegate these to parallel subagents **once the user has approved the phase plan**, each subagent given a narrow brief and an explicit output path. The main agent then reviews the subagents' edits before staging the next sub-task.

For DB phases (DDL, RLS, triggers, backfills), keep the writes in the main agent — the cost of an MCP `apply_migration` going wrong is much higher than the cost of doing it serially.

### W3 dispatch brief (when delegating sub-tasks)

```
You are an implementation subagent for phase N of the <feature> build campaign.

## Pre-existing files to read first

- docs/build-campaigns/<DATE>_<topic>/0N-phase-N-<topic>.md — the approved phase plan
- (specific sections of W1 files referenced by your scope)

## Your task

Implement <narrow scope, e.g. "the 3 React component edits in section 5b of the phase plan">.
Match the diffs in the phase plan exactly. If you find the plan's diff is wrong or incomplete
for the current code state, STOP and emit a "deviation needed" note in your output file — do
NOT improvise. The main agent will reconcile.

## Output

Write to `docs/build-campaigns/<DATE>_<topic>/0N-phase-N-<topic>.execution-<subtask>.md` with a
"Files Changed" section listing every path and a one-line summary per change. Do not write into
the main phase file — the main agent owns that.

You MAY edit code files in scope; do NOT edit anything outside the scope named above.
```

---

## W4 — Verification & vault log (sequential)

### W4 step 1 — Risk sweep (you do this, not a subagent)

Read every phase change-log file. Write `99-risk-sweep.md` per the template in [templates.md#risk-sweep](templates.md#risk-sweep). Cover:

1. **What shipped** — phase-by-phase status
2. **Surface coverage matrix** — every surface from W1 inventories: was it touched? is it consistent?
3. **Adjacent-feature regression risk** — every feature that shares a trigger, view, store, or component with anything we changed: was it verified?
4. **Post-deploy probes** — checkpoints for things that can only be verified after prod traffic
5. **Memory updates** — surprise discoveries, traps, conventions to capture
6. **Open items** — explicit deferrals to a follow-up campaign

### W4 step 2 — Vault-log entry

A single vault-log entry covers the whole campaign. Link the campaign folder. Per-phase migration filenames in the "Files Changed" table. P13 self-audit (if the project has one) lists every MCP call across all phases.

Template in [templates.md#vault-log](templates.md#vault-log).

### W4 step 3 — Memory entries

For each surprise / trap / convention surfaced in the risk sweep, create a memory entry per the project's memory system. Don't batch these — each lives as its own file with its own one-line index entry.

### W4 step 4 — Re-run docs (only if first build campaign on this project)

Create `docs/build-campaigns/README.md` from [assets/campaign-readme-template.md](../assets/campaign-readme-template.md) so future build campaigns know the convention. If P14 (or equivalent) already exists for audit-campaigns, extend it to cover both modes rather than adding a new rule.

---

## Subagent prompt skeleton (works for both modes)

When dispatching a subagent, this is the shape of every brief:

```
You are <task ID> of a <campaign topic> campaign (mode: <audit|build>).

## Pre-existing files to read first

- <path-1> — <one-line description>
- <path-2> — <one-line description>
- ...

## Your task

<concrete description of what to produce, with verifiable scope>

<key context the subagent needs — file paths, expected counts, hypotheses to verify>

## Output

Write to `<absolute path to NN-<task>.md>` with this header:

\`\`\`
---
task: <wave>.<num> - <Task Name>
agent: <subagent-type>
model: <opus|sonnet|haiku>
mode: <audit|build>
phase: <N>  # build mode only
date: <YYYY-MM-DD>
status: complete|partial|blocked
---
\`\`\`

Sections:
1. **Method**
2. **<task-specific section>**
...
N. **Recommendations** (audit) or **Approval gate** (build phase plans)
N+1. **Open questions**

<read-only designation — explicit for the mode/wave>
```
