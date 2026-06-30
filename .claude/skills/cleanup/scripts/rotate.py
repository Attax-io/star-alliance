#!/usr/bin/env python3
"""
rotate.py — rotation driver for the hourly `lex-cleanup-rotation` routine (R15).

The routine runs ONE cleanup mode per hour, then advances a cursor so the next
hour runs the next mode. This script OWNS that cursor so the logic lives in the
skill, not in prose inside a command file. Each scheduled run is a fresh session
with no memory, so the cursor on disk is the only state.

Cursor file (JSON):
  { "order": [<mode>, ...], "next_index": N, "history": [ {mode,applied,ts}, ... ] }

Subcommands:
  next                 Print the mode to run THIS run (order[next_index]). Nothing else.
  advance [--noop]     Log order[next_index] to history (applied=true, or false with
                       --noop), then next_index = (next_index+1) % len(order). Writes back.
  show                 Print the full cursor state (human-readable).
  sync-order           Reconcile order[] with the skill's LIVE modes parsed from SKILL.md:
                       append any newly-LIVE mode (except the non-rotatable ones) to the
                       END of order without disturbing next_index. This is what lets a
                       future `/cleanup` mode auto-join the rotation "from now".

Contract the routine must honor (NOT enforced here — see SKILL.md §Routine):
  - NEVER `git push`. Commit locally only.
  - Exactly ONE mode per run.
  - Full auto-apply (bounded by each mode's own guardrails).

Modes excluded from rotation (never auto-run unattended):
  release  — cuts a real version release; must stay human-driven.
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# Modes that must never enter the unattended rotation.
NON_ROTATABLE = {"release"}

HISTORY_CAP = 50

# Fallback if path detection fails (this device's layout).
FALLBACK_CURSOR = os.path.expanduser(
    "~/Documents/Claude/Projects/Lex Council App/.claude/cleanup-routine-state.json"
)
SKILL_MD = Path(__file__).resolve().parent.parent / "SKILL.md"


# ── path detection ───────────────────────────────────────────────────────────

def default_cursor():
    """Find <workspace>/.claude/cleanup-routine-state.json by walking up from the
    script dir and cwd. The workspace root is the dir that holds BOTH `.claude/`
    and the `lex_council/` submodule."""
    starts = [Path(__file__).resolve().parent, Path.cwd().resolve()]
    seen = set()
    for start in starts:
        for parent in [start, *start.parents]:
            if parent in seen:
                continue
            seen.add(parent)
            direct = parent / ".claude" / "cleanup-routine-state.json"
            if direct.is_file():
                return direct
            if (parent / ".claude").is_dir() and (parent / "lex_council").is_dir():
                return parent / ".claude" / "cleanup-routine-state.json"
    return Path(FALLBACK_CURSOR)


def cursor_path(args):
    return Path(args.cursor) if args.cursor else default_cursor()


# ── cursor io ────────────────────────────────────────────────────────────────

def load(path):
    try:
        with open(path) as f:
            data = json.load(f)
    except FileNotFoundError:
        sys.exit(f"rotate.py: cursor not found at {path} (create it or pass --cursor)")
    except Exception as e:
        sys.exit(f"rotate.py: cursor unreadable at {path}: {e}")
    order = data.get("order")
    if not isinstance(order, list) or not order:
        sys.exit(f"rotate.py: cursor has no non-empty 'order' list ({path})")
    data.setdefault("next_index", 0)
    data.setdefault("history", [])
    # Clamp a stale/out-of-range index instead of crashing.
    data["next_index"] %= len(order)
    return data


def save(path, data):
    data["history"] = data.get("history", [])[-HISTORY_CAP:]
    tmp = Path(str(path) + ".tmp")
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")
    os.replace(tmp, path)


# ── SKILL.md LIVE-mode parse (for sync-order) ────────────────────────────────

LIVE_ROW = re.compile(r"^\|\s*\*\*([a-z][a-z-]*)\*\*\s*\|\s*LIVE\b", re.MULTILINE)


def live_modes():
    try:
        text = SKILL_MD.read_text()
    except Exception:
        return []
    out, seen = [], set()
    for m in LIVE_ROW.finditer(text):
        name = m.group(1)
        if name in NON_ROTATABLE or name in seen:
            continue
        seen.add(name)
        out.append(name)
    return out


# ── subcommands ──────────────────────────────────────────────────────────────

def cmd_next(args):
    data = load(cursor_path(args))
    print(data["order"][data["next_index"]])


def cmd_advance(args):
    path = cursor_path(args)
    data = load(path)
    i = data["next_index"]
    mode = data["order"][i]
    data["history"].append({
        "mode": mode,
        "applied": not args.noop,
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    })
    data["next_index"] = (i + 1) % len(data["order"])
    save(path, data)
    print(f"ran {mode} (applied={not args.noop}) → next: {data['order'][data['next_index']]}")


def cmd_show(args):
    path = cursor_path(args)
    data = load(path)
    i = data["next_index"]
    print(f"cursor: {path}")
    print(f"next spot: {data['order'][i]}  (index {i} of {len(data['order'])})")
    print("order: " + " → ".join(
        f"[{m}]" if j == i else m for j, m in enumerate(data["order"])
    ))
    hist = data.get("history", [])
    if hist:
        print("\nlast runs:")
        for h in hist[-8:]:
            flag = "applied" if h.get("applied") else "no-op"
            print(f"  {h.get('ts','?')}  {h.get('mode','?'):16} {flag}")


def cmd_sync_order(args):
    path = cursor_path(args)
    data = load(path)
    live = live_modes()
    if not live:
        print("rotate.py: could not parse LIVE modes from SKILL.md — order unchanged")
        return
    have = set(data["order"])
    added = [m for m in live if m not in have]
    # Surface (don't auto-remove) modes in the cursor that are no longer LIVE.
    stale = [m for m in data["order"] if m not in set(live)]
    if added:
        data["order"].extend(added)
        save(path, data)
        print(f"added to rotation: {', '.join(added)}")
    else:
        print("rotation already covers every LIVE mode")
    if stale:
        print(f"NOTE: in cursor but not LIVE (left in place, review): {', '.join(stale)}")
    print("order: " + " → ".join(data["order"]))


def main():
    p = argparse.ArgumentParser(description="Hourly cleanup rotation driver (R15).")
    p.add_argument("--cursor", help="path to the cursor JSON (default: auto-detect)")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("next")
    adv = sub.add_parser("advance")
    adv.add_argument("--noop", action="store_true", help="mode applied nothing this run")
    sub.add_parser("show")
    sub.add_parser("sync-order")
    args = p.parse_args()
    {"next": cmd_next, "advance": cmd_advance, "show": cmd_show,
     "sync-order": cmd_sync_order}[args.cmd](args)


if __name__ == "__main__":
    main()
