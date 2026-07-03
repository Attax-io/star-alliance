#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────────────────
# Star Alliance — ROUTING ENFORCEMENT  (PreToolUse: ALL tools, BLOCKING)
#
# THE DOCTRINE: "The Butler is the voice, not the router." He hands the brief to
# the Strategist, and the Strategist decides who handles what. The Butler never
# picks specialists directly, and — as of 2026-07-03 — never investigates or
# fixes anything directly either: no Bash, no Read, no Supabase MCP, nothing,
# until the Strategist has been consulted this exchange.
#
# WIDENED 2026-07-03 (Atta): the original version of this gate only looked at
# Task/Agent calls. That missed the actual failure mode — the Butler ran a
# dozen Bash commands and a direct Supabase execute_sql to investigate and fix
# a bug, and never once called Task, so the old Task-only filter never even
# invoked this hook for those calls (see sa-pretool.py's GATES table, which
# used to route only {"Task","Agent"} here). Two things changed together:
#   1. sa-pretool.py now calls this hook for EVERY tool (tools=None).
#   2. This file adds a blanket pre-routing gate (below) that blocks ANY tool
#      outside a small pre-routing-exempt set until the Strategist has been
#      dispatched — not just specialist Task/Agent spawns.
#
# WHAT THIS HOOK DOES
# ───────────────────
# For the MAIN SESSION (Butler), on any tier except NONE (pure chat):
#
#   0. PRE-ROUTING GATE (new) — any tool NOT in PRE_ROUTING_EXEMPT (i.e. not
#      Task/Agent/Workflow/Skill/AskUserQuestion/ExitPlanMode) is BLOCKED
#      unless `strategist-dispatched` already exists. This is what stops the
#      Butler from reading files, running Bash, or touching Supabase/any MCP
#      tool before routing has happened.
#   1. Task/Agent with subagent_type="the-strategist" → ALLOW (and write
#      `strategist-dispatched` state file so subsequent specialist spawns AND
#      the pre-routing gate above pass for the rest of the exchange).
#   2. Task/Agent with subagent_type in SPECIALISTS → BLOCK unless
#      `strategist-dispatched` exists. If it exists, the Strategist was
#      consulted this exchange → ALLOW. If not → BLOCK with instructions to
#      dispatch the Strategist first.
#   3. Task/Agent with any other subagent_type (Explore, general-purpose, …)
#      → ALLOW (non-guild agents are not routed by the Strategist).
#
# TIER SCOPE (changed 2026-07-03): this used to fire only on FULL-tier turns
# (gated on the `approval-pending` state file). That's exactly how a "Quick
# Fix"-tagged LITE turn slipped past it entirely — the Butler just did the
# work inline under a low-stakes label. Now it fires on LITE and FULL; only
# NONE (pure chat, no work implied) is exempt, read from the tier sidecar
# `.claude/state/last-tier` written by guild-routing-gate.sh.
#
# NOTE (fixed 2026-07-03, kept from the original): this hook used to also
# exempt "child sessions" from the check, on the theory that
# CLAUDE_CODE_CHILD_SESSION=1 reliably marks a spawned helper. On the Desktop
# app that env var is "1" for the main Butler session too -- there is no
# reliable signal that distinguishes "Butler" from "spawned helper" here. That
# exemption made this gate a no-op for everyone, always. It has been removed.
# The rest of the logic doesn't actually need to know who's asking: it only
# cares whether `strategist-dispatched` exists, which is set the moment
# anyone calls Task(subagent_type="the-strategist"). So the Strategist itself
# (a "child" session), and any specialist dispatched after it, are unblocked
# the instant that flag is written — no chicken-and-egg problem.
#
# BYPASSES — STRICT MODE
# ──────────────────────
# No agent-controlled bypass. Kill switches:
#   • evolution/DISARMED                        (engine-wide)
#   • .claude/state/routing-enforce-disarmed     (this hook only)
#
# FAIL POSTURE
# ────────────
# Fail OPEN on any internal error — a broken gate must never brick the session.
# ─────────────────────────────────────────────────────────────────────────────
import os
import sys
import json

# Guild specialists — the agents the Butler must NOT spawn directly.
# The Strategist is excluded (he is the router, not a specialist).
SPECIALISTS = {
    "the-architect", "the-developer", "the-designer", "the-herald",
    "the-merchant", "the-quartermaster", "the-interpreter", "the-steward",
    "the-connector",
}
ROUTER = "the-strategist"

# Claude's own generic agents — legitimately used by the guild; never foreign.
KNOWN_BUILTINS = {"explore", "general-purpose", "plan", "claude",
                  "claude-code-guide", "statusline-setup", "fork"}

# Tools the Butler may use BEFORE the Strategist has been consulted:
#   Task/Agent    — the act of consulting IS this tool; can't require itself.
#   Workflow      — invoking it inherently STARTS a workflow.
#   Skill         — slash-skills are user-initiated entry points.
#   AskUserQuestion / ExitPlanMode — pre-work clarification / planning.
# Everything else — Bash, Read, Grep, Glob, LS, WebFetch, WebSearch,
# NotebookRead, Edit/Write/MultiEdit (already blocked elsewhere too), and any
# MCP tool including Supabase — requires strategist-dispatched first.
PRE_ROUTING_EXEMPT = {"Task", "Agent", "Workflow", "Skill",
                      "AskUserQuestion", "ExitPlanMode"}


def _guild_members(root):
    """Roster ids from guild-data.json (best-effort). Empty set on any failure."""
    import json as _json
    try:
        d = _json.load(open(_os_path_join(root, "guild-data.json"), encoding="utf-8"))
        return {m.get("id") for m in (d.get("members") or []) if isinstance(m, dict)}
    except Exception:
        return set()


def _os_path_join(*a):
    import os as _os
    return _os.path.join(*a)


def _proj():
    # P0 (self-enclosed campaign): prefer code-location root over a possibly-stale
    # env var; fall back to the legacy default on any error so behaviour never regresses.
    try:
        import importlib.util as _ilu, os as _os
        _sp = _ilu.spec_from_file_location("_saroot",
            _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "_saroot.py"))
        _sm = _ilu.module_from_spec(_sp); _sp.loader.exec_module(_sm)
        return _sm.resolve_root()
    except Exception:
        return os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def _state_dir():
    return os.path.join(_proj(), ".claude", "state")


def _is_kill_switch():
    if os.path.exists(os.path.join(_proj(), "evolution", "DISARMED")):
        return True
    if os.path.exists(os.path.join(_state_dir(), "routing-enforce-disarmed")):
        return True
    return False


def _current_tier():
    """Read the tier sidecar written by guild-routing-gate.sh. Defaults to
    'full' (fail-safe) if missing/unreadable — a broken tier read must never
    WEAKEN the gate."""
    try:
        p = os.path.join(_state_dir(), "last-tier")
        return open(p).read().strip().lower() if os.path.exists(p) else "full"
    except Exception:
        return "full"


def _strategist_dispatched():
    """Check if the Strategist has been dispatched this exchange."""
    return os.path.exists(os.path.join(_state_dir(), "strategist-dispatched"))


def check(data):
    """Pure decision. Returns {"exit":0|2, "stderr":str, "systemMessage":str}.
    Called by the sa-pretool.py dispatcher for EVERY tool (see GATES table).
    """
    if _is_kill_switch():
        return {"exit": 0}

    tool = data.get("tool_name", "")
    tier = _current_tier()

    # Pure-chat turns never imply work — nothing to enforce.
    if tier == "none":
        return {"exit": 0}

    # ── STEP 0: blanket pre-routing gate ────────────────────────────────────
    # Any tool outside the small pre-routing-exempt set requires the
    # Strategist to already be dispatched this exchange. This is what stops
    # the Butler from investigating (Bash/Read/Grep/WebFetch/...) or touching
    # any MCP tool (Supabase included) before routing has happened.
    if tool not in PRE_ROUTING_EXEMPT and not _strategist_dispatched():
        return {
            "exit": 2,
            "stderr": (
                f"⛔ ROUTING ENFORCE — the Butler tried to use '{tool}' directly. "
                f"The Butler has no investigation or fix ability of its own — it "
                f"routes. Dispatch the Strategist first:\n"
                f"     Task(subagent_type=\"the-strategist\", prompt=\"<the brief>\")\n"
                f"   NOTE: that Task call is ITSELF a tool call — workflow-gate.py will "
                f"also block it unless your workflow banner ('▸ Workflow — <Name>') is "
                f"already the first line of THIS turn's text. Do both together: banner "
                f"line first, then the Task(the-strategist) call — don't discover them "
                f"one at a time.\n"
                f"   Then let the Strategist — or the specialist it names — do the "
                f"looking and the doing. Restate the Strategist's routing decision in "
                f"plain English and, on a high-stakes turn, wait for the Guild "
                f"Master's \"go\" before anything else runs.\n"
                f"   No agent-controlled bypass. If this genuinely isn't a working "
                f"turn (a misclassified tier), disable the hook:\n"
                f"     touch .claude/state/routing-enforce-disarmed\n"
            ),
        }

    if tool not in ("Task", "Agent"):
        return {"exit": 0}

    ti = data.get("tool_input", {}) or {}
    sub = (ti.get("subagent_type") or ti.get("subagentType") or "").strip()

    # The Strategist — always allowed. Write the dispatched flag so
    # subsequent specialist spawns AND the pre-routing gate above know the
    # Strategist was consulted.
    if sub == ROUTER:
        try:
            with open(os.path.join(_state_dir(), "strategist-dispatched"), "w") as fh:
                fh.write("1")
        except OSError:
            pass
        return {"exit": 0}

    # A specialist — block unless the Strategist was dispatched first.
    if sub in SPECIALISTS:
        if _strategist_dispatched():
            return {"exit": 0}
        return {
            "exit": 2,
            "stderr": (
                "⛔ ROUTING ENFORCE — you are trying to spawn The " +
                sub.replace("the-", "").replace("-", " ").title() +
                f" ({sub}) directly. The Butler does not pick specialists — "
                f"that is the Strategist's job. You must dispatch the Strategist "
                f"first:\n"
                f"     Task(subagent_type=\"the-strategist\", prompt=\"<the brief>\")\n"
                f"   NOTE: if this is also your first tool call this turn, make sure "
                f"your workflow banner ('▸ Workflow — <Name>') is already the first "
                f"line of text — workflow-gate.py blocks this Task call too without it.\n"
                f"   The Strategist will read the brief, decide which specialist(s) "
                f"handle the work, and return the routing decision. Then you restate "
                f"it and halt for the Guild Master's approval.\n"
                f"   No agent-controlled bypass. If this is genuinely a non-FULL "
                f"task that was misclassified, the user can disable the hook:\n"
                f"     touch .claude/state/routing-enforce-disarmed\n"
            ),
        }

    # Non-specialist subagent. Allow Claude's own built-in generics and any guild
    # member; refuse an UNKNOWN / foreign agent under guild authority. Overridable
    # via the disarm file.
    low = sub.lower()
    if not sub or low in KNOWN_BUILTINS:
        return {"exit": 0}
    if sub in _guild_members(_proj()):
        return {"exit": 0}
    return {
        "exit": 2,
        "stderr": (
            f"⛔ ROUTING ENFORCE — '{sub}' is not a guild member and not a known "
            f"built-in agent. The guild does not run foreign agents under its authority "
            f"on a working turn. Route the work through the Strategist to a guild "
            f"member, or — if this foreign agent is genuinely intended — disable the hook:\n"
            f"     touch .claude/state/routing-enforce-disarmed\n"
        ),
    }


def main():
    try:
        data = json.load(sys.stdin)
    except Exception as e:
        sys.stderr.write(f"[routing-enforce] malformed payload, failing open: {e}\n")
        sys.exit(0)
    r = check(data)
    if r.get("stderr"):
        sys.stderr.write(r["stderr"])
    sys.exit(r.get("exit", 0))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        sys.stderr.write(f"[routing-enforce] {e}, failing open\n")
        sys.exit(0)
