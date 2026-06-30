---
type: Document
title: Normalization & Caching
description: Turning raw feeds into trustworthy data — aligning units, identifiers, calendars and timezones; reconciling load-bearing numbers across sources; and respecting rate limits with an as-of-keyed, freshness-aware cache.
timestamp: 2026-06-28T00:00:00Z
---
# Normalization and caching

Acquisition gets you bytes; normalization, reconciliation, and caching turn them into data you can trust and afford. The principle: **align before you compare, reconcile before you trust, and pull once.** A number that has not been normalized is not comparable; one that has not been reconciled is a hypothesis; and a source you hammer without caching is a ban waiting to strand the analysis.

## Normalize — align before you compare

Raw feeds disagree on the boring axes, and the boring axes are exactly where silent joins corrupt results.

- **Currency.** Convert to one reporting currency using a **dated** FX rate (which rate, as of which date, matters — see point-in-time). Never mix USD and reporting-currency figures in one ratio.
- **Splits & dividends.** Store **raw prices plus adjustment factors**, not pre-adjusted closes — adjusted series mutate every time a new dividend posts, so a cached "close" silently drifts. Reconstruct adjusted on read.
- **Identifiers.** Map everything to a **stable identifier** — CIK for SEC entities, a permanent vendor security ID, ISIN/CUSIP where appropriate — never the ticker. Tickers get **reused** across delisted and new companies and change on rebrands; carry the ticker↔stable-ID mapping with its own valid-from/valid-to dates.
- **Fiscal calendars.** Two peers with different fiscal year-ends are not comparable quarter-to-quarter without calendarization. Align to a common calendar before computing growth or building comps.
- **Timezones & sessions.** "Daily close" depends on the exchange session and your timezone; an off-by-one-day join silently corrupts every return downstream. Pin one timezone and the session definition.
- **Definitions.** "Revenue," "EPS (basic/diluted/adjusted)," "free cash flow," "net debt," "unemployment (U-3/U-6)" each have multiple definitions. Read the source's docs and record which definition you pulled.
- **Units & scale.** Thousands vs millions, basis points vs percent, per-share vs total. A 1000x scale error passes every sanity check that only looks at sign.

## Reconcile — verify the load-bearing few

You cannot cross-check every cell, and you do not need to. Identify the handful of numbers the conclusion actually rests on and verify **those** against an independent second source.

- A figure two independent sources agree on (within a documented tolerance) is a **fact**.
- A figure only one source carries is a **hypothesis** — usable for exploration, flagged before it becomes load-bearing.
- When two sources disagree, the **primary** (filing, exchange, statistical agency) wins over the vendor, and the gap is a **finding to log**, not a discrepancy to average away. A persistent gap often reveals a definition mismatch or a restatement.

## Cache — pull once, pay the bill once

Every source has rate limits; many have per-call costs. The cache is how you stay fast, cheap, and un-banned.

- **Key by as-of date.** A point-in-time pull for date `T` must not be clobbered by a fresher pull for `T+1`. The cache key includes the as-of/knowledge date, so each vintage persists. This is what makes point-in-time correctness durable rather than a one-time effort.
- **Freshness policy by data type.** Intraday quotes expire in seconds; an end-of-day bar is final after the session; a **filed 10-K is immutable forever** (cache it permanently). Tag each cached object with its natural TTL — caching a quote forever is as wrong as re-fetching a 10-K hourly.
- **Provenance in the cache record.** Store source, pull timestamp, as-of date, identifier scheme, currency, and the source's definition note alongside the value, so the handoff carries provenance for free.
- **Respect the meter.** Back off on 429/`Retry-After` immediately and exponentially; batch requests where the API supports it; stay under documented free-tier ceilings. A burst that gets a key throttled or banned can halt a whole recon — **a slow pull beats no pull.**
- **Invalidate deliberately.** When a corporate action, restatement, or revision lands, invalidate the affected derived series (e.g. adjusted prices after a new dividend) — but never the immutable primary records, and never the historical vintages.

## The handoff

The output of this craft is not just rows — it is **rows with provenance attached**: source, pull timestamp, as-of date, identifier scheme, currency, definitions used, and any reconciliation gaps found. The next craft (market-recon, probability-statistics, a backtest) should be able to trust the data without re-asking where it came from. Provenance is part of the deliverable, not a footnote — and it is the difference between data and a guess that happens to be in a table.
