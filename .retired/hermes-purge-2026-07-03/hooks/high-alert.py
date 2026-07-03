#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────────────────
# Star Alliance — HIGH-ALERT  (PreToolUse, harness-injected)
#
# Announces — cleanly, professionally — the instant an observable event happens:
#   • a Skill tool is invoked    →  ▸ Skill — <name>
#   • a Workflow tool is invoked →  ▸ Workflow — <name>
#   • an Agent/Task tool dispatches a GUILD MEMBER → ▸ Agent deployed — The <Member> (<model>)
#
# The ⚔ banner only auto-fires when a REAL sub-agent is spawned whose type is a
# known guild member (the-developer, the-quartermaster, …). In the single-context
# mode the members are personas the Butler plays inline — those handoffs have no
# tool footprint, so the ⚔ for them stays behavioral (the routing-gate klaxon +
# the turn-end banner-enforcer carry that case). We do NOT fire ⚔ for non-member
# agent types (Explore, general-purpose, …) — that would be a false klaxon.
#
# PreToolUse hooks receive the tool call as JSON on stdin. We emit a
# non-blocking {"systemMessage": …} banner and ALWAYS exit 0 so we never gate a
# tool call — high-alert announces, it does not block.
# ─────────────────────────────────────────────────────────────────────────────
import sys, os, json, re


def _sense(signal, **kw):
    """Fail-soft capability-signal emit into the evolution ledger; never breaks the
    banner path (high-alert announces, it does not block — and neither does this)."""
    try:
        proj = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
        sys.path.insert(0, os.path.join(proj, "evolution"))
        import signals  # noqa: E402
        signals.emit(signal, **kw)
    except Exception:
        pass


def guild_member_ids():
    """Member ids from guild-data.json (source of truth). Empty set on any error."""
    try:
        proj = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
        g = json.load(open(os.path.join(proj, "guild-data.json")))
        return {m["id"] for m in g.get("members", [])}
    except Exception:
        return set()


def check(data):
    """Pure decision. Returns {"exit":0, "systemMessage":str} — never blocks."""
    tool = data.get("tool_name", "")
    ti = data.get("tool_input", {}) or {}
    banner = None

    if tool == "Skill":
        name = ti.get("skill") or ti.get("name") or "?"
        banner = f"▸ Skill — {name}"
        _sense("skill-fire", surface="skills", detail=f"skill fired: {name}",
               meta={"skill": name})
    elif tool == "Workflow":
        name = ti.get("name")
        if not name:
            script = ti.get("script") or ""
            m = re.search(r"name:\s*['\"]([^'\"]+)['\"]", script)
            name = m.group(1) if m else "inline workflow"
        banner = f"▸ Workflow — {name}"
    elif tool in ("Agent", "Task"):
        sub = ti.get("subagent_type") or ti.get("subagentType") or ""
        if sub in guild_member_ids():
            friendly = "The " + sub.replace("the-", "").replace("-", " ").title()
            model = ti.get("model")
            banner = f"▸ Agent deployed — {friendly}" + (f" ({model})" if model else "")
            _sense("member-dispatch", detail=f"member dispatched: {sub}",
                   meta={"member": sub})

    return {"exit": 0, "systemMessage": banner} if banner else {"exit": 0}


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        return  # malformed payload — stay silent, never block
    r = check(data)
    if r.get("systemMessage"):
        print(json.dumps({"systemMessage": r["systemMessage"]}))

if __name__ == "__main__":
    main()
    sys.exit(0)
