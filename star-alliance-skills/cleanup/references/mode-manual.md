---
type: Document
timestamp: 2026-06-27T10:27:03Z
---

# Mode: `manual` — keep the in-app user manual fresh + translated

**Status: LIVE (added v1.15.0).**

The in-app user manual lives in the DB, EN-canonical with per-locale translations:

- `public.user_manual_pages` — one row per Part. `body_md` / `title` are the **English canonical**. 18 Parts (INDEX + 17), `status='final'` when published.
- `public.user_manual_page_translations` — `(page_id, locale)` rows for `ar/es/fr/ru/zh`. Columns: `title`, `body_md`, `source_md_hash` (= `md5` of the EN `body_md` at translation time), `updated_at`.
- Reader: `public.get_manual_page(p_slug, p_locale)` — returns the locale translation, **EN fallback** when absent, audience-gated. The FE route `/[locale]/manual/[slug]` calls it.

This mode does TWO things, mirroring how `docs` mode keeps the planet hubs fresh:

1. **Translation freshness (deterministic, auto-fix + publish).** When the EN `body_md` of a Part changes, every locale whose `source_md_hash` no longer matches is **stale**; locales with no row are **missing**. Re-translate those and upsert — `source_md_hash` is the single source of truth, so this self-heals.
2. **Content drift (heuristic, flag-only).** When the *app* changed (a release / recent vault-logs touched a page) but the EN manual Part that documents it wasn't updated, the Part's English may now be wrong. The skill can't safely rewrite English prose from code, so it **surfaces** the suspect Parts for a human/EN edit. Once EN is edited, check (1) auto-retranslates.

Supabase project_id = `bqgrpnsvplvicnmzxwkm` (prod). All DB work via the Supabase MCP.

---

## Step 1 — Detect stale / missing translations (deterministic)

Run via MCP `execute_sql`:

```sql
WITH expected AS (
  SELECT p.id, p.slug, l.locale
  FROM public.user_manual_pages p
  CROSS JOIN (VALUES ('ar'),('es'),('fr'),('ru'),('zh')) AS l(locale)
  WHERE p.is_deleted = false AND p.status = 'final'
)
SELECT e.slug, e.locale,
       CASE WHEN tr.page_id IS NULL THEN 'missing'
            ELSE 'stale' END AS state
FROM expected e
JOIN public.user_manual_pages p ON p.id = e.id
LEFT JOIN public.user_manual_page_translations tr
       ON tr.page_id = e.id AND tr.locale = e.locale
WHERE tr.page_id IS NULL
   OR tr.source_md_hash <> md5(p.body_md)
ORDER BY e.slug, e.locale;
```

Empty result → translations are fully fresh; skip to Step 3. Otherwise you have the `(slug, locale, missing|stale)` work-list. Group by `slug` (a Part usually needs the same set of locales).

## Step 2 — Re-translate + publish (auto)

Dispatch a **translation workflow** — one agent per affected `slug`, each (re)translating ONLY the stale/missing locales for that Part and upserting. This is the exact pattern used for the 2026-06-17 initial backfill (`manual-i18n-backfill`). Per-agent prompt MUST enforce:

- Preserve markdown structure exactly (heading levels, counts, order, tables, lists, code fences, hr, wikilinks).
- **Never translate / alter / reorder:** route paths (`/admin/files/tasks`), backticked code, URLs, `[[wikilinks]]`, `§` section numbers, and the kept tokens `Lex Council, WHBD, GFN, MFN, BFN, SFN, AFN, POA, NDA, OTP, GES, KPI`. The reader derives heading anchors from the route token in each heading — break it and intro-card deep links stop landing.
- Keep every heading's leading `#`/`##`/`###` + route token verbatim; translate only the words around it.
- Arabic is RTL — translate naturally, keep route/code tokens LTR + unchanged.

Upsert per locale (compute the hash in SQL so it always matches the current EN body — dollar-quote with a tag absent from the body, e.g. `$mbody$`):

```sql
INSERT INTO public.user_manual_page_translations (page_id, locale, title, body_md, source_md_hash)
VALUES (<ID>, '<LOCALE>', $mtitle$...$mtitle$, $mbody$...$mbody$,
        md5((SELECT body_md FROM public.user_manual_pages WHERE id=<ID>)))
ON CONFLICT (page_id, locale) DO UPDATE
  SET title=EXCLUDED.title, body_md=EXCLUDED.body_md,
      source_md_hash=EXCLUDED.source_md_hash, updated_at=now();
```

Auto-publish is the chosen default (set 2026-06-17): translations go live immediately; the reader EN-fallback means a bad/late translation is never worse than English. (To switch to review-first, write to a staging column / `status` instead and gate the reader.)

**Verify** after: re-run Step 1 — expect an empty result.

```sql
SELECT count(*) AS total_translations,
       count(*) FILTER (WHERE tr.source_md_hash = md5(p.body_md)) AS fresh
FROM public.user_manual_page_translations tr
JOIN public.user_manual_pages p ON p.id = tr.page_id
WHERE p.is_deleted = false AND p.status = 'final';
-- expect total = 5 × (#final Parts) and fresh = total
```

## Step 3 — Content drift (heuristic, flag-only)

Map recent app changes to the manual Parts that document them and flag Parts whose EN body may be out of date.

1. Gather changes since the last manual review **via the watermark** (it remembers the last pass, so this is driven by *new* work — not the whole history):
   ```sh
   python3 ~/.claude/skills/cleanup/scripts/watermark.py status manual   # exit 10 = escalate
   python3 ~/.claude/skills/cleanup/scripts/watermark.py since  manual   # the new vault-log filenames
   ```
   - **Escalation (exit 10 / 🚩, ≥3 new vault-logs):** more app change than a heuristic flag-pass should reconcile — `spawn_task` a `/conquering-campaign` AUDIT of the manual surface (or tell the user, interactively).
   - Otherwise use the `since manual` list (plus the latest `docs/logs/INDEX.md` release rows) as the change set for steps 2–3 below.
2. Each per-page Part documents routes embedded in its headings (e.g. `## §9.6 — Tasks · /admin/files/tasks`). Extract those route tokens:
   ```sql
   SELECT slug, regexp_matches(body_md, '/[a-z][a-z0-9/-]+', 'g') AS route
   FROM public.user_manual_pages WHERE is_deleted=false;
   ```
3. If a vault-log / release touched files under a route a Part documents (e.g. a change under `app/[locale]/(admin)/admin/files/tasks/` ↔ the Tasks section), flag that Part: **"EN may be stale — review."**
4. **Surface only.** Do not auto-rewrite English prose from code. Once EN is edited (in dev-tools → Manual tab), Step 1 detects the hash change and Step 2 retranslates automatically.

## Step 4 — Stamp the watermark

At the END of the run (translations healed and/or drift surfaced, OR a clean no-op), advance the watermark so the next run only looks at newer work:

```sh
python3 ~/.claude/skills/cleanup/scripts/watermark.py advance manual          # did real work
python3 ~/.claude/skills/cleanup/scripts/watermark.py advance manual --noop   # nothing to do
```

## When this runs

- **Explicit:** `/cleanup manual`, "update the manual translations", "is the manual up to date", "translate the manual".
- **At release:** the `release` gate (and `run_all`) should call Step 1; a non-empty result is a **surfaced** finding (not a hard gate) — translations auto-heal on the next `manual` run, and EN-fallback keeps the manual readable meanwhile. Wire by adding a `get_manual_page`-table staleness probe alongside the postgres MCP checks.

## Landmines

- **Hash must be computed in SQL** (`md5((SELECT body_md ...))`), never passed by the agent — an agent-computed hash drifts from the live EN body and the Part looks permanently stale.
- **Routes/anchors are load-bearing.** A translator that "helpfully" localizes `/admin/files/tasks` or drops the `§9.6` breaks the intro-card deep link silently. Keep them verbatim.
- **`en` is not a translations row.** EN lives on `user_manual_pages`; the translations table `CHECK` forbids `'en'`. The reader supplies EN via `COALESCE`.
- **Audience still applies.** Translations inherit the parent Part's audience via the reader RPC; never expose the translations table to a non-programmer read path (it has no audience column of its own).
