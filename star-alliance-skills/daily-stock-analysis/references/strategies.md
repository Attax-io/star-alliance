---
type: Document
timestamp: 2026-07-02T12:28:13Z
---

# Strategies — the fifteen built-in modes

The pipeline ships fifteen named strategies. Fourteen are *analytical* (run as
part of the daily batch); one — Agent Q&A — is *interactive* (the user
chats with the pipeline through the web workbench or compatible Bot).
Each strategy's contract: what it detects, the data it needs, when to use
it, and what it contributes to the Decision Dashboard.

## 1. Moving Average (均线)

- **Family:** Trend
- **What it detects:** Golden cross (MA5 crosses above MA10/MA20),
  death cross, MA fan-out (5/10/20/60 spread), MA20 as support flip, MA60
  as directional filter, 乖离率 (deviation) extremes.
- **Data needed:** OHLCV daily; MA5/10/20/60 series.
- **Use when:** the question is "is the tape trending" — long-only setups
  favour MA5 > MA10 > MA20 > MA60; short candidates use the inverse.
- **Dashboard contribution:** Trend label, score weighting, buy/sell
  levels (MA20 support / MA60 resistance).

## 2. Wyckoff (威科夫)

- **Family:** Structure
- **What it detects:** Accumulation phases (PS, SC, AR, ST, Spring,
  Test, SOS, LPS), distribution phases, UTAD, climactic action.
- **Data needed:** OHLCV + volume spread analysis, multi-month window
  (90+ bars preferred).
- **Use when:** the question is "what is the operator doing" — a Spring
  in an accumulation range is the high-conviction signal; UTAD at
  distribution top is the bearish mirror.
- **Dashboard contribution:** Background regime tag, catalyst weight
  (+15 if Spring confirmed, -15 if UTAD confirmed), operation
  checklist bias.

## 3. Elliott Wave (波浪)

- **Family:** Structure
- **What it detects:** Impulse wave counts (1-2-3-4-5), corrective wave
  counts (A-B-C, W-X-Y, etc.), Fibonacci extensions and retracements,
  Wave-3 acceleration, Wave-5 exhaustion.
- **Data needed:** OHLCV across at least one full cycle (typically
  months to a year).
- **Use when:** a multi-month or yearly view is needed and the count
  confidence is high. Wave counts are *interpretation-heavy* — only
  use when the structural breakouts confirm the count.
- **Dashboard contribution:** Trend label, score weighting, buy/sell
  levels anchored to Fibonacci extensions.

## 4. Trend (趋势)

- **Family:** Trend
- **What it detects:** Multi-timeframe trend agreement (daily + weekly),
  breakout from consolidation, breakdown from distribution, trend line
  touches, channel direction.
- **Data needed:** OHLCV daily and weekly; support/resistance lines.
- **Use when:** the question is "is the trend my friend" — the entry
  gating step before any strategy can fire.
- **Dashboard contribution:** Trend label (single source of truth for
  the dashboard trend field); pass/fail for any trend-following read.

## 5. Hotspot (热点题材)

- **Family:** Theme / Event
- **What it detects:** Theme intensity (mentions per day across news +
  social), sector rotation strength, news co-occurrence with the
  ticker, theme persistence half-life.
- **Data needed:** News + sector moves + tickers; works best with at
  least one of `ANSPIRE_API_KEYS`, `SERPAPI_API_KEYS`.
- **Use when:** the question is "is there a narrative drive here" — a
  new theme can lift weak technicals; an exhausted theme can wreck
  strong fundamentals.
- **Dashboard contribution:** Catalyst weight, risk alerts (theme
  exhaustion risk), trend label nudges.

## 6. Event-driven (事件驱动)

- **Family:** Theme / Event
- **What it detects:** Earnings surprise (beat/miss magnitude),
  guidance change, M&A activity, regulatory events, contract wins,
  dividend changes, index inclusion / exclusion.
- **Data needed:** News + filings + announcements; reliable news
  feeds materially improve this strategy.
- **Use when:** a discrete event is the *reason* to look at the stock —
  earnings tonight, regulatory action pending, M&A speculated.
- **Dashboard contribution:** Catalyst factors (top bullet), risk
  alerts (negative event), score weighting.

## 7. Growth (成长)

- **Family:** Fundamental
- **What it detects:** Revenue YoY/QoQ growth, earnings growth,
  growth durability (margin trend), growth quality (cash vs.
  accrual), forward growth consistency.
- **Data needed:** Fundamentals (revenue, net income, cash flow) over
  8 quarters minimum.
- **Use when:** the question is "is this a compounding business" —
  pairs with Valuation (Strategy 12) for GARP-style reads.
- **Dashboard contribution:** Long-horizon catalyst weight, score
  weighting (+/- based on growth quality).

## 8. Sentiment (舆情情绪)

- **Family:** Sentiment
- **What it detects:** Bull/bear/neutral ratio in news and social,
  attention peak (search + mention spikes), contrarian signal (extreme
  bullishness often tops; extreme bearishness often bottoms).
- **Data needed:** Social + news sentiment scores; English-quality
  social feeds (Reddit, X / Twitter, Polymarket via Stock Sentiment
  API) are optional and US-only.
- **Use when:** the question is "what is the crowd pricing in" —
  contrarian setups read extreme sentiment; momentum setups read
  confirmatory sentiment.
- **Dashboard contribution:** Risk alerts (extreme sentiment flag),
  score weighting (contrarian reversal points), operation checklist.

## 9. Capital Flow (资金流)

- **Family:** Flow
- **What it detects:** 主力 (institutional) net flow, 散户 (retail) net
  flow, north-bound flow (沪深港通), dragon-tiger lists (龙虎榜),
  intraday large-order concentration.
- **Data needed:** Funds flow feeds. Strongest for A-share via
  TickFlow + AkShare; HK via Longbridge; US partial via Longbridge;
  **JP/KR: `not_supported` for these fields** — strategy degrades,
  pipeline marks `capital_flow: not_supported` in the output.
- **Use when:** the question is "who is buying / who is selling" — the
  distinctive Chinese-market read; supplements trend signals with
  participant behaviour.
- **Dashboard contribution:** Risk alerts (净流出), catalyst factors
  (净流入), operation checklist bias.

## 10. Chip Distribution (筹码分布)

- **Family:** Flow
- **What it detects:** 获利盘比例 (profit-taking ratio), 集中度
  (concentration), average cost basis, trapped chips (套牢盘),
  peak-to-trough distribution shape.
- **Data needed:** Holder distribution + cost basis. A-share via
  AkShare / Tushare; HK via Longbridge; US / JP / KR: **`not_supported`**
  for non-CN markets — strategy degrades.
- **Use when:** a Chinese-market read needs "where is the crowd's
  pain / pleasure" — a 集中度 > 30% with 套牢盘 above current price
  is real overhead supply.
- **Dashboard contribution:** Risk alerts (拉升阻力 due to dispersion),
  score weighting (compression thesis).

## 11. Technical Composite (技术综合)

- **Family:** Technical
- **What it detects:** Multi-indicator consensus — MA + MACD + RSI +
  KDJ + BOLL — with weighted voting. Reaches Buy when > 60% of
  indicators agree; Sell when < 40% agree.
- **Data needed:** OHLCV + all five indicator series.
- **Use when:** the question is "what does the technical suite say" —
  the conservative default, especially when single-indicator signals
  contradict each other.
- **Dashboard contribution:** Score weighting (50% of base score),
  trend label corroboration.

## 12. Valuation (估值)

- **Family:** Fundamental
- **What it detects:** PE, PB, EV/EBITDA, PEG vs sector peers and
  trailing history. Cross-section percentile (where in the sector's
  range?) plus time-series percentile (where in its own range?).
- **Data needed:** Fundamentals + sector peer set.
- **Use when:** the question is "is this priced correctly" — pairs
  with Growth for GARP reads.
- **Dashboard contribution:** Score weighting (cheap = +ve, expensive
  = -ve), risk alerts (估值高位), catalyst (估值修复).

## 13. Backtesting (回测)

- **Family:** Automation
- **What it detects:** Hit rate, max drawdown, Sharpe, average win /
  loss ratio on a candidate parameter set the user supplies.
- **Data needed:** Strategy spec (entry/exit rules + parameters) +
  OHLCV history spanning at least one full market cycle.
- **Use when:** validating *before* committing a strategy to live —
  this is the safety net, not a daily signal. Run after designing a
  strategy in `trading-strategy`.
- **Dashboard contribution:** Optional dashboard module — emits a
  Backtest Report rather than a Decision Dashboard; web workbench
  surfaces both.

## 14. Expectation (预期)

- **Family:** Theme / Event
- **What it detects:** Forward estimate revisions (EPS / revenue
  consensus delta over 30/60/90 days), analyst price target gap,
  consensus dispersion (high dispersion = more uncertainty).
- **Data needed:** Consensus estimates + price targets; Tushare +
  Longbridge cover this best.
- **Use when:** the question is "is the market repricing this
  forward" — rising revisions are the cleanest pre-earnings
  catalyst.
- **Dashboard contribution:** Catalyst factors (estimate upgrades),
  risk alerts (estimate downgrades), score weighting.

## 15. Agent Q&A (策略问股)

- **Family:** Interactive
- **What it detects:** Whatever the user asks — the Agent mode lets
  you question the dashboard in plain language against any
  combination of the above 14 strategies. Multi-turn memory;
  per-turn evidence citation; export to push channels.
- **Data needed:** same data the daily batch uses, plus the user's
  follow-up prompts.
- **Use when:** the dashboard says one thing and you want to push
  back — "show me the dragon-tiger list for the past 5 days",
  "rerun the Wyckoff phase against a 6-month window",
  "explain the catalyst weight".
- **Dashboard contribution:** Lives in the web workbench `/chat` page
  and as a Bot endpoint, not in the daily push. Turn off with
  `AGENT_MODE=false`.

## Strategy selection precedes data config

The five operating principles assert: *match strategy to regime before
loading data.* A quick mental model:

- **Tape is trending up** → MA + Trend + Technical Composite +
  (optional) Elliott Wave. Don't load heavy `capital_flow` /
  `chip` — chase the tape, don't fight it.
- **Tape is ranging** → Wyckoff + Technical Composite + Chip
  Distribution. Capital flow inside the range tells you who's
  accumulating.
- **Tape is eventful** → Event-driven + Hotspot + Expectation.
  Catalyst factors dominate; trend signals are secondary.
- **Tape is volatile / uncertain** → Sentiment + Valuation +
  Risk-off checklist. Less is more — pick three strategies max.
- **JP / KR markets** → only the strategies that don't require
  `capital_flow` / `dragon_tiger` / `boards`: Trend, MA, Technical
  Composite, Hotspot, Event-driven, Growth, Sentiment, Valuation,
  Expectation, Agent Q&A. The others degrade.

This is the same regime-to-strategy map `cn-market-strategy-pack`
describes in richer detail; here the call to action is "which
subset of the 15 do I enable today, and which data layer do I
need to keep fed."
