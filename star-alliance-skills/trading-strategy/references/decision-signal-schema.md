---
name: decision-signal-schema
type: Reference
---
# DecisionSignal — the output contract and the post-hoc grading loop

The strategy spec is prose; the DecisionSignal is its machine-checkable contract. A
DecisionSignal records the advice, the evidence summary, the risk, the watch
conditions, the lifecycle, and the source — it never places an order or rebalances a
book. It is the structured index that sits above the written report, not a replacement
for it, and not a trade. The Merchant produces a paper-executable spec; the
DecisionSignal makes that spec queryable and, later, gradable. Nothing here executes.

Distilled and translated to English from `daily_stock_analysis/docs/decision-signals.md`
(the DSA P7 DecisionSignal spec).

## 1. The output contract (fixed schema)

Every strategy spec emits at least one DecisionSignal. The contract is fixed: an
emitter MUST fill the required fields, MAY add the optional ones, and MUST keep enum
values to the wire values below (the human-readable label is a presentation concern,
never the stored value).

### Required fields

| Field | Type | Meaning |
| --- | --- | --- |
| `action` | enum | The advised move. One of `buy`, `add`, `hold`, `reduce`, `sell`, `watch`, `avoid`, `alert`. |
| `horizon` | enum | The intended holding window. One of `intraday`, `1d`, `3d`, `5d`, `10d`, `swing`, `long`. |
| `entry` | object | `{ low, high }` — the entry band (use equal low/high for a single price). |
| `stop` | number | Stop-loss price. The risk floor of the plan. |
| `target` | number | Primary target price. The reward ceiling of the plan. |
| `invalidation` | string | The falsifier: the one condition that kills the thesis ("if X, this signal is dead"). |
| `watch_conditions` | string[] | Concrete conditions to monitor between entry and exit (level breaks, prints, catalysts). |
| `confidence` | enum | `low`, `med`, or `high` — graded on evidence strength, regime match, and out-of-sample support, never on conviction. |
| `evidence` | object[] | The proof trail: `{ kind, summary, ref? }` items the signal rests on. |

### Optional / lifecycle fields

| Field | Type | Meaning |
| --- | --- | --- |
| `stock_code` / `stock_name` | string | Instrument identity. |
| `market` | enum | `cn`, `hk`, `us`, `jp`, `kr`, `tw`. |
| `source_type` | enum | `analysis`, `agent`, `alert`, `market_review`, `manual`. |
| `source_report_id` / `trace_id` | string | Provenance: the report or trace this signal was extracted from. |
| `score` | number | Optional numeric strength, if a scoring engine produced one. |
| `market_phase` | enum | `premarket`, `intraday`, `lunch_break`, `closing_auction`, `postmarket`, `non_trading`, `unknown`. |
| `plan_quality` | enum | `complete`, `partial`, `minimal`, `unknown` — completeness of entry/stop/target/invalidation. |
| `reason` / `risk_summary` / `catalyst_summary` | string | Short prose justification, risk note, and catalyst note. |
| `status` | enum | `active`, `expired`, `invalidated`, `closed`, `archived`. |
| `expires_at` | datetime | Lifecycle bound; defaults follow the horizon. |

### YAML example

```yaml
action: buy
horizon: 5d
entry: { low: 101.20, high: 102.00 }
stop: 98.50
target: 108.00
invalidation: "daily close below 98.50, or the breakout volume fails to confirm within 2 sessions"
watch_conditions:
  - "reclaim and hold of the 20-day moving average"
  - "sector breadth stays positive"
  - "no earnings or guidance print inside the window"
confidence: med
evidence:
  - { kind: structure, summary: "higher-low base with a clean breakout retest", ref: "market-recon 2026-06-28" }
  - { kind: backtest, summary: "out-of-sample hit-rate 0.54, payoff 1.9, expectancy +0.41R" }
plan_quality: complete
source_type: analysis
status: active
```

### Contract rules

- Keep enum values to the wire values above; map to a display label only at the surface.
- `plan_quality` reflects how much of `entry`/`stop`/`target`/`invalidation` is filled —
  `complete` only when all four are present and mechanical.
- A new active signal that contradicts a prior active one on the same instrument should
  mark the older one `invalidated`, not silently overwrite it.
- Emitting, extracting, or grading a signal must never block the underlying analysis or
  report — a write failure degrades, it does not abort. And it never executes a trade.

## 2. Post-hoc outcome grading (`decision_signal_outcomes`)

The grading loop closes the circle that the backtest opens: a backtest grades the edge
on history; outcome grading grades each *live* signal against the bars that came after
it. This is still offline — the skill only frames and scores the loop, it never trades.

Each emitted signal is scored against the forward bars implied by its `horizon`,
producing a `decision_signal_outcomes` record keyed idempotently by
`(signal_id, horizon, engine_version)`.

| Outcome field | Meaning |
| --- | --- |
| `signal_id` | The signal being graded. |
| `horizon` | The horizon scored (a multi-horizon signal yields one row per gradable horizon). |
| `engine_version` | The grader version, e.g. `decision-signal-v1` — freezes the scoring rules. |
| `eval_status` | `graded` when scoring succeeded, `unable` when it could not. |
| `unable_reason` | Why grading was skipped (see gradability rules). |
| `result` | `hit` (target reached before stop), `miss` (stop reached before target), `flat` (neither inside the window). |
| `mfe` / `mae` | Max favorable / max adverse excursion across the forward bars (in price or R). |
| `realized_r` | Outcome in R-multiples relative to the entry-to-stop distance. |
| `bars_to_resolution` | How many forward bars until hit/miss/window-end. |

Freeze the statistical dimensions at grading time — `action`, `market`, `market_phase`,
`source_type`, `source_agent`, `plan_quality`, `data_quality_level`, `holding_state` —
so historical stats never depend on a later live join.

### Gradability rules

- Only **daily-verifiable directional horizons** are gradable here: `1d`, `3d`, `5d`,
  `10d`.
- `intraday`, `swing`, and `long` horizons, **non-directional actions** (`watch`,
  `alert`, `hold` with no entry/stop/target), **missing prices**, and **insufficient
  forward bars** all yield `eval_status=unable` with an explicit `unable_reason` rather
  than a fabricated score.
- Grading is idempotent on its key: re-running produces the same row, never duplicates.

### What the loop buys you

Aggregating graded outcomes by the frozen dimensions turns a pile of past signals into
calibration evidence: realized hit-rate and expectancy per `action`, per `horizon`, per
`plan_quality`, per regime. That feedback is what lets the next spec's `confidence`
grade be earned rather than asserted — the backtest→live-grading loop closed. The grade
informs the next paper spec; it still never places a trade.
