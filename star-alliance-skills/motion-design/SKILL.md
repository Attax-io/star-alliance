---
name: motion-design
description: "Specialist motion engine for UI — picks the exact easing curve, duration token, transform-origin, and spring-vs-bezier call for any animation, by interaction purpose and frequency. The deep counterpart to design-taste's broad `motion` mode: design-taste DECIDES whether/where a surface gets motion; motion-design SPECIFIES the precise curve and timing. Every animation needs a job — if it has no job, it recommends none. Carries a decision-tree (enter/exit · morph · time-based · hover · keyboard · gesture) and a full easing+duration token set (ease-out/in-out families, --dur-1..5), plus performance (compositor-only props, will-change, blur budget) and prefers-reduced-motion accessibility. Triggers: 'animate this', 'add a transition', 'motion for X', 'clean up this animation', 'this feels too fast/slow', 'make it feel more alive/natural', questions about easing, timing, micro-interactions, spring vs bezier, bounce. NOT for whether a design should have motion at all or overall visual style — that is design-taste."
metadata:
  version: 1.0.0
  mcpmarket-version: 1.0.0
type: Skill
---
# Motion Design — the guild's easing & timing specialist

Design intentional, purposeful motion for product UI. This skill evaluates an animation's need and
recommends specific **easing curves, durations, transform-origins, and implementation approaches**
based on interaction *frequency* and *purpose*.

**Every animation needs a job. If it has no job, don't animate.**

This is the deep specialist beneath `design-taste`'s `motion` mode. `design-taste` rules on whether a
surface should move and how it fits the overall aesthetic; **motion-design** picks the exact curve,
duration token, origin, and spring-vs-bezier call. When `design-taste` says "add motion here", hand the
specifics to this skill.

## Process

### Phase 1: Load References (Required)

Before any recommendation, read both reference files:

1. **Decision Tree** (`references/decision-tree.md`) — which easing category by interaction type, plus
   scale / transform-origin / hover / touch / accessibility guidance.
2. **Easing Tokens** (`references/easing-tokens.md`) — the curves (ease-out / ease-in-out families),
   duration tokens (`--dur-1`..`--dur-5`), the quick-reference table, and performance guidelines.

### Phase 2: Evaluate the Animation

For each component or interaction, determine:

**2.1 Purpose** — *Responsiveness* (button press, menu open), *Spatial continuity* (things come from /
go somewhere), *Understanding* (onboarding, illustration), *Delight* (rare interactions only). No clear
purpose → recommend no animation.

**2.2 Frequency** — *High / keyboard-driven* → none or near-instant; *Medium / common* → fast
(120–240ms); *Low / illustrative* → freedom for slower, richer motion.

**2.3 Pattern Type** — Enter/exit · On-screen morph · Time-based · Hover/subtle · Keyboard nav.
(Exits are typically faster than enters — users want things gone quickly.)

### Phase 3: Recommend

Give specifics using tokens from the reference files: easing token + cubic-bezier, duration token + ms,
properties (prefer `transform`/`opacity` — compositor-only), transform-origin, spring-vs-bezier, bounce
(default no), and a code snippet. Always respect `prefers-reduced-motion`.

## Output Format

```
## Animation Recommendation

**Component**: [What's being animated]

### Evaluation
- **Purpose**: [responsiveness / spatial / understanding / delight / none]
- **Frequency**: [high / medium / low]
- **Pattern**: [enter-exit / morph / time-based / hover / keyboard]

### Recommendation
- **Easing**: [token] — `[cubic-bezier]`
- **Duration**: [token] — `[ms]`
- **Properties**: [transform, opacity, …]
- **Transform Origin**: [if applicable]
- **Spring vs Bezier**: [recommendation + why]
- **Bounce**: [yes/no + why]

### Implementation
[CSS / Framer Motion / GSAP snippet]

### Notes
[case-specific guidance]
```

## Example

**User**: "How should I animate this dropdown menu?"

```
## Animation Recommendation
**Component**: Dropdown menu
### Evaluation
- **Purpose**: Responsiveness — immediate feedback on trigger click
- **Frequency**: Medium
- **Pattern**: Enter/exit
### Recommendation
- **Easing**: --ease-out-quart — `cubic-bezier(.165, .84, .44, 1)`
- **Duration**: --dur-2 — `180ms`
- **Properties**: transform (scale, translateY), opacity
- **Transform Origin**: Top center (match trigger side)
- **Spring vs Bezier**: Bezier; spring only if interruptible mid-animation
- **Bounce**: No — tap-to-open shouldn't bounce
### Implementation
.dropdown { transform-origin: top center; transition: transform 180ms cubic-bezier(.165,.84,.44,1), opacity 180ms cubic-bezier(.165,.84,.44,1); }
.dropdown[data-state="closed"] { opacity:0; transform: scale(0.96) translateY(-8px); }
.dropdown[data-state="open"]   { opacity:1; transform: scale(1) translateY(0); }
### Notes
- Use scale(0.96), not scale(0) · set origin to match trigger · keep under 240ms
```

## Tips for Best Results

1. Be specific about the component (dropdown vs modal vs tooltip).
2. Mention the trigger (click / hover / keyboard / scroll).
3. Share context (productivity app vs marketing page).
4. Ask about multiple states (open / close / hover / disabled).
5. Specify framework (CSS / Framer Motion / GSAP / React Spring).

## Resources

- **`references/decision-tree.md`** — flowchart for choosing easing category by interaction type, plus
  scale values, transform-origin, hover/touch, frequency/context modifiers, accessibility.
- **`references/easing-tokens.md`** — full easing curve set (ease-out / ease-in-out / ease-in / linear),
  duration tokens, CSS custom properties, quick-reference table, and performance budget.

## Gotchas

- **Name overlap with `design-taste` is real.** A request about *whether* something should move or about
  overall style belongs to `design-taste`; the *exact curve / timing* belongs here. Keep the NOT-clause in
  the description intact so the two don't cross-trigger.
- **Never animate from `scale(0)`** — it reads synthetic. Use 0.94–0.98 by element size (see decision-tree).
- **Compositor-only props.** Animate `transform`/`opacity`, not `width`/`height`/`top`/`left` (layout thrash).
- **Always honor `prefers-reduced-motion`.** Ship the reduce-motion media query with any motion.

## Versioning
Vendored from the upstream `motion-design` (mcpmarket 1.0.0); `metadata.mcpmarket-version` preserves the
provenance, `metadata.version` is the guild's own bump line. Bump `metadata.version` on any change
(PATCH: wording/refs · MINOR: new reference/pattern · MAJOR: method-contract change). Regenerate
`VERSIONS.md` with `python3 star-alliance-skills/skillsmith/scripts/skill_registry.py write`, then
`python3 build.py`.

## Changelog
- **1.0.0** — Initial guild release. Vendored from upstream motion-design (easing decision-tree + token
  set). Reframed as the specialist beneath `design-taste`'s `motion` mode; references preserved verbatim.
