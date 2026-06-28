---
type: Document
title: Point-in-Time Correctness
description: The discipline of using data as it was known on the as-of date — look-ahead and survivorship bias, as-reported vs as-restated, macro vintages, and how to reconstruct what was actually knowable when.
timestamp: 2026-06-28T00:00:00Z
---
# Point-in-time correctness

This is the single highest-leverage discipline in financial-data work, and the one most silently broken. A point-in-time-correct dataset answers the question: *what would I have known on this date?* — not *what do I know now about this date?* The two diverge constantly, and the divergence always flatters a backtest. The principle: **reconstruct the information set as it stood on the as-of date, no more.**

## The two biases

### Look-ahead bias — using a number that did not exist yet
The error of letting future information leak into a past decision. The most common forms:
- **Reporting lag ignored.** A company's Q1 results are *filed* weeks after the quarter *ends*. Joining "Q1 earnings" to "end-of-Q1 prices" uses a number that was not public yet. The correct join key is the **filing/release date**, not the period-end date.
- **Restatements treated as truth.** Vendor fundamentals are frequently *as-restated* — the latest, corrected value silently overwrites what was first reported. A model that "knew" the restated number on the original date is peeking. Use **as-first-reported** values for any historical decision; reserve restated values for present-day accounting analysis.
- **Macro vintages collapsed.** GDP, payrolls, and most macro series are revised repeatedly. The number printed today for 2018-Q1 is not the number traders saw in April 2018. Point-in-time / vintage series (e.g. ALFRED for FRED) preserve each release; collapsing to the latest vintage is look-ahead.
- **Index/membership and corporate actions applied early.** Knowing a merger closed, a stock joined an index, or a split happened *before the announcement date* leaks the future.

### Survivorship bias — studying only the ones that lived
The error of building a universe from today's survivors and applying it to the past. A screen over "today's S&P 500" backtested to 2010 silently excludes every company that went bankrupt, was acquired, or got dropped — exactly the losers whose absence inflates returns. The fix: **historical universe membership** — the constituents *as they stood* on each as-of date, including the names that later died.

## As-reported vs as-restated — the cleanest example

Suppose a company reported FY2022 EPS of $4.10, then restated it to $3.80 in 2024 after an accounting correction.
- A 2022 valuation decision could only use **$4.10** — that is what the market priced on.
- A 2024 audit of "what was the company's real 2022 earnings" uses **$3.80**.
- A backtest that uses $3.80 on a 2022 date is look-ahead bias: it traded on a number that did not exist for two more years.

Point-in-time correctness means the dataset can answer *both* questions because it preserves the value **and** the date each value became known.

## How to reconstruct "what was known when"

1. **Carry two dates on every fact:** the **period** it describes and the **knowledge date** it became public (filing date, release date, vintage date). Join on the knowledge date.
2. **Prefer as-first-reported sources** for historical decisions; record the restatement separately if you need it, never overwrite.
3. **Use vintage macro series** for any backtest touching macro; if only the latest vintage is available, say so and treat macro-conditioned results as upper bounds.
4. **Build the universe historically** — membership as of each date, delisted names included. If you only have today's universe, your study is exploratory, not evidential, and must say so.
5. **Apply corporate actions on their effective/announcement dates**, not retroactively to dates before they were known.
6. **Set a knowledge cutoff and enforce it** — for an as-of date `T`, every input must have a knowledge date `<= T`. A single field that violates this corrupts the whole row.

## When you cannot establish it

Sometimes the point-in-time version simply is not available (a free source carries only the latest vintage, or as-first-reported fundamentals are behind a paywall). The discipline then is honesty, not silence:
- State explicitly that the data is **as-restated / latest-vintage / survivor-only**.
- **Downgrade the claim** that rests on it — results are indicative, not point-in-time-validated.
- Flag it in the provenance so the next craft (recon, a backtest) does not mistake an exploratory number for an evidential one.

A point-in-time caveat loudly stated is a feature. A point-in-time error silently shipped is the most expensive kind of wrong, because every downstream number inherits it and none of them look wrong.
