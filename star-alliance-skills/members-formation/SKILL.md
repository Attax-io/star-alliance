---
name: members-formation
description: "The Butler's routing method — turn any mission into a formation: which member owns each slice, whether members work simultaneously or step by step, and where the gates fall. Use when the Butler receives an order and must decide who handles what and in what arrangement. Triggers: 'route this', 'who should handle this', 'form the team', 'distribute the work', 'can these run in parallel', 'coordinate the members', 'plan the dispatch', or any request touching more than one craft. Produces a formation (members + arrangement + gates) that, when the same sequence is worth repeating, the Quartermaster crystallizes into a star-map workflow in workflows.json. Skills are how each member works; workflows are how members work together; this skill is how the Butler decides the arrangement — it produces workflows, it is not one."
metadata:
  version: 1.0.2
---

# Members Formation — the Butler's routing method

This is **how the Butler decides who works, and in what arrangement.** It is the Butler's one
dedicated craft: he is not a specialist, he is the router.

Keep the three layers separate — never mix them:

- **Skills** = how *one member* works (their dedicated craft).
- **Workflows** = how *members work together* — the saved star map (`workflows.json`).
- **This skill** = the Butler's *method* for producing a **formation** for a single mission. A
  formation is a live decision. When the same formation proves worth repeating, the Butler hands
  it to the Quartermaster, who crystallizes it into a star-map workflow. **This skill produces
  workflows; it is not one.**

## What a formation is

A **formation** is the answer to three questions for one mission:

1. **Who** — which member owns each slice of the work.
2. **Arrangement** — do members work **simultaneously** (parallel) or **step by step**
   (sequential), and where does each hand off to the next.
3. **Gates** — where *you* (the Guild Master), the Quartermaster, and the Butler check the work.

Output of the method = a formation: a short ordered list of `member → does what → produces what`,
with the arrangement and gates marked. That is what the Butler dispatches against.

## The roster you route to — one dedicated craft each

Route by craft. Each member owns exactly one craft; that is the whole point of the guild. If a
slice doesn't match a craft below, it's the Butler's own (decompose it further or ask the user).

| Member | Dedicated craft | Route a slice here when… |
|---|---|---|
| **The Architect** | System & database architecture, domain modeling | it shapes schema, data flow, or structure — the foundations |
| **The Developer** | Writing code, fixing bugs, implementation, dev servers, tooling, knowledge graphs | code must be written/changed/debugged, the environment or tooling run, or a graph built |
| **The Designer** | UI/UX, visual quality, brand, skill/heraldry art | anything user-facing or visual — the guild's only artisan |
| **The Strategist** | Multi-wave campaign planning & deep synthesis | the mission is too big for one pass, or needs heavy up-front planning |
| **The Translator** | Legal codex, law translation, multi-locale content | laws or multilingual content must be loaded or translated |
| **The Herald** | Marketing, growth, demand gen — content/SEO, brand, email, social/paid | the firm needs leads, positioning, content, or distribution |
| **The Merchant** | Investment & market research (read-only) | a market/investment question — analysis only, no code |
| **The Quartermaster** | Skills, guild upkeep, conformance, crystallization | skills need managing, the repo needs verifying, or a formation must be saved |

The **Butler** never appears as a routing target — he is the router. He also never does the
specialist work himself.

## The method — five steps

1. **Decompose** the mission into atomic **slices** — each slice is one craft's worth of work.
2. **Map** each slice to the member who owns that craft (table above).
3. **Decide the arrangement** for each pair of slices — parallel or sequential (next section). This
   is the heart of the formation.
4. **Place the gates** — approval, certify, report (see *Gates*).
5. **Brief** each member — a scoped dispatch: what they get, what they own, what they produce.

## Parallel vs. sequential — the heart

Two members may work **simultaneously** only when **all three** hold:

- **Independent inputs** — neither needs the other's output to start.
- **Disjoint surfaces** — they don't write the same files/tables (no contention).
- **No ordering constraint** — correctness doesn't depend on who finishes first.

If **any** fails → **sequential**: the output of A becomes the input of B, and A must finish first.

**Quick test:** ask *"could B start right now, with nothing from A?"* — yes to all three ⇒ parallel;
any no ⇒ sequential.

| Situation | Arrangement |
|---|---|
| Designer mocks the UI **while** Architect models the schema (different surfaces, independent) | **Parallel** |
| Developer builds against a design that doesn't exist yet | **Sequential** — Designer → Developer |
| Translator does EN **while** Translator does FR (same craft, independent locales) | **Parallel** (fan-out) |
| Quartermaster verifies a build before it exists | **Sequential** — build → verify |

When unsure, default to **sequential** — a wrong parallel call causes rework; a wrong sequential
call only costs a little time.

## Formation patterns — the vocabulary

| Pattern | Shape | Use when |
|---|---|---|
| **Solo** | one member | the mission is one craft |
| **Relay** | A → B → C (sequential) | each step needs the prior step's output |
| **Parallel** | A ∥ B (simultaneous) | slices are independent and disjoint |
| **Fan-out / Fan-in** | split → A ∥ B ∥ C → merge | one input splits into independent slices, then results recombine |
| **Gated relay** | A → ⟨gate⟩ → B | a relay where a checkpoint must pass before the next member starts |

Most real missions are a **gated relay with a parallel middle** (plan → design ∥ architect →
build → verify).

## The gates — guild standard, baked in

Three gates, three owners:

- **approval** — *you* approve the brief before work starts.
- **certify** — *the Quartermaster* certifies the plan/design is buildable before construction.
- **report** — *the Butler* reports the finished mission in plain English. **Mandatory on every
  formation** (guild decision #23).

And one fixed closing step: the **last member before the report is always the Quartermaster**,
running a conformance pass (guild decision #26).

So every formation the Butler crystallizes **must end**:
`… → the-quartermaster (conformance) → ⟨report gate⟩`. Bake this in from the start — it is what
keeps a crystallized formation conformant.

## Crystallizing a formation into a star-map workflow

When a formation is **repeatable** (the same sequence will serve future missions), the Butler
**hands it to the Quartermaster** to save into `workflows.json`. The Butler does **not** edit
`workflows.json` himself — authoring the star map is the Quartermaster's craft (`skillsmith`).

The schema, the conformance rules that keep `conformity_check.py` green, and a full worked example
live in [`references/crystallize-to-workflow.md`](references/crystallize-to-workflow.md). The
short version:

- steps are `kind: member` or `kind: gate`;
- a member step = `{ actor, title, act, produces }`, actor ∈ roster ∪ `you`;
- a gate = `{ gate: approval | certify | report, label }`;
- it **ends with a `report` gate**, and the **last member step is `the-quartermaster`**.

One-off formations are **not** crystallized — the Butler says so in his report and moves on.

## How the Butler runs it

1. **Restate the order** in plain English so you both agree on the quest.
2. **Run the method** → produce the formation (who · arrangement · gates).
3. **Confirm** with the user at the approval gate — unless the route is obvious.
4. **Dispatch** per the arrangement: launch parallel slices together; relay sequential ones with a
   clean hand-off brief each time.
5. **Close** with the Quartermaster's conformance pass, then deliver the plain-English **report** —
   and **flag whether this formation should become a star-map workflow** (name the steps and who
   owns each) so the Quartermaster can crystallize it, or say plainly that it was a one-off.

A compact worked example (mission → formation → crystallized workflow) is in
[`references/crystallize-to-workflow.md`](references/crystallize-to-workflow.md).

## Versioning

Own skill. Bump `metadata.version` on any change (PATCH: wording/refs · MINOR: new pattern/section ·
MAJOR: method contract change). Regenerate `VERSIONS.md` with
`python3 skillsmith/scripts/skill_registry.py write` after a bump, then `python3 build.py`.

## Changelog
- **1.0.2** — Recruited the-herald (marketing): added the Herald to the roster table — leads, positioning, content, and distribution route to him.
- **1.0.1** — Folded the-engineer into the-developer in the roster table: dev servers, tooling, and knowledge graphs now route to the Developer; removed the Engineer row.
- **1.0.0** — Initial release. Five-step routing method, parallel-vs-sequential rule, five formation
  patterns, the three gates + Quartermaster-close baked in, and the hand-off that crystallizes a
  repeatable formation into a conformant `workflows.json` star map.
