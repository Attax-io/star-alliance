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
                   "solo-once", "version-bumped", "conformance-block",
                   "conformance-passed", "strategist-dispatched")


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

        # P5 (self-enclosed campaign): clear the dynamic per-turn workflow sentinels
        # (xp-workflow-<name>) so once_per_turn() re-arms every turn instead of
        # firing once per workflow-name for the life of the session.
        try:
            for p in state.glob("xp-workflow-*"):
                try:
                    p.unlink()
                except OSError:
                    pass
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

        # Fix 1 (level auto-refresh): once per day, rebuild guild-data so usage-based
        # levels (skills / members / workflows) move on their own — no manual build.
        # Throttled by a dated sentinel; launched DETACHED so it never slows the turn;
        # fail-silent. build.py regenerates only generated files (guild-data.*), so a
        # daily run is the sanctioned refresh path, not a hand-edit.
        try:
            import datetime as _dt
            marker = state / f"level-refresh-{_dt.date.today().isoformat()}"
            if not marker.exists():
                marker.write_text("1")
                for old in state.glob("level-refresh-*"):
                    if old.name != marker.name:
                        try:
                            old.unlink()
                        except OSError:
                            pass
                build_py = pathlib.Path(proj) / "build.py"
                if build_py.exists():
                    logf = open(state / "level-refresh.log", "a")
                    subprocess.Popen(
                        ["python3", str(build_py)], cwd=proj,
                        stdout=logf, stderr=subprocess.STDOUT, start_new_session=True,
                    )
        except Exception:
            pass
    except Exception:
        pass
    sys.exit(0)


if __name__ == "__main__":
    main()
