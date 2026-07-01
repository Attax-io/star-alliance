#!/usr/bin/env python3
'''guild_log.py — portable entry point for guild logging from ANY current directory.

The guild log always lives in the star-alliance repo, no matter which project
the guild is deployed into. This wrapper self-locates that repo and runs the
existing logging scripts by absolute path, so the guild-log skill never depends
on the current working directory.

Subcommands:
    build   [--dry-run]            run tools/build_guild_log.py (Tier 1, git-derived)
    event   [--type ... ...]       run tools/log_event.py (Tier 2, manual entry)
    rebuild [--check]              run build.py (regenerate guild-data)
    status                         print the resolved repo and log path

Usage:
    python3 guild_log.py build
    python3 guild_log.py event --type chore --title '...' --who the-quartermaster
    python3 guild_log.py rebuild
'''
import os, subprocess, sys
from pathlib import Path

def repo():
    env = os.environ.get('STAR_ALLIANCE_ROOT') or os.environ.get('STAR_ALLIANCE_REPO')
    if env:
        return Path(env).expanduser()
    here = Path(__file__).resolve()
    for anc in here.parents:
        if (anc / 'VERSIONS.md').exists() and (anc / '.git').exists():
            return anc
    return here.parent.parent

def main():
    r = repo()
    if len(sys.argv) < 2:
        print('usage: guild_log.py {build|event|rebuild|status} [args...]')
        return 2
    cmd, rest = sys.argv[1], sys.argv[2:]
    py = sys.executable
    if cmd == 'build':
        return subprocess.call([py, str(r / 'tools' / 'build_guild_log.py'), *rest])
    if cmd == 'event':
        return subprocess.call([py, str(r / 'tools' / 'log_event.py'), *rest])
    if cmd == 'rebuild':
        return subprocess.call([py, str(r / 'build.py'), *rest])
    if cmd == 'status':
        print('repo=' + str(r))
        print('guild_log=' + str(r / 'data' / 'guild-log.json'))
        return 0
    print('unknown subcommand: ' + cmd)
    return 2

if __name__ == '__main__':
    sys.exit(main())
