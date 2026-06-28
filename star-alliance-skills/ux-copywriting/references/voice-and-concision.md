---
type: Document
title: ux-copywriting — voice, tone, and concision
description: The tone-by-moment map, the concision passes, and voice-consistency checks against a project's design-language.
timestamp: 2026-06-28T00:00:00Z
---

# Voice, tone, and concision

Voice is constant; tone flexes (SKILL principle 4). Concision is a feature (principle 3). This file is
the operating detail for both.

## Voice vs tone

- **Voice** = the product's stable personality: its vocabulary, its level of formality, whether it
  says "we" or speaks impersonally, whether it uses the project's lore terms. This is *inherited* from
  `design-language` — UX copy does not invent voice, it applies it. Before writing, read the active
  voice playbook (e.g. star-alliance: forge/sigil/quest; lex-council: vault/codex/certify).
- **Tone** = how that voice modulates for the moment. The same voice is reassuring in an error,
  celebratory at a milestone, and matter-of-fact in a label.

If a string sounds like a different product than the rest of the app, the voice broke. If it sounds
tone-deaf to the user's current feeling, the tone broke.

## Tone-by-moment map

| Moment | User's state | Tone dial |
| --- | --- | --- |
| Onboarding / empty | curious, unsure | warm, encouraging, value-first |
| Routine label / button | task-focused | plain, neutral, action-named |
| Success (routine) | satisfied | brief, light |
| Success (milestone) | proud | celebratory, but earned |
| Error (recoverable) | mildly frustrated | calm, plain, blame-free, fix-forward |
| Error (data loss / failure) | anxious | sober, honest, apologetic, escape-route |
| Destructive confirm | cautious | precise, serious — no jokes |
| Permission prompt | guarded | transparent, benefit-led, reassuring on privacy |

Rule of thumb: **the more anxious the user, the plainer and more human the copy.** Wit lives in the
low-stakes moments only.

## Concision passes

Run these reductions in order; stop when further cutting removes meaning.

1. **Kill filler.** "please", "simply", "just", "in order to", "kindly", "that you'd like to".
   `In order to simply get started, please just click here` → `Get started`.
2. **De-hedge.** "might", "should", "we think" — say it or don't. `This might not work` → say what to do.
3. **Drop the obvious.** If the screen title already says "Settings", a button needn't say "Settings — Save".
4. **Verb up.** Replace noun-phrases with verbs: `Initiate a deletion of the file` → `Delete file`.
5. **One idea per string.** Split compound instructions; let the UI sequence them.

Stop-loss: never cut below clarity (principle 3). `Delete` → keep `Delete project` if the object is
ambiguous. Concision serves comprehension; it never overrides it.

## Voice-consistency checks

Before shipping a set of strings, scan for:

- **Person drift** — does the app say "you"/"we" consistently, or flip to passive/impersonal mid-flow?
- **Casing drift** — sentence case vs Title Case on buttons and headers, applied uniformly?
- **Verb-tense drift** — labels are imperative (`Save`), states are present/past (`Saving…` / `Saved`).
- **Terminology drift** — one name per concept. If it's a "project" don't also call it a "workspace".
  Cross-check against the `design-language` glossary for the active project.
- **Punctuation drift** — pick a rule for periods on buttons/labels (usually none) and toasts (usually
  none) and hold it.

A consistency miss reads as low quality even when each string is individually fine. Treat the string
set as one voice, not a pile of sentences.
