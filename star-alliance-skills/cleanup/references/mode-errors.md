# Mode: errors — full recipe

Triage the runtime errors that pile up during normal browsing of the
local dev app, **without** Claude ever opening its own preview session
(that hijacks port 3000 — banned per Atta's standing rule). Atta keeps
his dev server running with stdout tee'd to `/tmp/lex-dev.log`; a
dev-only client-error sink endpoint catches browser-side errors and
appends them to the same file. The script
(`scripts/errors_cleanup.py`) parses both streams, dedupes, classifies,
and produces a triage list Claude can read on demand.

**Why this mode exists.** Without it, every dev-time error required
the user to copy-paste a stack trace before Claude could diagnose. The
sink + log + parser turn that into a one-command read. The mode also
codifies what counts as an *unambiguous* code-bug so auto-fix is
safe (E4 rubric).

#### Step E0 — Pre-flight

Confirm `/tmp/lex-dev.log` exists. If not, surface the tee command and
abort:

```sh
npx turbo dev 2>&1 | tee /tmp/lex-dev.log
```

> **Unattended / scheduled context (no user — e.g. the
> `lex-cleanup-rotation` routine):** there is no teed dev server, so
> `/tmp/lex-dev.log` is absent every run. This mode is then a **structural
> no-op** — declare it immediately and `rotate.py advance --noop`. Do NOT
> start a dev server unattended (that's the user's job; the rotation must
> never spawn a long-running server). The mode only does real work when a
> human left a dev session running with the tee in place, so it is
> effectively interactive-only.

Also confirm the runtime pieces are present (one-time setup, but check
in case a future refactor removed them):

- `apps/web/app/api/_dev/client-error/route.ts` — dev-only POST sink,
  returns 404 in prod, appends JSON lines to `/tmp/lex-dev.log`.
- `apps/web/components/_dev/DevErrorSink.tsx` — `'use client'`
  component that registers `window.error` + `unhandledrejection`
  listeners and `sendBeacon`s payloads to the route above.
- `apps/web/app/layout.tsx` — mounts `<DevErrorSink />` behind
  `process.env.NODE_ENV === 'development'`.

If any is missing, surface the gap. Don't auto-recreate — the user
might have removed it deliberately.

#### Step E1 — Detect

```sh
python3 ~/.claude/skills/cleanup/scripts/errors_cleanup.py detect [--since]
```

Default reads the entire log. `--since` reads from
`/tmp/last_errors_cleanup_offset` (set by `mark` in E6) so a second
invocation in the same dev session only sees new entries.

The parser handles:

- Server-side: Next.js error glyph (` ⨯ `), bare `TypeError:` /
  `ReferenceError:` / `SyntaxError:` / `RangeError:` / `PostgrestError:`
  / `AuthError:` / `FetchError:` / `AbortError:` headers, plus stack
  trace lines in either `at name (path:line:col)` or bare
  `at path:line:col` form.
- Client-side: one-line JSON blobs prefixed with
  `[CLIENT_ERROR <iso-ts>]` written by the sink endpoint.
- Route attribution: tracks the most-recent ` GET|POST|… /path NNN`
  line and stamps subsequent server errors with that route.

Dedupe key: `(error_type, first 200 chars of message, first repo-frame
path:line)`. Output: `/tmp/dev_errors.json`.

#### Step E2 — Classify

```sh
python3 ~/.claude/skills/cleanup/scripts/errors_cleanup.py classify
```

Each unique entry classified as one of:

| Class | Signal | Action |
|---|---|---|
| **code-bug** | Any stack frame matches `apps/web/` or `packages/md/` / `packages/auth/` / `packages/supabase/` | Surface as actionable |
| **framework-noise** | HMR / webpack-internal / Fast Refresh / `node_modules/next/` / `node_modules/react/` / Deprecation / `MISSING_MESSAGE` | Suppress in surface (show only count) unless count > 5 (repeated noise can mask real bugs) |
| **external** | `fetch failed` / `ECONNREFUSED` / `ENOTFOUND` / `ETIMEDOUT` / `network` / `supabase` keywords, no repo frame | Surface as informational — Atta usually knows the cause |
| **unknown** | Nothing matched | Surface; user reclassifies |

Output: `/tmp/dev_errors_classified.json` + a printed summary table.

#### Step E3 — Surface the triage list

Show the user:

- All `code-bug` entries with file:line + message + routes-seen-on + count.
- All `external` entries grouped by host (one line per host).
- `framework-noise`: only the total count, unless a specific noise
  signature exceeds 5 occurrences (then list it).
- `unknown`: full list with the raw first line.

Format per entry:

```
[TypeError] Cannot read properties of undefined (reading 'nickname')
  apps/web/components/portal/PortalUserCard.tsx:42
  routes: /en/admin/files, /en/members
  count: 3
```

#### Step E4 — Auto-fix unambiguous code-bugs

**Auto-fix rubric (strict).** Apply a fix only if ALL of these hold:

1. The stack pinpoints a specific file:line under `apps/web/` or
   `packages/`.
2. The error matches exactly one of the named patterns below.
3. The fix is a single-line change.
4. The file has no uncommitted edits unrelated to this session.
5. Fewer than 4 auto-fixes are proposed in this batch (≥4 is a
   smell of broader breakage — surface, don't auto-fix).

Named patterns:

| Error pattern | Fix |
|---|---|
| `TypeError: Cannot read properties of (undefined|null) (reading 'X')` AND access site is `foo.X` in a read position (not LHS, not function-call where `?.()` would change semantics) | Replace `foo.X` → `foo?.X` |
| `ReferenceError: X is not defined` AND `X` is exported from exactly one module under `apps/web/` or `packages/` AND not already imported in the file | Add `import { X } from '<resolved-path>'` at the top |
| `ReferenceError: X is not defined` AND `X` is exactly one Levenshtein edit from one in-scope identifier AND that identifier is the only viable candidate | Replace `X` with the in-scope name at the pinpointed line |

Anything else: surface with the proposed fix and ask. When in doubt,
ask. Auto-fix mistakes are cheaper to avoid than to roll back.

After applying a fix, run `tsc` (E5) before the next fix in the
batch — if a fix breaks types, abort the batch and surface the
remaining errors for human triage.

#### Step E5 — Verify

```sh
cd lex_council && npx turbo run check-types --filter=web
```

Then ask the user to re-navigate the routes that produced the
fixed errors. After the re-browse:

```sh
python3 ~/.claude/skills/cleanup/scripts/errors_cleanup.py detect --since
```

If any of the original error signatures recurs, the auto-fix didn't
actually address the root cause — surface it for a second pass.

#### Step E6 — Mark

```sh
python3 ~/.claude/skills/cleanup/scripts/errors_cleanup.py mark
```

Records the current log EOF in `/tmp/last_errors_cleanup_offset` so
the next `detect --since` only reads new entries.

#### Step E7 — Vault log

Delegate to **vault-log-compliance** *only if code changed*. For
triage-only runs (no auto-fix applied, user did not request a manual
fix), no vault log needed — the log itself is the audit trail.

The entry should document:

- Each fixed error: signature + file:line + which patterned fix
  applied (A/B/C from E4).
- Routes that triggered each error.
- The verify result (E5).
- Any errors surfaced but not auto-fixed (deferred-to-user list).
