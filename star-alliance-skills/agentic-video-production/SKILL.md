---
name: agentic-video-production
description: "Produce finished video agentically from a plain-language brief: the agent runs research, proposal, script, scene-plan, assets, edit, compose, with gates between stages (approval, pre-compose validation, slideshow-risk scoring, mandatory post-render self-review, budget caps). Builds a REAL native-video corpus from free stock and open archives (Pexels, Archive.org, NASA, Wikimedia) by CLIP retrieval, not just animated stills; scored provider selection; present-both Remotion/HyperFrames/FFmpeg runtime choice; can start from a reference video. Triggers: 'make a video about X', 'produce this video', 'turn this script into a video', 'build a b-roll corpus', 'documentary montage', 'make me something like this'. Differs from imagegen-frontend (one still image), motion-design (UI micro-interactions), image-to-code (screenshot to markup): this orchestrates an end-to-end video production line."
metadata:
  version: 1.0.0
type: Skill
---

# Agentic Video Production

Turn an AI coding assistant into an end-to-end video production studio. From a plain-language
brief, the agent runs the full pipeline — research, script, asset generation, editing, final
composition — and renders a finished video, with governance gates between every stage.
Distilled from **OpenMontage**, the first open-source agentic video-production system.

The defining move: this can make a **real video video** — actual motion footage, retrieved
from free stock and open archives and cut into a timeline — not only the "animate a few
stills and call it video" trick.

## What it is / is not

**It is** an orchestration doctrine for producing video as a *staged production line*: the
agent reads a pipeline manifest, reads each stage's director skill, calls tools, self-reviews,
checkpoints a schema-validated artifact, and passes an approval/validation gate before the
next stage. It owns pipeline selection, provider selection, corpus building, reference-video
analysis, and the governance that stops garbage from shipping.

**It is not** a single-clip prompt-to-video toy. It is not `imagegen-frontend` (one still
image), not `motion-design` (UI micro-interaction craft), not `image-to-code` (screenshot →
markup). Those produce one asset; this orchestrates a multi-stage production that *consumes*
such assets. It is also not a code orchestrator — the agent itself is the control plane;
code provides only tools and persistence.

## Generative principles

1. **Every video request is a pipeline-selection problem first (Rule Zero).** Don't improvise
   API calls or ad-hoc scripts. Match the brief to a pipeline, read its manifest, read the
   stage director skill, *then* act. The intelligence is in the skills, not in improvised
   code. → `references/pipeline-and-stage-gates.md`

2. **Stages are contracts; gates guard the seams.** Each stage emits one schema-validated
   canonical artifact (`research_brief → proposal_packet → script → scene_plan →
   asset_manifest → edit_decisions → render_report`). Between stages stand real gates:
   creative-stage approval, pre-compose validation, slideshow-risk scoring, and a *mandatory*
   post-render self-review (ffprobe + frame sampling + audio analysis + delivery-promise
   check). If the review fails, the video is not shown — the implementer never grades its own
   work by eye. → `references/pipeline-and-stage-gates.md`

3. **Real footage over animated stills — and say which path you're on.** Three honest paths:
   image-based (stills animated by the composition engine), generated motion (a video model),
   and real-footage (a CLIP-searchable corpus from Pexels/Archive.org/NASA/Wikimedia, ranked
   semantically and cut into a timeline). "Use real footage only" mandates the corpus path;
   for motion-led briefs, silent still-image downgrade is forbidden. → `references/corpus-and-footage.md`

4. **Start from a reference when one exists.** "Make me something like this video" is a
   first-class workflow, not a search request: analyze the reference (transcript, pacing,
   scenes, keyframes, style), then present 2–3 *differentiated* concepts stating what each
   keeps, changes, costs, and will actually look like with available tools. Distinguish
   reference-driven ("like this") from source-footage ("edit this"). → `references/corpus-and-footage.md`

5. **Pick providers by score, never by memory; present both runtimes, swap neither.**
   Discover capability from the live registry at preflight; route multi-provider work through
   selectors that score 7 dimensions (task fit, quality, control, reliability, cost, latency,
   continuity) and log the decision with alternatives. Every capability has a free/local path
   (zero keys still ships real video). When both Remotion and HyperFrames are available,
   present both and let the user lock `render_runtime` — silent runtime swaps are a governance
   violation. → `references/providers-and-runtimes.md`

6. **Communicate every consequential decision; never spend silently.** Announce the exact
   tool/provider/model and why before any paid call; ask before switching provider, model,
   treatment, or engine; escalate blockers with structure instead of substituting unilaterally.
   Budget is first-class: `estimate → reserve → reconcile`, with caps and a per-action approval
   threshold. The user knows the cost before it is spent. → `references/pipeline-and-stage-gates.md`

7. **Specificity is the quality lever; default to distinctness for hero work.** Coach the
   brief toward named components, audience, duration, and tone — vagueness yields generic
   output. For batch/draft work, templated scene-types are fine; for marketing, launches, and
   brand films, prefer *atelier* mode (hand-authored composition) and close with a distinctness
   review: *could this be any other product's video?* → `references/prompt-patterns.md`,
   `references/providers-and-runtimes.md`

## References

- `references/pipeline-and-stage-gates.md` — the staged production line, canonical artifacts,
  the governance gates, the decision-communication contract, budget governance.
- `references/corpus-and-footage.md` — real video vs animated stills, CLIP corpus building and
  retrieval, the reference-video entry point, source-media inspection.
- `references/providers-and-runtimes.md` — runtime capability discovery, scored 7-dimension
  selection, the free-first ladder, the 3-layer knowledge architecture, Remotion/HyperFrames/
  FFmpeg, templated vs atelier, style playbooks and platform profiles.
- `references/prompt-patterns.md` — the five routing signals in a brief, pipeline triggers by
  brief shape, onboarding a vague brief, the proposal gate, the specificity lever.
