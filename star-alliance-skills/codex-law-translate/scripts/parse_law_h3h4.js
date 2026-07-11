#!/usr/bin/env node
/**
 * Phase 1 — MIXED H3+H4 main-article parser (reusable).
 *
 * Built for Y2018 L181 (Consumer Protection), whose first two main articles sit at
 * H3 `### مادة 1` / `### مادة 2` while the rest sit at H4 `#### مادة N`. The pure-H4
 * parser silently turns those H3 articles into section labels (data loss). This parser
 * accepts a main article at EITHER level.
 *
 * Hierarchy: chapter = last H2; section = last H3 that is a structural label (الباب/الفصل),
 * NOT an article/promulgation/table. Promulgation at H3 `### مادة N إصدار`. Tables H3/H4.
 * Output identical to the shared parser.
 */
const fs = require('fs')
const path = require('path')
const cfg = require(require('os').homedir() + '/.claude/skills/codex-law-translate/scripts/_config')

const AR_DIGITS = '٠١٢٣٤٥٦٧٨٩'
const toAr = (s) => String(s).replace(/\d/g, (d) => AR_DIGITS[+d])
const stripWikilinks = (s) =>
  s.replace(/\[\[([^\]|]+)\|([^\]]+)\]\]/g, '$2').replace(/\[\[([^\]]+)\]\]/g, '$1')

const RE_H1 = /^# (.+)$/
const RE_H2 = /^## (.+)$/
const RE_H3 = /^### (.+)$/
const RE_H4 = /^#### (.+)$/
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

function tryArticle(h, i, out) {
  let mm
  if ((mm = h.match(RE_PROMUL))) {
    const b = collectBody(i)
    out.push({ kind: 'promulgation', _n: promNum(mm), article_number_ar: `مادة ${toAr(promNum(mm))} إصدار`, chapter: cur.chapter, section: cur.section, content_ar: b.text })
    return b.next
  }
  if ((mm = h.match(RE_MAIN))) {
    const b = collectBody(i)
    out.push({ kind: 'main', _n: +mm[1], _bis: mm[2] || null, article_number_ar: artNum(mm[1], mm[2]), chapter: cur.chapter || null, section: cur.section || null, content_ar: b.text })
    return b.next
  }
  if ((mm = h.match(RE_TABLE))) {
    const title = (mm[2] || '').trim()
    const b = collectBody(i)
    out.push({ kind: 'table', _n: +mm[1], article_number_ar: `جدول رقم ${toAr(mm[1])}`, chapter: cur.chapter, section: title || cur.section, content_ar: b.text })
    return b.next
  }
  return -1
}

const cur = { chapter: '', section: '' }
const articles = []
let i = 0
while (i < lines.length) {
  let m
  if ((m = lines[i].match(RE_H1))) { const t = m[1].trim(); if (!t.startsWith(cfg.code)) { cur.chapter = t; cur.section = '' } i++; continue }
  if ((m = lines[i].match(RE_H2))) { cur.chapter = m[1].trim(); cur.section = ''; i++; continue }
  if ((m = lines[i].match(RE_H3))) {
    const h = m[1].trim()
    const next = tryArticle(h, i, articles)
    if (next >= 0) { i = next; continue }
    cur.section = h; i++; continue   // الباب/الفصل structural label
  }
  if ((m = lines[i].match(RE_H4))) {
    const h = m[1].trim()
    const next = tryArticle(h, i, articles)
    if (next >= 0) { i = next; continue }
    i++; continue   // H4 topic label → structural
  }
  i++
}

let pSeq = 0, mSeq = 0, tSeq = 0
articles.forEach((a) => { a.sort_order = a.kind === 'promulgation' ? ++pSeq : a.kind === 'main' ? 100 + (++mSeq) : 1000 + (++tSeq) })
articles.sort((x, y) => x.sort_order - y.sort_order)
const numbers = articles.filter((a) => a.kind === 'main').map((a) => a._n)
articles.forEach((a, k) => { a.idx = k + 1; delete a._n; delete a._bis })

fs.writeFileSync(path.join(cfg.tmp, 'articles.json'), JSON.stringify(articles, null, 2))

const counts = articles.reduce((acc, a) => ((acc[a.kind] = (acc[a.kind] || 0) + 1), acc), {})
const empties = articles.filter((a) => !a.content_ar || !a.content_ar.trim())
// source counts: main = any ### or #### "مادة N" that is NOT إصدار
const srcMain = (body.match(/^#{3,4} مادة \d+(?:\s+مكرر(?:\s+(?:\d+|[ء-ي]+))?)?\s*$/gm) || []).length
const srcPromul = (body.match(/^### مادة (?:\d+ إصدار|إصدار \d+)\s*$/gm) || []).length
const srcTable = (body.match(/^#{3,4} جدول رقم \d+/gm) || []).length

const reconcile = (label, got, src) => { const ok = got === src; console.log(`  ${ok ? '✓' : '✗'} ${label}: parsed ${got} vs ${src}${ok ? '' : ' — MISMATCH'}`); return ok }
console.log(`Parsed ${articles.length} rows → ${path.join(cfg.tmp, 'articles.json')}`)
console.log(`Kind breakdown: ${JSON.stringify(counts)}`)
const okP = reconcile('promulgation (### مادة N إصدار)', counts.promulgation || 0, srcPromul)
const okM = reconcile('main (### or #### مادة N)', counts.main || 0, srcMain)
const okT = reconcile('tables', counts.table || 0, srcTable)
console.log(`  ${empties.length === 0 ? '✓' : '✗'} content_ar non-empty: ${articles.length - empties.length}/${articles.length}` + (empties.length ? ` (EMPTY: ${empties.map((e) => e.article_number_ar).slice(0, 20).join(', ')})` : ''))
const bisCount = articles.filter((a) => a.article_number_ar.includes('مكرر')).length
if (bisCount) console.log(`  ℹ ${bisCount} bis (مكرر) articles captured`)
const sorted = [...numbers].sort((a, b) => a - b)
const gaps = []
for (let k = 1; k < sorted.length; k++) { if (sorted[k] !== sorted[k - 1] + 1 && sorted[k] !== sorted[k - 1]) gaps.push(`${sorted[k - 1]}→${sorted[k]}`) }
console.log(`  ℹ main numbers: min ${sorted[0]}, max ${sorted[sorted.length - 1]}, count ${numbers.length}${gaps.length ? `, gaps: ${gaps.slice(0, 12).join(' ')}` : ', contiguous'}`)
console.log(`First main: ${articles.find((a) => a.kind === 'main')?.article_number_ar} | chap="${articles.find((a) => a.kind === 'main')?.chapter}"`)
console.log(`Last:  ${articles[articles.length - 1]?.article_number_ar} | chap="${articles[articles.length - 1]?.chapter}"`)
const allOk = okP && okM && okT && empties.length === 0
console.log(`\n${allOk ? '✓✓ VALIDATION PASSED' : '✗✗ VALIDATION FAILED'}`)
process.exit(allOk ? 0 : 1)
