#!/bin/bash
# Star Alliance MCP server installer — double-click to install/repair on this Mac.
# Safe to run repeatedly. Determines the repo root from this script's own location
# so it works regardless of which device or username it runs under.

set -u

fail() {
    echo ""
    echo "❌ Install failed: $1"
    echo ""
    read -p "Press Enter to close..."
    exit 1
}

main() {
    REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
    echo "Star Alliance MCP installer"
    echo "Repo root: $REPO_ROOT"
    echo ""

    # 1. Check for python3.13
    if ! command -v python3.13 >/dev/null 2>&1; then
        fail "python3.13 not found. Install it with: brew install python@3.13"
    fi
    echo "Found python3.13: $(command -v python3.13)"

    VENV_DIR="$REPO_ROOT/mcp/.venv"
    SERVER_PY="$REPO_ROOT/mcp/server.py"

    if [ ! -f "$SERVER_PY" ]; then
        fail "Could not find mcp/server.py at $SERVER_PY"
    fi

    # 2. Create venv if missing
    if [ -d "$VENV_DIR" ]; then
        echo "Virtual environment already exists at $VENV_DIR (skipping creation)."
    else
        echo "Creating virtual environment at $VENV_DIR ..."
        python3.13 -m venv "$VENV_DIR" || fail "Failed to create virtual environment."
        echo "Installing mcp SDK..."
        "$VENV_DIR/bin/pip" install --quiet --upgrade pip || fail "Failed to upgrade pip in venv."
        "$VENV_DIR/bin/pip" install --quiet mcp || fail "Failed to install the mcp package."
    fi

    if [ ! -x "$VENV_DIR/bin/python" ]; then
        fail "Expected venv python at $VENV_DIR/bin/python but it's missing."
    fi

    # 3. Register the guild MCP server where Claude Code actually reads it.
    #    Claude Code reads mcpServers from a project-root .mcp.json (checked in)
    #    and from the user-scope ~/.claude.json — it does NOT read ~/.claude/mcp.json.
    #    The checked-in repo .mcp.json covers in-repo sessions portably; here we also
    #    merge a machine-correct absolute entry into ~/.claude.json so the guild MCP
    #    tools are reachable from any project on this Mac.
    echo "Registering star-alliance in ~/.claude.json ..."
    PYBIN="$VENV_DIR/bin/python"
    if [ ! -x "$PYBIN" ]; then
        PYBIN="python3.13"
    fi

    "$PYBIN" - "$REPO_ROOT" <<'PYEOF' || fail "Failed to update ~/.claude.json"
import json
import os
import sys

repo_root = sys.argv[1]
config_path = os.path.expanduser("~/.claude.json")

config = {}
if os.path.exists(config_path):
    with open(config_path, "r") as f:
        content = f.read().strip()
        if content:
            config = json.loads(content)

if "mcpServers" not in config or not isinstance(config.get("mcpServers"), dict):
    config["mcpServers"] = {}

config["mcpServers"]["star-alliance"] = {
    "type": "stdio",
    "command": f"{repo_root}/mcp/.venv/bin/python",
    "args": [f"{repo_root}/mcp/server.py"],
}

# Atomic write so a failed run never corrupts the main Claude Code config.
tmp_path = config_path + ".tmp"
with open(tmp_path, "w") as f:
    json.dump(config, f, indent=2)
    f.write("\n")
os.replace(tmp_path, config_path)

print(f"Registered star-alliance in {config_path}")
PYEOF

    # 4. Bootstrap the Hermes worker (idempotent; degrades gracefully with no network).
    #    The doer seat runs on Hermes profiles. This verifies/publishes them and runs a
    #    preflight so the operator knows whether the dispatch path is live. It never fails
    #    the install: every sub-step degrades to a printed instruction when a tool/key is absent.
    echo ""
    echo "Hermes worker bootstrap ..."
    if command -v hermes >/dev/null 2>&1; then
        echo "  Found hermes: $(command -v hermes)"
        if [ -f "$REPO_ROOT/tools/publish_profiles.py" ]; then
            if python3 "$REPO_ROOT/tools/publish_profiles.py" --update >/dev/null 2>&1; then
                echo "  ✓ Hermes profiles published/updated (auth + memories preserved)"
            else
                echo "  ⚠  publish_profiles.py returned nonzero — re-run manually when online"
            fi
        fi
    else
        echo "  ⚠  hermes not on PATH — install Hermes to enable the doer seat (gates stay off until then)"
    fi
    # Preflight: is the full dispatch path live? (hermes + at least one published profile + doer key)
    HERMES_OK=1
    command -v hermes >/dev/null 2>&1 || HERMES_OK=0
    { [ -d "$HOME/.hermes/profiles" ] && [ -n "$(ls -A "$HOME/.hermes/profiles" 2>/dev/null)" ]; } || HERMES_OK=0
    [ -f "$HOME/.config/minimax/m3-sub.key" ] || HERMES_OK=0
    if [ "$HERMES_OK" = "1" ]; then
        echo "  ✓ dispatch path preflight: LIVE (hermes + profiles + doer key)"
    else
        echo "  ⚠  dispatch path preflight: INCOMPLETE — doer seat not yet reachable (see notes above)"
    fi

    echo ""
    echo "✅ Star Alliance MCP server installed for this Mac. Restart Claude Code to connect."
    echo ""
    read -p "Press Enter to close..."
}

main "$@"
