#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────────────────
# Star Alliance — CONFORMANCE GATE  (Stop hook, BLOCKING)
#
# THE DOCTRINE: "The last specialist before the report is always the
# Quartermaster, running a conformance pass. Then the Butler delivers the
# plain-English report." Until now this was prose only — nothing checked that
# the Quartermaster actually ran before the report.
#
# WHAT THIS HOOK DOES
# ───────────────────
# At turn-end (Stop), for the MAIN SESSION (Butler), when:
#   • the turn was a FULL-tier approved work turn (approval-granted exists), AND
#   • source code changed this turn (fingerprint differs from baseline),
#
# it checks whether a Quartermaster conformance pass was logged this turn
# (state file `conformance-passed` exists, written by the Quartermaster or
# the Butler dispatching the Quartermaster).
#
#   • conformance-passed exists → ALLOW (the QM ran the conformance pass).
#   • conformance-passed does NOT exist → BLOCK. The turn cannot close until
#     the Butler dispatches the Quartermaster for a conformance pass.
#
# The gate does NOT fire when:
#   • No source changed this turn (conversation, planning, read-only turns).
#   • The turn was not a FULL-tier approved work turn (LITE/NONE tiers).
#   • We're in a child session (specialists don't close the report).
#
# Like verify-gate and delegation-gate, on BLOCK we drop a sentinel
# (.claude/state/conformance-block) that turn-finalize.sh honors to skip
# the commit. On pass we clear it.
#
# BYPASSES — STRICT MODE
# ──────────────────────
# No agent-controlled bypass. Kill switches:
#   • evolution/DISARMED                        (engine-wide)
#   • .claude/state/conformance-gate-disarmed   (this hook only)
# One-turn LOGGED override: SA_SKIP_CONFORMANCE=1 (for edge cases where the
# Butler judges the conformance pass is genuinely unnecessary — e.g., a
# trivial fix where the QM would add nothing).
#
# FAIL POSTURE
# ────────────
# Fail OPEN on any internal error — a broken gate must never trap the session.
# ─────────────────────────────────────────────────────────────────────────────
import os
import sys
import json
import subprocess

# Source extensions the gate cares about (must mirror verify_hash.py's set).
_SRC_EXT = {".py", ".js", ".ts", ".tsx", ".jsx", ".mjs", ".cjs", ".sh",
            ".sql", ".go", ".rs", ".rb", ".php", ".vue", ".svelte", ".css"}


def _proj():
    return os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def _state_dir():
    return os.path.join(_proj(), ".claude", "state")


def _is_kill_switch():
    if os.path.exists(os.path.join(_proj(), "evolution", "DISARMED")):
        return True
    if os.path.exists(os.path.join(_state_dir(), "conformance-gate-disarmed")):
        return True
    return False


def _is_child_session():
    return os.environ.get("CLAUDE_CODE_CHILD_SESSION") == "1"


def _source_fingerprint():
    """Get the current source fingerprint (same method as verify_hash.py)."""
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
    """Check if source code changed this turn (fingerprint != baseline)."""
    state = _state_dir()
    baseline_file = os.path.join(state, "verify-baseline")
    try:
        baseline = open(baseline_file).read().strip()
    except (OSError, IOError):
        baseline = ""
    if not baseline:
        return False  # no baseline → fail open
    current = _source_fingerprint()
    if current in ("", "CLEAN", "NOREPO"):
        return False
    return current != baseline


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    if _is_kill_switch():
        sys.exit(0)

    # One-turn logged override.
    if os.environ.get("SA_SKIP_CONFORMANCE") == "1":
        _clear_block()
        sys.exit(0)

    # Only fire in the main session (Butler). Child sessions don't close reports.
    if _is_child_session():
        sys.exit(0)

    state = _state_dir()
    approval_granted = os.path.exists(os.path.join(state, "approval-granted"))
    conformance_passed = os.path.exists(os.path.join(state, "conformance-passed"))

    # Only gate FULL-tier approved work turns.
    if not approval_granted:
        _clear_block()
        sys.exit(0)

    # Only gate turns where source actually changed.
    if not _source_changed():
        _clear_block()
        sys.exit(0)

    # Conformance pass already ran → allow.
    if conformance_passed:
        _clear_block()
        sys.exit(0)

    # Source changed on an approved work turn, no conformance pass → BLOCK.
    _set_block()
    sys.stderr.write(
        "⛔ CONFORMANCE GATE — this was an approved high-stakes work turn and "
        "source code changed, but no Quartermaster conformance pass was logged. "
        "The last specialist before the report must be the Quartermaster.\n"
        "   Dispatch the Quartermaster for a conformance pass:\n"
        "     Task(subagent_type=\"the-quartermaster\", prompt=\"Run the "
        "conformance pass on this work: verify agents, skills, workflows, and "
        "docs still agree and nothing the run produced contradicts guild state.\")\n"
        "   After the Quartermaster returns, write the conformance marker:\n"
        "     touch .claude/state/conformance-passed\n"
        "   Then end the turn again — the gate clears.\n"
        "   If the conformance pass is genuinely unnecessary (trivial fix), "
        "go on the record: SA_SKIP_CONFORMANCE=1\n"
        "   Kill switch: touch evolution/DISARMED\n"
    )
    sys.exit(2)


def _clear_block():
    sentinel = os.path.join(_state_dir(), "conformance-block")
    try:
        if os.path.exists(sentinel):
            os.remove(sentinel)
    except OSError:
        pass


def _set_block():
    sentinel = os.path.join(_state_dir(), "conformance-block")
    try:
        with open(sentinel, "w") as fh:
            fh.write("1")
    except OSError:
        pass


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        sys.stderr.write(f"[conformance-gate] {e}, failing open\n")
        sys.exit(0)