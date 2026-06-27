#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────────────────
# Star Alliance — TURN START  (UserPromptSubmit, non-blocking)
#
# Stamps .claude/state/turn-start with the epoch time (float seconds) so
# turn-cost.py can compute wall_ms = elapsed since prompt submission.
# Fails OPEN on any error — a broken timestamp must never block a turn.
# ─────────────────────────────────────────────────────────────────────────────
import sys, os, time, pathlib

def main():
    try:
        proj = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
        state = pathlib.Path(proj) / ".claude" / "state"
        state.mkdir(parents=True, exist_ok=True)
        (state / "turn-start").write_text(str(time.time()))
    except Exception:
        pass
    sys.exit(0)

if __name__ == "__main__":
    main()
