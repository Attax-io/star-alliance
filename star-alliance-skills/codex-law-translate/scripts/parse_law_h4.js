#!/usr/bin/env node
/**
 * Phase 1 — GENERIC H4-grammar parser (reusable across laws).
 *
 * Many firm extractions put MAIN articles at H4 `#### مادة N`, with the hierarchy:
 *   `## الباب/الكتاب` (H2) → `### الفصل/الفرع` (H3) → `#### مادة N` (H4 article)
 * and PROMULGATION articles at H3 `### مادة N إصدار` (or `### مادة إصدار N`).
 * The shared scripts/parse_law.js expects main articles at H3 and would mis-parse these.
 *
 * Mapping: chapter = last H2 (or non-title H1); section = last H3 that is NOT a
 * promulgation/table heading; section resets when chapter changes.
 *
 * Handles: bis (مكرر) with optional digit OR Arabic-letter suffix; both promulgation
 * forms (number-before/after إصدار); attached tables `### جدول رقم N` / `#### جدول رقم N`.
 * Skips H4 topic labels (non-article `#### …`) and H3 subsection labels — they carry no body.
 *
 * Output shape identical to the shared parser (consumed unchanged by insert_articles.js):
 *   <tmp>/articles.json  rows { idx, kind, article_number_ar, sort_order, chapter, section, content_ar }
 *   <tmp>/frontmatter.json
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
// promulgation: either "مادة N إصدار" or "مادة إصدار N"
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
  // H1 — book/part (skip the document-title line). Resets chapter+section.
  if ((m = lines[i].match(RE_H1))) {
    const t = m[1].trim()
    if (!t.startsWith(cfg.code)) { chapter = t; section = '' }
    i++; continue
  }
  // H2 — chapter (الباب/الكتاب/مواد الإصدار/الجداول). Resets section.
  if ((m = lines[i].match(RE_H2))) { chapter = m[1].trim(); section = ''; i++; continue }
  // H3 — promulgation article | table | section label
  if ((m = lines[i].match(RE_H3))) {
    const h = m[1].trim()
    let mm
    if ((mm = h.match(RE_PROMUL))) {
      const b = collectBody(i)
      articles.push({ kind: 'promulgation', _n: promNum(mm), article_number_ar: `مادة ${toAr(promNum(mm))} إصدار`, chapter, section, content_ar: b.text })
      i = b.next; continue
    }
    if ((mm = h.match(RE_TABLE))) {
      const title = (mm[2] || '').trim()
      const b = collectBody(i)
      articles.push({ kind: 'table', _n: +mm[1], article_number_ar: `جدول رقم ${toAr(mm[1])}`, chapter, section: title || section, content_ar: b.text })
      i = b.next; continue
    }
    section = h; i++; continue   // فصل/فرع subsection label
  }
  // H4 — main article | table | topic label (skip)
  if ((m = lines[i].match(RE_H4))) {
    const h = m[1].trim()
    let mm
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
    i++; continue   // topic label → structural only
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

/* ── Validation: reconcile against EVERY article/table heading in the source ── */
const counts = articles.reduce((acc, a) => ((acc[a.kind] = (acc[a.kind] || 0) + 1), acc), {})
const empties = articles.filter((a) => !a.content_ar || !a.content_ar.trim())
const srcPromul = (body.match(/^### مادة (?:\d+ إصدار|إصدار \d+)\s*$/gm) || []).length
const srcMain = (body.match(/^#### مادة \d+(?:\s+مكرر(?:\s+(?:\d+|[ء-ي]+))?)?\s*$/gm) || []).length
const srcTable = (body.match(/^#{3,4} جدول رقم \d+/gm) || []).length
// any #### مادة-like or ### مادة-like heading we failed to capture
const h4all = (body.match(/^#### مادة\b.*$/gm) || [])
const h4bad = h4all.filter((t) => !RE_MAIN.test(t.replace(/^#### /, '')))
const h3mada = (body.match(/^### مادة\b.*$/gm) || [])
const h3bad = h3mada.filter((t) => !RE_PROMUL.test(t.replace(/^### /, '')))

const reconcile = (label, got, src) => {
  const ok = got === src
  console.log(`  ${ok ? '✓' : '✗'} ${label}: parsed ${got} vs ${src} source headings${ok ? '' : ' — MISMATCH'}`)
  return ok
}

console.log(`Parsed ${articles.length} rows → ${path.join(cfg.tmp, 'articles.json')}`)
console.log(`Kind breakdown: ${JSON.stringify(counts)}`)
const okP = reconcile('promulgation (H3 …إصدار)', counts.promulgation || 0, srcPromul)
const okM = reconcile('main articles (H4 #### مادة N)', counts.main || 0, srcMain)
const okT = reconcile('tables (### / #### جدول رقم N)', counts.table || 0, srcTable)
console.log(`  ${empties.length === 0 ? '✓' : '✗'} content_ar non-empty: ${articles.length - empties.length}/${articles.length}` + (empties.length ? ` (EMPTY: ${empties.map((e) => e.article_number_ar).slice(0, 20).join(', ')})` : ''))
const bisCount = articles.filter((a) => a.article_number_ar.includes('مكرر')).length
if (bisCount) console.log(`  ℹ ${bisCount} bis (مكرر) articles captured`)
if (h4bad.length) console.log(`  ✗ ${h4bad.length} H4 مادة headings NOT captured: ${h4bad.slice(0, 8).join(' | ')}`)
if (h3bad.length) console.log(`  ℹ ${h3bad.length} H3 مادة headings treated as non-promulgation (check): ${h3bad.slice(0, 6).join(' | ')}`)
const sorted = [...numbers].sort((a, b) => a - b)
const gaps = []
for (let k = 1; k < sorted.length; k++) { if (sorted[k] !== sorted[k - 1] + 1 && sorted[k] !== sorted[k - 1]) gaps.push(`${sorted[k - 1]}→${sorted[k]}`) }
console.log(`  ℹ main numbers: min ${sorted[0]}, max ${sorted[sorted.length - 1]}, count ${numbers.length}${gaps.length ? `, gaps: ${gaps.slice(0, 12).join(' ')}${gaps.length > 12 ? ` (+${gaps.length - 12})` : ''}` : ', contiguous'}`)
console.log(`First: ${articles[0]?.article_number_ar} | chap="${articles[0]?.chapter}"`)
const fm2 = articles.find((a) => a.kind === 'main')
console.log(`First main: ${fm2?.article_number_ar} | chap="${fm2?.chapter}" | sec="${fm2?.section}"`)
console.log(`Last:  ${articles[articles.length - 1]?.article_number_ar} | chap="${articles[articles.length - 1]?.chapter}" | sec="${articles[articles.length - 1]?.section}"`)

const allOk = okP && okM && okT && empties.length === 0 && h4bad.length === 0
console.log(`\n${allOk ? '✓✓ VALIDATION PASSED' : '✗✗ VALIDATION FAILED — adjust parse_law_h4.js for this law.'}`)
process.exit(allOk ? 0 : 1)
