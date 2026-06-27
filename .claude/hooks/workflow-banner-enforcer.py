#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────────────────
# Star Alliance — WORKFLOW BANNER ENFORCER  (Stop, BLOCKING)
#
# THE GAP THIS CLOSES: workflow-gate.py is a PreToolUse hook — it only bites a
# TOOL call. A turn that fires zero tools (a plain answer, a greeting, a meta-
# question) never triggers it, so it escaped the "every turn runs in a workflow"
# rule entirely. The Guild Master ruled that a workflow must ALWAYS fire. That is
# a turn-level invariant, and the only event that fires once per turn regardless
# of tools is Stop. So enforcement lives here.
#
# THE RULE: when the assistant finishes a turn, its text (since the last real user
# message) MUST contain a valid banner —
#       🗺 Starmap Workflow Started: <name>!
# …naming a workflow that exists in workflows.json. The catch-all 'Conversation'
# workflow exists precisely so a no-tool turn still has a real lane to declare.
#
#   • valid banner present            → exit 0 (allow the turn to end)
#   • no banner, attempts < CAP        → exit 2 (block; the model is re-invoked and
#                                         must emit the banner to finish the turn)
#   • no banner, attempts >= CAP       → exit 0 + stderr note (fail-safe: never brick
#                                         a turn in an infinite block loop)
#
# CAP is a brick-safety, not a loophole: emitting the banner is trivial, so in
# practice the model declares on the first nudge and the invariant holds. Fails
# OPEN on any internal error — a broken enforcer must never freeze the session.
# ─────────────────────────────────────────────────────────────────────────────
import sys, os, json, re

CAP = 3  # max consecutive banner-less assistant turns before we relent (anti-brick)
BANNER_RE = re.compile(r"Starmap Workflow Started:\s*(.+?)\s*!")
MEMBER_RE = re.compile(r"Member reports for duty:\s*([^!]+?)(?:\s+using\b|!)", re.I)


def project_dir():
    return os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def _core(name):
    """Normalize a member name/id for tolerant matching: 'the-Developer' → 'developer'."""
    s = re.sub(r"(?i)^the[-\s]+", "", (name or "").strip())
    return re.sub(r"[^a-z0-9]", "", s.lower())


def load_workflows():
    """Return {name_lower: [member_actor_id, …]} — the cast each workflow names,
    in step order, excluding `you` and gate steps."""
    path = os.path.join(project_dir(), "workflows.json")
    with open(path) as f:
        data = json.load(f)
    wfs = data.get("workflows", data) if isinstance(data, dict) else data
    seq = list(wfs.values()) if isinstance(wfs, dict) else wfs
    out = {}
    for it in seq:
        nm = (it.get("name") or "").strip()
        if not nm:
            continue
        roster = []
        for s in it.get("steps", []) or []:
            if s.get("kind") == "member":
                actor = s.get("actor")
                if actor and actor != "you" and actor not in roster:
                    roster.append(actor)
        out[nm.lower()] = roster
    return out


def last_user_index(lines):
    """Index of the last REAL user turn (not a tool_result-only message)."""
    idx = -1
    for i, o in enumerate(lines):
        if o.get("type") != "user":
            continue
        c = o.get("message", {}).get("content")
        is_tool_result = isinstance(c, list) and any(
            isinstance(b, dict) and b.get("type") == "tool_result" for b in c
        )
        if not is_tool_result:
            idx = i
    return idx


def assistant_blocks_since(lines, start):
    """(joined assistant text, count of assistant messages) since `start`."""
    texts, count = [], 0
    for o in lines[start + 1:]:
        if o.get("type") != "assistant":
            continue
        count += 1
        for b in o.get("message", {}).get("content", []):
            if isinstance(b, dict) and b.get("type") == "text":
                texts.append(b.get("text", ""))
    return "\n".join(texts), count


def main():
    try:
        data = json.load(sys.stdin)
    except Exception as e:
        sys.stderr.write(f"[banner-enforcer] malformed payload, failing open: {e}\n")
        sys.exit(0)

    transcript = data.get("transcript_path")
    if not transcript or not os.path.exists(transcript):
        sys.stderr.write("[banner-enforcer] no transcript_path, failing open\n")
        sys.exit(0)

    try:
        lines = [json.loads(l) for l in open(transcript) if l.strip()]
        names = load_workflow_names()
    except Exception as e:
        sys.stderr.write(f"[banner-enforcer] read error, failing open: {e}\n")
        sys.exit(0)

    ui = last_user_index(lines)
    text, n_assistant = assistant_blocks_since(lines, ui)

    for m in BANNER_RE.finditer(text):
        if m.group(1).strip().lower() in names:
            sys.exit(0)  # a valid workflow was declared this turn — allow

    if n_assistant >= CAP:
        sys.stderr.write(
            f"[banner-enforcer] no valid workflow banner after {n_assistant} turns — "
            f"relenting to avoid a block loop. Declare one next turn.\n"
        )
        sys.exit(0)

    # Hard block: the turn cannot end without declaring a workflow.
    sys.stderr.write(
        "⛔ WORKFLOW GATE (turn-end) — this turn ended without declaring a star-map "
        "workflow. EVERY turn must run inside one. Emit, as your FIRST line, "
        "🗺 Starmap Workflow Started: <name>! naming a workflow from workflows.json "
        "(use 'Conversation' for a plain greeting/ack/meta-question, 'Inquiry / Recon' "
        "for a read-only question about the code or guild), then give your answer. "
        "If none fits, run Workflow Forge to create one.\n"
    )
    sys.exit(2)


if __name__ == "__main__":
    main()
