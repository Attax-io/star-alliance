#!/usr/bin/env python3
"""
consolidate_code.py — code-side duplicate detection for the /cleanup skill.

The code sibling of the i18n `consolidate` mode. Surfaces duplicate / copy-pasted
CODE (magic literals, config-in-N-places, off-token hex, copy-pasted function
bodies) and classifies it into the same tiers + candidate IDs (C1, C2, ...) as
CONSOLIDATION-CANDIDATES.md, which this refreshes.

Subcommands:
  scan      Run the deterministic detectors over apps/web (grep + os.walk over
            *.ts/*.tsx). Detects: PANEL_WIDTH magic-literal dup (C1),
            PAGE_SIZE_OPTIONS config-in-N-places (C2), off-token hex literals
            (advisory), and copy-pasted exported function bodies (highest value).
            Output: /tmp/consolidate_code_scan.json
  classify  Read the scan output and tier each candidate:
              T1 extract-now    mechanical, ≤ codemod / a few files, zero parity risk
              T2 needs-campaign  >15 sites OR behavior-parity risk (DB out of scope)
              T3 resolved        already consolidated (count == 0)
            Output: /tmp/consolidate_code_classified.json
  surface   Print a human triage list grouped by tier, each candidate with its
            detection evidence + recommended action (T1 codemod cmd / T2 campaign
            trigger phrase). Prints the registry priority order if present.
  extract   DRY-RUN by default. For the ONE safe mechanical candidate (C1:
            `const PANEL_WIDTH = 332` → import PORTAL_SIDEBAR_WIDTH) print the
            exact per-file change it WOULD make. Touches disk only with --apply
            AND only when each target line byte-matches the expected pattern.

HARD RULE (skill §L2/§L4 "look-alike-but-different" trap): this script NEVER
auto-merges or auto-edits source to consolidate anything beyond the single
safest mechanical case. Functions / views / RLS predicates must go through a
conquering-campaign with a byte-compare, never this script. Byte-compare before
claiming two things are identical.
"""

import json
import sys
import os
import subprocess
import re
import hashlib
from collections import defaultdict
from pathlib import Path

# ── constants ──────────────────────────────────────────────────────────────


def default_root() -> str:
    # Walk up from this file / cwd looking for the dir that contains
    # apps/web/config/app.config.ts (the lex_council repo root). Portable across
    # machines; falls back to the historical dev-machine path if not found.
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
    return os.path.expanduser(
        "~/Documents/Claude/Projects/Lex Council App/lex_council"
    )


LEX_ROOT = default_root()
WEB = os.path.join(LEX_ROOT, "apps/web")

SCAN_FILE       = "/tmp/consolidate_code_scan.json"
CLASSIFIED_FILE = "/tmp/consolidate_code_classified.json"

REGISTRY = os.path.expanduser(
    "~/Documents/Claude/Projects/Lex Council App/.claude/skills/cleanup/"
    "CONSOLIDATION-CANDIDATES.md"
)
DB_SYNTH_REL = ("docs/audit-campaigns/2026-05-22_db-wide-consolidation-audit/"
                "99-synthesis.md")

# C1: the copy-declared magic literal vs its canonical home.
C1_LOCAL_DECL = "const PANEL_WIDTH = 332"
C1_CANONICAL  = "PORTAL_SIDEBAR_WIDTH"

# Off-token hex: advisory campaign flag once it crosses this many lines.
HEX_CAMPAIGN_THRESHOLD = 10
# A cross-cutting site count above which a candidate is campaign-only, not T1.
T1_SITE_CEILING = 15

# Markers (house style).
OK   = "✓"
FLAG = "🚩"
ASK  = "?"


# ── helpers ────────────────────────────────────────────────────────────────

def _grep_files(pattern, root, exts=("*.ts", "*.tsx")):
    """grep -rln <pattern> over root for the given extensions. Returns rel paths."""
    if not os.path.isdir(root):
        return []
    cmd = ["grep", "-rln", pattern, root]
    for e in exts:
        cmd.append("--include=" + e)
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    except Exception:
        return []
    out = []
    for line in res.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(os.path.relpath(line, LEX_ROOT))
        except Exception:
            out.append(line)
    return sorted(out)


def _grep_lines(pattern, roots, exts=("*.tsx",)):
    """grep -rn <pattern> over roots. Returns raw 'path:line:text' strings."""
    cmd = ["grep", "-rn", pattern]
    real = [r for r in roots if os.path.isdir(r)]
    if not real:
        return []
    cmd += real
    for e in exts:
        cmd.append("--include=" + e)
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    except Exception:
        return []
    return [l for l in res.stdout.splitlines() if l.strip()]


def _walk_source_files(root, exts=(".ts", ".tsx")):
    """Yield absolute paths of source files under root, skipping junk dirs."""
    skip = {"node_modules", ".next", ".turbo", "dist", "build", ".git"}
    if not os.path.isdir(root):
        return
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in skip]
        for fn in filenames:
            if fn.endswith(exts):
                yield os.path.join(dirpath, fn)


# ── function-body extraction (best-effort, never throws) ─────────────────────

# export (async) function NAME( ... )  — capture name + the byte offset of '('.
_FN_DECL_RE = re.compile(
    r"export\s+(?:async\s+)?function\s+([A-Za-z_$][\w$]*)\s*[(<]"
)
# export const NAME = (async) ( ... ) =>   /  export const NAME = (async) X =>
_FN_ARROW_RE = re.compile(
    r"export\s+const\s+([A-Za-z_$][\w$]*)\s*(?::[^=]+)?=\s*(?:async\s+)?\(?"
)


def _match_brace_body(src, brace_idx):
    """Given the index of an opening '{', return the body string up to its match.

    Brace-aware but string/comment-naive — that's fine, we only hash it. Returns
    None if no balanced close is found within a sane window."""
    depth = 0
    end = min(len(src), brace_idx + 20000)  # cap runaway bodies
    for i in range(brace_idx, end):
        c = src[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return src[brace_idx + 1:i]
    return None


def _normalized_hash(body):
    """SHA-1 of body with all whitespace stripped. Empty/trivial → None."""
    compact = re.sub(r"\s+", "", body)
    if len(compact) < 40:  # too small to be a meaningful clone
        return None
    return hashlib.sha1(compact.encode("utf-8", "replace")).hexdigest()


def _extract_function_hashes(abs_path):
    """Return list of (func_name, body_hash) for exported fns in one file.

    Best-effort: brace-matches from the first '{' after the signature; if that
    fails, falls back to hashing the first ~400 non-whitespace chars after '{'.
    Wrapped by the caller in try/except; returns [] on any trouble here too."""
    results = []
    try:
        with open(abs_path, "r", encoding="utf-8", errors="replace") as fh:
            src = fh.read()
    except Exception:
        return results

    for rx in (_FN_DECL_RE, _FN_ARROW_RE):
        for m in rx.finditer(src):
            name = m.group(1)
            brace = src.find("{", m.end() - 1)
            if brace == -1 or brace - m.end() > 200:
                continue  # arrow with no block body, or too far → skip
            body = _match_brace_body(src, brace)
            if body is None:
                # Fallback: first ~400 non-whitespace chars after the brace.
                tail = src[brace + 1: brace + 1200]
                compact = re.sub(r"\s+", "", tail)[:400]
                if len(compact) < 40:
                    continue
                h = hashlib.sha1(compact.encode("utf-8", "replace")).hexdigest()
                results.append((name, h))
                continue
            h = _normalized_hash(body)
            if h:
                results.append((name, h))
    return results


# ── subcommands ──────────────────────────────────────────────────────────────

def cmd_scan():
    """Run all deterministic detectors and persist findings."""
    print("consolidate_code.py scan — scanning apps/web ...")
    detections = {}

    # ── C1: magic-literal duplication (PANEL_WIDTH = 332) ──
    c1_files = _grep_files(C1_LOCAL_DECL, WEB)
    canon = _grep_lines(C1_CANONICAL + " = 332", [WEB], exts=("*.ts", "*.tsx"))
    detections["C1"] = {
        "what": "const PANEL_WIDTH = 332 copy-declared instead of importing "
                "canonical " + C1_CANONICAL,
        "count": len(c1_files),
        "files": c1_files,
        "canonical": canon[0] if canon else None,
    }
    print("  %s C1 magic-literal PANEL_WIDTH=332: %d files" %
          (FLAG if c1_files else OK, len(c1_files)))

    # ── C2: config-in-N-places (PAGE_SIZE_OPTIONS) ──
    c2_files = _grep_files(r"PAGE_SIZE_OPTIONS[[:space:]]*=", WEB)
    detections["C2"] = {
        "what": "PAGE_SIZE_OPTIONS defined in multiple places",
        "count": len(c2_files),
        "files": c2_files,
    }
    print("  %s C2 config-in-N-places PAGE_SIZE_OPTIONS: %d files" %
          (FLAG if len(c2_files) > 1 else OK, len(c2_files)))

    # ── off-token hex literals (advisory) ──
    hex_roots = [os.path.join(WEB, "components"), os.path.join(WEB, "app")]
    hex_lines = _grep_lines(r"#[0-9a-fA-F]\{3,6\}", hex_roots, exts=("*.tsx",))
    hex_color = [l for l in hex_lines
                 if "//" not in l.split(":", 2)[-1]
                 and re.search(r"color|background|border", l, re.I)]
    detections["hex"] = {
        "what": "off-token hex literals on color/background/border (no token)",
        "count": len(hex_color),
        "campaign_flag": len(hex_color) > HEX_CAMPAIGN_THRESHOLD,
        "maps_to": "C19/C21",
        "sample": hex_color[:8],
    }
    mk = FLAG if len(hex_color) > HEX_CAMPAIGN_THRESHOLD else OK
    print("  %s off-token hex (color/bg/border): %d lines%s" %
          (mk, len(hex_color),
           "  → token-sweep campaign flag" if len(hex_color) >
           HEX_CAMPAIGN_THRESHOLD else ""))

    # ── copy-pasted function bodies (highest-value detector) ──
    by_hash = defaultdict(list)   # hash → list of {file, fn}
    scanned = 0
    skipped = 0
    for abs_path in _walk_source_files(WEB):
        scanned += 1
        try:
            pairs = _extract_function_hashes(abs_path)
        except Exception:
            skipped += 1
            continue
        rel = os.path.relpath(abs_path, LEX_ROOT)
        seen_here = set()
        for name, h in pairs:
            # dedupe identical (file,hash) so an in-file repeat isn't a "group"
            if (rel, h) in seen_here:
                continue
            seen_here.add((rel, h))
            by_hash[h].append({"file": rel, "fn": name})

    dup_groups = []
    for h, members in by_hash.items():
        files = {m["file"] for m in members}
        if len(files) >= 2:  # same body-hash in ≥2 distinct files
            dup_groups.append({
                "hash": h[:12],
                "file_count": len(files),
                "members": sorted(members, key=lambda m: (m["file"], m["fn"])),
            })
    dup_groups.sort(key=lambda g: -g["file_count"])
    detections["dup_functions"] = {
        "what": "exported function bodies with an identical normalized hash in "
                "≥2 files (best-effort extraction)",
        "group_count": len(dup_groups),
        "files_scanned": scanned,
        "files_skipped": skipped,
        "groups": dup_groups,
    }
    mk = FLAG if dup_groups else OK
    print("  %s copy-pasted function bodies: %d cross-file groups "
          "(%d files scanned, %d skipped)" %
          (mk, len(dup_groups), scanned, skipped))

    with open(SCAN_FILE, "w") as f:
        json.dump(detections, f, indent=2)
    print("  Wrote → " + SCAN_FILE)
    return detections


def cmd_classify():
    """Tier each scan candidate into T1 / T2 / T3."""
    if not os.path.exists(SCAN_FILE):
        print("  [ERROR] %s not found. Run scan first." % SCAN_FILE)
        sys.exit(1)
    det = json.load(open(SCAN_FILE))
    classified = {"T1": [], "T2": [], "T3": []}

    def add(tier, cid, evidence, action):
        classified[tier].append({"id": cid, "evidence": evidence,
                                  "action": action})

    # C1 — magic-literal dedup. Mechanical codemod regardless of count (it's a
    # single literal with one canonical home), but if 0 it's resolved.
    c1 = det.get("C1", {})
    if c1.get("count", 0) == 0:
        add("T3", "C1", "0 local PANEL_WIDTH=332 decls remain",
            "resolved — all sites import " + C1_CANONICAL)
    else:
        add("T1", "C1", "%d files copy-declare %s" % (c1["count"], C1_LOCAL_DECL),
            "codemod: python3 consolidate_code.py extract  (then --apply)")

    # C2 — config in N places. 0/1 = fine; ≥2 = extract to one shared const.
    c2 = det.get("C2", {})
    if c2.get("count", 0) <= 1:
        add("T3", "C2", "PAGE_SIZE_OPTIONS defined in %d place(s)" %
            c2.get("count", 0), "resolved — single source")
    else:
        add("T1", "C2", "PAGE_SIZE_OPTIONS defined in %d files: %s" %
            (c2["count"], ", ".join(c2.get("files", []))),
            "extract to one shared const (e.g. lib/pagination.ts); both import it")

    # off-token hex — advisory; >10 = token-sweep campaign (parity-adjacent),
    # so T2. Otherwise T1-ish tidy / resolved.
    hx = det.get("hex", {})
    if hx.get("count", 0) == 0:
        add("T3", "hex", "0 off-token hex lines", "resolved")
    elif hx.get("campaign_flag"):
        add("T2", "hex", "%d off-token hex lines (>%d)" %
            (hx["count"], HEX_CAMPAIGN_THRESHOLD),
            "token-sweep campaign — maps to %s; needs N new design tokens then "
            "a sweep" % hx.get("maps_to", "C19/C21"))
    else:
        add("T1", "hex", "%d off-token hex lines (≤%d)" %
            (hx["count"], HEX_CAMPAIGN_THRESHOLD),
            "tidy: replace with token (C.alwaysWhite / colors.navy)")

    # copy-pasted function bodies — every group carries behavior-parity risk
    # (§L2 byte-compare) and is cross-cutting, so always T2. 0 groups = clean.
    df = det.get("dup_functions", {})
    groups = df.get("groups", [])
    if not groups:
        add("T3", "dup_functions", "0 cross-file duplicate function bodies",
            "resolved / none detected")
    else:
        for g in groups:
            fns = ", ".join("%s (%s)" % (m["fn"], m["file"])
                            for m in g["members"])
            sites = g["file_count"]
            tier = "T2"  # never auto-merge a function; campaign + byte-compare
            add(tier, "dup_functions",
                "%d files share body-hash %s: %s" % (sites, g["hash"], fns),
                "campaign: byte-compare each body, extract one shared helper "
                "(NEVER auto-merged by this script)")

    # DB candidates are explicitly out of scope for this FE scanner — point at
    # the persisted synthesis so nobody re-mines them here.
    db_synth = os.path.join(LEX_ROOT, DB_SYNTH_REL)
    add("T2", "DB-views/RLS",
        "DB view/RLS consolidation (C23–C37) is out of scope for this FE scanner",
        "see %s%s" % (DB_SYNTH_REL,
                      "" if os.path.exists(db_synth) else "  [path missing]"))

    with open(CLASSIFIED_FILE, "w") as f:
        json.dump(classified, f, indent=2)

    print("\nTier summary:")
    print("  %s T1 extract-now   : %d" % (OK,   len(classified["T1"])))
    print("  %s T2 needs-campaign: %d" % (FLAG, len(classified["T2"])))
    print("  %s T3 resolved      : %d" % (OK,   len(classified["T3"])))
    print("\nWrote → " + CLASSIFIED_FILE)
    return classified


def _registry_priority():
    """Pull the 'Priority order' bullet/numbered lines from the registry md."""
    if not os.path.exists(REGISTRY):
        return []
    try:
        with open(REGISTRY, "r", encoding="utf-8", errors="replace") as fh:
            lines = fh.read().splitlines()
    except Exception:
        return []
    out, capture = [], False
    for ln in lines:
        low = ln.strip().lower()
        if low.startswith("## ") and "priority order" in low:
            capture = True
            continue
        if capture:
            if ln.strip().startswith("## "):
                break
            if re.match(r"^\s*\d+\.\s+", ln):
                out.append(ln.strip())
    return out


def cmd_surface():
    """Human triage list grouped by tier + recommended actions."""
    if not os.path.exists(CLASSIFIED_FILE):
        print("  [ERROR] %s not found. Run classify first." % CLASSIFIED_FILE)
        sys.exit(1)
    cls = json.load(open(CLASSIFIED_FILE))

    print("\n" + "=" * 60)
    print("CODE CONSOLIDATION TRIAGE")
    print("=" * 60)

    t1 = cls.get("T1", [])
    print("\n%s T1 extract-now (%d) — mechanical, run under autonomous cadence:"
          % (OK, len(t1)))
    for c in t1:
        print("  [%s] %s" % (c["id"], c["evidence"]))
        print("    → %s" % c["action"])

    t2 = cls.get("T2", [])
    print("\n%s T2 needs-campaign (%d) — open a conquering-campaign "
          "(byte-compare, §L2):" % (FLAG, len(t2)))
    for c in t2:
        print("  [%s] %s" % (c["id"], c["evidence"]))
        print("    → %s" % c["action"])
    if t2:
        print("    Trigger phrase: \"ship this refactor\" / "
              "\"consolidate <candidate>\" → conquering-campaign BUILD mode")

    t3 = cls.get("T3", [])
    if t3:
        print("\n%s T3 resolved (%d) — kept so re-mining doesn't re-flag:"
              % (OK, len(t3)))
        for c in t3:
            print("  [%s] %s" % (c["id"], c["evidence"]))

    prio = _registry_priority()
    if prio:
        print("\n%s Registry priority order (CONSOLIDATION-CANDIDATES.md):" % ASK)
        for ln in prio:
            print("  " + ln)

    print("=" * 60)


def cmd_extract():
    """DRY-RUN codemod for C1 (PANEL_WIDTH → PORTAL_SIDEBAR_WIDTH).

    Prints the exact per-file change it WOULD make. Touches disk only with
    --apply AND only when the target line byte-matches the expected pattern."""
    apply = "--apply" in sys.argv[2:]

    files = _grep_files(C1_LOCAL_DECL, WEB)
    print("consolidate_code.py extract — candidate C1 "
          "(%s → import %s)" % (C1_LOCAL_DECL, C1_CANONICAL))
    print("  %s %d file(s) copy-declare the literal." %
          (FLAG if files else OK, len(files)))

    print("\n  " + "!" * 56)
    print("  WARNING: this codemod handles ONLY C1 — the single safest")
    print("  mechanical case (one literal, one canonical home). Functions,")
    print("  DB views, and RLS predicates must go through a conquering-campaign")
    print("  with a byte-compare. This script NEVER auto-merges those.")
    print("  " + "!" * 56 + "\n")

    if not files:
        print("  Nothing to do.")
        return

    expected = "  " + C1_LOCAL_DECL  # 2-space indent guard for byte-match
    for rel in files:
        print("  [%s] %s" % (ASK, rel))
        print("    - remove local decl:  %s" % C1_LOCAL_DECL)
        print("    + add import:         import { %s } from "
              "'@/components/portal'" % C1_CANONICAL)
        print("    + rewrite usages:     PANEL_WIDTH → %s" % C1_CANONICAL)

    if not apply:
        print("\n  DRY-RUN. Re-run with --apply to write changes (byte-matched "
              "lines only).")
        return

    # ── --apply path ──
    # Byte-identical merges only: this script is deliberately conservative. The
    # PANEL_WIDTH codemod also has to rewrite N usage sites + insert an import
    # without colliding with existing imports — that is exactly the kind of
    # non-trivial rewrite §L4 warns about. Defer to a campaign.
    print("\n  %s --apply is not implemented — use a conquering-campaign." % FLAG)
    print("  Rationale: removing the decl is byte-safe, but rewriting every")
    print("  PANEL_WIDTH usage + inserting a non-colliding import is a")
    print("  multi-edit rewrite that must be byte-compared per file. Run the")
    print("  C1 codemod inside a campaign (BUILD mode), not from this scanner.")


# ── main ───────────────────────────────────────────────────────────────────

COMMANDS = {
    "scan": cmd_scan,
    "classify": cmd_classify,
    "surface": cmd_surface,
    "extract": cmd_extract,
}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print("Usage: python3 consolidate_code.py <%s>" % "|".join(COMMANDS))
        print(__doc__)
        sys.exit(1)
    COMMANDS[sys.argv[1]]()
