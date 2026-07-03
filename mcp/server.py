#!/usr/bin/env python3
"""Star Alliance MCP Server — exposes guild skills and agents as MCP tools."""

import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Self-location — resolve repo root from this file's location
REPO_ROOT = Path(__file__).resolve().parent.parent
CALLER_CWD = os.getcwd()

# Make repo importable for local helpers.
sys.path.insert(0, str(REPO_ROOT))

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("star-alliance")

TELEMETRY_FILE = REPO_ROOT / "data" / "mcp-telemetry.jsonl"
SKILLS_DIR = REPO_ROOT / "star-alliance-skills"
AGENTS_DIR = REPO_ROOT / ".claude" / "agents"
XP_LOG = REPO_ROOT / ".claude" / "state" / "xp-log.jsonl"

_FM_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.S)


def _agent_frontmatter(path: Path) -> dict:
    """Parse the YAML-ish frontmatter of a .claude/agents/*.md file into a dict.

    Only the flat scalar fields we need (name, description) are read; no YAML
    dependency. Never raises — returns {} on any problem.
    """
    try:
        txt = path.read_text(encoding="utf-8")
    except Exception:
        return {}
    m = _FM_RE.match(txt)
    if not m:
        return {}
    fields: dict = {}
    for line in m.group(1).splitlines():
        mm = re.match(r"([A-Za-z_][\w-]*)\s*:\s*(.*)$", line)
        if mm:
            val = mm.group(2).strip()
            if len(val) >= 2 and val[0] in "\"'" and val[-1] == val[0]:
                val = val[1:-1]
            fields[mm.group(1)] = val
    return fields


def _roster() -> dict:
    """Map agent id (filename stem, e.g. 'the-architect') -> its frontmatter dict.

    The Star Alliance agents are the Claude subagent definitions under
    .claude/agents/. Each file's stem is the agent id / subagent_type. Never
    raises — returns {} if the directory is missing.
    """
    roster: dict = {}
    try:
        for path in sorted(AGENTS_DIR.glob("*.md")):
            fields = _agent_frontmatter(path)
            roster[path.stem] = fields
    except Exception:
        pass
    return roster


def _xp_skill(name: str) -> None:
    """Record one skill-usage row so a skill pulled through the MCP earns XP too,
    not only when invoked via the Skill tool (closes the skill-telemetry gap).
    Same schema tools/xp.py counts. Never raises."""
    try:
        XP_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(XP_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "type": "skill", "name": str(name).strip(),
                "ts": datetime.now(timezone.utc).isoformat(), "via": "mcp",
            }) + "\n")
    except Exception:
        pass


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
    """List all Star Alliance agents (Claude subagents) with their descriptions.

    Each agent is a Claude subagent defined under .claude/agents/. The returned
    ``name`` is the id you pass as ``agent_name`` to dispatch_agent() (and as
    ``subagent_type`` when spawning it via the Task/Agent tool).
    """
    t0 = time.monotonic()
    try:
        agents = [
            {"name": agent_id, "description": fields.get("description", "")}
            for agent_id, fields in sorted(_roster().items())
        ]
        _log("list_agents", {}, True, int((time.monotonic() - t0) * 1000),
             str([a["name"] for a in agents]))
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
    _xp_skill(skill_name)  # skill earns XP for a real MCP pull, not just Skill-tool calls
    _log("invoke_skill", arguments, True, int((time.monotonic() - t0) * 1000), text[:200])
    return text


@mcp.tool()
def dispatch_agent(agent_name: str, prompt: str) -> str:
    """
    Resolve a Star Alliance guild agent so the calling session can spawn it.

    Star Alliance is a Claude-only harness: its agents are Claude subagents, not
    an external service this server can shell out to. This tool therefore does
    NOT run the agent itself — there is no separate doer process to call. It
    validates the agent name and returns clear instructions plus the echoed
    prompt, so the CALLING Claude session can spawn the subagent with its own
    Task/Agent tool (subagent_type=<agent_name>). Use list_agents() to see the
    available agents.
    """
    t0 = time.monotonic()
    roster = _roster()

    if agent_name not in roster:
        known = ", ".join(sorted(roster.keys())) or "(none found)"
        msg = (f"ERROR: unknown agent '{agent_name}'. "
               f"Known agents: {known}. Use list_agents() to see them.")
        _log("dispatch_agent", {"agent_name": agent_name, "prompt": prompt[:100]}, False,
             int((time.monotonic() - t0) * 1000), msg)
        return msg

    description = roster[agent_name].get("description", "")
    payload = {
        "status": "spawn_required",
        "agent": agent_name,
        "description": description,
        "prompt": prompt,
        "instructions": (
            "Star Alliance agents are Claude subagents, not an external service. "
            "This MCP server cannot run the agent for you. Spawn it from your own "
            f"Claude session with the Task/Agent tool, passing subagent_type='{agent_name}' "
            "and the prompt below."
        ),
    }
    result = json.dumps(payload, ensure_ascii=False, indent=2)
    _log("dispatch_agent", {"agent_name": agent_name, "prompt": prompt[:100]},
         True, int((time.monotonic() - t0) * 1000), result[:200])
    return result


if __name__ == "__main__":
    mcp.run()
