"""hygiene_run.py — Hygiene Rotation: parameterized wrapper around the cleanup skill.

Shells the cleanup skill's orchestrator
    star-alliance-skills/cleanup/scripts/run_all.py
which runs the LOCAL hygiene modes detect-only and merges them into ONE ranked
triage report (/tmp/cleanup_triage.md).

IMPORTANT: that orchestrator targets the *Lex Council* app repo (its own root
walk-up, see run_all.py `default_root`), NOT this star-alliance repo. This wrapper
just gives the rotation a stable CLI and an optional publish gate.

CLI:
    python3 guild/hygiene_run.py --modes i18n,lint,dev_errors,postgres,docs [--publish-gate] [--dry-run] [--fast]

--modes is an advisory selector kept for API parity with the workflow step; the
underlying orchestrator's `run` runs all of its local modes in one pass (postgres
needs MCP and is merged-if-present, never auto-run). --publish-gate makes the
script exit non-zero if any CRITICAL/HIGH finding surfaces. --dry-run prints the
command it would run and exits 0 without invoking cleanup.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
RUN_ALL = REPO_ROOT / "star-alliance-skills" / "cleanup" / "scripts" / "run_all.py"
TRIAGE_MD = Path("/tmp/cleanup_triage.md")

# Findings at or above this severity block a publish gate.
BLOCKING_SEV = ("CRITICAL", "HIGH")


def _parse_blocking(report: str) -> list[str]:
    """Return triage rows whose severity is CRITICAL or HIGH."""
    blocking: list[str] = []
    for line in report.splitlines():
        # triage rows look like: | ⛔ CRITICAL | mode | finding | `drill` |
        if line.startswith("|") and any(f" {s} " in line or f"{s} |" in line for s in BLOCKING_SEV):
            # skip the header separator row
            if set(line.replace("|", "").strip()) <= {"-", " "}:
                continue
            blocking.append(line.strip())
    return blocking


def run(modes: str, publish_gate: bool, dry_run: bool, fast: bool) -> int:
    if not RUN_ALL.exists():
        print(f"ERROR: cleanup orchestrator not found at {RUN_ALL}", file=sys.stderr)
        print("       (cleanup skill missing or moved) — cannot run hygiene rotation.",
              file=sys.stderr)
        return 1

    cmd = ["python3", str(RUN_ALL), "run"]
    if fast:
        cmd.append("--fast")

    print(f"hygiene_run: modes={modes!r} publish_gate={publish_gate} fast={fast}")
    print(f"             orchestrator={RUN_ALL}")
    print("             [note] cleanup targets the Lex Council repo, not star-alliance.")

    if dry_run:
        print(f"dry-run: would run: {' '.join(cmd)}")
        print("dry-run: nothing executed.")
        return 0

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=1200)
    except subprocess.TimeoutExpired:
        print("ERROR: cleanup orchestrator timed out after 1200s", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"ERROR: could not run cleanup orchestrator: {exc}", file=sys.stderr)
        return 1

    if proc.stdout.strip():
        print(proc.stdout.rstrip())
    if proc.returncode != 0:
        print(f"WARN: cleanup orchestrator exited {proc.returncode}: "
              f"{(proc.stderr or '').strip()[:300]}", file=sys.stderr)

    # The triage report is the source of truth for the gate (stdout mirrors it).
    report = ""
    if TRIAGE_MD.exists():
        report = TRIAGE_MD.read_text(encoding="utf-8")
    else:
        report = proc.stdout or ""

    if publish_gate:
        blocking = _parse_blocking(report)
        if blocking:
            print(f"\nPUBLISH GATE: BLOCKED — {len(blocking)} CRITICAL/HIGH finding(s):",
                  file=sys.stderr)
            for row in blocking:
                print(f"  {row}", file=sys.stderr)
            return 1
        print("\nPUBLISH GATE: PASS — no CRITICAL/HIGH findings.")

    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Hygiene Rotation — wrap the cleanup skill")
    ap.add_argument("--modes", default="i18n,lint,dev_errors,postgres,docs",
                    help="Advisory mode selector (orchestrator runs all local modes in one pass)")
    ap.add_argument("--publish-gate", action="store_true",
                    help="Exit non-zero if any CRITICAL/HIGH finding surfaces")
    ap.add_argument("--dry-run", action="store_true",
                    help="Print the command that would run; execute nothing")
    ap.add_argument("--fast", action="store_true",
                    help="Skip the two slowest modes (lint, consolidate-code)")
    args = ap.parse_args()
    return run(args.modes, args.publish_gate, args.dry_run, args.fast)


if __name__ == "__main__":
    sys.exit(main())
