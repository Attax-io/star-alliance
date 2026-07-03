---
type: Document
title: Running a workflow with guild/run.py
---

# Running a workflow with `guild/run.py`

The generic executor. It loads `workflows.json` from the repo root, finds the workflow by name (case-insensitive), and walks `steps[]` in order, resolving each step to a script, a prose delegation, or a human handoff.

## Invocation

```
python3 guild/run.py "<Workflow Name>" [--dry-run] [--state-dir runs/<id>]
```

- `name` (positional, required) — the workflow's `name` field, matched case-insensitively. If no match, the runner exits with the available names listed.
- `--dry-run` — print each step's resolution without executing (no scripts run, no weapons called, no files written beyond the summary path logic).
- `--state-dir <dir>` — where step outputs go. Default: `runs/<workflow id>` (the workflow's `id`, or a slug of its name). Relative paths resolve against the repo root.

Console output per step: `[i/total] <title>  ->  (<resolution>)`.

## Step resolution order (`resolve_step` in run.py)

For each step, exactly one of three resolutions, in this priority:

1. **human** — if `kind == "gate"` or a `gate` field is present; OR `actor` is `user`/`you`; OR the lowercased `title` is in `HUMAN_TITLES`.
2. **`script:<path>`** — the step carries a non-empty `script` field. Highest-priority *executing* resolver: a script step always runs the script, never spawns a subagent.
3. **`prose:<actor>/<model>`** — the fallback. The runner routes the prompt to the member's Claude model — spawn a Claude subagent via the Task tool (`subagent_type` = the step's `actor`).

`HUMAN_TITLES` (exact, lowercased): `place the order`, `report the bug`, `request the build`, `ask the question`. `DEFAULT_MODEL` is `sonnet`.

## Step fields the runner honors (`guild/STEP-SCHEMA.md`)

| Field | Meaning |
|---|---|
| `title` | display name; also a `HUMAN_TITLES` routing key |
| `act` | prose instruction → becomes the prompt for a prose step |
| `actor` | member id, or `user`/`you` (⇒ human handoff) |
| `model` | the member's Claude model (`opus`/`sonnet`/`haiku`); defaults to `sonnet` |
| `script` | repo-relative script path; **highest-priority resolver** |
| `args` | `{key: value}` → `--key value` CLI flags for a script step |
| `inputs` | earlier `produces` keys/paths; appended to a prose prompt, or resolved to `--in` for a script step that carries `args` |
| `produces` | output filename for this step's artifact (under the state dir) |
| `verify` | script that must exit 0 after a script step, else the run halts |
| `gate` | critical step: non-zero exit halts the **whole run** |

Steps with none of these are plain prose and behave exactly as before — the schema is fully additive.

## `args` → flags, and the file rails (`args_to_flags` + `resolve_io_args`)

A script step's `args` object becomes appended CLI flags:

- `{"style": "restate"}` → `--style restate`
- `{"dry-run": true}` → `--dry-run` (bare flag; `True` emits no value)
- `False` / `None` values are dropped; everything else is stringified.

For a script step that carries `args`, the runner also wires the **file rails** automatically: `--in` from the step's first `inputs` entry (resolved to a state-dir/repo path) and `--out` from `produces`, unless `args` already set them explicitly. A script step **without** `args` is invoked with no flags at all. This is how a workflow wires the framing/planning primitives, e.g.

```json
{ "script": "guild/frame_brief.py", "args": {"style": "restate"},
  "inputs": ["raw request"], "produces": "brief" }
```

## Verify after editing a workflow

- `python3 -c "import json; json.load(open('workflows.json'))"` — parses.
- `python3 guild/run.py "<name>" --dry-run` — confirm each step resolves as intended.
- `python3 tools/conformity_check.py` — extra step keys pass through untouched.

## Deferred fields — do NOT use yet

`loop {over, per}`, `parallel`, and workflow-level `state_dir` / `chain` / `pre` / `post` are in the proposal but **not implemented** in `run.py`. Using them does nothing until the runner is extended first.
