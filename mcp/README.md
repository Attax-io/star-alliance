# mcp/ — retired

The local Star Alliance MCP server (`server.py`) was retired 2026-07-12 as part of
the Supabase migration: the guild now lives in the Supabase `guild` schema and
`bin/sa` is the bridge. The server had 9 lifetime calls, all discovery-only.

Files moved to `.retired/2026-07-supabase-migration/mcp/`.
The `.venv/` here is gitignored machine junk and was left in place.
