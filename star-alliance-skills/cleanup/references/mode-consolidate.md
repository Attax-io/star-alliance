# Mode: consolidate — full recipe

> ✅ **#303 DB-native (done 2026-06-21):** `public.app_translations` (DB) is the
> i18n source of truth. This mode now deletes the doomed keys from the **DB and
> the JSON** in the same `apply` (new **Phase C** — direct service-role REST
> DELETE on `app_translations`, all 6 locales, prod-ref asserted), so a merged
> key does NOT reappear on the next build dump. `detect`/`verify` read the DB
> (auto-fallback to the committed JSON; `--files` to force). The TSX/TS callsite
> rewrites are unchanged (code isn't in the DB). No `push-translations.mjs`
> bridge. `--no-db` skips Phase C (JSON-only; the keys reappear on the next dump
> — for offline/testing only).
>
> **Why direct REST DELETE, not the `delete_translation` RPC:** that RPC is
> programmer-gated (a service-role caller has a NULL `auth.uid()` → rejected) and
> id-based (`p_id bigint`, no addressing by key). Direct table DELETE on the
> `(locale, namespace, key_path)` unique key is the headless-safe path — the
> symmetric counterpart to how `push-translations.mjs` upserts the table directly
> rather than via `upsert_translation`. See `scripts/_db_translations.py`.

Fold safe-to-merge i18n keys (groups where N>1 keys share the SAME English
value AND the SAME translation in every locale) into shared `common.*`
keys. AST-aware callsite rewrites + two-phase apply (dead keys first;
then live rewrites + key deletion). Script:
`scripts/consolidate_cleanup.py`.

**Why this is the riskiest cleanup mode.** Unlike `language` (JSON-only
edits) or `docs` (docs-only edits), consolidate touches TSX/TS source —
miss a callsite and you get a `MISSING_MESSAGE` runtime error in
production. Three traps documented from the 2026-05-28 first pass:

| Trap | What broke | Why |
|---|---|---|
| **Naive Explore agent says "0 callsites"** | Initial agent run reported all 62 keys dead — they weren't. | The agent only checked the full key path. It missed deeper-namespace patterns like `useTranslations('admin.chat.bubble').t('menu_delete')`. |
| **Suffix-grep over-matches** | A second attempt with all suffix variants reported 744 callsites — also wrong. | `'status_label'` matched `severance_calculator.form.contract_type_label` and dozens of unrelated keys. |
| **Variable-name confusion** | A file with `const tp = useTranslations('portal')` AND `const tc = useTranslations('common')` would have `tc('labels.status')` AND `tp('labels.status')` calls — string grep can't tell which is `portal.labels.status` (doomed) vs `common.labels.status` (target). | Only AST-aware parsing — read each file, track which `t` variable maps to which namespace via `useTranslations` bindings, then resolve each `t-call` to its full key — produces the right answer. |

**Rule for consolidate mode:** never trust a generic-purpose agent's
"callsite map". Always run `scripts/consolidate_cleanup.py map-callsites`,
which does the AST-aware resolution properly.

#### Step C1 — Detect safe-to-merge candidates

```bash
python3 ~/.claude/skills/cleanup/scripts/consolidate_cleanup.py detect
```

Outputs `/tmp/safe_to_merge.json` and prints the cross-NS table sorted
by lift (count desc). For each candidate, shows whether `common.json`
already has a key with the same EN value (clean target) or whether one
must be added.

The output is the input to a CONVERSATION with the user — not an
auto-apply candidate list. Most of these groups should NOT be merged.

#### Step C2 — Pick the surgical set with the user

Default policy (codified from the 2026-05-28 first run): **only merge
universal labels with zero domain semantics.** The accepted "safe to
merge" patterns:

- Pure UI verbs in `common.actions.*` — Save, Close, Delete, Download, Edit, Cancel, Send, Add
- Pure UI nouns in `common.labels.*` — Status, Type, Description, Date, Yes, No
- Language names in `common.{english,arabic,french,russian,chinese,spanish}`

The accepted "DO NOT merge" patterns (even though their EN value matches):

- Entity nouns — Tasks, Cases, Files, Documents, POAs, IDs, Clients, Members (domain-specific; likely to diverge per context)
- Generic-but-context-bound headers — Details, Home, Tools, Office, Notes (may want to specialize as "Case Details" vs "Task Details" later)
- Same-namespace dups — keep these; they may share an EN value by coincidence but their *contexts* differ within the namespace

When in doubt, ask the user explicitly. Don't infer.

Write the selected target set to `/tmp/consolidation_keys.json` as
`[{ "old": "fully.qualified.doomed.key", "new": "common.target.key" }, ...]`.

#### Step C3 — Verify target keys exist in `common.json`

Read `messages/en/common.json` and confirm every `new` key already
exists. If any are missing, the consolidate pass needs to ADD them
first (with translations in every locale — this is itself a small
`language` mode pass). Most surgical sets won't need this — common
already has `labels.*` and `actions.*` populated.

#### Step C4 — Map callsites (AST-aware)

```bash
python3 ~/.claude/skills/cleanup/scripts/consolidate_cleanup.py map-callsites
```

Outputs `/tmp/consolidation_callsites_final.json` with:

- `callsites`: verified `(file, line, var, key_arg, old_key → new_key)` tuples
- `dead_keys`: keys with zero callsites (safe to delete with no code changes)
- `plan`: per-file strategy classification
  - **Strategy A** (file already has a `useTranslations('common')` binding): swap the variable name in each t-call. Trivial.
  - **Strategy B** (file does NOT have a `common` binding): add `const tc = useTranslations('common')` after the existing useTranslations line, then swap.

Surface the totals to the user: `N callsites across M files; K dead
keys; strategy A vs B split`. Show the per-file plan if M > 20 (helps
spot weird outliers — e.g. a file with 10+ callsites likely needs
inspection).

**Two-component-per-file gotcha:** if a file has multiple React
components and only one declares `useTranslations('common')`, Strategy
A's plan output may falsely flag the file as "has common" when only
HALF the components do. `tsc` will catch this with `Cannot find name
'tc'` — fix by adding `const tc = useTranslations('common')` to the
other component(s) manually.

#### Step C5 — Apply (three-phase)

```bash
python3 ~/.claude/skills/cleanup/scripts/consolidate_cleanup.py apply
```

Internally runs:

1. **Phase A — dead-key deletion** (JSON): delete every key in
   `dead_keys` from every locale's JSON. No code touched.
2. **Phase B — callsite rewrites + live-key deletion** (TSX + JSON): for
   each file in `plan`, add the `tc` binding if needed, then replace
   `var('key_arg')` → `tc('new_suffix')` for each callsite. After all
   files written, delete the live keys from every locale's JSON.
3. **Phase C — DB deletion** (`app_translations`): delete every doomed
   key (dead + live) from the DB across all 6 locales via service-role
   REST. **This is what makes the merge stick** — without it the next
   build dump re-materializes the keys you just removed from the JSON.
   The prod project ref is asserted first; `--allow-other-project`
   overrides. No creds / `--no-db` → Phase C is skipped with a loud
   warning (the keys WILL reappear on the next dump — finish by re-running
   `apply` with credentials).

The `replace()` is global per `old_call` string, so duplicate callsites
on the same line/file get rewritten together. The "could not find" skip
messages on the second occurrence of identical callsites are benign
(already replaced).

> Phase C strips the namespace prefix before deleting (`admin.foo.bar` →
> DELETE where `namespace=admin` AND `key_path=foo.bar`). It never issues
> a DELETE without a `key_path` filter, so an empty doomed-set is a no-op
> (it can't wipe a namespace).

#### Step C6 — Verify

```bash
cd lex_council && npx turbo run check-types --filter=web
python3 ~/.claude/skills/cleanup/scripts/consolidate_cleanup.py verify
```

`tsc` failure usually means a missed `tc` binding (see C4 two-component
gotcha) — fix manually and re-run tsc.

The verify subcommand prints the new safe-to-merge group count + JSON
parse status. Expect the count to drop by the number of merged groups
(e.g. 10 surgical merges → drops by 10).

#### Step C7 — Vault log

Delegate to **vault-log-compliance**. The entry should document:

- The exact target set picked (and why each was chosen)
- The keys deleted with their callsite counts
- The strategy A/B split (how many files needed a new binding)
- Before/after safe-to-merge counts + total key counts per locale

If the consolidation pass extends a same-day `language` pass, link the
two vault logs as a sequence.

#### Step C8 — Memory update

If the surgical pass surfaced new keys that should become canonical
`common.*` targets (e.g. a frequently-duplicated label), add a memory
entry under `feedback_*` so the next `consolidate` pass auto-routes
to the right target.
