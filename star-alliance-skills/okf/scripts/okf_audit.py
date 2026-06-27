#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────────────────
# Star Alliance — OKF AUDIT  (producer side of the Open Knowledge Format)
#
# Keeps the whole repo tidy & conformant to the Open Knowledge Format (OKF v0.1,
# Google Cloud Data Cloud). OKF in one line: knowledge = a directory of markdown
# files, one concept per file, each carrying YAML frontmatter whose ONLY required
# field is `type:`; optional `title`, `description`, `resource`, `tags`,
# `timestamp`; the body is plain markdown; concepts cross-link with normal
# markdown links; the file path IS the concept's identity.
#
# Modes:
#   (default) audit  — report every governed .md that is NOT OKF-conformant.
#   --fix            — bring non-conformant files to baseline: inject a `type:`
#                      (derived from path) and a `timestamp:`, creating a
#                      frontmatter block when none exists. Idempotent.
#   --json           — machine-readable report (used by the okf-gate hook & CI).
#   --staged         — only consider files staged in git (fast pre-commit pass).
#   --path P         — audit a single file or subtree.
#
# This is the MIGRATE-FIRST tool: run `--fix` once before arming the okf-gate
# hook so the gate can't lock the guild out of its own docs.
#
# Exit: 0 if all governed files conform (or after a successful --fix), else 1.
# ─────────────────────────────────────────────────────────────────────────────
import sys, os, re, json, argparse, subprocess, datetime

# ── Governance scope ─────────────────────────────────────────────────────────
# Directories never governed (vendored, generated, machine, VCS internals).
EXCLUDE_DIR_PARTS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv",
    "scratchpad", "routine-logs", "routine-ledger",
}
# Any path containing one of these substrings is skipped wholesale.
EXCLUDE_PATH_SUBSTR = (
    "/impeccable/",   # vendored external skill (carries its own multi-agent mirrors)
)


def repo_root():
    here = os.path.dirname(os.path.abspath(__file__))
    # scripts/ -> okf/ -> star-alliance-skills/ -> repo
    d = here
    for _ in range(5):
        if os.path.isfile(os.path.join(d, "workflows.json")):
            return d
        d = os.path.dirname(d)
    return os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def is_governed(path: str, root: str) -> bool:
    """A markdown file the OKF standard governs."""
    if not path.endswith(".md"):
        return False
    rel = os.path.relpath(path, root)
    if any(sub in ("/" + rel.replace(os.sep, "/")) for sub in EXCLUDE_PATH_SUBSTR):
        return False
    parts = rel.replace(os.sep, "/").split("/")
    if any(p in EXCLUDE_DIR_PARTS for p in parts):
        return False
    return True


def iter_md(root: str):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIR_PARTS]
        for fn in filenames:
            full = os.path.join(dirpath, fn)
            if is_governed(full, root):
                yield full


def staged_md(root: str):
    out = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
        cwd=root, capture_output=True, text=True,
    ).stdout
    for line in out.splitlines():
        full = os.path.join(root, line.strip())
        if line.strip() and is_governed(full, root) and os.path.isfile(full):
            yield full


# ── Frontmatter parsing ──────────────────────────────────────────────────────
FM_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?", re.S)


def split_frontmatter(text: str):
    """Return (frontmatter_str_or_None, body)."""
    m = FM_RE.match(text)
    if not m:
        return None, text
    return m.group(1), text[m.end():]


def fm_has_type(fm: str) -> bool:
    return bool(re.search(r"(?m)^type\s*:", fm))


# ── type derivation from path ────────────────────────────────────────────────
def derive_type(rel: str) -> str:
    name = os.path.basename(rel)
    low = name.lower()
    if name == "SKILL.md":
        return "Skill"
    if rel.replace(os.sep, "/").startswith("star-alliance-members/") and low != "readme.md":
        return "Member"
    if low == "index.md":
        return "Index"
    if low == "log.md":
        return "Log"
    if low == "readme.md":
        return "Readme"
    if low.endswith("index.md"):
        return "Index"
    return "Document"


def now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def conform(text: str, rel: str) -> str:
    """Return OKF-conformant text (idempotent). Adds `type:` (+timestamp when
    creating a fresh block). Preserves any existing frontmatter & body."""
    fm, body = split_frontmatter(text)
    typ = derive_type(rel)
    if fm is None:
        new_fm = f"type: {typ}\ntimestamp: {now_iso()}\n"
        return f"---\n{new_fm}---\n\n{text.lstrip(chr(10))}"
    if fm_has_type(fm):
        return text  # already conformant
    fm2 = fm.rstrip("\n") + f"\ntype: {typ}\n"
    return f"---\n{fm2}\n---\n{body}"


def check_file(path: str, root: str):
    rel = os.path.relpath(path, root)
    try:
        text = open(path, encoding="utf-8").read()
    except Exception as e:
        return {"file": rel, "ok": False, "reason": f"unreadable: {e}"}
    fm, _ = split_frontmatter(text)
    if fm is None:
        return {"file": rel, "ok": False, "reason": "no YAML frontmatter"}
    if not fm_has_type(fm):
        return {"file": rel, "ok": False, "reason": "frontmatter missing required `type:` field"}
    return {"file": rel, "ok": True}


def main():
    ap = argparse.ArgumentParser(description="OKF conformance audit / fixer")
    ap.add_argument("--fix", action="store_true", help="rewrite non-conformant files to baseline OKF")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--staged", action="store_true", help="only git-staged files")
    ap.add_argument("--path", help="audit a single file or subtree")
    args = ap.parse_args()

    root = repo_root()
    if args.path:
        target = args.path if os.path.isabs(args.path) else os.path.join(root, args.path)
        if os.path.isfile(target):
            files = [target] if is_governed(target, root) else []
        else:
            files = [f for f in iter_md(target)]
    elif args.staged:
        files = list(staged_md(root))
    else:
        files = list(iter_md(root))

    results = [check_file(f, root) for f in files]
    bad = [r for r in results if not r["ok"]]

    fixed = []
    if args.fix and bad:
        for r in bad:
            full = os.path.join(root, r["file"])
            try:
                text = open(full, encoding="utf-8").read()
                new = conform(text, r["file"])
                if new != text:
                    open(full, "w", encoding="utf-8").write(new)
                    fixed.append(r["file"])
            except Exception as e:
                sys.stderr.write(f"[okf] fix failed {r['file']}: {e}\n")
        # re-check
        results = [check_file(os.path.join(root, r["file"]), root) for r in results]
        bad = [r for r in results if not r["ok"]]

    if args.json:
        print(json.dumps({
            "scanned": len(files), "conformant": len(files) - len(bad),
            "nonconformant": len(bad), "fixed": fixed,
            "violations": bad,
        }, indent=2))
    else:
        print(f"OKF audit — scanned {len(files)} governed .md")
        if fixed:
            print(f"  fixed {len(fixed)} file(s) → baseline OKF")
        if bad:
            print(f"  ✗ {len(bad)} non-conformant:")
            for r in bad[:50]:
                print(f"      {r['file']} — {r['reason']}")
            if len(bad) > 50:
                print(f"      … +{len(bad)-50} more")
        else:
            print("  ✓ all governed files conform to OKF v0.1")

    sys.exit(0 if not bad else 1)


if __name__ == "__main__":
    main()
