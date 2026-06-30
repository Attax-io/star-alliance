#!/usr/bin/env node
/**
 * Upsert <tmp>/translations.json into law_article_translations (locales × articles).
 * on_conflict=law_article_id,locale → safe to re-run after a review pass.
 */
const fs = require('fs')
const path = require('path')
const cfg = require('./_config')

const articles = JSON.parse(fs.readFileSync(path.join(cfg.tmp, 'articles.json'), 'utf8'))
const ID_MAP = JSON.parse(fs.readFileSync(path.join(cfg.tmp, 'article_ids.json'), 'utf8'))
const TX = JSON.parse(fs.readFileSync(path.join(cfg.tmp, 'translations.json'), 'utf8'))
const url = `${cfg.SUPABASE_URL}/rest/v1/law_article_translations?on_conflict=law_article_id,locale`

async function main() {
  const rows = []
  for (const a of articles) {
    const tx = TX[a.sort_order], id = ID_MAP[a.sort_order]
    if (!tx || !id) { console.warn(`skip sort ${a.sort_order}`); continue }
    for (const locale of cfg.locales) {
      const v = tx[locale]; if (!v) continue
      rows.push({
        law_article_id: id, locale,
        content: v.content ?? '',
        article_number: v.article_number || null,
        chapter: v.chapter || null,
        section: v.section || null,
      })
    }
  }
  console.log(`Upserting ${rows.length} translation rows…`)
  const CHUNK = 100
  for (let i = 0; i < rows.length; i += CHUNK) {
    const res = await fetch(url, { method: 'POST', headers: cfg.restHeaders({ Prefer: 'resolution=merge-duplicates,return=minimal' }), body: JSON.stringify(rows.slice(i, i + CHUNK)) })
    if (!res.ok) { console.error('Upsert failed:', res.status, await res.text()); process.exit(1) }
    console.log(`  …${Math.min(i + CHUNK, rows.length)}/${rows.length}`)
  }
  console.log(`✓ Upserted ${rows.length} rows.`)
}
main().catch((e) => { console.error('FATAL:', e); process.exit(1) })
