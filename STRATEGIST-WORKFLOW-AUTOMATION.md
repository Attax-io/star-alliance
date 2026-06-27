---
type: Document
timestamp: 2026-06-27T10:27:03Z
---

# Strategist Report — Workflow Automation Proposal

> **Status:** PROPOSAL (not yet built) · **Date:** 2026-06-27
> **Workflow followed:** Strategic Audit (ships a document, not code)
> **Investigated by:** the-developer's doer weapon `minimax-m3` (delegated, 7.5k tokens — the guild's first organic delegation, logged to the ledger)
> **Verified by:** the-butler's thinker (factual claims checked against the repo)
> **Trigger:** Guild Master — *"following workflows is a must … investigate if we can improve the workflows by adding scripts or something else."*

---

## Plain-English summary

Today the guild's **24 workflows are just written instructions.** Nothing runs by itself — every time, a member re-reads the steps and does them by hand. This is slow and easy to get wrong.

The fix is to add **small scripts** that do the boring, repeated steps automatically, while leaving the thinking steps (planning, design, legal wording) to the members. Three changes make it happen:

1. **A few shared scripts** cover steps that repeat across almost every workflow:
   - `delegate.py` — the key one. Every step would call it; it picks the cheap helper model **and** records the token usage automatically (feeding the dashboard ledger we just built).
   - `conformance.py` — the "check everything is consistent" step that ends **23 of 24** workflows.
   - `frame_brief.py` — the "Butler turns the request into a clear brief" step, in **all 24**.
2. **An optional new format** so a workflow step can point to a script (`"script": "guild/conformance.py"`) instead of just describing the work in words. Old prose steps keep working — this is additive.
3. **A small runner** (`guild/run.py`) that walks the steps: runs the script if there is one, otherwise hands the prose to the right member's weapon.

**What stays human:** all judgement steps — planning, design mockups, legal translation, the developer's actual code fix. Scripts only handle the mechanical rails.

**Recommended first step:** build just `delegate.py` + `conformance.py`, wire them into 2–3 workflows as a pilot, prove it, then expand.

---

## Thinker's verification notes (the-butler)

Checked the doer's factual claims against the repo before filing:

- ✅ `conformity_check.py`, `build.py`, `build_guild_log.py`, `log_event.py`, `member_level.py` — all **exist** (the proposal correctly reuses them).
- ✅ No `guild/` runner directory exists yet — this is **greenfield**, no conflicts.
- ✅ **0** of the current workflow steps have any `script` field — confirms workflows are pure prose today, so the additive schema breaks nothing.
- ⚠️ `bug_reports` table and Gmail/WhatsApp/calendar sources (Tier-2 items #8, #10) belong to the wider Lex Council / MCP surface — those primitives are real but cross into another project's data; scope them carefully if pursued.
- ✅ Highest-leverage call is sound: `delegate.py` is the engine — it routes every prose step through `summon.py` + `arsenal_usage.py`, making delegation **and** ledger cost-tracking the default path. This directly extends the enforcement+measurement work shipped this session.

---

## Full proposal (as delivered by the doer, verified)

# Star Alliance Workflow Automation Proposal

## 1. Script Opportunities — Ranked by Leverage

### Tier 1 — Hits 20+ workflows (do these first)

| # | Workflow · Step | Script | What it does |
|---|---|---|---|
| 1 | **Confirm Guild Conformance** (the final step in 23/24 workflows) | `guild/conformance.py` | Thin wrapper over the existing `conformity_check.py`: run it, parse the contradiction map, write `conformance_signoff.md`, exit non-zero on contradictions. Every "Confirm Guild Conformance" prose step becomes one line: `{"script": "guild/conformance.py", "produces": "conformance_signoff"}`. |
| 2 | **Butler frame/restate/sharpen** (step 2 in all 24 — "Restate the Order", "Clarify the Ask", "Shape the Brief", …) | `guild/frame_brief.py --style <restate\|clarify\|shape\|classify\|reframe> --in <request> --out <brief.md>` | Calls the Butler weapon (default Sonnet) with a templated prompt per style; writes a structured brief with acceptance criteria. Replaces 24 near-identical prose steps. |
| 3 | **Strategist plan/scope/lens/spec** (Campaign Plan, Sprint Plan, Scope Document, Routine Spec, Audit Lens, Panel) | `guild/plan.py --template <campaign\|sprint\|scope\|spec\|lens\|panel> --in <brief> --out <plan.md>` | Single templated planner: takes a brief, routes to a thinker weapon, emits a plan with waves/roles/checkpoints depending on template. |

### Tier 2 — Hits 3–9 workflows (high reuse, narrower scope)

| # | Workflow · Step | Script | What it does |
|---|---|---|---|
| 4 | **Forge via MiniMax** loop (Art Forge, Arsenal Forge, Skill Forge, Workflow Forge sigils) | `guild/commission_art.py --brief <brief.md> --out <asset.png> --max-iter N` | Calls MiniMax, critiques with a vision-capable weapon, re-prompts with deltas, writes final + `art_log.md`. |
| 5 | **Run the Sweep** (Hygiene Rotation, Legal Codex publish check, cleanup gates) | `guild/hygiene_run.py --modes i18n,lint,dev_errors,postgres,docs [--publish-gate]` | Parameterized wrapper around the cleanup skill; replaces 6 lines of prose with a flag list. |
| 6 | **Wire to the Arsenal / Skill / Star Map** (Arsenal Forge, Skill Forge, Workflow Forge) | `guild/wire.py --kind <weapon\|skill\|workflow> --spec <spec.json> [--propagate loadouts]` | Reads a spec, updates `arsenal`/`skills`/`workflows.json`, propagates role-icon across member loadouts, then calls `build.py`. |
| 7 | **Bump & Stamp** (Release Train, Conformity Sweep fallout) | `guild/version_bump.py --step <patch\|minor\|major> --changelog <changelog.md> [--stamp docs]` | Bumps version, regenerates changelog from `git log`, rewrites all `version:` stamps in docs. |
| 8 | **Close & File Spawn** (Bug Cycle) | `guild/bug_ops.py --action <pull\|close\|spawn> --row <id>` | Wraps `bug_reports` table: pull open rows, flip to Fixed, file spawn tickets. *(crosses into Lex Council data — scope carefully)* |
| 9 | **Watch tick / Scout the Sessions** (Standing Watch, Guild Log Sync) | `guild/watch_tick.py --routine <name>` + `guild/session_scout.py --window today,yesterday --dry-run\|apply` | Generic unattended runner; second wraps `build_guild_log.py` + `log_event.py` + `build.py` as one call. |
| 10 | **Sweep the Inboxes / Harvest the Threads** (Comms Triage, Relationship Intel) | `guild/triage.py --sources gmail,calendar,whatsapp --window N --out <digest.json>` → `guild/triage_to_tasks.py` | Two-stage: structured digest → tasks/calendar. Drafts stay prose. *(crosses into MCP data — scope carefully)* |
| 11 | **Scan / Extract / Index / Translate** (Law Harvest, Legal Codex) | `guild/law_pipeline.py --stage <scan\|extract\|index\|translate> --in <path> --locales ar,fr,en` | One script, four stages; the locale loop becomes `--locales` iteration. |

### Tier 3 — Single-workflow but high payoff

- **Strategic Audit (Convene Panel, Converge & Grade)** → `guild/panel_audit.py --question <q> --weapons <w1,w2,w3> --out <audit.md>`.
- **Architecture Build (Build Migrations)** → `guild/migrate.py --dry-run` (BEGIN/ROLLBACK) gates the apply step.
- **Security Sweep (Hunt the Holes)** → `guild/sec_audit.py --advisors supabase,rls,grants --out <vuln_map.md>`.
- **Conformity Sweep (Reconcile to Conformity)** → `guild/conform.py` runs `conformity_check.py`, applies fixes per contradiction ID, re-runs until clean.
- **Relationship Intel (harvest/profile/flag)** → `guild/rel_intel.py --stage <harvest\|profile\|flag>`.

---

## 2. Structural Change — Schema & Runner

### Proposed `workflows.json` step schema (additive, prose still works)

```json
{
  "name": "Standard Mission",
  "state_dir": "runs/standard-mission",
  "chain": null,
  "steps": [
    { "title": "Place the Order", "act": "You describe the mission…", "actor": "user", "produces": "raw_request" },
    { "title": "Rewrite as Clear Brief", "act": "The Butler rewrites…", "actor": "butler", "weapon": "sonnet", "inputs": ["raw_request"], "produces": "cleared_brief" },
    { "title": "Distribute the Assignments", "script": "guild/distribute.py", "inputs": ["cleared_brief", "campaign_plan"], "args": { "mode": "routed" }, "produces": "routed_assignments", "verify": "guild/verify_routing.py" },
    { "title": "Confirm Guild Conformance", "script": "guild/conformance.py", "produces": "conformance_signoff", "gate": "butler_report" }
  ]
}
```

**New optional fields per step:** `actor` (member name) · `weapon` (arsenal model) · `script` (runnable path, replaces/augments `act`) · `inputs` (earlier `produces` keys loaded as files) · `args` (literal object) · `verify` (script that must exit 0 before the next step) · `gate` (named human-approval checkpoint) · `loop` (`{over, per}` for data iteration) · `parallel` (run with siblings).

**New optional workflow fields:** `state_dir` (artifact dir) · `chain` (ordered list of follow-on workflows — the release closeout chain becomes data) · `pre`/`post` (shared scripts).

### Lightweight runner — `guild/run.py`

```python
for step in workflow.steps:
    inputs = {k: load(prev[k]) for k in step.get("inputs", [])}
    out    = state_dir / f"{step['produces']}.md"
    if step.get("script"):
        run(step["script"], inputs=inputs, args=step.get("args", {}), out=out)
    else:
        prompt = render(step["act"], inputs, actor=step["actor"], weapon=step["weapon"])
        delegate(prompt, weapon=step["weapon"], actor=step["actor"], out=out)
    if step.get("verify") and not run(step["verify"], in=out): halt(step["title"])
    if step.get("gate"): await_human(step["gate"])
    register(step["produces"], out)
```

Prose steps still work — they become one `delegate()` call to the named weapon, producing the artifact file. Script steps bypass the model. The runner makes the *boundary* between mechanical and judgement explicit; it does not replace judgement.

---

## 3. Shared Primitives — build once, use everywhere

| Primitive | Replaces prose in | Notes |
|---|---|---|
| `guild/delegate.py` | **All prose steps** | Takes (prompt, actor, weapon) → calls `summon.py` + `arsenal_usage.py`. **The runner's engine; highest leverage.** |
| `guild/conformance.py` | "Confirm Guild Conformance" ×23 | Wraps existing `conformity_check.py`. |
| `guild/frame_brief.py` | "Butler restates/sharpens/frames" ×24 | `--style` flag covers all variants. |
| `guild/plan.py` | Strategist planning ×7 | `--template` flag covers all named plans. |
| `guild/commission_art.py` | "Forge via MiniMax" ×4 | Vision-critique loop. |
| `guild/wire.py` | Arsenal/Skill/Workflow wiring ×3 | One `--kind` flag + one propagation pass. |
| `guild/hygiene_run.py` | Hygiene sweep + publish check | `--modes` flag list. |
| `guild/version_bump.py` | Bump & stamp | Bump + changelog + stamp walk. |
| `build.py` *(exists)* | "rebuild the dashboard" ×5 | Already there — wire as primitive. |
| `log_event.py` *(exists)* | "log the entry" ×many | Already there — wire as primitive. |
| `guild/session_scout.py` | Guild Log Sync steps | Wraps `build_guild_log.py` + `log_event.py` + `build.py`. |
| `guild/panel_audit.py` | Strategic Audit | Multi-weapon fan-out + converge. |

The single highest-leverage build is **`guild/delegate.py`** — every prose step eventually routes through it, and it makes the existing `summon.py` / `arsenal_usage.py` cost-tracking automatic.

---

## 4. Risks & What Stays Prose

**Must stay prose (judgement — never scripted):** Strategist/Architect planning (which waves, roles, dependencies) · Designer visual mockups · Translator fidelity · the Developer's "smallest correct fix" · the human input steps at the head of every workflow (Place the Order, Report the Bug) · defining an audit *lens* · *which* thinkers to seat on a panel · deciding *which* contradiction is real.

**Risks to watch:**
1. **Prose drift** — once a step gets a `script`, auto-generate its `act` text from the script's docstring so there's one source of truth.
2. **State-dir growth** — `produces` artifacts are files; needs a retention policy.
3. **Gate fatigue** — make gates *advisory* by default; hard-halt only on critical ones (`push`, `merge`, `publish`).
4. **Conformance coverage** — runner `out` paths must be in the source-of-truth set, or `conformance.py` flags them as missing.
5. **Model cost** — set each step's `weapon` deliberately; don't default to a frontier model for cheap steps.

**Net win:** the 23 conformance steps, 24 framing steps, and 7 plan steps collapse to one-line `{"script": …}` references; the 24 workflows become deterministic on the mechanical rails, freeing the members for the steps that actually need judgement.

---

## Recommended pilot (the-butler's call)

Build the two highest-reuse primitives first, prove them, then expand:

1. **`guild/delegate.py`** — the engine (routes through `summon.py` + `arsenal_usage.py`).
2. **`guild/conformance.py`** — wraps `conformity_check.py` (covers 23/24 workflows).
3. Wire them into **2–3 workflows** (e.g. Quick Fix, Conformity Sweep) and a minimal `guild/run.py`.

This is **Architecture Build / Standard Mission** territory — the-architect designs the schema, the-developer builds it — so no new workflow is needed.
