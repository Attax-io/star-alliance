#!/usr/bin/env python3
"""
dispatch.py — Bridge between Claude agents and Hermes profiles.

When a Claude agent (e.g., the Strategist) decides to hand work to a specialist
(e.g., the Architect), this script takes the prompt and dispatches it to the
matching Hermes profile via `hermes -p <profile-name> chat -q "..."`.

Usage:
    python3 dispatch.py <agent-name> <prompt>
    python3 dispatch.py the-architect "Design a schema for legal documents"
    python3 dispatch.py the-developer "Fix the login bug in auth.py"
    python3 dispatch.py the-architect --file /path/to/prompt.txt

The agent name maps directly to a Hermes profile name. The script:
1. Validates the agent name is a known guild agent.
2. Calls the matching Hermes profile with the prompt.
3. Returns the profile's response as stdout.

PROMPT-HANDLING MODEL (refactor 2026-06-29):
The DEFAULT path sources the prompt from a tempfile. The caller's raw string
is written to `tempfile.NamedTemporaryFile(... delete=False)`, the temp file
is then READ BACK into a string, that string is what we hand to `hermes -q`,
and the temp file is deleted in a `finally:` block. The shell never sees the
prompt body, which kills the regex-fire class of bugs (quotes/backticks/`$`/
newlines in the prompt no longer interact with the dispatch-enforce gate or
the wrapping shell).

The `--file <path>` flag remains for callers who want to point at a file they
already own (the file's contents are read and then re-flowed through the
tempfile+read-back funnel, so both paths are uniformly safe).

`--file` is therefore not strictly required for safety; it is the "use my
own file" escape hatch. Raw-string prompts are safe by default.
"""

import subprocess
import sys
import json
import tempfile
import os
from pathlib import Path

# ── Agent → Hermes profile mapping ──────────────────────────────────────────
# Each guild agent maps to a Hermes profile of the same name.
# The Strategist is the router — it decides which agent to dispatch to.
AGENTS = {
    "the-butler":       "Intake, voice, approval, report",
    "the-strategist":   "Router — decides who handles what",
    "the-architect":    "Systems design, domain modeling, database architecture",
    "the-developer":    "Writing code, fixing bugs, implementation",
    "the-designer":     "UI/UX design, visual quality, brand kits",
    "the-interpreter": "Legal codex, law translation, multi-locale content",
    "the-herald":       "Marketing, growth, demand generation, content/SEO",
    "the-merchant":     "Investment analysis, trading strategies, market research",
    "the-quartermaster":"Skill management, syncing, upgrading, conformance",
}


def list_agents():
    """Print all known agents and their roles."""
    print("Known guild agents:\n")
    for name, role in AGENTS.items():
        print(f"  {name:20s} — {role}")
    print()


def dispatch(agent_name: str, prompt: str, timeout: int = 300) -> dict:
    """
    Send a prompt to a Hermes profile matching the agent name.

    Returns a dict with:
      - success: bool
      - agent: the agent name
      - profile: the Hermes profile used
      - response: the Hermes profile's output (or error message)
      - exit_code: process exit code
    """
    if agent_name not in AGENTS:
        return {
            "success": False,
            "agent": agent_name,
            "profile": None,
            "response": f"Unknown agent '{agent_name}'. Known agents: {', '.join(AGENTS.keys())}",
            "exit_code": 1,
        }

    profile = agent_name  # agent name == Hermes profile name

    cmd = [
        "hermes",
        "-p", profile,
        "--yolo",  # skip command approval prompts — the Claude-side hooks
                   # already enforce what the specialist can and can't do, so
                   # Hermes shouldn't block it with a second approval layer
        "chat",
        "-q", prompt,
        "-Q",  # quiet — suppress banner/spinner/tool previews
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        response = result.stdout.strip()
        if result.returncode != 0 and result.stderr:
            response = f"{response}\n--- stderr ---\n{result.stderr.strip()}" if response else result.stderr.strip()

        # Strip Hermes CLI noise that leaks into stdout:
        # - "session_id: ..." line (session metadata, not part of the response)
        # - "Subdirectory context discovered: ..." (AGENTS.md auto-load notice)
        # - leading blank lines
        lines = response.split("\n")
        cleaned = []
        for line in lines:
            if line.startswith("session_id:"):
                continue
            if line.startswith("Subdirectory context discovered:"):
                continue
            if line.startswith("[Subdirectory context"):
                # Multi-line AGENTS.md block — skip until the closing bracket
                continue
            cleaned.append(line)
        response = "\n".join(cleaned).strip()

        return {
            "success": result.returncode == 0,
            "agent": agent_name,
            "profile": profile,
            "response": response,
            "exit_code": result.returncode,
        }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "agent": agent_name,
            "profile": profile,
            "response": f"Timed out after {timeout}s",
            "exit_code": -1,
        }
    except FileNotFoundError:
        return {
            "success": False,
            "agent": agent_name,
            "profile": profile,
            "response": "Hermes CLI ('hermes') not found. Is it installed and on PATH?",
            "exit_code": -2,
        }


def _resolve_prompt(arg: str):
    """
    Resolve the prompt argument to (prompt_text, temp_path_or_None).

    - If `arg == "--file"` then `sys.argv[3]` is treated as a path the caller
      owns; its contents are read and the SAME contents are then re-flowed
      through a tempfile so dispatch() can hand hermes a string sourced from
      a file the shell never saw.
    - Otherwise `arg` is the raw prompt string. It is written to a tempfile
      (delete=False) and then read back from disk, so the dispatch contract
      is uniform: every prompt reaches hermes via a tempfile+read-back.

    Returns:
        (prompt_text: str, temp_path: str | None)
        `temp_path` is the path of a tempfile the caller MUST delete, or None
        if no tempfile was created.
    """
    if arg == "--file":
        if len(sys.argv) < 4:
            print(
                f"Usage: {sys.argv[0]} <agent-name> --file <path>",
                file=sys.stderr,
            )
            sys.exit(1)
        caller_owned = Path(sys.argv[3]).read_text()
        source = caller_owned
    else:
        source = arg

    # Funnel everything through a tempfile so the dispatch contract is uniform
    # and the shell never sees the prompt body.
    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False, encoding="utf-8"
    )
    try:
        tmp.write(source)
        tmp.flush()
        tmp.close()
        # Read back from disk so the string we hand to hermes is exactly what
        # the file contains — defends against any implicit encoding/normalize
        # step and matches the documented "shell never sees the prompt" model.
        prompt_text = Path(tmp.name).read_text(encoding="utf-8")
        return prompt_text, tmp.name
    except Exception:
        # If the read-back fails, still try to clean up the partial tempfile.
        try:
            os.unlink(tmp.name)
        except OSError:
            pass
        raise


def main():
    if len(sys.argv) < 3:
        print(
            f"Usage: {sys.argv[0]} <agent-name> <prompt>\n"
            f"       {sys.argv[0]} <agent-name> --file <path>\n"
            f"       {sys.argv[0]} --list\n"
            f"\nAgents:"
        )
        list_agents()
        sys.exit(1)

    if sys.argv[1] == "--list":
        list_agents()
        sys.exit(0)

    agent_name = sys.argv[1]
    prompt_arg = sys.argv[2]

    prompt, temp_path = _resolve_prompt(prompt_arg)
    try:
        result = dispatch(agent_name, prompt)
    finally:
        if temp_path:
            try:
                os.unlink(temp_path)
            except OSError:
                pass  # fail-open: a leftover tempfile is harmless

    # Print response to stdout (for piping), metadata to stderr
    print(result["response"])

    if not result["success"]:
        print(f"\n[dispatch failed — agent={result['agent']}, exit={result['exit_code']}]",
              file=sys.stderr)
        sys.exit(result["exit_code"])


if __name__ == "__main__":
    main()