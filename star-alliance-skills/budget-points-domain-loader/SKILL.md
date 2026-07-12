---
name: budget-points-domain-loader
description: >
  Loads the Lex Council files-budget / lawyer-points / partner-pool spending subdomain before
  any work on it. This is the money-LIMIT and effort-COST layer that sits ON TOP of the
  transactions model: transactions-domain-model covers transaction types and the agree/certify
  lifecycle, but NOT this economics layer. Trigger on: file budget, credits cap, expenses cap,
  budget/spending limit, remaining budget, credits added/returned/outflow, Type 14 (Credits
  Add), Type 16 (Credits Return), on_customer_by_agreement, reimbursement paid, partner pool,
  partner credits pool, pool exhausted, pool inflow %, lawyer points, GES, general expenses
  share, budget_consumed, cost-per-point, BudgetLimitNotice, PartnerPoolBlockNotice,
  task_block/expense_block, bug #347, surplus-on-close, or credits-vs-budget naming. Also on
  "fix a budget/credits bug", "why is remaining budget wrong", "partner can not add credits",
  "file budget formula". Load silently in the background.
metadata:
  version: 1.0.0
type: Skill

---
# Budget · Points · Partner-Pool Domain Model

> ⚠️ **Staleness banner (read first).** This model was assembled 2026-07-12 from live code
> (`hooks/use-fd-budget-status.ts`, `hooks/use-partner-pool-status.ts`, `lib/mutations/partners.ts`,
> `components/portal/BudgetLimitNotice.tsx` + `PartnerPoolBlockNotice.tsx`) and the vault logs
> `2026-05-19_credits-limit-system`, `2026-05-27_partner-credits-pool`,
> `2026-07-09_bug347_file_budget_full_credit_outflow`, plus `docs/FINANCIAL-MODEL.md`. The **concepts,
> the three meters, the canonical formulas, and the recurring bug classes are accurate.** But the
> spending rules are the app's fastest-moving surface (the partner-pool formula alone changed four
> times in one day; the points/GES freeze model was rewritten mid-2026-06). **Trust the model and the
> bug classes; re-verify exact function bodies, thresholds, and constants against live prod
> `bqgrpnsvplvicnmzxwkm` before you change math.** Where a number is a fast-moving constant it is
> flagged inline.

This subdomain is the **spending economics** layered on the transactions system. Read
`transactions-domain-model` first for the 13 base types, the trigger, and the tab views — then read
this for how money is *capped, funded, and costed*. This skill exists because three correctness bugs
keep recurring here, each needing domain reasoning the transactions model does not carry (§7).

---

## 1. Axiom: there are THREE meters, not one

The single biggest source of bugs is collapsing three distinct quantities into "the budget." They
share the word "budget" and the actor "partner" but answer different questions:

| Meter | Question it answers | Unit | Drawn from |
|---|---|---|---|
| **File Budget** (a.k.a. credits cap / expenses cap) | "How much may this file still SPEND?" | money (EGP) | Type-14 credits added to the file |
| **Points / GES** | "How much of the firm's overhead does this file OWE?" | effort points | work + age the file consumed |
| **Partner Pool** | "How much credit may this partner still HAND OUT to files?" | money (EGP) | the partner's own net certified deposits |

They connect in one direction: a **partner's pool** funds the **file budgets** of the files they own
(each Type-14 credit-add debits the pool); **points/GES** is an independent cost meter that does not
touch either. Never let a change to one silently assume the shape of another.

---

## 2. The transaction types that drive this layer

Extends the base 1–13 table in `transactions-domain-model`. The ones that matter here:

| ID | Meaning | Role in this layer |
|----|---------|--------------------|
| 1 | Expense (مصروف) | **File-budget outflow.** Split firm-vs-customer by `on_customer_by_agreement` (both count) |
| 2 | Income (وارد) | On certify, **auto-creates** a Type-14 at `MIN(50% of income, owner pool_available)`; uncertify reverses |
| 13 | Expense Reimbursement (استرداد مصروفات) | **File-budget outflow** (was omitted before BUG 347) |
| 3 | Deposit (إيداع) | Feeds the **partner pool** (inflow), certified, `done_by` = partner |
| 4 | Withdrawal (سحب) | Reduces the **partner pool** (net), certified, `done_by` = partner |
| 14 | Credits Add (حد الإنفاق) | **Adds file budget**; debits the owner's partner pool |
| 16 | Credits Return | **Returns file budget**; credits the pool back |

Type-14 is hidden from customers (three layers of defense — see the credits-limit-system log). It is
an ordinary auditable `transactions` row, not a separate table, so it is comment-/agree-/certify-able
and reverses on delete for free (the meters are computed, never stored balances).

---

## 3. File Budget — the canonical formula (BUG 347)

A file's remaining budget is:

```
remaining = credits_added            (Σ Type-14)
          − credits_returned         (Σ Type-16)
          − firm_expenses            (Type-1, on_customer_by_agreement = false)
          − on_customer_expenses     (Type-1, on_customer_by_agreement = true)   ← omitted pre-347
          − reimbursements_paid      (Σ Type-13)                                 ← omitted pre-347
```

In the enforcement function this is: **credits = Σ(14) − Σ(16)**, **outflow = Σ amount WHERE
`transaction_type IN (1, 13)`** (all expenses regardless of the on-customer flag, plus reimbursements).
The pre-347 bug subtracted only firm expenses (`type=1 AND on_customer=false`), so files showed *more*
headroom than they had (file MFN 623: 331,727.50 shown vs 250,566.50 real — an 81 k overstatement).

**Status enum** (`unlimited | ok | warn | task_block | expense_block`) with escalating hard gates,
enforced by BEFORE INSERT triggers:

| Status | Usage | Effect |
|---|---|---|
| `unlimited` | no credits set (or a GFN — out of model) | no cap |
| `ok` | < 75% | — |
| `warn` | ≥ 75% | UI amber; no block |
| `task_block` | ≥ 90% | **task creation refused** (tasks are the primary spend driver) |
| `expense_block` | ≥ 100% | **expense creation refused** (last line) |

**Scope: budget lives at the MFN (matter, `file_class = 2`).** GFNs are out-of-model → always
`unlimited`; a GFN's badge is a roll-up of its MFN children via `gfn_budget_rollup_for_many`.
**Cascade is symmetric and DOWNward:** both credits and expenses aggregate `file + descendants`
(a Type-14 funds only the subtree it is attached to; attach matter-wide credit at the MFN, not the GFN).

---

## 4. Axiom: one formula, many sites — they WILL drift

The BUG 347 outflow math is re-derived independently in **three** places that must stay identical:

1. `public.file_budget_status_for(p_file_id)` — **SECURITY DEFINER** enforcement choke-point. Every
   guard and RPC funnels through it (`create_transaction`, the task/expense block triggers,
   `budget_return_on_close`, `certify_transactions`, the `*_for_many` roll-ups).
2. `admin_finances_budget_status` — `security_invoker` display view (members Balances + admin revenue).
3. `admin_finances_credits_status` — the **legacy twin** view, same math by hand.

Fixing only the function leaves the Balances page silently wrong, because the FE reads the *view*, not
the function. **Any change to the outflow/credits definition must touch all three (grep `pg_views` +
`pg_proc` for re-derivations first).** This is the recurring hazard the credits-limit-system log calls
"the math lives at N sites that must match" — here N was three.

---

## 5. Axiom: read status through the DEFINER path, never the invoker view

The display views are `security_invoker = true` (project canon), so they see only the caller's
RLS-visible transactions. A non-finance admin (no `tr_history_vap`, not in `user_concerned`) reads
`total_credits = 0` → `unlimited` → no chip, while Atta sees the real number on the *same* file. This
is the **Iter-10 asymmetry**: enforcement and UI diverge by user.

Rule: enforcement and any authoritative status read go through the **SECURITY DEFINER** RPCs —
`file_budget_status_for`, `gfn_budget_rollup_for_many`, `fd_credits_status_for_many`,
`partner_pool_status_for`, `partner_pool_status_for_file`. The invoker views are for pages already
gated by `tr_history_vap`, where RLS shows everything anyway.

---

## 6. Partner Pool — the funding governor

Only partners may fund file budgets, and only up to what they have personally brought in. Current
formula (live shape; the constant moved 0.75 → 0.90 on 2026-05-27, now per-partner tunable):

```
pool_available(partner) = inflow_pct × ( Σ certified Type-3 deposits − Σ certified Type-4 withdrawals ,
                                         both done_by = partner )
                        − Σ Type-14 amounts on files where folder_access.file_owner = partner
```

`inflow_pct` defaults to **0.90** and is set per partner via `set_partner_pool_inflow_pct(uuid, pct)`
(gated `tr_history_vap`; validates 0–100; writes only `is_partner = true` rows). The pool is a
**computed number, not a stored ledger** — deposits, withdrawals, and credit-adds all re-read live, so
refunds and re-growth are automatic. Pool status enum: `not_partner | exhausted | low | ok`
(`low` = remaining under ~20% of inflow).

**Guards enforced in `tr_on_tr_b_iu` / sibling triggers** (verify bodies live before editing):
- Type-14 owner must be a partner; Type-14 amount ≤ `pool_available + COALESCE(OLD.amount, 0)`.
- Type-3 / Type-4 `done_by` must be a partner; uncertify refused if it would push the pool negative;
  Type-4 pre-flight refuses at insert if eventual certification would.
- **Admin-on-behalf consent:** an admin (`created_by ≠ file_owner`) adding a *manual* Type-14 needs the
  owner's opt-in `user_preferences.allow_admin_credit_topup` (self-set via `set_my_admin_credit_topup`;
  default false). Auto-credits (Type-2 cert, `credit_source_tr_id` non-null) bypass consent. FE
  precedence ladder: `not_partner` → `no_consent` → `exhausted`.

---

## 7. Why this skill exists — the three recurring bug classes

Each has burned a real session. Reason about them explicitly before touching this code.

**(a) Surplus-on-close must RELEASE to the pool.** The pool's outflow term subtracts *every* Type-14 on
the partner's owned files. When a file closes with unused budget (a surplus), that surplus should flow
back to the owner's pool — the file no longer needs the headroom. The recurring bug: `pool_available`
keeps subtracting a **closed** file's Type-14 draw, so closing a file *consumes* the pool forever
instead of *releasing* it. The close-time mechanism is `budget_return_on_close` (it routes through
`file_budget_status_for`); **verify live whether close emits a Type-16 return vs. excludes closed files
from the outflow term — do not assume.** Invariant to hold: *closing a file must stop it drawing on the
owner's pool.*

**(b) The outflow formula silently omits categories.** BUG 347: on-customer expenses (`type=1,
on_customer=true`) and reimbursements paid (`type=13`) were invisible to the budget. Whenever you touch
the outflow definition, enumerate ALL money-out types (`1` firm, `1` on-customer, `13` reimbursement)
and confirm all three sites (§4) agree. A missing category always reads as *too much headroom*.

**(c) "Credits" and "budget" are one meter with two live names.** The subsystem shipped as **credits**
(Type-14 "Credits Add", `fd_credits_status_*`, `admin_finances_credits_status`) and was later
rescoped/renamed toward **file budget** (`file_budget_status_for`, `admin_finances_budget_status`) — but
**both names are live in the code side by side** (legacy twin view, `fd_credits_status_for_many` RPC).
Separately, **"points" is a THIRD thing** (§8), not a synonym for budget, even though `budget_consumed`
carries "budget" in its name. A mid-work scope correction from a "credits" mental model to
"files-budget + points" is exactly this trap. Rule: treat *credits ≡ file budget* (money limit), and
keep *points/GES* strictly separate (effort cost). Never assume the old name is gone.

---

## 8. Points / GES — the effort-cost meter (separate; route detail out)

Points (`file_budget.budget_consumed`) measure **effort + age**, and set each file's share of the
firm's overhead via the General Expenses Share (GES). Stably true today:

- Three buckets: **task points** (`point_ledger` type 1 — *the owner's own work on his own file is
  excluded*), **manual points** (certified grants), **age points** (a file being open).
- **Age points are MFN-only and front-loaded** — charged on the matter (`file_class = 2`) alone, so
  opening sub-files does not multiply cost; a large opening fee decays to a daily floor; accrual
  freezes on close. (Constants live in `private.fd_on_fd_a_cr_iu`.)
- A file's GES bill = its points × a cost-per-point derived from firm overhead ÷ total firm points,
  plus a retained markup.

> **Do NOT reproduce the exact rate/freeze formula as settled fact.** `docs/FINANCIAL-MODEL.md` is a
> live-plus-roadmap mix that supersedes its own body in the 2026-06-17 UPDATE boxes: the freeze is now
> **annual + on-close** (not monthly), the rate collapsed to a **single firm-wide** per-point price (no
> branch-local tier), and Part C reads "not started." **Anchor to the UPDATE boxes, route rate/freeze
> detail to FINANCIAL-MODEL.md, and flag which parts are live for re-check** before changing GES math.
> Points/GES matters here only so it is not confused with the file-budget meter (§7c).

---

## 9. Surfaces (where the meters render)

| Surface | File | Meter |
|---|---|---|
| File-budget status hook | `apps/web/hooks/use-fd-budget-status.ts` (`file_budget_status_for`) | File budget |
| Partner-pool status hooks | `apps/web/hooks/use-partner-pool-status.ts` (`_for` / `_for_file`) | Pool |
| Pre-flight block screen (budget) | `components/portal/BudgetLimitNotice.tsx` (`task_block` / `expense_block`) | File budget |
| Pre-flight block screen (pool) | `components/portal/PartnerPoolBlockNotice.tsx` (`exhausted`/`not_partner`/`no_consent`) | Pool |
| Pool inflow-% mutation | `lib/mutations/partners.ts` → `set_partner_pool_inflow_pct` | Pool |
| Partners dashboard | `(admin)/admin/finances/partners/page.tsx`, `(members)/.../partners/page.tsx` | Pool |
| Balances (added / outflow / remaining) | `(members)/.../balances/page.tsx`, `MemberBalanceListRow.tsx` | File budget |
| Files-page usage chip / revenue Expenses tab | `(admin)/admin/files/page.tsx`, `.../finances/revenue/page.tsx` | File budget |

Both block notices surface the reason **before** the user fills the form (avoiding a cryptic 409), and
both carry the `br330` "trigger-instead" action — hold the create and fire it automatically once the
cap/pool can absorb it (only for `expense_block` / `exhausted`). Both render `triggerError` on the
early-return path (an earlier bug swallowed it).

---

## 10. Quick pitfalls checklist

1. Changing outflow math? Touch **all three** sites (§4) or the Balances page lies.
2. Enumerate every money-out type: `1` firm, `1` on-customer, `13` reimbursement (§7b).
3. Read status via the **DEFINER RPC**, never the invoker view, or it diverges by user (§5).
4. Budget is **MFN-scoped**; GFN is `unlimited`; cascade is **down** (file + descendants).
5. Closing a file must **release** its surplus to the owner's pool, not keep consuming it (§7a).
6. `credits` ≡ file budget (money); `points`/`budget_consumed` ≡ effort (GES) — different meters (§7c).
7. Auto-Type-14 on Type-2 cert clamps to `MIN(50%, pool_available)`; bypasses admin consent.
8. Admin-on-behalf manual credit-add needs `allow_admin_credit_topup`; owner-self is exempt.
9. Pool is computed, not stored — never "fix" it by writing a balance; fix the source rows/formula.
10. The partner-pool constant (0.90) and file-budget thresholds (75/90/100) are fast-moving — confirm live.

---

## Related

- [[transactions-domain-model]] — the base 13 types, `tr_on_tr_b_iu`, tab views. **Read it first.**
- `docs/FINANCIAL-MODEL.md` — authoritative (and self-superseding) points/GES design; route rate/freeze
  detail here and flag live-vs-roadmap.
- Vault logs: `2026-05-19_credits-limit-system`, `2026-05-27_partner-credits-pool`,
  `2026-07-09_bug347_file_budget_full_credit_outflow`, `2026-06-20_gate-partner-pool-status-rpcs`,
  `2026-06-01_soft-delete-transactions-exclude-from-totals`, `2026-07-10_partner-ges-settlement`.

## Changelog

- **1.0.0** — Initial release. Three-meter model (file budget · points/GES · partner pool), the BUG 347
  canonical outflow formula and its three-site drift hazard, the SECURITY-DEFINER read rule, the
  partner-pool funding governor with consent, the three recurring bug classes (surplus-on-close,
  outflow omission, credits↔budget naming), surfaces map, and pitfalls. Points/GES rate/freeze routed to
  FINANCIAL-MODEL.md and flagged for live re-check.
