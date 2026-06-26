#!/usr/bin/env python3
"""member_level.py — the Quartermaster's member-leveling console.

A member's level is a CRAFT-DEPTH meter (arsenal + specialty), EARNED by an
objective checklist computed in build.py and CONFERRED by the Quartermaster.
This tool is how he confers it: it reads the build-derived levels, shows the
promotion queue + laggard board, and ratifies a promotion (write conferred
level → log a member-upgrade entry → rebuild → conformity-close).

The standard lives in build.py (MEMBER_TIER_THRESHOLDS) + the manual at
star-alliance-skills/skillsmith/references/member-leveling.md. Full rationale:
STRATEGIST-MEMBER-LEVELING.md.

Usage:
  python3 member_level.py report                  # promotion queue + laggard board
  python3 member_level.py promote <member>        # confer up to the earned tier
  python3 member_level.py promote <member> --to Advanced
  python3 member_level.py promote --all           # confer every due member (Wave-5 seed)
  python3 member_level.py promote <member> --to Intermediate --demote   # ratify a regression
Add --yes to skip the confirmation prompt.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ORDER = ["Foundational", "Intermediate", "Advanced", "Elite", "Master"]


def rank(t):
    return ORDER.index(t) if t in ORDER else 0


def load_guild():
    """Rebuild first so levels reflect the current repo, then read the data."""
    r = subprocess.run([sys.executable, "build.py"], cwd=ROOT, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"build.py failed:\n{r.stderr}")
    return json.loads((ROOT / "guild-data.json").read_text())


def member_by_id(guild, mid):
    for m in guild["members"]:
        if m["id"] == mid:
            return m
    return None


def fmt_checklist(rows):
    out = []
    for r in rows:
        box = "✓" if r["ok"] else "✗"
        if "have" in r:
            out.append(f"      [{box}] {r['label']}: {r['have']}/{r['need']}")
        else:
            out.append(f"      [{box}] {r['label']}")
    return "\n".join(out)


def cmd_report(guild):
    members = guild["members"]
    due = [m for m in members if m["levelInfo"]["dueForPromotion"]]
    over = [m for m in members if m["levelInfo"]["overConferred"]]

    print("\n  MEMBER LEVELS — Quartermaster's board")
    print("  " + "─" * 66)
    print(f"  {'member':20}{'conferred':>14}{'earned':>14}{'AD':>5}  status")
    for m in sorted(members, key=lambda m: (rank(m["levelInfo"]["earned"]), m["levelInfo"]["ad"]), reverse=True):
        li = m["levelInfo"]
        status = "DUE ↑" if li["dueForPromotion"] else ("OVER ↓" if li["overConferred"] else "✓ settled")
        print(f"  {m['id']:20}{m['conferred']:>14}{li['earned']:>14}{li['ad']:>5}  {status}")

    if due:
        print("\n  PROMOTION QUEUE — earned above conferred:")
        for m in due:
            li = m["levelInfo"]
            print(f"\n    ↑ {m['id']}  ({m['conferred']} → {li['earned']})")
            # show the highest tier they've cleared beyond conferred
            tgt = ORDER[rank(m["conferred"]) + 1]
            print(f"      checklist for {tgt}:")
            print(fmt_checklist(li["checklist"][tgt]))
    else:
        print("\n  PROMOTION QUEUE — empty. Every conferred level matches what's earned.")

    # Laggard board — lowest craft first; the guild's improvement backlog.
    print("\n  LAGGARD BOARD — thinnest arsenals first (next-tier gaps):")
    laggards = sorted(members, key=lambda m: (rank(m["levelInfo"]["earned"]), m["levelInfo"]["ad"]))[:3]
    for m in laggards:
        li = m["levelInfo"]
        nxt = li["nextTier"]
        if not nxt:
            print(f"    • {m['id']}: {li['earned']} (at the ceiling)")
            continue
        unmet = [r for r in li["progress"] if not r["ok"]]
        gaps = ", ".join(
            (f"{r['label']} {r['have']}/{r['need']}" if "have" in r else r["label"]) for r in unmet
        ) or "all boxes met — promotable"
        print(f"    • {m['id']}: {li['earned']} → {nxt} needs: {gaps}")

    if over:
        print("\n  REGRESSIONS — conferred above earned (policy A: restore arsenal or demote):")
        for m in over:
            li = m["levelInfo"]
            print(f"    ↓ {m['id']}: conferred {m['conferred']} > earned {li['earned']}")
    print()


def set_conferred(mid, tier):
    """Minimal-diff update of a member's conferred `level` in members-meta.json."""
    p = ROOT / "members-meta.json"
    txt = p.read_text()
    pat = re.compile(r'("' + re.escape(mid) + r'":\s*\{.*?"level":\s*")[^"]*(")', re.DOTALL)
    new, n = pat.subn(lambda m: m.group(1) + tier + m.group(2), txt, count=1)
    if n != 1:
        sys.exit(f"could not locate conferred level for '{mid}' in members-meta.json")
    json.loads(new)  # guard: still valid JSON
    p.write_text(new)


def log_promotion(mid, name, frm, to):
    direction = "Promote" if rank(to) > rank(frm) else "Demote"
    r = subprocess.run([
        sys.executable, "log_event.py",
        "--type", "member-upgrade",
        "--who", "The Quartermaster",
        "--title", f"{direction} {name}: {frm} → {to}",
        "--detail", f"Conferred member level {frm} → {to} (craft-depth tier). "
                    f"Prerequisite checklist for {to} verified against the build-derived "
                    f"signals per skillsmith/references/member-leveling.md.",
        "--ref", mid,
        "--from-ver", frm, "--to-ver", to,
    ], cwd=ROOT, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"log_event.py failed:\n{r.stderr}")
    print("   " + r.stdout.strip())


def conformity_close():
    subprocess.run([sys.executable, "build.py"], cwd=ROOT, capture_output=True, text=True)
    r = subprocess.run([sys.executable, "conformity_check.py"], cwd=ROOT, capture_output=True, text=True)
    print(r.stdout.rstrip())
    if r.returncode != 0:
        sys.exit("✗ conformity-close FAILED — fix before committing.")


def promote_one(guild, m, target, demote, assume_yes):
    mid, name, li = m["id"], m["name"], m["levelInfo"]
    conferred, earned = m["conferred"], li["earned"]
    target = target or earned
    if target not in ORDER:
        sys.exit(f"unknown tier '{target}' (valid: {', '.join(ORDER)})")
    if target == conferred:
        print(f"   {mid}: already conferred {conferred} — nothing to do.")
        return False
    if rank(target) > rank(earned):
        sys.exit(f"✗ refused: {mid} has only EARNED {earned}; cannot confer {target}. "
                 f"Deepen the arsenal first (see member_level.py report).")
    if rank(target) < rank(conferred) and not demote:
        sys.exit(f"✗ {mid}: {target} is BELOW conferred {conferred} (a demotion). "
                 f"Re-run with --demote to ratify a regression (policy A).")
    verb = "Promote" if rank(target) > rank(conferred) else "Demote"
    if not assume_yes:
        ans = input(f"   {verb} {name}: {conferred} → {target}?  [y/N] ").strip().lower()
        if ans not in ("y", "yes"):
            print("   skipped.")
            return False
    set_conferred(mid, target)
    log_promotion(mid, name, conferred, target)
    print(f"   ✓ {name}: {conferred} → {target}")
    return True


def cmd_promote(guild, who, target, do_all, demote, assume_yes):
    if do_all:
        due = [m for m in guild["members"] if m["levelInfo"]["dueForPromotion"]]
        if not due:
            print("   promotion queue empty — nothing to confer.")
            return
        # list-comprehension, NOT any(): any() short-circuits and stops after the first promotion.
        changed = any([promote_one(guild, m, None, demote, assume_yes) for m in due])
    else:
        m = member_by_id(guild, who)
        if not m:
            sys.exit(f"unknown member '{who}'. Try one of: "
                     f"{', '.join(x['id'] for x in guild['members'])}")
        changed = promote_one(guild, m, target, demote, assume_yes)
    if changed:
        print("\n   — conformity-close —")
        conformity_close()


def main():
    ap = argparse.ArgumentParser(description="The Quartermaster's member-leveling console.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("report", help="promotion queue + laggard board")
    pp = sub.add_parser("promote", help="confer a member's level")
    pp.add_argument("member", nargs="?", help="member id (omit with --all)")
    pp.add_argument("--to", dest="to", help="target tier (default: the earned tier)")
    pp.add_argument("--all", action="store_true", help="confer every due member (seed)")
    pp.add_argument("--demote", action="store_true", help="allow conferring below current (regression)")
    pp.add_argument("--yes", action="store_true", help="skip confirmation")
    args = ap.parse_args()

    guild = load_guild()
    if args.cmd == "report":
        cmd_report(guild)
    elif args.cmd == "promote":
        if not args.all and not args.member:
            sys.exit("name a member or pass --all")
        cmd_promote(guild, args.member, args.to, args.all, args.demote, args.yes)


if __name__ == "__main__":
    main()
