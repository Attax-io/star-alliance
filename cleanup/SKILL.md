---
name: cleanup
version: 1.2.0
description: Multi-mode hygiene skill for Lex Council. Today's modes — language (LIVE, translate every i18n key that any non-EN locale left equal to its EN value); consolidate (LIVE, fold safe-to-merge i18n keys whose translations agree in every locale into shared common.* keys via AST-aware callsite rewrites); docs (DRAFT recipe ready, awaiting script wire-up — sync stale frontmatter dates + counts, flag broken wikilinks, find orphan vault-logs, detect retired-primitive references, catch post-rename narrative artifacts); followups (DRAFT — sweep recent vault-logs for deferred items, classify each as doable-autonomously / needs-user-hands / accepted-exception, execute the doable ones in parallel). Use this skill whenever the user says "run cleanup", "/cleanup", "/lex_cleanup", "clean up the languages", "translate untranslated", "i18n cleanup", "fill in translations", "language cleanup", "consolidate translations", "merge safe-to-merge keys", "clear duplicates", "sync the doc footers", "doc cleanup", "finish the followups", "close the followups", or any phrasing that implies sweeping the app for a class of accumulated drift after new pages or keys or campaigns landed. Auto-discovers scope, parallelizes the heavy work across N subagents (5 for language; 1 per planet for docs), applies results, verifies, and delegates the vault log to vault-log-compliance. Skill is upgradable — add new modes by appending a §Mode section + adding a router branch under §Workflow; bump the `version` per §Versioning whenever the skill changes.
---

# Cleanup — Lex Council hygiene sweeps (v1.2.0)

This skill packages the operational recipes for periodic cleanup passes that
the app accumulates between feature builds. Each mode is independent; the
skill body routes to the right workflow based on what the user asked for.

## Modes

| Mode | Status | What it does |
|---|---|---|
| **language** | LIVE | Sweep every non-EN locale (ar/es/fr/ru/zh), find keys still equal to the English value, translate them in parallel via 5 subagents, write back, verify. |
| **consolidate** | LIVE | Detect cross-locale safe-to-merge i18n groups, pick surgical universal labels (Status / Type / Yes / etc.), AST-aware callsite mapping, two-phase apply (dead keys first then live rewrites), delete now-orphan keys. Script: `scripts/consolidate_cleanup.py`. Also future: code-side consolidation — surface 3+ near-duplicate hard-coded literals for refactor-with-helper. |
| **docs** | DRAFT (recipe ready, awaiting script) | Sync stale frontmatter dates + counts on planet hubs (BACKEND/FRONTEND/INTEGRATION/DESIGN-CANON/GENERAL-GUIDELINES/Vault Core); flag broken wikilinks + archived-pointers; find orphan vault-logs missing from INDEX.md; bump app version stamp in Vault Core; grep all docs for retired-primitive names; detect post-rename narrative artifacts (telltale "X (v2; was X)" patterns). |
| **followups** | DRAFT (recipe ready) | After a campaign closes, sweep the most recent vault-logs (+ campaign `99-risk-sweep.md` files) for explicitly-deferred items ("follow-up", "spawn_task", "future cleanup", "code cleanup checklist"). Classify each as doable-autonomously / needs-user-hands / accepted-permanent-exception. Execute the doable ones in parallel; surface the rest as a checklist. |

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
| "sync the doc footers", "doc cleanup", "/cleanup docs", "check the docs are fresh" | `docs` |
| "finish the followups", "close the followups", "/cleanup followups", "sweep the campaign followups" | `followups` |
| "run all cleanups" | execute each in order: language → consolidate → docs → followups (skip DRAFT modes silently) |

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

### Mode: docs (DRAFT — recipe ready, awaiting script wire-up)

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
companion script (TODO: `scripts/docs_cleanup.py`) owns the mechanical
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

### Mode: followups (DRAFT — recipe ready)

After a campaign closes, the campaign's `99-risk-sweep.md` (build mode)
or `99-synthesis.md` (audit mode) typically lists 5–10 deferred
follow-up items. The 2026-05-28 solar-system doc-sync audit shipped 8
follow-ups; 5 doable autonomously + 3 needing user hands. Without a
codified pattern, these get handled ad-hoc (each as a one-shot turn)
or silently dropped. This mode codifies the sweep.

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
| **1.2.0** | 2026-05-28 | `consolidate` mode promoted from TODO → LIVE. Companion script `scripts/consolidate_cleanup.py` ships with four subcommands: `detect` (find cross-locale safe-to-merge groups + show whether `common.json` already has a target), `map-callsites` (AST-aware resolution — parses `useTranslations()` bindings + tracks which `t` variable maps to which namespace, then resolves every `t-call` to its full key), `apply` (two-phase — delete dead keys first then rewrite callsites + delete live keys), `verify` (re-run safe-to-merge detector + JSON parse check). Three lessons codified from the first execution: (1) the naive Explore-agent approach reports false "0 callsites" — only AST-aware Python parses correctly; (2) suffix grep over-matches dramatically (`'status_label'` matches dozens of unrelated keys) — full-key + namespace-aware resolution required; (3) two-component-per-file files can have `tc` bound in only one component → tsc catches this as `Cannot find name 'tc'`; fix by adding the binding manually. Default surgical policy documented (universal UI labels only: Status/Type/Description/Date/Yes/No + Save/Close/Delete/Download + language names); entity nouns and context-bound headers stay separate. First execution baseline: surgical set of 62 doomed keys → 16 dead (auto-deleted) + 58 live callsites rewritten across 37 files; total JSON entries removed: 372 (62 × 6 locales); total keys per locale: 5,650 → 5,601; safe-to-merge groups: 164 → 150. Step 0 routing table + trigger-phrases list updated; description field now lists `consolidate` as LIVE. |
| **1.1.0** | 2026-05-28 | Lessons extracted from same-day solar-system doc-sync audit + 8-item follow-up sweep ([[2026-05-28_solar-system-doc-sync]], [[2026-05-28_solar-system-doc-sync-followups]], [[2026-05-28_storage-rls-bucket-matrix-helper]], [[2026-05-28_edge-fn-tombstone-cleanup]]). **`docs` mode** promoted from TODO → DRAFT with a 10-step concrete recipe (frontmatter sync, wikilink rot, orphan vault-logs, retired-name registry sweep, post-rename narrative-artifact detection, in-progress campaign drift). **`followups` mode** added as new DRAFT — codifies the post-campaign sweep pattern (locate → extract items → classify doable/needs-hands/exception → parallel execute → vault-log). New §Lessons learned section (L1–L8) covers cross-mode architecture: MCP-out-of-reach taxonomy, behavior-parity verification, post-rename artifact patterns, look-alike-but-different trap (the RLS-bucket-matrix discovery — 4 hard-coded arrays looked redundant but encoded distinct per-CMD access tiers), PostToolUse hook race conditions on batch Edits, same-session continuation markers (`/goal`, "finish the rest", "i am done"), vault-log size threshold, periodic-grep-after-rename-campaign discipline. Workflow Step 0 routing table updated; trigger-phrases list extended; Modes table refreshed (language LIVE / docs DRAFT / followups DRAFT / consolidate TODO). No script-side changes — `docs` + `followups` recipes are ready for the next person to wire up `scripts/docs_cleanup.py` and `scripts/followups_cleanup.py`. |
| **1.0.0** | 2026-05-28 | Initial release. `language` mode live — detects untranslated keys (locale value == EN), spawns 5 parallel locale subagents (AR/ES/FR/RU/ZH), applies translations back to `messages/{loc}/{ns}.json`, verifies. `docs` and `consolidate` modes stubbed for future. First execution baseline: 1,032 → 585 (−447 strings actually translated, remaining 585 = floor of brand acronyms + form placeholders + valid ES/FR cognates). |

## Related

- [[2026-05-28_languages-panel-cross-locale-stats]] — vault log for
  the Languages panel work that surfaced the original count.
- [[2026-05-28_translation-pass-non-en-locales]] — vault log for the
  first execution of this skill's `language` mode.
- `vault-log-compliance` skill — delegated to in Step L5.
- Brand glossary lives in
  `~/.claude/skills/cleanup/scripts/i18n_cleanup.py:BRAND_OR_CODE`.
