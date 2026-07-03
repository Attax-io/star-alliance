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
# plain-language gloss nearby. If it finds some, it prints a short reminder. It
# NEVER blocks (always exit 0): being understood is a standard we nudge toward, not
# a wall we slam. A reminder the Butler reads on the next turn is enough.
#
# Once per turn: guarded by the .claude/state/pe-nudged sentinel, which
# turn-start.py clears at the next real user turn (so it can fire again).
#
# Fails OPEN on any error — a broken reminder must never brick a turn.
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
    "doer", "thinker", "", "fan-out", "fanout", "main thread",
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

    state = pathlib.Path(project_dir()) / ".claude" / "state"
    # only run within a real turn (same anchor every other hook uses)
    if not (state / "turn-start").exists():
        sys.exit(0)
    # once per turn
    nudged = state / "pe-nudged"
    if nudged.exists():
        sys.exit(0)

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
    try:
        state.mkdir(parents=True, exist_ok=True)
        nudged.write_text("1")
    except Exception:
        pass

    if terms:
        shown = ", ".join(terms)
        print(
            "🗣  PLAIN-ENGLISH NUDGE — your last reply showed the Guild Master "
            f"technical words without a plain meaning beside them: {shown}. "
            "He is not a programmer. Next message, define each in the same breath "
            "(\"a worktree — a private copy of the project\") or replace it with a "
            "plain phrase. Being understood is the guild's first rule.",
            file=sys.stderr,
        )

    sys.exit(0)


if __name__ == "__main__":
    main()
