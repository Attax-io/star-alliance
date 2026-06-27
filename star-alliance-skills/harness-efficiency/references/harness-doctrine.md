# Harness Engineering Doctrine — context, recovery, verification

A model is unreliable, but the SYSTEM that surrounds it does not have to be. The Star Alliance guild orchestrates specialist members, offloads doer-grade work to a cheap model (MiniMax), and gates every turn through a routing classifier. Our only stable advantage is the harness: bounded context, recovery as a designed runtime path, independent verification, and partitioned agents that keep each context small. Token and time efficiency are not side effects — they are the design constraint, and the doctrine below is the engineering we use to honor it.

## Context is a budget, not a library

- Layer memory by lifetime, not by convenience. Long-lived rules in `CLAUDE.md` (managed / user / project / local, loaded by directory proximity), persistent memory split into a thin `MEMORY.md` index plus topic body files, session memory as a fixed operational template, ephemeral chat. Do not mix them or reinjection tax will eat every turn.
- Treat the entrypoint as an index, never a diary. Enforce `MAX_ENTRYPOINT_LINES` and `MAX_ENTRYPOINT_BYTES` on `MEMORY.md`. Once the index bloats, addressing fails and the system stops being able to find what it stored.
- Budget session memory like working memory, not a log. Per-section caps and a total session-memory token cap, with priority on `Current State` and `Errors & Corrections`. Session memory serves continuation; full replay is not the goal.
- Pre-reserve compact budget before the window is full. Reserve output tokens for the summary itself, and keep a separate autocompact warning buffer. Systems that reserve nothing defer risk to later turns.
- Make compact a controlled reboot, not a recap. Strip images, docs, and already-reinjected attachments; restore plans, recently accessed files, invoked-skill payloads, plan-mode state, and post-compact hooks. Truncate per-skill instead of dropping whole skills. Preserve action semantics, not linguistic surface.
- Allow truncation of compact itself as a last resort. When even the summary request hits prompt-too-long, strip head API rounds in chunks and retry. Refuse to dead-loop on "cannot compact compact."
- Govern for "able to continue work," not "max information packed." Stuffed context loses the ability to act; governed context stays operable.

## The error path is the main path

- Classify errors at the boundary. Treat prompt-too-long, media-size, and max-output-tokens as a fixed recoverable set. Route them to recovery first, surface them only after recovery is exhausted. Users care about continued work, not error taxonomy.
- Layer recovery from cheap-and-non-destructive to heavy. For prompt-too-long: drain staged collapse first, then reactive compact, then surface. Never hit every error with one giant hammer.
- Anti-loop is part of the recovery contract. Track `hasAttemptedReactiveCompact` so the same-class failure is not blindly retried. Guard stop hooks so a PTL state cannot drive `error → hook block → retry → error` death spirals.
- After max-output-tokens, optimize for continuation. If the cap is conservative, raise it and rerun the same request. If the cap is already max, append a meta message that says continue, no apology, no recap, split remaining work into smaller chunks. Polite truncation summaries burn budget and grow drift.
- Put a circuit breaker on the recovery system itself. Count consecutive compact failures and skip further attempts past the threshold. A recovery system that never stops is as dangerous as one that never starts.
- Treat interrupts as failure states requiring semantic closure. On Esc mid-stream, consume remaining tool results and synthesize `tool_result` for issued-but-unfinished calls. User abort of compact must not be counted as compact success.
- Maintain narrative consistency across failures. Track `transition.reason`, recovery counts, compact boundaries, and synthetic error messages. Recovery fixes the system's self-explainability, not only the error.

## Verification must be independent

- The implementer does not grade its own work. Verification is a separate stage and, in any non-trivial task, a separate role. "I changed code" and "the change is correct" are separated by a wide river.
- Pin the meaning of "done." Done means run tests with the feature enabled, investigate errors instead of dismissing them, stay skeptical, test independently, and never rubber-stamp. Code existence is not the deliverable.
- Verify memory and recommendations, not only code. Before acting on a memory record, check current reality; when memory conflicts with what is observed now, trust the present and update or delete. Verification is the system's baseline habit against temporal drift.
- Localize failure by role. After a run, be able to say: did research miss a key signal, did synthesis fail to digest, did implementation introduce defects, did verification undercheck? A single agent delivering one thick soup cannot be debugged by layer.
- Coordinator must digest, not forward. Research and implementation can be delegated; synthesis cannot. Concrete next prompts must name specific files, locations, and changes — not "based on the above findings."

## Multi-agent: partition uncertainty, not just parallelize

- Fork for cache discipline first. Share `CacheSafeParams` (`systemPrompt`, `userContext`, `systemContext`, `toolUseContext`, `forkContextMessages`) between parent and child so prompt-cache hits survive the fork. Parallelism that breaks the cache is parallel waste.
- Isolate mutable state by default. Clone `readFileState`, give the child its own abort controller, wrap `getAppState` to suppress prompts, make `setAppState` a no-op. Sharing is explicit opt-in (`shareAbortController`, `shareSetAppState`, etc.) — never the default.
- Separate the roles, not just the threads. Research, implementation, verification, and synthesis each get their own context and constraint container. Coordinator converges understanding; it does not generate it.
- Make agent lifecycle observable. Fire `SubagentStart` and `SubagentStop` hooks with `agent_id`, `agent_type`, and `agent_transcript_path`. Allow exit code 2 so stderr feeds back and the child can continue. A spawn is a start, not an end.
- Propagate abort down, never up. Parent abort must reach child abort controllers; cleanup handlers must unregister; outputs must be evictable. No orphans, no leaked handlers, no dangling `tool_use`.
- Refuse silent cache key drift. If a fork would mutate cache-critical params, refuse the fork or rebuild the cache. Do not let a child quietly invalidate the parent's cache.
- The real value of parallelism is clearer responsibility boundaries, not raw speed. A single agent delivers one thick soup; partitioned agents deliver four auditable containers.

## The ten principles (condensed)

1. Treat models as unstable components, not teammates.
2. Prompt is part of the control plane, not persona decoration.
3. Query loop is the heartbeat; without it, systems demo but do not run.
4. Tools are managed execution interfaces — scheduled, authorized, interruptible, ledger-closed.
5. Context is working memory; govern, do not stuff.
6. Error paths are main paths; design recovery at design time.
7. Recovery should optimize for continuation, not recap.
8. Multi-agent matters because it partitions uncertainty, not because it parallelizes.
9. Verification must be independent; implementers overtrust their own changes.
10. Team institutions matter more than personal tricks; institutionalize via layered `CLAUDE.md`, approval boundaries, skills, hooks, transcripts, and a shared definition of done.

## Efficiency reading of the doctrine

- Compaction caps premium-token growth. Pre-reserved summary output, section caps, entrypoint line and byte caps, and a hard ceiling on session memory stop context inflation before it forces expensive overflow handling on every premium turn.
- Independent verification by a cheap doer is cheaper than a wrong premium turn. Catching a bad answer with a low-cost worker costs a small MiniMax turn; shipping a bad answer costs a premium turn, a rollback, and a redo. Offload the verify role by default.
- Partitioned agents keep each context small. Research, implement, verify, and synthesize each work in narrow windows, so total token spend across the guild stays bounded even when the union of their work is large.
- Cache-safe fork params turn parallelism into an actual speedup. Children that share `CacheSafeParams` with the parent reuse the prompt cache; children that drift invalidate it. The routing classifier should treat cache-safe fork as the only default fork shape.
- Index discipline is a re-load tax avoided. A `MEMORY.md` kept under the line and byte caps is cheap to read every turn; a bloated index makes every turn pay for history it cannot use.
- Recovery layering saves the most expensive path. Drain staged collapse before reactive compact, and only surface after the cheap path fails. The guild's recovery policy must encode this order, not improvise it.
- Anti-loop guards stop silent token burn. `hasAttemptedReactiveCompact`, stop-hook dead-loop guards, and the autocompact circuit breaker prevent the system from spending API calls replaying the same failure in different postures.
- Continuation over recap on max-output-tokens. Skip the polite truncation summary that re-burns budget and grows semantic drift; append the meta continue message and move on.
- Routing classifier + offload keeps premium tokens scarce. Gate every turn through the classifier, send doer-grade work to MiniMax, reserve the premium model for routing, coordination, and synthesis — the fewest possible high-cost turns.
- Narrative consistency is operations efficiency. Tracking `transition.reason`, recovery counts, and compact boundaries means an on-call engineer can explain what the guild did in minutes rather than re-inferring it from logs across hours.

Bounded context, designed recovery, independent verification, and partitioned agents — the harness stays continuous, accountable, and cheap, even when the model inside it is not.
