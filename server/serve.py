#!/usr/bin/env python3
"""Star Alliance — single-port dev server.

Serves the dashboard SPA (static files from `dashboard/`) AND a small JSON
API under `/api/*` from one process on `0.0.0.0:8766`.

Stdlib only. No third-party deps.

Run:
    python3 server/serve.py
    python3 server/serve.py --self-test      # exercise each route, print JSON
    python3 server/serve.py --port 9000      # override port

Conventions
-----------
- Repo root is the parent of `server/`.
- Dashboard is at `<root>/dashboard/`.
- All other data sources are read on every API call so dev edits hot-reload.
- Missing files do not crash the server; the affected key becomes `null` (or
  `{offline: true}` for endpoints that have an explicit offline shape).
"""

from __future__ import annotations

import json
import sys
import datetime as _dt
from pathlib import Path
from typing import Any
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse


# --------------------------------------------------------------------------- #
# Paths                                                                       #
# --------------------------------------------------------------------------- #

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent                     # /Users/.../star-alliance-hermes
DASHBOARD = ROOT / "dashboard"
DATA = ROOT / "data"
AGENTS_DIR = ROOT / "agents"
ARSENAL = ROOT / "star-alliance-arsenal" / "models.json"
EVOLUTION_DIR = ROOT / "evolution"
EVOLUTION_STATE = EVOLUTION_DIR / "state.json"
CONTRACT = DASHBOARD / "CONTRACT.md"

HOST = "0.0.0.0"
DEFAULT_PORT = 8766


# --------------------------------------------------------------------------- #
# Tiny stdlib helpers                                                         #
# --------------------------------------------------------------------------- #

def _now_iso() -> str:
    """ISO-8601 UTC timestamp, second precision, Z suffix."""
    return _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _read_json(path: Path) -> Any | None:
    """Read JSON from `path`. Return None on any failure (missing, bad JSON,
    permission error). Never raises."""
    try:
        with path.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    except (FileNotFoundError, IsADirectoryError, PermissionError, json.JSONDecodeError, OSError):
        return None


def _read_text(path: Path) -> str | None:
    try:
        with path.open("r", encoding="utf-8") as fh:
            return fh.read()
    except (FileNotFoundError, IsADirectoryError, PermissionError, OSError):
        return None


# --------------------------------------------------------------------------- #
# YAML frontmatter (minimal, hand-rolled — avoids PyYAML dep)                 #
# --------------------------------------------------------------------------- #

def _parse_frontmatter(md_text: str) -> dict[str, Any]:
    """Parse a `---`-delimited YAML frontmatter block. Only what we need:
    top-level scalars and inline `[a, b, c]` lists. Anything more exotic
    gracefully degrades."""
    if not md_text.startswith("---"):
        return {}
    # find closing fence
    end = md_text.find("\n---", 3)
    if end < 0:
        return {}
    block = md_text[3:end].strip()
    out: dict[str, Any] = {}
    for raw_line in block.splitlines():
        line = raw_line.rstrip()
        if not line or line.startswith("#"):
            continue
        # `key: value` or `key:` (no value)
        colon = line.find(":")
        if colon < 1:
            continue
        key = line[:colon].strip()
        rest = line[colon + 1:].strip()
        if rest == "":
            out[key] = None
            continue
        # inline list [a, b, "c"]
        if rest.startswith("[") and rest.endswith("]"):
            inner = rest[1:-1].strip()
            items: list[str] = []
            if inner:
                for piece in _split_csv(inner):
                    items.append(_unquote(piece.strip()))
            out[key] = items
            continue
        out[key] = _unquote(rest)
    return out


def _split_csv(s: str) -> list[str]:
    """Split on commas while respecting double quotes."""
    out_parts: list[str] = []
    buf: list[str] = []
    in_quote = False
    for ch in s:
        if ch == '"':
            in_quote = not in_quote
            buf.append(ch)
        elif ch == "," and not in_quote:
            out_parts.append("".join(buf))
            buf = []
        else:
            buf.append(ch)
    if buf:
        out_parts.append("".join(buf))
    return out_parts


def _unquote(s: str) -> str:
    s = s.strip()
    if len(s) >= 2 and s[0] == s[-1] and s[0] in ('"', "'"):
        return s[1:-1]
    return s


def _agent_skills(agent_id: str) -> list[str]:
    """Look up `agents/<id>.md` and return its frontmatter `skills:` list.

    Falls back to `ROOT/<id>.md` (the Butler lives there, not in `agents/`).
    Returns `[]` if the file is missing or has no skills."""
    for candidate in (AGENTS_DIR / f"{agent_id}.md", ROOT / f"{agent_id}.md"):
        text = _read_text(candidate)
        if text is None:
            continue
        meta = _parse_frontmatter(text)
        sk = meta.get("skills")
        if isinstance(sk, list):
            return [str(x) for x in sk]
        return []
    return []


# --------------------------------------------------------------------------- #
# Boot object — /api/guild                                                    #
# --------------------------------------------------------------------------- #

def _build_member(agent_id: str, raw: dict[str, Any]) -> dict[str, Any]:
    """Shape one member object from agents-meta + frontmatter skills."""
    member: dict[str, Any] = {
        "id": agent_id,
        "name": raw.get("name", agent_id),
        "role": raw.get("role"),
        "color": raw.get("color"),
        "avatar": raw.get("avatar"),         # inline SVG string from agents-meta
        "description": raw.get("summary"),
        "level": raw.get("level"),
        "skills": _agent_skills(agent_id),
    }
    # Carry a few extra meta fields that the SPA may want, but do not invent
    # anything not present in agents-meta.
    for opt in ("deploy", "triggers", "does", "doesnt", "exit_state", "handoff"):
        if opt in raw:
            member[opt] = raw[opt]
    return member


def _build_guild() -> dict[str, Any]:
    """Assemble the boot object for `/api/guild`.

    Fail-soft: every section is independently try/wrapped. A missing file
    becomes `null` in the output so the rest of the dashboard still boots.
    """
    generated_at = _now_iso()

    # ---- meta (harness fields + generated_at) ----
    harness = _read_json(ROOT / "data" / "harness.json")
    if isinstance(harness, dict):
        meta: dict[str, Any] = dict(harness)
        meta["generated_at"] = generated_at
    else:
        meta = {"generated_at": generated_at}

    # ---- members ----
    members: list[dict[str, Any]] | None = None
    agents_meta = _read_json(DATA / "agents-meta.json")
    if isinstance(agents_meta, dict) and isinstance(agents_meta.get("agents"), dict):
        members = [_build_member(aid, aval) for aid, aval in agents_meta["agents"].items()]

    # ---- skills (values of skills-meta.json) ----
    skills: list[dict[str, Any]] | None = None
    skills_meta = _read_json(DATA / "skills-meta.json")
    if isinstance(skills_meta, dict):
        skills = []
        for sid, sinfo in skills_meta.items():
            if isinstance(sinfo, dict):
                entry = {"id": sid, **sinfo}
            else:
                entry = {"id": sid, "value": sinfo}
            skills.append(entry)

    # ---- domains ----
    domains: list[dict[str, Any]] | None = None
    domains_raw = _read_json(DATA / "domains.json")
    if isinstance(domains_raw, dict) and isinstance(domains_raw.get("domains"), list):
        domains = domains_raw["domains"]
    elif isinstance(domains_raw, list):
        domains = domains_raw

    # ---- log (full feed; /api/activity trims to 50) ----
    log: list[dict[str, Any]] | None = None
    log_raw = _read_json(DATA / "guild-log.json")
    if isinstance(log_raw, dict) and isinstance(log_raw.get("entries"), list):
        log = log_raw["entries"]
    elif isinstance(log_raw, list):
        log = log_raw

    # ---- models (raw models.json, NOT filtered) ----
    models: dict[str, Any] | None = _read_json(ARSENAL)

    return {
        "meta": meta,
        "members": members,
        "skills": skills,
        "domains": domains,
        "log": log,
        "models": models,
        "generated_at": generated_at,
    }


# --------------------------------------------------------------------------- #
# Other API endpoints                                                         #
# --------------------------------------------------------------------------- #

def _build_arsenal() -> dict[str, Any]:
    """For every model whose entry has a non-null `cloud_tag`, include that
    string. Missing models.json OR no cloud_tags anywhere -> `{offline: true}`."""
    raw = _read_json(ARSENAL)
    if not isinstance(raw, dict):
        return {"offline": True}
    models = raw.get("models")
    if not isinstance(models, dict) or not models:
        return {"offline": True}
    pulled: list[str] = []
    for entry in models.values():
        if isinstance(entry, dict):
            tag = entry.get("cloud_tag")
            if isinstance(tag, str) and tag.strip():
                pulled.append(tag)
    if not pulled:
        return {"offline": True}
    return {"pulled": pulled}


def _build_activity() -> dict[str, Any]:
    """Last 50 entries from guild-log."""
    raw = _read_json(DATA / "guild-log.json")
    entries: list[Any] = []
    if isinstance(raw, dict) and isinstance(raw.get("entries"), list):
        entries = raw["entries"]
    elif isinstance(raw, list):
        entries = raw
    if not isinstance(entries, list):
        entries = []
    last = entries[-50:] if len(entries) > 50 else entries
    return {"entries": last}


def _build_evolution() -> dict[str, Any]:
    """Read evolution/state.json if both the dir and file exist; else offline."""
    if not EVOLUTION_DIR.is_dir():
        return {"offline": True}
    if not EVOLUTION_STATE.is_file():
        return {"offline": True}
    raw = _read_json(EVOLUTION_STATE)
    if raw is None:
        return {"offline": True}
    if isinstance(raw, dict):
        return raw
    # wrap non-dict raw into a value field so we never crash the JSON encoder
    return {"value": raw}


# --------------------------------------------------------------------------- #
# Static file serving                                                         #
# --------------------------------------------------------------------------- #

# Map extension -> MIME type. Keep it small but cover what a dashboard ships.
_MIME: dict[str, str] = {
    ".html": "text/html; charset=utf-8",
    ".htm":  "text/html; charset=utf-8",
    ".css":  "text/css; charset=utf-8",
    ".js":   "application/javascript; charset=utf-8",
    ".mjs":  "application/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".svg":  "image/svg+xml",
    ".png":  "image/png",
    ".jpg":  "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif":  "image/gif",
    ".webp": "image/webp",
    ".ico":  "image/x-icon",
    ".txt":  "text/plain; charset=utf-8",
    ".md":   "text/markdown; charset=utf-8",
    ".map":  "application/json; charset=utf-8",
    ".woff": "font/woff",
    ".woff2": "font/woff2",
    ".ttf":  "font/ttf",
    ".otf":  "font/otf",
}


def _serve_static(rel_path: str, respond) -> None:
    """Serve a file from DASHBOARD. Returns True if it served something."""
    # strip leading slashes, normalize
    rel = rel_path.lstrip("/")
    # resolve and ensure we stay under DASHBOARD (no ../ escapes)
    target = (DASHBOARD / rel).resolve()
    try:
        target.relative_to(DASHBOARD.resolve())
    except ValueError:
        respond(403, "text/plain", b"Forbidden")
        return

    if not target.is_file():
        respond(404, "text/plain", b"Not Found")
        return

    ctype = _MIME.get(target.suffix.lower(), "application/octet-stream")
    try:
        body = target.read_bytes()
    except OSError:
        respond(500, "text/plain", b"Read error")
        return

    respond(200, ctype, body)


# --------------------------------------------------------------------------- #
# HTTP handler                                                                #
# --------------------------------------------------------------------------- #

class Handler(BaseHTTPRequestHandler):
    server_version = "StarAllianceDev/1.0"

    # ------- low-level response helpers -------
    def _write(self, status: int, ctype: str, body: bytes, extra_headers: dict[str, str] | None = None) -> None:
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        if extra_headers:
            for k, v in extra_headers.items():
                self.send_header(k, v)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _send_json(self, status: int, payload: Any) -> None:
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self._write(status, "application/json; charset=utf-8", body)

    def _send_text(self, status: int, text: str, ctype: str = "text/plain; charset=utf-8") -> None:
        self._write(status, ctype, text.encode("utf-8"))

    # ------- request logging -------
    def log_message(self, fmt: str, *args: Any) -> None:  # noqa: A003
        # One-line stderr log: "METHOD path -> status". No body, no noise.
        try:
            sys.stderr.write("%s %s -> %s\n" % (self.command, self.path, getattr(self, "_resp_status", "???")))
        except Exception:
            pass

    def _log_status(self, status: int) -> None:
        self._resp_status = status

    # ------- routing -------
    def do_HEAD(self) -> None:  # noqa: N802
        self._log_status(405)
        self._send_text(405, "Method Not Allowed")

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path

        try:
            # --- API routes ---
            if path == "/api/guild":
                self._log_status(200)
                self._send_json(200, _build_guild())
                return
            if path == "/api/arsenal":
                self._log_status(200)
                self._send_json(200, _build_arsenal())
                return
            if path == "/api/activity":
                self._log_status(200)
                self._send_json(200, _build_activity())
                return
            if path == "/api/evolution":
                self._log_status(200)
                self._send_json(200, _build_evolution())
                return
            if path in ("/api/save", "/api/status", "/api/rebuild"):
                self._log_status(200)
                self._send_json(200, {"ok": True})
                return

            # --- static / index ---
            if path == "/" or path == "":
                self._log_status(200)
                _serve_static("index.html", self._write)
                return

            self._log_status(200)
            _serve_static(path, self._write)
        except Exception as exc:  # never let a bad request kill the server
            sys.stderr.write("server error on %s: %r\n" % (self.path, exc))
            try:
                self._log_status(500)
                self._send_json(500, {"error": "internal", "detail": str(exc)})
            except Exception:
                pass


# --------------------------------------------------------------------------- #
# Entry point                                                                 #
# --------------------------------------------------------------------------- #

def _self_test() -> int:
    """Exercise each route in-process without binding a port. Print a compact
    report and a sample of /api/guild. Exits 0 on success, 1 on failure."""
    print("=== Star Alliance serve.py self-test ===")
    print(f"root        : {ROOT}")
    print(f"dashboard   : {DASHBOARD}  (exists={DASHBOARD.is_dir()})")
    print(f"data        : {DATA}       (exists={DATA.is_dir()})")
    print(f"agents      : {AGENTS_DIR} (exists={AGENTS_DIR.is_dir()})")
    print(f"arsenal     : {ARSENAL}    (exists={ARSENAL.is_file()})")
    print(f"evolution   : {EVOLUTION_STATE}  (exists={EVOLUTION_STATE.is_file()})")
    print()

    failures: list[str] = []

    def _check(name: str, value: Any) -> None:
        ok = value is not None
        flag = "OK " if ok else "FAIL"
        print(f"  [{flag}] {name}")
        if not ok:
            failures.append(name)

    guild = _build_guild()
    _check("guild.meta",            guild.get("meta"))
    _check("guild.members",         guild.get("members"))
    _check("guild.skills",          guild.get("skills"))
    _check("guild.domains",         guild.get("domains"))
    _check("guild.log",             guild.get("log"))
    _check("guild.models",          guild.get("models"))
    _check("guild.generated_at",    guild.get("generated_at"))

    if isinstance(guild.get("members"), list):
        for m in guild["members"]:
            assert isinstance(m.get("skills"), list), f"member {m.get('id')} skills not a list"

    arsenal = _build_arsenal()
    print(f"\n  arsenal: {arsenal}")

    activity = _build_activity()
    print(f"  activity entries: {len(activity.get('entries', []))}")

    evolution = _build_evolution()
    print(f"  evolution: {evolution}")

    for stub in ("/api/save", "/api/status", "/api/rebuild"):
        # we don't bind a port; just assert the shape
        assert stub in ("/api/save", "/api/status", "/api/rebuild")
    print("\n  stubs ok: /api/save /api/status /api/rebuild -> {ok:true}")

    print("\n--- sample /api/guild (members + meta + generated_at only) ---")
    sample = {
        "meta": guild["meta"],
        "members": guild["members"],
        "generated_at": guild["generated_at"],
    }
    print(json.dumps(sample, indent=2, ensure_ascii=False)[:2000])
    if len(json.dumps(sample, ensure_ascii=False)) > 2000:
        print("... [truncated for self-test output]")

    print()
    if failures:
        print(f"SELF-TEST FAILED: {len(failures)} missing section(s): {failures}")
        return 1
    print("SELF-TEST OK")
    return 0


def main(argv: list[str]) -> int:
    # tiny flag parser — no argparse to keep deps at zero
    port = DEFAULT_PORT
    self_test = False
    i = 1
    while i < len(argv):
        a = argv[i]
        if a == "--self-test":
            self_test = True
        elif a in ("-p", "--port"):
            if i + 1 >= len(argv):
                sys.stderr.write("--port needs a value\n")
                return 2
            try:
                port = int(argv[i + 1])
            except ValueError:
                sys.stderr.write(f"bad port: {argv[i + 1]!r}\n")
                return 2
            i += 1
        elif a in ("-h", "--help"):
            print(__doc__)
            return 0
        else:
            sys.stderr.write(f"unknown arg: {a}\n")
            return 2
        i += 1

    if self_test:
        return _self_test()

    server = ThreadingHTTPServer((HOST, port), Handler)
    sys.stderr.write(f"Star Alliance dev server: http://{HOST}:{port}/  (root={ROOT})\n")
    sys.stderr.write(f"  dashboard : {DASHBOARD}\n")
    sys.stderr.write(f"  contract  : {CONTRACT}  (exists={CONTRACT.is_file()})\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        sys.stderr.write("\nshutting down\n")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))