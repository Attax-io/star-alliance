# Workflow Step Schema — the-architect's design spec

Status: **BLESSED CONTRACT** (implemented in `guild/run.py`) · wiring into `workflows.json` **deferred** (see bottom).

This formalizes the optional fields a `workflows.json` step may carry so the runner
can execute it deterministically. **Fully additive:** a step with none of these is a
plain prose step and behaves exactly as before. Prose never breaks.

## Step fields the runner honors today

| Field | Type | Meaning |
|---|---|---|
| `title` | string | Display name. Also the fallback routing key (see `TITLE_SCRIPT`, `HUMAN_TITLES` in `run.py`). |
| `act` | string | The prose instruction. For a prose step, this becomes the prompt sent to the member's weapon. |
| `actor` | string | Member id (`the-butler`, `the-developer`, …) **or** `user`/`you`. `user` ⇒ the step is a human handoff (skipped by the runner). |
| `weapon` | string | Arsenal model id (`minimax-m3`, `kimi-k2.7`, …). Defaults to `minimax-m3` if absent. The weapon that executes a prose step. |
| `script` | string | Path to a runnable script (repo-relative). If present, the step runs the script instead of a model. **Highest-priority resolver.** |
| `inputs` | string[] | Earlier `produces` keys / paths, loaded as files and appended to the prose prompt. |
| `produces` | string | Output filename for this step's artifact (written under the run's `state_dir`). |
| `verify` | string | Script path that must exit 0 after a script step, or the run halts. |
| `gate` | string | Marks a critical step: if its script exits non-zero, the **whole run halts** (not just skips). Use for `push`/`merge`/`publish`-class steps. |

## Resolution order (per step, as implemented)

1. `actor ∈ {user, you}` **or** `title ∈ HUMAN_TITLES` → **human** (skipped).
2. explicit `step.script` → **run that script**.
3. `title` matches the built-in `TITLE_SCRIPT` map (e.g. *"confirm guild conformance"* → `guild/conformance.py`) → **run that script**.
4. otherwise → **prose**: `delegate(weapon, act + inputs)` and write `produces`.

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

## Wiring plan (deferred — `workflows.json` is the bottleneck)

The actual application of these fields to `workflows.json` is **intentionally not done in
this slice**: at authoring time `workflows.json` (and its generated `guild-data.*`) were
**dirty with a concurrent session's uncommitted work** (the "web-oracle" workflow). Editing
the shared file would entangle two sessions' changes and violate the commit-scope rule
(decision #63). When `workflows.json` is clean:

1. Add `actor`/`weapon`/`produces` to each step of 2–3 pilot workflows (start: Quick Fix,
   Conformity Sweep) — purely additive keys.
2. Replace the *"Confirm Guild Conformance"* prose step's reliance on `TITLE_SCRIPT` with an
   explicit `"script": "guild/conformance.py"` + `"gate": "conformance"`.
3. Run `python3 build.py` and confirm `guild-data.js` still parses and the dashboard renders
   (extra step keys are ignored by the renderer — verified: `build.load_workflows` passes
   unknown fields through untouched).
4. `python3 guild/run.py "<workflow>" --dry-run` to confirm resolution, then commit.

Until then the runner already executes correctly via `title`-based resolution, so nothing is
blocked operationally — only the formal in-file annotation waits.
