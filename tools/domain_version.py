#!/usr/bin/env python3
"""domain_version.py — resolve a real version + history for every domain in
data/domains.json, from that domain's own true source of truth.

Never hand-edits data/domains.json (that file stays the project list only).
Called by build.py's load_domains() to merge version/versionSource/versionHistory
onto each domain dict before it enters guild["domains"].

Three resolver branches, keyed by domain id:

  star-alliance          -> reuses build.py's derive_version() log-replay
                             (data/guild-log.json), NOT reimplemented here.
  lex-council-app        -> reads (READ-ONLY) the app's package.json version.
                             History from `git tag -l 'v<major>.<minor>.*'`
                             in that repo (read-only); falls back to a single
                             current-point history entry if no tags match.
  lex-council-business    -> derives from vault-logs/*.md (excluding INDEX.md).
                             Each log = one version bump. Tier is read from
                             frontmatter `type:` if present, else inferred from
                             the filename slug (restructure -> MAJOR,
                             implementation/model/proposal -> MINOR, else PATCH).
                             Deterministic, order-independent (sorted by
                             date then filename).

Any domain id not in this map, or any source that is missing/unreadable,
resolves to version:null, versionSource:"unavailable" — this function must
NEVER crash the build.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

# ── External, read-only paths (outside this repo) ───────────────────────────

LEX_APP_PACKAGE_JSON = Path(
    "/Users/attaselim/Documents/Claude/Projects/Lex Council App/lex_council/apps/web/package.json"
)
LEX_APP_REPO_ROOT = Path("/Users/attaselim/Documents/Claude/Projects/Lex Council App")

LEX_BUSINESS_VAULT_LOGS = Path(
    "/Users/attaselim/Documents/Claude/Projects/Lex Council Business/The Business/vault-logs"
)

# ── Business vault-log tiering ───────────────────────────────────────────────

_MAJOR_SLUG_RE = re.compile(r"restructure", re.IGNORECASE)
_MINOR_SLUG_RE = re.compile(r"implementation|model|proposal", re.IGNORECASE)

# Frontmatter `type:` values mapped to tiers, if a log ever carries one.
_TYPE_TIER_MAP = {
    "restructure": "major",
    "implementation": "minor",
    "model": "minor",
    "proposal": "minor",
}


def _unavailable() -> dict:
    return {"version": None, "versionSource": "unavailable", "versionHistory": []}


def _fmt_version(major: int, minor: int, patch: int) -> str:
    return f"{major}.{minor}.{patch}"


# ── Branch: star-alliance (reuse build.py's derive_version) ─────────────────

def _resolve_star_alliance(repo: Path) -> dict:
    """Reuse build.py's own log-replay (derive_version) rather than
    reimplementing SemVer-from-log logic a second time. Imported lazily to
    avoid a circular import at module load (build.py imports this module)."""
    try:
        import sys
        sys.path.insert(0, str(repo))
        import build as _build  # noqa: PLC0415  (intentional lazy/circular-safe import)

        log = _build.load_log(repo)
        version, tiers = _build.derive_version(log)
        # History: the guild log itself is the append-only ledger. Give the
        # last N entries (cap ~10, matched by the dashboard tooltip cap) as
        # a running-version-esque trail. We don't replay a running version
        # per entry here (that's a heavier feature); instead surface the
        # tier breakdown as the one "current" snapshot plus raw recent
        # entries as context.
        entries = log.get("entries", [])[-10:]
        history = [
            {
                "date": e.get("date") or e.get("at") or "",
                "slug": e.get("title") or e.get("type") or "entry",
                "type": e.get("type", ""),
            }
            for e in entries
        ]
        return {
            "version": version,
            "versionSource": "guild-log",
            "versionHistory": history,
        }
    except Exception as exc:  # noqa: BLE001 — never crash the build
        print(f"[domain_version] warning: star-alliance version resolution failed: {exc}")
        return _unavailable()


# ── Branch: lex-council-app (package.json + git tags, read-only) ────────────

def _resolve_lex_council_app() -> dict:
    try:
        if not LEX_APP_PACKAGE_JSON.exists():
            return _unavailable()
        pkg = json.loads(LEX_APP_PACKAGE_JSON.read_text())
        version = pkg.get("version")
        if not version:
            return _unavailable()

        history: list[dict] = []
        try:
            major_minor = ".".join(version.split(".")[:2])
            result = subprocess.run(
                ["git", "tag", "-l", f"v{major_minor}.*"],
                cwd=str(LEX_APP_REPO_ROOT),
                capture_output=True,
                text=True,
                timeout=10,
            )
            tags = sorted(t.strip() for t in result.stdout.splitlines() if t.strip())
            if tags:
                for tag in tags[-10:]:
                    history.append({"version": tag.lstrip("v"), "date": "", "slug": tag})
            else:
                history.append({"version": version, "date": "", "slug": "current"})
        except Exception as exc:  # noqa: BLE001
            print(f"[domain_version] warning: lex-council-app git tag read failed: {exc}")
            history = [{"version": version, "date": "", "slug": "current"}]

        return {
            "version": version,
            "versionSource": "package.json",
            "versionHistory": history,
        }
    except Exception as exc:  # noqa: BLE001 — never crash the build
        print(f"[domain_version] warning: lex-council-app version resolution failed: {exc}")
        return _unavailable()


# ── Branch: lex-council-business (vault-logs derived SemVer) ────────────────

def _tier_for_log(text: str, slug: str) -> str:
    """Tier by frontmatter `type:` if present, else by filename-slug rule."""
    m = re.search(r"^type:\s*(\S+)", text, re.MULTILINE)
    if m:
        t = m.group(1).strip().strip('"').strip("'").lower()
        if t in _TYPE_TIER_MAP:
            return _TYPE_TIER_MAP[t]
    if _MAJOR_SLUG_RE.search(slug):
        return "major"
    if _MINOR_SLUG_RE.search(slug):
        return "minor"
    return "patch"


def _resolve_lex_council_business() -> dict:
    try:
        if not LEX_BUSINESS_VAULT_LOGS.exists():
            return _unavailable()

        logs = [
            p for p in LEX_BUSINESS_VAULT_LOGS.glob("*.md")
            if p.name.upper() != "INDEX.MD"
        ]
        if not logs:
            return _unavailable()

        def _date_key(p: Path) -> str:
            m = re.match(r"^(\d{4}-\d{2}-\d{2})_", p.name)
            return m.group(1) if m else ""

        # Deterministic, order-independent: sort by date-prefix then filename.
        logs.sort(key=lambda p: (_date_key(p), p.name))

        major = minor = patch = 0
        history: list[dict] = []
        for p in logs:
            try:
                text = p.read_text(errors="replace")
            except Exception as exc:  # noqa: BLE001
                print(f"[domain_version] warning: could not read vault log {p}: {exc}")
                continue
            slug = p.stem
            tier = _tier_for_log(text, slug)
            if tier == "major":
                major += 1
                minor = 0
                patch = 0
            elif tier == "minor":
                minor += 1
                patch = 0
            else:
                patch += 1
            history.append({
                "version": _fmt_version(major, minor, patch),
                "date": _date_key(p),
                "slug": slug,
                "tier": tier,
            })

        version = _fmt_version(major, minor, patch)
        return {
            "version": version,
            "versionSource": "vault-logs",
            "versionHistory": history[-10:],
        }
    except Exception as exc:  # noqa: BLE001 — never crash the build
        print(f"[domain_version] warning: lex-council-business version resolution failed: {exc}")
        return _unavailable()


# ── Public API ────────────────────────────────────────────────────────────

_RESOLVERS = {
    "lex-council-app": lambda repo: _resolve_lex_council_app(),
    "lex-council-business": lambda repo: _resolve_lex_council_business(),
    "star-alliance": _resolve_star_alliance,
}


def resolve_all(domains: list[dict], repo: Path | None = None) -> dict[str, dict]:
    """Return {domain_id: {version, versionSource, versionHistory[]}} for every
    domain dict passed in. Domains with no matching resolver, or whose
    resolver fails/finds nothing, get the 'unavailable' shape. Never raises."""
    if repo is None:
        repo = Path(__file__).resolve().parent.parent

    out: dict[str, dict] = {}
    for d in domains:
        did = d.get("id", "")
        resolver = _RESOLVERS.get(did)
        if resolver is None:
            out[did] = _unavailable()
            continue
        try:
            out[did] = resolver(repo)
        except Exception as exc:  # noqa: BLE001 — resolver-level safety net
            print(f"[domain_version] warning: resolver for '{did}' raised: {exc}")
            out[did] = _unavailable()
    return out


if __name__ == "__main__":
    _repo = Path(__file__).resolve().parent.parent
    _domains = json.loads((_repo / "data" / "domains.json").read_text()).get("domains", [])
    result = resolve_all(_domains, _repo)
    print(json.dumps(result, indent=2))
