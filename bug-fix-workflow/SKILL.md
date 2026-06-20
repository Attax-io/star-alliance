---
name: bug-fix-workflow
description: The Lex Council end-to-end bug workflow — pull reports from the bug_reports table, triage their status, investigate + reproduce the real root cause, fix following project conventions, flip each row to Fixed once the fix is genuinely live, AND file (push) new bugs it surfaces back into the table. Use whenever the user says "pull the bugs", "work the bugs", "fix the bugs", "triage bugs", "what bugs are open", or any phrasing about pulling / triaging / fixing / closing reported bugs — OR to push/file bugs: "file a bug", "log this as a bug", "push these as bugs", "file the bugs you find". Loads the bug_reports schema, the status-code conventions, the status-trigger gotcha, the INSERT/push pattern (identity PK, trigger-filled names, reporter-uuid lookup, status=1, no notification fires), the "doesn't work" reproduction technique, and the rule for WHEN a bug may be marked Fixed (DB fixes now, frontend fixes only after deploy).
metadata:
  version: 1.1.1
---

# Bug-Fix Workflow (Lex Council)

This is the canonical loop for working user-reported bugs in Lex Council. Reports live in the
`public.bug_reports` table (admins file them from the in-app bug button; reporters often write in
**Arabic**). The job is: pull → triage → investigate → fix → close — **and push** (file new bugs the
work surfaces) — without lying about "Fixed".

**Production project_id = `bqgrpnsvplvicnmzxwkm`.** Every MCP `execute_sql` / `apply_migration` runs there.

---

## The `bug_reports` table

| Column | Notes |
|---|---|
| `br_id` | bigint PK — always scope status flips by this, never by status alone |
| `br_at` | filed-at timestamp |
| `br_title` | short title (often Arabic) |
| `br_text` | full report body (often Arabic — **translate it**) |
| `br_user` / `br_user_name` | reporter uuid + denormalized name |
| `br_status` | **bigint status code** — on triage the only column you write; on a new INSERT also set `br_title`/`br_text`/`br_user` (see **Push**) |
| `br_status_name` | denormalized label — **do NOT write it**, a trigger maintains it |
| `br_image_url` | optional attached screenshot |
| `br_deleted_at` | soft-delete; always filter `br_deleted_at IS NULL` |

Page view: `admin_files_bugs_list`. Admin UI: `/admin/files/bugs` (open to every admin, no `perm`).

### Status codes

| Code | Name | Meaning |
|---|---|---|
| `1` | Submitted | Freshly filed, not yet looked at |
| `2` | Pending | Acknowledged / in progress (or fixed-but-not-yet-deployed) |
| `3` | Rejected | Won't-fix / not-a-bug / duplicate |
| `4` | Fixed | The fix is **live** |

### ⚠️ Status trigger gotcha

`bug_reports` has a `BEFORE INSERT OR UPDATE` trigger `brp_on_brp_b` (`private.brp_on_brp_b`) that
**recomputes `br_status_name` from `br_status`** and refreshes `br_user_name` from
`user_preferences.nickname`. So:

- **On triage, only ever `UPDATE ... SET br_status = N`.** The name follows automatically. Setting
  `br_status_name` yourself is pointless and will be overwritten.
- An UPDATE re-reads the reporter's nickname; harmless, but don't be surprised if `br_user_name` shifts.
- On **INSERT** the same trigger fills both `br_status_name` and `br_user_name` — so when filing a new
  bug, set only `br_status` (+ `br_title`/`br_text`/`br_user`) and let the trigger name them. See **Push**.

---

## Push — filing a new bug (when the work *surfaces* one)

Beyond working existing reports, this workflow can **file** new bugs into `bug_reports` — e.g. an audit,
a review, or an investigation turns up real defects that are out of scope to fix right now. Pick the route
by where the bug belongs:

- **A real defect / tech-debt in *this* app (Lex Council)** → **INSERT a row** (below). It then shows on
  `/admin/files/bugs` like any reported bug, and a later run of this same workflow can pull + fix it.
- **Belongs to a *different* repo, or each item wants its own one-click fix session** → prefer a
  `spawn_task` chip instead (lighter; gives the user a worktree per item). Don't double-file the same item.

### The INSERT (validated 2026-06-19)

```sql
INSERT INTO public.bug_reports (br_title, br_text, br_user, br_status)
VALUES (
  '<short English title>',
  '<self-contained body — what is wrong, where (file / RPC / view), how it was found; NO chat refs>',
  '<reporter uuid>',   -- the acting admin; look it up, never guess
  1                    -- 1 = Submitted (newly found)
)
RETURNING br_id, br_status_name, br_user_name;   -- read back: confirm the trigger filled the names
```

Column rules (the INSERT counterpart to the trigger gotcha above):

- **Set only** `br_title`, `br_text`, `br_user`, `br_status`.
- **Never set** `br_id` (identity `BY DEFAULT` — auto, off `bug_reports_br_id_seq`), `br_at` (defaults
  `now()`), or `br_status_name` / `br_user_name` (the `brp_on_brp_b` BEFORE-INSERT trigger fills both —
  anything you write is overwritten).
- `br_status = 1` (Submitted) for a freshly found bug. Use `2` (Pending) only if it's already
  acknowledged/triaged-but-deferred.
- `RETURNING` and read it back — a NULL `br_user_name` just means the reporter has no
  `user_preferences.nickname`, not a failure.
- Batch many at once with `VALUES (…),(…),(…)`.

### Reporter uuid — look it up, never guess

```sql
SELECT id FROM auth.users WHERE email = '<reporter-email>';   -- e.g. atta@lexcouncil.com
```

File under the acting admin unless told otherwise (Atta = `ebee8b0b-fc92-4cb6-ac44-b89fabbcee4c`).

### Safe-to-file notes

- **No notification spam:** the only trigger on `bug_reports` is `brp_on_brp_b` (BEFORE INSERT/UPDATE,
  name-recompute). There is **no AFTER-INSERT notify** — filing does not alert staff. Re-check if a
  notification trigger is ever added.
- **Prod write, but plain DML** (not DDL): no migration file, and **no vault log** required for *filing*
  (same rule as a status flip — operational data maintenance). Fixing the filed bug later still does.
- **Self-contained body:** the row outlives the session — put file paths, the RPC/view name, and how it
  was found in `br_text`. Never "see above".
- **Title hygiene:** prefix non-defect backlog so it isn't mistaken for a user defect — `[Mobile-prep] …`,
  `[Tech-debt] …`, `[Security] …`, `[Perf] …`.

---

## Step 1 — Pull

```sql
SELECT br_id, br_status, br_status_name, br_title, br_user_name, br_at
FROM public.bug_reports
WHERE br_deleted_at IS NULL AND br_status IN (1,2)   -- open work; widen as asked
ORDER BY br_status, br_id;
```

Then pull `br_text` (+ `br_image_url`) for the rows in scope and **translate any Arabic** into a short
English gloss so the user can act. Note the reporter — different reporters hit different surfaces (e.g.
an admin who uses the global nav vs. one who works "from inside a file" expose different code paths).

## Step 2 — Triage statuses (the "pull and sort" the user usually means)

A typical request — *"switch finished→fixed from pending, submitted→pending, list them"* — is a status
sweep. Apply each transition **scoped by `br_id`** so a multi-step sweep can't bleed (e.g. don't flip
Submitted→Pending and then Pending→Fixed in a way that catches the just-promoted rows):

```sql
UPDATE public.bug_reports SET br_status = 4 WHERE br_id = 273 AND br_status = 2;  -- Pending → Fixed
UPDATE public.bug_reports SET br_status = 2 WHERE br_id IN (281,282,283) AND br_status = 1; -- Submitted → Pending
```

Re-`SELECT` the affected rows to confirm `br_status_name` updated, and list the now-actionable bugs.
A pure status flip is **operational data maintenance** (like clicking the bugs admin page) — it does
**not** by itself require a vault log. Fixing the underlying bug **does**.

## Step 3 — Investigate (before any fix)

For each bug worth fixing:

1. **Translate** the report; restate the expected vs. actual behavior in one line.
2. **Find the code path.** For >1 bug or unfamiliar areas, fan out parallel `Explore` agents (one per
   bug) to locate the form/store/mutation/RPC/view end-to-end. Treat their conclusions as leads, not
   gospel — they read excerpts and sometimes cite **stale migration files instead of the live DB**.
3. **Classify the cause** before deciding the fix:
   - **Real defect** → fix it.
   - **Expected behavior / a deliberate guard** (e.g. the customer-GFN item guard) → don't "fix" by
     weakening it; the bug may be a FE/UX gap instead.
   - **Product decision** (relax a rule vs. change the UI) → surface the choice to the user, don't guess.
4. **Reproduce "X doesn't work" bugs against the live DB — don't theorize.**
   - The fastest discriminator for a broken create/update is a **rollback'd inline repro**. You usually
     **can't call the RPC directly** (SECURITY DEFINER RPCs do `auth.uid()` → raise `unauthorized`
     under MCP), so **replicate the RPC's INSERT/UPDATE inline** inside a `DO $$ ... RAISE EXCEPTION
     'rollback' $$;` block on a realistic row and read the error.
   - **`jsonb_populate_record(null::T, payload)` trap:** create_* RPCs built this way silently NULL
     every column the payload omits, defeating that column's DEFAULT — so a `NOT NULL DEFAULT now()`
     column the FE never sends makes **every** insert fail `23502`. A loud signal: **zero rows created
     since the RPC's deploy date.** (Bit `create_folder`/documents 2026-06-03, `create_case` 2026-06-09.)
   - Always confirm the suspected cause empirically (repro before; repro after the fix) rather than
     reasoning to a conclusion. Check migration **timestamps** vs. the bug's `br_at` to kill red herrings.

## Step 4 — Fix (follow project law)

Fix per `CLAUDE.md` / `V2-CONVENTIONS.md`:

- **DB:** new/changed RPCs, views, triggers, RLS → `apply_migration` to prod, and **write the same
  `.sql` into `supabase/migrations/`** (MCP-applied migrations don't auto-write the repo file — they
  drift). Honor naming + security rules (security_invoker views, `SET search_path TO ''`, etc.).
- **FE:** writes through `lib/mutations/`, views via `VIEWS.*` registry, design-canon primitives,
  i18n keys in **all 6 locales** (`apps/web/public/messages/{en,ar,fr,es,ru,zh}`), no hardcoded hex.
- **Verify:** `npx tsc --noEmit` + `npx eslint <files>` clean. **Do not start a dev server** — Atta runs
  one; delegate visual checks to him.
- **Vault log is mandatory** (P8) — write `docs/vault-logs/YYYY-MM-DD_*.md` + prepend the INDEX row.
  Reference the sibling-bug log if one exists. Delegate to the `vault-log-compliance` skill if unsure.

## Step 5 — Mark Fixed **only when the fix is genuinely live**

This is the rule the skill exists to protect: **"Fixed" (4) means deployed, not merely coded.**

- **DB-only fix** (migration applied to prod) → effective immediately → may go to **Fixed (4)** now.
- **Frontend fix** → only takes effect after the next release/deploy → leave at **Pending (2)** until
  it ships, then flip to Fixed. Tell the user which bugs are waiting on a deploy and offer to flip them
  after release.
- **Won't-fix / not-a-bug / duplicate** → **Rejected (3)** with a one-line reason to the user.

```sql
UPDATE public.bug_reports SET br_status = 4 WHERE br_id = <id> AND br_status <> 4;  -- only once LIVE
```

Never mark a bug Fixed because the code is written; mark it Fixed because a user could now see it work.

---

## Gotchas checklist

- [ ] Wrote `br_status` only — let the trigger set `br_status_name`.
- [ ] Scoped every status flip by `br_id` (no status-only sweeps that bleed).
- [ ] Translated the Arabic; identified the reporter's surface.
- [ ] Reproduced "doesn't work" with a rollback'd inline repro, not theory.
- [ ] Checked migration timestamps vs `br_at` to rule out red herrings.
- [ ] Didn't weaken a deliberate guard to "fix" a bug.
- [ ] DB fix → `.sql` written to `supabase/migrations/` too (not just MCP).
- [ ] i18n keys added to all 6 locales.
- [ ] `tsc` + `eslint` clean; no dev server started.
- [ ] Vault log written + INDEX row prepended.
- [ ] Flipped to Fixed **only** for fixes that are live (DB now / FE post-deploy).
- [ ] **Filing** a new bug? Set only `br_title`/`br_text`/`br_user`/`br_status=1`; let the trigger name it; `RETURNING` to confirm.
- [ ] Looked up the reporter uuid by email (never guessed); `br_text` is self-contained (no chat refs); non-defect rows prefixed (`[Mobile-prep]` etc.).
