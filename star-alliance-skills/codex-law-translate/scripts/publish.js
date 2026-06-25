#!/usr/bin/env node
/**
 * Phase 6 — Publish: set published=true on all law_articles of this law + the source_laws row.
 * The source_laws.article_count trigger fires on publish. ONLY run when the user asks to publish.
 *
 *   node publish.js                  → publish articles + the source law
 *   node publish.js --articles-only  → publish articles, leave source_laws.published as-is
 */
const fs = require('fs')
const path = require('path')
const cfg = require('./_config')

const SOURCE_LAW_ID = fs.readFileSync(path.join(cfg.tmp, 'source_law_id.txt'), 'utf8').trim()
const articlesOnly = process.argv.includes('--articles-only')

async function patch(p, body) {
  const res = await fetch(`${cfg.SUPABASE_URL}/rest/v1/${p}`, {
    method: 'PATCH',
    headers: cfg.restHeaders({ Prefer: 'return=representation' }),
    body: JSON.stringify(body),
  })
  if (!res.ok) { console.error('PATCH failed:', res.status, await res.text()); process.exit(1) }
  return res.json()
}

async function main() {
  const arts = await patch(`law_articles?source_law_id=eq.${SOURCE_LAW_ID}&published=eq.false&select=id`, { published: true })
  console.log(`✓ Published ${arts.length} articles.`)
  if (!articlesOnly) {
    const law = await patch(`source_laws?id=eq.${SOURCE_LAW_ID}&select=code,published`, { published: true })
    console.log(`✓ Published source law: ${law[0]?.code} (published=${law[0]?.published}).`)
  }
  console.log(`\nLaw is live at /admin/files/insights/codex/${encodeURIComponent(cfg.code)}`)
}
main().catch((e) => { console.error('FATAL:', e); process.exit(1) })
