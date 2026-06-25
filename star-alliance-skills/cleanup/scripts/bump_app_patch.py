#!/usr/bin/env python3
"""
bump_app_patch.py — lightweight app PATCH-version bump for the /cleanup skill.

Every cleanup session (any mode, big or small) that APPLIES a change bumps the
app version's last segment by 1 — e.g. 1.7.26 → 1.7.27. This is the small,
always-on counter the user asked for; it is NOT the heavy `release` ceremony
(changelog + doc-stamps + git block) — that still lives in `release` mode and
performs its own (possibly minor/major) bump, so `release` MUST NOT also call
this script.

Keeps the two version literals in sync:
  • apps/web/config/app.config.ts  → APP_CONFIG.version   (canonical)
  • apps/web/package.json          → "version"            (mirror)

Subcommands:
  show          Print the current version from both files (+ drift warning).
  bump          Increment the PATCH segment by 1 in BOTH files. Prints old→new.
  bump --dry    Compute + print the next version without writing.

Exit codes: 0 ok / 2 version literal not found / 3 the two files disagree
(refuses to bump on drift — run `release` to reconcile first).

Call EXACTLY ONCE per cleanup session, at closeout, after every mode's edits
have landed and tsc/lint are green. Skip entirely when the session applied no
changes (a pure detect-only / dry-run sweep does not bump).
"""

import re
import sys
from pathlib import Path

APP_CONFIG_REL = Path('apps') / 'web' / 'config' / 'app.config.ts'
PACKAGE_REL = Path('apps') / 'web' / 'package.json'

CONFIG_RE = re.compile(r"(version:\s*')(\d+\.\d+\.\d+)(')")
PKG_RE = re.compile(r'("version":\s*")(\d+\.\d+\.\d+)(")')


def default_root() -> Path:
    # Walk up from this file / cwd to the dir containing apps/web/config/app.config.ts
    # (the lex_council repo root). Portable across machines.
    starts = [Path(__file__).resolve().parent, Path.cwd().resolve()]
    seen = set()
    for start in starts:
        for parent in [start, *start.parents]:
            if parent in seen:
                continue
            seen.add(parent)
            if (parent / APP_CONFIG_REL).is_file():
                return parent
            cand = parent / 'lex_council'
            if (cand / APP_CONFIG_REL).is_file():
                return cand
    return Path.home() / 'Documents' / 'Claude' / 'Projects' / 'Lex Council App' / 'lex_council'


def read_version(path: Path, rx: re.Pattern) -> str | None:
    m = rx.search(path.read_text())
    return m.group(2) if m else None


def bump_patch(v: str) -> str:
    major, minor, patch = v.split('.')
    return f"{major}.{minor}.{int(patch) + 1}"


def main() -> int:
    args = sys.argv[1:]
    cmd = args[0] if args else 'bump'
    dry = '--dry' in args or '--dry-run' in args

    root = default_root()
    config_path = root / APP_CONFIG_REL
    pkg_path = root / PACKAGE_REL

    if not config_path.is_file():
        print(f"app.config.ts not found under {root}", file=sys.stderr)
        return 2

    cfg_v = read_version(config_path, CONFIG_RE)
    pkg_v = read_version(pkg_path, PKG_RE) if pkg_path.is_file() else None

    if cfg_v is None:
        print("could not find APP_CONFIG.version literal in app.config.ts", file=sys.stderr)
        return 2

    if cmd == 'show':
        print(f"app.config.ts : {cfg_v}")
        print(f"package.json  : {pkg_v if pkg_v is not None else '(not found)'}")
        if pkg_v is not None and pkg_v != cfg_v:
            print(f"⚠ drift: app.config.ts={cfg_v} package.json={pkg_v}", file=sys.stderr)
        return 0

    if cmd != 'bump':
        print(f"unknown command '{cmd}' (use: show | bump [--dry])", file=sys.stderr)
        return 2

    # refuse to bump if the two literals already disagree — reconcile via `release`
    if pkg_v is not None and pkg_v != cfg_v:
        print(f"version drift — app.config.ts={cfg_v} package.json={pkg_v}; "
              f"reconcile via `/cleanup release` before patch-bumping", file=sys.stderr)
        return 3

    new_v = bump_patch(cfg_v)

    if dry:
        print(f"{cfg_v} → {new_v} (dry-run; no files written)")
        return 0

    # write canonical
    config_path.write_text(CONFIG_RE.sub(rf"\g<1>{new_v}\g<3>", config_path.read_text(), count=1))
    touched = [str(APP_CONFIG_REL)]
    # write mirror
    if pkg_path.is_file() and pkg_v is not None:
        pkg_path.write_text(PKG_RE.sub(rf'\g<1>{new_v}\g<3>', pkg_path.read_text(), count=1))
        touched.append(str(PACKAGE_REL))

    print(f"app version bumped {cfg_v} → {new_v}")
    print("updated: " + ", ".join(touched))
    return 0


if __name__ == '__main__':
    sys.exit(main())
