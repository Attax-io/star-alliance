#!/usr/bin/env python3
"""
commit_scope.py — concurrent-actor commit-scoper for the /cleanup skill (R10).

Cleanup/followups sweeps run in a working tree that a PARALLEL session is
actively editing (FE source + DB + all-locale i18n + docs-daemon counter bumps).
Three of the four 2026-05-30→06-02 sweeps hit this: 35–119 dirty files belonging
to other workstreams sat next to the campaign's own. A naive `git add -A` commits
someone else's half-finished work and can break `main`. This helper mechanizes
the §L27 discipline so it isn't re-derived by hand each sweep.

It NEVER commits. It partitions the dirty tree, runs a buildability check, and
emits the exact `git add` block for the human/Claude to run.

Subcommands:
  scan       `git status --porcelain` → partition every dirty path into
               owned        — the campaign's own files (from --files / --campaign)
               tell:daemon  — docs frontmatter counter-only diff (claude_hits …)
               tell:barrel  — index.ts with ONLY `export …` line additions
               tell:i18n    — apps/web/public/messages/* (parallel locale run)
               foreign      — everything else dirty (NOT yours → do not commit)
             Owned set comes from `--files a,b,c` OR `--campaign <dir-name>`
             (derives candidates from the campaign's [[wikilink]] refs + its own
             dir). With neither, owned is empty (still classifies the tells).
             Writes /tmp/commit_scope.json.
  buildcheck For each owned .ts/.tsx file, resolve its repo-local imports; WARN if
             any resolves to a foreign-dirty sibling (committing owned alone may
             leave `main` referencing a half-edited file). Reads the json.
  emit       Print the exact `git -C <root> add <owned…>` block. Never runs it.

Exit codes: 0 ok; 2 buildcheck found a foreign-import risk; 3 not a git tree.
"""

import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path


# ── root (shared house helper) ───────────────────────────────────────────────

def default_root() -> str:
    # Walk up from this file / cwd to the dir holding apps/web/config/app.config.ts
    # (the lex_council repo root). Portable; falls back to the dev-machine path.
    starts = [Path(__file__).resolve().parent, Path.cwd().resolve()]
    seen = set()
    for start in starts:
        for parent in [start, *start.parents]:
            if parent in seen:
                continue
            seen.add(parent)
            if (parent / 'apps' / 'web' / 'config' / 'app.config.ts').is_file():
                return str(parent)
            cand = parent / 'lex_council'
            if (cand / 'apps' / 'web' / 'config' / 'app.config.ts').is_file():
                return str(cand)
    return os.path.expanduser("~/Documents/Claude/Projects/Lex Council App/lex_council")


def _arg(flag):
    """Return the value after `--flag` in argv, or None."""
    if flag in sys.argv:
        i = sys.argv.index(flag)
        if i + 1 < len(sys.argv):
            return sys.argv[i + 1]
    return None


LEX_ROOT = _arg("--root") or default_root()
DOCS = os.path.join(LEX_ROOT, "docs")
SCOPE_FILE = "/tmp/commit_scope.json"

# Frontmatter keys the docs housekeeper daemon bumps on its own — a diff that
# touches ONLY these is the daemon, not your edit (§L27, discovery_docs-daemon-races-edit-tool).
DAEMON_KEYS = ("claude_hits", "housekeeper_passes", "last_housekeeper_pass", "vault_log_version")


# ── git plumbing ─────────────────────────────────────────────────────────────

def git(*args):
    """Run git in LEX_ROOT; return (rc, stdout)."""
    p = subprocess.run(["git", "-C", LEX_ROOT, *args],
                       capture_output=True, text=True)
    return p.returncode, p.stdout


def dirty_paths():
    """Parse `git status --porcelain=v1 -z` → list of repo-relative paths
    (post-rename name for renames). Robust to spaces; -z avoids quoting."""
    rc, out = git("status", "--porcelain=v1", "-z")
    if rc != 0:
        print("🚩 Not a git work tree (or git unavailable):", LEX_ROOT)
        sys.exit(3)
    paths, toks = [], out.split("\0")
    i = 0
    while i < len(toks):
        tok = toks[i]
        if not tok:
            i += 1
            continue
        status, path = tok[:2], tok[3:]
        # Rename/copy: the NUL after the entry holds the old path → skip it.
        if status and status[0] in ("R", "C"):
            i += 2
        else:
            i += 1
        if path:
            paths.append(path)
    return paths


def diff_added_lines(path):
    """`git diff -U0` added lines (without the leading '+') for a tracked file.
    Empty list for untracked/new files."""
    rc, out = git("diff", "-U0", "--", path)
    if rc != 0 or not out:
        return None  # untracked / no textual diff
    added = []
    for ln in out.splitlines():
        if ln.startswith("+") and not ln.startswith("+++"):
            added.append(ln[1:])
    return added


# ── classification ───────────────────────────────────────────────────────────

def is_daemon_only(path):
    """True if the file's diff changes ONLY docs-daemon frontmatter counters."""
    if "/docs/" not in f"/{path}" and not path.startswith("docs/"):
        return False
    added = diff_added_lines(path)
    if not added:
        return False
    for ln in added:
        s = ln.strip()
        if not s:
            continue
        key = s.split(":", 1)[0].strip()
        if key not in DAEMON_KEYS:
            return False
    return True


def is_barrel_export_only(path):
    """True if a *index.ts barrel changed by ADDING only `export …` lines."""
    if not path.endswith("index.ts") and not path.endswith("index.tsx"):
        return False
    added = diff_added_lines(path)
    if not added:
        return False
    saw = False
    for ln in added:
        s = ln.strip()
        if not s:
            continue
        if not (s.startswith("export ") or s.startswith("export{") or s.startswith("//")):
            return False
        saw = True
    return saw


def is_i18n(path):
    return path.startswith("apps/web/public/messages/") and path.endswith(".json")


# ── owned-set derivation ─────────────────────────────────────────────────────

def owned_from_files():
    raw = _arg("--files")
    if not raw:
        return set()
    return {p.strip().lstrip("./") for p in raw.split(",") if p.strip()}


def owned_from_campaign():
    """Derive owned candidates from a campaign dir: the dir's own files +
    every [[wikilink]] in its plan/vault artifacts resolved to a repo path."""
    name = _arg("--campaign")
    if not name:
        return set()
    cdir = None
    for sub in ("build-campaigns", "audit-campaigns"):
        cand = os.path.join(DOCS, sub, name)
        if os.path.isdir(cand):
            cdir = cand
            break
    if not cdir:
        print(f"🚩 --campaign '{name}' not found under docs/{{build,audit}}-campaigns/")
        return set()

    owned = set()
    # the campaign dir's own files
    for root, _d, files in os.walk(cdir):
        for fn in files:
            ap = os.path.join(root, fn)
            owned.add(os.path.relpath(ap, LEX_ROOT))
    # [[wikilink]] basenames in its markdown → resolve by basename match
    wl = re.compile(r"\[\[([^\]|#]+)")
    wanted = set()
    for root, _d, files in os.walk(cdir):
        for fn in files:
            if fn.endswith(".md"):
                try:
                    txt = open(os.path.join(root, fn), encoding="utf-8", errors="replace").read()
                except OSError:
                    continue
                for m in wl.findall(txt):
                    wanted.add(os.path.basename(m.strip()))
    if wanted:
        owned |= resolve_basenames(wanted)
    return owned


def resolve_basenames(basenames):
    """Map a set of file basenames (possibly extensionless wikilinks) to actual
    repo-relative paths by scanning apps/ + packages/ + docs/. Best-effort:
    only unambiguous single matches are added."""
    targets = defaultdict(list)
    want = set()
    for b in basenames:
        want.add(b)
        if "." not in b:
            for ext in (".ts", ".tsx", ".md"):
                want.add(b + ext)
    scan_roots = [os.path.join(LEX_ROOT, d) for d in ("apps", "packages", "docs")]
    for sr in scan_roots:
        for root, _d, files in os.walk(sr):
            # skip node_modules / .next
            if "node_modules" in root or "/.next" in root:
                continue
            for fn in files:
                if fn in want:
                    targets[fn].append(os.path.relpath(os.path.join(root, fn), LEX_ROOT))
    out = set()
    for _b, hits in targets.items():
        if len(hits) == 1:        # unambiguous only
            out.add(hits[0])
    return out


# ── subcommands ──────────────────────────────────────────────────────────────

def cmd_scan():
    owned = owned_from_files() | owned_from_campaign()
    paths = dirty_paths()

    buckets = {"owned": [], "tell:daemon": [], "tell:barrel": [],
               "tell:i18n": [], "foreign": []}
    for p in paths:
        if p in owned:
            buckets["owned"].append(p)
        elif is_daemon_only(p):
            buckets["tell:daemon"].append(p)
        elif is_barrel_export_only(p):
            buckets["tell:barrel"].append(p)
        elif is_i18n(p):
            buckets["tell:i18n"].append(p)
        else:
            buckets["foreign"].append(p)

    # owned files that git doesn't see as dirty (already clean / typo'd path)
    owned_not_dirty = sorted(owned - set(paths))

    with open(SCOPE_FILE, "w") as f:
        json.dump({"root": LEX_ROOT, "owned_input": sorted(owned),
                   "buckets": buckets, "owned_not_dirty": owned_not_dirty}, f, indent=2)

    print(f"commit_scope.py scan — {LEX_ROOT}")
    print(f"  dirty files: {len(paths)}   owned-input: {len(owned)}\n")
    order = ["owned", "tell:daemon", "tell:barrel", "tell:i18n", "foreign"]
    mark = {"owned": "✓", "tell:daemon": "·", "tell:barrel": "·",
            "tell:i18n": "·", "foreign": "🚩"}
    for k in order:
        n = len(buckets[k])
        print(f"  {mark[k]} {k:<13}: {n}")
        for p in buckets[k][:12]:
            print(f"        {p}")
        if n > 12:
            print(f"        … +{n - 12} more")
    if owned_not_dirty:
        print(f"\n  ? owned-but-not-dirty ({len(owned_not_dirty)}) — already clean or wrong path:")
        for p in owned_not_dirty[:12]:
            print(f"        {p}")
    print(f"\n  foreign + all tells are NOT yours — leave them uncommitted (§L27).")
    print(f"  Wrote → {SCOPE_FILE}")
    if not buckets["owned"]:
        print("  ⚠ owned bucket empty — pass --files or --campaign to scope a commit.")
    return buckets


def _load_scope():
    if not os.path.exists(SCOPE_FILE):
        print(f"🚩 {SCOPE_FILE} not found. Run scan first.")
        sys.exit(1)
    return json.load(open(SCOPE_FILE))


IMPORT_RE = re.compile(r"""(?:import|export)\b[^'"]*?from\s*['"]([^'"]+)['"]""")
BARE_IMPORT_RE = re.compile(r"""\bimport\s*['"]([^'"]+)['"]""")


def _resolve_import(spec, from_file):
    """Resolve a module spec to a repo-relative path, or None if external."""
    base = None
    if spec.startswith("@/"):
        base = os.path.join(LEX_ROOT, "apps", "web", spec[2:])
    elif spec.startswith("."):
        base = os.path.normpath(os.path.join(LEX_ROOT, os.path.dirname(from_file), spec))
    else:
        return None  # node_modules / @repo/* alias — out of scope for this check
    for cand in (base, base + ".ts", base + ".tsx",
                 os.path.join(base, "index.ts"), os.path.join(base, "index.tsx")):
        if os.path.isfile(cand):
            return os.path.relpath(cand, LEX_ROOT)
    return None


def cmd_buildcheck():
    scope = _load_scope()
    owned = scope["buckets"]["owned"]
    foreign = set(scope["buckets"]["foreign"]) | set(scope["buckets"]["tell:i18n"])
    risks = []
    for p in owned:
        if not (p.endswith(".ts") or p.endswith(".tsx")):
            continue
        ap = os.path.join(LEX_ROOT, p)
        try:
            src = open(ap, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        specs = set(IMPORT_RE.findall(src)) | set(BARE_IMPORT_RE.findall(src))
        for spec in specs:
            rel = _resolve_import(spec, p)
            if rel and rel in foreign:
                risks.append((p, spec, rel))

    print("commit_scope.py buildcheck")
    print(f"  owned source files checked: "
          f"{sum(1 for p in owned if p.endswith(('.ts', '.tsx')))}")
    if not risks:
        print("  ✓ no owned file imports a foreign-dirty sibling — safe to commit owned in isolation.")
        return
    print(f"  🚩 {len(risks)} foreign-import risk(s) — committing owned alone may break `main`:")
    for p, spec, rel in risks:
        print(f"     {p}")
        print(f"        imports '{spec}' → {rel}  (foreign-dirty, NOT in owned)")
    print("\n  → Either add the sibling to --files (if it's really yours) or hold the commit.")
    sys.exit(2)


def cmd_emit():
    scope = _load_scope()
    owned = scope["buckets"]["owned"]
    if not owned:
        print("  (owned bucket empty — nothing to stage. Re-run scan with --files/--campaign.)")
        return
    print("# Stage ONLY the campaign-owned files (§L27). Review, then run:")
    print(f"git -C {LEX_ROOT} add \\")
    for i, p in enumerate(sorted(owned)):
        tail = "" if i == len(owned) - 1 else " \\"
        print(f"  {p}{tail}")
    print(f"\n# {len(owned)} file(s). Foreign + tells left untouched. Never `git add -A` here.")


# ── main ─────────────────────────────────────────────────────────────────────

COMMANDS = {"scan": cmd_scan, "buildcheck": cmd_buildcheck, "emit": cmd_emit}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print(f"Usage: python3 commit_scope.py <{'|'.join(COMMANDS)}> "
              f"[--campaign <dir-name>] [--files a,b,c] [--root <path>]")
        print(__doc__)
        sys.exit(1)
    COMMANDS[sys.argv[1]]()
