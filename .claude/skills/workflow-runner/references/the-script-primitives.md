---
type: Document
title: The four standalone primitives
---

# The four standalone primitives

These run on their own — no workflow needed. The two framing/planning primitives are the same scripts a workflow's `args`-carrying steps wire; running them directly is how you frame or plan a one-off. The two reporting primitives answer the guild's two standing questions: is the offload paying off, and who is due to level up.

Both `frame_brief.py` and `plan.py` reuse `guild/delegate.py`'s `delegate()`, so token spend auto-logs to the arsenal ledger; both default to weapon `minimax-m3`; both accept a **file path OR literal text** as `--in`; both exit 0 on success, non-zero on failure.

## `guild/frame_brief.py` — frame a request into a structured brief

Collapses the near-identical framing steps that open most workflows into one templated call. Emits a Markdown brief: a one-line **Summary**, a **Scope — what will be touched** list, and **Acceptance criteria**.

```
python3 guild/frame_brief.py --style <style> --in <request_or_text> --out <brief.md> [--weapon <model>]
```

`--style` (required), one of: `restate` (strip ceremony, capture true intent), `clarify` (resolve vagueness into testable requirements), `shape` (a crisp brief the guild can act on), `classify` (identify type + workflow + members/skills to route to), `reframe` (sharpen the underlying question). Importable: `frame_brief(style, request, weapon="minimax-m3") -> str`. Raises `ValueError` on an unknown style or an empty request.

## `guild/plan.py` — turn a brief into a plan

Routes a framed brief to a thinker weapon with a per-template system prompt. Emits Markdown starting with a single-sentence objective, then the structured plan.

```
python3 guild/plan.py --template <template> --in <brief_or_text> --out <plan.md> [--weapon <model>]
```

`--template` (required), one of: `campaign` (ordered waves: goal, roles, checkpoint, success condition), `sprint` (tickets: title, owner, acceptance, dependencies), `scope` (in/out of scope, surfaces, risks, assumptions), `spec` (behaviour, I/O, edge cases, verification), `lens` (an audit rubric — dimensions + what good looks like, NOT the audit itself), `panel` (expert perspectives + the question each owns + how verdicts converge). Importable: `plan(template, brief, weapon="minimax-m3") -> str`. Raises `ValueError` on an unknown template or an empty brief.

## `tools/efficiency_report.py` — the offload-ROI report

Joins two measurement streams: `star-alliance-arsenal/usage-log.jsonl` (every offloaded cheap-bench call, with phase + wall_ms) and `data/turn-cost.jsonl` (per-turn premium tokens + routing tier, written by the turn-cost Stop hook).

```
python3 tools/efficiency_report.py [--days N] [--json]
```

- `--days N` — trailing window in days (`0`/omitted = all).
- `--json` — raw JSON instead of the human table.

Prints **OFFLOAD** (per-model calls / in / out / median wall-ms), **PREMIUM** (per-tier turns / in / out / median in-per-turn), and a **NET** line: `displaced output tokens = offload out − premium out`, with the assumption stated inline (1 bench output token = 1 Opus output token avoided; output only — a deliberately conservative proxy, NOT a billing figure). If the turn-cost hook has recorded no turns yet, it prints a warning that the baseline is incomplete — read it, don't invent a number.

## `tools/member_level.py` — the member-leveling console

A member's level is a craft-depth meter (arsenal + specialty), earned by an objective checklist computed in `build.py` and conferred by the Quartermaster. This tool reads the build-derived levels and confers promotions. It **rebuilds via `build.py` first**, so the board reflects the current repo. Tiers, low→high: Foundational, Intermediate, Advanced, Elite, Master.

```
python3 tools/member_level.py report                       # promotion queue + laggard board (READ-ONLY)
python3 tools/member_level.py promote <member>             # confer up to the earned tier
python3 tools/member_level.py promote <member> --to Advanced
python3 tools/member_level.py promote --all                # confer every due member
python3 tools/member_level.py promote <member> --to Intermediate --demote   # ratify a regression
```

Add `--yes` to skip the per-member confirmation prompt.

- **`report`** — prints the conferred-vs-earned table, the **promotion queue** (earned above conferred, with the next tier's checklist), the **laggard board** (thinnest arsenals first, with next-tier gaps), and any **regressions** (conferred above earned). Safe to run anytime.
- **`promote`** — writes the conferred `level` into `data/members-meta.json`, logs a `member-upgrade` event via `tools/log_event.py`, rebuilds, then runs the conformity close (`build.py` + `conformity_check.py`). It **refuses** to confer a tier above what was *earned* ("deepen the arsenal first"), and refuses to confer below the current tier unless `--demote` is passed.
