#!/usr/bin/env python3
'''resolve_vault.py — locate the vault-log directory of the TARGET project.

Detection order (first hit wins):
  1. VAULT_LOG_DIR env override            source=env
  2. nearest .claude/vault.json walking up source=config
  3. convention: nearest docs/vault-logs   source=convention
  4. nothing found                          status=not_found + scaffold proposal
No fallback to any specific project.
'''
from __future__ import annotations
import argparse, json, os, sys
from datetime import date
from pathlib import Path

DEFAULTS = {'filename_format': '{date}_{slug}', 'date_format': '%Y-%m-%d', 'profile': 'full'}

def _project_dir_for(config_path):
    return config_path.parent.parent

def _resolve_rel(root, value):
    p = Path(value).expanduser()
    return p if p.is_absolute() else (root / p)

def find_config(start):
    for anc in [start, *start.parents]:
        cand = anc / '.claude' / 'vault.json'
        if cand.is_file():
            return cand
    return None

def find_convention(start):
    for anc in [start, *start.parents]:
        cand = anc / 'docs' / 'vault-logs'
        if cand.is_dir():
            return anc
    return None

def _git_root(start):
    for anc in [start, *start.parents]:
        if (anc / '.git').exists():
            return anc
    return None

def _finalize(d):
    d.setdefault('footer_docs', [])
    d.setdefault('notes', '')
    d['today'] = date.today().strftime(d.get('date_format', DEFAULTS['date_format']))
    return d

def resolve(cwd):
    cwd = cwd.resolve()
    env_dir = os.environ.get('VAULT_LOG_DIR')
    if env_dir:
        log_dir = Path(env_dir).expanduser().resolve()
        root = Path(os.environ.get('VAULT_ROOT', str(log_dir.parent.parent))).expanduser().resolve()
        return _finalize({'status': 'resolved', 'source': 'env', 'name': root.name,
                          'vault_root': str(root), 'log_dir': str(log_dir),
                          'index_path': str(log_dir / 'INDEX.md'), **DEFAULTS})
    cfg_path = find_config(cwd)
    if cfg_path:
        try:
            cfg = json.loads(cfg_path.read_text())
        except Exception as e:
            return {'status': 'error', 'source': 'config', 'error': 'vault.json parse failed: ' + str(e), 'config_path': str(cfg_path)}
        proj = _project_dir_for(cfg_path)
        root = _resolve_rel(proj, cfg.get('vault_root', '.')).resolve()
        log_dir = _resolve_rel(proj, cfg['log_dir']).resolve()
        index_path = _resolve_rel(proj, cfg['index_path']).resolve() if cfg.get('index_path') else log_dir / 'INDEX.md'
        footer = [str(_resolve_rel(proj, f)) for f in cfg.get('footer_docs', [])]
        return _finalize({'status': 'resolved', 'source': 'config', 'name': cfg.get('name', root.name),
                          'vault_root': str(root), 'log_dir': str(log_dir), 'index_path': str(index_path),
                          'filename_format': cfg.get('filename_format', DEFAULTS['filename_format']),
                          'date_format': cfg.get('date_format', DEFAULTS['date_format']),
                          'profile': cfg.get('profile', DEFAULTS['profile']), 'footer_docs': footer,
                          'notes': cfg.get('notes', ''), 'config_path': str(cfg_path)})
    conv_root = find_convention(cwd)
    if conv_root:
        log_dir = conv_root / 'docs' / 'vault-logs'
        index = log_dir / 'INDEX.md'
        return _finalize({'status': 'resolved', 'source': 'convention', 'name': conv_root.name,
                          'vault_root': str(conv_root), 'log_dir': str(log_dir), 'index_path': str(index), **DEFAULTS})
    root = _git_root(cwd) or cwd
    proposed_log = root / 'docs' / 'vault-logs'
    return {'status': 'not_found', 'source': None, 'name': root.name, 'vault_root': str(root),
            'scaffold': {'config_path': str(root / '.claude' / 'vault.json'), 'log_dir': str(proposed_log),
                         'index_path': str(proposed_log / 'INDEX.md'), **DEFAULTS},
            'hint': 'No vault registered. Re-run with --scaffold after approval to create .claude/vault.json and docs/vault-logs.'}

def do_scaffold(cwd):
    info = resolve(cwd)
    if info['status'] == 'resolved':
        info['scaffold_result'] = 'already_configured'; return info
    if info['status'] != 'not_found':
        return info
    sc = info['scaffold']
    log_dir = Path(sc['log_dir']); cfg_path = Path(sc['config_path']); root = Path(info['vault_root'])
    log_dir.mkdir(parents=True, exist_ok=True)
    index = Path(sc['index_path'])
    if not index.exists():
        index.write_text('# Vault Log Index — ' + root.name + chr(10) + chr(10) + '| Entry | Date | Summary |' + chr(10) + '|---|---|---|' + chr(10))
    cfg = {'name': root.name, 'vault_root': '.', 'log_dir': os.path.relpath(log_dir, root),
           'index_path': os.path.relpath(index, root), 'filename_format': DEFAULTS['filename_format'],
           'date_format': DEFAULTS['date_format'], 'profile': DEFAULTS['profile'], 'footer_docs': [],
           'notes': 'Auto-scaffolded by resolve_vault.py --scaffold'}
    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    cfg_path.write_text(json.dumps(cfg, indent=2) + chr(10))
    out = resolve(cwd); out['scaffold_result'] = 'created'; return out

def _human(info):
    if info['status'] == 'not_found':
        sc = info['scaffold']
        return 'WARN No vault registered for ' + info['name'] + ' (' + info['vault_root'] + ')' + chr(10) + '  Proposed: ' + sc['log_dir'] + chr(10) + '  ' + info['hint']
    if info['status'] == 'error':
        return 'ERROR ' + info['error'] + ' (' + str(info.get('config_path')) + ')'
    return ('OK Vault: ' + info['name'] + '  (source=' + info['source'] + ')' + chr(10) +
            '  log_dir:  ' + info['log_dir'] + chr(10) + '  index:    ' + info['index_path'] + chr(10) +
            '  filename: ' + info['filename_format'] + '  (today=' + info['today'] + ')' + chr(10) +
            '  profile:  ' + info['profile'])

def main():
    ap = argparse.ArgumentParser(description='Resolve the active project vault-log directory.')
    ap.add_argument('--cwd', default=os.getcwd())
    ap.add_argument('--json', action='store_true')
    ap.add_argument('--scaffold', action='store_true')
    args = ap.parse_args()
    cwd = Path(args.cwd)
    info = do_scaffold(cwd) if args.scaffold else resolve(cwd)
    print(json.dumps(info, indent=2) if args.json else _human(info))
    return 0 if info['status'] == 'resolved' else 1

if __name__ == '__main__':
    sys.exit(main())