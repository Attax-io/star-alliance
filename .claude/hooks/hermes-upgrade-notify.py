#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────────────────
# Star Alliance — HERMES UPGRADE NOTIFY  (PostToolUse, non-blocking)
#
# After any skill, member, or agent file is saved, notify the corresponding
# Hermes profile(s) to upgrade themselves using:
#   hermes --profile <name> -z "<task>"
#
# Triggers:
#   star-alliance-skills/<id>/**  → find members carrying that skill, notify each
#   star-alliance-members/<name>.md → notify that member directly
#   .claude/agents/<name>.md        → notify that member directly
#
# The Strategist is excluded (it is a router, not a craft member).
# Fires in the background — never blocks the save.
# ─────────────────────────────────────────────────────────────────────────────
import json
import sys
import os
import subprocess
from pathlib import Path

EXCLUDED = {"the-strategist", "the-butler"}
ALL_MEMBERS = {
    "the-developer", "the-architect", "the-designer",
    "the-herald", "the-merchant", "the-quartermaster", "the-translator",
}


def notify(profile: str, message: str) -> None:
    """Fire hermes --profile <profile> -z <message> in the background."""
    subprocess.Popen(
        ["hermes", "--profile", profile, "-z", message],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def members_carrying_skill(skill_id: str, root: str) -> list[str]:
    """Return member IDs that carry the given skill_id, from guild-data.json."""
    gd_path = os.path.join(root, "guild-data.json")
    if not os.path.exists(gd_path):
        return []
    try:
        with open(gd_path) as f:
            gd = json.load(f)
        result = []
        for member in gd.get("members", []):
            mid = member.get("id", "")
            if mid in EXCLUDED:
                continue
            if mid not in ALL_MEMBERS:
                continue
            skills = member.get("skills", [])
            # skills is a list of strings (skill IDs)
            ids = [s if isinstance(s, str) else s.get("id", "") for s in skills]
            if skill_id in ids:
                result.append(mid)
        return result
    except Exception:
        return []


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    ti = data.get("tool_input", {}) or {}
    path = (ti.get("file_path") or ti.get("filePath") or "").replace("\\", "/")
    if not path:
        sys.exit(0)

    root = os.environ.get("STAR_ALLIANCE_ROOT") or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    rel = os.path.relpath(path, root).replace("\\", "/")

    # ── Member file upgraded ──────────────────────────────────────────────────
    if rel.startswith("star-alliance-members/") and rel.endswith(".md"):
        name = Path(rel).stem
        if name in ALL_MEMBERS and name not in EXCLUDED:
            msg = (
                f"Your member profile at {path} was just upgraded by the Quartermaster. "
                f"Read it with the Read tool and integrate any changes into how you work."
            )
            notify(name, msg)

    # ── Agent definition upgraded ─────────────────────────────────────────────
    elif rel.startswith(".claude/agents/") and rel.endswith(".md"):
        name = Path(rel).stem
        if name in ALL_MEMBERS and name not in EXCLUDED:
            msg = (
                f"Your agent definition at {path} was just upgraded. "
                f"Read it with the Read tool and integrate any changes into how you work."
            )
            notify(name, msg)

    # ── Skill file upgraded ───────────────────────────────────────────────────
    elif "star-alliance-skills/" in rel:
        parts = rel.split("/")
        # parts[0] = 'star-alliance-skills', parts[1] = skill_id
        if len(parts) >= 2:
            skill_id = parts[1]
            carriers = members_carrying_skill(skill_id, root)
            if not carriers:
                # Skill may be new or not yet wired — broadcast to all members
                carriers = list(ALL_MEMBERS)
            for name in carriers:
                msg = (
                    f"The skill '{skill_id}' at {path} was just upgraded. "
                    f"Read the updated SKILL.md at star-alliance-skills/{skill_id}/SKILL.md "
                    f"and integrate any changes into how you use this skill."
                )
                notify(name, msg)

    sys.exit(0)


if __name__ == "__main__":
    main()