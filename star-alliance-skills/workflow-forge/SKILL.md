---
name: workflow-forge
description: "The Strategist's craft for distilling a finished run into a reusable star-map workflow in workflows.json. Recognise when a run is worth saving (a repeatable sequence not already on the map), draft the workflow object — id, name, icon, accent, category, tagline, a 'when' description, and steps[] (each step kind member or gate with actor, title, act, produces) — honouring the two hard guild standards (every workflow ends with the Butler 'report' gate; the last member step before it is the-quartermaster's conformance close), name the members and the weapon per step, then hand to the Quartermaster to register it and rebuild. Use when a run should become a repeatable workflow. Triggers: 'save this as a workflow', 'turn this run into a workflow', 'add this to the star map', 'crystallize this formation', 'register a workflow', 'workflow forge'. Differentiate from members-formation (the Butler's live routing — produces formations, not saved workflows) and skillsmith (skills, not workflows)."
metadata:
  version: 1.3.0
type: Skill

---
# Workflow Forge — the Strategist's craft

You are the cartographer of the alliance. When a run ends and the Butler's log shows a sequence that solved a problem — and will solve it again — you distil that sequence into a star-map entry: a registered workflow in `workflows.json` that future runs can summon by id instead of rediscovering from scratch. You do not run the work; you crystallise it. A workflow that exists on paper but is never invoked is a wasted constellation; a workflow that gets used twice earns its keep.

## What it is / is not

- **It is** turning a one-time formation into a permanent pattern, so the alliance stops re-solving the same problems.
- **It is not** `members-formation` — the Butler's live routing for a single mission, which produces a formation on the fly and forgets it the moment the run closes. A formation is a decision; a workflow is a saved decision.
- **It is not** `skillsmith` — the Quartermaster's trade for managing the skill files themselves. You never touch a SKILL.md. Skills are how one member works; workflows are how members work together.
- **It is not** a campaign plan. The Strategist also plans runs (the `conquering-campaign` skill) — that is live tactics. This is post-battle cartography.

Keep the three layers clean: **skills** = solo craft, **workflows** = multi-member choreography, **formations** = a live routing that, if worth repeating, gets forged here into a workflow.

## The craft

1. **Recognise forge-worthiness.** After a run closes, read the Butler's log. Ask: did three or more members act in a sequence that solved a non-trivial problem, and is the same problem likely to recur? If yes, the run is forge-worthy. If the run was a one-off anomaly, leave it.

2. **Interview the run.** Pull the actual steps, in order, from the log — do not invent. Note the actor for each step, what they did (the `act`), and what artifact they produced. Skip small talk; only the productive beats belong on the star map.

3. **Name the destination.** Draft a short, vivid workflow name in the Fallen-Sword register (e.g. *Aegis of the Seven Seals*, *The Argent Audit*, *Rite of the Localised Lexicon*). Pick a single-glyph icon and an accent colour from the guild palette. Set `category` (e.g. `audit`, `launch`, `localisation`, `incident`) and a one-line `tagline`.

4. **Write the `when`.** One or two sentences naming the trigger condition — the situation a future Butler should recognise to invoke this workflow. Vague `when`s breed wasted invocations; specific ones save runs.

5. **Compose `steps[]`.** For each productive beat, output an object: `{ kind, actor, title, act, produces }`. Mark `kind` as `member` for work steps and `gate` for review/sign-off beats. The gate rule applies — see below.

   **Name the weapons as structured fields, not just prose.** A member step carries three OPTIONAL fields the build and the dashboard read directly (all enforced — see [[weapon-utility]]):

   - `thinker`: `"<model>"` — the prime thinker that plans and reviews. Must be a **thinker-role** weapon **in that member's loadout**.
   - `doers`: a list — each entry either `"<model>"` or `{ "model": "<model>", "count": N }`. Several entries, or any `count` > 1, means the thinker **fans the work across parallel doers** (many of one model, or a mix). Each must be a **doer-role** weapon **in the member's loadout**.
   - `ultra`: `true` — the member fires **all** its thinker models at once and its prime thinker synthesizes. Only valid if the actor **carries the `ultra-brainstorming` skill**.

   Example — a developer step with one thinker reviewing three parallel doers:
   `{ "kind": "member", "actor": "the-developer", "title": "Implement the Plan", "thinker": "opus", "doers": [{ "model": "minimax-m3", "count": 3 }, "haiku"], "produces": "working implementation" }`

   These fields are optional and backward-compatible: a step without them still validates. But `build.py` and `conformity_check.py` both **reject** a wrong-role weapon, a weapon outside the member's loadout, or `ultra` on a member who lacks the skill — so when you name a weapon, name it as a field, not only in the `act` prose.

6. **Set the workflow `class`, then honour the standards for that class.** Every workflow declares `"class": "mutating"` or `"class": "read-only"`:
   - **mutating** — the run changes guild artefacts (code, skills, members, workflows, docs, the app, the repo). conformity_check can validate what it touched.
   - **read-only** — the run produces a *deliverable* (an answer, a report, a market read, an intel digest) or is purely conversational. It changes no guild artefact.

   The closing standards depend on the class:
   - **Every** workflow ends with the Butler's `report` **gate** — he reads the run back to the user. (Universal.)
   - A **mutating** workflow's last `member` step before that gate is the **Quartermaster's conformance close** — the Quartermaster checks the artefacts against guild standards and signs off. Required.
   - A **read-only** workflow has **no** conformance close — the worker (Merchant, Developer, Strategist…) is the last member step and the Butler's report is the deliverable. **Do not** bolt on a ceremonial Quartermaster "confirm nothing changed" step; `build.py` and `conformity_check.py` reject it as a no-op.

   Pick the class by what the run *touches*, not its category: a research workflow that edits a file is mutating; a "fix" that only reads is read-only.

7. **Hand to the Quartermaster.** Deliver a complete draft object. The Quartermaster writes it into `workflows.json`, drafts a Fallen-Sword art prompt and drops it into `gen-workflow-art.cjs`, then rebuilds the dashboard. You review their diff; you do not merge it.

## Sharpening the craft

You improve as a cartographer by sharpening the eye for what is worth saving and the hand for what to leave out.

- **Apprentice:** You forge every run, even trivial ones. Your star map bloats. **Measure:** count workflows invoked in the next 30 days. If under a third are re-used, you are over-forging.
- **Journeyman:** You learn to write `when`s that are neither too narrow (never triggered) nor too broad (triggered on every run). **Outgrow:** the habit of copying the formation's literal steps — refactor for reuse, name the *intent* of each step, not the exact wording.
- **Master:** You spot patterns across multiple runs and forge *composed* workflows that branch or call smaller ones. You prune the star map ruthlessly. **Measure:** the ratio of forge events to deprecation events — a healthy star map is being edited, not just appended to. You also learn to refuse the forge when the formation was actually a skill gap in disguise — and route the request to the Quartermaster for a new skill instead.

Keep a private ledger: workflow id, date forged, first re-use date, count of re-uses. A workflow unused for six months gets a yellow flag; one year, a red flag and a deprecation proposal.

## Gotchas

- **Forgetting the conformance close.** The most common defect. Every workflow *must* end `[... member steps, quartermaster-conformance member step, butler-report gate]`. If your last member step is anyone but the Quartermaster, the draft is broken.
- **Treating the report as a member step.** It is a `gate` — the Butler reads the run aloud to the user. Gates are review points, not work.
- **Forging from memory instead of the log.** You will invent steps that did not happen, or drop ones that did. Always read the Butler's log first; the log is the only honest source.
- **Conflating workflow and formation.** A formation is perishable; a workflow is permanent. If you catch yourself forking a workflow mid-run to handle a one-off detour, you are building a formation, not a workflow — let the Butler route it live instead.
- **Naming in the mundane register.** Workflows named *Step 1, Step 2* or *New Workflow 7* carry no gravity and signal no intent. The guild speaks in the Fallen-Sword register; honour it.
- **Skipping the artist.** A workflow without art is half a constellation. Always include a handoff so `gen-workflow-art.cjs` gets a prompt in the same pass as the JSON write.
- **Shipping unreviewed.** You draft; the Quartermaster writes. Do not touch `workflows.json` yourself. The guild gate rule holds: thinker plans, doer executes, nothing ships unreviewed.

## Versioning
Own skill. Bump `metadata.version` on any change (PATCH: wording/refs · MINOR: new mode/section · MAJOR: method contract change). Regenerate `VERSIONS.md` with `python3 star-alliance-skills/skillsmith/scripts/skill_registry.py write` after a bump, then `python3 build.py`.

## Cast validation after forge (1.3.0)

After writing a new workflow to `workflows.json`, the `workflow-banner-enforcer.py` Stop hook reads the cast from `steps[].actor` and enforces that at least one member reports for duty each turn. A workflow with an actor name that does not match a `guild-data.json` member ID will silently never satisfy the enforcer — the turn will loop forever with the member gate firing.

**Add to every forge close:**

```sh
# Verify all actors in the new workflow exist as guild members:
python3 -c "
import json
wfs = json.load(open('workflows.json'))['workflows']
members = {m['id'] for m in json.load(open('guild-data.json'))['members']}
for wf in wfs:
    for s in wf.get('steps', []):
        a = s.get('actor')
        if a and a not in ('you',) and a not in members:
            print(f'UNKNOWN ACTOR in {wf[\"name\"]}: {a}')
print('cast check done')
"
```

Gotcha: `the-butler`, `the-developer`, etc. — the `the-` prefix is the canonical member ID. Do not drop it or abbreviate it in the `actor` field. The enforcer normalizes via `_core()` (strips `the-`, lowercases), but `guild-data.json` lookup is exact-match.

## Changelog
- **1.3.0** — New §Cast validation after forge: documents the cast-actor lookup gap (unknown actor → enforcer loops forever), adds a one-shot validation command to run after every `workflows.json` write, and calls out the `the-` prefix invariant. Prevents harness lock-up from a typo in `actor`.
- **1.2.0** — Introduced the workflow **`class`** (`mutating` | `read-only`). The Quartermaster conformance-close is now required **only** for mutating workflows; read-only/advisory workflows end at the Butler report with the worker as the last step, and a ceremonial Quartermaster no-op close is now **rejected**. Stops force-fitting a conformance sweep onto conversation/research runs that change nothing.
- **1.1.0** — Documented the **structured weapon fields** on member steps (`thinker`, `doers` with parallel `count`, `ultra`), now enforced by `build.py` + `conformity_check.py` and rendered on the dashboard. Step authoring names weapons as fields, not only prose.
- **1.0.0** — Initial release. The Strategist's craft for distilling a finished run into a registered star-map workflow.
