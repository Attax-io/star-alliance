---
name: workflow-forge
description: "The Strategist's craft for distilling a finished run into a reusable star-map workflow in workflows.json. Recognise when a run is worth saving (a repeatable sequence not already on the map), draft the workflow object — id, name, icon, accent, category, tagline, a 'when' description, and steps[] (each step kind member or gate with actor, title, act, produces) — honouring the two hard guild standards (every workflow ends with the Butler 'report' gate; the last member step before it is the-quartermaster's conformance close), name the members and the weapon per step, then hand to the Quartermaster to register it and rebuild. Use when a run should become a repeatable workflow. Triggers: 'save this as a workflow', 'turn this run into a workflow', 'add this to the star map', 'crystallize this formation', 'register a workflow', 'workflow forge'. Differentiate from members-formation (the Butler's live routing — produces formations, not saved workflows) and skillsmith (skills, not workflows)."
metadata:
  version: 1.0.0
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

5. **Compose `steps[]`.** For each productive beat, output an object: `{ kind, actor, title, act, produces }`. Mark `kind` as `member` for work steps and `gate` for review/sign-off beats. Each member step names the recommended weapon (thinker weapon for plan/review, doer weapon `minimax` for execution). The gate rule applies — see below.

6. **Honour the two hard standards.**
   - The final step of every workflow is the Butler's `report` **gate** — the formal close, where the Butler reads the run back to the user.
   - The last `member` step before that report gate is the **Quartermaster's conformance close** — a `member` step (not a gate) where the Quartermaster checks the artefacts against guild standards and signs off.
   If your draft violates either rule, rewrite. Do not negotiate.

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

## Changelog
- **1.0.0** — Initial release. The Strategist's craft for distilling a finished run into a registered star-map workflow.
