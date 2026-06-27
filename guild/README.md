# guild/ — workflow runner (PILOT)

First slice of the [workflow automation proposal](../STRATEGIST-WORKFLOW-AUTOMATION.md):
turn prose-only workflows into script-backed, deterministic runs. Additive — prose
steps still work.

## Scripts

| Script | What it does |
|---|---|
| `delegate.py` | The engine. `delegate(model, prompt, …)` shells `star-alliance-arsenal/summon.py`, so every call auto-logs to the arsenal ledger. CLI: `python3 guild/delegate.py <model> "<prompt>"`. |
| `conformance.py` | Wraps the repo's `conformity_check.py`; writes `runs/conformance_signoff.md`; **exits with the check's code** so it can gate a workflow. |
| `run.py` | Executes a workflow from `workflows.json` by name. Resolves each step → **human** (user input), **script** (explicit `step.script` or a known title), or **prose** (→ `delegate()` with the step's `actor`/`weapon`). `--dry-run` shows the plan without calling models. |

## Run

```sh
python3 guild/run.py "Quick Fix" --dry-run      # see how each step resolves
python3 guild/conformance.py                    # standalone conformance gate
```

## Status

Pilot. Proves the runner + the two highest-leverage primitives. Steps are wired by a
title→script map in `run.py` (no `workflows.json` schema change yet). Next: bless the
optional step schema (`script`/`actor`/`weapon`/`verify`/`gate`) into `workflows.json`
and expand the primitive set — see the proposal. Built by `the-developer` via doer
delegation (drafted by `minimax-m3` after `kimi-k2.7` overran its budget), verified by
the thinker.

Runtime output lands in `runs/` (gitignored).
