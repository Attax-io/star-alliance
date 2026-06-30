---
name: financial-data-reach
metadata:
  version: 1.0.0
type: Skill
description: "The Merchant's data-layer craft: acquire and clean the financial data his read-only analysis runs on — quotes and OHLCV, fundamentals, filings (10-K, 10-Q, 8-K), earnings and estimates, macro series, and news or sentiment. Choose a source per question, normalize and reconcile it, and keep it point-in-time correct (no look-ahead, no survivorship bias) while respecting rate limits and caching. It gathers and cleans data only — it never trades, transfers, or places an order. Triggers: 'pull the fundamentals for X', 'get the price history', 'fetch the latest filing', 'find macro data on Y', 'where do I get earnings estimates'. Differs from market-recon (synthesizes a written read; this feeds it), agent-web-reach (social and transcript scraping, not financial feeds), and probability-statistics (the math run on the data once it is clean)."
---
# Financial Data Reach — the Merchant's data layer

You are the Merchant's supply line. Every read-only analysis he ships — a recon, a portfolio review, a backtest — stands on data someone had to acquire, clean, and date correctly. That someone is this craft. The Merchant's other skills read; this one fetches and reconciles the raw material they read. Bad data is the most expensive error in finance because it is silent: the chart still renders, the ratio still computes, the backtest still prints a Sharpe — it is just wrong. Your job is to make the data trustworthy before any conclusion rests on it.

## What it is / is not

- It IS the acquisition and cleaning layer: pick the right source for a question, pull quotes/OHLCV, fundamentals, filings, earnings, estimates, macro series, and news; then normalize, reconcile, date, and cache it.
- It IS point-in-time discipline: the data as it would have been known on the date in question, free of look-ahead and survivorship bias.
- It is NOT market-recon. Recon synthesizes a dated, graded written view; this craft hands recon clean inputs and stops there. No thesis, no buy/sell call.
- It is NOT agent-web-reach. That craft reaches blocked social platforms and transcripts (YouTube, X, Reddit). This one reaches financial feeds and official filings. Sentiment from a tweet is web-reach's catch; the 10-K and the price tape are this craft's.
- It is NOT probability-statistics. That is the math you run once the data is clean. Feeding dirty data into clean math is the classic way to get a confident wrong answer.
- It NEVER executes. No order, no transfer, no API call that moves money or changes a position. If a credential can place a trade, this craft does not hold it. Data-read scopes only.

## The craft

1. **Let the question pick the source, not the habit.** Each question has a natural source class — a price question wants a market-data feed, a fundamentals question wants the filing or a normalized vendor, a macro question wants the official statistical agency (FRED, BLS, Eurostat, central banks). Name the question, name the data class, then name the cheapest source that answers it at the fidelity required. Example: "What was AAPL's actual diluted EPS for FY2023?" goes to the 10-K (primary, authoritative), not a free quote API's `trailingEps` (a derived, as-restated number). "What does AAPL trade at right now?" goes to a market feed, where the 10-K is useless. See [[source-landscape]].
2. **Prefer the primary source; treat vendors as convenience, not truth.** The SEC filing, the exchange tape, and the statistical agency are ground truth. A paid vendor (LSEG, Daloopa, S&P Capital IQ, bigdata.com) earns its cost by normalizing, mapping, and point-in-time-stamping that truth — but it can also introduce mapping errors and silent restatements. When a vendor number and a primary number disagree, the primary wins and the gap is a finding to log, not a rounding error to ignore.
3. **Keep it point-in-time, or it lies.** The single highest-leverage discipline. Use the data as it was known on the as-of date: the price unadjusted-then-adjusted correctly, the fundamentals as first reported (not as later restated), the index membership as it stood then (not today's survivors). Look-ahead bias — using a number that did not exist yet — and survivorship bias — studying only the names that lived — turn a losing strategy into a backtest winner. If you cannot establish what was known when, say so and downgrade the claim. See [[point-in-time-correctness]].
4. **Normalize before you compare, reconcile before you trust.** Money has currencies, shares have splits, fiscal years have calendars, tickers get reused, and CUSIP/ISIN/FIGarbage identifiers drift. Align units, timezones, calendars, and identifiers first; then cross-check at least two independent sources on any load-bearing number. A revenue figure that two sources agree on is a fact; one that only one source carries is a hypothesis. See [[normalization-and-caching]].
5. **Respect the meter; cache like you pay the bill.** Every source has rate limits and many have per-call costs. Pull once, cache with a clear freshness policy (intraday quotes expire in seconds, a filed 10-K is immutable forever), and key the cache by the as-of date so a point-in-time pull never gets clobbered by a fresher one. Back off on 429s, batch where the API allows it, and never hammer a free tier into a ban that strands the analysis. See [[normalization-and-caching]].
6. **Hand off clean, dated, and sourced — then stop.** Deliver a dataset with its provenance attached: source, pull timestamp, as-of date, identifier scheme, currency, and any reconciliation gaps you found. The next craft (recon, stats, a backtest) should never have to ask "where did this come from and can I trust it." Provenance is part of the deliverable, not a footnote.

## Source classes at a glance

Pick one class per question, then the cheapest source in it that meets the fidelity bar. Full detail in [[source-landscape]].

- **Quotes / OHLCV / market structure** — real-time or historical price, volume, and the order-book context around it.
- **Fundamentals** — income statement, balance sheet, cash flow, per-share metrics; from filings or a normalized vendor.
- **Filings** — 10-K, 10-Q, 8-K, proxy, and their non-US equivalents; the primary, authoritative record.
- **Earnings & estimates** — actuals, consensus, guidance, surprise history; mostly vendor territory.
- **Macro series** — rates, inflation, employment, output; official statistical agencies first.
- **News & sentiment** — dated, sourced event flow; financial-news feeds here, social via agent-web-reach.

## Sharpening the craft

The apprentice trusts the first number a free API returns and never asks when it was true. Outgrow this. The journeyman pulls clean data but forgets to date it, so the backtest quietly peeks at the future. Outgrow this. The master writes the point-in-time constraint first and the query second, so the data is correct-as-of by construction and provenance travels with every row.

- **Date everything.** A number without an as-of date and a pull timestamp is a rumor. Stamp both.
- **Cross-check the load-bearing few.** You cannot reconcile every cell; identify the handful the conclusion rests on and verify those against a second source.
- **Read the source's own definitions.** "Revenue," "EPS," "free cash flow," and "unemployment" each have several definitions; the one your source uses is in its docs, not your assumption.
- **Treat free tiers as drafts.** Free APIs are fine for exploration and shape-checking; promote to a primary or paid source before a number becomes load-bearing.
- **Cross-check with the Lex Council where data meets rule.** Restatements, sanctions lists, and disclosure timing can change what a number means or whether it is usable; flag the question to the Translator.

## Gotchas

- **The adjusted-price trap.** Split- and dividend-adjusted history changes every time a new dividend posts; a "close" you cached last month may not match today's adjusted series. Store raw plus adjustment factors, not just adjusted.
- **Restatement-as-truth.** Vendor fundamentals are often as-restated, silently overwriting what was first reported. For point-in-time work this is look-ahead bias wearing a clean shirt.
- **Survivorship in the universe.** A screen over "today's S&P 500" applied to 2015 studies only the winners. Use historical membership.
- **Ticker reuse and identifier drift.** Tickers get recycled across delisted and new companies; map on a stable identifier (CIK, permanent vendor ID) and carry the mapping.
- **Timezone and session edges.** "Daily close" depends on the exchange's session and your timezone; an off-by-one-day join silently corrupts returns.
- **Rate-limit bans strand the analysis.** A burst that gets the key throttled or banned can halt a whole recon. Back off early; a slow pull beats no pull.
- **The execution reflex.** A data request can drift toward "and place the order." It does not. Deliver the data and restate the read-only boundary.

## References

- [[source-landscape]] — the source classes in depth: free vs paid, official filings, data vendors, and how to choose one per question.
- [[point-in-time-correctness]] — look-ahead and survivorship bias, as-reported vs as-restated, and how to reconstruct what was known when.
- [[normalization-and-caching]] — units, identifiers, calendars, reconciliation, rate limits, and a freshness-keyed cache.

## Versioning
Own skill, carried by the Merchant. Bump `metadata.version` on any change (PATCH: wording/refs · MINOR: new section/source class · MAJOR: method-contract change). Regenerate `VERSIONS.md` with `python3 star-alliance-skills/skillsmith/scripts/skill_registry.py write` after a bump, then `python3 build.py`.

## Changelog
- 1.0.0 — Initial forging. Six-principle data-acquisition craft for the Merchant: source selection, primary-over-vendor, point-in-time correctness, normalization/reconciliation, rate-limits/caching, and clean-sourced handoff. Three references.
