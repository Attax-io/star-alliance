---
name: daily-stock-analysis
description: "AI-powered daily stock analysis for A-share HK US JP KR markets generating a structured Decision Dashboard per stock with verdict, score, trend, buy/sell levels, risk alerts, catalyst factors, and operation checklist. 15 built-in strategies: MA, Wyckoff, Elliott Wave, trend, hotspot, event-driven, growth, sentiment, capital flow, chip distribution, technical composite, valuation, backtesting, expectation, Agent Q&A. Runs automated daily analysis via GitHub Actions (zero-cost), Docker, or local scheduled task; pushes to WeChat Work Feishu Lark Telegram Discord Slack or email. Includes web workbench and multi-round Agent Q&A. Distilled from ZhuLinsen/daily_stock_analysis. Triggers: daily analysis, stock decision dashboard, multi-market stock report, automated stock analysis, push stock alerts. Differs from trading-strategy (systematic strategies, no automation infra), chart-patterns (reading formations, no pipeline), portfolio-risk (risk management, no daily report)."
metadata:
  version: 1.0.0
type: Skill
---

# Daily Stock Analysis — the Merchant's automation grade

A working trader does not want one perfect read; he wants **yesterday's verdict,
today's verdict, every weekday, in his chat, before the market reopens**. This
pack is the Merchant's deployment grade for the *daily-stock-analysis* system:
a five-market (A-share, HK, US, JP, KR) AI-driven analyzer that emits a
structured **Decision Dashboard** per stock, then pushes it through the
channel you actually read (WeChat Work, Feishu, Lark, Telegram, Discord, Slack,
email). It is the operational twin of `cn-market-strategy-pack` and
`market-recon` — where those are the read, this is the *daily-rhythm machine
that ships the read every weekday at 18:00 Beijing time*.

The pack is distilled from [ZhuLinsen/daily_stock_analysis](https://github.com/ZhuLinsen/daily_stock_analysis), a
production open-source system handling 5 markets, 15 strategies, 7 push channels,
and 3 deployment modes (GitHub Actions, Docker, local Python). What follows is
the Merchant's operating contract: what to deploy, what to push, what each
strategy detects, what each channel expects, and where the read degrades so you
know when to trust the dashboard and when to fall back to `market-recon`.

## What it is

- A **deployment-grade daily analysis pipeline** covering five markets
  (A-share, HK, US, JP, KR) with code-format normalisation, multi-source data
  aggregation with graceful degradation, AI-driven analysis, and push to a
  first-class channel of your choice.
- A **Decision Dashboard** output contract — fixed six-field card per stock
  with a final verdict, a score on 0–100, a trend tag, buy/sell levels,
  risk alerts, catalyst factors, and an operation checklist, plus a summary
  header that shows buy/hold/sell counts at a glance.
- A **catalogue of 15 built-in strategies** grouped into five families
  (trend, structure, theme/event, sentiment/fundamental, automation &
  backtesting, interactive Q&A), each with a defined detection logic, the
  data it needs, and the regime it fits.
- A **data layer** that picks the best source per market (TickFlow, AkShare,
  Tushare, Pytdx, Baostock for CN; YFinance / Longbridge for global; Anspire,
  SerpAPI, Tavily, Bocha, Brave, MiniMax, SearXNG for news) with a documented
  fallback chain and **degradation markers** for market-boundary gaps
  (JP/KR: `capital_flow`, `dragon_tiger`, `boards` degrade to
  `not_supported`).
- A **deployment matrix** that treats "how do I run this?" as a real choice,
  not an afterthought — three modes (GitHub Actions for zero-cost, Docker for
  private cloud, local Python for development), each with its own env-var
  contract.
- A **push-channel matrix** that treats each of 6 channels as a first-class
  output target — not a "wouldn't it be nice" — with per-channel env vars,
  signature hooks, and test patterns.
- **Web workbench + Agent Q&A mode** — a FastAPI-driven UI for manual runs,
  historical report browsing, configuration, and a multi-round chat that lets
  you question the dashboard in plain language against any of the 15
  strategies.

## What it is NOT

- **Not a trading system, broker, or order router.** It generates analysis and
  pushes it to chat. The user (or another member) acts. Placing orders is the
  user's job and is explicitly out of scope.
- **Not licensed financial advice.** Output is research and signal, not a
  recommendation. Treat every verdict as a hypothesis, not an instruction.
- **Not a bespoke strategy spec.** This is the deployment pack; turning a
  market view into a falsifiable, paper-executable strategy document is
  `trading-strategy`. The Decision Dashboard is the *output format* — it is
  not the spec.
- **Not a one-off read.** The whole point is daily rhythm + automated push.
  A single ad-hoc stock analysis still belongs to `market-recon`.
- **Not a portfolio audit.** Per-stock verdicts, not book-level exposures,
  VaR, or correlation. The book view is `portfolio-risk`.
- **Not classic chart-pattern recognition** (Bulkowski). It does ship
  technical signals but does not name formations like head-and-shoulders or
  triangles — those are `chart-patterns`.
- **Not Japanese candlestick reading** — those are `japanese-candlesticks`;
  not pure volume-price reading — those are `volume-price-analysis`.
- **Not stock selection.** Picking *which* stocks to put on the watchlist is
  upstream — AlphaSift handles screening, this system takes the watchlist
  you give it.

## Five markets — code formats the pipeline understands

The pipeline normalises every ticker to a canonical form before any data call.
Misformatted tickers are the single most common failure mode — treat this as
the contract.

| Market | Code format examples | Suffix rule | Notes |
|---|---|---|---|
| A-share (CN) | `600519`, `000657`, `300260`, `688xxx` | bare 6-digit numeric; STAR (科创板) `688xxx`, ChiNext (创业板) `300xxx` | exchange suffix not required; defaults work |
| HK (Hong Kong) | `hk00700`, `hk09988`, `hk03690` | lowercase `hk` prefix + 5-digit zero-padded code | case-insensitive; `HK00700` accepted |
| US | `AAPL`, `TSLA`, `NVDA`, `BRK.B` (or `BRK-B`) | bare ticker; dots/hyphens as in the listing | mutual funds / ETFs accepted |
| JP (Japan) | `7203.T`, `9984.T`, `6758.T` | 4-digit code + `.T` suffix (Tokyo) | `.S` (Sapporo/Nagoya) also parsed |
| KR (Korea) | `005930.KS` (KOSPI), `039490.KQ` (KOSDAQ) | 6-digit code + `.KS` or `.KQ` | KOSPI default; KOSDAQ explicit |

A complete daily watchlist mixes suffixes freely:

```
600519,hk00700,AAPL,7203.T,005930.KS
```

A-share requires the first digit to encode the board (6 = Shanghai main,
0/3 = Shenzhen main / ChiNext, 4/8 = Beijing, 5 = funds). HK requires the
`hk` prefix; missing prefix causes US-source fallback. JP `.T` and KR `.KS` /
`.KQ` are the only suffixes parsed for those markets.

## Decision Dashboard — the six-field card

Every stock produces one card. The pipeline emits a summary header first, then
one card per stock in the watchlist. Treat the six fields as the
**output contract** — a field is missing only when its source degraded.

```
🎯 2026-02-08 决策仪表盘
共分析3只股票 | 🟢买入:0 🟡观望:2 🔴卖出:1

📊 分析结果摘要
⚪ 中钨高新(000657): 观望 | 评分 65 | 看多
⚪ 永鼎股份(600105): 观望 | 评分 48 | 震荡
🟡 新莱应材(300260): 卖出 | 评分 35 | 看空

⚪ 中钨高新 (000657)
📰 重要信息速览
💭 舆情情绪: 市场关注其AI属性与业绩高增长，情绪偏积极，但需消化短期获利盘。
📊 业绩预期: 公司2025年前三季度业绩同比大幅增长，基本面强劲。

🚨 风险警报:
  风险点1：2月5日主力资金大幅净卖出3.63亿元，需警惕短期抛压。
  风险点2：筹码集中度高达35.15%，拉升阻力可能较大。
✨ 利好催化:
  利好1：公司被市场定位为AI服务器HDI核心供应商，受益于AI产业发展。
📢 最新动态: 舆情显示公司是AI PCB微钻领域龙头…
---
生成时间: 18:00
```

The six fields per card, in contract order:

1. **Verdict + Score** — `买入` (61–100), `观望` (41–60), `卖出` (0–40).
   Color-coded: 🟢 / 🟡 / 🔴. Score is a single integer in `[0, 100]`.
2. **Trend** — direction tag (`看多` bullish / `看空` bearish / `震荡`
   sideways). One of three discrete labels, never blank.
3. **Buy/sell levels** — concrete entry zone, target, and stop-loss numbers
   when the strategy produces them. Absent for strategies that are read-only.
4. **Risk alerts** — bullet list of named risk points (主力资金流出, 筹码
   集中度过高, 历史违规, etc.). Empty list is a valid value, not a
   missing field.
5. **Catalyst factors** — bullet list of positive drivers (主题催化, 业绩
   兑现, 政策利好, etc.).
6. **Operation checklist** — what the user should do this session: watch,
   trim, add, hold, exit, etc.

All six fields use emoji + Chinese labels by convention; Feishu and Lark render
them natively, Telegram and Discord need no special mark-up, and email
defaults to plain text with the emoji preserved. Full Markdown and JSON export
exist for the web workbench.

## Fifteen built-in strategies

The pipeline ships fifteen named strategies across five families. They are
read-only analysis modes the AI runs *against* the aggregated data; each one
detects a different signal pattern. See `references/strategies.md` for the
full per-strategy contract.

| # | Strategy | Family | What it detects | Data it needs |
|---|---|---|---|---|
| 1 | Moving Average (均线) | Trend | Golden/death cross, MA fan-out, support flip | OHLCV, MA5/10/20/60 |
| 2 | Wyckoff (威科夫) | Structure | Accumulation/distribution phases, springs, UTAD | OHLCV + volume spread, multi-month |
| 3 | Elliott Wave (波浪) | Structure | Impulse/corrective wave counts, Fib levels | OHLCV across cycles |
| 4 | Trend (趋势) | Trend | Multi-timeframe trend agreement, breakout/breakdown | OHLCV, daily + weekly |
| 5 | Hotspot (热点题材) | Theme/Event | Theme intensity, sector rotation, news co-occurrence | News + sector moves + tickers |
| 6 | Event-driven (事件驱动) | Theme/Event | Earnings surprise, M&A, regulatory, contracts | News + filings + announcements |
| 7 | Growth (成长) | Fundamental | Revenue/earnings growth quality vs market expectation | Fundamentals + YoY/QoQ |
| 8 | Sentiment (舆情情绪) | Sentiment | Bull/bear ratio, attention peak, contrarian signal | Social + news sentiment |
| 9 | Capital Flow (资金流) | Flow | 主力/散户 net flow, north-bound, dragon-tiger | Funds flow + A/H-specific feeds |
| 10 | Chip Distribution (筹码) | Flow | 获利盘比例, 集中度, average cost, trapped chips | Holder distribution + cost basis |
| 11 | Technical Composite (技术综合) | Technical | Multi-indicator consensus: MA + MACD + RSI + KDJ + BOLL | OHLCV + all technicals |
| 12 | Valuation (估值) | Fundamental | PE/PB/EV-EBITDA vs peers and history, PEG | Fundamentals + sector peers |
| 13 | Backtesting (回测) | Automation | Hit rate, max drawdown, Sharpe on candidate parameters | Strategy spec + OHLCV history |
| 14 | Expectation (预期) | Theme/Event | Forward estimate revisions, analyst target gap | Consensus + price target |
| 15 | Agent Q&A (策略问股) | Interactive | Multi-turn chat against any combination of the above | User prompt + context |

The Agent Q&A mode is interactive — the other fourteen are analytical and
run as part of the daily batch. Backtesting is the only one that requires a
candidate parameter set the user supplies; the other analytical strategies
derive their parameters from the data.

## Data layer — multi-source with degradation

The pipeline's principle: **never let one source outage block the dashboard**.
Every market has a primary + secondary + fallback chain; every source failure
is logged and a `degradation_marker` (one of `ok`, `partial`, `missing`,
`not_supported`) is attached to the affected fields. The user sees the marker
in the dashboard footer so they know which fields to trust.

### Market data sources

| Source | Best for | Coverage | Notes |
|---|---|---|---|
| **TickFlow** | A-share tick + minute bars | CN | Real-time tick + aggregated bars; recommended primary |
| **AkShare** | A-share fundamentals + indicators | CN | Open, broad, default fallback for A/HK |
| **Tushare** | A/HK fundamentals + history | CN / HK | Token-gated; richer fundamentals than AkShare |
| **Pytdx** | A-share real-time via TDxX protocol | CN | Lower latency; no fundamentals |
| **Baostock** | A-share free history | CN | Free, no token, daily-bar heavy |
| **YFinance** | US/JP/KR/HK fundamentals + history | Global | Default for non-CN markets; `.KS/.KQ/.T` parsed |
| **Longbridge** | HK + US professional feeds | HK/US | Token-gated, lower latency than YFinance |

Default chain per market:

- A-share: TickFlow → AkShare → Tushare → Pytdx → Baostock
- HK: Longbridge → YFinance → AkShare (fallback)
- US: YFinance → Longbridge
- JP: YFinance only (suffix `.T`); downstream `capital_flow`/`dragon_tiger`/
  `boards` degrade to `not_supported`
- KR: YFinance only (suffix `.KS` / `.KQ`); same JP boundary

### News search sources

| Source | Strong at | Region |
|---|---|---|
| **Anspire** | CN-focused web + AI ranking | CN-strong |
| **SerpAPI** | Baidu / Google result scraping | global |
| **Tavily** | General news, English | global |
| **Bocha** | CN search with AI summaries | CN |
| **Brave** | Privacy-first, English | global |
| **MiniMax** | Structured search results | mixed |
| **SearXNG** | Self-hosted no-quota fallback | deployer-hosted |

### AI models

| Provider | Notes |
|---|---|
| **Anspire** (recommended) | One key unlocks models + search; CN-friendly |
| **AIHubMix** (recommended) | OpenAI-compatible aggregator |
| **Gemini** | Google's, good price/perf |
| **Anthropic** | Claude family |
| **OpenAI-compatible** | DeepSeek, 通义千问, etc., via base URL |
| **Ollama** | Local models — Docker / local mode recommended |

A full per-market source table and the fallback chain diagram live in
`references/data-sources.md`.

## Five operating principles

These are the doctrine the pipeline is built around. They look like design
choices; in practice they are the *why* behind every decision in this skill.

1. **Dashboard-first, not data-first.** The deliverable is the six-field card,
   not a dataset. Data sources exist to feed the card; if a field degrades,
   the dashboard degrades too, transparently. Never optimise for the
   dataset's completeness at the cost of the dashboard's reliability.
2. **Multi-source with graceful degradation.** Every market has a primary +
   secondary + fallback chain; every failure is logged and tagged with a
   `degradation_marker`. The user trusts the dashboard because every
   green/yellow/red field is honest about its lineage.
3. **Automation is a deployment decision with three modes.** GitHub Actions
   is the zero-cost path for most users. Docker is the private-cloud path.
   Local Python is the development path. Each mode has its own env-var
   contract; the dashboard shape is identical across modes. See
   `references/deployment.md`.
4. **Push channels are first-class output, not afterthoughts.** Every channel
   in the matrix (WeChat Work, Feishu/Lark, Telegram, Discord, Slack, email)
   has its own env vars, signature hooks, and test pattern. The dashboard
   is built once and shipped to whichever channel(s) the user configures;
   missing channels silently disable. See `references/push-channels.md`.
5. **Strategy selection precedes data config.** Before you choose what data
   to pull, choose what strategy is reading the tape. A bull-trend stock in
   a chop market should not be loaded with `capital_flow` and `chip`
   fields — that's a range-play read. Match the strategy to the regime
   first (`cn-market-strategy-pack` does this in the read-the-market
   sense); this system runs the chosen strategy against the chosen data.

## References

The five reference files in `references/` carry the operational depth the
SKILL.md cannot. Load them when you actually deploy, configure, or
troubleshoot.

- `references/deployment.md` — GitHub Actions (zero-cost), Docker, local
  Python setup, secrets table, all CLI flags (`--debug`, `--dry-run`,
  `--stocks`, `--market-review`, `--schedule`, `--serve-only`,
  `--webui`, `--webui-only`).
- `references/strategies.md` — every one of the 15 strategies: what it
  detects, required data, regime fit, output fields it contributes to the
  Decision Dashboard.
- `references/data-sources.md` — per-market source table, fallback chain,
  degradation markers, JP/KR boundary table.
- `references/push-channels.md` — config for all 6 channels with env-var
  names, signature verification, test patterns.
- `references/dashboard-format.md` — six-field card contract, score scale
  and color coding, summary header format, operation checklist structure.

## Quick start — eight steps

A working deployment, end-to-end, in eight steps. Zero to dashboard in an
afternoon; zero to daily push in a week.

1. **Choose deployment mode.** GitHub Actions for zero-cost and zero-server;
   Docker for private cloud; local Python for dev. (Default: GitHub
   Actions.) See `references/deployment.md`.
2. **Pick at least one AI provider.** Anspire and AIHubMix are recommended
   because one key unlocks both models and search. Set `ANSPIRE_API_KEYS`
   or `AIHUBMIX_KEY`. Optional: add `GEMINI_API_KEY`, `ANTHROPIC_API_KEY`,
   `OPENAI_API_KEY` + `OPENAI_BASE_URL` / `OPENAI_MODEL`.
3. **Set your watchlist.** Define `STOCK_LIST` as a comma-separated list of
   normalised tickers — `600519,hk00700,AAPL,7203.T,005930.KS`. This is
   the *only* required secret.
4. **Configure at least one push channel.** The dashboard is useless if it
   sits in a log file. Pick your chat (Telegram and Discord are the
   easiest) and set the channel's env vars. See `references/push-channels.md`.
5. **Add a news source.** Recommended: `ANSPIRE_API_KEYS` (search) or
   `SERPAPI_API_KEYS`. The dashboard's catalyst + sentiment fields depend
   on news; without it those fields degrade and the verdict weight drops.
6. **Run the test trigger manually.** GitHub: Actions → `每日股票分析` →
   `Run workflow`. Local: `python main.py --dry-run`. Verify one stock
   produces a complete six-field card before turning on the schedule.
7. **Confirm the schedule.** Default is every weekday 18:00 Beijing time;
   non-trading days (A/H/US holidays) skip automatically. Override with
   the cron config. See `references/deployment.md`.
8. **Audit the first dashboard read.** Open the report in the push channel,
   then in the web workbench (`python main.py --webui`), and check four
   things: (a) every stock has all six fields present or marked degraded;
   (b) the score is plausible against your prior read; (c) catalysts
   cite actual news; (d) the operation checklist is actionable. If any
   is off, return to step 1 and re-audit the source chain.

## Changelog

| Version | Date | Change |
|---|---|---|
| 1.0.0 | 2026-06-30 | Initial distillation from ZhuLinsen/daily_stock_analysis: five-market pipeline, 15 strategies, six-field Decision Dashboard, three deployment modes, six push channels, five operating principles, five references, eight-step quick start. |

— Daily Stock Analysis — 2026-06-30 — v1.0.0
