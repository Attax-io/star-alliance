#!/usr/bin/env python3
# Star Alliance — GUILD LOG NUDGE (Stop hook, NON-blocking, fails open)
# Reminds when star-alliance guild surfaces changed this session but no covering
# guild-log entry is evident. Never blocks (always exit 0).
import sys, os, json, subprocess, pathlib

def project_dir():
    return os.environ.get('CLAUDE_PROJECT_DIR') or os.getcwd()

def repo():
    env = os.environ.get('STAR_ALLIANCE_ROOT') or os.environ.get('STAR_ALLIANCE_REPO')
    if env:
        return pathlib.Path(env).expanduser()
    return pathlib.Path(project_dir())

GUILD_HINTS = ('index.html','app.css','app.js','dashboard','skills-meta.json','members-meta.json','guild-data.js','workflows.json','star-alliance-members/','star-alliance-skills/')

def changed(r):
    try:
        out = subprocess.check_output(['git','-C',str(r),'status','--porcelain'], text=True, stderr=subprocess.DEVNULL)
    except Exception:
        return []
    files = []
    for line in out.splitlines():
        path = line[3:].strip()
        if path:
            files.append(path)
    return files

def main():
    try:
        json.load(sys.stdin)
    except Exception:
        sys.exit(0)
    state = pathlib.Path(project_dir()) / '.claude' / 'state'
    ts = state / 'turn-start'
    if not ts.exists():
        sys.exit(0)
    anchor = str(ts.stat().st_mtime)
    sentinel = state / 'guild-log-nudged'
    try:
        if sentinel.exists() and sentinel.read_text().strip() == anchor:
            sys.exit(0)
    except Exception:
        pass
    r = repo()
    files = changed(r)
    hits = [f for f in files if any(h in f for h in GUILD_HINTS)]
    logged = any('guild-log.json' in f or 'guild-data.json' in f for f in files)
    try:
        state.mkdir(parents=True, exist_ok=True)
        sentinel.write_text(anchor)
    except Exception:
        pass
    if hits and not logged:
        shown = ', '.join(sorted(set(hits))[:6])
        print('GUILD-LOG NUDGE — guild surfaces changed without a covering log entry: ' + shown + '. Before ending, run: python3 $STAR_ALLIANCE_ROOT/tools/guild_log.py build  (then log non-git-visible changes with the same wrapper: event --type dashboard or structure or chore).', file=sys.stderr)
    sys.exit(0)

if __name__ == '__main__':
    main()
