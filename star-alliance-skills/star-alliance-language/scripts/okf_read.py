#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────────────────
# Star Alliance — OKF READ  (consumer side: the "star-alliance-language")
#
# The fast way for ANY member to take in a Quartermaster-tidied repo on a future
# run. Instead of blind full-reads, a member runs this once and gets a compact
# CONCEPT MAP: every governed knowledge file as a single line —
#       <path>  ·  [type]  title — description   {tags}  → linked,concepts
# grouped by directory, index.md surfaced first (progressive disclosure). The
# member reads the map, then opens ONLY the few concepts the task needs.
#
# This is the consumer half of the OKF pair: `okf` (producer) keeps the repo
# conformant; `star-alliance-language` (this) reads it efficiently. The okf-gate
# hook guarantees every file shown here actually carries the `type:` the map
# relies on.
#
# Usage:
#   okf_read.py                 whole-repo concept map (text)
#   okf_read.py --dir P         scope to a subtree
#   okf_read.py --type Skill    only concepts of a given type
#   okf_read.py --grep TERM     only concepts whose title/desc/tags match
#   okf_read.py --json          machine-readable map
#   okf_read.py --links FILE    show the cross-link neighbourhood of one concept
# ─────────────────────────────────────────────────────────────────────────────
import sys, os, re, json, argparse

EXCLUDE_DIR_PARTS = {
    ".git", ".claude", "worktrees", "node_modules", "__pycache__", ".venv", "venv",
    "scratchpad", "routine-logs", "routine-ledger",
}
EXCLUDE_PATH_SUBSTR = ("/impeccable/",)

FM_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?", re.S)
MD_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)")


def repo_root():
    d = os.path.dirname(os.path.abspath(__file__))
    for _ in range(5):
        if os.path.isfile(os.path.join(d, "workflows.json")):
            return d
        d = os.path.dirname(d)
    return os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def is_governed(path: str, root: str) -> bool:
    if not path.endswith(".md"):
        return False
    rel = os.path.relpath(path, root)
    if any(s in ("/" + rel.replace(os.sep, "/")) for s in EXCLUDE_PATH_SUBSTR):
        return False
    if any(p in EXCLUDE_DIR_PARTS for p in rel.replace(os.sep, "/").split("/")):
        return False
    return True


def iter_md(root: str, base: str):
    for dirpath, dirnames, filenames in os.walk(base):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIR_PARTS]
        for fn in filenames:
            full = os.path.join(dirpath, fn)
            if is_governed(full, root):
                yield full


def scalar(fm: str, key: str) -> str:
    m = re.search(rf"(?m)^{key}\s*:\s*(.+?)\s*$", fm)
    if not m:
        return ""
    v = m.group(1).strip().strip("\"'")
    return v


def parse_concept(path: str, root: str) -> dict:
    rel = os.path.relpath(path, root)
    try:
        text = open(path, encoding="utf-8").read()
    except Exception:
        return {"path": rel, "type": "?", "title": "", "description": "", "tags": [], "links": []}
    m = FM_RE.match(text)
    fm = m.group(1) if m else ""
    body = text[m.end():] if m else text
    tags_raw = scalar(fm, "tags")
    tags = []
    if tags_raw:
        tags = [t.strip().strip("[]\"'") for t in tags_raw.strip("[]").split(",") if t.strip()]
    links = set()
    for mlink in MD_LINK_RE.findall(body):
        if mlink.endswith(".md") and not mlink.startswith("http"):
            links.add(os.path.normpath(mlink.lstrip("/")))
    for wl in WIKILINK_RE.findall(body):
        links.add(wl.strip())
    return {
        "path": rel,
        "type": scalar(fm, "type") or "?",
        "title": scalar(fm, "title"),
        "description": scalar(fm, "description"),
        "tags": tags,
        "links": sorted(links),
    }


def main():
    ap = argparse.ArgumentParser(description="OKF concept-map reader (star-alliance-language)")
    ap.add_argument("--dir", help="scope to a subtree")
    ap.add_argument("--type", dest="ftype", help="filter by concept type")
    ap.add_argument("--grep", help="filter by term in title/description/tags/path")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--links", help="show the cross-link neighbourhood of one concept (path)")
    args = ap.parse_args()

    root = repo_root()
    base = (args.dir if os.path.isabs(args.dir) else os.path.join(root, args.dir)) if args.dir else root
    concepts = [parse_concept(p, root) for p in iter_md(root, base)]

    if args.ftype:
        concepts = [c for c in concepts if c["type"].lower() == args.ftype.lower()]
    if args.grep:
        t = args.grep.lower()
        concepts = [c for c in concepts if t in (c["title"] + c["description"] + " ".join(c["tags"]) + c["path"]).lower()]

    if args.links:
        target = os.path.normpath(args.links)
        by_path = {c["path"]: c for c in (parse_concept(p, root) for p in iter_md(root, root))}
        node = by_path.get(target)
        if not node:
            print(f"no concept at {target}")
            sys.exit(1)
        out = node["links"]
        inbound = [p for p, c in by_path.items() if any(target in l or os.path.basename(target).replace(".md", "") == l for l in c["links"])]
        if args.json:
            print(json.dumps({"concept": target, "outbound": out, "inbound": inbound}, indent=2))
        else:
            print(f"● {target}  [{node['type']}] {node['title']}")
            print(f"  → outbound: {', '.join(out) or '(none)'}")
            print(f"  ← inbound:  {', '.join(inbound) or '(none)'}")
        return

    if args.json:
        print(json.dumps({"root": os.path.relpath(base, root), "count": len(concepts), "concepts": concepts}, indent=2))
        return

    # text concept map — index.md first within each dir, grouped by directory
    groups = {}
    for c in concepts:
        d = os.path.dirname(c["path"]) or "."
        groups.setdefault(d, []).append(c)
    print(f"OKF concept map — {len(concepts)} concepts under {os.path.relpath(base, root)}")
    for d in sorted(groups):
        rows = sorted(groups[d], key=lambda c: (os.path.basename(c["path"]) != "index.md", c["path"]))
        print(f"\n{d}/")
        for c in rows:
            name = os.path.basename(c["path"])
            title = c["title"] or name.replace(".md", "")
            desc = f" — {c['description']}" if c["description"] else ""
            tags = f"  {{{', '.join(c['tags'])}}}" if c["tags"] else ""
            arrow = f"  → {len(c['links'])} link(s)" if c["links"] else ""
            print(f"  {name:<34} [{c['type']}] {title}{desc}{tags}{arrow}")


if __name__ == "__main__":
    main()
