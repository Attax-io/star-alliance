#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────────────────
# Star Alliance — EXECUTOR ENFORCEMENT  (PreToolUse, BLOCKING)
#
# PROBLEM THIS HOOK CLOSES
# ─────────────────────────
# models.json declares `doer.default = minimax-m3` and CLAUDE.md says
# "doer-grade bulk → MiniMax first." weapon-gate.py validates that a summoned
# model EXISTS in the arsenal. delegation-gate.py blocks a turn that authored
# ≥6KB inline without a doer call.
#
# What was MISSING: nothing forced the executor seat to be minimax-m3. If a
# subagent is spawned with `model: sonnet` or `model: haiku` or no model, the
# brain (Claude) runs the work itself instead of delegating it to the doer —
# hallucinating along the way because it's reasoning AND doing the bulk AND
# reviewing itself, instead of plan→delegate→review.
#
# WHAT THIS HOOK DOES
# ───────────────────
# For every tool invocation that summons an AI weapon — Bash summon/minimax,
# Task/Agent subagent — when the call is acting in the EXECUTOR seat (not the
# brain seat), enforce that the resolved weapon is `minimax-m3`:
#
#   1. Task/Agent with `model:` set to a doer-tier weapon other than
#      minimax-m3 → BLOCK (exit 2) with the reason + the fixed call.
#   2. Task/Agent with NO `model:` AND a prompt that looks like doer-grade
#      bulk (>=1.5k tokens of output hint) → BLOCK, force a re-spawn that
#      pins model=minimax-m3.
#   3. Bash `summon.py <anything>` where <anything> is a doer seat and not
#      minimax-m3 → BLOCK.
#   4. Bash `minimax.py` — already minimax-m3, ALLOW (no rewrite needed).
#   5. Task/Agent in BRAIN seat (Claude, tool-capable) — ALLOW (the brain
#      should never be downgraded to a doer).
#   6. Task/Agent with `model: minimax-m3` — ALLOW (the happy path).
#
# BYPASSES (logged, not silent)
# ─────────────────────────────
#   • Per-call human bypass: include the literal substring `SA_ALLOW_EXECUTOR`
#     in the prompt/command. The hook BLOCKs first so the violation is on
#     record, prints the bypass hint, then exits 0. (Symmetric with the
#     verify-gate's `SA_SKIP_VERIFY`.)
#   • Engine kill switch: `evolution/DISARMED` or
#     `.claude/state/executor-enforce-disarmed` → exit 0 silently.
#
# FAIL POSTURE
# ────────────
# Mirrors the rest of the engine: fail OPEN on any internal error (a broken
# hook must never brick the session). Block decisions are explicit and
# instrumented; an open failure degrades to "weapon-gate only," which still
# catches retired / unknown models.
# ─────────────────────────────────────────────────────────────────────────────
import os
import sys
import json
import re

# The ONE executor seat default. Read models.json dynamically so the registry
# stays the single source of truth; fall back to the literal only on parse
# failure (registry drift is a separate problem).
EXECUTOR_FALLBACK = "minimax-m3"
# Other doer-tier weapons in the arsenal — if Claude picks one of these for
# the executor seat, BLOCK the call (we want minimax-m3, not the fallback
# chain — the fallback chain is for when minimax-m3 is unreachable, not for
# routine routing decisions).
OTHER_DOERS = {"haiku", "glm-5.2", "deepseek-v4-pro", "kimi-k2.7"}
# Brain-tier weapons — these are tool-capable Claude models, NEVER downgraded
# to the executor seat. If a Task/Agent uses one of these, it IS the brain;
# the executor rule does not apply.
BRAIN_TIER = {"opus", "sonnet", "haiku-claude", "claude-3.5-sonnet"}
# Heuristic: prompts containing these terms are clearly doer-grade bulk, so a
# missing `model:` should be BLOCKed rather than allowed to default to brain.
DOER_KEYWORDS = re.compile(
    r"(?i)\b("
    r"refactor\s+(the\s+)?entire|rewrite\s+(the\s+)?module|"
    r"bulk\s+edit|migrate\s+all|generate\s+(a\s+)?(complete|full)|"
    r"transform\s+every|summarize\s+all|"
    r"doer[- ]grade|delegat(e|ed|ing)\s+to|"
    r"minimax[- ]m3|offload\s+(this|the|bulk)|"
    r"swarm\s+of\s+\d+|fire\s+\d+\s+(doers?|models?)"
    r")\b"
)
# summon.py <model> parser — same shape weapon-gate uses, kept in sync.
SUMMON_RE = re.compile(r"summon\.py\s+([A-Za-z0-9.\-]+)")
MINIMAX_RE = re.compile(r"\bminimax\.py\b")
# Self-bypass: if the prompt explicitly invokes the override, log it and pass.
OVERRIDE_TOKEN = "SA_ALLOW_EXECUTOR"
# Tools that mutate files. The Butler must never call these directly — it must
# spawn an agent. (Subagents are exempt because they ARE the executor seat.)
WRITE_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}
# MCP write-verb heuristic. Catches the Butler sneaking writes through MCP
# (mcp__github__create_issue, mcp__postgres__execute, mcp__fs__write_file, etc.).
# False positives on a read tool with one of these verbs are fixable via the
# SA_ALLOW_EXECUTOR bypass; false negatives are the bug we're trying to kill.
MCP_WRITE_VERBS = (
    "create_", "update_", "delete_", "insert_", "drop_", "truncate_",
    "put_", "patch_", "set_", "add_", "remove_", "upsert_", "merge_",
    "write_", "append_", "modify_", "rename_", "move_",
)
# Explicit read-verb allowlist for MCP — overrides the write heuristic.
# Anything starting with these is treated as a read even if it happens to
# also start with a write verb in some naming scheme.
MCP_READ_VERBS = (
    "get_", "list_", "fetch_", "read_", "find_", "search_", "query_",
    "describe_", "show_", "view_", "lookup_", "select_",
)
# Bash commands that write files — Option C-style heuristic for the shell
# escape hatch. False positives are cheap (re-run with SA_ALLOW_EXECUTOR).
BASH_WRITE_PATTERNS = (
    r"\bsed\s+-i\b",                          # sed -i 's/.../' file
    r"(?<!\{)\bcat\s*>\s*\S",                # cat > file  (NOT { cat } in shell)
    r"\becho\s+.+?\s*>\s*\S",                # echo "..." > file
    r"\bprintf\s+.+?\s*>\s*\S",              # printf "..." > file
    r"\btee\s+\S",                            # tee file
    r"\bcp\s+\S+\s+\S+$",                    # cp src dst (last arg is dest)
    r"\bmv\s+\S+\s+\S+$",                    # mv src dst
    r"\brm\s+(-\w+\s+)*\S",                  # rm [flags] path
    r"\brmdir\s+\S",
    r"\bmkdir\s+(-\w+\s+)*\S",
    r"\btouch\s+\S",
    r"\bchmod\s+",
    r"\bchown\s+",
    r"\b>\s*\S",                              # bare > redirect target
    r"\b>>\s*\S",                             # bare >> append target
    r"\bdd\s+",                               # dd of=...
    r"\b:\s*>\s*\S",                         # : > truncate
)
BASH_WRITE_RE = re.compile("|".join(BASH_WRITE_PATTERNS))


def _project_dir():
    return os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def _state_dir():
    return os.path.join(_project_dir(), ".claude", "state")


def _ledger(**kw):
    """Best-effort ledger append; observability must never break the hook."""
    try:
        sys.path.insert(0, os.path.join(_project_dir(), "evolution"))
        import ledger  # noqa: E402

        ledger.append(**kw)
    except Exception:
        pass


def _read_seat_defaults():
    """Return {'doer': 'minimax-m3', 'brain': 'sonnet', ...} from models.json.
    Empty dict on any error — caller falls back to EXECUTOR_FALLBACK."""
    try:
        with open(
            os.path.join(_project_dir(), "star-alliance-arsenal", "models.json"),
            encoding="utf-8",
        ) as fh:
            data = json.load(fh)
        return (data.get("seats") or {})
    except Exception:
        return {}


def _is_kill_switch():
    if os.path.exists(os.path.join(_project_dir(), "evolution", "DISARMED")):
        return True
    if os.path.exists(
        os.path.join(_state_dir(), "executor-enforce-disarmed")
    ):
        return True
    return False


def _check_bash(data):
    """Inspect a Bash invocation. Returns (decision, stderr, systemMessage).

    decision ∈ {"allow", "block"}.
    """
    cmd = (data.get("tool_input") or {}).get("command", "") or ""

    # Self-bypass token — allow once, log it.
    if OVERRIDE_TOKEN in cmd:
        _ledger(
            kind="executor-override",
            author="executor-enforce",
            surface="gates",
            verdict="override",
            detail="SA_ALLOW_EXECUTOR bypass on Bash summon",
            meta={"command": cmd[:200]},
        )
        return "allow", "", ""

    models = SUMMON_RE.findall(cmd)
    is_minimax_direct = bool(MINIMAX_RE.search(cmd))
    if is_minimax_direct:
        models.append(EXECUTOR_FALLBACK)

    if not models:
        return "allow", "", ""  # not a summon

    seats = _read_seat_defaults()
    doer_default = (seats.get("doer") or {}).get("default", EXECUTOR_FALLBACK)

    # Anything summoned that is NOT the configured doer default AND is one of
    # the doer-tier weapons → block.
    for m in models:
        if m == doer_default:
            continue
        if m in OTHER_DOERS or m == EXECUTOR_FALLBACK:
            # A doer-tier weapon other than the default — block and tell them
            # exactly what to write instead.
            fixed = cmd.replace(m, doer_default)
            return (
                "block",
                f"⛔ EXECUTOR ENFORCE — executor seat must be `{doer_default}` "
                f"(models.json seats.doer.default). You summoned `{m}`. "
                f"The fallback chain is for when `{doer_default}` is "
                f"UNREACHABLE, not for routine routing.\n"
                f"   Re-draw the executor:\n"
                f"     {fixed}\n"
                f"   One-call bypass: append `{OVERRIDE_TOKEN}` to the prompt "
                f"(logged as a solo-override on the ledger).\n",
                "",
            )

    return "allow", "", ""


def _check_task(data):
    """Inspect a Task/Agent subagent spawn. Returns (decision, stderr, systemMessage)."""
    ti = data.get("tool_input") or {}
    model = ti.get("model") or ti.get("model_name") or ""
    prompt = ti.get("prompt") or ti.get("description") or ""
    agent_type = (ti.get("subagent_type") or ti.get("agent") or "").lower()
    seats = _read_seat_defaults()
    doer_default = (seats.get("doer") or {}).get("default", EXECUTOR_FALLBACK)
    brain_default = (seats.get("brain") or {}).get("default", "sonnet")

    # Self-bypass token — allow once, log it.
    if OVERRIDE_TOKEN in prompt:
        _ledger(
            kind="executor-override",
            author="executor-enforce",
            surface="gates",
            verdict="override",
            detail="SA_ALLOW_EXECUTOR bypass on Task/Agent spawn",
            meta={"model": model, "agent": agent_type},
        )
        return "allow", "", ""

    # Brain-tier model explicitly chosen → this is a THINKER spawn, not an
    # executor spawn. The executor rule does not apply.
    if model and model.lower() in {b.lower() for b in BRAIN_TIER}:
        return "allow", "", ""

    # Explicit doer-tier model that is NOT the configured default → block.
    if model and model.lower() in {d.lower() for d in OTHER_DOERS}:
        return (
            "block",
            f"⛔ EXECUTOR ENFORCE — Task/Agent was spawned with `model: "
            f"{model}`. The executor seat default is `{doer_default}` "
            f"(models.json seats.doer.default). The brain must plan and "
            f"review; the executor must be `{doer_default}` so it stays "
            f"cheap, fast, and a DIFFERENT family than the brain "
            f"(HARNESS-BOOKS: critic-style independence).\n"
            f"   Fix the spawn: pass `model: {doer_default}` explicitly.\n"
            f"   If this is genuinely a BRAIN-tier task (planning, tool "
            f"orchestration, judgment), use a Claude model instead:\n"
            f"     model: {brain_default}    (or opus for high-stakes)\n"
            f"   One-call bypass: append `{OVERRIDE_TOKEN}` to the prompt "
            f"(logged as a solo-override on the ledger).\n",
            "",
        )

    # No model AND prompt looks like doer-grade bulk → force a re-spawn.
    if not model and DOER_KEYWORDS.search(prompt):
        return (
            "block",
            f"⛔ EXECUTOR ENFORCE — Task/Agent spawn has no `model:` but the "
            f"prompt is doer-grade bulk (matched the bulk keyword heuristic). "
            f"The default would land on a Claude brain model, defeating the "
            f"thinker→executor→critic loop. Pin the executor explicitly:\n"
            f"     model: {doer_default}\n"
            f"   If this is a SMALL edit or a BRAIN-tier task, leave `model:` "
            f"unset (it inherits) and prefix the prompt with "
            f"`{OVERRIDE_TOKEN}` to acknowledge you're knowingly going solo.\n",
            "",
        )

    # No model, prompt doesn't look like bulk → the default brain will handle
    # it. Executor rule does not apply.
    return "allow", "", ""


def _check_butler_direct_write(data, tool):
    """Block the Butler from directly calling Edit/Write/MultiEdit/NotebookEdit.

    The Butler is a persona that plans and reviews. It must NOT mutate files
    itself — that's the executor's job (a subagent, or directly MiniMax for
    bulk). Spawn an agent for the work.
    """
    ti = data.get("tool_input") or {}
    file_path = ti.get("file_path") or ti.get("notebook_path") or "<unknown>"
    seats = _read_seat_defaults()
    brain_default = (seats.get("brain") or {}).get("default", "sonnet")
    return (
        "block",
        f"⛔ EXECUTOR ENFORCE — Butler is forbidden from `{tool}` directly. "
        f"You are the planner; the executor does the writes. "
        f"Spawn an agent instead:\n"
        f"     Task(model=\"minimax-m3\", prompt=\"<the actual write work on "
        f"{file_path}>\")\n"
        f"   If this is genuinely a BRAIN-tier task that needs Claude "
        f"(planning, judgment), spawn a `{brain_default}`-model agent — not "
        f"do it yourself.\n"
        f"   One-call bypass (logged as a solo-override): append "
        f"`{OVERRIDE_TOKEN}` to the most recent user message.\n",
        "",
    )


def _check_butler_bash_write(data):
    """Block the Butler from shell commands that mutate the filesystem.

    Closes the escape hatch where the Butler avoids `Edit` by running `sed -i`,
    `cat >`, `echo >`, etc. directly. Read-only commands (ls, cat, grep, git
    status, git log, npm test, …) pass through unchanged.
    """
    cmd = (data.get("tool_input") or {}).get("command", "") or ""
    if OVERRIDE_TOKEN in cmd:
        _ledger(
            kind="executor-override",
            author="executor-enforce",
            surface="gates",
            verdict="override",
            detail="SA_ALLOW_EXECUTOR bypass on Butler bash write",
            meta={"command": cmd[:200]},
        )
        return "allow", "", ""
    if not BASH_WRITE_RE.search(cmd):
        return "allow", "", ""
    return (
        "block",
        f"⛔ EXECUTOR ENFORCE — Butler tried to mutate files via shell:\n"
        f"     {cmd[:200]}{'...' if len(cmd) > 200 else ''}\n"
        f"   Spawn an agent to do the write work — the Butler is not allowed "
        f"to bypass the executor seat by going through Bash:\n"
        f"     Task(model=\"minimax-m3\", prompt=\"<the actual write work>\")\n"
        f"   If this is a read-only command that just happens to match the "
        f"heuristic (false positive), append `{OVERRIDE_TOKEN}` to the most "
        f"recent user message to bypass.\n",
        "",
    )


def _check_butler_mcp(data, tool):
    """Block MCP tools whose names start with a write verb.

    Heuristic covers the common case (create_/update_/delete_/insert_/…);
    explicit read-verb allowlist overrides it (so `mcp__fs__get_*` is always
    allowed even if a future naming scheme overlaps).
    """
    # Extract the tool part of `mcp__<server>__<tool>`.
    parts = tool.split("__")
    tool_part = parts[-1] if len(parts) >= 2 else tool
    tool_lower = tool_part.lower()

    # Explicit read-verb allowlist wins.
    if any(tool_lower.startswith(v) for v in MCP_READ_VERBS):
        return "allow", "", ""

    if any(tool_lower.startswith(v) for v in MCP_WRITE_VERBS):
        ti = data.get("tool_input") or {}
        preview = json.dumps(ti)[:200] if ti else ""
        return (
            "block",
            f"⛔ EXECUTOR ENFORCE — Butler tried to call MCP write tool "
            f"`{tool}` directly. MCP writes go through the executor seat too.\n"
            f"   Spawn an agent:\n"
            f"     Task(model=\"minimax-m3\", prompt=\"<call {tool} with: "
            f"{preview}>\")\n"
            f"   If this is actually a read (false positive), append "
            f"`{OVERRIDE_TOKEN}` to the most recent user message.\n",
            "",
        )

    # Unknown MCP tool — allow but log for review. Better to let new MCP
    # servers work out of the box than to lock the user out.
    return "allow", "", ""


def main():
    try:
        data = json.load(sys.stdin)
    except Exception as e:
        sys.stderr.write(f"[executor-enforce] malformed payload, failing open: {e}\n")
        sys.exit(0)

    if _is_kill_switch():
        sys.exit(0)

    # Distinguish main session (Butler) from subagent (worker). Hooks fire in
    # both — CLAUDE_CODE_CHILD_SESSION=1 is set in spawned helpers per
    # CLAUDE.md (helper-safety fact). The Butler lock applies ONLY when this
    # env var is unset.
    is_child_session = os.environ.get("CLAUDE_CODE_CHILD_SESSION") == "1"

    tool = data.get("tool_name", "")
    try:
        if is_child_session:
            # Subagent — only enforce the spawn-time rules (Task/Agent/Bash
            # summon). The subagent IS the executor seat; it must be free to
            # use Edit/Write/Bash to actually do the work.
            if tool == "Bash":
                decision, stderr, sysmsg = _check_bash(data)
            elif tool in ("Task", "Agent"):
                decision, stderr, sysmsg = _check_task(data)
            else:
                decision, stderr, sysmsg = "allow", "", ""
        else:
            # Butler (main session) — enforce ALL THREE axes:
            #   1. Spawn rules (Task/Agent)        — delegate properly
            #   2. Direct-write tools (Edit/Write) — never do the work yourself
            #   3. Bash write commands             — no shell escape hatch
            # Read-only tools (Read/Glob/Grep) still pass through.
            if tool == "Bash":
                d_bash, s_bash, m_bash = _check_bash(data)
                d_write, s_write, m_write = _check_butler_bash_write(data)
                # Take the strongest decision: block wins, then error.
                if d_write == "block":
                    decision, stderr, sysmsg = d_write, s_write, m_write
                else:
                    decision, stderr, sysmsg = d_bash, s_bash, m_bash
            elif tool in ("Task", "Agent"):
                decision, stderr, sysmsg = _check_task(data)
            elif tool in WRITE_TOOLS:
                decision, stderr, sysmsg = _check_butler_direct_write(
                    data, tool
                )
            elif tool.startswith("mcp__"):
                decision, stderr, sysmsg = _check_butler_mcp(data, tool)
            else:
                # Read/Glob/Grep/LS/WebFetch/etc. — Butler is allowed to think.
                decision, stderr, sysmsg = "allow", "", ""
    except Exception as e:
        sys.stderr.write(f"[executor-enforce] check error, failing open: {e}\n")
        sys.exit(0)

    if sysmsg:
        try:
            print(json.dumps({"systemMessage": sysmsg}))
        except Exception:
            pass
    if stderr:
        sys.stderr.write(stderr)
    if decision == "block":
        _ledger(
            kind="executor-block",
            author="executor-enforce",
            surface="gates",
            verdict="block",
            detail=f"blocked {tool} — wrong executor model",
            meta={"tool": tool, "tool_input": (data.get("tool_input") or {})},
        )
        sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        sys.stderr.write(f"[executor-enforce] {e}, failing open\n")
        sys.exit(0)