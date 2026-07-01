#!/usr/bin/env python3
# Star Alliance — VAULT LOG NUDGE (Stop hook, NON-blocking, opt-in per vault)
# Reminds when the TARGET project (the active vault) changed code/backend files
# this session but has no vault-log entry dated today. Opt-in: only fires when
# the resolved vault profile is present and not 'off'. Never blocks (exit 0).
import sys, os, json, subprocess, pathlib

def project_dir():
    return os.environ.get('CLAUDE_PROJECT_DIR') or os.getcwd()

def repo():
    env = os.environ.get('STAR_ALLIANCE_ROOT') or os.environ.get('STAR_ALLIANCE_REPO')
    if env:
        return pathlib.Path(env).expanduser()
    return pathlib.Path(project_dir())

def resolve(r, cwd):
    try:
        out = subprocess.check_output([sys.executable, str(r / 'tools' / 'resolve_vault.py'), '--cwd', str(cwd), '--json'], text=True, stderr=subprocess.DEVNULL)
        return json.loads(out)
    except Exception:
        return None

def vault_dirty(root):
    try:
        out = subprocess.check_output(['git','-C',str(root),'status','--porcelain'], text=True, stderr=subprocess.DEVNULL)
    except Exception:
        return False
    for line in out.splitlines():
        path = line[3:].strip()
        low = path.lower()
        if low.endswith('.md'):
            continue
        if '.claude/state' in low:
            continue
        if path:
            return True
    return False

def has_today_entry(log_dir, today):
    p = pathlib.Path(log_dir)
    if not p.is_dir():
        return False
    for f in p.iterdir():
        if f.name.startswith(today):
            return True
    return False

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
    sentinel = state / 'vault-log-nudged'
    try:
        if sentinel.exists() and sentinel.read_text().strip() == anchor:
            sys.exit(0)
    except Exception:
        pass
    r = repo()
    info = resolve(r, project_dir())
    try:
        state.mkdir(parents=True, exist_ok=True)
        sentinel.write_text(anchor)
    except Exception:
        pass
    if not info or info.get('status') != 'resolved':
        sys.exit(0)
    if str(info.get('profile','')).lower() in ('off','none',''):
        sys.exit(0)
    if has_today_entry(info['log_dir'], info['today']):
        sys.exit(0)
    if not vault_dirty(info['vault_root']):
        sys.exit(0)
    print('VAULT-LOG NUDGE — the ' + str(info.get('name','active')) + ' vault changed code/backend files with no vault-log entry dated ' + str(info['today']) + '. Draft one before ending (P8). Resolve dest with python3 $STAR_ALLIANCE_ROOT/tools/resolve_vault.py --json, then write to ' + str(info['log_dir']) + '.', file=sys.stderr)
    sys.exit(0)

if __name__ == '__main__':
    main()
