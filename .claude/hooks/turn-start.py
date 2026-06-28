#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────────────────
# Star Alliance — TURN START  (UserPromptSubmit, non-blocking)
#
# Fires once per REAL user turn (UserPromptSubmit only — never on a blocking Stop
# hook's re-prompt). It establishes the turn's anchors:
#   1. .claude/state/turn-start      — epoch seconds, so turn-cost.py can compute
#      wall_ms AND use it as the once-per-turn sentinel (it deletes it after the
#      first Stop so re-prompt Stops don't log duplicate records).
#   2. .claude/state/verify-baseline — the SOURCE fingerprint AT TURN START, so
#      verify-gate.py can tell "source changed THIS turn" from "the tree already
#      carried uncommitted source". Without a baseline the gate fired on ANY dirty
#      tree and re-prompted every turn — the cause of the "triple response" loop.
#   3. clears per-turn reminder sentinels (e.g. weapon-reminded) so once-per-turn
#      doctrine reminders fire again on the new turn.
#
# Fails OPEN on any error — a broken anchor must never block a turn.
# ─────────────────────────────────────────────────────────────────────────────
import sys, os, time, pathlib, subprocess

# per-turn sentinels other hooks set and we reset each new turn
RESET_SENTINELS = ("weapon-reminded", "wf-ledgered", "pe-nudged",
                   "delegation-block", "delegation-ledgered", "thinker-attested",
                   "solo-once")


def main():
    try:
        proj = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
        state = pathlib.Path(proj) / ".claude" / "state"
        state.mkdir(parents=True, exist_ok=True)
        (state / "turn-start").write_text(str(time.time()))

        for s in RESET_SENTINELS:
            try:
                (state / s).unlink()
            except OSError:
                pass

        # Snapshot the source fingerprint at turn start (best-effort).
        try:
            hash_script = pathlib.Path(proj) / ".claude" / "hooks" / "verify_hash.py"
            cur = subprocess.run(
                ["python3", str(hash_script)],
                capture_output=True, text=True, timeout=20,
            ).stdout.strip()
            (state / "verify-baseline").write_text(cur)
        except Exception:
            pass
    except Exception:
        pass
    sys.exit(0)


if __name__ == "__main__":
    main()
