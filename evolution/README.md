---
type: reference
---

# The Evolution Engine

The Star Alliance's self-improving spine. One closed loop that every self-modifying
path plugs into — turns, the nightly reflector, skillsmith, Strategic Audit —
instead of the six disconnected fragments the 2026-06-28 audit found.

## Why it exists

The audit verdict: *every autonomous self-modifying path could commit its own
changes with **no independent review** and **no fitness feedback**.* The Critic
existed but nothing called it. Metrics were collected but never read back.
Learnings accumulated but were never promoted. A regression shipped through
Strategic Audit and sat in the repo across several commits — caught only when a
human happened to run the critic by hand.

A system that can mutate itself but cannot catch its own regressions is not
self-improving. It is self-mutating. The Engine adds the two missing organs:
**VERIFY** (independent review, in the path) and **REMEMBER** (a fitness score
that decides whether a change stuck).

## The loop — five organs, one invariant

```
SENSE ──▶ DIAGNOSE ──▶ CHANGE ──▶ VERIFY ──▶ REMEMBER ──┐
ledger    engine       engine     verify-    scoreboard  │
          (diagnose)   (route)    gate / verdict          │
   ▲                                                       │
   └──────────────── score decides what sticks ───────────┘
```

> **INVARIANT:** nothing enters the repo without (a) an independent critic verdict
> and (b) a ledger event. Autonomous or human. No exceptions.

| Organ | File | Role |
|---|---|---|
| **SENSE** | `ledger.py` → `ledger.jsonl` | one append-only, git-tracked event stream (`change`, `verdict`, `learning`, `metric`, `proposal`, `revert`, `block`) |
| **SENSE (stale)** | `stale_scan.py` + `stale_registry.json` | scans the repo for mentions of removed/renamed concepts; reports or auto-removes (Tier-A) |
| **VERIFY** | `verdict.py` | *runs* the Critic (`critique.py`, kimi-k2.7 — a different model family) and returns a parsed `pass`/`concerns`/`block`/`error` |
| **DIAGNOSE + CHANGE** | `engine.py` | reads the scoreboard + stale scanner → tier-tagged proposals → routes them (Tier-A reversible vs Tier-B human-gated) |
| **REMEMBER** | `scoreboard.py` | turns the ledger into fitness numbers: regression escapes, block rate, concern density, repeated learnings, cost trend, stale mentions |
| **The gate** | `.claude/hooks/verify-gate.py` | the VERIFY organ wired as a Stop hook — armed by default, auto-runs the critic, auto-clears on pass, blocks on block |

## Reversibility tiers — the safety line

- **Tier A** — `skills`, `memory`, `docs`. Reversible. *May* be auto-applied (only
  with `--apply`, only after an independent pass).
- **Tier B** — `gates`, `doctrine`, `arsenal`, `workflows`. Load-bearing.
  **Never** auto-applied. The engine files a proposal and waits for a human "go".
  This is the line that stops an unsupervised nightly run from rewriting its own
  safety rails.

## Risk posture — fail OPEN on infra, fail CLOSED on judgment

- **Critic unreachable** (no network): the MCP verify gate *degrades to manual* — it
  never hard-traps a human session on infrastructure. Unsupervised routines get
  their fail-closed guarantee in their own flow (`verdict.py --fail-closed` before
  commit), because an unattended run must not commit unreviewed.
- **Critic says BLOCK**: stop. That is the gate doing its job.

## Controls

```
touch evolution/DISARMED      # kill switch — stands the whole engine + gate down
SA_SKIP_VERIFY=1              # one-turn human bypass of the verify gate
SA_AUTO_CRITIC=0             # verify gate falls back to manual review (no auto-critic)
python3 evolution/engine.py            # shadow: propose only, commit nothing (default)
python3 evolution/engine.py --apply    # leave shadow (still Tier-B-gated, still honors DISARMED)
python3 evolution/scoreboard.py        # read the fitness scoreboard (includes stale-mention scan)
python3 evolution/stale_scan.py         # scan repo for stale mentions (shadow — report only)
python3 evolution/stale_scan.py --apply # remove Tier-A stale mentions (Tier-B still human-gated)
python3 evolution/ledger.py tail -n 20 # inspect the event stream
```

## Evaluated, not changed — small-diff auto-critic skip (2026-06-28)

The MCP verify gate runs a synchronous ~150s cold critic on every
source-touching turn. A proposed optimization was to skip the auto-critic for
small interactive diffs (< N changed lines) and defer them to routine-time
grounded review, to keep interactive UX snappy.

**Decision: not adopted.** A line-count threshold is a poor proxy for risk — the
regression that motivated this whole engine was a *small* diff that shipped
unreviewed through Strategic Audit. Auto-skipping small diffs would re-open exactly
that hole, and "defer to routine-time review" reintroduces the un-closed-loop the
audit found (review that is owed but never happens). The latency is already opt-out:
`SA_AUTO_CRITIC=0` falls back to manual review for fast interactive work, and
`SA_SKIP_VERIFY=1` bypasses one turn. Coverage stays diff-size-agnostic up to the
60KB cold-critique cap (above which it escalates to grounded review, never skips).
Revisit only if a cheaper/faster local critic makes per-turn latency a non-issue.

## Migration — the strangler (do NOT big-bang)

Ripping out the old gate before the new loop works would remove the only thing
that catches regressions. So the rebuild is a strangler:

- **Phase 0 — Shadow + ledger.** ✅ `ledger`/`verdict`/`scoreboard`/`engine` built;
  engine runs read-only, commits nothing.
- **Phase 1 — Mandatory critic-gate.** ✅ the MCP verify gate — armed by default,
  auto-runs the critic, auto-clears on pass, ledgers every verdict.
- **Phase 2 — Unify the ledger.** ⏳ route `turn-cost.py` + `learn.py` into the one
  stream; old stores become compat views, then retire.
- **Phase 3 — Reflector live.** ⏳ nightly cron runs `engine.py` (shadow first, then
  `--apply` for Tier-A only once it has proven itself on real cycles).
- **Phase 4 — Retire the dead fragments.** ⏳ only after the new loop is proven;
  each removal is itself critic-reviewed and git-reversible.

See `docs/` / the guild log for the originating audit.
