#!/usr/bin/env node
/**
 * Final verification — counts via REST (no MCP needed).
 * Prints: law published flag + article_count, article totals (published/total), translation rows, meta rows.
 */
const fs = require('fs')
const path = require('path')
const cfg = require('./_config')

const SOURCE_LAW_ID = fs.readFileSync(path.join(cfg.tmp, 'source_law_id.txt'), 'utf8').trim()

async function get(p) {
  const res = await fetch(`${cfg.SUPABASE_URL}/rest/v1/${p}`, { headers: cfg.restHeaders() })
  if (!res.ok) throw new Error(`${res.status}: ${await res.text()}`)
  return res.json()
}
async function count(p) {
  const res = await fetch(`${cfg.SUPABASE_URL}/rest/v1/${p}`, { method: 'HEAD', headers: cfg.restHeaders({ Prefer: 'count=exact', Range: '0-0' }) })
  const cr = res.headers.get('content-range') || '*/0'
  return Number(cr.split('/')[1] || 0)
}

async function main() {
  const law = (await get(`source_laws?id=eq.${SOURCE_LAW_ID}&select=code,published,article_count`))[0]
  const ids = await get(`law_articles?source_law_id=eq.${SOURCE_LAW_ID}&select=id`)
  const idList = ids.map((r) => r.id)
  const articlesTotal = idList.length
  const articlesPublished = await count(`law_articles?source_law_id=eq.${SOURCE_LAW_ID}&published=eq.true`)
  // translation rows: count in chunks of in.() filter
  let trRows = 0
  const CH = 100
  for (let i = 0; i < idList.length; i += CH) {
    trRows += await count(`law_article_translations?law_article_id=in.(${idList.slice(i, i + CH).join(',')})`)
  }
  const metaRows = await count(`source_law_translations?source_law_id=eq.${SOURCE_LAW_ID}`)

  console.log('── Verify:', law.code, '──')
  console.log(`  law_published:      ${law.published}`)
  console.log(`  article_count:      ${law.article_count}`)
  console.log(`  articles total:     ${articlesTotal}`)
  console.log(`  articles published: ${articlesPublished}/${articlesTotal}`)
  console.log(`  translation rows:   ${trRows}  (expected ${articlesTotal * cfg.locales.length})`)
  console.log(`  meta rows:          ${metaRows}  (expected ${cfg.locales.length})`)
  const ok = trRows === articlesTotal * cfg.locales.length && metaRows === cfg.locales.length
  console.log(ok ? '✓ counts consistent' : '✗ count mismatch — investigate')
}
main().catch((e) => { console.error('FATAL:', e); process.exit(1) })
