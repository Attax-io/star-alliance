---
name: ux-copywriting
metadata:
  version: 1.0.0
type: Skill
description: "Write functional in-product copy — the words a user reads while operating an interface. Covers microcopy (buttons, labels, tooltips, placeholders), state copy (error, empty, loading, success), onboarding and permission prompts, form help text, and confirmation or destructive-action wording, all held to one voice and tone and to plain-language accessibility. Use to write or fix the literal text inside a UI. Triggers: 'write the error message', 'microcopy for this button', 'empty-state copy', 'onboarding copy', 'reword this confirmation', 'name this label'. NOT design-language (brand voice and world or lore narrative — how a product sounds, not what its controls say). NOT article-creator (long-form marketing or editorial). NOT growth-marketing (campaigns, ads, lifecycle email). The smallest unit of product writing: the sentence on the button."
---

# UX Copywriting — the words inside the interface

This is the craft of **functional in-product copy**: the text a person reads while using a product,
not the text that sells it. A label, an error, an empty state, a confirm dialog — each is a tiny
piece of interface that happens to be made of words. Write it so the user always knows what just
happened, what to do next, and what will happen if they act.

## What it is / is not

- It **is** the *functional* layer: microcopy for controls (buttons, labels, tooltips, placeholders,
  menu items), state copy (error / empty / loading / success / zero-results), onboarding and
  permission prompts, inline form help and validation, and confirmation / destructive-action wording.
  It governs **what a control says and how a state explains itself** — held to one voice/tone and to
  plain-language, screen-reader-friendly accessibility.
- It is **NOT** `design-language`. That picks a product's *narrative voice and world* — vocabulary,
  lore, naming conventions, tone of address (forge, vault, codex). UX copy *inherits* that voice but
  applies it to the literal mechanics of operating the UI. Voice is the accent; UX copy is the
  instruction spoken in it.
- It is **NOT** `article-creator` (long-form marketing, editorial, docs prose).
- It is **NOT** `growth-marketing` (campaigns, ads, lifecycle/nurture email, positioning).
- It is **NOT** visual styling (`design-taste`) or layout — though copy length and line-breaks are a
  design constraint, so write to the space you are given.

If the deliverable is a sentence a user reads *while clicking*, it is this skill. If it is a sentence
that runs *before they ever arrive* (an ad, a landing headline, a blog post), it is not.

## Principles

Seven generative axioms. Compose them; do not run them as a checklist.

### 1. Lead with the user's next action, not the system's state

Copy exists to move someone forward. Name the action or the resolution first; demote the mechanism.
A button is a verb the user is about to perform, so label it with *their* outcome.

- Weak (system-voiced): `Submit` · `Error: request failed` · `No data`
- Strong (action-voiced): `Send invite` · `We couldn't save your changes — try again` · `No invoices yet — add your first one`

A control labeled with the result it produces (`Delete account`, `Export as CSV`, `Pay $40`) is
self-documenting; one labeled with a generic mechanic (`OK`, `Submit`, `Confirm`) makes the user
guess what they are agreeing to.

### 2. Every state is a sentence the UI owes the user

Empty, loading, error, success, and zero-result states are not decoration — they are the product
talking. An unstyled state is a dropped sentence. Each owes the user one of: *what happened*, *why*,
and *what to do now*.

- **Empty:** explain the space and offer the first step. `No projects yet. Create one to get started.`
- **Error:** say what failed, in plain terms, plus a recovery path — never a stack trace or a code alone.
  `That email is already registered. Sign in instead?`
- **Loading:** if it may take a while, say what is happening. `Generating your report — about 10 seconds.`
- **Success:** confirm and point at the natural next move. `Invite sent. Add another?`
- **Zero results:** distinguish *nothing matched* from *nothing exists*, and offer a way out
  (clear filters, broaden, create).

See `references/state-copy-patterns.md` for the full per-state template set.

### 3. Concision is a feature, not a style — cut every word that isn't load-bearing

In an interface, words cost attention and screen space. The shortest phrasing that stays *clear and
specific* wins. Cut filler ("please", "in order to", "simply", "just"), cut hedges, cut anything the
user already knows from context. But never cut at the expense of meaning — `Delete` alone is shorter
than `Delete this comment`, yet the second prevents a wrong, irreversible click.

- `In order to continue, please click here` → `Continue`
- `An error has occurred while attempting to process your request` → `Something went wrong — try again`
- Concision ≠ terseness: a destructive confirm earns more words, not fewer (principle 6).

### 4. One voice, calibrated tone — same product, different moments

Voice (who the product is) stays constant; tone (how it speaks *right now*) flexes to the user's
emotional state. Be warmer in onboarding and success, plainer and more deferential in errors and
destructive moments. Never be cute where the user is anxious — a failed payment is not the place for
a pun. Inherit the project's voice from `design-language`; this skill decides the *tone dial* per moment.

See `references/voice-and-concision.md` for the tone-by-moment map and the voice-consistency checks.

### 5. Make consequences legible before the user commits — especially destructive ones

The user must understand what an action does *before* they take it. For ordinary actions, a clear
verb-label is enough. For irreversible or costly ones, spell out the scope, the permanence, and the
fallback — and label the confirm button with the actual action, never a generic `Yes`/`OK`.

- Destructive confirm: title states the object, body states the permanence, button states the act.
  `Delete 3 projects? · This can't be undone. Their files and history will be removed. · [Delete projects] [Cancel]`
- Match the danger to the friction: a benign toggle needs no dialog; deleting an account may warrant
  typing the name to confirm. Don't over-gate the harmless or under-gate the unrecoverable.
- Permission prompts follow the same rule: say *why* you need the access and *what the user gets*,
  right before the OS dialog — `Allow camera access to scan documents.`

### 6. Write for the screen reader and the plainest reader at once

Accessible copy is just clearer copy. Plain language, no jargon, no idioms that don't translate, no
meaning carried by color or icon alone. Labels must stand on their own when read aloud out of visual
context: an icon-only button still needs an accessible name; `Click here` is meaningless to a
screen-reader user scanning links. Error text must be programmatically tied to its field, not just
shown nearby.

- Link text describes its destination: `Click here` → `View billing history`.
- Icon button → real label: trash icon → `aria-label="Delete comment"`.
- Don't encode state in color words: `the red fields` → `the required fields marked below`.

See `references/accessible-copy.md` for the screen-reader, plain-language, and i18n rules.

### 7. Write to the real context — surface, length budget, and locale

The same idea needs different copy in a 30-character mobile toast versus a desktop modal. Write to the
actual space, the actual surface, and the actual reader. Account for translation expansion (German and
Finnish run ~30% longer than English), never concatenate sentence fragments into one string (it breaks
grammar in other languages), and never hardcode data into copy that a variable should carry.

- Respect the length budget the design gives you; if the truth doesn't fit, change the layout, don't
  lie by truncation.
- Keep full sentences as single translatable units; don't build `You have` + `5` + `new messages` from
  three glued strings.

## References

- `references/state-copy-patterns.md` — per-state templates and worked examples for error, empty,
  loading, success, zero-results, onboarding, and permission prompts.
- `references/voice-and-concision.md` — the tone-by-moment map, the concision passes, and voice-
  consistency checks against a project's `design-language`.
- `references/accessible-copy.md` — plain-language, screen-reader, and internationalization rules for
  in-product text.
