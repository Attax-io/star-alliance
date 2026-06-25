---
name: dev-server
description: "Use this skill whenever the user says 'open dev server', 'run dev server', 'restart dev server', 'start the app', 'launch dev', 'open the app', or any variation of starting/restarting/viewing the local Next.js development server. Handles start and restart in one turn — no ToolSearch round-trips needed."
metadata:
  version: 1.1.0
---

# Dev Server

Manages the local Next.js dev server for the current project using the Claude Preview MCP tools. Assumes the project has a `.claude/launch.json` entry named `web` (or another configurable name — see Notes).

## Step 0 — Project precedence check (do this FIRST, once per session)

This skill is generic. Some projects **forbid the preview MCP tools** and mandate a plain terminal start instead. Before doing anything else, check the active project for such a directive:

- Scan the project's `CLAUDE.md` and its memory (`.claude/.../memory/` or the loaded `MEMORY.md`) for a **preview-tools ban** or a **mandated terminal/Bash-start directive** (phrases like "don't invoke the dev-server skill", "preview tools banned", "preview_start banned", "give terminal command instead", "use background Bash to start").
- **If such a directive exists:** do NOT call any `preview_*` MCP tool. Instead run the project's prescribed terminal start (e.g. kill the port then background-start: `lsof -ti:3000 | xargs kill -9 2>/dev/null; cd <dir> && npx turbo dev` as a background process), report the command + URL, and STOP. The project directive always wins.
- **If no such directive exists:** proceed with the normal preview path below.

> Example (Lex Council): its memory `feedback_no-dev-server-hijack` bans this skill + all preview tools and requires `kill :3000` then `cd lex_council && npx turbo dev` via background Bash. In that project, Step 0 short-circuits to the Bash start and the preview path is never used.

## Tools (pre-loaded — no ToolSearch needed)

- `mcp__Claude_Preview__preview_start` — starts a server by name from `.claude/launch.json`
- `mcp__Claude_Preview__preview_stop` — stops a server by ID
- `mcp__Claude_Preview__preview_screenshot` — takes a screenshot of the running server

The server name in `launch.json` is **`web`** (port 3000).

## Actions

### Open (default)
User says: "open dev server", "run dev server", "start the app", etc.

**Run Step 0 first.** If the project bans preview tools, follow that path and stop. Otherwise:

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

## Changelog

| Version | Date | Summary |
|---|---|---|
| **1.1.0** | 2026-06-20 | Added **Step 0 — Project precedence check** (skillsmith routine, conf 9/10). The skill mandated the preview MCP path unconditionally, which collided with projects that ban preview tools and require a terminal start (e.g. Lex Council's `no-dev-server-hijack` memory — collision had already fired twice). Step 0 now detects a per-project preview-ban / mandated-terminal-start directive once per session and, if found, runs the project's own Bash start instead of any `preview_*` tool. Conditional + additive — generic projects keep the preview path unchanged. |
| **1.0.0** | — | Initial release: start/restart the local Next.js dev server via Claude Preview MCP tools in one turn. |
