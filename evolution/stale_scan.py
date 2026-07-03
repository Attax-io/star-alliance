#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────────────────
# Star Alliance — STALE-MENTION SCANNER  (SENSE organ for doctrinal drift)
#
# The evolution engine already catches regression escapes, dead skills, and
# cost trends. But it was blind to a whole class of rot: stale mentions of
# removed or renamed concepts lingering in docs, tooling, and member files.
# The 2026-07-03 audit found "triple-seat", "Critic seat", and
# "Brain/Doer/Critic/Bench" scattered across the repo months after the Critic
# seat was removed. This scanner prevents that class of drift.
#
# It reads evolution/stale_registry.json — a hand-curated list of concepts that
# were removed or renamed — scans the repo for stale mentions, and either
# reports them (default) or removes them (--apply, Tier-A for docs/tooling,
# human-gated for doctrine).
#
# SAFETY:
#   • SHADOW IS DEFAULT. With no flags the scanner reports hits, changes nothing.
#   • --apply removes the stale text. Tier-A surfaces (docs, tooling, members)
#     are auto-applied; Tier-B surfaces (doctrine: CLAUDE.md, AGENTS.md) are
#     gated — the scanner reports them and waits for a human go.
#   • DISARMED kill switch respected (same as the rest of the engine).
#   • Every scan + apply is ledgered so the scoreboard can track drift over time.
#
# Usage:
#   python3 evolution/stale_scan.py            # report stale mentions (shadow)
#   python3 evolution/stale_scan.py --apply    # remove Tier-A, report Tier-B
#   python3 evolution/stale_scan.py --json     # machine-readable output
# ─────────────────────────────────────────────────────────────────────────────
from __future__ import annotations

import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
DISARMED = os.path.join(HERE, "DISARMED")
REGISTRY = os.path.join(HERE, "stale_registry.json")

sys.path.insert(0, HERE)
import ledger  # noqa: E402

# Tier-B surfaces — load-bearing doctrine files that always need a human go.
TIER_B_FILES = {"CLAUDE.md", "AGENTS.md"}

# File extensions to scan (text files only).
SCAN_EXTENSIONS = {".md", ".py", ".js", ".json", ".yaml", ".yml", ".sh", ".cjs", ".ts", ".tsx"}

# Directories to skip (noise, archives, generated data, git).
SKIP_DIRS = {".git", "__pycache__", "node_modules", "evolution/archive", "evolution/proposals",
             ".claude/state", "data"}

# Files to skip (the scanner and registry themselves contain the patterns by design).
SKIP_FILES = {"stale_scan.py", "stale_registry.json"}


def is_disarmed() -> bool:
    return os.path.exists(DISARMED)


def load_registry() -> list[dict]:
    """Load the stale-concept registry. Returns list of entry dicts."""
    try:
        with open(REGISTRY, encoding="utf-8") as fh:
            data = json.load(fh)
        return data.get("entries", [])
    except Exception:
        return []


def _should_scan(path: str) -> bool:
    """True if this file should be scanned (text file, not in a skip dir, not itself)."""
    _, ext = os.path.splitext(path)
    if ext.lower() not in SCAN_EXTENSIONS:
        return False
    # Check skip dirs in the relative path.
    rel = os.path.relpath(path, REPO)
    parts = rel.split(os.sep)
    for skip in SKIP_DIRS:
        if skip in parts:
            return False
    # Skip the scanner and registry themselves.
    if os.path.basename(path) in SKIP_FILES:
        return False
    return True


def _tier_for(path: str) -> str:
    """A (auto-apply) or B (human-gated). Doctrine files are always Tier-B."""
    name = os.path.basename(path)
    if name in TIER_B_FILES:
        return "B"
    return "A"


def scan() -> list[dict]:
    """Scan the repo for stale mentions. Returns list of hit dicts:
    {entry_id, file, line, line_no, matched_text, replaced_by, tier, surface}."""
    entries = load_registry()
    if not entries:
        return []

    # Build compiled patterns.
    patterns = []
    for e in entries:
        try:
            patterns.append((e, re.compile(e["pattern"], re.IGNORECASE)))
        except re.error:
            continue

    hits: list[dict] = []
    for root, dirs, files in os.walk(REPO):
        # Prune skip dirs in-place.
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for fname in files:
            fpath = os.path.join(root, fname)
            if not _should_scan(fpath):
                continue
            try:
                with open(fpath, encoding="utf-8", errors="replace") as fh:
                    lines = fh.readlines()
            except Exception:
                continue
            for i, line in enumerate(lines, 1):
                for entry, pat in patterns:
                    m = pat.search(line)
                    if m:
                        hits.append({
                            "entry_id": entry["id"],
                            "file": os.path.relpath(fpath, REPO),
                            "line_no": i,
                            "matched_text": m.group(0),
                            "replaced_by": entry.get("replaced_by"),
                            "tier": _tier_for(fpath),
                            "surface": entry.get("surface", "docs"),
                            "note": entry.get("note", ""),
                        })
    return hits


def apply(hits: list[dict]) -> dict:
    """Remove stale mentions. Tier-A hits are auto-applied; Tier-B hits are
    reported only (human-gated). Returns {applied, gated, details}."""
    disarmed = is_disarmed()
    applied = []
    gated = []

    if disarmed:
        for h in hits:
            h["action"] = "skipped — engine DISARMED"
        return {"applied": [], "gated": hits, "disarmed": True}

    # Group by file for efficient patching.
    by_file: dict[str, list[dict]] = {}
    for h in hits:
        by_file.setdefault(h["file"], []).append(h)

    for fpath, file_hits in by_file.items():
        abs_path = os.path.join(REPO, fpath)
        tier = file_hits[0]["tier"]
        if tier == "B":
            gated.extend(file_hits)
            continue

        # Tier-A: auto-apply.
        try:
            with open(abs_path, encoding="utf-8") as fh:
                content = fh.read()
        except Exception:
            continue

        original = content
        for h in file_hits:
            entry = next((e for e in load_registry() if e["id"] == h["entry_id"]), None)
            if entry:
                pat = re.compile(entry["pattern"], re.IGNORECASE)
                if entry.get("replaced_by"):
                    content = pat.sub(entry["replaced_by"], content)
                else:
                    # No replacement — remove the matched text (replace with empty).
                    content = pat.sub("", content)

        if content != original:
            with open(abs_path, "w", encoding="utf-8") as fh:
                fh.write(content)
            for h in file_hits:
                h["action"] = "removed"
                applied.append(h)

    return {"applied": applied, "gated": gated, "disarmed": False}


def run(apply_mode: bool = False) -> dict:
    """Scan + optionally apply. Ledgers the result for scoreboard tracking."""
    hits = scan()

    ledger.append(
        "metric", author="stale-scanner", surface="evolution",
        detail=f"stale-mention scan: {len(hits)} hit(s) found",
        meta={"signal": "stale-mention", "count": len(hits),
              "hit_files": list({h["file"] for h in hits})})

    if apply_mode and hits:
        result = apply(hits)
        if result["applied"]:
            ledger.append(
                "change", author="stale-scanner", surface="evolution",
                detail=f"removed {len(result['applied'])} stale mention(s) (Tier-A auto-apply)",
                meta={"signal": "stale-mention", "applied": len(result["applied"]),
                      "gated": len(result["gated"])})
        return {
            "hits": hits,
            "applied": result["applied"],
            "gated": result["gated"],
            "disarmed": result.get("disarmed", False),
        }

    return {"hits": hits, "applied": [], "gated": [h for h in hits if h["tier"] == "B"]}


def _cli():
    import argparse
    ap = argparse.ArgumentParser(prog="stale-scan",
                                description="Scan repo for stale mentions of removed/renamed concepts")
    ap.add_argument("--apply", action="store_true",
                    help="remove Tier-A stale mentions (Tier-B still human-gated)")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    a = ap.parse_args()

    r = run(apply_mode=a.apply)
    hits = r["hits"]

    if a.json:
        print(json.dumps(r, ensure_ascii=False, indent=2))
        return

    if not hits:
        print("── Stale-Mention Scanner ──\n  ✓ no stale mentions found")
        return

    tier_a = [h for h in hits if h["tier"] == "A"]
    tier_b = [h for h in hits if h["tier"] == "B"]

    print("── Stale-Mention Scanner ──")
    print(f"  {len(hits)} stale mention(s) found ({len(tier_a)} Tier-A, {len(tier_b)} Tier-B)")

    if tier_a:
        print("\n  ▸ Tier-A (auto-removable):")
        for h in tier_a:
            status = "✓ removed" if h.get("action") == "removed" else "  found"
            print(f"     {status}  {h['file']}:{h['line_no']}  '{h['matched_text']}'"
                  f"  → {h['replaced_by'] or '(removed)'}")

    if tier_b:
        print("\n  ⛔ Tier-B (needs your GO — doctrine files):")
        for h in tier_b:
            print(f"     {h['file']}:{h['line_no']}  '{h['matched_text']}'"
                  f"  → {h['replaced_by'] or '(removed)'}")

    if r.get("applied"):
        print(f"\n  ✓ {len(r['applied'])} stale mention(s) removed (Tier-A auto-apply)")
    elif a.apply and tier_b:
        print(f"\n  ⛔ {len(tier_b)} stale mention(s) in doctrine files — review and remove manually")
    elif not a.apply:
        print("\n  (run with --apply to remove Tier-A hits)")


if __name__ == "__main__":
    _cli()