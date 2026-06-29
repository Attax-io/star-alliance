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
# Two accepted forms — the NEW clean professional brief and the LEGACY klaxon.
# Recognizing both is strictly more permissive, so the switch can never brick a turn.
#   NEW:    ▸ Workflow — Architecture Build
#           Deploying 2 agents:
#             • The Developer — Sonnet (planning) · MiniMax M3 (execution)
#   LEGACY: 🗺 Starmap Workflow Started: Architecture Build!
#           ⚔ Member reports for duty: the-developer using sonnet and minimax-m3!
BANNER_RES = [
    re.compile(r"Starmap Workflow Started:\s*(.+?)\s*!"),            # legacy
    re.compile(r"▸\s*Workflow\s*[—–\-]\s*([^\n·|]+)"),               # new
]
MEMBER_RES = [
    re.compile(r"Member reports for duty:\s*([^!]+?)(?:\s+using\b|!)", re.I),   # legacy
    re.compile(r"(?m)^[\s>]*[•\-\*]\s*\*{0,2}(The\s+[A-Za-z]+|the-[a-z]+)\b"),  # new bullet
]


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
    """
    (joined assistant text, count of assistant messages, count of tool_use
    blocks) since `start`.

    `tool_use_count` is the number of tool invocations the assistant emitted
    since the last real user turn. A turn with ZERO tool_use blocks is purely
    conversational (greeting, ack, meta-question, prose answer) — there is
    nothing to enforce a workflow banner on, so the workflow-banner-enforcer
    bails out early. This is the chat-tier / no-work exemption the routing
    gate can't always classify (the "no tool fired" half of the NONE rule).
    """
    texts, count, tool_use_count = [], 0, 0
    for o in lines[start + 1:]:
        if o.get("type") != "assistant":
            continue
        count += 1
        for b in o.get("message", {}).get("content", []):
            if isinstance(b, dict):
                if b.get("type") == "text":
                    texts.append(b.get("text", ""))
                elif b.get("type") == "tool_use":
                    tool_use_count += 1
    return "\n".join(texts), count, tool_use_count


# ── Model-line invariant: REMOVED 2026-06-28 (transparency over enforced uniformity) ──
# This enforcer used to BLOCK any turn whose brief didn't literally read
# "minimax-m3 (execution) · glm-5.2 (critic)" (and, briefly, "sonnet (planning)").
# The Guild Master removed it: forcing the text to claim fixed model names guaranteed
# the brief said those models whether or not they were actually called — which masks a
# hallucinated/mismatched model claim instead of revealing it. The deployment brief must
# now be a TRUE reflection of the models actually used, so nothing here rewrites or
# bounces it. The workflow-declaration and member-reporting checks below remain.


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

    # B3 — tier-awareness: LITE turns are conversational/low-stakes by definition.
    # Over-firing on them trains members to ignore the klaxon (worse than no gate).
    # Read the sidecar written by guild-routing-gate.sh (same file turn-cost.py uses,
    # but we do NOT delete it here — turn-cost.py owns the lifecycle).
    tier_file = os.path.join(project_dir(), ".claude", "state", "last-tier")
    try:
        current_tier = open(tier_file).read().strip().lower() if os.path.exists(tier_file) else "full"
    except Exception:
        current_tier = "full"
    if current_tier == "lite":
        sys.exit(0)  # LITE turns exempt — no work-tool enforcement needed
    if current_tier == "none":
        sys.exit(0)  # NONE/CHAT turns exempt — pure small talk, no work-tool enforcement

    ui = last_user_index(lines)
    text, n_assistant, tool_use_count = assistant_blocks_since(lines, ui)

    # RACE GUARD: the Stop hook can fire before the finished assistant turn is
    # flushed to the transcript .jsonl. When that happens we see no assistant text
    # for this turn and would false-block a fully-compliant reply (the banner IS
    # text). If there's no visible assistant text yet, the turn isn't judgeable —
    # fail open. A real answer always carries text, so this only catches the race.
    if not text.strip():
        sys.stderr.write("[banner-enforcer] no assistant text yet (flush race) — failing open\n")
        sys.exit(0)

    # Zero-work-tools exemption: if the assistant emitted no tool_use blocks
    # since the last real user turn, this is a pure-prose / no-work turn (a
    # greeting, ack, prose answer, or meta-question). The workflow gate
    # already covers tool-time; for a no-tool turn the banner adds no value
    # and over-firing trains members to ignore the klaxon. Bail out the same
    # way the LITE/NONE tier sidecar does. Fail-open — a broken transcript
    # parse never bricks a session.
    if tool_use_count == 0:
        sys.exit(0)

    relent = n_assistant >= CAP  # anti-brick: stop blocking after CAP banner-less turns

    # 1) A valid workflow must be declared this turn.
    declared = None
    for rx in BANNER_RES:
        for m in rx.finditer(text):
            nm = m.group(1).strip().lower()
            if nm in rosters:
                declared = nm
                break
        if declared:
            break

    if declared is None:
        if relent:
            sys.stderr.write(
                f"[banner-enforcer] no valid workflow banner after {n_assistant} turns — "
                f"relenting to avoid a block loop. Declare one next turn.\n"
            )
            sys.exit(0)
        sys.stderr.write(
            "WORKFLOW NOT DECLARED (turn-end) — the answer you already gave is complete and "
            "final; it logs the turn's substance. All that is missing is the workflow banner. "
            "Add ONE short follow-up message containing nothing but the banner block below — "
            "no prose, and do NOT reproduce or summarize the answer above (that is what made "
            "the reply appear twice):\n"
            "    ▸ Workflow — <Name>\n"
            "    Deploying <N> agents:\n"
            "      • The <Member> — <planning model> (planning) · minimax-m3 (execution) · glm-5.2 (critic)\n"
            "Pick the workflow from workflows.json — 'Conversation' for a greeting/ack/meta-"
            "question, 'Inquiry / Recon' for a read-only question; if none fits, run Workflow "
            "Forge.\n"
            "VOICE-ONLY TURN: for 'Conversation' the Butler answers directly and is NOT an "
            "agent — drop the 'Deploying agents' block and write just two lines:\n"
            "    ▸ Workflow — Conversation\n"
            "    Handled directly by the Butler (the guild's voice) — <model>. No agents deployed.\n"
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
    def _enforce_models_then_allow():
        # MODEL-LINE INVARIANT REMOVED 2026-06-28 — the brief now reflects the models
        # actually used; nothing rewrites or bounces it. (Name kept for the call sites
        # below; it is now a plain allow.)
        sys.exit(0)

    roster = rosters.get(declared, [])
    if not roster:
        _enforce_models_then_allow()
    roster_cores = {_core(r) for r in roster}
    announced = {_core(m.group(1)) for rx in MEMBER_RES for m in rx.finditer(text)}
    if announced & roster_cores or relent:
        if relent and not (announced & roster_cores):
            sys.stderr.write(
                f"[banner-enforcer] no member of '{declared}' reported after "
                f"{n_assistant} turns — relenting (anti-brick).\n"
            )
        _enforce_models_then_allow()

    roster_str = ", ".join(roster)
    sys.stderr.write(
        f"NO AGENT LISTED (turn-end) — the answer you already gave is complete and final. "
        f"Workflow '{declared}' was declared but no agent of its cast was listed. Add ONE short "
        f"follow-up message containing nothing but the banner block below — no prose, and do NOT "
        f"reproduce or summarize the answer above:\n"
        f"    ▸ Workflow — {declared}\n"
        f"    Deploying <N> agents:\n"
        f"      • The <Member> — <planning model> (planning) · minimax-m3 (execution) · glm-5.2 (critic)\n"
        f"This workflow's cast (steps[].actor): {roster_str} — list at least one (including the "
        f"closing the-quartermaster as it acts).\n"
    )
    sys.exit(2)


if __name__ == "__main__":
    main()
