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
#
# This set is now consumed by THREE sibling scripts (okf_audit.py's iter_md,
# okf_enrich.py's backlog walk, and okf_index.py's folder walk). Entries must
# therefore be safe for BOTH per-file walks (only .md matters there, so a
# folder full of venv/cache noise used to be invisible) AND folder walks
# (every directory is a hit, so noise becomes a flood).
#
# The 2026-07 widen was triggered specifically by okf_index.py exposing
# folders per-file walks never touched: .hermes/plans, .retired/* (an
# explicitly-archived 'safe to delete' folder per its own README),
# .scratch/*, and worst of all .scratch-thumbs-venv/lib/python3.14/site-packages/
# — a full vendored Python venv (PIL/pip + pip's vendored deps) that nested
# hundreds of site-packages subfolders. Entries added below shut the gate
# on those families. NOTE: 'state' here means the top-level 'state/' runtime
# dir at repo root (gitignored Hermes runtime state — wf-ledgered /
# xp-workflow-*); it is NOT the same as '.claude/state' which is already
# covered by the '.claude' entry above.
EXCLUDE_DIR_PARTS = {
    ".git", ".claude", "worktrees", "node_modules", "__pycache__", ".venv", "venv",
    "scratchpad", "routine-logs", "routine-ledger",
    # Widened 2026-07 to stop okf_index.py from walking vendored / scratch /
    # runtime folders that per-file iter_md never surfaced:
    ".hermes", ".retired", ".scratch", ".scratch-thumbs-venv",
    "site-packages", "dist-info", ".dylibs",
    # Gitignored Hermes / workflow-runner runtime output dirs:
    "state", "runs",
}
# Any path containing one of these substrings is skipped wholesale.
EXCLUDE_PATH_SUBSTR = (
    "/impeccable/",   # vendored external skill (carries its own multi-agent mirrors)
    "/_impeccable-upstream-source/",  # vendored upstream source mirror (same reason)
)

# ── Layout taxonomy (concept-path placement) ─────────────────────────────────
# OKF's prose has always promised that NON-markdown files are "tidied by placement
# and pruning — files live under the concept-path they belong to." `--layout` is
# the check that finally makes that promise real: it classifies every loose file at
# the repo ROOT against a target concept-path. Markdown frontmatter is checked
# elsewhere; this is the orthogonal placement axis.
#
# The ROOT CONTRACT — files that LEGITIMATELY live at repo root, never misplaced:
# human-facing entrypoints, the generated dashboard runtime/data the browser loads
# from root, the repo-root ANCHOR every script walks up to find, and the build engine
# everything is path-relative to. Moving any of these is not "tidying" — it strands a
# hardcoded path, the dashboard's <script src>, or root detection itself.
LAYOUT_PINNED = {
    "README.md", "CLAUDE.md", "VERSIONS.md",            # canonical root docs + skill registry
    "index.html", "app.js", "app.css",                  # dashboard runtime, served from root
    "guild-data.js", "guild-data.json",                 # generated dashboard data (build.py output; index.html loads guild-data.js)
    "workflows.json",                                   # repo-root ANCHOR + loaded by the turn-gating hooks (move = session brick)
    "build.py",                                         # the build engine — root entrypoint everything resolves relative to
    "package.json", "package-lock.json",
}
# Ordered (regex, target_dir, safety) rules — FIRST match wins. `safety`:
#   "safe"   — inert content nothing references → a mover may relocate it freely.
#   "review" — reached by hardcoded paths (build.py, serve.cjs, hooks, sibling scripts)
#              → relocation needs a path-rewrite sweep (a gated Architecture Build).
# (The 2026-06 reorg moved every match below into its concept-path; these rules now
#  catch any NEW loose file of the same kind so the root cannot silt up again.)
LAYOUT_RULES = [
    (r"^(?:STRATEGIST|AUDIT)[-A-Z].*\.md$", "docs/",            "safe"),
    (r"^gen-.*\.(?:cjs|py)$",               "tools/generators/", "review"),
    (r"^(?:build_guild_log|conformity_check|install|log_event|member_level)\.py$",
                                            "tools/",            "review"),
    (r".*\.json$",                          "data/",             "review"),
]


def count_refs(name: str, root: str) -> int:
    """How many OTHER tracked files mention this filename (markdown links, `see X.md`
    pointers, code comments, JSON detail strings). Inbound refs are what make a move
    unsafe — any one would go stale. Uses `git grep` so it only counts the tracked
    integrity surface and is fast on a big repo."""
    r = subprocess.run(["git", "grep", "-I", "-l", "-F", name],
                       cwd=root, capture_output=True, text=True)
    if r.returncode not in (0, 1):  # 0=hits, 1=no hits; anything else = git error
        return -1  # unknown → caller treats as 'not provably safe'
    hits = [ln for ln in r.stdout.splitlines() if ln.strip() and os.path.basename(ln.strip()) != name]
    return len(hits)


def classify_placement(name: str, root: str):
    """For a ROOT-level filename, return (target_path, safety, refs) if misplaced, or
    None if it belongs at root (pinned) or carries no rule. `safety` is computed, not
    guessed: a rule's base tag is 'safe' ONLY when the file has zero inbound refs;
    any reference (or a rule tagged 'review') downgrades it to 'review' — a move that
    needs a path/link-rewrite sweep."""
    if name in LAYOUT_PINNED or name.startswith("."):
        return None
    for pat, target, base in LAYOUT_RULES:
        if re.match(pat, name):
            refs = count_refs(name, root)
            safety = "safe" if (base == "safe" and refs == 0) else "review"
            return (target + name, safety, refs)
    return None  # unclassified root file — advisory only, not flagged


def root_loose_files(root: str):
    """Plain files sitting directly at repo root (no subdir, no dotfiles)."""
    for fn in sorted(os.listdir(root)):
        full = os.path.join(root, fn)
        if os.path.isfile(full) and not fn.startswith("."):
            yield fn


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


def run_layout(root: str, do_fix: bool, as_json: bool) -> int:
    """Placement audit: flag root-level files that belong under a concept-path.
    With do_fix, relocate ONLY the 'safe' class via `git mv` (inert files nothing
    references); 'review' class is reported and deferred to a path-rewrite sweep."""
    misplaced = []
    for fn in root_loose_files(root):
        verdict = classify_placement(fn, root)
        if verdict:
            target, safety, refs = verdict
            misplaced.append({"file": fn, "target": target, "safety": safety, "refs": refs})

    moved, deferred = [], []
    if do_fix:
        for m in misplaced:
            if m["safety"] != "safe":
                deferred.append(m)
                continue
            tdir = os.path.join(root, os.path.dirname(m["target"]))
            os.makedirs(tdir, exist_ok=True)
            r = subprocess.run(["git", "mv", m["file"], m["target"]],
                               cwd=root, capture_output=True, text=True)
            if r.returncode == 0:
                moved.append(m)
            else:  # fall back to a plain move if the file isn't tracked
                try:
                    os.replace(os.path.join(root, m["file"]), os.path.join(root, m["target"]))
                    moved.append(m)
                except Exception as e:
                    sys.stderr.write(f"[okf-layout] move failed {m['file']}: {e}\n")
        moved_names = {m["file"] for m in moved}
        misplaced = [m for m in misplaced if m["file"] not in moved_names]

    safe_left = [m for m in misplaced if m["safety"] == "safe"]
    review = [m for m in misplaced if m["safety"] == "review"]

    if as_json:
        print(json.dumps({
            "root_files": sum(1 for _ in root_loose_files(root)),
            "misplaced": len(misplaced), "moved": [m["file"] for m in moved],
            "safe_unmoved": safe_left, "review_deferred": review,
        }, indent=2))
    else:
        print("OKF layout audit — concept-path placement of root files")
        if moved:
            print(f"  moved {len(moved)} safe file(s) → concept-path:")
            for m in moved:
                print(f"      {m['file']} → {m['target']}")
        if safe_left:
            print(f"  ✗ {len(safe_left)} safe-to-move file(s) still at root (run --layout --fix):")
            for m in safe_left:
                print(f"      {m['file']} → {m['target']}")
        if review:
            print(f"  ⚠ {len(review)} file(s) need a path/link-rewrite sweep (Phase-2 Architecture Build):")
            for m in review:
                why = "ref-count unknown" if m["refs"] < 0 else f"{m['refs']} inbound ref(s)"
                print(f"      {m['file']} → {m['target']}  [review: {why}]")
        if not misplaced and not moved:
            print("  ✓ every root file is pinned or correctly placed")
    # Enforce only the 'safe' class — 'review' is advisory until the sweep runs.
    return 1 if safe_left else 0


def main():
    ap = argparse.ArgumentParser(description="OKF conformance audit / fixer")
    ap.add_argument("--fix", action="store_true", help="rewrite non-conformant files to baseline OKF")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--staged", action="store_true", help="only git-staged files")
    ap.add_argument("--path", help="audit a single file or subtree")
    ap.add_argument("--layout", action="store_true",
                    help="placement audit: flag root files that belong under a concept-path "
                         "(--fix relocates only the safe class)")
    args = ap.parse_args()

    root = repo_root()
    if args.layout:
        sys.exit(run_layout(root, args.fix, args.json))
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
