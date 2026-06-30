#!/bin/bash
# Star Alliance — double-click launcher.
# Restarts the dashboard dev server (serve.cjs) and opens it in the browser.
# Double-click in Finder to run. First time: right-click → Open to clear Gatekeeper.

# Repo root = the folder this script lives in (works no matter where it's launched from).
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT" || exit 1

PORT=4178
URL="http://localhost:$PORT"

echo "✦ Star Alliance — Mission Console"
echo "  root: $ROOT"

# Need node.
if ! command -v node >/dev/null 2>&1; then
  echo "✗ node not found. Install Node.js, then try again."
  echo "  Press any key to close."; read -n 1 -s; exit 1
fi

# Kill any existing serve.cjs (clean restart). Never touch :8000 (WhatsApp MCP).
echo "↻ Restarting dev server on :$PORT…"
pkill -f "$ROOT/serve.cjs" 2>/dev/null
pkill -f "serve.cjs" 2>/dev/null
sleep 1

# Start detached so closing this window leaves the server running.
nohup node "$ROOT/serve.cjs" >"$ROOT/serve.out" 2>&1 &
SERVER_PID=$!

# Wait for the port to answer (up to ~10s).
for i in $(seq 1 20); do
  if curl -s -m1 "$URL/api/status" >/dev/null 2>&1; then break; fi
  sleep 0.5
done

if curl -s -m1 "$URL/api/status" >/dev/null 2>&1; then
  echo "✓ Server LIVE  (pid $SERVER_PID) — log: serve.out"
  echo "→ Opening $URL"
  open "$URL"
else
  echo "✗ Server did not come up. Check serve.out for the error."
  echo "  Press any key to close."; read -n 1 -s; exit 1
fi

echo ""
echo "Dashboard is running. You can close this window — the server stays up."
echo "(To stop it later, run this launcher again or: pkill -f serve.cjs)"
sleep 2
