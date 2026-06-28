---
type: Document
title: Run outputs and gates
---

# Run outputs and gates

What a run leaves behind, and the exact points at which it stops.

## The state dir

Every run writes under a **state dir** — `runs/<workflow id>/` by default, or whatever `--state-dir` names. The id is the workflow's `id` field, or a slug of its name. Relative state dirs resolve against the repo root; the runner `mkdir -p`s it.

Inside the state dir:

- **Per-step `produces` files** — each prose step writes its `delegate()` output to its `produces` filename (a bare name gets a `.md` suffix; a step with no `produces` falls back to `<i>_<slug-of-title>.md`). Script steps that declare a `produces` artifact write to it via their own `--out` rail.
- **`run_summary.md`** — written at the end (even on a halt). It carries the workflow name, id, state dir, dry-run flag, the per-step resolution table (`| # | Step | Resolution |`), and a final verdict line: `**Completed** all steps.` or `**HALTED**: <reason>`.

Read `run_summary.md`, not the console scroll — the console is ephemeral, the summary is the durable record of what resolved to what and where it stopped.

## `runs/` is gitignored scratch, outside conformity scope

`runs/` is in `.gitignore`. `conformity_check.py` audits only the JSON guild model and a fixed set of known source dirs — it does **no** filesystem scan for stray files and never reads `runs/`. So run outputs are never flagged as stray or missing, and no ignore-list is needed. To cap the scratch: `python3 guild/prune_runs.py [--keep N] [--dry-run]` keeps the N most-recent run dirs.

## The three halt paths

The runner returns `1` (and writes `**HALTED**` into the summary) at the **first** of these; otherwise it returns `0` with `**Completed** all steps.`:

1. **Approval gate** — a step with `kind: gate` or a `gate` field resolves to `human`. When the runner reaches it, it **breaks** with `⏸ step i '<title>' — approval gate: <label or 'awaiting human go'>`. A gate is a hard human checkpoint: it can never be skipped and never routes to a weapon.
2. **Gate-marked script fails** — a script step that *also* carries a `gate` field and exits non-zero halts the whole run (`! step i '<title>' (gate) exited <code>`). Use this for `push`/`merge`/`publish`-class steps. A non-gate script that fails is logged and the run continues.
3. **`verify` fails** — after a script step, if the step has a `verify` script and it exits non-zero, the run halts (`! step i '<title>' verify exited <code>`).

A **passive** human step (actor `you`/`user`, or a `HUMAN_TITLES` title, with NO gate) does not halt — the runner just `continue`s past it. Only a true gate stops the run.

## Resuming after a halt

The runner is forward-only — it does not checkpoint-and-resume mid-`steps[]`. After a gate halt: act on the gate (do the human approval / fix the failing script), then re-run. For an idempotent workflow, re-running from the top is fine; for a partial replay, point `--state-dir` at the same dir so completed `produces` files are still present for later `inputs` to load, and lean on `--dry-run` first to confirm the resolutions.

## Reading order after a run

1. Open `runs/<id>/run_summary.md` → check the verdict line and which step it stopped on.
2. If a prose step produced an artifact you need, open its `produces` file in the same dir.
3. If it halted on a gate, that is by design (e.g. the Butler's report gate that ends every workflow) — bring the judgement the gate asks for.
