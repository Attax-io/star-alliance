#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────────────────
# Star Alliance — HIGH-ALERT  (PreToolUse, harness-injected)
#
# Fires the session klaxon the instant an observable essential event happens:
#   • a Skill tool is invoked   →  ⚡ Member Skill Activated: <name>!
#   • a Workflow tool is invoked →  🗺 Starmap Workflow Started: <name>!
#
# The third banner (⚔ Member reports for duty …) is a routing-STEP-1 decision
# with no tool footprint, so it stays behavioral — the Butler emits it himself.
#
# PreToolUse hooks receive the tool call as JSON on stdin. We emit a
# non-blocking {"systemMessage": …} banner and ALWAYS exit 0 so we never gate a
# tool call — high-alert announces, it does not block.
# ─────────────────────────────────────────────────────────────────────────────
import sys, json, re

def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        return  # malformed payload — stay silent, never block
    tool = data.get("tool_name", "")
    ti = data.get("tool_input", {}) or {}
    banner = None

    if tool == "Skill":
        name = ti.get("skill") or ti.get("name") or "?"
        banner = f"⚡ Member Skill Activated: {name}!"
    elif tool == "Workflow":
        name = ti.get("name")
        if not name:
            # inline script — pull name from the meta literal
            script = ti.get("script") or ""
            m = re.search(r"name:\s*['\"]([^'\"]+)['\"]", script)
            name = m.group(1) if m else "inline workflow"
        banner = f"\U0001f5fa Starmap Workflow Started: {name}!"

    if banner:
        print(json.dumps({"systemMessage": banner}))

if __name__ == "__main__":
    main()
    sys.exit(0)
