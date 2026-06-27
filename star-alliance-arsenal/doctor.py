#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────────────────
# Star Alliance — ARSENAL DOCTOR
#
# Runtime connectivity health-check for the guild's weapons. Answers ONE
# question: "which weapons can actually fire right now, and how do I fix the
# ones that can't?" — the gap guild-sync (device/repo parity) never covered.
#
# Pattern stolen from Agent-Reach's `doctor` command (Learning Pool mining,
# 2026-06-28): one command → per-capability PASS / WARN / FAIL + a fix line.
#
# Read-only and FREE by default: probes presence/reachability, not paid APIs.
#   --ping   also fires a 1-token live call at each reachable LLM doer (costs $).
#   --json   machine-readable report.
#
# Exit 0 if no FAIL, 1 if any FAIL (so CI / a Stop check can key on it).
# ─────────────────────────────────────────────────────────────────────────────
import argparse
import json
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
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


def check_minimax(ping):
    key = os.path.join(HOME, ".config", "minimax", "m3.key")
    runner = os.path.join(ROOT, "minimax.py")
    ok_key = check_file("minimax.key", key, "place API key at ~/.config/minimax/m3.key")
    check_file("minimax.runner", runner, "expected at star-alliance-arsenal/minimax.py")
    if ping and ok_key:
        try:
            out = subprocess.run(
                ["python3", runner, "say OK"], capture_output=True, text=True, timeout=60)
            if out.returncode == 0 and out.stdout.strip():
                add("minimax.ping", PASS, "live call returned", "")
            else:
                add("minimax.ping", FAIL, (out.stderr or out.stdout).strip()[:120],
                    "check key validity / network")
        except Exception as e:
            add("minimax.ping", FAIL, str(e)[:120], "check key validity / network")


def check_ollama(ping):
    if shutil.which("ollama") is None:
        add("ollama.cli", WARN, "ollama not on PATH",
            "install ollama, or ignore if Ollama weapons unused")
        return
    try:
        out = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=20)
        if out.returncode == 0:
            n = max(0, len(out.stdout.strip().splitlines()) - 1)
            add("ollama.list", PASS if n else WARN, f"{n} model(s) pulled",
                "" if n else "ollama pull <model> for the weapons you use")
        else:
            add("ollama.list", FAIL, out.stderr.strip()[:120], "is the ollama daemon running?")
    except Exception as e:
        add("ollama.list", FAIL, str(e)[:120], "is the ollama daemon running?")


def check_registry():
    reg = os.path.join(ROOT, "models.json")
    if not check_file("models.registry", reg, "single source of truth for model facts"):
        return
    try:
        data = json.load(open(reg))
        models = data if isinstance(data, list) else data.get("models", data)
        count = len(models) if hasattr(models, "__len__") else 0
        add("models.registry.parse", PASS, f"{count} model entries", "")
    except Exception as e:
        add("models.registry.parse", FAIL, str(e)[:120], "fix JSON syntax in models.json")


def check_summon():
    check_file("summon.runner", os.path.join(ROOT, "summon.py"),
               "expected at star-alliance-arsenal/summon.py")


def main():
    ap = argparse.ArgumentParser(description="Star Alliance arsenal health-check")
    ap.add_argument("--ping", action="store_true", help="also fire a live 1-token call (costs $)")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args()

    check_minimax(args.ping)
    check_ollama(args.ping)
    check_summon()
    check_registry()

    failed = sum(1 for _, s, _, _ in results if s == FAIL)
    warned = sum(1 for _, s, _, _ in results if s == WARN)

    if args.json:
        print(json.dumps({
            "results": [
                {"name": n, "status": s, "detail": d, "fix": f} for n, s, d, f in results],
            "summary": {"fail": failed, "warn": warned, "pass": len(results) - failed - warned},
        }, indent=2))
    else:
        print("⚔  ARSENAL DOCTOR")
        for n, s, d, f in results:
            line = f"  {ICON[s]} {n:<24} {d}"
            print(line)
            if f and s != PASS:
                print(f"       ↳ fix: {f}")
        print(f"\n  {len(results) - failed - warned} pass · {warned} warn · {failed} fail")

    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
