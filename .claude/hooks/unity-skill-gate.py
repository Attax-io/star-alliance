#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────────────────
# Star Alliance — UNITY-SKILL GATE  (PreToolUse, harness-injected, non-blocking)
#
# Binds two members to their unity craft — the instant a member is put on the
# field, its unity skill MUST be drawn:
#
#     the-developer  ->  code-unity      (one code source-of-truth)
#     the-designer   ->  design-unity    (one design source-of-truth)
#
# Trigger = the observable moment the member is invoked:
#   - Task / Agent tool with subagent_type == the-developer | the-designer
#   - Bash tool running  tools/dispatch.py the-developer | the-designer  ...
#
# Emits a NON-BLOCKING {"systemMessage": ...} MANDATE (never exit 2) so the
# member reads it as the first thing it must do, and never brick the tool layer.
# Mirrors the high-alert contract: pure check(data) -> dict, consumed either
# standalone or in-process by sa-pretool.py's dispatcher.
# ─────────────────────────────────────────────────────────────────────────────
import sys, json, re

# member id -> (unity skill, one-line reason)
UNITY = {
    "the-developer": (
        "code-unity",
        "before adding any new module / type / constant / util, prove the "
        "canonical source-of-truth doesn't already exist; unify fragmentation first",
    ),
    "the-designer": (
        "design-unity",
        "hold every surface to ONE design source-of-truth - tokens over "
        "hardcoded values, the canonical component over a re-invented one",
    ),
    "the-architect": (
        "code-unity",
        "before adding any new table / view / RPC / trigger, prove the canonical "
        "schema object doesn't already exist; unify divergent definitions first",
    ),
    "the-strategist": (
        "code-unity",
        "before a campaign spawns new modules across waves, enforce ONE source of "
        "truth - reuse canonical primitives, never fork parallel implementations",
    ),
}

# tools/dispatch.py the-developer "..."   /   dispatch.py the-designer '...'
_DISPATCH = re.compile(r"dispatch\.py\s+(the-developer|the-designer|the-architect|the-strategist)\b")


def _member(data):
    """Return the bound member id for this tool call, or None."""
    tool = data.get("tool_name", "")
    ti = data.get("tool_input", {}) or {}

    if tool in ("Agent", "Task"):
        sub = ti.get("subagent_type") or ti.get("subagentType") or ""
        return sub if sub in UNITY else None

    if tool == "Bash":
        m = _DISPATCH.search(ti.get("command", "") or "")
        return m.group(1) if m else None

    return None


def check(data):
    """Pure decision. Returns {"exit":0, "systemMessage":str|absent} - never blocks."""
    member = _member(data)
    if not member:
        return {"exit": 0}

    skill, why = UNITY[member]
    friendly = "The " + member.replace("the-", "").replace("-", " ").title()
    msg = (
        f"UNITY MANDATE - {friendly} is engaged. Before any build work this "
        f"turn you MUST invoke the `{skill}` skill (Skill tool) as the FIRST "
        f"action of this member's craft - {why}. This binding is not optional."
    )
    return {"exit": 0, "systemMessage": msg}


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        return  # malformed payload - stay silent, never block
    r = check(data)
    if r.get("systemMessage"):
        print(json.dumps({"systemMessage": r["systemMessage"]}))


if __name__ == "__main__":
    main()
    sys.exit(0)
