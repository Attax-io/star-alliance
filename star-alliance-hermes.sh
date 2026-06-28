#!/bin/bash
# Star Alliance — Hermes launcher.
# Starts the Butler profile for a Star Alliance session.
# Add this as an alias: alias sa="~/Documents/Claude/Projects/star-alliance/star-alliance-hermes.sh"

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT" || exit 1

echo "✦ Star Alliance — Hermes Butler session"
echo "  root: $ROOT"
echo "  profile: star-alliance-butler"
echo "  type /help for commands, /exit to quit"
echo ""

# Set STAR_ALLIANCE_ROOT so all skill/MCP scripts find the repo
export STAR_ALLIANCE_ROOT="$ROOT"

# Launch the Butler profile (the Guild Master's interface)
exec hermes --profile star-alliance-butler