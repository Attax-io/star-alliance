# /doer — Bulk & parallel work now runs as Claude subagents

**This command is deprecated as a router to an external model.** The Star Alliance
is now a **Claude-only** harness — there is no minimax/Hermes doer seat to route
bulk work to. That external executor has been removed.

## What replaced it

Bulk or parallel work is now handled by **spawning Claude subagents** with the
Task/Agent tool. A subagent is a separate Claude helper that runs on its own
context and returns its result to you. For heavy work, pick the cheapest capable
Claude model (usually **haiku** for mechanical bulk, **sonnet** for balanced work)
and spawn it:

```
Task(subagent_type="general-purpose", model="haiku",
     prompt="Refactor the auth module to use JWT tokens")
```

For a fan-out (the old "panel"), spawn several Task/Agent calls **in one message**
so they run concurrently, then converge and synthesize their results yourself.

## When to spawn a subagent vs. do it inline

- **Spawn a subagent** — large or repetitive output (≈1.5k+ tokens, many
  transforms), or several independent chunks that can run in parallel. Offloading
  keeps the main session's context clean.
- **Do it inline** — small edits (a few lines, one file); spawning is net-negative
  overhead. Also do tool-heavy orchestration (Edit/Write/Bash/MCP) and high-stakes
  judgment (architecture, schema, security review) in the main session or a
  tool-capable subagent.

## After a subagent returns

- Review its output against your original request.
- Apply the result via Edit/Write or pass it downstream.
- If it doesn't match, re-spawn with a sharper prompt — don't hand-patch a bad
  return, get a fresh one.

There is no external doer script to call and no dispatch routing to remember —
everything is Claude, and the Task/Agent tool is the only fan-out you need.
