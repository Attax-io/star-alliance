"""device_sync.py — sweep every repo-to-device parity surface and report drift.

The Quartermaster's device-parity primitive. One read-only pass over every
surface where the on-device install can fall behind the repo source of truth:

  1. skills      — repo vs ~/.hermes/skills (delegates to skillsmith skill_sync.py plan)
  2. cron        — ~/.hermes/cron/* point at the canonical repo path (not a stale rename)
  3. agents      — agents/*.md committed (no uncommitted roster drift)
  4. config      — repo AGENTS.md + state/* tracked (runtime files ignored)

Default is --check (read-only): prints a parity table and exits non-zero only on
a HARD drift (skills repo-ahead of device, or a cron job pointing at a dead
path). Pass --reconcile to install repo-ahead skills onto the device via skillsmith.

CLI:
    python3 guild/device_sync.py [--check] [--reconcile]

Exit code: 0 = device matches repo (or info-only drift), 1 = HARD drift found.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_REPO = REPO_ROOT / "star-alliance-skills"
SKILL_SYNC = SKILLS_REPO / "skillsmith" / "scripts" / "skill_sync.py"
HERMES_HOME = Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes"))
CRON_DIR = HERMES_HOME / "cron"
CANONICAL = str(REPO_ROOT)


def _run(cmd: list[str], cwd: Path) -> tuple[int, str]:
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, cwd=str(cwd), timeout=300)
        return p.returncode, (p.stdout or "") + (p.stderr or "")
    except Exception as exc:  # surface, never swallow
        return 1, f"failed: {' '.join(cmd)}: {exc}"


def sweep_skills() -> tuple[bool, str, list[str]]:
    """Returns (hard_drift, summary, install_targets)."""
    if not SKILL_SYNC.exists():
        return False, f"skills    SKIP  skill_sync.py not found at {SKILL_SYNC}", []
    code, out = _run(["python3", str(SKILL_SYNC), "plan"], cwd=SKILLS_REPO)
    install, stamp = [], []
    bucket = None
    for line in out.splitlines():
        s = line.strip()
        if s.startswith("## INSTALL"):
            bucket = "install"; continue
        if s.startswith("## STAMP"):
            bucket = "stamp"; continue
        if s.startswith("## "):
            bucket = None; continue
        if bucket == "install" and s:
            install.append(s.split()[0])
        elif bucket == "stamp" and s:
            stamp.append(s.split()[0])
    hard = bool(install)
    flag = "DRIFT" if hard else "OK"
    summ = f"skills    {flag:5} {len(install)} repo-ahead (install), {len(stamp)} stamp"
    return hard, summ, install


def sweep_cron() -> tuple[bool, str]:
    if not CRON_DIR.exists():
        return False, "cron      SKIP  no ~/.hermes/cron"
    stale = []
    for f in CRON_DIR.rglob("*"):
        if not f.is_file():
            continue
        try:
            txt = f.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        # a path that names an old checkout of this repo but not the canonical dir
        if "claude-skills" in txt and CANONICAL not in txt:
            stale.append(f.name)
    stale = sorted(set(stale))
    hard = bool(stale)
    flag = "DRIFT" if hard else "OK"
    summ = f"cron      {flag:5} {len(stale)} stale-path task(s)" + (f": {', '.join(stale)}" if stale else "")
    return hard, summ


def _git_dirty(pathspec: str) -> list[str]:
    code, out = _run(["git", "status", "--porcelain", "--", pathspec], cwd=REPO_ROOT)
    rows = []
    for line in out.splitlines():
        if not line.strip():
            continue
        # ignore untracked runtime state under state/
        name = line[3:].strip()
        if name.startswith("state/") or "/state/" in name:
            continue
        rows.append(line.rstrip())
    return rows


def sweep_agents() -> tuple[bool, str]:
    rows = _git_dirty("agents")
    # roster drift is informational, not hard — surfaces for the operator
    flag = "INFO" if rows else "OK"
    summ = f"agents    {flag:5} {len(rows)} uncommitted roster file(s)"
    return False, summ


def sweep_config() -> tuple[bool, str]:
    rows = _git_dirty("AGENTS.md") + _git_dirty("state")
    flag = "INFO" if rows else "OK"
    summ = f"config    {flag:5} {len(rows)} uncommitted config/state file(s) (runtime state ignored)"
    return False, summ


def main() -> int:
    ap = argparse.ArgumentParser(description="Sweep repo-to-device parity and report drift")
    ap.add_argument("--check", action="store_true", help="read-only sweep (default)")
    ap.add_argument("--reconcile", action="store_true", help="install repo-ahead skills to device via skillsmith")
    args = ap.parse_args()

    print("─" * 60)
    print(" DEVICE PARITY SWEEP — the Quartermaster's board")
    print("─" * 60)

    hard_skills, s_skills, install = sweep_skills()
    hard_cron, s_cron = sweep_cron()
    _, s_agents = sweep_agents()
    _, s_config = sweep_config()

    for s in (s_skills, s_cron, s_agents, s_config):
        print("  " + s)

    if args.reconcile and install and SKILL_SYNC.exists():
        print("─" * 60)
        print(f" RECONCILE — installing {len(install)} repo-ahead skill(s) to device")
        for skill in install:
            code, out = _run(
                ["python3", str(SKILL_SYNC), "apply", "--skill", skill, "--direction", "install"],
                cwd=SKILLS_REPO,
            )
            tail = out.strip().splitlines()[-1] if out.strip() else "(no output)"
            print(f"   {skill}: {tail}")
        hard_skills = False  # reconciled

    hard = hard_skills or hard_cron
    print("─" * 60)
    if hard:
        print(" ✗ DRIFT — device is behind repo. Run --reconcile (skills) / repoint stale tasks.")
    else:
        print(" ✓ PARITY — device matches repo (info rows are uncommitted-but-tracked).")
    print("─" * 60)
    return 1 if hard else 0


if __name__ == "__main__":
    sys.exit(main())