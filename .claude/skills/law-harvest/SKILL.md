---
name: law-harvest
description: "The shared Architect + Translator craft for ingesting real law PDFs into a clean, verified Source-Law library — the feed for the legal codex. The Architect scans the Stock Laws folder, identifies each misnamed PDF by its content, renames to the canonical scheme, resolves conflicts, and queues an extraction; the Translator extracts the queued law verbatim — Arabic canonical, page-ranges intact, no paraphrase and no gaps — into Source Laws, then updates the index and writes a dated harvest digest. A certify gate between the halves proves the extraction is faithful and complete before it enters the library. Feeds codex-law-translate (which then translates and publishes). Use to bring real law PDFs into the library. Triggers: 'harvest the laws', 'process the stock laws', 'extract this law', 'identify these law PDFs', 'add laws to the source library', 'law harvest'. Differentiate from codex-law-translate (translate + publish) and db-rename-sweep (DB renames, not files)."
metadata:
  version: 1.0.0
type: Skill

---
# Law Harvest — the Architect · Translator's craft

This craft turns a folder of messy, misnamed, half-OCR'd law PDFs into a clean Source-Law library — the verified feed that every downstream translation, citation, and publication in Lex Council drinks from. You carry it two-handed: the Architect reads the scrolls, names them true, and queues them; the Translator drains them word for word into the library, page-ranges intact, and seals the harvest with a dated digest. One dropped clause downstream becomes a mistranslation in five languages; one renamed law with the wrong number becomes a citation that points at the wrong statute. The harvest is where the chain either holds or breaks.

## What it is / is not

- It is ingesting real statute PDFs into the Source-Law library. It is not `codex-law-translate` — that craft translates and publishes what you have already harvested; you feed it, you do not speak the law aloud yet.
- It is renaming PDF files on disk and in `Stock Laws/`. It is not `db-rename-sweep` — that craft renames database tables and columns; your blade never touches the schema.
- It is two-handed, not solo. The Architect must not extract; the Translator must not rename. The certify gate is the seam between the two halves and it must not be skipped.
- It is verbatim. Paraphrase is a category error here. You copy the law; you do not retell it.

## The craft

### The Architect's half — name what is true

1. Inventory `Stock Laws/`. List every PDF, capture its current filename, byte size, page count, and a content fingerprint (first-page text hash, if text-extractable).
2. Read the title block of every PDF. Identify the *real* law: jurisdiction, law number, year of issuance, and any amendments or consolidated version. Do not trust the filename.
3. Resolve identity conflicts before you rename: two files claiming to be the same law, one file containing two laws, an amendment merged into a base statute, a regulation masquerading as a law. Each gets its own entry in the conflicts log.
4. Rename to the canonical scheme: `Source Laws/<jurisdiction>/<law-type>-<number>-<year>[-amended].pdf`. Lowercase, hyphenated, no diacritics, no Arabic script in filenames. Move the file.
5. Write an extraction task: target path, page range (cover-to-cover unless the PDF is a known anthology), locale target `ar` (canonical), and a one-line "law ID" comment for the Translator.
6. Hand off. Do not extract. Do not "just peek at the body". The handoff is the gate.

### The certify gate

Before the Translator opens the file, the Architect's metadata must be self-evident: correct path, correct page count, correct law ID, no remaining conflict. If the Translator cannot verify these three from the file alone in under a minute, the Architect re-does the queue. No silent fixes.

### The Translator's half — drain it word for word

1. Take one queued task. Open the PDF, confirm page count matches the queue, confirm the law on page one matches the law ID in the task.
2. Extract page-by-page. Preserve line breaks where the source has them. Preserve Arabic RTL flow. Preserve diacritics, taqrid clauses, footnote markers, and the law's own numbering — including sub-clauses like ٣/١/أ.
3. If the PDF is image-only, run OCR with a verified Arabic model and flag the harvest as `ocr-derived` in the digest. Never silently mix OCR'd pages with native text pages in the same file.
4. Write to `Source Laws/<jurisdiction>/<law-type>-<number>-<year>[-amended].md`. Wrap with a YAML header carrying: law ID, jurisdiction, source PDF path, source SHA-256, page count, harvest date, harvester, and a `verbatim: true` flag.
5. Update the Source Laws index (the JSON manifest the codex reads). Mark the law as `harvested` and ready for `codex-law-translate`.
6. Write the dated harvest digest to `logs/harvests/YYYY-MM-DD.md`: files processed, page totals, conflicts resolved, pages flagged OCR or skipped. The digest is the audit trail; if a downstream translator is wrong, the digest is where you begin the trace.

## Sharpening the craft

**Apprentice.** You can rename a clean file and drain a clean PDF. You cannot yet tell a taqrid from a law, a regulation from a statute, or a consolidation from an amendment. You read the first page and stop. You are dangerous here — you will rename confidently and be wrong. Measure yourself: how often does a downstream translator report a "wrong law" against your harvest?

**Journeyman.** You read cover, preamble, and the law's own closing. You spot merged-PDFs, you handle conflicts, you run the certify gate alone, and you write a digest that is actually useful in a postmortem. Your OCR-derived harvests are correctly flagged. You still occasionally drop a footnote or a schedule.

**Master.** You build pre-flight heuristics so the Architect's queue is right the first time. You recognize a malformed PDF by its shadow — wrong metadata, mismatched TOC, suspicious page count — and you reject the queue before a single word is drained. You can reverse-trace a bad harvest back to the exact page and line where the chain broke, using only the digest and the source SHA. You have read enough statutes to know when "as amended in 2019" is part of the title and when it is a separate instrument.

The honest measure of this craft is not how fast you harvest. It is how many downstream translations are wrong because of you. Aim for zero. Then keep aiming.

## Gotchas

- **Text layers that lie.** A PDF can report a text layer and still be image-only on certain pages (scanned inserts). Sample mid-document pages, not just page one.
- **RTL bidi traps.** Extraction tools sometimes flip Arabic punctuation or split diacritics from their base letters. Render the extracted file and compare visually before you commit.
- **Cover page ≠ law.** Decrees, royal preambles, and ministerial introductions are part of the instrument; press releases and ministry letterhead are not. Know the difference.
- **Consolidations vs amendments.** "As amended" can mean the consolidated text or a pointer to a separate amendment law. Read the source's own statement; do not guess.
- **Footnotes and schedules.** Both are law. Both get extracted. Skipping them is a silent omission and surfaces as a missing citation six months later.
- **Two laws, one PDF.** Common with annual legislative compendia. Split at the page where the second law's title block begins; do not let it bleed.
- **Encrypted / watermarked PDFs.** Some jurisdictions ship protected files. Decrypt or request clean copies; do not harvest through the watermark.
- **Diacritics in filenames.** They break tooling across OSes. Canonical filenames are ASCII only; the Arabic title lives in the file header, not the path.

## Versioning
Own skill. Bump `metadata.version` on any change (PATCH: wording/refs · MINOR: new mode/section · MAJOR: method contract change). Regenerate `VERSIONS.md` with `python3 star-alliance-skills/skillsmith/scripts/skill_registry.py write` after a bump, then `python3 build.py`.

## Changelog
- **1.0.0** — Initial release. The Architect+Translator craft for ingesting law PDFs verbatim into the verified Source-Law library.
