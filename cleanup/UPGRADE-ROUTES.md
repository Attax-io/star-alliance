# Cleanup skill — upgrade routes

Checkup of `cleanup` v1.9.1. Maps every place the skill can still grow, ranked by
value × effort. Companion to SKILL.md §Versioning. Re-read this before the next upgrade
pass so routes aren't re-derived from scratch.

**Current state (v1.11.0):** 10 LIVE modes (added `hardcoded` — i18n extraction, R11) + a `run_all.py` orchestrator (R7) + a `commit_scope.py`
helper (R10) + an always-on app patch bump on every change-applying sweep (v1.9.0). 0 DRAFT.
**R1–R7 + R10 all DONE.** 8 codified lessons (L9/L10/L11/L14/L15/L16/L17/L19 + **L27 → `commit_scope.py`**)
wired into their scripts; cross-machine `default_root()` portability across all scripts. **31 cross-mode
lessons (L1–L31)** — L25–L31 added 2026-06-02 from mining the heavy 2026-05-30→06-02 usage; L27 now
mechanized (R10), L25/L26/L28–L31 still prose-only.
**Open routes: R8 (dead-code mode), R9 (`--since` incremental).** R11 (i18n extraction) DONE v1.11.0.

---

## Route table (ranked)

| # | Route | Type | Value | Effort | Blocker |
|---|---|---|---|---|---|
| ~~R1~~ | `consolidate-code` mode | **DONE (v1.7.0)** | — | — | LIVE — `scripts/consolidate_code.py` (scan/classify/surface/extract) |
| ~~R2~~ | ~~`app-upgrade` mode~~ | **DONE (v1.6.0)** | — | — | RESOLVED — merged `update-app-version` INTO cleanup as the `release` mode (user chose merge over the recommended hand-off) |
| ~~R3~~ | `docs` mode → LIVE | **DONE (v1.7.0)** | — | — | LIVE — `scripts/docs_cleanup.py` |
| ~~R4~~ | `postgres` supplementary queries | **DONE (v1.8.0)** | — | — | L9/L10/L15/L17 baked into `postgres_cleanup.py detect` + classify |
| ~~R5~~ | `lint` baseline-delta + view-registry | **DONE (v1.8.0)** | — | — | `baseline` subcommand + VIEWS↔registry cross-check in `lint_cleanup.py` |
| ~~R6~~ | `followups` mode → LIVE | **DONE (v1.7.0)** | — | — | LIVE — `scripts/followups_cleanup.py` |
| ~~R7~~ | `run all cleanups` orchestrator | **DONE (v1.8.0)** | — | — | `scripts/run_all.py` — runs local modes + ranked `/tmp/cleanup_triage.md` |
| R8 | `dead-code` / orphan-sweep mode | new mode | MED | M | ts-prune/knip integration |
| R9 | cross-mode `--since` incremental | enhance all | LOW | S | per-mode offset markers |
| ~~R10~~ | concurrent-actor commit-scoper | **DONE (v1.10.0)** | — | — | LIVE — `scripts/commit_scope.py` (scan/buildcheck/emit), wired into followups Step F5.5 |
| ~~R11~~ | `hardcoded` i18n-extraction mode | **DONE (v1.11.0)** | — | — | LIVE — `scripts/i18n_extract.py` (detect/merge/propagate/verify) + `references/mode-hardcoded.md`; find raw hardcoded UI text → keys → translate via `language` |

---

## R1 — `consolidate` code-side (the user's "unconsolidated instances" ask)

> **✅ DONE 2026-05-29 (v1.7.0).** Shipped as the LIVE `consolidate-code` mode — `scripts/consolidate_code.py`. Live scan: PANEL_WIDTH×45, PAGE_SIZE_OPTIONS×2, 119 off-token hex, 3 dup-function groups. `extract` dry-run only (byte-compare hard rule). Analysis below kept as the build record.

**Current:** `consolidate` mode is i18n-only (folds duplicate translation keys). SKILL.md §Modes
already notes the unbuilt extension: *"Also future: code-side consolidation — surface 3+
near-duplicate hard-coded literals for refactor-with-helper."*

**Target:** a `consolidate code` sub-mode (or new `consolidate-code` mode) that scans for and
surfaces — then optionally extracts — these recurring duplication shapes:

| Shape | Detection | Example from sessions |
|---|---|---|
| Copy-pasted functions across files | AST hash of function body; flag N≥2 identical | `mapAuthError` × 4 auth pages |
| Inline pattern repeated N≥3× | grep + structural match | 6 inline KPI strip implementations |
| Near-duplicate DB views | normalize SELECT, diff only WHERE | 7 transaction views, 3 advance views |
| Duplicated RLS predicates | `pg_policies.qual` text-hash across tables | admin-check inlined across 9–12 policies |
| Config defined in multiple places | grep for the literal/default | page-size default in 2 components + 1 useState |
| Orphan code (0 consumers) | grep callsites = 0 | 11 orphan views in one audit; dead style-constants |
| Two competing mechanisms | manual pairing flag | old prop-flow + new shell-flow modal |

**Output:** a `CONSOLIDATION-CANDIDATES.md` registry (the format this campaign produced) +
a per-candidate classification: `extract-now` (≤3 files, mechanical) / `needs-campaign`
(cross-cutting, behavior-parity risk per §L2) / `accepted` (intentional divergence).

**Hard rule (from §L2 + §L4):** never merge N near-duplicate literals into one helper without
byte-comparing them first. Look-alike-but-different (the RLS bucket-matrix trap) silently widens
access. Only consolidate when all N are byte-identical OR the helper preserves every difference.

**Script:** `scripts/consolidate_code.py` — subcommands `scan` (produce candidate registry),
`classify`, `extract` (only `extract-now` tier).

---

## R2 — `app-upgrade` mode (the user's "upgrading the app" ask)

> **✅ RESOLVED 2026-05-29 (cleanup v1.6.0).** The user chose to **merge** `update-app-version` into
> cleanup rather than the recommended hand-off (b) below. `pre-release` (DRAFT gate) was promoted to a
> unified two-phase `release` mode: Phase 1 hygiene gate (steps 1–3 below) + Phase 2 full version bump
> (steps 4–7), with the bump recipe in `references/release-procedure.md`. The standalone
> `skills/update-app-version/` was deleted. The analysis below is kept as the record of the decision.

**Current:** No mode. App upgrades happen via the `update-app-version` skill +
`docs/VERSION-RELEASE-WORKFLOW.md`.

**Critical finding:** `VERSION-RELEASE-WORKFLOW.md` is **STALE**. Its doc-header-sync targets
predate the solar-system restructure:
- References `docs/logs/INDEX.md`, `docs/architecture/ARCHITECTURE.md`,
  `docs/architecture/frontend/ZUSTAND-STORES.md` — these paths are from the "2026-04-15 restructure"
- Current structure is `docs/vault-logs/`, BACKEND.md, FRONTEND.md, INTEGRATION.md, Vault Core.md
- App is at **1.7.25** now; the workflow examples still say `1.6.X`

**The cleanup-skill angle is PRE-RELEASE HYGIENE**, not the version bump itself. An `app-upgrade`
mode would orchestrate the pre-push gate:

1. Run `lint` mode (tsc + ESLint clean on touched files)
2. Run `errors` mode (dev-log triage — no unfixed code-bugs)
3. Run `postgres` mode advisory check (no new schema-campaign items introduced)
4. Bump `apps/web/config/app.config.ts` (last figure +1)
5. **Doc-header staleness check** — verify which docs actually carry version stamps NOW
   (the workflow's hard-coded list is wrong) and sync them
6. Generate version log
7. Memory tier-demotion review

**Decision needed:** the existing `update-app-version` skill already does steps 4–7. Either
(a) `app-upgrade` mode *delegates* to that skill after running the hygiene gate (steps 1–3), or
(b) the cleanup skill stays out of version-bumps entirely and just offers a `pre-release` mode
that runs steps 1–3 and hands off. **Recommend (b)** — don't duplicate the version-bump skill;
own only the hygiene gate.

**Side-fix:** whichever path, file a follow-up to reconcile `VERSION-RELEASE-WORKFLOW.md`'s
doc-header targets with the current solar-system hubs. The stale target list will silently
skip the real version stamps.

---

## R3 — `docs` mode → LIVE

> **✅ DONE 2026-05-29 (v1.7.0).** `scripts/docs_cleanup.py` shipped (frontmatter/wikilinks/orphans/retired-names/artifacts/campaign-drift/all, detect-only).

**Current:** DRAFT. Full 10-step recipe (D1–D10) already in SKILL.md. Needs the script.

**Target:** `scripts/docs_cleanup.py` with subcommands matching the recipe:
- `frontmatter` (D2 — stale date/count sync, ground-truth probes D3)
- `wikilinks` (D4 — broken-link + archived-pointer sweep)
- `orphans` (D5 — vault-logs missing from INDEX.md)
- `retired-names` (D6 — grep the hard-coded registry)
- `artifacts` (D7 — `X (v2; was X)` post-rename pattern)
- `campaign-drift` (D8 — in-progress plans with existing vault-logs)

Lowest-novelty route — the recipe is complete; it's a transcription job.

---

## R4 — `postgres` script: bake supplementary queries

> **✅ DONE 2026-05-29 (v1.8.0).** L9 (security_invoker), L10 (`qual='true'`), L15 (stale prosrc), L17 (dead service_role + rls-no-policy) baked into `postgres_cleanup.py detect` as emitted queries + classify rules (all → schema-campaign).

**Current:** `postgres_cleanup.py detect` reads `get_advisors` + 3 health queries. Lessons
L10/L15/L17 document 4 more queries that `get_advisors` MISSES but the script doesn't run:

1. `qual='true'` permissive RLS policies (L10)
2. stale `pg_proc.prosrc` bodies referencing v2-renamed tables (L15)
3. dead `auth.role()='service_role'` policies (L17)
4. orphan views (0 FE callsites) + near-duplicate views (R1 overlap)

**Target:** add these as additional health queries the `detect` phase emits into the same
`/tmp/pg_health.json`. Smallest-effort highest-value route — the SQL is already written in
the lessons; just wire it into the script's documented health-query set.

---

## R5 — `lint` script: baseline-delta + view-registry check

> **✅ DONE 2026-05-29 (v1.8.0).** `baseline` subcommand (new-on-touched vs pre-existing) + L19 view-registry cross-check (`VIEWS.<key>` usages vs `view-registry.ts` keys → missing = guaranteed TS2304) in `lint_cleanup.py`.

**Current:** `lint_cleanup.py` classifies but reports absolute counts. L11 says report DELTA
(new warnings on touched files vs pre-existing suppressed). L19 says TS2304 `Cannot find name
'VIEWS'` always = missing `view-registry.ts` key.

**Target:** add `baseline` subcommand (snapshot at session start) + a view-registry cross-check
in `detect`. Filter `.next/types/*.d 2.ts` duplicates from tsc output (L11 tail).

---

## R6 — `followups` mode → LIVE

> **✅ DONE 2026-05-29 (v1.7.0).** `scripts/followups_cleanup.py` shipped (locate/extract/classify/mark; execution stays Claude's job).

**Current:** DRAFT. Recipe F1–F6 complete. Needs `scripts/followups_cleanup.py`.

**Target:** locate most-recent closed campaign → extract deferred items → classify
(doable / needs-hands / accepted) → execute doable in parallel → vault-log. The classification
taxonomy (L1) is the load-bearing logic; the script is mostly orchestration.

---

## R7 — `run all cleanups` orchestrator

> **✅ DONE 2026-05-29 (v1.8.0).** `scripts/run_all.py` — `run` (re-run local modes + merge) / `report` (merge existing) / `--fast`. Writes a severity-ranked `/tmp/cleanup_triage.md` + per-mode last-run age. postgres (MCP) + apply-modes excluded. Unblocks R9 (`--since`).

**Current:** documented order (language → consolidate → errors → postgres → lint → docs →
followups) but no driver. Each mode is invoked manually.

**Target:** a thin orchestrator that runs LIVE modes in order, collects each mode's triage
output, produces one combined report. Natural pre-release gate (feeds R2). Skip DRAFT modes
silently until their scripts land.

---

## R8 — `dead-code` / orphan-sweep mode

**Current:** none. Orphan detection is scattered (postgres orphan views, lint unused style
constants, L13 orphan grep).

**Target:** unify symbolic dead-code detection — `ts-prune` / `knip` for TS dead exports +
the orphan-view SQL + unused-style-constant grep — into one mode. Deterministic tooling
outperforms LLM here (per conquering-campaign §0.5.1 4th skip reason).

---

## R9 — cross-mode `--since` incremental

**Current:** only `errors` mode has `--since` (offset marker). Others re-scan from scratch.

**Target:** per-mode offset markers (`/tmp/last_<mode>_cleanup_marker`) so a same-day second
run only sees new drift. Low value until the modes are run frequently.

---

## R10 — concurrent-actor commit-scoper (from §L27)

> **✅ DONE 2026-06-02 (v1.10.0).** Shipped as `scripts/commit_scope.py` (`scan`/`buildcheck`/`emit`,
> stdlib-only, `git` via subprocess) + wired into the followups mode as Step F5.5. Live-validated on its
> own build: 57 dirty files in `lex_council/` → 2 owned correctly isolated from 45 foreign + 12 daemon
> counter-bumps. The spec below is kept as the build record.

**Why now:** the followups sweep auto-spawned by `conquering-campaign` at campaign close (v1.8.1)
lands in a working tree that a *parallel* session is actively editing (FE source + DB + all-locale
i18n + docs-daemon counter bumps). Three of the four 2026-05-30→06-02 sweeps hit this: 35–119 dirty
files belonging to other workstreams sat next to the campaign's own. A naive `git add -A` commits
someone else's half-finished work and can break `main`. §L27 codifies the discipline; this route
mechanizes it so it isn't re-derived by hand each sweep.

**Target:** a `scripts/commit_scope.py` (or a `followups`/`run_all` subcommand) that, given a campaign
dir (or an explicit owned-file list), emits:

1. `git status --porcelain` → the full dirty set.
2. The **campaign-owned** subset = files named in the campaign plan / vault log / `git diff` of the
   campaign's own commits, MINUS the exclusion tells (docs `claude_hits:` counter-only diffs, barrel
   `index.ts` export adds you didn't author, `messages/*` from a parallel locale run).
3. A **buildability gate**: parse the staged files' imports; fail if any resolves to a still-dirty
   sibling (so the partial commit can't leave `main` un-buildable in isolation).
4. The exact `git add <list>` block for the human to run (never auto-commits — staging is the deliverable).

**Effort:** S — it's git porcelain + a shallow import-graph walk; the exclusion heuristics are already
written in §L27. Pairs naturally with wiring L25–L31 (the lessons are the spec).

**Caveat:** git lives **inside** `lex_council/` (submodule); the script must `cd` there, not the
workspace root (memory `discovery_lex-council-git-submodule`).

## Version-path guidance

- R4 + R5 (script enhancements, no new mode) → **PATCH** (1.4.x)
- R1, R2, R3, R6, R7, R8 (new mode or DRAFT→LIVE) → **MINOR** (1.x.0)
- Renaming/removing a mode or changing a script's subcommand contract → **MAJOR**

Ship script enhancements (R4/R5) as a quick patch; batch new-mode work (R1/R2) as minors.
