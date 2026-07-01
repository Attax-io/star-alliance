---
description: Auto-mandate the unity source-of-truth skill whenever a bound member (the-developer, the-designer, the-architect, the-strategist) is invoked, via a PreToolUse hook gate.
---

## Plain-English Summary
Two of the guild's craftsmen now always draw their "unity" skill the moment they're put to work. Whenever the Developer is dispatched, a hook fires a mandate to run `code-unity` first; whenever the Designer is dispatched, the same for `design-unity`. This keeps one source of truth for code and for UI — no re-inventing a type, constant, or button that already exists. It is enforced by a small script hooked into the existing PreToolUse dispatcher, so nobody has to remember to do it by hand. The mandate is non-blocking (it never freezes a tool call); it just injects a first-action instruction the member reads and obeys. The mandate now also covers the Architect (schema source-of-truth — no duplicate table/view/RPC/trigger) and the Strategist (campaign source-of-truth — reuse canonical primitives across waves); both draw `code-unity`, the same code-side guard the Developer uses. Only the Designer draws `design-unity`.

## Files Changed
- [[unity-skill-gate.py]] — PreToolUse gate; UNITY map now binds four members → the-developer/the-architect/the-strategist → `code-unity`, the-designer → `design-unity`. Detects invocation via Task/Agent subagent_type OR a Bash `dispatch.py <member>` call (regex covers all four). Emits a non-blocking systemMessage mandating the matching unity skill.
- [[sa-pretool.py]] — added one GATES entry `("unity-skill-gate.py", {"Task","Agent","Bash"})` right after high-alert so the gate runs in-process (single interpreter).

## Why
The-developer carries `code-unity` and the-designer carries `design-unity` in their skill lists, but a listed skill is not a guaranteed-invoked skill. Binding each member to its unity craft at the observable dispatch moment makes the source-of-truth check automatic rather than discretionary. Mirrors the high-alert.py contract (pure check(data) -> dict, fail-open, never exit 2). Trigger paths: Task/Agent tool with subagent_type in {the-developer, the-designer}, and Bash commands matching `dispatch.py the-(developer|designer)`.

## Verification
Syntax parsed clean (ast.parse). Smoke-tested three payloads: Task→the-designer emits the design-unity mandate; Bash dispatch.py the-developer emits the code-unity mandate; Task→the-herald emits nothing (correctly silent for non-bound members). Second pass (4-member map): syntax OK; smoke-tested the-architect (Task + Bash dispatch) and the-strategist → both emit the code-unity mandate; the-merchant → silent (unbound).
