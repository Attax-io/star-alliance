#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────────────────
# Star Alliance — INSTALL AGENTS  (costume → crew)
#
# THE PROBLEM (audit Wave D): the members are written as Claude Code agent
# definitions, and high-alert.py already fires the ⚔ "Member reports for duty"
# klaxon when a tool dispatches a sub-agent whose type is a guild member — but
# there is no  .claude/agents/  directory, so `subagent_type: the-developer`
# resolves to nothing. The whole roster therefore runs as PERSONAS the Butler
# role-plays inline in one context: no real parallelism, no context isolation,
# no independent doer fan-out. The guild is a costume.
#
# THE FIX (safe + additive): generate one real agent file per member into
# .claude/agents/ from the star-alliance-members/ source of truth. Once present,
# the orchestrator can dispatch a member with the Agent tool for real — parallel,
# isolated, each with its own context budget — and high-alert's ⚔ path goes live.
# The inline-persona path still works as the single-thread fallback; this only
# ADDS the real-dispatch option. Nothing is removed.
#
# Agent frontmatter is kept to the fields Claude Code's loader expects
# (name, description, model, tools); the member-only fields (skills, weapons,
# type) are dropped from the agent file but remain in the source member .md.
# The body (system prompt) is copied verbatim.
#
#   python3 guild/install_agents.py            # write .claude/agents/*.md
#   python3 guild/install_agents.py --check    # report drift, write nothing
# ─────────────────────────────────────────────────────────────────────────────
import os, sys, re, glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "star-alliance-members")
DST = os.path.join(ROOT, ".claude", "agents")

FM_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", re.S)
# keep only the keys the agent loader expects
KEEP = ("name", "description", "model", "tools")


def parse(path):
    txt = open(path, encoding="utf-8").read()
    m = FM_RE.match(txt)
    if not m:
        return None, None, None
    fm, body = m.group(1), m.group(2)
    fields = {}
    for line in fm.splitlines():
        mm = re.match(r"([A-Za-z_][\w-]*)\s*:\s*(.*)$", line)
        if mm:
            fields[mm.group(1)] = mm.group(2).strip()
    return fields, body, txt


def agent_text(fields, body):
    out = ["---"]
    for k in KEEP:
        if k in fields and fields[k]:
            out.append(f"{k}: {fields[k]}")
    out.append("---")
    out.append("")
    out.append(body.strip())
    out.append("")
    return "\n".join(out)


def main():
    check = "--check" in sys.argv
    members = sorted(glob.glob(os.path.join(SRC, "the-*.md")))
    if not members:
        print("no member files found", file=sys.stderr)
        return 1
    os.makedirs(DST, exist_ok=True)
    drift = 0
    for path in members:
        fields, body, _ = parse(path)
        if not fields or "name" not in fields:
            print(f"  skip (no name): {os.path.basename(path)}", file=sys.stderr)
            continue
        text = agent_text(fields, body)
        dst = os.path.join(DST, fields["name"] + ".md")
        cur = open(dst, encoding="utf-8").read() if os.path.exists(dst) else None
        if cur == text:
            print(f"  ok    {fields['name']}")
            continue
        drift += 1
        if check:
            print(f"  DRIFT {fields['name']} (would update)")
        else:
            open(dst, "w", encoding="utf-8").write(text)
            print(f"  wrote {fields['name']}")
    if check and drift:
        print(f"{drift} agent file(s) out of date — run without --check to install")
        return 1
    print(f"{len(members)} members → .claude/agents/  ({'check' if check else 'installed'})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
