---
type: Document
title: Live Review Surfaces — Alert Rules & Signal Queue
description: Housekeeping reference for auditing live alert-rule lifecycle (price_cross / volume_spike trigger + cooldown semantics) and the DecisionSignal status queue (active → expired / invalidated / closed), distilled and translated from the daily-stock-analysis alert-center and decision-signal specs. The reviewer audits these surfaces; it never creates rules, fires triggers, or executes trades.
timestamp: 2026-06-28T00:00:00Z
---

# Live Review Surfaces — Alert Rules & Signal Queue

Static strategy docs (`docs/strategy/`) capture *intent*. Two **live** surfaces capture
*standing state* that drifts on its own between reviews: the **alert-rule roster** and the
**signal status queue**. This reference tells the reviewer how to audit them as
housekeeping — confirming the live state still matches declared intent, flagging stale or
contradictory entries. **The reviewer audits only; it never creates a rule, forces a
trigger, mutates a signal status, or places an order.**

---

## A. Alert-rule lifecycle (audit surface)

An `alert_rule` is a standing, user-managed watch condition. Reviewing it means checking
that each rule is still wanted, still valid, and not silently suppressed.

### A.1 Rule shape (the fields a review reads)

| Field | What a review checks |
| --- | --- |
| `id` / `name` | Identity; a missing/auto-generated name on a long-lived rule is worth a readable rename flag. |
| `target_scope` / `target` | Scope (single symbol, watchlist, portfolio, market) and its referent. Flag rules pointing at a delisted symbol or a deleted account/watchlist. |
| `alert_type` | Rule type (see A.2). Flag any rule of a type the runtime no longer executes. |
| `parameters` | Type-specific thresholds (`direction`, `price`, `multiplier`, …). Flag absurd/never-trigger thresholds. |
| `severity` | `info` / `warning` / `critical`. Flag mismatches (e.g. a stop-loss breach rule left at `info`). |
| `enabled` | Whether the rule is live. Flag rules disabled long ago that should be deleted, or critical rules left disabled. |
| `cooldown_policy` | Cooldown config (see A.3). |
| `notification_policy` | Delivery routing; defaults to the alert route. |
| `source` | Where it came from: `legacy_env`, `web`, `api`, `import`. Useful for de-duplicating legacy vs. managed rules. |
| `created_at` / `updated_at` | Age and last edit — staleness signal. |

### A.2 The two runtime rule types this review centres on

Many rule types exist in the spec, but a review prioritizes the **runtime-executable**
ones. Two are the housekeeping core:

- **`price_cross`** — fires when the live price crosses a fixed level.
  - `direction`: `above` / `below`
  - `price`: the threshold level
  - Semantics: real-time price breaks up through (`above`) or down through (`below`) `price`.
  - Review checks: is `price` still anywhere near the current trading range? A cross
    level far from the market is either stale (the symbol moved) or a never-trigger rule.

- **`volume_spike`** — fires on an abnormal volume surge.
  - `multiplier`: how many times the baseline volume.
  - Semantics: latest volume exceeds the ~20-day average volume by `multiplier`×.
  - Review checks: is `multiplier` sane (e.g. not `0`, not so high it can never fire)?

> Other types (`price_change_percent`, and technical-indicator / portfolio / market-light
> families) extend this surface but are out of the housekeeping core. Treat a rule whose
> `alert_type` the runtime no longer accepts (placeholders like `sentiment_shift`,
> `risk_flag`, `custom`) as **stale** — flag it; the worker will skip it silently.

### A.3 Trigger and cooldown semantics (what a review must not misread)

- **A trigger is a record, not the rule.** Each real firing writes an `alert_trigger`
  (`observed_value`, `threshold`, `reason`, `triggered_at`, `status`). `status` is one of
  `triggered` / `skipped` / `degraded` / `failed`. A normal *not-triggered* poll writes
  **nothing** — so absence of recent triggers is not evidence a rule is broken.
  - `skipped` = no evaluable condition this round (e.g. missing real-time quote).
  - `degraded` = data source / snapshot / parse problem; result unusable, no notification.
  - `failed` = evaluation error on that one rule; it does not stop the other rules.

- **Cooldown suppresses repeat noise; it is not the rule being off.** A managed rule's
  `cooldown_policy.cooldown_seconds` (default 24h; `0` disables) drives an `alert_cooldown`
  row with `last_triggered_at`, `cooldown_until`, and a `state` of `active` / `expired`.
  While `cooldown_until` is in the future the rule is *intentionally quiet*.
  - Review trap: **`cooldown_active=true` does not mean the rule misfired or is disabled.**
    Read `cooldown_until` before flagging "rule stopped working."
  - Legacy `AGENT_EVENT_ALERT_RULES_JSON` rules use an in-process fingerprint instead of a
    persisted cooldown — their suppression does not survive a restart, and that is expected.
  - For batch scopes (`watchlist` / `portfolio_holdings`), the list-level `cooldown_active`
    is only a *parent summary*; per-child cooldown lives in the trigger history keyed by the
    effective target. Don't assert a child's state from the parent badge.

### A.4 Alert-rule review checklist

> [!info] For each live rule, confirm and flag:
> - Type is still runtime-executable (not a placeholder type the worker will skip).
> - `target` still resolves (symbol listed; account/watchlist exists).
> - Threshold is plausible vs. current range (`price_cross.price`, `volume_spike.multiplier`).
> - `severity` matches the rule's real consequence.
> - `enabled` state is intentional (no zombie disabled rules, no critical rule left off).
> - A long cooldown isn't being misread as a dead rule — check `cooldown_until`.
> - No duplicate of a `legacy_env` rule already managed via `web`/`api`.

---

## B. Signal status queue (audit surface)

A `DecisionSignal` is a recorded recommendation with evidence, a plan, a lifecycle, and a
source — **a queryable index over reports; it never places an order or rebalances.**
Reviewing the queue means auditing that each signal's status reflects reality.

### B.1 Status lifecycle

`status` ∈ `active` · `expired` · `invalidated` · `closed` · `archived`.

- `active` — live recommendation, still within its horizon.
- `expired` — passed `expires_at` (driven by `horizon` / market phase TTL).
- `invalidated` — superseded: a newer **opposite** active signal on the same instrument
  flips the old one to `invalidated` and records the source in metadata.
- `closed` — deliberately retired by a reviewer/user.
- `archived` — removed from the working view.

> [!warning] Terminal statuses are one-way. `expired`, `invalidated`, `closed`, and
> `archived` **cannot** be restored to `active` via a status patch. A review never tries to
> "reactivate" a terminal signal — it would open a fresh signal instead (and the reviewer
> does neither; it only flags).

### B.2 Lifecycle rules a review relies on

- **Expiry.** When `horizon` / `expires_at` aren't explicit: `alert`-sourced or
  pre-market / intraday / lunch-break / closing-auction phases default to `intraday`;
  post-market, non-trading, or unknown phases default to `3d`. An `active` signal sitting
  well past a plausible TTL is a flag — expiry may not have run.
- **De-dup / invalidation.** Same-source signals de-dup on
  `(source_report_id, source_type, market, stock_code, action, horizon, market_phase)`
  (or `trace_id` when there's no report). A new contrary active signal invalidates the
  prior one. Two co-existing `active` signals with opposite `action` on one instrument is a
  contradiction to flag — invalidation didn't fire.
- **Source.** `source_type` ∈ `analysis` · `agent` · `alert` · `market_review` · `manual`.
  Alert-born signals are minimal (`source_type=alert`, `action=alert`) when no active
  signal exists for the instrument — don't mistake a thin alert signal for a full plan.

### B.3 Signal-queue review checklist

> [!info] Scanning the queue (default view = `status=active`):
> - Any `active` signal past a sane TTL → flag possible missed expiry.
> - Two opposing `active` signals on the same instrument → flag missed invalidation.
> - A terminal signal that someone expects to be live → note it cannot be reactivated.
> - Thin `source_type=alert` signals not mistaken for full analysis plans.
> - Never patch a status during review; record the discrepancy as a finding only.

---

## C. How these feed the strategy review output

Fold live-surface findings into the same Obsidian note the static review produces, using
the existing callout vocabulary:

- `> [!warning]` — a stale rule, an over-far `price_cross`, a missed-expiry signal.
- `> [!bug]` — a genuine contradiction (two opposing active signals; a runtime-rejected rule type still enabled).
- `> [!info]` — housekeeping notes (rename a nameless long-lived rule; de-dup legacy vs. managed).
- `> [!success]` — a surface that is clean and consistent with declared strategy intent.

The reviewer reports; the human (or a separate execution surface) acts.
