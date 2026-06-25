#!/usr/bin/env node
/**
 * Merge batch outputs + validate full coverage.
 *
 *   node merge_validate.js --phase translate
 *       merges batches/out_<id>.json → <tmp>/translations.json, validates 184×5×4 coverage,
 *       and writes batches/cur_<id>.json slices for the review phase.
 *
 *   node merge_validate.js --phase review
 *       merges batches/rev_<id>.json → <tmp>/translations.json (overwrite), aggregates
 *       batches/changelog_<id>.json → <tmp>/qa_fixes.json, and prints the changed-cell count
 *       (diffed against the pre-review translations.json).
 */
const fs = require('fs')
const path = require('path')
const cfg = require('./_config')

const phase = (process.argv[process.argv.indexOf('--phase') + 1]) || 'translate'
const articles = JSON.parse(fs.readFileSync(path.join(cfg.tmp, 'articles.json'), 'utf8'))
const manifest = JSON.parse(fs.readFileSync(path.join(cfg.batchesDir, 'manifest.json'), 'utf8'))
const LOCS = cfg.locales
const FIELDS = ['article_number', 'chapter', 'section', 'content']
const txPath = path.join(cfg.tmp, 'translations.json')

const prefix = phase === 'review' ? 'rev' : 'out'
const merged = {}
const problems = []
for (const m of manifest) {
  const f = path.join(cfg.batchesDir, `${prefix}_${m.id}.json`)
  if (!fs.existsSync(f)) { problems.push(`MISSING ${prefix}_${m.id}.json`); continue }
  let o
  try { o = JSON.parse(fs.readFileSync(f, 'utf8')) } catch (e) { problems.push(`BAD JSON ${prefix}_${m.id}: ${e.message}`); continue }
  Object.assign(merged, o)
}
if (problems.length) { console.error('PROBLEMS:\n  ' + problems.join('\n  ')); process.exit(1) }

// coverage
const gaps = []
for (const a of articles) {
  const e = merged[a.sort_order]
  if (!e) { gaps.push(`${a.sort_order} MISSING`); continue }
  for (const l of LOCS) {
    if (!e[l]) { gaps.push(`${a.sort_order}.${l}`); continue }
    for (const f of FIELDS) if (typeof e[l][f] !== 'string') gaps.push(`${a.sort_order}.${l}.${f} not-string`)
    if (!e[l].content || !e[l].content.trim()) gaps.push(`${a.sort_order}.${l}.content EMPTY`)
    if (!e[l].article_number || !e[l].article_number.trim()) gaps.push(`${a.sort_order}.${l}.article_number EMPTY`)
  }
}
if (gaps.length) { console.error(`COVERAGE GAPS (${gaps.length}):\n  ` + gaps.slice(0, 40).join('\n  ')); process.exit(1) }

if (phase === 'review') {
  const orig = fs.existsSync(txPath) ? JSON.parse(fs.readFileSync(txPath, 'utf8')) : {}
  const fixes = []
  for (const m of manifest) {
    const clf = path.join(cfg.batchesDir, `changelog_${m.id}.json`)
    if (fs.existsSync(clf)) {
      try { const cl = JSON.parse(fs.readFileSync(clf, 'utf8')); if (Array.isArray(cl)) fixes.push(...cl.map((x) => ({ batch: m.id, ...x }))) } catch {}
    }
  }
  let changed = 0
  for (const a of articles) for (const l of LOCS) for (const f of FIELDS) {
    if ((orig[a.sort_order]?.[l]?.[f] ?? '') !== (merged[a.sort_order][l][f] ?? '')) changed++
  }
  fs.writeFileSync(path.join(cfg.tmp, 'qa_fixes.json'), JSON.stringify(fixes, null, 2))
  fs.writeFileSync(txPath, JSON.stringify(merged, null, 2))
  console.log(`✓ review merged: ${manifest.length} batches, full coverage ${articles.length}×${LOCS.length}×${FIELDS.length}`)
  console.log(`  reviewer-logged fixes: ${fixes.length}; actual changed cells vs prior: ${changed}`)
  console.log(`  → ${txPath} (updated), ${path.join(cfg.tmp, 'qa_fixes.json')}`)
  fixes.sort((x, y) => x.sort_order - y.sort_order).slice(0, 60).forEach((f) => console.log(`    sort=${f.sort_order} ${f.locale}.${f.field}: ${String(f.issue).slice(0, 120)}`))
} else {
  fs.writeFileSync(txPath, JSON.stringify(merged, null, 2))
  // write cur slices for review
  for (const m of manifest) {
    const slice = {}
    for (const s of m.sorts) slice[s] = merged[s]
    fs.writeFileSync(m.cur, JSON.stringify(slice, null, 2))
  }
  console.log(`✓ translate merged: ${manifest.length} batches, full coverage ${articles.length}×${LOCS.length}×${FIELDS.length}`)
  console.log(`  → ${txPath}  (+ cur_*.json slices for review)`)
}
