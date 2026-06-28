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
2. **Pre-compose validation gate.** Blocks the render if the *delivery promise* is violated
   (a "motion-led" brief that resolved to 80% still images), if the **slideshow risk score**
   is critical, or if the chosen renderer family is missing. Catches broken plans *before*
   wasting GPU time and money.
3. **Slideshow risk scoring.** A 6-dimension check (repetition, decorative visuals, weak
   motion, shot intent, typography overreliance, unsupported cinematic claims) that prevents
   "animated PowerPoint."
4. **Post-render self-review (mandatory).** After every render: ffprobe validation, frame
   extraction at 4 positions (black frames / broken overlays), audio level analysis (silence,
   clipping), delivery-promise verification, subtitle presence. **If review fails, the video
   is not presented.** The implementer never grades its own work by eye.
5. **Source media inspection.** When the user supplies footage, probe every file (resolution,
   codec, audio channels, duration) and derive planning implications before any creative
   decision. Never hallucinate content from a filename.

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
