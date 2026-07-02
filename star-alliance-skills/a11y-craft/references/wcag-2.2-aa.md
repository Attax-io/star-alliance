---
type: Document
timestamp: 2026-07-02T12:28:13Z
---

# WCAG 2.2 AA — the designer's checklist

Scope: criteria a designer owns, owns-cooperatively, or must sign off before dev ships. Not pure-engineering items (parsing, media captions, timeouts) are excluded. Numbers are WCAG 2.2 published values, no invented thresholds.

## Color contrast — text (1.4.3)

**Rule.** Normal text (under 18pt / under 14pt bold / under ~24px regular / ~18.66px bold) needs ≥ 4.5:1 contrast against its background. Large text needs ≥ 3:1. Compute against the *actual* surface under the text in the live theme — both light and dark. Logo text is exempt; inactive UI components are exempt; pure decoration is exempt.

**Why.** Low-vision users (≈ 8% of men have red-green deficiency; ≈ 2% have low vision) cannot read low-contrast text. Text is the primary content channel; its threshold is the strictest.

**How to check.**
- Manual: pick 6–10 token pairs from your theme (`--text-primary` on `--surface-1`, etc.) and verify each ratio.
- Tooling: Stark (Figma plugin), Colour Contrast Analyser, axe DevTools, Polypane.
- Token-build: enforce ≥ 4.5:1 at generation; fail the build otherwise.

## Color contrast — large text & UI components (1.4.3 / 1.4.11)

**Rule.** Large text (≥ 18pt regular, ≥ 14pt bold), UI component boundaries, and graphical objects need ≥ 3:1 against adjacent colors. Adjacent = the color the user must perceive the component against. Active component states count; disabled components are exempt by spec but must be programmatically inert (see `disabled` exemption below).

**Why.** 3:1 is the empirical threshold below which component silhouettes fragment and large text loses readability. Designers pick the borders, focus rings, and icon strokes — this is your surface, not dev's.

**How to check.**
- Manual: zoom to 100%; check every icon, divider, input border, toggle track in both themes.
- Tooling: Stark, Polypane contrast grid, axe.

## Non-text contrast (1.4.11)

**Rule.** Visual information required to identify UI components and states (input borders, radio fill, switch thumb vs track, chart series) must have ≥ 3:1 against adjacent colors. State must be perceivable without color alone (see 1.4.1).

**Why.** Form controls, icons, and data viz are how users operate; if their outline disappears, so does usability.

**How to check.**
- Manual: desaturate screenshots — can you still tell inputs, selected rows, and chart series apart? If no, add shape/label/pattern.
- Tooling: axe (partial), manual grayscale.

## Use of color (1.4.1)

**Rule.** Color is never the *sole* means of conveying information, indicating state, prompting action, or distinguishing an element. Always pair color with a second channel: text label, icon, underline, pattern, shape, position.

**Why.** ~8% of men, ~0.5% of women have color-vision deficiency. Color-only error states, chart legends, or required-field markers are invisible to them.

**How to check.**
- Manual: print the screen in grayscale; route every state through monochrome. If meaning disappears, add a non-color channel.
- Tooling: Sim Daltonism (macOS), Stark CVD sim.

## Visible focus — appearance, visibility, no obscuring (2.4.7 / 2.4.11 / 2.4.12)

**Rule.**
- 2.4.7: keyboard focus indicator is visible.
- 2.4.11 (AA, WCAG 2.2): focus indicator is not entirely obscured by author content (sticky headers, modals, cookie banners).
- 2.4.12 (AA, WCAG 2.2): focus indicator has minimum area = 1 CSS px × 4 CSS px thick perimeter of the focused control, OR equivalent area not less than the perimeter calculation, AND ≥ 3:1 contrast between indicator and adjacent content, AND ≥ 3:1 between indicator and component background.

**Why.** Keyboard-only users (motor disability, power users, screen-reader users) navigate by focus. Invisible or lost focus bricks the session.

**How to check.**
- Manual: tab through every interactive element; verify the focus ring is visible, on top, not covered by sticky UI, ≥ 3:1 against both background and component fill.
- Tooling: keyboard-only pass; Polypane focus overlay.

## Focus order (2.4.3)

**Rule.** Focus order preserves meaning and operability. Reading and tab order match the visual/DOM order the user expects.

**Why.** Tabbing that jumps unpredictably breaks spatial memory and disorients screen-reader users.

**How to check.**
- Manual: tab from page top to bottom; the order should match the visual flow. `tabindex` > 0 is forbidden; `tabindex="0"` is a smell — refactor DOM instead.

## Target size minimum (2.5.8)

**Rule.** Interactive targets are at least 24×24 CSS px, *unless* the target is in a sentence/link inline, the size is set by user agent, or a functionally equivalent larger target exists on the same page (spacing exception: 24px center-to-center is sufficient). Note: 2.5.5 (AAA, 44×44) is stricter — adopt it where feasible.

**Why.** Motor-impaired users, touch users, and users with tremor cannot reliably hit sub-24px targets.

**How to check.**
- Manual: measure each button, link, checkbox, switch in CSS px. Add invisible hit-area padding where visual size is locked.
- Tooling: Polypane, browser devtools ruler.

## Keyboard operable + no trap (2.1.1 / 2.1.2)

**Rule.** All functionality is operable through a keyboard interface; no keyboard trap — focus can always move away using standard keys (Tab, Shift+Tab, arrow keys, Esc). Custom widgets (combobox, dialog, menu, tabs) implement the WAI-ARIA Authoring Practices keyboard model.

**Why.** Switch-device users, screen-reader users, and power users depend on the keyboard as the primary or only input.

**How to check.**
- Manual: unplug the mouse; complete the primary task end-to-end. Open every modal, menu, and custom widget; verify Esc closes and Tab traverses internally then returns.

## Dragging alternatives (2.5.7)

**Rule.** Any dragging action (slider, sortable list, kanban, map pan) provides a single-pointer alternative that does not require dragging — typically a click-to-select + buttons, or keyboard arrows, or a text input.

**Why.** Dragging requires fine motor control and is mouse/trackpad-bound. Excluding keyboard/touch users from a core feature is exclusion.

**How to check.**
- Manual: complete the same task with keyboard only and with a single tap (no hold-and-drag).

## Reflow / responsive (1.4.10)

**Rule.** At 320 CSS px width (the equivalent of 400% zoom on a 1280px viewport), no content requires two-dimensional scrolling to access. Disabling reflow (e.g., horizontal carousels) is a failure unless the content's meaning requires 2D layout (maps, data tables, presentations).

**Why.** Low-vision users zoom 200–400%; if the page forces horizontal scroll, content on the right is lost or requires panning.

**How to check.**
- Manual: open at 320px width; scroll only vertically. At 200% browser zoom, same test.

## Text spacing (1.4.12)

**Rule.** When the user overrides styles to: line height ≥ 1.5× font size, paragraph spacing ≥ 2× font size, letter spacing ≥ 0.12× font size, word spacing ≥ 0.16× font size — content must not lose information. No clipped text, no overlapping controls, no cut-off labels.

**Why.** Dyslexic and low-vision users apply these overrides via browser extension or user style.

**How to check.**
- Manual: inject the four overrides into devtools; verify no clipping/overlap.
- Tooling: Polypane "Text Spacing" preset.

## Animation from interactions (2.3.3)

**Rule.** Motion animation triggered by interaction (parallax on scroll, auto-playing carousels, decorative motion) can be disabled, *unless* the animation is essential to the functionality or the user has `prefers-reduced-motion: reduce` set — in which case essentiality is the only justification. Honor `prefers-reduced-motion: reduce` for non-essential motion: zero, or ≤ 200ms with no large displacement.

**Why.** Vestibular disorders: motion causes nausea, dizziness, migraines. ~35% of adults report some vestibular sensitivity.

**How to check.**
- Manual: enable reduced motion in OS settings; reload. All non-essential motion must stop.
- Tooling: Chrome devtools "Emulate CSS prefers-reduced-motion".

## ARIA roles / states / names — discipline

**Rule.** Use semantic HTML first (`<button>`, `<a>`, `<nav>`, `<main>`, `<label>`, `<fieldset>`). Add ARIA only when no native element exists. Roles must match the widget's actual behavior. States (`aria-expanded`, `aria-pressed`, `aria-selected`, `aria-disabled`, `aria-invalid`, `aria-busy`) must reflect real state at all times. Every interactive element has an accessible name.

**Why.** Screen readers announce role + name + state. Wrong role, missing name, stale state = broken announcement = unusable control.

**How to check.**
- Manual: VoiceOver rotor → "Form Controls" or NVDA "F"; each item has name + role + state.
- Tooling: Accessibility Inspector, axe.

## Accessible name + label (4.1.2 / 2.5.3 / 3.3.2)

**Rule.** Every interactive element has an accessible name that includes the visible label text (when a visible label exists). Name is computed from: `aria-labelledby` > `aria-label` > native label/text > `title` (last resort). Icon-only buttons need `aria-label`. Inputs need a programmatic label via `<label for>` or `aria-labelledby`. Visible label text must appear in the accessible name (WCAG 2.5.3 "Label in Name").

**Why.** Voice control users say "Click *Save*"; if the accessible name is `aria-label="Submit form"`, the click fails.

**How to check.**
- Manual: inspect computed accessible name in devtools; compare to visible label.

## Alt text (1.1.1)

**Rule.**
- Informative images: concise description of the *function* or *content* conveyed, not "image of".
- Decorative: `alt=""` (empty string) or `role="presentation"` + `aria-hidden="true"`.
- Functional (image-as-button/link): describe the *action*, not the picture ("Search", not "Magnifier").
- Complex (chart, diagram): short alt + longdesc or in-page description.
- Text-in-image: alt = the text itself; avoid text-in-image when CSS text is possible.

**Why.** Screen readers announce alt; missing or wrong alt makes content inaccessible to blind users.

**How to check.**
- Manual: walk every `<img>`; verify alt matches intent.
- Tooling: axe.

## Error identification + suggestion + labels (3.3.1 / 3.3.3 / 3.3.2)

**Rule.**
- 3.3.1: errors are identified in text (not by color alone), with the field and the error.
- 3.3.3: when a known failure is detectable, a suggestion is provided (e.g., "Did you mean `user@acme.com`?"). Suggestions must not be security-sensitive (no revealing whether a username exists in login).
- 3.3.2: labels or instructions are provided when content requires user input.

**Why.** Form errors are the most common accessibility failure. Color-only error states fail ~8% of users at the gate.

**How to check.**
- Manual: trigger every error state; verify text description, programmatic association (`aria-describedby` or inline), and a suggested fix where possible.

## Consistent help (3.2.6, WCAG 2.2)

**Rule.** If a help mechanism (contact, FAQ, chat, support link) appears on multiple pages of a set, it appears in the same relative order and location on each page where present.

**Why.** Users with cognitive disabilities rely on predictable placement; hunting for help each page is a barrier.

**How to check.**
- Manual: navigate 5+ pages; verify help mechanism is in the same place/label/order.
