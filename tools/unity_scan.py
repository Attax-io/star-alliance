#!/usr/bin/env python3
"""Code Unity scanner — harvest name collisions across the Star Alliance repo.

A read-only, regex-based scanner that walks every source file and indexes
type/class/interface names, constants, utility functions, and service/client
instantiations. Names defined in more than one file are flagged as "candidates"
for the Code Unity STORM pass (Phase 3 of the evolution cron job).

CLI:
  python3 tools/unity_scan.py          → prints JSON report to stdout
  python3 tools/unity_scan.py --report → prints human-readable table

Exit 0 always — it's a scanner, not a gate.
"""
import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = next(
    (p for p in Path(__file__).resolve().parents
     if (p / "VERSIONS.md").exists() and (p / ".git").exists()),
    Path(__file__).resolve().parent,
)

# ── File extensions to scan ─────────────────────────────────────────────────
SCAN_EXTS = {".py", ".ts", ".tsx", ".js", ".json", ".yaml", ".yml"}

# ── Directory fragments to skip (any path component matching) ───────────────
SKIP_DIRS = {
    ".git",
    "node_modules",
    "__pycache__",
    "dist-info",
    "site-packages",
}

# ── Path fragments to skip (substring match against relative path) ──────────
# .claude/ contains installed mirrors (arsenal/, skills/, agents/) and runtime
# (state/) — all generated from repo sources. Only .claude/hooks/ is real source,
# so we skip the mirror subdirs but keep hooks.
# _impeccable-upstream-source/ is a vendored external mirror (same file ×16 copies
# for different agent platforms) — not guild source, not useful for unity analysis.
SKIP_FRAGMENTS = [
    "/.claude/state/",
    "/.claude/arsenal/",
    "/.claude/skills/",
    "/.claude/agents/",
    "/.claude/hooks/.deprecated/",
    "/_impeccable-upstream-source/",
    "/evolution/",
    "/star-alliance-arsenal/models/",
    "/art/",
    "/desktop/",
    "/mcp/.venv/",
]

# ── Path prefix patterns to skip (via glob) ─────────────────────────────────
SKIP_PREFIX_GLOBS = [".scratch*"]


def _should_skip(rel_path: str) -> bool:
    """Return True if the relative path should be excluded from scanning."""
    parts = rel_path.replace("\\", "/").split("/")
    for part in parts:
        if part in SKIP_DIRS:
            return True
    for frag in SKIP_FRAGMENTS:
        if frag in ("/" + rel_path + "/"):
            return True
    # Check .scratch* prefix on any path component
    for part in parts:
        for glob_pat in SKIP_PREFIX_GLOBS:
            prefix = glob_pat.rstrip("*")
            if part.startswith(prefix):
                return True
    return False


# ── Generic names that are too common to be useful duplication candidates ───
# These are language idioms, lifecycle hooks, or standard names that appear in
# nearly every file and don't represent real duplication.
NOISE_NAMES = {
    "main",
    "check",
    "init",
    "run",
    "start",
    "stop",
    "sync",
    "tick",
    "desc",
    "test",
    "setup",
    "teardown",
    "handle",
    "process",
    "parse",
    "load",
    "save",
    "open",
    "close",
    "read",
    "write",
    "get",
    "set",
    "add",
    "remove",
    "update",
    "delete",
    "create",
    "build",
    "make",
    "apply",
    "handleEvent",
    "handleError",
    "handleMessage",
    "handleMouseMove",
    "handleClick",
    "handleKey",
    "handleKeyDown",
    "handleKeyUp",
    "handleInput",
    "handleScroll",
    "handleResize",
    "handleDrop",
    "handleDrag",
    "handleDragStart",
    "handleDragEnd",
    "handleDragOver",
    "handleMouseMove",
    "handleMouseDown",
    "handleMouseUp",
    "handleTouchStart",
    "handleTouchEnd",
    "handleTouchMove",
    "handlePointerDown",
    "handlePointerUp",
    "handlePointerMove",
    "handleWheel",
    "handleFocus",
    "handleBlur",
    "handleChange",
    "handleSubmit",
    "handleSelect",
    "handleToggle",
    "handleClose",
    "handleOpen",
    "handleCancel",
    "handleConfirm",
    "handleReset",
    "handleNext",
    "handlePrev",
    "handleBack",
    "handleForward",
    "handleEnter",
    "handleExit",
    "handleTransitionEnd",
    "handleAnimationEnd",
    "handleLoad",
    "handleUnload",
    "handleBeforeUnload",
    "handleResize",
    "handleError",
    "handleAbort",
    "handleTimeout",
    "handleSuccess",
    "handleFailure",
    "handleComplete",
    "handleProgress",
    "handleReady",
    "handleConnect",
    "handleDisconnect",
    "handleOnline",
    "handleOffline",
    "handleVisible",
    "handleHidden",
    "handlePlay",
    "handlePause",
    "handleStop",
    "handleSeek",
    "handleVolume",
    "handleMute",
    "handleUnmute",
    "handleFullscreen",
    "handlePictureInPicture",
}

# ── Local path/state resolution patterns ────────────────────────────────────
# These are per-script locals for repo-root resolution, state-dir paths, and
# project-root discovery. Every hook/script defines its own — they're not
# real duplication, just the standard boilerplate pattern.
NOISE_NAMES.update({
    "REPO_ROOT", "ROOT", "PROJECT_ROOT", "LEX_ROOT", "STAR_ALLIANCE_ROOT",
    "project_dir", "project_root", "repo_root", "repo",
    "default_root", "root", "here", "this_dir", "base_dir", "base_path",
    "_proj", "_root", "_repo", "_here", "_dir", "_path", "_base",
    "_ledger", "_state_dir", "_state", "_hooks_dir", "_arsenal_dir",
    "state_dir", "hooks_dir", "arsenal_dir", "skills_dir",
    "COMMANDS", "ARGS", "ARGUMENTS", "OPTIONS", "CONFIG",
    "DATA", "META", "RESULTS", "OUTPUT", "OUTPUT_DIR",
    "path", "rel_path", "abs_path", "full_path", "file_path", "dir_path",
    "name", "key", "val", "value", "data", "item", "entry", "result",
    "verbose", "debug", "dry", "quiet",
})

# ── More boilerplate: kill-switch checks, regex helpers, FM frontmatter ──
# _is_kill_switch / _is_disarmed is the standard guard every gate runs.
# HERE is the per-file dirname-anchor pattern (same as _here above but UPPER).
# FM_RE / REPO are per-file constants for frontmatter regex / repo path.
NOISE_NAMES.update({
    "_is_kill_switch", "_is_disarmed", "is_disarmed", "is_kill_switch",
    "HERE", "REPO", "FM_RE", "FM",
    "default_repo", "canonical_repo", "repo_path",
    "cmd_detect", "cmd_apply", "cmd_report",  # cleanup script CLI dispatchers
    "artNum", "collectBody", "reconcile", "stripWikilinks", "toAr",  # parse_law family
    "AR_DIGITS", "BIS", "RE_H2", "RE_H3", "RE_H4", "RE_H5",  # parse_law regexes
    "RE_PROMUL", "RE_TABLE", "RE_SECTION",  # parse_law regexes
})

# ── Regex patterns for definition extraction ────────────────────────────────

# Python: class definitions
RE_PY_CLASS = re.compile(r"^\s*class\s+([A-Za-z_][A-Za-z0-9_]*)", re.M)
# Python: @dataclass decorator (capture the class line that follows)
RE_PY_DATACLASS = re.compile(r"@dataclass\s*\n\s*class\s+([A-Za-z_][A-Za-z0-9_]*)", re.M)
# Python: module-level UPPER_CASE constant assignments
RE_PY_CONST = re.compile(
    r"^([A-Z][A-Z0-9_]*)\s*=\s*[^\n]", re.M
)
# Python: def (function) — capture name
RE_PY_DEF = re.compile(r"^\s*def\s+([A-Za-z_][A-Za-z0-9_]*)", re.M)
# Python: service/client instantiation — new client objects
RE_PY_SERVICE = re.compile(
    r"=\s*(?:createClient|SupabaseClient|supabase|Supabase|Client|"
    r"ServiceClient|APIClient|HttpClient|create_client|Client\(?"
    r"|AsyncClient|createAsyncClient)"
    r"\s*\(", re.M
)
# Also catch variable = SomeService(...)
RE_PY_SERVICE_NAMED = re.compile(
    r"=\s*([A-Z][A-Za-z0-9_]*(?:Client|Service|Supabase|API|Adapter|Connector))\s*\(",
    re.M,
)

# JS/TS: class definitions
RE_JS_CLASS = re.compile(r"^\s*class\s+([A-Za-z_$][A-Za-z0-9_$]*)", re.M)
# TS: interface definitions
RE_TS_INTERFACE = re.compile(r"^\s*interface\s+([A-Za-z_$][A-Za-z0-9_$]*)", re.M)
# TS: type definitions
RE_TS_TYPE = re.compile(r"^\s*type\s+([A-Za-z_$][A-Za-z0-9_$]*)\s*[=<{]", re.M)
# JS/TS: const declarations (named constants)
RE_JS_CONST = re.compile(
    r"^\s*(?:export\s+)?const\s+([A-Za-z_$][A-Za-z0-9_$]*)\s*=", re.M
)
# JS/TS: function declarations
RE_JS_FUNC = re.compile(
    r"^\s*(?:export\s+)?(?:async\s+)?function\s+([A-Za-z_$][A-Za-z0-9_$]*)", re.M
)
# JS/TS: arrow functions assigned to const (const foo = (...) => ...)
RE_JS_ARROW = re.compile(
    r"^\s*(?:export\s+)?const\s+([A-Za-z_$][A-Za-z0-9_$]*)\s*=\s*(?:async\s+)?\([^)]*\)\s*=>",
    re.M,
)
# JS/TS: service/client instantiation — new SomeClient(...)
RE_JS_SERVICE = re.compile(
    r"=\s*new\s+([A-Z][A-Za-z0-9_]*(?:Client|Service|Supabase|API|Adapter|Connector))\s*\(",
    re.M,
)
# JS/TS: createClient / supabase client creation
RE_JS_CREATE_CLIENT = re.compile(
    r"=\s*(?:createClient|supabase|createSupabaseClient|SupabaseClient)"
    r"\s*\(", re.M
)


def _scan_python(text: str):
    """Yield (name, line, kind) tuples from Python source."""
    seen = set()  # (name, line) dedup

    for m in RE_PY_DATACLASS.finditer(text):
        line = text[: m.start()].count("\n") + 1
        name = m.group(1)
        key = (name, line)
        if key not in seen:
            seen.add(key)
            yield name, line, "type"

    for m in RE_PY_CLASS.finditer(text):
        line = text[: m.start()].count("\n") + 1
        name = m.group(1)
        key = (name, line)
        if key not in seen:
            seen.add(key)
            yield name, line, "type"

    for m in RE_PY_DEF.finditer(text):
        line = text[: m.start()].count("\n") + 1
        name = m.group(1)
        key = (name, line)
        if key not in seen:
            seen.add(key)
            yield name, line, "utility"

    for m in RE_PY_CONST.finditer(text):
        name = m.group(1)
        # Skip very short names (like "A", "X") and __dunder__
        if len(name) < 3 or name.startswith("__"):
            continue
        line = text[: m.start()].count("\n") + 1
        key = (name, line)
        if key not in seen:
            seen.add(key)
            yield name, line, "constant"

    for m in RE_PY_SERVICE.finditer(text):
        line = text[: m.start()].count("\n") + 1
        # Use a generic "service" name from the match context
        # Find the variable name being assigned
        line_start = text.rfind("\n", 0, m.start()) + 1
        prefix = text[line_start : m.start()].strip()
        var_match = re.match(r"([a-z_][A-Za-z0-9_]*)\s*$", prefix)
        name = var_match.group(1) if var_match else "client"
        key = (name, line)
        if key not in seen:
            seen.add(key)
            yield name, line, "service"

    for m in RE_PY_SERVICE_NAMED.finditer(text):
        line = text[: m.start()].count("\n") + 1
        name = m.group(1)
        key = (name, line)
        if key not in seen:
            seen.add(key)
            yield name, line, "service"


def _scan_jsts(text: str):
    """Yield (name, line, kind) tuples from JS/TS source."""
    seen = set()

    for m in RE_TS_INTERFACE.finditer(text):
        line = text[: m.start()].count("\n") + 1
        name = m.group(1)
        key = (name, line)
        if key not in seen:
            seen.add(key)
            yield name, line, "type"

    for m in RE_TS_TYPE.finditer(text):
        line = text[: m.start()].count("\n") + 1
        name = m.group(1)
        key = (name, line)
        if key not in seen:
            seen.add(key)
            yield name, line, "type"

    for m in RE_JS_CLASS.finditer(text):
        line = text[: m.start()].count("\n") + 1
        name = m.group(1)
        key = (name, line)
        if key not in seen:
            seen.add(key)
            yield name, line, "type"

    for m in RE_JS_FUNC.finditer(text):
        line = text[: m.start()].count("\n") + 1
        name = m.group(1)
        key = (name, line)
        if key not in seen:
            seen.add(key)
            yield name, line, "utility"

    for m in RE_JS_ARROW.finditer(text):
        line = text[: m.start()].count("\n") + 1
        name = m.group(1)
        key = (name, line)
        if key not in seen:
            seen.add(key)
            yield name, line, "utility"

    for m in RE_JS_CONST.finditer(text):
        name = m.group(1)
        # Arrow functions are already captured by RE_JS_ARROW; skip them here
        # to avoid double-categorizing. Check if this const is an arrow func.
        # Upper-case const → constant; lower-case → skip (likely a variable)
        line_start = text.rfind("\n", 0, m.start()) + 1
        rest = text[m.start() :]
        # Skip if it's an arrow function (already handled)
        if re.match(
            r"(?:export\s+)?const\s+" + re.escape(name) + r"\s*=\s*(?:async\s+)?\([^)]*\)\s*=>",
            text[line_start : m.start() + 200],
        ):
            continue
        if len(name) < 3:
            continue
        # UPPER_CASE or PascalCase → constant; camelCase starting with uppercase → constant
        if name[0].isupper():
            line = text[: m.start()].count("\n") + 1
            key = (name, line)
            if key not in seen:
                seen.add(key)
                yield name, line, "constant"

    for m in RE_JS_SERVICE.finditer(text):
        line = text[: m.start()].count("\n") + 1
        name = m.group(1)
        key = (name, line)
        if key not in seen:
            seen.add(key)
            yield name, line, "service"

    for m in RE_JS_CREATE_CLIENT.finditer(text):
        line = text[: m.start()].count("\n") + 1
        line_start = text.rfind("\n", 0, m.start()) + 1
        prefix = text[line_start : m.start()].strip()
        var_match = re.match(r"(?:const|let|var)\s+([a-z_$][A-Za-z0-9_$]*)\s*$", prefix)
        name = var_match.group(1) if var_match else "client"
        key = (name, line)
        if key not in seen:
            seen.add(key)
            yield name, line, "service"


def _scan_json(text: str):
    """JSON files don't have definitions in the traditional sense — skip."""
    return []


def _scan_file(path: Path, rel: str):
    """Scan a single file and yield (name, file_path, line, kind) tuples."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return

    ext = path.suffix.lower()

    if ext == ".py":
        scanner = _scan_python
    elif ext in (".js", ".ts", ".tsx"):
        scanner = _scan_jsts
    elif ext == ".json":
        scanner = _scan_json
    elif ext in (".yaml", ".yml"):
        scanner = _scan_json  # YAML has no top-level definitions to harvest
    else:
        return

    for name, line, kind in scanner(text):
        yield name, rel, line, kind


def scan_repo():
    """Walk the repo and return (definitions, total_files)."""
    definitions = []  # list of (name, file, line, kind)

    # Use git ls-files for efficiency, fall back to os.walk
    try:
        import subprocess

        result = subprocess.run(
            ["git", "ls-files"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=10,
        )
        tracked = [ln.strip() for ln in result.stdout.splitlines() if ln.strip()]
    except Exception:
        tracked = []
        for dirpath, dirnames, filenames in os.walk(ROOT):
            # Skip excluded dirs in-place
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
            for fn in filenames:
                fp = Path(dirpath) / fn
                rel = str(fp.relative_to(ROOT))
                tracked.append(rel)

    total_files = 0
    seen_files = set()

    for rel in tracked:
        rel_norm = rel.replace("\\", "/")
        if _should_skip(rel_norm):
            continue
        ext = os.path.splitext(rel_norm)[1].lower()
        if ext not in SCAN_EXTS:
            continue
        fp = ROOT / rel_norm
        if not fp.is_file():
            continue
        if rel_norm in seen_files:
            continue
        seen_files.add(rel_norm)
        total_files += 1
        for name, file_path, line, kind in _scan_file(fp, rel_norm):
            definitions.append({"name": name, "file": file_path, "line": line, "kind": kind})

    return definitions, total_files


def find_candidates(definitions):
    """Find names defined in more than one file. Return candidate list sorted by blast radius."""
    from collections import defaultdict

    name_map = defaultdict(list)  # (name, kind) → [defs]
    for d in definitions:
        # Skip generic noise names — they're language idioms, not real duplication
        if d["name"] in NOISE_NAMES:
            continue
        name_map[(d["name"], d["kind"])].append(d)

    candidates = []
    for (name, kind), defs in name_map.items():
        # Count distinct files
        files = set(d["file"] for d in defs)
        if len(files) > 1:
            candidates.append(
                {
                    "name": name,
                    "kind": kind,
                    "definitions": [
                        {"file": d["file"], "line": d["line"]} for d in sorted(defs, key=lambda x: x["file"])
                    ],
                    "blast_radius": len(files),
                }
            )

    # Sort by blast_radius descending, then name
    candidates.sort(key=lambda c: (-c["blast_radius"], c["name"]))
    return candidates


def main():
    parser = argparse.ArgumentParser(description="Code Unity scanner")
    parser.add_argument(
        "--report",
        action="store_true",
        help="Print human-readable table instead of JSON",
    )
    args = parser.parse_args()

    definitions, total_files = scan_repo()
    candidates = find_candidates(definitions)

    report = {
        "scan_ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "total_files": total_files,
        "total_definitions": len(definitions),
        "candidates": candidates,
    }

    if args.report:
        print("═" * 72)
        print(" CODE UNITY SCAN — Star Alliance repo")
        print("═" * 72)
        print(f" Scan timestamp    : {report['scan_ts']}")
        print(f" Files scanned     : {total_files}")
        print(f" Definitions found  : {len(definitions)}")
        print(f" Candidates (dupes) : {len(candidates)}")
        print("─" * 72)
        if not candidates:
            print(" ✓ 0 candidates — clean (no name collisions found)")
        else:
            print(f" Top {min(len(candidates), 30)} candidates by blast radius:")
            print()
            print(f" {'NAME':<35} {'KIND':<12} {'FILES':>5}  DEFINITIONS")
            print(" " + "─" * 70)
            for c in candidates[:30]:
                name = c["name"][:35]
                kind = c["kind"][:12]
                br = c["blast_radius"]
                def_str = ", ".join(
                    f"{d['file'].split('/')[-1]}:{d['line']}" for d in c["definitions"][:4]
                )
                if len(c["definitions"]) > 4:
                    def_str += f", +{len(c['definitions']) - 4} more"
                print(f" {name:<35} {kind:<12} {br:>5}  {def_str}")
        print("═" * 72)
    else:
        print(json.dumps(report, indent=2))

    # Exit 0 always — it's a scanner, not a gate
    return 0


if __name__ == "__main__":
    sys.exit(main())