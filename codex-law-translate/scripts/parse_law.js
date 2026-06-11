#!/usr/bin/env node
/**
 * Phase 1 — Parse a firm "Legal Memos" Arabic markdown extraction → JSON.
 *
 * Output: <tmp>/articles.json  (rows: { idx, kind, article_number_ar, sort_order, chapter, section, content_ar })
 *         <tmp>/frontmatter.json (the YAML front-matter, parsed shallowly)
 *
 * kind ∈ 'promulgation' | 'main' | 'table'
 * sort_order: promulgation 1..N ; main 100+N ; table 300+N (tables last)
 *
 * HEADING GRAMMAR (edit the regexes below if a new law's markdown differs — the validation
 * asserts at the end will flag a mis-parse):
 *   ## مواد الإصدار / ## الباب … / ## الجداول الملحقة   → chapter boundary (resets section)
 *   ### الفصل …                                          → section boundary
 *   ### مادة N إصدار                                     → promulgation article
 *   ### مادة N                                           → main article (form A)
 *   ### Article N — مادة N                               → main article (form B)
 *   ### جدول رقم N — <title>                             → attached table
 * Body = lines after the heading until the next `## `/`### ` (so `#### `/`##### `/`| … |` stay in tables).
 */
const fs = require('fs')
const path = require('path')
const cfg = require('./_config')

const AR_DIGITS = '٠١٢٣٤٥٦٧٨٩'
const toAr = (s) => String(s).replace(/\d/g, (d) => AR_DIGITS[+d])
const stripWikilinks = (s) =>
  s.replace(/\[\[([^\]|]+)\|([^\]]+)\]\]/g, '$2').replace(/\[\[([^\]]+)\]\]/g, '$1')

const RE_H2      = /^## (.+)$/
const RE_H3      = /^### (.+)$/
const RE_PROMUL  = /^مادة\s+(\d+)\s+إصدار\s*$/
const RE_MAIN_A  = /^مادة\s+(\d+)\s*$/
const RE_MAIN_B  = /^Article\s+(\d+)\s+—\s+مادة\s+(\d+)\s*$/
const RE_TABLE   = /^جدول\s+رقم\s+(\d+)\s*(?:—\s*(.+))?$/
const RE_SECTION = /^الفصل\b/

const raw = fs.readFileSync(cfg.sourcePath, 'utf8')

// Shallow YAML front-matter parse (key: value + simple lists)
const fm = {}
const fmMatch = raw.match(/^---\n([\s\S]*?)\n---\n/)
if (fmMatch) {
  for (const line of fmMatch[1].split('\n')) {
    const m = line.match(/^([A-Za-z_]+):\s*(.*)$/)
    if (m) fm[m[1]] = m[2].replace(/^["']|["']$/g, '').trim()
  }
}
fs.writeFileSync(path.join(cfg.tmp, 'frontmatter.json'), JSON.stringify(fm, null, 2))

const body = raw.replace(/^---\n[\s\S]*?\n---\n/, '')
const lines = body.split('\n')

function collectBody(startIdx) {
  const out = []
  let i = startIdx + 1
  for (; i < lines.length; i++) {
    if (RE_H2.test(lines[i]) || RE_H3.test(lines[i])) break
    out.push(lines[i])
  }
  while (out.length && out[0].trim() === '') out.shift()
  while (out.length && out[out.length - 1].trim() === '') out.pop()
  return { text: stripWikilinks(out.join('\n')).trim(), next: i }
}

let chapter = '', section = ''
const articles = []
let i = 0
while (i < lines.length) {
  let m = lines[i].match(RE_H2)
  if (m) { chapter = m[1].trim(); section = ''; i++; continue }
  m = lines[i].match(RE_H3)
  if (m) {
    const h = m[1].trim()
    let mm
    if ((mm = h.match(RE_PROMUL))) {
      const b = collectBody(i)
      articles.push({ kind: 'promulgation', _num: +mm[1], article_number_ar: `مادة ${toAr(mm[1])} إصدار`, chapter, section, content_ar: b.text })
      i = b.next; continue
    }
    if ((mm = h.match(RE_MAIN_B))) {
      const b = collectBody(i)
      articles.push({ kind: 'main', _num: +mm[2], article_number_ar: `مادة ${toAr(mm[2])}`, chapter, section, content_ar: b.text })
      i = b.next; continue
    }
    if ((mm = h.match(RE_MAIN_A))) {
      const b = collectBody(i)
      articles.push({ kind: 'main', _num: +mm[1], article_number_ar: `مادة ${toAr(mm[1])}`, chapter, section, content_ar: b.text })
      i = b.next; continue
    }
    if ((mm = h.match(RE_TABLE))) {
      const title = (mm[2] || '').trim()
      const b = collectBody(i)
      articles.push({ kind: 'table', _num: +mm[1], article_number_ar: `جدول رقم ${toAr(mm[1])}`, chapter, section: title || section, content_ar: b.text })
      i = b.next; continue
    }
    if (RE_SECTION.test(h)) { section = h; i++; continue }
    section = h; i++; continue   // unknown ### → treat as section marker (defensive)
  }
  i++
}

articles.forEach((a) => {
  a.sort_order = a.kind === 'promulgation' ? a._num : a.kind === 'main' ? 100 + a._num : 300 + a._num
})
articles.sort((x, y) => x.sort_order - y.sort_order)
articles.forEach((a, k) => { a.idx = k + 1; delete a._num })

fs.writeFileSync(path.join(cfg.tmp, 'articles.json'), JSON.stringify(articles, null, 2))

/* ── Validation ── */
const counts = articles.reduce((acc, a) => ((acc[a.kind] = (acc[a.kind] || 0) + 1), acc), {})
const mainNums = articles.filter((a) => a.kind === 'main').map((a) => a.sort_order - 100).sort((p, q) => p - q)
const promulNums = articles.filter((a) => a.kind === 'promulgation').map((a) => a.sort_order).sort((p, q) => p - q)
const empties = articles.filter((a) => !a.content_ar || !a.content_ar.trim())

function contiguous(nums, label, from) {
  const exp = Array.from({ length: nums.length }, (_, k) => from + k)
  const ok = nums.length === exp.length && nums.every((v, k) => v === exp[k])
  console.log(`  ${ok ? '✓' : '✗'} ${label}: ${nums.length} numbers ${nums[0] ?? '-'}–${nums[nums.length - 1] ?? '-'} ${ok ? 'contiguous' : 'GAPS/DUPS → ' + JSON.stringify(exp.filter((v) => !nums.includes(v)).slice(0, 30))}`)
  return ok
}

console.log(`Parsed ${articles.length} rows → ${path.join(cfg.tmp, 'articles.json')}`)
console.log(`Kind breakdown: ${JSON.stringify(counts)}`)
const okP = articles.some((a) => a.kind === 'promulgation') ? contiguous(promulNums, 'promulgation', 1) : true
const okM = contiguous(mainNums, 'main articles', 1)
console.log(`  ${empties.length === 0 ? '✓' : '✗'} content_ar non-empty: ${articles.length - empties.length}/${articles.length}` + (empties.length ? ` (EMPTY: ${empties.map((e) => e.article_number_ar).join(', ')})` : ''))
console.log(`  tables: ${counts.table || 0}`)
console.log(`First: ${articles[0]?.article_number_ar} | chap="${articles[0]?.chapter}"`)
console.log(`Last:  ${articles[articles.length - 1]?.article_number_ar} | sec="${articles[articles.length - 1]?.section}"`)

const allOk = okP && okM && empties.length === 0
console.log(`\n${allOk ? '✓✓ VALIDATION PASSED — review the breakdown, then proceed.' : '✗✗ VALIDATION FAILED — adjust the heading regexes in parse_law.js for this law.'}`)
process.exit(allOk ? 0 : 1)
