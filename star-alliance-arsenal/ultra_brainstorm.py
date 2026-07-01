#!/usr/bin/env python3
"""ultra_brainstorm.py — mechanical Phase-2 fan-out for the ultra-brainstorming skill.

The skill (../star-alliance-skills/ultra-brainstorming/SKILL.md) is doctrine: it
*describes* firing every available thinker on the same brief, but nothing forced
the fan-out to actually happen — an orchestrator could "synthesize" in its own
single head and the panel never ran. This runner makes Phase 2 REAL: it calls
each available thinker over `summon.py` and returns their candidates as JSON for
the prime thinker (the orchestrator) to converge + synthesize in Phases 3-5.

It runs the panel SEQUENTIALLY by default. That is correct on Ollama Cloud Free
(1 concurrent model — a parallel fan-out just gets the overflow rejected). On
Pro/Max raise --concurrency; ollama_cloud.py's slot semaphore keeps it inside the
plan cap either way.

Claude thinkers (opus/sonnet/haiku) are NOT run here — they are native to the
orchestrator. The runner lists them in `run_via_task` so the caller knows to spawn
them with delegate_task (model=glm-5.2, …) and fold those minds into the same panel.
Note: opus/sonnet/haiku are reserve models — pass them via --models if wanted.

Usage:
    python ultra_brainstorm.py "<brief>"                 # auto-detect panel
    python ultra_brainstorm.py -f brief.txt
    echo "<brief>" | python ultra_brainstorm.py
    python ultra_brainstorm.py "<brief>" --models glm-5.2,kimi-k2.7,minimax-sub
    python ultra_brainstorm.py "<brief>" --max-tokens 2000 --timeout 180

Output (stdout): one JSON object —
    {"brief":"…","panel":[{"model":"glm-5.2","ok":true,"candidate":{…}}, …],
     "run_via_task":["opus"],"ran":4,"failed":0}
Token/usage lines from each backend go to stderr (pipe-friendly).
"""

import argparse
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SUMMON = os.path.join(HERE, "summon.py")

# Reverse map of summon.py's cloud tags so we can detect which cloud thinkers are
# actually pulled. Imported from summon so the two never drift.
try:
    sys.path.insert(0, HERE)
    from summon import CLOUD_TAG, CLAUDE  # noqa: E402
except Exception:  # pragma: no cover - summon must be importable in practice
    CLOUD_TAG = {}
    CLAUDE = {"opus", "sonnet", "haiku"}

# Default panel — the guild's THINKER set. minimax-sub is direct-API (its own pool,
# costs no Ollama slot); the rest are Ollama-cloud thinkers (glm-5.2 + kimi-k2.7).
# Pass other cloud models via --models if wanted.
_DEFAULT_ORDER = [
    "minimax-sub",
    "glm-5.2",
    "kimi-k2.7",
]  # surviving doer panel — minimax-sub direct + Ollama-cloud thinkers

_PANEL_SYSTEM = (
    "You are ONE independent mind on a multi-model brainstorm panel. Other models "
    "see the same brief separately; your value is a DIFFERENT angle, not consensus. "
    "Read the brief and respond with ONLY a JSON object, no prose around it: "
    '{"best_plan":["step 1","step 2","step 3"],'  # 3-5 steps
    '"heaviest_risk":"the single risk you weigh most",'
    '"orphan_idea":"one idea you doubt any other model would propose"}'
)


def _pulled_cloud_tags():
    """Return the set of :cloud tags currently shown by `ollama list`."""
    try:
        out = subprocess.run(
            ["ollama", "list"], capture_output=True, text=True, timeout=20
        ).stdout
    except Exception:
        return set()
    tags = set()
    for line in out.splitlines()[1:]:
        name = line.split()[0] if line.split() else ""
        if name:
            tags.add(name)
    return tags


def _available_panel(requested):
    """Resolve the panel: explicit --models, else auto-detect what's reachable."""
    pulled = _pulled_cloud_tags()
    run_now, run_via_task, skipped = [], [], []
    candidates = requested if requested else _DEFAULT_ORDER
    for mid in candidates:
        if mid in CLAUDE:
            run_via_task.append(mid)
            continue
        if mid == "minimax-sub":
            run_now.append(mid)  # direct API; assume keyed (summon will error if not)
            continue
        tag = CLOUD_TAG.get(mid)
        if tag and tag in pulled:
            run_now.append(mid)
        else:
            skipped.append(mid)
    return run_now, run_via_task, skipped


def _call(model, brief, max_tokens, timeout):
    cmd = [
        sys.executable, SUMMON, model,
        "-s", _PANEL_SYSTEM,
        "--json",
        "--max-tokens", str(max_tokens),
        "--timeout", str(timeout),
        brief,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    # backend usage/token lines -> our stderr, so the caller still sees spend
    if proc.stderr:
        sys.stderr.write(proc.stderr)
    if proc.returncode != 0:
        return {"model": model, "ok": False,
                "error": (proc.stderr or "exit %d" % proc.returncode).strip()[:400]}
    out = proc.stdout.strip()
    try:
        candidate = json.loads(out)
    except json.JSONDecodeError:
        return {"model": model, "ok": False, "error": "non-JSON output", "raw": out[:400]}
    return {"model": model, "ok": True, "candidate": candidate}


def main():
    ap = argparse.ArgumentParser(prog="ultra_brainstorm",
                                 description="Run the ultra-brainstorming thinker fan-out.")
    ap.add_argument("brief", nargs="?", default=None, help="The brief; omit to read stdin.")
    ap.add_argument("-f", "--file", default=None, help="Read the brief from this file.")
    ap.add_argument("--models", default=None,
                    help="Comma list of model ids to run (default: auto-detect).")
    ap.add_argument("--max-tokens", type=int, default=16000,
                    help="Per-thinker budget (default 16000; reasoning models burn "
                         "the budget on <think> first — low values return empty).")
    ap.add_argument("--timeout", type=int, default=180, help="Per-call HTTP timeout (s).")
    args = ap.parse_args()

    if args.file:
        with open(args.file, "r", encoding="utf-8") as fh:
            brief = fh.read().strip()
    elif args.brief:
        brief = args.brief.strip()
    else:
        brief = sys.stdin.read().strip()
    if not brief:
        print("ultra_brainstorm: empty brief", file=sys.stderr)
        sys.exit(2)

    requested = [m.strip() for m in args.models.split(",")] if args.models else None
    run_now, run_via_task, skipped = _available_panel(requested)

    if len(run_now) + len(run_via_task) < 2:
        print(
            "ultra_brainstorm: panel too small ({} model(s)) — a single mind is not "
            "a brainstorm. Pull more cloud thinkers or pass --models.".format(
                len(run_now) + len(run_via_task)
            ),
            file=sys.stderr,
        )
    if skipped:
        print("ultra_brainstorm: skipped (not pulled/reachable): {}".format(
            ", ".join(skipped)), file=sys.stderr)

    panel = []
    for mid in run_now:  # sequential — safe under the Free=1 concurrency cap
        print("ultra_brainstorm: running {} …".format(mid), file=sys.stderr)
        panel.append(_call(mid, brief, args.max_tokens, args.timeout))

    failed = sum(1 for p in panel if not p["ok"])
    result = {
        "brief": brief,
        "panel": panel,
        "run_via_task": run_via_task,  # orchestrator runs these with delegate_task
        "ran": len(panel),
        "failed": failed,
    }
    sys.stdout.write(json.dumps(result, indent=2))
    sys.stdout.write("\n")
    sys.exit(0)


if __name__ == "__main__":
    main()
