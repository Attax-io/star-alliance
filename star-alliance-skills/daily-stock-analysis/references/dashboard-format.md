---
type: Document
timestamp: 2026-07-02T12:28:13Z
---

# Dashboard format — the six-field card contract

The Decision Dashboard is the pipeline's only output the user sees (besides
the full Markdown exported through the web workbench). Its shape is fixed.
This file is the **contract** — what every field is, what scale it lives on,
and what an empty or degraded field looks like.

## Top-level structure

A daily push has two parts:

1. **Summary header** — one line: date, total watchlist size, and the
   buy/hold/sell counts across the whole run. This is the line you read
   while waiting for the kettle.
2. **Per-stock card (six fields)** — emitted once per ticker, in the order
   declared by the watchlist.

```
🎯 2026-02-08 决策仪表盘
共分析3只股票 | 🟢买入:0 🟡观望:2 🔴卖出:1

📊 分析结果摘要
⚪ 中钨高新(000657): 观望 | 评分 65 | 看多
⚪ 永鼎股份(600105): 观望 | 评分 48 | 震荡
🟡 新莱应材(300260): 卖出 | 评分 35 | 看空

[then 6-field cards for each]

---
生成时间: 18:00
audit: 5 ok, 1 partial, 0 missing, 2 not_supported
```

The `audit:` footer is the honesty contract — it tells the user, at a
glance, how much of the run degraded and whether a rerun is warranted.

## Summary header — format

| Field | Type | Example | Notes |
|---|---|---|---|
| Date | ISO-8601 | `2026-02-08` | Beijing timezone by default |
| Total watchlist size | integer | `3` | includes all tickers, including degradations |
| Buy count | integer + 🟢 | `🟢买入:0` | score 61–100 |
| Hold count | integer + 🟡 | `🟡观望:2` | score 41–60 |
| Sell count | integer + 🔴 | `🔴卖出:1` | score 0–40 |

The summary list under "分析结果摘要" is one row per stock with the format:

```
⚪ {name} ({code}): {verdict} | 评分 {score} | {trend}
```

Emoji glyph here is the **neutral** `⚪` — the verdict colour lives in
the per-stock card, not the summary. The summary is for skimming; the
card is for reading.

## The six-field card

Every card has six fields in this order. Field 1 and 2 are always present;
fields 3–6 may degrade.

### Field 1 — Verdict + score

The verdict is one of three discrete labels:

| Verdict | Chinese label | Score range | Color |
|---|---|---|---|
| **Buy** | `买入` | 61–100 | 🟢 green |
| **Hold** | `观望` | 41–60 | 🟡 yellow |
| **Sell** | `卖出` | 0–40 | 🔴 red |

The score is an integer in `[0, 100]`. It is the *cumulative weight* of
all enabled strategies, with technical composite at 50% baseline and the
others at +/− 5–15 each. Score band → verdict mapping is fixed, not
overridable.

```
⚪ 中钨高新 (000657)
   观望 | 评分 65   ← actually wait — 65 is in Buy band
```

The user's example above would map to 🟢 on 65. The example shown in the
repo README uses `⚪` (neutral) in the *summary list* but `🟡` (yellow)
in the *card* for the same stock. The convention:

- **Summary list:** `⚪` always (it doesn't take colour).
- **Card:** `🟢 / 🟡 / 🔴` by verdict band.

The fix: the example in the SKILL.md reproduces the README *as written*,
which has a small inconsistency between summary and card. Trust the
**rules above**, not the example output — the rules are the contract;
the README is illustrative.

### Field 2 — Trend

| Label | Chinese | Meaning |
|---|---|---|
| Bullish | `看多` | technicals and flows agree up |
| Sideways | `震荡` | mixed signals, range trade |
| Bearish | `看空` | technicals and flows agree down |

The trend label is the authoritative single field for direction. If Trend
(Strategy 4) and MA (Strategy 1) disagree, the pipeline prefers Trend
because it considers the multi-timeframe agreement.

### Field 3 — Buy / sell levels

Concrete entry zone, target, stop-loss numbers when the strategy produces
them. Absent for strategies that are read-only (Sentiment, Hotspot,
Event-driven). Format:

```
📍 买入区间: ¥123.4 - ¥125.8
🎯 目标位:   ¥132.0 (前高)
🛑 止损位:   ¥119.5 (MA20)
```

For HK / US / JP / KR stocks the price unit adapts: HK → HKD, US → USD,
JP → JPY, KR → KRW. The unit appears in the dashboard footer.

### Field 4 — Risk alerts

Bullet list of named risk points. Empty list is a *valid value* — an
empty risk list is good news, not a missing field. Format:

```
🚨 风险警报:
  风险点1：2月5日主力资金大幅净卖出3.63亿元。
  风险点2：筹码集中度高达35.15%。
  风险点3：舆情中提及历史违规记录及重组相关风险。
```

Standard risk tags the pipeline recognises:

- 主力资金净流出 (institutional net outflow)
- 获利盘集中 (concentrated profit-taking)
- 筹码分散 (chip dispersion)
- 估值历史高位 (valuation at historical high)
- 舆情偏极端 (extreme sentiment)
- 监管事件 (regulatory event)
- 业绩不及预期 (earnings miss)
- 主题退潮 (theme exhaustion)
- 系统性风险 (systemic risk flag — when applicable)

A risk tag without a number means the tag fired qualitatively (news
language, social sentiment); with a number it has a quantified threshold.

### Field 5 — Catalyst factors

Bullet list of positive drivers. Mirror of Field 4. Format:

```
✨ 利好催化:
  利好1：公司被市场定位为AI服务器HDI核心供应商。
  利好2：2025年前三季度扣非净利润同比+407.52%。
  利好3：行业景气度上行，板块近期轮动至该方向。
```

Standard catalyst tags:

- 业绩兑现 (earnings delivered)
- 行业景气 (sector tailwind)
- 政策利好 (policy tailwind)
- 主题催化 (theme catalyst)
- 估值修复 (valuation mean-reversion)
- 资金流入 (inflow)
- 事件驱动 (event-driven: contract, M&A, regulatory win)
- 预期上调 (estimate upgrade)
- 筹码集中 (chip concentration thesis)

### Field 6 — Operation checklist

What the user should do this session. The checklist is the *call to
action* — not a rephrasing of the verdict. Each item is a discrete
action verb + scope + threshold.

```
📋 操作检查清单:
  ✅ 已持仓者：继续持有，跌破 ¥119.5 止损。
  🔍 未持仓者：等待回踩 MA20 (¥125.0) 不破再考虑。
  📅 关注：本周五 22:00 业绩电话会。
```

Standard actions:

- 已持仓者 → 继续持有 / 减仓一半 / 全部清仓 / 逢高减仓
- 未持仓者 → 暂不介入 / 等待回踩 X / 突破 X 再跟进 / 立即建仓 ≤ X%
- 关注事件 → 业绩披露日 / 电话会 / 股东大会 / 数据发布
- 风控 → 止损位 / 止盈位 / 时间止损
- 复盘 → 与昨日结论交叉对比

Each action line carries the *condition* (price level, date, threshold)
that flips the action. The goal: the user reads the dashboard and knows
*what to do this session*, not just what the model thinks.

## Score scale — full details

The score is a single integer in `[0, 100]`. Composition:

- **Base: 50** — neutral starting point.
- **Technical Composite (Strategy 11): up to ±20** — weighted voting of
  MA + MACD + RSI + KDJ + BOLL.
- **Trend (Strategy 4): up to ±10** — multi-timeframe agreement.
- **Hotspot (Strategy 5): up to ±5** — theme intensity.
- **Capital Flow (Strategy 9): up to ±10** — net institutional flow
  direction (CN/HK only; degrades on JP/KR).
- **Chip Distribution (Strategy 10): up to ±10** — concentration
  thesis (CN only; degrades elsewhere).
- **Event-driven (Strategy 6): up to ±10** — discrete event impact.
- **Sentiment (Strategy 8): up to ±5** — contrarian / confirmatory.
- **Growth (Strategy 7): up to ±5** — long-horizon compounding.
- **Valuation (Strategy 12): up to ±5** — cheap vs peers.
- **Expectation (Strategy 14): up to ±5** — estimate revisions.
- **Wyckoff (Strategy 2): up to ±5** — phase context.
- **Elliott Wave (Strategy 3): up to ±5** — multi-cycle structure.
- **Bounds:** score is clamped to `[0, 100]` before verdict mapping.

**Degraded strategies don't subtract.** A `not_supported` strategy
contributes 0, not negative. A `partial` strategy contributes half its
weight. A `missing` strategy contributes 0 and the field is flagged in
the audit footer.

## Color coding — where the emoji live

The same score-band rules apply across the entire push output and the web
workbench:

| Decision | Score | Emoji |
|---|---|---|
| Buy | 61–100 | 🟢 |
| Hold | 41–60 | 🟡 |
| Sell | 0–40 | 🔴 |

Use the band's emoji in the *card*. The summary list always uses `⚪`
because the colour belongs to the card, not the summary.

## Markdown export (web workbench)

The web workbench `/report/{date}` endpoint serves both a rendered HTML view
and a Markdown export. The Markdown export uses the same six-field card
structure with a `## {ticker}` heading and `### {field}` sub-headings,
preserving the bullets. JSON export adds the raw score-per-strategy
breakdown under a `score_breakdown` key — useful for debugging "why did
the dashboard say Buy when I expected Hold".
