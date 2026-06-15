#!/usr/bin/env python3
"""skillsmith — move a top-level `version:` frontmatter key into `metadata.version`.

The Anthropic Agent Skills spec (enforced by skill-creator's quick_validate.py) only allows
these top-level frontmatter keys: name, description, license, allowed-tools, metadata, compatibility.
A top-level `version:` is rejected as an unexpected key — so the spec-clean place for the version is
`metadata.version` (which also matches what vendored skills already do and what the lenient Claude
Code loader accepts). This script relocates it, preserving the value.

Idempotent: skips a skill that has no top-level `version:`. If `metadata.version` already exists,
the top-level key is just removed (the metadata value wins — reconcile by hand if they differ).

Usage:
  python3 migrate_version.py <skill-dir> [<skill-dir> ...]   # migrate specific skills
  python3 migrate_version.py --all [--repo PATH]             # every skill in the repo
  python3 migrate_version.py --all --exclude impeccable      # skip externals you don't hand-edit
  add --dry to print what would change without writing.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path


def default_repo() -> Path:
    """Resolve the claude-skills repo regardless of cwd / install location."""
    env = os.environ.get("CLAUDE_SKILLS_REPO")
    if env:
        return Path(env).expanduser()
    here = Path(__file__).resolve()
    for anc in here.parents:
        if (anc / "VERSIONS.md").exists() and (anc / ".git").exists():
            return anc
    known = Path.home() / "Documents" / "Claude" / "Projects" / "claude-skills"
    if (known / "VERSIONS.md").exists():
        return known
    return here.parents[2]


def split_fm(text: str):
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---", 4)
    if end == -1:
        return None
    fm = text[4:end]
    rest = text[end + 4:]
    return fm, rest


def migrate(skill_md: Path, dry: bool) -> str:
    text = skill_md.read_text()
    parts = split_fm(text)
    if not parts:
        return "no-frontmatter"
    fm, rest = parts
    lines = fm.splitlines()

    # find a TOP-LEVEL version line (col 0, not indented under metadata)
    top_idx = next((i for i, l in enumerate(lines) if re.match(r"^version:\s*\S", l)), None)
    if top_idx is None:
        return "skip (no top-level version)"
    value = re.sub(r"^version:\s*", "", lines[top_idx]).strip()
    del lines[top_idx]

    # does a metadata: block exist?
    meta_idx = next((i for i, l in enumerate(lines) if re.match(r"^metadata:\s*$", l)), None)
    if meta_idx is not None:
        # is there already an indented version under metadata?
        has_meta_ver = False
        j = meta_idx + 1
        while j < len(lines) and (re.match(r"^\s+\S", lines[j]) or lines[j].strip() == ""):
            if re.match(r"^\s+version:\s*\S", lines[j]):
                has_meta_ver = True
                break
            j += 1
        if not has_meta_ver:
            lines.insert(meta_idx + 1, f"  version: {value}")
        action = "moved into existing metadata" if not has_meta_ver else "removed redundant top-level (metadata.version kept)"
    else:
        # append a metadata block at the end of the frontmatter
        if lines and lines[-1].strip() != "":
            pass
        lines.append("metadata:")
        lines.append(f"  version: {value}")
        action = "created metadata block"

    new = "---\n" + "\n".join(lines) + "\n---" + rest
    if dry:
        return f"DRY {action} (version={value})"
    skill_md.write_text(new)
    return f"{action} (version={value})"


def main():
    ap = argparse.ArgumentParser(description="move top-level version: -> metadata.version")
    ap.add_argument("skills", nargs="*", help="skill dir names (under --repo) or paths")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--repo", type=Path, default=default_repo())
    ap.add_argument("--exclude", nargs="*", default=[])
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()
    repo = a.repo.expanduser().resolve()

    targets = []
    if a.all:
        for d in sorted(repo.iterdir()):
            if d.is_dir() and not d.name.startswith(".") and (d / "SKILL.md").exists() and d.name not in a.exclude:
                targets.append(d / "SKILL.md")
    for s in a.skills:
        p = Path(s)
        md = p / "SKILL.md" if (p.is_dir()) else (repo / s / "SKILL.md")
        if md.exists():
            targets.append(md)
        else:
            print(f"not found: {s}", file=sys.stderr)

    for md in targets:
        print(f"{md.parent.name:34} {migrate(md, a.dry)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
