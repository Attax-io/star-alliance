---
name: conquering-campaign
version: 1.13.1
description: "Multi-wave campaign skill for work too big to do in one pass. Two modes plus an extension sub-pattern — AUDIT (deep audits, doc-sync, reconciling docs with code/DB), BUILD (multi-phase feature builds, refactors, phased migrations touching >=3 surfaces), and EXTENSION (a build that extends a predecessor that shipped recently — skip W1, reuse the predecessor's primitives and prescan). Triggers on 'audit my app', 'build this feature', 'ship this refactor', 'phase this migration', 'proceed in application', or any work that must stay deployable at every step. Also triggers on extension phrases like 'extend [prior campaign] to X', 'roll out [pattern] to [other surface/route group]', 'apply [v1.X.Y] to [Z]'. The contract: in the planning phase Claude asks every question upfront (scope, approval cadence, reference patterns, success criteria, memory consultation); after the plan is approved Claude executes autonomously — BUT any phase that mass-renames imports across >15 sites, moves a top-level namespace, or alters a public component name still earns an automatic single-question approval gate (cheaper than rolling back 25+ files). Work runs in waves where each task uses the right tier — Ollama for free local pre-scans (with ANSI/thinking-trace stripping mandatory), Claude sonnet for mechanical scanning, Claude opus for security/RLS/synthesis. During execution Claude follows conformity (matches the app's existing UX patterns and docs), consolidation (extracts shared primitives instead of copy-pasting), self-verification (tsc + lint + preview at phase exit only — not after every Edit; mid-refactor breakage is expected), and an autonomous decision ladder (plan -> convention -> recommended -> safer-reversible -> stop only if irreversible+high-risk). Plans list candidate deletions, never committed deletions — orphan-proof via grep in the cleanup phase before any rm. When done, the skill self-cleans: deletes confirmed-dead code, updates the campaign plan's status to completed, writes the vault-log immediately, creates memory entries for surprise discoveries — without being prompted."
---

# Conquering Campaign

## Core philosophy

**Plan thoroughly. Then conquer without stopping.**

A campaign has two phases with a hard boundary between them:

1. **Planning phase** — Claude asks every question, surfaces every ambiguity, maps every surface, and gets full alignment. The user is actively involved. Nothing is assumed.
2. **Execution phase** — Claude works autonomously through the waves. It self-verifies after every phase (`tsc`, `lint`, preview). When it hits a fork, it follows the decision ladder instead of stopping to ask. When it finishes, it cleans up and logs — without being prompted.

The boundary is the moment the user approves the campaign plan. Before that: ask everything. After that: conquer.

**Conformity first.** Before writing anything, read how the app already does it. The project has documented patterns (FRONTEND.md, GENERAL-GUIDELINES.md, design tokens, component conventions), and the codebase has living examples. Claude must conform to the existing UX patterns, design language, and code conventions — not invent new styles. If 15 admin pages use a 3-line card row with `ListRowBase`, the 16th page uses it too. If the design system says `C.borderLight`, you don't write `#e5e7eb`. Conformity prevents the app from drifting into multiple visual and structural styles.

**Consolidation, not copy-paste.** When the campaign touches N pages/components with the same pattern, extract the shared primitive first, then compose it N times. Never copy-paste a block into multiple files. If a shared component already exists, use it. If it doesn't and 3+ consumers need it, create it. Every campaign should leave the codebase with fewer repeated patterns than it found.

**Self-cleanup is mandatory.** When the campaign is done:
- Dead code created by the campaign (replaced components, old shims) is deleted, not left behind
- The campaign plan's `status` frontmatter is updated to `completed`
- A vault-log entry is written immediately — not "at the end of the session," not "when the user asks"
- Memory entries are created for surprise discoveries
- `tsc --noEmit` and `npm run lint` pass clean

---

## Two modes

The same wave skeleton drives two distinct kinds of work. Pick the mode in Step 1; everything that follows specialises for that mode.

| Mode | Goal | Subagents | Final artefact |
|---|---|---|---|
| **AUDIT** | Reconcile docs with code/DB reality; produce evidence trail + staged doc rewrites | Read-only — write findings files only | Promoted source-of-truth docs + vault-log |
| **BUILD** | Ship a multi-phase feature or refactor that must stay deployable at every step | May write code/migrations/types per phase, under the campaign's approval cadence | Shipped feature + vault-log + risk sweep + tests passing |
| **BUILD · Extension** | A build that extends a predecessor that shipped recently (~30 days) and touches the same surface area — reuses the predecessor's primitives and findings | Same as BUILD, but W1 discovery is skipped or shrunk to a 1-task probe; W0 may be skipped entirely | Shipped extension + vault-log that links the predecessor + risk sweep that diffs against the predecessor's |

If the user only wants a quick check on one file, a single small bug fix, or a one-file feature, this skill is overkill — say so and offer a lighter-weight pass instead.

## When this skill triggers

**Audit mode:**

- "Audit my whole app", "deep dive on the codebase", "reconcile our docs with the code"
- After a graphify / dependency-graph run shows weakly-connected nodes, god-objects, or doc-vs-code drift
- Pre-release readiness check on a system the user cannot mentally hold in one piece
- Symptoms: same doc cites 4 different counts of the same thing; "headline X" claims contradict reality; ghost references to functions that don't exist; "we have 32 rules" but the rule list has 39 items

**Build mode:**

- "Build this feature", "ship this refactor", "implement multi-language X", "phase this migration", "I need this to land in stages" — where the work touches >=3 surfaces (schema, RLS, views, triggers, types, FE pages, admin UI, mutations, docs)
- Anything money-adjacent, anything that must remain deployable at every step, anything where a rollback would mean restoring from backup
- User explicitly says "proceed in application", "apply this in the app", "go build it" after a multi-phase plan has been laid out
- The phased-db-refactor or admin-page-builder skills have already shaped the design and the user now wants the execution wrapped in the same parallel/numbered/evidence-trail discipline

**Build · Extension sub-pattern:**

- "Extend [v1.7.3 admin-ui-unification] to the members panel and clients panel"
- "Apply the [card-list + sidebar] pattern to [another route group]"
- "Roll out [the migration we just shipped] to [another surface]"
- "Bump [campaign that just shipped] to also cover [X]"
- Recognise via: the user names or links a predecessor campaign that completed within ~30 days, or describes the new work as a propagation of recently-shipped primitives to new consumers

When you detect extension intent: run as BUILD, but in Step 2 populate the `predecessor:` frontmatter field, skip W1 discovery (the predecessor's risk sweep is the discovery), and consider skipping W0 entirely (see §0.6).

**Both modes:**

- The user wants to coordinate many parallel subagents on a multi-task investigation or implementation with a synthesis or risk sweep at the end

## What "good" looks like at the end

### Audit mode

1. There's a `docs/audit-campaigns/<YYYY-MM-DD>_<topic>/` directory containing 8-12 numbered findings files plus `99-synthesis.md`.
2. Every doc that needed to change has been **rewritten to a staged path** (`docs/staged/<doc>.md`), reviewed, then promoted.
3. Anything that couldn't be verified at audit time is captured as `<!-- CHECKPOINT: CHK-<id> -->` markers with a `CHECKPOINTS.md` registry of queries to run when the blocker clears.
4. A vault-log entry exists per the project's P8-style rule.
5. The user has a clear "what's left" list — usually a code-cleanup PR with concrete file/line targets, separate from the doc work.
6. The campaign plan's frontmatter reads `status: completed`.

### Build mode

1. There's a `docs/build-campaigns/<YYYY-MM-DD>_<topic>/` directory containing the master plan (`00-campaign-plan.md`), one numbered file per phase, and a final `99-risk-sweep.md`.
2. Each phase is independently deployable — the codebase compiles, the DB is consistent, tests pass at every phase boundary.
3. Approval gates have been honoured per the campaign's approval cadence (strict, autonomous, or hybrid).
4. Shared primitives were extracted before being composed into multiple consumers — no copy-paste.
5. Dead code replaced by the campaign (old components, legacy shims, deprecated wrappers) has been deleted.
6. A single vault-log entry summarises every phase, with links to the build-campaign folder.
7. Memory entries exist for surprise discoveries.
8. `tsc --noEmit` and `npm run lint` pass clean.
9. The campaign plan's frontmatter reads `status: completed` with all phases listed in `phases_completed`.
10. The feature ships.

---

## Step 0 — Resume check, environment detection & Ollama probe

Run this before Step 1, every time.

### 0.0 — Check for in-progress campaigns

Before starting anything new, check if there's an unfinished campaign on the same codebase:

```bash
# Look for campaigns with status: in-progress
grep -rl "status: in-progress" docs/build-campaigns/*/00-campaign-plan.md docs/audit-campaigns/*/00-campaign-plan.md 2>/dev/null
```

If found, present to the user: "There's an in-progress campaign: `<name>` (currently at phase `<current_phase>`). Resume it or start a new campaign?"

If resuming:
- Read the campaign plan to restore context (mode, phases, approval cadence, model assignments)
- Skip W0/W1/W2 — jump straight to the next incomplete W3 phase (build) or the next incomplete W1-W3 task (audit)
- The plan's `phases_completed` array tells you where to pick up

> **The frontmatter IS the crash-recovery log.** `status`, `current_phase`, `phases_completed`, and `phases_remaining` must be kept accurate after every phase completion — not as documentation hygiene, but because context compaction can occur mid-campaign and the only way to resume cleanly is from these fields. A campaign whose frontmatter is stale after compaction requires full context reconstruction from the vault-log. Update the frontmatter immediately after each phase closes.

If starting new: continue to Step 0.0.1.

### 0.0.1 — Same-session pivot detection

Before treating a fresh `/conquering-campaign` invocation as a new campaign, check whether the user is actually pointing at a *just-shipped* campaign and asking you to extend its scope inside the same session. This sits between §0.0 (resume an `in-progress` campaign), §Step 4 W4-discovered phases (defect surfaces *during* verification), and §5.8 (post-closure tweak *days* later) — none of which fire for the same-session mid-flight case.

**Detection signals — treat as a same-session pivot if ALL hold:**

- The previous vault-log entry on the affected surface was written **this session** (check `docs/vault-logs/` for the most recent entry matching the user's named surface)
- The user's framing names a deficit on the just-shipped campaign — phrases like "you still have work", "you missed", "doesn't match the UI", "lots more to do", "match X" with X being the campaign's reference page
- The previous campaign's plan was marked `status: completed` less than ~30 minutes ago (or in the same session — judge from conversation context)

**When this fires, do NOT run a fresh campaign:**

1. **Skip W0 entirely.** The previous prescan is still on disk; selected models are still cached in conversation context. Setting `w0_enabled: skipped — same-session pivot` is correct.
2. **Do NOT write a new `00-campaign-plan.md`.** Reopen the predecessor's plan: flip frontmatter `status: completed` → `status: in-progress`, push a new phase ID (e.g. `P3_same-session-pivot`) to `phases_remaining`.
3. **Append a phase file** with frontmatter `discovered_during: same-session-pivot` (mirrors the §Step 4 W4-discovered-phase pattern). The phase file's "Inputs" section names the screenshots / framing that surfaced the pivot.
4. **Skip W1 discovery.** The predecessor's discovery is still valid — the pivot is a *visual-conformity* or *scope-completion* miss, not new surface area.
5. **Run W3 + W4 normally** on the new phase. Phase-exit verification is the same.
6. **Update the existing vault-log entry in place.** Do NOT write a duplicate dated file. Add the new files to the existing entry's Files Changed list and tweak the description.

The pivot phase still goes through the standard W3 execution loop (including the new pre-execution gates from §Step 3) and the standard W4 verification (including the browser recipe — see Step 1.2 Q9).

If signals are mixed (e.g. user names a deficit but the predecessor is from yesterday, not this session), classify as post-closure tweak per §5.8 instead. The same-session pivot is a strictly tighter window with a strictly cheaper procedure.

### 0.0.2 — Reset stale TodoWrite from prior campaigns

Before any `W0`/`W1` work in a fresh-or-pivoted campaign, **reset the session todo list** if it carries items from an unrelated prior campaign in the same session. The TodoWrite tracker is session-scoped, not campaign-scoped — items from yesterday's "Phase 2: Create TasksActionBar" can survive into today's "Phase 1: Build TaskListRow" and the harness will keep nagging about them.

Decision rule:

- **Same-session pivot (§0.0.1 fired)** — keep the existing list; the new pivot phase appends to it.
- **Resume in-progress campaign (§0.0 found one)** — keep the existing list; resumption continues it.
- **Fresh new campaign (any other path)** — `TodoWrite` an empty list (or a list seeded with W0/W1 items for the new campaign) **before** the first Bash/Agent call. Inheriting "completed" items from a sibling campaign creates two failure modes: (a) the harness reminds you about stale items mid-flight, costing a turn each time; (b) genuinely-stale "in_progress" items mislead the next agent invocation about what's actually live.
- **Inline stub-extension fix following a closed campaign (per §5.8 classification)** — even though no new campaign opens, reset the todo list before the first Edit of the stub-extension turn. Stale `[completed] W4` items from the predecessor will otherwise trigger harness nags during the inline fix.

A single `TodoWrite` call costs nothing; cleaning the slate is the right default for a new campaign. See failure mode #29.

### 0.0.3 — Pivot-chain detection (3+ same-session pivots)

§0.0.1 handles ONE same-session pivot cleanly. When the user fires THREE OR MORE pivots into the same campaign in the same session, the per-pivot close-out overhead (flip plan `status: completed → in-progress`, append vault-log section, write phase file, run tsc/lint, flip back to completed) becomes the dominant cost. Worse, the campaign accretes scope past its original frame — the "Actions tab" campaign that ends with two new DB tables + a visibility audit is no longer the same artifact, but the plan / vault-log still pretend it is.

**Detection signals — treat as a pivot-chain when ALL hold:**

- §0.0.1 has fired ≥2 times already this session against the same predecessor campaign (i.e. you are about to add P3 or later as a pivot phase)
- The cumulative `phases_completed` array on the predecessor plan has more than 6 entries
- The newest pivot adds a *new surface area* not covered by the original plan (new DB schema, new component family, new audit target) — not just a visual-conformity miss on the original surface

**When this fires, do BOTH:**

1. **Switch to batched close-out.** Stop flipping `status: completed → in-progress → completed` per pivot. Mark the plan `status: in-progress` once at the start of the chain and leave it there until the user ends the session or explicitly closes the campaign. Phase files are still appended per pivot; the vault-log is still appended per pivot; but the plan frontmatter only flips at the end. Saves ~3 Edit calls per pivot.

2. **Offer a spin-off gate at the next pivot.** Before writing the next phase file, present a single `AskUserQuestion`:

   > "This is the Nth same-session pivot on `<predecessor>` — total phases now N+M, last K added new surface area. Spin off as a new campaign or keep chaining?"

   Options:
   - **Keep chaining (cheapest, recommended for small additions)** — continue as a pivot phase, batched close-out.
   - **Spin off as a new campaign (cleaner for big additions)** — close the predecessor at current state, open a fresh build campaign that names the predecessor as its predecessor, skip W0 (still same session).
   - **Stop and re-plan** — close the predecessor, do a fresh planning interrogation before next pivot.

   The gate fires once per chain (track via a single `pivot_chain_gate_fired: true` field on the predecessor plan's frontmatter), not on every pivot. The user's answer becomes a standing instruction for the rest of the chain.

**Why this is necessary:** without the gate, a campaign that started as "add Actions tab" can ship 11 phases including 2 DB tables and a visibility audit — and the artifact's vault-log entry will be 200+ lines summarising work that has nothing to do with the original campaign's name. Future readers can't find the visibility-audit deliverable because they wouldn't think to look in `2026-05-16_dev-tools-actions-tab/`. The spin-off gate forces an explicit user decision before the campaign drifts past recognisable shape.

**Anti-pattern:** silently chaining indefinitely. Every same-session pivot looks cheap individually; the cost is in artifact recognisability + re-find cost months later. See failure mode #37.

### 0.0.4 — Preview reachability probe (once per session, then cache)

Before the first phase that promises preview verification, probe whether the preview server is actually reachable end-to-end (page renders past the login wall). Many projects gate every route behind auth; the dev server happily returns 200 OK on the login redirect, the snapshot shows "Loading your workspace", and `preview_eval` times out — but the skill keeps adding "preview verification" to every phase's exit checklist and keeps marking it `deferred — login wall` over and over.

**Probe (run once per session):**

```bash
# 1. Confirm a preview server is alive
# (use preview_list if available; otherwise curl)
# 2. Hit a representative gated route + check body text
curl -s -m 5 http://localhost:3000/<gated-route> | grep -qE 'Loading your workspace|/login|Sign in'
```

If the body matches a login wall AND no test session / cookie / env-credential exists in the project (check `apps/web/.env.local`, `.env.test`, `PLAYWRIGHT_AUTH_STATE`, or similar), set in the campaign plan frontmatter:

```yaml
preview_verification: blocked-by-auth
preview_verification_reason: <one-line> (e.g. "no test session in env; routes redirect to /en/login")
```

When this flag is set:
- **Stop adding "preview verification" to phase exit checklists.** It will fail every time; pretending otherwise is theatre.
- **Replace with explicit code-only verification claim:** "tsc + lint clean; preview verification blocked by auth — code structure verified statically." Goes in the phase change-log + vault-log Verification section.
- **Do NOT spend tokens on `preview_eval` / `preview_snapshot` polling loops** for any phase. The probe already told you the answer.
- **Exception:** if a single phase ships an unauthenticated route (login page itself, public marketing page, /api/health), preview verification CAN run for that phase — note `preview_verification: partial` instead.

The probe replaces the implicit "preview always works" assumption with explicit evidence. Saves several `preview_eval` calls per phase × N phases in the campaign.

### 0.0.5 — Monorepo artifact-root resolution

Many projects have **two docs roots**: a workspace-level `/docs/` (where `CLAUDE.md`, `README.md`, and architecture docs live) and a nested `<app>/docs/` (where vault-logs, memory, and project-specific docs live). The skill's default paths (`docs/build-campaigns/`, `docs/audit-campaigns/`) silently resolve against the working directory, which may put the campaign-plan at workspace root while the project's vault-log convention puts the log under `<app>/docs/vault-logs/`. The result: the vault-log's wikilink to its own campaign-folder resolves from the wrong root and breaks.

**Probe (run once per session, before writing the campaign-plan file):**

```bash
# 1. Find every docs root in the project tree
find . -maxdepth 4 -type d -name docs 2>/dev/null | head -5

# 2. Find where vault-logs/ actually lives
find . -maxdepth 5 -type d -name vault-logs 2>/dev/null | head -3
```

**Resolution rule:**

| Scenario | `campaign_folder_root` | `vault_log_root` |
|---|---|---|
| Single docs root | `docs/` | `docs/vault-logs/` |
| Two docs roots, vault-logs/ exists only under `<app>/docs/` | `<app>/docs/build-campaigns/` (co-locate with vault-logs) | `<app>/docs/vault-logs/` |
| Two docs roots, vault-logs/ exists at both | Use the one named in `CLAUDE.md` / `AGENTS.md` P8 rule | Same |

**Record both roots in the plan frontmatter:**

```yaml
campaign_folder_root: lex_council/docs/build-campaigns/
vault_log_root: lex_council/docs/vault-logs/
```

When these are set, ALL campaign artifacts (campaign-plan, phase-files, prescan, risk-sweep) live under `campaign_folder_root` and ALL vault-log entries live under `vault_log_root`. Wikilinks between them use relative paths that resolve from a single common ancestor. Co-location is preferred — if both roots can be the same parent directory, use it.

**Anti-pattern:** writing the campaign-plan to workspace `docs/build-campaigns/` and the vault-log to `<app>/docs/vault-logs/` without recording the asymmetry. Future readers can't trace the link in either direction. See failure mode #46.

**CLAUDE.md / AGENTS.md location probe (extends §0.0.5).** The authoring-rule file (`CLAUDE.md` / `AGENTS.md`) frequently lives at **workspace root** even when planet-hub docs live nested under `<app>/docs/`. The skill's instinct is to look for it next to the nested docs (`<app>/CLAUDE.md`); that read fails silently when the file is actually at `./CLAUDE.md`. Probe both and record the location:

```bash
find . -maxdepth 3 -name "CLAUDE.md" -not -path "./node_modules/*" -not -path "./.next/*" 2>/dev/null
# Also check AGENTS.md
find . -maxdepth 3 -name "AGENTS.md" -not -path "./node_modules/*" -not -path "./.next/*" 2>/dev/null
```

Record in plan frontmatter alongside the docs roots:

```yaml
claude_md_path: CLAUDE.md             # workspace root (most common)
# OR
claude_md_path: lex_council/CLAUDE.md # nested
agents_md_path: <path>                # if AGENTS.md exists
```

When the C5 / portal-page / route-pattern blueprint sits in CLAUDE.md, P3 doc edits target the *recorded* path — not a guessed nested path. A failed `Read` on `<app>/CLAUDE.md` followed by a fallback to `./CLAUDE.md` is one wasted round-trip per campaign and a confusing error trail in the change log.

**Wikilink convention across docs-root split.** When `campaign_folder_root` and `vault_log_root` resolve to the SAME parent (co-located), wikilinks use bare filenames (`[[2026-05-16_topic]]`) and the Obsidian graph resolves cleanly. When they DIFFER (workspace + nested split), prescribe an explicit convention in the plan frontmatter:

```yaml
wikilink_convention: bare-filename    # default — works when both roots are co-located OR project uses an Obsidian vault that indexes recursively
# OR
wikilink_convention: relative-path    # when roots differ and Obsidian indexes only one; use `[[../build-campaigns/<date>_<topic>/00-campaign-plan]]` from inside vault-logs
```

Pick once at plan time and stick to it through W4. Mixed conventions inside the same artifact set break the graph in subtle ways that only surface on a future reader's Obsidian backlink panel.

**W4 write-time enforcement.** Frontmatter declares the convention but Edit/Write tools don't auto-validate. At §5.2 verification, scan every artifact for wikilinks and assert match against the declared convention:

```bash
# Find every [[...]] wikilink across campaign artifacts + vault-log entry
grep -nrE "\[\[[^]]+\]\]" \
  "${campaign_folder_root}/${MODE}-campaigns/${campaign_id}/" \
  "${vault_log_root}/${campaign_date}_${topic}.md" 2>/dev/null

# Then classify each:
# - bare-filename: [[foo]] or [[2026-05-17_topic]]
# - relative-path: [[../foo/bar]] or [[apps/web/components/Foo]]
# If declared convention is bare-filename but matches contain '/' → violation
# If declared convention is relative-path but matches lack '/' AND aren't sibling files → violation
```

Fix violations or downgrade the declared convention before campaign closes. The check costs one `grep`; it prevents the Obsidian graph from acquiring broken edges that future campaigns trip over.

### 0.1 — Detect your environment

Check how this skill was invoked:

- **Cowork** — `anthropic-skills:conquering-campaign` appears in your active skills list in the
  system context, and you are executing via the Skill tool.
- **Claude Code CLI** — you are reading this directly from a file path
  (`_skill-updates/conquering-campaign/SKILL.md` or `.claude/commands/conquering-campaign.md`),
  invoked via a `/` slash command or a direct file reference.

**If you are in Cowork: skip Steps 0.2-0.5 entirely. Set `w0_enabled: no` in the campaign plan
and go directly to Step 1.** Ollama runs locally on the user's machine and is not reliably
accessible from Cowork sessions. All model assignments fall back to the Claude-only tiers in the
[model assignment](#model-assignment) table.

**If you are in Claude Code CLI: continue with Steps 0.2-0.5 below.**

Takes under 30 seconds and can eliminate the majority of exploration-phase Claude token spend
across W1 and W2.

### 0.2 — Probe for Ollama

```bash
ollama list 2>/dev/null && echo "OLLAMA_OK" || echo "OLLAMA_UNAVAILABLE"
```

If `OLLAMA_UNAVAILABLE`: set `w0_enabled: no` in the campaign plan and jump straight to Step 1.
All model assignments fall back to the Claude-only tiers in the [model assignment](#model-assignment) table.

**W0 is mandatory when Ollama is available.** If `OLLAMA_OK`, the pre-scan MUST run — do not skip it because exploration already happened via Claude Explore agents during plan-mode. Reasons:

- Ollama runs locally — zero API tokens. Substituting it with a Claude `Explore` agent spends the same tokens as any Claude subagent.
- The pre-scan file (`00-w0-offline-prescan.md`) is the shared grounding document every W1+ subagent reads *first*. Without it, each subagent re-explores raw files independently — multiplying the token cost of the discovery work by the number of subagents.
- "We already ran Explore agents in plan-mode" is not a valid substitute. Those agents produced findings for the human; the W0 file is for the *subagents*. Run W0, write the file, and let W1 agents compress against it instead of starting from scratch.

### 0.3 — Check available RAM (Mac)

Use **available** memory (free + inactive + speculative), not just free pages. macOS keeps free
pages near-zero by design — it assigns them to caches that are instantly reclaimable. Dev servers
like Next.js fill these caches heavily, making "free pages only" reads misleadingly low.

```bash
sysctl -n hw.memsize | awk '{printf "Total: %.0f GB\n", $1/1073741824}'
vm_stat | awk '
  /Pages free/        { free=$3 }
  /Pages inactive/    { inactive=$3 }
  /Pages speculative/ { spec=$3 }
  END { printf "Available (free+inactive+speculative): %.1f GB\n", (free+inactive+spec)*16384/1073741824 }
'
```

This matches what Activity Monitor shows as "Available Memory" and is the correct signal for
whether Ollama can load a model — even with Next.js running.

### 0.4 — Auto-select W0 models

Pick models from what `ollama list` returned, using this priority table. Select one model per role —
don't ask the user, just pick the best available fit.

**On Apple Silicon (M-series) Macs, always attempt the model regardless of the available RAM
reading.** macOS unified memory aggressively reclaims inactive pages from caches (Next.js dev
server, browser tabs, etc.) the moment a new process requests memory. The "available" number
from Step 0.3 is a floor, not a ceiling — the real headroom is always higher. Only skip a model
if available RAM is below the hard minimum below, where macOS genuinely cannot reclaim enough.

| Role | Best fit (in priority order) | Hard minimum available RAM |
|---|---|---|
| **Code-pattern tasks** — grep, file listing, surface map | `qwen2.5-coder` (any size) -> any `qwen3` coder variant | 1 GB |
| **Summarization tasks** — multi-file docs, architectural overview | `qwen3:8b` -> `qwen3:14b` -> `qwen2.5-coder` as fallback | 1 GB (8b) / 4 GB (14b) |
| **Avoid for W0** | `deepseek-r1:*` — reasoning model, too slow for listing/grepping | -- |

If Ollama fails to load the model (error output, timeout >120s), fall back gracefully: set
`w0_enabled: no` and proceed to Step 1. Do not retry. Write the selected model names into the
resource map (included in the campaign plan header — see Step 2).

### 0.5 — Run the pre-scan (the main agent does this, not a subagent)

Call Ollama directly via the Bash tool. Write output to `00-w0-offline-prescan.md` in the campaign
folder. This is the only file W1 subagents are required to read before anything else.

**Always strip the spinner + thinking-trace noise.** Interactive shells capture `⠙ ⠹ ⠸` spinner
frames and `Thinking…/…done thinking` lines from chat-tuned models like `qwen3`. Pipe through a
sed/grep filter — otherwise the artifact is unreadable and forces a manual cleanup pass:

```bash
OLLAMA_NOSPINNER=1 ollama run --hidethinking <model> "<prompt>" 2>&1 \
  | sed -E 's/\x1b\[[0-9;?]*[a-zA-Z]//g' \
  | grep -vE '^(Thinking|Okay|\.\.\.done thinking)' \
  > <campaign-folder>/00-w0-offline-prescan.md
```

If your Ollama build does not support `--hidethinking`, the `grep -vE` still removes the trace
lines from the captured output.

**Audit mode pre-scan:**

```bash
# 1. Build a file list (adapt paths to the project)
find <project_root>/apps/web -type f \( -name "*.ts" -o -name "*.tsx" \) \
  | grep -v node_modules | grep -v .next \
  | xargs wc -l 2>/dev/null | sort -rn | head -60 \
  > /tmp/cc_prescan_files.txt

# Separately collect pattern counts
grep -rl "_js" <project_root>/apps/web/lib/query-configs/ 2>/dev/null | wc -l   # view consumers
ls <project_root>/apps/web/lib/mutations/ 2>/dev/null                            # mutation modules
find <project_root>/apps/web/app/\(admin\) -name "page.tsx" 2>/dev/null | wc -l # admin pages

# 2. Run the summarisation model
cat /tmp/cc_prescan_files.txt | ollama run <code-pattern-model> \
"You are analyzing a Next.js/Supabase codebase for an audit campaign.
Given the file list above, produce ONLY the following 4 sections in clean markdown:

## 1. File inventory
Top 30 files by size — name, line count, one-line purpose guess.

## 2. Pattern counts
- Views (_js suffix or _js in imports): <count>
- Mutation modules (lib/mutations/): <list names>
- Admin pages (in (admin)/ routes): <count>
- Type files (types/ directory): <count>

## 3. Surface map
For each main entity (infer from file names), list which files read/write it.

## 4. Gaps spotted
Anything obviously missing or inconsistent based on file names alone.

No preamble, no conclusion. Output only the 4 sections."
```

**Build mode pre-scan:**

```bash
# Collect files relevant to the feature area (narrow the scope)
find <project_root> -type f \( -name "*.ts" -o -name "*.tsx" -o -name "*.sql" \) \
  | grep -v node_modules | grep -v .next \
  | xargs grep -l "<feature_keyword>" 2>/dev/null \
  > /tmp/cc_prescan_feature_files.txt

cat /tmp/cc_prescan_feature_files.txt | ollama run <code-pattern-model> \
"You are analyzing a Next.js/Supabase codebase to help plan a feature build.
Feature: <feature description>
Files that mention it: (listed above)

Produce ONLY the following 4 sections in clean markdown:

## 1. Surface inventory
Every file likely touched by this feature — path, and one-line reason.

## 2. Existing patterns to follow
Find 1-2 existing mutation modules, components, or type files to model new code after.
Include the file path and what pattern it demonstrates.

## 3. Missing pieces
What clearly does not exist yet and needs to be created (inferred from the feature description
vs what's in the file list).

## 4. Inter-dependencies
What must be created before what — so phase ordering is correct.

No preamble, no conclusion. Output only the 4 sections."
```

Write the Ollama output to:
- Audit: `docs/audit-campaigns/<DATE>_<topic>/00-w0-offline-prescan.md`
- Build: `docs/build-campaigns/<DATE>_<topic>/00-w0-offline-prescan.md`

**Every W1 subagent brief must list `00-w0-offline-prescan.md` as its first pre-existing file to read.**
W1 subagents verify, deepen, and reason about the pre-scan — they do not re-explore raw files from scratch.

### 0.5.2 — Ollama REST API for W3 batch/structured tasks

`ollama run` is correct for prescan (one prompt → markdown). For W3 phases that require structured JSON output from Ollama (batch translation, fixture gen, value extraction), **prefer the REST API** — the CLI captures terminal ANSI spinner frames and thinking-trace lines that corrupt JSON parsing even with the `sed`/`grep` filter:

```bash
curl -s http://localhost:11434/api/generate \
  -d '{"model":"<model>","prompt":"...","stream":false,"think":false,"options":{"temperature":0.1}}'
```

The `stream: false` response returns `{"response": "<full output>", ...}` — clean, no ANSI, no spinner, no thinking trace. `think: false` is the REST equivalent of `--hidethinking` for qwen3 models (the flag is CLI-only; `think: false` is the REST API option).

**Format-example key collision.** When the prompt includes a JSON format example like `{"EnValue": {"ar": "arabic"}}`, smaller models (qwen3:8b and below) may treat the example key (`EnValue`) as a real output key — silently dropping the first actual value into the example slot. The fix: use a sentinel that cannot appear in real data:

```
Format: {"__EXAMPLE__": {"ar": "arabic translation", "fr": "french translation"}}
```

Also defensively remove the sentinel from the parsed result:
```python
result.pop("__EXAMPLE__", None)
```

### 0.5.1 — Validate prescan output before relying on it

Local Ollama models can produce **prompt-echo garbage** instead of real file insight — especially smaller models given long file lists or unfamiliar codebases. The output looks structured (it has the `## 1. ... ## 2. ...` headers your prompt requested) but the contents just paraphrase the prompt back without naming functions, props, line ranges, or specific patterns from the files. If W1 subagents cite this as "pre-loaded context," they're grounded in nothing.

**Quality gate** — before §0.6 / §Step 1, read the written `00-w0-offline-prescan.md` and ask:

| Signal | Useful prescan | Echo-back garbage |
|---|---|---|
| File inventory cites concrete line counts? | yes (`page.tsx — 1190 lines`) | no (`<file> — <line count>`) |
| Pattern counts include real names? | yes (`mutations: cases.ts, tasks.ts, ...`) | no (`<list names>`) |
| Surface map names actual entities? | yes (`tasks_s_js consumed by tasks/page.tsx, useTasksRealtime`) | no (`<entity>: <files>`) |
| Gaps section names a specific file or symbol? | yes | no — vague advice (`adjust styles to be consistent`) |

Mark the result in the campaign-plan frontmatter:

```yaml
w0_enabled: yes
w0_useful: yes|no
```

**If `w0_useful: no`:**
1. Do NOT instruct W1 subagents to "read the prescan as pre-loaded context" — they'll hallucinate against an empty signal. Tell them to read the listed files cold instead.
2. Note the failure in the plan's "Offline resources" section: `Prescan output was prompt-echo (model X on N files); W1 will read files cold.`
3. Do not retry — Ollama's outputs are not deterministically improvable from a longer prompt. Falling back to cold reads is cheaper than a re-run.

**Skip W0 entirely for builds touching <10 files.** The prescan's payoff comes from compressing W1 subagent token spend across many parallel reads. For a 3-5 file refactor, you (the main agent) will read every file in W1 anyway — the prescan adds a Bash + Read round-trip with no compression to amortize. Mark `w0_enabled: skipped — small-scope build (<10 files)` in the plan.

**Skip W0 for content-only campaigns where domain-specific analysis is already complete.** When the campaign surface is pure content files (i18n JSON, fixture seed files, config bundles) and the main agent has already run a comprehensive extraction (e.g. Python deep-flatten diff, grep matrix, CSV comparison), W0 adds no signal — it would only describe the file structure, which is already mapped. W0's value = "compress file-structure discovery for W1 subagents"; if the structure is fully known, the prescan compresses nothing. Mark `w0_enabled: skipped — content analysis already complete via <method>` in the plan.

This is not a contradiction with §0.2's "W0 is mandatory when Ollama is available" — that rule presumes the prescan produces real signal. When it doesn't, the cheaper path is honesty in the plan, not a ritual artifact. See failure mode #30.

### 0.6 — Skip W0 for extension campaigns

If the campaign extends a predecessor that completed within ~30 days **and** touches the same surface area, skip W0 entirely. The predecessor's `00-w0-offline-prescan.md` is the cheaper input. Set `w0_enabled: skipped — predecessor reused` in the new plan's frontmatter and reference the predecessor's prescan path in the plan's "Inputs" section.

Detection signals:
- The user explicitly references a recent campaign (e.g. "extend v1.7.3 admin-ui to members + clients", "roll out the portal-shell migration to clients")
- The new work names primitives that the predecessor created (`PortalPageShell`, `MemberListRow`, etc.)
- The new work is "apply X to N more surfaces" where X already exists

If in doubt — run W0. The cost is minutes, the benefit is grounding. But don't run it just because the skill says to; an extension's W1 subagents have stronger pre-loaded context from the predecessor than any fresh W0 can give them.

---

## Step 1 — Planning interrogation

This is the **only** time Claude stops to ask questions. After the plan is approved, Claude works autonomously until the goal is conquered.

### 1.1 — Consult project memory and past campaigns

Before asking the user anything, gather context silently:

1. **Scan `docs/memory/MEMORY-INDEX.md`** for entries relevant to the campaign scope (matching entities, surfaces, patterns). List the top 3-5 matches.
2. **Scan past campaign risk sweeps** (`docs/build-campaigns/*/99-risk-sweep.md` and `docs/audit-campaigns/*/99-synthesis.md`) for recurring traps on the same surfaces. Note any "lessons learned" or "open items" that apply.
3. **Read the project's general guidelines** for rules that constrain the campaign scope.

This pre-loading prevents repeating mistakes from past campaigns and ensures the interrogation asks informed questions.

### 1.2 — Mandatory interrogation checklist

Ask the user ALL of the following in a single batch. Do not scatter these across multiple exchanges — the goal is to exhaust every question now so execution never needs to stop.

**Scope questions:**

1. **What are we building / auditing?** (specific feature, surfaces, entities)
2. **Which surfaces does this touch?** (schema, RLS, views, triggers, types, FE pages, admin, mutations, docs — confirm or correct the pre-scan's inventory)
3. **Are there known constraints?** (must keep existing API shape, must not break X, time pressure, etc.)

**Authority questions:**

4. **Approval cadence** — how much autonomy does Claude have during execution?
   - **strict** — stop before every DB write, every destructive delete, every merge (money, schema, RLS, production data)
   - **autonomous** — single master review at the end; Claude runs all phases without stopping (FE refactors, styling, docs, non-destructive work)
   - **hybrid** — Claude runs green/amber phases autonomously, stops only at red phases (see risk tags below)
5. **Decision authority** — when two valid approaches exist mid-execution, should Claude pick the recommended option and log the decision, or stop and ask? (Default: pick and log.)
6. **Edge cases** — handle them or skip them? (Default: handle if green/amber, skip and CHECKPOINT if red.)

**Pattern questions:**

7. **Reference file or page** — is there an existing implementation to use as the pattern? (e.g., "Tasks page is the reference for admin pages")
8. **Consolidation targets** — are there existing shared primitives to use, or should new ones be extracted? (e.g., "use `ListRowBase`, don't create a new base component")

**Verification questions:**

9. **Success criteria** — what does "done" look like? (user describes the observable end state)
   - **Browser verification recipe** — for any user-facing outcome (UI, theme, auth, hydration, realtime, locale, i18n), write the smallest possible browser test that proves the outcome. Concrete shape: "set X in storage, navigate to URL Y, poll Z attribute / element / network call, expect value W within N ms." Example: `set localStorage[lex-theme]=dark, reload /en/login, poll document.documentElement.getAttribute('data-theme'), expect 'dark' within 1s`. These tests run at the W4 boundary; **the campaign is not "done" until they pass — this is outcome verification, not process completion.** A campaign that ships every planned phase but the user-facing outcome is broken is a failed campaign.
   - **For CRUD / editor / form / multi-step features, the recipe must include BOTH a render recipe AND an interaction recipe.** A page that loads without console errors is a strictly weaker check than the same trap from failure mode #20 — the interactive feature is the campaign's value, not the page chrome. Render-only verification of a CRUD page ships an unverified write path. Concrete two-part shape:
     - *Render recipe:* "navigate to URL Y, expect element Z visible, console clean"
     - *Interaction recipe:* "click cell at (row=N, col=M), type 'TEST_VALUE', click Save (or press ⌘+Enter), reload page, expect cell to display 'TEST_VALUE', click Revert, reload, expect cell to display original static value"
     The plan marks these phases with `verification_class: interactive` (see Step 2). Render-only verification is forbidden for `interactive` phases — a campaign that ships an editor where the user never clicked a cell at phase exit is shipping on faith. See failure mode #35.
   - **For accessibility / contrast / dark-mode / color-token campaigns, the recipe must include a WCAG contrast-ratio measurement step.** Token-swap fixes for "unreadable text" can ship combinations that are still below WCAG thresholds — e.g., `C.alwaysWhite` (#FFF) on `C.gold` (#C9A84C) computes to ~2.8:1, which still fails AA for normal text. Render-only verification (or "I can see the text on the screen") doesn't detect this. The plan marks these phases with `verification_class: contrast-measured` (see Step 2). Concrete probe shape:
     ```js
     const el = document.querySelector('<selector>')
     const cs = getComputedStyle(el)
     // Use a WCAG contrast helper (e.g. wcag-contrast npm, or DevTools accessibility panel)
     // Expect: ratio >= 4.5 (normal text), >= 3.0 (large text or UI components)
     ```
     The interaction recipe records the measured ratio in the change-log: "Active chip fg=#FFF on bg=#C9A84C → 2.8:1 FAIL AA. Switched fg to `colors.navy` (#0A1A3B) → 6.4:1 PASS AA." Without this gate, "fix unreadable text" ships "still unreadable but different colors." See failure mode #53.
10. **Verification method** — `tsc` + `lint` only, or also preview verification on specific pages? (Reminder: for the surfaces in Q9's recipe, preview verification is *required*, not optional — see § Self-verification loop.) **For content-only campaigns (i18n JSON, fixture files, config bundles), substitute a domain-specific gate** — JSON validity (`python3 -m json.tool` per file), deep-flatten diff (0 source-language values remain), and placeholder check (no `[DRAFT]` / sentinel markers remaining). Skip `tsc` + `lint` — they pass trivially and are ceremony without signal. Record `verification_class: content-only` in the plan frontmatter; see §2 full plan requirements.

**Past-campaigns context** (present to user, don't ask — just confirm):

11. **Memory hits** — "From project memory, these entries are relevant: [list]. I'll follow them."
12. **Past traps** — "From past campaigns on these surfaces, these traps were found: [list]. I'll avoid them."
13. **Session-level standing instructions inherited from earlier campaigns this session** — quote them verbatim and confirm they still apply. Examples: "work without stopping for clarifying questions", "always use ghost buttons going forward", "match Files page styling on every list view". These instructions silently propagate across campaigns in the same session and end up shaping execution without being recorded anywhere. Capture them in the new plan's `standing_instructions:` field (see Step 2). If the user wants them lifted for this campaign, they say so now; otherwise they're in force.

If the user's initial prompt already answers some of these, don't re-ask — acknowledge and move on. The point is that every item is covered, not that every item is a question.

### 1.3 — Infer what you can, ask what you must

Many campaigns are obvious: "migrate all admin pages to v2 sidebar" is clearly BUILD / autonomous / FE-only. Don't ask 12 questions when 3 will do. Present your inferences and let the user correct:

> "This is a BUILD campaign, autonomous cadence (pure FE, no schema). I'll use Tasks page as the reference pattern, extract shared primitives before composing, verify with tsc + lint + preview. The only thing I need to confirm is: [specific question]."

The interrogation is **thorough**, not **tedious**.

### 1.4 — Investigate-verb detection + symptom-reproduction gate

When the user's trigger prompt contains a **vague symptom verb** ("shows nothing", "doesn't work", "broken", "not loading", "looks weird", "wrong colors") mixed with imperative fixes ("make X", "change Y", "rename Z", "also fix W"), the planning phase MUST split into two parts:

**Part A — Investigation (mandatory before planning fixes):**

1. **Symptom reproduction.** Either:
   - Reproduce directly via preview/screenshot/console (if §0.0.4 says preview is reachable), OR
   - Ask the user for evidence: screenshot, console output, video, or a verbatim quote of what they see ("loading spinner stuck", "blank pane", "rows missing", "stats all zero", "error toast"). **One short question. Do not skip.**
2. **Diagnosis from observation, not from code.** Map the observed symptom to one of N hypothesised root causes. Code-only diagnosis ships fixes for the wrong cause when the observed symptom could resolve to multiple internal states (e.g., "kinds shows nothing" maps to ≥4 distinct internal states: empty `allKinds`, empty `filtered`, error toast, stuck loading spinner, JS exception). Without reproduction, you commit to one hypothesis from N.
3. **Confirm interpretation with the user before drafting fixes.** Brief: "I think the symptom is X (rendered cause: Y). Plan to fix is Z. Confirm?" One sentence each. The user takes 5 seconds; you save the cost of shipping the wrong fix.

**Part B — Fix planning** proceeds only after Part A is signed off.

**Default order when in doubt:** investigation-first. The cost of asking is ~30 seconds; the cost of fixing the wrong symptom is the campaign's full close-out + a follow-up campaign to undo and redo.

**Override:** when the symptom is precise and observable from code alone (`TypeError: Cannot read property 'foo' of undefined at line 42`, `MISSING_MESSAGE: admin.x.y`, a syntax error, a specific stack trace), Part A reproduction reduces to "git log + grep" — no user round-trip needed. Vague symptom verbs are the trigger, not investigation work itself.

**Trigger phrases that fire this gate:**

| Phrase | Why ambiguous |
|---|---|
| "X shows nothing" | Empty render, missing rows, stuck loading, error state, blank pane — 5+ internal states |
| "X is broken" | Anything from white screen to silently-wrong data |
| "X doesn't work" | Runtime error, network error, validation failure, hidden by CSS, gated by permission |
| "X looks weird" | Layout, color, spacing, font, density, alignment — all valid |
| "fix the audit too" | Unaddressed adjective from a predecessor's re-anchor block (also see §5.8) |
| "some stuff got messed up" / "things look off" + screenshot | Vague-symptom + scope-qualifier + image attachment — screenshot is evidence, not yet a diagnosis. Confirm interpretation before fixing. |

**Screenshot-with-vague-prompt sub-rule.** When the user attaches an image alongside a vague-symptom phrase ("some stuff got messed up", "this is wrong", "looks weird") with no specific element named, the screenshot is *one of many* potentially-broken things, not the diagnosis. Part A reduces to one short question with a hypothesis: "I see [specific observed defect]. Is that what you mean by 'messed up', or is there something else in the screenshot you want me to look at?" Confirmation before fix. The cost of guessing right is hidden; the cost of guessing wrong shows up as an extra round of "no, the other thing" tweaks.

See failure mode #44.

### 1.4.1 — Ambiguous-direction migration verb

When the user's trigger names a migration with a **directional adjective** (`horizontal/vertical`, `above/below`, `inline/block`, `modal/page`, `cascade/stacked`, `expanded/collapsed`, `light/dark` when applied to layout not theme) but does NOT clearly state which side is the keeper, the planning phase MUST fire a single-question gate confirming the direction of travel **before** scope is locked.

The directional adjective is **not self-evidently aligned with the current naming**. A component named `FooHorizontal.tsx` may render multiple layouts including the soon-to-be-canonical "vertical" mode; a prop named `layout="cascade"` may be the legacy mode while `layout="vertical"` is the keeper. A campaign that infers the keeper from filename or default-prop-value alone ships a 50/50 chance of pursuing the WRONG side and discovering the inversion only after writing the full plan.

**Trigger phrases:**

| Phrase shape | Why ambiguous |
|---|---|
| "Migrate from X-direction to Y-direction" | Direction-of-travel reads either way without context |
| "Kill the inline version" / "remove the modal version" | The named side may be the keeper if the other mode is the dead one |
| "Make all modals into pages" / "make all pages into modals" | Either side could be canonical depending on app's UX direction |
| "Replace the vertical layout" | Same — the replacement target could be in either direction |
| "Apply X to all" where X is one of two competing patterns | "All" doesn't resolve which is X and which is the legacy mate |
| "Match the new UI" where the "new UI" surface has multiple competing patterns | Surface itself contains both — direction needs explicit naming |

**The gate (single `AskUserQuestion` at plan time, BEFORE §1.2 scope confirmation):**

> "Confirming direction of travel — which is the keeper?
>   - Option A: [direction-1] is canonical; [direction-2] is removed
>   - Option B: [direction-2] is canonical; [direction-1] is removed"

Cost: 1 question. Saves the cost of a full re-plan + re-interrogation after Q1 of §1.2 reveals the inversion. The 2026-05-16 `files-stack-sidebar-canonical` campaign hit this trap: the agent assumed `layout="vertical"` was the OLD pattern (because the keeper file was named `FilesStackHorizontal`), wrote planning questions in that direction, and had to drop them and re-interrogate when the user's first answer inverted the assumption.

**Inversion-detected → re-interrogate.** If §1.2 Q1's answer inverts a core assumption (scope direction, intended keeper, primary actor) that was baked into the rest of the batched questions, drop the remaining Qs and fire a fresh second round on the now-changed core. Do NOT proceed with stale questions — they were drafted for a now-defunct scope and will mislead the user. Codify: "Q1-inverts-scope ⇒ Q2..QN are stale; re-batch on the corrected core."

**Distinction from §1.4 (vague-symptom verbs):** §1.4 fires on "X shows nothing"-style symptoms where the *internal state* is ambiguous. §1.4.1 fires on direction-named migrations where the *direction of travel* is ambiguous. Different ambiguity classes; both need a single-question gate before scope locks.

See failure mode #57.

---

## Step 2 — Design the campaign plan

Always write a campaign plan as the first artefact. Path depends on mode:

- **Audit:** `<campaign_folder_root>/audit-campaigns/<YYYY-MM-DD>_<topic>/00-campaign-plan.md`
- **Build:** `<campaign_folder_root>/build-campaigns/<YYYY-MM-DD>_<topic>/00-campaign-plan.md`

(Use the `campaign_folder_root` resolved in §0.0.5. Default is `docs/` when no monorepo split exists.)

### Express mode (`scope: small`) — for ≤5 files + ≤1 migration

When the campaign clearly touches ≤5 files AND ≤1 migration AND no architectural one-way door (no >15-site rename, no namespace move, no public API surface change), declare `scope: small` in the plan frontmatter and apply these explicit trims:

| Wave | Full mode | Express mode |
|---|---|---|
| W0 prescan | Run if Ollama available | Skip (already covered by §0.5.1 "<10 files") |
| W1 discovery | One subagent per surface | **Skip** — main agent investigates inline; investigation summary lives as `## Investigation` section in the plan |
| W2 phase plans | One subagent per phase | **Skip** — phase intent lives as `## Phases` section in the plan, one bullet per phase |
| W3 implementation | Per-phase `0N-phase-N-<topic>.md` file with change log | **Skip per-phase files** — append a single `## Execution log` section to the plan with one block per phase |
| W4 risk sweep | `99-risk-sweep.md` | **Skip** — single `## Risk sweep` section in the plan covering surface coverage + post-deploy probes |

**Express mode keeps mandatory:**

- §1.4 investigate-verb / symptom-reproduction gate when triggered (express mode does NOT skip diagnosis discipline)
- §3 W3 step 1.5d subagent reality-check (still verify schema claims via `information_schema` before migration)
- §3 W3 step 2a post-migration ground-truth check (still SELECT against live schema after `apply_migration`)
- §3 W3 step 2b RLS effective-access check (when phase changes a permission gate — see below)
- §3 W3 step 2.5 stale-override sweep when a visual default changed
- §5.3 vault-log with full P13 self-audit table
- §5.4 memory entries for surprise discoveries

**Required frontmatter for express mode shrinks to:**

```yaml
mode: build
scope: small
status: in-progress
approval_cadence: autonomous | hybrid | strict
standing_instructions: <inherited from session OR "none">
predecessor: <if applicable, else "none">
campaign_folder_root: <resolved per §0.0.5>
vault_log_root: <resolved per §0.0.5>
w0_enabled: skipped — small-scope build
preview_verification: <yes | blocked-by-auth | n/a>
current_phase: P1
phases_completed: []
phases_remaining: [P1, ..., W4]
verification_recipe: <one-line browser test from §1.2 Q9>
verification_class: render | interactive | contrast-measured | content-only
```

The `Per-task agent + model assignment` table, `Reference render structure` block, `Consolidation plan`, and `Cleanup plan — candidate deletions` sections become **optional** under `scope: small` — list them as "N/A — scope: small" if they don't apply. They are not skipped silently; the plan must say why.

**Scope-mode declaration gate (REQUIRED before W3 starts).** If the plan's `phases_remaining` skips W1 / W2 / per-phase files / 99-risk-sweep (full or partial), the frontmatter MUST contain `scope: small` OR `scope: medium` plus every required field listed for that scope tier. **Silent trims are forbidden.** This is the inverse of failure mode #45 (full pipeline on small builds): the v1.7.0 trim rules erode one campaign at a time if the discipline is "skip whatever feels right" instead of "declare the trim explicitly." Pre-execution check before §Step 3 W3:

```
phases_remaining excludes W1/W2/per-phase files? → frontmatter MUST have:
  scope: small | medium
  standing_instructions: <verbatim or "none">
  preview_verification: <yes | blocked-by-auth | n/a>
  verification_recipe: <one-line>
  verification_class: <render | interactive | contrast-measured | content-only>
If any field is missing → stop, add it, then proceed.
```

Future readers must be able to tell whether the missing W1/W2 sections were a deliberate trim or a sloppy plan. See failure mode #54.

**When NOT to use express (`scope: small`) mode:**

- Cross-cutting refactors (>5 files OR a base primitive change that cascades — consider `scope: medium` instead)
- Any DB phase that touches >1 table or >1 RLS layer
- Any phase with `forced_gate: true` (mass-rename, namespace move, public-component rename)
- Money-adjacent / data-backfill / column-drop work (any red-tagged phase)
- Multi-locale / multi-surface generation (translations, fixtures, seed data — see `generation_strategy`)

If you're uncertain whether the scope is small enough, default upward (small → medium → full). Express mode is a **declared** trim with explicit boundary; it isn't "I'll skip whatever I want." Failure mode #45 covers what happens when the skill runs the full pipeline on a 4-file fix — the user stops invoking the skill for small things because the ceremony exceeds the work.

### Medium mode (`scope: medium`) — for 6-20 files + ≤1 migration + no >15-site rename

When the campaign exceeds the ≤5-file express threshold but stays bounded — 6 to 20 files, at most one migration, no mass-rename across >15 sites, at most one single `forced_gate` (e.g. one public-component rename pre-approved at planning time) — declare `scope: medium`. The 2026-05-16 `files-stack-sidebar-canonical` campaign was the prototype: 1 component + 11 page consumers + 3 docs + 1 hook, 0 migrations, 1 forced gate (rename) satisfied at planning time. Express was too tight; full mode produced ceremony in excess of the work (W1 subagent fan-out on a fully-inventoried 15-file surface adds zero signal).

| Wave | Full mode | Medium mode |
|---|---|---|
| W0 prescan | Run if Ollama available | Skip if main agent can inventory inline (typical for <20 files) |
| W1 discovery | One subagent per surface | **Skip** — main agent inventories inline; lives as `## Scope inventory` section in the plan with explicit per-file table |
| W2 phase plans | One subagent per phase | **Skip** — phase intent lives as `## Phase list` table in the plan, one row per phase with risk tag + gate column |
| W3 implementation | Per-phase `0N-phase-N-<topic>.md` files | **Skip per-phase files** — change-log lives as `## Per-phase verification` section in the risk sweep, one block per phase |
| W4 risk sweep | `99-risk-sweep.md` | **Keep as standalone `99-risk-sweep.md`** — surface coverage matrix + post-deploy probes + grep proofs are too valuable to inline at 6-20 files; future readers grep the risk sweep first |

**Medium mode keeps mandatory** (same as `scope: small` + standalone risk sweep):

- §1.4 + §1.4.1 gates when triggered (vague-symptom + ambiguous-direction)
- §3 W3 step 1.5d subagent reality-check (still verify schema claims before migration)
- §3 W3 step 2a post-migration ground-truth check
- §3 W3 step 2b RLS effective-access check (when phase changes a permission gate)
- §3 W3 step 2.5 stale-override sweep when a visual default changed
- §Consolidation discipline rule 5 (N=3+ union-prop audit)
- §5.3 vault-log with full P13 self-audit table
- §5.4 memory entries for surprise discoveries
- **Standalone `99-risk-sweep.md`** (this is the only artifact medium keeps that small drops)

**Required frontmatter for medium mode:**

```yaml
mode: build
scope: medium
status: in-progress
approval_cadence: autonomous | hybrid | strict
standing_instructions: <inherited from session OR "none">
predecessor: <if applicable, else "none">
campaign_folder_root: <resolved per §0.0.5>
vault_log_root: <resolved per §0.0.5>
w0_enabled: skipped — medium-scope build, inventory done inline, no W1 fan-out
preview_verification: <yes | blocked-by-auth | n/a>
current_phase: P1
phases_completed: []
phases_remaining: [P1, ..., W4]
verification_recipe: <one-line browser test from §1.2 Q9>
verification_class: render | interactive | contrast-measured | content-only
```

**When NOT to use medium mode:**

- >20 files in scope (escalate to full)
- >1 migration (escalate to full)
- Mass-rename across >15 sites (forced gate cascade — escalate to full; the single-gate budget is one rename, not a class of them)
- Any phase with multiple `forced_gate: true` markers (one rename pre-approved at planning is fine; multiple one-way-doors needs full mode discipline)
- Money-adjacent / data-backfill / column-drop work
- DB phase touching >1 table or >1 RLS layer

Medium mode's expected artifact set: `00-campaign-plan.md` + `99-risk-sweep.md` + vault-log entry + memory entries. No per-phase files, no W0 prescan, no W1/W2 subagent dispatch. The plan carries the inventory; the risk sweep carries the verification. See failure mode #59.

### Micro mode (`scope: micro`) — for ≤2 files + ≤10 lines changed + no new artifacts

When the work is a **single-property tweak** — change one CSSProperties value, swap one icon, fix one boolean, rename one local variable — even express mode is ceremony in excess of the work. Declare `scope: micro` and apply the deepest possible trim:

| Wave | Express mode | Micro mode |
|---|---|---|
| `00-campaign-plan.md` | Single inline plan file | **Skip — the conversation IS the plan.** Decision recorded in the vault-log instead. |
| `00-w0-offline-prescan.md` | Skip | Skip |
| W1-W3 artifacts | Inline `## Investigation` / `## Phases` / `## Execution log` | **Skip — no artifact files.** |
| W4 risk sweep | Inline `## Risk sweep` | **Skip** |

**Micro mode keeps mandatory:**

- §1.4 investigate-verb / symptom-reproduction gate (even a one-line fix can target the wrong cause — diagnose from observation, not from the user's guess)
- tsc + lint pass at exit (no exceptions; the CI pipeline doesn't know the work was "small")
- §0.0.4 preview verification at completion (the change IS observable by definition — one screenshot or one DOM read)
- §5.3 vault-log entry — P8 is non-negotiable regardless of scope. The entry can be 5 lines (`Files Changed` / `Why` / no P13 needed if no MCP calls), but it must exist.

**When `scope: micro` applies:**

- ≤2 files touched
- ≤10 lines changed (net)
- No new files created
- No migrations, no DDL, no DB writes
- No new exports, no public-API changes, no rename of any symbol used in >1 file
- Trigger phrase shape: "fix this", "the X is broken", "change Y to Z", "active state wrong color", any imperative paired with a named property and an observable defect

**When `scope: micro` does NOT apply (escalate to express or full):**

- The fix requires reading 3+ files to understand the system before writing
- Any structural change (new component, new state, new conditional render branch)
- The user said "investigate" without naming the specific defect — that triggers §1.4 Part A first, then re-classify based on what the investigation finds
- Any change to a *shared primitive's* default — a 4-line tweak to `Button.tsx` cascades; not micro

Failure mode #50 covers the v1.8.0 gap this closes: a single-property fix routed through express mode still produces a plan file + vault-log entry + memory entries — the plan file alone exceeds the patch's size. Micro mode collapses the artifacts to the vault-log only.

### Full plan requirements

Use the templates in [references/templates.md](references/templates.md). The plan must include:

- **Mode** — `audit` or `build`
- **Status frontmatter** — `status: planning` (updated to `in-progress` when W3 starts, `completed` when W4 finishes)
- **Trigger / context** — why this campaign
- **Predecessor (extension mode only)** — `predecessor: <YYYY-MM-DD>_<topic>` frontmatter field naming the campaign this one extends. The risk sweep diffs against the predecessor's; the new W1 may be skipped entirely. Without this field, the campaign is treated as a fresh BUILD, not an extension.
- **Standing instructions (REQUIRED when running ≥2 campaigns in the same session)** — `standing_instructions:` frontmatter field that quotes verbatim every session-level instruction from prior campaigns that still applies (e.g. `"work without stopping for clarifying questions" — set 2026-05-15 in tasks-ui-consolidation campaign`). The approval-cadence field captures the general posture; this field captures the *user's exact words* so nothing is paraphrased into a different meaning. If empty, write `standing_instructions: none — first campaign of session OR all prior instructions explicitly lifted by user`. A campaign that silently inherits an instruction is a campaign whose execution rules are invisible to the next reader. See failure mode #31.
- **Approval cadence** — `strict`, `autonomous`, or `hybrid` (see Step 1). This determines which phases Claude runs without stopping.
- **Offline resource map** — the W0 probe result: Ollama availability, detected models, free RAM, selected W0 models, `w0_enabled: yes|no`
- **Lessons from memory / past campaigns** — relevant memory entries and past risk-sweep findings, listed by ID/title
- **Wave structure** — W0 + 4 waves with task lists
- **Per-task agent + model assignment** — this table is **mandatory**. Every planned Agent call listed with task ID, subagent type, model, and effort. A campaign plan without this table cannot be approved:

  | Task ID | Wave | Run by | Model | Effort | Output file |
  |---|---|---|---|---|---|
  | W0 | Bash (main agent) | ollama / qwen2.5-coder | fast | `00-w0-offline-prescan.md` |
  | W1.1 | Agent / general-purpose | opus | deep | `01-w1-discovery-schema.md` |
  | W1.2 | Agent / general-purpose | sonnet | standard | `02-w1-discovery-frontend.md` |
  | ... | ... | ... | ... | ... |

- **Phase list with risk tags** (build mode) — every phase gets a risk tag:

  | Tag | Meaning | Under `autonomous` | Under `hybrid` | Under `strict` |
  |---|---|---|---|---|
  | **green** | Reversible, FE-only, additive, no data changes | run | run | gate |
  | **amber** | Schema additive, new views, new RLS, new indexes | run | run | gate |
  | **red** | Destructive DDL, data backfill, money-adjacent, column drops | gate | gate | gate |

  Example phase table:

  | # | Phase | Risk | Surface | Gate? |
  |---|---|---|---|---|
  | P1 | Extract shared primitives | green | FE | no (autonomous) |
  | P2 | Migrate finance pages | green | FE | no |
  | P3 | Add scoring column | amber | schema | depends on cadence |
  | P4 | Backfill historical scores | red | data | always |

- **Reference render structure (REQUIRED for any campaign where the user named a reference component / page to mirror visually).** A labelled-line extraction of the reference's rendered JSX — not its imports, prop types, or signature. The block specifies: outer wrapper (e.g. `TableShell + flex column gap:6`), each named line ("Line 1: rowNum + headline/slug + spacer + Edit/View actions"; "Line 2: status chip + author + category + date"), hover/transition (e.g. `border-color C.borderLight → C.navy, 0.15s ease`), and the leaf primitive(s) being composed (e.g. `<ListRowBase>`, `<MemberListRow>`, `<TableShell>`). If this block is empty for a visual-conformity campaign, the plan **cannot be approved** — fill it from the reference's full render function before presenting the plan. See failure mode #26.
- **Verification recipe (REQUIRED for any campaign that touches the FE surface).** The smallest browser test that proves the user-facing outcome from Step 1.2 Q9. Concrete shape: "navigate to URL Y, take screenshot, expect rendered card row with `border-radius: 8` and headline+slug on line 1." Lives in the plan; re-runs at every phase-exit per §Self-verification loop step 5. A campaign that ships green `tsc + lint` without this recipe is shipping on faith. See failure mode #20.
- **Verification class (REQUIRED for every phase).** Each phase declares one of:
  - `verification_class: render` — FE phase verified by page render + console check
  - `verification_class: interactive` — mandatory for CRUD / editor / form / multi-step features; must include both a render recipe AND an interaction recipe (click, type, save, reload, confirm persisted). A campaign that ships a Save button no one clicked at phase exit is shipping on faith. See failure mode #35.
  - `verification_class: contrast-measured` — accessibility / dark-mode / color-token phases; must include WCAG contrast-ratio measurement, not just render. See failure mode #53.
  - `verification_class: content-only` — pure content-file campaigns (i18n JSON, fixtures, config bundles); skip `tsc + lint + preview`; verify via JSON validity + deep-flatten diff + placeholder-free check. Record the specific verification commands run in the change-log.

  Phase-exit verification that doesn't match the declared class is incomplete — the phase is not done.
- **Generation strategy (REQUIRED for any phase that generates >5KB of artifact content — translations, fixtures, seed data, message bundles).** The plan stores the **spec**, not the content: target path(s), source-of-truth locale or seed, expected key count or row count, sampling rule. The plan declares `generation_strategy: deferred-parallel-subagents` so W3 spawns parallel subagents per file that write directly to disk. The post-phase change-log records the file sizes shipped + a 5-10 line diff sample per file as evidence — not the full content. Pre-drafting 80KB of JSON inline in the plan defeats readability and blows past the planning subagent's response budget; this happens often enough on i18n / fixture / seed campaigns to deserve a named pattern. See failure mode #34.

  **For i18n / translation campaigns, the generation_strategy section MUST include two sub-sections:**

  - *Intentionally-EN values* — values that must NOT be translated even if they appear in non-EN locale files. Common categories: brand names, numeric stats, email/phone format placeholders, technical abbreviations (CSV, ID, MFN, etc.), URLs. Enumerate them; the final verification script uses this list as an exclude list.
  - *Valid cognates per locale* — words/phrases identical in English and the target language (French: Finances, Documents; Spanish: Error, No). The EN=locale verification check flags these as suspicious. Pre-documenting them prevents false-positive rework and accidental over-translation of domain abbreviations.

  Without both sections, the verification produces false alarms on cognates and risks translating technical abbreviations into locale-specific strings that break component logic.

  **Unicode normalization in translation lookups.** When building an EN→translated dict from Ollama output, normalize both keys and file values to canonical Unicode form before comparison — a file written with `ensure_ascii=True` may contain literal `…` (6 chars) where the Ollama output has the actual `…` (1 char U+2026), causing silent lookup misses:

  ```python
  import unicodedata
  def norm(s): return unicodedata.normalize('NFC', s)
  # Build: translations[norm(en_val)] = translations
  # Lookup: translations.get(norm(file_val))
  ```

  Always write locale JSON files with `ensure_ascii=False` to prevent future mismatch. If literal `\uXXXX` sequences exist in a source file, fix them with a one-time pass before building the lookup dict.
- **Consolidation plan** — which shared primitives exist, which need extraction, which copy-paste hotspots to eliminate. This section prevents the campaign from creating more duplication than it resolves. **N=3 alarm:** if the campaign is about to create the 3rd hand-rolled implementation of a recurring shape (e.g. a 3rd `*ListRow.tsx` clone after `FileListRow` + `BalanceListRow`), the consolidation plan must explicitly identify the base primitive that should compose all N — not produce the Nth clone. See failure mode #27.
- **Cleanup plan — *candidate* deletions, not committed deletions.** List legacy files / components / shims that *may* become orphan after the migration, but mark each one as **"verify in Phase N cleanup"**. The grep-proof in the cleanup phase is what authorizes the `rm`, not the plan. (Most plans over-promise deletions — chrome migrates but inner content stays load-bearing. A "delete X" promise in the plan that gets walked back in the change-log is a credibility leak; phrase it as "candidate for deletion if grep proves zero live consumers post-migration".)
- **Forced single-question gates.** Mark every phase that mass-renames imports across >15 sites, moves a top-level namespace, or alters a public component name with a `forced_gate:` field. These phases get an automatic `AskUserQuestion` (with your recommendation as the first option) even under `autonomous` cadence. A 30-second question prevents hours of rollback churn from a one-way-door decision.

  **`forced_gate:` state machine (enumerated values):**

  | Value | Meaning | When |
  |---|---|---|
  | `pending` | Gate identified at plan time but not yet asked | Default initial value when the phase is added to the plan |
  | `true` | Gate ACTIVE — must fire `AskUserQuestion` before execution | Equivalent to `pending` but more readable; either works |
  | `satisfied — pre-approved in planning Q<N>` | Gate question was asked AND answered during the §1.2 / §1.4.1 planning batch, so it does NOT need to re-fire at W3 execution | When the planning interrogation explicitly surfaced the rename/namespace/component-name change with the same options the W3 gate would have presented. **The recommendation as the first option + the same risk framing must match** — otherwise the gate is NOT pre-satisfied and must still fire at execution time. |
  | `false` | Phase no longer qualifies as a forced gate (scope reduced; sites count dropped below threshold) | Rare — usually means the phase should drop the `forced_gate` field entirely. |

  Pre-execution check before §Step 3 W3: read each phase's `forced_gate:` value. If `pending` or `true`, fire the AskUserQuestion. If `satisfied — …`, log the deferral reason in the phase change-log and proceed. If the satisfaction citation doesn't match a real planning Q, treat as `pending` and fire the gate. The state machine prevents both (a) silent skipping ("the user already approved this somewhere") and (b) duplicate gating ("I'll ask again to be safe" — burns user trust on every campaign).

  **Flip-point rule (who flips `pending → satisfied`).** The planning agent flips the field IMMEDIATELY after the matching AskUserQuestion resolves — not the W3 agent at execution time. Reason: planning is when the question's framing + options are freshest; the W3 agent reading a flipped state minutes-to-hours later may have lost context on whether the planning Q actually matched the W3 gate. Citation format: `satisfied — Q "<question header text>" → "<answer label>"`. Examples:

  ```yaml
  # Good — verbatim header + answer label
  forced_gate: satisfied — Q "Rename" → "`FilesStack` (Recommended)"

  # Bad — Q-number is non-canonical across multi-batch interrogations
  forced_gate: satisfied — pre-approved in Q2

  # Bad — paraphrased ≠ verbatim; W3 agent can't audit match
  forced_gate: satisfied — user approved the rename earlier
  ```

  Q-numbering across multiple `AskUserQuestion` calls in the same planning session is non-canonical (batches restart at 1; recovery from a re-batch loses ordering). Header text + answer label is canonical because both come straight from the tool call's `question` + selected `label`.
- **Success criteria** — what "done" looks like for this specific run
- **Campaign tracking frontmatter:**

  ```yaml
  status: planning
  current_phase: null
  phases_completed: []
  phases_remaining: [P0, P1, P2, P3, P4, P5]
  ```

Show the plan to the user and get explicit approval before dispatching subagents. The plan is cheap to revise; a wave of 5 subagents — or a migration that runs against the DB — is not.

**Once the user approves the plan, execution begins. Claude does not stop until the goal is conquered** (or a red-gated phase requires approval under the campaign's cadence).

---

## Step 3 — Execute the four waves

The full wave-by-wave playbook (including prompt templates for each subagent type, for both modes) lives in [references/wave-playbook.md](references/wave-playbook.md). Read it when you're ready to dispatch subagents.

### Audit mode waves

| Wave | Mode | What it does | Typical task count |
|------|------|--------------|---|
| **W0 — Offline pre-scan** | sequential (main agent, Bash) | Probe Ollama, auto-select models, run pre-scan, write `00-w0-offline-prescan.md` | 1 (skip if Ollama unavailable) |
| **W1 — Foundation reality** | parallel | Reconciles each major doc against actual code/DB — reads W0 output first | 4 |
| **W2 — Deep structural** | parallel (some depend on W1.1) | Dead code, API route mapping, permission/RLS parity, hierarchy/scoping | 4 |
| **W3 — Domain depth** | parallel | God-object decomposition, realtime/subscription map, mutation layer | 2-4 |
| **W4 — Synthesis** | sequential | Master synthesis -> staged doc rewrites -> promotion -> vault-log -> cleanup | 1 (or 1+N if you parallelise the rewrites) |

### Build mode waves

| Wave | Mode | What it does | Typical task count |
|------|------|--------------|---|
| **W0 — Offline pre-scan** | sequential (main agent, Bash) | Probe Ollama, auto-select models, run pre-scan for the feature area, write `00-w0-offline-prescan.md` | 1 (skip if Ollama unavailable) |
| **W1 — Discovery** | parallel (read-only) | Inventory the surfaces this feature touches. One subagent per surface. **Reads W0 output first. Findings only — no writes.** | 3-5 |
| **W2 — Phase plans** | parallel (with cross-references) | One subagent per planned phase. Each produces a phase plan: SQL drafts, type drafts, code sketches, risks, rollback. **Plans only — no execution.** | 4-8 (matches phase count) |
| **W3 — Implementation** | **sequential per phase, parallel within a phase** | Execute each phase under the [self-verification loop](#self-verification-loop). Update campaign tracking after each phase. | 4-8 |
| **W4 — Verification & cleanup** | sequential | Risk sweep, vault-log, memory updates, dead-code cleanup, campaign status -> completed | 1 |

### Critical rules for both modes

- **Wait for the previous wave's hard dependencies before launching the next.** W4 always waits for everything. In build mode, W3 phases run sequentially because P2 may depend on P1.
- **Inside a wave, run tasks in parallel** — same message, multiple Agent calls. Sequential dispatch defeats the parallelism that makes the campaign tractable.
- **Respect the approval cadence.** Under `autonomous`, only stop at red-gated phases. Under `hybrid`, stop at red. Under `strict`, stop at everything. Under no cadence should Claude stop for green phases — that's the whole point of the planning interrogation.

If a subagent comes back blocked (DB unreachable, MCP timing out, missing input), don't abandon the wave — fall back to a tractable proxy (migration files, git history, AST output) and emit `<!-- CHECKPOINT: CHK-<id> -->` markers for anything that can't be verified now. See [references/checkpoint-pattern.md](references/checkpoint-pattern.md).

### W3 execution loop (build mode)

**Pre-W3 checklist box (tick before first Write of each phase).** Condensed version of §1.5a-1.5e gates. The agent ticks each box mentally (or in the phase change-log) before any Edit/Write:

```
Pre-W3 phase checklist:
□ 1.5a Reference render-structure block filled in phase file (UI phases only)
□ 1.5b N=3 alarm cleared — sibling-clone grep done; base-primitive identified if N≥3 (UI phases)
□ 1.5b' N=3+ union-prop audit done — consumer grep for each value of any ≥3-value union prop (consolidation phases)
□ 1.5c Reference file re-Read THIS turn (cached mental model is unreliable; cost = 1 Read call)
□ 1.5d Schema claim verified via information_schema / pg_policies / pg_views (DB phases only)
□ 1.5e Themable-token semantic audit done (theme / dark-mode / contrast phases only)
□ forced_gate value read for this phase; if pending/true, AskUserQuestion fired
□ phase risk tag (green/amber/red) checked against campaign cadence
```

Skip checkboxes that don't apply (e.g. 1.5d on a pure-FE phase) but mark them N/A explicitly in the phase change-log so future readers see the gate was considered, not silently skipped.

For each phase, in order:

1. **Check the cadence.** If this phase's risk tag requires a gate under the campaign's cadence, present the phase plan and wait for approval. Otherwise, proceed.
1.5. **Pre-execution gates (UI campaigns only).** Run these *before* the first Write call of the phase. They are cheap, they enforce disciplines that v1.3.0 left as prose:

   **(a) Reference render-structure gate.** If this phase writes a UI component intended to mirror a reference, the phase file's `## Reference render structure` block must be filled in. If empty, **stop and fill it now** by Reading the reference's full render function and extracting the labelled lines (outer wrapper → Line 1 → Line 2 → hover/transition → leaf primitives). Writing the target component without this block is failure mode #26. The block must name what the reference *renders*, not what it imports.

   **(b) Consolidation grep gate (N=3 alarm).** If this phase creates a new `*ListRow.tsx` / `*Card.tsx` / `*Row.tsx` / similar shape-recurring file:

   ```bash
   # How many sibling implementations of this shape already exist?
   find apps/web -name "*ListRow.tsx" -o -name "*ListCard.tsx" 2>/dev/null | wc -l
   # Are there base primitives we should be composing instead?
   grep -rn "ListRowBase\|MemberListRow\b" apps/web/components/ apps/web/app/ 2>/dev/null | head -10
   ```

   If `≥2` siblings exist and the planned file doesn't import a base primitive, **stop**. Re-read CLAUDE.md / FRONTEND.md for the expected base component name. The Nth hand-rolled clone is failure mode #27 — extract / compose, don't copy.

   **(c) Re-read the reference immediately before drafting.** The reference file may have been edited during this session (by the user, by a parallel agent, or by an earlier phase of this campaign). A cached mental model is unreliable. Cost: one Read call.

   **(d) Subagent reality-check gate (DB campaigns only).** If this phase's migration body depends on a W1 structural claim — "column X lives on table T", "RLS policy Y references column Z", "view V joins on column W" — verify with `information_schema` (or `pg_policies` / `pg_views`) **before** writing the migration SQL:

   ```sql
   -- Where does column X actually live?
   select table_schema, table_name
   from information_schema.columns
   where column_name = '<X>' and table_schema = 'public';

   -- Does the RLS policy actually reference what W1 said?
   select policyname, qual, with_check
   from pg_policies
   where tablename = '<T>' and schemaname = 'public';
   ```

   If the result disagrees with W1's claim, **stop and update the plan before writing migration SQL**. Cost: one `execute_sql` MCP call; benefit: avoids a failed `apply_migration` followed by debugging from an error message. W1 subagents reliably mis-locate columns when a table has been renamed mid-history or when the column conceptually "belongs" to one entity but lives on a permission-overlay table (`is_programmer` lives on `admin_perms`, not `council_members`). The current skill's failure mode #8 covers audit-mode hypothesis verification; this is its build-mode mirror — don't write the migration on faith of a W1 structural claim. See failure mode #32.

   **(e) Themable-token semantic audit (theme-rollout / dark-mode / contrast-fix campaigns only).** Before the first Write call of any phase that fixes foreground/background color usage, **scan the project's design-token file for named-vs-bound mismatches**:

   ```bash
   # Find tokens whose name reads as a static color literal but binding is a CSS var
   grep -nE "(navy|white|black|grey|gray|red|blue|green|gold|amber):\s+['\"]var\(" \
     apps/web/lib/design-tokens.ts packages/md/src/tokens/*.ts 2>/dev/null
   ```

   For each match, document in the campaign plan's "Inputs" section (or the phase file's preamble):

   | Token | Binding | Light value | Dark value | Intended role | Safe-replacement for misuse |
   |---|---|---|---|---|---|
   | `C.white` | `var(--color-secondary-bg)` | `#FFFFFF` | `#282828` | background surface | `C.alwaysWhite` for true-white foregrounds |
   | `C.navy` | `var(--color-primary)` | `#0A1A3B` | `#D6D2CA` | primary text/border | `colors.navy` (flat hex) for always-dark on gold |

   Then the same phase should grep the codebase for **every** use of the misused token as a foreground (where the token name read as "white text" but the binding becomes a dark foreground in the alternate theme):

   ```bash
   grep -rn "color:\s*C\.white\b\|color={C\.white}" apps/web/ packages/ --include="*.tsx"
   ```

   Fix all matches in a **single mass-edit phase**, not one-at-a-time as bug reports arrive. Without this audit, the same root cause (e.g. `C.white = var(--color-secondary-bg)` reached for as if static) re-surfaces as N sequential follow-up fixes — the `2026-05-16` dark-mode chain hit this 13+ times across 9 files in 3 sequential campaigns before the pattern was named. See failure mode #52.

2. **Execute the writes** — file edits, migrations (if gated and approved), type generation.

   **2a. Post-migration ground-truth check (DB phases only).** When `apply_migration` returns `{"success": true}` — *especially* after a prior failed attempt that was fixed and retried — do NOT mark the phase complete on the success response alone. Run a SELECT against the live schema to confirm the change landed as specified:

   ```sql
   -- Table exists?
   select table_name from information_schema.tables
   where table_schema = 'public' and table_name = '<table>';

   -- Columns + types match the migration?
   select column_name, data_type, is_nullable from information_schema.columns
   where table_schema = 'public' and table_name = '<table>';

   -- RLS enabled + policies present?
   select policyname, cmd, qual from pg_policies
   where schemaname = 'public' and tablename = '<table>';

   -- View has security_invoker = true?
   select c.relname, c.reloptions from pg_class c
   join pg_namespace n on n.oid = c.relnamespace
   where n.nspname = 'public' and c.relname = '<view>' and c.relkind = 'v';
   ```

   Record the SELECT results in the phase change-log as evidence. A migration that "succeeded" but applied the wrong RLS qual or dropped `security_invoker = true` on view rewrite is a silent failure the success response can't distinguish from a clean apply. See failure mode #33.

   **2a-RLS. Effective-access check (REQUIRED when this phase changed an RLS policy, grant, or view-security attribute).** Verifying the policy's `qual` text matches the migration body proves the *text* updated — it does NOT prove the *effective access* changed as intended. Effective access depends on policy permissive/restrictive flag, other policies on the same table, grants, RLS enabled flag, and `security_invoker` propagation. Run a representative SELECT under a simulated authenticated context for both the OLD and NEW gate:

   ```sql
   -- Sample test: confirm the new gate admits users it should
   set local role authenticated;
   set local request.jwt.claim.sub to '<test-user-uuid-matching-NEW-condition>';
   select count(*) from <view_or_table>;
   -- Expect: > 0 (this user should now see rows)

   -- Sample test: confirm the new gate still excludes users it should
   reset role;
   set local role authenticated;
   set local request.jwt.claim.sub to '<test-user-uuid-NOT-matching-any-condition>';
   select count(*) from <view_or_table>;
   -- Expect: 0 (this user should still see nothing)
   ```

   Record both counts in the phase change-log. A policy whose `qual` text reads `(notifications_vap = true OR is_programmer = true)` could still fail to admit an `is_programmer` user if a restrictive policy on the same table blocks them, or if the view wrapping the table is `security_invoker=false` (definer mode bypasses RLS entirely). Text-matches-intent is necessary; effective-access-matches-intent is sufficient. See failure mode #47.

   **2b. Phase atomicity for orthogonal access-control changes.** When a single phase bundles ≥2 changes that touch **different access-control layers** — RLS policies + grants, grants + view-security, view-security + definer functions, etc. — assign each change a sub-phase ID (`P1a`, `P1b`) and run §2a + §2a-RLS independently per sub-phase. Different AC layers have different risk profiles and different revert costs; collapsing them into one migration makes the ground-truth check ambiguous ("did the security_invoker change land? did the RLS policy land? did both? in what order?").

   The migration itself can stay atomic (one `apply_migration` call); the *verification* must enumerate each layer. Record per-sub-phase evidence:

   ```
   P1a — RLS policy change on n_kinds_audit: qual=<new>, effective-access counts: programmer=N, non-admin=0
   P1b — View security on n_kinds_stats: reloptions=[security_invoker=false], aggregate count=19 (all kinds)
   ```

   If sub-phases are independently approvable (e.g., one is amber, one is red), the migration body splits into ≥2 `apply_migration` calls and each goes through its own approval gate. See failure mode #47.
3. **Stale override sweep** — *mandatory when this phase changed the visual default of a shared primitive* (button bg/fg, icon color default, font size default, border style, layout direction, etc.). For each property whose effective default just changed:

   ```bash
   # Enumerate every consumer override of the property whose meaning just changed
   grep -rn "<PropName>=" apps/web/ --include="*.tsx" | grep -v "<PrimitiveFile>:"
   ```

   Classify each result against the **new** default:

   | Classification | Meaning | Action |
   |---|---|---|
   | **Still correct** | Override matches the new design intent (e.g. `iconColor={C.red}` for a flag-active state) | Accept |
   | **Stale against old default** | Override was correct against the OLD default and is now broken (e.g. `iconColor={C.white}` was for a navy-filled button, now invisible on a transparent ghost button) | **Fix in this same phase** — do not defer |
   | **Newly redundant** | Override now equals the new default — clean noise | Remove the override |

   Also grep for **stale header comments** describing the old design facts: `grep -rn "<old design fact>" apps/web/ --include="*.tsx"` (e.g. "32×32 navy background", "white icons", "filled style"). Header comments that lie are worse than absent ones — they mislead the next reader. Update or remove.

   Without this sweep, the cascade leaks out as N follow-up one-shot turns after the campaign closes (see failure mode #23). **The phase is not done until every stale override is reclassified.**
4. **Run the [self-verification loop](#self-verification-loop)** — `tsc`, `lint`, preview if applicable.
5. **Update the campaign tracking** — add this phase to `phases_completed`, update `current_phase`, update `phases_remaining`.
6. **Append "What actually ran" to the phase file** — full record of what was executed, deviations, autonomous decisions made. If the stale override sweep found anything, list every fixed override with file:line and the before/after value.
7. **Continue to the next phase.** Do not stop between green phases. Do not ask "shall I proceed?" — the plan was approved, proceed.

---

## Step 4 — Synthesise (audit) or Verify (build)

### Audit mode — Master synthesis

Read every findings file. Write `99-synthesis.md` yourself (don't delegate — synthesis benefits from reading all the evidence with a single mind). Structured as:

1. **TL;DR** — drift one-liner, real bugs, security findings, latent design gaps
2. **Critical findings** (security & defence-in-depth)
3. **Real bugs** (worth fixing soon)
4. **Doc ghosts** (referenced but don't exist)
5. **Doc orphans** (in doc but not in reality)
6. **Undocumented reality** (in code but not in doc)
7. **Architecture patterns to document**
8. **Per-doc rewrite checklist**
9. **Code cleanup checklist** (separate PR; not this campaign's job)
10. **Open questions for the user**
11. **Re-audit cadence**

### Build mode — Risk sweep & verification

Read every phase change-log file. Write `99-risk-sweep.md` yourself. Structured as:

1. **TL;DR** — what shipped, post-rollout watch items
2. **Per-phase verification** — for each phase: ran-as-planned vs deviations, autonomous decisions logged, verification results
3. **Surface coverage matrix** — every surface from W1: was it touched? is it consistent? **Every "✓" needs a concrete observation behind it (screenshot, polled DOM read, network call) — not an intent. Status assigned without evidence is a credibility leak.**
4. **Conformity & consolidation audit** — visual/pattern/token consistency with existing app; which shared primitives were extracted; which copy-paste was eliminated; any remaining duplication; any conformity violations found and fixed
5. **Risk-area sweep** — adjacent features that could regress: verified or not?
6. **Post-deploy probes** — checkpoints for things that can only be verified after prod traffic
7. **Memory updates** — surprise discoveries, traps, conventions to capture
8. **Open items** — explicit deferrals to a follow-up campaign

#### W4-discovered phases

Browser verification at W4 sometimes surfaces a real defect that the original plan didn't anticipate (e.g., a hydration bug that no compile-time check catches; a regression on a route the discovery wave missed; a pre-existing bug that the migration exposed). When this happens, do **not** silently inline-fix the bug into a previous phase's change-log — that lies about the campaign's history and hides a real lesson.

Instead, formalise the fix as a **discovered phase**:

1. Allocate a new phase ID with a `discovered` suffix or marker — e.g., `P5_w4-fix`, `P6_discovered`. Add it to `phases_remaining` in the campaign-plan frontmatter.
2. Write a phase file (`05-phase-5-w4-fix-<topic>.md`) with the same structure as a planned phase — context, plan, change log — and stamp it with `discovered_during: w4` in the frontmatter so it's distinguishable from original-plan phases.
3. Run the discovered phase through the **full self-verification loop** (tsc + lint + browser recipe). If it touches the same outcomes as the original plan, re-run all of W4's browser recipes — not just the new one.
4. The vault-log entry lists discovered phases under a distinct header (e.g., `### W4 verification fixes`) so future readers immediately see "these were not planned; they were caught by browser verification" rather than reading them as part of the original scope.
5. The risk sweep's TL;DR explicitly mentions "+N W4-discovered phases shipped" — don't bury it.
6. Memory entry: if the defect was caused by a generic pattern (e.g., SSR/client hydration mismatch with Zustand), file a memory entry about the pattern, not just this instance.

**The campaign closes only after every discovered phase passes verification.** A campaign with 5 planned phases shipped + 2 discovered phases unfixed is still in-progress.

#### Mid-execution scope discovery — notification threshold

When a W3 phase discovers *additional scope* beyond the plan (more files, more keys, more surfaces), apply this decision table before autonomously expanding:

| Discovery size | Under `autonomous` | Under `hybrid` | Under `strict` |
|---|---|---|---|
| ≤5 files / ≤20 keys / same surface | Proceed silently; log in phase change-log | Proceed; note in change-log | Gate |
| 6–50 files / 21–200 keys / same surface | Proceed; append new phase to plan; log prominently in change-log | Gate: one-line note "Found X, proceeding" + user can interrupt | Gate |
| >50 files / >200 keys / any new surface | Gate regardless of cadence | Gate | Gate |

"Proceeding silently" means the change-log records the discovery — not that the user is unaware after reading it. The vault-log's phase list should show the discovered phase explicitly ("+P6 discovered mid-execution: 888 [DRAFT] attributes"). A user who reads the vault-log should never be surprised by what shipped.

---

## Step 5 — Cleanup & close

This step is **mandatory and automatic**. Claude does not wait to be asked.

### 5.1 — Delete dead code (grep-first, then `rm`)

If the campaign replaced components, removed legacy patterns, or deprecated wrappers, work from the **candidate-deletions** list in the plan (Step 2). Do **not** trust the list — most plans over-promise:

1. For each candidate: `grep -rn "<ComponentName>\|from.*<filename>" apps/web/ --include="*.ts*" | grep -v "<filename>:"` — confirm zero live consumers (the `grep -v` filters out the file's own declaration)
2. Re-categorise each candidate as **confirmed-orphan** or **still-load-bearing**. Most "I'm sure this is dead now" candidates are still load-bearing — chrome migrated but inner content stayed.
3. Delete only the confirmed-orphan files
4. Run `tsc --noEmit` to confirm nothing breaks
5. In the change-log, record the grep proof + final delete list. If candidates moved to "still-load-bearing", note them as deferred to a follow-up campaign (don't silently drop them).

### 5.2 — Final verification

Phase-exit verification runs at the **end of every phase**, not just at campaign close. If the project enforces `--max-warnings 0`, unused-import sweeps are part of every phase exit — a single lint pass at campaign close is too late to triage 9 surprise warnings across 9 files.

```bash
npm run check-types --force   # must pass clean; --force bypasses stale Turbo cache on first run per phase
npm run lint                  # must pass clean (zero warnings if the project enforces it)
```

> **Turbo cache note:** If the project uses Turbo for `check-types`, the first run after a phase edit must include `--force` (e.g., `npx turbo run check-types --force`) to get an uncached baseline. A cached "pass" from before your edits is not a verification result. If the forced run surfaces errors in files you didn't touch, grep + `git log` to confirm they predate the campaign — treat them as `CHK-<id>` items, not campaign failures.

> **Runtime error provenance (preview verification).** When preview verification surfaces a console error or warning, do NOT silently ignore it as "pre-existing" and do NOT auto-attribute it to the campaign. Run the provenance check first:
>
> ```bash
> # Did our diff introduce the error string, or did it predate us?
> git diff <campaign-start-sha>..HEAD | grep -F '<error-substring>'
> # If absent: pre-existing. If present: campaign-introduced.
> ```
>
> | Result | Provenance | Action |
> |---|---|---|
> | Error string absent from campaign diff | **Pre-existing** | `spawn_task` to flag for separate resolution, continue the phase |
> | Error string present in campaign diff | **Campaign-introduced** | **Phase blocker** — fix before marking phase complete |
>
> This is the runtime mirror of the Turbo cache note above: that one separates pre-existing *compile* errors from campaign-introduced ones; this one separates pre-existing *runtime* errors from campaign-introduced ones. See failure mode #36.
>
> **Untracked-files caveat.** Both the git-diff provenance check above and the common `git stash → re-run check → git stash pop` pattern presume the affected files were **tracked** at campaign-start. When the edited files are untracked (long-running feature branch with `.gitignore`-d build artifacts, scaffolding before first commit, or recently-added files not yet staged), `git stash` skips them by default and the test compares identical states (no counterfactual). Either pass `-u` (`git stash -u` includes untracked) or rely on `npx turbo run <task> --force` + manual file inspection of the offending file (grep + read). Without `-u`, an untracked-only edit set makes the stash-test silently meaningless. See failure mode #56.

**Preview verification timing.** If the project has preview tools (live dev-server snapshot), run them at **phase exit only** — never after each Edit. During an in-flight mass refactor the build is intentionally broken between Edits; preview verification then is meaningless. The PostToolUse hook reminder fires often; ignore it until the phase's Edits + type-check + lint are all clean.

**Scoped-lint pattern (when project-wide lint surfaces an unrelated WIP warning).** Under `--max-warnings 0`, a project-wide `npm run lint` may fail because of an unrelated in-progress refactor in a file your campaign never touched. Provenance (§5.2 above) confirms the warning is pre-existing. To prove that the campaign-touched surface is clean, run lint scoped to the file list this campaign actually edited:

```bash
# Compute the campaign-touched file list from git status
git status --short | awk '$1 ~ /^M+$/ || $1 == "M" {print $2}' > /tmp/touched.txt

# Then run ESLint scoped to those files (skip with the project's max-warnings setting)
cd apps/web
npx eslint --max-warnings 0 $(cat /tmp/touched.txt | grep "^apps/web/" | sed 's|^apps/web/||')
echo "EXIT=$?"
```

`EXIT=0` proves the campaign-touched surface is clean independent of the pre-existing warning. Record both: full-project lint result (with provenance note for the failing line) AND the scoped result. Phase verification passes when the scoped result is clean; the project-wide warning rides as a `CHK-<id>` item in the risk sweep. Codifies what the 2026-05-16 `files-stack-sidebar-canonical` campaign did organically; see failure mode #61.

If type-check or lint fails on campaign-touched files, fix the issues. Do not leave the campaign with a broken build on its own surface.

### 5.3 — Vault-log entry

Write immediately — not "later," not "when asked." One vault-log entry per the project's P8 rule:

- `docs/vault-logs/YYYY-MM-DD_<campaign-topic>.md`
- All phases listed with files changed
- P13 self-audit (if Supabase MCP was used)

**Campaign-date convention (artifact internal consistency).** Use the date the campaign **started** for every artifact filename and INDEX row, even if the campaign spans a midnight rollover. The campaign folder, vault-log filename, INDEX.md row, memory entry references, and the start-date stamps inside the plan all use the same YYYY-MM-DD. The rationale: future readers find the campaign by topic + start-date; splitting an artifact set across two dates (folder dated D1, vault-log dated D2) makes the set unreadable as a whole — the wikilinks resolve, but the *narrative* fractures. The skill's system context updates the current-date marker during long sessions; ignore that for artifact dating purposes. If a session is *resumed days later* via §0.0 (`status: in-progress` found on disk), the start-date is still the original start — not the resume date.
- Link to the campaign folder

**Same-session pivots update the existing entry, never duplicate.** When §0.0.1 fired and the work added a phase to an already-shipped campaign in the same session, edit the existing dated entry — add the new files to Files Changed, refine the description. A duplicate `YYYY-MM-DD_<same-topic>.md` would split the campaign's history across two files for no benefit.

**Incidental fixes.** If a pre-existing lint warning, dead import, or trivially-broken line is in a file the campaign is *already editing for in-scope reasons*, and the fix is ≤3 lines, fix it and note under an `## Incidental fixes` heading in the vault log (file + before/after). If the fix is larger or in a file the campaign wouldn't otherwise touch, CHECKPOINT it (`CHK-<id>`) and defer — drive-by cleanups are how campaigns silently bloat. The discipline: in-scope file + tiny fix + named in the log is acceptable; anything else is scope-creep.

### 5.4 — Memory entries

For each surprise discovery, trap, or new convention surfaced in the risk sweep:

- Create a memory entry per the project's memory system
- Each is its own file with its own one-line index entry
- Don't batch them

**Explicit memory triggers** (write the entry whenever any of these fire during a campaign — do not wait for the W4 risk sweep to catch them):

| Trigger | Memory entry pattern |
|---|---|
| Any lint rule fires under `--max-warnings 0` and reveals a project-enforced pattern | `feedback_<rule-shortname>.md` with the failing snippet, the rule name, and the corrected pattern |
| A user correction names a project-specific convention not in the docs | `feedback_<topic>.md` with the corrected behavior and the file path where the convention lives |
| A surprise discovery in W1 (a primitive exists that wasn't in the prescan, a sibling exists that wasn't on the inventory) | `discovery_<topic>.md` with how to find it next time |
| A grep result that contradicts the user's mental model ("I thought we only used X in one place — actually 7 files use it") | `inventory_<topic>.md` capturing the real consumer count |

Zero-tolerance lint rules in particular are worth memorizing immediately — they are project laws that the docs may not state explicitly, and they will trip again.

### 5.5 — Update campaign status

Edit the campaign plan's frontmatter:

```yaml
status: completed
current_phase: done
phases_completed: [P0, P1, P2, P3, P4, P5]
phases_remaining: []
```

### 5.6 — Promotion gate (audit mode only)

Create `docs/staged/` and write each rewritten doc there first. Promotion gate:

- [ ] All checkpoint markers either resolved or explicitly accepted
- [ ] Diff reviewed by the user
- [ ] Surgical edits applied to meta-docs
- [ ] Empty `staged/` directory removed after promotion

### 5.7 — Re-run docs (first campaign only)

If this is the first campaign of its type on this project, create `docs/build-campaigns/README.md` and/or `docs/audit-campaigns/README.md` from [assets/campaign-readme-template.md](assets/campaign-readme-template.md).

### 5.8 — Post-closure tweak detection

A campaign is rarely "done" in the moment the vault-log lands. Within ~7 days of closure, the user often returns with short imperative tweaks that touch the same surface(s). The skill must classify these **before** acting — treating every tweak as a fresh imperative is what produces multi-hour follow-up cascades and the "we shipped this last week but it's still being polished" smell.

**Detection signals** (the new request arrives while the predecessor's vault-log entry is the latest one on the touched surface, OR the user explicitly references it):

| User phrase | Underlying signal | Treat as |
|---|---|---|
| "Fix X too" / "while you're at it" / "also Y" / `..` trailing imperative | **Unaddressed adjective from the predecessor's Step 4.5 re-anchor block.** The user's framing wasn't fully covered. | Re-read the predecessor's re-anchor. Identify which adjective the new request maps to. Then act. |
| "Make X match Y" where Y is a surface the predecessor already touched | Single-reference blindness (failure mode #18) bit the predecessor's W1 sibling sweep — Y was a sibling that was missed | EXTENSION mode — skip W1, reuse the predecessor's prescan, run a focused sibling-sweep on Y |
| 1-3 line cosmetic tweak to a single primitive | Stub-extension | Handle inline, but **append the tweak to the predecessor's `99-risk-sweep.md` under a new §10 "Follow-up tweaks"** section — never silent |
| 4+ files, or a new surface, or "match X across all of these" | Mini-extension | Re-open the predecessor as EXTENSION (per §0.6) — `predecessor: <YYYY-MM-DD>_<topic>` frontmatter, skip W1, run the stale override sweep + sibling sweep |

**The "fix X too" rule** specifically means: the user is naming an adjective from the original framing that Step 4.5 marked `addressed` but actually wasn't. Before acting, open the predecessor's risk sweep and re-read the re-anchor block. The fix lives where the original framing pointed, not where the new prompt points.

**Hard rule: every post-closure tweak that touches the campaign's surface gets logged against the campaign** — either in the existing risk sweep's §10 (for stub-extensions) or as a re-opened EXTENSION (for everything bigger). A tweak that gets handled in a one-shot turn with no link back to the predecessor is the campaign equivalent of a silent write — it bypasses the discipline that produced the original artifact.

**When to refuse the one-shot framing.** If the user fires a tweak that would touch >3 files or a new sibling not in the predecessor's W1, do not handle it inline even under "work without stopping for clarifying questions." Instead: in a single response, classify the tweak as a mini-extension and proceed with EXTENSION mode (skip the planning interrogation; the predecessor's plan is the input). The user gets the work done autonomously; the framework stays intact.

**Stub-extension chain visibility.** When a mini-extension (re-opened EXTENSION campaign) follows one or more stub-extensions (inline-fix vault logs) on the same surface in the same session, the new campaign's `predecessor:` frontmatter points to the **last full campaign**, not to the intermediate stub-fix vault logs (which have no campaign artifact). This is correct, but the chain becomes invisible: a future reader tracing `predecessor: A → new campaign B` skips the intermediate stub-fix log entirely. Mitigation — the new EXTENSION plan's "Trigger / Context" section must list every intermediate same-session vault log on the affected surface:

```markdown
## Trigger / Context

[Original trigger description]

Prior touches on this surface in same session (not in any campaign):
- [[docs/vault-logs/YYYY-MM-DD_<stub-fix-topic>.md]] — ad-hoc fix between predecessor and this campaign
```

One-line addition per stub-fix; the chain becomes reconstructable from the new plan alone. See failure mode #55.

---

## Step 6 — Reflection-pass procedure (post-campaign skill upgrade)

After a campaign closes (status: completed, vault-log filed, memory entries written), the user MAY ask: *"reflect on this session and propose skill upgrades against the current SKILL.md version."* This is a distinct workflow from §Step 5 (close) and from running a new campaign — it produces a v(N+1) skill diff, not a vault-log entry or new artifact.

Codifying the procedure prevents instinct-drift. Two prior sessions did this ad-hoc; the steps below are the canonical sequence.

### 6.1 — Inputs

Gather before reflecting:

1. **The closed campaign's full artifact set** — `00-campaign-plan.md`, all phase files (or per-phase blocks in the risk sweep if `scope: medium`/`scope: small`), `99-risk-sweep.md`, vault-log entry, memory entries written.
2. **Current `SKILL.md`** — read the actual file on disk, not your context's cached version (the user may have upgraded the skill mid-session).
3. **The session transcript or summary** — what disciplines did the agent invent on the fly that the skill doesn't currently codify? What stops / re-plans / re-interrogations happened?

### 6.2 — Walk procedure (per-phase + per-discipline)

For each W3 phase AND each W4-discovered phase AND each §5.8 post-closure tweak in the closed campaign:

| Question | If yes → action |
|---|---|
| Did the agent stop / re-ask / re-plan? | Candidate for a new pre-execution gate (§Step 3 W3 step 1.5*) or a new §1.4-style trigger gate |
| Did the agent invent a new procedure (e.g. `git mv + atomic Write`)? | Candidate named pattern (§Subagent dispatch named patterns) |
| Did a discipline fire that the skill names but the call site re-derived the procedure? | Candidate for a quick-ref / checklist box |
| Did a frontmatter field get used informally (e.g. ad-hoc `forced_gate: satisfied — pre-approved`)? | Candidate for enum codification in §Step 2 |
| Did the agent hit a project-shape that §0.0.5 didn't probe? | Candidate for §0.0.5 extension |
| Did W4 verification surface a project-wide vs scoped contention? | Candidate for §5.2 / §5.3 extension |

Output of the walk: a flat list of candidate findings, each tagged with `proposed-section` + `severity`.

### 6.3 — MINOR vs PATCH classification rule

Once findings are listed, classify each. The split prevents bundling everything into one large release.

| Classification | Trigger | Goes in |
|---|---|---|
| **MINOR** (v1.X.0) | Introduces a NEW top-level section, a NEW discipline class, OR a NEW failure mode that names a class of trap (not a specific instance of an existing class) | Next `1.X.0` bump |
| **PATCH** (v1.X.Y, Y>0) | Clarifies an existing section, adds a frontmatter enum value, names a sub-pattern of an existing pattern, extends an existing probe, adds a checklist of an existing prose discipline | Next `1.X.Y` bump |
| **MAJOR** (v2.X.0) | Reorganises the wave structure, changes the campaign-folder layout, removes a frontmatter field that was load-bearing, or otherwise breaks an existing campaign's artifact set | Rare; never bundle with anything else |

Heuristic: "would a future reader looking up the discipline need a new heading to find it?" → MINOR. "Would they find it under an existing heading once they know to look?" → PATCH.

### 6.4 — Same-session release-split rule

When one campaign produces both MINOR-class and PATCH-class findings (typical), ship as two sequential releases: `v1.X.0` (MINOR — paradigm) immediately followed by `v1.X.1` (PATCH — clarifications) in the same reflection turn. Each gets its own version-history entry. The split keeps the MINOR entry readable (paradigm-level only) and the PATCH entry concrete (small frontmatter / procedure clarifications). Both entries cite the same triggering campaign in their post-mortem header.

Anti-pattern: bundling everything into one MINOR — the version-history entry becomes a wall of bullets where the paradigm-level changes are buried among 8 clarifications. Future reader scanning version history can't tell what's load-bearing.

Anti-pattern: skipping MINOR entirely and packing paradigm-level additions into a PATCH — silently widens what "PATCH" means and erodes semver discipline.

### 6.5 — Cross-reference completeness check (before applying edits)

Each new section / failure mode / named pattern needs cross-references pointing in BOTH directions:

- New §section X must reference the failure mode it cures
- New failure mode #N must reference the §section that cures it
- New named pattern X must reference the campaign that motivated naming it AND the failure mode it short-circuits
- Version-history entry must cite every new failure mode by number + every new section by name

Run a grep over your draft edits before applying: every `See failure mode #N` resolves; every `§X.Y.Z` resolves; every named pattern (`PDAAV`, `RIBS`, etc.) appears in the named-pattern index (added in v1.13.1).

### 6.6 — Apply edits + verify

Apply via Edit/Write. After each edit, run a sanity grep:

```bash
grep -c "^version:" _skill-updates/conquering-campaign/SKILL.md  # expect 1
grep -c "^### v1\." _skill-updates/conquering-campaign/SKILL.md   # expect N (history entries)
grep -cE "^[0-9]+\. \*\*" _skill-updates/conquering-campaign/SKILL.md  # expect highest failure mode # is correct
```

If MINOR + PATCH ship in the same turn, bump version twice (once after MINOR edits, once after PATCH edits). Each version-history entry goes in immediately before the prior release entry (reverse-chron order).

### 6.7 — Output to the user

After applying edits, report:
- Version bump path (e.g. `1.12.1 → 1.13.0 → 1.13.1`)
- New sections / failure modes / named patterns
- File line delta
- Any LOW-signal findings deferred (with reasoning)

Reflection-pass triggers on phrases: *"reflect on this session and propose skill upgrades"*, *"upgrade as recommended"*, *"review this session and note lessons"*. Do NOT trigger on phrases like *"summarize what we did"* (that's a vault-log task, not a skill-upgrade task).

---

## Named patterns index

Quick-ref dashboard of named sub-patterns. Phases that follow a named pattern declare it in plan frontmatter (`db_pattern:` / `fe_pattern:` / `subagent_pattern:`); future readers + agents understand the tool-call chain without re-describing it. Each pattern has its own detailed section deeper in the skill.

| Pattern | Surface | Frontmatter tag | Use when | Section |
|---|---|---|---|---|
| **PDAAV** | DB | `db_pattern: PDAAV` | Schema / RLS / view / trigger change | §Subagent dispatch — Named DB sub-pattern |
| **PDAAV-RIBS** | DB | `db_pattern: PDAAV-RIBS` | DB function/view rename + body shrink (SQL mirror of RIBS) | §Subagent dispatch — SQL-RIBS variant |
| **RIBS** | FE | `fe_pattern: RIBS` | Component rename + >40% body shrink (single file) | §Subagent dispatch — Named FE sub-pattern: RIBS |
| **RIBS-N** | FE | `fe_pattern: RIBS-N` | Multi-file lockstep rename (component + test + storybook) | §Subagent dispatch — RIBS multi-file variant |
| **Source-walk template** | Either | brief shape, no frontmatter | >20 files inspected, JSON-on-disk output required | §Subagent dispatch best practices |
| **Scoped-lint** | FE verification | inline at W4 | Project-wide lint fails on unrelated WIP; need to prove campaign-surface clean | §5.2 |
| **Checkpoint markers** | Either | `<!-- CHECKPOINT: CHK-<id> -->` | External blocker prevents verification (MCP down, prod telemetry not yet available, etc.) | §Checkpoint pattern |

Naming convention: BE-side patterns capitalised acronyms (PDAAV); FE-side capitalised acronyms (RIBS); multi-surface or procedural patterns descriptive lowercase-hyphenated (source-walk, scoped-lint, checkpoint).

When a campaign uses ≥2 named patterns, list them in the campaign plan's frontmatter (`db_pattern:` + `fe_pattern:`). At W4 risk sweep, the per-phase verification rows cite the pattern used (e.g. "P1 applied RIBS — git mv + atomic Write + barrel update; verified zero old-name imports via grep proof").

---

## Model assignment

### Three-tier summary

The campaign's token efficiency comes from a strict division of labour across three tiers. Use the cheapest tier that can do the job.

| Tier | Who runs it | When | Token cost |
|---|---|---|---|
| **W0 — Ollama** | Main agent via `Bash` (not an Agent call) | File listing, grep counts, surface map, doc summarisation | Free — local inference |
| **W1-W3 — Claude sonnet** | `general-purpose` subagent | Mechanical scanning, route/hook/type mapping, standard pattern work | API tokens (mid) |
| **W1-W3 — Claude opus** | `general-purpose` subagent | Security, RLS, synthesis, money-adjacent phases, schema/trigger reasoning | API tokens (highest) |
| **W4 — You (main agent)** | Main agent directly | Synthesis (audit) or risk sweep (build) — never delegated | Conversation turn |

The savings are structural: Ollama handles everything it can (free), then Claude subagents get pre-loaded context from the W0 file instead of re-exploring. Running W0 once at the start compresses the W1 discovery token spend across every subagent that would otherwise have explored the same files independently.

---

### Effort levels

Pick the model **and** the effort level for each task. The Agent tool has no effort parameter —
effort is set through **prompt language** in the subagent brief. Use these three effort phrases
verbatim:

| Effort | Phrase to include in the subagent brief |
|---|---|
| **deep** | `"Reason step by step. Think through every implication and edge case. Flag anything you are uncertain about rather than guessing."` |
| **standard** | *(no special phrase — normal reasoning applies)* |
| **fast** | `"This is a mechanical task. List, count, or map only. Do not reason beyond what you directly observe. Speed matters more than depth here."` |

The Ollama tier is selected automatically in Step 0; all other tiers are fixed.

---

### Tier 0 — Ollama (free, local — selected by W0 probe)

| Task type | Mode | Model | Effort |
|---|---|---|---|
| Pre-scan: file inventory, grep counts, surface map | both | `qwen2.5-coder:*` (auto-selected) | fast — mechanical listing only |
| Pre-scan: multi-file doc summarisation, architectural overview | both | `qwen3:8b` or `qwen3:14b` (auto-selected by RAM) | fast — summarise, do not analyse |

W0 rules: Ollama **only** does file listing, grepping, and summarisation. It never writes code,
SQL, or plan files. Its output is a pre-scan file that Claude subagents read as pre-loaded context.
If Ollama is unavailable, skip W0 entirely — do not let its absence block the campaign.

---

### Tier 1 & 2 — Claude API (used for all reasoning, planning, writing)

| Task type | Mode | Model | Effort |
|---|---|---|---|
| Schema reasoning, RLS parity, security audits | audit | **opus** | **deep** |
| Architecture reality (god objects, dead code, refactor risk) | audit | **opus** | **deep** |
| Master synthesis | audit | **opus** (you, not a subagent) | **deep** |
| Doc rewrites (Backend.md, Frontend.md — biggest scope) | audit | **opus** | **deep** |
| Permission system / RLS parity matrix | audit | **opus** | **deep** |
| Pattern compliance (grep-driven counting) | audit | **sonnet** | **fast** |
| API route / fetch-callsite mapping | audit | **sonnet** | **fast** |
| File-system inventory, dead-code verification | audit | **sonnet** | **fast** |
| Realtime channel / subscription mapping | audit | **sonnet** | standard |
| Mutation-module compliance per file | audit | **sonnet** | standard |
| Doc rewrites (Integration.md, Guidelines.md — smaller scope) | audit | **sonnet** | standard |
| Mass file-listing, trivial extractions | both | **haiku** | **fast** — only if W0 unavailable |
| Surface discovery (W1 of build) — schema/RLS/views | build | **opus** | **deep** |
| Surface discovery (W1 of build) — types/FE/admin | build | **sonnet** | standard |
| Phase plan drafting (W2 of build) — DDL/RLS/triggers | build | **opus** | **deep** |
| Phase plan drafting (W2 of build) — types/FE/mutations | build | **sonnet** | standard |
| Implementation (W3 of build) — schema/RLS/triggers | build | **opus** | **deep** |
| Implementation (W3 of build) — types/FE/mutations | build | **sonnet** | standard |
| Risk sweep & vault log (W4 of build) | build | **opus** (you, not a subagent) | **deep** |

**Avoid haiku for anything that requires nuance or domain context.** When W0 ran successfully, haiku is redundant — the pre-scan already did the cheap work.

**Effort compounds with model:** opus + deep is the most thorough combination — reserve it for
security, RLS, synthesis, and money-adjacent phases. Sonnet + fast handles all mechanical
scanning. Never use deep effort on a fast/mechanical task.

---

## Conformity discipline

**Follow the app's existing patterns. Do not invent new styles.**

The codebase and its docs define how things are done. A campaign's job is to extend that system, not to introduce a parallel one. When Claude builds a new page, component, mutation, or view, it must look like it was written by the same hand that wrote the existing ones.

### Before writing any code

1. **Read the project's pattern docs** — FRONTEND.md (component patterns C1-C10), GENERAL-GUIDELINES.md (39 rules), design tokens (`C.*` constants), the relevant planet hub for the surface you're touching. These are the law.
2. **Find the reference implementation** — the planning interrogation (Step 1) should have identified one. If not, find the closest existing page/component to what you're building and use it as the model. **Read its full render function** — not just the imports, prop types, or component signature. The visual hierarchy (how lines, sections, and indentation are layered in the JSX) is only visible in the complete render tree. For UI consolidation campaigns, extract the exact line-level layout from the reference before writing the target component: e.g., "Line 1: row# + headline + actions | Line 2: icon-label metadata pairs (`paddingInlineStart: 40`) | Line 3: status chips (`paddingInlineStart: 40`)." A component that reuses the same tokens but misses the render hierarchy will look structurally different from the reference at a glance.

   **Visual alignment extraction.** When told to match a reference component's visual style (buttons, cards, action bars), the style almost always lives in a *sub-component*, not the page-level row. A page like `TaskListRow` delegates to `TaskListActionBar`; the design language is defined there, not in the row. Follow the import chain to the leaf component and extract these properties explicitly before writing anything — don't approximate:
   - Button: `background`, `border` (thickness + color token), `borderRadius` (token name — e.g. `borderRadius.lg` — not the pixel value), icon `size`, icon `color` token, `transition`, `flexShrink`, `padding`
   - Wrapper: `display`, `gap`, `alignItems`
   - Hover: CSS transition or `useState` (not inline `onMouseEnter` style mutation)
   - Tooltip: wrapping mechanism (`<Tooltip>` component vs `title` attribute)

   A component that approximates "similar" values but misses one token (e.g., hardcoded `8` instead of `borderRadius.lg`, or `title=` instead of `<Tooltip>`) will look subtly off and require an extra correction round. Also: **re-read the reference file immediately before implementing** — it may have been updated in the same session by the user or a parallel edit.

   **Sidebar nav lock-in.** Any `<button>` placed inside `<SidebarCard>` (or equivalent sidebar primitive) that participates in a list of selectable items — section nav, tab switcher, view picker — MUST use the project's canonical nav-row primitive (`PortalNavRow` in lex_council). No hand-rolled buttons, even in "dev-only" or "throwaway" panels. The canonical primitive encodes active-state styling, hover, optional lock-badge, disabled state — all the chrome that a hand-rolled button silently re-invents (and gets wrong). The classic failure: hand-rolled active state uses `background: <some active token>` with `color: <same family token>` and ships text the same color as the background → invisible label on a solid rectangle. `tsc + lint` green; visual regression invisible to the type system. Detection at write-time: if you are about to write `<button>` inside `<SidebarCard>`, stop, grep for the project's nav-row primitive, use it. If the sidebar already has a working nav row visible in the design (e.g., a "View" card immediately above your new "Sections" card), the new card uses the same primitive — no exceptions. See failure mode #49.

3. **Inventory the conventions** that apply to this phase:
   - Layout structure (sidebar width, padding, flex direction)
   - Layout direction — LTR or RTL? If Arabic text comes from the DB but the UI is an English admin panel, the *container* direction should be LTR even if text content is Arabic. Don't inherit `direction: 'rtl'` from old table-column patterns.
   - Color tokens (never hardcode hex — use `C.*`)
   - Icon system (`<MIcon>` only, never raw Material Symbols)
   - Component structure (C1: directive → imports → header → types → component → styles)
   - Type naming (`{entity}-{role}-{shape}.ts`, all-hyphen)
   - View naming (`{table}_{purpose}_js`)
   - Mutation pattern (`MutationResult<T>`, `ok()`, `fail()`)

### During execution

- **Match the reference implementation's structure exactly** — same prop patterns, same state management approach, same sidebar card ordering, same tag/chip styling.
- **When you see inconsistency in the existing code, resolve it — don't add to it.** If 10 pages do it one way and 2 pages do it another, the 2 are wrong. Migrate them to match the 10 (or flag for a follow-up if out of scope).
- **Never introduce a new UI pattern, component structure, or naming convention without documenting it.** If you must diverge (rare — only when the existing pattern genuinely can't serve the use case), document the new pattern in the relevant doc and explain why.
- **Design tokens are non-negotiable.** Colors from `C.*`, icons from `<MIcon>`, spacing from design tokens. No `style={{ color: '#1a1a1a' }}` when `C.textDark` exists.

### Conformity + consolidation together

Conformity tells you *what* the pattern is. Consolidation tells you *how to share it*:

| Situation | Conformity says | Consolidation says |
|---|---|---|
| Building a new admin page | Follow the AdminPageShell + SidebarStack + card-list pattern | Use the existing `ListRowBase`, `SidebarActionButton`, etc. |
| Adding a filter dropdown | Match the existing multi-select style | Use `MultiSelectFilterDropdown`, don't build a new one |
| Creating a new entity row | Follow the 3-line card row layout (headline / meta / tags) | If file-domain: compose `ListRowBase`. If person-domain: compose `MemberListRow`. |
| Found 2 pages with a different style | The 15 other pages define the standard | Extract what's common, migrate the 2, delete the old code |

### At the end of the campaign

As part of the risk sweep (Step 4), include a conformity check:

- **Visual consistency** — do all pages touched by the campaign look like they belong to the same app?
- **Pattern consistency** — do all new components follow the project's C1-C10 patterns?
- **Token consistency** — zero hardcoded hex, zero raw Material Symbols, zero Tailwind classes?
- **Naming consistency** — new files follow the project's naming conventions?
- **Stale doc-comment sweep** — for every design fact the campaign changed (e.g. "navy background", "white icons", "filled style", "32×32 navy bg"), `grep -rn "<old fact>" apps/web/ --include="*.tsx"` to find header comments that still describe the pre-campaign design. Header comments that lie are worse than absent ones — they actively mislead the next reader who trusts the comment over the current code. Update or delete them in the same pass.

If conformity violations are found during the risk sweep, fix them before closing the campaign.

---

## Consolidation discipline

**Never copy-paste a pattern into multiple files.** Every campaign must leave the codebase with fewer repeated patterns than it found.

### Before writing any phase

1. **Inventory existing shared primitives** that the campaign's consumers should use. List them in the phase plan.
2. **Identify copy-paste hotspots** — if 3+ files will receive the same pattern (a row layout, a filter dropdown, a sidebar button), extract it into a shared component first, then compose.
3. **Check for near-duplicates** — if a component does 80% of what you need, extend it rather than creating a parallel one.
4. **Grep before changing a shared default.** For any phase that changes the effective meaning of a design token, a base-component default, or a shared style (`C.textMid` → `C.navy`, `bg: navy` → `bg: transparent`, default font size shift, etc.), the **first** action is `grep -rn` to enumerate every consumer site **before** picking which files to edit. Decide the new value across **all** sites in one pass, not per-complaint. A single Edit that resolves one site while ignoring the other N is not a fix — it is the seed of N follow-up one-shot turns. The grep result becomes the input to the §W3 stale override sweep — the two disciplines are paired.

5. **N=3+ union-prop audit.** When a single component exposes a render-mode union prop (`layout`, `variant`, `mode`, `kind`, `size` when used for layout not text-size) with ≥3 values, AND any consolidation campaign touches its consumers, do a write-time audit:

   ```bash
   # How many consumers pass each value of the union?
   grep -rn 'layout="cascade"\|layout="inline"\|layout="vertical"' apps/web/ --include="*.tsx" 2>/dev/null | sort
   # Or, generalised:
   grep -rn '<ComponentName' apps/web/ --include="*.tsx" 2>/dev/null | sort
   ```

   For each value: count consumers, check whether deleting that branch would lose any user-facing functionality. If N-1 values cluster around one keeper and the others are legacy survivors:

   - **Drop the prop entirely** (not just the dead values) — once one value survives, the prop's only purpose was to disambiguate, and a single-value union is misleading dead weight
   - **Delete the dead render branches** in the same phase (the cascade/inline blocks, their helper components, their unused imports — see §28/§51 for Multi-Edit atomicity guidance on large branch deletions)
   - **Drop helper components used only by deleted branches** (e.g. `FileContainerChip` lived only inside `cascade`; once `cascade` dies, the helper dies too)
   - If the file's name encoded one of the removed directions (e.g. `FooHorizontal.tsx` when `vertical` survives), see §1.4.1 + failure mode #57 — rename happens in the same campaign, not deferred

   The N=3 alarm (failure mode #27) fires on Nth hand-rolled clone of a recurring file shape. This is its sibling for **enum union props** — same root pattern (≥3 of a thing, one is canonical, rest are legacy), different surface (prop union, not file replication). Both need the same write-time grep before the first Edit.

   The 2026-05-16 `files-stack-sidebar-canonical` campaign did this organically (deleted `layout: 'cascade' | 'inline' | 'vertical'` entirely, dropped the cascade + inline branches, shrunk the component 61%) but the discipline was implicit. Codifying it as Rule 5 prevents the next campaign from leaving a stale 1-value union behind. See failure mode #58.

### Extraction-first phase ordering

When the campaign creates shared primitives, the extraction phase must come before the consumption phases:

| Order | What | Example |
|---|---|---|
| Phase 1 | Extract shared primitives | `ListRowBase`, `SidebarActionButton`, `useKpiCells` |
| Phase 2-N | Compose primitives into consumers | Credits page uses `ListRowBase`, Members page uses `MemberListRow` |
| Phase N+1 | Delete legacy code that the primitives replaced | Remove `AdminDataTable`, `AdminFilterBar` |

### During execution

- If you find yourself writing the same JSX block in a second file: **stop**. Extract it. Then import it in both files.
- If a subagent's phase plan contains copy-pasted code across multiple files, reject the plan and re-draft with extraction.
- Every shared primitive gets its own file in the appropriate directory (e.g., `components/admin/v2/`) and a barrel export.

### At cleanup

- Verify zero live imports of replaced components: `grep -r "OldComponent" apps/web/`
- Delete the replaced files
- Confirm `tsc` still passes

---

## Self-verification loop

After every phase (build mode) or every wave (audit mode), run this loop automatically. Do not ask the user. Do not skip it.

### Build mode — after every phase

```
1. Run `tsc --noEmit` (or the project's check-types command)
2. Run `npm run lint`
3. If BOTH pass → log "verification: clean" in the phase file, continue
4. If EITHER fails:
   a. Read the error output
   b. Fix the issues (up to 3 attempts, each more targeted)
   c. Re-run the failing check after each fix
   d. If fixed → log "verification: fixed (N attempts)" with what was wrong
   e. If 3 attempts fail → CHECKPOINT the issue, log "verification: deferred — CHK-<id>", continue
5. **If the phase touches user-facing UI / theme / auth / hydration / realtime / locale / i18n state, preview verification is REQUIRED, not optional** (regardless of whether the plan listed it):
   a. Start the preview (or navigate to the relevant page)
   b. Take a screenshot AND a polled DOM read at multiple timestamps (e.g., 100 ms, 500 ms, 1 s, 3 s) — single-snapshot reads miss hydration timing bugs (the SSR-rendered value can survive several hundred ms before the client effect overrides it)
   c. Run the **browser verification recipe** captured in Step 1.2 Q9 for any outcome this phase contributes to
   d. Verify the observable change matches the phase plan's expected output
   e. Log the result in the phase file with the actual snapshot values + timestamps as evidence — every "✓" in the surface coverage matrix needs a concrete observation behind it, not an intent
   f. **Diagnostic discipline:** if you manually mutate DOM/storage state during debugging (e.g., `document.documentElement.setAttribute(...)`, `localStorage.setItem(...)`), always `location.reload()` (or open a clean tab) before the next verification read — otherwise the manual poke pollutes the observation. See failure mode #21.
6. Never stop to ask about verification results — self-heal or mark-and-move
```

### Audit mode — after every wave

```
1. Verify all expected findings files exist on disk
2. Spot-check one findings file for completeness (has all expected sections)
3. If a subagent's file is missing or truncated → relaunch that specific task
4. Continue to the next wave
```

---

## Autonomous decision framework

When Claude hits a choice not explicitly covered in the plan during execution, follow this ladder. The goal: keep moving, log the decision, never stop for something resolvable.

| Priority | Condition | Action |
|---|---|---|
| 1 | **Plan says** | Follow the plan exactly |
| 2 | **Project memory / docs say** | Follow the established convention, log it |
| 3 | **Clear recommended option** (one approach is standard, the other is unusual) | Take the recommended option, log it |
| 4 | **Reversible choice** (both options work, easy to change later) | Pick the safer/simpler option, log it |
| 5 | **Irreversible + no guidance + high-risk** | **STOP and ask** — this is the only case |

Every autonomous decision gets logged in the phase file:

```markdown
> **Decision:** Used `ListRowBase` composing `MemberListRow` instead of a raw div
> for member rows — matches the pattern established in Tasks/Cases pages (decision
> ladder: level 2, project convention).
```

**What counts as "irreversible + high-risk":**
- Dropping a column or table
- Deleting data (not code — code is in git)
- Changing RLS policies on money-adjacent tables
- Any `apply_migration` that alters production data shape

**What does NOT count (never stop for these):**
- Choosing between two component structures (reversible)
- Naming a new file or variable (reversible)
- Picking a CSS layout approach (reversible)
- Deciding whether to extract a shared primitive now or later (the answer is always "now" per consolidation discipline)
- Fixing a lint error introduced by the phase (self-verification handles this)

---

## Subagent dispatch best practices

- **Use `general-purpose` as the subagent type by default.** Specialised agents (`backend-auditor`, `frontend-auditor`, `code-reviewer`) often have constrained contracts. If a specialised agent exists and matches the task scope, use it; otherwise default to general-purpose so the agent can write to disk freely.
- **Hand each subagent a self-contained brief** that includes: pre-existing files to read first (including `00-w0-offline-prescan.md`), exact output path, frontmatter to use, sections expected, and **explicit read-only vs may-write designation**.
- **In audit mode, every subagent is read-only.** Tell them so explicitly: "Read-only audit. Do not modify code or other docs — only write the findings file."
- **In build mode W1 (discovery), subagents are read-only.** Same wording as audit.
- **In build mode W2 (phase plans), subagents are read-only and write only their own phase-plan file.** Plans, not execution. "Draft SQL/types/code in your phase-plan file. Do not run migrations or modify code outside that file."
- **In build mode W3 (implementation), the main agent does the writes** — never a subagent that the user hasn't explicitly approved. Subagents may draft files; the main agent reviews and applies them under the campaign's approval cadence.
- **Run waves in parallel within a wave** — same message, multiple Agent calls. Sequential dispatch defeats the parallelism that makes the campaign tractable.
- **Track agent IDs** — when a subagent gets blocked or returns partial work, you'll need to relaunch with corrected scope.
- **If you said you dispatched something, verify it actually ran.** Check the file's existence on disk before claiming done.
- **After any wait >30s (subagent return, Monitor stream end, MCP round-trip), re-Read the next target file before the next Edit.** Background tooling (PostToolUse linters, IDE formatters, parallel agents) often mutate files during the pause; your stale Read state will fail the next Edit with `File has been modified since read`. Read is cheap; failed Edit + recovery is not. See failure mode #41.

### Source-walk subagent template

When a task requires inspecting MANY files (>20 mutations, >50 callsites, >30 components) and producing structured findings for the main thread to consume, dispatch a `general-purpose` subagent with this exact shape:

```
Task: <one-line goal>

Project root: <absolute path>

Inputs:
- <pre-existing canonical inventory file, e.g. actions-manifest.ts>
- <any prior subagent's JSON output that this one builds on>
- <directories to walk, with excludes — node_modules, .next, _skill-updates>

For every item:
1. <read step>
2. <inspect step — what to capture per item>
3. <classification or extraction rule>

Output: write a JSON array to this exact path (no commentary, no markdown):
  docs/build-campaigns/<campaign-id>/NN-<topic>.json

Shape:
  [{ "<key>": "<value>", ... }, ...]

Rules:
- Cover every input item exactly once. No omissions.
- Dedupe by <natural key> if applicable.
- Cap at <expected order of magnitude>; flag if you exceed it (signals broken filter).

When done reply with:
- Total rows written
- Per-category counts
- Anomalies / fallbacks / items needing human review

Do not paste the JSON inline.
```

**Why JSON-on-disk:** the main thread parses one file with `JSON.parse`, builds SQL / UI / report from a typed shape, and the campaign folder retains the findings as evidence. Inline replies bloat conversation context, can't be re-read by a later phase, and force fragile regex parsing. Three uses in one campaign (descriptions, callsites, classifications) makes this a reusable shape. See failure mode #42.

**Always pair with a build-from-JSON helper.** After the subagent returns, the main thread typically runs a one-liner Node script (`/tmp/build.js`) that reads the JSON, escapes SQL strings, and writes `/tmp/seed.sql` (or `.tsx`, `.md`). Pass this through to `execute_sql` / `Write` / etc. Keep the build script ephemeral (`/tmp/`); the JSON is the durable artifact.

### Named DB sub-pattern: PDAAV (probe → draft → approve → apply → verify)

When a phase touches DB schema (migration, RLS, view, trigger, seed), follow the named **probe-draft-approve-apply-verify** chain:

1. **Probe** — `execute_sql` against `information_schema.columns`, `pg_policies`, `pg_views`, or `pg_class.reloptions` to find the existing pattern to mimic (see §Step 3 W3 step 1.5d). Confirms column locations, RLS shape, view conventions.
2. **Draft** — write the migration SQL inline in the conversation. Don't execute yet.
3. **Approve** — `AskUserQuestion` with the SQL visible + 3 options: `Apply (Recommended)` / `Tighten <some axis>` / `Hold — want to change something`. P3 (No Silent Writes) is the contract.
4. **Apply** — `apply_migration` on approval. Single MCP call.
5. **Verify** — `execute_sql` post-flight: count rows, aggregate by group, confirm policies' `qual` text, view's `reloptions` (see §Step 3 W3 step 2a). Record as evidence in the phase change-log.

Phases that follow PDAAV can name it in their plan: `db_pattern: PDAAV`. Future campaigns reading the plan understand the five tool calls without re-describing them. See failure mode #43.

### Named DB sub-pattern: PDAAV-RIBS (SQL mirror of RIBS — rename + body shrink)

When a DB phase renames a function/view/trigger AND simultaneously shrinks its body (drops dead branches, removes unused parameters, eliminates fallback logic), single-call `apply_migration` with `CREATE OR REPLACE FUNCTION new_name(...) ...` paired with `DROP FUNCTION old_name(...)` has two trap classes: (a) RLS policies + view definitions that referenced the old name break in the same migration if not updated atomically; (b) `security_invoker = true` and other view options silently drop on `CREATE OR REPLACE VIEW` per the add-new-view skill's known trap. **PDAAV-RIBS** is the SQL mirror of RIBS — combines PDAAV's verify discipline with a rename+shrink atomic migration:

1. **P — Probe** (same as PDAAV) — `execute_sql` against `information_schema.routines` / `pg_views` / `pg_policies` to enumerate every dependent of the old name. List every RLS policy, view, trigger, function, materialised view that references the old name. The dependents list is the input to the migration body.
2. **D — Draft** — write the migration SQL inline with:
   - `CREATE OR REPLACE FUNCTION new_name(...)` (shrunken body)
   - For views: `CREATE OR REPLACE VIEW new_name AS ... ; ALTER VIEW new_name SET (security_invoker = true);` (the `ALTER VIEW` is mandatory — see add-new-view skill failure mode for the silent drop)
   - `UPDATE` statements for every dependent's body (RLS policy `qual` rewrites, view bodies, trigger function bodies)
   - `DROP FUNCTION/VIEW old_name(...)` at the END (after all dependents updated)
3. **A — Approve** (same as PDAAV) — `AskUserQuestion` showing the full migration body + Apply / Tighten / Hold options.
4. **A — Apply** (same as PDAAV) — single `apply_migration` call. Atomic; either all dependents update or rollback.
5. **V — Verify** — `execute_sql` post-flight:
   - Confirm `new_name` exists with the shrunken body (`SELECT pg_get_functiondef(...)`).
   - Confirm `old_name` is gone (`SELECT count(*) FROM information_schema.routines WHERE routine_name = 'old_name'` → expect 0).
   - Confirm every dependent's body now references `new_name` (re-query `pg_policies.qual`, `pg_views.definition`, etc.).
   - Confirm `security_invoker = true` on any renamed view (re-query `pg_class.reloptions` for `[security_invoker=true]`).
   - Confirm the effective access didn't shift unexpectedly (re-run §3 W3 step 2a-RLS effective-access check if RLS policies were touched).

Phases that follow PDAAV-RIBS declare `db_pattern: PDAAV-RIBS` in the plan. The five-step shape mirrors PDAAV; the difference is that the migration body is non-trivial (multiple atomic statements; the dependent-update list is the planning artifact). Sibling of FE-side RIBS — same `rename + body shrink` shape, different surface.

### Named FE sub-pattern: RIBS (rename-incidental-body-shrink)

When a campaign renames a public component AND simultaneously deletes >40% of its body (dead branches, orphan helpers, dropped union-prop modes), git's rename-detection heuristic stops firing — git records the change as `add new file + delete old file`, not `rename + edit`. The wave of intermediate states a chained-Edit-then-rename would produce is also lint-dirty (helpers exist with no callers between Edits — see failure mode #28). The **RIBS chain** is the named procedure for this shape:

1. **R — git mv.** `git mv apps/web/components/<old>.tsx apps/web/components/<new>.tsx`. Single shell call. Keeps file in version control, restamps the path.
2. **I — Initial Read.** Read the newly-renamed file to satisfy the Edit/Write tool's pre-Edit invariant (the harness tracks files by path; the `git mv` changed the path).
3. **B — Body Write (atomic).** Single `Write` over the entire new file with: imports trimmed to only what the survivor branch needs; helper components deleted; dead render branches deleted; dropped union-prop values removed from the type; default export renamed to match new filename. **Not** chained Edits — a 60%-shrink body is structurally too large for incremental edits without lint-dirty intermediates (failure mode #28). The atomic Write is one diff, one lint pass, one consistent end state.
4. **S — Surface sweep.** Update the barrel export (`export { default as <new> } from './<new>'`). Then a project-wide grep proves zero remaining imports of the old name:
   ```bash
   grep -rln "<OldName>" apps/web/ --include="*.tsx" --include="*.ts"   # expect zero hits before consumer updates
   ```
   The actual consumer-import rewrite happens in P2 (the campaign's page-consumer phase), not P1.

Phases that follow RIBS can name it in their plan: `fe_pattern: RIBS`. Used by the 2026-05-16 `files-stack-sidebar-canonical` campaign on `FilesStackHorizontal.tsx` → `FilesStack.tsx` (962 → 374 lines, −61%). Without the named pattern, the natural instinct on a rename-with-shrink is chained Edits (`Edit` to delete branch A, `Edit` to delete branch B, `Edit` to rename function) — and the PostToolUse linter strips helpers between Edits per failure mode #28. RIBS short-circuits the trap. See failure mode #60.

### Named FE sub-pattern: RIBS-N (multi-file lockstep rename)

When a component's rename touches N>1 companion files in lockstep (e.g. `Foo.tsx` + `Foo.test.tsx` + `Foo.stories.tsx` + `Foo.types.ts`), single-file RIBS doesn't cover the cross-file consistency requirement. The **RIBS-N chain** generalises RIBS for multi-file lockstep:

1. **R-N — Batch git mv.** All companions renamed in a single Bash batch so the working tree stays consistent:
   ```bash
   git mv apps/web/components/Foo.tsx           apps/web/components/Bar.tsx
   git mv apps/web/components/Foo.test.tsx      apps/web/components/Bar.test.tsx
   git mv apps/web/components/Foo.stories.tsx   apps/web/components/Bar.stories.tsx
   git mv apps/web/components/Foo.types.ts      apps/web/components/Bar.types.ts
   ```
2. **I — Initial Read of each renamed file** (cheap; needed to satisfy Edit pre-invariants for the next step).
3. **B — Atomic Body Write per file.** One Write per file, each carrying its full final content. Imports trimmed, helpers deleted, dropped union-prop values removed from types, default-export name updated to match new filename. **Not** chained Edits; the multi-file shape amplifies failure mode #28's risk because the linter fires across the batch.
4. **S — Surface sweep.** Update barrel + grep-proof zero remaining imports of OLD name across the entire `apps/web/` tree. Specifically check that `*.test.tsx` files don't import from the OLD path via deep imports.
5. **C — Companion consistency check.** After Writes complete, grep that all N companions reference the NEW name consistently (no test file still importing the old type-definition module, etc.):
   ```bash
   grep -rn "Foo\b" apps/web/components/ --include="*.tsx" --include="*.ts" --include="*.test.tsx"
   # expect: zero hits except in archived/historical docs
   ```

Phases following this declare `fe_pattern: RIBS-N` in the plan. RIBS-N also covers cases where the rename touches a hook + its consuming components + its test in lockstep, or a Zustand store + the types file it imports.

When N=1 (single file), use plain RIBS — RIBS-N's batch-mv adds overhead without benefit at N=1.

---

## Environment hazards (PostToolUse hooks + mass-edit patterns)

### Aggressive PostToolUse hooks

Many projects wire linters / formatters / token-rewriters as `PostToolUse` hooks. Expect:

- **"File has been modified since read" errors** mid-Edit. The hook touched the file between your Read and your Edit. Mitigations:
  - Prefer `Write` over `Edit` for files you just refactored — `Write` has no Read precondition once you have the full content in hand
  - Re-Read just the smallest slice you need, then Edit again
- **Design-token rewrites mid-flight.** Hooks may rewrite `colors.X` → `var(--color-X)` or strip unused imports right after your Edit. That's expected, not a regression. Accept the linter's output as the source of truth.
- **Cascade lint errors from "helpful" reformatting.** A token swap (`colors.X` → CSS var) leaves the original `colors` import unused; the hook may then strip it, cascading to other files that imported the same symbol. Run lint at every phase exit (not just campaign close) so you catch this in batches.
- **Multi-Edit atomicity trap.** When a phase needs ≥2 sequential `Edit` calls to the same file where the **intermediate state would fail lint** — e.g., `Edit #1` adds a helper function, `Edit #2` adds the call sites — the linter fires *between* the two Edits, sees the helper as `no-unused-vars`, and **deletes it**. `Edit #2` then either fails (anchor missing) or compiles to a broken state. Mitigation: when intermediate state would be lint-dirty, use a single `Write` over the whole file instead of chained Edits. The `Write` is atomic; the linter only sees the final, consistent state. Tell: any time you're about to add a util/helper/constant whose first call site is in a *later* Edit of the same phase, choose `Write`. See failure mode #28.

### Mass-edit patterns (>=10 files of the same shape)

When touching ≥10 files with a consistent shape (rename an import path, wrap pages in a shell, swap a component name), inline `python3 << 'PY'` heredocs with `re.sub` are 10× faster than per-file Edit calls.

```bash
python3 << 'PY'
import os, re
for d, _, files in os.walk('.'):
    if 'node_modules' in d or '.next' in d:
        continue
    for f in files:
        if not f.endswith(('.ts', '.tsx')):
            continue
        path = os.path.join(d, f)
        with open(path) as fh:
            src = fh.read()
        new = re.sub(r"from '@/components/admin/v2'", r"from '@/components/portal'", src)
        if new != src:
            with open(path, 'w') as fh:
                fh.write(new)
            print(f"  rewrote {path}")
PY
```

Two footguns:

- **JSX double-quote escapes in Python strings.** Use raw strings `r'...'` and prefer non-quote-containing match anchors. If you need to match `className="x"`, write `r'className="x"'`, never `'className=\"x\"'` (Python escapes will leak into the file).
- **No Read precondition = no safety net.** The Edit tool's "modified since read" guard doesn't fire on Bash-mediated writes. Always run `tsc --noEmit` immediately after a batch pass — within seconds, not at end of phase.

### Runtime module caches that don't HMR

The runtime mirror of failure mode #18 (Turbo cache hiding pre-existing compile errors). Several dev-server caches survive HMR and serve stale content even after the source-of-truth file on disk is correct:

- **Next.js dev-server JSON imports.** A locale file like `messages/<locale>/<ns>.json` is loaded once at server start via `await import('...json')`. Adding a key mid-session does NOT trigger re-evaluation of the dynamic import. Runtime `t('new.key')` falls through `getMessageFallback` and renders the raw key path. Sibling keys in the same object resolve correctly. Detection signal trio: (a) raw key path renders in the UI; (b) `git blame` shows the key on a line marked `00000000 (Not Committed Yet)`; (c) other keys in the same JSON object render fine. All three present ⇒ stale dev-server JSON cache. Fix: restart the dev server. Don't query the DB for overrides, don't re-read the i18n config, don't suspect the namespace scoping.
- **SWC bundler stale parses.** A removed component (e.g. a `ModalShell` that the file no longer imports or defines) continues to produce parse errors that cite the file's current line numbers. Detection signal: the bundler error names a symbol that `grep` cannot find in the current file, AND `git diff HEAD` shows the file is clean. Fix: clear `.next/` and restart, or touch the file to force re-parse.
- **`.next/` cache after large file moves or renames.** Module-resolution lookup tables are written at first compile and serve stale paths after renames.

**Umbrella discipline: symptom-impossible-vs-current-file-state ⇒ restart dev server first.** When the visible runtime behavior contradicts what the current file on disk says, the first action is restart, not investigation. Cost of restart: ~5-15s. Cost of chasing the wrong layer (DB, config, namespace, build output): minutes-to-hours plus risk of introducing a "fix" for something that was already correct. Add this as the first item on any §W4 verification checklist: *if the runtime symptom and the current file disagree, restart before diagnosing.*

The fix is not a code change — it's a "restart the dev server" instruction in the change log + a vault-log note. The file changes that triggered the stale-cache state still ship; the cache invalidation is a session-local action. Don't ship a phantom-edit commit ("touch file to force HMR") — that's the wrong layer.

### JSX structural pivot via chained Edits

Sibling case of failure mode #28 (Multi-Edit atomicity trap). The trap fires when a phase wraps N>3 JSX siblings with the same conditional pattern — e.g., converting "render all 7 sections" to "render whichever section is active" requires wrapping each section's `<div>` with `{activeSection === '<id>' && <div>`. Done with N chained Edits, the chain has three weaknesses:

1. **Each Edit needs a unique anchor in a file where many sites have the same shape** — easy to mis-target, especially when section content is similar.
2. **Aggressive PostToolUse linters fire between Edits** — the intermediate state has N/2 sections gated, N/2 not. The linter sees an inconsistent file and may try to "fix" it.
3. **Review is fragmented** — the diff is N small hunks instead of one coherent restructure. Future readers can't see the pivot as a single intent.

Distinction from #28: #28's intermediate state is **lint-dirty** (a helper exists with no callers); this trap's intermediate state is **lint-clean but structurally inconsistent** (some sections wrapped, others not). The linter doesn't strip anything; the cost is review-quality + edit-fragility.

Cure: when applying the same conditional/wrapping pattern at N>3 sites in the same file, use a single `Write` over the final content, OR a single Edit with a `replace_all` pattern that captures all sites at once. Rule of thumb: *N>3 same-shape wraps in one file ⇒ Write, not Edit.* The Write is one atomic restructure; the diff is one hunk; the linter sees the final state only.

See failure mode #51.

### SSR / client hydration mismatch with module-level state

Recurs in any campaign touching client state that persists across reloads (theme, auth, locale, feature flags, role hint, last-route). The trap looks like this:

```ts
// store/theme-store.ts
function readStored() {
  if (typeof window === 'undefined') return 'light'   // SSR fallback
  return localStorage.getItem('lex-theme') ?? 'light'
}

export const useThemeStore = create((set) => ({
  mode: readStored(),   // called at MODULE LOAD time
  ...
}))
```

In Next.js App Router, the Client Component module is evaluated during server-side RSC rendering. At that point `typeof window === 'undefined'` is true, so `readStored()` returns the SSR fallback. The store ships in the client bundle with `mode: 'light'` baked in, **even though localStorage actually has `'dark'`**. The `useEffect` that applies the theme runs with the stale value and never corrects itself because `mode` never "changes" — it was always `'light'` from the client's perspective.

Symptoms:
- Storage has the correct value (`localStorage.getItem(...)` returns `'dark'`)
- The visual outcome reflects the SSR fallback (light theme renders)
- `useEffect` fires once and applies the fallback value, then never re-fires
- A `MutationObserver` on the affected attribute shows zero changes
- `tsc` and `lint` are completely green

**Two-layer fix** (apply both — they cover different failure points):

1. **Synchronous bootstrap in root layout `<head>`** — prevents FOUC by setting the attribute before first paint, before any React code runs:

   ```tsx
   // app/layout.tsx
   <html lang={locale} dir={dir}>
     <head>
       <script
         dangerouslySetInnerHTML={{
           __html: `(function(){try{var t=localStorage.getItem('lex-theme');var dark=t==='dark'||(t==='system'&&window.matchMedia('(prefers-color-scheme:dark)').matches);document.documentElement.setAttribute('data-theme',dark?'dark':'light');}catch(e){document.documentElement.setAttribute('data-theme','light');}})();`,
         }}
       />
   ```

   Do **not** hardcode `data-theme="light"` on the `<html>` element — that's exactly what creates the SSR/client gap.

2. **Mount-time re-sync `useEffect` in the Client Component provider** — closes the gap when the store was initialised with the SSR fallback:

   ```tsx
   useEffect(() => {
     const stored = localStorage.getItem('lex-theme') as ThemeMode | null
     if (stored === 'dark' || stored === 'system') setMode(stored)
     // eslint-disable-next-line react-hooks/exhaustive-deps
   }, [])
   ```

   Alternative: replace the bare `create()` with Zustand's `persist` middleware and `skipHydration: true`, then call `useStore.persist.rehydrate()` in the provider's mount effect. Same idea, more machinery.

When a campaign migrates components to use a client store (theme, auth, locale, role), Step 1.2 Q9 must include a browser recipe that reloads the page with a non-default storage value and verifies the outcome — otherwise this trap will pass every `tsc + lint` and ship broken. See failure mode #20.

---

## The checkpoint pattern (when external data is unreachable)

If a subagent can't verify something at campaign time (DB pooler down, third-party API throttled, MCP unavailable; prod telemetry not yet available, post-deploy probe queued), don't guess. Insert a marker:

```
<!-- CHECKPOINT: CHK-<id> - short description - expected: <value or "unknown"> -->
```

Then add a row to `CHECKPOINTS.md` in the campaign folder. The doc can ship with the marker visible — readers see "we don't know yet" rather than a false claim.

When the blocker clears: run all queries, resolve every marker, and emit a follow-up vault-log entry.

Full pattern in [references/checkpoint-pattern.md](references/checkpoint-pattern.md).

---

## Standing principles

These are the always-on disciplines. Every campaign honours them; they're not "watch-out traps" but the default posture. Numbered P1-P7 to distinguish from numbered failure modes. If a principle is violated, that's a campaign failure, not a "consider this" — fix and continue.

| # | Principle | Source |
|---|---|---|
| P1 | **W0 runs when Ollama is available.** Free tokens. Pre-scan compresses every W1 subagent's exploration. Skip only via documented reasons (small scope, content-only, predecessor reuse — see §0.5.1, §0.5.2, §0.6) recorded in `w0_enabled:` frontmatter. | §0.2, originally failure mode #1 |
| P2 | **Plan carries the model assignment table.** Every Agent call listed with subagent type + model + effort + output file. No table → plan cannot be approved. | §Step 2, originally failure mode #2 |
| P3 | **Execution does not stop for resolvable forks.** Autonomous decision ladder (§Autonomous decision framework) handles every choice that isn't irreversible + high-risk. Stopping mid-execution means the planning interrogation was incomplete; flag for next campaign. | §Autonomous decision framework, originally failure mode #3 |
| P4 | **Conformity over invention.** Read the project's pattern docs + the reference implementation's full render function BEFORE writing. Match existing visual hierarchy, token usage, naming conventions. Inventing a new style is a campaign failure. | §Conformity discipline, originally failure mode #4 |
| P5 | **Consolidation over copy-paste.** N=3 alarm fires on both file-clone shape (failure mode #27) AND union-prop modes (failure mode #58). Extract before composing N times. | §Consolidation discipline, originally failure mode #5 |
| P6 | **Vault-log writes immediately at §5.3.** Not "later", not "when asked". P8 of CLAUDE.md mandates per-change logging; campaigns are no exception. | §5.3, originally failure mode #7 |
| P7 | **Dead code deleted at §5.1.** Replaced components + legacy shims removed via grep-proof + `rm`. Plan lists candidate-deletions only; cleanup phase authorises actual removal. | §5.1 |

The numbered "Common failure modes" below are specific traps with cure pointers — distinct from principles, which are paradigm-level standing rules.

---

## Trigger-phrase precedence

Multiple gates can fire on one user prompt (e.g. "fix the broken modal mess" could match §1.4 vague-symptom AND §1.4.1 ambiguous-direction). Apply in this order; earlier rule wins; later rules only fire if earlier didn't:

| Order | Trigger | Section |
|---|---|---|
| 1 | Resume in-progress campaign on disk | §0.0 |
| 2 | Same-session pivot (predecessor closed this session, user names a deficit) | §0.0.1 |
| 3 | Pivot-chain (≥2 prior pivots on same predecessor) | §0.0.3 |
| 4 | Post-closure tweak (predecessor closed within ~7 days) | §5.8 |
| 5 | Reflection-pass on closed campaign | §Step 6 |
| 6 | Vague-symptom verb (Part A reproduction needed) | §1.4 |
| 7 | Ambiguous-direction migration verb (keeper-side question needed) | §1.4.1 |
| 8 | Standard §1.2 planning interrogation | §Step 1 |

If a prompt matches order 2 AND order 6 (e.g. "fix the broken sidebar — you missed it during the just-shipped campaign"), the same-session pivot wins because the predecessor's discovery + scope is already valid; the vague-symptom Part A reduces to "screenshot or specific defect?" inside the pivot phase, not a fresh investigation.

If unclear which fires, default LATER rather than earlier (don't auto-bind to a pivot if the predecessor is stale; fall through to §1.4 or §1.2). Wrong-direction binding is more expensive than over-cautious re-interrogation.

---

## Common failure modes

1. **Skipping W0 when Ollama is available.** *Now a standing principle (P1).* Free tokens wasted. Every Claude subagent re-explores from scratch instead of compressing against the pre-scan.
2. **Missing model assignment table in the plan.** *Now a standing principle (P2).* No audit trail for which model did what. Token spend is unaccountable.
3. **Stopping mid-execution to ask the user.** *Now a standing principle (P3).* The planning interrogation exists to prevent this. If Claude is stopping, the interrogation was incomplete — note it for next time.
4. **Inventing a new style instead of following the existing one.** *Now a standing principle (P4).* The app already has a design language. Claude builds a page that looks different from the other 26 admin pages. The conformity discipline exists to prevent this.
5. **Copy-pasting patterns instead of extracting.** *Now a standing principle (P5).* The campaign creates more duplication than it resolves. The consolidation discipline exists to prevent this.
6. **Forgetting dead-code cleanup.** Legacy components left behind after migration. The cleanup plan in Step 2 and the deletion step in Step 5 exist to prevent this.
7. **Skipping the vault-log.** *Now a standing principle (P6).* The log must be written immediately at Step 5, not "when the user asks."
8. **Audit mode — Trusting a graph hypothesis without code verification.** Always verify before recommending a refactor.
9. **Audit mode — Skipping the synthesis step.** Without `99-synthesis.md`, the doc rewrites drift from the evidence.
10. **Build mode — Running `apply_migration` without approval on a red-gated phase.** Even under `autonomous` cadence, red phases always gate.
11. **Build mode — Skipping the risk sweep.** `99-risk-sweep.md` catches "we fixed Insights but broke Notifications because they share a trigger."
12. **Both modes — Leaving the campaign plan with `status: in-progress` after finishing.** Update it to `completed`.
13. **Both modes — Stalling after the plan.** If the plan is approved, execution begins immediately. The 37% stall rate in past campaigns happened because this wasn't enforced.
14. **Pre-committing deletions in the plan.** The plan promises "delete X, Y, Z" before any consumer audit. Reality: most candidates are still load-bearing after the migration — chrome moved but the inner content stayed (legacy filter bars, summary bars, topbars often survive a chrome migration intact). The plan must list **candidate** deletions, the cleanup phase must grep-prove orphan status before any `rm`, and the change-log must honestly record what was kept vs deleted.
15. **Mass-rename without a gate.** Standing "don't pause until done" instructions don't cover architectural one-way doors. A 25-file namespace move is reversible only at the cost of a churn cycle. Any phase that mass-renames imports across >15 sites, moves a top-level namespace, or alters a public component name must hit a single-question `AskUserQuestion` gate first — even under `autonomous` cadence. 30 seconds of approval beats hours of rollback.
16. **Ollama prescan ANSI/thinking-trace pollution.** Piping `ollama run` straight to `tee`/file captures spinner frames and `Thinking…/…done thinking` lines from chat-tuned models. The artifact is unreadable. Always pipe through the sed/grep filter in §0.5.
17. **Preview-verification thrash on every Edit.** PostToolUse hooks may remind you to preview-verify after every observable edit. During an in-flight mass refactor the build is intentionally broken between Edits; preview verification then is meaningless. Verify at **phase exit only**. *Clarification for single-turn cosmetic phases:* when a single Edit completes the entire phase (one component, one property, no in-flight refactor), the turn IS the phase — run preview verification once at the end of that turn. Ignore the hook only when the build is *known* to be broken mid-refactor; honor it when the build is whole and the turn is closing.
18. **Build toolchain cache (Turbo) masking pre-existing errors.** `npx turbo run check-types` returns a cached "pass" when Turbo's task hash hasn't changed — even after file edits, if those files are not in Turbo's tracked input set for the `check-types` task. On the *first* verification run per phase, always add `--force`: `npx turbo run check-types --force`. When the forced run surfaces errors in files you never touched, confirm with `git log -- <file>` or a grep that they predate the campaign — then document them as `CHK-<id>` items and continue. The same trap applies to lint: a "green" result before your edits is only trustworthy if the cache was cold. Never treat a cached "pass" as ground truth; never attribute pre-existing errors to the campaign.
19. **UI consolidation: matching visual hierarchy requires reading the full render function.** The first draft of a new row/card component looks structurally wrong (flat table-like columns) even when it reuses the correct design tokens — because it was modelled from the old component's structure rather than from reading the reference component's full render JSX. The conformity discipline says "match the reference implementation's structure exactly," but that only works if you actually read the reference's complete render tree. Import lists, prop types, and component signatures don't reveal layout hierarchy. Read the full render function before drafting any UI component; extract the named line-levels (e.g., "Line 1: row# + headline + actions | Line 2: icon-label metadata | Line 3: chips") explicitly.
20. **`tsc + lint` green = false-confidence trap for client-state features.** For UI / theme / auth / hydration / realtime / locale / i18n campaigns, compile-time checks confirm that the code parses and types match — they cannot detect a broken user-facing outcome. The dark-mode rollout v1.0 shipped P0–P4 with a green type-check + lint while the actual visible feature was broken on every non-admin page (SSR-hydration mismatch in the Zustand store + FOUC in the root layout — see § Environment hazards). Browser verification at phase exit is mandatory for these surfaces, not optional. The risk sweep's surface coverage matrix needs evidence (screenshot, polled DOM read, console log, network call) behind every "✓" — not intent. Status marks assigned from "I think this works" instead of "I observed this work" are how broken features ship behind a passing build.
21. **Diagnostic state pollution.** When debugging a hydration / DOM / storage bug, manual pokes during evaluation (`document.documentElement.setAttribute(...)`, `localStorage.setItem(...)`, `window.__store__.setState(...)`) persist into subsequent verification reads in the same page session. Without a `location.reload()` between "set state to debug" and "read state to verify," the next read sees your manual mutation, not the system's natural behavior — leading to false "it works!" conclusions that evaporate on a real fresh load. Discipline: always reload (or open a clean tab/incognito) between any manual state poke and the next observation. Treat verification reads as if they're snapshots from a cold cache. The dark-mode rollout v1.0 burned 6+ diagnostic evals on a phantom "ThemeProvider works on /login" finding because an earlier eval had manually set `data-theme="dark"` and that mutation persisted across the next read.
22. **Design-language matching from the wrong or stale reference.** When the user says "match X page's button style" or "match X's design language," the style lives in X's action-bar or primitive component, not at the page-level row. `DocListRow` delegates to `DocActionBar` which uses `TableActionBtn` (solid navy); `TaskListRow` delegates to `TaskListActionBar` which uses ghost buttons — these are two hops down from the row. Reading only the row gives you the wrong picture. Follow the import chain to the leaf component. Also: the reference may have been edited during the current session by the user or a parallel agent — re-read it immediately before implementing, not just at planning time. A cached mental model of what X's buttons look like is unreliable.
23. **Cascading-default leak.** A phase changes a shared primitive's visual default (filled→ghost, navy→transparent, `C.white` → `C.navy`, etc.) and stops at the primitive's definition file. Every consumer that passed an explicit prop override against the OLD default — e.g. `<TableActionBtn iconColor={C.white} />` chosen to read against navy bg — is now silently broken (invisible icon on the new transparent bg). The breakage doesn't surface in `tsc` or `lint`; it surfaces as N follow-up one-shot turns ("the flag is invisible", "the container button is washed out", "the task pin is gone") that each look small but compound into hours. The §W3 stale override sweep is the gate. If a phase changes a default and skips the sweep, every override that overrode the OLD default is a latent bug planted in the codebase. Pair this with §Consolidation discipline rule #4 (grep before changing a shared default): the grep is the *input* to the sweep, the sweep is the *action* on the grep's output.
24. **Post-closure tweak drag.** The campaign closes — vault-log lands, status set to `completed`, risk sweep filed. The user then fires N short imperative tweaks over the following days that touch the same surface: "fix X too", "match Y", "also Z's color is wrong". Each is handled as a fresh one-shot turn, bypassing the sibling sweep, the conformity audit, the re-anchor check, and the stale override sweep. The campaign technically shipped but the work is still ongoing in disguise — and worse, the predecessor's risk sweep is no longer accurate because the surface has drifted past it. §5.8 (Post-closure tweak detection) classifies each tweak as stub-extension (log against the predecessor) or mini-extension (re-open as EXTENSION mode). The trigger phrase "**fix X too**" specifically signals that the predecessor's Step 4.5 re-anchor missed an adjective from the original framing — re-read the re-anchor before acting. A tweak that touches the campaign's surface and never gets logged against the campaign is the campaign equivalent of a silent write.
25. **Same-session mid-flight pivot misclassified as a new campaign.** The user invokes `/conquering-campaign` a second time in the same session — minutes after the first one closed — because they visually inspected the just-shipped work and pointed at a deficit ("you still have lots of work to match UI"). The state falls between every existing classification: §0.0 resume only catches `in-progress` campaigns; §Step 4 W4-discovered only catches defects during W4; §5.8 post-closure only catches tweaks days later. Without a dedicated classification the skill re-runs Step 0 in full — wasteful Ollama probe, duplicate plan file, duplicate vault log — even though the predecessor's prescan + discovery are still in-context and still valid. §0.0.1 (Same-session pivot detection) is the cure: skip W0, append a phase to the existing plan with `discovered_during: same-session-pivot`, edit the vault log in place. The signals to detect: predecessor's vault-log was written this session + user names a deficit + predecessor closed less than ~30 minutes ago. If signals are mixed, fall through to §5.8 instead — same-session pivot is a strictly tighter window with a strictly cheaper procedure.
26. **Plan named the reference but never extracted its render structure.** The campaign plan says "model `InsightsList.tsx` on `FilesList.tsx`" and stops there. The W3 implementation reads `FilesList.tsx`'s imports, prop types, and component signature — none of which reveal that `FilesList` renders `TableShell + flex column gap:6 + FileListRow` cards, not an HTML `<table>`. The agent then drafts the target component around whatever shape the *old* code (or the wrong mental model) suggests, and ships a structurally-wrong file that compiles cleanly. Failure mode #19 names the discipline ("read the full render function"); v1.4.0 makes it a *required plan section* (`## Reference render structure`) and a *required pre-execution gate* (§Step 3 W3 step 1.5a). Both fire before the first Write call. The block must record what the reference *renders* — outer wrapper, named lines, hover/transition, leaf primitives — not what it imports or signs. Without enforcement at plan-time and write-time, #19 is a prose recommendation the agent can read, agree with, and skip.
27. **Nth hand-rolled clone of a recurring shape.** The campaign creates a 3rd `*ListRow.tsx` that mirrors `FileListRow.tsx` and `BalanceListRow.tsx` line-by-line (Line 1: rowNum + headline + actions; Line 2: status chip + metadata) — but doesn't compose `ListRowBase` or any other base primitive. `tsc + lint` pass; the file ships; the codebase ends up with three structurally-identical card-row implementations. The Consolidation discipline says "if 3+ files use the same pattern, extract" — but the check fires at *plan time* against whatever inventory the agent listed. If the inventory missed the base primitive (because the plan-phase didn't grep for it), the discipline never triggers. §Step 3 W3 step 1.5b is the cure: a write-time grep that counts sibling implementations of the file shape *before* the Write call, plus a re-read of CLAUDE.md / FRONTEND.md for the expected base component name. Hand-rolling the Nth clone is the campaign violating its own consolidation contract — leaving the codebase with more duplication than it found.
28. **Multi-Edit atomicity trap.** A phase plans two sequential `Edit` calls to the same file: `Edit #1` adds a helper (e.g. `ghostHover`/`ghostLeave` functions for hover handlers); `Edit #2` adds the call sites that consume the helper. The aggressive PostToolUse linter fires *between* the two Edits, sees the helper as `no-unused-vars` under `--max-warnings 0`, and **strips it from the file**. `Edit #2` then either fails (anchor missing) or compiles to a broken state where the call sites reference deleted symbols. The fix is structural, not vigilance: when a phase needs ≥2 sequential Edits to the same file *where the intermediate state would fail lint*, use a single `Write` over the whole final content instead. The `Write` is atomic; the linter only sees the final, consistent state. The `Edit` tool is for *consistent* incremental changes; chained Edits with lint-dirty intermediate states are a misuse. See §Environment hazards → Aggressive PostToolUse hooks.
29. **TodoWrite list survives across same-session campaigns.** A new campaign starts in a session that already ran a previous campaign. The TodoWrite list still carries `[completed] Phase 2: Create TasksActionBar` from the earlier campaign; the harness reminds the agent about stale items mid-flight (one wasted turn each); a partially-completed `[in_progress]` item can mislead the next agent invocation about what's actually live. The fix is mechanical: §0.0.2 mandates a `TodoWrite` reset before any W0/W1 call in a fresh campaign. The list is session-scoped; campaigns are not — the discipline must reconcile them at every campaign boundary.
30. **W0 prescan ships echo-back garbage and downstream agents cite it as ground truth.** Local Ollama (especially smaller models on long file lists) sometimes produces output that mirrors the prompt's structure (the requested `## 1. ... ## 2. ...` headers) without inserting any actual file insight — instead of `tasks/page.tsx — 1190 lines` you get `<file> — <line count>`; instead of `mutations: cases.ts, tasks.ts` you get `<list names>`. W1 subagents told to "read the prescan as pre-loaded context" then hallucinate against an empty signal. The current skill's "W0 mandatory when Ollama is available" rule presumes the prescan *contains* signal; it doesn't validate that. §0.5.1 (prescan quality gate) is the cure: read the written prescan against a checklist of concrete signals (line counts, real entity names, named files in the surface map), mark `w0_useful: no` when the model echoed back, and instruct W1 subagents to read files cold instead of citing the prescan. Also: skip W0 entirely for builds touching <10 files — the prescan's compression payoff doesn't exist when there's no fan-out to amortize.
31. **Standing instructions silently inherited across same-session campaigns.** A user's "work without stopping for clarifying questions" set in campaign 1 of a session silently propagates through campaigns 2, 3, 4 in the same session — the planning interrogation is effectively waived (Step 1.2 "if the user's prompt already answers some of these, don't re-ask"), but the override is never *recorded* in the new plan. Future readers of campaign 4's plan see `approval_cadence: autonomous` but don't see the user's literal phrasing that produced it; the next agent invocation in the session can't tell whether the standing instruction still applies or was lifted. The fix: §1.2 Q13 + §Step 2 `standing_instructions:` frontmatter field force every new campaign to quote the verbatim instruction and name the predecessor it was set in. If the user wants it lifted, they say so during the (now-shortened) interrogation; otherwise it's in force *and visible in the plan*. The approval-cadence field captures the posture; standing-instructions captures the words.
32. **W1 subagent mis-locates a DB column and the migration body inherits the error.** A discovery subagent claims `is_programmer` lives on `council_members` (the conceptual home of a member's identity); the W2 phase plan writes RLS policies and grant logic against that table; W3's first `apply_migration` returns `ERROR: 42703: column cm.is_programmer does not exist`. Cost: one failed migration + the time to re-investigate via `information_schema.columns` and find that `is_programmer` actually lives on `admin_perms` (a permission-overlay table). Under a more autonomous cadence (or a less-watching user) the migration body could ship with a stale assumption that an `apply_migration` returning `{"success": true}` after a wider-shaped retry would mask. W1 subagents reliably hallucinate column locations in three patterns: (a) tables renamed mid-history, (b) columns conceptually "belonging" to one entity but living on an overlay table, (c) views that expose a column from a join. The cure is §Step 3 W3 step 1.5d: before writing the migration body for any phase that depends on a W1 structural claim, run an `execute_sql` against `information_schema.columns` / `pg_policies` / `pg_views` and confirm. Build-mode mirror of failure mode #8.
33. **`apply_migration: success` trusted as ground truth after a prior failed retry.** A migration fails on attempt 1 (RLS policy referenced a nonexistent column), gets fixed, retries successfully on attempt 2 — the `{"success": true}` response is then taken as confirmation that the table, RLS policies, view (with `security_invoker = true`), and trigger all landed as specified. They might not have. `CREATE OR REPLACE VIEW` silently drops `security_invoker` (failure mode for add-new-view skill); RLS policies can apply with a different qual than the migration body if a partial earlier migration left state behind; triggers can fail-without-error if `set search_path = ''` was omitted. The success response cannot distinguish a clean apply from a partially-applied or wrong-shape apply. Cure: §Step 3 W3 step 2a — post-migration ground-truth SELECT against the live schema (table existence, column types, policies' `qual` text, view's `reloptions`) recorded as evidence in the phase change-log. This is also where the post-flight check belongs in the §P13 self-audit table in the vault-log.
34. **Phase plan tries to inline >5KB of generated content and either truncates or blows past the planning subagent's response budget.** Campaigns that generate translation bundles, fixture sets, seed data, or message catalogs often need to produce 10s-100s of KB per phase. The planning subagent is asked to pre-draft the full content in the phase-plan file; small artifacts pre-draft fine, but a 75KB `public.json` for one of 6 locales overflows the response, gets silently truncated, or arrives with hallucinated middle sections. The campaign technically "succeeds" but the plan file is not the artifact's source of truth — the W3 implementation has to regenerate from scratch anyway. The cure is §Step 2 `generation_strategy: deferred-parallel-subagents` — the plan stores the *spec* (target path, source-of-truth locale, expected key count, sampling rule), not the content; W3 spawns parallel subagents per file that write directly to disk; the change-log records file sizes shipped + a 5-10 line diff sample per file as evidence. Plan-time inlining is for content the agent can produce in one shot; generation-strategy is for content that must be produced in fan-out.
35. **"Page renders + no console errors" verification skips the campaign's actual value (CRUD/editor/multi-step features).** A campaign ships a translation editor / form builder / multi-step wizard / inline-CRUD page; phase-exit verification opens the page, confirms entities load, takes a screenshot, checks console errors clean — and marks the phase complete. The Save button was never clicked. The Revert button was never tested. The persistence-across-reload check never ran. The W4 risk sweep's surface coverage matrix shows "✓ verified" against the editor surface based on render-only evidence. This is the strict successor to failure mode #20 — `tsc + lint green = false confidence` for client-state features. Render-passes-without-error is *weaker than* that same trap because the build's correctness signal is at least binary; "the page rendered" is satisfiable by a completely broken write path. The cure is two-fold: §Step 1.2 Q9 requires BOTH a render recipe AND an interaction recipe for any CRUD/editor/form/multi-step feature; §Step 2 plan template requires every FE phase to declare `verification_class: render | interactive`; phases marked `interactive` cannot be verified by the render recipe alone. The interaction recipe must include the round-trip (write → reload → confirm persisted → revert → reload → confirm restored). A campaign that ships an editor where the user never clicked a cell at phase exit is shipping on faith.
36. **Pre-existing runtime errors get attributed to the campaign or vice-versa.** Preview verification surfaces a console error like `MISSING_MESSAGE: admin.components.attributes.title.no_documents`. Without provenance check, the error is either (a) ignored as "pre-existing" without evidence and the phase ships with a latent attribution risk, or (b) attributed to the campaign and chased down for hours — only to discover it predates the campaign by weeks. The runtime mirror of failure mode #18 (Turbo cache hiding pre-existing *compile* errors): you can't tell pre-existing from campaign-introduced by inspection alone. The cure (§5.2 runtime error provenance note): `git diff <campaign-start-sha>..HEAD | grep -F '<error-substring>'`; if absent → `spawn_task` to flag and continue; if present → phase blocker. Provenance check first, classification second, action third — never skip step 1.
37. **Same-session pivot-chain accretes scope past artifact recognisability.** §0.0.1 cleanly handles ONE pivot. By pivot 3+, the per-pivot close-out overhead (flip plan status, append vault-log, write phase file, run tsc/lint, re-close plan) dominates real work — and worse, the campaign drifts past its named shape. The "Actions tab" campaign ends with 11 phases, 2 DB tables, an LLM-classification pass, and a visual divergence audit; the vault-log entry runs 200+ lines summarising work that has nothing to do with the original campaign's name; future readers can't find the visibility-audit deliverable because they wouldn't think to look under `_dev-tools-actions-tab/`. §0.0.3 is the cure: detect the chain (≥2 prior pivots + plan has >6 phases + new pivot adds new surface area), batch the close-out (flip status once at chain start, not per pivot), and present a single spin-off `AskUserQuestion` gate ("keep chaining or spin off as a new campaign?") whose answer becomes a standing instruction for the rest of the chain.
38. **Preview verification claimed as "deferred" every phase under a permanent auth wall.** Every phase exit logs "preview verification deferred — login wall" and moves on. The cost is N wasted `preview_eval` / `preview_snapshot` / `preview_list` calls per phase × N phases (typically 3-6 calls × 10+ phases = 30-60 wasted tool uses per campaign) plus the cognitive weight of pretending verification *might* happen next phase. §0.0.4 is the cure: one probe at session start (curl the gated route, check for `/login` redirect or `Loading your workspace` body), set `preview_verification: blocked-by-auth` in plan frontmatter when confirmed, and stop adding preview steps to phase checklists for the rest of the session. Code-only verification is *enough* under this flag — make that claim explicit, not euphemistic.
39. **Long-running batch script with stdout buffering = opaque 15-minute wait.** A codegen script that calls Ollama per function (92 mutations × 5-15s each) runs `console.log` after every call — but Node's stdout is line-buffered to a non-TTY, so `tail -f output.log` shows zero lines until the script exits. The user sees 15 minutes of silence and reasonably assumes hang. The cure is structural, not patience: any subagent-spawned or background-spawned batch script that loops N>20 items MUST write progress to a sidecar file via `fs.appendFileSync('<path>/progress.log', '<line>\\n')` after each iteration, NOT via `console.log`. The main thread can `tail` the sidecar in a Monitor or Bash poll loop and see real progress. Bonus: the sidecar survives a kill mid-flight, so resume becomes possible. Long-running batches without per-iteration sidecar logging are opaque waits in disguise.
40. **Pivoting to a different strategy mid-batch discards N partial calls.** The Ollama-summarize batch ran ~80/92 calls when the user pivoted to a DB-backed approach; the script writes the manifest only at end-of-run, so all 80 successful summaries were discarded by the kill. The cure is two-layer: (a) any long-running batch >5min must checkpoint incrementally — write the partial output to disk after every K iterations (K=5 for ≤100 items, K=20 for >100) so a mid-flight pivot can at least salvage what completed; (b) before launching the batch, the skill should pause for one `AskUserQuestion` confirming the strategy when the work will take >5min — "I'm about to run 92 Ollama summarisations, ~5min total. Confirm strategy or pivot before launch?" — to catch strategy reversals BEFORE the spend, not after.
41. **File mutated by background tooling between Read and Edit (long-pause variant).** Failure mode #28 covers the multi-Edit atomicity trap within a single turn. The long-pause variant: between waiting for a subagent / Monitor / MCP call to return (often 30s-5min), the file you intend to next Edit has been silently mutated by a PostToolUse linter, IDE formatter, or another agent in parallel — your next Edit returns `File has been modified since read`. Symptom is identical to #28; the cause is *temporal distance from your last Read*, not chained Edits. Cure: after any wait >30s (subagent, Monitor stream end, MCP round-trip, sleep), re-Read the next target file before the next Edit. The Read is cheap; the failed Edit + recovery is not. Add to the §Subagent dispatch best practices and §Self-verification loop sections.
42. **Source-walk subagent output bypasses the JSON-on-disk pattern.** When a subagent needs to inspect many files (92 mutations, 108 callsites, 36 visual signatures, etc.) and report results to the main thread, the natural temptation is for the subagent to return findings inline in its response. The inline return then has to be parsed by the main thread, often via a fragile regex, and the findings become invisible in the campaign folder. Cure (codified pattern): every source-walk subagent MUST write its full findings as JSON to `docs/build-campaigns/<id>/NN-<topic>.json` and return only a short summary inline (counts, top items, anomalies). The main thread builds SQL / UI / report from the JSON file; the campaign folder retains it as evidence. Three uses in one campaign (descriptions, callsites, classifications) shows the shape is reusable enough to deserve a named template — see §Source-walk subagent template in §Subagent dispatch best practices.
43. **DB sub-pattern reinvented per phase instead of named.** Three phases in the same campaign followed the identical shape: (1) `execute_sql` to probe `information_schema` / `pg_policies` / `pg_views` for existing patterns to mimic; (2) draft the migration SQL inline in the conversation; (3) `AskUserQuestion` showing the SQL with options Apply / Tighten / Hold; (4) `apply_migration` on approval; (5) `execute_sql` post-flight check counting rows + recording per-form / per-status aggregates. Each phase re-invented the shape from scratch. Cure (codified pattern): name it the **probe-draft-approve-apply-verify (PDAAV) DB sub-pattern**. The §Step 3 W3 step 1.5d (subagent reality-check) is the *probe*; the new §Step 3 W3 step 2a (post-migration ground-truth check) is the *verify*. The draft + approve + apply steps are already documented in P3 (No Silent Writes). Naming the chain lets future campaigns reference "applied PDAAV" in their plan instead of re-describing the same five tool calls.
44. **Symptom diagnosed from code, not from observation (bug-investigation variant of #20).** User reports a vague symptom ("kinds shows nothing", "audit doesn't work", "looks weird"). The skill jumps to code/DB introspection, picks one of N hypothesised root causes, ships a fix, marks the phase done on `tsc + lint` green. The user's actual symptom — which could have been a different internal state (stuck loading, error toast, empty filtered array, JS exception, layout collapse, RLS denial) — was never reproduced or verified. The cure is §1.4: when the trigger contains a vague symptom verb mixed with imperative fixes, the planning phase MUST split into Part A (reproduce symptom + confirm interpretation with user) and Part B (plan fixes). Part A is one short question if preview is auth-blocked. The cost of asking is ~30 seconds; the cost of fixing the wrong cause is the campaign's full close-out plus a follow-up campaign to undo. This is the strict variant of failure mode #20 for *bug investigations* — #20 covers "tsc+lint green doesn't prove the feature works"; this covers "tsc+lint green doesn't prove the bug was fixed."
45. **Express-mode acknowledgment gap — full pipeline run on small builds.** User explicitly invokes `/conquering-campaign` on a 4-file fix + 1 migration. The skill either (a) refuses ("this is overkill, do it inline") and rejects the user's explicit choice, or (b) runs the full pipeline (W0 probe, W1 discovery, W2 phase plans, W3 per-phase files, W4 risk sweep, 10+ artifacts) producing ceremony that exceeds the work. The result is that users stop invoking the skill for small things because the cost is too high, and the discipline never gets applied to the cases where it's still valuable (verification, vault-log, P13 audit, schema verification before migration). Cure: §Step 2 `scope: small` express mode declares explicit trims for ≤5-file + ≤1-migration builds — skip W1/W2/W3-per-phase-files/99-risk-sweep, keep §1.4 + §1.5d + §2a + §2a-RLS + §5.3 + §5.4. Required frontmatter shrinks; required discipline doesn't. "I'll skip whatever I want" is not express mode; declared trims are.
46. **Vault-log + campaign-plan split across docs roots (monorepo wikilink breakage).** Project has TWO docs roots: workspace-level `/docs/` and nested `<app>/docs/`. CLAUDE.md's P8 rule puts vault-logs at `<app>/docs/vault-logs/`; the skill's default puts the campaign-plan at `docs/build-campaigns/` (workspace root). The vault-log wikilinks to `[campaign folder](../build-campaigns/...)` — which from inside `<app>/docs/vault-logs/` resolves to `<app>/docs/build-campaigns/`, which doesn't exist. Future readers can't trace either link. Cure: §0.0.5 monorepo artifact-root probe at session start; resolve `campaign_folder_root` and `vault_log_root` once and record both in plan frontmatter; co-locate by default (campaign-plan goes under the same parent as vault-logs).
47. **RLS qual-text matches ≠ effective-access matches.** A migration changes an RLS policy's `qual` from `(notifications_vap = true)` to `(notifications_vap OR is_programmer)`. The post-flight check verifies the new `qual` text via `pg_policies` and marks the phase complete. But effective access depends on: policy permissive/restrictive flag, OTHER policies on the same table, grants for the `authenticated` role, RLS-enabled flag, and the calling view's `security_invoker` setting. The policy text could match intent while a different layer blocks the user — e.g., a restrictive policy on the same table, or a wrapping view set to `security_invoker=false` that bypasses RLS entirely. Cure: §3 W3 step 2a-RLS — run a representative SELECT under a simulated authenticated context for both an admit-user and a deny-user, recording counts in the change-log. Text-matches-intent is necessary; effective-access-matches-intent is sufficient. Also: when a phase bundles ≥2 changes touching different access-control layers (RLS + grant, grant + view-security, etc.), assign sub-phase IDs and verify each layer independently (§3 W3 step 2b — phase atomicity). One `apply_migration` call is fine; one verification line per layer is required.
48. **Dev-server module cache for newly-added JSON keys (runtime mirror of #18).** Adding a key to `messages/<locale>/<ns>.json` (or any other dynamically-imported JSON) mid-session does not trigger HMR. The dev server's `await import('...json')` was evaluated at startup; the parsed object is frozen in module-level cache. Runtime `t('new.key')` falls through the i18n library's `getMessageFallback` and renders the raw key path as button text — e.g., `admin.nav.files_menu.dev_tools` literally rendered inside a `<NavRow>`. `tsc + lint + git blame` all green; the static JSON on disk has the value; the DB has no override. Detection trio: (a) raw key path renders in the UI, (b) `git blame` shows the key on a line marked `00000000 (Not Committed Yet)`, (c) sibling keys in the same JSON object render fine. All three present ⇒ stale dev-server JSON cache; restart the dev server. The cure is *not* a code change. Add to §Environment hazards → "Runtime module caches that don't HMR" alongside the SWC bundler stale-parse symptom (phantom symbol reference at a line that doesn't contain that symbol in the current file). Umbrella discipline: *if the runtime symptom contradicts the current file on disk, restart before diagnosing.*

49. **Sidebar nav primitive lock-in violation (specific case of #27).** A new sidebar card (Sections nav, tab switcher, view picker) hand-rolls a `<button>` instead of using the project's canonical nav-row primitive (`PortalNavRow` in lex_council). The hand-rolled button silently re-invents active-state styling — and gets it wrong: `background: <some active token>` paired with `color: <same family token>` ships text the same color as the background → invisible label on a solid rectangle. `tsc + lint` green; visual regression invisible to the type system. The View card sitting two cards above the broken Sections card was the working reference — reading it for 30s before writing would've shipped the right primitive first time. This is the highest-frequency violation site for #27 because sidebar buttons feel "trivial" (just icon + label) and the cost of forking the visual language is hidden until the active state renders broken. Cure (§Conformity discipline → "Sidebar nav lock-in"): any `<button>` inside `<SidebarCard>` that participates in a list of selectable items uses the canonical nav-row primitive — no exceptions for "dev-only" panels. Detection at write-time: about to write `<button>` inside `<SidebarCard>`? Stop, grep for the project's nav-row, use it.

50. **Single-property follow-up tweak shouldn't re-enter campaign machinery.** v1.8.0's `scope: small` express mode trims W1/W2/W3/W4 artifacts but still demands a campaign-plan file + frontmatter + memory entries + execution log section. For a 4-line CSS tweak ("active state wrong color"), the plan file alone exceeds the patch's size. The user invokes the skill, gets ceremony exceeding the work, and over time stops invoking the skill for small tweaks — exactly the cases where the §1.4 reproduction gate, vault-log entry, and tsc+lint discipline are still valuable. Cure: §Step 2 `scope: micro` for ≤2 files + ≤10 lines + no new artifacts. Allowed elisions vs express: no plan file (conversation IS the plan), no per-phase log, no memory entry unless surprise. Kept mandatory: §1.4 reproduction gate, tsc + lint at exit, preview verification, §5.3 vault-log entry (P8 non-negotiable regardless of scope). Trigger phrases: "fix this", "the X is broken", named-property + observable-defect. Routes the smallest tweaks into the lightest discipline that still preserves P8 + diagnostic correctness.

51. **JSX structural pivot via chained Edits.** Sibling case of #28 (multi-Edit atomicity trap). Wrapping N>3 JSX siblings with the same conditional pattern — e.g., converting "render all sections" to "render whichever section is active" by adding `{activeSection === '<id>' && <div>` around each section — done with N chained Edits has three weaknesses: (a) each Edit needs a unique anchor in a file where many sites share the same shape, easy to mis-target; (b) PostToolUse linters fire between Edits and see an inconsistent file (N/2 sections wrapped, N/2 not); (c) the diff is N small hunks instead of one coherent restructure, fragmenting review. Distinction from #28: #28's intermediate state is **lint-dirty**; this trap's intermediate state is **lint-clean but structurally inconsistent**. The cost is review-quality + edit-fragility, not lint stripping. Cure: when the same conditional/wrapping pattern applies at N>3 sites in one file, use a single `Write` over the final content (or one Edit with a multi-site `replace_all` pattern). Rule of thumb: *N>3 same-shape wraps in one file ⇒ Write, not chained Edits.* The Write is atomic; the diff is one hunk; the linter sees the final state only.

52. **Misnamed themable token reached for as if it were static.** A project design-token file binds tokens with static-color *names* to themable CSS variables — e.g., `white: 'var(--color-secondary-bg)'`. In light mode `C.white` is `#FFFFFF` (fits the name). In dark mode it's `#282828` (a surface panel). Devs (and AI) read the name "white" and reach for `C.white` to mean "white text/icon" — every such use becomes a dark-foreground on dark-background combination in dark mode. The codebase typically provides an escape-hatch alias (`C.alwaysWhite = '#FFFFFF'`) for the static-white role, but the natural-named token wins every time it's reached for because the binding isn't visible at the call site. The `2026-05-16` dark-mode chain on lex_council hit this pattern 13+ times across 9 files (Heading default, 6 topbar files, PortalNavRow tooltip, 2 client-domain buttons, 4 portal sidebar components) in 3 sequential campaigns before the pattern was named. `tsc + lint` cannot detect it because the call site is type-correct. Cure (§Step 3 W3 step 1.5e): theme-rollout / dark-mode / contrast-fix campaigns run a **themable-token semantic audit** at W1 — grep the design-token file for tokens whose name reads as a static color literal but whose binding is `var(--color-*)`, document each in the plan's "Inputs" with safe-replacement tokens for misuse cases, then grep the codebase for the misuse pattern (`color: C.white` as a *foreground*) and fix all matches in a single mass-edit phase. One cheap grep at W1 of campaign 1 replaces N sequential fix campaigns.

53. **Visual-contrast fix shipped without WCAG measurement.** A campaign fixes "unreadable text" by swapping color tokens (e.g. `C.white → C.alwaysWhite`) and verifies via "I can see the text on the screen" or a screenshot inspection. The new combination may still fail WCAG: `C.alwaysWhite` (#FFFFFF) on `C.gold` (#C9A84C) computes to ~2.8:1 — below AA's 4.5:1 threshold for normal text. The brand-correct alternative `colors.navy` (#0A1A3B) on `C.gold` gives ~6.4:1. Render-only verification doesn't catch "I fixed it to a different unreadable combination"; the `tsc + lint` discipline doesn't measure contrast; even preview verification with a screenshot doesn't measure contrast unless explicitly probed. The `2026-05-16` component-sweep campaign shipped the active pagination chip at 2.8:1 (FAIL AA) because consistency-with-other-buttons won over measurement. Cure (§Step 1.2 Q9 + §Step 2 `verification_class: contrast-measured`): for accessibility / contrast / dark-mode / color-token campaigns, the verification recipe must include a WCAG contrast-ratio measurement step (`getComputedStyle` + ratio compute, or DevTools accessibility panel) and record the measured ratio in the change-log. Phases marked `verification_class: contrast-measured` cannot be marked complete on render-only verification.

54. **Express mode trimmed silently without declaring `scope: small`.** v1.7.0 (#45) cured "full pipeline on small builds" by introducing express mode. v1.8.0 strengthened this to "Express mode is a **declared** trim with explicit boundary; it isn't 'I'll skip whatever I want.'" But the inverse trap appeared: the plan's `phases_remaining` correctly skips W1 / W2 / per-phase files / 99-risk-sweep (because the work is genuinely small-scope), but the frontmatter doesn't contain `scope: small` and none of the express-mode required fields (`standing_instructions`, `preview_verification`, `verification_recipe`, `verification_class`) are populated. Future readers can't distinguish whether the trims were deliberate express-mode discipline or a sloppy/incomplete plan. The `2026-05-16` component-sweep campaign was a textbook express-mode candidate (4 files, 0 migrations, no mass-renames) but shipped without declaring `scope: small`. Cure (§Step 2 — Express-mode declaration gate): before W3 starts, if `phases_remaining` excludes W1/W2/per-phase-files, the frontmatter MUST contain `scope: small` plus every express-mode required field. Silent trims erode the discipline that v1.7.0 added one campaign at a time.

55. **Stub-extension vault logs invisible in successor campaign's predecessor chain.** §5.8 cleanly classifies post-closure tweaks as stub-extensions (handled inline, vault log only) or mini-extensions (re-opened as EXTENSION campaigns). When the chain is `Campaign A (closed) → stub-extension fix (vault log only) → Campaign B (EXTENSION)`, Campaign B's `predecessor:` field correctly points to Campaign A (the last full campaign) — because the stub-extension has no campaign artifact to point to. The unintended consequence: future readers tracing `predecessor: A → B` skip over the intermediate stub-extension vault log entirely. The work is lost from the chain. The `2026-05-16` dark-mode chain on lex_council shipped: obsidian-palette campaign → topbar text fix (vault log, no campaign) → component-sweep campaign — and the component-sweep plan pointed only at obsidian-palette, dropping the topbar fix from the visible chain. Cure (§5.8 — stub-extension chain visibility): the new EXTENSION plan's "Trigger / Context" section must list every intermediate same-session vault log on the affected surface as a one-line wikilink ("Prior touches on this surface in same session: [[...]]"). One-line addition per stub-fix; the chain becomes reconstructable from the new plan alone.

56. **`git stash → re-run → git stash pop` provenance check silently meaningless for untracked files.** §5.2 + failure mode #36 codify the `git diff <campaign-start-sha>..HEAD | grep -F '<error>'` pattern for runtime/compile error provenance — pre-existing vs campaign-introduced. A natural variant: `git stash` the working changes, re-run `tsc` / `lint`, and check whether the error still appears (if yes → pre-existing; if no → campaign-introduced). This works for tracked files but `git stash` skips untracked files by default. When the campaign's edited files are untracked (long-running feature branch with `.gitignore`-d build artifacts, recently-added files not yet `git add`-ed, or a scaffolding branch where the new directory hasn't been committed once), `git stash` leaves them in place and the post-stash check compares identical states — no counterfactual, no signal. The `2026-05-16` component-sweep campaign hit this when probing whether a `ThemesPanel.tsx` parse error was pre-existing — the stash test was a no-op because most edited files were untracked, returning misleading "yes the error is pre-existing" while in reality the test never ran. Cure (§5.2 — Untracked-files caveat): either pass `-u` (`git stash -u` includes untracked in the stash), or rely on `npx turbo run <task> --force` + manual file inspection (grep + git log on the offending file). The git-diff pattern from §5.2 also presumes the target file existed and was tracked at campaign-start commit; for files added during the campaign, neither stash nor git-diff produces a valid counterfactual.

57. **Directional-adjective migration verb infers the wrong keeper.** A user prompt like "fully migrate from the files vertical to the files horizontal side panel card" names two competing patterns by direction but doesn't clearly state which is being preserved. The natural inference is "the named-second one is the keeper" or "the file's name encodes the keeper" — but both can lie. The 2026-05-16 `files-stack-sidebar-canonical` campaign hit this: the keeper file was named `FilesStackHorizontal.tsx` but the keeper RENDER MODE was `layout="vertical"` (the sidebar). The agent opened §1.2 planning questions on the wrong direction (assumed `vertical` was old because file said `Horizontal`); the user's Q1 answer inverted the scope, forcing a re-interrogation round + a stale set of planned questions to discard. Cure (§1.4.1 — Ambiguous-direction migration verb): when a trigger names competing patterns by directional adjective (`horizontal/vertical`, `above/below`, `inline/block`, `modal/page`, `cascade/stacked`), fire a single `which side is the keeper?` AskUserQuestion BEFORE §1.2 scope locks. Cheaper than a re-plan after the first scope-confirmation answer reveals the inversion. Sibling of §1.4: different ambiguity class (direction-of-travel, not internal-state), same one-question cure. Also codifies the `Q1-inverts-scope ⇒ Q2..QN are stale; re-batch on corrected core` discipline.

58. **N=3+ enum-prop union — one value canonical, N-1 legacy — left as a stale 1-value union after consolidation.** A component exposes a `layout: 'cascade' | 'inline' | 'vertical'` (or `variant`, `mode`, `kind`) union prop where N-1 values are legacy survivors that no consumer needs. A consolidation campaign migrates consumers off the dead values but stops short of *deleting the prop itself*, *removing the dead render branches*, AND *dropping helper components used only by the dead branches*. The component is left with a misleading 1-value union (`layout: 'vertical'`), dead render code (cascade + inline branches that no one reaches), and orphan helpers (`FileContainerChip`, `NatureSelectorPopover`, `InlineBreadcrumbSegment`) that only `cascade` or `inline` called. `tsc + lint` pass because the dead code is syntactically valid; future readers can't tell which branches are live. Sibling of failure mode #27 (Nth hand-rolled clone): same root pattern (≥3 of a thing, one is canonical, rest are legacy), different surface (prop union, not file replication). Cure (§Consolidation discipline rule 5 — N=3+ union-prop audit): at write time, grep consumer usage of each union value; if N-1 cluster around one keeper, drop the prop entirely + delete the dead branches + delete the helper components used only by them, all in the same phase. The 2026-05-16 `files-stack-sidebar-canonical` campaign did this organically (shrunk the component 61%) but the discipline was implicit. Codifying it as Rule 5 prevents the next campaign from leaving a stale 1-value union behind.

59. **Express vs full mismatch on medium-scope builds (6-20 files).** v1.7.0 introduced `scope: small` (≤5 files). v1.8.0 introduced `scope: micro` (≤2 files). The 2026-05-16 `files-stack-sidebar-canonical` campaign hit ~15 files (1 component + 11 consumers + 3 docs + 1 hook), 0 migrations, no >15-site rename, 1 pre-approved forced gate (rename). Express (`scope: small`) was too tight — strict ≤5-file boundary. Full mode produced ceremony in excess of the work: W1 discovery subagent fan-out for a fully-inventoried 15-file surface adds zero signal because the main agent's inline inventory IS the surface map; per-phase change-log files for 3 sequential FE phases bloat the artifact set vs a single risk-sweep block per phase. The campaign shipped with an abbreviated artifact set (plan + risk sweep, no per-phase files, no subagent dispatch) — but the trim was *undeclared* in frontmatter, repeating failure mode #54's mistake one tier up. Cure (§Step 2 — Medium mode, `scope: medium`): explicit declared tier for 6-20 files + ≤1 migration + no >15-site rename + ≤1 forced gate. Trims match `scope: small` (skip W1/W2/per-phase files) plus the addition of a **standalone `99-risk-sweep.md`** — the surface coverage matrix + grep proofs at 6-20 files are too valuable to inline. The scope-mode declaration gate in §Step 2 covers both `scope: small` and `scope: medium`; the inverse of #54 (silent trim) still applies — declared trim with explicit boundary, not "I'll skip whatever I want."

60. **Rename-with-shrink chained-Edit trap.** A campaign renames a public component (`FooHorizontal.tsx` → `Foo.tsx`) AND simultaneously deletes >40% of its body (dead render branches, orphan helper components, dropped union-prop values). The natural instinct is chained Edits: `Edit` #1 deletes branch A, `Edit` #2 deletes branch B, `Edit` #3 renames the function default-export, then `mv` the file. Between every Edit the file is in a structurally inconsistent state — orphan helpers exist with no callers (lint-dirty per failure mode #28), the rename hasn't happened yet (consumers still type-error), and the PostToolUse linter strips the helpers as `no-unused-vars` mid-flight. Cure: the **RIBS chain** (rename-incidental-body-shrink) — `git mv` first, Read the new path once to satisfy the Edit invariant, then a single atomic `Write` over the entire final file content (imports trimmed, helpers deleted, branches removed, function renamed), then update the barrel export. One atomic body diff, one consistent lint pass, one git operation. The 2026-05-16 `files-stack-sidebar-canonical` campaign used RIBS on `FilesStackHorizontal.tsx` → `FilesStack.tsx` (962 → 374 lines, −61%). Named in §Subagent dispatch — Named FE sub-pattern: RIBS. Phases following it declare `fe_pattern: RIBS` in the plan.

61. **Project-wide lint conflated with campaign-scope lint.** Under `--max-warnings 0`, a project-wide `npm run lint` fails because of an unrelated in-progress refactor in a file the campaign never touched. Without a scoped-lint pattern, the agent either (a) treats the project-wide failure as a campaign blocker and chases an unrelated WIP fix into the campaign's vault log, expanding scope — see #24 post-closure tweak drag; or (b) waves it off as "pre-existing" without proving the campaign's own files are clean, leaving a real campaign-introduced warning hidden. Cure (§5.2 — Scoped-lint pattern): after the §5.2 provenance check confirms the failing warning is pre-existing, run `npx eslint --max-warnings 0` scoped to the campaign-touched file list (computed from `git status --short`). `EXIT=0` proves the campaign's own surface is clean independent of the unrelated warning. The full-project warning becomes a `CHK-<id>` in the risk sweep (or a `spawn_task` chip for a separate fix). Phase verification passes on the scoped result, not the full-project one. The 2026-05-16 `files-stack-sidebar-canonical` campaign hit this with `SingleMemberSelector.tsx:22` unused `MIcon` from a parallel dropdown-unification refactor — scoped lint on the 14 campaign-touched files returned exit 0, the warning rode as CHK-1 with a spawn_task follow-up.

---

## Output conventions

Every campaign produces:

### Audit mode

- `docs/audit-campaigns/<YYYY-MM-DD>_<topic>/00-campaign-plan.md` — the plan (status: completed)
- `docs/audit-campaigns/<YYYY-MM-DD>_<topic>/00-w0-offline-prescan.md` — Ollama pre-scan (if W0 ran)
- `docs/audit-campaigns/<YYYY-MM-DD>_<topic>/NN-<task>.md` — one per audit task (typically 8-12 files)
- `docs/audit-campaigns/<YYYY-MM-DD>_<topic>/99-synthesis.md` — the master changelog
- `docs/audit-campaigns/<YYYY-MM-DD>_<topic>/CHECKPOINTS.md` — only if external blockers existed
- Updated live docs
- One vault-log entry
- `docs/audit-campaigns/README.md` (first audit run only)

### Build mode

- `docs/build-campaigns/<YYYY-MM-DD>_<topic>/00-campaign-plan.md` — the plan (status: completed, all phases in phases_completed)
- `docs/build-campaigns/<YYYY-MM-DD>_<topic>/00-w0-offline-prescan.md` — Ollama pre-scan (if W0 ran)
- `docs/build-campaigns/<YYYY-MM-DD>_<topic>/0N-phase-N-<topic>.md` — phase plan + change log fused
- `docs/build-campaigns/<YYYY-MM-DD>_<topic>/99-risk-sweep.md` — post-rollout sweep
- `docs/build-campaigns/<YYYY-MM-DD>_<topic>/CHECKPOINTS.md` — only if post-deploy probes are still pending
- New / modified code shipped via the per-phase execution loop
- Dead code deleted per the cleanup plan
- One vault-log entry covering all phases
- Memory entries for surprise discoveries
- `docs/build-campaigns/README.md` (first build run only)

---

## Reference files

- [references/wave-playbook.md](references/wave-playbook.md) — full wave-by-wave playbook with subagent prompt templates for each task, both modes
- [references/templates.md](references/templates.md) — campaign-plan, findings-file, phase-plan, phase-change-log, synthesis, risk-sweep, checkpoint-registry, vault-log templates
- [references/checkpoint-pattern.md](references/checkpoint-pattern.md) — when and how to use CHECKPOINT markers, both modes
- [assets/campaign-readme-template.md](assets/campaign-readme-template.md) — boilerplate for the project's audit-campaigns/ and build-campaigns/ README files

---

## Version history

Bump the `version:` frontmatter field with each meaningful upgrade (semver: MAJOR for paradigm shifts, MINOR for new sections / new failure modes / new disciplines, PATCH for clarifications and typo fixes). Append a one-line entry below per release.

### v1.13.1 — 2026-05-17 — Named-pattern index + forced_gate flip-point + wikilink enforcement + RIBS-N + PDAAV-RIBS + pre-W3 checklist (patch)

Same meta-reflection pass as v1.13.0 — six clarifications that extend existing sections rather than introducing new paradigms. Same-session release-split rule (§Step 6 §6.4) ships as the structural example.

- **§Named patterns index** — quick-ref dashboard listing PDAAV, PDAAV-RIBS, RIBS, RIBS-N, source-walk, scoped-lint, checkpoint patterns. Maps frontmatter tag → use case → section. Future campaigns with ≥2 named patterns reference the index rather than re-reading every named-pattern section.
- **§Step 2 `forced_gate:` flip-point rule** — planning agent flips `pending → satisfied` immediately after the matching AskUserQuestion resolves (not W3 agent at execution). Citation format canonicalised to `Q "<header text>" → "<answer label>"` (verbatim, not paraphrased, not Q-numbered — batch numbering is non-canonical across multi-batch interrogations).
- **§0.0.5 wikilink convention W4 enforcement** — at §5.2 verification, grep every artifact for `[[...]]` wikilinks; classify each against the declared convention (`bare-filename` vs `relative-path`); fix violations or downgrade convention. Costs one grep; prevents Obsidian graph from acquiring broken edges.
- **§Subagent dispatch Named FE sub-pattern: RIBS-N** — multi-file lockstep rename variant of RIBS for `Foo.tsx + Foo.test.tsx + Foo.stories.tsx + Foo.types.ts`-shape companion sets. Batch `git mv` + per-file atomic Write + companion-consistency grep. Declared as `fe_pattern: RIBS-N`. When N=1, use plain RIBS.
- **§Subagent dispatch Named DB sub-pattern: PDAAV-RIBS** — SQL mirror of RIBS for DB function/view/trigger rename + body shrink. Combines PDAAV's verify discipline with atomic rename+shrink migration. Five-step shape mirrors PDAAV; the migration body is non-trivial (multiple atomic statements; dependent-update list is the planning artifact). Declared as `db_pattern: PDAAV-RIBS`.
- **§W3 pre-execution checklist box** — condensed version of §1.5a-1.5e gates at top of W3 execution loop. Eight ticked boxes covering reference render-structure, N=3 alarms (file-clone + union-prop), reference re-Read, schema reality-check, themable-token audit, `forced_gate` state, and phase risk tag vs cadence. Replaces re-reading §3's prose every phase.

No new failure modes — this release is patches.

### v1.13.0 — 2026-05-17 — Reflection-pass procedure + Standing principles tier + Trigger-phrase precedence (meta-reflection on v1.12 additions)

Triggered by: meta-reflection pass on what the v1.12.0 + v1.12.1 patches revealed about the skill's own structure. Three paradigm-level gaps that v1.12 exposed but didn't fix:

- **§Step 6 — Reflection-pass procedure** — codifies the post-campaign skill-upgrade workflow. Previously instinct-driven; two prior sessions did this ad-hoc. The procedure has 7 sub-steps: 6.1 inputs → 6.2 walk → 6.3 MINOR vs PATCH classification → 6.4 same-session release-split rule → 6.5 cross-reference completeness → 6.6 apply + verify → 6.7 user report. Triggers on phrases like *"reflect on this session"*, *"upgrade as recommended"*, *"review and note lessons"*. Distinct from §Step 5 (close) and from a new campaign — produces a v(N+1) skill diff, not a vault-log entry.
- **Standing principles tier (P1-P7)** — failure-mode list bifurcated. Early items (#1 skip W0, #2 missing model table, #3 stop mid-execution, #4 invent new style, #5 copy-paste, #7 skip vault-log) are paradigm-level always-on disciplines, not "watch-out traps". Promoted to a numbered Principles list (P1-P7) ahead of the numeric failure modes. The originals remain in the failure-modes list with a *"Now a standing principle (P<N>)"* annotation so existing cross-references still resolve. Without bifurcation, the failure-mode list (#1-#61) would keep growing past readability — at #80 it'd be unscannable.
- **Trigger-phrase precedence table** — multiple trigger-phrase tables exist (§0.0, §0.0.1, §0.0.3, §1.4, §1.4.1, §5.8, §Step 6). A user prompt could match two simultaneously. Codified order: 0.0 resume → 0.0.1 pivot → 0.0.3 chain → 5.8 post-closure → Step 6 reflection → 1.4 vague-symptom → 1.4.1 ambiguous-direction → standard 1.2. Earlier rule wins; later rules only fire if earlier didn't. Default LATER if unclear — wrong-direction binding is more expensive than over-cautious re-interrogation.

No new failure modes — this release is structural (principles tier + precedence table + new section).

### v1.12.1 — 2026-05-17 — Frontmatter + procedure clarifications from the files-stack-sidebar-canonical session (patch)

Same session post-mortem as v1.12.0 — six smaller gaps surfaced during the reflection pass that don't warrant new sections but are too valuable to leave un-codified. Patch release; no paradigm shifts.

- **§0.0.5 extension — CLAUDE.md / AGENTS.md location probe + wikilink convention** — the authoring-rule file usually lives at workspace root even when planet-hub docs are nested under `<app>/docs/`. Probe both via `find . -maxdepth 3 -name "CLAUDE.md"`, record `claude_md_path:` (and `agents_md_path:` if present) in plan frontmatter, P3 doc edits target the recorded path. Also adds explicit `wikilink_convention: bare-filename | relative-path` frontmatter for the two-docs-root case to prevent mixed conventions inside a single artifact set.
- **§Step 2 — `forced_gate:` state machine enumeration** — replaces the binary `true`/`absent` with a four-value enum: `pending | true | satisfied — pre-approved in planning Q<N> | false`. The `satisfied` value lets a planning-time AskUserQuestion that matched the W3 gate's risk framing pre-satisfy it; the state machine prevents both silent skipping and duplicate gating. The satisfaction citation must reference a real planning Q with matching options + risk framing — otherwise the gate still fires at W3.
- **§5.2 — Scoped-lint pattern (failure mode #61)** — when project-wide `--max-warnings 0` lint fails on an unrelated WIP file, compute the campaign-touched file list from `git status --short` and run `npx eslint --max-warnings 0 <file-list>`. `EXIT=0` proves the campaign's own surface is clean. The unrelated warning rides as `CHK-<id>` / `spawn_task`. Phase verification passes on the scoped result.
- **§5.3 — Campaign-date convention** — every artifact in the campaign set (folder name, vault-log filename, INDEX row, memory references, plan frontmatter dates) uses the date the campaign STARTED, even if a session spans a midnight rollover. Resumed campaigns (§0.0) also keep the original start-date. Prevents fractured artifact sets where the folder is dated D1 and the vault-log dated D2.
- **§Subagent dispatch — Named FE sub-pattern: RIBS (failure mode #60)** — `rename-incidental-body-shrink`: `git mv` + Read + atomic `Write` over the full final body + barrel update. The chain handles the chained-Edit trap (failure mode #28) when a rename simultaneously deletes >40% of the file. Phases declare `fe_pattern: RIBS` in the plan. Sibling of PDAAV for FE-only restructures.

Two new failure modes (#60 rename-with-shrink chained-Edit trap, #61 project-wide vs campaign-scope lint conflation).

### v1.12.0 — 2026-05-17 — Directional-adjective migration gate + N=3+ union-prop audit + medium scope mode (files-stack-sidebar-canonical post-mortem)

Triggered by: lex_council `2026-05-16_files-stack-sidebar-canonical` campaign — a ~15-file FE consolidation that migrated 11 admin/members pages onto a single sidebar `<FilesStack>` pattern, renamed `FilesStackHorizontal` → `FilesStack`, and deleted two competing render branches (`cascade` + `inline`) from the component (962 → 374 lines, −61%). The campaign exposed three gaps in 1.11.0's discipline catalog: (1) the planning phase opened §1.2 questions on the wrong direction-of-travel because the file's name (`Horizontal`) suggested it as the keeper while the actual keeper render mode was `vertical` — Q1's answer inverted the scope and forced a re-interrogation; (2) the 3-value union prop (`layout: 'cascade' | 'inline' | 'vertical'`) needed an explicit consolidation discipline alongside the existing #27 N=3 file-clone alarm — without it, future campaigns could leave a stale 1-value union with dead render branches and orphan helpers behind; (3) the campaign sat awkwardly between `scope: small` (≤5 files) and full mode — a medium tier was missing, and the campaign de-facto produced the medium-mode artifact set (plan + standalone risk sweep, no per-phase files, no subagent dispatch) without declaring it in frontmatter, repeating failure mode #54 one tier up. Three additions + three new failure modes:

- **§1.4.1 — Ambiguous-direction migration verb** — when a trigger names competing patterns by directional adjective (`horizontal/vertical`, `above/below`, `inline/block`, `modal/page`, `cascade/stacked`, `expanded/collapsed`) without naming the keeper, fire a single `which side is the keeper?` AskUserQuestion BEFORE §1.2 scope locks. Strict sibling of §1.4 (vague-symptom verb): different ambiguity class (direction-of-travel, not internal-state), same one-question cure. Also codifies the `Q1-inverts-scope ⇒ Q2..QN are stale; re-batch on corrected core` discipline — a campaign whose first scope-confirmation answer inverts the assumption must drop the remaining batched questions and re-interrogate the corrected core, not press on with stale Qs.
- **§Consolidation discipline rule 5 — N=3+ union-prop audit** — at write time on any consolidation campaign that touches a component with a ≥3-value render-mode union prop, grep consumer usage of each value; if N-1 cluster around one keeper, drop the prop entirely + delete the dead render branches + drop helper components used only by them, all in the same phase. Codifies what the 2026-05-16 campaign did organically. Sibling of #27 (Nth hand-rolled clone): same root pattern (≥3 of a thing, one canonical, rest legacy), different surface (prop union, not file replication).
- **§Step 2 — `scope: medium` mode** — declared tier for 6-20 files + ≤1 migration + no >15-site rename + ≤1 forced gate. Trims match `scope: small` (skip W1/W2/per-phase files) plus addition of a standalone `99-risk-sweep.md` (surface coverage matrix at 6-20 files is too valuable to inline). The scope-mode declaration gate now covers both `scope: small` and `scope: medium`; silent trims still forbidden per failure mode #54 — declared trim with explicit boundary or escalate to full.

Three new failure modes (#57 directional-adjective inversion, #58 stale 1-value union after consolidation, #59 express-vs-full mismatch on medium scope).

### v1.11.0 — 2026-05-16 — Content-only campaigns + Ollama REST API + i18n translation discipline + mid-execution scope gate (missing-translations post-mortem)
Triggered by: lex_council `2026-05-16_missing-translations-all-locales` campaign — a 6-phase pure-JSON translation campaign (customer_wizard propagation + 888 [DRAFT] attribute values) that exposed four gaps absent from all prior campaigns because they were all FE/DB-oriented: (1) `ollama run` CLI ANSI artifacts breaking JSON parsing for W3 batch tasks; (2) no skip condition for content-only campaigns where domain analysis is complete; (3) `tsc + lint + preview` verification gate meaningless for JSON-only changes; (4) no plan requirement to document intentionally-EN values and valid cognates per locale, leading to false-alarm noise in final verification. Also: Ollama format-example key collision (model emits example key as real output key); unicode normalization miss (`…` literal vs `…` char); mid-execution scope discovery (888 values) handled silently without a documented threshold. Five additions + zero new failure modes (all gaps were omissions, not anti-patterns that caused shipped defects):
- **§0.5.2 — Ollama REST API for W3 batch/structured tasks** — `curl .../api/generate stream:false think:false` gives clean JSON output; `ollama run` CLI leaks ANSI spinner + thinking traces that break JSON parsing even with the sed strip. Format-example key collision: use `__EXAMPLE__` as the example key in JSON format instructions; smaller models conflate plausible-named placeholders (`EnValue`) with real output keys.
- **§0.5.1 — Skip W0 for content-only campaigns** — when the campaign surface is pure content files and domain-specific analysis is already complete (Python deep-flatten, CSV diff, grep matrix), W0 provides no signal. Mark `w0_enabled: skipped — content analysis already complete via <method>`.
- **§1.2 Q10 + §Step 2 — `verification_class: content-only`** — for pure-JSON / fixture / config-bundle campaigns, substitute JSON validity + deep-flatten diff + placeholder-free check for `tsc + lint + preview`. The standard gate is ceremony without signal. Content-only phases declare `verification_class: content-only`; express-mode frontmatter updated to include this class.
- **§Step 2 — Generation strategy: i18n sub-sections (intentionally-EN + valid cognates)** — translation campaigns must document values that must NOT be translated (brand names, numeric stats, abbreviations, format placeholders) and words identical in EN and target language (French: Finances, Documents; Spanish: Error, No). Without both, verification floods with false alarms and risks over-translating domain abbreviations that break component logic. Also: unicode normalization (`unicodedata.normalize('NFC', ...)`) applied to both keys and file values before lookup; always write locale JSON with `ensure_ascii=False`.
- **§Step 4 — Mid-execution scope discovery threshold** — when W3 discovers additional scope, apply the ≤20-keys / 21–200-keys / >200-keys table. Under `autonomous`, the change-log must document the discovery prominently (not silently); the vault-log phase list must show the discovered phase explicitly. "Proceeding silently" ≠ "user unaware after reading the vault-log."

### v1.10.0 — 2026-05-16 — Themable-token semantic audit + WCAG contrast verification + express-mode declaration gate + stub-extension chain visibility (dark-mode-component-sweep post-mortem)
Triggered by: lex_council `2026-05-16` chain of three sequential dark-mode fixes (`dark-mode-obsidian-palette` full campaign → topbar text fix ad-hoc stub-extension → `dark-mode-component-sweep` EXTENSION campaign) where the SAME root cause — themable token `C.white` bound to `var(--color-secondary-bg)` reached for as if it were a static white — surfaced 13+ times across 9 files in 3 separate sessions before the pattern was named. v1.9.0's same-session pivot detection, preview-auth-wall flag, and turbo-cache disciplines all fired correctly and saved cycles. The new gaps are domain-specific to **theme/contrast/accessibility campaigns** where the value at stake is *visual readability* — a metric `tsc + lint` can't measure, that render-only verification can't measure, and that the existing `verification_class: interactive` doesn't cover. Six additions + five new failure modes:
- **§Step 3 W3 step 1.5e — Themable-token semantic audit (theme-rollout / dark-mode / contrast-fix campaigns)** — grep the project's design-token file for tokens whose NAME reads as a static color literal (`white`, `navy`, `black`) but whose BINDING is `var(--color-*)`; document each in the plan's "Inputs" with safe-replacement tokens for misuse cases; grep the codebase for the misuse pattern and fix all matches in a single mass-edit phase. One cheap grep at W1 of session 1 replaces N sequential fix campaigns.
- **§Step 1.2 Q9 + §Step 2 — `verification_class: contrast-measured`** — for accessibility / contrast / dark-mode / color-token campaigns, the verification recipe must include a WCAG contrast-ratio measurement step (`getComputedStyle` + ratio compute, or DevTools accessibility panel) with the measured ratio recorded in the change-log. Phases marked `contrast-measured` cannot be marked complete on render-only verification. Strict successor to failure mode #20 for visual-readability outcomes — render-passes-without-error is satisfiable by "I fixed it to a different unreadable combination."
- **§Step 2 — Express-mode declaration gate** — if `phases_remaining` skips W1 / W2 / per-phase files / 99-risk-sweep, the frontmatter MUST contain `scope: small` plus every express-mode required field (`standing_instructions`, `preview_verification`, `verification_recipe`, `verification_class`). Silent trims erode the v1.7.0 discipline one campaign at a time. Inverse of failure mode #45 (full pipeline on small builds).
- **§5.8 — Stub-extension chain visibility** — when a mini-extension (re-opened EXTENSION campaign) follows one or more stub-extensions (inline-fix vault logs) on the same surface in the same session, the new plan's "Trigger / Context" section must list every intermediate vault log as a one-line wikilink. The `predecessor:` field correctly points to the last full campaign but skips the stub-fix vault log; the new convention makes the chain reconstructable from the new plan alone.
- **§5.2 clarification — `git stash` provenance test caveat for untracked files** — `git stash` skips untracked files by default; for campaigns with untracked-only edits, stash is a no-op and the "is this error pre-existing?" test produces no counterfactual. Either pass `-u` or rely on `--force` + manual file inspection.
- **§0.0.2 clarification — TodoWrite reset also fires before inline stub-extension fixes** — not just before fresh campaigns. Stale `[completed] W4` items from the predecessor otherwise trigger harness nags during the inline fix turn.
- **Failure modes #52-56:** misnamed themable token reached as if static (#52), visual-contrast fix without WCAG measurement (#53), express mode trimmed silently without `scope: small` (#54), stub-extensions invisible in successor's predecessor chain (#55), `git stash` provenance test no-op for untracked files (#56).

### v1.9.0 — 2026-05-16 — Micro scope + runtime cache routing + sidebar nav lock-in + JSX-structural Write (themes-dev-tool campaign post-mortem)
Triggered by: lex_council `2026-05-16_themes-dev-tool` campaign — a 3-file build that ran clean under v1.8.0 express, but exposed four gaps. (1) A follow-up active-state styling tweak rendered as invisible text on a solid navy rectangle because the panel hand-rolled a `<button>` inside `<SidebarCard>` instead of using the canonical `PortalNavRow` primitive — `tsc + lint` green; defect visible only at render time. (2) Translation keys added to `messages/en/admin.json` mid-session rendered as raw key paths (`admin.nav.files_menu.dev_tools`) because Next.js dev-server module cache for dynamic JSON imports doesn't HMR; the cure is "restart dev server," not a code change. (3) A 4-line CSS tweak invoked the campaign skill but v1.8.0 express still demanded a plan file + frontmatter + execution log — ceremony exceeding the patch. (4) A render-tree pivot from "show all 7 sections" to "show one of N" was applied via 7 chained Edits instead of one Write — diff fragmented, intermediate state structurally inconsistent. Four additions + four new failure modes:
- **§Step 2 — `scope: micro` mode** — for ≤2 files + ≤10 lines + no new artifacts. Allowed elisions vs express: no plan file (conversation IS the plan), no per-phase log, no memory entry unless surprise. Kept mandatory: §1.4 reproduction gate, tsc + lint at exit, preview verification, §5.3 vault-log entry (P8 non-negotiable). Routes the smallest tweaks into the lightest discipline that preserves P8 + diagnostic correctness. Trigger phrases: "fix this", "the X is broken", named-property + observable-defect.
- **§Environment hazards — "Runtime module caches that don't HMR"** — umbrella for Next.js dev-server JSON imports + SWC bundler stale parses + `.next/` cache. Umbrella discipline: *if the runtime symptom contradicts the current file on disk, restart before diagnosing.* First item on any W4 verification checklist.
- **§Conformity discipline — "Sidebar nav lock-in"** — any `<button>` inside `<SidebarCard>` that participates in a list of selectable items uses the canonical nav-row primitive — no exceptions for "dev-only" panels. Detection at write-time, not at follow-up-tweak time.
- **§Environment hazards — "JSX structural pivot via chained Edits"** — sibling case of #28; N>3 same-shape wraps in one file ⇒ single `Write`, not chained Edits. Intermediate state is lint-clean but structurally inconsistent; the cost is review fragmentation + edit fragility.
- **§1.4 — Screenshot-with-vague-prompt sub-rule** — when a vague-symptom phrase ("messed up", "looks weird") arrives with a screenshot, the screenshot is evidence not yet a diagnosis. One short question with a hypothesis ("I see [specific defect] — is that what you mean?") before fix planning. Image attachment is not a substitute for confirmation.

Failure modes #48 (dev-server JSON cache), #49 (sidebar nav primitive lock-in), #50 (single-property tweak shouldn't re-enter campaign machinery), #51 (JSX structural pivot via chained Edits) appended.

### v1.8.0 — 2026-05-16 — Express mode + symptom reproduction + monorepo artifact-root + RLS effective-access (notifications-devtools-fix campaign post-mortem)
Triggered by: lex_council `2026-05-16_notifications-devtools-fix` campaign that shipped a 4-file + 1-migration fix where the user reported "kinds shows nothing" + "audit doesn't work". The skill at v1.7.0 ran the full wave pipeline but several disciplines either misfired or were silently skipped: §0.0.4 preview probe was not run at session start (preview hit `/login` at W4); diagnosis was performed from DB introspection alone without observing the user's actual symptom; the campaign-plan landed at workspace `docs/build-campaigns/` while the vault-log landed at `lex_council/docs/vault-logs/` (broken wikilinks); the migration changed a permission gate but post-flight verified only the policy text, not the effective access for a representative user. Four additions + four new failure modes:
- **§0.0.5 — Monorepo artifact-root resolution** — probe for nested docs roots at session start; record `campaign_folder_root` + `vault_log_root` in plan frontmatter; co-locate campaign artifacts with vault-logs by default. Prevents wikilink breakage when the project has both `/docs/` (workspace) and `<app>/docs/` (nested) roots.
- **§1.4 — Investigate-verb detection + symptom-reproduction gate** — when the trigger contains a vague symptom verb ("shows nothing", "doesn't work", "broken") mixed with imperative fixes, split planning into Part A (reproduce symptom + confirm interpretation with user) and Part B (plan fixes). Vague symptoms map to ≥4 internal states; diagnosing from code alone commits to one hypothesis from N. One short question costs ~30s; fixing the wrong cause costs a full campaign close-out + an undo campaign.
- **§Step 2 — `scope: small` express mode** — explicit trim for ≤5 files + ≤1 migration: skip W1/W2/W3-per-phase-files/99-risk-sweep, keep §1.4/§1.5d/§2a/§2a-RLS/§5.3/§5.4. Required frontmatter shrinks (no model-assignment table, no reference render structure, no consolidation plan); required discipline doesn't. Closes the "user invoked skill but full pipeline is overkill" gap that the v1.7.0 "skill is overkill, offer lighter pass" advice didn't address.
- **§3 W3 step 2a-RLS + 2b — RLS effective-access check + phase atomicity for orthogonal AC changes** — when a phase changes an RLS policy, grant, or view-security attribute, run a representative SELECT under a simulated authenticated context (`set local role authenticated; set local request.jwt.claim.sub to ...`) for both an admit-user and a deny-user; record counts in the change-log. When a phase bundles ≥2 changes across different AC layers (RLS + grant, grant + view-security, etc.), assign sub-phase IDs and verify each layer independently. Text-matches-intent is necessary; effective-access-matches-intent is sufficient.
- **Failure modes #44-47:** symptom diagnosed from code not observation (#44), express-mode acknowledgment gap (#45), monorepo docs-root wikilink breakage (#46), RLS qual-text matches ≠ effective-access matches (#47).

### v1.7.0 — 2026-05-16 — Pivot-chain detection + named DB sub-pattern + source-walk template (dev-tools-actions-tab campaign post-mortem)
Triggered by: lex_council `2026-05-16_dev-tools-actions-tab` campaign that ran SEVEN same-session pivots through P11, accreting a Dev Tools Actions tab + body-hash dedup codegen + DB-backed descriptions (`action_descriptions` table) + visibility audit (`action_visibility` table) + LLM classification of all 108 surface rows + visual-divergence audit (36 distinct signatures surfaced). §0.0.1 (single-pivot) held, but per-pivot close-out overhead dominated the campaign and the artifact drifted past its named shape. Three additions + seven new failure modes:
- **§0.0.3 — Pivot-chain detection** — when §0.0.1 has fired ≥2 times and the predecessor plan has >6 phases AND the new pivot adds new surface area, switch to *batched close-out* (don't flip `status: completed → in-progress → completed` per pivot — flip once at chain start, leave open until session end) and fire a *spin-off gate* `AskUserQuestion` exactly once per chain ("keep chaining or spin off as a new campaign?"). Prevents 11-phase campaigns whose vault-log entry doesn't reflect what was actually shipped.
- **§0.0.4 — Preview reachability probe** — probe gated routes ONCE per session. If they redirect to `/login` and no test session is available, set `preview_verification: blocked-by-auth` in plan frontmatter and stop adding preview-verification steps to phase checklists. Saves 3-6 wasted `preview_eval` / `preview_snapshot` / `preview_list` calls per phase × N phases.
- **§Subagent dispatch — Source-walk subagent template + PDAAV DB sub-pattern** — names two patterns that recurred 3+ times in the campaign. *Source-walk template:* general-purpose subagent walks many files (>20), writes a JSON findings file to `docs/build-campaigns/<id>/NN-<topic>.json`, returns only summary inline; main thread parses JSON and builds SQL/UI/report from typed shape. *PDAAV chain:* probe (information_schema) → draft (inline SQL) → approve (AskUserQuestion) → apply (apply_migration) → verify (post-flight execute_sql). Phases following PDAAV can declare `db_pattern: PDAAV` in their plan instead of re-describing the five tool calls.
- **Failure modes #37-43:** pivot-chain accretion (#37), preview-verification-deferred theatre (#38), opaque long-running batches without sidecar progress logs (#39), mid-batch strategy pivot discarding partial work (#40), Read-Edit gap across waits >30s (#41), source-walk subagent returning inline instead of JSON-on-disk (#42), DB sub-pattern reinvented per phase instead of named (#43).

### v1.6.0 — 2026-05-15 — Build-mode DB safety + interactive verification (languages-admin campaign post-mortem)
Triggered by: lex_council `2026-05-15_languages-admin` campaign that shipped a FlutterFlow-inspired translation editor (6 locales × 9 namespaces × ~2700 keys + DB-backed override layer + admin gate). Three frictions surfaced that v1.5.0 didn't anticipate, plus one verification gap that compounds failure mode #20. Five additions:
- **§Step 3 W3 step 1.5d — Subagent reality-check gate (DB campaigns)** — before writing the migration body for any phase that depends on a W1 structural claim ("column X lives on table T", "policy Y references column Z"), run `execute_sql` against `information_schema.columns` / `pg_policies` / `pg_views` to confirm. W1 subagents reliably mis-locate columns when tables have been renamed mid-history or when a column conceptually belongs to one entity but lives on a permission-overlay table (`is_programmer` lives on `admin_perms`, not `council_members`). Build-mode mirror of failure mode #8.
- **§Step 3 W3 step 2a — Post-migration ground-truth check** — when `apply_migration` returns `{"success": true}`, *especially* after a fixed-and-retried failure, do not trust the response alone. Run SELECTs against `information_schema`, `pg_policies`, and `pg_class.reloptions` (for view `security_invoker`) and record as evidence in the phase change-log. Catches partial-apply, silently-dropped `security_invoker`, and missing `search_path = ''` on trigger functions.
- **§Step 2 plan template — `generation_strategy: deferred-parallel-subagents`** — when a phase needs to *generate* >5KB of artifact content per file (translations, fixtures, seed data, message bundles), the plan stores the *spec* not the content; W3 spawns parallel subagents per file writing directly to disk; the change-log records file sizes + a 5-10 line diff sample. Pre-drafting large artifacts inline overflows the planning subagent's response budget and silently truncates.
- **§Step 1.2 Q9 expansion + §Step 2 `verification_class: render | interactive`** — for CRUD/editor/form/multi-step features, the verification recipe must include BOTH a render recipe AND an interaction recipe (click X, save Y, reload, observe persisted, revert, reload, observe restored). Every FE phase declares `verification_class` in its frontmatter; `interactive` phases cannot be verified by the render recipe alone. Strict successor to failure mode #20 — render-passes-without-error is weaker than `tsc + lint green` for client-state features because it's satisfiable by a completely broken write path.
- **§5.2 — Runtime error provenance note** — when preview verification surfaces a console error, do not silently ignore as "pre-existing" or auto-attribute to the campaign. `git diff <campaign-start>..HEAD | grep -F '<error-substring>'`: absent → pre-existing → `spawn_task` + continue; present → campaign-introduced → phase blocker. Runtime mirror of failure mode #18.
- **Failure modes #32, #33, #34, #35, #36** — DB column mis-location, post-migration success not ground truth, large-artifact plan-time overflow, render-only verification of interactive features, runtime error provenance.

### v1.5.0 — 2026-05-15 — Session-scoped hygiene + W0 honesty (tasks-card-redesign chain post-mortem)
Triggered by: lex_council `2026-05-15` session that ran four sequential campaigns on the tasks page (`tasks-ui-consolidation` → `tasks-visual-bug-fixes` → `tasks-sidebar-restructure` → `tasks-card-redesign`) plus ~5 follow-up cosmetic refinement turns. The same-session pivot detection from v1.4.0 caught the obvious cases, but four lower-frequency frictions surfaced repeatedly across the chain. Four additions:
- **§0.0.2 — TodoWrite reset before fresh campaigns** (new sub-step) — the session todo list survives across campaign boundaries; without an explicit reset, the harness keeps reminding about completed items from the previous campaign for the rest of the session. Mandates a `TodoWrite` clear (or new-campaign seed) before the first Bash/Agent call of any new campaign.
- **§0.5.1 — W0 prescan quality gate** (new sub-step) — local Ollama can produce prompt-echo garbage (output shape matches the prompt's headers but contains no actual file insight); the v1.4.0 "W0 mandatory when Ollama is available" rule presumes the prescan *contains* signal but never validates it. Adds a checklist (line counts, real entity names, named files in surface map) to mark `w0_useful: yes|no` in the plan. When `no`, W1 subagents read files cold instead of citing the empty prescan. Also: skip W0 entirely for builds touching <10 files (no fan-out, no compression payoff).
- **§Step 1.2 Q13 + §Step 2 `standing_instructions:` frontmatter** — when running ≥2 campaigns in the same session, every new campaign's plan must quote verbatim every standing instruction inherited from prior campaigns ("work without stopping for clarifying questions") and name the predecessor it was set in. The approval-cadence field captures the posture; standing-instructions captures the user's literal words so nothing is paraphrased into a different meaning.
- **§Environment hazards — Multi-Edit atomicity trap** (new bullet) — when a phase needs ≥2 sequential Edits to the same file where the intermediate state would fail lint (e.g. add a helper function in Edit #1, add its call sites in Edit #2), the linter fires between Edits and strips the unused helper. Mitigation is structural: use a single `Write` over the whole final content. The `Edit` tool is for *consistent* incremental changes.
- **Failure modes #28, #29, #30, #31** — multi-Edit atomicity trap, TodoWrite list survives across campaigns, W0 prescan ships echo-back garbage, standing instructions silently inherited.

### v1.4.0 — 2026-05-15 — Same-session pivot + plan-time render extraction (insights-sidebar-refactor post-mortem)
Triggered by: lex_council `2026-05-14_insights-sidebar-refactor` campaign, which shipped Phase 1 + Phase 2 cleanly (vault-log, status: completed, tsc + lint green) but the user invoked `/conquering-campaign` again minutes later with screenshots showing the just-shipped `InsightsList.tsx` was an HTML `<table>` while the named reference (`FilesList.tsx`) renders card rows. The pivot took a second full pass (re-ran W0, re-drafted plan, hand-rolled a 3rd `*ListRow.tsx` clone alongside `FileListRow` + `BalanceListRow`) when the predecessor's plan, prescan, and discovery were all still in-context. Five additions:
- **§0.0.1 — Same-session pivot detection** (new sub-step in Step 0) — classifies the case where the user re-invokes the skill within the same session after a campaign just closed; skips W0, appends a phase to the existing plan with `discovered_during: same-session-pivot` (mirrors W4-discovered-phase pattern), edits the vault log in place. Sits between §0.0 (resume `in-progress`), §Step 4 W4-discovered (defect during W4), and §5.8 (post-closure days later) — none of which fired before.
- **§Step 2 plan template — `## Reference render structure` is REQUIRED** for visual-conformity campaigns. The block extracts the reference's *rendered JSX* into labelled lines (outer wrapper, Line 1, Line 2, hover/transition, leaf primitives) — not its imports or signature. Plans without this block cannot be approved. Promotes failure mode #19 from prose discipline to plan-time enforcement.
- **§Step 2 plan template — `## Verification recipe` is REQUIRED** for any FE-surface campaign. The Q9 browser recipe is no longer a soft "captured during interrogation" item; it lives in the plan and re-runs at every phase-exit. A campaign that ships green `tsc + lint` without this recipe is shipping on faith.
- **§Step 3 W3 step 1.5 — Pre-execution gates** (new) — three checks before the first Write call of any UI phase: (a) reference render-structure gate, (b) consolidation grep gate (N=3 alarm) for new `*ListRow.tsx`/`*Card.tsx`/`*Row.tsx` files, (c) re-read the reference immediately before drafting. Pairs with the §W3 stale override sweep — both are grep-driven gates that catch a known cascading mistake before it lands.
- **§5.3 vault-log — Same-session pivots update in place; incidental fixes get an `## Incidental fixes` heading** when ≤3 lines and in a file already being edited. Drive-by larger fixes get CHECKPOINTED instead.
- **Failure modes #25, #26, #27** — same-session pivot misclassification, plan named reference but didn't extract render, Nth hand-rolled clone of a recurring shape.

### v1.3.0 — 2026-05-15 — Post-closure tweak drag + cascading-default leak (documents-ui-features post-mortem)
Triggered by: lex_council `2026-05-15_documents-ui-features` campaign, where the 3-phase BUILD shipped cleanly (vault-log, risk sweep, status: completed) and was then followed by ~5 one-shot tweak turns over the next hour that each addressed an unaddressed adjective from the original framing or a stale `iconColor` override against the now-ghost `TableActionBtn` default. Six additions:
- **§W3 step 2.5 — Stale override sweep** (new mandatory phase step) — when a phase changes a shared primitive's visual default, grep every consumer prop override and classify against the new default (still-correct / stale / newly-redundant). Pair with the stale doc-comment sweep in the same step. Without this gate, cascading-default leaks surface as N follow-up one-shot turns
- **§5.8 — Post-closure tweak detection** (new section) — classifies post-closure tweaks as stub-extension (log to predecessor's §10 follow-ups) vs mini-extension (re-open as EXTENSION mode); names "fix X too" as the trigger phrase for unaddressed-adjective signal
- **Consolidation discipline §4 — Grep before changing a shared default** — `grep -rn` the property/token across the codebase **before** picking which files to edit; decide the new value across all sites in one pass, never per-complaint
- **Conformity discipline — Stale doc-comment sweep** added to the end-of-campaign checklist — header comments stating "32×32 navy bg, white icons" lie after a ghost migration; grep and update/remove
- **§5.4 — Memory entry triggers table** — explicit triggers for lint-rule-under-`--max-warnings 0`, user corrections, surprise W1 discoveries, contradictory grep results. Zero-tolerance lint rules are project laws worth memorizing immediately
- **Failure mode #17 clarification** — when a single-turn cosmetic phase completes in one Edit, the turn IS the phase — honor the preview hook at turn close
- **Failure mode #23** — cascading-default leak; latent bugs from explicit overrides against the OLD default
- **Failure mode #24** — post-closure tweak drag; "fix X too" = unaddressed adjective from predecessor's re-anchor

### v1.2.0 — 2026-05-15 — Visual alignment post-mortem (IDs row redesign)
Triggered by: lex_council `2026-05-15_ids-row-redesign` session, where repeated back-and-forth rounds over icon button style exposed three gaps in the conformity discipline. Three additions:
- **Conformity discipline "Before writing any code" §2** — new "Visual alignment extraction" sub-section: follow the import chain to the leaf action-bar/primitive component (not the page-level row), extract specific property values (border, radius token, icon size/color, tooltip mechanism, hover pattern) before writing anything, and re-read the reference immediately before implementing in case it was updated mid-session
- **Conformity discipline "Before writing any code" §3** — added "Layout direction (LTR/RTL)" to the conventions inventory; if the UI is English admin, container direction is LTR even when DB values are Arabic
- **Failure mode #22** — design-language matching from the wrong or stale reference; style lives in leaf sub-components, not row-level components; re-read before implementing

### v1.1.0 — 2026-05-15 — Dark-mode rollout post-mortem
Triggered by: lex_council `2026-05-15_dark-mode-rollout` campaign, where P0–P4 shipped green type-check + lint but the user-facing dark mode was broken on every non-admin page due to an SSR/client hydration mismatch in the Zustand theme store. Six additions:
- **Step 1.2 Q9** — added "browser verification recipe" sub-question to capture the smallest possible browser test for any user-facing outcome; campaign close gates on outcome verification, not process completion
- **Self-verification loop** (build mode, step 5) — preview verification is now REQUIRED (not optional) for UI / theme / auth / hydration / realtime / locale / i18n surfaces; multi-timestamp polled DOM reads required to catch hydration timing bugs
- **Environment hazards** — new subsection "SSR / client hydration mismatch with module-level state" documents the Zustand-style trap, symptoms, and the two-layer fix (synchronous `<head>` bootstrap + mount-time re-sync `useEffect`)
- **Step 4 build mode** — new subsection "W4-discovered phases" formalises how to handle defects surfaced during W4 verification (allocate phase ID with `discovered` marker, run through full self-verification loop, label distinctly in vault-log; campaign closes only after discovered phases pass)
- **Failure mode #20** — `tsc + lint` green is a false-confidence trap for client-state features; risk-sweep matrix needs observation behind every "✓"
- **Failure mode #21** — diagnostic state pollution; always `location.reload()` between manual state pokes and verification reads
- **Risk-sweep §3 (surface coverage matrix)** — explicitly requires concrete observations behind every "✓"

### v1.0.0 — initial release
Two modes (AUDIT / BUILD) + EXTENSION sub-pattern, four-wave structure (W0 Ollama prescan + W1 discovery + W2 phase plans + W3 implementation + W4 verification), three approval cadences (strict / autonomous / hybrid), three-tier model assignment (Ollama / sonnet / opus), conformity + consolidation disciplines, autonomous decision ladder, forced-gate rules for >15-site renames, candidate-deletions cleanup pattern, 19 documented failure modes. Current total: 56 failure modes through v1.11.0.
