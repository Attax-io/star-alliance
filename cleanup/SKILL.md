---
name: cleanup
description: "Multi-mode hygiene skill for Lex Council. Modes — language (i18n translations); consolidate (i18n key dedup); hardcoded (extract raw UI text to next-intl keys); leaks (i18n keys USED in code but ABSENT from JSON → render as raw key-paths); errors (dev log sweep); postgres (Supabase advisors + pg health); lint (ESLint --fix + tsc); consolidate-code (duplicate component/RLS/constant detection); bundle (Cloudflare/OpenNext Worker size-wall hygiene); release (version bump + hygiene gate); docs (frontmatter/wikilinks/orphans); followups (deferred items). Run all at once via scripts/run_all.py. Triggers: \"run cleanup\", \"/cleanup\", \"i18n cleanup\", \"translate untranslated\", \"find hardcoded text\", \"find leaking keys\", \"raw key paths\", \"fix dev errors\", \"check postgres\", \"run lint\", \"consolidate code\", \"check the bundle size\", \"doc cleanup\", \"finish followups\", \"bump the version\", \"release X.Y.Z\", or any hygiene sweep after a campaign. Full mode recipes in references/."
metadata:
  version: 1.14.1
---

# Cleanup — Lex Council hygiene sweeps (v1.14.1)

This skill packages the operational recipes for periodic cleanup passes that
the app accumulates between feature builds. Each mode is independent; the
skill body routes to the right workflow based on what the user asked for.

> **Full mode recipes live in `references/`** — each mode section below
> has a one-liner + a `Read` pointer. The landmine lessons are in
> `references/landmines.md`. This stub fits within the Cowork installer
> word limit; verbose content is loaded on-demand.

## Modes

| Mode | Status | What it does |
|---|---|---|
| **language** | LIVE | Sweep every non-EN locale (ar/es/fr/ru/zh), find keys still equal to the English value, translate them in parallel via 5 subagents, write back, verify. |
| **consolidate** | LIVE | Detect cross-locale safe-to-merge i18n groups, pick surgical universal labels (Status / Type / Yes / etc.), AST-aware callsite mapping, two-phase apply (dead keys first then live rewrites), delete now-orphan keys. Script: `scripts/consolidate_cleanup.py`. |
| **errors** | LIVE | Parse `/tmp/lex-dev.log` (tee'd `npx turbo dev` stdout + DevErrorSink browser payloads), dedupe by error-signature, classify each unique entry as code-bug / framework-noise / external / unknown. Surface a per-error triage list; auto-fix unambiguous code-bugs. Script: `scripts/errors_cleanup.py`. |
| **postgres** | LIVE | Run Supabase `get_advisors` MCP + pg health queries; classify as advisory-auto-fix / advisory-surface / schema-campaign / noise. Auto-apply additive migrations for missing FK indexes. Flag RLS/schema issues as requiring a campaign. Script: `scripts/postgres_cleanup.py`. |
| **lint** | LIVE | Run ESLint, classify as auto-fixable / architectural / wip-noise. Auto-run `eslint --fix` for safe rules, run `tsc`, surface architectural violations as campaign candidates. Script: `scripts/lint_cleanup.py`. |
| **consolidate-code** | LIVE | Scan for duplicate/copy-pasted CODE → refresh `CONSOLIDATION-CANDIDATES.md` → classify T1 extract-now / T2 needs-campaign / T3 resolved → extract T1, surface T2. Byte-compare before merging. Script: `scripts/consolidate_code.py`. |
| **release** | LIVE | App-upgrade gate + version bump. Phase 1 — hygiene gate: lint + errors + postgres + Cloudflare/OpenNext bundle wall + Next.js 16 hazard probes → green/red verdict. Phase 2 (only if green) — full bump: `app.config.ts` + changelog + doc-stamp sync + git block. Full recipe in `references/release-procedure.md`. Gate-only via `/cleanup release --gate`. |
| **docs** | LIVE | Sync stale frontmatter dates + counts on planet hubs; flag broken wikilinks + archived-pointers; find orphan vault-logs; bump app version stamp in Vault Core; grep for retired-primitive names; detect post-rename narrative artifacts. Script: `scripts/docs_cleanup.py`. |
| **followups** | LIVE | After a campaign closes, sweep vault-logs + risk-sweep files for deferred items. Classify as doable-autonomously / needs-user-hands / accepted-permanent-exception. Execute doable ones in parallel; surface the rest. Script: `scripts/followups_cleanup.py`. |
| **hardcoded** | LIVE | Find raw hardcoded user-facing English text still in components (.tsx/.ts) and extract it to next-intl `t()` keys — the gap `language` (translates existing keys) / `consolidate` (dedups keys) never covered. Script: `scripts/i18n_extract.py` (detect/merge/propagate/verify); recipe `references/mode-hardcoded.md`. Scales 1-file → one-agent-per-file fan-out → `/conquering-campaign`. |
| **leaks** | LIVE | The INVERSE of `hardcoded`: keys USED in code (`t('ns.key')`) but ABSENT from the locale JSON → render as the raw uppercased key-path (next-intl `getMessageFallback`) in the UI. `scripts/i18n_extract.py leaks` resolves every static `t()` key app-wide (matches `useTranslations` **and** `getTranslations`/`{namespace:}`), flags EN-absent (HIGH) + locale-parity (MED). Detect+surface only. The class that leaked the public Codex page twice. Recipe `references/mode-leaks.md`. |
| **bundle** | LIVE | Cloudflare/OpenNext **Worker size-wall** hygiene. `detect` (static, build-free) flags heavy client-only libs (`recharts`) imported OUTSIDE the `.body`+`dynamic({ssr:false})` convention so they leak into the SSR/Worker bundle (the class that failed the 1.7.60 deploy); `measure` (build-gated) gzips the built worker vs the 3 MiB free / 10 MiB paid wall. Feeds the `release` gate + `run_all`. Script: `scripts/bundle_cleanup.py`. Recipe `references/mode-bundle.md`. |

## When to invoke this skill

Trigger phrases (any of):

- `/cleanup` (slash invocation)
- "run cleanup", "do the cleanup pass"
- "clean up the languages", "language cleanup", "i18n cleanup"
- "translate the untranslated keys", "fill in translations", "translate the missing strings"
- "we shipped a new page — let's do the cleanup"
- "consolidate the duplicate translations", "merge safe-to-merge keys", "clear duplicates" → routes to `consolidate`
- "check the dev log", "sweep the dev errors", "what errors did i hit", "fix the dev errors", "/cleanup errors" → routes to `errors`
- "check postgres", "check the db health", "check supabase advisors", "fix the advisor issues", "/cleanup postgres" → routes to `postgres`
- "run lint", "fix the lint errors", "check eslint", "run eslint", "/cleanup lint" → routes to `lint`
- "find duplicate code", "what should we consolidate", "consolidation candidates", "/cleanup consolidate-code" → routes to `consolidate-code`
- "pre-release check", "ready to release", "bump the version", "update the app version", "release X.Y.Z", "ship a release", "make it 1.7.X", "/cleanup release" → routes to `release` (use `--gate` for gate-only)
- "sync the doc footers", "doc cleanup", "check the docs are fresh" → routes to `docs`
- "finish the followups", "close the followups", "sweep the campaign followups" → routes to `followups`
- "find hardcoded text", "extract hardcoded strings", "key-ify the hardcoded strings", "/cleanup hardcoded" → routes to `hardcoded`
- "find leaking keys", "missing translation keys", "keys showing as raw text", "raw key paths", "why is the UI showing the key name", "/cleanup leaks" → routes to `leaks`
- "check the bundle size", "is the app too big", "worker size limit", "trim the bundle", "the deploy failed on size", "/cleanup bundle" → routes to `bundle`

Skip when: user is mid-feature and work isn't ready; a cleanup pass ran today and nothing new was added; user is asking about something else ("clean up this component" = refactoring, not this skill).

## Workflow

### Step 0 — Pick the mode

Look at the user's phrasing. Default mode is `language` unless they explicitly named another. If unsure, ask before proceeding — the modes have very different blast radius.

| Phrasing | Mode |
|---|---|
| `/cleanup`, "run cleanup" (bare), "i18n cleanup", "language cleanup", "translate untranslated" | `language` |
| "consolidate the translations", "merge safe-to-merge keys", "clear duplicates", "/cleanup consolidate" | `consolidate` |
| "check the dev log", "sweep the dev errors", "fix the dev errors", "/cleanup errors" | `errors` |
| "check postgres", "check the db health", "check supabase advisors", "/cleanup postgres" | `postgres` |
| "run lint", "fix the lint errors", "check eslint", "/cleanup lint" | `lint` |
| "find duplicate code", "consolidation candidates", "/cleanup consolidate-code" | `consolidate-code` |
| "pre-release check", "bump the version", "release X.Y.Z", "make it 1.7.X", "/cleanup release" | `release` (add `--gate` for gate-only) |
| "sync the doc footers", "doc cleanup", "/cleanup docs" | `docs` |
| "finish the followups", "close the followups", "/cleanup followups" | `followups` |
| "find hardcoded text", "extract hardcoded strings", "key-ify the hardcoded strings", "/cleanup hardcoded" | `hardcoded` |
| "find leaking keys", "missing translation keys", "raw key paths", "/cleanup leaks" | `leaks` |
| "check the bundle size", "worker size limit", "the deploy failed on size", "/cleanup bundle" | `bundle` |
| "run all cleanups", "/cleanup all", "what's drifted" | run `python3 ~/.claude/skills/cleanup/scripts/run_all.py run [--fast]` — runs local hygiene modes detect-only, writes severity-ranked `/tmp/cleanup_triage.md` + per-mode last-run age |

If the user's phrasing matches more than one mode (e.g. "run cleanup after that campaign"), prefer `followups` over `docs` — the post-campaign sweep is more specific.

### Step CL — Closeout: app patch bump (every mode, binding)

Every cleanup session that **applies at least one change** bumps the app
version's last segment by 1 (e.g. `1.7.26 → 1.7.27`) — no matter how big or
small the sweep. This is a deliberate always-on counter so every hygiene pass
is traceable to a version.

At closeout — after the mode's edits have landed and verification (tsc/lint, or
the mode's own checks) is green, alongside the vault log — run **once**:

```sh
python3 ~/.claude/skills/cleanup/scripts/bump_app_patch.py bump
```

It increments the PATCH segment in **both** `apps/web/config/app.config.ts`
(canonical `APP_CONFIG.version`) and `apps/web/package.json` (mirror), keeps them
in sync, and prints `old → new`. Stage both edited files in the **same commit**
as the cleanup, and name the new version in the vault log + commit message.

Rules:
- **Exactly once per session**, even when several modes ran (e.g. `run all cleanups` then a couple of applies) — one session = one patch bump.
- **Skip when the session applied no changes** — a pure detect-only / dry-run sweep does not bump (`run_all.py` detect, any `*_cleanup.py detect`, `/cleanup release --gate`, `--dry`, or a "nothing to clean" result).
- **`release` mode does NOT call this** — it performs its own full version bump (possibly minor/major) per `references/release-procedure.md`. Never double-bump in a release session.
- Drift guard: if the two version literals already disagree the script refuses (exit 3) — run `/cleanup release` to reconcile, then proceed.

### Mode: language

Read `references/mode-language.md` for the full recipe (Steps L1–L5: detect scope, spawn 5 parallel translation agents, pre-flight + apply, verify, vault log). That file also contains the brand glossary, locale contracts, agent prompt templates, and per-locale fill tables needed to construct the subagent prompts.

### Mode: hardcoded

Read `references/mode-hardcoded.md` for the full recipe (Steps H1–H8: detect candidates + reuse-map + briefs, extract scoped-inline-or-fan-out, single-writer merge + reuse-existence check, propagate to 6 locales, translate via the `language` mode, verify t()-keys resolve + smart-quote scan, fix the 4 known fan-out failure modes, vault log). Finds + extracts raw hardcoded UI text to keys — the producer half that `language` (the translator) and `consolidate` (the deduper) lack.

### Mode: leaks

Read `references/mode-leaks.md` for the full recipe (Steps LK1–LK3: detect via `i18n_extract.py leaks` — resolve every static `t()` key app-wide, classify EN-absent HIGH / locale-absent MED; mint the EN value (never auto-added) + propagate/translate; verify + log). The INVERSE of `hardcoded` and the blind spot of `language` — keys used in code but absent from the JSON render as raw key-paths in the UI.

### Mode: docs

Read `references/mode-docs.md` for the full recipe (Steps D1–D10: planet hub inventory, frontmatter sweep, ground-truth count probes, wikilink rot sweep, orphan vault-logs, retired-name registry, post-rename narrative artifacts, in-progress campaign drift, findings file, apply + vault log).

### Mode: followups

Read `references/mode-followups.md` for the full recipe (Steps F1–F6: locate the campaign, extract follow-up items, classify each item, parallel execution of doable items, vault log per surface, mark the cleanup marker).

> **Auto-spawned by `conquering-campaign` at campaign close** (its v3.3.0 §5.7 calls `spawn_task` → a fresh session runs `/cleanup followups` with the campaign's `99-risk-sweep.md` ## Open items inlined). If the spawn was skipped or dismissed, the committed risk-sweep is the durable fallback.

### Mode: consolidate

Read `references/mode-consolidate.md` for the full recipe (Steps C1–C8: detect safe-to-merge candidates, pick the surgical set, verify target keys, map callsites AST-aware, apply two-phase, verify, vault log, memory update).

**Why this is the riskiest mode:** unlike `language` (JSON-only) or `docs` (docs-only), consolidate touches TSX/TS source — a missed callsite produces a `MISSING_MESSAGE` runtime error in production.

### Mode: errors

Read `references/mode-errors.md` for the full recipe (Steps E0–E7: pre-flight, detect, classify, surface triage list, auto-fix rubric, verify, mark, vault log).

### Mode: postgres

Read `references/mode-postgres.md` for the full recipe (Steps PG0–PG6: pre-flight, detect with MCP advisors + health SQL, classify, apply auto-fix, verify, surface schema-campaign items, vault log). MCP project_id: `bqgrpnsvplvicnmzxwkm`.

### Mode: lint

Read `references/mode-lint.md` for the full recipe (Steps L0–L7: pre-flight, detect, classify, scoping, apply, verify, surface architectural violations, vault log).

### Mode: consolidate-code

Read `references/mode-consolidate-code.md` for the full recipe (Steps CC1–CC5: refresh registry, classify T1/T2/T3, byte-compare hard rule, extract T1 + surface T2, vault log).

**Priority order:** C35 ghost-views (CRITICAL) → C1 PANEL_WIDTH ×44 (codemod) → C38 i18n dup groups → C28/C29 legacy `_js` views → C7/C8/C11 V9-container primitives → C23–C27 DB view/RLS merge → C30 admin_perms god-table (XL).

### Mode: bundle

Read `references/mode-bundle.md` for the full recipe: `detect` (static, build-free — flags heavy client-only libs imported outside the `.body`+`dynamic({ssr:false})` isolation convention; exit 2 on findings) + `measure` (build-gated — gzip `.open-next/worker.js` vs the 3 MiB free / 10 MiB paid wall; degrades-with-receipts when unbuilt or a stale placeholder). The `release` gate PR2 delegates its hard size check here; also wired into `run_all`.

### Mode: release

Read `references/mode-release.md` for the full gate recipe (Steps PR1–PR4: hygiene gate, release-specific hazard checks, doc-stamp staleness warning, gate verdict). Phase 2 (version bump) runs per `references/release-procedure.md`.

## Lessons learned (cross-mode architecture)

39 codified landmine lessons (L1–L39) covering MCP reachability taxonomy, behavior-parity verification, post-rename artifacts, look-alike-but-different trap, PostToolUse race conditions, continuation markers, vault-log size thresholds, `security_invoker` silent-drop, postgres multi-pass discipline, lint baseline noise, `no-unused-expressions` architectural status, hex literal grep, ThemeToggle/StrictMode noise, stale trigger bodies, i18n namespace scope trap, release-time failure cluster, byte-compare before merge, dev-server session survival, skill version-sync drift, language count-semantics (verify vs detect + absent-key blindness), exact-JSON-writer churn, concurrent-actor commit scoping, offline-MCP degrade-with-receipts, zero-edit no-bump, scanner self-reference, advisor accepted-by-convention netting, mutation-module error-codes-not-strings (L32), ternary/nullish-fallback literal escape (L33), campaign locale-parity gaps (L34), single-word-label domain specificity (L35), orphaned-INDEX vault-logs (L36), followups over-tagging environmental items (L37), used-but-absent key leaks (L38), and heavy-lib Worker-wall busting (L39).

> **Read `references/landmines.md`** before any cleanup pass that touches DB schema, consolidation, or release.

Lessons also wired into scripts: L9/L10/L15/L17 → `postgres_cleanup.py`; L11 + L19 → `lint_cleanup.py`; L14 → `errors_cleanup.py`; L16 → `i18n_cleanup.py`; L27 → `commit_scope.py` (v1.10.0); L33 → `i18n_extract.py detect` (`expr` context, v1.12.0); L34/L36/L37 → `followups_cleanup.py` (`parity` / `orphan-index` / classifier guard, v1.12.0); L38 → `i18n_extract.py leaks` (v1.13.0); L39 → `bundle_cleanup.py` (v1.14.0).

## Why this skill exists

The Languages dev-tools panel shows a "Not fully translated" counter that grows every time a new page ships without i18n keys translated into the 5 non-EN locales. Without periodic cleanup, the counter only grows — manually filling 1000+ strings across 5 locales is perpetually deferred. This skill makes it a one-command pass: `/cleanup` → 5 agents in parallel → done in ~5 minutes wall-clock.

Empirical baseline from 2026-05-28 first run:
- Before: 1,032 (ar 143, es 206, fr 340, ru 171, zh 172)
- After: 585 (ar 31, es 156, fr 280, ru 59, zh 59) — −447 actual translations; remaining 585 is the inherent floor (brand acronyms + form placeholders + valid cognates).

The broader motivation: cleanup drift (i18n gaps, dup keys, dev-log errors, postgres advisors, lint, consolidation candidates) should be swept automatically, not re-discovered by hand each time. This skill (+ its companion scripts) exists to economize that spend.

## Versioning

This skill carries a semantic version in its frontmatter (`version: X.Y.Z`) and at the top of the body heading. **Bump it whenever the skill is modified.** Contract:

- **PATCH (1.0.x)** — bugfix in the script, prompt-template wording tweak, brand-glossary addition, new tone example, doc clarification. No workflow change for the user.
- **MINOR (1.x.0)** — new mode goes live, new optional flag, new locale added, new decision point that doesn't break existing invocations. Backward-compatible.
- **MAJOR (x.0.0)** — workflow change that breaks existing invocations. Rare.

**On every bump:** (1) edit `version:` in frontmatter; (2) update `(vX.Y.Z)` tag in body heading; (3) prepend a row to §Changelog; (4) update §Modes table if a mode status changed.

## Changelog

| Version | Date | Summary |
|---|---|---|
| **1.14.1** | 2026-06-15 | **Cowork packaging (stub copy).** Trimmed the frontmatter description 1186 → 973 chars to satisfy the ≤1024-char limit (dropped redundant trigger phrases; the full set stays in §When to invoke). No behavioral/mode change → PATCH. (Repo stub copy only; the device monolith keeps its richer description.) |
| **1.14.0** | 2026-06-09 | **New `bundle` mode — Cloudflare/OpenNext Worker size-wall hygiene** (the class that failed the 1.7.60 deploy: members `CreditStatsBar` imported recharts directly into an SSR'd component). New `scripts/bundle_cleanup.py`: `detect` (static, build-free — direct-heavy-import / broken-isolation, exit 2) + `measure` (gzip `.open-next/worker.js` vs the 3 MiB free / 10 MiB paid wall, degrade-with-receipts). The `release` gate PR2 now delegates its hard size check to `bundle measure`; wired into `run_all` + router + Modes table + §L39. New mode → MINOR. |
| **1.13.0** | 2026-06-04 | **New `leaks` mode — detect i18n keys USED in code but ABSENT from the locale JSON** (render as raw key-paths; leaked the public Codex page twice). New `i18n_extract.py leaks`: resolves every STATIC `t()` key app-wide → `en_absent` (HIGH) + `locale_absent` (MED); matches BOTH `useTranslations` AND `getTranslations`/`{namespace:}` (the server-page gap that would have missed the Codex leak), skips template-literal keys (zero false positives). Wired into `run_all` + router + Modes table + §Mode: leaks (LK1–LK3) + §L38. New mode → MINOR. |
| **1.12.0** | 2026-06-04 | **Mechanized R12 + R13 — wired L33/L34/L36/L37 into their scripts.** R12: `i18n_extract.py detect` gains an `expr` candidate context (nullish-fallback + ternary-tail + `fail(`) closing the 57-file residual gap (L33). R13: `followups_cleanup.py` gains `parity` (per-locale key-presence, exit 2 on absent — L34) + `orphan-index` (disk-present/INDEX-absent vault-logs, own-log-only — L36) + an `ENVIRONMENTAL_KW` classifier guard (prod-vs-repo items → accepted-exception — L37). Backward-compatible → MINOR. |
| **1.11.1** | 2026-06-04 | §Lessons +L32–L37 — mined the June 3–4 sessions (app-wide `hardcoded` extraction + the parity/orphan follow-ups). Prose-only landmines; no script change → PATCH. |
| **1.11.0** | 2026-06-03 | **New `hardcoded` mode — find + extract raw hardcoded UI text to i18n keys** (the gap `language`/`consolidate` never covered: they translate/dedup existing keys; neither reads component source). New `scripts/i18n_extract.py` (detect/merge/propagate/verify) + `references/mode-hardcoded.md` (recipe H1–H8). detect harvests JSX/prop/toast literal candidates + reuse-maps against existing keys + emits per-file agent briefs; merge single-writer-merges agent key-maps into `en/<ns>.json` + reuse-existence check (catches mislabeled-reuse keys → runtime MISSING_MESSAGE); propagate fills all 6 locales (EN placeholder); verify asserts every t()-key resolves + flags smart-quote useTranslations (TS1127). #91-safe fan-out (1 agent/file → key-map → main single writer); scales 1-file → app-wide → `/conquering-campaign` for multi-session. Mined from the 2026-06-03 app-wide extraction (109 files / 372 keys / 393×5 translated). New mode → MINOR. |
| **1.10.0** | 2026-06-02 | **Lessons L25–L31 + route R10 mechanized (`scripts/commit_scope.py`).** Mined the heavy 2026-05-30→06-02 usage (4 followup sweeps + 2 run-all passes) into 7 new landmine lessons: language count-semantics (verify>detect, detect-blind-to-absent-keys, cognate floor, phantom MISSING_MESSAGE=stale dev cache) (L25), exact-JSON-writer minimal-diff (L26), concurrent-actor scoped commit (L27), offline-MCP/dead-dev-log degrade-with-receipts (L28), zero-edit no-bump/no-log (L29), scanner self-reference false positives (L30), advisor accepted-by-convention netting (L31). **R10 shipped** — `scripts/commit_scope.py` (`scan`/`buildcheck`/`emit`) partitions the co-mingled dirty tree so a followups commit stages only campaign-owned files (mechanizes L27); wired into mode-followups Step F5.5. Live-validated: 57 dirty files in `lex_council/`, isolated the 2 owned from 45 foreign + 12 daemon bumps. New script, backward-compatible → MINOR. |
| **1.9.0** | 2026-05-31 | **Two simultaneous MINOR additions.** (1) **Always-on app patch bump (every mode).** New closeout step (§Workflow Step CL): every cleanup session that applies ≥1 change bumps the app version's last segment by 1. New `scripts/bump_app_patch.py` (`show` / `bump [--dry]`) increments PATCH in BOTH `apps/web/config/app.config.ts` (canonical) and `apps/web/package.json` (mirror), keeps them in sync, refuses on drift (exit 3). Rules: once per session; skip on no-op/detect-only/dry-run/`--gate`; `release` mode excluded (does its own full bump — never double-bump). (2) **Reference extraction refactor (Cowork installer word-limit fix).** All 9 mode recipes + 24 landmine lessons extracted to `references/mode-*.md` + `references/landmines.md`. SKILL.md is now a slim routing stub (target < 3,000 words vs prior 15,000+). No behavioral change — all content preserved in reference files; `Read references/mode-X.md` at the top of each mode section. Cowork skill installer limit is ~10,000 words; prior 15,342-word file failed installation. |
| **1.8.1** | 2026-05-29 | `followups` is now auto-spawned by `conquering-campaign` at campaign close (its v3.3.0 §5.7 calls `spawn_task`). Doc note added; no script change. |
| **1.8.0** | 2026-05-29 | Tier-0 lesson-wiring + `run_all.py` orchestrator. Wired L9/L10/L15/L17 → `postgres_cleanup.py`; L11+L19 → `lint_cleanup.py`; L14 → `errors_cleanup.py`; L16 → `i18n_cleanup.py`. Three DRAFT modes (`docs`, `followups`, `consolidate-code`) promoted LIVE. 9 LIVE modes, 0 DRAFT. |
| **1.6.0** | 2026-05-29 | `release` mode goes LIVE — merged the retired `update-app-version` skill. Full bump recipe in `references/release-procedure.md`. |
| **1.5.0** | 2026-05-29 | Session-mining pass (146 sessions → 219 fresh findings). Two new DRAFT modes: `consolidate-code` + `pre-release`. L20–L24 added. `UPGRADE-ROUTES.md` + `CONSOLIDATION-CANDIDATES.md` added. |
| **1.4.0** | 2026-05-29 | `postgres` + `lint` modes go LIVE. L9–L19 lessons added from mining. |
| **1.3.0** | 2026-05-28 | `errors` mode goes LIVE. `scripts/errors_cleanup.py` + dev-error sink runtime shipped. |
| **1.2.0** | 2026-05-28 | `consolidate` mode promoted LIVE. `scripts/consolidate_cleanup.py` ships with AST-aware callsite resolution. |
| **1.1.0** | 2026-05-28 | L1–L8 lessons extracted from solar-system doc-sync audit. `docs` + `followups` modes added as DRAFT. |
| **1.0.0** | 2026-05-28 | Initial release. `language` mode live. First run: 1,032 → 585 (−447 strings). |

## Related

- `UPGRADE-ROUTES.md` — skill roadmap; 10 ranked growth routes (R1–R10; R1–R7 + R10 done).
- `CONSOLIDATION-CANDIDATES.md` — 41 open consolidation candidates (FE/config/DB/i18n, 3 tiers).
- `references/release-procedure.md` — full version-bump recipe (Phase 2 of release mode).
- `references/mode-language.md` — language mode recipe + brand glossary + locale contracts + agent prompt templates.
- `references/mode-docs.md` — docs mode recipe.
- `references/mode-followups.md` — followups mode recipe.
- `references/mode-consolidate.md` — consolidate mode recipe.
- `references/mode-errors.md` — errors mode recipe.
- `references/mode-postgres.md` — postgres mode recipe.
- `references/mode-lint.md` — lint mode recipe.
- `references/mode-consolidate-code.md` — consolidate-code mode recipe.
- `references/mode-release.md` — release mode gate recipe (Phase 1).
- `references/mode-hardcoded.md` — hardcoded mode recipe (find + extract raw UI text to keys).
- `references/mode-leaks.md` — leaks mode recipe (used-but-absent i18n keys → raw key-paths).
- `references/mode-bundle.md` — bundle mode recipe (Cloudflare/OpenNext Worker size-wall hygiene).
- `scripts/i18n_extract.py` — hardcoded + leaks mode machinery (detect/merge/propagate/verify/leaks).
- `scripts/bundle_cleanup.py` — bundle mode machinery (detect/measure).
- `references/landmines.md` — L1–L39 cross-mode lessons.
- `scripts/commit_scope.py` — concurrent-actor commit-scoper (R10, §L27): scan/buildcheck/emit; never commits.
- [[2026-06-02_cleanup-skill-lessons-l25-l31]] — vault log for the L25–L31 + R10 (v1.10.0) upgrade.
- `vault-log-compliance` skill — delegated to in every mode's vault log step.
- [[2026-05-22_db-wide-consolidation-audit]] — 74-finding staged DB consolidation plan.
- [[2026-05-29_cleanup-skill-upgrade]] — vault log for v1.4.0 + v1.5.0 upgrades.
- [[2026-05-28_translation-pass-non-en-locales]] — vault log for first `language` mode execution.
