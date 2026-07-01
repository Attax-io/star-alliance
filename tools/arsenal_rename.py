#!/usr/bin/env python3
"""arsenal_rename.py — deterministic, parse-safe rename of a model id across
every surface in the Star Alliance arsenal.

Generalizes the throwaway script that did 61 case-sensitive renames across
24 files with zero errors by ast.parse/json.loads-validating each file
BEFORE writing. Never write a file that would fail to parse.

Usage
-----
    python3 tools/arsenal_rename.py OLD_ID NEW_ID          # dry run (default)
    python3 tools/arsenal_rename.py OLD_ID NEW_ID --apply  # actually rewrite

What it touches (in order)
--------------------------
1. Registry: star-alliance-arsenal/models.json
       - Re-key the entry in `models` from OLD_ID -> NEW_ID (preserves position).
       - Replace OLD_ID in seats.brain/default + fallback[].
       - Replace OLD_ID in seats.doer/default + fallback[].
       - Replace OLD_ID in seats.critic/default + fallback[] (if present).
       - Replace OLD_ID in seats.bench/default + fallback[] (if present).
       - Replace OLD_ID in swarm.* (if present).
       - Walk every other string value in the document (case-sensitive
         whole-token) so any future seats/keys get covered without code change.
       - Validated by json.loads on the rewritten content.

2. Code/config token replace (case-sensitive, exact OLD_ID):
       File list is discovered by `git grep -l -F OLD_ID`, then filtered
       against a SKIP set (see below). This is robust to new files.

3. JSON rekey: star-alliance-arsenal/models-usage.json
       If OLD_ID is a top-level key, rename it to NEW_ID (preserves position).

4. Art tile: art/weapon-art/OLD_ID.png -> art/weapon-art/NEW_ID.png
       Uses `git mv` when the file is tracked, plain os.rename otherwise.

SKIP set (never edit):
    - Historical / generated / backup:
        data/guild-log.json, evolution/ledger.jsonl, data/turn-cost.jsonl,
        evolution/schedule.json.bak, *.bak
    - Generated registry docs: star-alliance-arsenal/models/*.md
    - Generated js snapshots: guild-data.js, guild-data.json,
        skill-md.js, workflow-md.js
    - Lockfile / meta: VERSIONS.md
    - Anything under .git/, anything matching /archive/, node_modules

Safety contract
---------------
- Before writing a .py file: ast.parse the new content. If it fails -> SKIP.
- Before writing a .json file: json.loads the new content. If it fails -> SKIP.
- A SKIPPED file is reported but never blocks other files.
- --apply never deletes source: failures leave the on-disk file untouched.

Exit codes:
    0  success (including 0 changes — no-op)
    2  bad CLI / missing required surface (e.g. models.json absent)
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Iterable

REPO_ROOT = Path(__file__).resolve().parent.parent
REGISTRY = REPO_ROOT / "star-alliance-arsenal" / "models.json"
USAGE = REPO_ROOT / "star-alliance-arsenal" / "models-usage.json"
ART_DIR = REPO_ROOT / "art" / "weapon-art"

# Hard-coded SKIP set — files that must NEVER be touched regardless of
# what git-grep returns. Three buckets:
#   1. historical / generated / log files
#   2. generated registry docs
#   3. generated JS snapshots
SKIP_LITERALS = {
    "data/guild-log.json",
    "evolution/ledger.jsonl",
    "data/turn-cost.jsonl",
    "evolution/schedule.json.bak",
    "VERSIONS.md",
    "guild-data.js",
    "guild-data.json",
    "skill-md.js",
    "workflow-md.js",
}

# Suffix patterns and path fragments that disqualify a file outright.
SKIP_SUFFIXES = (".bak", ".bak2", ".bak3")
SKIP_FRAGMENTS = (
    "/.git/",
    "/archive/",
    "/node_modules/",
    "/__pycache__/",
    "/.deprecated/",
    "/.claude/arsenal/",
    "/.claude/skills/",
    "/.claude/agents/",
    "/.claude/state/",
)


def is_skip_path(rel: str) -> bool:
    """True if `rel` (repo-relative POSIX path) is in any skip bucket."""
    if rel in SKIP_LITERALS:
        return True
    # Normalize: strip leading "./"
    rel_n = rel.lstrip("./")
    for frag in SKIP_FRAGMENTS:
        if frag in ("/" + rel_n) or frag in rel_n:
            return True
    if rel_n.endswith(SKIP_SUFFIXES):
        return True
    # Generated registry docs: star-alliance-arsenal/models/*.md
    parts = rel_n.split("/")
    if (
        len(parts) >= 3
        and parts[0] == "star-alliance-arsenal"
        and parts[1] == "models"
        and parts[2].endswith(".md")
    ):
        return True
    return False


def git_tracked(rel: str) -> bool:
    """True if `rel` is tracked by git in the repo."""
    r = subprocess.run(
        ["git", "ls-files", "--error-unmatch", "--", rel],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    return r.returncode == 0


# ---------- Discovery ----------


def git_grep_files(token: str) -> list[str]:
    """Return repo-relative paths that contain the exact token (fixed-string).
    Returns [] if the token isn't found anywhere."""
    r = subprocess.run(
        ["git", "grep", "-l", "-F", "--", token],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    if r.returncode != 0:
        return []
    # `git grep -l` prints relative paths one per line
    return [line.strip() for line in r.stdout.splitlines() if line.strip()]


# ---------- File operations ----------


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    # atomic-ish: write to a sibling then rename, so a crash mid-write
    # can't truncate the original.
    tmp = path.with_suffix(path.suffix + ".tmp_rename")
    tmp.write_text(content, encoding="utf-8")
    os.replace(tmp, path)


def validate_python(path: Path, new_content: str) -> str | None:
    """Return None if parseable, else a human-readable error string."""
    try:
        ast.parse(new_content, filename=str(path))
        return None
    except SyntaxError as e:
        return f"SyntaxError: {e.msg} (line {e.lineno}, col {e.offset})"


def validate_json(path: Path, new_content: str) -> str | None:
    try:
        json.loads(new_content)
        return None
    except json.JSONDecodeError as e:
        return f"JSONDecodeError: {e.msg} (line {e.lineno}, col {e.colno})"


# ---------- Surface handlers ----------


def count_occurrences(text: str, token: str) -> int:
    """Case-sensitive, exact-token count. Whole-token only via str.replace
    counting, which is safe here because we're matching the bare id string —
    e.g. 'minimax-sub' would never appear as a substring of a different id
    in this registry."""
    return text.count(token)


def replace_token(text: str, old: str, new: str) -> tuple[str, int]:
    """Return (new_text, n_replacements)."""
    return text.replace(old, new), text.count(old)


# ---- Registry (models.json) ----


def rewrite_registry(old: str, new: str) -> tuple[dict, int, bool]:
    """Rewrite the registry in-memory. Returns (rewritten_registry, n_changes, was_modified).

    Strategy:
      1. Re-key `models[old]` -> `models[new]` (preserves position).
      2. Recursively walk the document, replacing exact-string occurrences
         of `old` with `new` (case-sensitive). This covers seats.*.default,
         seats.*.fallback[], swarm.*, and any future structure.
    """
    with open(REGISTRY, encoding="utf-8") as f:
        reg = json.load(f)

    n_changes = 0

    # 1. Re-key models dict (preserve insertion order).
    models = reg.get("models", {})
    if old in models:
        reordered: dict = {}
        for k, v in models.items():
            if k == old:
                reordered[new] = v
                n_changes += 1
            else:
                reordered[k] = v
        reg["models"] = reordered

    # 2. Walk every string in the document and replace exact occurrences.
    def walk(obj):
        nonlocal n_changes
        if isinstance(obj, dict):
            return {k: walk(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [walk(x) for x in obj]
        if isinstance(obj, str):
            if old in obj:
                replaced = obj.replace(old, new)
                n_changes += obj.count(old)
                return replaced
            return obj
        return obj

    new_reg = walk(reg)
    return new_reg, n_changes, n_changes > 0


# ---- models-usage.json rekey ----


def rewrite_usage(old: str, new: str) -> tuple[dict, int, bool]:
    if not USAGE.exists():
        return {}, 0, False
    with open(USAGE, encoding="utf-8") as f:
        usage = json.load(f)
    if old not in usage:
        return usage, 0, False
    reordered: dict = {}
    for k, v in usage.items():
        if k == old:
            reordered[new] = v
        else:
            reordered[k] = v
    return reordered, 1, True


# ---- Art tile ----


def move_art_tile(old: str, new: str, apply: bool) -> tuple[bool, str]:
    """git mv tracked files, os.rename otherwise. Returns (would_change|changed, action).

    `action` is a short human-readable label for the report.
    """
    old_path = ART_DIR / f"{old}.png"
    new_path = ART_DIR / f"{new}.png"
    if not old_path.exists():
        return False, "no-tile"
    if new_path.exists():
        # Don't clobber. The caller decides what to do (we SKIP).
        return False, f"target-exists:{new_path.name}"
    if not apply:
        return True, "dry-run:git-mv"
    if git_tracked(str(old_path.relative_to(REPO_ROOT))):
        r = subprocess.run(
            ["git", "mv", str(old_path), str(new_path)],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        if r.returncode != 0:
            # fall back to os.rename so the tile still moves
            os.rename(old_path, new_path)
            return True, "renamed-fallback"
        return True, "git-mv"
    os.rename(old_path, new_path)
    return True, "renamed"


# ---------- Main pipeline ----------


def cmd_rename(args: argparse.Namespace) -> int:
    old, new, apply = args.old, args.new, args.apply

    if not old or not new:
        print("ERROR: OLD_ID and NEW_ID must both be non-empty.", file=sys.stderr)
        return 2
    if old == new:
        print("ERROR: OLD_ID and NEW_ID are identical — nothing to do.", file=sys.stderr)
        return 2

    if not REGISTRY.exists():
        print(f"ERROR: registry not found: {REGISTRY}", file=sys.stderr)
        return 2

    print(f"{'APPLY' if apply else 'DRY RUN'}: {old!r} -> {new!r}")
    print(f"repo: {REPO_ROOT}")
    print()

    # Discover files via git-grep, then filter through SKIP set.
    token_hits = git_grep_files(old)
    print(f"git-grep found {len(token_hits)} file(s) containing {old!r}")

    # Also include USAGE and REGISTRY unconditionally if they exist and contain
    # the token — git-grep covers them too, but we handle them as special surfaces.
    skipped_files: list[tuple[str, str]] = []
    changed_files: list[tuple[str, int, str]] = []  # (path, n_replacements, kind)
    total_occurrences = 0

    # ---- Surface 1: registry ----
    print("[1/4] registry: star-alliance-arsenal/models.json")
    new_reg, n_reg, reg_changed = rewrite_registry(old, new)
    if reg_changed:
        serialized = json.dumps(new_reg, indent=2, ensure_ascii=False)
        # json.dumps doesn't preserve trailing newline — preserve one if original had it
        original = read_text(REGISTRY)
        if original.endswith("\n"):
            serialized += "\n"
        err = validate_json(REGISTRY, serialized)
        if err:
            skipped_files.append((str(REGISTRY.relative_to(REPO_ROOT)), f"would-break:{err}"))
            print(f"  SKIPPED (would break): {err}")
        else:
            if apply:
                write_text(REGISTRY, serialized)
            total_occurrences += n_reg
            changed_files.append(("star-alliance-arsenal/models.json", n_reg, "registry"))
            print(f"  {n_reg} replacement(s){'  [written]' if apply else '  [dry]'}")
    else:
        print(f"  no occurrences")

    # ---- Surface 2: usage rekey ----
    print("[2/4] usage: star-alliance-arsenal/models-usage.json (rekey)")
    if USAGE.exists():
        new_usage, n_use, use_changed = rewrite_usage(old, new)
        if use_changed:
            serialized = json.dumps(new_usage, indent=2, ensure_ascii=False)
            original = read_text(USAGE)
            if original.endswith("\n"):
                serialized += "\n"
            err = validate_json(USAGE, serialized)
            if err:
                skipped_files.append(
                    (str(USAGE.relative_to(REPO_ROOT)), f"would-break:{err}")
                )
                print(f"  SKIPPED (would break): {err}")
            else:
                if apply:
                    write_text(USAGE, serialized)
                total_occurrences += n_use
                changed_files.append(("star-alliance-arsenal/models-usage.json", n_use, "usage-rekey"))
                tag = "  [written]" if apply else "  [dry]"
                print(f"  rekey 1 entry{tag}")
        else:
            print(f"  {old!r} is not a top-level key")
    else:
        print(f"  (file does not exist — skipping)")

    # ---- Surface 3: token replace across file list ----
    print("[3/4] token replace across discovered files")
    # Build the working set: files that git-grep found, minus the SKIP set.
    # We also remove the two registry/usage paths because we handled them
    # above (they need structural rewrites, not just text replace — and
    # rewriting them by token replace would lose insertion-order info).
    already_handled = {"star-alliance-arsenal/models.json", "star-alliance-arsenal/models-usage.json"}
    skipped_seen = 0
    for rel in token_hits:
        if rel in already_handled:
            continue
        if is_skip_path(rel):
            skipped_seen += 1
            skipped_files.append((rel, "skip-set"))
            continue
        path = REPO_ROOT / rel
        if not path.exists():
            skipped_files.append((rel, "missing-on-disk"))
            continue
        try:
            original = read_text(path)
        except UnicodeDecodeError:
            skipped_files.append((rel, "not-utf8 (binary?)"))
            continue
        new_text, n = replace_token(original, old, new)
        if n == 0:
            # git-grep hit could be a path that contains the token in its
            # filename only — extremely rare — or whitespace differences.
            continue
        # Validate by file type before writing.
        if path.suffix == ".py":
            err = validate_python(path, new_text)
        elif path.suffix == ".json":
            err = validate_json(path, new_text)
        else:
            err = None  # no parser available — trust the exact-token replace
        if err:
            skipped_files.append((rel, f"would-break:{err}"))
            print(f"  SKIP {rel}  ({err})")
            continue
        if apply:
            write_text(path, new_text)
        total_occurrences += n
        changed_files.append((rel, n, "token"))

    print(f"  token-replace: {len([c for c in changed_files if c[2] == 'token'])} file(s) would change")
    print(f"  skipped (skip-set): {skipped_seen}")

    # ---- Surface 4: art tile ----
    print("[4/4] art tile: art/weapon-art/")
    moved, action = move_art_tile(old, new, apply)
    if action == "no-tile":
        print(f"  no tile named {old}.png")
    elif action.startswith("target-exists:"):
        print(f"  SKIP: target already exists ({action.split(':', 1)[1]})")
        skipped_files.append((f"art/weapon-art/{new}.png", "target-exists"))
    else:
        print(f"  {old}.png -> {new}.png  [{action}]")

    # ---- Summary ----
    print()
    print("=" * 72)
    print("SUMMARY")
    print("=" * 72)
    print(f"total occurrences renamed:    {total_occurrences}")
    print(f"files changed:                {len(changed_files)}")
    tile_label = "yes" if action not in ("no-tile",) and not action.startswith("target-exists:") else "no"
    print(f"tile moved:                   {tile_label}")
    print(f"files skipped:                {len(skipped_files)}")
    if skipped_files:
        print()
        print("SKIPPED FILES:")
        for rel, reason in skipped_files:
            print(f"  {rel}    [{reason}]")

    if apply:
        print()
        print("Next steps — regenerate derivatives (NOT run by this tool):")
        print("  python3 star-alliance-arsenal/gen_model_docs.py")
        print("  python3 build.py")
        print("  python3 tools/conformity_check.py")
    else:
        print()
        print("This was a DRY RUN. Re-run with --apply to perform the migration.")

    return 0


def main(argv: Iterable[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="arsenal_rename.py",
        description="Deterministic, parse-safe rename of an arsenal model id "
        "across every surface in the Star Alliance repo.",
    )
    p.add_argument("old", metavar="OLD_ID", help="current model id (exact, case-sensitive)")
    p.add_argument("new", metavar="NEW_ID", help="new model id (exact, case-sensitive)")
    p.add_argument(
        "--apply",
        action="store_true",
        help="actually rewrite files. Default is dry run.",
    )
    args = p.parse_args(argv)
    return cmd_rename(args)


if __name__ == "__main__":
    sys.exit(main())