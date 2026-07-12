---
name: dev-server
description: "Use this skill whenever the user says 'open dev server', 'run dev server', 'restart dev server', 'start the app', 'launch dev', 'open the app', or any variation of starting/restarting/viewing the local Next.js development server. Also use it to start a persistent/detached server that survives the session closing, or to visually verify a logged-in or RTL page behind the app's auth gate without hijacking the user's running server. Handles start, restart, persistent start, and auth-aware preview in one turn — no ToolSearch round-trips needed."
metadata:
  version: 1.2.0
type: Skill

---
# Dev Server

Manages the local Next.js dev server for the current project using the Claude Preview MCP tools. Assumes the project has a `.claude/launch.json` entry named `web` (or another configurable name — see Notes).

## Step 0 — Project precedence check (do this FIRST, once per session)

This skill is generic. Some projects **forbid the preview MCP tools** and mandate a plain terminal start instead. Before doing anything else, check the active project for such a directive:

- Scan the project's `CLAUDE.md` and its memory (`.claude/.../memory/` or the loaded `MEMORY.md`) for a **preview-tools ban** or a **mandated terminal/Bash-start directive** (phrases like "don't invoke the dev-server skill", "preview tools banned", "preview_start banned", "give terminal command instead", "use background Bash to start").
- **If such a directive exists:** do NOT call any `preview_*` MCP tool. Instead run the project's prescribed terminal start (e.g. kill the port then background-start: `lsof -ti:3000 | xargs kill -9 2>/dev/null; cd <dir> && npx turbo dev` as a background process), report the command + URL, and STOP. The project directive always wins.
- **If no such directive exists:** proceed with the normal preview path below.

> Example (Lex Council): its memory `feedback_no-dev-server-hijack` bans this skill + all preview tools and requires `kill :3000` then `cd lex_council && npx turbo dev` via background Bash. In that project, Step 0 short-circuits to the Bash start and the preview path is never used.

**This one decision — preview path vs. terminal path — is the "start mechanism" for the whole skill.** Every later action (Restart, Persistent start, Auth-aware preview) reuses whichever mechanism Step 0 selected. Never switch to `preview_*` for a later action in a project that banned it.

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

### Persistent start (survives the session closing)
User says: "keep the server running", "start it so it doesn't die", "persistent dev server", or the server has died repeatedly when a session was archived/closed.

The preview MCP path is harness-managed and dies with the session. A **detached terminal start** survives it. Use the **terminal path** for this (regardless of Step 0's ban status — a persistent server is always a terminal-start job):

1. Kill anything on the port, then start **detached** with `nohup`, logging to a **deterministic, tail-able path** (not an ephemeral temp name):

   ```
   lsof -ti:3000 | xargs kill -9 2>/dev/null
   cd <project-dir> && nohup npx turbo dev > /tmp/dev-web-3000.log 2>&1 &
   ```

   Adapt `npx turbo dev` to the project's real dev command and `3000`/log path if the port differs.

2. **Confirm startup by polling, not by reading foreground output** (there is none once detached). Poll the port and the log until ready, e.g.:

   ```
   for i in $(seq 1 30); do curl -sf http://localhost:3000 >/dev/null && break; sleep 1; done
   tail -n 20 /tmp/dev-web-3000.log
   ```

3. If the log shows a startup error, quote the exact error and stop — don't retry blindly.
4. Report the URL + the log path so the user (or a later session) can tail it: `Running at http://localhost:3000 — logs: /tmp/dev-web-3000.log`.

### Auth-aware preview (verify a logged-in or RTL page without hijacking the user's server)
User says: "show me the logged-in page", "screenshot the dashboard behind login", "check the Arabic/RTL layout", or any request to visually verify a page behind the app's auth gate.

The user's own server on `:3000` may already be running — **do not kill, restart, or navigate it away**. Instead run a **separate, agent-owned instance on an alternate port** and drive that one.

**Why a second instance is allowed where hijacking the first was banned:** the non-hijacking invariant is about the *port*, not the tool — the ban exists so the agent never disrupts the user's live `:3000`. A fresh instance on a different port (e.g. `3100`) leaves `:3000` untouched, so it honors the ban. Use whichever **start mechanism Step 0 selected** (preview where allowed, detached terminal start where banned) — just target the alternate port.

1. Start the second instance on an alternate port, e.g. `PORT=3100 nohup npx turbo dev > /tmp/dev-web-3100.log 2>&1 &`, and confirm startup by polling `http://localhost:3100` (as in Persistent start).
2. **Authenticate using the project's documented LOCAL-DEV auth — never a real password.** Entering credentials into a login field is prohibited. Discover, per-project (same spirit as Step 0, scan `CLAUDE.md`/memory), the project's local-dev auth path: a seeded test user + dev session cookie, an auth-bypass env flag, or a documented dev login token. If the project documents none, do NOT type credentials — report that you need a documented local-dev auth path and stop.
3. Navigate the agent's browser/preview to `http://localhost:3100`, apply the dev session (cookie/flag), open the gated or RTL route, and screenshot.
4. Report the screenshot + which route/locale it shows. Leave the user's `:3000` exactly as it was.

## Session State

Track the current `serverId` (preview path) and any detached PID/port + log path (terminal path) in memory across turns within the session. Each restart replaces the prior ID. A persistent/second instance is separate from the user's `:3000` server — keep them distinct.

## Response Format

After a successful start/restart, reply with:
- The screenshot (rendered inline)
- One line: `Running at http://localhost:3000`

For a persistent or second-instance start, add the log path so it can be tailed later.

If the server fails to start, quote the exact error and stop — don't retry blindly. On the detached path, "the error" means the relevant lines from the log file, since there is no foreground output.

## Notes

- Don't call ToolSearch — these tools are available via MCP directly
- Don't explain the steps — just do them and show the result
- If the project's `launch.json` uses a different server name than `web`, replace the `name: "web"` arg with the actual name. Detect via `cat .claude/launch.json` once per session.
- If caveman / terse mode is active in the project, keep responses minimal — screenshot + one URL line, no narration.
- Never enter a real password/credential into a login field — that's prohibited. Auth-aware preview relies only on the project's documented local-dev auth.

## Changelog

| Version | Date | Summary |
|---|---|---|
| **1.2.0** | 2026-07-12 | Added two capabilities from 5 sessions of evidence. **Persistent start** — a detached `nohup` start logging to a deterministic path (`/tmp/dev-web-3000.log`) that survives the session being archived/closed, with startup confirmed by polling the port + reading the log instead of foreground output (fixes 20+ manual restarts in one session; a surviving nohup server was the proven pattern). **Auth-aware preview** — verify a logged-in or RTL page behind the app's auth gate by running a separate agent-owned instance on an alternate port (never touching the user's `:3000`), authenticating via the project's *documented local-dev auth only* (never a real password), so the agent can visually verify gated pages without hijacking the user's running server. Both reuse Step 0's start-mechanism decision so they work in preview-banned projects (e.g. Lex Council) too. |
| **1.1.0** | 2026-06-20 | Added **Step 0 — Project precedence check** (skillsmith routine, conf 9/10). The skill mandated the preview MCP path unconditionally, which collided with projects that ban preview tools and require a terminal start (e.g. Lex Council's `no-dev-server-hijack` memory — collision had already fired twice). Step 0 now detects a per-project preview-ban / mandated-terminal-start directive once per session and, if found, runs the project's own Bash start instead of any `preview_*` tool. Conditional + additive — generic projects keep the preview path unchanged. |
| **1.0.0** | — | Initial release: start/restart the local Next.js dev server via Claude Preview MCP tools in one turn. |