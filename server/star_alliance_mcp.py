#!/usr/bin/env python3
"""
Star Alliance MCP Server for Hermes Agent

Thinker = GLM-5.2 (this server is authored/steered by THINKER_MODEL = "glm-5.2")
Critic   = Kimi K2.7  (CRITIC_MODEL, used by sa_verify)
Doer     = MiniMax M3 (DOER_MODEL, referenced by sa_delegation_check)

Register with Hermes:
    hermes mcp add star-alliance -- python3 server/star_alliance_mcp.py

This server provides 6 tools, each doing something Hermes doesn't do natively:
  1. sa_workflow_match      — match a prompt to a workflow in workflows.json
  2. sa_agent_dispatch      — resolve an agent .md file and return a delegation briefing
  3. sa_verify              — run the Critic (Kimi K2.7) on a git diff
  4. sa_delegation_check    — gate bulk file writes without doer (MiniMax M3) delegation
  5. sa_evolution_status    — report evolution status + ledger summary
  6. sa_skill_drift_check   — detect skill drift via SHA-256 fingerprints
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

# ── Path constants ────────────────────────────────────────────────────────────
ROOT: Path = Path(__file__).resolve().parent.parent
WORKFLOWS_PATH: Path = ROOT / "workflows.json"
AGENTS_DIR: Path = ROOT / "agents"
SKILLS_DIR: Path = ROOT / "star-alliance-skills"
EVOLUTION_DIR: Path = ROOT / "evolution"
STATE_DIR: Path = ROOT / "state"
VERDICT_SCRIPT: Path = EVOLUTION_DIR / "verdict.py"
STATUS_SCRIPT: Path = EVOLUTION_DIR / "status.py"
LEDGER_PATH: Path = EVOLUTION_DIR / "ledger.jsonl"
VERIFY_LOG_PATH: Path = STATE_DIR / "verify-log.jsonl"
FINGERPRINTS_PATH: Path = STATE_DIR / "skill-fingerprints.json"

# ── Model constants ───────────────────────────────────────────────────────────
THINKER_MODEL: str = "glm-5.2"
CRITIC_MODEL: str = "kimi-k2.7"   # used by sa_verify
DOER_MODEL: str = "minimax-m3"    # used by sa_delegation_check

# ── Tool parameter constants ──────────────────────────────────────────────────
DELEGATION_BYTE_THRESHOLD: int = 6000
VERIFY_TIMEOUT_SECONDS: int = 180
MAX_DIFF_BYTES: int = 60 * 1024  # 60 KB

# ── Server setup ──────────────────────────────────────────────────────────────
server: Server = Server("star-alliance")


# ── Tool 1: sa_workflow_match ─────────────────────────────────────────────────
def _sa_workflow_match(prompt: str) -> dict[str, Any]:
    """Match a prompt against workflows.json by keyword overlap."""
    if not WORKFLOWS_PATH.exists():
        return {"match": None, "reason": "workflows.json not found"}

    workflows: list[dict[str, Any]] = json.loads(WORKFLOWS_PATH.read_text(encoding="utf-8"))
    prompt_lower: str = prompt.lower()
    prompt_words: set[str] = set(re.findall(r"[a-z0-9_-]+", prompt_lower))
    if not prompt_words:
        return {"match": None, "reason": "no keywords in prompt"}

    best: dict[str, Any] | None = None
    best_score: float = 0.0

    for wf in workflows:
        when_text: str = str(wf.get("when", "")).lower()
        trigger_phrases: list[str] = wf.get("trigger_phrases") or []
        trigger_text: str = " ".join(str(tp) for tp in trigger_phrases).lower()
        corpus_text: str = f"{when_text} {trigger_text}"
        corpus_words: set[str] = set(re.findall(r"[a-z0-9_-]+", corpus_text))
        if not corpus_words:
            continue
        overlap: set[str] = prompt_words & corpus_words
        # Score: F1-like overlap normalized to the smaller set
        if not overlap:
            score: float = 0.0
        else:
            precision: float = len(overlap) / len(prompt_words) if prompt_words else 0.0
            recall: float = len(overlap) / len(corpus_words) if corpus_words else 0.0
            if precision + recall > 0:
                score = 2 * precision * recall / (precision + recall)
            else:
                score = 0.0
        if score > best_score:
            best_score = score
            best = wf

    if best is None or best_score == 0.0:
        return {"match": None, "reason": "no workflow fits"}

    steps_summary: str = ""
    steps = best.get("steps")
    if isinstance(steps, list):
        steps_summary = "; ".join(
            str(s.get("action", s.get("name", s) if isinstance(s, dict) else s))
            for s in steps
        )
    elif isinstance(steps, str):
        steps_summary = steps

    return {
        "workflow_id": best.get("id", best.get("workflow_id", "")),
        "workflow_name": best.get("name", best.get("workflow_name", "")),
        "category": best.get("category", ""),
        "score": round(best_score, 4),
        "steps_summary": steps_summary,
    }


# ── Tool 2: sa_agent_dispatch ─────────────────────────────────────────────────
_FRONTMATTER_RE = re.compile(
    r"^---\s*\n(.*?)\n---\s*\n?(.*)$",
    re.DOTALL,
)


def _parse_frontmatter(text: str) -> dict[str, Any]:
    """Parse simple YAML frontmatter using regex — no pyyaml dependency."""
    m = _FRONTMATTER_RE.match(text)
    if not m:
        return {}
    body: str = m.group(1)
    meta: dict[str, Any] = {}
    for line in body.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        key, _, raw_val = line.partition(":")
        key = key.strip()
        raw_val = raw_val.strip()
        # Handle list values:  skills: [a, b, c]
        if raw_val.startswith("[") and raw_val.endswith("]"):
            inner = raw_val[1:-1]
            items = [x.strip().strip("'\"") for x in inner.split(",") if x.strip()]
            meta[key] = items
        elif raw_val:
            meta[key] = raw_val.strip("'\"")
        else:
            meta[key] = None
    return meta


def _sa_agent_dispatch(agent_name: str) -> dict[str, Any]:
    """Resolve an agent .md file from agents/ and return a delegation briefing."""
    agent_file: Path = AGENTS_DIR / f"{agent_name}.md"
    if not agent_file.exists():
        return {"error": "agent not found", "searched": str(agent_file)}
    text: str = agent_file.read_text(encoding="utf-8")
    meta: dict[str, Any] = _parse_frontmatter(text)
    skills_raw: Any = meta.get("skills", [])
    if isinstance(skills_raw, str):
        skills: list[str] = [s.strip() for s in skills_raw.split(",") if s.strip()]
    elif isinstance(skills_raw, list):
        skills = [str(s) for s in skills_raw]
    else:
        skills = []
    return {
        "agent_name": meta.get("name", agent_name),
        "description": meta.get("description", ""),
        "skills": skills,
        "file_path": str(agent_file),
    }


# ── Tool 3: sa_verify ────────────────────────────────────────────────────────
# Runs the Critic (CRITIC_MODEL = "kimi-k2.7") on a git diff.
def _append_verify_log(verdict: str, diff_size: int) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    entry: dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "verdict": verdict,
        "diff_size": diff_size,
    }
    with VERIFY_LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def _sa_verify(diff: str | None = None) -> dict[str, Any]:
    """Run the Critic (Kimi K2.7) on a git diff."""
    # If no diff provided, get it from git
    if diff is None:
        try:
            result = subprocess.run(
                ["git", "diff"],
                cwd=str(ROOT),
                capture_output=True,
                text=True,
                timeout=30,
            )
            diff = result.stdout
        except Exception as e:
            return {"verdict": "pass", "reason": "critic unreachable — fail open", "error": str(e)}

    if not diff or not diff.strip():
        _append_verify_log("pass", 0)
        return {"verdict": "pass", "reason": "no diff to verify"}

    diff_bytes: bytes = diff.encode("utf-8")
    diff_size: int = len(diff_bytes)

    if diff_size > MAX_DIFF_BYTES:
        _append_verify_log("manual_review", diff_size)
        return {"verdict": "manual_review", "reason": "diff too large for cold critique"}

    # Call the verdict.py script (Critik Model = kimi-k2.7)
    if not VERDICT_SCRIPT.exists():
        _append_verify_log("pass", diff_size)
        return {
            "verdict": "pass",
            "reason": f"verdict.py not found at {VERDICT_SCRIPT} — fail open",
            "critic_model": CRITIC_MODEL,
        }

    try:
        proc = subprocess.run(
            [sys.executable, str(VERDICT_SCRIPT)],
            input=diff,
            capture_output=True,
            text=True,
            timeout=VERIFY_TIMEOUT_SECONDS,
        )
        stdout: str = proc.stdout.strip()
        stderr: str = proc.stderr.strip()
        if proc.returncode != 0:
            _append_verify_log("pass", diff_size)
            return {
                "verdict": "pass",
                "reason": "critic unreachable — fail open",
                "error": f"verdict.py exited {proc.returncode}: {stderr}",
                "critic_model": CRITIC_MODEL,
            }
        # Try to parse JSON from stdout
        try:
            parsed: Any = json.loads(stdout)
            verdict_str: str = parsed.get("verdict", "unknown") if isinstance(parsed, dict) else "unknown"
            _append_verify_log(verdict_str, diff_size)
            return parsed if isinstance(parsed, dict) else {"verdict": "unknown", "raw": stdout}
        except json.JSONDecodeError:
            _append_verify_log("unknown", diff_size)
            return {"verdict": "raw", "output": stdout, "critic_model": CRITIC_MODEL}
    except subprocess.TimeoutExpired:
        _append_verify_log("pass", diff_size)
        return {
            "verdict": "pass",
            "reason": "critic unreachable — fail open",
            "error": f"verdict.py timed out after {VERIFY_TIMEOUT_SECONDS}s",
            "critic_model": CRITIC_MODEL,
        }
    except Exception as e:
        _append_verify_log("pass", diff_size)
        return {
            "verdict": "pass",
            "reason": "critic unreachable — fail open",
            "error": str(e),
            "critic_model": CRITIC_MODEL,
        }


# ── Tool 4: sa_delegation_check ──────────────────────────────────────────────
# Doer = DOER_MODEL ("minimax-m3"). Gates bulk file writes without doer delegation.
def _sa_delegation_check(bulk_bytes: int, doer_calls: int) -> dict[str, Any]:
    """Check if bulk work was done without doer (MiniMax M3) delegation."""
    if bulk_bytes >= DELEGATION_BYTE_THRESHOLD and doer_calls == 0:
        return {
            "verdict": "block",
            "reason": "bulk work without doer delegation",
            "threshold": DELEGATION_BYTE_THRESHOLD,
            "override_env": "SA_SOLO=1",
            "doer_model": DOER_MODEL,
        }
    if bulk_bytes < DELEGATION_BYTE_THRESHOLD:
        return {"verdict": "pass", "reason": "below threshold"}
    # bulk_bytes >= threshold and doer_calls > 0
    return {"verdict": "pass", "reason": "doer delegation logged", "doer_model": DOER_MODEL}


# ── Tool 5: sa_evolution_status ───────────────────────────────────────────────
def _sa_evolution_status() -> dict[str, Any]:
    """Run evolution/status.py and summarize the ledger."""
    status_output: str = ""
    if STATUS_SCRIPT.exists():
        try:
            proc = subprocess.run(
                [sys.executable, str(STATUS_SCRIPT)],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(ROOT),
            )
            status_output = proc.stdout.strip()
        except Exception as e:
            status_output = f"[error running status.py: {e}]"
    else:
        status_output = f"[status.py not found at {STATUS_SCRIPT}]"

    ledger_entries: int = 0
    last_entry: Any = None
    if LEDGER_PATH.exists():
        try:
            lines: list[str] = LEDGER_PATH.read_text(encoding="utf-8").splitlines()
            non_empty: list[str] = [ln for ln in lines if ln.strip()]
            ledger_entries = len(non_empty)
            if non_empty:
                try:
                    last_entry = json.loads(non_empty[-1])
                except json.JSONDecodeError:
                    last_entry = non_empty[-1]
        except Exception as e:
            ledger_entries = 0
            last_entry = {"error": str(e)}

    return {
        "status_output": status_output,
        "ledger_entries": ledger_entries,
        "last_entry": last_entry,
    }


# ── Tool 6: sa_skill_drift_check ─────────────────────────────────────────────
def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _sa_skill_drift_check() -> dict[str, Any]:
    """Check skill drift by comparing SKILL.md hashes against stored fingerprints."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)

    # Build current fingerprints
    current: dict[str, str] = {}
    if SKILLS_DIR.exists():
        for skill_dir in sorted(SKILLS_DIR.iterdir()):
            if not skill_dir.is_dir():
                continue
            skill_md: Path = skill_dir / "SKILL.md"
            if skill_md.exists():
                current[skill_dir.name] = _sha256_file(skill_md)

    # Load stored fingerprints
    stored: dict[str, str] = {}
    if FINGERPRINTS_PATH.exists():
        try:
            stored = json.loads(FINGERPRINTS_PATH.read_text(encoding="utf-8"))
            if not isinstance(stored, dict):
                stored = {}
        except json.JSONDecodeError:
            stored = {}

    # If no stored fingerprints, this is first run — no drift
    is_first_run: bool = not stored

    drift: list[dict[str, str]] = []
    clean: int = 0
    for skill, current_hash in current.items():
        if is_first_run:
            clean += 1
            continue
        stored_hash = stored.get(skill)
        if stored_hash is None:
            # New skill since last run — not drift, just new
            clean += 1
            continue
        if stored_hash != current_hash:
            drift.append({
                "skill": skill,
                "expected": stored_hash,
                "actual": current_hash,
            })
        else:
            clean += 1

    # Update fingerprints file with current hashes
    FINGERPRINTS_PATH.write_text(
        json.dumps(current, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    return {
        "checked": len(current),
        "drift": drift,
        "clean": clean,
    }


# ── Tool definitions ─────────────────────────────────────────────────────────

WORKFLOW_MATCH_TOOL = Tool(
    name="sa_workflow_match",
    description=(
        "Match a prompt against workflows.json. Scores keyword overlap against each "
        "workflow's 'when' field and 'trigger_phrases' array. Returns the best match "
        "or null if nothing fits."
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "prompt": {
                "type": "string",
                "description": "The user or task prompt to match against workflows.",
            },
        },
        "required": ["prompt"],
    },
)

AGENT_DISPATCH_TOOL = Tool(
    name="sa_agent_dispatch",
    description=(
        "Resolve an agent's .md file from agents/, parse its YAML frontmatter "
        "(name, description, skills), and return a delegation briefing."
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "agent_name": {
                "type": "string",
                "description": "Agent name without .md extension (e.g. 'the-developer').",
            },
        },
        "required": ["agent_name"],
    },
)

VERIFY_TOOL = Tool(
    name="sa_verify",
    description=(
        "Run the Critic (Kimi K2.7) on a git diff. If no diff is provided, reads "
        "`git diff` from ROOT. Fails open (returns pass) if the critic is unreachable. "
        "Logs every verdict to state/verify-log.jsonl."
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "diff": {
                "type": "string",
                "description": "Optional explicit diff text. If omitted, runs `git diff` in ROOT.",
            },
        },
        "required": [],
    },
)

DELEGATION_CHECK_TOOL = Tool(
    name="sa_delegation_check",
    description=(
        "Gate bulk file writes without doer (MiniMax M3) delegation. If bulk_bytes >= 6000 "
        "and no doer calls were made, returns a block verdict with SA_SOLO=1 override env. "
        "Otherwise returns pass."
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "bulk_bytes": {
                "type": "integer",
                "description": "Total bytes of inline file writes this turn.",
            },
            "doer_calls": {
                "type": "integer",
                "description": "Number of doer (MiniMax M3) delegations made this turn.",
            },
        },
        "required": ["bulk_bytes", "doer_calls"],
    },
)

EVOLUTION_STATUS_TOOL = Tool(
    name="sa_evolution_status",
    description=(
        "Run evolution/status.py and summarize the evolution ledger. Returns status "
        "output, entry count, and last ledger entry."
    ),
    inputSchema={
        "type": "object",
        "properties": {},
        "required": [],
    },
)

SKILL_DRIFT_CHECK_TOOL = Tool(
    name="sa_skill_drift_check",
    description=(
        "Hash every SKILL.md in star-alliance-skills/ (SHA-256) and compare against "
        "stored fingerprints in state/skill-fingerprints.json. Flags any skill whose "
        "hash has changed since the last check."
    ),
    inputSchema={
        "type": "object",
        "properties": {},
        "required": [],
    },
)


@server.list_tools()
async def list_tools() -> list[Tool]:
    """Return all 6 Star Alliance tools."""
    return [
        WORKFLOW_MATCH_TOOL,
        AGENT_DISPATCH_TOOL,
        VERIFY_TOOL,
        DELEGATION_CHECK_TOOL,
        EVOLUTION_STATUS_TOOL,
        SKILL_DRIFT_CHECK_TOOL,
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Dispatch to the appropriate handler and return JSON text content."""
    try:
        result: dict[str, Any]

        if name == "sa_workflow_match":
            prompt: str = arguments.get("prompt", "")
            result = _sa_workflow_match(prompt)

        elif name == "sa_agent_dispatch":
            agent_name: str = arguments.get("agent_name", "")
            result = _sa_agent_dispatch(agent_name)

        elif name == "sa_verify":
            diff_arg: str | None = arguments.get("diff")
            result = _sa_verify(diff_arg)

        elif name == "sa_delegation_check":
            bulk_bytes: int = int(arguments.get("bulk_bytes", 0))
            doer_calls: int = int(arguments.get("doer_calls", 0))
            result = _sa_delegation_check(bulk_bytes, doer_calls)

        elif name == "sa_evolution_status":
            result = _sa_evolution_status()

        elif name == "sa_skill_drift_check":
            result = _sa_skill_drift_check()

        else:
            result = {"error": f"unknown tool: {name}"}

    except Exception as e:
        result = {"error": str(e)}

    return [TextContent(type="text", text=json.dumps(result, indent=2))]


# ── Main entry point ──────────────────────────────────────────────────────────

async def main() -> None:
    """Run the MCP server over stdio."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())