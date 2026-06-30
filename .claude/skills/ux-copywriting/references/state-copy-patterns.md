---
type: Document
title: ux-copywriting — state copy patterns
description: Per-state templates and worked examples for error, empty, loading, success, zero-results, onboarding, and permission-prompt copy.
timestamp: 2026-06-28T00:00:00Z
---

# State copy patterns

Every UI state is a sentence the product owes the user (SKILL principle 2). This is the template set.
Each pattern names the slots to fill; fill them in the project's voice, at the moment's tone.

## The universal triad

Most state copy answers up to three questions, in this order of priority:

1. **What happened / what is this?** (orientation)
2. **Why?** (only when it changes what the user does)
3. **What now?** (the next action — almost always required)

Drop "why" when it doesn't help. Never drop "what now".

## Error states

Structure: *plain statement of what failed* + *recovery path*. Never a bare code, never a stack trace,
never blame the user.

- Validation (inline, tied to the field): `Enter a valid email address.`
- Conflict: `That username is taken. Try another?`
- Recoverable system error: `We couldn't save your changes. Check your connection and try again.`
- Unrecoverable: say so honestly + give an escape: `This link has expired. Request a new one.`
- Include an error code only as a *secondary* detail for support, never as the whole message.

Anti-patterns: `Error 500` · `Invalid input` · `Something went wrong` *with no next step* ·
`You entered the wrong password` (prefer `That password doesn't match — try again or reset it`).

## Empty states

The space has nothing in it *yet*. Orient + invite the first action. This is an onboarding moment in
disguise — the friendliest tone.

- `No projects yet. Create your first one to get started. [New project]`
- `Your inbox is clear. New messages will show up here.`
- Distinguish *empty-by-success* (`All caught up!`) from *empty-by-default* (`No invoices yet`).

## Zero-results states

Different from empty: the user searched/filtered and nothing matched. Always offer an exit.

- `No results for "<query>". Check the spelling or try a broader search.`
- `No transactions match these filters. [Clear filters]`
- Distinguish *nothing matched* from *nothing exists* — they need different next actions.

## Loading states

If it resolves instantly, say nothing (a spinner suffices). If it may take noticeable time, narrate.

- Short, indeterminate: `Loading…`
- Long, known work: `Generating your report — this can take up to a minute.`
- Multi-step: name the current step (`Uploading 3 of 5…`).
- Never lie about progress; never show a frozen `99%`.

## Success / confirmation states

Confirm the result, then point at the natural next move. Keep it brief — the user already succeeded.

- Toast: `Invite sent.`
- With next step: `Report exported. [Download] [Export another]`
- Don't over-celebrate routine actions; save emphasis for genuine milestones.

## Onboarding copy

Teach by doing, one idea per step. Lead with the user's benefit, not the feature name.

- Value-first: `Connect a bank to see all your spending in one place.` (not `Plaid integration`)
- Keep steps skippable; never trap the user. `Skip for now` is a kindness.
- Progressive disclosure: introduce a feature at the moment it becomes relevant, not all upfront.

## Permission prompts

Pre-prime *before* the OS dialog: say why you need the access and what the user gets. The OS dialog
itself is not editable, so the priming screen carries the persuasion.

- `Allow notifications to get told when your transfer completes.`
- `Allow camera access to scan documents — we never store the photos.`
- Ask at the point of need, not on first launch. A permission requested in context is granted far more
  often than one requested cold.

## Worked example — one action, all states

A "Send invite" flow:

- Button: `Send invite`
- Loading: `Sending…`
- Success: `Invite sent to ana@x.com.`
- Error (recoverable): `Couldn't send the invite. Try again.`
- Error (validation): `Enter an email address to invite.`
- Empty (no invites yet): `No teammates yet. Invite someone to collaborate. [Send invite]`
