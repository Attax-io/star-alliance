#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────────────────
# Star Alliance — CONFORMITY PRE-COMMIT GATE  (Stop hook, BLOCKING)
#
# THE RULE: a turn that changed source code cannot close with the repo out of
# conformity. This hook runs `tools/conformity_check.py` — the mechanical
# roster/parity/versions auditor (AG agents==members, VER versions==frontmatter,
# P guild-data parity, RG routing-gate roster==guild-data, FB fallback dicts==
# models.json, and every other check that script owns) — once per turn, only
# when source actually changed this turn, and BLOCKS the commit on failure.
#
# Mirrors the sibling-Stop sentinel pattern used by verify-gate.py /
# delegation-gate.py / conformance-gate.py: this hook is a SIBLING Stop command
# and its own exit 2 does NOT abort turn-finalize.sh (a Stop hook's non-zero
# exit stops that hook's own event chain, not sibling hooks registered under
# the same event). So on BLOCK we drop a sentinel
# (.claude/state/conformity-precommit-block) that turn-finalize.sh honors to
# skip the commit; on pass we clear it.
#
# Uses the SAME CLEAN-detection approach as verify_hash.py — a "CLEAN"/"NOREPO"
# fingerprint means no source changed this turn, so the gate stands aside.
# Anything else means source changed and the conformity check must run.
#
# KILL SWITCHES
#   • evolution/DISARMED                          (engine-wide)
#   • .claude/state/conformity-precommit-disarmed (this hook only)
# One-turn LOGGED override: SA_SKIP_CONFORMITY=1
#
# FAIL POSTURE
# ────────────
# Fails OPEN if conformity_check.py itself crashes, errors, or is missing —
# an infra failure in the auditor must never brick the session. Only a CLEAN
# conformity_check.py run that reports real FAIL lines blocks the turn.
# ─────────────────────────────────────────────────────────────────────────────
import os
import sys
import json
import subprocess


def _proj():
    return os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def _state_dir():
    return os.path.join(_proj(), ".claude", "state")


def _is_kill_switch():
    if os.path.exists(os.path.join(_proj(), "evolution", "DISARMED")):
        return True
    if os.path.exists(os.path.join(_state_dir(), "conformity-precommit-disarmed")):
        return True
    return False


def _source_fingerprint():
    """Same CLEAN-detection approach as verify_hash.py (turn-finalize.sh mirrors this too)."""
    hash_script = os.path.join(_proj(), ".claude", "hooks", "verify_hash.py")
    try:
        result = subprocess.run(
            ["python3", hash_script],
            capture_output=True, text=True, timeout=20
        )
        return result.stdout.strip()
    except Exception:
        return ""


def _source_changed():
    fp = _source_fingerprint()
    return fp not in ("", "CLEAN", "NOREPO")


def _run_conformity_check():
    """Run tools/conformity_check.py. Returns (ok, output) where ok=True means
    PASS or the script itself failed to run (infra failure -> fail open)."""
    script = os.path.join(_proj(), "tools", "conformity_check.py")
    if not os.path.isfile(script):
        # Infra failure: auditor missing -> fail open, don't block on our own absence.
        return True, "[conformity-precommit-gate] tools/conformity_check.py not found, failing open\n"
    try:
        result = subprocess.run(
            ["python3", script],
            capture_output=True, text=True, timeout=120,
            cwd=_proj(),
        )
    except Exception as e:
        # Infra failure (crash, timeout, etc.) -> fail open.
        return True, f"[conformity-precommit-gate] conformity_check.py errored, failing open: {e}\n"

    output = (result.stdout or "") + (result.stderr or "")
    # conformity_check.py exits non-zero on real conformity failures.
    # A clean run (exit 0) always passes.
    if result.returncode == 0:
        return True, output
    return False, output


def _clear_block():
    sentinel = os.path.join(_state_dir(), "conformity-precommit-block")
    try:
        if os.path.exists(sentinel):
            os.remove(sentinel)
    except OSError:
        pass


def _set_block():
    sentinel = os.path.join(_state_dir(), "conformity-precommit-block")
    try:
        with open(sentinel, "w") as fh:
            fh.write("1")
    except OSError:
        pass


def main():
    try:
        json.load(sys.stdin)
    except Exception:
        # Malformed payload -> fail open.
        sys.exit(0)

    if _is_kill_switch():
        sys.exit(0)

    if os.environ.get("SA_SKIP_CONFORMITY") == "1":
        _clear_block()
        sys.exit(0)

    if not _source_changed():
        _clear_block()
        sys.exit(0)

    ok, output = _run_conformity_check()

    if ok:
        _clear_block()
        sys.exit(0)

    _set_block()
    sys.stderr.write(
        "⛔ CONFORMITY PRE-COMMIT GATE — source changed this turn and "
        "`tools/conformity_check.py` reports the repo is OUT of conformity. "
        "The commit is skipped until this is fixed.\n"
        "----------------------------------------------------------------\n"
        f"{output.strip()}\n"
        "----------------------------------------------------------------\n"
        "   Fix the reported FAIL line(s), then end the turn again — the gate\n"
        "   re-runs the check and clears once it passes.\n"
        "   One-turn logged override (use only for a genuine false positive):\n"
        "     SA_SKIP_CONFORMITY=1\n"
        "   Kill switches:\n"
        "     touch .claude/state/conformity-precommit-disarmed   (this hook only)\n"
        "     touch evolution/DISARMED                            (engine-wide)\n"
    )
    sys.exit(2)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        sys.stderr.write(f"[conformity-precommit-gate] {e}, failing open\n")
        sys.exit(0)
