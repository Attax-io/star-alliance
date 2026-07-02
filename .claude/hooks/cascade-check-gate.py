#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────────────────
# Star Alliance — CASCADE-CHECK GATE  (PreToolUse: Bash + Supabase MCP writes,
#                                       BLOCKING — but REGISTERED, NOT ARMED)
#
# THE DOCTRINE (watch-where-you-step): "no direct write to a database without
# first walking the cascade." Before any UPDATE/DELETE/INSERT/TRUNCATE/DDL
# lands on a Postgres table — via raw psql, via the Supabase MCP execute_sql,
# or via apply_migration — the operator must have on record (this turn) a
# cascade-check: at least one read-only call to pg_constraint / pg_depend /
# pg_trigger / information_schema.referential_constraints against the
# target table, with the target table's name appearing in the query text.
#
# This hook enforces the doctrine by intercepting the tool call BEFORE it
# runs and blocking it when no cascade-check is on record for this turn.
#
# ARMING — REGISTERED, NOT ARMED. Mirrors the Tier-B invariant in
# evolution/ENFORCEMENT-MODEL: hooks and gates are HUMAN-GATED. The gate
# ships in the catalog but is off by default. To arm, delete the disarmed
# sentinel:
#
#     rm -f .claude/state/cascade-check-gate-disarmed
#
# To disarm (same as the other gates — one file stands the gate down):
#
#     touch .claude/state/cascade-check-gate-disarmed
#
# Per-turn override: SA_CASCADE_SKIP=1 (logged in the evolution ledger).
#
# RISK POSTURE — mirrors destructive-gate.py and verify-gate.py:
#   • Disarmed by default. The doctrine is enforced by SKILL.md alone until
#     the Guild Master explicitly arms.
#   • Disarmed sentinel = .claude/state/cascade-check-gate-disarmed (same
#     pattern as the other gates) OR evolution/DISARMED (the engine-wide
#     kill switch).
#   • One-turn override: SA_CASCADE_SKIP=1  (logged via the evolution ledger)
#   • Fails OPEN on infrastructure errors. A broken safety hook must never
#     trap a session.
#
# STATE — the gate reads .claude/state/cascade-check-pass after every tool
# call. turn-start.py clears it; the cascade-check skill writes it when the
# read-only probe runs. The gate's job is to see it on disk before the
# write runs.
# ─────────────────────────────────────────────────────────────────────────────
import os
import sys
import json
import re

# ── Tool-name allowlist ────────────────────────────────────────────────────
# The gate fires only on:
#   • Bash — raw psql / pgcli / psql -c "…"
#   • mcp__1ee3ddfd-27aa-4176-9539-d9a2081c163d__execute_sql — Supabase MCP
#   • mcp__1ee3ddfd-27aa-4176-9539-d9a2081c163d__apply_migration — Supabase MCP
SUPABASE_WRITE_TOOLS = (
    "mcp__1ee3ddfd-27aa-4176-9539-d9a2081c163d__execute_sql",
    "mcp__1ee3ddfd-27aa-4176-9539-d9a2081c163d__apply_migration",
)
GATED_TOOLS = ("Bash",) + SUPABASE_WRITE_TOOLS

# ── Cascade-triggering patterns ────────────────────────────────────────────
# Anything matching this list is a write-shaped call that requires a
# cascade-check on record for this turn. The match is intentionally
# conservative — false positives cost one extra cascade-check, false
# negatives let the gate through and the doctrine is bypassed.
#
# Order matters: first match wins for the message. The Supabase MCP tools
# short-circuit at the top (apply_migration is a write by definition;
# execute_sql is a write only if the SQL body contains a DML/DDL verb).
WRITE_VERB_PATTERNS = [
    ("UPDATE",        re.compile(r"\bUPDATE\s+[A-Za-z_][\w\.\"]*\s+SET\b",   re.IGNORECASE)),
    ("DELETE",        re.compile(r"\bDELETE\s+FROM\s+[A-Za-z_][\w\.\"]*",     re.IGNORECASE)),
    ("INSERT",        re.compile(r"\bINSERT\s+INTO\s+[A-Za-z_][\w\.\"]*",    re.IGNORECASE)),
    ("TRUNCATE",      re.compile(r"\bTRUNCATE\s+(TABLE\s+)?[A-Za-z_]",        re.IGNORECASE)),
    ("DROP TABLE",    re.compile(r"\bDROP\s+TABLE\s+",                       re.IGNORECASE)),
    ("DROP COLUMN",   re.compile(r"\bDROP\s+COLUMN\s+",                      re.IGNORECASE)),
    ("ALTER TABLE",   re.compile(r"\bALTER\s+TABLE\s+",                      re.IGNORECASE)),
    ("RENAME",        re.compile(r"\bALTER\s+TABLE\s+[A-Za-z_][\w\.\"]*\s+RENAME\b", re.IGNORECASE)),
    ("MERGE",         re.compile(r"\bMERGE\s+INTO\s+",                       re.IGNORECASE)),
    ("COPY",          re.compile(r"\bCOPY\s+[A-Za-z_][\w\.\"]*\s+FROM\b",    re.IGNORECASE)),
]

# Raw psql / pgcli shell invocations: same doctrine, different surface.
# A shell command that pipes to psql / invokes psql -c / is a pg_dump /
# psql shell — if it carries an UPDATE/DELETE/INSERT/TRUNCATE/DDL, gate it.
PSQL_PATTERNS = [
    ("psql",          re.compile(r"\bpsql\b",                                re.IGNORECASE)),
    ("pgcli",         re.compile(r"\bpgcli\b",                               re.IGNORECASE)),
    ("pg_dump",       re.compile(r"\bpg_dump\b",                             re.IGNORECASE)),
]

# Read-only verbs that are NOT gate-triggering even if the surrounding
# command is psql: SELECT, EXPLAIN, VACUUM, ANALYZE, SHOW, \d, etc. The
# gate only blocks the WRITE half of a tool call.
READ_ONLY_VERBS = re.compile(
    r"^\s*(SELECT|EXPLAIN|VACUUM|ANALYZE|SHOW|HELP|DESCRIBE|\$|\\)",
    re.IGNORECASE,
)

# Cascade-check surface queries — what the doctrine says counts as
# "I have walked the catalog for this table." The gate looks for
# any of these tokens in the body of a recent read-only call.
CASCADE_CHECK_TOKENS = [
    re.compile(r"\bpg_constraint\b",          re.IGNORECASE),
    re.compile(r"\bpg_depend\b",              re.IGNORECASE),
    re.compile(r"\bpg_trigger\b",             re.IGNORECASE),
    re.compile(r"\bpg_class\b",               re.IGNORECASE),
    re.compile(r"\binformation_schema\.referential_constraints\b", re.IGNORECASE),
    re.compile(r"\binformation_schema\.table_constraints\b",      re.IGNORECASE),
    re.compile(r"\bconfdeltype\b",            re.IGNORECASE),
    re.compile(r"\bconfupdtype\b",            re.IGNORECASE),
    re.compile(r"\breferential_constraints\b", re.IGNORECASE),
]


def _project_dir():
    return os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def _state_dir():
    return os.path.join(_project_dir(), ".claude", "state")


def _disarmed():
    """True if the gate is disarmed (off by default)."""
    proj = _project_dir()
    return (
        os.path.exists(os.path.join(proj, "evolution", "DISARMED"))
        or os.path.exists(os.path.join(_state_dir(), "cascade-check-gate-disarmed"))
    )


def _cascade_check_on_record():
    """Return the most recent cascade-check on disk, or '' if none.

    The state file holds the JSON of the last cascade-check (target table
    + the catalog tables it touched). The gate compares the target-table
    name against the current write's target. If they match, doctrine
    followed. If the file is missing or stale (different table), block.
    """
    path = os.path.join(_state_dir(), "cascade-check-pass")
    try:
        with open(path, encoding="utf-8") as fh:
            return fh.read().strip()
    except OSError:
        return ""


def _record_state(target):
    """Write the most recent cascade-check target to state, so the gate
    (and other consumers) can read it. Best-effort: a broken write must
    not block the gate's main path."""
    path = os.path.join(_state_dir(), "cascade-check-pass")
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(target)
        return True
    except OSError:
        return False


def _extract_text_from_payload(tool_input):
    """Pull the meaningful text out of a tool call. The Supabase MCP and
    Bash both put their payload in different places; the gate is
    permissive — anything string-shaped is concatenated and scanned."""
    if not tool_input:
        return ""
    parts = []
    for key in ("command", "query", "sql", "statement", "content", "text", "input"):
        v = tool_input.get(key)
        if isinstance(v, str):
            parts.append(v)
    # MCP payloads sometimes nest the SQL under "arguments"; be liberal.
    if not parts:
        args = tool_input.get("arguments") or {}
        if isinstance(args, dict):
            for v in args.values():
                if isinstance(v, str):
                    parts.append(v)
    return "\n".join(parts)


def _first_write_verb(text):
    """Return (verb_label, table_name) for the first write verb in text,
    or (None, None) if no write verb is present. Conservative: only
    matches a table-shaped token after the verb."""
    # Strip SQL line-comments so a write-verb mentioned in a comment
    # doesn't trip the gate.
    no_comments = re.sub(r"--[^\n]*", " ", text)
    for label, pat in WRITE_VERB_PATTERNS:
        m = pat.search(no_comments)
        if not m:
            continue
        # Heuristic table-name capture: the next identifier-shaped
        # token after the verb. Good enough for the gate's purpose —
        # the doctrine's full procedure reads the SQL aloud anyway.
        tail = no_comments[m.end(): m.end() + 200]
        name_match = re.search(
            r"[\"']?([A-Za-z_][\w]*)[\"']?",
            tail,
        )
        table = name_match.group(1) if name_match else "<unknown>"
        return label, table
    return None, None


def _has_cascade_check_surface(text):
    """True if the text touches any of the catalog tables/views the
    doctrine treats as a cascade-check. Used to identify the
    read-only probe in turn-start.py's passthrough log, NOT for
    the gate's primary check (which reads the state file)."""
    return any(p.search(text) for p in CASCADE_CHECK_TOKENS)


def check(data):
    """Pure decision. Returns {"exit":0|2, "stderr":str}."""
    tool_name = data.get("tool_name", "")
    if tool_name not in GATED_TOOLS:
        return {"exit": 0}

    # The Supabase MCP apply_migration is a write by definition; gate it
    # without inspecting the SQL body.
    if tool_name.endswith("apply_migration"):
        # We still want the operator to have a cascade-check on record
        # for the migration's surface. The state file's "most recent
        # cascade-check" must mention at least one table. If the operator
        # just submitted the migration without a probe, the gate blocks.
        on_record = _cascade_check_on_record()
        if not on_record:
            return {"exit": 2, "stderr": _gate_message(
                verb="APPLY_MIGRATION",
                target="<see migration body>",
                reason="apply_migration is a write by definition; a cascade-check must be on record for this turn.",
            )}
        return {"exit": 0}

    tool_input = data.get("tool_input", {}) or {}
    text = _extract_text_from_payload(tool_input)

    if not text.strip():
        return {"exit": 0}

    # Supabase MCP execute_sql: gate only on write verbs.
    if tool_name.endswith("execute_sql"):
        # Read-only queries (SELECT, EXPLAIN, …) are never gate-triggering.
        if READ_ONLY_VERBS.match(text):
            # If the read-only body touches a catalog surface, treat it
            # as a cascade-check probe and record it. The doctrine says
            # the probe is the gate's input.
            if _has_cascade_check_surface(text):
                # Try to extract a target table name from the query body;
                # fall back to "<unknown>" if the probe was generic.
                m = re.search(
                    r"(?:FROM|UPDATE|INTO|TABLE)\s+[\"']?([A-Za-z_][\w]*)",
                    text, re.IGNORECASE,
                )
                target = m.group(1) if m else "<catalog-probe>"
                _record_state(target)
            return {"exit": 0}
        verb, table = _first_write_verb(text)
        if verb is None:
            return {"exit": 0}  # Not a write; let it through.
        on_record = _cascade_check_on_record()
        if not on_record or (table and on_record.split("|", 1)[-1] != table):
            return {"exit": 2, "stderr": _gate_message(
                verb=verb, target=table,
                reason="no cascade-check on record for this turn (or for this target table).",
            )}
        return {"exit": 0}

    # Bash: gate on psql / pgcli invocations carrying a write verb.
    if tool_name == "Bash":
        # First — is this even a psql-shaped command?
        is_psql = any(p[1].search(text) for p in PSQL_PATTERNS)
        if not is_psql:
            return {"exit": 0}
        # Read-only psql calls (e.g. \dt, SELECT …) are not gate-triggering.
        if READ_ONLY_VERBS.match(text):
            return {"exit": 0}
        verb, table = _first_write_verb(text)
        if verb is None:
            return {"exit": 0}
        on_record = _cascade_check_on_record()
        if not on_record or (table and on_record.split("|", 1)[-1] != table):
            return {"exit": 2, "stderr": _gate_message(
                verb=verb, target=table,
                reason="no cascade-check on record for this turn (or for this target table).",
            )}
        return {"exit": 0}

    return {"exit": 0}


def _gate_message(verb, target, reason):
    return (
        "⛔ CASCADE-CHECK GATE — direct database write blocked; doctrine not on record.\n"
        f"   Detected:  {verb} on `{target}`\n"
        f"   Reason:    {reason}\n"
        "   The watch-where-you-step doctrine says: walk the catalog (pg_constraint /\n"
        "   pg_depend / pg_trigger / information_schema.referential_constraints) for the\n"
        "   target table, count the cascade fan-out, then state the blast radius aloud.\n"
        "   Either:\n"
        "     1. Run a read-only cascade-check FIRST (e.g. a Supabase MCP execute_sql\n"
        "        or a raw psql -c that touches the catalog tables for this target), OR\n"
        "     2. State the blast radius to the Guild Master and wait for explicit\n"
        "        acknowledgement before re-running the write, OR\n"
        "     3. Per-turn override:  SA_CASCADE_SKIP=1  (logged in the evolution ledger)\n"
        "   See:  star-alliance-skills/watch-where-you-step/SKILL.md\n"
        "   Disarm the gate (off by default — Tier-B gate, human-gated):\n"
        "           touch .claude/state/cascade-check-gate-disarmed\n"
        "   Arm:    rm -f .claude/state/cascade-check-gate-disarmed\n"
    )


def main():
    # Kill switch — disarmed by default. The gate is REGISTERED, NOT
    # ARMED. This is the Tier-B invariant for hooks/gates per the
    # Evolution Engine: human-gated. To arm, the Guild Master must
    # explicitly delete the disarmed sentinel.
    if _disarmed():
        sys.exit(0)

    # Per-turn override — logged via the evolution ledger if a doer
    # later chooses to grade it; here we just stand aside.
    if os.environ.get("SA_CASCADE_SKIP") == "1":
        sys.exit(0)

    try:
        data = json.load(sys.stdin)
    except Exception as e:
        # Fails OPEN on infrastructure errors. A broken safety hook
        # must never trap a session.
        sys.stderr.write(f"[cascade-check-gate] malformed payload, failing open: {e}\n")
        sys.exit(0)

    r = check(data)
    stderr_msg = r.get("stderr") or ""
    if stderr_msg:
        sys.stderr.write(str(stderr_msg))
    exit_code = r.get("exit", 0)
    sys.exit(int(exit_code) if isinstance(exit_code, int) else 0)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        sys.stderr.write(f"[cascade-check-gate] {e}, failing open\n")
        sys.exit(0)
