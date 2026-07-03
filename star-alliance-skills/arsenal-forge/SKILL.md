---
name: arsenal-forge
description: "The Quartermaster's craft for tending the guild's Claude model roster (opus, sonnet, haiku) in models.json, or re-skinning a model's card. Set the model's identity (id, element, colour, visual metaphor, Fallen-Sword name), confirm it is one of the three Claude models, commission its art via the Designer (art-forge), then wire it into the model registry and card. The registry is Claude-only — a non-Claude model is refused. Use when a model card changes. Triggers: 'add a weapon', 'recruit a model', 'a new model joined', 're-skin this weapon', 'change a weapon role', 'arsenal forge'. Differentiate from art-forge (only the image) and members-formation (members, not weapons)."
metadata:
  version: 1.0.1
type: Skill

---
# Arsenal Forge — the Strategist's craft

This is your craft, Strategist: seating a Claude model in the guild arsenal, or re-skinning and re-roling one that already serves. A weapon here is a Claude model — the guild runs on exactly three: **opus**, **sonnet**, **haiku**. There is no non-Claude model in the arsenal. A member that fights without a properly forged model card is a soldier holding a name instead of a blade. A model that is not in the registry (`models.json`) is a phantom, and phantoms are forbidden. The craft is short but unforgiving: identity, role, slot, art, wire, gate.

## What it is / is not

- IS — naming the model (Claude model id, element, colour, visual metaphor, Fallen-Sword name), assigning its depth-role (deepest / workhorse / lightest), placing it in a priority slot, commissioning its art, and handing a complete model-card stub to the Quartermaster for wiring.
- IS NOT — drawing the image yourself. That is art-forge. The Designer paints; you commission.
- IS NOT — arranging the nine members into formations or loadouts. That is members-formation. You forge weapons; you do not seat soldiers.
- IS NOT — drafting a member's SKILL.md. A SKILL codifies a member's craft. A weapon card codifies a model. Different artefact, different forge.

## The craft

Follow these steps in order. Do not skip. Do not parallelize art and routability.

1. **Name and bind the model.** On a model-card stub write six fields: the canonical Claude model id as `models.json` holds it (`opus`, `sonnet`, `haiku` — the only three), the element (void, storm, frost, iron, ember, tide, aether, bone), the colour (one or two), the visual metaphor (crossbow, greatbow, siege-lance, ward-blade, mirror-shield, lantern, coil, brand), and the Fallen-Sword name — a single mythic noun that fits the metaphor (the Crossbow, the Greatbow, the Siege-Lance). Keep the name lowercase in code; capitalise in prose.

2. **Assign the depth-role and the slot.** Role is depth: **opus** is the deepest mind (the Architect's model), **haiku** the lightest and fastest (the Quartermaster's), **sonnet** the workhorse everyone else runs as. Slot follows the **arsenal-order rule**: order the three best-first by depth for the job, with **haiku last** as the lightest. Record both on the stub.

3. **Verify the model is in the registry before commissioning art.** The model must be one of the three Claude models named in `star-alliance-arsenal/models.json`. Nothing else is in the arsenal — there is no cloud/API bench. If a request names a non-Claude model, stop and refuse it: the guild is Claude-only. Do not commission art for a phantom. Return to step 1.

4. **Commission the art.** Hand the stub to the Designer via art-forge. Receive back the image path. You do not draw.

5. **Hand to the Quartermaster.** Deliver the complete stub plus the art path. The Quartermaster wires `models.json`, every member's `model:` frontmatter, and the model card with its depth icon (opus: deep-eye, sonnet: quill, haiku: spark). This is their work, not yours — but you must hand them a complete stub, not fragments.

6. **Run the gate and ship.** You lead this craft; the gate is yours. Confirm the model is a registry Claude model, the slot order, and art integrity. Then announce in the war-room log. Nothing ships unreviewed.

## Modes

**Greenfield seating.** A Claude model the guild has not yet carded (e.g. a new Claude tier joins the three). Steps 1 through 6 in full. Element, colour, metaphor, and name are all chosen fresh. The loud mode — the model appears in the registry the same day.

**Re-skin or re-role.** An existing model whose identity (element / colour / metaphor / name) or depth-role and slot has changed. Run steps 1, 2, 4, 5, 6. Skip the registry check only if the model id is unchanged; otherwise treat as greenfield. If the visual metaphor changed, the art must be re-commissioned. A re-wire is mandatory even when only the colour changes — identity drift is a lie on the model card.

## Sharpening the craft

- **Apprentice.** Can name a model and put it in a slot, but asks the Architect which model ids the registry holds. Commissions art before confirming the model is a registry Claude model about half the time. Forgets to re-wire on a re-skin.
- **Journeyman.** Holds the three-Claude-model registry in memory. Always confirms the model is in the registry before art. Slot ordering is right nine times out of ten. Begins to develop a personal palette — preferred element and metaphor pairings that read as a coherent set.
- **Master.** Knows the arsenal-order rule cold and slots a model without consulting it. Sees when a "re-skin" is secretly a re-role, or when a re-role is secretly a fresh seating that should be greenfield. Trains apprentices by reviewing their stubs *before* art is commissioned — phantoms caught at the stub cost nothing; phantoms caught after the art cost a Designer's afternoon. Maintains the guild's model lexicon so names do not collide.
- **Measure these.** Time from request to `models.json` updated (target: under a day greenfield, under an hour re-skin). Phantoms forged this quarter (target: zero). Model cards with stale identity (target: zero). Slot-ordering mistakes caught by the gate (a *rising* number is good — it means the gate is working). Re-skins that turned out to be greenfield in disguise (target: declining).
- **Outgrow.** Forging phantoms — carding a non-Claude model, which the guild forbids. Wrong slots. Identity drift between card and registry. Confusing arsenal-forge with art-forge or members-formation.

## Gotchas

- The arsenal-order rule is **best-first by depth for the job, with haiku last** as the lightest. "Best-first" is your call within the three Claude models, not a fixed ladder.
- The arsenal is exactly three: `opus`, `sonnet`, `haiku`. There is no non-Claude bench — a request to card any other model is refused, not slotted.
- Registry membership is checked **before** the art commission, not after. Never waste a Designer's cycles on a phantom.
- A re-skin that changes the model id is greenfield. A re-role that changes the slot still requires a re-wire and a re-card.
- Code names are lowercase nouns (`crossbow`, `greatbow`). Prose names take the article and the capital (`the Crossbow`, `the Greatbow`). Mixing them is a small rot that compounds.
- You plan, the Designer paints, the Quartermaster wires, the gate reviews. Stop at the handoff. Doing another member's job is how slots drift and phantoms slip through.

## Renaming or removing a model id (2026-07-01)

A model rename/removal is NEVER a manual multi-file hunt. Use the tool — it does every surface
in one pass and writes nothing half-written:

```sh
python3 tools/arsenal_rename.py OLD_ID NEW_ID        # dry-run, prints the diff
python3 tools/arsenal_rename.py OLD_ID NEW_ID --apply # commit-ready rewrite
```

`arsenal_rename.py` rewrites, in one command:

- registry keys + seats in `star-alliance-arsenal/models.json`
- all live code/config (hooks, generators, guild scripts, workflows, fallback dicts)
- the cost sidecar (`models-usage.json` — rekeyed)
- the art tile (`art/weapon-art/<id>.png` via `git mv`)
- doctrine prose (`CLAUDE.md` / `AGENTS.md` / `README.md`)

It **parse-validates each file before writing** — a bad edit never lands on disk, so no
half-written file. Skips historical, generated, and installed-mirror files (same exclusion set
the `HM` check uses). Prints the follow-up regen commands at the end.

After the rename (or after removing a model id entirely), run the regen chain:

```sh
python3 star-alliance-arsenal/gen_model_docs.py
python3 build.py
python3 tools/conformity_check.py
```

**Safety net:** `HM` (stale model id) in `conformity_check.py` catches any surface the tool or
a human missed. If `HM` fires after a rename, treat it as a bug in the tool — not as something
to silently hand-fix.

## Versioning
Own skill. Bump `metadata.version` on any change (PATCH: wording/refs · MINOR: new mode/section · MAJOR: method contract change). Regenerate `VERSIONS.md` with `python3 star-alliance-skills/skillsmith/scripts/skill_registry.py write` after a bump, then `python3 build.py`.

## Changelog
- **1.0.1** — New §Renaming or removing a model id (2026-07-01): documents `tools/arsenal_rename.py` as the canonical surface-wide renamer (registry, code/config, sidecar, art tile `git mv`, doctrine), states "a rename is never a manual multi-file hunt", lists the regen follow-up chain (`gen_model_docs.py` → `build.py` → `conformity_check.py`), and names `HM` as the safety net for surfaces the tool missed. Doc-only add → PATCH per user directive.
- **1.0.0** — Initial release. The Strategist's craft for seating/re-roleing a Claude model — identity, depth-role, wire to the registry and every member's `model:` frontmatter.
