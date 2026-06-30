---
type: Document
title: Harness Efficiency — Deeper Analysis & Implementation Plan
description: Root-cause reframe of the efficiency audit plus a sequenced, file-level implementation plan with proof-metrics, risks, and rollbacks.
timestamp: 2026-06-27T14:30:00Z
---

# Harness Efficiency — Deeper Analysis & Implementation Plan

Companion to [`HARNESS-EFFICIENCY-AUDIT.md`](HARNESS-EFFICIENCY-AUDIT.md). The audit asked *does it work*. This asks *why is it shaped this way, and exactly what to change*.

---

## 1. Deeper diagnosis — one root cause, four symptoms

The audit listed costs (per-turn injection, mandatory banners, approval halts, self-upkeep) as separate problems. On reflection they are **one** problem wearing four masks:

> **The harness has no model of a task's *size* or *stakes*, so it applies a single worst-case, campaign-grade policy to every turn.**

A correction first, in fairness to the code: `workflow-gate.py` already exempts every read-only tool (`Read/Bash/Grep/Glob/WebFetch/…`) — it only bites on `Edit/Write/Task/MultiEdit`, and it fails open on error with a first-tool "race grace." The enforcement layer is more careful than the audit implied. The waste is therefore **not** "everything is blocked." It is narrower and more precise:

- **~1,331 tokens of doctrine injected on *every* `UserPromptSubmit`** (measured), regardless of whether the turn is a typo fix or a 12-wave campaign. This is the single largest fixed cost and it is uniform.
- **A workflow banner required for every *work-producing* tool**, with no proportionality — the same procedure for a one-character edit and an architecture build.
- **An approval halt keyed on *action type* (write/build/git), not on *reversibility*** — so it fires identically on `echo > scratch.md` and `git push --force`.
- **Self-upkeep that scales with edit count** — autocommit-per-edit, member-table-sync-per-edit, dashboard regen — so the harness's own cost grows the more work it does.

### The second, subtler theme: instrumented for ceremony, not outcome

The harness can show you a klaxon (`⚡`, `🗺`, `⚔`), a 423 KB dashboard, and per-skill art. It **cannot** show you net tokens or time saved. It is richly instrumented for *theater* and blind to *truth*. The offload ledger is the one outcome metric in the system, and even it measures gross displacement, not net. **A harness whose stated purpose is efficiency should measure efficiency first and decorate second.** Today that priority is inverted.

### The corollary: honesty is itself an efficiency lever

99% of 549 offload calls went to one weapon; six bench weapons are dead. Maintaining the *fiction* of an 8-weapon arsenal has real recurring cost — member loadouts, dashboard tiles, routing rules, and the `weapon-gate.py` validity set all must stay consistent with weapons nobody draws. Pruning fiction shrinks the surface that must stay true.

### The refined principle (supersedes the audit's "task-size fast lane")

Govern on **two independent axes**, not one:

| Axis | Question | Controls |
|---|---|---|
| **Stakes** (reversibility / blast radius) | "How hard is this to undo?" | the approval halt + autocommit |
| **Size / novelty** | "Is this routine and small, or large/ambiguous?" | doctrine injection depth + workflow-banner requirement |

A one-line edit to a migration file is *small* but *high-stakes* — it must still halt. A 200-line edit to a scratch doc is *large* but *low-stakes* — it should not. The audit's single "size" lane would have gotten this wrong. **Stakes always wins over size.**

---

## 2. Implementation plan

Five phases. **Phase 0 goes first on purpose** — it makes every later gain provable instead of modeled (the audit's own #3). If you want relief before proof, 0 and 1 can swap, but then the first measured number is post-fix and you lose the baseline.

Each phase: objective · files · change · effort · risk · rollback · **proof-metric** (how we know it worked).

---

### Phase 0 — Close the measurement loop *(prerequisite; ~0.5 day)*

**Objective.** Make "tokens/time saved" a measured number, not my estimate.

**Files.**
- `star-alliance-arsenal/arsenal_usage.py` — extend the record with `phase` (`"offload"`) and `wall_ms` per call.
- `star-alliance-arsenal/minimax.py` / `ollama_cloud.py` — time the HTTP call, pass `wall_ms`.
- New `.claude/hooks/turn-cost.py` (Stop hook) — parse `transcript_path` usage blocks to record **per-turn Opus input/output tokens** + whether the turn was fast-lane or full-ceremony, to `data/turn-cost.jsonl`.
- New `tools/efficiency_report.py` — join `usage-log.jsonl` + `turn-cost.jsonl` → a "net saved" summary (offload cost avoided − injection tax − orchestration tokens).

**Change.** Two new fields + one Stop hook + one reporter. No behavior change to the work loop.

**Effort** S. **Risk** very low (additive, best-effort, fails open like the others). **Rollback** remove the hook line from `settings.json`; the extra JSONL fields are ignored by old readers.

**Proof-metric.** `efficiency_report.py` prints a real net-saved figure and a per-turn-type breakdown after one week of normal use. *This is the baseline every later phase is measured against.*

---

### Phase 1 — Proportional gate: the stakes/size classifier *(the big win; ~1–1.5 days)*

**Objective.** Stop paying campaign-grade overhead on small, low-stakes turns — without ever letting a high-stakes op skip approval.

**Files.**
- `.claude/hooks/guild-routing-gate.sh` — split the static heredoc into **two tiers**. A small Python classifier (it already runs inline Python for slash-skill detection) reads the prompt and emits either:
  - **LITE** (~150 tokens): one-line router reminder + "this looks small; if it's a quick-fix, declare `Quick Fix` and proceed; if it touches migrations/git/prod/mass-edits, treat as high-stakes and restate-and-halt."
  - **FULL** (current ~1,331 tokens): only when the prompt matches campaign/build/multi-member/ambiguous signals.
- `.claude/hooks/workflow-gate.py` — accept the existing lightweight `Quick Fix` banner (already in `workflows.json`) as a valid one-line declaration; keep the hard block for everything that claims a heavier workflow.
- `data/harness.json` — add a `policy` block (the stakes keywords + size signals) so the classifier is config, not buried in shell.

**Change.** The injection becomes conditional. Stakes keywords (`migration`, `push`, `force`, `prod`, `DROP`, `rm -rf`, `rename`, mass-edit globs) force the FULL gate + halt **regardless of size**. Everything else gets LITE.

**Effort** M. **Risk** **medium — this is the one phase that can create a safety hole.** Mitigated by: stakes-list is allow-by-exception (unknown → treat as FULL), and the Phase-0 baseline catches regressions. **Rollback** one env flag `SA_GATE=full` restores today's uniform behavior instantly.

**Proof-metric.** Median per-turn injection tokens drop ~80% on small turns (1,331 → ~150–250); `turn-cost.jsonl` shows no high-stakes turn took the LITE path (the regression test below enforces this).

---

### Phase 2 — Batch & persist the offload path *(time win; ~1 day)*

**Objective.** Cut the wall-clock overhead of 500+ sequential subprocess + HTTP calls per campaign.

**Files.**
- `star-alliance-arsenal/minimax.py` — add a `--batch <file.jsonl>` mode: one process, one keep-alive HTTP connection, N prompts → N results. Keep single-shot mode unchanged (backward compatible).
- `guild/delegate.py` — add `delegate_many(prompts)` that uses batch mode when >1 prompt.
- `guild/run.py` — when a workflow step fans out, route through `delegate_many`.

**Change.** Additive batch entry point; existing call sites keep working.

**Effort** M. **Risk** low (old path untouched; batch is opt-in). **Rollback** stop calling `delegate_many`.

**Proof-metric.** `wall_ms` (from Phase 0) per offloaded token drops materially on multi-call steps; a 50-prompt campaign step that took N sequential round-trips now takes ~1.

---

### Phase 3 — Cap the self-upkeep tax *(steady-state win; ~0.5 day)*

**Objective.** Stop the harness's cost from scaling with its own edit count.

**Files.**
- `.claude/hooks/autocommit.sh` — debounce: coalesce rapid edits into one commit per logical change (or per turn) instead of per file write; kills the `auto: Edit app.css` storm.
- `.claude/settings.json` — move `member-table-sync.py` and any dashboard regen off the per-edit `PostToolUse` path; run them on a `Stop` hook or release only, not on every write.
- `build.py` / `guild-data.js` — regenerate on demand / at release, not implicitly in the work loop.

**Change.** Decouple cosmetic + bookkeeping regen from the critical path.

**Effort** S. **Risk** low (dashboard can lag the repo by a turn — acceptable; it's a view). **Rollback** restore the `PostToolUse` lines.

**Proof-metric.** Commits-per-session and PostToolUse hook invocations per edit both drop; no `auto: Edit` runs longer than a handful.

---

### Phase 4 — Honest arsenal *(surface reduction; ~0.5 day)*

**Objective.** Stop maintaining six weapons nobody draws.

**Files.**
- `data/members-meta.json` + `star-alliance-members/*.md` — move the 6 idle bench weapons from active loadouts to a `reserve` tier (kept, documented, not advertised as live).
- `star-alliance-arsenal/README.md` + `summon.py` routing table — reconcile the **tag drift** flagged earlier (`kimi-k2.7-code:cloud` vs `kimi-k2:cloud`, `deepseek-v4-pro:cloud` vs `deepseek-v3.1:cloud`, etc.): verify which tags actually pull, fix or mark unreachable.
- `weapon-gate.py` validity set — narrows automatically once loadouts shrink.

**Change.** Reclassify, don't delete. Reactivation is a one-line move back to active once a weapon is actually pulled and used.

**Effort** S. **Risk** very low. **Rollback** move tiers back.

**Proof-metric.** `weapon-gate.py`'s known-weapon set matches weapons with ≥1 ledger call in the trailing 30 days; README routing table matches `summon.py` exactly (a `conformance.py` check can assert this).

---

## 3. Regression / safety matrix (gates Phase 1 ship)

Phase 1 must pass all of these before it replaces the uniform gate:

| Scenario | Expected | Why it matters |
|---|---|---|
| "fix the typo in line 12" | LITE inject, `Quick Fix` banner, no halt | the target win |
| "rename the `wages` column" | FULL inject + restate-and-halt | small but high-stakes — must NOT slip to LITE |
| "git push --force" / "drop table" | FULL + halt | reversibility floor |
| "plan the Q3 campaign" | FULL inject, workflow required | large/ambiguous stays heavy |
| empty/garbled prompt | FULL (fail-safe default) | unknown → treat as heavy |
| classifier crashes | fail open to FULL | a broken classifier must never *weaken* the gate |

Rule encoded in one line: **unknown or high-stakes ⇒ FULL+halt; only clearly-small-and-clearly-low-stakes ⇒ LITE.**

---

## 4. Sequencing & expected cumulative effect

| Phase | Effort | Primary gain | Provable after |
|---|---|---|---|
| 0 Measurement | S | none (enables proof) | itself |
| 1 Proportional gate | M | ~25–40% premium tokens (blended) | Phase 0 |
| 2 Batch offload | M | ~10–25% wall-clock on campaigns | Phase 0 |
| 3 Upkeep cap | S | steady-state token + git-noise | Phase 0 |
| 4 Honest arsenal | S | maintenance surface, correctness | conformance check |

Total ~3.5–4 days. The earlier modeled estimates (≈25–40% tokens, ≈15–30% wall-clock, blended) become **measured** the moment Phase 0 lands — at which point we stop arguing about percentages and read them off `efficiency_report.py`.

---

## 5. What I need from you to start

1. **Go / no-go on the sequence** — default is 0→1→2→3→4. Say "flip 0 and 1" if you want relief before proof.
2. **The stakes list is policy, not code** — confirm the high-stakes keyword set (I'll propose: migrations, `git push`/`force`, prod, `DROP`/`rm -rf`, table/column renames, mass-edit globs). You own this list; the safety of Phase 1 rides on it.
3. **Permission to modify hooks** — Phases 1 & 3 edit `.claude/hooks/` and `settings.json`. Per guild conduct I won't touch them until you say go.

I recommend approving **Phase 0 alone first** — it's half a day, zero behavior change, and it converts this whole plan from "Claude's estimates" into your own dashboard number before you authorize anything riskier.
