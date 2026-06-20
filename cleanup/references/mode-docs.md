# Mode: docs — full recipe

> **Script:** `python3 ~/.claude/skills/cleanup/scripts/docs_cleanup.py <frontmatter|wikilinks|orphans|retired-names|artifacts|campaign-drift|all>` — detect-only, never edits a docs file. The DB count-probes (D3) remain Claude's job via MCP.

A periodic hygiene sweep of the planet hubs. Lighter-weight than a full
audit campaign (`conquering-campaign` AUDIT mode) — runs the cheap
catch-all checks that surface drift without re-querying the entire DB.

#### Step D0 — Watermark: act on what changed, not the baseline

This mode used to re-flag the same broken-wikilink / stale-date baseline every
run because it had no memory of its last pass. Start with the watermark so the
run is driven by *new* feature activity:

```sh
python3 ~/.claude/skills/cleanup/scripts/watermark.py status docs   # exit 10 = escalate
```

- **Escalation (exit 10 / 🚩):** ≥3 vault-logs shipped since the last docs pass.
  The cheap catch-all checks won't reconcile that much drift — `spawn_task` a
  `/conquering-campaign` AUDIT for the docs surface (or, in interactive use, tell
  the user), then still run the cheap checks below for anything quick.
- **Nothing new (✓):** the hubs haven't fallen behind any shipped work — run the
  cheap checks (D1–D8) only if the frontmatter dates are themselves stale;
  otherwise this is a legitimate fast no-op.
- **A few new logs:** proceed with D1–D8 as normal, prioritizing the hub sections
  the new vault-logs touched (`watermark.py since docs` lists them).

**At the END of the run** (whether it applied fixes or was a no-op), stamp the
watermark so the next run diffs from here:

```sh
python3 ~/.claude/skills/cleanup/scripts/watermark.py advance docs          # did real work
python3 ~/.claude/skills/cleanup/scripts/watermark.py advance docs --noop   # no-op pass
```

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
DB-NAMING-OVERHAUL.md
FINANCIAL-MODEL.md
RLS-BUNDLES.md
```

> Better than a hard-coded list: `ls lex_council/docs/*.md` and treat every
> top-level `.md` as a candidate hub (the list above drifts as hubs are added —
> `FINANCIAL-MODEL.md` / `RLS-BUNDLES.md` existed unlisted for weeks). Glob first,
> then narrow to the ones with planet-hub frontmatter.

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

**Systemic threshold (same logic as D5).** When the broken-wikilink count is
**> 50**, the docs corpus has systemic link rot, not isolated typos. Stop
enumerating per-link; emit one systemic finding recommending a wholesale link
audit (often the same unmaintained-INDEX root cause as D5 — reconcile them into
a single systemic recommendation in the D9 summary rather than two walls of
per-item flags). Below 50, flag each broken link individually as above.

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

**Systemic vs. per-file — stop enumerating past the threshold.** When the
orphan count is **> 25 files OR > 20% of all vault-log files**, the INDEX is
*structurally* unmaintained — this is one systemic class, not N per-file misses.
Do **not** list 540 orphans and do **not** add entries to the INDEX one-by-one.
Emit a **single** systemic finding instead:

> `systemic: vault-log INDEX unmaintained — <N> orphans (<P>% of files).
>  Wholesale decision required: (a) regenerate INDEX.md from the file list
>  + per-file summaries, or (b) accept the unmaintained state and watermark
>  it so future runs stop re-flagging. NOT a per-file triage.`

A real session (2026-06-20) hit exactly this: ~540 orphans + ~1299 broken
wikilinks. Enumerating them is noise; the wholesale decision is the only
actionable output. Below the threshold (a handful of orphans), surface each
for triage as before — auto-fixing is risky (the entry's summary needs prose).

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

When D4/D5 cross their systemic thresholds, the per-hub lines collapse into a
single corpus-level systemic line at the top of the findings file:

```markdown
- **SYSTEMIC — vault-log INDEX unmaintained** — 540 orphans (82% of files) +
  1299 broken wikilinks. Wholesale decision required (regenerate INDEX or
  accept+watermark). Per-file orphan/link enumeration suppressed (noise).
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
