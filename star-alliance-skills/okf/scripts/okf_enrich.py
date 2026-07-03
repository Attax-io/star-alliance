#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────────────────
# Star Alliance — OKF ENRICH  (find the enrichment backlog, read-only)
#
# Baseline OKF requires only `type:` in frontmatter. Real value comes from
# adding `title`, `description`, and `tags`. okf_enrich.py reports every
# governed .md that PASSES the baseline (so it has a type:) but is MISSING
# any of those three enrichment keys — giving humans and Claude subagents a
# prioritized backlog per SKILL.md step 3 ("Enrich").
#
# Read-only on purpose: this script is advisory, never a gate. It must NEVER
# fail a build over missing metadata. Exit is always 0.
#
# Imports repo_root, EXCLUDE_DIR_PARTS, EXCLUDE_PATH_SUBSTR, is_governed,
# iter_md, split_frontmatter, and fm_has_type from okf_audit.py so governance
# scope stays in one place — drift-proof by construction.
# ─────────────────────────────────────────────────────────────────────────────
import sys
import os
import re
import json
import argparse
from typing import Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from okf_audit import (  # noqa: E402
    repo_root,
    iter_md,
    is_governed,
    split_frontmatter,
    fm_has_type,
    EXCLUDE_DIR_PARTS,  # re-exported for tests / downstream tooling parity
    EXCLUDE_PATH_SUBSTR,  # ditto
)

# Keys the enrichment backlog tracks. Extending the list (e.g. `resource:`)
# only requires adding a (key, regex) pair here + a help-line in --missing.
_ENRICH_KEYS = ("title", "description", "tags")
# Per-key presence regexes — match `key: …` at the start of a frontmatter line.
# Each runs against the raw frontmatter string; flags are anchored to line start
# so a description body mentioning "tags:" doesn't false-positive.
_KEY_RE = {k: re.compile(rf"(?m)^{re.escape(k)}\s*:") for k in _ENRICH_KEYS}


def has_key(fm: str, key: str) -> bool:
    return bool(_KEY_RE[key].search(fm))


def collect(root: str, subset: Tuple[str, ...]) -> Tuple[int, list]:
    """Walk every governed .md; return (scanned_total, backlog_entries).

    A governed file appears in the backlog only when:
      (a) its frontmatter parses,
      (b) the frontmatter carries the required `type:` field,
      (c) AT LEAST ONE of the keys in `subset` is absent.
    """
    files = list(iter_md(root))
    backlog: list[dict] = []
    for full in files:
        rel = os.path.relpath(full, root)
        try:
            text = open(full, encoding="utf-8").read()
        except OSError:
            continue
        fm, _ = split_frontmatter(text)
        if fm is None or not fm_has_type(fm):
            continue  # baseline audit's job, not ours
        missing = [k for k in subset if not has_key(fm, k)]
        if missing:
            backlog.append({"file": rel, "missing": missing})
    return len(files), backlog


def emit_text(scanned: int, backlog: list[dict]) -> None:
    print(f"OKF enrichment backlog — {len(backlog)} of {scanned} governed files missing metadata")
    for entry in backlog:
        missing_csv = ", ".join(entry["missing"])
        print(f"  {entry['file']} — missing: {missing_csv}")
    if not backlog:
        print("  ✓ no enrichment work pending")


def emit_json(scanned: int, backlog: list[dict]) -> None:
    payload = {
        "scanned": scanned,
        "backlog": len(backlog),
        "files": backlog,
    }
    print(json.dumps(payload, indent=2))


def parse_subset(raw) -> Tuple[str, ...]:
    if not raw:
        return _ENRICH_KEYS
    keys = tuple(k.strip() for k in raw.split(",") if k.strip())
    invalid = [k for k in keys if k not in _ENRICH_KEYS]
    if invalid:
        sys.stderr.write(
            f"[okf-enrich] unknown enrichment key(s): {', '.join(invalid)} "
            f"(valid: {', '.join(_ENRICH_KEYS)})\n"
        )
        sys.exit(1)
    return keys


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Report governed .md files that pass the OKF baseline (have type:) "
                    "but are missing title/description/tags. Read-only.",
    )
    ap.add_argument("--path", help="audit a single file or subtree")
    ap.add_argument("--json", action="store_true",
                    help="machine-readable output {scanned, backlog, files}")
    ap.add_argument("--missing",
                    help="comma-separated subset to check (default: title,description,tags)")
    args = ap.parse_args()

    root = repo_root()
    subset = parse_subset(args.missing)

    if args.path:
        target = args.path if os.path.isabs(args.path) else os.path.join(root, args.path)
        if os.path.isfile(target):
            # Single-file mode mirrors okf_audit.py's --path handling: governed
            # only, never a directory walk through the unified path.
            files = [target] if is_governed(target, root) else []
            backlog: list[dict] = []
            for full in files:
                rel = os.path.relpath(full, root)
                try:
                    text = open(full, encoding="utf-8").read()
                except OSError:
                    continue
                fm, _ = split_frontmatter(text)
                if fm is None or not fm_has_type(fm):
                    continue
                missing = [k for k in subset if not has_key(fm, k)]
                if missing:
                    backlog.append({"file": rel, "missing": missing})
            scanned = len(files)
        else:
            # Subtree mode reuses the shared walker (governance scope identical).
            files = list(iter_md(target))
            backlog = []
            for full in files:
                rel = os.path.relpath(full, root)
                try:
                    text = open(full, encoding="utf-8").read()
                except OSError:
                    continue
                fm, _ = split_frontmatter(text)
                if fm is None or not fm_has_type(fm):
                    continue
                missing = [k for k in subset if not has_key(fm, k)]
                if missing:
                    backlog.append({"file": rel, "missing": missing})
            scanned = len(files)
    else:
        scanned, backlog = collect(root, subset)

    if args.json:
        emit_json(scanned, backlog)
    else:
        emit_text(scanned, backlog)
    # Advisory by design — never fail a build over missing enrichment.
    sys.exit(0)


if __name__ == "__main__":
    main()
