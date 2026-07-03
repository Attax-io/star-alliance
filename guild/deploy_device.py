#!/usr/bin/env python3
"""
deploy_device.py — Star Alliance DEPLOY DEVICE  (full fresh-device orchestrator)

Runs the complete setup sequence for bringing a new device up to working order:

    1. Preflight (warn-only) — STAR_ALLIANCE_ROOT resolvable, node on PATH,
       pyyaml importable.
    2. Execute the setup steps in order, streaming each step's stdout/stderr.
    3. Stop on the first hard error (returncode != 0).
    4. Print a final PASS / FAIL banner.

Usage:
    python3 guild/deploy_device.py            # run preflight + all steps
    python3 guild/deploy_device.py --help     # show CLI options

All commands are idempotent — safe to re-run after partial failures or on a
machine that has already been deployed.

Star Alliance is a Claude-only harness: there is no external doer/Hermes layer,
so the old Hermes profile-publish and profile-content steps are gone.

Steps:
    1. python3 guild/install_agents.py
    2. python3 build.py
    3. python3 star-alliance-skills/skillsmith/scripts/skill_sync.py plan
    4. python3 star-alliance-skills/skillsmith/scripts/skill_sync.py apply
    5. python3 .claude/tools/skill_fingerprint.py
    6. python3 tools/conformity_check.py
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Tuple


# ── Configuration ────────────────────────────────────────────────────────────

SCRIPT_PATH = Path(__file__).resolve()
REPO_ROOT = SCRIPT_PATH.parent.parent

# Fallback when STAR_ALLIANCE_ROOT is not set in the environment.
DEFAULT_REPO = "/Users/attaselim/Documents/Claude/Projects/star-alliance"

# Use the same Python interpreter that's running this script so venv/deps match.
PYTHON = sys.executable

# Ordered sequence: (display_name, argv[1:]). argv[0] is PYTHON.
SEQUENCE: List[Tuple[str, List[str]]] = [
    (
        "install_agents.py",
        [str(REPO_ROOT / "guild" / "install_agents.py")],
    ),
    (
        "build.py",
        [str(REPO_ROOT / "build.py")],
    ),
    (
        # step 3 only REPORTS the sync plan — the actual install of all skills
        # happens in step 4 via `apply`.
        "skill_sync (plan)",
        [
            str(REPO_ROOT / "star-alliance-skills" / "skillsmith" / "scripts" / "skill_sync.py"),
            "plan",
        ],
    ),
    (
        "skill_sync (apply)",
        [
            str(REPO_ROOT / "star-alliance-skills" / "skillsmith" / "scripts" / "skill_sync.py"),
            "apply",
        ],
    ),
    (
        "skill_fingerprint.py",
        [str(REPO_ROOT / ".claude" / "tools" / "skill_fingerprint.py")],
    ),
    (
        "conformity_check.py",
        [str(REPO_ROOT / "tools" / "conformity_check.py")],
    ),
]


# ── Preflight ────────────────────────────────────────────────────────────────

def _resolve_root() -> Optional[Path]:
    """Resolve STAR_ALLIANCE_ROOT: env wins, else fall back to DEFAULT_REPO."""
    env = os.environ.get("STAR_ALLIANCE_ROOT")
    if env:
        p = Path(env).expanduser().resolve()
        if p.is_dir():
            return p
    fallback = Path(DEFAULT_REPO).expanduser().resolve()
    if fallback.is_dir():
        return fallback
    return None


def _which(cmd: str) -> bool:
    return shutil.which(cmd) is not None


def preflight() -> List[str]:
    """
    Run all preflight checks. Return a list of warnings (empty = all OK).

    Preflight never hard-fails the deploy — missing prerequisites are surfaced
    as warnings so the operator can decide whether to proceed.
    """
    warnings: List[str] = []

    # 1. STAR_ALLIANCE_ROOT resolvable (env or fallback)
    root = _resolve_root()
    if root is None:
        warnings.append(
            f"STAR_ALLIANCE_ROOT not resolvable "
            f"(env unset and default {DEFAULT_REPO} missing)"
        )

    # 2. node on PATH
    if not _which("node"):
        warnings.append("'node' not on PATH (some skills require node)")

    # 3. pyyaml importable
    try:
        import yaml  # noqa: F401
    except ImportError:
        warnings.append("pyyaml not importable (`python3 -c 'import yaml'` fails)")

    return warnings


# ── Step execution ───────────────────────────────────────────────────────────

def run_step(idx: int, name: str, args: List[str]) -> bool:
    """
    Run one step via subprocess.run() with capture_output=False (the default)
    so the child's stdout/stderr stream straight through to the parent.

    Returns True on success, False on any failure (non-zero exit, missing
    executable, or KeyboardInterrupt).
    """
    print()
    print(f"== Step {idx}: {name} ==")
    cmd = [PYTHON] + args
    try:
        result = subprocess.run(cmd, cwd=str(REPO_ROOT))
    except FileNotFoundError as e:
        print(f"ERROR: could not launch step {idx} ({name}): {e}", file=sys.stderr)
        return False
    except KeyboardInterrupt:
        print(f"INTERRUPTED at step {idx} ({name})", file=sys.stderr)
        return False

    if result.returncode != 0:
        print(
            f"ERROR: step {idx} ({name}) failed with exit code {result.returncode}",
            file=sys.stderr,
        )
        return False
    return True


# ── Orchestration ────────────────────────────────────────────────────────────

def deploy(skip_preflight: bool = False) -> int:
    """Run preflight then the seven-step sequence. Returns process exit code."""
    root = _resolve_root()
    if root is None:
        print("FATAL: STAR_ALLIANCE_ROOT not resolvable.", file=sys.stderr)
        print(
            f"  set STAR_ALLIANCE_ROOT, or ensure {DEFAULT_REPO} exists.",
            file=sys.stderr,
        )
        return 2

    # Export the resolved root so child processes see it.
    os.environ["STAR_ALLIANCE_ROOT"] = str(root)
    print(f"STAR_ALLIANCE_ROOT: {root}")

    if not skip_preflight:
        warnings = preflight()
        print()
        if warnings:
            print(f"⚠  {len(warnings)} preflight warning(s):")
            for w in warnings:
                print(f"  - {w}")
        else:
            print("preflight: all checks passed")

    print()
    print(f"Running {len(SEQUENCE)} deploy steps…")
    print()

    failed_at: Optional[int] = None
    for i, (name, args) in enumerate(SEQUENCE, start=1):
        ok = run_step(i, name, args)
        if not ok:
            failed_at = i
            break

    print()
    if failed_at is None:
        print("═ DEPLOY DEVICE COMPLETE — PASS ═")
        return 0
    else:
        print(f"═ DEPLOY DEVICE FAILED at step {failed_at} ═")
        return 1


# ── CLI ──────────────────────────────────────────────────────────────────────

def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="deploy_device.py",
        description=(
            "Run the full fresh-device setup sequence. Preflight validates that "
            "PATH, keys, and tools are available (warnings only — no hard fail), "
            "then executes 7 setup steps in order, streaming each step's output "
            "and stopping on the first hard error. All steps are idempotent — "
            "safe to re-run."
        ),
    )
    parser.add_argument(
        "--skip-preflight", action="store_true",
        help="Skip the preflight checks (STAR_ALLIANCE_ROOT is still resolved).",
    )

    args = parser.parse_args(argv)
    return deploy(skip_preflight=args.skip_preflight)


if __name__ == "__main__":
    sys.exit(main())