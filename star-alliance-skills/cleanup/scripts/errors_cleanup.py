#!/usr/bin/env python3
"""errors_cleanup.py — dev-error log triage for the cleanup skill.

Reads /tmp/lex-dev.log (tee'd `npx turbo dev` stdout/stderr + the
DevErrorSink client-error payloads), groups + dedupes entries, and
classifies each as `code-bug` / `framework-noise` / `external` /
`unknown`. The cleanup skill's `errors` mode reads the JSON output
and surfaces a triage list to the user.

Subcommands
-----------
detect    Parse the log (optionally --since the last cleanup marker)
          and write /tmp/dev_errors.json.
classify  Re-read /tmp/dev_errors.json, attach a class to each entry,
          write /tmp/dev_errors_classified.json + print summary.
mark      Record the current log EOF in /tmp/last_errors_cleanup_offset
          so the next `detect --since` only sees new entries.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Iterable

LOG_PATH = Path("/tmp/lex-dev.log")
MARKER_PATH = Path("/tmp/last_errors_cleanup_offset")
DETECT_OUT = Path("/tmp/dev_errors.json")
CLASSIFY_OUT = Path("/tmp/dev_errors_classified.json")

# ── regexes ──────────────────────────────────────────────────────────

# A line that starts a server-side error block.
SERVER_ERR_RE = re.compile(
    r"^(?:\s*[⨯×]\s+)?"  # Next.js error glyph (optional)
    r"(?:\[Error\]\s+|unhandledRejection:\s+|uncaughtException:\s+)?"
    r"(TypeError|ReferenceError|SyntaxError|RangeError|Error|"
    r"PostgrestError|AuthError|FetchError|AbortError):\s+(.+)$"
)

# Client-error block (one-line JSON appended by the API route).
CLIENT_ERR_RE = re.compile(r"^\[CLIENT_ERROR\s+(\S+)\]\s+(\{.*\})\s*$")

# A stack-trace line.
STACK_LINE_RE = re.compile(r"^\s+at\s+(.+?)\s+\((.+?):(\d+):(\d+)\)\s*$")
STACK_LINE_BARE_RE = re.compile(r"^\s+at\s+(.+?):(\d+):(\d+)\s*$")

# Routes Next.js logs: ` ○ Compiling /foo`, ` ✓ Compiled /foo`, ` GET /foo 200 in 12ms`
ROUTE_RE = re.compile(r"\s(?:GET|POST|PUT|DELETE|PATCH)\s+(/[^\s]+)\s+\d{3}")

# Framework-noise signals.
NOISE_SIGNALS = [
    "Fast Refresh had to perform a full reload",
    "Hot reload",
    "[HMR]",
    "webpack-internal",
    "node_modules/next/",
    "node_modules/react/",
    "node_modules/react-dom/",
    "Download the React DevTools",
    "[Deprecation]",
    # The next-intl missing-key warning is noisy but not a bug per se.
    "MISSING_MESSAGE",
    # L14: ThemeToggle hydration noise. The server renders <html> without a
    # theme attribute; the sync bootstrap script in app/layout.tsx sets
    # data-theme on the client immediately to kill FOUC. React flags the
    # resulting attribute diff on <html> every dev session — not a bug.
    "Extra attributes from the server",
    "Warning: Extra attributes",
    # L14: React StrictMode double-invocation. StrictMode intentionally calls
    # render/lifecycle twice in dev, so the same error signature can surface
    # exactly twice consecutively with no intervening route. Structurally
    # detecting the "exactly twice consecutive" pattern is a future refinement
    # (would key off dedupe count==2 + single route + adjacent timestamps);
    # for now the literal hydration signatures above cover the common case and
    # the dedupe step already collapses the doubled entries into one count=2 row.
]

# Repo-root markers — anything under these counts as a code-bug.
REPO_PATHS = ["apps/web/", "packages/md/", "packages/auth/", "packages/supabase/"]


# ── data ─────────────────────────────────────────────────────────────


@dataclass
class ErrorEntry:
    kind: str  # 'client' | 'server'
    message: str
    error_type: str = ""
    file: str | None = None
    line: int | None = None
    col: int | None = None
    stack: list[str] = field(default_factory=list)
    route: str | None = None
    url: str | None = None
    timestamps: list[str] = field(default_factory=list)
    count: int = 1
    raw_first: str = ""

    def signature(self) -> str:
        # Dedupe key: error type + first message line + first stack frame's file:line.
        first_frame = self.stack[0] if self.stack else (self.file or "?")
        return f"{self.error_type}|{self.message[:200]}|{first_frame}"


# ── log reader ───────────────────────────────────────────────────────


def read_log(since_offset: int = 0) -> tuple[str, int]:
    if not LOG_PATH.exists():
        sys.stderr.write(
            f"error: {LOG_PATH} does not exist. Start dev with:\n"
            f"  npx turbo dev 2>&1 | tee {LOG_PATH}\n"
        )
        sys.exit(2)
    size = LOG_PATH.stat().st_size
    start = since_offset if 0 <= since_offset <= size else 0
    with LOG_PATH.open("rb") as f:
        f.seek(start)
        data = f.read()
    return data.decode("utf-8", errors="replace"), size


# ── parsing ──────────────────────────────────────────────────────────


def parse_stack(lines: list[str], idx: int) -> tuple[list[str], int]:
    stack: list[str] = []
    j = idx
    while j < len(lines):
        m = STACK_LINE_RE.match(lines[j]) or STACK_LINE_BARE_RE.match(lines[j])
        if not m:
            break
        stack.append(lines[j].strip())
        j += 1
    return stack, j


def first_repo_frame(stack: Iterable[str]) -> tuple[str, int] | None:
    for frame in stack:
        for prefix in REPO_PATHS:
            idx = frame.find(prefix)
            if idx == -1:
                continue
            # Pull path:line:col after the prefix marker.
            tail = frame[idx:]
            m = re.search(r"(\S+?):(\d+):\d+", tail)
            if m:
                return m.group(1), int(m.group(2))
        # Webpack-internal paths: ignore.
    return None


def parse_entries(text: str) -> list[ErrorEntry]:
    lines = text.splitlines()
    entries: list[ErrorEntry] = []
    current_route: str | None = None
    i = 0
    while i < len(lines):
        line = lines[i]

        # Track the last logged route so server errors can be tagged with it.
        rm = ROUTE_RE.search(line)
        if rm:
            current_route = rm.group(1)
            i += 1
            continue

        # Client-error payload (one JSON line).
        cm = CLIENT_ERR_RE.match(line)
        if cm:
            ts, blob = cm.group(1), cm.group(2)
            try:
                payload = json.loads(blob)
            except json.JSONDecodeError:
                i += 1
                continue
            entry = ErrorEntry(
                kind="client",
                message=str(payload.get("msg", ""))[:500],
                error_type=str(payload.get("kind", "error")),
                file=payload.get("src"),
                line=payload.get("line"),
                col=payload.get("col"),
                stack=(payload.get("stack") or "").splitlines() if payload.get("stack") else [],
                url=payload.get("url"),
                timestamps=[ts],
                raw_first=line[:500],
            )
            entries.append(entry)
            i += 1
            continue

        # Server-error first line.
        sm = SERVER_ERR_RE.match(line)
        if sm:
            err_type, msg = sm.group(1), sm.group(2)
            stack, next_i = parse_stack(lines, i + 1)
            frame = first_repo_frame(stack)
            entries.append(
                ErrorEntry(
                    kind="server",
                    message=msg.strip()[:500],
                    error_type=err_type,
                    file=frame[0] if frame else None,
                    line=frame[1] if frame else None,
                    stack=stack,
                    route=current_route,
                    raw_first=line[:500],
                )
            )
            i = next_i
            continue

        i += 1

    return entries


# ── dedupe ──────────────────────────────────────────────────────────


def dedupe(entries: list[ErrorEntry]) -> list[ErrorEntry]:
    grouped: dict[str, ErrorEntry] = {}
    for e in entries:
        sig = e.signature()
        if sig in grouped:
            g = grouped[sig]
            g.count += 1
            g.timestamps.extend(e.timestamps)
            if e.route and e.route not in (g.route or "").split(","):
                g.route = ",".join(filter(None, [g.route, e.route]))
        else:
            grouped[sig] = e
    return list(grouped.values())


# ── classify ────────────────────────────────────────────────────────


def classify(entry: ErrorEntry) -> str:
    haystack = " ".join(
        filter(
            None,
            [entry.raw_first, entry.message, entry.file or "", *entry.stack],
        )
    )
    for sig in NOISE_SIGNALS:
        if sig in haystack:
            return "framework-noise"
    if any(p in haystack for p in REPO_PATHS):
        return "code-bug"
    # Network / external — fetch / Supabase / 3rd-party domain.
    if any(
        s in entry.message.lower()
        for s in ("fetch failed", "econnrefused", "enotfound", "etimedout", "network", "supabase")
    ):
        return "external"
    return "unknown"


# ── subcommands ─────────────────────────────────────────────────────


def cmd_detect(args: argparse.Namespace) -> int:
    offset = 0
    if args.since and MARKER_PATH.exists():
        try:
            offset = int(MARKER_PATH.read_text().strip() or "0")
        except ValueError:
            offset = 0
    text, eof = read_log(since_offset=offset)
    entries = parse_entries(text)
    deduped = dedupe(entries)
    DETECT_OUT.write_text(
        json.dumps(
            {
                "from_offset": offset,
                "to_offset": eof,
                "total_raw": len(entries),
                "total_unique": len(deduped),
                "entries": [asdict(e) for e in deduped],
            },
            indent=2,
        )
    )
    print(f"detect: parsed {len(entries)} raw → {len(deduped)} unique → {DETECT_OUT}")
    return 0


def cmd_classify(args: argparse.Namespace) -> int:
    if not DETECT_OUT.exists():
        sys.stderr.write(f"error: {DETECT_OUT} missing — run `detect` first\n")
        return 2
    payload = json.loads(DETECT_OUT.read_text())
    by_class: dict[str, list[dict]] = defaultdict(list)
    for raw in payload["entries"]:
        e = ErrorEntry(**{k: v for k, v in raw.items() if k in ErrorEntry.__dataclass_fields__})
        cls = classify(e)
        item = {**raw, "class": cls}
        by_class[cls].append(item)
    CLASSIFY_OUT.write_text(
        json.dumps(
            {
                "from_offset": payload["from_offset"],
                "to_offset": payload["to_offset"],
                "counts": {k: len(v) for k, v in by_class.items()},
                "by_class": by_class,
            },
            indent=2,
        )
    )

    print(f"classify: {sum(len(v) for v in by_class.values())} unique errors")
    for cls in ("code-bug", "external", "unknown", "framework-noise"):
        items = by_class.get(cls, [])
        if not items:
            continue
        print(f"\n── {cls} ({len(items)}) ──")
        for it in items[:20]:
            loc = f" {it['file']}:{it['line']}" if it.get("file") else ""
            route = f" route={it['route']}" if it.get("route") else ""
            cnt = f" x{it['count']}" if it.get("count", 1) > 1 else ""
            print(f"  [{it['error_type']}] {it['message'][:120]}{loc}{route}{cnt}")
    print(f"\n→ {CLASSIFY_OUT}")
    return 0


def cmd_mark(args: argparse.Namespace) -> int:
    if not LOG_PATH.exists():
        sys.stderr.write(f"error: {LOG_PATH} missing\n")
        return 2
    size = LOG_PATH.stat().st_size
    MARKER_PATH.write_text(str(size))
    print(f"mark: offset {size} → {MARKER_PATH}")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description="Dev-error log triage for the cleanup skill.")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_detect = sub.add_parser("detect", help="Parse the log and write /tmp/dev_errors.json")
    p_detect.add_argument(
        "--since",
        action="store_true",
        help="Only read from the last `mark` offset (default: read full log)",
    )
    p_detect.set_defaults(func=cmd_detect)

    p_classify = sub.add_parser("classify", help="Classify entries; print summary")
    p_classify.set_defaults(func=cmd_classify)

    p_mark = sub.add_parser("mark", help="Record current log EOF for next --since run")
    p_mark.set_defaults(func=cmd_mark)

    args = p.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
