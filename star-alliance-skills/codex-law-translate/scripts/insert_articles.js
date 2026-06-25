#!/usr/bin/env node
/**
 * Phase 2b — Bulk-insert the AR articles (content_ar canonical). All published=false.
 * Idempotent: deletes existing articles for this source_law first.
 * → <tmp>/article_ids.json  (sort_order → uuid)
 */
const fs = require('fs')
const path = require('path')
const cfg = require('./_config')

const SOURCE_LAW_ID = fs.readFileSync(path.join(cfg.tmp, 'source_law_id.txt'), 'utf8').trim()
const articles = JSON.parse(fs.readFileSync(path.join(cfg.tmp, 'articles.json'), 'utf8'))

async function rest(method, p, body) {
  const opts = { method, headers: cfg.restHeaders({ Prefer: 'return=representation' }) }
  if (body !== undefined) opts.body = JSON.stringify(body)
  const res = await fetch(`${cfg.SUPABASE_URL}/rest/v1/${p}`, opts)
  if (!res.ok) throw new Error(`${method} ${p} → ${res.status}: ${await res.text()}`)
  return res.status === 204 ? null : res.json()
}

async function main() {
  console.log(`Source law id: ${SOURCE_LAW_ID}\nArticles to insert: ${articles.length}`)
  console.log('Clearing prior articles…')
  await rest('DELETE', `law_articles?source_law_id=eq.${SOURCE_LAW_ID}`, undefined)

  const rows = articles.map((a) => ({
    source_law_id: SOURCE_LAW_ID,
    article_number: a.article_number_ar,
    sort_order: a.sort_order,
    chapter: a.chapter || null,
    section: a.section || null,
    content_ar: a.content_ar,
    status: 'active',
    published: false,
  }))

  const CHUNK = 50
  let inserted = []
  for (let i = 0; i < rows.length; i += CHUNK) {
    inserted = inserted.concat(await rest('POST', 'law_articles', rows.slice(i, i + CHUNK)))
    console.log(`  …inserted ${inserted.length}/${rows.length}`)
  }
  const idBySort = Object.fromEntries(inserted.map((r) => [r.sort_order, r.id]))
  fs.writeFileSync(path.join(cfg.tmp, 'article_ids.json'), JSON.stringify(idBySort, null, 2))
  console.log(`✓ Inserted ${inserted.length}. Saved id map → ${path.join(cfg.tmp, 'article_ids.json')}`)
}
main().catch((e) => { console.error('FATAL:', e.message); process.exit(1) })
