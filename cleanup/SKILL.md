---
name: cleanup
version: 1.8.1
description: Multi-mode hygiene skill for Lex Council. Today's modes — language (LIVE); consolidate (LIVE, i18n key dedup); errors (LIVE); postgres (LIVE, Supabase advisors + pg health, auto-fix FK indexes, flag schema issues for campaign); lint (LIVE, ESLint --fix safe rules + tsc, surface architectural violations); consolidate-code (LIVE, code-side duplicate detection via scripts/consolidate_code.py — components/views/RLS-predicates/constants/literals — registry CONSOLIDATION-CANDIDATES.md, byte-compare before merge, dry-run extract); release (LIVE, app-upgrade gate + version bump — runs the lint+errors+postgres+bundle/Next16 hygiene gate then performs the full version bump: app.config.ts + changelog + doc-stamp sync + git block; absorbs the retired update-app-version skill); docs (LIVE, scripts/docs_cleanup.py — frontmatter/wikilinks/orphans/retired-names/artifacts/campaign-drift); followups (LIVE, scripts/followups_cleanup.py — locate/extract/classify deferred items). See UPGRADE-ROUTES.md for the skill roadmap. Run every hygiene mode at once + get one severity-ranked triage dashboard via `scripts/run_all.py` ("run all cleanups"). Use this skill whenever the user says "run cleanup", "/cleanup", "/lex_cleanup", "clean up the languages", "translate untranslated", "i18n cleanup", "fill in translations", "language cleanup", "consolidate translations", "merge safe-to-merge keys", "clear duplicates", "check the dev log", "sweep the dev errors", "what errors did i hit", "fix the dev errors", "check postgres", "check the db health", "run the postgres sweep", "check supabase advisors", "fix the advisor issues", "check the db errors", "run lint", "fix the lint errors", "sweep the lint issues", "check tsc", "run eslint", "sync the doc footers", "doc cleanup", "finish the followups", "close the followups", "bump the version", "update the app version", "release X.Y.Z", "ship a release", "cut a new version", or any phrasing that implies sweeping the app for a class of accumulated drift after new pages or keys or campaigns landed. Auto-discovers scope, parallelizes the heavy work across N subagents (5 for language; 1 per planet for docs), applies results, verifies, and delegates the vault log to vault-log-compliance. Skill is upgradable — add new modes by appending a §Mode section + adding a router branch under §Workflow; bump the `version` per §Versioning whenever the skill changes.
---

# Cleanup — Lex Council hygiene sweeps (v1.8.1)

This skill packages the operational recipes for periodic cleanup passes that
the app accumulates between feature builds. Each mode is independent; the
skill body routes to the right workflow based on what the user asked for.

## Modes

| Mode | Status | What it does |
|---|---|---|
| **language** | LIVE | Sweep every non-EN locale (ar/es/fr/ru/zh), find keys still equal to the English value, translate them in parallel via 5 subagents, write back, verify. |
| **consolidate** | LIVE | Detect cross-locale safe-to-merge i18n groups, pick surgical universal labels (Status / Type / Yes / etc.), AST-aware callsite mapping, two-phase apply (dead keys first then live rewrites), delete now-orphan keys. Script: `scripts/consolidate_cleanup.py`. Also future: code-side consolidation — surface 3+ near-duplicate hard-coded literals for refactor-with-helper. |
| **errors** | LIVE | Parse `/tmp/lex-dev.log` (tee'd `npx turbo dev` stdout + the DevErrorSink browser payloads), dedupe by error-signature, classify each unique entry as code-bug / framework-noise / external / unknown. Surface a per-error triage list with file:line context; auto-fix the unambiguous code-bugs (single-line ?.-chain, missing import, named-typo); surface the rest. Script: `scripts/errors_cleanup.py`. |
| **postgres** | LIVE | Run Supabase `get_advisors` MCP + pg health queries; write raw output to `/tmp/pg_advisors.json` + `/tmp/pg_health.json`. Classify each finding as advisory-auto-fix / advisory-surface / schema-campaign / noise. Auto-apply additive migrations for missing FK indexes. Flag RLS/schema issues as requiring a dedicated campaign. Script: `scripts/postgres_cleanup.py`. |
| **lint** | LIVE | Run `npm run lint -- --format json` from `lex_council/`, parse ESLint output, dedupe by `(file, rule)`, classify as auto-fixable / architectural / wip-noise. Auto-run `eslint --fix` for safe rules, run `tsc` to verify, surface architectural violations as campaign candidates. Script: `scripts/lint_cleanup.py`. |
| **consolidate-code** | LIVE | Code-side sibling of `consolidate`. Scan for duplicate/copy-pasted CODE (components, functions, DB views/RLS predicates, style-constants, magic literals, config defined in N places) → produce/refresh `CONSOLIDATION-CANDIDATES.md` → classify each extract-now / needs-campaign / resolved → extract the T1 (mechanical) tier, surface the rest. **Byte-compare before merging (§L2/§L4 look-alike-but-different).** Registry pre-seeded from 146-session mining (41 open candidates). |
| **release** | LIVE | App-upgrade gate **+ version bump** (absorbed the retired `update-app-version` skill, cleanup v1.6.0). Phase 1 — hygiene gate: lint + errors + postgres advisory checks, Cloudflare/OpenNext bundle-wall + Next.js 16 hazard probes, green/red verdict. Phase 2 (only if green) — full bump: `apps/web/config/app.config.ts` + changelog (`logs/X.Y.Z.md` + `logs/INDEX.md` row) + doc-stamp sync (Vault Core ×3 + ARCHITECTURE) + git block. Full recipe in `references/release-procedure.md`. Gate-only via `/cleanup release --gate`. |
| **docs** | LIVE | Sync stale frontmatter dates + counts on planet hubs (BACKEND/FRONTEND/INTEGRATION/DESIGN-CANON/GENERAL-GUIDELINES/Vault Core); flag broken wikilinks + archived-pointers; find orphan vault-logs missing from INDEX.md; bump app version stamp in Vault Core; grep all docs for retired-primitive names; detect post-rename narrative artifacts (telltale "X (v2; was X)" patterns). |
| **followups** | LIVE | After a campaign closes, sweep the most recent vault-logs (+ campaign `99-risk-sweep.md` files) for explicitly-deferred items ("follow-up", "spawn_task", "future cleanup", "code cleanup checklist"). Classify each as doable-autonomously / needs-user-hands / accepted-permanent-exception. Execute the doable ones in parallel; surface the rest as a checklist. |

When more modes are added, append the section + add a router branch under
§Workflow. Modes do not assume each other — a `language` pass does not
imply a `docs` pass, and `followups` is intentionally separate from
`docs` (followups runs after a specific campaign; docs runs on a periodic
hygiene cadence regardless of recent campaign activity).

## When to invoke this skill

Trigger phrases (any of):

- `/cleanup` (slash invocation)
- "run cleanup", "do the cleanup pass"
- "clean up the languages", "language cleanup", "i18n cleanup"
- "translate the untranslated keys", "fill in translations", "translate the missing strings"
- "we shipped a new page — let's do the cleanup"
- "consolidate the duplicate translations", "merge safe-to-merge keys", "clear duplicates", "clear the duplicate translations" → routes to `consolidate`
- "check the dev log", "sweep the dev errors", "what errors did i hit", "fix the dev errors", "triage the errors", "/cleanup errors" → routes to `errors`
- "check postgres", "check the db health", "run the postgres sweep", "check supabase advisors", "fix the advisor issues", "check the db errors", "sweep db issues", "/cleanup postgres" → routes to `postgres`
- "run lint", "fix the lint errors", "sweep the lint issues", "check eslint", "run eslint", "check tsc warnings", "fix lint", "/cleanup lint" → routes to `lint`
- "find duplicate code", "what should we consolidate", "consolidation candidates", "find copy-pasted code", "what needs consolidating", "/cleanup consolidate-code" → routes to `consolidate-code`
- "pre-release check", "ready to release", "pre-push sweep", "release hygiene", "bump the version", "update the app version", "release X.Y.Z", "ship a release", "cut a new version", "make it 1.7.X", "/cleanup release" → routes to `release` (use `--gate` for gate-only)
- "sync the doc footers", "doc cleanup", "check the docs are fresh", "are the docs stale" → routes to `docs`
- "finish the followups", "close the followups", "sweep the campaign followups", "what's left from the audit" → routes to `followups`

Skip when:

- The user is mid-feature and the work isn't ready to be swept yet.
- A previous cleanup pass ran today and nothing new was added since.
- The user asks about cleanup but is really asking about something else
  (e.g. "clean up this component" = refactoring, not this skill).

## Workflow

### Step 0 — Pick the mode

Look at the user's phrasing. Default mode is `language` unless they
explicitly named another. If unsure, ask before proceeding — the modes have
very different blast radius.

| Phrasing | Mode |
|---|---|
| `/cleanup`, "run cleanup" (bare), "i18n cleanup", "language cleanup", "translate untranslated" | `language` |
| "consolidate the translations", "merge safe-to-merge keys", "clear duplicates", "/cleanup consolidate" | `consolidate` |
| "check the dev log", "sweep the dev errors", "fix the dev errors", "what errors did i hit", "/cleanup errors" | `errors` |
| "check postgres", "check the db health", "check supabase advisors", "fix the advisor issues", "/cleanup postgres" | `postgres` |
| "run lint", "fix the lint errors", "check eslint", "run eslint", "/cleanup lint" | `lint` |
| "find duplicate code", "what should we consolidate", "consolidation candidates", "/cleanup consolidate-code" | `consolidate-code` |
| "pre-release check", "ready to release", "pre-push sweep", "bump the version", "update the app version", "release X.Y.Z", "make it 1.7.X", "/cleanup release" | `release` (add `--gate` to stop after the hygiene gate) |
| "sync the doc footers", "doc cleanup", "/cleanup docs", "check the docs are fresh" | `docs` |
| "finish the followups", "close the followups", "/cleanup followups", "sweep the campaign followups" | `followups` |
| "run all cleanups", "/cleanup all", "what's drifted" | run `python3 ~/.claude/skills/cleanup/scripts/run_all.py run [--fast]` — runs the local hygiene modes detect-only (docs, errors, language, consolidate-code, lint) then writes a severity-ranked `/tmp/cleanup_triage.md` dashboard + per-mode last-run age. postgres needs MCP (run `/cleanup postgres` first; the report merges any existing pg JSON); apply-modes are never auto-run. |

If the user's phrasing matches more than one mode (e.g. "run cleanup after
that campaign"), prefer `followups` over `docs` — the post-campaign sweep
is more specific.

### Mode: language

The end-to-end recipe. The companion script
`scripts/i18n_cleanup.py` owns the mechanical detect/apply/verify steps;
this section owns the agent orchestration that sits between them.

#### Step L1 — Detect scope

Run from the repo root:

```bash
python3 ~/.claude/skills/cleanup/scripts/i18n_cleanup.py detect
```

This writes 5 files to `/tmp/translation_targets_{loc}.json` (one per
non-EN locale) — each is a JSON array of `{ns, key, en}` triples where
the locale's value still equals the EN value (the
`isRowUntranslated` heuristic the Languages dev-tools panel uses).

Default behavior translates ALL flagged strings. To skip ES/FR
single-word-no-placeholder cognates (e.g. "Finances", "Documents"),
pass `--skip-cognates`. By default Atta has rejected this filter —
keep that as the project default unless he says otherwise this session.

Show the user the per-locale counts and ask whether to proceed. If the
total is large (>500), surface the top 3 namespaces by count so they
know where the work is concentrated.

#### Step L2 — Spawn 5 parallel translation agents

Spawn 5 general-purpose subagents **in a single message** (so they run
concurrently). Each gets the per-locale agent prompt from §"Agent prompt
templates" below, with the locale-specific bits filled in.

Use `run_in_background: true` for each. The user's terminal will
notify you as each completes — do NOT poll.

Hard contract every agent must satisfy:

- Read its target file (`/tmp/translation_targets_{loc}.json`).
- Translate each `en` field per the locale-specific register guidance.
- Preserve every `{placeholder}` exactly (no translating variable
  names; Russian may reorder placeholders due to grammatical case —
  that's OK).
- Keep brand glossary terms in Latin script (see §Brand glossary).
- Return identical count, same order as input.
- Write output to `/tmp/translations_{loc}.json` as a pure JSON array
  of `{ns, key, translated}` — no markdown fences, no commentary.

#### Step L3 — Pre-flight + apply

When all 5 agents have completed:

```bash
python3 ~/.claude/skills/cleanup/scripts/i18n_cleanup.py apply
```

This runs pre-flight (count match, placeholder match, no empty
translations) **before** touching any messages file. If any locale
fails pre-flight, the script aborts unless `--force` is set. Surface
the failure to the user and ask before forcing.

On pass, the script writes each translation into
`messages/{loc}/{ns}.json` via a dotted-key nested-dict walker. JSON
structure + indentation + trailing newlines preserved.

#### Step L4 — Verify

```bash
python3 ~/.claude/skills/cleanup/scripts/i18n_cleanup.py verify
cd lex_council && npx turbo run check-types --filter=web
```

The verify step re-runs the detector and prints the new untranslated
counts per locale. Expect the number to drop sharply but **NOT** reach
zero — the floor is brand acronyms + form placeholders
(`email@example.com`, `0.00`, etc.) + ES/FR cognates that are
correctly identical to English. Report the delta (before → after) to
the user.

`tsc` should pass cleanly — JSON edits can't break types but it's
worth confirming nothing else regressed.

#### Step L5 — Vault log

Delegate to the **vault-log-compliance** skill. Provide it a one-line
summary of what changed (locale counts + delta) so it can draft an
entry similar to `2026-05-28_translation-pass-non-en-locales.md`.

Then update auto-memory if anything surprising came up during the pass
(new brand terms to add to the glossary, a locale-specific gotcha,
etc.).

### Mode: docs (LIVE)

> **Script:** `python3 ~/.claude/skills/cleanup/scripts/docs_cleanup.py <frontmatter|wikilinks|orphans|retired-names|artifacts|campaign-drift|all>` — detect-only, never edits a docs file. The DB count-probes (D3) remain Claude's job via MCP.

A periodic hygiene sweep of the planet hubs. Lighter-weight than a full
audit campaign (`conquering-campaign` AUDIT mode) — runs the cheap
catch-all checks that surface drift without re-querying the entire DB.

#### Step D1 — Inventory the planet hubs

The skill ships with a hard-coded list of planet hubs (matches what the
2026-05-28 solar-system audit covered). If a future hub is added, append
it here:

```
Vault Core.md
primary_instructions.md
GENERAL-GUIDELINES.md
BACKEND.md
FRONTEND.md
INTEGRATION.md
DESIGN-CANON.md
V2-CONVENTIONS.md
```

#### Step D2 — Per-hub frontmatter sweep

For each hub, run these checks and produce a per-hub findings line. The
companion script `scripts/docs_cleanup.py` owns the mechanical
parts; this section owns the contract.

| Check | Probe | Action when flagged |
|---|---|---|
| **Stale `last_full_audit` / `counts_updated` / `last_synced` date** | YAML frontmatter field; flag if > **14 days** old | Surface; don't auto-update unless the substance check below also passes |
| **Stale `counts: {…}` numbers** | For each count key, run the matching ground-truth command (see §D3) | If delta < 5% → auto-bump the count; if ≥ 5% → flag for a full audit campaign |
| **Frontmatter promises a checkpoint file that doesn't exist** | `checkpoint_file` field resolves to a real path | Surface |
| **App version stamp drift (Vault Core only)** | `app_version` frontmatter + body "App version: X.Y.Z" line vs `apps/web/config/app.config.ts` | Auto-update both Vault Core surfaces |

#### Step D3 — Ground-truth counts table

For each planet hub, run these probes (composable; the script can skip
any whose hub doesn't declare the matching count key):

| Count key | Probe |
|---|---|
| `pages` (FRONTEND) | `find lex_council/apps/web/app -name "page.tsx" \| wc -l` |
| `admin_pages` | `find "lex_council/apps/web/app/[locale]/(admin)" -name "page.tsx" \| wc -l` (same for members / clients / public / auth / portal) |
| `stores` | `ls lex_council/apps/web/store/*.ts \| wc -l` |
| `hook_files` | `ls lex_council/apps/web/hooks/*.ts \| wc -l` |
| `mutation_modules` | `ls lex_council/apps/web/lib/mutations/*.ts \| wc -l` |
| `perm_keys` | count entries in `PERM_META` in `apps/web/lib/permissions.ts` |
| `tables` (BACKEND) | `execute_sql` against `information_schema.tables` filter `schema=public, type=BASE TABLE` |
| `views` | same — `information_schema.views` |
| `triggers` | `pg_trigger` join `pg_class` filter `schema=public, NOT tgisinternal` |
| `pub_fns` / `priv_fns` | `information_schema.routines` filter `routine_schema in (public, private)` |
| `rls_policies` | `pg_policies` filter `schemaname=public` |
| `cron_jobs` | `cron.job` |
| `edge_functions` | `list_edge_functions` MCP call |

**MCP project_id is always `bqgrpnsvplvicnmzxwkm`** (production). Skip
DB probes silently if MCP isn't available; flag the skip in the output.

#### Step D4 — Wikilink rot sweep

Across `lex_council/docs/`:

```bash
grep -rnoE '\[\[[^]]+\]\]' lex_council/docs/ --include="*.md" \
  > /tmp/docs_wikilinks.tsv
```

For each `[[X]]`:

- **Broken** — no file matching `X*.md` exists anywhere under
  `lex_council/docs/` (recursive). Flag.
- **Archived-pointer** — resolves only to `architecture/_archived/`.
  Per `primary_instructions §2`, archived content is off-limits. Flag
  with the recommendation to retarget or strike.
- **Resolved** — silently OK.

#### Step D5 — Orphan vault-logs

```bash
# Vault-log files that exist
ls lex_council/docs/vault-logs/ | grep -E '^[0-9]{4}-[0-9]{2}-[0-9]{2}_' > /tmp/vl_files.txt
# Vault-log basenames referenced in INDEX.md
grep -oE '\[\[[0-9]{4}-[0-9]{2}-[0-9]{2}_[^]]+\]\]' lex_council/docs/vault-logs/INDEX.md \
  | sed 's/\[\[//; s/\]\]//' | sort -u > /tmp/vl_indexed.txt
# Files present but not indexed
comm -23 <(sort /tmp/vl_files.txt) <(sort /tmp/vl_indexed.txt | sed 's/$/.md/')
```

Surface every orphan. Auto-fixing is risky (the entry's summary needs
prose); flag for the user to triage.

#### Step D6 — Retired-name registry sweep

Maintain a hard-coded list of names retired by past large refactors.
Grep all docs for each occurrence; surface for triage. Auto-fixing is
forbidden — some occurrences are legitimate historical context.

```
# v2 schema (2026-05-26 merge)
fd, fd_access, fd_access_js, council_members, ppl, cm_hr, admin_perms,
whbd_responses, whbd_*, atnd_*, n_*, evi, evo, is_verified, cm_ap_js,
cm_basic_js, cm_notification_types

# retired primitives
KpiStrip, useKpiCells, PageHeaderStrip, AdminPageShell, AdminFilterBar,
AdminDataTable, TableActionBtn, BottomActionBtn, ModalShell,
FormModalWrapper, MultiSelectFilterDropdown, STAT_CARDS

# stale tokens
C.borderLight, C.hoverRow, C.greySurface, iconSize.*
```

When adding to the registry, also add a one-line note about the
retirement (vault-log link + date) so the surfaced grep hit is easy to
classify.

#### Step D7 — Post-rename narrative-artifact sweep

Telltale pattern from the 2026-05-28 audit's BACKEND.md global-replace
leftovers: prose that reads `X (v2; was X)` — same name on both sides
of the parenthetical. Indicates a botched mass-rename that
over-rewrote the historical "was" leg.

```bash
# Find "X (v2; was X)" patterns
grep -rnoE '`([a-z_]+)` \(v2; was `\1`\)' lex_council/docs/ --include="*.md"
# Also: "X (was X)" with identical leg
grep -rnoE '`([a-z_]+)` \(was `\1`\)' lex_council/docs/ --include="*.md"
```

Surface each; the user picks the correct pre-v2 name from their head
(or the script can look up `<retired-names-registry>` for the matching
pre-rename name when there's only one candidate).

#### Step D8 — In-progress campaign drift

Cross-reference `build-campaigns/*/00-campaign-plan.md` frontmatter
`status:` against vault-log existence:

```bash
grep -l "status: in-progress" lex_council/docs/build-campaigns/*/00-campaign-plan.md \
  | while read plan; do
    topic=$(dirname "$plan" | xargs basename)
    if ls lex_council/docs/vault-logs/${topic}*.md 2>/dev/null | head -1 > /dev/null; then
      echo "DRIFT: $plan says in-progress but vault-log exists"
    fi
  done
```

Surface each. Auto-update to `status: completed` is risky (the
`phases_completed` array may not be accurate either) — flag for the
user.

#### Step D9 — Per-hub findings file + summary

Each hub gets a one-line summary in the findings file
(`/tmp/docs_cleanup_findings.md`) so the user can scan + triage:

```markdown
- **BACKEND.md** — counts: tables 132→106 (DRIFT >5%, flag for audit);
  wikilinks: 0 broken; orphan vault-logs in scope: 0; retired-names in
  prose: 4 occurrences; narrative artifacts: 2 (`X (v2; was X)`); status: STALE.
```

#### Step D10 — Apply + vault log

Auto-fixed items (frontmatter date bumps, count auto-bumps when delta
< 5%, app version stamp) get a single small vault-log entry via
**vault-log-compliance**. Larger drift (>5% count drift, broken
wikilinks, retired-name prose) is **NOT** auto-fixed by this mode — it
needs the full `conquering-campaign` AUDIT pass.

> **Cleanup-docs vs full audit campaign.** Cleanup-docs runs every
> ~14 days and catches small drift cheaply. A full audit campaign
> (via `/conquering-campaign`) runs when cleanup-docs flags a delta
> >5%, when a major refactor (v2-style schema rename, primitive
> family retirement) ships, or when ≥3 large vault-logs land between
> cleanup runs. The two are complementary, not substitutes.

### Mode: followups (LIVE)

> **Script:** `python3 ~/.claude/skills/cleanup/scripts/followups_cleanup.py <locate|extract|classify|mark>` — automates locate→extract→classify (+ mark). EXECUTION of the doable items (F4) is Claude's job, not the script.

After a campaign closes, the campaign's `99-risk-sweep.md` (build mode)
or `99-synthesis.md` (audit mode) typically lists 5–10 deferred
follow-up items. The 2026-05-28 solar-system doc-sync audit shipped 8
follow-ups; 5 doable autonomously + 3 needing user hands. Without a
codified pattern, these get handled ad-hoc (each as a one-shot turn)
or silently dropped. This mode codifies the sweep.

> **Auto-spawned by `conquering-campaign` at campaign close** (its v3.3.0 §5.7 calls `spawn_task` → a fresh session/worktree runs `/cleanup followups` with the campaign's `99-risk-sweep.md` ## Open items + touched-surface list inlined in the prompt). So this mode often runs in a session the campaign kicked off — no manual invoke. If that spawn was skipped (Cowork/headless) or the chip dismissed, nothing is lost: the committed `99-risk-sweep.md` is still the durable queue F1 locates (most-recent `status: completed`).

#### Step F1 — Locate the campaign

```bash
# Most recent campaign with status: completed
find lex_council/docs/{audit,build}-campaigns -name "00-campaign-plan.md" \
  -newer /tmp/last_cleanup_marker 2>/dev/null \
  | xargs grep -l "status: completed"
```

If the user invoked `/cleanup followups` with a specific campaign name,
use that; otherwise default to "the most recently-closed campaign whose
follow-ups haven't been swept yet" (track via `/tmp/last_followup_sweep_marker`).

#### Step F2 — Extract follow-up items

Grep the campaign's W4 artifact for the standard markers:

```bash
# Audit mode: 99-synthesis.md "## Code cleanup checklist" + "## Open items"
# Build mode: 99-risk-sweep.md "## Open items" + per-phase "deferred to" mentions
# Vault-log: search for "follow-up", "spawn_task", "future cleanup", "Atta to dispatch"
```

Produce a per-item list with `{ id, surface, description, blocker_hint }`.

#### Step F3 — Classify each item

For each item, decide:

| Class | Examples | Action |
|---|---|---|
| **doable-autonomously** | small code edits, MCP-doable DB checks, `git rm` of confirmed-orphan files, frontmatter sync, RLS verification queries | Do now under autonomous cadence |
| **needs-user-hands** | external dashboard clicks (Supabase delete edge fn, NAS scripts, third-party API config), `[!atta]` block edits, security gates the user explicitly reserved | Surface as checklist; user dispatches |
| **accepted-permanent-exception** | items the user has previously marked as "leave as-is" (cite the prior decision) | Note in followups file; don't surface as actionable |

The classification rubric is empirical — when in doubt, surface as
needs-user-hands. Misclassifying a doable item as needing-hands is
cheap (user can say "do it"); misclassifying a hands item as doable
risks unauthorized actions on a surface the skill can't reach.

#### Step F4 — Parallel execution of doable items

For 3+ doable items: dispatch in parallel as the `language` mode does
its 5 locale subagents. For 1–2 doable items: handle inline (no
subagent fan-out overhead).

For each doable item, run the standard verification gate appropriate
to the surface:

- **Code edit** — tsc + lint on touched files
- **DB refactor** — PDAAV pattern from `conquering-campaign` (probe →
  apply → verify post-state matches pre-state matrix)
- **File delete** — `git ls-files` confirms untracked OR `git rm`
  succeeds cleanly
- **MCP check** — record the SELECT result as evidence in the
  follow-up vault-log

#### Step F5 — Vault log per surface

When ≥3 follow-ups touched the same surface (e.g. 5 DB changes), file
one combined vault-log entry; otherwise file one entry per follow-up
item. Title pattern: `YYYY-MM-DD_<predecessor-campaign>-followups.md`.
Each entry's `predecessor:` frontmatter field points to the campaign
the follow-up extends.

The vault-log also surfaces the **deferred-to-user** checklist + the
**accepted-permanent-exception** list, so future readers can see the
full disposition of the original campaign's follow-up backlog from
one entry.

#### Step F6 — Mark the cleanup marker

```bash
touch /tmp/last_followup_sweep_marker
```

So the next `/cleanup followups` invocation knows where to start.

### Mode: consolidate

Fold safe-to-merge i18n keys (groups where N>1 keys share the SAME English
value AND the SAME translation in every locale) into shared `common.*`
keys. AST-aware callsite rewrites + two-phase apply (dead keys first;
then live rewrites + key deletion). Script:
`scripts/consolidate_cleanup.py`.

**Why this is the riskiest cleanup mode.** Unlike `language` (JSON-only
edits) or `docs` (docs-only edits), consolidate touches TSX/TS source —
miss a callsite and you get a `MISSING_MESSAGE` runtime error in
production. Three traps documented from the 2026-05-28 first pass:

| Trap | What broke | Why |
|---|---|---|
| **Naive Explore agent says "0 callsites"** | Initial agent run reported all 62 keys dead — they weren't. | The agent only checked the full key path. It missed deeper-namespace patterns like `useTranslations('admin.chat.bubble').t('menu_delete')`. |
| **Suffix-grep over-matches** | A second attempt with all suffix variants reported 744 callsites — also wrong. | `'status_label'` matched `severance_calculator.form.contract_type_label` and dozens of unrelated keys. |
| **Variable-name confusion** | A file with `const tp = useTranslations('portal')` AND `const tc = useTranslations('common')` would have `tc('labels.status')` AND `tp('labels.status')` calls — string grep can't tell which is `portal.labels.status` (doomed) vs `common.labels.status` (target). | Only AST-aware parsing — read each file, track which `t` variable maps to which namespace via `useTranslations` bindings, then resolve each `t-call` to its full key — produces the right answer. |

**Rule for consolidate mode:** never trust a generic-purpose agent's
"callsite map". Always run `scripts/consolidate_cleanup.py map-callsites`,
which does the AST-aware resolution properly.

#### Step C1 — Detect safe-to-merge candidates

```bash
python3 ~/.claude/skills/cleanup/scripts/consolidate_cleanup.py detect
```

Outputs `/tmp/safe_to_merge.json` and prints the cross-NS table sorted
by lift (count desc). For each candidate, shows whether `common.json`
already has a key with the same EN value (clean target) or whether one
must be added.

The output is the input to a CONVERSATION with the user — not an
auto-apply candidate list. Most of these groups should NOT be merged.

#### Step C2 — Pick the surgical set with the user

Default policy (codified from the 2026-05-28 first run): **only merge
universal labels with zero domain semantics.** The accepted "safe to
merge" patterns:

- Pure UI verbs in `common.actions.*` — Save, Close, Delete, Download, Edit, Cancel, Send, Add
- Pure UI nouns in `common.labels.*` — Status, Type, Description, Date, Yes, No
- Language names in `common.{english,arabic,french,russian,chinese,spanish}`

The accepted "DO NOT merge" patterns (even though their EN value matches):

- Entity nouns — Tasks, Cases, Files, Documents, POAs, IDs, Clients, Members (domain-specific; likely to diverge per context)
- Generic-but-context-bound headers — Details, Home, Tools, Office, Notes (may want to specialize as "Case Details" vs "Task Details" later)
- Same-namespace dups — keep these; they may share an EN value by coincidence but their *contexts* differ within the namespace

When in doubt, ask the user explicitly. Don't infer.

Write the selected target set to `/tmp/consolidation_keys.json` as
`[{ "old": "fully.qualified.doomed.key", "new": "common.target.key" }, ...]`.

#### Step C3 — Verify target keys exist in `common.json`

Read `messages/en/common.json` and confirm every `new` key already
exists. If any are missing, the consolidate pass needs to ADD them
first (with translations in every locale — this is itself a small
`language` mode pass). Most surgical sets won't need this — common
already has `labels.*` and `actions.*` populated.

#### Step C4 — Map callsites (AST-aware)

```bash
python3 ~/.claude/skills/cleanup/scripts/consolidate_cleanup.py map-callsites
```

Outputs `/tmp/consolidation_callsites_final.json` with:

- `callsites`: verified `(file, line, var, key_arg, old_key → new_key)` tuples
- `dead_keys`: keys with zero callsites (safe to delete with no code changes)
- `plan`: per-file strategy classification
  - **Strategy A** (file already has a `useTranslations('common')` binding): swap the variable name in each t-call. Trivial.
  - **Strategy B** (file does NOT have a `common` binding): add `const tc = useTranslations('common')` after the existing useTranslations line, then swap.

Surface the totals to the user: `N callsites across M files; K dead
keys; strategy A vs B split`. Show the per-file plan if M > 20 (helps
spot weird outliers — e.g. a file with 10+ callsites likely needs
inspection).

**Two-component-per-file gotcha:** if a file has multiple React
components and only one declares `useTranslations('common')`, Strategy
A's plan output may falsely flag the file as "has common" when only
HALF the components do. `tsc` will catch this with `Cannot find name
'tc'` — fix by adding `const tc = useTranslations('common')` to the
other component(s) manually.

#### Step C5 — Apply (two-phase)

```bash
python3 ~/.claude/skills/cleanup/scripts/consolidate_cleanup.py apply
```

Internally runs:

1. **Phase A — dead-key deletion** (zero-risk JSON-only): delete every
   key in `dead_keys` from every locale's JSON. No code touched.
2. **Phase B — callsite rewrites + live-key deletion**: for each
   file in `plan`, add the `tc` binding if needed, then replace
   `var('key_arg')` → `tc('new_suffix')` for each callsite. After all
   files written, delete the live keys from every locale's JSON.

The `replace()` is global per `old_call` string, so duplicate callsites
on the same line/file get rewritten together. The "could not find" skip
messages on the second occurrence of identical callsites are benign
(already replaced).

#### Step C6 — Verify

```bash
cd lex_council && npx turbo run check-types --filter=web
python3 ~/.claude/skills/cleanup/scripts/consolidate_cleanup.py verify
```

`tsc` failure usually means a missed `tc` binding (see C4 two-component
gotcha) — fix manually and re-run tsc.

The verify subcommand prints the new safe-to-merge group count + JSON
parse status. Expect the count to drop by the number of merged groups
(e.g. 10 surgical merges → drops by 10).

#### Step C7 — Vault log

Delegate to **vault-log-compliance**. The entry should document:

- The exact target set picked (and why each was chosen)
- The keys deleted with their callsite counts
- The strategy A/B split (how many files needed a new binding)
- Before/after safe-to-merge counts + total key counts per locale

If the consolidation pass extends a same-day `language` pass, link the
two vault logs as a sequence.

#### Step C8 — Memory update

If the surgical pass surfaced new keys that should become canonical
`common.*` targets (e.g. a frequently-duplicated label), add a memory
entry under `feedback_*` so the next `consolidate` pass auto-routes
to the right target.

### Mode: errors

Triage the runtime errors that pile up during normal browsing of the
local dev app, **without** Claude ever opening its own preview session
(that hijacks port 3000 — banned per Atta's standing rule). Atta keeps
his dev server running with stdout tee'd to `/tmp/lex-dev.log`; a
dev-only client-error sink endpoint catches browser-side errors and
appends them to the same file. The script
(`scripts/errors_cleanup.py`) parses both streams, dedupes, classifies,
and produces a triage list Claude can read on demand.

**Why this mode exists.** Without it, every dev-time error required
the user to copy-paste a stack trace before Claude could diagnose. The
sink + log + parser turn that into a one-command read. The mode also
codifies what counts as an *unambiguous* code-bug so auto-fix is
safe (E4 rubric).

#### Step E0 — Pre-flight

Confirm `/tmp/lex-dev.log` exists. If not, surface the tee command and
abort:

```sh
npx turbo dev 2>&1 | tee /tmp/lex-dev.log
```

Also confirm the runtime pieces are present (one-time setup, but check
in case a future refactor removed them):

- `apps/web/app/api/_dev/client-error/route.ts` — dev-only POST sink,
  returns 404 in prod, appends JSON lines to `/tmp/lex-dev.log`.
- `apps/web/components/_dev/DevErrorSink.tsx` — `'use client'`
  component that registers `window.error` + `unhandledrejection`
  listeners and `sendBeacon`s payloads to the route above.
- `apps/web/app/layout.tsx` — mounts `<DevErrorSink />` behind
  `process.env.NODE_ENV === 'development'`.

If any is missing, surface the gap. Don't auto-recreate — the user
might have removed it deliberately.

#### Step E1 — Detect

```sh
python3 ~/.claude/skills/cleanup/scripts/errors_cleanup.py detect [--since]
```

Default reads the entire log. `--since` reads from
`/tmp/last_errors_cleanup_offset` (set by `mark` in E6) so a second
invocation in the same dev session only sees new entries.

The parser handles:

- Server-side: Next.js error glyph (` ⨯ `), bare `TypeError:` /
  `ReferenceError:` / `SyntaxError:` / `RangeError:` / `PostgrestError:`
  / `AuthError:` / `FetchError:` / `AbortError:` headers, plus stack
  trace lines in either `at name (path:line:col)` or bare
  `at path:line:col` form.
- Client-side: one-line JSON blobs prefixed with
  `[CLIENT_ERROR <iso-ts>]` written by the sink endpoint.
- Route attribution: tracks the most-recent ` GET|POST|… /path NNN`
  line and stamps subsequent server errors with that route.

Dedupe key: `(error_type, first 200 chars of message, first repo-frame
path:line)`. Output: `/tmp/dev_errors.json`.

#### Step E2 — Classify

```sh
python3 ~/.claude/skills/cleanup/scripts/errors_cleanup.py classify
```

Each unique entry classified as one of:

| Class | Signal | Action |
|---|---|---|
| **code-bug** | Any stack frame matches `apps/web/` or `packages/md/` / `packages/auth/` / `packages/supabase/` | Surface as actionable |
| **framework-noise** | HMR / webpack-internal / Fast Refresh / `node_modules/next/` / `node_modules/react/` / Deprecation / `MISSING_MESSAGE` | Suppress in surface (show only count) unless count > 5 (repeated noise can mask real bugs) |
| **external** | `fetch failed` / `ECONNREFUSED` / `ENOTFOUND` / `ETIMEDOUT` / `network` / `supabase` keywords, no repo frame | Surface as informational — Atta usually knows the cause |
| **unknown** | Nothing matched | Surface; user reclassifies |

Output: `/tmp/dev_errors_classified.json` + a printed summary table.

#### Step E3 — Surface the triage list

Show the user:

- All `code-bug` entries with file:line + message + routes-seen-on + count.
- All `external` entries grouped by host (one line per host).
- `framework-noise`: only the total count, unless a specific noise
  signature exceeds 5 occurrences (then list it).
- `unknown`: full list with the raw first line.

Format per entry:

```
[TypeError] Cannot read properties of undefined (reading 'nickname')
  apps/web/components/portal/PortalUserCard.tsx:42
  routes: /en/admin/files, /en/members
  count: 3
```

#### Step E4 — Auto-fix unambiguous code-bugs

**Auto-fix rubric (strict).** Apply a fix only if ALL of these hold:

1. The stack pinpoints a specific file:line under `apps/web/` or
   `packages/`.
2. The error matches exactly one of the named patterns below.
3. The fix is a single-line change.
4. The file has no uncommitted edits unrelated to this session.
5. Fewer than 4 auto-fixes are proposed in this batch (≥4 is a
   smell of broader breakage — surface, don't auto-fix).

Named patterns:

| Error pattern | Fix |
|---|---|
| `TypeError: Cannot read properties of (undefined|null) (reading 'X')` AND access site is `foo.X` in a read position (not LHS, not function-call where `?.()` would change semantics) | Replace `foo.X` → `foo?.X` |
| `ReferenceError: X is not defined` AND `X` is exported from exactly one module under `apps/web/` or `packages/` AND not already imported in the file | Add `import { X } from '<resolved-path>'` at the top |
| `ReferenceError: X is not defined` AND `X` is exactly one Levenshtein edit from one in-scope identifier AND that identifier is the only viable candidate | Replace `X` with the in-scope name at the pinpointed line |

Anything else: surface with the proposed fix and ask. When in doubt,
ask. Auto-fix mistakes are cheaper to avoid than to roll back.

After applying a fix, run `tsc` (E5) before the next fix in the
batch — if a fix breaks types, abort the batch and surface the
remaining errors for human triage.

#### Step E5 — Verify

```sh
cd lex_council && npx turbo run check-types --filter=web
```

Then ask the user to re-navigate the routes that produced the
fixed errors. After the re-browse:

```sh
python3 ~/.claude/skills/cleanup/scripts/errors_cleanup.py detect --since
```

If any of the original error signatures recurs, the auto-fix didn't
actually address the root cause — surface it for a second pass.

#### Step E6 — Mark

```sh
python3 ~/.claude/skills/cleanup/scripts/errors_cleanup.py mark
```

Records the current log EOF in `/tmp/last_errors_cleanup_offset` so
the next `detect --since` only reads new entries.

#### Step E7 — Vault log

Delegate to **vault-log-compliance** *only if code changed*. For
triage-only runs (no auto-fix applied, user did not request a manual
fix), no vault log needed — the log itself is the audit trail.

The entry should document:

- Each fixed error: signature + file:line + which patterned fix
  applied (A/B/C from E4).
- Routes that triggered each error.
- The verify result (E5).
- Any errors surfaced but not auto-fixed (deferred-to-user list).

### Mode: postgres

Check Supabase advisor output + pg health queries; auto-fix additive issues; flag schema-level
issues for a dedicated campaign. Script: `scripts/postgres_cleanup.py`.

**Why advisory-only auto-fix.** Only additive, non-destructive SQL is auto-applied (e.g.
`CREATE INDEX IF NOT EXISTS`). Anything requiring a destructive DDL change, an RLS rewrite,
or a trigger/function update is surfaced as a `schema-campaign` item — the user opens a
conquering-campaign session to handle it safely with the PDAAV pattern.

**MCP pre-flight contract.** This mode calls Supabase MCP tools before running the script.
Claude writes the raw JSON outputs to temp files; the script classifies and acts on them.
Always use `project_id bqgrpnsvplvicnmzxwkm` for every MCP call.

#### Step PG0 — Pre-flight

Confirm the Supabase MCP is reachable:

```bash
# Verify project is accessible
# (Claude calls get_project MCP with project_id=bqgrpnsvplvicnmzxwkm)
```

If MCP is unavailable, surface the error and abort — postgres mode cannot run without
Supabase MCP access.

#### Step PG1 — Detect

Run the two MCP calls and write their output:

```bash
# 1. Supabase security + performance advisors
# Claude: get_advisors(project_id='bqgrpnsvplvicnmzxwkm') → write to /tmp/pg_advisors.json

# 2. pg health queries (missing FK indexes, tables without RLS, high dead-tuple tables)
# Claude: execute_sql(project_id='bqgrpnsvplvicnmzxwkm', query=HEALTH_SQL) → write to /tmp/pg_health.json
```

Standard health SQL to run (matches what the health-checker skill uses):

```sql
-- Missing FK indexes
SELECT
    tc.table_schema, tc.table_name, kcu.column_name,
    ccu.table_name AS references_table
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
    AND tc.table_schema = kcu.table_schema
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
AND tc.table_schema = 'public'
AND NOT EXISTS (
    SELECT 1 FROM pg_indexes
    WHERE schemaname = tc.table_schema
    AND tablename = tc.table_name
    AND indexdef ILIKE '%' || kcu.column_name || '%'
);

-- Tables without RLS
SELECT schemaname, tablename
FROM pg_tables
WHERE schemaname = 'public'
AND NOT rowsecurity;

-- High dead-tuple tables (> 10 000 dead rows)
SELECT relname, n_dead_tup, n_live_tup,
    round(100.0 * n_dead_tup / NULLIF(n_live_tup + n_dead_tup, 0), 1) AS dead_pct
FROM pg_stat_user_tables
WHERE n_dead_tup > 10000
ORDER BY n_dead_tup DESC;
```

Then run the script's detect phase:

```bash
python3 ~/.claude/skills/cleanup/scripts/postgres_cleanup.py detect
```

Show the user the total issue count per source (advisors vs health queries) and ask whether to proceed.

#### Step PG2 — Classify

```bash
python3 ~/.claude/skills/cleanup/scripts/postgres_cleanup.py classify
```

Tier mapping:

| Tier | Signal | Action |
|---|---|---|
| **advisory-auto-fix** | Missing FK index, no-primary-key on empty table | Generate `CREATE INDEX IF NOT EXISTS` SQL |
| **advisory-surface** | Dead tuples, cache hit ratio, index bloat | Surface as informational — Atta decides if VACUUM/REINDEX needed |
| **schema-campaign** | RLS disabled on a table, SECURITY DEFINER view, unused index candidate for DROP, any policy rewrite | Flag as needing a conquering-campaign session |
| **noise** | Long-running queries (ephemeral), replication lag (not applicable for single-project) | Suppress |

Print the classification summary. Confirm auto-fix count before proceeding.

#### Step PG3 — Apply (advisory-auto-fix only)

```bash
python3 ~/.claude/skills/cleanup/scripts/postgres_cleanup.py apply
```

The script generates `/tmp/pg_apply.sql`. Review the SQL, then apply:

```
# Claude: apply_migration(project_id='bqgrpnsvplvicnmzxwkm', query=<contents of /tmp/pg_apply.sql>)
```

**Hard constraint:** Only `CREATE INDEX IF NOT EXISTS` is auto-applied. Any other DDL found in the
auto-fix tier (unexpected by the script) is escalated to `schema-campaign` instead. Never apply
`DROP`, `ALTER TABLE`, or `CREATE OR REPLACE FUNCTION` via auto-fix.

**Migration filename safety.** The project uses 14-digit timestamp format for migration names
(`YYYYMMDDHHMMSS`). Confirm the format matches before calling `apply_migration`. A mismatch
causes `MIGRATIONS_FAILED` on preview branches, leaving the DB empty and unresponsive.

#### Step PG4 — Verify

Re-run health queries and advisors; report delta:

```bash
# Claude: get_advisors + execute_sql again → overwrite /tmp/pg_advisors.json + /tmp/pg_health.json
python3 ~/.claude/skills/cleanup/scripts/postgres_cleanup.py verify
```

Expected: advisory-auto-fix count drops to 0. If any remain, surface them as needing manual review.

#### Step PG5 — Surface schema-campaign items

```bash
python3 ~/.claude/skills/cleanup/scripts/postgres_cleanup.py surface
```

Print the full triage list. For each `schema-campaign` item, suggest the conquering-campaign
trigger phrase the user would use (e.g., "add RLS to the `notifications` table").

#### Step PG6 — Vault log

Delegate to **vault-log-compliance** *only if a migration was applied*. For triage-only runs,
no vault log needed.

The entry should document: each auto-fixed index (table + column + `CREATE INDEX` SQL), advisor
delta (before → after count), and the schema-campaign checklist for the user.

**Key traps for postgres mode:**

- **`CREATE OR REPLACE VIEW` silently drops `security_invoker=true`** — if any view is touched
  during this pass (even incidentally), follow up with `ALTER VIEW <v> SET (security_invoker = true)`.
- **Intentional advisor warnings** — some advisories are expected (e.g. a public SECURITY DEFINER
  RPC is intentional per the v2 conventions). Document intentional exceptions in the vault log
  with a `// BR-NNN:` style comment so future postgres passes don't re-flag them.
- **`GROUP BY` + aggregate in views** — makes the view non-streamable to PostgREST (silently
  ignores `Range` headers on paginated queries). Classify as `advisory-surface`.
- **New trigger/RPC advisor warnings** — new trigger functions and RPCs almost always generate
  `search_path` + anon-EXECUTE advisor warnings. Fix inline when writing the object; don't
  defer to a cleanup pass.

---

### Mode: lint

Run ESLint + TypeScript health sweep; auto-fix safe rules; surface architectural violations
as campaign candidates. Script: `scripts/lint_cleanup.py`.

**Scoped vs full-project lint.** The project enforces `--max-warnings 0`. A full project-wide
lint run often surfaces pre-existing warnings in files the current campaign never touched. This
mode supports BOTH: (a) full-project sweep (to build a debt baseline), and (b) scoped sweep
(to prove a campaign's changes are clean). See Step L3 for scoping options.

**No preview server required.** This mode does not need Claude to open a browser session.
All verification is tsc + ESLint only.

#### Step L0 — Pre-flight

```bash
# Confirm we're in lex_council/
ls lex_council/package.json   # must exist
# Check that npm run lint exists
grep '"lint"' lex_council/package.json
```

If not in the right directory or lint script missing, surface and abort.

#### Step L1 — Detect

```bash
python3 ~/.claude/skills/cleanup/scripts/lint_cleanup.py detect
```

The script runs `npx eslint --format json --ext .ts,.tsx apps/web packages` from `lex_council/`,
parses the JSON output, dedupes by `(file, rule)`, and writes `/tmp/lint_issues.json`.

Show the user: total unique issues (N errors, M warnings), top 5 rules by occurrence.
Ask whether to proceed with classification.

**Turbo cache trap.** Stale Turbo cache causes lint to report errors in unmodified files. If
unexpected errors appear in files clearly not related to recent work, run:

```bash
cd lex_council && npx turbo run check-types --force --filter=web
```

before investigating — the force flag bypasses stale cache.

#### Step L2 — Classify

```bash
python3 ~/.claude/skills/cleanup/scripts/lint_cleanup.py classify
```

Tier mapping:

| Tier | Signal | Action |
|---|---|---|
| **auto-fixable** | ESLint `fixable: true` in JSON output, or rule in safe-fixable list (prefer-const, no-var, import/order, etc.) | Run `eslint --fix`, then tsc |
| **architectural** | `react-hooks/exhaustive-deps`, `react-hooks/rules-of-hooks`, `import/no-cycle`, `no-unused-expressions`, `no-restricted-imports`, syntax/parse errors | Surface as campaign candidate |
| **wip-noise** | `no-unused-vars` / `@typescript-eslint/no-unused-vars` in files not touched this session | Suppress — tsc handles this better |
| **unknown** | No match | Surface with raw error text |

**`no-unused-expressions` is always architectural.** The most common trigger is a ternary used
as a statement (`cond ? a.foo() : a.bar()`), which fails `no-unused-expressions`. The fix is
always `if/else` — never `eslint-disable`. Auto-fix is blocked for this rule.

#### Step L3 — Scoping (optional)

For proving a campaign's changes are clean independent of pre-existing project-wide warnings:

```bash
# Get files touched in the current campaign/session
git status --short | awk '$1 ~ /^M/ || $1 == "M" {print $2}' > /tmp/touched.txt

# Run eslint scoped to those files only
cd apps/web
npx eslint --max-warnings 0 $(cat /tmp/touched.txt | grep "^apps/web/" | sed 's|^apps/web/||')
echo "EXIT=$?"
```

`EXIT=0` proves the campaign-touched surface is clean. Report both the full-project result
(with provenance note for pre-existing failures) AND the scoped result.

#### Step L4 — Apply

```bash
python3 ~/.claude/skills/cleanup/scripts/lint_cleanup.py apply
```

The script runs `eslint --fix` on files with auto-fixable issues, then runs tsc to verify.
If tsc fails after --fix, surface the failures — do NOT mark the phase complete until tsc passes.

**Safe-fixable rules**: prefer-const, no-var, import/order, import/no-duplicates,
@typescript-eslint/no-extra-semi, react/jsx-boolean-value, react/self-closing-comp, eol-last,
no-trailing-spaces. Full list in `scripts/lint_cleanup.py:SAFE_FIXABLE_RULES`.

**Auto-fix batch limit**: apply at most 50 files per run. Larger batches risk a single
unfixable file blocking the whole batch. Run verify between batches if > 50 files.

#### Step L5 — Verify

```bash
python3 ~/.claude/skills/cleanup/scripts/lint_cleanup.py verify
```

Re-runs full ESLint, reports delta vs the pre-fix baseline. Then:

```bash
cd lex_council && npx turbo run check-types --force --filter=web
```

Expected: auto-fixable count drops to 0. tsc passes. Architectural count unchanged
(those require campaigns, not auto-fix).

#### Step L6 — Surface architectural violations

```bash
python3 ~/.claude/skills/cleanup/scripts/lint_cleanup.py surface
```

Print the triage list. For each architectural violation cluster (same rule across N files),
suggest the conquering-campaign trigger (e.g., "sweep no-unused-expressions ternary violations
across 12 files").

**Off-token hex grep bonus scan.** ESLint does not catch raw hex color literals in CSSProperties.
Run after the standard lint sweep:

```bash
grep -rn '#[0-9a-fA-F]\{3,6\}' \
  lex_council/apps/web/components \
  lex_council/apps/web/app \
  --include="*.tsx" --include="*.ts" | grep -v "//.*#" | wc -l
```

A count > 10 is a flag for a token-sweep campaign. Surface to the user as an advisory.

#### Step L7 — Vault log

Delegate to **vault-log-compliance** *only if code changed* (auto-fix was applied). For
triage-only runs, no vault log needed.

The entry should document: files fixed, rules resolved, tsc result, architectural violations
surfaced as campaign candidates, and the off-token hex count if > 0.

**Key traps for lint mode:**

- **Pre-existing parse errors block the whole app typecheck.** A single unterminated string
  literal stops tsc from analyzing any other file. Run `tsc --noEmit` first to confirm the
  baseline is clean before attributing new errors to the current session's changes.
- **`'use client'` + `generateMetadata` in same file** is a hard Next.js build error (not a
  lint or tsc error — only surfaces at `next build`). Classify as `architectural`.
- **Module-level `const` style objects** have dead-code that ESLint's `no-unused-vars` does not
  catch because the object itself is exported. This requires a manual `grep` for usage or a
  `knip`/`ts-prune` run — out of scope for auto-fix, surface as advisory.
- **`useTranslations` cleanup** requires removing BOTH the import AND the `const t = ...` line.
  ESLint `--fix` removes unused-import but leaves the `const` declaration, causing a follow-up
  `no-unused-vars` error on the next run. Fix both in one pass.

---

### Mode: consolidate-code (LIVE)

> **Script:** `python3 ~/.claude/skills/cleanup/scripts/consolidate_code.py <scan|classify|surface|extract>` — `extract` is dry-run by default and refuses to auto-merge (byte-compare + a conquering-campaign required for any real consolidation, per §L4).

The code-side sibling of `consolidate` (which is i18n-only). Surfaces — then extracts the
mechanical tier of — duplicate/copy-pasted CODE. The registry `CONSOLIDATION-CANDIDATES.md`
ships pre-seeded with 41 open candidates mined from 146 sessions (2026-05-29); this mode
refreshes it and acts on the safe tier.

**Why a separate mode from `consolidate`.** `consolidate` touches i18n JSON + TSX callsites
via AST resolution. `consolidate-code` touches arbitrary code shapes (components, DB views,
RLS predicates, constants) with different detection + different risk. Conflating them would
overload one script.

#### Step CC1 — Refresh the registry

Re-run the detection greps for each candidate class against the live codebase. The
highest-signal verified-live detections:

```bash
cd lex_council
# Magic-literal duplication (canonical const exists, local copies proliferate)
grep -rln "const PANEL_WIDTH = 332" apps/web --include="*.tsx" --include="*.ts" | wc -l   # C1: was 44
# Config defined in N places
grep -rn "PAGE_SIZE_OPTIONS\s*=" apps/web --include="*.tsx" --include="*.ts"               # C2: 2 files
# Copy-pasted function bodies — SHA-1 the body, flag N>=2 identical
# (the 1d944474 session built a mutation duplicate-detector that escalated
#  name-equality -> SHA-1 body-hash and caught 2 missed exports)
# Off-token hex (pairs with lint mode L13)
grep -rn '#[0-9a-fA-F]\{3,6\}' apps/web/components apps/web/app --include="*.tsx" | grep -c "Token gap"
```

For DB-side candidates, the canonical source is the persisted
`docs/audit-campaigns/2026-05-22_db-wide-consolidation-audit/99-synthesis.md` (74 findings) —
read it; don't re-derive.

#### Step CC2 — Classify each candidate (3 tiers)

| Tier | Criteria | Action |
|---|---|---|
| **T1 extract-now** | Mechanical, ≤ codemod or a few files, zero behavior-parity risk (magic-literal dedup, orphan `git rm`, identical-helper extraction) | Do under autonomous cadence |
| **T2 needs-campaign** | Cross-cutting, >15 sites, OR behavior-parity risk (DB view merge, RLS predicate extraction, button-role standardization) | Surface; open a conquering-campaign |
| **T3 resolved** | Already consolidated | Record so re-mining doesn't re-flag |

#### Step CC3 — Byte-compare before any merge (HARD RULE)

§L2 + §L4 (look-alike-but-different). Before merging N near-duplicate literals/views/predicates
into one helper, **byte-compare them**. If any pair differs, either keep them separate or make
the helper's API preserve every difference (per-arm CASE, parameter, etc.). The RLS-bucket-matrix
trap (4 arrays looked identical, encoded distinct access tiers) is why this is non-negotiable.

The i18n `consolidate` mode already encodes this (only merge when translation matches in every
locale). `consolidate-code` must encode it for code: only merge when all N are byte-identical
OR the difference is captured in the merged API.

#### Step CC4 — Extract T1, surface T2

For T1: extract the shared primitive/const FIRST, then replace each consumer (per the
conquering-campaign extraction-first phase ordering). Run tsc + lint after each extraction.

For T2: write/refresh the registry entry, recommend the conquering-campaign trigger phrase.

#### Step CC5 — Vault log

Delegate to **vault-log-compliance** if code changed. The entry documents: which T1 candidates
were extracted (before/after consumer counts), which T2 were surfaced, registry delta.

**Priority order (from the seeded registry):** C35 ghost-views (CRITICAL, fix now not campaign)
→ C1 PANEL_WIDTH ×44 (codemod) → C38 294 i18n dup groups → C28/C29 legacy `_js` views →
C7/C8/C11 V9-container primitives → C23–C27 DB view/RLS merge → C30 admin_perms god-table (XL).

---

### Mode: release (LIVE)

The unified app-upgrade flow (merged the retired `update-app-version` skill in cleanup v1.6.0).
Two phases: **Phase 1 — hygiene gate** (PR1–PR4 below) runs the cheap LIVE-mode checks + release
hazard probes and returns a green/red verdict; **Phase 2 — version bump** runs only if the gate
is green and performs the full bump per `references/release-procedure.md`. Invoke gate-only with
`/cleanup release --gate` (stops after PR4); the bare `release` invocation runs both phases.

**Why this exists.** Release-time breakage is a recurring class (Cloudflare bundle wall, Next.js
16 hazards, uncommitted migrations, stale doc stamps). The sessions show ~6 distinct release
failures that a pre-push gate would have caught.

#### Step PR1 — Run the hygiene gate

In order, collect each mode's verdict (do not auto-fix — this is a gate, not a sweep):

1. `lint` mode detect+classify — **red if** any architectural violation on touched files
2. `errors` mode detect+classify — **red if** any unfixed code-bug in the dev log
3. `postgres` mode detect+classify — **red if** any NEW schema-campaign item vs last release

#### Step PR2 — Release-specific hazard checks

| Hazard | Probe | Verified-recurring |
|---|---|---|
| **Cloudflare/OpenNext bundle wall** | `du -sh .open-next/` or a gzip check; free-tier 3 MiB, paid 10 MiB | SSR worker hit 15.4 MiB raw / 3.2 MiB gzip — fixed via webpack alias + dynamic `recharts`. `serverExternalPackages` NOT honored by OpenNext. |
| **`generateMetadata` in `'use client'` page** | `grep -rln "'use client'" + "generateMetadata"` same file | Hard Next.js 16 build error; keep `page.tsx` a Server Component. |
| **Uncommitted migration / route changes** | `git status` — uncommitted `[locale]` or `i18n/` or migration dirs | Whole `[locale]` migration was uncommitted → prod-only 404. |
| **Import-depth off-by-one after route move** | `tsc` TS2307 count | `[locale]` segment moved every admin file one dir level → 718 TS2307. |
| **Migration filename format** | migration names must be 14-digit `YYYYMMDDHHMMSS` | 14-digit mismatch → Supabase branch stuck MIGRATIONS_FAILED. |
| **Next.js 16 `middleware`→`proxy` deprecation** | dev-server output grep | Forward-looking; not yet blocking. |

#### Step PR3 — Doc-stamp staleness warning

`VERSION-RELEASE-WORKFLOW.md` §4 was **reconciled 2026-05-29** — its target list now matches the
live tree (and `references/release-procedure.md` carries the same list). Current version-stamp
surfaces (still worth a verify grep before trusting any list):

```bash
cd lex_council
# Find what actually carries an app-version stamp NOW
grep -rln "App version:\|app_version:\|APP_CONFIG\|Version {version}" docs/ apps/web/config/ \
  --include="*.md" --include="*.ts" --include="*.json" 2>/dev/null
```

Also: app version lives in TWO places that drift — `apps/web/config/app.config.ts`
(`APP_CONFIG.version`, the canonical) AND the web `package.json` `version` field. The prod live
stamp is the reliable deploy-lag signal.

**Side-finding to action:** reconcile `VERSION-RELEASE-WORKFLOW.md`'s target list with the current
solar-system hubs (Vault Core + the changelog INDEX files). Until then, the workflow's hard-coded
list silently skips the real stamps.

#### Step PR4 — Gate verdict

Emit a green/red gate result. **Green →** proceed to Phase 2 (the bump) unless the user passed
`--gate`. **Red →** surface the blocking items and STOP; do not bump.

No vault log for a gate-only run (no code changed). If the gate auto-fixed anything (it
shouldn't — it's a gate), delegate to vault-log-compliance.

#### Phase 2 — Version bump (only if gate green and `--gate` not passed)

Run the full bump procedure in **`references/release-procedure.md`** (R-1 … R-6): confirm scope +
classify the bump, compose the changelog, bump `apps/web/config/app.config.ts` (the canonical
literal) + decide the `package.json` mirror, write `docs/logs/X.Y.Z.md`, sync the doc stamps
(`logs/INDEX.md` + `ARCHITECTURE.md` + Vault Core ×3 — NOT the archived ZUSTAND-STORES), verify
with a version grep, and output the single git block (do NOT push unless told). This phase
absorbed the retired standalone `update-app-version` skill.

---

## Brand glossary

These terms stay in Latin script across every locale. Every agent prompt
must enumerate them. Source of truth lives in
`scripts/i18n_cleanup.py:BRAND_OR_CODE` — keep them in sync when adding
new terms.

```
Lex Council, LexCouncil, Lex
POA, NDA, OTP
GFN, MFN, BFN, SFN, AFN, FN
HR, CSV, PDF, URL, UI, API, JSON, SQL, RLS, RPC
TSL, WHBD, KPI, UUID, ID, IDs
CIS, P&L, TM, PM, GCal, BC
```

Plus: any single-char string, any pure-digit string, any all-caps
1–4-letter token, any string of pure punctuation.

## Locale contracts

These are the register/style constraints each translation agent must
follow. Encoded as the locale-specific override in §Agent prompt
templates.

| Locale | Register | Notes |
|---|---|---|
| **ar** | Modern Standard Arabic (فصحى) | NOT Egyptian colloquial, NOT Levantine. Formal pan-Arabic legal/business. |
| **es** | Neutral professional Spanish | Latin American–biased but acceptable to Spain. Use proper accents (á é í ó ú ñ ¿ ¡). Formal "usted" form. Cognates kept where natural ("Total"); accents added where required ("Vídeo"). |
| **fr** | Standard European French | Formal legal/business register. Use "vous" form. Proper accents (é è ê ç à ù ô). Cognates kept identical where natural ("Finances", "Documents", "Notifications", "Transactions"); accents added where missing ("Détails"). |
| **ru** | Standard professional Russian | Formal "вы". Russian grammatical case may reorder placeholders — that's required, not a violation. |
| **zh** | Simplified Chinese (简体中文) | Mainland register, NOT Traditional. Use full-width sentence punctuation (，。：；！？) but half-width for placeholders and brand. Arabic numerals (1, 2, 3), not 一二三. |

## Agent prompt templates

Use these verbatim when spawning the 5 subagents (subagent_type:
`general-purpose`, `run_in_background: true`). Each prompt is a
self-contained brief — the agent has no memory of this conversation, so
context like "what is Lex Council" must be in the prompt itself.

### Per-locale prompt skeleton

```text
You are a professional translator for a legal practice management SaaS
called Lex Council. The app manages legal matters (cases, tasks, documents,
files), members (attorneys/staff), and clients. Tone: formal, professional,
B2B SaaS, suitable for lawyers and administrators.

Your task: translate {COUNT} English strings into {LOCALE_NAME} —
{REGISTER_GUIDANCE}.

Input file: /tmp/translation_targets_{LOCALE}.json — a JSON array of
{ns, key, en} objects.
Output file: /tmp/translations_{LOCALE}.json — write a JSON array of
{ns, key, translated} objects, one per input entry, **same order**, **same
count ({COUNT})**.

Hard rules — non-negotiable:

1. Preserve every {placeholder} exactly. Do not translate variable names.
2. Brand/acronym glossary — keep in Latin script:
   Lex Council, POA, NDA, OTP, HR, CSV, PDF, URL, UI, API, JSON, SQL, RLS,
   RPC, KPI, UUID, ID, CIS, P&L, TM, PM, GFN, MFN, BFN, SFN, AFN, FN, WHBD,
   GCal, BC.
3. {COGNATE_NOTE}
4. Numbers, dates, percentages stay as-is unless embedded in a translated
   phrase.
5. Output count must equal input count ({COUNT}).
6. Output is pure JSON — no markdown fences, no commentary. Write directly
   to /tmp/translations_{LOCALE}.json.

{TONE_EXAMPLES}

Process:
1. Read /tmp/translation_targets_{LOCALE}.json in full.
2. Translate each entry. Use the `ns` field as context for register.
3. Write the result as a single JSON array.
4. Reply: "Wrote N translations to /tmp/translations_{LOCALE}.json".
```

### Per-locale fills

| Locale | LOCALE_NAME / REGISTER_GUIDANCE | COGNATE_NOTE | TONE_EXAMPLES |
|---|---|---|---|
| **ar** | Modern Standard Arabic (MSA / فصحى) — NOT Egyptian colloquial, NOT Levantine — neutral pan-Arabic legal/business register | Not applicable (different script). | "Loading…" → "جارٍ التحميل…", "Approved {noun}{suffix}" → "تم اعتماد {noun}{suffix}", "Pending" → "قيد الانتظار" |
| **es** | neutral professional Spanish — Latin American–biased but acceptable to Spain, formal "usted" register, include proper accents | Cognates are OK to keep identical to English IF that's the natural Spanish form — "Total" stays "Total", "Video" → "Vídeo" (add accent), "Documents" → "Documentos". When in doubt, prefer proper Spanish form. | "Loading…" → "Cargando…", "Force Close" → "Cierre forzado" |
| **fr** | standard European French — formal legal/business register, "vous" form, proper accents | Cognates OK identical to English where natural — FR "Finances", "Documents", "Notifications", "Transactions", "Performance", "Permissions" are the correct French; but "Details" → "Détails" (add accent), "Created" → "Créé". When EN form is identical to natural French, return it unchanged. | "Loading…" → "Chargement…", "Castle" (chess metaphor) → "Roque", "Force Close" → "Fermeture forcée" |
| **ru** | standard professional Russian — formal "вы" form | Not applicable. Russian grammatical case may reorder placeholders — that's required. | "Loading…" → "Загрузка…", "Castle" → "Рокировка", "Force Close" → "Принудительное закрытие" |
| **zh** | Simplified Chinese (简体中文) — Mainland register, NOT Traditional, full-width sentence punctuation, half-width for placeholders/brand | Not applicable. Use Arabic numerals (1, 2, 3) not 一二三. | "Loading…" → "加载中…", "Castle" → "易位", "Kanban" → "看板", "Force Close" → "强制关闭" |

## Decision points to surface to the user

Always pause for explicit confirmation at these gates:

1. **After detect** — show counts, ask "proceed with {N} translations across {M} locales?"
2. **After pre-flight in apply** — if any locale fails, show what failed
   and ask whether to skip or force.
3. **Before vault log** — the vault-log-compliance skill always shows
   its draft and asks; let that gate inherit normally.

Do NOT pause between agent completions — they run in parallel and you'll
be notified as each finishes.

## Memory + drift

When this skill discovers something the project should remember
(new brand terms, locale-specific gotchas, a namespace that should be
exempt), update auto-memory in
`/Users/atta/.claude/projects/-Users-atta-Documents-Claude-Projects-Lex-Council-App/memory/`
per the auto-memory rules. Also append the new brand term to
`scripts/i18n_cleanup.py:BRAND_OR_CODE` so the next pass picks it up
automatically.

## Lessons learned (cross-mode architecture)

> **Wired into scripts (v1.8.0):** L9/L10/L15/L17 → `postgres_cleanup.py` detect (emits + classifies the security_invoker / stale-prosrc / permissive-RLS / dead-service_role / rls-no-policy queries); L11 + L19 → `lint_cleanup.py` (baseline-delta + view-registry cross-check); L14 → `errors_cleanup.py` noise list; L16 → `i18n_cleanup.py` detect (window.confirm scan). The rest remain cross-mode prose guidance.

Patterns extracted from the 2026-05-28 solar-system doc-sync audit +
follow-up sweep. These apply across **every** cleanup mode, not just one.

### L1 — MCP-out-of-reach taxonomy

When a cleanup mode generates an action list, classify each item by
reachability **before** trying to execute:

| Class | Signal | Action |
|---|---|---|
| **doable from MCP** | Has a matching MCP tool (`apply_migration`, `execute_sql`, `deploy_edge_function`, etc.) AND falls within the autonomous-cadence remit | Do now |
| **doable from Bash/local-fs** | Local file edit, git operation, npm script — within the workspace tree | Do now |
| **needs-user-hands** | Supabase dashboard click (no `delete_edge_function` MCP), external service (cron on office NAS, third-party API), `[!atta]` block edit, signed-out user account, OS-level config | Surface as checklist |
| **accepted-permanent-exception** | Item the user has explicitly marked "leave as-is" in a prior turn; cite the prior decision verbatim | Note in findings; don't re-surface |

The 2026-05-28 solar-system audit had 8 follow-ups split 5/2/1 across
these classes. Codifying the taxonomy prevents the skill from silently
dropping needs-hands items (they become checklist-with-receipts) and
prevents accepted exceptions from re-appearing on every future cleanup.

### L2 — Behavior-parity verification post-refactor

When cleanup mode merges, consolidates, or replaces a structure (RLS
policies, hard-coded arrays, repeated CSS literals, i18n key
deduplication), the verify gate is **not** "does it compile / does
type-check pass" — it's **"does the post-state admit/produce the
exact same outputs as the pre-state for every input?"**

The FU-5 storage RLS refactor produced a 17-admit parity matrix
across 12 buckets × 5 ops:

```sql
with buckets(b) as (values (...)), ops(op) as (values (...))
select b, op, helper(b, op) as admitted from buckets, ops
where helper(b, op)  -- only show admits
order by b, op;
```

The matrix returned 17 admits — exactly matching the pre-refactor admit
set. **If parity check returns a delta, the refactor is wrong even if
type-check passes.** The look-alike-but-different trap (L4 below) is
the primary reason this check is non-negotiable for any consolidation.

### L3 — Post-rename narrative-artifact sweep

When a large rename campaign ships (v2 schema, primitive family
rename, naming overhaul), narrative documentation often retains
pre-rename names in prose **and** acquires telltale artifacts from
botched global-replaces. Two pattern classes worth a periodic grep:

**Pattern A — retained pre-rename names** (treat as documentation
drift; surface for triage, never auto-fix):

```bash
grep -rnE '\b(fd|council_members|ppl|whbd_|atnd_|n_kinds|KpiStrip|PageHeaderStrip|AdminPageShell)\b' \
  lex_council/docs/ --include="*.md"
```

**Pattern B — global-replace artifacts** (almost always a bug; the
2026-05-28 BACKEND.md audit found 3 of these):

```bash
# "X (v2; was X)" — same name on both sides of a "was" parenthetical
grep -rnoE '`([a-z_]+)` \(v2; was `\1`\)' lex_council/docs/ --include="*.md"
grep -rnoE '`([a-z_]+)` \(was `\1`\)' lex_council/docs/ --include="*.md"
```

The `docs` mode codifies this as Step D7.

### L4 — Look-alike-but-different trap

The FU-5 RLS refactor revealed that 4 storage policies LOOKED like
they hard-coded the same bucket array but actually encoded distinct
per-CMD access tiers (`200` was SELECT-only; `attendance` + `elections`
were SELECT+INSERT only; `documents`/`1`/`2` were full-CRUD). A naive
"replace all 4 with a single `is_private_bucket()` helper" would have
silently widened access on 3 buckets.

**Rule for any consolidation cleanup:** before merging N near-duplicate
literals into one helper, compare them byte-for-byte. If any pair
differs, preserve the difference in the helper's API (e.g. per-CMD CASE
arms; per-locale dispatch; etc.). Only consolidate when all N are
byte-identical.

The `language` mode's safe-to-merge detector already encodes this for
i18n (only merge when translation matches in every locale). The
`consolidate` mode (when wired up) MUST encode it for code as well.

### L5 — PostToolUse hook race conditions with Edit

The Edit tool's "file has been modified since read" guard fires when a
PostToolUse hook (linter, formatter, IDE) touches the target between
Read and Edit. The 2026-05-28 audit hit this 5+ times on INTEGRATION.md
+ vault-logs INDEX.md edits.

**Rule for any mode performing batch edits to many files:** use
`Bash` + Python (or sed) for the substitution sweep, NOT chained
`Edit` calls. The `language` mode already does this via
`scripts/i18n_cleanup.py:apply`. The `docs` mode's Step D2 frontmatter
sync should follow suit when it goes live.

For single-target edits (e.g. one-line frontmatter bump), `Edit` is
fine — race conditions are rare enough that the failure-then-retry
pattern is cheap.

### L6 — Same-session continuation markers

Atta uses brief continuation markers between turns to indicate
"keep going" without re-issuing the original directive:

- `/goal` — generic "continue toward the goal we agreed on"
- "finish the rest" / "finish [X]" — execute remaining items
- "i am done" / "i am done..." — user-side action complete; resume
  on the agent side
- "leave [X] as exception" — accept-and-skip, mark as L1 permanent-exception

When a cleanup mode is interrupted by a needs-user-hands item, the
**next-turn pickup** should preserve all in-progress state (which items
were classified as doable / needs-hands / exception). Don't re-classify
from scratch on continuation — the prior turn's findings file is the
input.

### L7 — Vault-log size threshold

For ≤3 follow-up items touching the same surface, write a single inline
vault-log entry (the `2026-05-28_solar-system-doc-sync-followups.md`
shape). For ≥4 items OR multi-surface changes, delegate to
**vault-log-compliance** for a fuller entry with P13 self-audit table.

The `language` mode always delegates because translation passes are
multi-locale by definition (5 surfaces). The `docs` + `followups`
modes pick per-pass based on scope.

### L8 — Long-running global replaces leave artifacts; periodic grep

L3 above is a specific instance of a broader pattern: any mass-edit
campaign (rename sweep, token consolidation, primitive retirement)
leaves stray artifacts that don't surface for weeks because they're
syntactically valid. The `docs` mode's Step D7 + Step D6 grep these
proactively; without periodic cleanup, the artifacts accumulate and
the next person reading the doc gets a false mental model.

When a future BUILD ships a rename, the FOLLOWING `/cleanup docs` run
should be scheduled within a week.

### L9 — `CREATE OR REPLACE VIEW` silently drops `security_invoker = true` (postgres mode)

Confirmed across 5+ independent sessions: every `CREATE OR REPLACE VIEW` statement silently
drops the `reloptions` including `security_invoker = true`, reverting the view to definer
mode. This is a silent regression — tsc and lint pass cleanly, RLS still "works" (definer
mode bypasses RLS, so the query returns data), but the security contract is broken.

**Mandatory postgres mode check:**

```sql
-- After any migration that touched views, verify ALL public views still have security_invoker
SELECT c.relname, c.reloptions
FROM pg_class c
JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE n.nspname = 'public' AND c.relkind = 'v'
AND (c.reloptions IS NULL OR NOT 'security_invoker=true' = ANY(c.reloptions));
-- Expect 0 rows. Any row = silent regression.
```

If any view is missing `security_invoker = true`, the fix is:

```sql
ALTER VIEW public.<view_name> SET (security_invoker = true);
```

The postgres mode's PG4 verify step must run this check. The docs mode's retired-name sweep
should also check for `SECURITY DEFINER` views added unintentionally.

### L10 — `get_advisors` misses overly-permissive RLS; supplement with direct query (postgres mode)

The Supabase `get_advisors` MCP tool does not catch RLS policies with `qual = 'true'`
(i.e. policies that grant access to ALL rows unconditionally). These are syntactically valid
and pass all type checks, but effectively disable row-level isolation for the table.

**Supplement to PG1 detect:**

```sql
-- Find unconditionally-permissive RLS policies
SELECT schemaname, tablename, policyname, cmd, qual, with_check
FROM pg_policies
WHERE schemaname = 'public'
AND (qual = 'true' OR qual IS NULL)
ORDER BY tablename, policyname;
```

Any result where `qual = 'true'` (not `(select auth.uid()) IS NOT NULL` or similar) is a
candidate for a `schema-campaign` item — not safe to auto-fix without understanding intent.

Also supplement with the stale-function-body scan (catches v2 rename drift):

```sql
-- Detect function bodies still referencing renamed columns/tables
SELECT p.proname, LEFT(p.prosrc, 200) AS body_preview
FROM pg_proc p
WHERE p.prosrc ILIKE '%user_preferences%nickname%'   -- old column path
   OR p.prosrc ILIKE '%folder_classes%'              -- old lookup table ref
   OR p.prosrc ILIKE '%council_members%';            -- pre-v2 table name
-- Expect 0 rows post-v2 rename
```

### L11 — Pre-existing lint warnings create baseline noise; always track delta (lint mode)

At `--max-warnings 0`, a full project-wide lint run surfaces pre-existing warnings in files
the current campaign never touched. Running the lint mode and reporting "N warnings" creates
false alarm fatigue and wastes triage time.

**Canonical pattern (from conquering-campaign scoped-lint):**

```bash
# Baseline at session start
cd lex_council && npx eslint --format json --ext .ts,.tsx apps/web packages \
  > /tmp/lint_baseline.json

# After changes, compute delta (new files only)
git status --short | awk '$1 ~ /^M/ || $1 == "M" {print $2}' > /tmp/touched.txt
npx eslint --max-warnings 0 $(cat /tmp/touched.txt | grep "^apps/web/" | sed 's|^apps/web/||')
```

The lint mode's report MUST say "N new warnings on campaign-touched files (M pre-existing
suppressed)" — not a raw count. The suppressed count IS the signal: a high suppressed count
means a lint-debt campaign is overdue.

Also: filter tsc output to exclude `.next/` paths. The `.next/` directory contains stale
`*.d 2.ts` duplicate files that produce spurious type errors unrelated to source changes.

### L12 — `no-unused-expressions` is always architectural — never auto-fix (lint mode)

The `no-unused-expressions` rule fires most often on the ternary-as-statement pattern:
`cond ? a.foo() : a.bar()`. This fails the rule because the ternary's result value is unused.
ESLint `--fix` CANNOT resolve this automatically — the correct fix is `if/else`, which changes
code structure. The pattern is common in portal pages and event handlers.

**Detection:** `grep -rn '?\s*[a-z].*\..*()' apps/web/ --include="*.tsx" | grep -v '//'`

**Fix pattern:** Always `if (cond) { a.foo() } else { a.bar() }`. Never use `void cond ?...`
or `eslint-disable-line` — the rule exists to prevent subtle bugs in React event handlers.

Similarly, `react-hooks/rules-of-hooks` is always architectural. A hook called inside a
conditional is a structural problem that requires component decomposition, not suppression.

### L13 — Scope ESLint to campaign-touched files first; grep for hex literals separately (lint mode)

Two items ESLint misses entirely that the lint mode should check as supplementary scans:

**1. Off-token hex color literals** — ESLint does not scan CSSProperties objects for `#hex`
strings. A grep sweep is more reliable:

```bash
grep -rn '#[0-9a-fA-F]\{3,6\}\b' \
  lex_council/apps/web/components \
  lex_council/apps/web/app \
  --include="*.tsx" --include="*.ts" | grep -v "//.*#" | grep "color\|background\|border"
```

Count > 10 = flag for a token-sweep campaign. Count > 50 = existing tech-debt worth a
dedicated pass.

**2. Module-level `const` style-object orphans** — `no-unused-vars` does not catch exported
objects that are declared but never imported. These accumulate after refactors. Use:

```bash
# Find style-constant files with zero downstream imports
grep -rn "^export const.*Style\|^export const.*Styles\|^export const.*STYLE" \
  lex_council/apps/web/ --include="*.ts" --include="*.tsx" | \
  while read file; do
    fname=$(echo "$file" | cut -d: -f1)
    grep -rl "$fname" lex_council/apps/web/ 2>/dev/null | grep -v "$fname" | wc -l
  done
```

### L14 — ThemeToggle + StrictMode errors are known noise in `errors` mode

Two error signatures that appear in virtually every dev session and should be suppressed
by the `errors` mode classifier without requiring triage:

1. **ThemeToggle hydration errors** — `Warning: Extra attributes from the server: class` on
   the `<html>` element. Caused by the server rendering without a theme attribute and the
   client immediately setting `data-theme`. These are not bugs — the sync bootstrap script
   in `app/layout.tsx` eliminates FOUC. Classifier: `framework-noise` + suppress.

2. **React StrictMode double-invocation errors** — components appear to error twice because
   StrictMode intentionally calls lifecycle functions twice in development. If the same error
   signature appears exactly twice consecutively with no intervening route, it's StrictMode.
   Classifier: `framework-noise` + suppress.

Add both to `errors_cleanup.py`'s noise-pattern list.

### L15 — Stale trigger bodies after v2 rename are invisible to advisor + lint (postgres mode)

The 2026-05-24 v2 campaign renamed 54 tables. Many trigger functions reference old table/column
names that no longer exist. These **pass all advisor checks** (Supabase advisor only checks
structure, not function bodies), **pass tsc** (pg functions are opaque to TypeScript), and
**pass lint** (ESLint doesn't read SQL). The functions compile and run — they just operate on
the wrong data silently.

The only way to detect this class is a `pg_proc.prosrc` full-text scan:

```sql
-- Stale trigger function body references (v2 rename targets)
SELECT p.proname AS fn_name,
       n.nspname AS schema,
       LEFT(p.prosrc, 300) AS body_preview
FROM pg_proc p
JOIN pg_namespace n ON n.oid = p.pronamespace
WHERE n.nspname IN ('public', 'private')
AND (
    p.prosrc ILIKE '%council_members%'
    OR p.prosrc ILIKE '%ppl%'
    OR p.prosrc ILIKE '%fd_access%'
    OR p.prosrc ILIKE '%cm_hr%'
    OR p.prosrc ILIKE '%admin_perms%'
    OR p.prosrc ILIKE '%whbd_%'
    OR p.prosrc ILIKE '%atnd_%'
    OR p.prosrc ILIKE '%n_kinds%'
)
ORDER BY p.proname;
-- Expect 0 rows. Each row = stale trigger body needing a campaign fix.
```

Add this as an additional detect step in the postgres mode's PG1 phase. Results classified as
`schema-campaign` (they require careful, campaign-scoped SQL surgery — not auto-fixable).

### L16 — i18n namespace scope trap: `useTranslations` scope must match the JSON file tree (language mode)

A component that calls `useTranslations('customer_wizard')` while living under a page that
loads `admin.json` will silently fall through to `getMessageFallback` and render raw key paths
in production. The correct call is `useTranslations('admin.customer_wizard')`.

This is undetectable by the `language` mode's key-scan (the key exists in the JSON; the issue
is the namespace prefix at the call site). Symptom: the Languages panel shows 0 untranslated
keys but users see literal `admin.customer_wizard.step_1_title` strings in the UI.

Detection grep (pair with the language mode's detect step):

```bash
grep -rn "useTranslations(['\"]" lex_council/apps/web/ --include="*.tsx" |
  grep -v "^.*useTranslations('admin\." |
  grep -E "(admin|portal|members|clients)" | head -20
# Results may indicate a missing namespace prefix
```

Also: **`window.confirm()` calls are untranslatable** and should be flagged as technical debt
during any language pass. The language mode's detect step should grep for `window.confirm(`
and surface a count. These must be migrated to a custom modal component before the string
can be covered by the i18n system.

### L17 — Postgres advisor requires multi-pass until clean; common recurring types (postgres mode)

The Supabase `get_advisors` result does not stabilise after fixing one batch of issues —
fixing the top-N advisories often reveals a new Nth+1 advisory that was hidden behind them.
**Loop until `get_advisors` returns an empty list** (or only known-intentional exceptions).

The two most common advisor types in this project:

| Advisor | Signal | Action |
|---|---|---|
| `rls_enabled_no_policy` | Table has `ALTER TABLE ... ENABLE ROW LEVEL SECURITY` but zero policies — usually a stale backup/archive table | Classify `schema-campaign`; user decides to DROP or add a blanket policy |
| `authenticated_security_definer_function_executable` | A `SECURITY DEFINER` function is still EXECUTE-able by `authenticated` after `REVOKE ... FROM PUBLIC` — `authenticated` inherits via PUBLIC | Add explicit `REVOKE EXECUTE ON FUNCTION ... FROM authenticated;` if not intentional; document as exception if intentional |

Dead `auth.role() = 'service_role'` in RLS policies (308 across 77 tables historically)
generate a "multiple permissive policies" advisor. These are always dead code — `service_role`
bypasses RLS entirely and the policy is never evaluated. Flag as `schema-campaign` for batch
DROP in a dedicated cleanup migration.

### L18 — `react-hooks/exhaustive-deps` suppressions on mutation callbacks are intentional (lint mode)

In this codebase, mutation callbacks are intentionally passed as stable refs and deliberately
excluded from `useEffect` dependency arrays. These lines have explicit
`// eslint-disable-next-line react-hooks/exhaustive-deps` comments.

**The lint mode must NOT remove these suppressions.** They are not technical debt — they are
correct design decisions. Classify any file with this pattern as `reviewed-intentional` and
skip it in the auto-fix pass.

Similarly, `no-undef` errors for `Buffer`, `process`, `module`, or `require` in `scripts/`
files are not real errors — the ESLint config uses browser environment, but `scripts/` files
run in Node.js. Fix is `/* eslint-env node */` at the top of the file, NOT per-line `eslint-disable`.

### L19 — TS2304 `Cannot find name 'VIEWS'` always means a missing view-registry key (lint mode)

The most common tsc error in this codebase. Whenever a new view is created and added to a
page query, it must also be added to `apps/web/lib/view-registry.ts` as a key in the `VIEWS`
constant. If this step is missed, every file that calls `VIEWS.<new_key>` fails tsc with
`TS2304 Cannot find name 'VIEWS'` or `TS2339 Property '<key>' does not exist on type...`.

The lint mode's detect step should explicitly grep for this pattern:

```bash
grep -rn "VIEWS\." lex_council/apps/web/ --include="*.tsx" --include="*.ts" |
  grep -v "view-registry" | grep -oE "VIEWS\.[a-zA-Z_]+" | sort -u > /tmp/view_usages.txt

grep -n "^\s*[a-zA-Z_]" lex_council/apps/web/lib/view-registry.ts > /tmp/view_registry.txt

# Find usages not in registry
comm -23 <(sort /tmp/view_usages.txt | sed 's/VIEWS\.//') \
         <(grep -oE "^\s*[a-zA-Z_]+" /tmp/view_registry.txt | sort)
```

Any row in the comm output = missing view-registry entry = tsc error on that page.

### L20 — `VERSION-RELEASE-WORKFLOW.md` doc-stamp drift (RESOLVED 2026-05-29; release mode)

> **RESOLVED 2026-05-29.** VERSION-RELEASE-WORKFLOW.md §4 was reconciled to the live tree (ZUSTAND-STORES removed — archived; Vault Core ×3 stamps; package.json documented as a real drift-prone mirror) and the bump procedure now lives in `references/release-procedure.md`, run by the `release` mode. The historical drift below is the record of what was wrong.

The canonical release procedure doc points its doc-header-sync step at paths that predate the
solar-system docs restructure: `docs/logs/INDEX.md`, `docs/architecture/ARCHITECTURE.md`,
`docs/architecture/frontend/ZUSTAND-STORES.md`. Current structure is `docs/vault-logs/` +
the planet hubs (Vault Core, BACKEND, FRONTEND, INTEGRATION). The workflow examples still say
`1.6.X`; the app is at **1.7.25**.

Consequence: following the workflow's hard-coded target list silently SKIPS the real version
stamps. The `release` mode's PR3 step greps for what actually carries a stamp NOW instead
of trusting the list.

Also: **app version lives in TWO places that drift** — `apps/web/config/app.config.ts`
(`APP_CONFIG.version`, canonical) AND the web `package.json` `version` field. And there are
**two hand-maintained changelog indexes** (`docs/vault-logs/INDEX.md` +
`docs/logs/INDEX.md`) synced by hand on every release. The prod live version stamp (surfaced
in the running site) is the reliable signal for whether a commit actually deployed.

**Action item beyond the skill:** reconcile `VERSION-RELEASE-WORKFLOW.md` with the current
docs structure. Until then, treat its target list as advisory, not authoritative.

### L21 — Release-time breakage is a recurring class; gate before bump (release mode)

Across the mined sessions, ~6 distinct release failures recur — each catchable by a pre-push
gate (the `release` mode). The cluster:

| Failure | Root | Catch |
|---|---|---|
| Cloudflare/OpenNext bundle wall | SSR worker 15.4 MiB raw / 3.2 MiB gzip > 3 MiB free-tier | `du`/gzip gate; webpack alias + dynamic `recharts`; `serverExternalPackages` NOT honored by OpenNext |
| `generateMetadata` in `'use client'` page | Next.js 16 hard build error | grep same-file co-occurrence; keep `page.tsx` a Server Component |
| Whole `[locale]` migration uncommitted | local-only i18n migration | `git status` → prod-only 404 |
| Import-depth off-by-one after route move | every admin file moved one dir level | 718 TS2307; webpack masks by stopping at first error |
| Migration filename not 14-digit | `YYYYMMDD` vs `YYYYMMDDHHMMSS` | Supabase branch stuck MIGRATIONS_FAILED, DB empty |
| CF Pages cache-wedge / lockfile bug | ast-grep Linux-binary npm#4828 | `optionalDependencies`; empty-retrigger commit precedent |

The automation wish the user voiced: a `measure-worker.mjs` prebuild/CI gate that fails if
gzip > 3 MiB — once size-bound on Workers, every PR is one dependency away from breaking the build.

### L22 — Code-consolidation: byte-compare before merge; the registry is pre-seeded (consolidate-code mode)

The `consolidate-code` mode ships with `CONSOLIDATION-CANDIDATES.md` pre-seeded (41 open
candidates from 146-session mining). Two load-bearing disciplines:

1. **Byte-compare before merging N near-duplicates** (§L2/§L4). The look-alike-but-different
   trap: 4 RLS storage policies looked like they hard-coded the same bucket array but encoded
   distinct per-CMD access tiers; a naive merge silently widened access on 3 buckets. Only merge
   when all N are byte-identical OR the merged API preserves every difference.

2. **Mechanical-tier first, codemod where possible.** The single biggest verified-live candidate
   is `const PANEL_WIDTH = 332` copy-declared in **44 files** while the canonical
   `PORTAL_SIDEBAR_WIDTH = 332` already exists — a pure codemod. Magic-literal dedup, orphan
   `git rm`, identical-helper extraction are all T1 (autonomous). DB view merges, RLS predicate
   extraction, and the 36-button-signature standardization are T2 (campaign).

The duplicate-detector pattern that works (session 1d944474): escalate from name-equality to
**SHA-1 body-hash** — it caught 2 missed mutation exports that name-matching missed.

### L23 — Standing instruction: dev server must survive session archive (skill-meta)

Recurring across 3+ sessions, now a standing instruction: the local dev server must NOT be tied
to the Claude Code session lifecycle — it dies when the harness archives/recycles the session,
forcing ~10 "open dev server" / "restart dev server" prompts. Launch it **detached** (outside
the harness) so it survives. This matters to the `errors` mode specifically — `/tmp/lex-dev.log`
only exists if the tee'd dev server is running; if the server died with the session, the log is
stale and `errors` mode reads nothing.

The deeper user complaint behind it: "burning all Claude tokens on basic feature work" — the
cleanup skill (and its auto-sweep modes) exist precisely to economize that spend by making
hygiene a one-command pass instead of a manual grind. Hygiene drift (i18n gaps, cross-NS dup
keys, dev-log errors, postgres advisors, lint, consolidation candidates) should be swept
automatically, not re-discovered by hand each time.

### L24 — Skill version-sync drift: skills live in multiple copies (skill-meta)

Both the `cleanup` and `conquering-campaign` skills exist in multiple locations that drift:
a CLI/staging copy (`_skill-updates/` or `.claude/skills/`) and a deployed plugin-cache copy,
plus an unverifiable cloud `anthropic-skills` copy. Sessions hit version drift (canonical at
v1.6.0 while deployed plugin-cache at v1.3.0) and manual copy-paste deploys.

For the `cleanup` skill: the canonical is `.claude/skills/cleanup/SKILL.md` (this file). When
bumping, confirm there isn't a second deployed copy serving a stale version. The recurring
"duplicate frontmatter breakage on every skill deploy" is a symptom of this multi-copy reality —
a deploy step concatenates or re-wraps frontmatter.

This is itself a consolidation candidate (registry C-skill-drift): the skill should have ONE
canonical home with a deterministic deploy, not N hand-synced copies.

## Why this skill exists

The Languages dev-tools panel (LanguagesPanel.tsx) shows a
"Not fully translated" counter. The counter grows every time a new page
ships with i18n keys that aren't translated into the 5 non-EN locales.
Without periodic cleanup, the counter only grows — manually filling
1000+ strings across 5 locales is the kind of task that gets perpetually
deferred. This skill makes it a one-command pass: `/cleanup` → 5 agents
in parallel → done in ~5 minutes wall-clock.

The empirical baseline from the 2026-05-28 first run:

- Before: 1,032 (ar 143, es 206, fr 340, ru 171, zh 172)
- After: 585 (ar 31, es 156, fr 280, ru 59, zh 59) — −447 actual
  translations applied; remaining 585 is the inherent floor (brand
  acronyms + form placeholders + valid cognates).

## Versioning

This skill carries a semantic version in its frontmatter (`version: X.Y.Z`)
and at the top of the body heading. **Bump it whenever the skill is
modified.** The contract:

- **PATCH (1.0.x)** — bugfix in the script, prompt-template wording tweak,
  brand-glossary addition, new tone example, doc clarification. No
  workflow change for the user.
- **MINOR (1.x.0)** — new mode goes live (docs, consolidate, etc.), new
  optional flag on a script subcommand, new locale added, new decision
  point added that does not break existing invocations. Backward-compatible.
- **MAJOR (x.0.0)** — workflow change that breaks existing invocations
  (e.g. renaming `language` → something else; removing a subcommand;
  changing the per-locale agent contract in an incompatible way). Rare.

**On every bump:**

1. Edit `version:` in the frontmatter.
2. Update the `(vX.Y.Z)` tag in the body heading.
3. Prepend a row to §Changelog with date + summary.
4. If a new mode goes live, also update the §Modes table (status LIVE) and
   add §When-to-invoke triggers for that mode.

## Changelog

| Version | Date | Summary |
|---|---|---|
| **1.8.1** | 2026-05-29 | **`followups` is now auto-spawned by `conquering-campaign` at campaign close** (its v3.3.0 §5.7 calls `spawn_task` → a fresh session/worktree runs `/cleanup followups` with the campaign's `99-risk-sweep.md` ## Open items inlined). Doc note added to the followups mode recording the pairing; **no script change** — the mode already locates the most-recent `status: completed` campaign + greps `## Open items` / `spawn_task` / `follow-up`. The committed risk-sweep stays the durable fallback if the spawn is skipped/dismissed. |
| **1.8.0** | 2026-05-29 | **Tier-0 lesson-wiring + Tier-1 orchestrator (resolves UPGRADE-ROUTES R4/R5/R7).** Wired 7 codified-but-never-built lessons into their scripts: **L9/L10/L15/L17** → `postgres_cleanup.py detect` now emits + classifies the security_invoker-missing / stale-prosrc / permissive-RLS (`qual='true'`) / dead-`service_role` / rls-enabled-no-policy health queries (were prose-only, depended on Claude remembering); **L11 + L19** → `lint_cleanup.py` gained a `baseline` subcommand (reports new-on-touched-files vs pre-existing-suppressed) + a view-registry cross-check (every `VIEWS.<key>` usage must exist in `view-registry.ts` — the guaranteed-TS2304 guard; live: 151 keys / 333 callsites / 0 missing); **L14** → `errors_cleanup.py` suppresses ThemeToggle/`Extra attributes` hydration noise; **L16** → `i18n_cleanup.py detect` surfaces untranslatable `window.confirm()` debt (live: 7 calls / 5 files). Bug fixes: `docs_cleanup.py wikilinks` now buckets code-file links (`[[page.tsx]]`) as `code-link` not `broken` (broken 3238→1015); the hardcoded home-path `LEX_ROOT` in lint/docs/followups/consolidate_code replaced with a `default_root()` walk-up (cross-machine portability per W1); `postgres` `datetime.utcnow()`→`now(timezone.utc)`. **NEW `scripts/run_all.py` (R7)** — the `run all cleanups` orchestrator: runs the local hygiene modes detect-only, merges every `/tmp/*.json` into one severity-ranked (CRITICAL→HIGH→MED→LOW) `/tmp/cleanup_triage.md` dashboard + per-mode last-run age; postgres (MCP) + apply-modes excluded. `run` re-runs then merges, `report` merges existing, `--fast` skips the two slowest. Step-0 `run all cleanups` row now points at it. | **All three DRAFT modes go LIVE — `docs`, `followups`, `consolidate-code`** ("add the drafts + upgrade"). Companion scripts written + smoke-tested against the live tree: `scripts/docs_cleanup.py` (610 ln; subcommands frontmatter/wikilinks/orphans/retired-names/artifacts/campaign-drift/all — detect-only, never edits docs; live run surfaced 3,238 broken + 3,717 archived-pointer wikilinks, 393 orphan vault-logs, 17 retired names), `scripts/followups_cleanup.py` (396 ln; locate/extract/classify/mark — execution of doable items stays Claude's job), `scripts/consolidate_code.py` (514 ln; scan/classify/surface/extract — live: PANEL_WIDTH×45, PAGE_SIZE_OPTIONS×2, 119 off-token hex, 3 dup-function groups; `extract` dry-run only, byte-compare hard rule enforced — never auto-merges). Description, §Modes table, Step-0 router, and the three §Mode section headers flipped DRAFT→LIVE; "run all cleanups" now includes docs + followups (consolidate-code + release stay explicit-invoke). **9 LIVE modes, 0 DRAFT.** UPGRADE-ROUTES.md R1/R3/R6 resolved. |
| **1.6.0** | 2026-05-29 | **`release` mode goes LIVE — merged the retired `update-app-version` skill into cleanup.** The DRAFT `pre-release` gate is promoted to a unified two-phase `release` mode: Phase 1 hygiene gate (lint+errors+postgres + Cloudflare/OpenNext bundle-wall + Next.js 16 hazards → green/red verdict), Phase 2 full version bump (canonical `app.config.ts` + `package.json` mirror decision + `logs/X.Y.Z.md` changelog + `logs/INDEX.md` row + doc-stamp sync to ARCHITECTURE + Vault Core ×3 + git block). Full bump recipe extracted to `references/release-procedure.md` (lifted from the deleted skill, with the 2026-05-29 corrections baked in: ZUSTAND-STORES dropped — archived; Vault Core has THREE stamps; package.json is a real drift-prone mirror, not a 0.x placeholder). Standalone `skills/update-app-version/` deleted. Description + Step-0 router + trigger phrases absorbed ("bump the version", "release X.Y.Z", "ship a release", "make it 1.7.X"). `--gate` flag added for gate-only runs. UPGRADE-ROUTES.md R2 resolved (user chose merge over the recommended hand-off); L20 marked RESOLVED. |
| **1.5.0** | 2026-05-29 | Checkup + 2nd session-mining pass (consolidation + app-upgrade lens, 8 subagents over 146 sessions → 219 fresh findings). Two new DRAFT modes: **consolidate-code** (code-side sibling of `consolidate` — scans for duplicate components/views/RLS-predicates/constants/literals, classifies extract-now / needs-campaign / resolved, byte-compares before merge per §L2/§L4, extracts the T1 mechanical tier) and **pre-release** (app-upgrade hygiene GATE run before a version bump — lint+errors+postgres checks + Cloudflare/OpenNext bundle-wall + Next.js 16 hazard probes + doc-stamp staleness check; green/red verdict, hands off to the `update-app-version` skill, does NOT do the bump). New companion docs: `UPGRADE-ROUTES.md` (9 ranked skill-growth routes R1–R9) + `CONSOLIDATION-CANDIDATES.md` (41 open candidates across FE/config/DB/i18n, 3 tiers, pre-seeded + verified-live; references the 74-finding `2026-05-22_db-wide-consolidation-audit` synthesis). §Lessons extended L20–L24: VERSION-RELEASE-WORKFLOW.md stale (doc-stamp targets predate solar-system restructure; app at 1.7.25 vs doc's 1.6.X examples; version in 2 drift-prone places) (L20); release-time breakage is a recurring 6-failure class catchable by a pre-push gate (L21); code-consolidation byte-compare discipline + registry pre-seeded, biggest verified-live candidate `PANEL_WIDTH=332` in 44 files vs canonical `PORTAL_SIDEBAR_WIDTH` (L22); dev-server-survives-archive standing instruction + token-economizing rationale (L23); skill version-sync drift across multiple copies (L24). Step 0 routing table + trigger phrases + description extended. Both new modes are DRAFT pending `scripts/consolidate_code.py` + `scripts/pre_release.py`. |
| **1.4.0** | 2026-05-29 | `postgres` + `lint` modes go LIVE. New scripts: `scripts/postgres_cleanup.py` (subcommands: `detect`, `classify`, `apply`, `verify`, `surface`) and `scripts/lint_cleanup.py` (subcommands: `detect`, `classify`, `apply`, `verify`, `surface`). **postgres mode**: calls Supabase `get_advisors` MCP + three health queries (missing FK indexes, tables without RLS, high dead-tuple tables); classifies each finding as advisory-auto-fix / advisory-surface / schema-campaign / noise; auto-generates `CREATE INDEX IF NOT EXISTS` SQL for missing FK indexes; flags all destructive or structural issues (unused indexes, RLS disabled, SECURITY DEFINER views, stale trigger bodies) as `schema-campaign`; requires multi-pass until clean; migration filename must be 14-digit timestamp (YYYYMMDDHHMMSS). **lint mode**: runs `npx eslint --format json` from `lex_council/`; dedupes by (file, rule); classifies as auto-fixable / architectural / wip-noise; auto-runs `eslint --fix` for safe rules only (prefer-const, no-var, import/order, etc.); runs tsc after; surfaces `no-unused-expressions` (ternary-as-statement), `react-hooks/*`, `import/no-cycle`, and parse errors as architectural campaign candidates; never removes `react-hooks/exhaustive-deps` suppressions on mutation callbacks (intentional); includes off-token hex grep bonus scan. §Lessons learned extended with L9–L19 from mining 146 archived session files (8 parallel subagents, ~250 lessons synthesised): `security_invoker` silent-drop trap (L9), `get_advisors` gaps (L10, L15, L17), lint baseline noise (L11), `no-unused-expressions` architectural (L12), hex literal + orphan scan (L13), ThemeToggle+StrictMode noise (L14), i18n namespace scope (L16, L18), mutation-callback suppression (L18), view-registry TS2304 pattern (L19). Step 0 routing table updated with postgres + lint rows; trigger-phrases extended; `run all cleanups` order updated to language → consolidate → errors → postgres → lint → docs → followups. |
| **1.3.0** | 2026-05-28 | `errors` mode goes LIVE. New script `scripts/errors_cleanup.py` (subcommands: `detect`, `classify`, `mark`). Companion runtime shipped alongside: dev-only `apps/web/app/api/_dev/client-error/route.ts` (POST sink, gated on `NODE_ENV === 'development'`, returns 404 in prod, appends to `/tmp/lex-dev.log`) + `apps/web/components/_dev/DevErrorSink.tsx` (`'use client'` component registering `window.error` + `unhandledrejection` listeners that `navigator.sendBeacon` JSON payloads to the route) mounted from `apps/web/app/layout.tsx` under a NODE_ENV gate. Atta runs dev with `npx turbo dev 2>&1 | tee /tmp/lex-dev.log` — server stdout/stderr tees into the file; browser errors arrive as `[CLIENT_ERROR <iso-ts>] {…json…}` lines from the sink. Parser supports Next.js error glyph (` ⨯ `), the standard JS error families plus PostgrestError / AuthError / FetchError / AbortError, both `at name (path:line:col)` and bare `at path:line:col` stack-line shapes, and the client JSON shape. Route attribution piggybacks on the standard ` GET|POST|… /path NNN` lines that Next.js logs. Dedupe by `(error_type, first 200 chars of message, first repo-frame path:line)`. Classification: any frame under `apps/web/` / `packages/{md,auth,supabase}/` → `code-bug`; HMR / webpack-internal / Fast Refresh / `node_modules/{next,react,react-dom}/` / Deprecation / `MISSING_MESSAGE` → `framework-noise`; `fetch failed` / `ECONNREFUSED` / `ENOTFOUND` / `ETIMEDOUT` / `network` / `supabase` without repo frame → `external`. Auto-fix rubric (E4, strict): single-line `?.`-chain for null/undefined member access; missing-import insertion when the symbol is exported from exactly one repo module; Levenshtein-1 typo replacement when exactly one in-scope candidate exists. Auto-fix BLOCKED when stack lacks precise file:line / file has unrelated uncommitted edits / the fix would alter a signature/export/type def / >3 auto-fixes proposed in one batch (smell-test). `tsc` runs between fixes within a batch; first failure aborts the batch. Step 0 routing table + trigger-phrases extended; description field now lists `errors` as LIVE; `run all cleanups` order updated to language → consolidate → errors → docs → followups. Smoke-test on synthetic log confirmed parse + classify behaviour. |
| **1.2.0** | 2026-05-28 | `consolidate` mode promoted from TODO → LIVE. Companion script `scripts/consolidate_cleanup.py` ships with four subcommands: `detect` (find cross-locale safe-to-merge groups + show whether `common.json` already has a target), `map-callsites` (AST-aware resolution — parses `useTranslations()` bindings + tracks which `t` variable maps to which namespace, then resolves every `t-call` to its full key), `apply` (two-phase — delete dead keys first then rewrite callsites + delete live keys), `verify` (re-run safe-to-merge detector + JSON parse check). Three lessons codified from the first execution: (1) the naive Explore-agent approach reports false "0 callsites" — only AST-aware Python parses correctly; (2) suffix grep over-matches dramatically (`'status_label'` matches dozens of unrelated keys) — full-key + namespace-aware resolution required; (3) two-component-per-file files can have `tc` bound in only one component → tsc catches this as `Cannot find name 'tc'`; fix by adding the binding manually. Default surgical policy documented (universal UI labels only: Status/Type/Description/Date/Yes/No + Save/Close/Delete/Download + language names); entity nouns and context-bound headers stay separate. First execution baseline: surgical set of 62 doomed keys → 16 dead (auto-deleted) + 58 live callsites rewritten across 37 files; total JSON entries removed: 372 (62 × 6 locales); total keys per locale: 5,650 → 5,601; safe-to-merge groups: 164 → 150. Step 0 routing table + trigger-phrases list updated; description field now lists `consolidate` as LIVE. |
| **1.1.0** | 2026-05-28 | Lessons extracted from same-day solar-system doc-sync audit + 8-item follow-up sweep ([[2026-05-28_solar-system-doc-sync]], [[2026-05-28_solar-system-doc-sync-followups]], [[2026-05-28_storage-rls-bucket-matrix-helper]], [[2026-05-28_edge-fn-tombstone-cleanup]]). **`docs` mode** promoted from TODO → DRAFT with a 10-step concrete recipe (frontmatter sync, wikilink rot, orphan vault-logs, retired-name registry sweep, post-rename narrative-artifact detection, in-progress campaign drift). **`followups` mode** added as new DRAFT — codifies the post-campaign sweep pattern (locate → extract items → classify doable/needs-hands/exception → parallel execute → vault-log). New §Lessons learned section (L1–L8) covers cross-mode architecture: MCP-out-of-reach taxonomy, behavior-parity verification, post-rename artifact patterns, look-alike-but-different trap (the RLS-bucket-matrix discovery — 4 hard-coded arrays looked redundant but encoded distinct per-CMD access tiers), PostToolUse hook race conditions on batch Edits, same-session continuation markers (`/goal`, "finish the rest", "i am done"), vault-log size threshold, periodic-grep-after-rename-campaign discipline. Workflow Step 0 routing table updated; trigger-phrases list extended; Modes table refreshed (language LIVE / docs DRAFT / followups DRAFT / consolidate TODO). No script-side changes — `docs` + `followups` recipes are ready for the next person to wire up `scripts/docs_cleanup.py` and `scripts/followups_cleanup.py`. |
| **1.0.0** | 2026-05-28 | Initial release. `language` mode live — detects untranslated keys (locale value == EN), spawns 5 parallel locale subagents (AR/ES/FR/RU/ZH), applies translations back to `messages/{loc}/{ns}.json`, verifies. `docs` and `consolidate` modes stubbed for future. First execution baseline: 1,032 → 585 (−447 strings actually translated, remaining 585 = floor of brand acronyms + form placeholders + valid ES/FR cognates). |

## Related

- `UPGRADE-ROUTES.md` — skill roadmap; 9 ranked growth routes (R1–R9). Re-read before the next upgrade pass.
- `CONSOLIDATION-CANDIDATES.md` — 41 open consolidation candidates (FE/config/DB/i18n, 3 tiers); seeds the `consolidate-code` mode.
- [[2026-05-22_db-wide-consolidation-audit]] — 74-finding staged DB consolidation plan; canonical source for the DB rows in the registry.
- `references/release-procedure.md` — full version-bump recipe run by the `release` mode (Phase 2). Absorbed the retired standalone `update-app-version` skill (cleanup v1.6.0).
- `docs/VERSION-RELEASE-WORKFLOW.md` — human-readable release procedure (doc-stamp targets reconciled 2026-05-29; its §4 and this skill's release mode agree).
- [[2026-05-29_cleanup-skill-upgrade]] — vault log for v1.4.0 + v1.5.0 upgrades (postgres + lint + consolidate-code + pre-release modes + session-mining lessons).
- [[2026-05-28_languages-panel-cross-locale-stats]] — vault log for
  the Languages panel work that surfaced the original count.
- [[2026-05-28_translation-pass-non-en-locales]] — vault log for the
  first execution of this skill's `language` mode.
- `vault-log-compliance` skill — delegated to in Step L5.
- Brand glossary lives in
  `~/.claude/skills/cleanup/scripts/i18n_cleanup.py:BRAND_OR_CODE`.
- `scripts/postgres_cleanup.py` — companion script for postgres mode.
- `scripts/lint_cleanup.py` — companion script for lint mode.
- `scripts/docs_cleanup.py` — companion script for docs mode (detect-only).
- `scripts/followups_cleanup.py` — companion script for followups mode.
- `scripts/consolidate_code.py` — companion script for consolidate-code mode (dry-run extract).
- `scripts/run_all.py` — `run all cleanups` orchestrator (R7): runs local modes detect-only, writes the severity-ranked `/tmp/cleanup_triage.md` dashboard.
