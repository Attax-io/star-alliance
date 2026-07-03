#!/usr/bin/env python3
# -----------------------------------------------------------------------------
# Star Alliance -- PROVE-IT GATE  (Stop hook, BLOCKING)
#
# verify-gate.py already runs an independent critic on the DIFF -- is the code
# correct, does it introduce duplication/bugs. It never reads what the user
# actually ASKED FOR. This gate closes that different hole: when the final
# assistant message this turn CLAIMS the task is done, an independent critic
# checks the claim against the original request plus the actual evidence (diff
# and tool calls), not just against code quality. Mismatch leads to block,
# forcing the turn to continue and rework instead of closing on an unproven
# claim.
#
# Complementary to verify-gate.py, not a replacement:
#   verify-gate.py -- is the diff good code
#   prove-it.py    -- does the diff or output actually satisfy what was asked
#
# CONTROLS (mirrors verify-gate.py):
#   - Kill switch: evolution/DISARMED (whole engine) OR .claude/state/prove-it-disarmed
#   - One-turn bypass: SA_SKIP_PROVE_IT=1
#   - Fails OPEN on any internal error or unreachable critic -- a broken gate or a
#     dead backend must never trap a session. Only a real critic BLOCK verdict stops.
#   - Loop-breaker: if the SAME (request plus claim plus evidence) hash gets blocked
#     twice in a row unchanged, the third Stop allows through rather than deadlocking
#     the session -- logged to the ledger as an escape, not a silent pass.
# -----------------------------------------------------------------------------
import os
import sys
import json
import hashlib
import subprocess
import re

MAX_DIFF_CHARS = 20_000
MAX_TOOL_CHARS = 4_000
MAX_REQUEST_CHARS = 4_000
MAX_CLAIM_CHARS = 3_000
CRITIC_TIMEOUT = 150
LOOP_BREAK_AFTER = 2

PROVE_IT_SYSTEM = (
    "You are the Prove-It Auditor -- an independent reviewer checking whether a "
    "claimed-finished task ACTUALLY satisfies what was asked, not whether the code "
    "is well-written (a separate gate already checks that). You will be given the "
    "ORIGINAL REQUEST, the AGENT COMPLETION CLAIM, and EVIDENCE (a code diff "
    "and or a list of tool calls made this turn). Do not take the claim at face "
    "value -- cross-check it against the evidence. Ask specifically: "
    "(1) Did every distinct thing the user asked for get addressed, or only part "
    "of it? (2) Does the evidence actually support the claim -- is a test-pass "
    "backed by a real test-run tool call in the evidence, or just asserted? "
    "(3) Is there a scope mismatch -- real work happened, but on the wrong file, "
    "wrong entity, or a narrower slice than requested? (4) Any hedge or "
    "should-work language standing in for actual verification? If there is no "
    "diff and no tool-call evidence at all for a request that clearly required "
    "action, that is a strong signal the claim is unproven. "
    "Output: a short list of concrete findings (what is missing or unverified, "
    "why, what to check), then a final line  VERDICT: pass | concerns | block. "
    "pass means the request is fully met with real evidence behind it. concerns "
    "means mostly done but minor gaps or unverified sub-claims -- allow, but flag. "
    "block means a distinctly requested item was skipped or contradicted, or the "
    "done claim has no evidence behind it at all. No filler."
)

DONE_RE = re.compile(
    r"\ball (set|done)\b"
    r"|\btask (is |has )?(now )?(complete|completed|done|finished)\b"
    r"|\b(this|that|it|everything) (is |has )?(now )?(complete|completed|done|finished|fixed|resolved|shipped|deployed|working)\b"
    r"|\bsuccessfully (implemented|completed|fixed|deployed|added|created|migrated|shipped)\b"
    r"|\bchanges (are|is) (live|complete|committed|pushed|deployed)\b"
    r"|\bready (for|to) (review|use|test|ship|merge)\b"
    r"|\xe2\x9c\x85"
    r"|^\s*(done|complete|completed|finished|shipped|fixed)[.!]?\s*$",
    re.IGNORECASE | re.MULTILINE,
)


def _text_of(o):
    msg = o.get("message", {}) or {}
    c = msg.get("content")
    if isinstance(c, str):
        return c
    out = []
    if isinstance(c, list):
        for b in c:
            if isinstance(b, dict) and b.get("type") == "text":
                out.append(b.get("text", ""))
    return "\n".join(out)


def _last_real_user_index(lines):
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


def _last_assistant_text(window):
    for o in reversed(window):
        if o.get("type") != "assistant":
            continue
        t = _text_of(o)
        if t.strip():
            return t
    return ""


def _tool_summary(window):
    parts = []
    for o in window:
        if o.get("type") != "assistant":
            continue
        content = (o.get("message", {}) or {}).get("content")
        if not isinstance(content, list):
            continue
        for b in content:
            if isinstance(b, dict) and b.get("type") == "tool_use":
                name = b.get("name", "?")
                try:
                    inp_s = json.dumps(b.get("input", {}), default=str)[:200]
                except Exception:
                    inp_s = "?"
                parts.append(f"- {name}({inp_s})")
    return "\n".join(parts)


def _diff_evidence(proj, src_ext):
    parts = []
    try:
        parts.append(subprocess.run(
            ["git", "-C", proj, "diff", "HEAD"],
            capture_output=True, text=True, timeout=20).stdout)
    except Exception:
        pass
    try:
        untracked = subprocess.run(
            ["git", "-C", proj, "ls-files", "--others", "--exclude-standard"],
            capture_output=True, text=True, timeout=20).stdout.splitlines()
    except Exception:
        untracked = []
    for rel in untracked:
        rel = rel.strip()
        if not rel:
            continue
        _, ext = os.path.splitext(rel)
        if ext not in src_ext:
            continue
        try:
            with open(os.path.join(proj, rel), encoding="utf-8", errors="replace") as fh:
                body = fh.read()
        except OSError:
            continue
        parts.append("\n--- /dev/null\n+++ b/" + rel + "  (new untracked source)\n"
                     + "\n".join("+" + ln for ln in body.splitlines()))
    return "\n".join(p for p in parts if p)


def _ledger(repo, **kw):
    try:
        sys.path.insert(0, os.path.join(repo, "evolution"))
        import ledger  # noqa: E402
        ledger.append(**kw)
    except Exception:
        pass


def _run_critic(repo, composed_text):
    critique = os.path.join(repo, "star-alliance-arsenal", "critique.py")
    if not os.path.exists(critique):
        return None
    try:
        r = subprocess.run(
            ["python3", critique, "-s", PROVE_IT_SYSTEM],
            input=composed_text, capture_output=True, text=True, timeout=CRITIC_TIMEOUT,
        )
    except Exception:
        return None
    try:
        sys.path.insert(0, os.path.join(repo, "evolution"))
        import verdict as V  # noqa: E402
    except Exception:
        return None
    decision = V.parse(r.stdout)
    if decision == "error":
        return None
    out = (r.stdout or "") + (("\n" + r.stderr) if r.stderr else "")
    return decision, out.strip()


def _truncate(s, n):
    if len(s) <= n:
        return s
    return s[:n] + "\n...[TRUNCATED, " + str(len(s) - n) + " more chars]"


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    proj = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    state = os.path.join(proj, ".claude", "state")

    if (os.path.exists(os.path.join(repo, "evolution", "DISARMED")) or
            os.path.exists(os.path.join(state, "prove-it-disarmed"))):
        sys.exit(0)
    if os.environ.get("SA_SKIP_PROVE_IT") == "1":
        sys.exit(0)

    transcript = data.get("transcript_path")
    if not transcript or not os.path.exists(transcript):
        sys.exit(0)
    try:
        lines = [json.loads(l) for l in open(transcript) if l.strip()]
    except Exception:
        sys.exit(0)
    if not lines:
        sys.exit(0)

    ui = _last_real_user_index(lines)
    if ui < 0:
        sys.exit(0)

    original_request = _text_of(lines[ui]).strip()
    if not original_request:
        sys.exit(0)

    window = lines[ui:]
    claim = _last_assistant_text(window).strip()
    if not claim or not DONE_RE.search(claim):
        sys.exit(0)

    try:
        sys.path.insert(0, os.path.join(repo, ".claude", "hooks"))
        import verify_hash as VH  # noqa: E402
        src_ext = VH.SRC_EXT
    except Exception:
        src_ext = {".py", ".js", ".ts", ".tsx", ".jsx", ".mjs", ".cjs", ".sh",
                   ".sql", ".go", ".rs", ".rb", ".php", ".vue", ".svelte", ".css"}

    diff_text = ""
    try:
        diff_text = _diff_evidence(proj, src_ext)
    except Exception:
        pass
    tool_text = _tool_summary(window)

    composed = (
        "=== ORIGINAL REQUEST (most recent user turn) ===\n"
        + _truncate(original_request, MAX_REQUEST_CHARS)
        + "\n\n=== AGENT COMPLETION CLAIM (final message this turn) ===\n"
        + _truncate(claim, MAX_CLAIM_CHARS)
        + "\n\n=== TOOL-CALL EVIDENCE (this turn, chronological) ===\n"
        + (_truncate(tool_text, MAX_TOOL_CHARS) if tool_text else "(none -- no tools were used this turn)")
        + "\n\n=== CODE DIFF EVIDENCE (working tree vs HEAD, incl. new untracked source) ===\n"
        + (_truncate(diff_text, MAX_DIFF_CHARS) if diff_text else "(no source diff -- not a code task, or nothing changed)")
    )

    cur = hashlib.sha256(composed.encode("utf-8", "ignore")).hexdigest()[:16]

    passfile = os.path.join(state, "prove-it-pass")
    if os.path.exists(passfile):
        try:
            if open(passfile).read().strip() == cur:
                sys.exit(0)
        except OSError:
            pass

    hashfile = os.path.join(state, "prove-it-last-hash")
    countfile = os.path.join(state, "prove-it-block-count")
    prev_hash, prev_count = "", 0
    try:
        if os.path.exists(hashfile):
            prev_hash = open(hashfile).read().strip()
        if os.path.exists(countfile):
            prev_count = int(open(countfile).read().strip() or "0")
    except Exception:
        prev_hash, prev_count = "", 0

    os.makedirs(state, exist_ok=True)

    if prev_hash == cur and prev_count >= LOOP_BREAK_AFTER:
        _ledger(repo, kind="block", author="prove-it", surface="gates",
                diff_hash=cur, verdict="escaped",
                detail="prove-it: identical claim blocked twice, allowing stop to avoid deadlock")
        for f in (hashfile, countfile):
            try:
                os.remove(f)
            except OSError:
                pass
        sys.stderr.write(
            "WARNING PROVE-IT GATE -- same unproven claim blocked twice already; allowing "
            "the turn to close rather than loop forever. Re-check by hand.\n")
        sys.exit(0)

    verdict = _run_critic(repo, composed)
    if verdict is None:
        sys.stderr.write(
            "WARNING PROVE-IT GATE -- critic unreachable, standing aside (infra, not judgment). "
            "Consider a manual re-read of the request vs. what actually changed.\n")
        sys.exit(0)

    decision, raw = verdict
    _ledger(repo, kind="verdict", author="prove-it-critic", surface="gates",
            diff_hash=cur, verdict=decision, detail="prove-it request-fulfillment check")

    if decision in ("pass", "concerns"):
        try:
            with open(passfile, "w") as fh:
                fh.write(cur)
        except OSError:
            pass
        for f in (hashfile, countfile):
            try:
                os.remove(f)
            except OSError:
                pass
        tail = "\n".join(raw.strip().splitlines()[-6:])
        sys.stderr.write(
            "PASS PROVE-IT GATE -- completion claim checked against the original request: " + decision.upper() + ".\n"
            + ("   findings:\n" + tail + "\n" if decision == "concerns" and tail else ""))
        sys.exit(0)

    try:
        with open(hashfile, "w") as fh:
            fh.write(cur)
        with open(countfile, "w") as fh:
            fh.write(str(prev_count + 1 if prev_hash == cur else 1))
    except OSError:
        pass
    _ledger(repo, kind="block", author="prove-it-critic", surface="gates",
            diff_hash=cur, verdict="block", detail="prove-it BLOCKED an unproven completion claim")
    sys.stderr.write(
        "BLOCK PROVE-IT GATE -- completion claim does not hold up against the original request.\n"
        "   The turn claimed done; the evidence does not back it up. Do not close on this.\n"
        "   Findings:\n"
        + "\n".join("     " + ln for ln in raw.strip().splitlines()[-20:]) + "\n"
        "   Re-read the ORIGINAL REQUEST, address every gap listed above, THEN end the turn again.\n"
        "   One-turn bypass: SA_SKIP_PROVE_IT=1 . Kill switch: touch evolution/DISARMED\n")
    sys.exit(2)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        sys.stderr.write("[prove-it] " + str(e) + ", failing open\n")
        sys.exit(0)
