---
type: Document
timestamp: 2026-06-27T10:27:03Z
---

# Cleanup skill — upgrade notes (mined 2026-06-19)

**Baseline:** v1.16.0 (last upgrade 2026-06-17 ~11:37, added `manual` mode).
**Window mined:** every session 2026-06-17 11:37 → 2026-06-19 15:30 (~60 sessions: 8 cleanup-rotation runs + the RPC-thinning campaign, FileActionBar migration, 29-lock RPC audit, batch-task fix, news-wall build, marketing audit, codex/customs work).
**Method:** 3 parallel transcript readers over `~/.claude/projects/-Users-attaselim-…/*.jsonl`.

This file is the input to the next skill bump. Nothing here is applied yet.

---

## A. How the skill actually performed (rotation lessons)

Per-mode observed behavior this window:

| Mode | Observed | Verdict |
|---|---|---|
| `language` | Worked. 556 strings translated, detect 556→460. | Keep. |
| `hardcoded` | 800+ candidates, mostly noise; nibbles 6–12/run, ~288 files deferred forever. | **Never converges.** |
| `leaks` | 62 flags, **all false positive** (dynamic-prefix helper). | **Noise-only.** |
| `consolidate` | Worked but mapper falsely marked 3 server-component keys dead. | Keep + fix dead-key scan. |
| `lint` | Effectively always no-op; only "finding" was a regex false positive. | Mis-scoped regex. |
| `errors` | Structural no-op — needs `/tmp/lex-dev.log` that never exists in scheduled runs. | **Drop from autonomous rotation or self-provision the log.** |
| `consolidate-code` | This run: 2 dup-groups, both false/T2. Byte-compare gate held. | Detector over-flags (normalized hash). |
| `docs` | Re-flags the same baseline every run; can't clear its own red dates. | Needs watermark + escalation. |
| `manual` | DB layer solid (18 Parts, 90/90 translations fresh). EN drift caught only reactively. | Needs watermark + `.md`↔DB reconcile. |
| `postgres`/`bundle`/`followups` | Not exercised destructively this window. | — |

### Recurring friction (deduped)
1. **Background subagents are write-denied in the no-user scheduled context.** `mode-language` recipe spawns `run_in_background: true` translators — all failed silently, had to re-run foreground. → Patch every mode recipe that spawns *writing* subagents to force foreground when no user present.
2. **`rotate.py` path drift.** Runs repeatedly hit `can't open … ~/.claude/skills/cleanup/scripts/rotate.py` — real path is project-relative. → Make rotate.py resolve its own dir; fix routine prompt path.
3. **`timeout` not found on macOS** in a recipe. → Use `gtimeout` or drop it.
4. **Permission stalls** block unattended runs (bare `grep`/`mkdir` prompted). → Document exact allowlist or rely on bypass mode (already set).
5. **Detector false-positive classes** (each will recur every rotation until fixed):
   - `leaks`: blind to wrapper helpers / template-literal prefixes (`ic=(k)=>t(\`inheritance_calculator.${k}\`)`).
   - `consolidate`/`hardcoded` dead-key scan: blind to `getTranslations` server-component usage → would delete live keys.
   - `lint`/registry: substring regex (`VIEWS.map` matched `LINK_VIEWS.map`). Anchor to word boundaries.
   - `hardcoded`/`consolidate` `expr` bucket: includes `rgba(...)`, hex, single-token identifiers → 800+ phantom candidates. Pre-filter.
   - `consolidate-code` dup-function: normalized hash flags non-identical bodies (INDUSTRIES 12 vs 10 entries). Byte-compare gate is the only thing saving it.
6. **Concurrent-actor tree pollution** — another session edits the tree mid-run; `commit_scope.py` exact-path staging is load-bearing. Keep, never blanket-commit.

---

## B. New debt classes the skill does NOT catch (highest-value gaps)

The dominant new debt this period is **FE↔DB coupling registries that fail silently at runtime and survive tsc/lint.** Ranked by recurrence:

1. **`server-rpc-allowlist.ts` drift (≥6 sessions, highest stakes).** Every write routes `callServerRpc('x') → /api/rpc`, validated against a ~148-entry Set. Missing entry = silent 400. A vitest exists (`__tests__/server-rpc-allowlist.test.ts`) but no mode runs/asserts it. Also no check that each allowlist entry resolves to a live `pg_proc` (dead names `create_poa_office`, `create_tasks_batch` were allowlisted but absent).
2. **`view-registry.ts` invariant (W3) unenforced.** New view = +1 registry key + 1 hand row type, neither tsc-checked. No mode validates FE view-name literals against registry keys (or against the live DB).
3. **Write-RPC gate-predicate divergence (the 29-lock audit).** `tx_file_visible` drops `has_vap`; `create_folder` lacks parent-visibility; generic `soft_delete_row`/`restore_row` have no branch scope; some `private.*` SECURITY DEFINER fns miss `REVOKE … FROM anon`; some public wrappers skip the `auth.uid()` null-check. `postgres` mode catches generic advisors, not family-divergence.
4. **Anon-SEO source probe.** sitemap/RSS/feed/`generateMetadata` must read an anon-granted SECURITY DEFINER RPC, else empty feed (the "sitemap-killer trap", repeat of the `clients_articles_list` leak). No mode asserts this with a `SET LOCAL ROLE anon` row-count probe.
5. **View-column ↔ FE-mapper contract drift.** Mapper hardcodes `undefined` for a column the source view omits (`isFlagged: undefined`). tsc-valid, invisible. Hit in Points + Balances.
6. **Public-bundle i18n scoping.** Public layout loads all 11 namespaces (~250KB incl. admin.json) to every ad-landing visitor — no `pick()`. Plus single-locale metadata fields (`subject_ar` in `<title>`/OG on every locale).
7. **Near-dup components beyond byte-identical** (3 copies of one file-row action bar) + orphan manifest/comment refs to deleted files. `consolidate-code` only merges byte-identical.
8. **Stale retired-view-names in code comments** (`fd_cf_js`, `articles_s_js`) — `docs` mode does wikilinks, not stale-symbol-in-comments.

**Recommendation:** add a single new **`contracts` mode** (or fold 1–5 into existing modes) that asserts the FE↔DB registries. Highest-priority single addition = the allowlist two-direction + live-`pg_proc` check.

---

## C. Docs + Manual freshness loop (explicit user requirement)

> "The skill must also loop over the docs and user manual to keep them up to date."

Both `docs` and `manual` are **already** rotation modes — cadence is fine. The problem is **thoroughness + escalation**, not frequency. Required upgrades:

**Deterministic halves work, keep them:** manual translation staleness (`source_md_hash <> md5(body_md)`, currently 0 stale / 0 missing across 90 translations) and Vault Core version-stamp auto-sync.

**Gaps to close:**
- **G1 — `docs/user-manual/*.md` ↔ DB divergence is unmanaged (top gap).** EN canonical lives in `user_manual_pages.body_md` (edited via MCP); the 18 authoring `.md` files are never reconciled. Proven live: `docs/user-manual/12-admin-finances.md` still says "Pool Inflow (90%)" with a GAP marker the DB Part 13 already resolved. → Add `.md`↔DB hash-diff to `manual`, OR declare the `.md` set dead/tombstone.
- **G2/G5 — reactive-only EN drift + no escalation.** Step-3 content drift only fired because the feature task pointed at it. The documented "≥3 large vault-logs → spawn audit campaign" rule is not mechanized. → drive both off a watermark (below) and `spawn_task` a `/conquering-campaign` AUDIT automatically when the threshold trips.
- **G3 — `manual` absent from `run_all.py` and the `release` gate.** mode-manual prescribes a release-gate staleness probe that was never wired. → add the cheap Step-1 `execute_sql` probe to both.
- **G4 — hub `last_full_audit` dates perpetually red (stuck 2026-05-28), docs mode can't clear them.** → add a separate `counts_verified_by_cleanup: <date>` stamp so a clean count-probe clears the recurring flag without claiming a full audit happened.
- **G6 — `docs/logs/INDEX.md` release-row drift** (says 1.7.84, config is 1.7.87; rows for .85/.86/.87 missing). → docs mode should verify every shipped version has a log row, not just the Vault Core stamp.
- **G7 — hard-coded inventories.** docs D1 8-hub list misses existing hubs (`FINANCIAL-MODEL.md`, `RLS-BUNDLES.md`); a new manual Part escapes coverage. → self-discover via glob/registry.
- **G8 — no feature→doc-section coverage check** (parallel to manual Step-3). vault-log "Files Changed" paths ↔ hub section anchors.

**Single new primitive that fixes most of it — per-mode watermark files** (mirror `rotate.py`'s cursor):
`.claude/cleanup-docs-state.json` and `.claude/cleanup-manual-state.json`, each recording `last_pass_date` + `last_seen_vault_log`. Every docs/manual rotation run diffs vault-logs added since the watermark, drives the EN-drift heuristic and the auto-escalation trigger off it, and updates it on completion. Converts both modes from "re-flag the same baseline" to "act on what changed since I last looked" — the one change that makes docs+manual track feature velocity.

| Staleness signal | Source | Wired today? |
|---|---|---|
| Manual translation staleness | `source_md_hash <> md5(body_md)` per locale | ✅ |
| Manual EN content drift | vault-logs since watermark × Part route tokens | ⚠️ reactive |
| Manual authoring-source drift | `md5(docs/user-manual/NN-*.md)` vs DB `body_md` | ❌ (G1) |
| App version stamp | `app.config.ts` (1.7.87) + package.json | ⚠️ Vault Core only (G6) |
| Vault-logs since last docs pass | watermark diff | ❌ no watermark |
| Hub count ground truth | find/ls/PERM_META + MCP `information_schema` | ✅ (D3) |
| Feature surface vs hub coverage | vault-log paths ↔ hub anchors | ❌ (G8) |
| Manual locale parity | `pages × {ar,es,fr,ru,zh}` LEFT JOIN | ✅ |

---

## D. Proposed upgrade route (ranked for the next bump)

1. ✅ **DONE (v1.17.0)** — **Fix the false-positive detectors** (`leaks` dynamic-prefix backtick wrapper, `lint`/registry word-boundary, dead-key `await getTranslations`/object-ns server-component awareness, `expr` CSS/hex/dimension pre-filter, `consolidate-code` array/object-literal guard + `byte_identical` flag). Cheapest, stops chronic noise/no-ops.
2. ✅ **DONE (v1.17.0)** — **Watermark primitive** for `docs` + `manual` (`watermark.py` + `cleanup-docs-state.json`/`cleanup-manual-state.json` + vault-log diff + escalation; wired into both recipes). Closes G2/G5; partial G4 (hub-list G7 also widened).
3. ⏳ **`contracts` checks** — allowlist two-direction + live-`pg_proc`; view-registry invariant; view-column↔mapper contract. Catches the dominant silent-runtime debt class. (needs MCP)
4. ⏳ **Manual `.md`↔DB reconcile (G1)** + wire `manual` into `run_all.py` and the `release` gate (G3).
5. ✅ **DONE (v1.17.0)** — **Scheduled-context hardening** — foreground writing subagents when unattended (language/hardcoded recipes); `~/.claude/skills/cleanup` symlinked so routine paths resolve; `errors` mode explicit unattended no-op (no server auto-start). (`timeout` cmd: not actually present in any recipe — no fix needed.)
6. ⏳ **Extend `postgres`** with write-RPC gate-divergence + anon-SEO row-count probe (29-lock + sitemap-killer classes). (needs MCP)
7. ⏳ **Self-discovering inventories** (G7) for hubs + manual Parts; stale-view-name-in-comment sweep (extend `docs`). (docs hub-list widened in v1.17.0; full glob-discovery still TODO)

Items 1, 2, 5 (mechanical, high-leverage) shipped in v1.17.0. Items 3, 6 need MCP and are the biggest remaining correctness win.
