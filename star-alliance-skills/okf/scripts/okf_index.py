#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────────────────
# Star Alliance — OKF INDEX  (folder-index audit / fixer)
#
# The third OKF audit dimension: every governed FOLDER in the repo should carry
# a conformant `index.md` that (a) declares `type: Index` in its frontmatter
# and (b) carries a regenerable `## Contents` block delimited by HTML comment
# markers, listing that folder's direct children (subdirs first, then files,
# case-insensitive sort, dotfiles and __pycache__ excluded).
#
# Sits alongside okf_audit.py (per-file frontmatter conformance +
# `--layout` root-file placement) and okf_enrich.py (enrichment backlog). They
# are complementary dimensions, not duplicates: this script walks FOLDERS,
# the other two walk FILES.
#
# Modes:
#   (default) report — list every folder missing an index.md or carrying a
#                      stale one (no `type: Index`, no Contents markers,
#                      or Contents markers in the wrong order). Exit 0 when
#                      every governed folder is conformant; exit 1 otherwise.
#   --fix            — generate fresh index.md for missing folders, MERGE
#                      stale ones: never touch hand-written prose, only
#                      ensure frontmatter `type: Index` is present and the
#                      delimited Contents block is fresh. Idempotent — a
#                      second `--fix` is a no-op.
#   --json           — machine-readable report.
#   --path P         — scope the walk to a single subtree.
#
# Exit: 0 when every governed folder has a conformant index.md (or after a
# successful --fix); 1 on any violation found in report mode.
# ─────────────────────────────────────────────────────────────────────────────
import sys
import os
import re
import json
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from okf_audit import (  # noqa: E402
    repo_root,
    EXCLUDE_DIR_PARTS,
    EXCLUDE_PATH_SUBSTR,
    now_iso,
    split_frontmatter,
    fm_has_type,
)

# ── Markers + sort order for the regenerable Contents block ─────────────────
CONTENTS_START = "<!-- okf:generated-contents:start -->"
CONTENTS_END = "<!-- okf:generated-contents:end -->"
HEADING_CONTENTS = "## Contents"
FALLBACK_FLAG = "_Needs human review — could not infer a richer description from context._"
NEEDS_REVIEW_BODY = "_Needs human review — could not infer a description from context._"


def governed_dirs(root: str, scope: str = None):
    """Walk every folder under `root` (or `scope`) that is NOT excluded.

    Mirrors okf_audit.iter_md's pruning discipline: `dirnames[:] = [...]` to
    skip EXCLUDE_DIR_PARTS directory names in-place so os.walk never descends
    into them, plus a per-directory path-substring check against
    EXCLUDE_PATH_SUBSTR. Skips genuinely empty directories (no children at
    all after exclusion pruning) — those are noise, not violations."""
    base = root if scope is None else (
        scope if os.path.isabs(scope) else os.path.join(root, scope)
    )
    base = os.path.abspath(base)
    if os.path.isfile(base):
        # a single file was scoped — its containing folder is the only folder
        parent = os.path.dirname(base)
        norm = parent.replace(os.sep, "/")
        if not any(sub in ("/" + norm) for sub in EXCLUDE_PATH_SUBSTR) \
                and not any(p in EXCLUDE_DIR_PARTS
                            for p in norm.replace(parent.replace(os.sep, "/"), "", 1).strip("/").split("/")):
            if parent.startswith(root):
                yield parent
        return
    for dirpath, dirnames, filenames in os.walk(base):
        # In-place prune: never descend into EXCLUDE_DIR_PARTS directory names.
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIR_PARTS]
        # Skip the whole directory if its path carries an excluded substring.
        norm = dirpath.replace(os.sep, "/")
        if any(sub in ("/" + norm) for sub in EXCLUDE_PATH_SUBSTR):
            continue
        # Skip genuinely empty folders (nothing left after pruning).
        if not dirnames and not filenames:
            continue
        # Only yield folders that fall under the repo root.
        if dirpath.startswith(root):
            yield dirpath


def _title_from_name(name: str) -> str:
    """Derive a human title from a folder basename: hyphens/underscores -> spaces,
    each word title-cased. Mirrors okf_new.heading_from's stem logic."""
    parts = re.split(r"[-_]+", name.strip())
    parts = [p[:1].upper() + p[1:] if p else p for p in parts if p]
    return " ".join(parts) if parts else name


def _truncate(s: str, n: int = 200) -> str:
    s = s.strip()
    if len(s) <= n:
        return s
    return s[: n - 1].rstrip() + "…"


def _first_prose_line(text: str) -> str:
    """First non-empty, non-heading, non-frontmatter line of prose from a
    markdown file. Used to lift a description from a README.md."""
    _, body = split_frontmatter(text)
    for ln in body.splitlines():
        s = ln.strip()
        if not s:
            continue
        if s.startswith("#"):
            continue
        if s.startswith("<!--") or s.startswith("-->"):
            continue
        # strip leading list markers / blockquote for the prose check
        s = re.sub(r"^[-*+]\s+", "", s)
        s = re.sub(r"^>\s*", "", s)
        if s:
            return s
    return ""


def infer_description(folder: str) -> tuple:
    """Best-effort description inference for a folder. Returns (description, ok)
    where ok=True means a real description was lifted; ok=False means we fell
    back to the generic templated form + the human-review flag."""
    readme = os.path.join(folder, "README.md")
    if os.path.isfile(readme):
        try:
            text = open(readme, encoding="utf-8").read()
            prose = _first_prose_line(text)
            if prose:
                return _truncate(prose, 200), True
        except Exception:
            pass
    skill = os.path.join(folder, "SKILL.md")
    if os.path.isfile(skill):
        try:
            text = open(skill, encoding="utf-8").read()
            fm, _ = split_frontmatter(text)
            if fm:
                m = re.search(r"(?m)^description\s*:\s*(.+?)\s*$", fm)
                if m:
                    return _truncate(m.group(1).strip(), 200), True
        except Exception:
            pass
    # Fallback — generic templated form, with a clearly flagged review line.
    name = os.path.basename(folder.rstrip(os.sep)) or "."
    parent = os.path.dirname(folder.rstrip(os.sep))
    parent_path = os.path.relpath(parent, repo_root()) if parent else ""
    # Count live children after exclusion pruning.
    live = []
    try:
        for entry in os.listdir(folder):
            if entry.startswith(".") or entry == "__pycache__":
                continue
            live.append(entry)
    except Exception:
        pass
    n_files = sum(1 for e in live
                  if os.path.isfile(os.path.join(folder, e)))
    n_dirs = sum(1 for e in live
                 if os.path.isdir(os.path.join(folder, e)))
    fallback = (f"Holds {n_files} files and {n_dirs} subfolders under "
                f"{parent_path or '.'}.")
    return fallback, False


def _children_for_contents(folder: str) -> list:
    """Build the Contents bullet list for a folder's DIRECT children.
    Subdirectories first, then files; case-insensitive sort; skip dotfiles and
    __pycache__. Returns a list of bullet-line strings (no trailing newline)."""
    entries = []
    try:
        for entry in os.listdir(folder):
            full = os.path.join(folder, entry)
            if entry.startswith(".") or entry == "__pycache__":
                continue
            if os.path.isdir(full):
                entries.append((0, entry.lower(), f"- `{entry}/` — folder"))
            elif os.path.isfile(full):
                entries.append((1, entry.lower(), f"- `{entry}` — file"))
    except Exception:
        pass
    entries.sort(key=lambda t: (t[0], t[1]))
    return [t[2] for t in entries]


def generate_index_body(folder: str) -> str:
    """Produce the full index.md text for a folder that has none yet.
    Frontmatter (type: Index) + level-1 heading + description prose +
    delimited Contents block listing direct children."""
    name = os.path.basename(folder.rstrip(os.sep)) or "."
    title = _title_from_name(name)
    desc, ok = infer_description(folder)
    bullets = _children_for_contents(folder)
    bullets_block = "\n".join(bullets) if bullets else "_empty folder_"
    body_prose = desc if ok else desc + "\n\n" + NEEDS_REVIEW_BODY
    fm = (f"---\n"
          f"type: Index\n"
          f"title: {title}\n"
          f"description: {desc}\n"
          f"timestamp: {now_iso()}\n"
          f"---\n")
    return (
        f"{fm}\n"
        f"# {title}\n\n"
        f"{body_prose}\n\n"
        f"{HEADING_CONTENTS}\n\n"
        f"{CONTENTS_START}\n"
        f"{bullets_block}\n"
        f"{CONTENTS_END}\n"
    )


def is_contents_conformant(text: str) -> bool:
    """True iff the file declares `type: Index` in frontmatter AND carries the
    `## Contents` heading immediately followed by the start/end markers in
    order. Matches okf_audit's tolerance: fm_has_type-style whitespace."""
    fm, body = split_frontmatter(text)
    if fm is None or not fm_has_type(fm):
        return False
    # Must declare `type: Index` (not just any type).
    if not re.search(r"(?m)^type\s*:\s*Index\s*$", fm):
        return False
    # Markers in order, with ## Contents immediately before the start marker.
    s_idx = body.find(CONTENTS_START)
    e_idx = body.find(CONTENTS_END)
    if s_idx < 0 or e_idx < 0 or e_idx <= s_idx:
        return False
    pre = body[:s_idx].rstrip()
    if not pre.endswith(HEADING_CONTENTS):
        return False
    return True


def _ensure_index_frontmatter(fm: str | None, folder: str) -> str:
    """Return a frontmatter string with `type: Index`. If fm is None, synthesize
    a fresh block (type + title + description + timestamp). If fm is present,
    rewrite JUST the type line — leave every other key (title, description,
    timestamps, etc.) untouched, preserving the existing key order."""
    if fm is None:
        name = os.path.basename(folder.rstrip(os.sep)) or "."
        title = _title_from_name(name)
        desc, _ = infer_description(folder)
        return (
            f"type: Index\n"
            f"title: {title}\n"
            f"description: {desc}\n"
            f"timestamp: {now_iso()}\n"
        )
    if re.search(r"(?m)^type\s*:\s*Index\s*$", fm):
        return fm
    # Rewrite ONLY the existing type line; preserve everything else verbatim.
    return re.sub(r"(?m)^type\s*:.*$", "type: Index", fm, count=1)


def merge_index(folder: str) -> str:
    """Merge path: preserve 100% of hand-written prose, ensure frontmatter
    `type: Index`, and ensure the delimited Contents block is fresh. Returns
    the new file text. Idempotent — calling twice yields the same text."""
    path = os.path.join(folder, "index.md")
    text = open(path, encoding="utf-8").read()
    fm, body = split_frontmatter(text)
    fm_new = _ensure_index_frontmatter(fm, folder)

    bullets = _children_for_contents(folder)
    bullets_block = "\n".join(bullets) if bullets else "_empty folder_"

    s_idx = body.find(CONTENTS_START)
    e_idx = body.find(CONTENTS_END)
    if s_idx >= 0 and e_idx > s_idx:
        # Markers exist — regen ONLY the slice strictly between them.
        body_new = body[: s_idx + len(CONTENTS_START)] + "\n" + bullets_block + "\n" + body[e_idx:]
    else:
        # Append a fresh Contents block at the very end. Never touch prose
        # above the append point.
        sep = "" if body.endswith("\n") else "\n"
        body_new = (
            body
            + sep
            + "\n"
            + HEADING_CONTENTS
            + "\n\n"
            + CONTENTS_START
            + "\n"
            + bullets_block
            + "\n"
            + CONTENTS_END
            + "\n"
        )

    new_text = f"---\n{fm_new.rstrip(chr(10))}\n---\n{body_new.lstrip(chr(10))}"
    if new_text != text:
        with open(path, "w", encoding="utf-8") as f:
            f.write(new_text)
    return new_text


def classify_folder(folder: str, root: str) -> str:
    """Return one of: 'ok', 'missing', 'stale'. Used both for the audit and
    the post-fix recheck."""
    index = os.path.join(folder, "index.md")
    if not os.path.isfile(index):
        return "missing"
    try:
        text = open(index, encoding="utf-8").read()
    except Exception:
        return "stale"
    return "ok" if is_contents_conformant(text) else "stale"


def main():
    ap = argparse.ArgumentParser(description="OKF folder-index audit / fixer")
    ap.add_argument("--fix", action="store_true",
                    help="generate missing index.md and merge stale ones (idempotent)")
    ap.add_argument("--json", action="store_true",
                    help="machine-readable output")
    ap.add_argument("--path", help="scope the walk to a single subtree")
    args = ap.parse_args()

    root = repo_root()
    folders = list(governed_dirs(root, args.path))
    rel = lambda p: os.path.relpath(p, root)  # noqa: E731

    verdicts = {rel(f): classify_folder(f, root) for f in folders}
    missing = sorted(k for k, v in verdicts.items() if v == "missing")
    stale = sorted(k for k, v in verdicts.items() if v == "stale")
    created: list = []
    merged: list = []

    if args.fix:
        for f in folders:
            r = rel(f)
            if verdicts[r] == "missing":
                with open(os.path.join(f, "index.md"), "w", encoding="utf-8") as fh:
                    fh.write(generate_index_body(f))
                created.append(r)
            elif verdicts[r] == "stale":
                merge_index(f)
                merged.append(r)
        # re-check
        verdicts = {rel(f): classify_folder(f, root) for f in folders}
        missing = sorted(k for k, v in verdicts.items() if v == "missing")
        stale = sorted(k for k, v in verdicts.items() if v == "stale")

    conformant = sum(1 for v in verdicts.values() if v == "ok")

    if args.json:
        print(json.dumps({
            "scanned": len(folders),
            "conformant": conformant,
            "missing": missing,
            "stale": stale,
            "created": created,
            "merged": merged,
        }, indent=2))
    else:
        print(f"OKF folder-index audit — scanned {len(folders)} governed folders")
        if created:
            print(f"  ✓ created {len(created)} new index.md:")
            for r in created[:50]:
                print(f"      {r}/index.md")
            if len(created) > 50:
                print(f"      … +{len(created) - 50} more")
        if merged:
            print(f"  ✓ merged {len(merged)} stale index.md (Contents refreshed):")
            for r in merged[:50]:
                print(f"      {r}/index.md")
            if len(merged) > 50:
                print(f"      … +{len(merged) - 50} more")
        if missing:
            print(f"  ✗ {len(missing)} folder(s) missing index.md:")
            for r in missing[:50]:
                print(f"      {r}")
            if len(missing) > 50:
                print(f"      … +{len(missing) - 50} more")
        if stale:
            print(f"  ⚠ {len(stale)} folder(s) with stale index.md (need Contents refresh):")
            for r in stale[:50]:
                print(f"      {r}")
            if len(stale) > 50:
                print(f"      … +{len(stale) - 50} more")
        if not missing and not stale:
            print("  ✓ every folder has a conformant index.md")

    sys.exit(0 if (not missing and not stale) else 1)


if __name__ == "__main__":
    main()