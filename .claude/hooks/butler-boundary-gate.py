#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────────────────
# Star Alliance — BUTLER BOUNDARY GATE  (PreToolUse: ALL tools, BLOCKING)
#
# THE DOCTRINE (LENIENT, 2026-07-04): the Butler is the guild's VOICE. He may
# LOOK before he routes — read files, search, run read-only commands to
# understand the order — but he never does the CRAFT himself. Writing, editing,
# installing, moving, deleting, touching data, or spawning a craft specialist all
# still route through the Strategist first. In short: looking is free, doing is
# routed. (This replaces the old hard line that blocked the Butler from every
# non-routing tool until he dispatched the Strategist.)
#
# HOW IT STAYS SAFE (the key trick): a PreToolUse hook cannot reliably tell the
# Butler (main session) apart from a spawned specialist — on the Desktop app the
# child-session env var is "1" for both. So this gate does NOT ask "who are you".
# It asks "has the Strategist been dispatched this exchange yet?" (a per-turn
# state file). Before that: read-only tools pass, but WRITE / destructive actions
# are held. The instant anyone calls Task(subagent_type="the-strategist"), the
# flag is written and every work tool unlocks for the rest of the exchange — so
# the Strategist and the specialists it names can freely do their jobs.
# turn-start.py clears the flag each new turn, so every fresh request re-forces
# routing-first for the doing (not the looking).
#
# OVERRIDE / KILL SWITCH (no agent-controlled bypass):
#   • evolution/DISARMED                         (engine-wide)
#   • .claude/state/butler-boundary-disarmed      (this hook only)
#
# FAIL POSTURE: fail OPEN on any internal error — a broken gate must never brick
# the session. Pure-chat turns (tier NONE) are exempt.
# ─────────────────────────────────────────────────────────────────────────────
import os, sys, json, re

ROUTER = "the-strategist"
# The craft specialists the Butler must NOT spawn before the Strategist has routed.
SPECIALISTS = {
    "the-architect", "the-developer", "the-designer", "the-herald",
    "the-merchant", "the-quartermaster", "the-interpreter", "the-steward",
}
# Claude's own generic agents — legitimately used by the guild, never foreign.
KNOWN_BUILTINS = {"explore", "general-purpose", "plan", "claude",
                  "claude-code-guide", "statusline-setup", "fork"}
# ── Write / destructive classification (lenient routing) ─────────────────────
# The Butler may investigate read-only before routing. Only WRITE actions are
# held until the Strategist is dispatched. These are the tools / commands that
# count as "doing", not "looking".
WRITE_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}

_MCP_READ_VERBS = ("get_", "list_", "fetch_", "read_", "find_", "search_",
                   "query_", "describe_", "show_", "view_", "lookup_", "select_")
_MCP_WRITE_VERBS = ("create_", "update_", "delete_", "insert_", "drop_",
                    "truncate_", "put_", "patch_", "set_", "add_", "remove_",
                    "upsert_", "merge_", "write_", "append_", "modify_",
                    "rename_", "move_", "alter_", "execute_", "run_", "apply_",
                    "save_", "send_", "post_", "publish_", "deploy_", "upload_",
                    "schedule_", "cancel_", "trigger_", "submit_", "sign_")

# Shell commands that mutate files / repo / system -> routed, not free.
_BASH_WRITE_RE = re.compile("|".join((
    r"\bcat\s*>\s*\S", r"\becho\s+.+?>\s*\S", r"\bprintf\s+.+?>\s*\S",
    r"\btee\s+\S", r"(?:^|[;&|()\s])>\s*\S", r"(?:^|[;&|()\s])>>\s*\S",
    r":\s*>\s*\S", r"\bsed\s+-i\b", r"\bcp\s+\S+\s+\S", r"\bmv\s+\S+\s+\S",
    r"\brm\s+", r"\brmdir\s+\S", r"\bmkdir\s+", r"\btouch\s+\S",
    r"\bchmod\b", r"\bchown\b", r"\bdd\b", r"\bln\s+-s", r"\bperl\s+-[ie]\b",
    r"\bruby\s+-e\b", r"\bnode\s+-e\b", r"\bnode\s+--eval\b",
    r"\bpip3?\s+install\b", r"\buv\s+pip\s+install\b", r"\bnpm\s+(install|i)\b",
    r"\byarn\s+add\b", r"\bcargo\s+install\b",
    r"\bgit\s+(checkout|reset|stash|rebase|clean|rm|commit|push|merge|apply|revert|tag)\b",
    r"\binstall\s+-m\b", r"\brsync\b", r"\bscp\b", r"\bwget\b",
    r"\bcurl\s+.+?>\s*\S", r"\bunzip\s+\S", r"\btar\s+.*-[a-zA-Z]*x",
)), re.IGNORECASE)


def _mcp_is_write(tool, data):
    part = tool.split("__")[-1].lower()
    if any(part.startswith(v) for v in _MCP_READ_VERBS):
        return False
    if part == "execute_sql":
        q = ((data.get("tool_input") or {}).get("query", "") or "").strip().lower()
        body = q[:-1] if q.endswith(";") else q
        if (";" not in body
                and re.match(r"^\s*(select|with)\b", body)
                and not re.search(r"\b(insert|update|delete|drop|alter|truncate|create|grant|revoke|merge)\b", body)):
            return False
        return True
    if any(part.startswith(v) for v in _MCP_WRITE_VERBS):
        return True
    return False   # unknown MCP tool -> lenient (treat as a read)


def _is_write_action(tool, data):
    """True if this tool call would DO work (write / change), not just look."""
    if tool in WRITE_TOOLS:
        return True
    if tool == "Bash":
        cmd = (data.get("tool_input") or {}).get("command", "") or ""
        return bool(_BASH_WRITE_RE.search(cmd))
    if tool.startswith("mcp__"):
        return _mcp_is_write(tool, data)
    return False


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

    # STEP 0 — lenient pre-routing gate: looking is free, doing is routed.
    # Read-only tools pass before the Strategist is dispatched; only WRITE /
    # destructive actions (and spawning a specialist, handled below) are held.
    if not _routed() and tool not in ("Task", "Agent") and _is_write_action(tool, data):
        return {"exit": 2, "stderr": (f"⛔ BUTLER BOUNDARY — the Butler tried to DO something with '{tool}' "
                   f"before routing. Looking is fine now — read and search freely — but "
                   f"anything that writes a file, edits the repo, touches data, installs, "
                   f"moves, or deletes still goes through the Strategist first:\n{DISPATCH}")}

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
