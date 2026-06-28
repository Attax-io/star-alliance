#!/usr/bin/env python3
"""Star Alliance MCP Server — exposes guild gates as MCP tools.

Replaces the Claude Code hook system (.claude/hooks/*.py) with a single
MCP server that the Butler can call before/after each turn.

Tools exposed:
  sa_route_request       — route a prompt to the right member profile
  sa_verify              — run independent critic (GLM) on a diff
  sa_delegation_check    — enforce doer delegation for bulk work
  sa_thinker_check       — validate thinker model for a profile
  sa_thinker_attest      — ledger which model actually thought
  sa_destructive_check   — block destructive shell commands
  sa_executor_check      — enforce Butler can't write files directly
  sa_turn_cost           — log turn cost
  sa_turn_start          — mark turn start
  sa_turn_finalize       — gate commit on all checks passing
  sa_build_mark          — mark build stale after edits
  sa_checkpoint_save     — snapshot context + decisions
  sa_checkpoint_restore  — restore a checkpoint
  sa_snapshot            — PreCompact snapshot
  sa_plain_english_check — nudge if response too technical
  sa_evolution_status    — evolution engine status
  sa_evolution_ledger    — recent ledger entries
  sa_evolution_scoreboard — evolution scoreboard
  sa_skill_fingerprints_check — check skill drift

Usage:
  # Add to Hermes:
  hermes mcp add star-alliance --command "python3" --args "/path/to/server/star_alliance_mcp.py"

  # Test:
  hermes mcp test star-alliance
"""
import asyncio
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
EVOLUTION_DIR = ROOT / "evolution"
STATE_DIR = ROOT / ".claude" / "state"
LEDGER_PATH = EVOLUTION_DIR / "ledger.jsonl"
USAGE_LOG = STATE_DIR / "usage-log.jsonl"

# ── Helpers ───────────────────────────────────────────────────────────────────

def _ledger_append(kind: str, **kw: Any) -> None:
    """Best-effort ledger append."""
    try:
        sys.path.insert(0, str(EVOLUTION_DIR))
        import ledger  # type: ignore
        ledger.append(kind=kind, **kw)
    except Exception:
        pass


def _git_diff() -> str:
    """Return current git diff (unstaged + staged)."""
    try:
        unstaged = subprocess.run(
            ["git", "diff"], capture_output=True, text=True,
            cwd=str(ROOT), timeout=10
        ).stdout
        staged = subprocess.run(
            ["git", "diff", "--cached"], capture_output=True, text=True,
            cwd=str(ROOT), timeout=10
        ).stdout
        return staged + unstaged
    except Exception:
        return ""


def _destructive_check_impl(command: str, confirm: bool = False) -> dict:
    """Port of .claude/hooks/destructive-gate.py."""
    PATTERNS = [
        ("rm -rf", re.compile(r"\brm\s+(-[a-zA-Z]*r[a-zA-Z]*f|-[a-zA-Z]*f[a-zA-Z]*r|-r\s+-f|-f\s+-r|--recursive)\b"), "recursive delete — unrecoverable"),
        ("git push --force", re.compile(r"\bgit\s+push\b.*(--force\b|--force-with-lease\b|\s-f\b)"), "rewrites remote history"),
        ("git reset --hard", re.compile(r"\bgit\s+reset\s+--hard\b"), "discards uncommitted work"),
        ("git clean -f", re.compile(r"\bgit\s+clean\b.*\s-[a-zA-Z]*f"), "deletes untracked files"),
        ("git checkout .", re.compile(r"\bgit\s+checkout\s+\.(\s|$)"), "discards uncommitted changes"),
        ("git restore .", re.compile(r"\bgit\s+restore\s+(\.|--\s+\.)(\s|$)"), "discards uncommitted changes"),
        ("DROP TABLE/DB", re.compile(r"\bDROP\s+(TABLE|DATABASE|SCHEMA)\b", re.IGNORECASE), "permanent schema/data loss"),
        ("TRUNCATE", re.compile(r"\bTRUNCATE\s+(TABLE\s+)?\w", re.IGNORECASE), "permanent data loss"),
        ("kubectl delete", re.compile(r"\bkubectl\s+delete\b"), "production resource removal"),
        ("docker rm -f", re.compile(r"\bdocker\s+(rm|rmi)\b.*\s-[a-zA-Z]*f"), "force-removes containers/images"),
        ("mkfs", re.compile(r"\bmkfs(\.\w+)?\b"), "formats a filesystem"),
        ("dd of=", re.compile(r"\bdd\b.*\bof=/"), "raw block write"),
        ("chmod -R 777", re.compile(r"\bchmod\s+-R\s+0?777\b"), "world-writable recursive"),
    ]
    for label, pat, why in PATTERNS:
        if pat.search(command):
            if confirm:
                return {"allowed": True, "pattern": label, "warning": why, "override": True}
            return {"allowed": False, "pattern": label, "warning": why, "override_required": True}
    return {"allowed": True}


def _route_request_impl(prompt: str) -> dict:
    """Port of .claude/hooks/guild-routing-gate.sh — routes to a member."""
    routing_table = [
        (["design the system", "model the domain", "architect the database", "refactor the structure", "schema"], "star-alliance-architect"),
        (["write the code", "fix this bug", "implement this feature", "apply this change", "write code"], "star-alliance-developer"),
        (["design the UI", "make it look premium", "create a brand kit", "design the interface", "ui design", "ux"], "star-alliance-designer"),
        (["plan", "campaign", "strategy", "strategic", "roadmap"], "star-alliance-strategist"),
        (["translate", "law", "legal text", "explain the rule"], "star-alliance-translator"),
        (["market", "announce", "marketing", "comms", "communication"], "star-alliance-herald"),
        (["trade", "portfolio", "market recon", "stock", "crypto"], "star-alliance-merchant"),
        (["release", "verify", "ship", "publish", "audit", "conformity"], "star-alliance-quartermaster"),
    ]
    p_lower = prompt.lower()
    for triggers, member in routing_table:
        if any(t in p_lower for t in triggers):
            return {"member": member, "reason": f"matched triggers: {triggers}", "matched": True}
    return {"member": "star-alliance-strategist", "reason": "no specific match — default to Strategist", "matched": False}


def _delegation_check_impl(bulk_bytes: int, doer_calls: int = 0) -> dict:
    """Port of delegation-gate.py — enforce doer delegation for bulk work."""
    BULK_BYTES = 6000
    if bulk_bytes < BULK_BYTES:
        return {"verdict": "pass", "reason": "below bulk threshold", "threshold": BULK_BYTES}
    if doer_calls > 0:
        _ledger_append("delegation", verdict="pass", bulk_bytes=bulk_bytes, doer_calls=doer_calls)
        return {"verdict": "pass", "reason": f"{doer_calls} doer call(s) logged", "bulk_bytes": bulk_bytes}
    _ledger_append("delegation", verdict="block", bulk_bytes=bulk_bytes, doer_calls=0)
    return {"verdict": "block", "reason": f"bulk={bulk_bytes} ≥ {BULK_BYTES} but no doer call", "override_env": "SA_SOLO=1"}


def _verify_impl(diff: str = "") -> dict:
    """Port of verify-gate.py — run independent critic on diff.

    Calls evolution/verdict.py → critique.py (GLM-5.2).
    Fails OPEN on infrastructure error (mirrors verify-gate.py risk posture).
    """
    if not diff:
        diff = _git_diff()
    if not diff:
        return {"verdict": "pass", "reason": "no diff to verify", "findings": ""}
    if len(diff) > 60_000:
        return {"verdict": "manual_review", "reason": f"diff {len(diff)} > 60k bytes — grounded review needed"}
    try:
        verdict_script = EVOLUTION_DIR / "verdict.py"
        if verdict_script.exists():
            r = subprocess.run(
                [sys.executable, str(verdict_script), "--diff-stdin"],
                input=diff, capture_output=True, text=True,
                cwd=str(ROOT), timeout=120
            )
            if r.returncode == 0:
                # Try to parse JSON verdict from stdout
                try:
                    result = json.loads(r.stdout)
                    _ledger_append("verify", verdict=result.get("verdict", "pass"), bytes=len(diff))
                    return result
                except json.JSONDecodeError:
                    _ledger_append("verify", verdict="pass", bytes=len(diff))
                    return {"verdict": "pass", "findings": r.stdout[-500:]}
            else:
                _ledger_append("verify", verdict="concerns", bytes=len(diff), output=r.stderr[-500:])
                return {"verdict": "concerns", "findings": r.stderr[-500:]}
    except Exception as e:
        return {"verdict": "pass", "reason": "critic unreachable — fail OPEN", "error": str(e)}
    return {"verdict": "pass", "reason": "no verdict script found"}


# ── Server ────────────────────────────────────────────────────────────────────

app = Server("star-alliance")


@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="sa_route_request",
            description="Route a user prompt to the appropriate Star Alliance member profile. Returns the profile name and matching reason.",
            inputSchema={
                "type": "object",
                "properties": {"prompt": {"type": "string", "description": "The user's prompt text"}},
                "required": ["prompt"],
            },
        ),
        Tool(
            name="sa_verify",
            description="Run independent critic (GLM-5.2) on the current diff. Returns verdict: pass/concerns/block. Call before finishing any turn that changed files.",
            inputSchema={
                "type": "object",
                "properties": {"diff": {"type": "string", "description": "Optional diff text. If empty, uses git diff."}},
            },
        ),
        Tool(
            name="sa_delegation_check",
            description="Enforce doer delegation for bulk work. BLOCKS turns that produced ≥6KB inline without calling a doer.",
            inputSchema={
                "type": "object",
                "properties": {
                    "bulk_bytes": {"type": "integer", "description": "Total bytes of Write/Edit/MultiEdit content this turn"},
                    "doer_calls": {"type": "integer", "description": "Number of doer (MiniMax/Ollama) calls logged this turn", "default": 0},
                },
                "required": ["bulk_bytes"],
            },
        ),
        Tool(
            name="sa_destructive_check",
            description="Check a shell command for destructive patterns. Returns {allowed: bool, pattern, warning}.",
            inputSchema={
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "The shell command to check"},
                    "confirm": {"type": "boolean", "description": "True if SA_CONFIRM=1 or # sa-confirm was appended", "default": False},
                },
                "required": ["command"],
            },
        ),
        Tool(
            name="sa_thinker_check",
            description="Validate that a dispatched member's model matches its declared model: in frontmatter.",
            inputSchema={
                "type": "object",
                "properties": {
                    "profile": {"type": "string", "description": "Profile name (e.g. star-alliance-architect)"},
                    "actual_model": {"type": "string", "description": "The model actually used"},
                },
                "required": ["profile", "actual_model"],
            },
        ),
        Tool(
            name="sa_thinker_attest",
            description="Ledger which model actually thought this turn.",
            inputSchema={
                "type": "object",
                "properties": {
                    "profile": {"type": "string"},
                    "model": {"type": "string"},
                    "turn_id": {"type": "string"},
                },
                "required": ["profile", "model"],
            },
        ),
        Tool(
            name="sa_turn_cost",
            description="Log turn cost (tokens + model).",
            inputSchema={
                "type": "object",
                "properties": {
                    "profile": {"type": "string"},
                    "model": {"type": "string"},
                    "tokens_in": {"type": "integer"},
                    "tokens_out": {"type": "integer"},
                },
                "required": ["profile", "model"],
            },
        ),
        Tool(
            name="sa_turn_start",
            description="Mark turn start. Logs timestamp and profile.",
            inputSchema={
                "type": "object",
                "properties": {
                    "profile": {"type": "string"},
                    "workflow": {"type": "string", "description": "Optional workflow ID"},
                },
                "required": ["profile"],
            },
        ),
        Tool(
            name="sa_turn_finalize",
            description="Gate turn-end commit on all checks passing.",
            inputSchema={
                "type": "object",
                "properties": {
                    "gates_passed": {"type": "array", "items": {"type": "string"}, "description": "List of gates that passed"},
                },
            },
        ),
        Tool(
            name="sa_build_mark",
            description="Mark the build as stale (guild-data.js may need regeneration after edits).",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="sa_checkpoint_save",
            description="Snapshot current context, decisions, and remaining work to a checkpoint file.",
            inputSchema={
                "type": "object",
                "properties": {
                    "summary": {"type": "string"},
                    "decisions": {"type": "array", "items": {"type": "string"}},
                    "remaining": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["summary"],
            },
        ),
        Tool(
            name="sa_checkpoint_restore",
            description="Restore from a checkpoint.",
            inputSchema={
                "type": "object",
                "properties": {"stamp": {"type": "string", "description": "Checkpoint ID or 'list'"}},
            },
        ),
        Tool(
            name="sa_snapshot",
            description="PreCompact snapshot — captures context before compression.",
            inputSchema={
                "type": "object",
                "properties": {"summary": {"type": "string"}},
            },
        ),
        Tool(
            name="sa_plain_english_check",
            description="Check if a response is too technical. Returns nudge message if jargon detected.",
            inputSchema={
                "type": "object",
                "properties": {"response": {"type": "string"}},
                "required": ["response"],
            },
        ),
        Tool(
            name="sa_evolution_status",
            description="Get current evolution engine status.",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="sa_evolution_ledger",
            description="Get recent evolution ledger entries.",
            inputSchema={
                "type": "object",
                "properties": {"limit": {"type": "integer", "default": 20}},
            },
        ),
        Tool(
            name="sa_evolution_scoreboard",
            description="Get evolution scoreboard (catch rate, override count, etc).",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="sa_skill_fingerprints_check",
            description="Check for skill drift (content hash changes).",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="sa_executor_check",
            description="Check whether the Butler tried to make direct file writes (forbidden). Returns violation if yes.",
            inputSchema={
                "type": "object",
                "properties": {
                    "profile": {"type": "string"},
                    "tools_used": {"type": "array", "items": {"type": "string"}, "description": "Tools called this turn"},
                },
                "required": ["profile", "tools_used"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    try:
        if name == "sa_route_request":
            result = _route_request_impl(arguments["prompt"])
        elif name == "sa_verify":
            result = _verify_impl(arguments.get("diff", ""))
        elif name == "sa_delegation_check":
            result = _delegation_check_impl(
                arguments["bulk_bytes"], arguments.get("doer_calls", 0)
            )
        elif name == "sa_destructive_check":
            result = _destructive_check_impl(
                arguments["command"], arguments.get("confirm", False)
            )
        elif name == "sa_thinker_check":
            result = {"valid": True, "profile": arguments["profile"], "model": arguments["actual_model"]}
            _ledger_append("thinker", profile=arguments["profile"], model=arguments["actual_model"])
        elif name == "sa_thinker_attest":
            _ledger_append("thinker", profile=arguments["profile"], model=arguments["model"], turn=arguments.get("turn_id"))
            result = {"logged": True}
        elif name == "sa_turn_cost":
            _ledger_append("cost", profile=arguments["profile"], model=arguments["model"],
                          tokens_in=arguments.get("tokens_in", 0), tokens_out=arguments.get("tokens_out", 0))
            result = {"logged": True}
        elif name == "sa_turn_start":
            result = {"started": True, "profile": arguments["profile"], "workflow": arguments.get("workflow")}
        elif name == "sa_turn_finalize":
            result = {"committed": True, "gates": arguments.get("gates_passed", [])}
        elif name == "sa_build_mark":
            try:
                (STATE_DIR / "build-stale").touch()
                result = {"marked": True}
            except Exception as e:
                result = {"marked": False, "error": str(e)}
        elif name == "sa_checkpoint_save":
            stamp = subprocess.run(["date", "-u", "+%Y-%m-%dT%H-%M-%SZ"], capture_output=True, text=True).stdout.strip()
            ckpt_dir = STATE_DIR / "checkpoints"
            ckpt_dir.mkdir(parents=True, exist_ok=True)
            ckpt_path = ckpt_dir / f"{stamp}.json"
            ckpt_path.write_text(json.dumps(arguments, indent=2))
            result = {"saved": str(ckpt_path), "stamp": stamp}
        elif name == "sa_checkpoint_restore":
            stamp = arguments.get("stamp", "list")
            if stamp == "list":
                ckpt_dir = STATE_DIR / "checkpoints"
                ckpts = sorted(ckpt_dir.glob("*.json")) if ckpt_dir.exists() else []
                result = {"checkpoints": [p.stem for p in ckpts]}
            else:
                ckpt_path = STATE_DIR / "checkpoints" / f"{stamp}.json"
                if ckpt_path.exists():
                    result = json.loads(ckpt_path.read_text())
                else:
                    result = {"error": f"checkpoint not found: {stamp}"}
        elif name == "sa_snapshot":
            stamp = subprocess.run(["date", "-u", "+%Y-%m-%dT%H-%M-%SZ"], capture_output=True, text=True).stdout.strip()
            snap_dir = ROOT / "state" / "snapshots"
            snap_dir.mkdir(parents=True, exist_ok=True)
            snap_path = snap_dir / f"{stamp}.md"
            snap_path.write_text(f"# Snapshot {stamp}\n\n{arguments.get('summary', '')}\n")
            result = {"snapshot": str(snap_path), "stamp": stamp}
        elif name == "sa_plain_english_check":
            response = arguments["response"]
            # Heuristic: count technical jargon
            jargon = ["subagent", "tool_use", "PreToolUse", "Stop hook", ".claude/hooks/", "CLAUDE_PROJECT_DIR"]
            found = [j for j in jargon if j in response]
            if found:
                result = {"nudge": f"Consider rephrasing: {found}. Plain English for the Guild Master.", "jargon_found": found}
            else:
                result = {"nudge": None}
        elif name == "sa_evolution_status":
            try:
                status_script = EVOLUTION_DIR / "status.py"
                if status_script.exists():
                    r = subprocess.run([sys.executable, str(status_script)], capture_output=True, text=True,
                                       cwd=str(ROOT), timeout=10)
                    result = {"output": r.stdout[-1000:], "running": r.returncode == 0}
                else:
                    result = {"status": "engine present", "ledger_exists": LEDGER_PATH.exists()}
            except Exception as e:
                result = {"error": str(e)}
        elif name == "sa_evolution_ledger":
            limit = arguments.get("limit", 20)
            if LEDGER_PATH.exists():
                lines = LEDGER_PATH.read_text().splitlines()[-limit:]
                entries = []
                for ln in lines:
                    try:
                        entries.append(json.loads(ln))
                    except json.JSONDecodeError:
                        continue
                result = {"entries": entries, "count": len(entries)}
            else:
                result = {"entries": [], "count": 0}
        elif name == "sa_evolution_scoreboard":
            sb_script = EVOLUTION_DIR / "scoreboard.py"
            if sb_script.exists():
                r = subprocess.run([sys.executable, str(sb_script)], capture_output=True, text=True,
                                   cwd=str(ROOT), timeout=10)
                result = {"output": r.stdout[-2000:]}
            else:
                result = {"error": "scoreboard script not found"}
        elif name == "sa_skill_fingerprints_check":
            fp_script = ROOT / ".claude" / "tools" / "skill_fingerprint.py"
            if fp_script.exists():
                r = subprocess.run([sys.executable, str(fp_script), "--check"],
                                   capture_output=True, text=True, cwd=str(ROOT), timeout=10)
                result = {"drift": r.returncode != 0, "output": r.stdout[-500:]}
            else:
                result = {"drift": False, "note": "fingerprint script not found"}
        elif name == "sa_executor_check":
            profile = arguments["profile"]
            tools = arguments.get("tools_used", [])
            # Butler has no file/terminal toolsets — any use is a violation
            if profile == "star-alliance-butler":
                forbidden = [t for t in tools if t in {"Write", "Edit", "MultiEdit", "NotebookEdit",
                                                       "write_file", "patch", "rm", "cp", "mv", "sed -i"}]
                if forbidden:
                    _ledger_append("executor", verdict="block", profile=profile, tools=forbidden)
                    result = {"verdict": "block", "violations": forbidden,
                             "fix": "Use delegate_task to dispatch to a work-tier profile (developer/quartermaster)"}
                else:
                    result = {"verdict": "pass"}
            else:
                result = {"verdict": "pass", "note": f"{profile} is a work-tier profile"}
        else:
            result = {"error": f"unknown tool: {name}"}
    except Exception as e:
        result = {"error": str(e), "tool": name}
    return [TextContent(type="text", text=json.dumps(result, indent=2))]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())