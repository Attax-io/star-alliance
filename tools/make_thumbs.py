#!/usr/bin/env python3
"""make_thumbs.py — generate dashboard thumbnails from art/{skill,workflow,member}-art/.

The dashboard tiles render <100px icons, but the source PNGs are 1024x1024 JPEGs
(~80MB across the three dirs), causing a multi-second hitch on first paint.
This script writes per-source-dir sibling '<dir>-thumb' directories holding 96x96
(or 192x192 for portraits) JPEG thumbnails, and is idempotent (skips a thumb if
it already exists AND is newer than its source).

The source files are JPEG bytes misnamed with a .png suffix — Pillow opens them
with Image.open() regardless of extension. Output keeps the same filename so the
dashboard can swap `art/skill-art/${id}.png` to `art/skill-art-thumb/${id}.png`
with no other plumbing changes.

Usage:
  python3 tools/make_thumbs.py
  python3 tools/make_thumbs.py --force   # regenerate even when source is older

Requires: Pillow (PIL). Install with:
  python3 -m pip install pillow
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image

REPO = Path(__file__).resolve().parent.parent
ART = REPO / "art"

# (source dir, output dir, max_edge_px)
TARGETS: list[tuple[str, str, int]] = [
    ("skill-art",    "skill-art-thumb",    96),
    ("workflow-art", "workflow-art-thumb", 96),
    ("member-art",   "member-art-thumb",  192),  # portraits show at 88px in the card
]


def needs_regen(src: Path, dst: Path) -> bool:
    """A thumb needs regenerating when it doesn't exist or the source is newer."""
    if not dst.exists():
        return True
    try:
        return src.stat().st_mtime > dst.stat().st_mtime
    except OSError:
        return True


def make_thumb(src: Path, dst: Path, max_edge: int) -> tuple[bool, str]:
    """Write a JPEG thumbnail of `src` at `dst`. Returns (wrote, reason).

    Returns (False, 'up-to-date') when skipped, (True, ...) when written.
    On failure returns (False, 'error: ...') — we never crash the whole run.
    """
    if not needs_regen(src, dst):
        return False, "up-to-date"
    try:
        with Image.open(src) as im:
            im = im.convert("RGB")
            im.thumbnail((max_edge, max_edge), Image.Resampling.LANCZOS)
            dst.parent.mkdir(parents=True, exist_ok=True)
            # Save as JPEG but keep the .png extension — matches how the
            # browser currently requests these (and the dashboard.js task).
            im.save(dst, "JPEG", quality=80, optimize=True)
        return True, f"-> {max_edge}px"
    except Exception as e:
        return False, f"error: {e}"


def process_dir(src_name: str, dst_name: str, max_edge: int, force: bool) -> tuple[int, int, int]:
    """Process every .png in art/<src_name>/ -> art/<dst_name>/. Returns (wrote, skipped, errors)."""
    src_dir = ART / src_name
    dst_dir = ART / dst_name
    if not src_dir.is_dir():
        print(f"  ! {src_dir} not found, skipping")
        return 0, 0, 0

    wrote = skipped = errors = 0
    files = sorted(p for p in src_dir.iterdir() if p.is_file() and p.suffix.lower() == ".png")
    for src in files:
        dst = dst_dir / src.name  # same filename, kept .png extension
        if force:
            dst.unlink(missing_ok=True)
        ok, reason = make_thumb(src, dst, max_edge)
        if ok:
            wrote += 1
        elif reason.startswith("error"):
            errors += 1
            print(f"    ! {src.name}: {reason}")
        else:
            skipped += 1
    return wrote, skipped, errors


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Generate dashboard thumbnails for art/ PNGs.")
    p.add_argument("--force", action="store_true", help="regenerate every thumb regardless of mtime")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    print(f"Star Alliance — make_thumbs.py")
    print(f"  repo: {REPO}")
    print(f"  mode: {'force' if args.force else 'incremental'}")

    total_wrote = total_skipped = total_errors = 0
    for src_name, dst_name, max_edge in TARGETS:
        print(f"\n→ {src_name} -> {dst_name}  (max edge: {max_edge}px)")
        wrote, skipped, errors = process_dir(src_name, dst_name, max_edge, args.force)
        total_wrote += wrote
        total_skipped += skipped
        total_errors += errors
        print(f"  wrote: {wrote}   skipped (up-to-date): {skipped}   errors: {errors}")

    print()
    print("=" * 60)
    print(f"  totals — wrote: {total_wrote}  skipped: {total_skipped}  errors: {total_errors}")
    print("=" * 60)
    return 0 if total_errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
