# Crystallizing a formation into a star-map workflow

> **This is the fallback path.** The Butler's primary job is to *select* an existing workflow from
> `workflows.json` and follow it — see `SKILL.md`. He only forms a fresh formation when **no**
> existing workflow fits the request. This file covers that case: turning a fresh formation into a
> new, conformant workflow via **Workflow Forge**.

A **formation** is a live routing decision the Butler makes for one mission when nothing on the star
map fits. A **workflow** is a formation that proved worth keeping — saved into `workflows.json` so
the guild can run it again without re-deciding. This file is the bridge: how a formation becomes a
conformant workflow.

> The Butler **produces** the formation and **hands it off**. The Quartermaster (via `skillsmith`)
> **writes** `workflows.json` and regenerates the dashboard. Keep that split — the Butler does not
> hand-edit the star map.

## When to crystallize

Crystallize only when **all** hold:

- the same sequence of members + arrangement will serve **future** missions of this shape;
- it isn't already on the star map (check the existing `workflows.json` ids);
- it has a clear trigger ("use this when…") a future Butler can match against.

If it was a one-off, **don't** — the Butler just says so in his report.

## The schema

Mirror the existing entries in `workflows.json`. One workflow:

```json
{
  "id": "kebab-case-id",
  "name": "Title Case Name",
  "icon": "🛰️",
  "accent": "cyan",
  "tagline": "One line on what this formation is for.",
  "when": "Use this when … (the trigger a future Butler matches).",
  "steps": [ /* ordered member + gate steps */ ]
}
```

A **member** step:

```json
{ "kind": "member", "actor": "the-designer", "title": "Design the Interface",
  "act": "What this member does, in one sentence.", "produces": "design spec" }
```

A **gate** step:

```json
{ "kind": "gate", "gate": "approval", "label": "What the gate checks and who clears it." }
```

- `actor` ∈ the roster (`the-architect`, `the-developer`, `the-designer`, `the-strategist`,
  `the-translator`, `the-herald`, `the-merchant`, `the-quartermaster`, `the-butler`) **or**
  `you` (the Guild Master).
- `gate` ∈ `approval` · `certify` · `report`.

## Conformance rules — keep `conformity_check.py` green

These are enforced; a crystallized workflow that breaks one will fail the Conformity Sweep:

1. **Ends with a `report` gate** — the Butler's plain-English report (decision #23, check `D23`).
2. **Last member step before the report is `the-quartermaster`** — the conformance close
   (decision #26, check `C`).
3. **Every `actor` resolves** to a roster member or `you`; **every `gate`** is one of the three
   valid kinds (check `R`).
4. **Art prompt exists** — add an entry for the new `id` in `gen-workflow-art.cjs` so the sigil can
   be forged (check `G`).
5. After editing `workflows.json`, run **`python3 build.py`** so `guild-data.js` / `guild-data.json`
   regenerate and `meta.counts.workflows` matches (checks `P`, `N`).

The canonical closing tail of every workflow:

```
… → the-quartermaster ("Confirm Guild Conformance") → ⟨gate: report⟩
```

## Worked example

**Mission:** "Add a settings page — design it, build it, ship it."

**Step 1 — decompose into slices:** ① shape the brief · ② design the UI · ③ model any new
settings storage · ④ build it · ⑤ verify + conform.

**Step 2 — map to members:** ① Butler · ② Designer · ③ Architect · ④ Developer · ⑤ Quartermaster.

**Step 3 — arrangement:** ② Designer and ③ Architect have **independent inputs, disjoint surfaces,
no ordering constraint** → **parallel**. ④ Developer needs both their outputs → **sequential** after
the parallel pair. ⑤ verify needs the build → sequential last.

**Step 4 — gates:** approval after the brief; certify after design+architecture, before build;
report at the end.

**Step 5 — formation (what the Butler dispatches):**

```
Butler: clear brief
  ⟨approval⟩
Designer  ∥  Architect          (parallel — independent, disjoint)
  ⟨certify — Quartermaster⟩
Developer: build                (sequential — needs design + schema)
Quartermaster: verify + conform (sequential — needs the build)
  ⟨report — Butler⟩
```

**Crystallized** (`workflows.json` entry, abbreviated):

```json
{
  "id": "feature-page", "name": "Feature Page", "icon": "🧩", "accent": "cyan",
  "tagline": "Design, build, and ship a self-contained page.",
  "when": "Use when a single user-facing page needs design + build together.",
  "steps": [
    { "kind": "member", "actor": "you", "title": "Request the Page", "act": "You describe the page you want.", "produces": "raw request" },
    { "kind": "member", "actor": "the-butler", "title": "Clear the Brief", "act": "The Butler rewrites it into an actionable brief with success criteria.", "produces": "cleared brief" },
    { "kind": "gate", "gate": "approval", "label": "You approve the brief before work begins." },
    { "kind": "member", "actor": "the-designer", "title": "Design the UI", "act": "The Designer produces the page's visual design — in parallel with the Architect.", "produces": "design spec" },
    { "kind": "member", "actor": "the-architect", "title": "Model the Storage", "act": "The Architect models any new settings storage — in parallel with the Designer.", "produces": "schema" },
    { "kind": "gate", "gate": "certify", "label": "The Quartermaster certifies design + schema are buildable before construction." },
    { "kind": "member", "actor": "the-developer", "title": "Build the Page", "act": "The Developer implements the page against the design and schema.", "produces": "working page" },
    { "kind": "member", "actor": "the-quartermaster", "title": "Verify and Conform", "act": "The Quartermaster verifies the page and runs the repo conformance pass.", "produces": "verified page" },
    { "kind": "gate", "gate": "report", "label": "The Butler reports the finished page in plain English and flags whether this run is reusable." }
  ]
}
```

Note the parallel pair (Designer ∥ Architect) is expressed as **two adjacent member steps** — the
star map renders steps in order; the *parallelism* is the Butler's dispatch decision, recorded in
the `act` text ("in parallel with…"). The tail (`the-quartermaster` → `report`) is fixed.

## The hand-off

The Butler's report names the candidate workflow and its steps; the Quartermaster takes it from
there: adds the entry, adds the `gen-workflow-art.cjs` prompt, runs `build.py`, and logs a
`decision` guild-log entry if the new workflow sets a convention worth recording.
