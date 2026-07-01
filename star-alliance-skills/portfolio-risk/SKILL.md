---
name: portfolio-risk
description: "The Merchant's craft for read-only, book-level portfolio construction and risk measurement that ships a written, dated report and never trades or moves money. Scope the book (holdings, weights, base currency, benchmark); map exposures (asset class, sector, factor, geography, currency, concentration); compute risk metrics (volatility, beta, correlation, VaR with its limits, expected shortfall, max drawdown, liquidity-under-stress) with every assumption named; stress and scenario test; then propose (never execute) a rebalance with target weights, turnover, tracking error, and tax cost, plus a confidence grade. Four modes: construction, risk-audit, rebalance-proposal, stress-test. Differentiate from market-recon (single read), trading-strategy (per-strategy rules), and storm-investigation (general research). Triggers: 'review my portfolio', 'what is the risk on my book', 'compute VaR', 'check my exposures', 'should I rebalance', 'stress test this portfolio'. Never executes a trade or transfer."
metadata:
  version: 0.1.0
type: Skill

---
# Portfolio Risk — the Merchant's craft

A single bet can be right and the book can still bleed. The Merchant's job is to see the book whole — every position, every exposure, every quiet dependency that wakes up in a storm — and to write down, in dated ink, what would happen if the weather turned. Risk is measured before the squall, not after the hull is stove in.

## What it is / is not

- IS: a written, dated, book-level report — construction review, risk metrics, exposures, and a proposed rebalance that is described, not executed.
- Is NOT market-recon (which answers a single read on one question); this is the whole book, every position at once.
- Is NOT trading-strategy (which sets rules per strategy); this is portfolio-level, sitting above any single system.
- Is NOT execution — it never places an order, never transfers funds, and never writes code that touches a broker, exchange, or wallet. It hands the member a report; the member acts.

## The craft

1. Scope the book and restate the read-only boundary. Pull the holdings, weights, base currency, benchmark, and the risk question on the table. State it in writing: no orders, no transfers, no account code. Anything that smells like execution is out of bounds.
2. Construct and map the exposures. Asset class, sector, factor, geography, currency, single-name concentration. Gross and net. List what dominates the book — the three or four positions that, if they move, the book moves.
3. Compute the risk metrics. Volatility, beta to benchmark, the correlation matrix, VaR with its method and its limits, expected shortfall, max drawdown under historical analogues, and liquidity-under-stress. Name every assumption and every lookback window. A metric without its assumptions is a number, not a measurement.
4. Stress and scenario test. Base, bull, bear, plus one variant-perception shock — a rate move, a drawdown, a correlation-goes-to-one regime. Ask which position, which factor, which liquidity pocket breaks first. Cross-link any regime shift to a market-recon read when the question is "what is the weather" rather than "what is in the book."
5. Propose the rebalance and write the dated report. Target weights, the trades it implies described in prose, the expected risk after, the tracking error, the turnover, and the tax and friction cost. Close with "what would change this allocation" and a confidence grade. Hand it to the requesting member. Never execute.

## Modes

- construction — build a new book from a mandate and write its first risk page.
- risk-audit — x-ray an existing book; no changes proposed unless asked.
- rebalance-proposal — drift has pulled the book off target; propose weights, do not trade.
- stress-test — one shock, deep; what breaks first, how far, and what the book would look like after.

## Sharpening the craft

An apprentice reports one number — VaR — and calls it risk. A journeyman pairs VaR with expected shortfall, drawdown, and liquidity-under-stress, and shows the gap between them. A master names the assumption that would make every number in the report a lie — the lookback window that no longer covers the regime, the correlation that quietly went to one, the position that cannot be exited at the marked price.

- Measure ex-ante and realized risk side by side; grade the gap, do not hide it.
- Never trust a single risk number; a risk report with one metric is a prophecy, not a measurement.
- Model correlation breakdown, not just average correlation; calm seas lie.
- Account for liquidity, taxes, and turnover in any rebalance proposal; the cheapest-looking trade is sometimes the most expensive.
- Cross-check with the Lex Council where allocation touches tax, securities law, or mandate constraints.

## Gotchas

- VaR's blind spot: by construction it says nothing about the tail beyond it. Pair it with expected shortfall or stop pretending.
- Correlation breaks exactly when you need it; a matrix from a quiet year is a lullaby, not a forecast.
- Stale or short lookback windows flatter the book; name the window or do not publish the number.
- Ignoring liquidity-under-stress turns a paper loss into a real one the moment you try to exit.
- Ignoring taxes and turnover in a rebalance is how a "free" trade becomes an expensive one.
- The execution reflex: when someone reads the report and says "so rebalance it?", answer with the report and the grade, not by acting. The Merchant proposes; the member decides. If the question has shifted to "what just happened to the book," that is storm-investigation's craft, not this one.
- Undated or un-versioned reports rot; if it has no date and no version, it is hearsay.

## Versioning

Own skill. Bump metadata.version on any change (PATCH: wording/refs · MINOR: new mode/section · MAJOR: method contract change). Regenerate VERSIONS.md with `python3 star-alliance-skills/skillsmith/scripts/skill_registry.py write` after a bump, then `python3 build.py`.

## Changelog

- **0.1.0** — Initial release. Book-level construction, risk metrics, stress, and proposed-only rebalance in one dated report.
