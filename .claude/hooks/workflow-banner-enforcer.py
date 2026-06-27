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


def _is_stop_feedback(content):
    """True if this user message is injected Stop-hook feedback — a re-invocation
    nudge WITHIN one logical turn, not a fresh Guild Master turn. The harness
    records hook block output as a plain (non-tool_result) user message, so without
    this check `last_user_index` advances onto it and the inspection window collapses
    to the single retry: banners never accumulate across re-invokes and the anti-brick
    CAP freezes at n_assistant=1. Both bugs trace back here."""
    if isinstance(content, str):
        s = content
    elif isinstance(content, list):
        s = " ".join(
            b.get("text", "") for b in content
            if isinstance(b, dict) and b.get("type") == "text"
        )
    else:
        return False
    return s.lstrip().startswith("Stop hook feedback")


def last_user_index(lines):
    """Index of the last REAL user turn — not a tool_result-only message, and not
    injected Stop-hook feedback (see _is_stop_feedback). Skipping both keeps the
    inspection window anchored to the Guild Master's actual prompt so assistant text
    accumulates across every re-invocation of the turn."""
    idx = -1
    for i, o in enumerate(lines):
        if o.get("type") != "user":
            continue
        c = o.get("message", {}).get("content")
        is_tool_result = isinstance(c, list) and any(
            isinstance(b, dict) and b.get("type") == "tool_result" for b in c
        )
        if is_tool_result or _is_stop_feedback(c):
            continue
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
        rosters = load_workflows()
    except Exception as e:
        sys.stderr.write(f"[banner-enforcer] read error, failing open: {e}\n")
        sys.exit(0)

    ui = last_user_index(lines)
    text, n_assistant = assistant_blocks_since(lines, ui)

    # RACE GUARD: the Stop hook can fire before the finished assistant turn is
    # flushed to the transcript .jsonl. When that happens we see no assistant text
    # for this turn and would false-block a fully-compliant reply (the banner IS
    # text). If there's no visible assistant text yet, the turn isn't judgeable —
    # fail open. A real answer always carries text, so this only catches the race.
    if not text.strip():
        sys.stderr.write("[banner-enforcer] no assistant text yet (flush race) — failing open\n")
        sys.exit(0)

    relent = n_assistant >= CAP  # anti-brick: stop blocking after CAP banner-less turns

    # 1) A valid workflow must be declared this turn.
    declared = None
    for m in BANNER_RE.finditer(text):
        nm = m.group(1).strip().lower()
        if nm in rosters:
            declared = nm
            break

    if declared is None:
        if relent:
            sys.stderr.write(
                f"[banner-enforcer] no valid workflow banner after {n_assistant} turns — "
                f"relenting to avoid a block loop. Declare one next turn.\n"
            )
            sys.exit(0)
        sys.stderr.write(
            "⛔ WORKFLOW GATE (turn-end) — this turn ended without declaring a star-map "
            "workflow. EVERY turn must run inside one. Emit, as your FIRST line, "
            "🗺 Starmap Workflow Started: <name>! naming a workflow from workflows.json "
            "(use 'Conversation' for a plain greeting/ack/meta-question, 'Inquiry / Recon' "
            "for a read-only question about the code or guild), then give your answer. "
            "If none fits, run Workflow Forge to create one. "
            "IMPORTANT — BOTH gates are checked in the same pass: in this SAME reply you "
            "must ALSO emit a ⚔ Member reports for duty: <member> using <thinker> and "
            "<doer>! banner for a member of that workflow's cast. Emit both banners at "
            "once or you will be re-prompted again for the one you drop.\n"
        )
        sys.exit(2)

    # 2) At least one of the declared workflow's members must report for duty (⚔)
    #    this turn. The cast is the workflow's own steps[].actor list. A workflow can
    #    span several turns (the lead acts early, the closing the-quartermaster late),
    #    so we CANNOT demand a specific member every turn — that false-positives on a
    #    multi-turn run. The enforceable invariant is: a turn that runs under a declared
    #    workflow must show at least one of that workflow's members taking the field.
    #    The full roster is surfaced so each member — notably the closing
    #    the-quartermaster — announces as it acts. (Persona switches inside one context
    #    have no tool footprint, so per-turn we can only require ≥1, not the whole cast.)
    roster = rosters.get(declared, [])
    if not roster:
        sys.exit(0)
    roster_cores = {_core(r) for r in roster}
    announced = {_core(m.group(1)) for m in MEMBER_RE.finditer(text)}
    if announced & roster_cores or relent:
        if relent and not (announced & roster_cores):
            sys.stderr.write(
                f"[banner-enforcer] no member of '{declared}' reported after "
                f"{n_assistant} turns — relenting (anti-brick).\n"
            )
        sys.exit(0)

    roster_str = ", ".join(roster)
    sys.stderr.write(
        f"⚔ MEMBER GATE (turn-end) — workflow '{declared}' was declared but NO member of "
        f"its cast reported for duty this turn. Emit the klaxon "
        f"⚔ Member reports for duty: <member> using <thinker> and <doer>! the instant a "
        f"member takes the field. This workflow's cast (steps[].actor): {roster_str} — each "
        f"fires ⚔ as it acts (one per member, including the closing the-quartermaster), "
        f"NOT one per workflow. Keep the 🗺 Starmap Workflow Started: {declared}! banner in "
        f"this SAME reply alongside the ⚔ — both gates are checked together; emit both at "
        f"once or you'll be re-prompted for whichever you drop.\n"
    )
    sys.exit(2)


if __name__ == "__main__":
    main()
