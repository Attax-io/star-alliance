#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────────────────
# Star Alliance — CONNECTOR GATE  (PreToolUse: Task|Agent, BLOCKING)
#
# THE DOCTRINE: a stuck specialist may only summon The Connector for escalation
# AFTER it has logged SEVEN real attempts on the same task. Sanctioned direct
# connector work (a Claude connector, browser/computer-use, a web search/fetch,
# an MCP tool prefix, etc.) is NOT escalation — it routes DIRECT and the
# seven-try rule is waived.
#
# Two routes, two outcomes:
#   • DIRECT route    — haystack matches a connector keyword → allow + ledger
#                       (kind=connector, verdict=direct). System message:
#                       "Connector DIRECT route, connector work, seven-try rule waived."
#   • ESCALATION route — no keyword match, task=id present, count ≥ 7 → allow
#                       + ledger (kind=connector, verdict=escalation). System
#                       message: "Connector ESCALATION allowed, N attempts logged."
#
# Blocks (exit 2) fire when an escalation spawn lacks a task=id, or when the
# count for the declared id is below 7. A deliberate override may be put on
# the record with SA_ALLOW_CONNECTOR_ESCALATION=1 — that allows the spawn and
# ledger it (kind=connector, verdict=override) regardless of the route.
#
# This gate governs ONLY summons of the-connector; other subagent_types pass
# through untouched. Fails OPEN on any error — a broken gate never bricks the
# tool layer. Designed as a pure check(data) for the sa-pretool.py dispatcher.
# ─────────────────────────────────────────────────────────────────────────────
import sys
import os
import re
import json


CONNECTOR_KEYWORDS = (
    "supabase",
    "whatsapp",
    "gmail",
    "calendar",
    "web search",
    "websearch",
    "web fetch",
    "webfetch",
    "computer-use",
    "computer use",
    "browser",
    "mcp__",
    "claude connector",
)

TASK_ID_RE = re.compile(r"task=([a-z0-9._-]+)")
STATE_REL = os.path.join(".claude", "state", "connector-attempts.jsonl")
SEVEN = 7


def _proj():
    return os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def _ledger(repo, **kw):
    """Best-effort evolution ledger — swallows errors so a ledger hiccup
    never blocks a gate decision (parity with sibling gates)."""
    try:
        sys.path.insert(0, os.path.join(repo, "evolution"))
        import ledger  # noqa: E402
        ledger.append(**kw)
    except Exception:
        pass


def _count_attempts(repo, task_id):
    path = os.path.join(repo, STATE_REL)
    if not os.path.isfile(path):
        return 0
    n = 0
    try:
        with open(path, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if obj.get("task_id") == task_id:
                    n += 1
    except OSError:
        return 0
    return n


def check(data):
    """Pure decision. Returns {"exit":0|2, "stderr":str, "systemMessage":str}."""
    tool = data.get("tool_name", "")
    if tool not in ("Task", "Agent"):
        return {"exit": 0}

    ti = data.get("tool_input", {})
    if not isinstance(ti, dict):
        return {"exit": 0}
    sub = ti.get("subagent_type") or ti.get("subagentType") or ""
    if sub != "the-connector":
        return {"exit": 0}

    repo = _proj()
    prompt = ti.get("prompt", "") or ""
    description = ti.get("description", "") or ""
    haystack = (prompt + " " + description).lower()

    # Logged override — deliberate escalation, put on the record.
    if os.environ.get("SA_ALLOW_CONNECTOR_ESCALATION") == "1":
        _ledger(repo, kind="connector", author="connector-gate",
                surface="arsenal", verdict="override",
                detail="connector escalation: override flag set, allowed on the record",
                meta={"role": "connector", "member": "the-connector",
                      "override": True})
        return {"exit": 0,
                "systemMessage": "▸ Connector escalation (override) — logged override"}

    # DIRECT route: connector work — waiver applies.
    if any(kw in haystack for kw in CONNECTOR_KEYWORDS):
        _ledger(repo, kind="connector", author="connector-gate",
                surface="arsenal", verdict="direct",
                detail="connector DIRECT route: connector work, seven-try rule waived",
                meta={"role": "connector", "member": "the-connector",
                      "route": "direct"})
        return {"exit": 0,
                "systemMessage": "Connector DIRECT route, connector work, seven-try rule waived."}

    # ESCALATION route: seven-try rule.
    m = TASK_ID_RE.search(haystack)
    if not m:
        return {"exit": 2, "stderr": (
            "⛔ CONNECTOR GATE — The Connector takes escalation work only after "
            "the stuck specialist logs seven real attempts. Declare the task by "
            "putting task=<id> in the spawn prompt, and log each attempt with "
            "python3 .claude/tools/connector_attempts.py log <id> <member> <note>.\n"
        )}
    task_id = m.group(1)
    n = _count_attempts(repo, task_id)
    if n < SEVEN:
        return {"exit": 2, "stderr": (
            f"⛔ CONNECTOR GATE — escalation for task '{task_id}' needs seven real "
            f"attempts before The Connector is summoned. {n} logged so far. Log "
            f"more with: python3 .claude/tools/connector_attempts.py log "
            f"{task_id} <member> <note>.\n"
        )}
    _ledger(repo, kind="connector", author="connector-gate",
            surface="arsenal", verdict="escalation",
            detail=f"connector ESCALATION allowed: task {task_id} has {n} attempts",
            meta={"role": "connector", "member": "the-connector",
                  "route": "escalation", "task_id": task_id, "attempts": n})
    return {"exit": 0,
            "systemMessage": f"Connector ESCALATION allowed, {n} attempts logged."}


def main():
    try:
        data = json.load(sys.stdin)
    except Exception as e:
        sys.stderr.write(f"[connector-gate] malformed payload, failing open: {e}\n")
        sys.exit(0)
    r = check(data)
    if r.get("stderr"):
        sys.stderr.write(r["stderr"])
    sys.exit(r.get("exit", 0))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        # Parity with sibling gates: a broken gate must never brick the tool layer
        # (in production sa-pretool.py also wraps check() → fail open).
        sys.stderr.write(f"[connector-gate] {e}, failing open\n")
        sys.exit(0)
