# Mode: language — full recipe

The end-to-end recipe. The companion script
`scripts/i18n_cleanup.py` owns the mechanical detect/apply/verify steps;
this section owns the agent orchestration that sits between them.

#### Step L1 — Detect scope

Run from the repo root:

```bash
python3 ~/.claude/skills/cleanup/scripts/i18n_cleanup.py detect
```

This writes 5 files to `/tmp/translation_targets_{loc}.json` (one per
non-EN locale) — each is a JSON array of `{ns, key, en}` triples where
the locale's value still equals the EN value (the
`isRowUntranslated` heuristic the Languages dev-tools panel uses).

Default behavior translates ALL flagged strings. To skip ES/FR
single-word-no-placeholder cognates (e.g. "Finances", "Documents"),
pass `--skip-cognates`. By default Atta has rejected this filter —
keep that as the project default unless he says otherwise this session.

Show the user the per-locale counts and ask whether to proceed. If the
total is large (>500), surface the top 3 namespaces by count so they
know where the work is concentrated.

#### Step L2 — Spawn 5 parallel translation agents

Spawn 5 general-purpose subagents **in a single message** (so they run
concurrently). Each gets the per-locale agent prompt from §"Agent prompt
templates" below, with the locale-specific bits filled in.

Use `run_in_background: true` for each. The user's terminal will
notify you as each completes — do NOT poll.

Hard contract every agent must satisfy:

- Read its target file (`/tmp/translation_targets_{loc}.json`).
- Translate each `en` field per the locale-specific register guidance.
- Preserve every `{placeholder}` exactly (no translating variable
  names; Russian may reorder placeholders due to grammatical case —
  that's OK).
- Keep brand glossary terms in Latin script (see §Brand glossary).
- Return identical count, same order as input.
- Write output to `/tmp/translations_{loc}.json` as a pure JSON array
  of `{ns, key, translated}` — no markdown fences, no commentary.

#### Step L3 — Pre-flight + apply

When all 5 agents have completed:

```bash
python3 ~/.claude/skills/cleanup/scripts/i18n_cleanup.py apply
```

This runs pre-flight (count match, placeholder match, no empty
translations) **before** touching any messages file. If any locale
fails pre-flight, the script aborts unless `--force` is set. Surface
the failure to the user and ask before forcing.

On pass, the script writes each translation into
`messages/{loc}/{ns}.json` via a dotted-key nested-dict walker. JSON
structure + indentation + trailing newlines preserved.

#### Step L4 — Verify

```bash
python3 ~/.claude/skills/cleanup/scripts/i18n_cleanup.py verify
cd lex_council && npx turbo run check-types --filter=web
```

The verify step re-runs the detector and prints the new untranslated
counts per locale. Expect the number to drop sharply but **NOT** reach
zero — the floor is brand acronyms + form placeholders
(`email@example.com`, `0.00`, etc.) + ES/FR cognates that are
correctly identical to English. Report the delta (before → after) to
the user.

`tsc` should pass cleanly — JSON edits can't break types but it's
worth confirming nothing else regressed.

#### Step L5 — Vault log

Delegate to the **vault-log-compliance** skill. Provide it a one-line
summary of what changed (locale counts + delta) so it can draft an
entry similar to `2026-05-28_translation-pass-non-en-locales.md`.

Then update auto-memory if anything surprising came up during the pass
(new brand terms to add to the glossary, a locale-specific gotcha,
etc.).

---

## Brand glossary

These terms stay in Latin script across every locale. Every agent prompt
must enumerate them. Source of truth lives in
`scripts/i18n_cleanup.py:BRAND_OR_CODE` — keep them in sync when adding
new terms.

```
Lex Council, LexCouncil, Lex
POA, NDA, OTP
GFN, MFN, BFN, SFN, AFN, FN
HR, CSV, PDF, URL, UI, API, JSON, SQL, RLS, RPC
TSL, WHBD, KPI, UUID, ID, IDs
CIS, P&L, TM, PM, GCal, BC
```

Plus: any single-char string, any pure-digit string, any all-caps
1–4-letter token, any string of pure punctuation.

## Locale contracts

These are the register/style constraints each translation agent must
follow. Encoded as the locale-specific override in §Agent prompt
templates.

| Locale | Register | Notes |
|---|---|---|
| **ar** | Modern Standard Arabic (فصحى) | NOT Egyptian colloquial, NOT Levantine. Formal pan-Arabic legal/business. |
| **es** | Neutral professional Spanish | Latin American–biased but acceptable to Spain. Use proper accents (á é í ó ú ñ ¿ ¡). Formal "usted" form. Cognates kept where natural ("Total"); accents added where required ("Vídeo"). |
| **fr** | Standard European French | Formal legal/business register. Use "vous" form. Proper accents (é è ê ç à ù ô). Cognates kept identical where natural ("Finances", "Documents", "Notifications", "Transactions"); accents added where missing ("Détails"). |
| **ru** | Standard professional Russian | Formal "вы". Russian grammatical case may reorder placeholders — that's required, not a violation. |
| **zh** | Simplified Chinese (简体中文) | Mainland register, NOT Traditional. Use full-width sentence punctuation (，。：；！？) but half-width for placeholders and brand. Arabic numerals (1, 2, 3), not 一二三. |

## Agent prompt templates

Use these verbatim when spawning the 5 subagents (subagent_type:
`general-purpose`, `run_in_background: true`). Each prompt is a
self-contained brief — the agent has no memory of this conversation, so
context like "what is Lex Council" must be in the prompt itself.

### Per-locale prompt skeleton

```text
You are a professional translator for a legal practice management SaaS
called Lex Council. The app manages legal matters (cases, tasks, documents,
files), members (attorneys/staff), and clients. Tone: formal, professional,
B2B SaaS, suitable for lawyers and administrators.

Your task: translate {COUNT} English strings into {LOCALE_NAME} —
{REGISTER_GUIDANCE}.

Input file: /tmp/translation_targets_{LOCALE}.json — a JSON array of
{ns, key, en} objects.
Output file: /tmp/translations_{LOCALE}.json — write a JSON array of
{ns, key, translated} objects, one per input entry, **same order**, **same
count ({COUNT})**.

Hard rules — non-negotiable:

1. Preserve every {placeholder} exactly. Do not translate variable names.
2. Brand/acronym glossary — keep in Latin script:
   Lex Council, POA, NDA, OTP, HR, CSV, PDF, URL, UI, API, JSON, SQL, RLS,
   RPC, KPI, UUID, ID, CIS, P&L, TM, PM, GFN, MFN, BFN, SFN, AFN, FN, WHBD,
   GCal, BC.
3. {COGNATE_NOTE}
4. Numbers, dates, percentages stay as-is unless embedded in a translated
   phrase.
5. Output count must equal input count ({COUNT}).
6. Output is pure JSON — no markdown fences, no commentary. Write directly
   to /tmp/translations_{LOCALE}.json.

{TONE_EXAMPLES}

Process:
1. Read /tmp/translation_targets_{LOCALE}.json in full.
2. Translate each entry. Use the `ns` field as context for register.
3. Write the result as a single JSON array.
4. Reply: "Wrote N translations to /tmp/translations_{LOCALE}.json".
```

### Per-locale fills

| Locale | LOCALE_NAME / REGISTER_GUIDANCE | COGNATE_NOTE | TONE_EXAMPLES |
|---|---|---|---|
| **ar** | Modern Standard Arabic (MSA / فصحى) — NOT Egyptian colloquial, NOT Levantine — neutral pan-Arabic legal/business register | Not applicable (different script). | "Loading…" → "جارٍ التحميل…", "Approved {noun}{suffix}" → "تم اعتماد {noun}{suffix}", "Pending" → "قيد الانتظار" |
| **es** | neutral professional Spanish — Latin American–biased but acceptable to Spain, formal "usted" register, include proper accents | Cognates are OK to keep identical to English IF that's the natural Spanish form — "Total" stays "Total", "Video" → "Vídeo" (add accent), "Documents" → "Documentos". When in doubt, prefer proper Spanish form. | "Loading…" → "Cargando…", "Force Close" → "Cierre forzado" |
| **fr** | standard European French — formal legal/business register, "vous" form, proper accents | Cognates OK identical to English where natural — FR "Finances", "Documents", "Notifications", "Transactions", "Performance", "Permissions" are the correct French; but "Details" → "Détails" (add accent), "Created" → "Créé". When EN form is identical to natural French, return it unchanged. | "Loading…" → "Chargement…", "Castle" (chess metaphor) → "Roque", "Force Close" → "Fermeture forcée" |
| **ru** | standard professional Russian — formal "вы" form | Not applicable. Russian grammatical case may reorder placeholders — that's required. | "Loading…" → "Загрузка…", "Castle" → "Рокировка", "Force Close" → "Принудительное закрытие" |
| **zh** | Simplified Chinese (简体中文) — Mainland register, NOT Traditional, full-width sentence punctuation, half-width for placeholders/brand | Not applicable. Use Arabic numerals (1, 2, 3) not 一二三. | "Loading…" → "加载中…", "Castle" → "易位", "Kanban" → "看板", "Force Close" → "强制关闭" |
