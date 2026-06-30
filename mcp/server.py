#!/usr/bin/env python3
"""Star Alliance MCP Server — exposes guild skills and agents as MCP tools."""

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Self-location — resolve repo root from this file's location
REPO_ROOT = Path(__file__).resolve().parent.parent
CALLER_CWD = os.getcwd()

# Make repo importable so tools.dispatch is reachable
sys.path.insert(0, str(REPO_ROOT))

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("star-alliance")

TELEMETRY_FILE = REPO_ROOT / "data" / "mcp-telemetry.jsonl"
SKILLS_DIR = REPO_ROOT / "star-alliance-skills"


def _log(tool: str, arguments: dict, success: bool, duration_ms: int, result_preview: str) -> None:
    """Append one telemetry line. Never raises."""
    try:
        entry = {
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
            "tool": tool,
            "arguments": arguments,
            "caller_cwd": CALLER_CWD,
            "success": success,
            "duration_ms": duration_ms,
            "result_preview": str(result_preview)[:200],
        }
        with open(TELEMETRY_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass


@mcp.tool()
def list_skills() -> list:
    """List all available Star Alliance skills."""
    t0 = time.monotonic()
    try:
        skills = sorted(
            d.name for d in SKILLS_DIR.iterdir()
            if d.is_dir() and (d / "SKILL.md").exists()
        )
        _log("list_skills", {}, True, int((time.monotonic() - t0) * 1000), str(skills[:5]))
        return skills
    except Exception as e:
        _log("list_skills", {}, False, int((time.monotonic() - t0) * 1000), str(e))
        return []


@mcp.tool()
def list_agents() -> list:
    """List all dispatchable Star Alliance agents."""
    t0 = time.monotonic()
    try:
        from tools.dispatch import AGENTS
        agents = sorted(AGENTS.keys())
        _log("list_agents", {}, True, int((time.monotonic() - t0) * 1000), str(agents))
        return agents
    except Exception as e:
        _log("list_agents", {}, False, int((time.monotonic() - t0) * 1000), str(e))
        return []


@mcp.tool()
def invoke_skill(skill_name: str, args: str = "") -> str:
    """
    Return the SKILL.md document for the named skill.
    The calling agent reads and follows the returned instructions.
    """
    t0 = time.monotonic()
    # Security: block path traversal
    if any(c in skill_name for c in ("/", "..", "\\")):
        msg = f"ERROR: invalid skill name '{skill_name}'"
        _log("invoke_skill", {"skill_name": skill_name}, False, int((time.monotonic() - t0) * 1000), msg)
        return msg
    skill_path = SKILLS_DIR / skill_name / "SKILL.md"
    if not skill_path.exists():
        msg = f"ERROR: skill '{skill_name}' not found. Use list_skills() to see available skills."
        _log("invoke_skill", {"skill_name": skill_name}, False, int((time.monotonic() - t0) * 1000), msg)
        return msg
    text = skill_path.read_text(encoding="utf-8")
    if args:
        text += f"\n\n---\n## Invocation context\n{args}"
    arguments = {"skill_name": skill_name}
    if args:
        arguments["args"] = args
    _log("invoke_skill", arguments, True, int((time.monotonic() - t0) * 1000), text[:200])
    return text


@mcp.tool()
def dispatch_agent(agent_name: str, prompt: str) -> str:
    """
    Dispatch a task to a Star Alliance guild agent and return its response.
    Use list_agents() to see available agents.
    """
    t0 = time.monotonic()
    try:
        from tools.dispatch import dispatch, AGENTS
    except ImportError as e:
        msg = f"ERROR: could not import dispatch module: {e}"
        _log("dispatch_agent", {"agent_name": agent_name, "prompt": prompt[:100]}, False,
             int((time.monotonic() - t0) * 1000), msg)
        return msg

    if agent_name not in AGENTS:
        msg = f"ERROR: unknown agent '{agent_name}'. Known agents: {', '.join(sorted(AGENTS.keys()))}"
        _log("dispatch_agent", {"agent_name": agent_name, "prompt": prompt[:100]}, False,
             int((time.monotonic() - t0) * 1000), msg)
        return msg

    try:
        result = dispatch(agent_name, prompt)
        success = result.get("success", False)
        response = result.get("response", "")
        _log("dispatch_agent", {"agent_name": agent_name, "prompt": prompt[:100]},
             success, int((time.monotonic() - t0) * 1000), response[:200])
        return response
    except FileNotFoundError:
        msg = f"ERROR: Hermes CLI not found. Is hermes installed and on PATH?"
        _log("dispatch_agent", {"agent_name": agent_name, "prompt": prompt[:100]}, False,
             int((time.monotonic() - t0) * 1000), msg)
        return msg
    except TimeoutError:
        msg = f"ERROR: agent '{agent_name}' timed out"
        _log("dispatch_agent", {"agent_name": agent_name, "prompt": prompt[:100]}, False,
             int((time.monotonic() - t0) * 1000), msg)
        return msg


if __name__ == "__main__":
    mcp.run()
