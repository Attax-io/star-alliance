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

The agent name maps directly to a Hermes profile name. The script:
1. Validates the agent name is a known guild agent.
2. Calls the matching Hermes profile with the prompt.
3. Returns the profile's response as stdout.
"""

import subprocess
import sys
import json
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
    "the-translator":   "Legal codex, law translation, multi-locale content",
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


def main():
    if len(sys.argv) < 3:
        print(
            f"Usage: {sys.argv[0]} <agent-name> <prompt>\n"
            f"       {sys.argv[0]} --list\n"
            f"\nAgents:"
        )
        list_agents()
        sys.exit(1)

    if sys.argv[1] == "--list":
        list_agents()
        sys.exit(0)

    agent_name = sys.argv[1]
    prompt = sys.argv[2]

    # Support reading prompt from a file: --file <path>
    if prompt == "--file" and len(sys.argv) >= 4:
        prompt = Path(sys.argv[3]).read_text()

    result = dispatch(agent_name, prompt)

    # Print response to stdout (for piping), metadata to stderr
    print(result["response"])

    if not result["success"]:
        print(f"\n[dispatch failed — agent={result['agent']}, exit={result['exit_code']}]",
              file=sys.stderr)
        sys.exit(result["exit_code"])


if __name__ == "__main__":
    main()