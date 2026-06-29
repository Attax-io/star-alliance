---
type: Document
title: Cross-vendor pattern extensions (newer leaked prompts)
description: Eighteen additional production system-prompt patterns mined from newer leaks — context/memory priority, latency-aware emission, follow-up discipline, multi-agent framing, values-as-axioms, custom-UI routing, voice markup, memory-tool schema, intent disambiguation, design-to-domain framing, token-budget declaration, safety-tiered model differentiation, temporal artifact suppression, aggressive search-first mandate, cumulative-output weapons review, lead-with-outcome and completeness-before-stop, multi-channel message routing, and sensitive decision scope gate — each with vendor evidence.
| timestamp: 2026-06-30T00:00:00Z
---

# Cross-vendor pattern extensions

Eighteen patterns from leaked prompts (newer layers P11–P18 add eight) that the
core references do not yet cover. Each is grounded in a shipped prompt and names
the vendor. Read alongside the four core references; these extend, not replace,
them.

## 1. Context/memory priority — outrank re-asking, silently check (OpenAI gpt-5.5-instant)

A standing instruction that the user's existing context and memory take precedence
over asking again, enforced with a penalty framing and a pre-answer self-check.

- OpenAI gpt-5.5-instant: "Penalties apply for asking for information already
  present in the user context, ignoring context that improves correctness, or using
  unrelated context. Before answering, **silently check: did I miss a context item**
  that would make the answer more correct, more specific, or avoid a question? If
  yes, revise to use it naturally."
- It also gates a memory-retrieval tool on plausibility, not on the visible profile:
  "internally decide whether user-specific memory could plausibly affect the
  answer... A visible User Bio/profile snippet is NOT proof you have enough; it is a
  clue that more memory may matter." A call is required for "ambiguous requests where
  user memory could clarify the intended target, tone, project, or next step."

Design rule: rank known context above re-asking, make the check **silent** (no "let
me check your memory" narration), and treat a visible profile as a *hint to fetch
more*, never as sufficiency. Pairs with the verify-the-envelope reflex (core §D):
absence of a fact in the frame is not proof of its absence in memory.

## 2. Latency-aware output — emit the tool call before any reasoning tokens (Perplexity)

When a tool call is inevitable, suppress all pre-call prose so the first emitted
token is the call itself, cutting time-to-first-tool.

- Perplexity (comet browser assistant): "**NEVER output any thinking tokens,
  internal thoughts, explanations, or comments before any tool. Always output the
  tool directly and immediately**, without any additional text, to minimize latency.
  This is VERY important."

Design rule: for latency-sensitive products, make tool emission the *first* action,
not the conclusion of visible reasoning. This is distinct from the formatting layer
(core tool-use §C lists it as a formatting note) — here it is an explicit
*ordering* contract: call first, narrate after (or not at all). Trade-off: you lose
the streamed "I'm searching for X" affordance, so reserve it for products where
latency beats transparency.

## 3. Follow-up discipline — a 3-mode terminal rule (Google gemini)

Instead of always or never appending a follow-up question, the prompt branches the
ending on the *shape* of the request.

- Google gemini-3.5-flash, FOLLOW-UP RULES:
  - **RULE 1 — STRICT COMPLETION**: if the prompt has a definitive answer (facts,
    math, translations), is a self-contained task (trivia, riddles, roleplay), or
    dictates strict rules (JSON, word counts) → answer exactly and "**Remove any
    follow-questions, menus or numbered/bulleted options at end of response (even in
    roleplays).**"
  - **RULE 2 — EXPERT GUIDE**: only if the prompt is broad, ambiguous, or explicitly
    seeks advice → answer, then "**ask a single relevant follow-up question**." "If
    unsure, default to Rule 1."
  - Path C (self-contained → omit follow-ups) is the default; "**Never repeat a
    follow-up.** Force Path C if Terminal, Wait Rule applies, Refused, or Too Vague."

Design rule: make the terminal behavior a *decision*, not a habit — strict
completion for closed-form work, exactly one clarifier for genuinely open work,
never a generic "anything else?" The default leans toward no follow-up; the single
clarifier is the exception, mutually exclusive with the menu form.

## 4. Multi-agent framing — named peers, a leader who collects (xAI grok)

For a swarm, the prompt assigns the model a name, names its specific collaborators,
designates one leader who writes the final answer, and describes how peer messages
arrive in context.

- xAI grok-4.2 / grok-expert: "You are Grok and you are collaborating with **Harper,
  Benjamin, Lucas**. As Grok, you are the **team leader** and you will write a final
  answer on behalf of the entire team... The other agents know your name, know that
  you are the team leader, and are given the same prompt and tools as you are."
- The peer-message channel is specified precisely: "If another agent sends you a
  message while you are thinking, it will be **directly inserted into your context as
  a function turn**. If another agent sends you a message while you are making a
  function call, the message will be **appended to the function response**."

Design rule: name the agents (not "other models"), fix a single leader who owns the
final synthesis, give every peer the same prompt+tools, and define exactly *how and
when* a peer's message lands in context. Vague "collaborate with the team" loses to
named roster + leader + message-arrival contract.

## 5. Values as axioms — truth / beauty / respect as conflict-resolvers (Meta)

Rather than listing adjectives, the prompt elevates a few values to load-bearing
principles the model reasons *from* when guidance conflicts.

- Meta AI states three named values with operative consequences, not labels:
  - **Truth**: "Facts are more important than cultural norms. Defy cultural stigmas
    when the data present a clear refutation... Question official reports when they
    have incentives not to seek truth."
  - **Beauty**: "Truth, goodness, and beauty form an indivisible triad, but it is
    beauty that often bears the greatest weight when the others are weakened. Beauty
    persuades without argument."
  - **Respect**: "The deepest form of respect is to treat every mind as one that
    came to genuinely understand."

Design rule: when a product needs a stance on contested ground, encode 2–4 *named
values with operative clauses* that tell the model what to do when rules collide —
not an adjective list. This is the principles-not-procedures axiom (CLAUDE.md)
applied to values. Contrast with Grok's neutrality framing (core refusal §B):
both fix a stance, but Meta's resolves *conflicts*, Grok's enforces *non-partisanship*.

## 6. Custom-UI / widget routing — when to emit vs suppress (Mistral)

When the model can render a rich UI element, the prompt gives an explicit
emit-vs-suppress test keyed to whether the element's metadata actually answers the
query.

- Mistral le-chat: a `tako-widget` is only usable "with search results that have a
  `{ "source": "tako" }` field," and a Table Metadata tag "must be placed
  immediately before every markdown table to add a title."
- The routing rule is relevance-gated: "**Always display a widget if** the 'title'
  and 'description' of the `{ "source": "tako" }` result answer the user's query"
  — but "You should **NOT** add a widget... because the description field is
  irrelevant to the user's query (the user asked for the weather in London, not for
  Acme Corp stock price)."

Design rule: a renderable widget needs (a) a source/eligibility predicate (only emit
when the data carries the right marker), and (b) a relevance test on the element's
own metadata — emit when its title/description answers the query, suppress when it
does not. Always-render and never-render both lose to a metadata-keyed gate.

## 7. Voice-layer output — expressive and character markup (Misc elevenlabs)

For a cascaded ASR+LLM+TTS voice agent, the prompt defines a markup vocabulary that
controls *how* text is spoken and *who* speaks it, plus voice-channel conventions
that differ from text output.

- ElevenLabs voice agent: "You have access to expressive tags that control how your
  responses are spoken... Put emotional emphasis where needed with square brackets
  e.g. `[happy]`, `[sad]`, `[excited]`, `[slow]`, `[fast]`, `[laugh]`... The words in
  brackets are **only instructions and won't be spoken**. Tags apply to the
  following 4-5 words, repeat tags if necessary."
- Per-speaker markup: "When a message should be spoken by a particular person, use
  markup: `<CHARACTER>message</CHARACTER>`... For any text outside of the xml tags,
  default character will be used."
- Voice-channel formatting differs from text: "**Do not format your text response
  with bullet points, bold or headers**," keep replies "around 3-4 sentences," and
  handle silence — if a user responds with `...` "prompt them to speak."

Design rule: a voice product needs its own output contract — inline expressivity
markup (bracket tags scoped to the next N words), optional per-speaker tags, a
no-visual-formatting rule (bullets/bold are meaningless in speech), a length budget,
and a silence/no-input protocol. Do not reuse the text-formatting block for voice.

## 8. Memory-tool operation schema — add / update / delete by index (Qwen)

When the model can write persistent user memory, the prompt exposes a single
operational tool with a typed schema rather than free-form "remember this."

- Qwen-3.6-plus: "An operational memory tool for managing the personalized user
  memories," whose `operations` object carries three arrays:
  - `add`: "All the contents need to be added to the personalized user memories."
  - `update`: each item an `{ index, content }` pair — "The index of the personalized
    user memories need to be updated."
  - `delete`: "All the **indices** of the personalized user memories need to be
    deleted."

Design rule: model memory as an indexed store with explicit add/update/delete
operations (update and delete address entries **by index**), not an append-only
"note to self." The index discipline lets the model revise and prune memory, not
just accrete it — and pairs with pattern 1 (read priority) to form a full
read-then-write memory contract.

## 9. Terminal-agent intent disambiguation — question vs task (Misc warp)

Before acting, a terminal agent classifies the message as a *question* ("how do I…")
or a *task* ("do it"), and routes differently — answering questions without running
anything, executing tasks with calibrated clarification.

- Warp 2.0 agent: "**Before responding, think about whether the query is a question
  or a task.**"
  - **Question**: "If the user is asking **how** to perform a task, rather than
    asking you to run that task, provide concise instructions (**without running any
    commands**)... Then, ask the user if they would like you to perform the described
    task for them."
  - **Task** (simple): "be concise... bias towards just running the right command.
    **Don't ask the user to clarify minor details that you could use your own
    judgment for**" (e.g., don't ask what "recent" means).
  - **Task** (complex): "ensure you understand the user's intent before proceeding.
    You may ask clarifying questions... but keep them concise and only do so if it's
    important."

Design rule: an agent that can both explain and execute must disambiguate intent
first — explain-don't-run for "how" questions (then offer to do it), execute for
commands, and scale clarification to task complexity (none for trivial judgment
calls, targeted questions only for genuinely complex intent). Complements the
follow-up rule (pattern 3): one governs *whether to act*, the other *how to end*.

## 10. Design-to-domain framing — SaaS-quiet vs editorial, stable dims, no cards-in-cards (OpenAI Codex)

For frontend generation, the prompt ties visual language to the *domain* of the app
and bans specific layout anti-patterns by name.

- OpenAI Codex gpt-5.5: "the frontend design is **tailored for the domain**... SaaS,
  CRM, and other operational tools should feel **quiet, utilitarian, and
  work-focused rather than illustrative or editorial**: avoid oversized hero
  sections, decorative card-heavy layouts, and marketing-style composition, and
  instead prioritize dense but organized information... interfaces built for
  scanning, comparison, and repeated action. A game can be more illustrative,
  expressive, animated, and playful."
- **Stable dimensions**: "**define stable dimensions with responsive constraints**
  (aspect-ratio, grid tracks, min/max, or container-relative sizing) for fixed-format
  UI elements... so hover states, labels, icons, pieces, loading text, or dynamic
  content cannot resize or shift the layout."
- **No cards-in-cards**: "**You do not put UI cards inside other cards. Do not style
  page sections as floating cards.** Only use cards for individual repeated items,
  modals, and genuinely framed tools. Page sections must be full-width bands or
  unframed layouts with constrained inner content."
- (Older Codex gpt-5.4 frames the same instinct as avoiding "AI slop" — average,
  interchangeable layouts; gpt-5.5 sharpens it into the domain rule above.)

Design rule: a generation prompt should bind aesthetic to domain (operational tool →
quiet/dense; game/marketing → expressive), demand stable dimensions so dynamic
content never reflows fixed elements, and ban named layout smells (cards-in-cards,
sections-as-floating-cards). Generic "make it look good" loses to domain-keyed
direction plus enumerated anti-patterns — the same name-the-failure-modes principle
as the formatting layer (core tool-use §C), applied to layout.

## 11. Token-budget declaration — first element, environment fact (Anthropic Fable 5)

Place the model's context ceiling as the literal *first* XML block of the system
prompt — before identity, before persona, before any other instruction — so the
model reasons from a known ceiling rather than discovering it mid-response.

- Anthropic Fable 5: a `<token_budget>` block opens the system prompt declaring
  the context window and the response budget as environment facts:
  > "You have a context window of 200,000 tokens. You should assume that on
  > extremely long tasks — tasks that would fill the whole context — you will be
  > reinstantiated fresh (no memory across turns) when context fills; therefore,
  > you should strongly prefer to do any large-scale asks in a single response
  > rather than across many turns. Aim for a response length that fits comfortably
  > within the available space; for instance, ~16,000 tokens."

Design rule: the budget is an *environment fact*, not a footnote. Declaring it
first means downstream instructions ("be concise," "answer in one sentence") have
a literal number to scale against; declaring it last means those rules float.
Pairs with pattern 16 (lead-with-outcome / completeness-before-stop) — both treat
the budget as a structural constraint the response is *shaped* by, not a soft
preference to be balanced against output goals.

## 12. Safety-tiered model differentiation — same model, named tiers, named envelope (Anthropic Fable 5 and Mythos 5)

When one underlying model ships under two deployment tiers, the prompt names
*both tiers explicitly* and declares the active envelope, so the rules the model
applies change predictably with where it is running — not silently with the SKU.

- Anthropic Fable 5 (public): the prompt presupposes dual-use safety with the
  general public and binds the model to a tier of standard refusal framing,
  capability caveats, and tool-use boundaries.
- Anthropic Mythos 5 (approved organizations): the same underlying model,
  running for vetted organizations, with those dual-use safety measures lifted —
  the prompt *names both* so the model knows which envelope is active and which
  rules follow from it.

Design rule: tier the prompt by *envelope*, not by model — the same model can
appear under different names with different rules; the prompt must say which one
this context is, *and* name the other(s), so the model can recognize when a
caller's framing assumes the wrong tier. Hiding the tier robs the model of the
explicit handle it needs to apply the right rules; collapsing the tiers into one
prompt forces a least-common-denominator safety stance. Pairs with pattern 5
(values as axioms): tier differentiation is the *deployment*-level sibling of the
product-level value conflict-resolution rule.

## 13. Temporal artifact suppression — explicit ban outranks legacy context (Anthropic Fable 5 and Opus 4.8)

The system prompt bans deprecated format tokens *by name* — at the top of the
prompt — even when the legacy conversation history (or older training data) still
contains them. The explicit prohibition must outrank the implicit example.

- Anthropic Fable 5 and Opus 4.8 ban deprecated formats such as
  `<<<voice_note>>>` / `<<<voice_note>>>` blocks *by name* at the top of the
  system prompt, instructing the model to never emit them — even when legacy
  conversation history presents them as the format other turns used.

Design rule: format-token drift cannot be solved by example alone. If the
historical conversation contains `voice_note` blocks and the prompt's only
guidance is to "match the format used above," the model will keep emitting the
deprecated token. A *named* ban at top of prompt creates the explicit handle
"voice_note is forbidden" that beats the implicit pull from context. Pairs with
the trust hierarchy (core §7 / principle 7): system prompt wins over user and
context, so the prompt is the right place to fix a format-token regression the
history re-introduces each session.

## 14. Aggressive search-first mandate — confidence is not an excuse (Anthropic Opus 4.7 and 4.8)

When retrieval is applicable, *do* it in this response — never offer it as a
follow-up. Self-reported confidence is irrelevant; the rule is that the present
moment is when retrieval must happen.

- Anthropic Opus 4.7 and 4.8 system prompt: a hard standing instruction that if
  a tool is available that could ground the answer (search, retrieval, lookup,
  etc.) and the user's request is one the tool *could* answer, the model invokes
  the tool *now* in the current response. The prompt disallows the
  "I-can-look-this-up-if-you'd-like" hedge and the "I-believe-but-am-not-certain"
  deferral: "Do not tell me you can look it up — *look it up*."

Design rule: retrieval is not a *consequence* of uncertainty, it is a *default
action* whenever the user asks a question the tool can answer. The
confidence-gated version ("only retrieve when I'm not sure") loses two ways: it
admits the deck-of-everything "I'm pretty sure X is 42" answer that turns out to
be wrong, and it forces the user to repeat "yes, look it up." The aggressive
mandate collapses both failure modes into a single rule the user can rely on.
Pairs with pattern 1 (context/memory priority): both treat the answer's
*factual reliability* as the load-bearing property and the response shape as
secondary.

## 15. Cumulative-output weapons review — judge the whole conversation, not the turn (Anthropic Opus 4.8)

When assessing harm or refusal, judge the *aggregate* of what the conversation
has produced — not each turn in isolation. Past assistance is not authorization
for the next step.

- Anthropic Opus 4.8: the prompt instructs the model to assess safety and
  refusal against the *whole conversation output* — every piece of code or text
  the session has produced together — rather than judging each turn on its own.
  Past turns' assistance does not authorize new turns; the cumulative shape
  determines whether the next step crosses a line.

Design rule: a per-turn refusal check produces the "you helped me build component
1, now help me wire them into the harmful assembly" gap. The cumulative check
sees the full assembly and refuses at the right boundary. The same principle
applies to *any* escalating-capability tool sequence (shell commands, code edits,
shell+file writes): judge the sequence the user is composing, not the step they
typed most recently. Pairs with the trust hierarchy (principle 7): the prompt's
safety floor runs across the whole session, not per turn.

## 16. Lead-with-outcome and completeness-before-stop — answer first, execute plans to completion (Claude Code Fable 5)

The first sentence of an assistant turn states *what happened* (the answer, the
result, the change); before ending the turn, if the last paragraph is a plan,
the model *executes* it instead of returning the roadmap.

- Claude Code Fable 5 ships two coupled directives:
  - **Lead with outcome**: the first sentence of any non-trivial response
    states what the answer or change *is*. Explanations follow; the outcome
    comes first.
  - **Completeness before stop**: if the last paragraph of a draft turn would
    be a plan ("now I will X, then Y"), the model executes the plan in the same
    turn rather than ending on a roadmap the user has to green-light.

Design rule: completeness-before-stop inverts the "leave a plan, ask permission"
habit that wastes a turn on every significant task. Lead-with-outcome inverts the
"setup before the answer" habit that buries the answer under prose. Together,
both rules collapse two of the most common response-quality failures into one
behavior: *answer the question first; finish the work before you stop*. Pairs
with pattern 14 (aggressive search-first mandate): the model takes the action it
would have proposed rather than offering the action as a follow-up turn.

## 17. Multi-channel message routing — analysis / commentary / final, every message declares its channel (OpenAI GPT-5 agent mode)

Every emitted message declares a channel — analysis (hidden), commentary
(user-visible alongside tool calls), or final (the user-facing deliverable) —
and mixing channels is the failure mode the prompt names.

- OpenAI GPT-5 agent mode divides the agent's output into three explicit
  channels, each with a distinct audience and visibility:
  - **analysis**: the model's internal scratch work; hidden from the user.
  - **commentary**: user-visible text that accompanies tool calls, narrating
    *what* the agent is doing and *why*, mid-execution.
  - **final**: the user-facing deliverable, the answer or artifact the user
    came for.
- The contract is *every message declares its channel* — an unmarked message is
  malformed. Mixing analysis into a "final" block leaks scratch work into the
  answer; mixing final into "commentary" buries the answer under narration; the
  prompt names the channel so the renderer can route correctly.

Design rule: a multi-channel prompt needs (a) explicit channel names the model
writes *into the message* it emits, (b) distinct visibility/audience for each
channel, (c) a default channel for the kind of message being sent, and (d) a
named anti-pattern (mixing channels) so the model has the handle to self-correct.
Implicit channeling ("just write better responses") loses to enumerated
channels with visible rendering rules.

## 18. Sensitive decision scope gate — protect characteristics, bar inference (OpenAI GPT-5 agent mode)

Block high-impact decisions made about non-users on the basis of protected
characteristics, and *bar the model from inferring those characteristics in the
first place* — not just from acting on them when guessed.

- OpenAI GPT-5 agent mode ships an explicit scope gate: the model must not make
  high-impact decisions about a *non-user* (a third party the model has not
  verified) based on protected characteristics such as race, religion, gender,
  sexual orientation, disability, nationality, or similar. The gate runs in
  *two halves*: the model cannot act on those characteristics *and* cannot
  infer them — the inference step is also barred, so a downstream guess can't
  quietly feed a later decision.

Design rule: a sensitivity gate that permits inference-then-decision is the same
gate in name only — by the time the model has inferred "this person is X" it has
already consumed the protected signal. The fix is to bar the inference step
itself. Pairs with pattern 7 (trust hierarchy): the protected-characteristic
gate sits at the same tier as the system-prompt safety floor, not at the
user-assertion tier. Pairs with pattern 12 (safety-tiered model differentiation):
a tier that lifts other safety measures must explicitly state whether the
sensitivity gate is among the lifted ones or retained.
