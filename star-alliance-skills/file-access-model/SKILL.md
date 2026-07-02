---
name: file-access-model
description: >
  Loads full context for the Lex Council file access model before any related work begins.
  Use this skill whenever the user mentions or asks about: fd_access table, users_access,
  file_owner, file_admin, member_assistants, external_assistants, fd_access_js view,
  view_for_customer flag, RLS for files, file permissions, who can see a file, access
  inheritance, the two-gate OR model, branches_access invariant, user_can_see_file helper,
  supabase-js insert().select() trap, or any migration related to file access. Also trigger
  when the user says "work on access", "build the access migration", "access model",
  "permission model", "who has access", or references anything about granting or revoking
  access to files. Load silently in the background — no need to announce the skill is running.
version: 1.1.0
type: Skill

---
# File Access Model — Context Loader

This skill loads the full design context for the Lex Council file access model so work can continue without re-explaining prior decisions. **All content below reflects the model currently shipped in Lex Council App's production database** — not a pre-migration planning draft.

## Step 1 — Load the live reference doc

Read this file in full before doing anything else (it mirrors what is live in prod):

- `lex_council/docs/references/FILE-ACCESS-MODEL.md` — `fd_access` table, `users_access`, the two-gate OR, the `user_can_see_file()` helper, the `aa_branches_access_invariant` trigger, and the supabase-js `fd` insert/select trap.

This is the canonical source of truth for this domain. Everything below is a quick orientation — the doc has the full detail.

---

## Quick Orientation

### The shipped model

**Table:** `fd_access` — one row per file. (Older doc drafts called this `file_access`; that name was never used in prod.)

**`users_access`** is a stored UUID array column on `fd_access` (denormalized set of user UUIDs with access to the file). It is *also* re-projected in a view called **`fd_access_js`** — that view is what every Supabase `_js` view reads from. Don't confuse `fd_access_js` with `file_access_full`; the latter name only appeared in a discarded plan.

### The two-gate OR

Access is decided by **`private.user_can_see_file(file_id)`** — a single Postgres function called by every RLS policy on a file-domain table. Its body is a **two-gate OR**:

- **Path A — per-user grant.** The acting user's UUID is a member of `users_access` on the file, or on the file's `gfn_ref / mfn_ref / bfn_ref / sfn_ref` ancestor chain. If Path A passes, the file is visible — Path B is skipped entirely.
- **Path B — branch supervision.** The acting user holds the relevant permission verb on their branch (e.g. `ppl_ac`, `ppl_admin`, etc.) **AND** their branch is a member of `fd_access.branches_access`. Inside Path B the two clauses are AND'd — both must hold.

There is **no third gate**. Do not reintroduce one. New file-domain RLS policies must call `private.user_can_see_file(file_id)` rather than re-inlining these two clauses — that's the contract as of the `writes_unify_with_vap` migration (2026-05-03), which rewrote both SELECT and INSERT/UPDATE policies on file-domain tables to use the helper.

### `branches_access` invariant

`aa_branches_access_invariant` is a BEFORE INSERT trigger on `fd_access`. It enforces:

- `default_branch` ∈ `branches_access`

Omitting `default_branch` from `branches_access` on INSERT fires a constraint violation. This is intentional — the default branch is the file's home branch and must always be in the access list.

### The `fd` insert/select trap

`supabase-js`'s `.insert().select()` triggers an internal SELECT after the INSERT (so the client receives the new row). For every other file-domain table this is fine — `user_can_see_file()` resolves against a `fd_access` row that already exists. **For the `fd` table specifically**, the `fd_access` row is created by a deferred trigger that runs AFTER `fd`'s INSERT lands, so during the `.select()` the `fd_access` row may not exist yet and `user_can_see_file()` would return false on the brand-new `fd`.

**The fix already shipped:** `fd`'s SELECT policy has an extra `OR file_created_by = auth.uid()` self-creator-fallback clause that lets the row's own creator see it regardless of `fd_access` state.

**Trap warning:** this is `fd`-only. Dropping the `OR file_created_by = auth.uid()` clause from a new policy on `fd` will not raise an exception — the `.insert().select()` call will **silently return an empty array**. The INSERT commits, the row exists, but the client sees nothing. If you ever revise the `fd` SELECT policy, preserve that self-creator fallback.

---

## Rules when working in this domain

1. **All access reads come from `fd_access` / `fd_access_js`** — never from `fd` directly.
2. **Use `private.user_can_see_file(file_id)` for new file-domain RLS policies** — never re-inline the two-gate logic. Migration `writes_unify_with_vap` (2026-05-03) made this the convention.
3. **No cascade triggers** — hierarchy inheritance is handled by Path A's ancestor walk, not by propagating data downward.
4. **`default_branch` must be in `branches_access`** on every `fd_access` INSERT — `aa_branches_access_invariant` will reject the row otherwise.
5. **`fd` SELECT policies must keep the `OR file_created_by = auth.uid()` self-creator fallback** — without it, `supabase-js`'s `.insert().select()` silently returns an empty array on the new row.
6. **Show SQL and get approval before applying** — this is a RULES.md requirement for all migrations.
7. **The exclusion flag is one flag** (`view_for_customer`) — do not introduce separate flags.

---

## Changelog

- **1.1.0** — Corrected against Lex Council App's shipped production reality. Replaced the stale pre-migration planning draft (which named the table `file_access`, described a three-gate RLS, and listed `org_users` / `external_assistants` / `subers` as pending work — none of which shipped) with the model that actually lives in prod today: `fd_access` table + `fd_access_js` view, the **two-gate OR** (Path A per-user-grant bypasses Path B branch-supervision; Path B's two clauses are AND'd), the `private.user_can_see_file(file_id)` helper as the single policy entry point (mandated by the 2026-05-03 `writes_unify_with_vap` migration), the `aa_branches_access_invariant` `default_branch ∈ branches_access` trigger on `fd_access` INSERT, and the `fd`-only `OR file_created_by = auth.uid()` self-creator fallback that prevents `supabase-js`'s `.insert().select()` from silently returning an empty array. Dropped the `org_users` / `external_assistants` / `subers` / `file_access_full` "still pending" checklist — those never shipped and are not coming back. Lex Council App is a separate project by the same developer this repo already deep-links to for schema and RLS patterns; this correction reconciles the skill with that project's live prod state.
- **1.0.0** — Initial release. (Stale planning draft — superseded by 1.1.0.)
