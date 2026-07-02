#!/usr/bin/env python3
"""sync_hermes_skills.py — sync Star Alliance repo skills into the Hermes profile.

Scans the repo's `star-alliance-skills/` directory and creates symlinks in the
Hermes profile's `skills/` directory, one per skill (each skill dir has a
SKILL.md). Removes dead symlinks first (old ones pointing to a deleted repo).
Does NOT touch non-symlink directories (built-in Hermes skills like apple/,
research/, etc.). Idempotent — running twice produces the same result.

Usage:
    python3 tools/sync_hermes_skills.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# --- Paths --------------------------------------------------------------------

REPO_ROOT = Path("/Users/attaselim/Documents/Claude/Projects/star-alliance")
SOURCE = REPO_ROOT / "star-alliance-skills"
TARGET = Path.home() / ".hermes" / "profiles" / "star-alliance-butler" / "skills"


# --- Helpers ------------------------------------------------------------------


def is_skill_dir(d: Path) -> bool:
    """A skill directory is a directory containing a SKILL.md file."""
    return d.is_dir() and (d / "SKILL.md").is_file()


def symlink_target(link: Path) -> Path | None:
    """Return the resolved target of a symlink, or None if not a symlink."""
    if not link.is_symlink():
        return None
    # readlink gives the raw target as stored (may be absolute or relative).
    # .resolve() follows it to the real path; we compare via .resolve() too.
    try:
        return Path(os.readlink(str(link))).resolve()
    except OSError:
        return None


# --- Main sync ----------------------------------------------------------------


def sync() -> int:
    if not SOURCE.is_dir():
        print(f"error: source skills directory not found: {SOURCE}", file=sys.stderr)
        return 1

    # Collect repo skills (sorted for deterministic output).
    repo_skills: dict[str, Path] = {}
    for child in sorted(SOURCE.iterdir()):
        if is_skill_dir(child):
            repo_skills[child.name] = child.resolve()

    # Ensure the target directory exists.
    if not TARGET.exists():
        print(f"creating target directory: {TARGET}")
        TARGET.mkdir(parents=True, exist_ok=True)
    elif not TARGET.is_dir():
        print(f"error: target exists but is not a directory: {TARGET}", file=sys.stderr)
        return 1

    added: list[str] = []
    removed: list[str] = []
    skipped: list[str] = []

    # Walk existing entries in the target dir.
    for entry in sorted(TARGET.iterdir()):
        name = entry.name
        if entry.name.startswith("."):
            # Skip dotfiles / hidden (e.g. .hub, .bundled_manifest, .usage.json).
            continue
        if not entry.is_symlink():
            # Non-symlink directory or file — built-in Hermes skill. Do NOT touch.
            continue
        # It's a symlink. Resolve its stored target.
        current_target = symlink_target(entry)
        desired = repo_skills.get(name)
        if desired is not None:
            if current_target == desired:
                # Already correct — skip.
                skipped.append(name)
            else:
                # Points somewhere wrong (or dead). Remove and re-link below.
                entry.unlink()
                removed.append(name)
        else:
            # Symlink to a skill that no longer exists in the repo.
            entry.unlink()
            removed.append(name)

    # Re-create symlinks for repo skills that aren't already correctly linked.
    # (skipped ones are already correct; removed ones need re-linking; new ones
    # need linking.)
    skipped_set = set(skipped)
    for name, src in repo_skills.items():
        if name in skipped_set:
            continue
        link = TARGET / name
        if link.exists() or link.is_symlink():
            # Was removed above (or is a non-symlink we're not touching — but
            # those aren't in repo_skills by construction since is_symlink
            # filter above). Unlink to be safe and re-create.
            if link.is_symlink():
                link.unlink()
        added.append(name)
        link.symlink_to(src)

    # --- Summary ---------------------------------------------------------------
    print("Star Alliance skill sync")
    print(f"  source: {SOURCE}/")
    print(f"  target: {TARGET}/")
    print(f"  synced: {len(added)} skills")
    print(f"  removed: {len(removed)} dead symlinks")
    print(f"  skipped: {len(skipped)} already linked")

    if added:
        print()
        print("  added:")
        for n in added:
            print(f"    + {n}")
    if removed:
        print()
        print("  removed:")
        for n in removed:
            print(f"    - {n}")
    if skipped:
        print()
        print("  skipped (already linked):")
        for n in skipped:
            print(f"    = {n}")

    return 0


if __name__ == "__main__":
    raise SystemExit(sync())