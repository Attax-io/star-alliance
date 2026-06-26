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
