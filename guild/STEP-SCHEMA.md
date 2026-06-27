---
type: Document
timestamp: 2026-06-27T10:27:03Z
---

# Workflow Step Schema — the-architect's design spec

Status: **BLESSED CONTRACT** (implemented in `guild/run.py`) · wiring into `workflows.json` **LIVE** as of Wave 0 (see bottom).

This formalizes the optional fields a `workflows.json` step may carry so the runner
can execute it deterministically. **Fully additive:** a step with none of these is a
plain prose step and behaves exactly as before. Prose never breaks.

## Step fields the runner honors today

| Field | Type | Meaning |
|---|---|---|
| `title` | string | Display name. Also a routing key for the human handoff fallback (see `HUMAN_TITLES` in `run.py`). |
| `act` | string | The prose instruction. For a prose step, this becomes the prompt sent to the member's weapon. |
| `actor` | string | Member id (`the-butler`, `the-developer`, …) **or** `user`/`you`. `user` ⇒ the step is a human handoff (skipped by the runner). |
| `weapon` | string | Arsenal model id (`minimax-m3`, `kimi-k2.7`, …). Defaults to `minimax-m3` if absent. The weapon that executes a prose step. |
| `script` | string | Path to a runnable script (repo-relative). If present, the step runs the script instead of a model. **Highest-priority resolver.** |
| `args` | object | Literal `{key: value}` flags for a **script** step. The runner translates them to `--key value` CLI flags appended to the invocation (see *args → flags* below). Steps with no `args` invoke the script exactly as before — fully backward-compatible. |
| `inputs` | string[] | Earlier `produces` keys / paths, loaded as files and appended to the prose prompt (prose steps) **or** resolved to a file path passed as `--in` (script steps that carry `args`, unless `args` set `in` explicitly). |
| `produces` | string | Output filename for this step's artifact (written under the run's `state_dir`). |
| `verify` | string | Script path that must exit 0 after a script step, or the run halts. |
| `gate` | string | Marks a critical step: if its script exits non-zero, the **whole run halts** (not just skips). Use for `push`/`merge`/`publish`-class steps. |

## Resolution order (per step, as implemented)

1. `actor ∈ {user, you}` **or** `title ∈ HUMAN_TITLES` → **human** (skipped).
2. explicit `step.script` → **run that script**.
3. otherwise → **prose**: `delegate(weapon, act + inputs)` and write `produces`.

Resolution is now **purely data-driven**: there is no hardcoded title→script map. A step
runs a script if and only if it carries a `script` field. (The earlier `TITLE_SCRIPT` crutch
that auto-mapped *"confirm guild conformance"* → `guild/conformance.py` was removed in Wave 0;
that mapping now lives in the data — all 24 conformance steps carry `"script": "guild/conformance.py"`.)

## `args` → CLI flags (Wave 1)

A script step may carry an `args` object. The runner (`args_to_flags` in `run.py`) turns it
into appended CLI flags:

- `{"style": "restate"}` → `--style restate`
- `{"dry-run": true}` → `--dry-run` (a bare flag; `true` emits no value)
- `false` / `null` values are dropped; everything else is stringified.

For a script step that carries `args`, the runner also wires the **file rails** automatically
(`resolve_io_args` in `run.py`): it supplies `--in` from the step's first `inputs` entry
(resolved to a `state_dir` / repo path) and `--out` from `produces`, unless `args` already set
`in` / `out` explicitly. Steps **without** `args` (e.g. every *Confirm Guild Conformance*
step) are invoked with no flags at all — exactly as before.

This is how Wave 1 wires the framing/planning primitives: a framing step becomes
`{"script": "guild/frame_brief.py", "args": {"style": "<style>"}, "inputs": ["<raw request>"], "produces": "<brief>"}`
and a planning step `{"script": "guild/plan.py", "args": {"template": "<template>"}, ...}`.

## Run outputs & conformity scope (Wave 3)

A run writes its artifacts under a **state dir** — `runs/<workflow id>/` by default:
per-step `produces` files (`*.md`) plus a `run_summary.md`. **`runs/` is gitignored
scratch** (`.gitignore` line `runs/`) and is **outside conformity scope**:
`conformity_check.py` audits only the JSON guild model and a fixed set of known
source dirs (`star-alliance-skills/`, `star-alliance-members/`, …) — it performs **no
filesystem scan for stray/orphan files** and never reads `runs/`. So run outputs are
never flagged as stray or missing, and no ignore-list is needed. To cap the scratch,
use `guild/prune_runs.py [--keep N] [--dry-run]` (keeps the N most-recent run dirs).

## Deferred fields (in the proposal, NOT yet implemented — do not use until run.py supports them)

`loop {over, per}` · `parallel` · workflow-level `state_dir` / `chain` / `pre` / `post`.
Adding any of these is a follow-on slice that must extend `run.py` first.

## Example (the shape to apply to a real workflow once unblocked)

```json
{
  "name": "Quick Fix",
  "steps": [
    { "title": "Report the Bug", "actor": "user", "produces": "raw_request" },
    { "title": "Make the Fix", "actor": "the-developer", "weapon": "minimax-m3",
      "inputs": ["raw_request"], "produces": "fix_notes" },
    { "title": "Confirm Guild Conformance", "script": "guild/conformance.py",
      "produces": "conformance_signoff", "gate": "conformance" }
  ]
}
```

## Wiring status (Wave 0 — DONE)

The additive fields are now applied to `workflows.json`:

- **24 × "Confirm Guild Conformance"** steps carry `"script": "guild/conformance.py"` in the
  data. The runner resolves them via the step's own `script` field — the `TITLE_SCRIPT` crutch
  is removed from `run.py`.
- Every other member step stays **prose** (judgement). Steps that *touch* tooling but bundle
  judgement or chain multiple calls — *Reconcile to Conformity* (decide which contradiction is
  real → fix at source → `build.py` → re-run), *Log the Missing Entries* (`build_guild_log.py`
  + `log_event.py` + `build.py`), *Scout the Sessions*, *Write to the Star Map*, *Wire the Art*
  — are **not** pure single tool calls, so they remain prose for now.
- Framing/planning steps stay prose: their future scripts (`frame_brief.py`, `plan.py`) do not
  exist yet, so wiring them would point at nothing. They get a `weapon` hint at most.

Only scripts that exist today are wired: `guild/conformance.py`. The rest of the proposal's
primitives (`frame_brief.py`, `plan.py`, `commission_art.py`, …) are later waves.

### Verify after editing
- `python3 -c "import json; json.load(open('workflows.json'))"` — parses.
- `python3 guild/run.py "Quick Fix" --dry-run` — *Confirm Guild Conformance* → `script:guild/conformance.py`.
- `python3 conformity_check.py` — exits 0 (extra step keys pass through untouched).
- A dashboard rebuild (`build.py`) + version bump is the **Wave-5 close-out**, not this slice.
