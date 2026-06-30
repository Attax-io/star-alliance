#!/usr/bin/env python3
"""
watermark.py — per-mode "what changed since I last looked" cursor for the
`docs` and `manual` cleanup modes.

Both modes used to re-flag the same baseline (broken wikilinks, stale hub dates,
unmapped manual Parts) every rotation because they had no memory of their last
pass. This script gives each mode a small state file recording when it last ran
and the newest vault-log it had seen. Every run diffs the vault-logs added since
that watermark, so the mode acts on *new* feature activity instead of nagging
about the same old baseline — and escalates to a full audit campaign when enough
has shipped.

State files (workspace `.claude/`):
  cleanup-docs-state.json    — { "last_pass_date": ISO, "last_seen_vault_log": "<filename>" }
  cleanup-manual-state.json  — same shape

Vault-logs live at  lex_council/docs/vault-logs/YYYY-MM-DD_*.md  — the date prefix
makes lexicographic filename order == chronological order, so "since the
watermark" is just `filename > last_seen_vault_log`.

Subcommands:
  status  <docs|manual>          Print watermark + vault-logs added since + whether
                                 the escalation threshold is crossed. JSON with --json.
  since   <docs|manual>          Print just the new vault-log filenames (one per line).
  advance <docs|manual> [--noop] Stamp last_pass_date=now (UTC) and
                                 last_seen_vault_log=newest vault-log. With --noop,
                                 only the seen-log is advanced (the pass did no work)
                                 — keeps the date of the last REAL pass.

Escalation: when the number of vault-logs since the watermark is >= --threshold
(default 3), `status` prints an ESCALATE line recommending a
`/conquering-campaign` AUDIT for that surface. The recipe decides whether to
spawn_task it; this script only signals.

Exit code of `status`: 0 normally, 10 when the escalation threshold is crossed
(so a recipe/shell can branch on it without parsing).
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# Vault-log filenames come in two date formats — dashed `YYYY-MM-DD_*` and
# bare `YYYYMMDD_*`. Raw string sort interleaves them wrong (`-` < digit), so we
# normalize the leading date to YYYYMMDD for ordering. Files with no parseable
# date sort first (treated as oldest) by their name.
_DATE_RE = re.compile(r"^(\d{4})-?(\d{2})-?(\d{2})")


def _log_key(name):
    m = _DATE_RE.match(name)
    norm = (m.group(1) + m.group(2) + m.group(3)) if m else "0000_" + name
    return (norm, name)

MODES = ("docs", "manual")
DEFAULT_THRESHOLD = 3
STATE_FILE = {
    "docs": "cleanup-docs-state.json",
    "manual": "cleanup-manual-state.json",
}


# ── path detection (mirrors rotate.py) ───────────────────────────────────────

def workspace_root():
    """The dir holding BOTH `.claude/` and the `lex_council/` submodule."""
    starts = [Path(__file__).resolve().parent, Path.cwd().resolve()]
    seen = set()
    for start in starts:
        for parent in [start, *start.parents]:
            if parent in seen:
                continue
            seen.add(parent)
            if (parent / ".claude").is_dir() and (parent / "lex_council").is_dir():
                return parent
    # Fallback to this device's layout.
    return Path(os.path.expanduser(
        "~/Documents/Claude/Projects/Lex Council App"))


def state_path(root, mode):
    return root / ".claude" / STATE_FILE[mode]


def vault_logs_dir(root):
    return root / "lex_council" / "docs" / "vault-logs"


# ── io ───────────────────────────────────────────────────────────────────────

def load_state(path):
    try:
        with open(path) as f:
            data = json.load(f)
    except FileNotFoundError:
        return {"last_pass_date": None, "last_seen_vault_log": None}
    except Exception as e:
        sys.exit(f"watermark.py: state unreadable at {path}: {e}")
    data.setdefault("last_pass_date", None)
    data.setdefault("last_seen_vault_log", None)
    return data


def save_state(path, data):
    tmp = Path(str(path) + ".tmp")
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")
    os.replace(tmp, path)


def list_vault_logs(root):
    """Sorted list of vault-log .md filenames (chronological via date prefix)."""
    d = vault_logs_dir(root)
    if not d.is_dir():
        return []
    names = [p.name for p in d.glob("*.md")
             if p.name.lower() not in ("index.md", "readme.md")]
    return sorted(names, key=_log_key)


def logs_since(root, last_seen):
    logs = list_vault_logs(root)
    if not last_seen:
        return logs
    seen_key = _log_key(last_seen)
    return [n for n in logs if _log_key(n) > seen_key]


# ── subcommands ──────────────────────────────────────────────────────────────

def cmd_status(args):
    root = workspace_root()
    st = load_state(state_path(root, args.mode))
    new = logs_since(root, st["last_seen_vault_log"])
    escalate = len(new) >= args.threshold
    if args.json:
        print(json.dumps({
            "mode": args.mode,
            "last_pass_date": st["last_pass_date"],
            "last_seen_vault_log": st["last_seen_vault_log"],
            "vault_logs_since": new,
            "count_since": len(new),
            "threshold": args.threshold,
            "escalate": escalate,
        }, indent=2))
    else:
        print(f"mode:            {args.mode}")
        print(f"last pass:       {st['last_pass_date'] or '(never)'}")
        print(f"last seen log:   {st['last_seen_vault_log'] or '(none)'}")
        print(f"vault-logs since:{len(new)} (threshold {args.threshold})")
        for n in new[:20]:
            print(f"   + {n}")
        if len(new) > 20:
            print(f"   … (+{len(new) - 20} more)")
        if escalate:
            print(f"\n🚩 ESCALATE: {len(new)} vault-logs since last {args.mode} "
                  f"pass (≥{args.threshold}). Recommend spawn_task a "
                  f"/conquering-campaign AUDIT for the {args.mode} surface "
                  f"instead of nibbling the baseline.")
        elif not new:
            print(f"\n✓ nothing new since last {args.mode} pass.")
    return 10 if escalate else 0


def cmd_since(args):
    root = workspace_root()
    st = load_state(state_path(root, args.mode))
    for n in logs_since(root, st["last_seen_vault_log"]):
        print(n)
    return 0


def cmd_advance(args):
    root = workspace_root()
    path = state_path(root, args.mode)
    st = load_state(path)
    logs = list_vault_logs(root)
    newest = logs[-1] if logs else st["last_seen_vault_log"]
    st["last_seen_vault_log"] = newest
    if not args.noop:
        st["last_pass_date"] = datetime.now(timezone.utc).isoformat(
            timespec="seconds")
    save_state(path, st)
    kind = "noop" if args.noop else "applied"
    print(f"watermark[{args.mode}] {kind} → seen={newest} "
          f"pass={st['last_pass_date']}")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name, fn in (("status", cmd_status), ("since", cmd_since),
                     ("advance", cmd_advance)):
        p = sub.add_parser(name)
        p.add_argument("mode", choices=MODES)
        p.add_argument("--threshold", type=int, default=DEFAULT_THRESHOLD)
        if name == "advance":
            p.add_argument("--noop", action="store_true")
        p.add_argument("--json", action="store_true")
        p.set_defaults(func=fn)
    args = ap.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
