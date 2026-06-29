---
name: members-formation
description: "The Butler's routing method — match an incoming request to the right star-map workflow in `workflows.json` and follow it. The Butler does not assemble a fresh team per mission; each workflow already names its members and their arrangement, so routing is a *selection* problem: read the request, scan the workflows' triggers, pick the one that fits, follow its steps. Use when the Butler receives an order and must decide which workflow to run. Triggers: 'route this', 'which workflow', 'who should handle this', 'how do we run this', 'pick the workflow', 'what's the play', or any incoming order that must be matched to a procedure. Only when NO existing workflow fits does the Butler fall back to forming a fresh formation (members + arrangement + gates) and hand it to the Quartermaster's Workflow Forge to crystallize. Workflow-selection first; formation-building is the fallback."
metadata:
  version: 1.4.0
type: Skill

---
# Members Formation — the Butler's routing method

This is **how the Butler decides which workflow to run.** It is the Butler's one dedicated craft:
he is not a specialist, he is the router.

The key correction: **the Butler does not choose members — he chooses the workflow.** Each
workflow in `workflows.json` already names its members, their order, and its gates. So at routing
time the Butler is not assembling a team from scratch; he is **matching the request to a saved
procedure** and following it. Picking the right workflow *is* the routing decision.

Keep the three layers separate — never mix them:

- **Skills** = how *one member* works (their dedicated craft).
- **Workflows** = how *members work together* — the saved star map (`workflows.json`). Each one is
  a fixed cast + arrangement + gates.
- **This skill** = the Butler's *method* for **selecting** the workflow that fits a request — and,
  only when none fits, for **forming a fresh formation** to hand off for crystallization.

## Fast-Route Shortcuts

For common task types, dispatch immediately — no deliberation needed:

| Task involves... | Route to | Never do... |
|---|---|---|
| Skill create / upgrade / delete / sync / wire | **Quartermaster — immediately** | Manual bash, manual file edits |
| build.py / conformity_check / publish_profiles / skillsmith | **Quartermaster — immediately** | Run these yourself from Butler |
| Version bumps, SKILL.md edits, member file edits | **Quartermaster** | Edit directly from main session |
| Code bugs, new features, tooling, dev server | Developer | |
| DB schema, domain model, migrations, Supabase DDL | Architect | |
| UI/UX, visual polish, design system | Designer | |
| Marketing, content, SEO, growth | Herald | |
| Trading, market analysis, portfolio | Merchant | |
| Legal, law translation, contracts | Translator | |
| Multi-wave campaigns, routing decisions, performance | Strategist | |

**Rule:** If the task mentions a skill name, a version bump, build.py, conformity_check, publish_profiles, or skillsmith — stop, dispatch to QM. Do not attempt it in the main session first.

## The primary method — workflow selection (five steps)

This is what the Butler does on almost every order.

1. **Restate the order** in plain English so you both agree on the quest.
2. **Read the request's shape** — what craft(s) does it touch, how big is it, is it build / design /
   legal / research / hygiene / comms / guild-self?
3. **Scan the workflows** in `workflows.json` — read each entry's `when` trigger and `tagline`.
   Match the request against them.
4. **Pick the workflow** whose `when` fits best. If two fit, prefer the **narrower / cheaper** one
   (a Quick Fix over a Standard Mission when the work is genuinely small).
5. **Follow its steps** — dispatch each member step in order, honor each gate, do not improvise a
   different path. The workflow already decided who works and in what arrangement; the Butler's job
   is to run it faithfully.

**If exactly one workflow fits → run it.** **If several fit → pick the narrowest and say why.**
**If none fits → fall back to formation-building (below) — do not force a bad match.**

## The workflow catalogue — what to match against

Match by request shape. (Authoritative list is always `workflows.json`; this is the map.)

| Category | Workflows | Route a request here when… |
|---|---|---|
| **Build & Fix** | Quick Fix · Standard Mission · Architecture Build · Bug Cycle · Security Sweep | code is written/changed/debugged, structure is shaped, or a vuln is hunted |
| **Design** | Design Sprint · Art Forge | anything user-facing or visual — UI, brand, heraldry, tiles |
| **Legal** | Legal Codex · Legal Drafting · Tool Forge · Law Harvest | laws are loaded/translated, legal docs drafted, or legal tooling built |
| **Research & Intel** | Market Recon · Brand Audit · Relationship Intel | a read-only question — market, brand, or relationship analysis |
| **Guild Self** | Skill Forge · Arsenal Forge · Strategic Audit · Workflow Forge | the guild improves itself — skills, weapons, audits, new workflows |
| **Hygiene & Release** | Compliance Audit · Hygiene Rotation · Guild Log Sync · Release Train | cleanup, conformance, log upkeep, or shipping a version |
| **Comms & Automation** | Comms Triage · Standing Watch | inbound comms are triaged or a watch runs on a schedule |

Each workflow already encodes its members. The Butler reads the `when`, not the roster.

## When no workflow fits — fall back to forming a formation

Only when the request matches **no** existing workflow does the Butler stop selecting and start
**forming**. A **formation** is a fresh, live answer to three questions for one mission:

1. **Who** — which member owns each slice of the work.
2. **Arrangement** — do members work **simultaneously** (parallel) or **step by step** (sequential),
   and where each hands off.
3. **Gates** — where you (the Guild Master), the Quartermaster, and the Butler check the work.

The Butler does **not** silently improvise this and run it. Per the routing gate: **a missing
workflow is a STOP** — the Butler tells you no workflow fits, forms the candidate formation, and
hands it to the Quartermaster's **Workflow Forge** to crystallize into `workflows.json` *before*
the work runs. The roster and the formation method below are the tools for that fallback.

### The roster — one dedicated craft each (for the fallback only)

| Member | Dedicated craft | Give a slice here when… |
|---|---|---|
| **The Architect** | System & database architecture, domain modeling | it shapes schema, data flow, or structure — the foundations |
| **The Developer** | Writing code, fixing bugs, implementation, dev servers, tooling, knowledge graphs | code must be written/changed/debugged, the environment run, or a graph built |
| **The Designer** | UI/UX, visual quality, brand, skill/heraldry art | anything user-facing or visual — the guild's only artisan |
| **The Strategist** | Multi-wave campaign planning & deep synthesis | the mission is too big for one pass, or needs heavy up-front planning |
| **The Translator** | Legal codex, law translation, multi-locale content | laws or multilingual content must be loaded or translated |
| **The Herald** | Marketing, growth, demand gen — content/SEO, brand, email, social/paid | the firm needs leads, positioning, content, or distribution |
| **The Merchant** | Investment & market research (read-only) | a market/investment question — analysis only, no code |
| **The Quartermaster** | Skills, guild upkeep, conformance, crystallization | skills need managing, the repo verified, or a formation saved |

The **Butler** is never a routing target — he is the router, and never does specialist work himself.

### Parallel vs. sequential — the heart of a formation

Two members may work **simultaneously** only when **all three** hold:

- **Independent inputs** — neither needs the other's output to start.
- **Disjoint surfaces** — they don't write the same files/tables (no contention).
- **No ordering constraint** — correctness doesn't depend on who finishes first.

If **any** fails → **sequential**: A's output is B's input, and A must finish first.

**Quick test:** *"could B start right now, with nothing from A?"* — yes to all three ⇒ parallel; any
no ⇒ sequential. When unsure, default to **sequential** — a wrong parallel call causes rework; a
wrong sequential call only costs a little time.

### Formation patterns — the vocabulary

| Pattern | Shape | Use when |
|---|---|---|
| **Solo** | one member | the mission is one craft |
| **Relay** | A → B → C (sequential) | each step needs the prior step's output |
| **Parallel** | A ∥ B (simultaneous) | slices are independent and disjoint |
| **Fan-out / Fan-in** | split → A ∥ B ∥ C → merge | one input splits into independent slices, then recombines |
| **Gated relay** | A → ⟨gate⟩ → B | a relay where a checkpoint must pass before the next member starts |
| **Swarm** | A×N → A (inline) | N instances of ONE member, disjoint slices, followed by inline integration |

Most real missions are a **gated relay with a parallel middle** (plan → design ∥ architect → build
→ verify).

### Swarm — recognize and route; do NOT decompose here

The **swarm** arrangement is recognized at routing time but **never decomposed here.** When a step
in a matched workflow carries a `swarm` object, or when a fallback formation calls for N parallel
instances of one member working on disjoint slices, the Butler **delegates entirely** to
`[[decompose-and-swarm]]` — that skill owns every decomposition detail (worthiness gate, scout,
slice-cutting, per-instance brief, fan-out, per-slice critic, integration).

**members-formation's role with swarm:**
- Read a `swarm` step in `workflows.json` → recognize it as a swarm stage → hand control to
  `decompose-and-swarm`.
- For a fallback formation, if the request is big enough and the slices are disjoint → mark the
  step as a swarm candidate → hand the decomposition to `decompose-and-swarm`.
- Never write the briefs, cut the slices, or run the fan-out yourself.

Keep the decomposition logic OUT of members-formation. Routing chooses swarm as a pattern;
`decompose-and-swarm` executes it.

## The gates — guild standard, baked into every workflow

Three gates, three owners:

- **approval** — *you* approve the brief before work starts.
- **certify** — *the Quartermaster* certifies the plan/design is buildable before construction.
- **report** — *the Butler* reports the finished mission in plain English. **Mandatory on every
  formation** (guild decision #23).

And one fixed closing step: the **last member before the report is always the Quartermaster**,
running a conformance pass (guild decision #26).

So every formation the Butler hands off to be crystallized **must end**:
`… → the-quartermaster (conformance) → ⟨report gate⟩`. The existing workflows already obey this —
when matching, the Butler trusts that tail; when forming a fallback, he bakes it in from the start.

## Crystallizing a fallback formation into a star-map workflow

When the fallback formation is **repeatable** (the same sequence will serve future missions of this
shape), the Butler **hands it to the Quartermaster** to save into `workflows.json` via **Workflow
Forge**. The Butler does **not** edit `workflows.json` himself — authoring the star map is the
Quartermaster's craft (`skillsmith`).

The schema, the conformance rules that keep `conformity_check.py` green, and a full worked example
live in [`references/crystallize-to-workflow.md`](references/crystallize-to-workflow.md). The short
version:

- steps are `kind: member` or `kind: gate`;
- a member step = `{ actor, title, act, produces }`, actor ∈ roster ∪ `you`;
- a gate = `{ gate: approval | certify | report, label }`;
- it **ends with a `report` gate**, and the **last member step is `the-quartermaster`**.

A one-off fallback is **not** crystallized — the Butler says so in his report and moves on.

## How the Butler runs it — the full loop

1. **Restate the order** in plain English so you both agree on the quest.
2. **Select the workflow** — scan `workflows.json`, match the request's shape to a `when` trigger,
   pick the best fit. **This is the routing decision.**
3. **If a workflow fits → follow its steps**, honoring every gate, in arrangement. Confirm at the
   approval gate unless the route is obvious.
4. **If no workflow fits → STOP** — tell the Guild Master, form the candidate formation (who ·
   arrangement · gates), and hand it to **Workflow Forge** to crystallize before running the work.
5. **Close** with the Quartermaster's conformance pass, then deliver the plain-English **report** —
   and, for a fallback, flag whether the new formation should stay on the star map or was a one-off.

A compact worked example (request → no fit → formation → crystallized workflow) is in
[`references/crystallize-to-workflow.md`](references/crystallize-to-workflow.md).

## Reading a step's execution tags (`exec` · `parallel`)

Each workflow step now carries how it should run — honor it:

- **`exec: "spawn"`** — dispatch this step to a **real helper** (Agent tool, `subagent_type`
  = the step's `actor`), with the step's intent as the brief. This is every specialist step.
- **`exec: "inline"`** — the Butler does this himself in the main thread (his own framing,
  the approval gate, the closing report). He never spawns himself.
- **`parallel: true`** — this step fans out to **several helpers at once**. Spawn them in a
  single message (multiple Agent calls) so they run concurrently, then collect every
  result. This is the swarm win — independent work running side-by-side, not in series.

Steps **without** these tags keep the default: specialist → spawn, Butler/you → inline,
and run in listed order. The build→verify→confirm chain is sequential by design — never
parallelize a verify or a conformance step ahead of the work it checks.

## Failure-mode routing — route the stuck, not just the start

The Butler routes the START of work by workflow. He also routes FAILURES: when a member or
agent gets stuck mid-work, the stuck has a deterministic owner (bug → developer, missing spec →
architect, scope overflow → strategist, vague intent → `butler-onboarding`, high-stakes ambiguity →
HALT/Confusion Protocol, no workflow → Workflow Forge, missing role → Guild Recruitment). A blocked
agent DECLARES the failure mode instead of silently retrying the same blind action. Full table:
[`references/failure-mode-routing.md`](references/failure-mode-routing.md).

## Versioning

Own skill. Bump `metadata.version` on any change (PATCH: wording/refs · MINOR: new pattern/section ·
MAJOR: method contract change). Regenerate `VERSIONS.md` with
`python3 skillsmith/scripts/skill_registry.py write` after a bump, then `python3 build.py`.

## Changelog
- **1.4.0** — New **Fast-Route Shortcuts** table right after the three-layers framing: a one-glance
  dispatch cheatsheet (skill name / build.py / conformity_check / publish_profiles / skillsmith /
  version bumps / SKILL.md edits → Quartermaster immediately; code → Developer; schema → Architect;
  UI → Designer; marketing → Herald; trading → Merchant; legal → Translator; campaigns →
  Strategist). Hard rule: if the task mentions a skill name, version bump, build.py, conformity_check,
  publish_profiles, or skillsmith, stop and dispatch to QM — never attempt it in the main session.
  New section → MINOR.
- **1.3.0** — New **swarm arrangement** row in the formation patterns table + "Swarm — recognize
  and route" section: members-formation recognizes `swarm` as a pattern and delegates all
  decomposition to `[[decompose-and-swarm]]`; no decomposition logic lives here. New pattern row
  + new section → MINOR.
- **1.2.0** — New **failure-mode routing** section + `references/failure-mode-routing.md`: a table mapping every mid-work stuck (bug, missing spec, scope overflow, vague intent, high-stakes ambiguity, doer miss, no-workflow, missing-role) to a deterministic owner, so a blocked agent declares the failure mode instead of silently retrying. New section → MINOR.
- **1.1.1** — Workflow-catalog fix: the Hygiene & Release row now lists **Compliance Audit** (the merged Conformity Sweep + OKF Tidy) instead of the old "Conformity Sweep". Wording/refs → PATCH.
- **1.1.0** — Reframed around the Butler's true job: **workflow selection, not member assembly**.
  Workflow-matching is now the primary five-step method (scan `workflows.json` `when` triggers →
  pick the fit → follow it); formation-building (decompose → map → arrange) demoted to the explicit
  "no workflow fits → Workflow Forge" fallback. Added the workflow catalogue table.
- **1.0.2** — Recruited the-herald (marketing): added the Herald to the roster table — leads, positioning, content, and distribution route to him.
- **1.0.1** — Folded the-engineer into the-developer in the roster table: dev servers, tooling, and knowledge graphs now route to the Developer; removed the Engineer row.
- **1.0.0** — Initial release. Five-step routing method, parallel-vs-sequential rule, five formation
  patterns, the three gates + Quartermaster-close baked in, and the hand-off that crystallizes a
  repeatable formation into a conformant `workflows.json` star map.
</content>
</invoke>
