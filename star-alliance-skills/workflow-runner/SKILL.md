---
name: workflow-runner
metadata:
  version: 1.1.0
type: Skill
description: "The Quartermaster's craft for operating the guild's own machinery — RUN a star-map workflow end to end via guild/run.py (resolve each step to a script, a prose delegate call, or a human gate; halt at gates; write run_summary.md under runs/), and invoke the four standalone primitives: guild/frame_brief.py (frame a request into a brief), guild/plan.py (brief into a plan), tools/efficiency_report.py (offload-ROI), tools/member_level.py (promotion queue + levels). Run ONLY an existing workflow that fits the request's nature — never force-fit a mismatch; if none fits, STOP and hand back. Use to actually run the procedures the guild only declares. Triggers: 'run the X workflow', 'execute this workflow', 'dry-run the workflow', 'frame this brief', 'plan this', 'show the efficiency report', 'show the promotion queue', 'who is due for promotion'. Differs from members-formation (SELECTS which workflow fits, does not run it), workflow-forge (AUTHORS a workflow), and skillsmith (skill versioning)."
---

# Workflow Runner — operating the guild's own machinery

The guild is good at *declaring* procedures and bad at *running* them. Every member step, every gate, every framing instruction lives in `workflows.json` as a star-map entry — but `guild/run.py` is a finished, generic executor that almost nothing surfaces. Members re-derive a formation by hand when the runner would have walked it for them. This skill is the Quartermaster's craft of turning that latent machinery on: running a workflow by name, reading what the run produced, knowing where it will halt, and invoking the four standalone primitives directly when a full workflow is overkill.

You are not authoring a procedure here (that is **workflow-forge**) and not choosing which one fits (that is **members-formation**). You are the operator who pulls the lever.

## What this is / is not

- **Is:** running an existing `workflows.json` workflow via `python3 guild/run.py "<name>"`; reading its `run_summary.md`; invoking `frame_brief.py`, `plan.py`, `efficiency_report.py`, `member_level.py` standalone.
- **Is not:** authoring a workflow (workflow-forge), selecting a workflow for a request (members-formation), or versioning a skill (skillsmith). It runs what already exists; it does not write to `workflows.json`.
- **Is not:** a substitute for judgement. The runner mechanises the *mechanical* steps (scripts, prose delegations, gate halts); a member step that bundles judgement still stays prose and routes to a Claude subagent — the runner does not replace the member's own thinking.

## Principles

### 1. Run only an existing workflow that fits — if none fits, STOP before you start; never force-fit a mismatch
The name you hand to `run.py` must resolve to an **existing** `workflows.json` workflow whose **nature matches the request**. Following the existing workflows is a hard rule, not a default. A read-only audit request is run through **Strategic Audit**, never shoehorned into the write-oriented **Architecture Build** (or any build/change workflow) just because that entry exists and is close enough — a write-oriented workflow on a read-only request will produce and gate on changes the Guild Master never asked for.

This is a **pre-flight halt** — the same halting behaviour Principle 4 gives to gates, moved to before the first step. If no existing workflow fits the request, the runner does not improvise, does not bend the nearest entry, and does not invent a shape. It **stops and hands back**:

- **Wrong workflow picked, a right one exists** → return to **members-formation** to reselect.
- **No fitting workflow exists at all** → route to **workflow-forge** to author one, and surface the gap to the Guild Master. Per the guild's stop rule, a request that needs a *new* workflow STOPS and asks — it is never improvised into a mismatched run.

Confirm the fit with `--dry-run` (Principle 2) before spending a token: the resolution table shows you exactly which steps that workflow will run. If those steps do not match the request's nature, halt — do not run.

### 2. Run a workflow by its name; the runner resolves every step for you
`python3 guild/run.py "<Workflow Name>"` looks up the workflow case-insensitively in `workflows.json` and walks its `steps[]` in order. For each step it computes one of three resolutions and prints `[i/total] <title>  ->  (<resolution>)`:

- `script:<path>` — the step carries a `script` field; the runner executes `python3 <path>` (highest-priority resolver).
- `prose:<actor>/<model>` — no script, so the runner routes `act` + any `inputs` to the member's Claude model: spawn a Claude subagent via the Task tool (`subagent_type` = the step's `actor`; defaults to `sonnet`).
- `human` — `actor` is `user`/`you`, the `title` is in `HUMAN_TITLES` (place the order, report the bug, request the build, ask the question), or the step is a gate.

**Always dry-run first** to see the resolution without spending tokens or touching files — and to confirm the workflow fits the request per Principle 1:

```
python3 guild/run.py "Quick Fix" --dry-run
```

A dry-run prints what *would* run (e.g. `(dry-run) would run: python3 guild/conformance.py`) and exits — invent nothing about a workflow's shape; let `--dry-run` show you.

### 3. The run produces a state dir + a run_summary.md — read that, not the console
Every run writes its artifacts under a **state dir**, `runs/<workflow id>/` by default (override with `--state-dir runs/<id>`). Inside it: each prose step's `produces` file (a `*.md`), and a `run_summary.md` with the per-step resolution table and a final verdict line — `**Completed** all steps.` or `**HALTED**: <reason>`. The console scroll is ephemeral; `run_summary.md` is the durable record.

```
python3 guild/run.py "Conformance Sweep"
cat runs/conformance-sweep/run_summary.md
```

`runs/` is gitignored scratch and outside conformity scope — it is never flagged as stray. Cap it with `python3 guild/prune_runs.py --keep N`.

### 4. A gate is a hard halt — the runner stops and waits for a human, never routes a gate to a subagent
A step with `kind: gate` (or a `gate` field) is an approval checkpoint. `resolve_step` forces it to `human`, and when the runner reaches it the run **breaks** with `⏸ step i '<title>' — approval gate: <label>` and exits non-zero (`return 1`). It does not skip ahead. Two other halt paths exist for `script` steps: a `gate`-marked script that exits non-zero halts the whole run, and a step's `verify` script that exits non-zero halts it too. A passive human step (actor `you`, e.g. "Place the Order") merely *continues* — only a true gate stops the run. So a workflow that ends at the Butler's report gate will halt there by design; resume by acting on the gate, then re-running the downstream steps.

### 5. For framing and planning, call the two primitives directly — a full workflow is often overkill
Both reuse `guild/delegate.py` so spend auto-logs to the arsenal ledger, default to Claude model `sonnet`, and accept a file path *or* literal text as `--in`.

**Frame a raw request into a structured brief** (summary / scope / acceptance):
```
python3 guild/frame_brief.py --style restate --in request.md --out brief.md
```
Styles: `restate` · `clarify` · `shape` · `classify` · `reframe`.

**Turn a brief into a plan:**
```
python3 guild/plan.py --template campaign --in brief.md --out plan.md
```
Templates: `campaign` (waves) · `sprint` (tickets) · `scope` · `spec` · `lens` (audit rubric) · `panel` (expert seating).

These are the same primitives a workflow's framing/planning steps wire via `args` — running them standalone is how you frame or plan a one-off without authoring a star-map entry.

### 6. The two reporting primitives answer "is the offload paying off?" and "who is due to level up?"
**Efficiency report** — the offload-ROI baseline, joining `usage-log.jsonl` (cheap-bench calls) against `data/turn-cost.jsonl` (premium per-turn tokens):
```
python3 tools/efficiency_report.py            # human table
python3 tools/efficiency_report.py --days 7 --json
```
It prints offload-by-model, premium-by-tier, and a conservative `net displaced output tokens` line with its assumption stated inline. If the turn-cost hook has no data yet it says so — read the warning, don't fabricate a saving.

**Member-leveling console** — the promotion queue + laggard board (it rebuilds via `build.py` first, so levels reflect the current repo):
```
python3 tools/member_level.py report
python3 tools/member_level.py promote <member>          # confer up to the earned tier
python3 tools/member_level.py promote --all             # confer every due member
```
`report` is read-only and safe. `promote` writes a conferred level, logs a `member-upgrade` entry, rebuilds, and runs the conformity close — it **refuses** to confer a tier above what was earned, and needs `--demote` to regress. Add `--yes` to skip the prompt.

### 7. Operating the machinery is itself hands-on work — run, then read the artifact, then judge
The runner does the walking; you bring the judgement at the gates and on the produced artifacts. Run it, open `run_summary.md` or the `--out` file, and decide. Don't hand-simulate a workflow you could execute, and don't trust a console line you could verify by reading the file the step wrote.

## References

- `references/running-a-workflow.md` — `run.py` invocation, step resolution order, `--dry-run` / `--state-dir`, the `HUMAN_TITLES` set, the `args`→flags + file-rail wiring.
- `references/the-script-primitives.md` — `frame_brief.py`, `plan.py`, `efficiency_report.py`, `member_level.py`: every flag, style/template, and exit behaviour, grounded in the scripts.
- `references/run-outputs-and-gates.md` — what a run writes (state dir, `produces` files, `run_summary.md`), the three halt paths, and `runs/` scratch / conformity scope.

## Source of truth

`guild/run.py` · `guild/STEP-SCHEMA.md` · `guild/frame_brief.py` · `guild/plan.py` · `tools/efficiency_report.py` · `tools/member_level.py`. When this skill and a script disagree, the script wins — re-read it and fix the skill.
