#!/usr/bin/env python3
"""
followups_cleanup.py — post-campaign follow-up sweeper for the /cleanup skill.

Automates the MECHANICAL parts of the post-campaign follow-up sweep
(locate → extract → classify → mark). The actual EXECUTION of doable items is
performed by Claude, NOT this script — so it stops at `classify` and hands
Claude the doable list.

Subcommands:
  locate    Find the campaign to sweep. Scans DOCS/audit-campaigns/*/ and
            DOCS/build-campaigns/*/ for 00-campaign-plan.md with frontmatter
            status: completed; picks the most-recently-modified one not yet
            swept (marker /tmp/last_followup_sweep_marker). Optional arg forces
            one: `locate <campaign-dir-name>`. Writes /tmp/followup_campaign.txt.
  extract   Read the located campaign's 99-synthesis.md / 99-risk-sweep.md +
            00-campaign-plan.md; pull deferred items (bullets under Open-items /
            Follow-ups / Cleanup headings + inline marker sentences), de-dupe.
            Writes /tmp/followup_items.json.
  classify  Bucket each item: doable-autonomously / needs-user-hands /
            accepted-permanent-exception (uncertain → needs-user-hands;
            environmental/prod-vs-repo → accepted, overriding the verb heuristic
            — R13/L37). Writes /tmp/followup_classified.json + prints the doable list.
  parity    [R13/L34] Per-locale key-PRESENCE count for a namespace subtree
            (parity <ns> [dotted.subtree]); flags locales where the subtree is
            ABSENT (raw MISSING_MESSAGE, invisible to `language detect`). exit 2
            if any locale is absent.
  orphan-index  [R13/L36] Vault-logs present on disk but missing from
            vault-logs/INDEX.md; scopes to the located campaign's own log (per
            L27) and emits the INDEX row template. Never edits INDEX.md.
  mark      Stamp /tmp/last_followup_sweep_marker so the next locate starts
            after this sweep.

Missing 99-* files are handled (build → 99-risk-sweep only; audit → 99-synthesis
only). No completed campaign → "nothing to sweep" + exit 0.
"""

import json
import sys
import os
import re
from collections import defaultdict
from datetime import datetime, timezone
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
DOCS = os.path.join(LEX_ROOT, "docs")
CAMPAIGN_ROOTS = [
    os.path.join(DOCS, "audit-campaigns"),
    os.path.join(DOCS, "build-campaigns"),
]

CAMPAIGN_FILE   = "/tmp/followup_campaign.txt"
ITEMS_FILE      = "/tmp/followup_items.json"
CLASSIFIED_FILE = "/tmp/followup_classified.json"
MARKER_FILE     = "/tmp/last_followup_sweep_marker"

PLAN_NAME    = "00-campaign-plan.md"
CLOSING_ARTIFACTS = ["99-synthesis.md", "99-risk-sweep.md"]

# Heading phrases that introduce a deferred-work list (matched case-insensitively
# as a SUBSTRING of the heading text — real headings vary: "Open items / follow-ups",
# "## 8. Open items — explicit deferrals", "Code Cleanup Checklist (separate PR)").
SECTION_HEADINGS = ("open items", "code cleanup checklist", "follow-up", "follow-ups")

# Inline marker phrases — a sentence/line containing one is a candidate item.
INLINE_MARKERS = (
    "follow-up", "spawn_task", "future cleanup", "deferred to",
    "atta to dispatch", "needs-hands", "needs hands",
)

# ── classification keyword rules ─────────────────────────────────────────────

# accepted-permanent-exception wins first — explicit "we are not doing this".
EXCEPTION_KW = (
    "leave as-is", "leave as is", "leave it as-is", "won't fix", "wont fix",
    "accepted", "intentional", "by design", "not a bug", "no regression",
    "acceptable",
)
# R13/L37 — environmental steady-state: the resolution lives OUTSIDE this session's
# reach (prod-vs-repo drift, the apply-via-MCP migration ledger, a concurrent actor's
# tree). The verb heuristic mis-tags these "doable" because they contain
# "migration" / "verify" — this guard runs BEFORE the doable check and overrides it.
# Source: 2026-06-04 doc-version-merge followups (FU-002 was wrongly tagged doable);
# memory discovery_supabase-migrations-applied-via-mcp-not-pipeline.
ENVIRONMENTAL_KW = (
    "migration ledger", "prod migration", "ledger diverge", "diverges from",
    "apply-via-mcp", "apply via mcp", "applied to prod", "already on prod",
    "prod-vs-repo", "prod vs repo", "steady-state", "steady state",
    "concurrent actor", "concurrent session", "belongs to other",
    "belongs to another", "other workstream",
)
# needs-user-hands — reachable only outside the repo / dangerous to auto-do.
HANDS_KW = (
    "supabase dashboard", "dashboard", "delete edge function", "edge function",
    "external service", "third-party", "third party", "nas", "cron job", "cron",
    "[!atta]", "signed-out", "signed out", "unauthenticated", "os-level",
    "os level", "visual", "screenshot", "preview", "browser", "manual",
    "atta to dispatch", "for atta", "awaits atta", "ask atta", "ask the user",
)
# doable-autonomously — reachable from Bash / MCP inside the repo.
DOABLE_KW = (
    "code edit", "grep", "frontmatter", "git rm", "rls", "execute_sql",
    "apply_migration", "migration", "delete the file", "delete file",
    "remove the file", "drop column", "drop the", "rename", "verify",
    "verification query", "doc sync", "stale", "dedup", "consolidat",
    "import", "type ", "view def", "constraint", "hygiene pr", "separate pr",
)


# ── helpers ──────────────────────────────────────────────────────────────────

def read_frontmatter(path):
    """Return the frontmatter block (between the first two '---' fences) as a
    list of lines, or [] if there is no leading frontmatter."""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.read().splitlines()
    except OSError:
        return []
    if not lines or lines[0].strip() != "---":
        return []
    out = []
    for ln in lines[1:]:
        if ln.strip() == "---":
            return out
        out.append(ln)
    return []  # unterminated frontmatter → treat as none


def is_completed(plan_path):
    """True if the plan's frontmatter status starts with 'complete'.

    Reads ONLY the frontmatter block, so decoy body lines like
    'status: complete|partial|blocked' or 'status: planning' in template
    examples are ignored."""
    for ln in read_frontmatter(plan_path):
        m = re.match(r"\s*status\s*:\s*(.+)", ln, re.IGNORECASE)
        if m:
            return m.group(1).strip().lower().startswith("complete")
    return False


def completed_campaigns():
    """Return list of (campaign_dir, plan_path, mtime) for every campaign whose
    00-campaign-plan.md frontmatter is status: completed."""
    found = []
    for root in CAMPAIGN_ROOTS:
        if not os.path.isdir(root):
            continue
        for name in os.listdir(root):
            cdir = os.path.join(root, name)
            plan = os.path.join(cdir, PLAN_NAME)
            if os.path.isdir(cdir) and os.path.isfile(plan) and is_completed(plan):
                found.append((cdir, plan, os.path.getmtime(cdir)))
    return found


def swept_marker_mtime():
    """mtime of the sweep marker, or None if it doesn't exist."""
    return os.path.getmtime(MARKER_FILE) if os.path.exists(MARKER_FILE) else None


def split_sentences(line):
    """Cheap sentence split on '. ' boundaries — good enough for marker capture."""
    parts = re.split(r"(?<=[.!?])\s+", line.strip())
    return [p.strip() for p in parts if p.strip()]


def norm(text):
    """Normalise a description for de-dupe: lowercase, collapse whitespace,
    strip leading markdown bullets / numbering / emphasis markers."""
    t = text.lower().strip()
    t = re.sub(r"^[-*\d.\)\s]+", "", t)      # bullet / number prefix
    t = re.sub(r"[`*_\[\]]", "", t)           # md emphasis / link syntax
    t = re.sub(r"\s+", " ", t)
    return t[:140]


# ── subcommands ──────────────────────────────────────────────────────────────

def cmd_locate():
    """Find the campaign to sweep and write its path to CAMPAIGN_FILE."""
    forced = sys.argv[2] if len(sys.argv) > 2 else None

    if forced:
        for root in CAMPAIGN_ROOTS:
            cdir = os.path.join(root, forced)
            if os.path.isdir(cdir):
                with open(CAMPAIGN_FILE, "w") as f:
                    f.write(cdir + "\n")
                print(f"✓ Forced campaign: {forced}")
                print(f"  → {cdir}")
                print(f"  Wrote → {CAMPAIGN_FILE}")
                return cdir
        print(f"🚩 Forced campaign '{forced}' not found under audit/build roots.")
        sys.exit(1)

    completed = completed_campaigns()
    if not completed:
        print("✓ Nothing to sweep — no completed campaign found.")
        sys.exit(0)

    marker_mtime = swept_marker_mtime()
    if marker_mtime is not None:
        # Only consider campaigns modified AFTER the last sweep.
        candidates = [c for c in completed if c[2] > marker_mtime]
        if not candidates:
            print("✓ Nothing to sweep — all completed campaigns already swept "
                  f"(marker: {datetime.fromtimestamp(marker_mtime).isoformat(timespec='seconds')}).")
            sys.exit(0)
    else:
        candidates = completed

    # Most-recently-modified candidate wins.
    cdir, _plan, mtime = max(candidates, key=lambda c: c[2])
    with open(CAMPAIGN_FILE, "w") as f:
        f.write(cdir + "\n")

    print(f"✓ Campaign to sweep: {os.path.basename(cdir)}")
    print(f"  mtime  : {datetime.fromtimestamp(mtime).isoformat(timespec='seconds')}")
    print(f"  path   : {cdir}")
    print(f"  ({len(candidates)} unswept completed campaign(s) considered)")
    print(f"  Wrote → {CAMPAIGN_FILE}")
    return cdir


def _extract_from_file(path):
    """Pull candidate follow-up items from one markdown file.

    Two passes:
      (a) bullet/numbered lines under a heading whose text contains a
          SECTION_HEADINGS phrase, until the next same-or-higher heading;
      (b) any line/sentence anywhere containing an INLINE_MARKER phrase.
    """
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.read().splitlines()
    except OSError:
        return []

    src = os.path.basename(path)
    items = []

    # ── pass (a): section bullets ──
    in_section = False
    section_level = 0
    for ln in lines:
        hm = re.match(r"^(#{1,6})\s+(.*)$", ln)
        if hm:
            level = len(hm.group(1))
            title = hm.group(2).strip().lower()
            if any(p in title for p in SECTION_HEADINGS):
                in_section, section_level = True, level
                continue
            # Any heading at same-or-higher level closes the section.
            if in_section and level <= section_level:
                in_section = False
            continue
        if in_section:
            bm = re.match(r"^\s*(?:[-*]|\d+[.)])\s+(.+)$", ln)
            if bm:
                desc = bm.group(1).strip()
                if len(desc) >= 8:
                    items.append({"surface": "section", "description": desc,
                                  "source_file": src})

    # ── pass (b): inline markers ──
    for ln in lines:
        low = ln.lower()
        if not any(m in low for m in INLINE_MARKERS):
            continue
        if re.match(r"^(#{1,6})\s", ln):     # skip headings themselves
            continue
        for sent in split_sentences(ln):
            sl = sent.lower()
            if any(m in sl for m in INLINE_MARKERS) and len(sent) >= 12:
                items.append({"surface": "inline", "description": sent,
                              "source_file": src})
    return items


def cmd_extract():
    """Extract deferred follow-up items from the located campaign."""
    if not os.path.exists(CAMPAIGN_FILE):
        print(f"🚩 {CAMPAIGN_FILE} not found. Run locate first.")
        sys.exit(1)
    cdir = open(CAMPAIGN_FILE).read().strip()
    if not os.path.isdir(cdir):
        print(f"🚩 Campaign dir gone: {cdir}")
        sys.exit(1)

    targets = []
    for name in CLOSING_ARTIFACTS + [PLAN_NAME]:
        p = os.path.join(cdir, name)
        if os.path.isfile(p):
            targets.append(p)
    if not targets:
        print(f"🚩 No closing artifacts or plan found in {os.path.basename(cdir)}.")
        sys.exit(1)

    print(f"followups_cleanup.py extract — {os.path.basename(cdir)}")
    raw = []
    for p in targets:
        hits = _extract_from_file(p)
        print(f"  {os.path.basename(p):<22} → {len(hits)} candidate line(s)")
        raw.extend(hits)

    # De-dupe near-identical descriptions, assign ids.
    seen, items = {}, []
    for it in raw:
        key = norm(it["description"])
        if not key or key in seen:
            continue
        seen[key] = True
        items.append({
            "id": f"FU-{len(items) + 1:03d}",
            "surface": it["surface"],
            "description": it["description"],
            "source_file": it["source_file"],
        })

    with open(ITEMS_FILE, "w") as f:
        json.dump(items, f, indent=2)
    print(f"  {len(items)} unique follow-up item(s) after de-dupe")
    print(f"  Wrote → {ITEMS_FILE}")
    return items


def _classify_one(desc):
    """Heuristic bucket for a single description. Default → needs-user-hands
    (misclassifying a hands-item as doable risks unauthorized action)."""
    low = desc.lower()
    if any(k in low for k in EXCEPTION_KW):
        return "accepted-permanent-exception"
    if any(k in low for k in ENVIRONMENTAL_KW):    # R13/L37 — override the verb heuristic
        return "accepted-permanent-exception"
    hands = any(k in low for k in HANDS_KW)
    doable = any(k in low for k in DOABLE_KW)
    if doable and not hands:
        return "doable-autonomously"
    if hands:
        return "needs-user-hands"
    return "needs-user-hands"   # uncertain → safest bucket


def cmd_classify():
    """Classify extracted items and print the doable list."""
    if not os.path.exists(ITEMS_FILE):
        print(f"🚩 {ITEMS_FILE} not found. Run extract first.")
        sys.exit(1)
    items = json.load(open(ITEMS_FILE))

    counts = defaultdict(int)
    for it in items:
        it["klass"] = _classify_one(it["description"])
        counts[it["klass"]] += 1

    with open(CLASSIFIED_FILE, "w") as f:
        json.dump(items, f, indent=2)

    print("\nClassification summary:")
    for klass in ("doable-autonomously", "needs-user-hands",
                  "accepted-permanent-exception"):
        marker = "✓" if klass == "doable-autonomously" else (
            "?" if klass == "needs-user-hands" else "🚩")
        print(f"  {marker} {klass:<30}: {counts.get(klass, 0)}")

    doable = [it for it in items if it["klass"] == "doable-autonomously"]
    print(f"\n✓ DOABLE — Claude executes these next ({len(doable)}):")
    if not doable:
        print("  (none — nothing autonomously actionable this sweep)")
    for it in doable:
        print(f"  [{it['id']}] ({it['source_file']}) {it['description'][:110]}")

    hands = [it for it in items if it["klass"] == "needs-user-hands"]
    if hands:
        print(f"\n? NEEDS-USER-HANDS — surface to Atta ({len(hands)}):")
        for it in hands[:10]:
            print(f"  [{it['id']}] {it['description'][:100]}")
        if len(hands) > 10:
            print(f"  … +{len(hands) - 10} more")

    print(f"\n  Wrote → {CLASSIFIED_FILE}")
    return items


# ── R13/L34 — per-locale key-PRESENCE parity ─────────────────────────────────

MSG_ROOT = os.path.join(LEX_ROOT, "apps", "web", "public", "messages")
ALL_LOCALES = ["en", "ar", "es", "fr", "ru", "zh"]


def _count_leaves(node):
    """Count string leaves under a JSON node (a namespace subtree)."""
    if isinstance(node, str):
        return 1
    if isinstance(node, dict):
        return sum(_count_leaves(v) for v in node.values())
    return 0


def cmd_parity():
    """L34 — per-locale key-PRESENCE count for a namespace subtree. Flags locales
    where the subtree is ABSENT (renders raw MISSING_MESSAGE, worse than English,
    and INVISIBLE to `language detect` which only sees present-but-equal-to-EN).
    A campaign that hand-adds keys to only some locales is the recurring cause.

    Usage: parity <ns> [dotted.subtree]
      e.g. parity admin containers.document.merge
    """
    if len(sys.argv) < 3:
        print("Usage: python3 followups_cleanup.py parity <ns> [dotted.subtree]")
        sys.exit(1)
    ns = sys.argv[2]
    sub = sys.argv[3] if len(sys.argv) > 3 else None
    counts = {}
    for loc in ALL_LOCALES:
        fp = os.path.join(MSG_ROOT, loc, f"{ns}.json")
        if not os.path.isfile(fp):
            counts[loc] = -1
            continue
        try:
            node = json.load(open(fp, encoding="utf-8"))
            ok = True
            if sub:
                for p in sub.split("."):
                    if isinstance(node, dict) and p in node:
                        node = node[p]
                    else:
                        ok = False
                        break
            counts[loc] = _count_leaves(node) if ok else 0
        except Exception:
            counts[loc] = -1
    base = counts.get("en", 0)
    label = ns + (f" / {sub}" if sub else "")
    print(f"locale parity — {label}:")
    absent = []
    for loc in ALL_LOCALES:
        c = counts[loc]
        if c == -1:
            tag = "  (file missing)"
        elif c == 0 and base > 0:
            tag = "  ← ABSENT (raw MISSING_MESSAGE — propagate EN values first)"
            absent.append(loc)
        elif base and c != base:
            tag = f"  (≠ en {base} — translation gap, run `language`)"
        else:
            tag = ""
        print(f"  {loc}: {c}{tag}")
    if absent:
        print(f"\n!! {len(absent)} locale(s) ABSENT: {', '.join(absent)} — "
              f"propagate the EN subtree into them, THEN run the `language` mode on {ns}.")
        sys.exit(2)
    print("\n✓ all locales present (any count diff is a translation gap, not absence).")


# ── R13/L36 — predecessor orphan-INDEX detector ──────────────────────────────

def cmd_orphan_index():
    """L36 — vault-log files present on disk but absent from vault-logs/INDEX.md.
    Campaigns reliably forget the INDEX row; the followups `docs` check is the
    backstop. Scopes to the LOCATED campaign's own log(s) (per L27 — other
    sessions' orphans are flagged but left for their owners). Detect + emit the
    INDEX row template; Claude writes it (this script never edits INDEX.md)."""
    vl_dir = os.path.join(DOCS, "vault-logs")
    index = os.path.join(vl_dir, "INDEX.md")
    if not os.path.isdir(vl_dir) or not os.path.isfile(index):
        print(f"🚩 vault-logs dir or INDEX.md missing under {DOCS}")
        sys.exit(1)
    refs = set(re.findall(r"\[\[([0-9]{4}-[0-9]{2}-[0-9]{2}_[^\]]+?)\]\]",
                          open(index, encoding="utf-8").read()))
    files = [f[:-3] for f in os.listdir(vl_dir)
             if re.match(r"^\d{4}-\d{2}-\d{2}_", f) and f.endswith(".md") and " " not in f]
    orphans = sorted(f for f in files if f not in refs)

    # Scope hint: the located campaign's topic (so we surface YOURS, not the sea of others).
    topic = None
    if os.path.exists(CAMPAIGN_FILE):
        base = os.path.basename(open(CAMPAIGN_FILE).read().strip())
        m = re.match(r"\d{4}-\d{2}-\d{2}_(.+)", base)
        if m:
            topic = m.group(1)
    mine = [o for o in orphans if topic and topic in o]
    others = [o for o in orphans if o not in mine]

    if not orphans:
        print("✓ no orphan vault-logs — INDEX.md is complete.")
        return
    if mine:
        print(f"!! predecessor orphan(s) — ADD to INDEX.md (this is YOURS):")
        for o in mine:
            print(f"   | {o[:10]} | [[{o}]] | <one-line summary> |")
    if others:
        print(f"\n? {len(others)} other orphan(s) — flagged by `docs`; per L27 leave for their owners:")
        for o in others[:15]:
            print(f"   [[{o}]]")
        if len(others) > 15:
            print(f"   … +{len(others) - 15} more (historical backlog — a `docs`/audit job, not this sweep)")
    if not mine and topic:
        print(f"\n✓ the located campaign ('{topic}') is indexed — no predecessor orphan to fix.")


def cmd_mark():
    """Record this sweep so the next locate starts after it."""
    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    swept = "(unknown)"
    if os.path.exists(CAMPAIGN_FILE):
        swept = os.path.basename(open(CAMPAIGN_FILE).read().strip()) or swept
    with open(MARKER_FILE, "w") as f:
        f.write(f"{stamp}\nswept: {swept}\n")
    print(f"✓ Marked sweep complete.")
    print(f"  timestamp : {stamp}")
    print(f"  swept     : {swept}")
    print(f"  Wrote → {MARKER_FILE}")


# ── main ─────────────────────────────────────────────────────────────────────

COMMANDS = {
    "locate": cmd_locate,
    "extract": cmd_extract,
    "classify": cmd_classify,
    "parity": cmd_parity,
    "orphan-index": cmd_orphan_index,
    "mark": cmd_mark,
}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print(f"Usage: python3 followups_cleanup.py <{'|'.join(COMMANDS)}> [campaign-dir-name]")
        print(__doc__)
        sys.exit(1)
    COMMANDS[sys.argv[1]]()
