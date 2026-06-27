---
name: a11y-craft
description: "The Designer's accessibility craft — make WCAG 2.2 AA a gate every surface clears before it ships, not an afterthought. Three modes: audit (run the gate — automated scan + manual keyboard sweep + screen-reader spot-check + zoom/reflow + contrast in both themes, each finding as criterion + location + severity + fix); build (design accessible from the start — contrast 4.5:1 text / 3:1 UI in light AND dark, visible focus order, 24px targets, full keyboard path, prefers-reduced-motion, correct ARIA + alt + labels); contrast (contrast-as-token — derive the on-color from a surface's luminance so an inaccessible pairing is structurally impossible to emit). Use to audit accessibility, fix contrast, make a UI accessible, pass WCAG. Triggers: 'is this accessible', 'a11y audit', 'check contrast', 'WCAG', 'fix focus states', 'keyboard navigation', 'make it accessible'. Differentiate from design-unity (enforces one visual language) and design-tokens (structures the token system)."
metadata:
  version: 1.0.0
type: Skill

---
# a11y-craft — accessibility as a gate, not an afterthought

This is the Designer's craft for **accessibility**. An interface is not premium until it is
accessible: an elite design clears **WCAG 2.2 AA** as a *gate before it ships*, never as a
remediation pass bolted on after launch. This skill turns "looks fine" into "proven usable by
everyone" — keyboard-only, screen-reader, low-vision, reduced-motion, colour-blind.

It pairs with [[design-unity]] (which hosts the a11y gate in its audit) and [[design-tokens]]
(where **contrast-as-token** makes accessible colour structural). design-taste decides the
look; a11y-craft proves the look is operable.

## Three modes

- **audit** — run the gate on an existing UI. The repeatable pass + the finding/report shape
  live in [references/audit-recipe.md](references/audit-recipe.md): automated scan (catches
  ~30-40%) then manual keyboard sweep then screen-reader spot-check then zoom/reflow at 200% and
  320px then contrast in **both** themes then reduced-motion. Each finding = **criterion · location
  (file:line / selector) · severity · fix**, severity tied to launch-blocking vs backlog.
- **build** — design accessible from the first frame. The criteria a *designer* owns (not just
  the dev) are the checklist in [references/wcag-2.2-aa.md](references/wcag-2.2-aa.md): contrast
  (4.5:1 text / 3:1 UI, in light **and** dark), never colour alone, visible focus + focus order +
  focus-not-obscured (2.4.11/2.4.12), 24x24px targets (2.5.8), full keyboard path + no trap,
  dragging alternatives (2.5.7), reflow & text-spacing, prefers-reduced-motion (2.3.3), ARIA
  roles/states/names, accessible name + label, alt text, error identification, consistent help.
- **contrast** — make AA un-violatable by construction. [references/contrast-as-token.md](references/contrast-as-token.md)
  shows how to derive the on-colour (text/icon foreground) from a surface token's **relative
  luminance** so a palette can never emit an inaccessible pairing — plus the APCA (WCAG 3 draft)
  alternative and the CSS (color-contrast(), relative-colour syntax, light-dark()) that does it live.

## How you work

1. **Lead with the gate, don't trail it.** In build mode, treat AA as a constraint on every
   colour, focus state, target, and motion decision *as you make it* — not a later audit.
2. **Prefer structural accessibility over checked accessibility.** Where a token can guarantee the
   property (contrast-as-token, focus-visible as a token, a reduced-motion variant baked into the
   motion token), do that — a property the system cannot violate beats a property you re-verify.
3. **Audit observes, it does not assert.** In audit mode, ground every finding in a real check
   (a keyboard pass actually run, a contrast ratio actually computed) — never claim a criterion
   passes from inspection alone. Tooling catches a minority; the keyboard + screen-reader passes
   catch the rest.
4. **Report in the gate's shape** — criterion, location, severity, fix — so the Developer can act
   on it directly. You specify the requirement; the Developer implements it.

## Versioning

Own skill. Bump metadata.version on any change (PATCH: wording/refs · MINOR: new mode/criteria
coverage · MAJOR: method-contract change). Regenerate VERSIONS.md with
python3 star-alliance-skills/skillsmith/scripts/skill_registry.py write, then python3 build.py.

## Changelog
- **1.0.0** — Initial release. WCAG 2.2 AA as a designer-owned gate. Three modes — audit (the
  repeatable pre-ship pass + finding/report shape), build (the designer-owned AA criteria), and
  contrast (contrast-as-token: derive the on-colour from surface luminance so AA is structurally
  un-violatable). Authored in the 2026-06-27 the-designer deep-audit follow-up.
