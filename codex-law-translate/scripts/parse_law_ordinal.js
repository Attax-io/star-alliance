#!/usr/bin/env node
/**
 * Phase 1 — "المادة" (with al-) + spelled-ordinal grammar parser. Built for Y2017 L213
 * (Trade Union Organizations Law), reusable for any law in this shape:
 *   - chapters `## الباب / ## مواد الإصدار` (H2)
 *   - sections `### الفصل …` (H3)
 *   - promulgation `### المادة الأولى … السادسة` (H3, spelled-out ordinal)
 *   - main `### المادة N` (H3, digit; bis-tolerant)
 *
 * Normalises article_number_ar to the codex house format: promulgation `مادة N إصدار`,
 * main `مادة N` (drops the al-). Output identical to the shared parser.
 */
const fs = require('fs')
const path = require('path')
const cfg = require('/Users/attaselim/.claude/skills/codex-law-translate/scripts/_config')

const AR_DIGITS = '٠١٢٣٤٥٦٧٨٩'
const toAr = (s) => String(s).replace(/\d/g, (d) => AR_DIGITS[+d])
const stripWikilinks = (s) =>
  s.replace(/\[\[([^\]|]+)\|([^\]]+)\]\]/g, '$2').replace(/\[\[([^\]]+)\]\]/g, '$1')

const ORDINALS = {
  'الأولى': 1, 'الاولى': 1, 'الثانية': 2, 'الثالثة': 3, 'الرابعة': 4, 'الخامسة': 5,
  'السادسة': 6, 'السابعة': 7, 'الثامنة': 8, 'التاسعة': 9, 'العاشرة': 10,
  'الحادية عشرة': 11, 'الثانية عشرة': 12,
}

const RE_H2 = /^## (.+)$/
const RE_H3 = /^### (.+)$/
const RE_SECTION = /^الفصل\b/
const BIS = '(مكرر(?:\\s+(?:\\d+|[\\u0621-\\u064A]+))?)'
const RE_MAIN = new RegExp(`^المادة\\s+(\\d+)(?:\\s+${BIS})?\\s*$`)
const RE_PROMUL_ORD = new RegExp(`^المادة\\s+(${Object.keys(ORDINALS).join('|')})\\s*$`)

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
    if (RE_H2.test(lines[i]) || RE_H3.test(lines[i])) break
    out.push(lines[i])
  }
  while (out.length && out[0].trim() === '') out.shift()
  while (out.length && out[out.length - 1].trim() === '') out.pop()
  return { text: stripWikilinks(out.join('\n')).trim(), next: i }
}

const artNum = (n, bis) => `مادة ${toAr(n)}${bis ? ' ' + toAr(bis) : ''}`

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
    if ((mm = h.match(RE_PROMUL_ORD))) {
      const n = ORDINALS[mm[1]]
      const b = collectBody(i)
      articles.push({ kind: 'promulgation', _n: n, article_number_ar: `مادة ${toAr(n)} إصدار`, chapter, section, content_ar: b.text })
      i = b.next; continue
    }
    if ((mm = h.match(RE_MAIN))) {
      const b = collectBody(i)
      articles.push({ kind: 'main', _n: +mm[1], _bis: mm[2] || null, article_number_ar: artNum(mm[1], mm[2]), chapter, section, content_ar: b.text })
      i = b.next; continue
    }
    if (RE_SECTION.test(h)) { section = h; i++; continue }
    section = h; i++; continue
  }
  i++
}

let pSeq = 0, mSeq = 0
articles.forEach((a) => { a.sort_order = a.kind === 'promulgation' ? ++pSeq : 100 + (++mSeq) })
articles.sort((x, y) => x.sort_order - y.sort_order)
const numbers = articles.filter((a) => a.kind === 'main').map((a) => a._n)
articles.forEach((a, k) => { a.idx = k + 1; delete a._n; delete a._bis })

fs.writeFileSync(path.join(cfg.tmp, 'articles.json'), JSON.stringify(articles, null, 2))

const counts = articles.reduce((acc, a) => ((acc[a.kind] = (acc[a.kind] || 0) + 1), acc), {})
const empties = articles.filter((a) => !a.content_ar || !a.content_ar.trim())
const h3s = lines.map((l) => { const m = l.match(RE_H3); return m ? m[1].trim() : null }).filter(Boolean)
const srcP = h3s.filter((t) => RE_PROMUL_ORD.test(t)).length
const srcMain = h3s.filter((t) => RE_MAIN.test(t)).length
const unrec = h3s.filter((t) => /^المادة\b/.test(t) && !RE_PROMUL_ORD.test(t) && !RE_MAIN.test(t))

const reconcile = (label, got, src) => { const ok = got === src; console.log(`  ${ok ? '✓' : '✗'} ${label}: parsed ${got} vs ${src}${ok ? '' : ' — MISMATCH'}`); return ok }
console.log(`Parsed ${articles.length} rows → ${path.join(cfg.tmp, 'articles.json')}`)
console.log(`Kind breakdown: ${JSON.stringify(counts)}`)
const okP = reconcile('promulgation (### المادة <ordinal>)', counts.promulgation || 0, srcP)
const okM = reconcile('main (### المادة N)', counts.main || 0, srcMain)
console.log(`  ${empties.length === 0 ? '✓' : '✗'} content_ar non-empty: ${articles.length - empties.length}/${articles.length}` + (empties.length ? ` (EMPTY: ${empties.map((e) => e.article_number_ar).slice(0, 20).join(', ')})` : ''))
const bisCount = articles.filter((a) => a.article_number_ar.includes('مكرر')).length
if (bisCount) console.log(`  ℹ ${bisCount} bis (مكرر) articles captured`)
if (unrec.length) console.log(`  ✗ ${unrec.length} UNRECOGNIZED المادة headings: ${unrec.slice(0, 10).join(' | ')}`)
const sorted = [...numbers].sort((a, b) => a - b)
const gaps = []
for (let k = 1; k < sorted.length; k++) { if (sorted[k] !== sorted[k - 1] + 1 && sorted[k] !== sorted[k - 1]) gaps.push(`${sorted[k - 1]}→${sorted[k]}`) }
console.log(`  ℹ main numbers: min ${sorted[0]}, max ${sorted[sorted.length - 1]}, count ${numbers.length}${gaps.length ? `, gaps: ${gaps.slice(0, 12).join(' ')}` : ', contiguous'}`)
console.log(`First main: ${articles.find((a) => a.kind === 'main')?.article_number_ar} | chap="${articles.find((a) => a.kind === 'main')?.chapter}"`)
const allOk = okP && okM && empties.length === 0 && unrec.length === 0
console.log(`\n${allOk ? '✓✓ VALIDATION PASSED' : '✗✗ VALIDATION FAILED'}`)
process.exit(allOk ? 0 : 1)
