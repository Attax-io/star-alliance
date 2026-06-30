#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────────────────
# Star Alliance — PRETOOLUSE DISPATCHER  (PreToolUse: *, BLOCKING-capable)
#
# Consolidates the five PreToolUse gates that used to be five separate hook
# entries — each a fresh `python3` interpreter cold-start (~30–50 ms) on every
# tool call. A Bash call paid for THREE (workflow + weapon + destructive); an
# Edit paid for TWO (workflow + okf). A 40-tool turn spent seconds just launching
# interpreters. This dispatcher pays ONE interpreter start, then imports the gate
# modules in-process and calls each one's pure `check(data)` function.
#
# Routing (only the relevant gates run for a given tool):
#   • workflow-gate   — every tool (it self-exempts read-only / entry tools)
#   • high-alert      — Skill | Workflow | Agent | Task   (banners, never blocks)
#   • okf-gate        — Write | Edit | MultiEdit
#   • weapon-gate     — Bash | Task | Agent
#   • destructive-gate— Bash
#
# Decision merge: FIRST blocker (exit 2) wins — its stderr is emitted and we exit
# 2 immediately, exactly as the separate-hook chain behaved (first non-zero hook
# blocked the tool). Non-blocking systemMessages from the gates that ran are
# merged into one banner. Every check() is wrapped in try/except → fail OPEN, so
# one broken gate can never brick the tool layer.
# ─────────────────────────────────────────────────────────────────────────────
import sys, os, json, importlib.util

HOOKS_DIR = os.path.dirname(os.path.abspath(__file__))

# gate file → tools it governs (None = all tools)
GATES = [
    ("workflow-gate.py",    None),
    ("high-alert.py",       {"Skill", "Workflow", "Agent", "Task"}),
    ("thinker-gate.py",     {"Task", "Agent"}),
    ("connector-gate.py",   {"Task", "Agent"}),
    ("okf-gate.py",         {"Write", "Edit", "MultiEdit"}),
    ("stop-line-gate.py",   {"Write", "Edit", "MultiEdit"}),
    ("weapon-gate.py",      {"Bash", "Task", "Agent"}),
    ("destructive-gate.py", {"Bash"}),
    ("devserver-gate.py",  {"Bash", "mcp__Claude_Preview__preview_start"}),
    # Dispatch enforcement — specialists must route through dispatch.py, not
    # call hermes directly or write files themselves. Only fires in child
    # sessions (subagents); the main session is handled by executor-enforce.py.
    # Note: None = all tools, so MCP write tools are covered too.
    ("dispatch-enforce.py", None),
]

_cache = {}


def load(fname):
    if fname in _cache:
        return _cache[fname]
    path = os.path.join(HOOKS_DIR, fname)
    spec = importlib.util.spec_from_file_location(
        "sa_" + fname.replace(".py", "").replace("-", "_"), path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    _cache[fname] = mod
    return mod


def main():
    try:
        data = json.load(sys.stdin)
    except Exception as e:
        sys.stderr.write(f"[sa-pretool] malformed payload, failing open: {e}\n")
        sys.exit(0)

    tool = data.get("tool_name", "")
    messages = []

    for fname, tools in GATES:
        if tools is not None and tool not in tools:
            continue
        try:
            mod = load(fname)
            r = mod.check(data) or {}
        except Exception as e:
            sys.stderr.write(f"[sa-pretool] {fname} errored, failing open: {e}\n")
            continue

        if r.get("exit", 0) == 2:
            # First blocker wins — emit its reason and stop the tool.
            if r.get("stderr"):
                sys.stderr.write(r["stderr"])
            sys.exit(2)
        if r.get("systemMessage"):
            messages.append(r["systemMessage"])
        if r.get("stderr"):
            sys.stderr.write(r["stderr"])  # non-blocking diagnostics

    if messages:
        print(json.dumps({"systemMessage": "\n".join(messages)}))
    sys.exit(0)


if __name__ == "__main__":
    main()
