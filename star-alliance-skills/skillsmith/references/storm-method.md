---
type: Document
timestamp: 2026-06-27T10:27:03Z
---

# The STORM method — adapted for skill evolution

`routine` mode researches every candidate change with **STORM** before it touches a skill. STORM
(*Synthesis of Topic Outlines through Retrieval and Multi-perspective Question Asking*) is the
Stanford OVAL Lab method (NAACL 2024). The insight that matters here: **one prompt returns the
majority view; five contrasting personas catch the blind spots.** Stanford measured multi-perspective
articles as ~25% more organized and ~10% broader than single-prompt ones. We borrow the *thinking*,
not the code.

Source: github.com/stanford-oval/storm · storm.genie.stanford.edu · the write-up in
`~/Downloads/The Stanford STORM Method ….md` (saved 2026-06-19).

The vanilla STORM personas are Practitioner / Academic / Skeptic / Economist / Historian. For
**skill evolution** we re-cast them so each interrogates a skill from a different failure axis.

---

## The five skill-evolution personas

Run all five against **one skill at a time** (or one candidate new-skill idea). Each persona gets the
harvested corpus for that skill (from `routine_scan.py`: the skill's `SKILL.md` + references, its
version/changelog/Cowork status, every place it's mentioned across your projects and session
transcripts, and the friction snippets near those mentions).

| # | Persona | Lens | The question only it asks |
|---|---|---|---|
| 1 | **The Daily-Driver** (practitioner) | Uses this skill in real sessions. | Where does it create friction, mis-trigger, or make me repeat myself? What does it *not* do that I keep doing by hand right after invoking it? |
| 2 | **The Red-Teamer** (skeptic) | Thinks the skill is wrong or redundant. | Where does it mislead, over-trigger, duplicate another skill, or encode a stale assumption? What would make me *stop* using it? |
| 3 | **The Architect** (maintainer) | Owns naming/versioning/Cowork limits. | Is it spec-clean (`metadata.version`, desc ≤1024 & no `<`/`>`, lean body, detail in `references/`)? What is the cleanest upgrade path that doesn't break callers? |
| 4 | **The Archaeologist** (historian) | Has read the changelog + the session transcripts. | What recurring pain in past sessions should this skill already solve? What pattern keeps reappearing that no skill covers? (← the new-skill signal.) |
| 5 | **The Economist** (ROI) | Counts tokens and leverage. | Which upgrade returns the most value per token/effort? Is a proposed new skill worth its maintenance cost, or is it a one-off better left as a prompt? |

For each persona capture exactly three things (STORM Prompt 1 shape):
- **core position** (2 sentences),
- **strongest evidence** (cite the corpus — a file path, a transcript snippet, a version/status fact),
- **the one thing it would tell me that no other persona would.**

> Running this as a Workflow: one subagent per persona per skill is the natural fan-out. See
> `routine-playbook.md` §R2. Each subagent returns a structured persona verdict; the parent runs the
> next three STORM steps.

---

## The four STORM steps (per skill)

### Step 1 — Multi-perspective scan
Produce the five persona verdicts above. This is the heart of the method: five different reads of the
same skill.

### Step 2 — Contradiction map
From the five verdicts:
1. **Where do two+ personas directly contradict** on what to change? List each clash with the specific claims.
2. **Strongest vs weakest evidence** — which persona's recommendation is best-supported by the corpus?
3. **The one question** that, if answered, resolves the biggest contradiction.
4. **What do ALL five agree on?** → this is a **high-confidence upgrade route**. Even the skeptic confirms it.
5. **What did NO persona address?** → a blind spot in the skill (or a gap with no skill at all → **new-skill candidate**).

### Step 3 — Synthesis (the per-skill dossier)
Pull the scan + contradiction map into a briefing the executor can act on:
1. **One-paragraph summary** of the skill's current health.
2. **Ranked findings** — the concrete upgrade routes, ordered by reliability; for each, which personas support and which challenge it.
3. **The hidden connection** — one non-obvious link (e.g. "two skills both hand-roll the same scan → extract a shared script / new skill").
4. **The actionable upgrade** — the specific edit + the SemVer bump it implies (PATCH/MINOR/MAJOR).
5. **The frontier question** — the one unknown that would most change how this skill should evolve.

### Step 4 — Peer review (the autonomy gate)
STORM's known weakness is that it does not self-critique; this step forces it to grade its own dossier.
**This score is what gates autonomous execution.**
1. **Confidence scores (1–10)** for each ranked finding, with the reason for each score.
2. **Weakest link** — the finding you're least sure of + exactly what evidence would verify it.
3. **Bias check** — did one persona dominate? Is the dossier over-weighted to one axis?
4. **Missing perspective** — is there a 6th angle that would change the conclusion?
5. **Overall grade** — what would a maintainer reviewing this say, and what must be fixed first?

**Gate:** `routine` only auto-applies a finding whose peer-review confidence is **≥ 8/10** (and which
clears the other guards in `routine-playbook.md` §R4). Findings below 8 are written to the ledger as
**proposals**, not applied. A new skill is only created when *both* synthesis and peer-review rate the
idea ≥ 8 **and** it doesn't duplicate an existing skill.

---

## The raw prompt templates

These are the vanilla Stanford prompts, kept verbatim for reference. `routine` uses the
skill-evolution recast above, but the shape is identical — swap "[YOUR TOPIC]" for the skill name and
the generic personas for the five in the table.

**The four prompts (verbatim Stanford shape):**

**Prompt 1 (scan):** "Simulate 5 expert perspectives on [TOPIC]. For each give: core position in 2
sentences; strongest supporting evidence; the one thing they'd tell me no other perspective would."

**Prompt 2 (contradiction map):** "From the 5 perspectives: where do they contradict? strongest vs
weakest evidence? the one question that resolves the biggest conflict? what do ALL agree on? what did
NONE address?"

**Prompt 3 (synthesis):** "Synthesize into a briefing: one-paragraph summary; 5 key findings ranked
by reliability (note which perspectives support/challenge each); the hidden connection; the actionable
insight; the frontier question."

**Prompt 4 (peer review):** "Peer-review your own briefing: confidence score 1–10 per finding;
weakest link + what would verify it; bias check (did one voice dominate?); missing 6th perspective;
overall grade + what to fix."
</invoke>
