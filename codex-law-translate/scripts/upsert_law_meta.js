#!/usr/bin/env node
/**
 * Phase 4 — Upsert law-level metadata translations into source_law_translations.
 * Reads <tmp>/meta_translations.json which YOU (Claude) write first:
 *   { "en": {subject, issuing_authority, summary}, "fr": {...}, ... }
 * The `summary` is generated (1–2 sentences) since laws have no AR summary source.
 * on_conflict=source_law_id,locale.
 */
const fs = require('fs')
const path = require('path')
const cfg = require('./_config')

const SOURCE_LAW_ID = fs.readFileSync(path.join(cfg.tmp, 'source_law_id.txt'), 'utf8').trim()
const metaPath = path.join(cfg.tmp, 'meta_translations.json')
if (!fs.existsSync(metaPath)) {
  console.error(`Write ${metaPath} first — { "<locale>": {subject, issuing_authority, summary} } for each of: ${cfg.locales.join(', ')}`)
  process.exit(1)
}
const META = JSON.parse(fs.readFileSync(metaPath, 'utf8'))

async function main() {
  const rows = cfg.locales.map((locale) => {
    const m = META[locale]
    if (!m) { console.error(`meta_translations.json missing locale ${locale}`); process.exit(1) }
    return { source_law_id: SOURCE_LAW_ID, locale, subject: m.subject, issuing_authority: m.issuing_authority, summary: m.summary }
  })
  const res = await fetch(`${cfg.SUPABASE_URL}/rest/v1/source_law_translations?on_conflict=source_law_id,locale`, {
    method: 'POST',
    headers: cfg.restHeaders({ Prefer: 'resolution=merge-duplicates,return=minimal' }),
    body: JSON.stringify(rows),
  })
  if (!res.ok) { console.error('Upsert failed:', res.status, await res.text()); process.exit(1) }
  console.log(`✓ Upserted ${rows.length} source_law_translations rows for ${SOURCE_LAW_ID}`)
}
main().catch((e) => { console.error('FATAL:', e); process.exit(1) })
