# Mode: leaks — full recipe

> ✅ **#303 DB-native (done 2026-06-21):** `public.app_translations` (DB) is the
> i18n source of truth. **Detection** still defaults to the committed JSON
> (offline-safe for `run_all`/rotation, no in-flight noise) — but now also offers
> `--db`, the **deploy-truth** check: it reads `app_translations` directly and
> flags every t()-key that would render as a raw key-path after the next build
> dump (DB → JSON), **including keys that sit in the committed JSON but were never
> pushed to the DB** (those vanish on the next dump). **Remediation** targets the
> DB: mint the EN value and add it to `app_translations` (admin Languages panel →
> `upsert_translation`, or seed the JSON + `push-translations.mjs --namespace
> <ns>`), then run the `language` mode to fill the non-EN cells — a hand-edit to
> the JSON alone is overwritten by the next build dump. See
> `docs/build-campaigns/2026-06-20_i18n-db-source-of-truth/`.

> **Script:** `python3 ~/.claude/skills/cleanup/scripts/i18n_extract.py leaks [--scope ...] [--db] [--out /tmp/i18n_leaks.json]` — detect-only; never edits a JSON or `.tsx`.

Find i18n keys USED in code (`t('ns.key')`) but ABSENT from the locale JSON. next-intl renders an absent key as its raw uppercased dotted path via `getMessageFallback` (e.g. `PUBLIC.CODEX.COL_TYPE`) — a visible UX break. The class neither `language` (only sees keys present-but-equal-to-EN — §L25/L34) nor `hardcoded` (finds literals NOT yet keyed) catches. It twice leaked the public Codex page (`codex.col_type` / `col_status` / `filter_status` absent from `public.json`).

#### Step LK1 — Detect

```bash
python3 ~/.claude/skills/cleanup/scripts/i18n_extract.py leaks          # vs committed JSON (default)
python3 ~/.claude/skills/cleanup/scripts/i18n_extract.py leaks --db     # vs the DB (deploy-truth)
```

Resolves every STATIC `t()` key app-wide → `/tmp/i18n_leaks.json`. The
output header prints the source (`committed JSON (files)` or
`app_translations (DB)`):

- **`en_absent`** (HIGH) — resolves to no EN entry → raw key-path in EVERY locale. Guaranteed user-visible.
- **`locale_absent`** (MED) — present in EN but missing from ≥1 non-EN locale → raw in that locale only (the §L34 class).

> **Default vs `--db`.** The default (committed JSON) is offline-safe and free of
> in-flight noise — use it for `run_all`/rotation. `--db` is the **deploy-truth**
> check: since the deploy dumps DB → JSON, a key absent from the DB renders as a
> raw path live even if it's currently in the committed JSON. `--db` therefore
> ALSO surfaces keys added to the JSON but not yet pushed to the DB — useful right
> before a deploy, but it can flag a concurrent actor's in-flight WIP, so triage
> with §LK2's Concurrent-WIP row in mind.

Why the resolver is accurate (and what it can't do):

- Matches BOTH `useTranslations('ns')` AND `getTranslations('ns' | {namespace:'ns'})` — server components (the Codex page) declare ns the second way; a `useTranslations`-only scan misses every server-page leak (this was the latent bug in the old `verify`, now also fixed).
- Maps each `t`-var to its namespace; tries the key as `ns.rest`, as a bare key under each declared ns, and under sub-namespace decls (`useTranslations('portal.x')` + `t('band')` → `portal.x.band`).
- **Skips template-literal keys** (`t(\`x.${y}\`)`) — can't statically resolve → no false positives (limit: won't catch a fully-absent *dynamic* prefix subtree; the admin Codex page is dynamic and was a manual false-alarm the tool correctly cleared — §L38).
- **Skips files with no declared namespace** (prop-passed `t`) and excludes the ns-declaring calls themselves.

#### Step LK2 — Classify + fix (the EN value must be MINTED — `leaks` never auto-adds)

**Remediation targets the DB** (`app_translations`) — a hand-edit to the JSON
alone is overwritten by the next build dump.

| Case | Fix |
|---|---|
| **Trivial label** — value obvious from key + siblings (`col_type` beside `col_code`/`col_subject` → "Type") | mint the EN value → add the key to `app_translations`: admin Languages panel (→ `upsert_translation`), OR seed it into `en/<ns>.json` and `node apps/web/scripts/push-translations.mjs --namespace <ns>` (idempotent), then run the `language` mode to fill the non-EN cells |
| **Whole subtree absent** — a feature shipped without its keys | a `hardcoded`/feature gap → route to the `hardcoded` mode or the owning author (its `merge`/`propagate` still write JSON — push the result to the DB afterward, same as above) |
| **Concurrent-WIP file** — key belongs to an in-flight feature (common when `--db` flags JSON keys not yet pushed) | leave it; lands with that work — don't fix another session's WIP (§L27/§L41) |
| **`locale_absent`** — EN exists, non-EN missing | run the `language` mode (it upserts the translations into the DB) — same as followups `parity`, but app-wide |

#### Step LK3 — Verify + log

Re-run `leaks` → `en_absent` drops by what you fixed (residual = template-key + genuinely-WIP features). If you edited locale JSON: §Step CL patch bump + delegate the vault log to **vault-log-compliance**. Detect-only runs skip both (§L29). **Co-mingled-tree-aware (§L27):** locale JSON is the most contended file in this repo — stage ONLY your keys, via a filtered per-hunk patch if the file also carries a parallel session's keys (the 2026-06-04 Codex fix did exactly this).
