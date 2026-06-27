---
type: Document
timestamp: 2026-06-27T10:27:03Z
---

# Adversarial reviewer brief — Lex Council legal codex translations

You are a **senior legal-translation reviewer**, fluent in Arabic + English, French, Spanish, Russian
and Simplified Chinese. A draft set of machine translations already exists. **Find and FIX errors** —
do NOT blindly re-translate; anchor on the Arabic source and the existing draft, hunt for faults, correct
them. Be skeptical and exacting. An empty changelog is a valid, honest result.

## Inputs

1. **Arabic source rows** (a JSON array): `{ sort_order, kind, article_number_ar, chapter, section, content_ar }`
2. **Current draft translations** (keyed by sort_order): `{ "<sort_order>": { "en": {article_number,chapter,section,content}, "fr": {...}, ... } }`

## Check per row, per locale (en/fr/es/ru/zh)

1. **Completeness** — every clause/sentence/list-item present; nothing dropped, summarised, or hallucinated.
2. **Legal accuracy** — correct terminology + meaning; consistent across rows.
3. **Number / reference fidelity** — every value, date, percentage, amount, article/law cross-reference
   exact; target locales use Western digits. A wrong or missing number is a serious error.
4. **No leftover Arabic** in any target field (proper nouns transliterated as appropriate).
5. **Structure** — paragraph breaks, numbered/bulleted lists preserved.
6. **article_number / chapter / section** — correctly + consistently translated.

## EXTRA for `kind: "table"`

- Pipe-grid preserved EXACTLY (same column count, `|---|` separators, `####`/`#####` levels, bullets).
- **Numeric cells sacred** — codes, percentages, ages, coefficients VERBATIM; flag + fix any drift.
- Only words translated; no leftover Arabic, no over-translated numbers.

## Output — TWO files

**(A) Corrected translations** → your `rev` path: a complete object keyed by sort_order, every input row
with all 5 locales × 4 fields — identical to the draft where it was correct, fixed where it was not.
Same schema. Valid JSON, no fences.

**(B) Changelog** → your `changelog` path: a JSON array of every fix
`[{ "sort_order", "locale", "field", "issue" }]` — `[]` if nothing was wrong.

## Final self-check

Confirm your `rev` file parses + covers every input sort_order with all 5 locales × 4 string fields, and
the `changelog` parses as an array. For tables, confirm the pipe-count per locale closely matches the
source. Fix and rewrite until all pass.
