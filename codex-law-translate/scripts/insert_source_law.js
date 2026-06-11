#!/usr/bin/env node
/**
 * Phase 2a — Upsert the source_laws row (idempotent on `code`). → <tmp>/source_law_id.txt
 * Metadata: config.json overrides win; otherwise read from <tmp>/frontmatter.json.
 */
const fs = require('fs')
const path = require('path')
const cfg = require('./_config')

const fm = JSON.parse(fs.readFileSync(path.join(cfg.tmp, 'frontmatter.json'), 'utf8'))
const pick = (k, fmKey, dflt) => cfg[k] ?? fm[fmKey] ?? dflt

async function main() {
  const payload = {
    code:              cfg.code,
    doc_type:          cfg.docType || fm.type || 'law',
    doc_number:        String(pick('docNumber', 'number', '')),
    year:              Number(pick('year', 'year', 0)) || null,
    calendar:          cfg.calendar || fm.calendar || 'gregorian',
    date_issued:       pick('dateIssued', 'date_issued', null) || null,
    date_effective:    pick('dateEffective', 'effective_date', null) || null,
    issuing_authority: cfg.issuingAuthorityAr || fm.issuing_authority || null,
    official_gazette:  cfg.officialGazette || fm.publication || null,
    subject_ar:        cfg.subjectAr || fm.subject || null,
    status:            cfg.status || 'active',
    published:         false,
    tags:              cfg.tags,
  }
  const res = await fetch(`${cfg.SUPABASE_URL}/rest/v1/source_laws?on_conflict=code`, {
    method: 'POST',
    headers: cfg.restHeaders({ Prefer: 'resolution=merge-duplicates,return=representation' }),
    body: JSON.stringify(payload),
  })
  if (!res.ok) { console.error('Insert failed:', res.status, await res.text()); process.exit(1) }
  const row = (await res.json())[0]
  fs.writeFileSync(path.join(cfg.tmp, 'source_law_id.txt'), row.id)
  console.log(`Source law upserted:\n  id:   ${row.id}\n  code: ${row.code}\n  subj: ${row.subject_ar}`)
  console.log(`Saved id → ${path.join(cfg.tmp, 'source_law_id.txt')}`)
}
main().catch((e) => { console.error(e); process.exit(1) })
