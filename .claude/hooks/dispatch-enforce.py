#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────────────────
# Star Alliance — DISPATCH ENFORCEMENT  (PreToolUse gate, BLOCKING)
#
# PROBLEM THIS HOOK CLOSES
# ────────────────────────────
# executor-enforce.py blocks the BUTLER (main session) from writing files
# directly. But subagents (specialists) were allowed to write freely. With the
# Hermes bridge in place, specialists must dispatch their work through
# tools/dispatch.py to their Hermes counterparts instead of writing files
# themselves.
#
# WHAT THIS HOOK DOES
# ──────────────────
# For subagent (child) sessions only — the main session is handled by
# executor-enforce.py:
#
#   1. Write/Edit/MultiEdit/NotebookEdit → BLOCK (must dispatch to Hermes)
#   2. Bash command containing `hermes -p ...` or `hermes chat` → BLOCK
#   3. Bash command containing `dispatch.py` → ALLOW *that sub-command only*
#      (chained write commands after && or ; are still blocked)
#   4. Bash write commands (sed -i, echo >, cat >, tee, cp, mv, rm, touch,
#      chmod, chown, > redirect, >> append, python3 -c, perl -i, ruby -e,
#      node -e, heredocs, git checkout/reset/stash/rebase, pip install,
#      npm install, etc.) → BLOCK
#   5. MCP write-verb tools (create_, update_, delete_, write_, etc.) → BLOCK
#   6. Read-only tools and commands → ALLOW
#
# BYPASSES
# ────────
# Kill switches (independent from executor-enforce.py):
#   • evolution/DISARMED                      (engine-wide — disarms everything)
#   • .claude/state/dispatch-enforce-disarmed (this hook only — disarms agents,
#                                              leaves the Butler's hook armed)
#   • .claude/state/executor-enforce-disarmed (legacy shared switch — disarms both)
#
# FAIL POSTURE
# ────────────
# Fail OPEN on any internal error — a broken hook must never brick the session.
# ─────────────────────────────────────────────────────────────────────────────
import os
import sys
import json
import re
import shlex

# Tools that specialists are NOT allowed to use directly — they must dispatch
# through dispatch.py to their Hermes counterpart.
BLOCKED_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}

# Patterns that indicate a direct Hermes call (bypassing dispatch.py).
HERMES_DIRECT_PATTERNS = [
    re.compile(r'\bhermes\s+(-p\b|--profile\b)', re.IGNORECASE),
    re.compile(r'\bhermes\s+chat\b', re.IGNORECASE),
]

# dispatch.py is the allowed path — but only for the sub-command that contains
# it. Chained commands after &&, ||, ;, | are checked separately.
DISPATCH_MARKER = "dispatch.py"

# ── Shell command splitting ─────────────────────────────────────────────────
# Chain delimiters that separate sub-commands in a Bash string.
CHAIN_SPLIT_RE = re.compile(r'(?:&&|\|\||;|\|)')


def _strip_quoted(command):
    """Replace content inside quoted strings with spaces, preserving length.

    This lets the write-pattern regex match against the command structure
    (where write operators actually appear) without false-positiving on
    incidental words like 'touch', 'rm', or pipes inside prose, markdown
    tables, or prompt text wrapped in quotes.

    Handles single quotes, double quotes, and backslash-escaped quotes.
    Quote characters themselves are left in place so positional anchors
    (^, ;, &, etc.) still match correctly.
    """
    out = []
    i = 0
    n = len(command)
    while i < n:
        ch = command[i]
        if ch == "\\" and i + 1 < n:
            # Skip escape — preserve the next char's slot
            out.append(command[i])
            out.append(" ")
            i += 2
            continue
        if ch in ('"', "'"):
            quote = ch
            out.append(quote)
            i += 1
            while i < n and command[i] != quote:
                if command[i] == "\\" and i + 1 < n:
                    out.append(" ")
                    out.append(" ")
                    i += 2
                else:
                    out.append(" ")
                    i += 1
            if i < n:
                out.append(quote)  # closing quote
                i += 1
            continue
        out.append(ch)
        i += 1
    return "".join(out)

# ── Shell write patterns ────────────────────────────────────────────────────
# Commands that mutate files via shell. Applied to each sub-command individually.
BASH_WRITE_PATTERNS = (
    # Direct file redirects
    r"(?<!\{)\bcat\s*>\s*\S",                # cat > file
    r"\becho\s+.+?\s*>\s*\S",                # echo "..." > file
    r"\bprintf\s+.+?\s*>\s*\S",              # printf "..." > file
    r"\btee\s+\S",                            # tee file
    # Bare > / >> redirects require a leading shell position so they don't
    # over-match on `>` inside filesystem paths (e.g. /Users/.../Projects/...).
    # Allowed leading positions: start-of-line, ;, &, |, (, ), or whitespace.
    r"(?:^|[;&|()\s])\s*>\s*\S",             # bare > redirect (shell-position)
    r"(?:^|[;&|()\s])\s*>>\s*\S",            # bare >> append (shell-position)
    r":\s*>\s*\S",                           # : > truncate
    # File mutation commands
    r"\bsed\s+-i\b",                         # sed -i
    r"\bcp\s+\S+\s+\S+",                     # cp src dst
    r"\bmv\s+\S+\s+\S+",                      # mv src dst
    r"\brm\s+(-\w+\s+)*\S",                   # rm [flags] path
    r"\brmdir\s+\S",                          # rmdir path
    r"\bmkdir\s+(-\w+\s+)*\S",                # mkdir [flags] path
    r"\btouch\s+\S",                          # touch file
    r"\bchmod\s+",                            # chmod
    r"\bchown\s+",                            # chown
    r"\bdd\s+",                               # dd of=...
    # Interpreters that can write files
    r"\bpython3?\s+-c\b",                     # python3 -c "..."
    r"\bpython3?\s+--?b\b",                    # python3 -b (boundary issue, rare)
    r"\bperl\s+-i\b",                          # perl -i (in-place edit)
    r"\bperl\s+-e\b",                          # perl -e "..."
    r"\bruby\s+-e\b",                          # ruby -e "..."
    r"\bnode\s+-e\b",                          # node -e "..."
    r"\bnode\s+--eval\b",                      # node --eval
    # Heredocs (can feed arbitrary code to an interpreter)
    r"<<\s*['\"]?\w+",                         # << EOF, <<'EOF', <<WORD
    # Package managers that write to disk
    r"\bpip3?\s+install\b",                    # pip install
    r"\buv\s+pip\s+install\b",                # uv pip install
    r"\bnpm\s+install\b",                     # npm install
    r"\bnpm\s+i\b(?!\S)",                      # npm i (short form)
    r"\byarn\s+add\b",                         # yarn add
    r"\bcargo\s+install\b",                    # cargo install
    # Git mutations that overwrite files
    r"\bgit\s+checkout\s+--\s*\S",             # git checkout -- file
    r"\bgit\s+checkout\s+\S+\s+--\s*\S",       # git checkout <ref> -- file
    r"\bgit\s+reset\s+--hard\b",               # git reset --hard
    r"\bgit\s+stash\b",                        # git stash (modifies working tree)
    r"\bgit\s+rebase\b",                       # git rebase (rewrites history)
    r"\bgit\s+clean\s+-[a-zA-Z]*f",            # git clean -f (deletes files)
    r"\bgit\s+rm\b",                           # git rm
    # Other file-writing commands
    r"\binstall\s+-m\b",                       # install -m (copies with perms)
    r"\brsync\b",                              # rsync can write files
    r"\bscp\b",                                # scp copies files
    r"\bcurl\s+.+?\s*>\s*\S",                  # curl ... > file
    r"\bwget\b",                               # wget (can write files with -O or default)
    r"\bunpack\s+\S",                          # unpack
    r"\bunzip\s+\S",                           # unzip
    r"\btar\s+.*-[a-zA-Z]*x",                  # tar -x, tar -xf, tar -xz, tar -xzf, etc.
    r"\b7z\s+.*\s+e\b",                        # 7z e (extracts)
    r"\bmake\b(?!\s+--version)(?!.*check)",    # make (can write build artifacts)
    # Text editors (interactive, but can write)
    r"\bvim?\b\s+\S",                          # vim/vi file
    r"\bnano\b\s+\S",                          # nano file
    r"\bemacs\b\s+\S",                         # emacs file
)
BASH_WRITE_RE = re.compile("|".join(BASH_WRITE_PATTERNS))

# ── MCP write-verb detection ────────────────────────────────────────────────
# MCP tools whose names start with a write verb are blocked for specialists.
MCP_WRITE_VERBS = (
    "create_", "update_", "delete_", "insert_", "drop_", "truncate_",
    "put_", "patch_", "set_", "add_", "remove_", "upsert_", "merge_",
    "write_", "append_", "modify_", "rename_", "move_",
    "alter_", "execute_", "run_", "apply_", "save_",
)
# Explicit read-verb allowlist — overrides the write heuristic.
MCP_READ_VERBS = (
    "get_", "list_", "fetch_", "read_", "find_", "search_", "query_",
    "describe_", "show_", "view_", "lookup_", "select_",
)


def _project_dir():
    return os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def _state_dir():
    return os.path.join(_project_dir(), ".claude", "state")


def _is_kill_switch():
    if os.path.exists(os.path.join(_project_dir(), "evolution", "DISARMED")):
        return True
    if os.path.exists(os.path.join(_state_dir(), "dispatch-enforce-disarmed")):
        return True
    if os.path.exists(os.path.join(_state_dir(), "executor-enforce-disarmed")):
        return True
    return False


def _split_commands(command):
    """Split a Bash command string on chain operators (&&, ||, ;, |).

    Returns a list of sub-command strings. Handles quoting minimally —
    if shlex.split fails, falls back to regex splitting.
    """
    # Try shlex first (respects quotes), but shlex doesn't understand shell
    # control operators well. Use regex split instead — good enough for
    # security checks since we're looking for patterns, not executing.
    parts = CHAIN_SPLIT_RE.split(command)
    return [p.strip() for p in parts if p.strip()]


def _check_mcp(tool, data):
    """Check if an MCP tool call is a write operation. Returns block dict or None."""
    # Extract the tool part of `mcp__<server>__<tool>`.
    parts = tool.split("__")
    tool_part = parts[-1] if len(parts) >= 2 else tool
    tool_lower = tool_part.lower()

    # Explicit read-verb allowlist wins.
    if any(tool_lower.startswith(v) for v in MCP_READ_VERBS):
        return None

    if any(tool_lower.startswith(v) for v in MCP_WRITE_VERBS):
        ti = data.get("tool_input") or {}
        preview = json.dumps(ti)[:200] if ti else ""
        return {
            "exit": 2,
            "stderr": (
                f"⛔ BLOCKED — MCP write tool `{tool}` is not allowed for specialists.\n"
                f"\n"
                f"WHY: You are a Claude-side specialist. All file and data writes must go\n"
                f"through your Hermes counterpart so the work is done with the right model,\n"
                f"the right tools, and the right audit trail. Writing directly — whether\n"
                f"through file edits, shell commands, or MCP tools — bypasses that pipeline\n"
                f"and is blocked by the dispatch enforcement hook.\n"
                f"\n"
                f"WHAT TO DO: Send this task to your Hermes profile via the dispatch script.\n"
                f"Frame the prompt so Hermes can do the work with its own tools:\n"
                f"\n"
                f"  python3 tools/dispatch.py <your-agent-name> \"<describe the task in detail>\"\n"
                f"\n"
                f"  Examples:\n"
                f"    python3 tools/dispatch.py the-architect \"Create a table called 'orders' with columns: id uuid, total numeric, created_at timestamptz\"\n"
                f"    python3 tools/dispatch.py the-developer \"Insert a row into the users table with name='test' and email='test@test.com'\"\n"
                f"\n"
                f"  The Hermes profile will receive your prompt, do the work with its own tools,\n"
                f"  and return the result. You then relay that result back to the caller.\n"
                f"\n"
                f"NOTE: Read-only MCP tools (get_, list_, search_, query_, describe_, etc.)\n"
                f"are still allowed — you can read data directly. Only writes are dispatched.\n"
            ),
        }

    # Unknown MCP tool — allow but don't block (fail open for new MCP servers).
    return None


def check(data):
    """Gate entry point — called by sa-pretool.py dispatcher.

    Returns a dict: {"exit": 0|2, "stderr": str, "systemMessage": str}
    Exit 0 = allow, Exit 2 = block.
    """
    if _is_kill_switch():
        return {"exit": 0}

    # Only enforce for child sessions (subagents / specialists).
    # The main session (Butler) is already handled by executor-enforce.py.
    is_child = os.environ.get("CLAUDE_CODE_CHILD_SESSION") == "1"
    if not is_child:
        return {"exit": 0}

    tool = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})

    # ── Block direct file edits (Write/Edit/MultiEdit/NotebookEdit) ──────
    if tool in BLOCKED_TOOLS:
        file_path = (
            tool_input.get("file_path")
            or tool_input.get("notebook_path")
            or "<unknown>"
        )
        return {
            "exit": 2,
            "stderr": (
                f"⛔ BLOCKED — {tool} is not allowed for specialists.\n"
                f"\n"
                f"WHY: You are a Claude-side specialist. Your job is to frame the task\n"
                f"and relay it to your Hermes counterpart — not to write files yourself.\n"
                f"Hermes has its own file tools, its own model, and its own audit trail.\n"
                f"Writing directly here bypasses that entire pipeline, which is why the\n"
                f"dispatch enforcement hook blocks it.\n"
                f"\n"
                f"WHAT TO DO: Send this task to your Hermes profile via the dispatch script.\n"
                f"Describe the edit in enough detail that Hermes can do it with its own tools:\n"
                f"\n"
                f"  python3 tools/dispatch.py <your-agent-name> \"<describe the task in detail>\"\n"
                f"\n"
                f"  Examples:\n"
                f"    python3 tools/dispatch.py the-architect \"Add a 'created_at' column to the orders table\"\n"
                f"    python3 tools/dispatch.py the-developer \"Fix the login bug in auth.py — the token check is missing a return statement on line 42\"\n"
                f"    python3 tools/dispatch.py the-designer \"Update the button color in styles.css to use the brand-blue token\"\n"
                f"\n"
                f"  The Hermes profile will receive your prompt, make the edit with its own\n"
                f"  tools, and return the result. You then relay that result back to the caller.\n"
                f"\n"
                f"NOTE: Reading files is still allowed — you can read any file to understand\n"
                f"the codebase before dispatching. Only writes and edits are dispatched.\n"
            ),
        }

    # ── Block MCP write tools ───────────────────────────────────────────
    if tool.startswith("mcp__"):
        result = _check_mcp(tool, data)
        if result:
            return result
        return {"exit": 0}

    # ── Block shell writes and direct Hermes calls ──────────────────────
    if tool == "Bash":
        command = tool_input.get("command", "") or ""

        # Strip quoted-string contents first so write-pattern matches target
        # the command structure (where operators actually live) and not the
        # prose inside prompt text. Then split on chain operators so a
        # dispatch.py call can't be used as a piggyback for a write command.
        scan_command = _strip_quoted(command)
        sub_commands = _split_commands(scan_command)

        for sub_cmd in sub_commands:
            # If this sub-command is the dispatch.py call, allow it.
            if DISPATCH_MARKER in sub_cmd:
                continue

            # Check for direct hermes calls.
            for pattern in HERMES_DIRECT_PATTERNS:
                if pattern.search(sub_cmd):
                    return {
                        "exit": 2,
                        "stderr": (
                            f"⛔ BLOCKED — Direct `hermes` calls are not allowed for specialists.\n"
                            f"\n"
                            f"WHY: Calling `hermes -p ...` directly bypasses the dispatch script,\n"
                            f"which means the call isn't logged, the profile name isn't validated,\n"
                            f"and there's no audit trail. The dispatch enforcement hook blocks\n"
                            f"this so every dispatch goes through one sanctioned, logged path.\n"
                            f"\n"
                            f"WHAT TO DO: Use the dispatch script instead. It does the same thing\n"
                            f"(calls your Hermes profile) but with validation and logging:\n"
                            f"\n"
                            f"  python3 tools/dispatch.py <your-agent-name> \"<describe the task in detail>\"\n"
                            f"\n"
                            f"  Examples:\n"
                            f"    python3 tools/dispatch.py the-architect \"Design a schema for a legal document system\"\n"
                            f"    python3 tools/dispatch.py the-developer \"Refactor the auth module to use async/await\"\n"
                            f"\n"
                            f"  The script sends your prompt to the correct Hermes profile and returns\n"
                            f"  the result. You then relay that result back to the caller.\n"
                        ),
                    }

            # Check for shell write commands.
            if BASH_WRITE_RE.search(sub_cmd):
                # Show the user the ORIGINAL (unstripped) command so the
                # block message includes the prose they actually wrote,
                # not blanks where the quoted content used to be.
                preview = command[:200] + ("..." if len(command) > 200 else "")
                return {
                    "exit": 2,
                    "stderr": (
                        f"⛔ BLOCKED — Shell command writes a file, which is not allowed for specialists.\n"
                        f"\n"
                        f"WHY: You tried to modify files via a shell command. Whether it's a redirect\n"
                        f"(echo >, cat >), an in-place edit (sed -i), a copy/move (cp, mv), a git\n"
                        f"mutation (checkout, reset, stash, rm), an interpreter one-liner\n"
                        f"(python3 -c, perl -e, ruby -e, node -e), a package install (pip, npm),\n"
                        f"or an archive extraction (tar -x, unzip) — all file writes must go through\n"
                        f"your Hermes counterpart, not the shell. The dispatch enforcement hook blocks\n"
                        f"these so the work is done with the right model and the right audit trail.\n"
                        f"\n"
                        f"  Command that was blocked:\n"
                        f"    {preview}\n"
                        f"\n"
                        f"WHAT TO DO: Send this task to your Hermes profile via the dispatch script.\n"
                        f"Describe what the shell command was supposed to do so Hermes can do it\n"
                        f"with its own tools:\n"
                        f"\n"
                        f"  python3 tools/dispatch.py <your-agent-name> \"<describe the task in detail>\"\n"
                        f"\n"
                        f"  Examples:\n"
                        f"    python3 tools/dispatch.py the-developer \"Run the test suite and report results\"\n"
                        f"    python3 tools/dispatch.py the-architect \"Install the Supabase CLI and run a migration\"\n"
                        f"\n"
                        f"  The Hermes profile has full terminal access and can run shell commands itself.\n"
                        f"You frame the task; Hermes executes it.\n"
                        f"\n"
                        f"NOTE: Read-only shell commands (ls, cat, grep, git status, git log, git diff)\n"
                        f"are still allowed — you can inspect the codebase directly. Only writes are\n"
                        f"dispatched.\n"
                    ),
                }

    # Everything else — allow.
    return {"exit": 0}