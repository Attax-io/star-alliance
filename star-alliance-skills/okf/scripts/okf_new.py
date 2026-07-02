#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────────────────
# Star Alliance — OKF NEW  (scaffold a new OKF-conformant concept file)
#
# Nobody should hand-type OKF frontmatter. okf_new.py scaffolds a fresh
# markdown file with the right frontmatter block, an ISO-8601 UTC timestamp,
# and a level-1 heading — so the only thing left for the human is to write the
# body. Mirrors okf_audit.py's frontmatter shape; reuses its repo_root() and
# scope constants so the two scripts can never drift on what counts as
# governed.
#
# Exit: 0 on success, 1 on any refusal (bad PATH, missing extension, exists
# without --force, etc.).
# ─────────────────────────────────────────────────────────────────────────────
import sys
import os
import re
import argparse
import datetime
from typing import Optional, Tuple

# Import the shared scope/utility layer from the sibling audit script so
# governed-file semantics, repo-root detection, and timestamp formatting stay
# in lockstep with the rest of the toolchain.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from okf_audit import repo_root, EXCLUDE_DIR_PARTS  # noqa: E402

# Force a trailing newline on emitted YAML to keep diffs clean.
_EMIT_LINESEP = "\n"


def now_iso() -> str:
    """Match okf_audit.now_iso() — UTC, second precision, trailing Z."""
    return (
        datetime.datetime.now(datetime.timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def heading_from(path: str, title: Optional[str]) -> str:
    """Level-1 heading text. Use --title when given, else derive from the
    filename stem with hyphens-turned-spaces and each segment title-cased."""
    if title:
        return title
    stem = os.path.splitext(os.path.basename(path))[0]
    # Title-case each hyphen/underscore-separated segment, preserve digits.
    parts = re.split(r"[-_]+", stem.strip())
    parts = [p[:1].upper() + p[1:] if p else p for p in parts if p]
    return " ".join(parts) if parts else stem


def format_tags(tags_csv: Optional[str]) -> Optional[str]:
    """Turn "a,b, c" into "[a, b, c]" (YAML flow list). Empty/None → None."""
    if not tags_csv:
        return None
    items = [t.strip() for t in tags_csv.split(",") if t.strip()]
    if not items:
        return None
    return "[" + ", ".join(items) + "]"


def build_frontmatter(args, ts: str) -> str:
    """Compose the YAML block. Keys are emitted in the canonical order
    (type → title → description → tags → timestamp) so diffs line up."""
    lines: list[str] = [f"type: {args.type}"]
    if args.title:
        # Single-line YAML — strip any embedded newlines so the block stays
        # valid no matter what the caller hands us.
        lines.append(f"title: {args.title.replace(chr(10), ' ').strip()}")
    if args.description:
        lines.append(
            f"description: {args.description.replace(chr(10), ' ').strip()}"
        )
    tags = format_tags(args.tags)
    if tags:
        lines.append(f"tags: {tags}")
    lines.append(f"timestamp: {ts}")
    return "---\n" + "\n".join(lines) + "\n---\n"


def refused(msg: str) -> "NoReturn":  # type: ignore[name-defined]
    sys.stderr.write(f"[okf-new] {msg}\n")
    sys.exit(1)


def validate_target(rel_path: str, force: bool) -> Tuple[str, bool, Optional[str]]:
    """Resolve the PATH. Returns (abs_path, exists, error_or_None).

    Refuses anything that isn't a `.md` file. Refuses an existing file unless
    --force is set. Refuses a path that would land inside an excluded directory
    (so the scaffold can't sneak past the gate's scope)."""
    if not rel_path.endswith(".md"):
        return "", False, "PATH must end in .md"

    root = repo_root()
    abs_path = (
        rel_path
        if os.path.isabs(rel_path)
        else os.path.join(root, rel_path)
    )
    # Resolve symlinks + `..` so the scope check below sees the real location.
    abs_path = os.path.realpath(abs_path)

    exists = os.path.isfile(abs_path)
    if exists and not force:
        return abs_path, True, "file already exists (pass --force to overwrite)"

    # Scope check: refuse to scaffold into a vendored/excluded directory.
    rel_for_scope = os.path.relpath(abs_path, root)
    parts = rel_for_scope.replace(os.sep, "/").split("/")
    if any(p in EXCLUDE_DIR_PARTS for p in parts):
        return abs_path, exists, (
            f"refusing to scaffold into excluded scope "
            f"({', '.join(sorted(p for p in parts if p in EXCLUDE_DIR_PARTS))})"
        )

    return abs_path, exists, None


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Scaffold a new OKF-conformant concept file with frontmatter + heading."
    )
    ap.add_argument("path", help="target file PATH (relative to repo root or absolute)")
    ap.add_argument("--type", required=True,
                    help="required frontmatter type (Document, Skill, Member, Index, Log, "
                         "Readme, … — freeform string)")
    ap.add_argument("--title", help="optional frontmatter title; defaults to a heading "
                                    "derived from the filename")
    ap.add_argument("--description", help="optional frontmatter description")
    ap.add_argument("--tags", help="optional comma-separated tags, emitted as YAML flow list")
    ap.add_argument("--force", action="store_true",
                    help="overwrite if the file already exists")
    args = ap.parse_args()

    abs_path, exists, err = validate_target(args.path, args.force)
    if err:
        refused(err)

    root = repo_root()
    ts = now_iso()
    fm_block = build_frontmatter(args, ts)
    heading = heading_from(args.path, args.title)

    body = f"{fm_block}\n# {heading}\n"
    os.makedirs(os.path.dirname(abs_path) or ".", exist_ok=True)
    with open(abs_path, "w", encoding="utf-8") as f:
        f.write(body)

    rel = os.path.relpath(abs_path, root)
    print(f"created {rel}  (type: {args.type})")
    sys.exit(0)


if __name__ == "__main__":
    main()
