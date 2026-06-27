---
name: harness-efficiency
description: "The Strategist's craft for proving the Star Alliance harness actually saves tokens and time, then tuning the levers that do it. Joins the two Phase-0 measurement streams via tools/efficiency_report.py — usage-log.jsonl (every offloaded model call, with phase + wall_ms) and data/turn-cost.jsonl (per-turn Opus tokens + which routing tier fired) — into a net-saved figure and a LITE-vs-FULL per-turn breakdown, watches for the one safety regression that matters (a high-stakes turn that took the cheap LITE gate path), and recommends edits to the stakes/size policy in data/harness.json. Use to answer how much the harness is saving, whether the proportional routing gate works, or before and after a hook change to the gate. Triggers: 'efficiency report', 'harness efficiency', 'how much are we saving', 'is the gate working', 'tier split', 'check the offload', 'net tokens saved', 'tune the stakes list'. Differentiate from performance (app hot-path profiling) and weapon-utility (which model a member draws)."
metadata:
  version: 1.1.0
type: Skill

---

# harness-efficiency

The Strategist's instrument for the one thing the harness was blind to: **is it actually
saving anything?** The guild is richly instrumented for theater (klaxons, the dashboard, per-skill
art) but, before Phase 0, could not show net tokens or time saved. This skill reads the measurement
streams Phase 0 laid down and turns them into a number you act on — and tunes the levers behind it.

## What it reads

Two append-only streams, joined by `tools/efficiency_report.py`:

- **`star-alliance-arsenal/usage-log.jsonl`** — one record per offloaded model call (the cheap bench
  doing doer-grade work), now carrying `phase` (`"offload"`) and `wall_ms` (the real round-trip).
- **`data/turn-cost.jsonl`** — one record per assistant turn, written by the `turn-cost.py` Stop hook:
  the turn's Opus `in`/`out` tokens (+ cache) and the routing **tier** (`lite` / `full` / `unknown`),
  detected from the `SA-GATE:<TIER>` marker the routing gate injects.

## How to run it

```sh
python3 tools/efficiency_report.py                 # all-time, human table
python3 tools/efficiency_report.py --days 7        # trailing window
python3 tools/efficiency_report.py --json          # raw, for further analysis
```

It prints three blocks: **OFFLOAD** (calls, out-tokens, median `wall_ms` per bench model — proves
where offload actually goes; ~99% is `minimax-m3`), **PREMIUM** (per-turn Opus tokens split by tier,
with median in/turn — proves the LITE path is cheaper), and **NET** (a conservative proxy: bench
out-tokens displaced − premium out-tokens, with the assumption printed inline so the number stays
honest).

## What to watch — the read each run

1. **Net trend.** Is displaced output growing relative to premium spend? Falling net = the harness is
   doing more bookkeeping than offloading; investigate which turns went FULL that should be LITE.
2. **Tier split.** `median in/turn` for **lite** should be materially below **full** (the gate's whole
   point — LITE injects ~200 tokens, FULL ~1060). If they converge, the classifier is sending too much
   to FULL — loosen the size signals, or the prompts genuinely are high-stakes.
3. **The safety regression — the only hard failure.** A turn tagged **lite** that actually touched
   anything high-stakes (a migration, a `git push --force`, a rename, a deploy) is the one thing the
   proportional gate must NEVER do. Cross-read `turn-cost.jsonl` tier against what the turn did; if a
   high-stakes turn slipped to LITE, the stakes list in `data/harness.json` has a gap — close it FIRST,
   then re-verify with the regression matrix below.

## Tuning the levers

The gate is governed by **policy, not code** — the `policy` block in `data/harness.json`:
`stakes_keywords`, `size_small_signals`, `size_large_signals`. Tune there, never in the shell.

- A high-stakes op reached LITE → **add its keyword to `stakes_keywords`** (stakes always beats size).
- A clearly-small turn went FULL and it's noise → add a `size_small_signals` term, but only if it can
  never co-occur with a stakes op.
- After ANY policy edit, re-run the regression matrix and confirm: every high-stakes/unknown case
  still resolves FULL, only clearly-small-and-low-stakes resolves LITE.

```sh
# regression check — drive a prompt through the gate, read the tier marker
printf '%s' '{"prompt":"git push --force"}' | CLAUDE_PROJECT_DIR="$PWD" \
  sh .claude/hooks/guild-routing-gate.sh 2>/dev/null | grep -oE 'SA-GATE:(LITE|FULL)'
```

Hard rule, encoded in one line: **unknown or high-stakes ⇒ FULL; only clearly-small-and-clearly-low-stakes ⇒ LITE.** A broken classifier must fail to FULL — never weaken the gate. The `SA_GATE=full`
env override restores uniform behavior instantly if a tuning change goes wrong.

## When the data is thin

`turn-cost.jsonl` only starts filling once the `turn-cost.py` Stop hook is wired and the session has
restarted (hooks load at session start). Until a week or so of turns accrue, the PREMIUM block reads
"(no turn-cost data yet)" and NET is offload-only — say so plainly; do not present a half-baseline as
proof. The baseline is complete when the LITE-vs-FULL split has enough turns on both sides to compare.

## Where it sits

```
data/harness.json policy   →  the stakes/size lever (what the gate reads)
guild-routing-gate.sh      →  injects LITE/FULL + the SA-GATE marker
turn-cost.py (Stop)        →  records per-turn premium + tier
arsenal usage-log.jsonl    →  records every offload call + wall_ms
   efficiency_report.py    →  joins them → net-saved + tier split   ← this skill drives it
```

Pairs with [[weapon-utility]] (offload is where the bench tokens come from) and the
[[scheduled-watch]] skill (run this weekly and alert on a regression rather than checking by hand).

## Versioning
Own skill. Bump `metadata.version` on any change (PATCH: wording/refs · MINOR: new check or lever ·
MAJOR: a change to what counts as a regression). Regenerate `VERSIONS.md` via
`python3 star-alliance-skills/skillsmith/scripts/skill_registry.py write`, then `python3 build.py`.

## New metrics (1.1.0)

`turn-cost.jsonl` now carries two additional fields populated by the B1/H2 hook patches:

- **`wall_ms`** — real wall-clock milliseconds from UserPromptSubmit to Stop. Now available in every record. Use to compute p50/p95 user-perceived latency alongside token cost.
- **`tier`** — now reliably `lite` or `full` (was `unknown` on 90% of turns due to a sidecar bug). The B1 fix (guild-routing-gate.sh writes `.claude/state/last-tier`; turn-cost.py reads + deletes it) resolves this.

Add to every `efficiency_report.py` run:

```sh
# Latency summary (requires wall_ms field, present from 2026-06-27 onward)
python3 tools/efficiency_report.py --latency      # p50/p95/p99 wall_ms by tier
python3 tools/efficiency_report.py --cache        # cache hit-rate (cache_read / (cache_read + cache_create))
```

### Updated read each run

4. **Tier coverage.** If `tier=unknown` rows persist after the B1 patch, the `.claude/state/` directory may be missing or the sidecar is being deleted before `turn-cost.py` reads it. Check hook order in `settings.json` (turn-cost must run after guild-routing-gate, which it does via Stop vs UserPromptSubmit ordering — this should not happen in normal operation).
5. **Latency spike detection.** p95 `wall_ms` > 120 000 (2 min) on FULL turns signals the context window is bloated. The PreCompact snapshot (new hook) should help rehydrate faster after compression.
6. **Cache hit-rate.** `cache_read / (cache_read + cache_create)` below 0.6 means the cache is thrashing — prompts are changing too much between turns or the 5-min TTL is expiring. Investigate turn cadence.

## Changelog
- **1.1.0** — B1 tier sidecar fix: `tier` now reliable. H2 wall_ms: real latency now in every record. New `--latency` and `--cache` flags documented. Updated "read each run" section with 3 new checks.
- **1.0.0** — Initial release. The Strategist's craft for proving and tuning harness efficiency: read
  `usage-log.jsonl` + `turn-cost.jsonl` via `efficiency_report.py`, watch the net trend + LITE/FULL
  tier split, hunt the one hard failure (a high-stakes turn that took LITE), and tune the
  `data/harness.json` policy with a regression re-check after every edit. Mined from the
  harness-efficiency build (Phases 0–1).
