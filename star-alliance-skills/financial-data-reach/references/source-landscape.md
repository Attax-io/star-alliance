---
type: Document
title: Source Landscape
description: The financial-data source classes in depth — quotes, fundamentals, filings, earnings/estimates, macro, news — with free vs paid trade-offs, official primaries, the vendor landscape, and how to pick one source per question.
timestamp: 2026-06-28T00:00:00Z
---
# The source landscape

The point of this reference is not a directory of APIs — those churn — but a way to *reason* about where a number should come from. The shape holds even as specific vendors come and go: every financial question has a natural source class, each class has a primary (authoritative, usually free, often raw) and a vendor tier (normalized, point-in-time-stamped, costed), and the right pick is the cheapest source that meets the fidelity the question demands.

## The decision, in one move

1. State the question in one sentence with its as-of date.
2. Name the **data class** it belongs to (below).
3. Within the class, pick the **cheapest source that meets the fidelity bar** — exploration tolerates a free API; a load-bearing number wants a primary or a reconciled vendor.
4. Record provenance with the data: source, pull timestamp, as-of date, identifier scheme, currency.

Fidelity bar examples: a quick "roughly where does this trade" tolerates a free delayed feed; "the exact diluted EPS that fed the FY2023 P/E in this memo" demands the filing.

## The classes

### Quotes / OHLCV / market structure
What it answers: price, volume, returns, and the microstructure around them (spread, depth, options skew, futures basis).
- **Primary:** the exchange tape itself, and consolidated feeds.
- **Free tier:** delayed or end-of-day APIs — fine for shape-checking and historical exploration; watch adjustment handling.
- **Vendor:** LSEG and similar for real-time, deep history, corporate-action-clean series, and derivatives analytics (vol surfaces, curves, basis).
- **Watch:** adjusted vs raw prices (store both / store factors), exchange session and timezone, and that "volume" can mean very different things across consolidated vs primary-listing feeds.

### Fundamentals
What it answers: income statement, balance sheet, cash flow, per-share metrics, capital structure.
- **Primary:** the filing (see Filings). Authoritative, but raw and inconsistently tagged across companies and years.
- **Vendor:** normalized fundamentals are where vendors earn their keep — Daloopa, S&P Capital IQ, bigdata.com map heterogeneous filings into a consistent schema and (the valuable part) point-in-time-stamp them. The cost buys you not having to parse a thousand 10-Ks by hand.
- **Watch:** as-reported vs as-restated (a point-in-time landmine — see [[point-in-time-correctness]]), differing definitions of "free cash flow" / "net debt," and fiscal-calendar misalignment across peers.

### Filings
What it answers: the official, legally-binding corporate record — 10-K (annual), 10-Q (quarterly), 8-K (material events), proxy/DEF 14A, plus non-US equivalents (annual reports, RNS, etc.).
- **Primary:** SEC EDGAR (US) is free, complete, and authoritative; map companies by CIK, not ticker. Non-US: the relevant national regulator or exchange.
- **Vendor:** convenience layers that parse, diff, and alert on filings; useful for scale, but the filing itself is truth.
- **Watch:** the filing *date* vs the period it covers (the gap is the point-in-time window), amended filings (10-K/A) that supersede, and that the financial statements live in the exhibits and footnotes, not just the face statements.

### Earnings & estimates
What it answers: reported actuals, consensus estimates, guidance, surprise history, revisions.
- **Primary:** actuals come from the filing and the earnings release (8-K exhibit). Guidance comes from the release and the call.
- **Vendor:** consensus and estimate history are almost entirely vendor territory (you cannot derive "what the street expected" from a primary source) — the major estimate aggregators, plus bigdata.com / S&P for digests and previews.
- **Watch:** estimate consensus is itself point-in-time (the consensus *as of* the day before the print, not today's), and "surprise" depends on which consensus snapshot you diff against.

### Macro series
What it answers: rates, inflation, employment, output, money supply, FX.
- **Primary:** the official statistical agency, always first — FRED (a free aggregator over US series), BLS, BEA, Eurostat, OECD, the Fed/ECB/BoE, IMF/World Bank. These are authoritative and free.
- **Vendor:** LSEG and similar for cleaned, aligned, real-time macro and curve construction.
- **Watch:** macro data is *heavily* revised — the first print of GDP or payrolls is not the final number. Vintage/ALFRED-style point-in-time series matter enormously for any backtest (see [[point-in-time-correctness]]). Seasonal-adjustment and base-year changes also silently shift a series.

### News & sentiment
What it answers: dated event flow, catalysts, narrative, and quantified sentiment.
- **Primary / financial:** financial-news feeds and the regulated disclosure channels (8-K, RNS) for hard events.
- **Sentiment / social:** *not this craft.* Social posts, transcripts, and forum sentiment are **agent-web-reach**'s domain — it reaches the blocked platforms and cleans the text. This craft consumes financial *feeds*; web-reach hands over social text.
- **Watch:** dedupe wire echoes, attach timestamps in a single timezone, and never let undated commentary masquerade as a dated catalyst.

## Free vs paid — the honest trade-off

- **Free (EDGAR, FRED, BLS, delayed quote APIs):** authoritative for primaries (filings, macro), but raw, rate-limited, and you do the normalization and point-in-time work yourself. Perfect for exploration and for any number you can get from a primary.
- **Paid (LSEG, Daloopa, S&P Capital IQ, bigdata.com, estimate aggregators):** they sell normalization, point-in-time stamping, coverage breadth, and real-time access — the expensive-to-build parts. Worth it when you need consistent cross-company schemas, historical point-in-time fundamentals/estimates, or real-time depth. Not a substitute for checking the primary on a load-bearing number.

The rule that survives every vendor change: **primary is truth; a vendor is convenience over truth.** When they disagree, the primary wins and the gap is a finding to log.
