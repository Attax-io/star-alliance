#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────────────────
# Star Alliance — WORKFLOW GATE  (PreToolUse, BLOCKING)
#
# THE HARD RULE: every working turn runs inside a declared star-map workflow.
# No work tool fires until the orchestrator has emitted, in its assistant text
# for the CURRENT turn, the klaxon:
#       🗺 Starmap Workflow Started: <name>!
# …naming a workflow that actually exists in workflows.json.
#
# Why this exists: STEP 2 of the routing gate ("FOLLOW THE WORKFLOW") was prose
# injected every turn — it reminded but never bit. The orchestrator audited 7
# sessions with NO workflow declared (should have been Strategic Audit). Prose
# gates don't bite; a mechanical PreToolUse hook does. Same lesson the skillsmith
# friction register already booked: "G0-as-prose did NOT bite → add a hook."
#
# If NO existing workflow fits, the path forward is itself a workflow:
#   emit  🗺 Starmap Workflow Started: Workflow Forge!  → create the new workflow
#   (that write passes this gate because the banner is valid) → re-declare under
#   the new workflow → proceed. No chicken-and-egg, no special-casing.
#
# Mechanics: PreToolUse hooks get the tool call as JSON on stdin, including
# `transcript_path`. The current turn's assistant text block is flushed to the
# transcript BEFORE the tool_use dispatches (verified), so we can scan it.
#   • banner present + name in registry → exit 0 (allow)
#   • banner present + unknown name     → exit 2 (block, name it)
#   • no banner                          → exit 2 (block, declare-or-forge)
# Fails OPEN on any internal error (unreadable transcript / malformed payload):
# a broken hook must never brick every tool in the session. Errors go to stderr.
# ─────────────────────────────────────────────────────────────────────────────
import sys, os, json, re

# Tools that do NOT require a prior workflow banner:
#   Workflow      — invoking it inherently STARTS a workflow (high-alert announces it)
#   Skill         — slash-skills are user-initiated entry points; each maps to a procedure
#   AskUserQuestion / ExitPlanMode — pre-work clarification / planning, not execution
# Read-only / inspection tools are exempt: looking around (reading files, running
# read-only bash, searching) is not "work" and should never require a workflow
# banner. The gate still bites on the work-producing tools (Edit/Write/Task/...).
EXEMPT = {"Workflow", "Skill", "AskUserQuestion", "ExitPlanMode",
          "Read", "Bash", "Grep", "Glob", "LS", "NotebookRead", "WebFetch", "WebSearch"}

# Accept the NEW clean brief ("▸ Workflow — <Name>") and the LEGACY klaxon
# ("🗺 Starmap Workflow Started: <Name>!"). Recognizing both can never brick a turn.
#
# NOTE ON "ROUTING" — "Routing" is the universal INTAKE banner (the Butler
# opens it on every intake turn so workflow-gate doesn't brick an empty
# preamble) — it is NOT a real lane. The Strategist picks the actual
# workflow (Quick Fix, Standard Mission, Architecture Build, …) from
# workflows.json; the turn then continues under that banner. Routing exists
# so the gate has a valid key while the Strategist is still deciding.
BANNER_RES = [
    re.compile(r"Starmap Workflow Started:\s*(.+?)\s*!"),     # legacy
    re.compile(r"▸\s*Workflow\s*[—–\-]\s*([^\n·|]+)"),        # new clean brief
]


def find_banner(text):
    for rx in BANNER_RES:
        m = rx.search(text)
        if m:
            return m.group(1).strip()
    return None


def project_dir():
    return os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def _sense_emit(signal, *, once=None, **kw):
    """Fail-soft capability-signal emit; never breaks the gate. `once` (a sentinel
    name) dedupes a per-turn signal so the banner — re-checked on every work tool —
    is recorded once per turn, not per tool call."""
    try:
        sys.path.insert(0, os.path.join(project_dir(), "evolution"))
        import signals  # noqa: E402
        if once is not None and not signals.once_per_turn(once):
            return
        signals.emit(signal, **kw)
    except Exception:
        pass


def load_workflow_names():
    path = os.path.join(project_dir(), "workflows.json")
    with open(path) as f:
        data = json.load(f)
    wfs = data.get("workflows", data) if isinstance(data, dict) else data
    seq = list(wfs.values()) if isinstance(wfs, dict) else wfs
    names, triggers = set(), []
    for it in seq:
        nm = (it.get("name") or "").strip()
        if not nm:
            continue
        names.add(nm.lower())
        for ph in it.get("trigger_phrases", []) or []:
            triggers.append((ph.lower(), nm))
    return names, triggers


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


def assistant_text_since(lines, start):
    out = []
    for o in lines[start + 1:]:
        if o.get("type") != "assistant":
            continue
        for b in o.get("message", {}).get("content", []):
            if isinstance(b, dict) and b.get("type") == "text":
                out.append(b.get("text", ""))
    return "\n".join(out)


def last_user_text(lines, idx):
    if idx < 0:
        return ""
    c = lines[idx].get("message", {}).get("content")
    if isinstance(c, str):
        return c
    if isinstance(c, list):
        return " ".join(b.get("text", "") for b in c if isinstance(b, dict) and b.get("type") == "text")
    return ""


def candidate_workflows(prompt, triggers):
    p = (prompt or "").lower()
    hits = []
    for phrase, name in triggers:
        if phrase and phrase in p and name not in hits:
            hits.append(name)
    return hits


def check(data):
    """Pure decision. Returns {"exit":0|2, "stderr":str, "systemMessage":str}.
    Used by the consolidated dispatcher (sa-pretool.py) and the standalone main()."""
    tool = data.get("tool_name", "")
    if tool in EXEMPT:
        return {"exit": 0}

    transcript = data.get("transcript_path")
    if not transcript or not os.path.exists(transcript):
        return {"exit": 0, "stderr": "[workflow-gate] no transcript_path, failing open\n"}

    try:
        lines = [json.loads(l) for l in open(transcript) if l.strip()]
        names, triggers = load_workflow_names()
    except Exception as e:
        return {"exit": 0, "stderr": f"[workflow-gate] read error, failing open: {e}\n"}

    ui = last_user_index(lines)
    text = assistant_text_since(lines, ui)

    # Race grace: at the FIRST tool of a turn the banner isn't flushed yet — allow.
    if not text.strip():
        return {"exit": 0}

    declared = find_banner(text)
    if declared:
        if declared.lower() in names:
            try:
                state_dir = os.path.join(project_dir(), ".claude", "state")
                os.makedirs(state_dir, exist_ok=True)
                open(os.path.join(state_dir, "last-workflow"), "w").write(declared)
            except Exception:
                pass
            # Capability telemetry: which workflows actually run (once per turn).
            _sense_emit("workflow-fire", once="wf-ledgered", surface="workflows",
                        detail=f"workflow ran: {declared}", meta={"workflow": declared})
            return {"exit": 0}  # valid workflow declared — allow
        # An unregistered name was declared — a candidate new-workflow signal.
        _sense_emit("workflow-unknown", surface="workflows",
                    detail=f"unregistered workflow declared: {declared}",
                    meta={"workflow": declared})
        return {"exit": 2, "stderr": (
            f"⛔ WORKFLOW GATE — you named '{declared}', which is NOT a registered workflow. "
            f"Declare a real one (see workflows.json) with '▸ Workflow — <Name>', or forge "
            f"'{declared}' first: open '▸ Workflow — Workflow Forge', create it, then re-declare.\n"
        )}

    cands = candidate_workflows(last_user_text(lines, ui), triggers)
    hint = (
        f" This prompt matches: {', '.join(cands)}. Emit that banner, or justify out loud why it doesn't fit."
        if cands
        else " No existing workflow obviously fits — run Workflow Forge to create one before proceeding."
    )
    return {"exit": 2, "stderr": (
        "⛔ WORKFLOW GATE (HARD RULE) — no workflow declared this turn. Every working turn "
        "runs inside a workflow. Emit, as your first line, '▸ Workflow — <Name>' naming a "
        "workflow from workflows.json, or forge a new one via Workflow Forge if none fits."
        + hint + "\n"
    )}


def main():
    try:
        data = json.load(sys.stdin)
    except Exception as e:
        sys.stderr.write(f"[workflow-gate] malformed payload, failing open: {e}\n")
        sys.exit(0)
    r = check(data)
    if r.get("stderr"):
        sys.stderr.write(r["stderr"])
    sys.exit(r.get("exit", 0))


if __name__ == "__main__":
    main()
