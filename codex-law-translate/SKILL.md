---
name: codex-law-translate
description: >
  End-to-end pipeline for loading a real-world law into the Lex Council legal codex,
  translated into all 5 non-Arabic locales (en/fr/es/ru/zh), then adversarially revised
  and published. Use whenever the user says "translate the law", "load a law into the codex",
  "push law X to DB", "translate the codes", "add Law N/YYYY to the codex", "translate and
  publish a law", "do the social/labour/whatever law like we did before", "revise the codex
  translations", or "publish the codex law". Covers parse → insert (source_laws + law_articles,
  AR canonical) → translate via Claude subagents → upsert (law_article_translations) → law-metadata
  translation (source_law_translations) → full adversarial QA revision (Opus reviewers) → publish
  (published=true on all articles + the source law). Translation is done by Claude subagents
  (Ollama is gone). All writes go to production via service-role REST — no DDL, idempotent.
metadata:
  version: 1.0.0
---

# Codex Law Translate (Lex Council)

Canonical pipeline for putting a law into the **legal codex** with AR + 5 translations, reviewed and
published. Predecessors: `2026-05-21_egypt-labor-law-14-2025` and `2026-06-11_egypt-social-insurance-law-148-2019`.

**Production project_id = `bqgrpnsvplvicnmzxwkm`.** Every DB write here goes there via the **service-role
REST API** (read from `apps/web/.env.local`) — no migration, no DDL, all idempotent. The destination
tables already exist: `source_laws`, `law_articles`, `law_article_translations`, `source_law_translations`.

## The data model (do not change it)

| Table | Holds | Key columns |
|---|---|---|
| `source_laws` | one row per law | `code` (unique, e.g. `Y2019 L148`), `subject_ar`, `issuing_authority`, `date_issued`, `date_effective`, `official_gazette`, `status`, `published`, `tags`, `article_count` (trigger-maintained) |
| `law_articles` | one row per article/table | `source_law_id` FK, `article_number` (AR), `sort_order`, `chapter`, `section`, `content_ar`, `status`, `published` |
| `law_article_translations` | 5 locales × each article | `law_article_id` FK, `locale` (en/fr/es/ru/zh), `content`, `article_number`, `chapter`, `section` — unique `(law_article_id, locale)` |
| `source_law_translations` | 5 locales × law metadata | `source_law_id` FK, `locale`, `subject`, `issuing_authority`, `summary` — unique `(source_law_id, locale)` |

- `sort_order`: assigned by **document order** — promulgation `1..N`, main articles `100 + seq`, attached
  tables `1000 + seq` (tables sort last). Document-order numbering is what lets `مكرر` (bis) articles get
  unique, in-sequence slots (e.g. `مادة 46 مكرر 3` between 46 and 47).
- `published = false` on load; flip to `true` only in the Publish phase. `source_laws.article_count` reads
  0 until articles are published, then the trigger sets it to the published count.
- The 5 target locales use **Western digits** (1,2,3) — including Chinese. AR keeps Arabic-Indic digits.

## Source documents

Firm-maintained Arabic extractions live in the **sibling repo**, not lex_council:
`…/Lex Council Business/Workflow/Legal Memos/Source Laws/Y{year} L{num}.md` (YAML front-matter with
`subject`/`number`/`year`/`date_issued`/`effective_date`/`publication`). Original PDFs in `…/Legal Memos/Stock Laws/`.
Most are **Arabic-only** → ALL 5 locales are machine-translated (the bilingual Labour Law was the one exception).

## How to run it

Work from this skill's `scripts/`. Everything is driven by one **`config.json`** you write per law; every
script reads it via the `CODEX_CONFIG` env var. Run scripts with `node`.

### Phase 0 — Config + scope

1. Locate the source markdown (ask the user for the law code, e.g. `Y2019 L148`, or the file path).
2. Read the front-matter and skim the body. **Verify the heading grammar** the parser expects (below);
   if this law's markdown differs, adjust `scripts/parse_law.js` regexes — legal markdown varies per law,
   so always eyeball the parser's structure report before trusting it.
3. Write `config.json` (see `scripts/config.example.json`). Minimum: `code`, `sourcePath`, `projectRoot`
   (the lex_council repo root), `tags`. Metadata defaults are read from the front-matter; override in config
   if needed (`issuingAuthorityAr`, `officialGazette`, `dateIssued`, `dateEffective`, `subjectAr`).
4. Export it: `export CODEX_CONFIG=/abs/path/config.json`.

### Phase 1 — Parse + validate

```sh
node scripts/parse_law.js
```
Writes `<tmp>/articles.json` + `<tmp>/frontmatter.json` and prints a structure report. It **reconciles**
parsed rows against EVERY article/table heading in the source (promulgation / main / table counts must
match), flags any unrecognized `### مادة …`/`### Article …` heading that matched no regex (would be silently
dropped — extend the regex if so), reports how many `مكرر` (bis) articles were captured, and asserts every
row has non-empty `content_ar`. **Do not proceed unless validation passes** (exit 0). Spot-check one
multi-paragraph article and one table (pipe grid preserved, `[[wikilinks]]` stripped to display text).

### Phase 2 — Insert source law + articles

```sh
node scripts/insert_source_law.js     # upsert source_laws (on code) → <tmp>/source_law_id.txt
node scripts/insert_articles.js       # bulk-insert AR articles → <tmp>/article_ids.json
```
Idempotent: `insert_articles` clears prior rows for this source_law first. All `published = false`.

### Phase 3 — Translate (Claude subagents)

```sh
node scripts/make_batches.js          # → <tmp>/batches/in_<id>.json + manifest.json
```
Read `<tmp>/batches/manifest.json`. For **each** batch, spawn a subagent (Agent tool). **Spawn in groups
of ~5, not all at once** — high concurrency causes API socket timeouts; re-run any that fail.

- **Model:** prose batches → `sonnet` (strong + cost-aware); table batches → `opus` (grid/number integrity).
- Each subagent: reads `references/TRANSLATE_INSTRUCTIONS.md` + its `in_<id>.json`, translates into
  en/fr/es/ru/zh, writes `<tmp>/batches/out_<id>.json` keyed by sort_order, self-validates coverage.
- Tell table-batch agents to emphasize the table rules (preserve pipe grid + numeric cells verbatim).

Then merge + validate full coverage:
```sh
node scripts/merge_validate.js --phase translate   # → <tmp>/translations.json + cur_<id>.json slices
```
Must report full coverage (rows × 5 × 4 fields, content/article_number non-empty). Upsert:
```sh
node scripts/upsert_translations.js
```

### Phase 4 — Law-metadata translation

Translate the law's `subject` + `issuing_authority` + a generated 1–2 sentence `summary` into all 5
locales yourself (it's small). Write `<tmp>/meta_translations.json` as `{ "<locale>": {subject, issuing_authority, summary} }`, then:
```sh
node scripts/upsert_law_meta.js
```

### Phase 5 — Revise (full adversarial QA) — when the user asks to "revise"

```sh
node scripts/make_batches.js --review   # ensures cur_<id>.json slices exist (idempotent)
```
For each batch, spawn an **Opus reviewer** (groups of ~5). Each reads `references/REVIEW_INSTRUCTIONS.md`
+ its `in_<id>.json` (Arabic source) + `cur_<id>.json` (current draft), hunts for omissions /
mistranslations / wrong legal terms / number-and-reference drift / leftover Arabic / broken structure,
**rewrites faulty fields**, writes `<tmp>/batches/rev_<id>.json` + `<tmp>/batches/changelog_<id>.json`
(`[]` if clean). Use Opus reviewers even for the prose that Sonnet translated — independent, stronger pass.

```sh
node scripts/merge_validate.js --phase review   # merge rev_*, aggregate qa_fixes.json, count changed cells
node scripts/upsert_translations.js             # re-upsert corrected rows (idempotent)
```
Surface the fix count + headline catches to the user (number errors, dropped content, hallucinations).

### Phase 6 — Publish — when the user asks to "publish"

```sh
node scripts/publish.js     # PATCH published=true on all law_articles + the source_laws row
node scripts/verify.js      # final counts: law_published, article_count, articles_published, translation_rows
```
Confirm `article_count` equals the article total (the trigger fires on publish). The law is now live at
`/admin/files/insights/codex/<code>` (URL-encode the space, e.g. `Y2019%20L148`).

### Phase 7 — Log it (mandatory, P8)

Write a vault log under `<projectRoot>/docs/vault-logs/YYYY-MM-DD_<slug>.md` with a Plain-English Summary,
files/rows changed, the QA fix list, and the publish result; prepend the INDEX.md row. A campaign folder
under `docs/build-campaigns/YYYY-MM-DD_<slug>/` holding the config + the per-law parser + `qa_fixes.json`
is good practice (mirrors the predecessors). Commit + push the docs to `main` (scope the commit to your files).

## The parser's expected heading grammar (adjust per law)

`scripts/parse_law.js` recognises, inside the Arabic markdown (after stripping YAML front-matter):

| Heading | Meaning |
|---|---|
| `## مواد الإصدار` / `## الباب …` / `## الجداول الملحقة` | chapter boundary (resets section) |
| `### الفصل …` | section boundary |
| `### مادة N إصدار` | promulgation article |
| `### مادة N` / `### مادة N مكرر` / `### مادة N مكرر K` | main article (form A, incl. bis/مكرر variants) |
| `### Article N — مادة N` | main article (form B — the 148/2019 extraction mixed both forms) |
| `### جدول رقم N — <title>` | attached table |

Body = lines after the heading until the next `##`/`###` (so `####`/`#####`/`| … |` stay inside table bodies).
If a new law uses different markers, edit the regexes at the top of `parse_law.js` and re-run; the validation
asserts will catch a mis-parse (gaps, wrong counts, empty content).

## Hard rules

- **Translation = Claude subagents.** Ollama (the old qwen3:14b engine) is uninstalled. Do not reinstall it.
- **Attached tables:** translate the title/headers/descriptive cells; **numeric codes, percentages, ages,
  coefficients are copied VERBATIM**; the markdown pipe grid is preserved exactly. Reviewers verify pipe-count
  + number parity per locale.
- **Never publish without the user asking.** Load + translate is safe (drafts); publishing makes the law public.
- **Verify project_id = `bqgrpnsvplvicnmzxwkm`** for any MCP cross-check.
- **Concurrency:** spawn translator/reviewer subagents in groups of ~5; expect a few socket timeouts and re-run.

## Checklist

- [ ] `config.json` written, `CODEX_CONFIG` exported, parser grammar verified for this law.
- [ ] Parse validation passed (contiguous, non-empty, table count); spot-checked an article + a table.
- [ ] source_laws + law_articles inserted (drafts); id map saved.
- [ ] All batches translated (groups of ~5), merge reports full coverage, translations upserted.
- [ ] Law metadata translated + upserted (5 rows).
- [ ] (If asked) Adversarial QA run; `qa_fixes.json` reviewed; corrections re-upserted.
- [ ] (If asked) Published; `verify.js` confirms article_count = total, all published.
- [ ] Vault log + INDEX row written; docs committed + pushed to `main`.
