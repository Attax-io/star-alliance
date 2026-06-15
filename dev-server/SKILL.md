---
name: dev-server
version: 1.0.0
description: "Use this skill whenever the user says 'open dev server', 'run dev server', 'restart dev server', 'start the app', 'launch dev', 'open the app', or any variation of starting/restarting/viewing the local Next.js development server. Handles start and restart in one turn — no ToolSearch round-trips needed."
---

# Dev Server

Manages the local Next.js dev server for the current project using the Claude Preview MCP tools. Assumes the project has a `.claude/launch.json` entry named `web` (or another configurable name — see Notes).

## Tools (pre-loaded — no ToolSearch needed)

- `mcp__Claude_Preview__preview_start` — starts a server by name from `.claude/launch.json`
- `mcp__Claude_Preview__preview_stop` — stops a server by ID
- `mcp__Claude_Preview__preview_screenshot` — takes a screenshot of the running server

The server name in `launch.json` is **`web`** (port 3000).

## Actions

### Open (default)
User says: "open dev server", "run dev server", "start the app", etc.

1. Call `preview_start` with `name: "web"`
2. Note the returned `serverId`
3. Call `preview_screenshot` with that `serverId`
4. Reply with the screenshot + `http://localhost:3000`

### Restart
User says: "restart dev server", "restart the server", etc.

If a `serverId` from this session is known:
1. Call `preview_stop` with that `serverId`
2. Call `preview_start` with `name: "web"`
3. Note the new `serverId`
4. Call `preview_screenshot`
5. Reply with screenshot + URL

If no prior `serverId` is known (new session), just do Open.

## Session State

Track the current `serverId` in memory across turns within the session. Each restart replaces it with the new ID.

## Response Format

After a successful start/restart, reply with:
- The screenshot (rendered inline)
- One line: `Running at http://localhost:3000`

If the server fails to start, quote the exact error and stop — don't retry blindly.

## Notes

- Don't call ToolSearch — these tools are available via MCP directly
- Don't explain the steps — just do them and show the result
- If the project's `launch.json` uses a different server name than `web`, replace the `name: "web"` arg with the actual name. Detect via `cat .claude/launch.json` once per session.
- If caveman / terse mode is active in the project, keep responses minimal — screenshot + one URL line, no narration.
