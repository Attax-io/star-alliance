---
description: Auto-mandate code-unity / design-unity skills whenever the-developer / the-designer members are invoked, via a PreToolUse hook gate.
---

## Plain-English Summary
Two of the guild's craftsmen now always draw their "unity" skill the moment they're put to work. Whenever the Developer is dispatched, a hook fires a mandate to run `code-unity` first; whenever the Designer is dispatched, the same for `design-unity`. This keeps one source of truth for code and for UI — no re-inventing a type, constant, or button that already exists. It is enforced by a small script hooked into the existing PreToolUse dispatcher, so nobody has to remember to do it by hand. The mandate is non-blocking (it never freezes a tool call); it just injects a first-action instruction the member reads and obeys.

## Files Changed
- [[unity-skill-gate.py]] — new PreToolUse gate; detects the-developer / the-designer invocation (Task/Agent subagent_type OR a Bash `dispatch.py <member>` call) and emits a non-blocking systemMessage mandating the matching unity skill.
- [[sa-pretool.py]] — added one GATES entry `("unity-skill-gate.py", {"Task","Agent","Bash"})` right after high-alert so the gate runs in-process (single interpreter).

## Why
The-developer carries `code-unity` and the-designer carries `design-unity` in their skill lists, but a listed skill is not a guaranteed-invoked skill. Binding each member to its unity craft at the observable dispatch moment makes the source-of-truth check automatic rather than discretionary. Mirrors the high-alert.py contract (pure check(data) -> dict, fail-open, never exit 2). Trigger paths: Task/Agent tool with subagent_type in {the-developer, the-designer}, and Bash commands matching `dispatch.py the-(developer|designer)`.

## Verification
Syntax parsed clean (ast.parse). Smoke-tested three payloads: Task→the-designer emits the design-unity mandate; Bash dispatch.py the-developer emits the code-unity mandate; Task→the-herald emits nothing (correctly silent for non-bound members).
