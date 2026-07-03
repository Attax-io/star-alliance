#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────────────────
# Star Alliance — ARSENAL DOCTOR
#
# Runtime health-check for the guild's Claude-only harness. Answers ONE
# question: "is the arsenal wired up correctly right now, and how do I fix what
# isn't?"
#
# Pattern from Agent-Reach's `doctor` command: one command → per-capability
# PASS / WARN / FAIL + a fix line.
#
# Read-only and FREE: probes presence/parse-ability of the local registry and
# MCP config, not paid APIs.
#   --json   machine-readable report.
#
# Exit 0 if no FAIL, 1 if any FAIL (so CI / a Stop check can key on it).
# ─────────────────────────────────────────────────────────────────────────────
import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(ROOT)
HOME = os.path.expanduser("~")

PASS, WARN, FAIL = "PASS", "WARN", "FAIL"
ICON = {PASS: "✅", WARN: "⚠️ ", FAIL: "❌"}

results = []  # (name, status, detail, fix)


def add(name, status, detail, fix=""):
    results.append((name, status, detail, fix))


def check_file(name, path, fix):
    if os.path.exists(path):
        add(name, PASS, path, "")
        return True
    add(name, FAIL, f"missing: {path}", fix)
    return False


def check_registry():
    reg = os.path.join(ROOT, "models.json")
    if not check_file("models.registry", reg, "single source of truth for model facts"):
        return
    try:
        with open(reg) as fh:
            data = json.load(fh)
        models = data if isinstance(data, list) else data.get("models", data)
        count = len(models) if hasattr(models, "__len__") else 0
        # Claude-only guarantee: every registered model must be a Claude backend.
        non_claude = [
            mid for mid, d in (models.items() if isinstance(models, dict) else [])
            if isinstance(d, dict) and d.get("backend") != "claude"
        ]
        if non_claude:
            add("models.registry.parse", FAIL,
                f"non-Claude backend(s): {', '.join(non_claude)}",
                "the arsenal is Claude-only — every model must have backend 'claude'")
        else:
            add("models.registry.parse", PASS, f"{count} Claude model entries", "")
    except Exception as e:
        add("models.registry.parse", FAIL, str(e)[:120], "fix JSON syntax in models.json")


def check_mcp():
    """The Claude harness ships as an MCP server; its config lives in .mcp.json."""
    mcp = os.path.join(REPO, ".mcp.json")
    if os.path.exists(mcp):
        try:
            with open(mcp) as fh:
                json.load(fh)
            add("mcp.config", PASS, mcp, "")
        except Exception as e:
            add("mcp.config", FAIL, str(e)[:120], "fix JSON syntax in .mcp.json")
    else:
        add("mcp.config", WARN, "no .mcp.json at repo root",
            "add .mcp.json to expose the guild as an MCP server (optional)")


def main():
    ap = argparse.ArgumentParser(description="Star Alliance arsenal health-check")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.parse_args()

    check_registry()
    check_mcp()

    failed = sum(1 for _, s, _, _ in results if s == FAIL)
    warned = sum(1 for _, s, _, _ in results if s == WARN)

    if _json_requested():
        print(json.dumps({
            "results": [
                {"name": n, "status": s, "detail": d, "fix": f} for n, s, d, f in results],
            "summary": {"fail": failed, "warn": warned, "pass": len(results) - failed - warned},
        }, indent=2))
    else:
        print("⚔  ARSENAL DOCTOR")
        for n, s, d, f in results:
            print(f"  {ICON[s]} {n:<24} {d}")
            if f and s != PASS:
                print(f"       ↳ fix: {f}")
        print(f"\n  {len(results) - failed - warned} pass · {warned} warn · {failed} fail")

    sys.exit(1 if failed else 0)


def _json_requested():
    return "--json" in sys.argv


if __name__ == "__main__":
    main()
