#!/usr/bin/env node
/**
 * Phase 3/5 — Split articles into translation/review batches.
 *
 *   node make_batches.js            → writes batches/in_<id>.json + batches/manifest.json
 *   node make_batches.js --review   → also (re)writes batches/cur_<id>.json from <tmp>/translations.json
 *
 * Batching: prose rows grouped by a char cap (~8000); each large table is its own batch,
 * small tables grouped. Manifest carries id, kind (prose|table), sorts[], and file paths.
 */
const fs = require('fs')
const path = require('path')
const cfg = require('./_config')

const CAP = cfg.batchCharCap || 8000
const articles = JSON.parse(fs.readFileSync(path.join(cfg.tmp, 'articles.json'), 'utf8'))
const bySort = Object.fromEntries(articles.map((a) => [a.sort_order, a]))
const review = process.argv.includes('--review')

const paths = (id) => ({
  id,
  in: path.join(cfg.batchesDir, `in_${id}.json`),
  out: path.join(cfg.batchesDir, `out_${id}.json`),
  cur: path.join(cfg.batchesDir, `cur_${id}.json`),
  rev: path.join(cfg.batchesDir, `rev_${id}.json`),
  changelog: path.join(cfg.batchesDir, `changelog_${id}.json`),
})

const manifest = []

// prose batches
const prose = articles.filter((a) => a.kind !== 'table').sort((p, q) => p.sort_order - q.sort_order)
let cur = [], len = 0, n = 0
const flush = () => {
  if (!cur.length) return
  const m = { ...paths(`prose_${n}`), kind: 'prose', sorts: cur.map((a) => a.sort_order) }
  fs.writeFileSync(m.in, JSON.stringify(cur, null, 2))
  manifest.push(m); cur = []; len = 0; n++
}
for (const a of prose) {
  if (len > 0 && len + a.content_ar.length > CAP) flush()
  cur.push(a); len += a.content_ar.length
}
flush()

// table batches: big tables solo, small ones grouped
const tables = articles.filter((a) => a.kind === 'table').sort((p, q) => p.sort_order - q.sort_order)
let group = [], glen = 0, tn = 0
const flushT = () => {
  if (!group.length) return
  const m = { ...paths(`table_${tn}`), kind: 'table', sorts: group.map((a) => a.sort_order) }
  fs.writeFileSync(m.in, JSON.stringify(group, null, 2))
  manifest.push(m); group = []; glen = 0; tn++
}
for (const a of tables) {
  if (a.content_ar.length >= CAP) { flushT(); group = [a]; flushT(); continue }
  if (glen > 0 && glen + a.content_ar.length > CAP) flushT()
  group.push(a); glen += a.content_ar.length
}
flushT()

fs.writeFileSync(path.join(cfg.batchesDir, 'manifest.json'), JSON.stringify(manifest, null, 2))
console.log(`Wrote ${manifest.length} batch input files → ${cfg.batchesDir}`)
manifest.forEach((m) => console.log(`  ${m.id} (${m.kind}) sorts=${m.sorts.length} [${m.sorts[0]}..${m.sorts[m.sorts.length - 1]}]`))

if (review) {
  const txPath = path.join(cfg.tmp, 'translations.json')
  if (!fs.existsSync(txPath)) { console.error(`\nNo ${txPath} — run the translate phase + merge first.`); process.exit(1) }
  const TX = JSON.parse(fs.readFileSync(txPath, 'utf8'))
  for (const m of manifest) {
    const slice = {}
    for (const s of m.sorts) slice[s] = TX[s]
    fs.writeFileSync(m.cur, JSON.stringify(slice, null, 2))
  }
  console.log(`\nWrote ${manifest.length} current-draft slices (cur_*.json) for review.`)
}
