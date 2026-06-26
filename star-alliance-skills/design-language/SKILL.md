---
name: design-language
description: "Pick and enforce a project's NARRATIVE VOICE — its vocabulary, lore, naming conventions, and tone of address. This is the words-and-world layer, NOT visual styling: it decides how a thing is *named and spoken*, never how it *looks* (that is `design-taste`). One multi-mode engine holding one verbatim playbook per language; add new languages by dropping a reference in. Languages: fallen-sword (dark-fantasy MMORPG / Erildath); star-alliance (the guild-dev meta-voice — forge, sigil, quest, wave, conformity); lex-council (the legal-finance product voice — vault, codex, ledger, certify, statute). Use when writing copy, UI strings, docs, commit prose, or member dialogue that must sound like a specific world. Triggers: 'use the X voice', 'make it sound like Fallen Sword', 'write this in the guild voice', 'Lex Council tone', 'reskin this copy', 'Erildath', 'pick a design language'. NOT for how the UI looks — that is `design-taste` (visual). NOT for identity/logo — that is `brandkit`."
metadata:
  version: 1.0.0
---

# Design Language — the guild's voice engine

This is the one craft for **deciding and enforcing how a project sounds and what it calls things.**
Pick the world a surface should speak in, load that language's playbook, and reskin the copy,
strings, docs, and dialogue into one consistent voice. One skill, many languages — add more by
dropping a `references/*.md` in.

## What it is / is not

- It **is** the *words-and-world* layer: vocabulary, lore, naming conventions, tone of address.
  It governs how a thing is **named and spoken**.
- It is **NOT** `design-taste`. That is the *visual* taste engine — typography, colour, layout, motion,
  how a thing **looks**. The two are orthogonal axes: `design-taste` dresses the pixels, `design-language`
  scripts the words. A surface usually wants both, but you pick them separately. **If the request is about
  appearance, style, or "make it premium" — that is `design-taste`, not this skill.**
- It is **NOT** `brandkit` — that defines identity (logo, palette, the brand *system*). A language consumes
  an established identity's terms; it doesn't mint the brand.

## The languages

| Language | Pick it when | Full playbook |
|---|---|---|
| `fallen-sword` | A game/quest project wants dark-fantasy MMORPG voice — Erildath, guilds, stamina, loot | `references/fallen-sword.md` |
| `star-alliance` | Writing *about the guild itself* — skills, members, workflows, releases; the dev meta-voice | `references/star-alliance.md` |
| `lex-council` | Copy, UI strings, or docs for the Lex Council product — the legal-finance council voice | `references/lex-council.md` |

- **`fallen-sword`** — the original. Dark fantasy, old-school MUD roots, item-driven combat, the world of
  Erildath. Maps plain English to quest/guild/stamina/corruption→cleanse. For game projects and lore-heavy tone.
- **`star-alliance`** — the meta-voice this framework uses to describe its *own* operations: skills are
  **forged**, members carry **weapons**, big work is a **conquering campaign** split into **waves**, the
  registry holds the **star map**, and everything must pass **conformity**. For commit prose, skill bodies,
  member dialogue, and dashboard copy.
- **`lex-council`** — the product voice of the Lex Council app: a legal-financial council. The **vault**
  holds records, the **codex** holds the law, the **ledger** holds transactions, admins **certify** and
  **seal**, and rules are **statutes**. For UI strings, changelogs, and client-facing copy.

## Shared laws (every language obeys)

- **One world per surface.** Never blend two languages in the same copy — pick the language the surface lives in.
- **Map, don't decorate.** A language is a *substitution table* (plain term → world term) plus a tone, not
  a sprinkle of flavour words on otherwise-plain text. Reskin consistently or not at all.
- **Stay grounded in the real lexicon.** Use the terms the world actually uses (the playbook lists them).
  Don't invent new world-words that aren't in the reference — that drifts the voice.
- **Voice serves clarity, never buries it.** If the reskin makes an instruction ambiguous, the plain meaning
  wins. Epic but legible.
- **Voice ≠ look.** This skill never touches CSS, colour, or layout. If you reach for a hex code, you're in
  the wrong skill — switch to `design-taste`.

## How the engine works

1. **Pick the language** from the table — by the world the surface belongs to.
2. **Load that language's `references/*.md`** for the full vocabulary map, tone notes, and re-skin examples.
   The dispatcher above is the index; the detail lives in the reference so this file stays lean.
3. **Reskin against the map** — run the plain copy through the language's substitution table, then adjust
   tone (sentence shape, register) to match the playbook's writing-style notes.
4. **Run the consistency test** — every domain term reskinned, no plain leftovers, no cross-language bleed,
   meaning still unambiguous.

## Sharpening the craft

- **Apprentice** — applies one language's substitution table literally. Measure: zero plain-term leftovers.
  Outgrow: flavour-sprinkling without consistency; mixing two worlds.
- **Journeyman** — matches tone, not just vocabulary (the register and sentence shape of the world), and
  knows which surfaces *shouldn't* be reskinned (error codes, legal text). Measure: voice reads native.
- **Artisan** — extends a language's reference with newly-attested terms as the project's real vocabulary
  grows, keeping the map current. Measure: the playbook never lags the product's actual words.
- **Master** — adds a coherent **new language** as an eighth `references/*.md` when a project needs a voice
  none of the existing ones carry. Measure: languages promoted into the engine. Outgrow: novelty over fidelity.

## Gotchas

- **Name collision with `design-taste` is real.** "design language" reads as *visual* to most callers. If a
  request is about appearance ("make it premium", "pick a style", "minimalist") it belongs to `design-taste`,
  not here. This skill is strictly the *words/world* axis — keep the description's NOT-clauses intact so the
  two don't cross-trigger.
- **Don't fabricate vocabulary.** Each language's terms are harvested from how the project *actually* speaks.
  Adding invented world-words drifts the voice; extend a reference only with terms the project really uses.
- The detail lives in `references/`; resist re-inflating this SKILL.md — keep it a lean dispatcher.

## Versioning
Own skill (generalises the former `fallen-sword-design-language` into a multi-language engine). Bump
`metadata.version` on any change (PATCH: wording/refs · MINOR: new language/reference · MAJOR: method
contract change). Regenerate `VERSIONS.md` with
`python3 star-alliance-skills/skillsmith/scripts/skill_registry.py write` (no `--repo` — it auto-resolves
the git root via the `VERSIONS.md`+`.git` marker), then `python3 build.py`.

## Changelog
- **1.0.0** — Initial release. Generalises `fallen-sword-design-language` into a multi-language voice engine;
  the original Fallen Sword playbook preserved verbatim under `references/fallen-sword.md` as mode #1, joined
  by `star-alliance` (guild-dev meta-voice) and `lex-council` (product voice). Distinct from `design-taste`
  (visual) and `brandkit` (identity).
