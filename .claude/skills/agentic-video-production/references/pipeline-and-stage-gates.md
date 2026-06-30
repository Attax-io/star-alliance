---
type: Document
title: Pipeline & Stage Gates
description: The staged video-production line and the governance gates between stages.
timestamp: 2026-06-28T00:00:00Z
---

# Pipeline & Stage Gates

The doctrine of producing video as a staged production line with governance gates between
stages — distilled from OpenMontage's agent-first architecture (`AGENT_GUIDE.md`,
`docs/ARCHITECTURE.md`, README "Production Governance").

## The agent IS the orchestrator

There is no runtime code orchestrator. The agent reads instructions and drives the line:

```
read pipeline manifest (YAML) → read stage director skill (MD) → call a tool
→ self-review → checkpoint (JSON artifact) → human approval gate → next stage
```

Code provides only **tools and persistence**. Every creative decision, review rule, quality
bar, and checkpoint policy lives in readable instruction files, not in code. The payoff: the
system is debuggable by *reading the skill*, and model-agnostic.

**Rule Zero — all production goes through a pipeline.** Never improvise: don't write ad-hoc
scripts that call generation tools directly, don't skip the pipeline to hit an API, don't
generate an asset before reading that stage's director skill. The intelligence is in the
skills, not in improvised code. A request like "make a video about X" is first a *pipeline
selection problem* — pick the pipeline, read its manifest, read the stage skill, then act.

## The canonical stage progression

```
research → proposal → script → scene_plan → assets → edit → compose → publish
```

Each stage emits exactly one **canonical artifact** that is the contract for the next stage,
and every artifact validates against a JSON schema before its checkpoint is written
(prevents garbage propagating downstream):

| Stage | Canonical artifact | What it locks |
|-------|-------------------|---------------|
| research | `research_brief` | landscape, data points, audience questions, angles, visual refs |
| proposal | `proposal_packet` | concept options, tool path, **render_runtime**, cost, approval gate |
| script | `script` | timestamped sections, narration, pronunciation/enhancement cues |
| scene_plan | `scene_plan` | ordered scenes, timings, per-scene asset requirements |
| assets | `asset_manifest` | each asset's path, source tool, model/seed, scene linkage |
| edit | `edit_decisions` | concrete cuts, overlays, subtitle/music, runtime carried unchanged |
| compose | `render_report` | output path, encoding profile, verification notes |

Specialized pipelines insert stages (e.g. `character-animation` adds `character_design` and
`rig_plan` before `scene_plan`). The progression is a spine, not a straitjacket.

## Research is a first-class stage, not a warm-up

Before a single word of script is written, the agent runs **live web research** — 15-25+
searches across YouTube, Reddit, Hacker News, news, and academic sources — and gathers data
points, audience questions, trending angles, and visual references into a cited
`research_brief`. Videos are grounded in real, current information, not hallucinated facts.
Skipping research is how you get confident, wrong, generic content.

## The gates between stages

OpenMontage treats video like engineering: quality gates, audit trails, enforcement. The
gates are not bureaucracy — each one blocks a specific, expensive failure mode.

1. **Approval gate (creative stages).** `idea`/`script`/`scene_plan` default to human
   approval; technical stages (`assets`/`edit`/`compose`) auto-proceed. Never begin asset
   generation before the user approves the production plan and cost.
2. **Pre-compose validation gate** (`video_compose.py` `_precompose_check`). Runs at the seam
   between `edit` and `compose` and **blocks the render** on critical violations: a
   *delivery-promise* violation (a motion-led brief that resolved to mostly stills), a
   *slideshow risk* verdict of `fail`, or a missing renderer family (the last only WARNs).
   Catches broken plans *before* wasting GPU time and money. Run it on the resolved cuts +
   `scene_plan` before any compose call.
3. **Slideshow risk scoring** (`lib/slideshow_risk.py`, `score_slideshow_risk`). Scores the
   `scene_plan` (and optionally `edit_decisions` + `renderer_family` + `render_runtime`) across
   **6 dimensions, each 0–5, lower is better** — averaged into a verdict:

   | Dimension | Fires when | What it catches |
   |-----------|------------|-----------------|
   | `repetition` | one scene `type` >70%, <60% unique descriptions, or one `shot_size` >60% | same layout/grammar recurring |
   | `decorative_visuals` | scenes with no `information_role` / `narrative_role` / `shot_intent` | scenes that decorate instead of communicate |
   | `weak_motion` | moving shots that lack a `shot_intent` | motion with no narrative purpose |
   | `weak_shot_intent` | low share of scenes carrying `shot_intent` | framing/reveal with no stated reason |
   | `typography_overreliance` | high share of `text_card`/`stat_card`/`kpi_grid` scenes | "animated PowerPoint" |
   | `unsupported_cinematic_claims` | renderer family says *cinematic* but scenes lack `hero_moment`, camera movement, or `lighting_key` | a cinematic label with no cinematic structure |

   **Verdict thresholds (on the average):** `< 2.0` strong · `< 3.0` acceptable · `< 4.0` revise
   · `≥ 4.0` **fail — must not proceed to compose.** Score at `scene_plan` (to revise early)
   and again at `edit` (the gate). Feeding the scenes the role/intent fields the scorer reads
   (`information_role`, `narrative_role`, `shot_intent`, `shot_language.{shot_size,
   camera_movement, lighting_key}`, `hero_moment`) is what lets the plan pass honestly.
4. **Post-render self-review (mandatory).** After every render: ffprobe validation, frame
   extraction at 4 positions (black frames / broken overlays), audio level analysis (silence,
   clipping), delivery-promise verification, subtitle presence. **If review fails, the video
   is not presented.** The implementer never grades its own work by eye.
5. **Source media inspection.** When the user supplies footage, probe every file (resolution,
   codec, audio channels, duration) and derive planning implications before any creative
   decision. Never hallucinate content from a filename.

### The delivery-promise gate, concretely (`lib/delivery_promise.py`)

The delivery promise is **classified at proposal and locked**, then enforced at the pre-compose
gate. It is the named defense against the single most damaging failure mode: silently
downgrading a motion-led brief into stills. Each `PromiseType` carries rules — the load-bearing
ones being `still_fallback_allowed`, `requires_video_generation`, and a **`min_motion_ratio`**:

| Promise type | still fallback | min motion ratio |
|--------------|:--:|:--:|
| `motion_led` | no | 0.70 |
| `avatar_presenter` | no | 0.30 |
| `source_led` | yes | 0.30 |
| `hybrid` | yes | 0.20 |
| `data_explainer` / `teacher_explainer` / `screen_demo` / `localization` | yes | 0.00 |

The promise's `validate_cuts(cuts)` classifies every cut into three buckets — and the crucial
rule is that **animated slides are not motion**: only `video` / `animation` / `avatar` cuts
count as *real motion*; `text_card`, `stat_card`, `chart`/`bar_chart`/`line_chart`/`pie_chart`,
`kpi_grid`, `comparison`, `progress`, `callout` are *slide-grammar* (they have transitions but
are not footage); everything else is a *still*. If the motion ratio falls below the promise's
floor, the cut set is invalid and the pre-compose gate **blocks**. Persist the promise at
`edit_decisions.metadata.delivery_promise` (or top-level on the proposal packet) so the gate
can read it; absence only WARNs. Post-render, `video_compose` re-verifies and records
`delivery_promise_honored` + `motion_ratio_actual` in the render report — a locked motion-led
promise must never be quietly satisfied by slides.

### Character-animation inserts two contract stages before `scene_plan`

The `character-animation` pipeline is the canonical example of the spine flexing: between
`script` and `scene_plan` it inserts **`character_design` then `rig_plan`**, each a
schema-validated artifact that the later stages consume:

| Stage | Artifact (`schemas/artifacts/…`) | Locks |
|-------|----------------------------------|-------|
| `character_design` | `character_design.schema.json` | per-character `id`, `role`, `body_type`, `style`, `required_emotions`, `required_actions` (+ optional `required_views`, `props`, `constraints`) and a shared `style` block (palette, line, texture) |
| `rig_plan` | `rig_plan.schema.json` | per-character `rig_type` (`svg_rig`/`canvas_procedural`/`lottie`/`hybrid`), `parts` (id/kind/layer/parent), `joints` (pivot/rotation/scale), `layers`, `required_poses`, `risks` |

`scene_plan`, `assets`, `edit`, and `compose` all list `character_design` + `rig_plan` in their
`required_artifacts_in` — design must precede rig, and rig must precede any scene work. Never
plan character scenes before both contracts are checkpointed.

## Self-review, checkpoints, and resumption

- **Self-review after every stage**, before checkpointing — load the stage's `review_focus`
  from the manifest, categorize findings (critical / suggestion / nitpick), fix criticals and
  re-review, max two rounds then pass-with-warnings and move on. The reviewer is advisory; the
  *gates* above are what actually block.
- **Checkpoints make every stage resumable.** State persists as JSON with the canonical
  artifact, review, and cost snapshot. A failed stage resumes from the last good checkpoint —
  completed stages never re-run.

## The decision communication contract

The user should never have to *infer* which provider, model, or render path was chosen.

- **Announce before execution.** Before any paid/consequential call, state the exact tool,
  provider, model/variant, why it was chosen, and whether it's a sample or a batch run.
- **Ask before major changes.** Switching provider, model family, video-led↔still-led
  treatment, composition engine, or dropping approved narration/music all require asking
  first. Minor prompt refinements inside an approved path do not.
- **No unilateral substitutions.** If the approved path is blocked, prepare alternatives but
  do not execute them without approval. Escalate the blocker with structure: what was
  attempted, what failed, whether it's auth/access/bug/quality, the options, the
  recommendation.
- **Decision audit trail.** Every provider, style, music, voice, renderer, fallback, and
  downgrade is logged with alternatives considered, confidence, and reasoning — persisting
  across all stages so the output is traceable to *why it looks the way it does*.

## Budget governance is a first-class concept

`estimate → reserve → reconcile`. Estimate cost before execution, reserve (lock) budget,
reconcile actual spend after. Modes: `observe` (track only), `warn` (log overruns), `cap`
(hard reject). Defaults: $10 total cap, 10% reserve holdback, $0.50 single-action approval
threshold, first-time use of any paid tool requires confirmation. The agent tells the user
what it will cost *before* it spends. No surprise bills.
