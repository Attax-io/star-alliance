#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────────────────
# Star Alliance — INSTALL AGENTS  (member → Claude subagent)
#
# THE PROBLEM: each guild member is authored ONCE as a source-of-truth file in
# `star-alliance-members/the-*.md`. Claude spawns members as subagents defined
# under `.claude/agents/the-*.md`. Those agent files are GENERATED from the
# member files — never hand-edit them, or the next run overwrites the edit.
#
# THE FIX: regenerate one Claude subagent file per member by copying the member
# file (frontmatter + body) verbatim to `.claude/agents/<name>.md`.
#
# THE BUTLER IS A PERSONA, NOT A SUBAGENT: `the-butler` runs as the active
# session voice, never as a spawnable subagent — it gets NO `.claude/agents`
# file and is skipped here.
#
#   python3 guild/install_agents.py            # regenerate all agent files
#   python3 guild/install_agents.py --check    # report DRIFT, write nothing (nonzero exit)
# ─────────────────────────────────────────────────────────────────────────────
import re
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "star-alliance-members"
DST = ROOT / ".claude" / "agents"

FM_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", re.S)


def parse(path):
    """Return (fields_dict, full_text). fields is {} if no frontmatter."""
    txt = path.read_text(encoding="utf-8")
    m = FM_RE.match(txt)
    fields = {}
    if m:
        for line in m.group(1).splitlines():
            mm = re.match(r"([A-Za-z_][\w-]*)\s*:\s*(.*)$", line)
            if mm:
                fields[mm.group(1)] = mm.group(2).strip()
    return fields, txt


def main():
    check = "--check" in sys.argv

    members = sorted(SRC.glob("the-*.md"))
    if not members:
        print(f"no member files found in {SRC}", file=sys.stderr)
        return 1

    DST.mkdir(parents=True, exist_ok=True)

    drift = 0
    written = 0
    for path in members:
        fields, text = parse(path)
        name = fields.get("name")
        if not name:
            print(f"  skip (no name): {path.name}", file=sys.stderr)
            continue

        # The Butler is a Persona — the session's own voice, never a spawnable
        # subagent. It gets NO .claude/agents file.
        if str(fields.get("type", "")).strip().lower() == "persona":
            print(f"  persona {name} (no agent file — correct)")
            continue

        dst_path = DST / f"{name}.md"
        cur = dst_path.read_text(encoding="utf-8") if dst_path.exists() else None
        if cur == text:
            print(f"  ok    {name}")
            continue

        drift += 1
        if check:
            state = "would create" if cur is None else "would update"
            print(f"  DRIFT {name} ({state})")
            continue
        dst_path.write_text(text, encoding="utf-8")
        written += 1
        print(f"  wrote {name}")

    if check and drift:
        print(f"\n{drift} drift(s) detected — run without --check to regenerate")
        return 1
    if check:
        print(f"\n{len(members)} members checked — no drift")
        return 0
    print(f"\n{len(members)} members processed, {written} agent file(s) written")
    return 0


if __name__ == "__main__":
    sys.exit(main())
