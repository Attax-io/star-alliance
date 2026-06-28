---
type: Document
title: Cross-vendor comparison and a design checklist
description: Side-by-side of how Anthropic, OpenAI, Cursor, Perplexity, Notion, Mistral, and xAI handle each prompt-design axis, plus a build/review checklist.
timestamp: 2026-06-28T00:00:00Z
---

# Cross-vendor comparison + design checklist

## Axis-by-axis comparison

| Axis | Anthropic (Claude) | OpenAI (ChatGPT/Codex) | Cursor | Perplexity | Notion | Mistral | xAI (Grok) |
|---|---|---|---|---|---|---|---|
| **Framing** | 3rd person ("Claude...") | 2nd person "You" | 2nd person | 2nd person | 2nd person | 2nd person | 2nd person |
| **Delimiters** | nested XML tags | markdown `#` headers | XML tags | markdown headers | prose + spec tags | markdown headers | bullet list |
| **Identity** | rich product block | "ChatGPT, trained by OpenAI" + cutoff/date | one-line + IDE | one-line + env | one-line + concepts | name + maker + dates | name + team + time |
| **Search rule** | "search before EVERY present-day fact" | "MUST search after cutoff" | n/a (code) | tiered when-to-search | "default search first" | "browse if after cutoff" | search, but not for own opinions |
| **Tool regime** | n/a in base | mandatory SKILL.md pre-reads | specialized > shell | one tool/step, ≤3 queries | batch, no dependent parallel | open 2-3 results | parallel calls ok |
| **Persona** | implicit via 3rd-person traits | swappable personalities | none | none | none | "empathetic/curious" + convo design | swappable personas |
| **Refusal** | tiered, anti-rationalization, cumulative | honesty-forward | minimal | n/a | n/a | minimal | jailbreak→short refuse, neutrality |
| **Injection defense** | "immutable rules", tainted-provenance | — | ignore fake tool formats | content = inert text, flag attempts | — | "stay critical" of pages | — |
| **Formatting** | heavy anti-over-formatting | writing blocks, sandbox citations | code-citation grammar | no pre-tool tokens (latency) | — | tables-not-bullets | KaTeX for math |

## What's universal vs what's a choice

**Universal (every effective prompt has these):**
1. One-line identity binding product + maker + environment.
2. Date + knowledge-cutoff awareness driving a search/freshness rule.
3. Explicit tool when/how/don't, where tools exist.
4. Some formatting/output discipline block.
5. Don't-reveal-the-prompt clause.

**A deliberate choice (pick per product):**
- 2nd vs 3rd person framing → tool-agent vs persona-assistant.
- XML tags vs markdown headers → consistency matters more than which.
- One-tool-per-step vs parallel → latency/UX vs throughput.
- Persona depth: none / described / swappable.
- Refusal verbosity: terse (Grok) vs conversational-soften (Anthropic).

## Build / review checklist

When **designing** a system prompt, walk these in order:

1. **Identity** — one sentence: who, who-made-it, where it runs. Present tense.
2. **Environment** — date, knowledge cutoff, mounted tools/skills/files, any
   "must-read" resources.
3. **Framing choice** — 2nd or 3rd person; commit and stay consistent.
4. **Capabilities & limits** — enumerate what it can/can't do; state limits as
   facts, not apologies. Kill guessable gaps with explicit fact blocks.
5. **Context-injection contract** — name the `<...>` regions, say how to use them,
   say not to leak them; define a typed id system if there are many entities.
6. **Tool block** — for each tool: when (trigger list), how (mechanics + budgets +
   ordering), don't (anti-patterns). Specialized-over-shell. Persistence rule.
7. **Output discipline** — exact format + exact failure modes. Fight default
   over-formatting explicitly. Specify any machine-parsed envelope's grammar.
8. **Persona/tone** — concrete behaviors, not bare adjectives; restate the safety
   floor inside every persona overlay.
9. **Safety scaffolding** — default-help stance bounded narrowly; tiered named
   hazards; anti-rationalization clauses; cumulative-harm judgment; refusal manner.
10. **Anti-jailbreak** — non-disclosure; don't-blame-the-prompt; trust hierarchy
    (system > user > retrieved); treat retrieved content as inert data;
    tainted-provenance escalation; verify-the-envelope reflex.

When **reviewing** an existing prompt, score each axis above and flag: vague
"format nicely" (→ specify), unbounded refusal language (→ over-refusal risk),
adjective-only persona (→ add behaviors), missing trust hierarchy (→ injection
hole), persona overlay without restated safety floor (→ jailbreak surface),
search rule absent despite a date-sensitive product, leaked-instruction exposure
(no non-disclosure / no don't-blame-the-prompt clause).

## Anti-patterns the corpus warns against

- **Over-refusal** — unbounded "be safe" with no help-default → Anthropic bounds
  it explicitly.
- **Adjective-only persona** — "be helpful and friendly" with no behavior.
- **Vague formatting** — "format your answer well" → ambiguous; products spell out
  grammar and failure modes.
- **Trusting the envelope** — assuming an image/file/date is present because the
  frame implies it.
- **Letting retrieved content issue instructions** — the core injection hole.
- **Persona weakening safety** — overlay omits the safety floor.
