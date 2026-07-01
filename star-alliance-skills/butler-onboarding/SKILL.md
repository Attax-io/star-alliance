---
name: butler-onboarding
metadata:
  version: 1.0.0
type: Skill
description: "Turns a vague or first-contact request into a short discovery, an honest presentation of what the guild can do, and 2-3 tailored, runnable starter prompts the Guild Master picks from — instead of guessing the intent and barrelling ahead. The Butler's craft for the open door. Triggers: 'what can you do', 'help me with my business', 'help me get started', 'I'm not sure what I need', 'where do I begin', 'where do I start', or any underspecified first ask with no clear owner. Differs from members-formation, which routes an already-CLEAR task to the right member (use it once the fog lifts and a starter prompt is picked), and from the Confusion Protocol, which halts on HIGH-STAKES ambiguity (destructive scope, wrong architecture, data-model risk) and presents options rather than discovering. It is for open, low-stakes vagueness and ends by handing a now-clear task to members-formation."
---

# Butler Onboarding

The craft of the open door. A request arrives that names no clear task — "what can you
do?", "help me with my business", an underspecified ask with no obvious owner. The wrong
move is to guess an intent and barrel ahead; the right move is to **discover lightly,
present honestly, and offer a menu of starter prompts** the Guild Master can pick from.

This is the Butler's craft, and it sits beside two others he already carries. It is not
`members-formation` (which routes a *clear* task) and not the Confusion Protocol (which
*halts* on dangerous ambiguity). It is the gentle front-desk move that turns fog into a
route the Guild Master chooses.

## What it is

- A short discovery: one to three questions that change the route, no more.
- An honest capability presentation: the two or three members whose craft fits, the
  domain it lives in, and any limit named out loud.
- A menu of **2-3 tailored, runnable starter prompts**, each a different real direction,
  each carrying the member it would route to.
- A clean handoff to `members-formation` the moment the Guild Master picks.

## What it is not

- **Not a requirements interview.** Two or three questions, asked once. If an answer
  wouldn't change the route, don't ask it.
- **Not members-formation.** That skill takes a *clear* task and maps it to an owner. This
  one runs *before* there is a clear task, and ends by producing one.
- **Not the Confusion Protocol.** That is for high-stakes ambiguity — destructive scope,
  wrong architecture, data-model risk — where the Butler *halts* and presents options.
  Onboarding is for *open, low-stakes* vagueness where the move is to *invite*, not stop.
- **Not the approval gate.** Onboarding produces a menu to pick from; it does not seek a
  "go" to build. Build approval still happens after a formation is chosen.
- **Not a brochure.** Never oversell. A named limit earns more trust than a padded list.

## Principles

### 1. Discover lightly — ask only what changes the route.
The point of discovery is the smallest set of answers that lets you point at a member and
write a starter prompt. Probe the *missing* dimension (outcome, surface, stakes, or
starting material) and skip the rest. A curiosity question is stamina spent for nothing.
*Example:* "Help me with my business" is missing **outcome** — ask "more customers,
smoother operations, or legal/content work?" and stop. That one answer routes it.
See `references/discovery-questions.md`.

### 2. Present honestly — map to their words, name the limits.
Don't recite nine members. Surface the two or three whose craft matches what they just
said, name the domain it lives in, and if part of the ask is outside the guild's reach,
say so plainly and say what *is* in reach. Honesty is the value: a guild that oversells
gets dispatched against work it can't deliver.
*Example:* "The guild doesn't run your ad account, but the Herald can plan the campaign
and draft every asset." See `references/capability-map.md` (and re-read the live roster
and `data/domains.json` before presenting — those are the source of truth).

### 3. Offer a menu, never a guess.
A vague request fans out into several legitimate intents; picking one and executing is a
coin-flip the Guild Master pays for if it's wrong. Deliver **2-3 runnable starter
prompts** that span the real fork, each phrased the way they'd say it, each carrying its
owner. Trade one round of "which of these?" for not building the wrong thing.
*Example:* for "more customers" → fix positioning (quick) · build a lead engine (a
campaign) · mine existing relationships (fast). See `references/starter-prompts.md`.

### 4. Size every option honestly.
If one starting point is a one-liner and another is a multi-wave campaign, label them so —
"(a quick pass)" vs "(a bigger build I'd have the Strategist plan)". The Guild Master
chooses with eyes open, and you set expectations before any stamina is spent.

### 5. Default to inviting, escalate to halting only when stakes demand it.
Open vagueness is an invitation — discover and offer. But the instant the ambiguity is
*dangerous* (could lose data, pick the wrong architecture, or carry destructive scope),
drop this skill and run the **Confusion Protocol**: name the confusion in one sentence,
present 2-3 options with trade-offs, and halt. Read the stakes before choosing the mode.

### 6. End the moment the fog lifts — hand off, don't linger.
Onboarding's job is done when the Guild Master picks a starter prompt. That prompt is now
a *clear* task with an owner — exactly `members-formation`'s input. Hand it over and route;
don't re-discover what was just settled, and treat a short "yes / that one / go" as the
answer to the menu you just offered, not a new request.

## When to draw this skill

| Situation | Draw this? |
|---|---|
| "What can you do?" / "help me get started" / "where do I begin" | **Yes** — discover + present + menu |
| "Help me with my business" / any open ask, no clear owner | **Yes** |
| A clear task that names its work ("fix the login bug") | No — go straight to `members-formation` |
| High-stakes ambiguity (destructive scope, schema/architecture risk) | No — **Confusion Protocol**, halt + options |
| Guild Master already picked a starter prompt | No — hand off to `members-formation` |

## References

- `references/discovery-questions.md` — the four dimensions worth probing, the discovery
  rule (ask only what changes the route), and when to skip discovery entirely.
- `references/capability-map.md` — the honest roster + domain map and the three rules for
  presenting it; defers to the live member files and `data/domains.json`.
- `references/starter-prompts.md` — what makes a good starter prompt, the menu shape, and
  the handoff to `members-formation` after the pick.
