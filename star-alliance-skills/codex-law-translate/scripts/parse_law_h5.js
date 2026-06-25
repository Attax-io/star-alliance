#!/usr/bin/env node
/**
 * Phase 1 — GENERIC H5-grammar parser (reusable).
 *
 * Some firm extractions put MAIN articles at H5 `##### مادة N`, with hierarchy:
 *   `## الكتاب/الباب` (H2) → `### الباب` (H3) → `#### الفصل` (H4) → `##### مادة N` (H5 article)
 * and promulgation at H5 `##### مادة N إصدار` (or `##### مادة إصدار N`).
 *
 * Mapping: chapter = last H2 (or non-title H1); section = the DEEPEST non-article
 * heading seen since the last chapter (last of H3/H4); section resets on chapter change.
 *
 * Handles bis (مكرر) digit-or-Arabic-letter suffix; both promulgation forms; tables
 * `#### / ##### جدول رقم N`. Skips non-article H5 labels and H3/H4 structural headings.
 *
 * Output identical to the shared parser (consumed unchanged by insert_articles.js).
 */
const fs = require('fs')
const path = require('path')
const cfg = require('/Users/attaselim/.claude/skills/codex-law-translate/scripts/_config')

const AR_DIGITS = '٠١٢٣٤٥٦٧٨٩'
const toAr = (s) => String(s).replace(/\d/g, (d) => AR_DIGITS[+d])
const stripWikilinks = (s) =>
  s.replace(/\[\[([^\]|]+)\|([^\]]+)\]\]/g, '$2').replace(/\[\[([^\]]+)\]\]/g, '$1')

const RE_H1 = /^# (.+)$/
const RE_H2 = /^## (.+)$/
const RE_H3 = /^### (.+)$/
const RE_H4 = /^#### (.+)$/
const RE_H5 = /^##### (.+)$/
const RE_HEADING = /^#{1,6}\s/
const RE_PROMUL = /^مادة\s+(?:(\d+)\s+إصدار|إصدار\s+(\d+))\s*$/
const BIS = '(مكرر(?:\\s+(?:\\d+|[\\u0621-\\u064A]+))?)'
const RE_MAIN = new RegExp(`^مادة\\s+(\\d+)(?:\\s+${BIS})?\\s*$`)
const RE_TABLE = /^جدول\s+رقم\s+(\d+)\s*(?:—\s*(.+))?$/

const raw = fs.readFileSync(cfg.sourcePath, 'utf8')
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
    if (RE_HEADING.test(lines[i])) break
    out.push(lines[i])
  }
  while (out.length && out[0].trim() === '') out.shift()
  while (out.length && out[out.length - 1].trim() === '') out.pop()
  return { text: stripWikilinks(out.join('\n')).trim(), next: i }
}

const promNum = (mm) => +(mm[1] || mm[2])
const artNum = (n, bis) => `مادة ${toAr(n)}${bis ? ' ' + toAr(bis) : ''}`

let chapter = '', section = ''
const articles = []
let i = 0
while (i < lines.length) {
  let m
  if ((m = lines[i].match(RE_H1))) {
    const t = m[1].trim()
    if (!t.startsWith(cfg.code)) { chapter = t; section = '' }
    i++; continue
  }
  if ((m = lines[i].match(RE_H2))) { chapter = m[1].trim(); section = ''; i++; continue }
  if ((m = lines[i].match(RE_H3))) { section = m[1].trim(); i++; continue }      // باب
  if ((m = lines[i].match(RE_H4))) { section = m[1].trim(); i++; continue }      // فصل (overrides باب)
  if ((m = lines[i].match(RE_H5))) {
    const h = m[1].trim()
    let mm
    if ((mm = h.match(RE_PROMUL))) {
      const b = collectBody(i)
      articles.push({ kind: 'promulgation', _n: promNum(mm), article_number_ar: `مادة ${toAr(promNum(mm))} إصدار`, chapter, section, content_ar: b.text })
      i = b.next; continue
    }
    if ((mm = h.match(RE_MAIN))) {
      const b = collectBody(i)
      articles.push({ kind: 'main', _n: +mm[1], _bis: mm[2] || null, article_number_ar: artNum(mm[1], mm[2]), chapter: chapter || null, section: section || null, content_ar: b.text })
      i = b.next; continue
    }
    if ((mm = h.match(RE_TABLE))) {
      const title = (mm[2] || '').trim()
      const b = collectBody(i)
      articles.push({ kind: 'table', _n: +mm[1], article_number_ar: `جدول رقم ${toAr(mm[1])}`, chapter, section: title || section, content_ar: b.text })
      i = b.next; continue
    }
    i++; continue   // non-article H5 label → structural
  }
  i++
}

let pSeq = 0, mSeq = 0, tSeq = 0
articles.forEach((a) => {
  a.sort_order = a.kind === 'promulgation' ? ++pSeq : a.kind === 'main' ? 100 + (++mSeq) : 1000 + (++tSeq)
})
articles.sort((x, y) => x.sort_order - y.sort_order)
const numbers = articles.filter((a) => a.kind === 'main').map((a) => a._n)
articles.forEach((a, k) => { a.idx = k + 1; delete a._n; delete a._bis })

fs.writeFileSync(path.join(cfg.tmp, 'articles.json'), JSON.stringify(articles, null, 2))

const counts = articles.reduce((acc, a) => ((acc[a.kind] = (acc[a.kind] || 0) + 1), acc), {})
const empties = articles.filter((a) => !a.content_ar || !a.content_ar.trim())
const srcPromul = (body.match(/^##### مادة (?:\d+ إصدار|إصدار \d+)\s*$/gm) || []).length
const srcMain = (body.match(/^##### مادة \d+(?:\s+مكرر(?:\s+(?:\d+|[ء-ي]+))?)?\s*$/gm) || []).length
const srcTable = (body.match(/^#{4,5} جدول رقم \d+/gm) || []).length
const h5all = (body.match(/^##### مادة\b.*$/gm) || [])
const h5bad = h5all.filter((t) => { const x = t.replace(/^##### /, ''); return !RE_MAIN.test(x) && !RE_PROMUL.test(x) })

const reconcile = (label, got, src) => {
  const ok = got === src
  console.log(`  ${ok ? '✓' : '✗'} ${label}: parsed ${got} vs ${src} source headings${ok ? '' : ' — MISMATCH'}`)
  return ok
}
console.log(`Parsed ${articles.length} rows → ${path.join(cfg.tmp, 'articles.json')}`)
console.log(`Kind breakdown: ${JSON.stringify(counts)}`)
const okP = reconcile('promulgation (H5 …إصدار)', counts.promulgation || 0, srcPromul)
const okM = reconcile('main articles (H5 ##### مادة N)', counts.main || 0, srcMain)
const okT = reconcile('tables', counts.table || 0, srcTable)
console.log(`  ${empties.length === 0 ? '✓' : '✗'} content_ar non-empty: ${articles.length - empties.length}/${articles.length}` + (empties.length ? ` (EMPTY: ${empties.map((e) => e.article_number_ar).slice(0, 20).join(', ')})` : ''))
const bisCount = articles.filter((a) => a.article_number_ar.includes('مكرر')).length
if (bisCount) console.log(`  ℹ ${bisCount} bis (مكرر) articles captured`)
if (h5bad.length) console.log(`  ✗ ${h5bad.length} H5 مادة headings NOT captured: ${h5bad.slice(0, 8).join(' | ')}`)
const sorted = [...numbers].sort((a, b) => a - b)
const gaps = []
for (let k = 1; k < sorted.length; k++) { if (sorted[k] !== sorted[k - 1] + 1 && sorted[k] !== sorted[k - 1]) gaps.push(`${sorted[k - 1]}→${sorted[k]}`) }
console.log(`  ℹ main numbers: min ${sorted[0]}, max ${sorted[sorted.length - 1]}, count ${numbers.length}${gaps.length ? `, gaps: ${gaps.slice(0, 12).join(' ')}${gaps.length > 12 ? ` (+${gaps.length - 12})` : ''}` : ', contiguous'}`)
console.log(`First main: ${articles.find((a) => a.kind === 'main')?.article_number_ar} | chap="${articles.find((a) => a.kind === 'main')?.chapter}" | sec="${articles.find((a) => a.kind === 'main')?.section}"`)
console.log(`Last:  ${articles[articles.length - 1]?.article_number_ar} | chap="${articles[articles.length - 1]?.chapter}"`)
const allOk = okP && okM && okT && empties.length === 0 && h5bad.length === 0
console.log(`\n${allOk ? '✓✓ VALIDATION PASSED' : '✗✗ VALIDATION FAILED — adjust parse_law_h5.js for this law.'}`)
process.exit(allOk ? 0 : 1)
