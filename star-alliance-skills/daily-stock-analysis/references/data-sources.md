# Data sources — per-market table, fallback chain, degradation markers

The pipeline's principle: **never let one source outage block the dashboard**.
Every market has a primary + secondary + fallback chain. Every failure is
logged; every degraded field is marked so the user knows where to trust the
read and where not to.

## Market data sources — full table

| Source | Coverage | Speed | Auth | Best for |
|---|---|---|---|---|
| **TickFlow** | CN A-share / HK | real-time tick + aggregated bars | free tier | recommended primary for CN, intraday |
| **AkShare** | CN A-share / partial HK | daily + minute | open | broad A-share fallback, includes fundamentals |
| **Tushare** | CN A-share + HK | daily + minute | token required | richest fundamentals for A / HK |
| **Pytdx** | CN A-share | real-time via TDxX protocol | none | lower latency than AkShare |
| **Baostock** | CN A-share | daily | free, no token | historical backfill, no fundamentals |
| **YFinance** | US / JP / KR / HK | daily + weekly | open, rate-limited | default for non-CN markets; `.T`, `.KS`, `.KQ`, `.KQ` parsed |
| **Longbridge** | HK / US | real-time + daily | token required | professional HK / US feeds, lower latency than YFinance |

## Per-market source ladder

The pipeline tries sources in order until one returns data. If all sources
fail for a market, the dashboard marks every market-dependent field as
`missing` and the user knows to rerun manually.

| Market | Primary | Secondary | Fallback | Quaternary |
|---|---|---|---|---|
| A-share | TickFlow | AkShare | Tushare | Pytdx → Baostock |
| HK | Longbridge | YFinance | AkShare | — |
| US | YFinance | Longbridge | — | — |
| JP | YFinance | — | — | — (YFinance only; derivative feeds degrade) |
| KR | YFinance | — | — | — (YFinance only; derivative feeds degrade) |

For CN markets, the priority order is a deliberate latency-vs-coverage
trade-off: TickFlow for real-time, AkShare for breadth, Tushare for
fundamentals, Pytdx/Baostock for low-rate / backfill.

## News / search sources

The Decision Dashboard's *catalyst factors* and *risk alerts* depend on the
news layer. Without at least one configured news source, those fields
degrade to `not_configured` and the verdict weight is reduced.

| Source | Strong at | Region | Provider tier |
|---|---|---|---|
| **Anspire** | CN web + AI ranking | CN-strong | recommended; one key unlocks models + search |
| **SerpAPI** | Baidu / Google scrape | global | recommended; broad recall |
| **Tavily** | general news | global / English | optional |
| **Bocha** | CN search with AI summaries | CN | optional; CN-optimised |
| **Brave** | privacy-first, English | global / English | optional |
| **MiniMax** | structured search results | mixed | optional |
| **SearXNG** | self-hosted no-quota fallback | deployer-hosted | optional; private deployment |

Recommended floor: one from {Anspire, SerpAPI} + one more for redundancy.
Without at least one search source, the Agent Q&A and Expectation
strategies cannot function.

## AI model providers

| Provider | API Key env | Notes |
|---|---|---|
| **Anspire** | `ANSPIRE_API_KEYS` | one key, also unlocks search; CN-friendly |
| **AIHubMix** | `AIHUBMIX_KEY` | OpenAI-compatible aggregator, no VPN needed |
| **Gemini** | `GEMINI_API_KEY` | Google's, good price/perf |
| **Anthropic** | `ANTHROPIC_API_KEY` | Claude family |
| **OpenAI** | `OPENAI_API_KEY` (+ `OPENAI_BASE_URL`, `OPENAI_MODEL`) | or DeepSeek / 通义千问 via base URL |
| **Ollama** | (local) | Docker / local mode only — not GitHub Actions |

Anspire and AIHubMix are recommended because one key covers both models and
search for Anspire specifically; for AIHubMix you pair with one of the
search providers above.

## Degradation markers

Every field on the Decision Dashboard carries one of four markers. The
marker is the **honesty contract** between the pipeline and the user — a
green field with `ok` is reliable; a yellow field with `partial` is a
read with caveats; a red field with `missing` is a known gap; and a grey
field with `not_supported` is a *market boundary*, not a bug.

| Marker | Meaning | What to do |
|---|---|---|
| `ok` | full data, full strategy execution | trust the read |
| `partial` | some sub-fields degraded; verdict still informed | cross-check with `market-recon` |
| `missing` | no source returned data for this field | rerun or check source credentials |
| `not_supported` | the market doesn't expose this field (e.g. JP `capital_flow`) | accept the gap; don't rerun |

The pipeline emits these markers in the dashboard footer as a one-line
audit: `audit: 2 ok, 1 partial, 0 missing, 1 not_supported`. Watch for the
audit line — if `missing` > 0, a source is down; if `not_supported` > 0
on a non-CN stock, you reached a market boundary (expected for JP / KR).

## JP / KR boundary table

JP (`.T`) and KR (`.KS` / `.KQ`) markets are yahoo-finance-only via
YFinance. Many of the high-touch CN-market feeds degrade to
`not_supported` here. This table is exhaustive:

| Field | A-share | HK | US | JP | KR |
|---|---|---|---|---|---|
| OHLCV daily | ✅ multi-source | ✅ Longbridge / YFinance | ✅ YFinance | ✅ YFinance | ✅ YFinance |
| Technicals (MA / MACD / RSI / KDJ / BOLL) | ✅ | ✅ | ✅ | ✅ | ✅ |
| Fundamentals (PE / PB / revenue / EPS) | ✅ | ✅ partial | ✅ | ⚠️ limited | ⚠️ limited |
| `capital_flow` (主力 / 散户 net) | ✅ | ✅ | ⚠️ partial | ❌ not_supported | ❌ not_supported |
| `dragon_tiger` (龙虎榜) | ✅ | ❌ | ❌ | ❌ | ❌ |
| `boards` (板块) | ✅ | ⚠️ partial | ⚠️ partial | ❌ | ❌ |
| Chip distribution (筹码) | ✅ | ⚠️ partial | ❌ | ❌ | ❌ |
| North-bound flow (北向) | ✅ | ⚠️ partial | n/a | n/a | n/a |
| Filings + announcements | ✅ | ✅ | ✅ | ⚠️ limited | ⚠️ limited |
| News / sentiment | ✅ | ✅ | ✅ | ✅ | ✅ |
| Backtesting | ✅ | ✅ | ✅ | ✅ | ✅ |
| Agent Q&A | ✅ | ✅ | ✅ | ✅ | ✅ |

Legend: ✅ full / ⚠️ partial or limited / ❌ not supported / n/a not applicable.

**Implication.** On JP / KR stocks, the strategies that need
`capital_flow` / `chip` / `dragon_tiger` degrade to
`not_supported`. The dashboard still produces a verdict — it is based on
the strategies that *can* run (Trend, MA, Technical Composite, Valuation,
Hotspot, Event-driven, Sentiment, Expectation, Agent Q&A). The user sees
a degraded-but-honest read, not a fabricated number.

## Fallback chain diagram

```
Ticker 600519  →  Try TickFlow          → OK       → done
                  Try AkShare           → fallback (already done above)
                  Try Tushare           → fallback
                  Try Pytdx             → fallback
                  Try Baostock          → fallback
                  All failed            → mark missing, log

Ticker AAPL     →  Try YFinance         → OK       → done
                  Try Longbridge        → n/a (YFinance succeeded)
                  All failed            → mark missing, log

Ticker 005930.KS
                →  Try YFinance         → OK       → done
                  derived feeds (capital_flow, chip)
                                       → not_supported (JP / KR boundary)

Ticker 7203.T   →  Try YFinance         → OK       → done
                  derived feeds (capital_flow, chip)
                                       → not_supported (JP / KR boundary)
```

The pipeline never silently replaces a source; if YFinance fails for AAPL
and Longbridge is not configured, the verdict carries `missing` on
price-derived fields, not a guessed number.
