# Star Alliance — Claude Instructions

## Default sub-agent model: MiniMax M3

For all delegated sub-work, default to MiniMax M3 via `python3 minimax.py`.

```
python3 minimax.py "<prompt>"
# flags: -s <system>  --json  -f <file>  (reads stdin if no arg)
# key: ~/.config/minimax/m3.key
```

Use Claude models (Opus/Sonnet/Haiku via Task tool) only when:
- Orchestration logic requires tool access (file edits, bash, MCP)
- Deep multi-step reasoning that MiniMax can't return structured output for
- The task requires native Claude Code capabilities

Otherwise: **MiniMax first.**

## Reading discipline (every member)

_Mined from full session history — 46 sessions hit this; it was the single most-repeated correction._

- Files may exceed token caps. Read large or unknown-size files with `offset`/`limit` or `grep` — never a blind full read.
- The instant a full read fails on the token limit, **switch to offset/limit** — never retry the same full read.
- Read a file before editing it (avoids "not read yet" errors); re-read a shared or parallel-touched file immediately before writing if more than ~30s passed.
- In scheduled or autonomous runs, loop files **one at a time**, not all at once.

## Guild conduct (every member)

- **Don't make unrequested changes** — wait for explicit permission before modifying code or visuals. When the spec is clear, proceed; don't ask permission just to continue.
- **`cancel` = immediate revert** of the prior change-set. Honor an explicit **`proceed`** — don't re-insert your own verification breakpoints.
- Before creating a component, grep for and **reuse** an existing one; reuse design-token constants, never hardcode hex.
- **Read the vault/memory logs before continuing** work started in a prior session.
- Save user **confirmations and wins** as feedback memories, not only corrections.
- **Log errors loudly** — never silently swallow them.
- **Confirm destructive git ops** (`reset --hard`, force push) before executing.
- On **MCP unavailability**, never fabricate a write — reconnect or fall back to non-write ops; when a dispatch channel is disabled, log intent verbatim and don't call the tool.
