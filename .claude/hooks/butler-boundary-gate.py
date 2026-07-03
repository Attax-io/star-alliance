#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────────────────
# Star Alliance — BUTLER BOUNDARY GATE  (PreToolUse: ALL tools, BLOCKING)
#
# THE DOCTRINE: the Butler is the guild's VOICE, not its hands. He never
# investigates and never does work himself — no Bash, no Read/Grep/Glob, no
# Edit/Write, no WebSearch/WebFetch, no MCP work (Supabase included). He ROUTES:
# he hands the brief to the Strategist, the Strategist investigates and decides
# which specialist does the craft.
#
# HOW IT STAYS SAFE (the key trick): a PreToolUse hook cannot reliably tell the
# Butler (main session) apart from a spawned specialist — on the Desktop app the
# child-session env var is "1" for both. So this gate does NOT ask "who are you".
# It asks "has the Strategist been dispatched this exchange yet?" (a per-turn
# state file). Before that: only routing/clarifying tools are allowed — this is
# what stops the Butler investigating. The instant anyone calls
# Task(subagent_type="the-strategist"), the flag is written and every work tool
# unlocks for the rest of the exchange — so the Strategist and the specialists it
# names can freely do their jobs. turn-start.py clears the flag each new turn, so
# every fresh request re-forces routing-first.
#
# OVERRIDE / KILL SWITCH (no agent-controlled bypass):
#   • evolution/DISARMED                         (engine-wide)
#   • .claude/state/butler-boundary-disarmed      (this hook only)
#
# FAIL POSTURE: fail OPEN on any internal error — a broken gate must never brick
# the session. Pure-chat turns (tier NONE) are exempt.
# ─────────────────────────────────────────────────────────────────────────────
import os, sys, json

ROUTER = "the-strategist"
# The craft specialists the Butler must NOT spawn before the Strategist has routed.
SPECIALISTS = {
    "the-architect", "the-developer", "the-designer", "the-herald",
    "the-merchant", "the-quartermaster", "the-interpreter", "the-steward",
}
# Claude's own generic agents — legitimately used by the guild, never foreign.
KNOWN_BUILTINS = {"explore", "general-purpose", "plan", "claude",
                  "claude-code-guide", "statusline-setup", "fork"}
# Tools the Butler may use BEFORE routing: the act of routing (Task/Agent), asking
# the Guild Master, planning, loading a doctrine Skill, and managing the visible
# task list. Everything else is "investigating / doing" and waits for routing.
PRE_ROUTING_EXEMPT = {
    "Task", "Agent", "AskUserQuestion", "ExitPlanMode", "Skill",
    "TaskCreate", "TaskUpdate", "TaskList", "TaskGet", "TaskStop", "TodoWrite",
}


def _proj():
    try:
        import importlib.util as ilu
        sp = ilu.spec_from_file_location(
            "_saroot", os.path.join(os.path.dirname(os.path.abspath(__file__)), "_saroot.py"))
        sm = ilu.module_from_spec(sp); sp.loader.exec_module(sm)
        return sm.resolve_root()
    except Exception:
        return os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def _state_dir():
    return os.path.join(_proj(), ".claude", "state")


def _kill_switch():
    return (os.path.exists(os.path.join(_proj(), "evolution", "DISARMED"))
            or os.path.exists(os.path.join(_state_dir(), "butler-boundary-disarmed")))


def _tier():
    try:
        p = os.path.join(_state_dir(), "last-tier")
        return open(p).read().strip().lower() if os.path.exists(p) else "full"
    except Exception:
        return "full"


def _routed():
    return os.path.exists(os.path.join(_state_dir(), "strategist-dispatched"))


def _mark_routed():
    try:
        os.makedirs(_state_dir(), exist_ok=True)
        with open(os.path.join(_state_dir(), "strategist-dispatched"), "w") as fh:
            fh.write("1")
    except OSError:
        pass


def _guild_members():
    try:
        d = json.load(open(os.path.join(_proj(), "guild-data.json"), encoding="utf-8"))
        return {m.get("id") for m in (d.get("members") or []) if isinstance(m, dict)}
    except Exception:
        return set()


DISPATCH = ("     Task(subagent_type=\"the-strategist\", prompt=\"<the brief>\")\n"
            "   Then restate the Strategist's routing decision to the Guild Master in "
            "plain English, and on a high-stakes turn wait for the \"go\" before work runs.\n"
            "   No agent bypass. If this turn genuinely isn't guild work, disable the gate:\n"
            "     touch .claude/state/butler-boundary-disarmed\n")


def check(data):
    if _kill_switch():
        return {"exit": 0}
    tool = data.get("tool_name", "")
    if _tier() == "none":
        return {"exit": 0}

    # STEP 0 — blanket pre-routing gate: no investigating/doing before the Strategist.
    if tool not in PRE_ROUTING_EXEMPT and not _routed():
        return {"exit": 2, "stderr": (f"⛔ BUTLER BOUNDARY — the Butler tried to use '{tool}' directly. The "
                   f"Butler routes; he does not investigate or do work himself. Dispatch "
                   f"the Strategist first:\n{DISPATCH}")}

    if tool not in ("Task", "Agent"):
        return {"exit": 0}

    ti = data.get("tool_input", {}) or {}
    sub = (ti.get("subagent_type") or ti.get("subagentType") or "").strip()

    if sub == ROUTER:
        _mark_routed()
        return {"exit": 0}

    if sub in SPECIALISTS:
        if _routed():
            return {"exit": 0}
        pretty = "The " + sub.replace("the-", "").replace("-", " ").title()
        return {"exit": 2, "stderr": (f"⛔ BUTLER BOUNDARY — spawning {pretty} ({sub}) directly. The Butler "
                   f"does not pick specialists — the Strategist does. Dispatch the "
                   f"Strategist first; it will name the specialist(s):\n{DISPATCH}")}

    low = sub.lower()
    if not sub or low in KNOWN_BUILTINS or sub in _guild_members():
        return {"exit": 0}
    return {"exit": 2, "stderr": (f"⛔ BUTLER BOUNDARY — '{sub}' is not a guild member or a known built-in "
               f"agent. Route through the Strategist to a guild member, or disable the "
               f"gate:\n     touch .claude/state/butler-boundary-disarmed\n")}


def main():
    try:
        data = json.load(sys.stdin)
    except Exception as e:
        sys.stderr.write(f"[butler-boundary] malformed payload, failing open: {e}\n")
        sys.exit(0)
    r = check(data) or {}
    if r.get("stderr"):
        sys.stderr.write(r["stderr"])
    sys.exit(r.get("exit", 0))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        sys.stderr.write(f"[butler-boundary] {e}, failing open\n")
        sys.exit(0)
