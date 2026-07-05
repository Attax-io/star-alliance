---
type: Document
timestamp: 2026-07-06T00:00:00Z
---

# Mode: activity-coverage — full recipe

Keep the **user-activity monitor** in lock-step with the app's mutation +
UI surface, so a newly-shipped page or action never goes silently untracked.

**Why this mode exists.** The activity monitor (`public.user_activity_log` +
`log_user_activity` RPC + `user_activity_event_types` allow-list, surfaced on
`/admin/users/activity`) is only as good as its instrumentation. Two failure
modes rot it over time:

1. A dev fires a **new `event_type` string** that was never seeded into
   `user_activity_event_types`. The RPC validates against the allow-list and
   **silently rejects** unknown types — the event logs **0 rows** and nobody
   notices (this is exactly how `record.create` died for ~6 weeks in 2026-05,
   and how `document.move` fired into the void until this mode caught it).
2. A dev ships a **new write** (`lib/mutations/*`) whose RPC verb isn't in the
   `VERB_EVENT` map at the mutation boundary (`_shared.ts`), or routes it
   through the legacy `callRpc` / a raw `.rpc()` instead of `callServerRpc` —
   so the auto-emit boundary never fires for it.

Since 2026-07-06 every write funnels through `callServerRpc`, which auto-emits
a `record.*` event via `VERB_EVENT` minus `WRITE_ACTIVITY_DENY`. That makes the
common case self-tracking; this mode is the **guard** that proves the invariant
still holds and repairs the mechanical drift.

**Script:** `python3 ~/.hermes/skills/cleanup/scripts/activity_coverage.py <detect|classify>`
(read-only; auto-wiring is applied by this recipe, not the script).

---

#### Step AC0 — Pre-flight

No dev server, no MCP needed. The detector reads the live allow-list straight
from `public.user_activity_event_types` via `DATABASE_URL` (from
`apps/web/.env.local`, psycopg2), and **falls back to a committed constant**
(`ALLOWLIST_FALLBACK`) when no creds are present — so the rotation never breaks
offline. This mode is safe to run fully unattended.

#### Step AC1 — Detect

```sh
python3 ~/.hermes/skills/cleanup/scripts/activity_coverage.py detect
python3 ~/.hermes/skills/cleanup/scripts/activity_coverage.py classify
```

`detect` writes `/tmp/activity_coverage.json`; `classify` ranks it into
`/tmp/activity_coverage_classified.json` + prints a severity summary. It parses
the **live** `VERB_EVENT` + `WRITE_ACTIVITY_DENY` out of `_shared.ts`, so the
report always reflects the real boundary config (never a hardcoded copy).

Four drift classes:

| Class | Sev | Meaning | Fix |
|---|---|---|---|
| `unknown_literal` | HIGH | `event_type` emitted in code, **absent** from the DB allow-list → RPC rejects it, 0 rows | Seed a row in `user_activity_event_types` (migration / REST) |
| `boundary_bypass` | MED | create/update/delete RPC invoked via `callRpc` or raw `.rpc()` — skips the auto-emit boundary | Migrate the module to `callServerRpc` |
| `uncovered_verb` | MED | write-verb prefix used by a mutation but missing from `VERB_EVENT`, not denied → untracked write | **MECHANICAL**: add the `verb: 'record.*'` entry to `VERB_EVENT` |
| `dead_type` | LOW | allow-list type with no emitter, not boundary-produced, not an auto-nav event | Wire a call site or retire the row |

#### Step AC2 — Auto-wire the mechanical fixes

Apply the safe, unambiguous repairs **autonomously** (this mode's remit):

- **`uncovered_verb`** → add `<verb>: '<record.event>'` to the `VERB_EVENT`
  object in `apps/web/lib/mutations/_shared.ts`. Pick the event by the verb's
  meaning: creators (`create/insert/add/upsert/grant/broadcast`) →
  `record.create`; mutators (`update/set/rename/link/save/merge`) →
  `record.update`; removers (`delete/remove`) → `record.delete`; lifecycle
  (`restore/suspend/archive/publish/certify/…`) → `record.status_change`;
  ownership (`assign`) → `record.assign`. All targets already exist in the
  allow-list, so **no DB change is needed** — this is a pure, reversible,
  data-only edit.
- **`boundary_bypass`** → swap the module's `callRpc(db().rpc('x', {…}))` for
  `callServerRpc('x', {…})` (the v2 default transport). Verify the args object
  matches; run tsc.

#### Step AC3 — Surface (do NOT auto-apply) the DB + transport gaps

- **`unknown_literal` (HIGH)** requires a **catalog INSERT** into
  `public.user_activity_event_types` — a production DB write. Do **not** apply
  it silently. Surface the exact idempotent SQL for the user to approve:

  ```sql
  INSERT INTO public.user_activity_event_types
    (event_type, event_group, is_write, is_enabled, weight, description)
  VALUES ('<type>', '<group>', <bool>, true, <weight>, '<desc>')
  ON CONFLICT (event_type) DO NOTHING;
  ```

  Group + weight by analogy with siblings (movement/record writes → `records`,
  weight 3; passive views → weight 1). The code already fires the event, so the
  seed alone makes it start logging.
- **`dead_type` (LOW)** — report only; retiring a row or wiring a new call site
  is a judgement call, not a mechanical fix.

#### Step AC4 — Verify + closeout

- `npx turbo run check-types --filter=web` + lint the touched files.
- If any mechanical fix landed: **Step CL** app-patch bump (once), vault log
  (delegate to `vault-log-compliance`), commit inside `lex_council/`.
- If detect-only (nothing applied): `rotate.py advance --noop`, no bump.

**Unattended / rotation context:** AC2 mechanical fixes are safe to apply
autonomously (data-only, tsc-gated). AC3 HIGH items must be **surfaced, never
auto-applied** — a prod catalog write waits for the user even in the routine.
