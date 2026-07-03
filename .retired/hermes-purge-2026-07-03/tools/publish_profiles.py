#!/usr/bin/env python3
"""
publish_profiles.py — Install/update the 7 specialist profiles as Hermes
distributions.

Each profile directory under profiles/<agent>/ contains a distribution.yaml
that makes it a native Hermes profile distribution. This script wraps
`hermes profile install` and `hermes profile update` so you can publish all
7 profiles in one command.

Usage:
    python3 tools/publish_profiles.py                # install all 7 (force)
    python3 tools/publish_profiles.py --dry-run      # preview only
    python3 tools/publish_profiles.py --only the-architect,the-merchant
    python3 tools/publish_profiles.py --update       # update existing profiles

The profiles are installed to ~/.hermes/profiles/<slug>/ via Hermes' native
distribution system. After git pull, run with --update to pull new SOUL.md,
config.yaml, and skills.yaml into the installed profiles — memories, sessions,
and auth are always preserved.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


# ── Configuration ────────────────────────────────────────────────────────────

SCRIPT_PATH = Path(__file__).resolve()
REPO_ROOT = SCRIPT_PATH.parent.parent
PROFILES_SRC_DIR = REPO_ROOT / "profiles"

# slug → source folder name
PROFILE_MAP = {
    "the-architect":     "architect",
    "the-developer":     "developer",
    "the-designer":      "designer",
    "the-interpreter": "interpreter",
    "the-herald":        "herald",
    "the-merchant":      "merchant",
    "the-quartermaster": "quartermaster",
    "the-steward":       "steward",
    "the-strategist":    "strategist",
}


# ── Helpers ──────────────────────────────────────────────────────────────────

def _hermes_cmd(args: list[str]) -> list[str]:
    """Build a hermes CLI command."""
    return ["hermes"] + args


def _profile_dir(slug: str) -> Path:
    """Where the profile is installed on disk."""
    return Path.home() / ".hermes" / "profiles" / slug


def _is_installed(slug: str) -> bool:
    d = _profile_dir(slug)
    return d.is_dir() and (d / "distribution.yaml").exists()


# ── Core operations ──────────────────────────────────────────────────────────

@dataclass
class PublishResult:
    slug: str
    status: str  # "installed" | "updated" | "skipped" | "error" | "would_install" | "would_update"
    message: str = ""


def _install_one(slug: str, folder: str, *, dry_run: bool) -> PublishResult:
    """Install (or reinstall) a profile via `hermes profile install --force`."""
    source = str(PROFILES_SRC_DIR / folder)

    if dry_run:
        existing = _is_installed(slug)
        action = "would_update" if existing else "would_install"
        return PublishResult(slug=slug, status=action,
                             message=f"{'update' if existing else 'install'} {slug} from {source}")

    cmd = _hermes_cmd([
        "profile", "install",
        source,
        "--name", slug,
        "--force",   # overwrite existing distribution-owned files
        "-y",        # skip confirmation
    ])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    except subprocess.TimeoutExpired:
        return PublishResult(slug=slug, status="error", message="timed out")
    except FileNotFoundError:
        return PublishResult(slug=slug, status="error", message="hermes CLI not found on PATH")

    if result.returncode == 0:
        action = "updated" if _is_installed(slug) else "installed"
        return PublishResult(slug=slug, status=action, message="ok")
    else:
        err = result.stderr.strip() or result.stdout.strip()
        return PublishResult(slug=slug, status="error", message=err)


def _update_one(slug: str, *, dry_run: bool) -> PublishResult:
    """Update an existing profile via `hermes profile update`."""
    if not _is_installed(slug):
        return PublishResult(slug=slug, status="error",
                             message=f"profile {slug} is not installed (run without --update first)")

    if dry_run:
        return PublishResult(slug=slug, status="would_update", message=f"update {slug}")

    cmd = _hermes_cmd(["profile", "update", slug, "-y"])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    except subprocess.TimeoutExpired:
        return PublishResult(slug=slug, status="error", message="timed out")
    except FileNotFoundError:
        return PublishResult(slug=slug, status="error", message="hermes CLI not found on PATH")

    if result.returncode == 0:
        return PublishResult(slug=slug, status="updated", message="ok")
    else:
        err = result.stderr.strip() or result.stdout.strip()
        return PublishResult(slug=slug, status="error", message=err)


def publish_all(
    only: Optional[List[str]],
    *,
    update: bool,
    dry_run: bool,
) -> List[PublishResult]:
    if only:
        unknown = [s for s in only if s not in PROFILE_MAP]
        if unknown:
            print(f"ERROR: unknown slug(s): {', '.join(unknown)}", file=sys.stderr)
            print(f"Valid slugs: {', '.join(PROFILE_MAP.keys())}", file=sys.stderr)
            sys.exit(2)
        slugs = [s for s in only if s in PROFILE_MAP]
    else:
        slugs = list(PROFILE_MAP.keys())

    action = "Updating" if update else "Installing"
    print(f"{action} {len(slugs)} profile(s)")
    print(f"  source: {PROFILES_SRC_DIR}")
    if dry_run:
        print("  mode:   DRY-RUN (no changes)")
    print()

    results: List[PublishResult] = []
    for slug in slugs:
        folder = PROFILE_MAP[slug]

        if update:
            r = _update_one(slug, dry_run=dry_run)
        else:
            r = _install_one(slug, folder, dry_run=dry_run)

        if r.status in ("installed", "updated"):
            print(f"  ✓ {slug:20s} {r.status}")
        elif r.status in ("would_install", "would_update"):
            print(f"  ~ {slug:20s} {r.status}")
        elif r.status == "skipped":
            print(f"  - {slug:20s} skipped")
        else:
            print(f"  ✗ {slug:20s} ERROR: {r.message}", file=sys.stderr)

        results.append(r)

    # Summary
    ok = sum(1 for r in results if r.status in ("installed", "updated"))
    would = sum(1 for r in results if r.status in ("would_install", "would_update"))
    errors = sum(1 for r in results if r.status == "error")

    print()
    print("=" * 64)
    if dry_run:
        print(f"DRY-RUN: would_process={would}, errors={errors}")
    else:
        print(f"SUMMARY: {ok} succeeded, {errors} errors")
    print("=" * 64)

    return results


# ── CLI ──────────────────────────────────────────────────────────────────────

def _parse_only(value: str) -> List[str]:
    return [s.strip() for s in value.split(",") if s.strip()]


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="publish_profiles.py",
        description=(
            "Install or update the 7 specialist profiles as Hermes distributions. "
            "Profiles are installed via `hermes profile install` — the repo is the "
            "source of truth. Use --update after git pull to refresh installed profiles."
        ),
    )
    parser.add_argument(
        "--update", action="store_true",
        help="Update existing profiles in place (preserves memories/sessions/auth). "
             "Default is to install (or reinstall with --force).",
    )
    parser.add_argument(
        "--only", type=_parse_only, default=None, metavar="SLUGS",
        help="Comma-separated list of slugs (e.g. the-architect,the-merchant).",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print what would happen without making changes.",
    )

    args = parser.parse_args(argv)

    results = publish_all(args.only, update=args.update, dry_run=args.dry_run)
    return 0 if not any(r.status == "error" for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())