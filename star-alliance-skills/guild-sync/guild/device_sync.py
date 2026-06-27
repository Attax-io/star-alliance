#!/usr/bin/env python3
"""guild-sync — repo→device parity sweep across all four surfaces.

The repo is the source of truth; the device is what actually runs. This primitive
proves the device still matches the repo, and (with --reconcile) closes the gap.

It orchestrates the SWEEP; it does NOT re-implement skill version logic — the skills
surface is delegated wholesale to skillsmith's scripts/skill_sync.py (plan + apply).

Surfaces (see SKILL.md):
  skills           HARD — repo-ahead silently runs old code        (delegated to skillsmith)
  scheduled-tasks  HARD — a stale-rename operating path kills the daily routine
  members          INFO — uncommitted roster drift (repo-local)
  config           INFO — uncommitted .claude hooks/settings (runtime state/* ignored)

Usage:
  python3 guild/device_sync.py --check       # read-only sweep + parity board (default)
  python3 guild/device_sync.py --reconcile   # + install repo-ahead skills via skillsmith

--check exits non-zero ONLY on HARD drift (skills repo-ahead, or a scheduled-task
pointing at a dead `claude-skills` path). --reconcile installs the skillsmith plan's
INSTALL/STAMP bucket (never FORK/external), then re-reports.
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

GLOBAL_SKILLS = Path.home() / ".claude" / "skills"
SCHEDULED_TASKS = Path.home() / ".claude" / "scheduled-tasks"

# skillsmith plan buckets that mean "repo is ahead → install repo→device" (HARD drift).
REPO_AHEAD_TAGS = {"INSTALL", "STAMP"}
# buckets that are informational in the repo→device direction (device ahead / device-only / fork).
INFO_TAGS = {"PUSH", "ADD-TO-REPO"}
SKIP_TAGS = {"FORK"}

# An absolute path token that contains `claude-skills` as a real path fragment.
# Prose like "the old claude-skills path" has no leading slash and won't match,
# so benign mentions of the old name are NOT flagged — only a real operating path is.
CLAUDE_SKILLS_PATH = re.compile(r"(/[^\s'\"`)]*claude-skills[^\s'\"`)]*)")


def find_repo() -> Path | None:
    """Resolve the star-alliance repo regardless of where this runs (device or repo)."""
    for env in ("STAR_ALLIANCE_ROOT", "STAR_ALLIANCE_REPO"):
        v = os.environ.get(env)
        if v and (Path(v).expanduser() / "VERSIONS.md").exists():
            return Path(v).expanduser().resolve()
    here = Path(__file__).resolve()
    for anc in here.parents:
        if (anc / "VERSIONS.md").exists() and (anc / ".git").exists():
            return anc
    known = Path.home() / "Documents" / "Claude" / "Projects" / "star-alliance"
    if (known / "VERSIONS.md").exists():
        return known.resolve()
    return None


def skill_sync_path(repo: Path) -> Path | None:
    p = repo / "star-alliance-skills" / "skillsmith" / "scripts" / "skill_sync.py"
    return p if p.exists() else None


def run_skillsmith_plan(repo: Path) -> tuple[dict[str, list[str]], str | None]:
    """Return {bucket_tag: [skill_name, ...]} by parsing `skill_sync.py plan`."""
    ss = skill_sync_path(repo)
    if not ss:
        return {}, f"skillsmith skill_sync.py not found under {repo}"
    try:
        out = subprocess.run(
            [sys.executable, str(ss), "plan"],
            capture_output=True, text=True, cwd=str(repo), timeout=120,
        )
    except Exception as e:  # noqa: BLE001
        return {}, f"skillsmith plan failed to run: {e}"
    if out.returncode != 0:
        return {}, f"skillsmith plan exited {out.returncode}: {out.stderr.strip()[:200]}"
    buckets: dict[str, list[str]] = {}
    cur = None
    for line in out.stdout.splitlines():
        m = re.match(r"##\s+([A-Z-]+)\s+\(\d+\)", line)
        if m:
            cur = m.group(1)
            buckets.setdefault(cur, [])
            continue
        if cur and line.startswith("  "):
            name = line.strip().split()[0]
            if name:
                buckets[cur].append(name)
    return buckets, None


# ── surface checks ────────────────────────────────────────────────────────────

def check_skills(repo: Path):
    """HARD. Delegates the compare to skillsmith. Returns (status, detail, payload)."""
    buckets, err = run_skillsmith_plan(repo)
    if err:
        return "SKIP", err, {}
    repo_ahead = [n for t in REPO_AHEAD_TAGS for n in buckets.get(t, [])]
    forks = buckets.get("FORK", [])
    info = [n for t in INFO_TAGS for n in buckets.get(t, [])]
    if repo_ahead:
        bits = [f"{len(repo_ahead)} repo-ahead → install: {', '.join(sorted(repo_ahead))}"]
        if forks:
            bits.append(f"{len(forks)} fork (skip): {', '.join(sorted(forks))}")
        if info:
            bits.append(f"{len(info)} device-ahead/device-only (review): {', '.join(sorted(info))}")
        return "DRIFT", "; ".join(bits), {"install": repo_ahead}
    extra = []
    if info:
        extra.append(f"{len(info)} device-ahead/device-only (review): {', '.join(sorted(info))}")
    if forks:
        extra.append(f"{len(forks)} fork (manual)")
    ok = len(buckets.get("OK", []))
    detail = f"{ok} in sync" + (" — " + "; ".join(extra) if extra else "")
    # device-ahead / device-only are INFO, not HARD; only repo-ahead gates the exit code.
    return ("INFO" if info else "OK"), detail, {"install": []}


def check_scheduled_tasks(repo: Path):
    """HARD. Flag any scheduled-task file whose operating path points at a dead
    `claude-skills` directory (the 1.1.8 rename class). Benign prose is ignored."""
    if not SCHEDULED_TASKS.is_dir():
        return "SKIP", f"no {SCHEDULED_TASKS}", {}
    stale: list[str] = []
    scanned = 0
    for f in sorted(SCHEDULED_TASKS.rglob("*")):
        if not f.is_file():
            continue
        try:
            text = f.read_text(errors="ignore")
        except Exception:  # noqa: BLE001
            continue
        scanned += 1
        for pathtok in CLAUDE_SKILLS_PATH.findall(text):
            # A real operating path that no longer exists on disk = stale rename drift.
            if not Path(pathtok).exists():
                rel = f.relative_to(SCHEDULED_TASKS)
                stale.append(f"{rel}: {pathtok}")
    if stale:
        return "DRIFT", f"{len(stale)} stale claude-skills path(s): " + " | ".join(stale), {}
    return "OK", f"{scanned} task file(s), no dead claude-skills paths", {}


def _git_dirty(repo: Path, pathspec: str) -> list[str]:
    try:
        out = subprocess.run(
            ["git", "-C", str(repo), "status", "--porcelain", "--", pathspec],
            capture_output=True, text=True, timeout=30,
        )
    except Exception:  # noqa: BLE001
        return []
    return [ln for ln in out.stdout.splitlines() if ln.strip()]


def check_members(repo: Path):
    """INFO. Uncommitted roster files are reported, never auto-committed."""
    dirty = _git_dirty(repo, "star-alliance-members")
    if dirty:
        return "INFO", f"{len(dirty)} uncommitted member file(s)", {}
    return "OK", "roster committed", {}


def check_config(repo: Path):
    """INFO. Uncommitted .claude config (hooks/settings); runtime state/* is NOT drift."""
    # porcelain lines are "XY <path>"; drop the 3-char status prefix to get the path.
    dirty = [
        ln for ln in _git_dirty(repo, ".claude")
        if ".claude/state/" not in ln[3:]  # invariant 4: per-turn runtime is not drift
    ]
    if dirty:
        return "INFO", f"{len(dirty)} uncommitted .claude config file(s)", {}
    return "OK", ".claude config committed", {}


SURFACES = [
    ("skills", check_skills, True),
    ("scheduled-tasks", check_scheduled_tasks, True),
    ("members", check_members, False),
    ("config", check_config, False),
]


def sweep(repo: Path):
    """Run every surface. Returns list of (name, status, detail, hard, payload)."""
    rows = []
    for name, fn, hard in SURFACES:
        status, detail, payload = fn(repo)
        rows.append((name, status, detail, hard, payload))
    return rows


def print_board(repo: Path, rows):
    print(f"\nGUILD-SYNC parity board   (repo: {repo})")
    print("-" * 72)
    glyph = {"OK": "✓", "DRIFT": "✗", "INFO": "·", "SKIP": "–"}
    for name, status, detail, hard, _ in rows:
        tag = f"{glyph.get(status, '?')} {status}"
        cls = "HARD" if hard else "INFO"
        print(f"  {name:16} {tag:9} [{cls}] {detail}")
    print("-" * 72)


def hard_drift(rows) -> bool:
    return any(status == "DRIFT" and hard for _, status, _, hard, _ in rows)


def reconcile_skills(repo: Path, install: list[str]) -> int:
    """Install each repo-ahead skill via skillsmith (INSTALL/STAMP bucket only)."""
    ss = skill_sync_path(repo)
    if not ss:
        print("  cannot reconcile: skillsmith skill_sync.py not found", file=sys.stderr)
        return 2
    rc = 0
    for name in sorted(set(install)):
        print(f"  → installing {name} (repo→device, via skillsmith)")
        r = subprocess.run(
            [sys.executable, str(ss), "apply", "--skill", name, "--direction", "install"],
            cwd=str(repo),
        )
        rc = rc or r.returncode
    return rc


def main() -> int:
    ap = argparse.ArgumentParser(description="guild-sync repo→device parity sweep")
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="read-only sweep (default)")
    mode.add_argument("--reconcile", action="store_true",
                      help="install repo-ahead skills via skillsmith, then re-report")
    a = ap.parse_args()

    # Line-buffer our prints so they interleave correctly with delegated subprocess
    # output (skillsmith writes to the inherited fd directly).
    try:
        sys.stdout.reconfigure(line_buffering=True)
    except Exception:  # noqa: BLE001
        pass

    repo = find_repo()
    if not repo:
        print("✗ cannot locate star-alliance repo (set STAR_ALLIANCE_ROOT)", file=sys.stderr)
        return 2

    rows = sweep(repo)
    print_board(repo, rows)

    if a.reconcile:
        install = []
        for name, status, _, _, payload in rows:
            if name == "skills" and status == "DRIFT":
                install = payload.get("install", [])
        if install:
            print("\nReconciling repo-ahead skills:")
            reconcile_skills(repo, install)
            rows = sweep(repo)          # re-sweep after install
            print_board(repo, rows)
        else:
            print("\nNo repo-ahead skills to install.")
        # scheduled-task drift is a device-config edit — surfaced, not auto-fixed.
        for name, status, detail, hard, _ in rows:
            if name == "scheduled-tasks" and status == "DRIFT":
                print(f"\n⚠ scheduled-tasks DRIFT needs a manual repoint: {detail}")

    if hard_drift(rows):
        print("\n✗ DRIFT — hard parity gap remains (see board above)")
        return 1
    print("\n✓ PARITY — device matches repo on all hard surfaces")
    return 0


if __name__ == "__main__":
    sys.exit(main())
