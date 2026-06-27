#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────────────────
# Star Alliance — OKF GATE  (PreToolUse, BLOCKING)
#
# THE HARD RULE: every markdown knowledge file the guild writes stays conformant
# to the Open Knowledge Format (OKF v0.1). A Write/Edit that would leave a
# governed .md without YAML frontmatter carrying a `type:` field is BLOCKED.
#
# This is the consumer-trust guarantee behind the `star-alliance-language` skill:
# any member opening a Quartermaster-tidied repo can rely on every knowledge file
# announcing its `type:` up front — so future runs read by frontmatter, never by
# blind full-reads.
#
# Scope mirrors okf_audit.py exactly: governed = .md, minus vendored mirrors
# (impeccable/), node_modules, .git, generated/machine dirs.
#
# Mechanics: PreToolUse gets the tool call as JSON on stdin. For Write we inspect
# `content`; for Edit/MultiEdit we inspect the on-disk file AFTER applying the
# proposed new_string in memory (best-effort) — if we cannot reconstruct, we fall
# back to the resulting-file heuristic of "does the edit keep/ään introduce a
# valid frontmatter". The check is intentionally cheap and structural.
#   • governed target + result conformant      → exit 0 (allow)
#   • governed target + result NOT conformant  → exit 2 (block, print fix line)
#   • non-governed / non-md / read-only tool    → exit 0 (allow)
# Fails OPEN on any internal error — a broken hook must never brick the session.
# ─────────────────────────────────────────────────────────────────────────────
import sys, os, json, re

WRITE_TOOLS = {"Write", "Edit", "MultiEdit"}

EXCLUDE_DIR_PARTS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv",
    "scratchpad", "routine-logs", "routine-ledger",
}
EXCLUDE_PATH_SUBSTR = ("/impeccable/",)

FM_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?", re.S)


def project_dir():
    return os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def is_governed(path: str, root: str) -> bool:
    if not path or not path.endswith(".md"):
        return False
    try:
        rel = os.path.relpath(path, root)
    except Exception:
        rel = path
    rel_slash = "/" + rel.replace(os.sep, "/")
    if any(sub in rel_slash for sub in EXCLUDE_PATH_SUBSTR):
        return False
    parts = rel.replace(os.sep, "/").split("/")
    if any(p in EXCLUDE_DIR_PARTS for p in parts):
        return False
    return True


def conformant(text: str) -> bool:
    m = FM_RE.match(text or "")
    if not m:
        return False
    return bool(re.search(r"(?m)^type\s*:", m.group(1)))


def resulting_text(tool: str, inp: dict, path: str) -> str:
    """Best-effort reconstruction of the file's content after the tool runs."""
    if tool == "Write":
        return inp.get("content", "")
    # Edit / MultiEdit — apply against current on-disk content.
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


def main():
    try:
        data = json.load(sys.stdin)
    except Exception as e:
        sys.stderr.write(f"[okf-gate] malformed payload, failing open: {e}\n")
        sys.exit(0)

    tool = data.get("tool_name", "")
    if tool not in WRITE_TOOLS:
        sys.exit(0)

    inp = data.get("tool_input", {}) or {}
    path = inp.get("file_path") or inp.get("path") or ""
    root = project_dir()

    if not is_governed(path, root):
        sys.exit(0)

    try:
        text = resulting_text(tool, inp, path)
    except Exception as e:
        sys.stderr.write(f"[okf-gate] reconstruct error, failing open: {e}\n")
        sys.exit(0)

    if conformant(text):
        sys.exit(0)

    rel = os.path.relpath(path, root) if path else path
    sys.stderr.write(
        "⛔ OKF GATE — this write would leave a governed knowledge file NON-conformant "
        "to the Open Knowledge Format (OKF v0.1).\n"
        f"   file: {rel}\n"
        "   Every governed .md MUST open with YAML frontmatter carrying a `type:` field:\n"
        "       ---\n"
        "       type: Document        # or Skill / Member / Index / Log / Readme …\n"
        "       title: <short name>   # optional but recommended\n"
        "       description: <one line>\n"
        "       timestamp: <ISO-8601>\n"
        "       ---\n"
        "   Add it and retry, or run the fixer:\n"
        f"       python3 star-alliance-skills/okf/scripts/okf_audit.py --fix --path {rel}\n"
    )
    sys.exit(2)


if __name__ == "__main__":
    main()
