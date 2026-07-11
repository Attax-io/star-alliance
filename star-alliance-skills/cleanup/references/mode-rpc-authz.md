---
type: Document
timestamp: 2026-07-06T00:00:00Z
---

# Mode: rpc-authz — full recipe

Prove that **no public `SECURITY DEFINER` RPC has drifted open** — i.e. become
callable by someone who shouldn't reach it.

**Why this mode exists.** Every `SECURITY DEFINER` function runs as its owner
and **bypasses RLS**. So the frontend `perm` gate (`<PortalPageShell perm=…>`)
is UX only — a logged-in user can skip the UI and call any *granted* RPC
directly with a plain HTTP request. Real authorization must live **inside the
function body** (or a `private.*` helper it calls): a `user_permissions … _vap`
check, a `user_can_see_file` / file-access check, or a self-scope on
`auth.uid()`. Two failure modes rot this over time:

1. **AUTH_UNGATED** — a new RPC is granted to `authenticated` but its body (and
   its whole call graph) has **no** perm / file-access / self-scope check. Any
   logged-in member — or any logged-in *client* — can call it and read/mutate
   data the UI would never show them. (The 2026-07-06 audit found the financial
   `file_budget_status_for*` / `fd_credits_status_for*` / `gfn_budget_rollup_*`
   family leaking any file's money totals by id enumeration, plus four
   backend-only fns — `render_full_email`, `get_pending_backup_files`,
   `prune_user_activity_log`, `rollup_user_activity_daily` — wrongly granted to
   `authenticated` instead of `service_role`.)
2. **ANON_REACHABLE** — a new RPC is executable by `anon` (logged-out) but is
   **not** one of the approved public reads (marketing / codex / newsletter /
   captcha-gated form intake). Anonymous data exposure.

**Script:** `python3 "/Users/atta/Documents/Claude/Projects/Lex Council App/lex_council/scripts/security/rpc_authz_audit.py"`
(read-only; lives in the **lex_council** repo, versioned with the app — NOT in
the skill scripts dir, because it is Lex-schema-specific and needs the prod DB).

---

#### Step RA0 — Pre-flight

No dev server, no MCP. The audit reads the LIVE DB via `DATABASE_URL` (from
`apps/web/.env.local`, psycopg2). Production project is `bqgrpnsvplvicnmzxwkm`.
The check is **100% read-only** — it never writes. If no creds are present it
exits with a message rather than a false green (there is no offline fallback;
authorization state can only be judged against the live grants + bodies).

#### Step RA1 — Detect

```sh
cd "/Users/atta/Documents/Claude/Projects/Lex Council App/lex_council"
python3 scripts/security/rpc_authz_audit.py ; echo "EXIT=$?"
```

For every public `SECURITY DEFINER` function the script:
- resolves real reachability via `has_function_privilege('anon'|'authenticated', oid, 'EXECUTE')` (OID form — never a signature string),
- call-graph-expands the body 3 levels deep into its `private.*` helpers,
- detects an authz gate (`user_permissions`/`_vap`/`is_programmer` · `user_can_see_file`/file-access · `auth.uid()` self-scope),
- flags **AUTH_UNGATED** or **ANON_REACHABLE** unless the fn is whitelisted.

`EXIT=0` + "clean" → no-op. `EXIT=1` + a slip-up list → drift found.

#### Step RA2 — Triage each slip-up (SURFACE ONLY — never auto-apply)

Security fixes are **never** auto-applied by the rotation. For each flagged fn,
read its body and decide:

| Situation | Action |
|---|---|
| Genuinely missing a gate | Surface it. Draft the fix (add the gate in the `private.*` body, or `REVOKE … FROM authenticated; GRANT … TO service_role` for a backend-only fn) and present the SQL for the user's approval per **P3 — No Silent Writes**. Do NOT apply in the rotation. |
| Actually safe (pure helper, static data, self-scoped read the regex missed, intentional public read) | Add the fn to `ANON_OK` or `AUTH_OK` in `rpc_authz_audit.py` **with a one-line reason**, and commit that. This is how the whitelist stays honest — every exemption is justified in-line. |

Re-run the script after any whitelist edit to confirm it returns to clean.

#### Step RA3 — Report

State: how many public SECDEF RPCs, the slip-up count (or "clean"), each flagged
fn + which class, and — for any real gap — the drafted fix awaiting approval.
**Nothing is applied and nothing is pushed** in this mode.

---

**Rotation note.** This mode is **surface-only**, so under `/cleanup-routine` it
never counts as "applied" — a slip-up is *reported*, not auto-fixed, so the run
is a no-op for the version-bump/commit steps (advance the cursor with
`--noop`). It never leaves a red tree because it changes nothing.

**Origin.** 2026-07-06 RPC authz audit —
`lex_council/docs/vault-logs/2026-07-06_rpc-authz-audit.md`. That pass found and
fixed 8 gaps: 4 grant-lockdowns + 1 shared `user_can_see_file` gate at
`private.file_budget_status_for` (the choke point all 5 financial RPCs funnel
through). Two documented-low surfaces (`touch_folder_refresh_counter`,
`get_org_calendar_work_days`) are whitelisted with reasons.
