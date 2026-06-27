"""version_bump.py — Release Train: bump a version, regenerate a changelog stub,
and (optionally) stamp the new version across docs.

Reads the current guild version from guild-data.json (meta.version), computes the
next version for the requested --step, writes a changelog stub built from
`git log` since the last tag/version, and — only with --stamp-docs — rewrites
`version:` stamps across docs (OFF by default; prints a diff-preview first).

CLI:
    python3 guild/version_bump.py --step patch|minor|major --changelog <file> [--stamp-docs]

Without --stamp-docs the script ONLY writes the changelog stub. --stamp-docs is a
mutating path; it prints a preview of every stamp it would change and applies them.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
GUILD_DATA = REPO_ROOT / "guild-data.json"

# Docs whose `version:` / `version X.Y.Z` stamps --stamp-docs may rewrite.
STAMP_GLOBS = ("*.md",)
_VERSION_RE = re.compile(r"\b(\d+)\.(\d+)\.(\d+)\b")


def current_version() -> str:
    if not GUILD_DATA.exists():
        raise SystemExit(f"guild-data.json not found at {GUILD_DATA}")
    data = json.loads(GUILD_DATA.read_text(encoding="utf-8"))
    v = (data.get("meta") or {}).get("version")
    if not v or not _VERSION_RE.fullmatch(str(v).strip()):
        raise SystemExit(f"meta.version missing or malformed in guild-data.json: {v!r}")
    return str(v).strip()


def bump(version: str, step: str) -> str:
    major, minor, patch = (int(x) for x in version.split("."))
    if step == "major":
        return f"{major + 1}.0.0"
    if step == "minor":
        return f"{major}.{minor + 1}.0"
    return f"{major}.{minor}.{patch + 1}"


def _git(*args: str) -> str:
    try:
        return subprocess.check_output(
            ["git", "-C", str(REPO_ROOT), *args], text=True, stderr=subprocess.STDOUT
        )
    except Exception:
        return ""


def last_tag() -> str | None:
    out = _git("describe", "--tags", "--abbrev=0").strip()
    return out or None


def commit_log_since(ref: str | None, limit: int = 50) -> list[str]:
    """Subjects since `ref` (or the most recent `limit` commits if no ref)."""
    rng = f"{ref}..HEAD" if ref else f"-n{limit}"
    out = _git("log", "--pretty=format:%s", rng)
    return [ln.strip() for ln in out.splitlines() if ln.strip()]


def write_changelog(path: Path, old: str, new: str, commits: list[str], ref: str | None) -> None:
    from datetime import date
    lines = [
        f"# {new}",
        "",
        f"_Bumped from {old} ({date.today().isoformat()})_",
        "",
        ("## Changes since last tag" if ref else "## Recent changes (no tag found)"),
        "",
    ]
    if commits:
        lines += [f"- {c}" for c in commits]
    else:
        lines.append("- (no commits found in range)")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def stamp_preview(old: str, new: str) -> list[tuple[Path, int]]:
    """Return [(doc, occurrence_count)] of files where `old` appears as a stamp."""
    hits: list[tuple[Path, int]] = []
    pat = re.compile(rf"(?m)^(\s*version:\s*){re.escape(old)}\b")
    for glob in STAMP_GLOBS:
        for p in REPO_ROOT.rglob(glob):
            if not p.is_file():
                continue
            try:
                text = p.read_text(encoding="utf-8")
            except Exception:
                continue
            n = len(pat.findall(text))
            if n:
                hits.append((p, n))
    return hits


def apply_stamps(old: str, new: str, hits: list[tuple[Path, int]]) -> int:
    pat = re.compile(rf"(?m)^(\s*version:\s*){re.escape(old)}\b")
    changed = 0
    for p, _ in hits:
        try:
            text = p.read_text(encoding="utf-8")
        except Exception:
            continue
        new_text = pat.sub(rf"\g<1>{new}", text)
        if new_text != text:
            p.write_text(new_text, encoding="utf-8")
            changed += 1
    return changed


def main() -> int:
    ap = argparse.ArgumentParser(description="Release Train — bump version + changelog stub")
    ap.add_argument("--step", required=True, choices=("patch", "minor", "major"),
                    help="Which part of the version to bump")
    # --out is the workflow-runner's file-rail alias for --changelog
    # (resolve_io_args supplies --out from the step's `produces`).
    ap.add_argument("--changelog", "--out", dest="changelog", required=True,
                    help="Path to write the changelog stub")
    ap.add_argument("--stamp-docs", action="store_true",
                    help="Rewrite version: stamps across docs (OFF by default; mutating)")
    # Tolerate the runner's --in rail (this step takes no input file).
    ap.add_argument("--in", dest="_in", default=None, help=argparse.SUPPRESS)
    args = ap.parse_args()

    try:
        old = current_version()
    except SystemExit as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    new = bump(old, args.step)
    print(f"version_bump: {old} -> {new} ({args.step})")

    ref = last_tag()
    if ref:
        print(f"  changelog range: {ref}..HEAD")
    else:
        print("  no git tag found — using the most recent commits for the stub")
    commits = commit_log_since(ref)

    chg_path = Path(args.changelog)
    if not chg_path.is_absolute():
        chg_path = (REPO_ROOT / chg_path).resolve()
    try:
        chg_path.parent.mkdir(parents=True, exist_ok=True)
        write_changelog(chg_path, old, new, commits, ref)
    except Exception as exc:
        print(f"ERROR writing changelog: {exc}", file=sys.stderr)
        return 1
    print(f"  wrote changelog stub: {chg_path} ({len(commits)} commit(s))")

    # --stamp-docs is mutating: always print a preview first, then apply.
    hits = stamp_preview(old, new)
    if hits:
        print(f"\n  version stamps for {old} found in {len(hits)} doc(s):")
        for p, n in hits:
            try:
                rel = p.relative_to(REPO_ROOT)
            except ValueError:
                rel = p
            print(f"    {rel}  ({n} occurrence(s)) -> {new}")
    else:
        print(f"\n  no `version: {old}` stamps found in docs.")

    if args.stamp_docs:
        changed = apply_stamps(old, new, hits)
        print(f"  --stamp-docs: rewrote stamps in {changed} doc(s).")
    else:
        print("  (--stamp-docs OFF — preview only, no docs rewritten.)")

    print("version_bump: done. NOTE — does not commit, tag, or rebuild the dashboard.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
