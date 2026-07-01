#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────────────────
# Star Alliance — MEMBER / SKILL WRITE-TIME LINTER  (PreToolUse, BLOCKING)
#
# THE RULE: a Write/Edit/MultiEdit that would leave a member source file
# (star-alliance-members/*.md) or a skill source file
# (star-alliance-skills/<name>/SKILL.md) missing its required frontmatter
# fields, missing its required sections, or below a sane minimum length (a
# stub) is BLOCKED before it lands.
#
# Conventions below are DERIVED from the real files in this repo, not
# invented — see star-alliance-members/the-steward.md (60 lines, the
# smallest real member) and star-alliance-skills/frontend-auditor/SKILL.md
# (23 lines, the smallest real skill) plus the-developer.md / the-architect.md
# / the-strategist.md / db-rename-sweep/SKILL.md / backend-auditor/SKILL.md.
#
# MEMBER frontmatter (required keys, all present on every real member file):
#   name, description, model, tools, skills, type: Member, version
# MEMBER required sections: at least one non-empty body paragraph after the
#   frontmatter close (the "You are **the X**..." intro every member opens
#   with) — checked structurally as "body has >= MIN_BODY_CHARS of prose
#   after stripping the frontmatter block."
#
# SKILL frontmatter (required keys, all present on every real SKILL.md):
#   name, description, metadata.version, type: Skill
# SKILL required sections: exactly one Markdown H1 (`# Title`) in the body —
#   every real SKILL.md opens its body with one.
#
# Minimum-content length (derived from the smallest REAL files in the repo,
# with a safety margin below them so a legitimately terse-but-real file is
# never falsely blocked):
#   MEMBER_MIN_LINES = 15   (smallest real member: the-steward.md at 60)
#   SKILL_MIN_LINES  = 12   (smallest real skill: frontend-auditor/SKILL.md at 23)
#   MEMBER_MIN_BODY_CHARS = 300
#   SKILL_MIN_BODY_CHARS  = 150
#
# Mechanics mirror okf-gate.py exactly: PreToolUse gets the tool call as JSON
# on stdin. For Write we inspect `content`; for Edit/MultiEdit we reconstruct
# the resulting file content by applying the proposed edit(s) in memory
# against the current on-disk text (best-effort). check(data) is a pure
# decision function so sa-pretool.py can import and call it in-process.
#   • non-governed path / non-write tool         -> exit 0 (allow)
#   • governed path + result conformant          -> exit 0 (allow)
#   • governed path + result NOT conformant      -> exit 2 (block, print reasons)
# Fails OPEN on any internal error — a broken hook must never brick the session.
# ─────────────────────────────────────────────────────────────────────────────
import sys, os, json, re

WRITE_TOOLS = {"Write", "Edit", "MultiEdit"}

FM_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?", re.S)
H1_RE = re.compile(r"(?m)^#\s+\S")

MEMBER_MIN_LINES = 15
SKILL_MIN_LINES = 12
MEMBER_MIN_BODY_CHARS = 300
SKILL_MIN_BODY_CHARS = 150

MEMBER_REQUIRED_FM_KEYS = ["name", "description", "model", "tools", "skills", "type", "version"]
SKILL_REQUIRED_FM_KEYS = ["name", "description", "type"]  # metadata.version checked separately


def project_dir():
    return os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def classify_path(path: str, root: str):
    """Return 'member', 'skill', or None (ungoverned) for the given path."""
    if not path or not path.endswith(".md"):
        return None
    try:
        rel = os.path.relpath(path, root)
    except Exception:
        rel = path
    rel_slash = rel.replace(os.sep, "/")
    parts = rel_slash.split("/")

    if len(parts) == 2 and parts[0] == "star-alliance-members" and parts[1].endswith(".md"):
        if parts[1] == "README.md":
            return None
        return "member"

    if len(parts) == 3 and parts[0] == "star-alliance-skills" and parts[2] == "SKILL.md":
        return "skill"

    return None


def resulting_text(tool: str, inp: dict, path: str) -> str:
    """Best-effort reconstruction of the file's content after the tool runs.
    Mirrors okf-gate.py's resulting_text()."""
    if tool == "Write":
        return inp.get("content", "")
    try:
        cur = open(path, encoding="utf-8").read()
    except Exception:
        cur = ""
    if tool == "Edit":
        old, new = inp.get("old_string", ""), inp.get("new_string", "")
        if inp.get("replace_all"):
            return cur.replace(old, new)
        return cur.replace(old, new, 1)
    if tool == "MultiEdit":
        for e in inp.get("edits", []) or []:
            old, new = e.get("old_string", ""), e.get("new_string", "")
            cur = cur.replace(old, new, -1 if e.get("replace_all") else 1)
        return cur
    return cur


def parse_frontmatter(text: str):
    """Returns (frontmatter_text_or_None, body_text)."""
    m = FM_RE.match(text or "")
    if not m:
        return None, text or ""
    return m.group(1), (text or "")[m.end():]


def fm_has_key(fm_text: str, key: str) -> bool:
    # Top-level YAML key match: "key:" at line start (allow leading whitespace
    # for nested reads of metadata.version handled separately).
    return bool(re.search(rf"(?m)^{re.escape(key)}\s*:", fm_text))


def fm_has_nested_key(fm_text: str, parent: str, child: str) -> bool:
    """Check for a nested key like metadata.version: either
         metadata:\n  version: ...
       or a flow-style metadata: { version: ... }."""
    # Block-style: find the parent key's block, then look for an indented child key.
    block_match = re.search(rf"(?m)^{re.escape(parent)}\s*:\s*$", fm_text)
    if block_match:
        rest = fm_text[block_match.end():]
        # Stop at the next top-level (non-indented) key.
        next_top = re.search(r"(?m)^\S", rest)
        block = rest[:next_top.start()] if next_top else rest
        if re.search(rf"(?m)^\s+{re.escape(child)}\s*:", block):
            return True
    # Flow-style or inline: metadata: { version: 1.0.0 } or metadata.version: 1.0.0
    if re.search(rf"(?m)^{re.escape(parent)}\.{re.escape(child)}\s*:", fm_text):
        return True
    if re.search(rf"{re.escape(parent)}\s*:\s*\{{[^}}]*{re.escape(child)}\s*:", fm_text):
        return True
    return False


def lint_member(text: str, rel: str):
    """Returns a list of failure-reason strings; empty list = pass."""
    reasons = []
    fm_text, body = parse_frontmatter(text)

    if fm_text is None:
        return [f"missing YAML frontmatter block (--- ... ---) entirely"]

    missing_keys = [k for k in MEMBER_REQUIRED_FM_KEYS if not fm_has_key(fm_text, k)]
    if missing_keys:
        reasons.append(f"frontmatter missing required key(s): {', '.join(missing_keys)}")

    type_match = re.search(r"(?m)^type\s*:\s*(\S+)", fm_text)
    if type_match and type_match.group(1).strip() != "Member":
        reasons.append(f"frontmatter `type:` must be `Member` (found `{type_match.group(1).strip()}`)")

    total_lines = len((text or "").splitlines())
    if total_lines < MEMBER_MIN_LINES:
        reasons.append(f"file is only {total_lines} lines (member minimum is {MEMBER_MIN_LINES}) — looks like a stub")

    body_stripped = (body or "").strip()
    if len(body_stripped) < MEMBER_MIN_BODY_CHARS:
        reasons.append(
            f"body prose after frontmatter is only {len(body_stripped)} chars "
            f"(member minimum is {MEMBER_MIN_BODY_CHARS}) — looks like a stub"
        )

    return reasons


def lint_skill(text: str, rel: str):
    reasons = []
    fm_text, body = parse_frontmatter(text)

    if fm_text is None:
        return [f"missing YAML frontmatter block (--- ... ---) entirely"]

    missing_keys = [k for k in SKILL_REQUIRED_FM_KEYS if not fm_has_key(fm_text, k)]
    if missing_keys:
        reasons.append(f"frontmatter missing required key(s): {', '.join(missing_keys)}")

    if not fm_has_nested_key(fm_text, "metadata", "version"):
        reasons.append("frontmatter missing required `metadata.version` field")

    type_match = re.search(r"(?m)^type\s*:\s*(\S+)", fm_text)
    if type_match and type_match.group(1).strip() != "Skill":
        reasons.append(f"frontmatter `type:` must be `Skill` (found `{type_match.group(1).strip()}`)")

    total_lines = len((text or "").splitlines())
    if total_lines < SKILL_MIN_LINES:
        reasons.append(f"file is only {total_lines} lines (skill minimum is {SKILL_MIN_LINES}) — looks like a stub")

    body_stripped = (body or "").strip()
    if len(body_stripped) < SKILL_MIN_BODY_CHARS:
        reasons.append(
            f"body prose after frontmatter is only {len(body_stripped)} chars "
            f"(skill minimum is {SKILL_MIN_BODY_CHARS}) — looks like a stub"
        )

    if not H1_RE.search(body or ""):
        reasons.append("body missing a required H1 heading (`# Title`) after the frontmatter")

    return reasons


def check(data):
    """Pure decision. Returns {"exit":0|2, "stderr":str}."""
    tool = data.get("tool_name", "")
    if tool not in WRITE_TOOLS:
        return {"exit": 0}

    inp = data.get("tool_input", {}) or {}
    path = inp.get("file_path") or inp.get("path") or ""
    root = project_dir()

    kind = classify_path(path, root)
    if kind is None:
        return {"exit": 0}

    try:
        text = resulting_text(tool, inp, path)
    except Exception as e:
        return {"exit": 0, "stderr": f"[member-skill-lint-gate] reconstruct error, failing open: {e}\n"}

    rel = os.path.relpath(path, root) if path else path

    try:
        if kind == "member":
            reasons = lint_member(text, rel)
            kind_label = "MEMBER"
        else:
            reasons = lint_skill(text, rel)
            kind_label = "SKILL"
    except Exception as e:
        return {"exit": 0, "stderr": f"[member-skill-lint-gate] lint error, failing open: {e}\n"}

    if not reasons:
        return {"exit": 0}

    reason_lines = "\n".join(f"   - {r}" for r in reasons)
    return {"exit": 2, "stderr": (
        f"⛔ MEMBER/SKILL LINT GATE — this write would leave a {kind_label} source file "
        "non-conformant to the guild's real conventions (derived from existing files):\n"
        f"   file: {rel}\n"
        f"{reason_lines}\n"
        "   Fix the issue(s) above and retry.\n"
    )}


def main():
    try:
        data = json.load(sys.stdin)
    except Exception as e:
        sys.stderr.write(f"[member-skill-lint-gate] malformed payload, failing open: {e}\n")
        sys.exit(0)
    r = check(data)
    if r.get("stderr"):
        sys.stderr.write(r["stderr"])
    sys.exit(r.get("exit", 0))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        sys.stderr.write(f"[member-skill-lint-gate] {e}, failing open\n")
        sys.exit(0)
