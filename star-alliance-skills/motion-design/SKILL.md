---
name: motion-design
description: "Two-mode motion & interaction design specialist for product UI. CREATE — build components with purposeful motion (React, Framer Motion, CSS, HTML) using a motion cookbook, a creation-gotchas self-check, and the guild easing+duration token set. AUDIT — review existing motion, flag AI-slop patterns (pulse-spam, hover-scale-on-everything, stagger-spam, blur-everywhere), run a motion-gap analysis, and emit a branded HTML report with looping demos (pass --terminal for markdown). Weights three designer lenses — Emil Kowalski (restraint/speed), Jakub Krehel (production polish), Jhey Tompkins (playful) — by project context. Every animation needs a job; no job, no motion. Accessibility (prefers-reduced-motion) is mandatory. Triggers: 'animate this', 'add a transition', 'build an animated X', 'make it feel alive', 'audit/review the motion', 'is this animation good', easing/timing/spring-vs-bezier questions. The deep specialist beneath design-taste's motion mode: design-taste DECIDES whether a surface moves; motion-design SPECIFIES and BUILDS the motion. NOT for overall visual style — that is design-taste."
metadata:
  version: 2.0.0
  mcpmarket-version: 1.0.0
type: Skill
---
# Motion Design — the guild's create & audit motion engine

Senior design-engineer specialism for **motion and interaction design** on product UI. This skill runs
in **two modes**:

- **Create** — Build interactive components with purposeful motion → `workflows/create.md`
- **Audit** — Review existing motion design and report findings (branded HTML report) → `workflows/audit.md`

**Scope**: Web and app UI motion — HTML/CSS, React, Framer Motion / Motion, iOS/Android transitions,
design-system animation. The frequency framework still applies to other motion work (game engines,
Lottie, Rive, video), but designer-specific techniques may not translate.

This is the deep specialist beneath `design-taste`'s `motion` mode. `design-taste` rules on **whether** a
surface should move and how it fits the overall aesthetic; **motion-design** picks the exact curve,
duration, origin, and spring-vs-bezier call **and builds it**. When `design-taste` says "add motion here",
hand the specifics here.

---

## STEP 0: Detect Mode (DO THIS FIRST)

| Signal in the request | Mode |
|-----------------------|------|
| "build", "create", "add animation", "animate this", "implement", "make it feel…" | **Create** |
| "audit", "review", "evaluate", "check", "feedback on", "is this motion good" | **Audit** |
| Ambiguous (e.g. "look at this modal animation") | Ask the user |

For ambiguous requests, if `AskUserQuestion` is available, present **Create** (build/improve the motion)
vs **Audit** (review existing motion and report). Otherwise ask in plain text.

**Once the mode is known, read the matching workflow file and follow it exactly.**

---

## The Three Designers

- **Emil Kowalski** (Linear, ex-Vercel) — Restraint, speed, purposeful motion. Best for productivity tools.
- **Jakub Krehel** (jakub.kr) — Subtle production polish, professional refinement. Best for shipped consumer apps.
- **Jhey Tompkins** (@jh3yy) — Playful experimentation, CSS innovation. Best for creative sites, kids apps, portfolios.

Each designer answers a different question:
- **Emil** — *"Should this animate at all?"*
- **Jakub** — *"Is this subtle and polished enough for production?"*
- **Jhey** — *"What could this become?"*

**Critical insight**: these perspectives are context-dependent, not universal rules. A kids' app should
prioritize Jakub + Jhey (polish + delight), not Emil's productivity-focused speed rules. Both modes weight
the designers by project context before doing anything.

> The three lenses distill each designer's *publicly published* work — courses, articles, talks, open-source.
> The weighting framework and "lens" framing are this skill's interpretation, named in tribute; they are
> **not** authored or endorsed by the designers themselves. See **Credits** below.

### Context-to-Perspective Mapping

| Project Type | Primary | Secondary | Selective |
|--------------|---------|-----------|-----------|
| Productivity tool (Linear, Raycast) | Emil | Jakub | Jhey (onboarding only) |
| Kids app / Educational | Jakub | Jhey | Emil (high-freq game interactions) |
| Creative portfolio | Jakub | Jhey | Emil (high-freq interactions) |
| Marketing/landing page | Jakub | Jhey | Emil (forms, nav) |
| SaaS dashboard | Emil | Jakub | Jhey (empty states) |
| Mobile app | Jakub | Emil | Jhey (delighters) |
| E-commerce | Jakub | Emil | Jhey (product showcase) |

---

## Core Principles (Both Modes)

**Every animation needs a job. If it has no job, don't animate.**

### The Frequency Gate

Before adding or approving any animation, ask how often the user triggers it:

| Frequency | Recommendation |
|-----------|----------------|
| Rare (monthly) | Delightful, expressive motion welcome |
| Occasional (daily) | Subtle, fast motion |
| Frequent (100s/day) | No animation or instant transition |
| Keyboard-initiated | Never animate |

### Duration Guidelines (Context-Dependent)

| Context | Guideline | Guild token |
|---------|-----------|-------------|
| Productivity UI (Emil) | Under 300ms — 180ms ideal | `--dur-2` |
| Production polish (Jakub) | 200–500ms for smoothness | `--dur-3`/`--dur-4` |
| Creative/kids/playful (Jhey) | Whatever serves the effect | `--dur-5`+ |

**Do not universally flag or cap durations.** Check the context weighting first. Exact tokens
(`--dur-1`..`--dur-5`) and curves live in `references/easing-tokens.md`.

### The Golden Rule

> "The best animation is that which goes unnoticed."

If users comment "nice animation!" on every interaction, it's probably too prominent for production.
(Exception: kids apps and playful contexts where delight IS the goal.)

### Accessibility is NOT Optional

Every animation — generated in Create mode or reviewed in Audit mode — must handle
`prefers-reduced-motion`. No exceptions. See `references/accessibility.md`.

### Compositor-only props

Animate `transform`/`opacity`, not `width`/`height`/`top`/`left` (layout thrash). Never animate from
`scale(0)` — use 0.94–0.98 by element size. See `references/performance.md`.

---

## Reference Index

| File | Contents | Load When |
|------|----------|-----------|
| [Decision Tree](references/decision-tree.md) | Easing category by interaction type · scale · transform-origin · hover/touch · frequency/context modifiers | Create mode (easing call); Audit recommendations |
| [Easing & Duration Tokens](references/easing-tokens.md) | The guild curve set + `--dur-1`..`--dur-5` duration tokens + quick-reference + performance budget | Create mode (exact tokens); Audit recommendations |
| [Motion Cookbook](references/motion-cookbook.md) | All motion recipes — enter/exit, easing, springs, clip-path, @property, FLIP, scroll-driven | Create mode (always); Audit for implementation recs |
| [Creation Gotchas](references/creation-gotchas.md) | Failure modes when writing motion (decorative-by-default, scale(0), bare ease, missing reduced-motion) | Create mode (always) |
| [Audit Checklist](references/audit-checklist.md) | Systematic audit checklist | Audit mode (always) |
| [Anti-Checklist](references/anti-checklist.md) | Quality gate — AI-slop motion categories + anti-patterns to flag | Audit mode (always) |
| [Emil Kowalski](references/emil-kowalski.md) | Restraint philosophy, frequency rule, decision frameworks | Either mode, if Emil is weighted |
| [Jakub Krehel](references/jakub-krehel.md) | Production-polish philosophy and decision frameworks | Either mode, if Jakub is weighted |
| [Jhey Tompkins](references/jhey-tompkins.md) | Playful experimentation philosophy and frameworks | Either mode, if Jhey is weighted |
| [Accessibility](references/accessibility.md) | prefers-reduced-motion, vestibular safety | Both modes (mandatory) |
| [Performance](references/performance.md) | GPU optimization, will-change, layout thrash | Either mode, complex animations |
| [Output Format](references/output-format.md) | Audit report template — HTML mode (default) + terminal mode (flag) | Audit mode only |
| [Demo Shell](references/demo-shell.html) | Visual container template for per-finding demo cards | Audit mode, HTML output |
| [Report Template](references/report-template.html) | Full worked-example audit report | Audit mode, HTML output |

## Workflow Index

| Workflow | Purpose |
|----------|---------|
| [Create](workflows/create.md) | Build interactive components with purposeful motion |
| [Audit](workflows/audit.md) | Review existing motion design, produce a per-designer report |

---

## Gotchas

- **Name overlap with `design-taste` is real.** A request about *whether* something should move or about
  overall style belongs to `design-taste`; the *exact curve / timing / build* belongs here. Keep the
  NOT-clause in the description intact so the two don't cross-trigger.
- **Never animate from `scale(0)`** — it reads synthetic. Use 0.94–0.98 by element size.
- **Compositor-only props.** Animate `transform`/`opacity` (no layout thrash).
- **Always honor `prefers-reduced-motion`.** Ship the reduce-motion media query with any motion.
- **Don't universally cap durations** — weight by the lens/context first.

## Credits

This skill's Create+Audit modes and the three-lens framework are distilled from the **publicly published**
work of three designers, named in tribute; **not** authored or endorsed by them. Upstream:
`design-motion-principles` (MIT, kylezantos).

- **Emil Kowalski** — emilkowal.ski, animations.dev, Sonner, Vaul
- **Jakub Krehel** — krehel.com
- **Jhey Tompkins** — jhey.dev, @jh3yy

## Versioning
`metadata.version` is the guild's bump line; `metadata.mcpmarket-version` preserves the original
easing-token provenance. Bump on any change (PATCH wording/refs · MINOR new reference/pattern · MAJOR
method-contract change). Regenerate `VERSIONS.md` via
`python3 star-alliance-skills/skillsmith/scripts/skill_registry.py write`, then `python3 build.py`.

## Changelog
- **2.0.0** — Absorbed `design-motion-principles` (MIT, kylezantos) → two-mode router. Added **Create**
  (motion cookbook, creation-gotchas, three designer lenses) and **Audit** (motion-gap analysis,
  anti-AI-slop checklist, branded HTML report with looping demos) modes, mode detection at STEP 0, the
  frequency gate, and context-to-lens weighting. New references: motion-cookbook, creation-gotchas,
  audit-checklist, anti-checklist, emil/jakub/jhey lenses, accessibility, performance, output-format,
  demo-shell + report-template (HTML). New `workflows/create.md` + `workflows/audit.md`. Kept the guild
  `decision-tree.md` + `easing-tokens.md` (`--dur-1..5`) and the design-taste delegation. Method-contract
  reshape (single-process → two-mode router) → MAJOR.
- **1.0.0** — Initial guild release. Vendored from upstream motion-design (easing decision-tree + token
  set). Reframed as the specialist beneath `design-taste`'s `motion` mode.
</content>
