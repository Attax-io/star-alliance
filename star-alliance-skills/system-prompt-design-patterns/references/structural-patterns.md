---
type: Document
title: Structural patterns of production system prompts
description: How shipped system prompts are organized — spine order, delimiters, framing, capability declarations, context-injection contract.
timestamp: 2026-06-28T00:00:00Z
---

# Structural patterns of production system prompts

How shipped prompts are *organized*. Distilled from leaked production prompts
(Anthropic Claude, OpenAI ChatGPT/Codex, Cursor, Perplexity, Notion, Mistral,
xAI Grok). Patterns, not copies.

## 1. Identity → environment → behavior → tools → safety (the spine)

Almost every production prompt opens with a one-line identity, then states the
runtime environment, then layers behavior, tools, and safety. Order matters:
the model reads top-to-bottom and later sections assume the earlier frame.

- **Identity line.** First sentence, present tense, names the product and maker:
  - Cursor: "You are an AI coding assistant, powered by {model_name}. You operate in Cursor."
  - Perplexity: "You are Perplexity Assistant, created by Perplexity, and you operate within the Perplexity browser environment."
  - Notion: "You are Notion AI, an AI assistant inside of Notion."
  - Mistral: "You are a conversational assistant... built by Mistral and power a chatbot named Le Chat."
  The identity binds *who*, *who-made-it*, and *where-it-runs* in one breath.

- **Environment block.** What's mounted, what date it is, what files/skills exist.
  OpenAI Codex/ChatGPT uses an explicit `# Environment` with `Knowledge cutoff`
  and `Current date`, then lists mounted skills as paths the model "*must* read."
  The date/cutoff pairing is near-universal and load-bearing for the search rule.

- **Behavior, then tools, then safety.** Behavior (tone, formatting, persistence)
  comes before tool mechanics; safety scaffolding is often last and framed as
  overriding everything above it.

## 2. Delimiter discipline: tag the regions

Production prompts fence sections so instructions don't bleed. Two dominant styles:

- **XML-ish tags** (Anthropic, Cursor): `<claude_behavior>`, `<search_first>`,
  `<refusal_handling>`, `<tone_and_formatting>`, `<lists_and_bullets>`,
  `<tool_calling>`, `<making_code_changes>`, `<citing_code>`. Tags are *named for
  the rule they hold*, nest, and double as anti-injection markers (content outside
  the trusted tags is suspect).
- **Markdown headers** (OpenAI, Perplexity, Notion, Mistral): `# Environment`,
  `# Instructions`, `## Web Search Tools`, `# STYLING INSTRUCTIONS`.

Pick one and stay consistent. The win is the same: a parser-friendly map so a
later rule can reference an earlier region, and so the model can tell *its own
instructions* apart from *user/web content*.

## 3. Third-person vs second-person framing

A real fork in the road:

- **Anthropic writes Claude in the third person**: "Claude defaults to helping,"
  "Claude avoids over-formatting." This makes the prompt a *character description*
  the model inhabits, and reads as policy about an entity rather than commands.
- **Everyone else writes "You"**: "You are an agent — keep going until..."
  (Perplexity), "You MUST use the Read tool" (Cursor).

Third-person suits a consumer assistant with a stable persona; second-person
imperative suits a tool/agent with a task to finish. Choose by product type.

## 4. Capability and limitation declarations are explicit, not implied

Strong prompts *enumerate* what the model can and cannot do, removing guesswork:

- Perplexity: "You cannot download files. If the user requests file downloads,
  inform them this action is not supported and do not attempt to download."
- Notion spends paragraphs defining the loop: "You may end the loop by replying
  without any tool calls... You are not an agent that runs on a trigger in the
  background." It states the *shape of agency* before any task.
- Anthropic's `<product_information>` is a long factual block ("the currently
  selected version is Claude Opus 4.8... API model strings are...") so the model
  answers product questions correctly instead of hallucinating.

Principle: anywhere the model would otherwise *guess* a capability, a fact, or a
boundary, the prompt states it outright. Limitations are framed as facts, not
apologies.

## 5. Context-injection contract (the `<...>` envelope)

Agentic prompts define a vocabulary for runtime-injected context and tell the
model how to treat it:

- Cursor: "The system may attach `<system_reminder>`, `<attached_files>`,
  `<system_notification>`. Heed them, but do not mention them directly in your
  response as the user cannot see them."
- Perplexity defines an **ID system**: every piece of injected info carries a
  `{type}:{index}` id (`tab:2`, `web:5`, `calendar_event:3`) used for tool calls
  and citations. A typed handle makes references unambiguous.
- Anthropic: "A prompt implying an image is present doesn't mean one is... Claude
  checks for itself." — never trust the envelope blindly.

The contract has three parts: (a) *name* the injected regions, (b) say *how to
use* them, (c) say *not to leak* them to the user.

## 6. Length and altitude self-management

Prompts tell the model how *much* to say and at what level:

- Anthropic: "keeps responses focused, brief, and concise... gives a high-level
  summary unless an in-depth one is specifically requested."
- Mistral "Economy of Language": active voice, concrete details, "Do not make 5+
  element lists unless explicitly asked."

This is the formatting layer (covered fully in `tool-use-and-refusal.md`), but
structurally it always lives in its own block so it's easy to override per-style.
