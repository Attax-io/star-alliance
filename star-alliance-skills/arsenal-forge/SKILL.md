---
name: arsenal-forge
description: "The Strategist's craft for recruiting a new weapon (AI model) into the guild arsenal, or re-skinning / re-roleing an existing one. Set the weapon's identity (model id, element, colour, visual metaphor, Fallen-Sword name), assign its role under the thinker/doer/both schema and its priority slot under the arsenal-order rule (doers first, then thinkers and duals best-first, sonnet always last), commission the weapon art via the Designer (art-forge), then hand to the Quartermaster to wire it into summon.py routing, every member's loadout, and the weapon card with its role icon. The weapon must be routable — reachable by summon.py or Claude-native — or it is a phantom that will not fire. Use when a model joins or changes. Triggers: 'add a weapon', 'recruit a model', 'a new model joined', 're-skin this weapon', 'change a weapon role', 'arsenal forge'. Differentiate from art-forge (only the image) and members-formation (members, not weapons)."
metadata:
  version: 1.0.0
---

# Arsenal Forge — the Strategist's craft

This is your craft, Strategist: recruiting a new weapon into the guild arsenal, or re-skinning and re-roling one that already serves. A weapon here is an AI model — minimax, opus, sonnet, haiku, kimi, or any cloud/API model the guild can reach. A member that fights without a properly forged weapon is a soldier holding a name instead of a blade. A weapon that cannot be summoned is a phantom, and phantoms are forbidden. The craft is short but unforgiving: identity, role, slot, art, wire, gate.

## What it is / is not

- IS — naming the weapon (model id, element, colour, visual metaphor, Fallen-Sword name), assigning it a role (thinker / doer / both), placing it in a priority slot, commissioning its art, and handing a complete weapon-card stub to the Quartermaster for wiring.
- IS NOT — drawing the image yourself. That is art-forge. The Designer paints; you commission.
- IS NOT — arranging the nine members into formations or loadouts. That is members-formation. You forge weapons; you do not seat soldiers.
- IS NOT — drafting a member's SKILL.md. A SKILL codifies a member's craft. A weapon card codifies a model. Different artefact, different forge.

## The craft

Follow these steps in order. Do not skip. Do not parallelize art and routability.

1. **Name and bind the weapon.** On a weapon-card stub write six fields: the canonical model id as summon.py expects it (`minimax`, `opus`, `sonnet`, `haiku`, `kimi`, `gpt-4o`, `gemini-…`, etc.), the element (void, storm, frost, iron, ember, tide, aether, bone), the colour (one or two), the visual metaphor (crossbow, greatbow, siege-lance, ward-blade, mirror-shield, lantern, coil, brand), and the Fallen-Sword name — a single mythic noun that fits the metaphor (the Crossbow, the Greatbow, the Siege-Lance). Keep the name lowercase in code; capitalise in prose.

2. **Assign the role and the slot.** Role is thinker (plans and reviews), doer (executes), or both. Slot follows the **arsenal-order rule**: doers first, then thinkers and duals best-first by your judgement of capability, with **sonnet ALWAYS last**. A `both` weapon is treated as a thinker when forced to pick a slot. Record both on the stub.

3. **Verify routability before commissioning art.** The weapon must be reachable by `star-alliance-arsenal/summon.py` — either a cloud/API model with a known routable tag, or Claude-native (opus / sonnet / haiku). If it is neither, stop. Do not commission art for a phantom. Return to step 1 or refuse the recruitment.

4. **Commission the art.** Hand the stub to the Designer via art-forge. Receive back the image path. You do not draw.

5. **Hand to the Quartermaster.** Deliver the complete stub plus the art path. The Quartermaster wires summon.py, every member's loadout in priority order, and the weapon card with its role icon (thinker: quill/eye, doer: gauntlet, both: crossed). This is their work, not yours — but you must hand them a complete stub, not fragments.

6. **Run the gate and ship.** You are the thinker for this craft; the gate is yours. Confirm routability, slot order, art integrity, and that sonnet is last. Then announce in the war-room log. Nothing ships unreviewed.

## Modes

**Greenfield recruitment.** A new weapon the guild has not seen. Steps 1 through 6 in full. Element, colour, metaphor, and name are all chosen fresh. The loud mode — a new weapon appears in every member's loadout the same day.

**Re-skin or re-role.** An existing weapon whose identity (element / colour / metaphor / name) or role and slot has changed. Run steps 1, 2, 4, 5, 6. Skip the routability check only if the model id is unchanged; otherwise treat as greenfield. If the visual metaphor changed, the art must be re-commissioned. A re-wire is mandatory even when only the colour changes — identity drift is a lie on the weapon card.

## Sharpening the craft

- **Apprentice.** Can name a weapon and put it in a slot, but asks the Architect which model ids summon.py knows. Commissions art before verifying routability about half the time. Forgets to re-wire on a re-skin.
- **Journeyman.** Holds the routable model list in memory. Always checks routability before art. Slot ordering is right nine times out of ten. Begins to develop a personal palette — preferred element and metaphor pairings that read as a coherent set.
- **Master.** Knows the arsenal-order rule cold and slots a new weapon without consulting it. Sees when a "re-skin" is secretly a re-role, or when a re-role is secretly a new weapon that should be greenfield. Trains apprentices by reviewing their stubs *before* art is commissioned — phantoms caught at the stub cost nothing; phantoms caught after the art cost a Designer's afternoon. Maintains the guild's weapon lexicon so names do not collide.
- **Measure these.** Time from request to summon.py updated (target: under a day greenfield, under an hour re-skin). Phantoms forged this quarter (target: zero). Weapon cards with stale identity (target: zero). Slot-ordering mistakes caught by the gate (a *rising* number is good — it means the gate is working). Re-skins that turned out to be greenfield in disguise (target: declining).
- **Outgrow.** Forging phantoms. Wrong slots — thinker before doer, or sonnet not last. Identity drift between card and routing. Confusing arsenal-forge with art-forge or members-formation. Letting a doer become a silent thinker, or a thinker become an overworked doer.

## Gotchas

- The arsenal-order rule is **doers first, then thinkers and duals best-first, with sonnet ALWAYS last**. "Best-first" is your call, not a fixed ladder. The "sonnet last" part is not negotiable.
- `both` weapons slot as thinkers when the line must be drawn.
- Routability is checked **before** the art commission, not after. Never waste a Designer's cycles on a phantom.
- A re-skin that changes the model id is greenfield. A re-role that changes the slot still requires a re-wire and a re-card.
- Code names are lowercase nouns (`crossbow`, `greatbow`). Prose names take the article and the capital (`the Crossbow`, `the Greatbow`). Mixing them is a small rot that compounds.
- Sonnet is a thinker. Putting it in a doer slot burns context and breaks the gate.
- You plan, the Designer paints, the Quartermaster wires, the gate reviews. Stop at the handoff. Doing another member's job is how slots drift and phantoms slip through.

## Versioning
Own skill. Bump `metadata.version` on any change (PATCH: wording/refs · MINOR: new mode/section · MAJOR: method contract change). Regenerate `VERSIONS.md` with `python3 star-alliance-skills/skillsmith/scripts/skill_registry.py write` after a bump, then `python3 build.py`.

## Changelog
- **1.0.0** — Initial release. The Strategist's craft for recruiting/re-roleing a weapon — identity, thinker/doer role, wire to loadouts.
