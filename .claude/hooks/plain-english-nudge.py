#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────────────────
# Star Alliance — PLAIN ENGLISH NUDGE  (Stop hook, NON-blocking)
#
# Why this exists: the Guild Master is not a programmer. The guild's first rule
# (CLAUDE.md → "Plain English to the Guild Master") is that every message to him is
# understandable — jargon defined in the same breath, choices written as plain
# sentences. This hook is the quiet reminder that keeps the Butler honest about it.
#
# What it does: after the Butler's turn, it reads the prose he showed the Guild
# Master (code blocks and `inline code` are stripped — those are legitimately
# technical and not addressed to him), and flags any technical term used WITHOUT a
# plain-language gloss nearby. If it finds any, it BLOCKS the turn from ending
# (exit 2) and tells the Butler to rewrite the WHOLE reply in plain English —
# every line, not just a summary. Plain English is now a wall, not a nudge:
# being understood is the guild's first rule, enforced on every reply, always.
#
# Never bricks: the block is bounded. .claude/state/pe-block-count caps how many
# times one turn can be held (MAX_BLOCKS); once the cap is hit the turn is allowed
# through with a final reminder so a reply we cannot satisfy never freezes the
# session. turn-start.py clears the counter at each real user turn.
#
# Kill switch: touch .claude/state/plain-english-disarmed (or evolution/DISARMED)
# to fall back to a soft, non-blocking reminder.
#
# Fails OPEN on any error — a broken gate must never brick a turn.
# ─────────────────────────────────────────────────────────────────────────────
import sys, os, re, json, pathlib

# Technical words that, shown bare to a non-programmer, need a plain gloss beside
# them. Lower-case; matched as whole words. Deliberately conservative — we would
# rather miss a term than nag on a false alarm.
JARGON = {
    "subagent", "subagents", "spawn", "spawning", "spawned", "dispatch",
    "worktree", "worktrees", "repo", "repository", "commit", "commits",
    "diff", "regex", "stdin", "stdout", "env var", "env vars", "daemon",
    "idempotent", "fingerprint", "ledger", "hook", "hooks", "gate", "gates",
    "rls", "schema", "migration", "cli", "mcp", "endpoint", "payload",
    "sentinel", "frontmatter", "yaml", "json", "stack trace", "compaction",
    "doer", "thinker", "fan-out", "fanout", "main thread",
    "token", "tokens", "cache", "transcript", "branch", "merge", "rebase",
}

# If the term is followed soon after by a "(" gloss or " — " dash explanation,
# treat it as defined. ~60 chars is roughly one short clause.
GLOSS_WINDOW = 60


def project_dir():
    return os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def last_assistant_prose(lines):
    """Prose the assistant showed the user in the latest turn, code stripped."""
    # walk back to the last assistant message that carried visible text
    text = ""
    for o in reversed(lines):
        if o.get("type") != "assistant":
            continue
        msg = o.get("message", {}) or {}
        c = msg.get("content")
        chunks = []
        if isinstance(c, str):
            chunks.append(c)
        elif isinstance(c, list):
            for b in c:
                if isinstance(b, dict) and b.get("type") == "text":
                    chunks.append(b.get("text", ""))
        joined = "\n".join(ch for ch in chunks if ch).strip()
        if joined:
            text = joined
            break
    if not text:
        return ""
    # strip fenced code blocks, then inline `code`, then markdown tables (those
    # are scannable structure, not prose sentences to the Guild Master)
    text = re.sub(r"```.*?```", " ", text, flags=re.DOTALL)
    text = re.sub(r"`[^`]*`", " ", text)
    text = "\n".join(l for l in text.splitlines() if not l.lstrip().startswith("|"))
    return text


def undefined_terms(prose):
    low = prose.lower()
    flagged = []
    for term in JARGON:
        for m in re.finditer(r"(?<!\w)" + re.escape(term) + r"(?!\w)", low):
            window = low[m.end(): m.end() + GLOSS_WINDOW]
            # a gloss right after the term ("(" or " — "/" - " dash) counts as defined
            if "(" in window or "—" in window or " - " in window:
                continue
            flagged.append(term)
            break  # one strike per term is enough
    # de-dupe, keep order, cap at 6 so the reminder stays short
    seen, out = set(), []
    for t in flagged:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out[:6]


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    proj = pathlib.Path(project_dir())
    state = proj / ".claude" / "state"
    # only run within a real turn (same anchor every other hook uses)
    if not (state / "turn-start").exists():
        sys.exit(0)

    # Kill switch — fall back to soft/off so a session can never freeze here.
    disarmed = (proj / "evolution" / "DISARMED").exists() or (state / "plain-english-disarmed").exists()

    transcript = data.get("transcript_path")
    if not transcript or not os.path.exists(transcript):
        sys.exit(0)
    try:
        lines = [json.loads(l) for l in open(transcript) if l.strip()]
    except Exception:
        sys.exit(0)

    prose = last_assistant_prose(lines)
    if not prose:
        sys.exit(0)

    terms = undefined_terms(prose)
    if not terms:
        sys.exit(0)  # plain — let the turn end.

    shown = ", ".join(terms)

    if disarmed:
        print(
            "🗣  PLAIN-ENGLISH — technical words without a plain meaning beside "
            f"them: {shown}. (Gate disarmed; not blocking.) Say it plainer.",
            file=sys.stderr,
        )
        sys.exit(0)

    MAX_BLOCKS = 2
    counter = state / "pe-block-count"
    try:
        n = int(counter.read_text().strip() or "0")
    except Exception:
        n = 0

    if n < MAX_BLOCKS:
        try:
            state.mkdir(parents=True, exist_ok=True)
            counter.write_text(str(n + 1))
        except Exception:
            pass
        print(
            "⛔ PLAIN-ENGLISH GATE — the Guild Master is not a programmer, and this "
            f"reply shows technical words with no plain meaning beside them: {shown}. "
            "Rewrite the WHOLE reply in simple English before it goes out — every "
            "line, not just the summary. Define any unavoidable term in the same "
            "breath (\"a worktree — a private copy of the project\") or swap it for a "
            "plain phrase. Keep it short and clear: what happened, what it means, "
            "what's next. Do not end the turn until the reply is plain.",
            file=sys.stderr,
        )
        sys.exit(2)  # BLOCK the stop -> the Butler revises and tries again.

    # Bound reached — let the turn end so nothing freezes, with a last nudge.
    print(
        "🗣  PLAIN-ENGLISH — still seeing technical words without a plain meaning "
        f"({shown}). Letting this turn close so the session never freezes, but the "
        "reply should be plainer.",
        file=sys.stderr,
    )
    sys.exit(0)


if __name__ == "__main__":
    main()
