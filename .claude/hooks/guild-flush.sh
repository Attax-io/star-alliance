#!/bin/sh
# SessionStart: drain the outbox opportunistically. Fail-open, short timeout.
timeout 3 python3 "$CLAUDE_PROJECT_DIR/bin/sa" flush >/dev/null 2>&1 || true
exit 0
