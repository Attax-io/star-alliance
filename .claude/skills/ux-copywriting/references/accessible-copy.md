---
type: Document
title: ux-copywriting — accessible and international copy
description: Plain-language, screen-reader, and internationalization rules for in-product text.
timestamp: 2026-06-28T00:00:00Z
---

# Accessible and international copy

Accessible copy is just clearer copy (SKILL principle 6), written for the plainest reader, the screen
reader, and the translator at once (principle 7). These are the operating rules.

## Plain language

- Prefer common words: `use` over `utilize`, `help` over `facilitate`, `start` over `commence`.
- Short sentences. One clause where one clause will do.
- No jargon or internal terms in user-facing copy. The user does not know your API names, your table
  names, or your team's slang. `Sync failed (RLS denied)` → `We couldn't load your data. Try again.`
- No idioms that don't survive translation or literal reading: `piece of cake`, `hit the ground
  running`, `back to square one`. They confuse non-native readers and screen-reader users alike.
- Reading level: aim for roughly grade 6–8. Simpler is rarely worse in an interface.

## Screen-reader and structural rules

- **Every interactive element has an accessible name.** An icon-only button needs a real label:
  trash icon → `aria-label="Delete comment"`, not nothing and not `aria-label="icon"`.
- **Link text describes its destination.** `Click here`, `Read more`, `Learn more` are meaningless to
  a user scanning links out of context. → `View billing history`, `Read the refund policy`.
- **Never carry meaning in color or icon alone.** `Fix the fields in red` excludes color-blind and
  screen-reader users. → `Fix the required fields marked below.` Pair every color/icon signal with text.
- **Tie error text to its field programmatically** (`aria-describedby`), not just visually near it, so
  it is announced when the field gets focus.
- **Don't rely on placeholder text as the only label** — placeholders vanish on input and are poorly
  announced. Keep a persistent visible label.
- **Announce dynamic changes.** Toasts, inline validation, and live results need a live region so a
  screen reader hears them; copy that only appears visually is silent to non-visual users.

## Internationalization (i18n)

- **Keep full sentences as single translatable strings.** Never build a sentence by concatenating
  fragments — `You have` + count + `messages` breaks pluralization and word order in most languages.
  Use one parameterized string with proper plural rules: `{count, plural, one {# message} other {#
  messages}}`.
- **Budget for expansion.** German, Finnish, and Russian commonly run 30–40% longer than English; some
  UI labels double. Don't design a button that only fits the English word.
- **Don't hardcode data into copy.** Names, counts, dates, currencies belong in variables with
  locale-aware formatting, not baked into the string.
- **Avoid culture-bound metaphors and examples.** Holidays, sports, and pop-culture references don't
  localize.
- **Mind directionality.** Copy may render right-to-left (Arabic, Hebrew); don't assume left-aligned
  layout or leading icons.

## Quick audit checklist

Before shipping user-facing strings, confirm:

- [ ] No jargon, internal names, or error codes shown alone.
- [ ] Every icon-only control has an accessible name.
- [ ] No link says only "click here" / "read more".
- [ ] No instruction depends on color or position words alone.
- [ ] Error text is tied to its field and announced.
- [ ] Sentences are whole translatable units, not glued fragments.
- [ ] Data (names, counts, dates) lives in variables, not the literal string.
