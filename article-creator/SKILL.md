---
name: article-creator
description: >
  End-to-end procedure for creating a public Insights article and pushing it to the
  Lex Council production DB (public.articles + public.article_translations) in all 6
  locales. Use this skill whenever the user asks to create an article, write an
  insights article, push an article to the DB, publish an article on the site, add a
  blog post, turn research/memos/findings into an article, or translate an article
  into all languages. Also trigger on "new insights post", "add it to /insights",
  "make this an article", "push to the articles table", or any request that implies
  writing rows into articles/article_translations. This skill exists because the
  insert has six landmines discovered in production: the article_locale enum cast,
  the uploaded_by FK to auth.users, EN-canonical fallback semantics, the draft-RLS
  admin-read trap, dollar-quoting for markdown bodies, and the mandatory P3 approval
  + P8 vault log. Load silently.
---

# Article Creator — Insights CMS Pipeline

Creates one article + 6 locale translations in the Lex Council production database,
following the exact pattern validated on 2026-06-10 (`vat-exemptions-egypt`).

## 1. Data model (verified against production)

| Table | Key columns | Notes |
|---|---|---|
| `public.articles` | `id uuid default gen_random_uuid()`, `slug` (UNIQUE, kebab-case), `status` (CHECK: `draft` / `published` / `archived`), `cover_url`, `author_user_id` (FK → `public.users`, nullable), `author_display_name` (NOT NULL), `author_title`, `uploaded_by` (NOT NULL, FK → **auth.users**), `category` (default `'General'`), `tags text[]`, `published_at` | One row per article. `published_at` stays NULL for drafts; set `now()` when publishing. |
| `public.article_translations` | `article_id` (FK), `locale` (**enum `public.article_locale`**: ar, en, es, fr, ru, zh), `headline` (NOT NULL), `subheadline`, `body_intro` (NOT NULL), `body` (NOT NULL, **markdown**), `meta_title`, `meta_description`, `reading_minutes`, `translated_by` | One row per locale. EN is canonical; missing locales fall back to EN via `articles_pub_js` / `get_articles_pub`. |

House conventions (match existing rows):
- `author_display_name`: `'Lex Council Team'` unless the user names an attorney.
- `uploaded_by`: reuse the id from an existing article (`SELECT uploaded_by FROM articles LIMIT 1`) unless told otherwise — it must exist in `auth.users`.
- `category`: reuse an existing one where possible (`Compliance`, `Pricing & Costs`, `Market Analysis`, `Best Practices`, `Labour Law`, `General`).
- `body`: markdown with `##` section headings, bold key phrases, bullet lists. `body_intro` = 1-paragraph excerpt (shown in lists/SEO). `reading_minutes` ≈ words/200.
- Legal content: every substantive claim must cite a law/article number. No speculation beyond the source texts.

## 2. Procedure

1. **Gather content.** If converting research/memos, use only what the sources support.
   Draft EN first (canonical), then translate to ar, fr, es, ru, zh. All 6 locales,
   equivalent structure. Arabic is RTL — plain markdown is fine, the FE handles direction.
2. **Discover before writing.** Confirm schema/conventions still hold:
   `list_tables`, sample an existing article + translation, check
   `articles_status_check` and the `article_locale` enum if anything looks off.
3. **Build ONE transaction** (CTE pattern). Dollar-quote every text field with a
   unique tag (`$tx$...$tx$`) — bodies contain apostrophes and quotes. Cast locale:
   `v.locale::public.article_locale`.

```sql
WITH a AS (
  INSERT INTO public.articles (slug, status, author_display_name, uploaded_by, category, tags, published_at)
  VALUES ('<slug>', '<draft|published>', 'Lex Council Team', '<auth-user-uuid>',
          '<Category>', ARRAY['tag1','tag2'], <NULL | now()>)
  RETURNING id
)
INSERT INTO public.article_translations
  (article_id, locale, headline, subheadline, body_intro, body, meta_title, meta_description, reading_minutes)
SELECT a.id, v.locale::public.article_locale, v.headline, v.subheadline, v.body_intro,
       v.body, v.meta_title, v.meta_description, v.reading_minutes
FROM a, (VALUES
  ('en', $tx$...$tx$, $tx$...$tx$, $tx$...$tx$, $tx$...$tx$, $tx$...$tx$, $tx$...$tx$, 7),
  ('ar', ...), ('fr', ...), ('es', ...), ('ru', ...), ('zh', ...)
) AS v(locale, headline, subheadline, body_intro, body, meta_title, meta_description, reading_minutes);
```

4. **P3 gate (mandatory).** Before executing: state what will be inserted, where
   (production = `bqgrpnsvplvicnmzxwkm`), and ask draft vs published. Never write
   without explicit approval. Default recommendation: **draft** (review in admin
   panel, publish from there).
5. **Execute** via `execute_sql` (data-only insert — not `apply_migration`).
6. **Verify:**

```sql
SELECT a.slug, a.status, count(t.locale) AS locales, array_agg(t.locale ORDER BY t.locale)
FROM articles a LEFT JOIN article_translations t ON t.article_id = a.id
WHERE a.slug = '<slug>' GROUP BY a.id, a.slug, a.status;
```

Expect 1 row, `locales = 6`.

7. **P8 vault log** in `lex_council/docs/vault-logs/YYYY-MM-DD_<slug>-insights-article.md`
   with Plain-English Summary + P13 self-audit table of every MCP call.

## 3. Landmines (each caused a real failure or near-miss)

- **Locale enum:** `locale` is `public.article_locale`, not text. Always cast.
  Valid values exactly: `ar, en, es, fr, ru, zh`.
- **`uploaded_by` → auth.users:** not `public.users`. A random users.id will FK-fail.
- **Draft RLS trap (fixed 2026-06-10, stay alert):** `article_translations` once had
  only the `read_published` policy, so draft translations were invisible in the admin
  editor (empty fields). `p_article_translations_admin_read`
  (`private.has_perm('insights_vap')`) now fixes this. If an admin editor shows an
  empty draft again, check `pg_policy` on `article_translations` FIRST.
- **Dollar-quoting:** never single-quote bodies; pick a tag (e.g. `$tx$`) and assert
  it doesn't occur inside any text.
- **Publishing:** `status='published'` must come with `published_at = now()`;
  drafts keep `published_at` NULL. Public/anon can only read published rows.
- **Slug:** unique, kebab-case, becomes `/insights/<slug>` and is auto-derived from
  the headline in the admin UI — keep them consistent.
- **One transaction:** never insert the article row without its translations; a
  half-inserted article shows as an empty shell in the admin list.

## 4. Where it surfaces

- Public: `/{locale}/insights` and `/{locale}/insights/<slug>` via `get_articles_pub`
  RPC / `articles_pub_js` (published only, EN fallback).
- Admin review/edit/publish: Admin Panel → Files → Insights
  (`apps/web/app/[locale]/(admin)/admin/files/insights/`, drawer fetches
  `article_translations` directly — RLS-enforced).
- Sitemap picks up published articles automatically (`app/sitemap.ts`).
