---
type: Document
timestamp: 2026-06-27T10:27:03Z
---

# Fallen Sword Design Language

> **Mode of `design-language`.** Dark-fantasy MMORPG voice — the world of Erildath.
> Load via the dispatcher when a project wants the Fallen Sword tone. Triggers:
> "use the Fallen Sword design language", "Fallen Sword style", "Erildath".

A reference for the vocabulary, mechanics, and lore of Fallen Sword — a free-to-play
browser MMORPG by Hunted Cow Studios, running since 2006. Use this to give any project
the feel of Fallen Sword: old-school MUD roots, deep skill trees, item-driven combat,
and a dark fantasy world called Erildath.

---

## 1. World & Lore

### The World: Erildath

The ancient world of **Erildath** consists of four realms:

| Realm | Name | Home Of | Key Fortress |
|---|---|---|---|
| North Lands | Eredas | Humans | **Eribor** — mighty fortress, home of Iluthar |
| East Lands | Mora | Elves, dark mercenaries | **Lanslil** — elven fortress |
| West Lands | Eagos | Dwarves | **Mitoa** — dwarven citadel |
| South | The Withered Lands | Forces of darkness | **Mogroth** — the Ice Fortress of the Shadow Lord |

### Key Lore Terms

| Term | Meaning |
|---|---|
| **Iluthar** | The Sword of Light — the lost artifact, hidden after the fall of Eribor |
| **Shadow Lord** | The antagonist — ruler of the Withered Lands, unleashed hellish terrors |
| **Gadraen** | Old King of Eribor, slain by the Shadow Lord at the Battle of Erila |
| **Battle of Erila** | The climactic siege — 5,000 humans + 600 dwarves + 200 elves vs 200,000 greenskins |
| **Isudur** | An elegantly crafted elven blade, carried by the Royal Elven Guard |
| **Edalir** | The Dwarf King, lord of the Dark Forests of Eagos |
| **Lothar** | Mysterious elven caves west of Lanslil |
| **Liwen** | A narrow valley through the Shadow Mountains |
| **Dali** | A small port north of the Mogroth Ice Mountains, under greenskin control |
| **Elrad** | An elven outpost near the Greenskin Bastion of Amdar |
| **Mirdan** | Elven continent within the East Lands of Mora |

### The Story (for tone reference)

> The Shadow Lord devised a campaign to divide the united forces of light. Mercenaries
> besieged Lanslil. Five legions of greenskins invaded Eagos. Then, with elves and dwarves
> distracted, he launched his final siege against Eribor — where the free people rallied
> on the fields of Erila. Eribor fell. Iluthar, the Sword of Light, was lost. The Shadow
> Lord now unleashes his terrors upon Erildath. The sword remains hidden. The fate of the
> world is undecided.

**Tone:** Epic, dark fantasy, high stakes. Small bands against overwhelming odds. Lost
artifacts. Ancient prophecies. The world is dangerous and unresolved.

---

## 2. Core Mechanics & Vocabulary

### Player Stats

| Stat | Role |
|---|---|
| **Attack** | Determines hit chance — compared against opponent's defense |
| **Defense** | Reduces chance of being hit |
| **Armor** | Reduces damage taken when hit |
| **Damage** | How much HP you remove per hit |
| **HP** | Health — when it hits zero, you're defeated |
| **Stamina** | The resource that fuels everything — moving, casting skills, combat. Regenerates over time. |

### Combat System

- Turn-based. Each round, attacker rolls attack vs defender's defense.
- If hit, damage is applied (reduced by armor).
- Combat continues until one side's HP reaches zero.
- **PvE** — player vs creatures (the default).
- **PvP** — player vs player. Has bounties, gold loss, XP loss, and buff-stealing mechanics.

### Character Progression

- **Levels** — over 1,000 levels of content. Gaining XP from kills levels you up.
- **Skill Points** — earned per level, allocated to skills.
- **Skills (buffs)** — spells that temporarily boost stats. Three categories:
  - **Offense** — boost attack, damage, or weaken enemies (Rage, Berserk, Dark Curse, Wither)
  - **Defense** — boost defense, armor, HP, or absorb damage (Great Vigor, Enchanted Armor, Deflect)
  - **Special** — utility: XP/gold multipliers, stamina conservation, crafting, inventing (Doubler, Conserve, Find Item, Treasure Hunter)
- Skills have **dependency trees** — e.g., Berserk requires Rage + Fury first.
- Skills cost **stamina** to cast. You can cast on yourself or others.
- **Buff Market** — players trade buffs for gold. Low-level players buy high-level buffs.

### Key Special Skills (design language gold)

| Skill | What it does | Design pattern |
|---|---|---|
| **Doubler** | 2x/3x/4x stamina usage for 2x/3x/4x rewards | Risk/reward multiplier |
| **Conserve** | Chance to use no stamina in combat | Resource conservation |
| **Adept Learner** | +XP per kill | Progression accelerator |
| **Treasure Hunter** | +Gold per kill | Economy accelerator |
| **Find Item** | +Drop rate from creatures | Loot manipulation |
| **Last Ditch** | Chance to survive death once per combat | Safety net |
| **Light Foot** | Chance to use no stamina while moving | Map exploration efficiency |
| **Buff Master** | Chance to halve stamina cost of casting on others | Economy of generosity |
| **Extend** | Increases duration of skills you cast | Time management |
| **Brewing Master** | Increases potion duration | Consumable enhancement |

---

## 3. Items & Equipment

### Item Slots

Helmets, Armor, Gloves, Boots, Weapons, Shields, Rings, Amulets, Runes

### Item Rarities

| Rarity | Description |
|---|---|
| **Common** | Basic gear |
| **Rare** | Better stats, harder to find |
| **Unique** | Special effects, often from quests |
| **Legendary** | Top-tier, from legendary creatures |
| **Super Elite** | Dropped by Super Elite creatures |
| **Crystalline** | Special — cannot be repaired, degrades permanently |
| **Epic** | The highest tier |

### Item Sets

Items can form **sets** — wearing multiple pieces of the same set unlocks bonuses.
Skills like **Coordinated Attack**, **Smashing Hammer**, and **Armor Boost** reward
full-set play. This is a core design pillar: **gear synergy matters**.

### Item Enhancement

- **Hell Forge** — upgrade items through forge levels, increasing stats permanently.
- **Crafting** — items can be crafted from components and resources.
- **Inventing** — combine components to invent new items or potions. Skills like
  **Inventor** and **Inventor II** improve success rates.
- **Durability** — items lose durability in combat. **Unbreakable** skill prevents loss.
  **Crystalline** items can't be repaired.

---

## 4. Creatures & Bestiary

### Creature Types

Aquatic, Avian, Beast, Canine, Chest, Demon, Dragon, Dwarf, Elf, Feline, Golem,
Greenskin, Human, Magical, Mechanical, Mounted, Plant, Reptile, Undead, Vermin

### Creature Tiers

| Tier | Description |
|---|---|
| **Normal** | Standard creatures, found everywhere |
| **Champions** | Stronger variants |
| **Elites** | Tough, rare, better drops |
| **Legendaries** | Very tough, drop Legendary items |
| **Super Elites** | The toughest — require specialized skills (Super Elite Slayer) |
| **Titans** | Event-based massive creatures, guilds compete for kills |

---

## 5. World Areas (naming conventions)

Fallen Sword areas follow a pattern: **evocative 2-word names** mixing terrain +
mood. Examples from the game:

- **Krul Island**, **Lotmar Island**, **Marsa Island** — islands
- **Elya Desert**, **The Golden Desert**, **Arid Valley** — deserts/wastes
- **Dreg Marshes**, **Eldgar Swamps** — wetlands
- **Entora Mountains**, **Antediluvian Mountains**, **The Grumble Mountains** — mountains
- **Undying Forest**, **Pensar Forest**, **Dark Mist Forest**, **Forest of Ral** — forests
- **Ember Wastes**, **Wastes of Kruz** — wastelands
- **Glacier Front**, **Frozen Divide**, **The Ice Fields of Graupel** — frozen
- **Azlore Plains**, **Adriel Flats**, **Xanlin Plain** — plains
- **Garford Valley**, **Liwen Valley** — valleys
- **Castle Morbidstein**, **City of Karthak** — built structures
- **The Lost Ruins**, **The Chambers of Mount Caugha** — ruins/dungeons
- **Path of Shadows**, **Domain of Heitwar**, **Realm of Riangi** — thematic domains

**Naming formula:** [Adjective/Terrain] + [Geographic feature], or [Proper noun] +
[Feature]. Keep it dark, evocative, and slightly archaic.

---

## 6. Guilds & Social Systems

- **Guilds** — player organizations. Can own **relics** (world structures that give
  bonuses), build **structures** (guild upgrades), and buy **upgrades**.
- **Guild Conflicts** — organized PvP between guilds.
- **Mercenaries** — guilds can hire mercenaries for combat.
- **Relics** — capturable world locations that provide stat bonuses to the holding guild.
- **Titan Events** — guilds compete to kill Titans for exclusive rewards.

---

## 7. Economy

- **Gold** — the main currency, earned from creature kills and quests.
- **Auction House** — buy and sell items.
- **Buff Market** — buy and sell skill casts.
- **Trading** — direct player-to-player item/gold exchange.
- **Stamina** — the meta-currency. Everything costs stamina. It regenerates slowly,
  making it the real bottleneck. This is the core tension of the game.

---

## 8. Design Language Summary

When making something sound like Fallen Sword, use these patterns:

### Vocabulary Mapping

| Plain English | Fallen Sword Style |
|---|---|
| Task / job | Quest |
| Team | Guild |
| Effort / energy | Stamina |
| Skill / ability | Buff (or Skill) |
| Level up | Gain a level |
| Experience | XP |
| Money | Gold |
| Shop | Shop / Auction House |
| Meeting / coordination | Guild gathering |
| Assignment | Dispatch / quest |
| Specialist | Guild member |
| Manager / coordinator | The Butler (or guild orchestrator) |
| Tool / script | Skill / artifact |
| Upgrade | Hell Forge / enhance |
| Rare item | Legendary / Super Elite drop |
| Hard challenge | Super Elite / Titan |
| Event | Titan Event / community event |
| Map / area | Realm / area |
| Database / system | The Citadel / the structure |
| Code | The craft / the forge |
| Bug | Corruption / dark curse |
| Fix | Cleanse / purify |
| Deploy | Dispatch / send forth |
| Plan | Campaign / strategy |
| Big project | Conquering campaign |
| Clean up | Purify the workspace |
| Knowledge base | The codex / the library |
| Documentation | The scrolls / the tome |
| Report | Herald's report |
| Review | Inspection / audit |
| Risk | The Withered Lands / the shadow |

### Writing Style

- **Dark fantasy tone** — speak of shadows, light, swords, and realms.
- **Old-school MUD feel** — direct, text-driven, no frills.
- **Guild-centric** — everything is about the guild, the roster, the quest.
- **Stamina-conscious** — acknowledge that everything has a cost.
- **Epic but grounded** — small numbers matter (5,000 humans vs 200,000 greenskins),
  not abstract armies.
- **Item-driven** — gear and buffs define your power, not just levels.

### Example Re-skin

**Before (plain):**
> "I'll dispatch the Developer to fix the bug, then run cleanup."

**After (Fallen Sword):**
> "I shall dispatch the Developer to cleanse the corruption from our code.
> Once the forge is quiet, we purify the workspace."

**Before (plain):**
> "This is a big project. Let me break it into waves."

**After (Fallen Sword):**
> "This quest spans many realms. I shall chart the conquering campaign
> and divide it into waves, as the Strategist does."

---

## 9. Quick Reference: The Skill Tree (for design inspiration)

Skills unlock at level milestones: 1, 25, 75, 150, 200, 250, 300, 400, 500, 600, 700,
800, 900, 1000, 1200, 1400, 1600, 2000, 2500, 3000, 3500, 4000, 4500.

Each tier introduces 2-3 new skills per category. Dependencies create a tree. This is
the model for any progression system in Fallen Sword style:

1. **Start simple** — Rage (+attack), Great Vigor (+HP), Find Item (+drops)
2. **Build complexity** — Berserk (requires Rage+Fury), Deflect (auto-fail attackers)
3. **Create synergy** — Coordinated Attack (rewards full gear sets), Guild Berserker
4. **Endgame shifts** — Relentless, Critical Strike, Guild Berserker (conflict-only)

The design lesson: **progression is a tree, not a line. Early choices gate later power.**