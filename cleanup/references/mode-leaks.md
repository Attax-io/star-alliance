# Mode: leaks — full recipe

> **Script:** `python3 ~/.claude/skills/cleanup/scripts/i18n_extract.py leaks [--scope ...] [--out /tmp/i18n_leaks.json]` — detect-only; never edits a JSON or `.tsx`.

Find i18n keys USED in code (`t('ns.key')`) but ABSENT from the locale JSON. next-intl renders an absent key as its raw uppercased dotted path via `getMessageFallback` (e.g. `PUBLIC.CODEX.COL_TYPE`) — a visible UX break. The class neither `language` (only sees keys present-but-equal-to-EN — §L25/L34) nor `hardcoded` (finds literals NOT yet keyed) catches. It twice leaked the public Codex page (`codex.col_type` / `col_status` / `filter_status` absent from `public.json`).

#### Step LK1 — Detect

```bash
python3 ~/.claude/skills/cleanup/scripts/i18n_extract.py leaks
```

Resolves every STATIC `t()` key app-wide → `/tmp/i18n_leaks.json`:

- **`en_absent`** (HIGH) — resolves to no `en/<ns>.json` entry → raw key-path in EVERY locale. Guaranteed user-visible.
- **`locale_absent`** (MED) — present in EN but missing from ≥1 non-EN locale → raw in that locale only (the §L34 class).

Why the resolver is accurate (and what it can't do):

- Matches BOTH `useTranslations('ns')` AND `getTranslations('ns' | {namespace:'ns'})` — server components (the Codex page) declare ns the second way; a `useTranslations`-only scan misses every server-page leak (this was the latent bug in the old `verify`, now also fixed).
- Maps each `t`-var to its namespace; tries the key as `ns.rest`, as a bare key under each declared ns, and under sub-namespace decls (`useTranslations('portal.x')` + `t('band')` → `portal.x.band`).
- **Skips template-literal keys** (`t(\`x.${y}\`)`) — can't statically resolve → no false positives (limit: won't catch a fully-absent *dynamic* prefix subtree; the admin Codex page is dynamic and was a manual false-alarm the tool correctly cleared — §L38).
- **Skips files with no declared namespace** (prop-passed `t`) and excludes the ns-declaring calls themselves.

#### Step LK2 — Classify + fix (the EN value must be MINTED — `leaks` never auto-adds)

| Case | Fix |
|---|---|
| **Trivial label** — value obvious from key + siblings (`col_type` beside `col_code`/`col_subject` → "Type") | add to `en/<ns>.json`, propagate + translate via the `hardcoded` H3–H5 machinery (`i18n_extract.py merge`/`propagate`) or a direct add + the `language` mode |
| **Whole subtree absent** — a feature shipped without its keys | a `hardcoded`/feature gap → route to the `hardcoded` mode or the owning author |
| **Concurrent-WIP file** — key belongs to an in-flight feature | leave it; lands with that work — don't fix another session's WIP (§L27) |
| **`locale_absent`** — EN exists, non-EN missing | propagate EN → missing locales, then translate via `language` (same as followups `parity`, but app-wide) |

#### Step LK3 — Verify + log

Re-run `leaks` → `en_absent` drops by what you fixed (residual = template-key + genuinely-WIP features). If you edited locale JSON: §Step CL patch bump + delegate the vault log to **vault-log-compliance**. Detect-only runs skip both (§L29). **Co-mingled-tree-aware (§L27):** locale JSON is the most contended file in this repo — stage ONLY your keys, via a filtered per-hunk patch if the file also carries a parallel session's keys (the 2026-06-04 Codex fix did exactly this).
