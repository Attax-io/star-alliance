"""prune_runs.py — cap the gitignored runs/ scratch directory.

Each workflow run writes its artifacts into a state-dir under runs/ (e.g.
runs/standard-mission/). These accumulate unbounded. This keeps the N most
recent run state-dirs (by mtime) and deletes the older ones. Only directories
are pruning candidates — loose files under runs/ are left alone.

CLI:
    python3 guild/prune_runs.py [--keep N] [--dry-run]

Defaults: --keep 10. --dry-run lists what would be deleted and removes nothing.
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
RUNS_DIR = REPO_ROOT / "runs"


def run_dirs() -> list[Path]:
    """Run state-dirs under runs/, newest first by mtime."""
    if not RUNS_DIR.exists():
        return []
    dirs = [p for p in RUNS_DIR.iterdir() if p.is_dir()]
    return sorted(dirs, key=lambda p: p.stat().st_mtime, reverse=True)


def main() -> int:
    ap = argparse.ArgumentParser(description="Prune old run state-dirs under runs/.")
    ap.add_argument("--keep", type=int, default=10,
                    help="Number of most-recent run dirs to keep (default: 10).")
    ap.add_argument("--dry-run", action="store_true",
                    help="List what would be deleted without deleting anything.")
    args = ap.parse_args()

    if args.keep < 0:
        print("--keep must be >= 0", file=sys.stderr)
        return 2

    if not RUNS_DIR.exists():
        print(f"runs/ not found at {RUNS_DIR} — nothing to prune.")
        return 0

    dirs = run_dirs()
    keep = dirs[: args.keep]
    doomed = dirs[args.keep:]

    print(f"runs/: {len(dirs)} run dir(s); keep {len(keep)}, "
          f"{'would delete' if args.dry_run else 'deleting'} {len(doomed)}.")

    if not doomed:
        print("nothing to prune.")
        return 0

    for p in doomed:
        rel = p.relative_to(REPO_ROOT)
        if args.dry_run:
            print(f"  would delete: {rel}")
            continue
        try:
            shutil.rmtree(p)
            print(f"  deleted: {rel}")
        except Exception as exc:
            print(f"  ! failed to delete {rel}: {exc}", file=sys.stderr)
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
