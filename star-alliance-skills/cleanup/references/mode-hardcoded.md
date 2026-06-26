# Mode: hardcoded — full recipe

> **Script:** `python3 ~/.claude/skills/cleanup/scripts/i18n_extract.py <detect|merge|propagate|verify>` — the deterministic machinery (candidate harvest + reuse-map + single-writer key merge + 6-locale propagate + MISSING_MESSAGE verify). The `.tsx` edits + the translation are the agent/recipe layer.

> **DB-native since v1.19.0 (Bug #303).** `public.app_translations` (prod
> `bqgrpnsvplvicnmzxwkm`) is the source of truth; the web build dumps DB →
> `messages/{locale}/{ns}.json`, so a key that lands ONLY in the JSON is silently
> wiped by the next build. `merge` therefore **UPSERTs the minted EN keys** and
> `propagate` **UPSERTs the propagated placeholder rows** into the DB (shared
> `_db_translations` service-role REST, prod-ref guarded) and keep the JSON as a
> mirror. This also closes a handoff hole: `language` detect reads the DB, so a
> JSON-only propagate would leave the new keys invisible to it — never translated,
> then wiped. Pass `--files-only` to skip the DB on either command (JSON-only —
> recover with `apps/web/scripts/push-translations.mjs --namespace <ns>`);
> `--allow-other-project` to point the upsert at a non-prod ref. No creds + real
> rows = FATAL (exit 2), same contract as `language apply`.

Find raw hardcoded user-facing English text still living in components and turn
it into next-intl `t()` keys. This is the capability the other i18n modes do NOT
have: `language` only translates JSON keys that already exist (it never reads
component source); `consolidate` only dedups existing keys. `hardcoded` reads the
`.tsx`/`.ts`, extracts the literal, mints (or reuses) a key, fills every locale,
then hands the new keys to `language` for translation.

**Scales from one file to the whole app.** ≤~15 files → the main agent edits
inline. More → fan out one agent per file. >~150 files across multiple sessions
is genuinely campaign-scale → `/conquering-campaign` (which DRIVES this same
machinery). The 2026-06-03 app-wide pass keyed 109 files / 372 keys / 393×5
translated this way (v1.7.42).

> **`hardcoded` vs `language`.** `hardcoded` is the *producer* (creates keys from
> source); `language` is the *translator* (fills non-EN values). A `hardcoded`
> pass ALWAYS ends by running `language` on the keys it just created. Never
> re-implement translation inside this mode.

#### Step H1 — Detect

```bash
python3 ~/.claude/skills/cleanup/scripts/i18n_extract.py detect \
  [--scope "app/[locale]/(admin)" components ...] --briefs
```

Harvests hardcoded-literal candidates (JSX text nodes, UI prop literals —
`label`/`placeholder`/`title`/`aria-label`/…, and `toast.*` / `throw new Error`
copy) across the scope (default: `app components lib hooks store`). Drops the
exclusion classes (CSS, `MIcon` glyphs, identifiers, ≤5-char acronyms, URLs/paths,
enum/snake ids, brand terms, test files). **Reuse-maps** every candidate against
the existing EN keys — a literal whose value already exists (preferring
`common.actions.*` / `common.labels.*`) gets a `reuseKey`; otherwise a
`proposedKey` in the path-inferred namespace. Writes
`/tmp/i18n_extract/inventory.json` + (with `--briefs`) one `_briefs/b<i>.json`
per file.

detect is **HIGH-RECALL** — like `language` detect it over-counts (§L25); the
agent layer (H2) is the accuracy pass that confirms which candidates are genuinely
user-facing. Show the user the counts + the >60-file scale note before proceeding.

#### Step H2 — Extract (scoped inline, or fan-out)

The agent layer turns each file's literals into `t()` calls. **#91-safe contract
(binding): an extraction agent edits ONLY its own file and returns/writes a
key-map — it NEVER touches a locale JSON. The MAIN agent is the single writer
(H3).** Fan-out agents touch disjoint files, so they never collide; they would
collide on the shared locale JSON, which is exactly why merge is centralized.

- **≤~15 files:** the main agent edits directly — read each brief, replace each
  literal (`reuseKey` → use it; else mint `proposedKey`), add
  `useTranslations`/`getTranslations` wiring if absent, move module-level English
  maps inside the component, add sub-component hooks where needed.
- **>~15 files (fan-out):** spawn one `general-purpose` agent per file (batch in
  waves of ~10–15, `run_in_background: true`, like the `language` mode's 5 agents).
  **Unattended/scheduled context (no user): spawn FOREGROUND (omit
  `run_in_background`)** — background *writing* subagents are denied in the no-user
  scheduled context and fail silently. See mode-language §L2.
  Each is briefed with its `_briefs/b<i>.json` + the brief below, edits its file,
  and writes a sidecar `b<i>.json` (`{file, namespace_keys, reused_keys,
  literals_replaced, needs_review, notes}`) to a keys dir.

Extraction-agent brief (fill `<BRIEF_PATH>` / `<KEYS_DIR>` / `<i>`):

```
Convert hardcoded user-facing text in ONE file to next-intl t() calls. Behavior-preserving — change only WHERE the text comes from, never the wording/logic.
1. Read <BRIEF_PATH> (has: abs file, alreadyUsesI18n, entries[] with line/literal/context/reuseKey/proposedKey/namespace) and the source file at brief.abs. Read the file fully.
2. For each entry: first dotted segment of the key = namespace, remainder = the t() key. reuseKey set → use it (add full path to reused_keys, NO new key). Else proposedKey → EN value is the literal verbatim; if it interpolates a runtime value, use ICU {name} placeholders. Put new keys in namespace_keys[ns][rest]=EN.
3. Wiring: reuse the file's existing useTranslations var for that ns; else add const t = useTranslations('<ns>') (client) / await getTranslations('<ns>') (server) inside the component; module-level English map → move inside; module-level sub-component → add its own hook.
4. Edit ONLY brief.abs. NEVER edit public/messages/* (the orchestrator merges keys). Keep EN values verbatim (brand names included). Keep JSX/TS valid; re-read changed regions to confirm balanced quotes/braces and no leftover literal. Use STRAIGHT quotes only.
5. Write your result object to <KEYS_DIR>/b<i>.json AND return it as StructuredOutput: {file, status, namespace_keys, reused_keys, wiring_added, literals_replaced, needs_review, notes}.
```

#### Step H3 — Merge (single writer)

```bash
python3 ~/.claude/skills/cleanup/scripts/i18n_extract.py merge --keys-dir <agent-sidecar-dir>
```

Merges every agent's `namespace_keys` into `en/<ns>.json` (split dotted,
conflict-detect, kept-first), **UPSERTs each newly-added EN key into
`app_translations`** (DB-native, #303 — added-only, so a pre-existing EN value is
never clobbered), and runs the **reuse-existence check**: every `reused_keys`
entry MUST already exist in EN — any that don't are keys the agent MISLABELED as
reuse (they'd be runtime `MISSING_MESSAGE`, invisible to `tsc` because the browser
client is untyped). For each missing one, recover the literal from that file's
brief and add it as a new key. Writes `/tmp/i18n_extract/merge_report.json`. (DB
write hits **prod** — needs `apps/web/.env.local` creds; `--files-only` to skip.)

#### Step H4 — Propagate to all 6 locales

```bash
python3 ~/.claude/skills/cleanup/scripts/i18n_extract.py propagate
```

Sets every merged key into ar/fr/ru/zh/es with the EN value as placeholder **and
UPSERTs those placeholder rows into `app_translations`** (DB-native, #303 —
added-only, so an existing real translation is never overwritten with EN). Absent
keys are invisible to `language` detect (§L25) — and since that detect reads the
DB, propagation must reach the DB, not just the JSON, or the keys never become
translatable. After this the app renders in every locale (no `MISSING_MESSAGE`),
just showing English until H5. (DB write hits **prod**; `--files-only` to skip.)

#### Step H5 — Translate (hand off to the `language` mode)

Run the `language` mode (above) end-to-end on the now-present-but-EN keys:
`i18n_cleanup.py detect` → 5 translation agents → `apply` → `verify`. Scope the
detect to the touched namespaces if you want to avoid re-translating pre-existing
drift. Do NOT re-implement translation here.

#### Step H6 — Verify

```bash
python3 ~/.claude/skills/cleanup/scripts/i18n_extract.py verify --scope <touched paths>
cd lex_council && npx turbo run check-types --force && npx eslint apps/web && npx vitest run __tests__/i18n
```

`verify` asserts every `t()`-key in the touched files resolves in `en/*.json` (the
MISSING_MESSAGE guard) and flags smart-quote `useTranslations`/`getTranslations`
calls (TS1127). Then the standard gate. Every new key must exist in all 6 locales.

#### Step H7 — Fix the known fan-out failure modes

The 2026-06-03 fan-out surfaced exactly these — auto-fix all before closing:

| Symptom | Fix |
|---|---|
| `merge` reports missing reuse keys | agent mislabeled a new key as reuse → recover the literal from its brief, add as a new key |
| `tsc` TS1127 "Invalid character" | smart-quote `useTranslations('ns')` → straight quotes |
| `react-hooks/exhaustive-deps` "missing 't' / 'tCommon'" | the added `t` var is a new hook dependency → add it to the `useMemo`/`useCallback`/`useEffect` dep array |
| dead-code file got i18n'd (rules-of-hooks on a 0-caller fn) | revert that file (don't carry dead i18n); prune its now-orphan keys |
| concurrent actor editing the same tree | stage with exact NUL-literal pathspecs (`commit_scope.py` / §F5.5); never `git add -A` |
| testing the merge/propagate DB write-path | use a throwaway key (`settings.__cleanup_selftest__`) + an isolated `--root /tmp/...` tree; clean up via a DB delete, **never `git checkout` a tracked `messages/*.json`** (§L41 — it silently destroys a concurrent actor's uncommitted edit) |

#### Step H8 — Vault log + patch bump

Delegate to **vault-log-compliance** (note locale counts + key totals + the
deferred tail). Run the §Step CL app patch bump once. If the pass spanned the
whole app across sessions, prefer `/conquering-campaign` so each batch ships green
with its own resume checkpoint.
