#!/usr/bin/env python3
'''resolve_output.py — locate the correct output folder for a skill artifact.

Detection order (first hit wins):
  1. OUTPUT_DIR env override                     source=env
  2. nearest .claude/output.json walking up       source=config  (per-kind override)
  3. OKF layout convention (okf_audit.LAYOUT_RULES)  source=convention
  4. unclassified — fall back to a scratch dir + propose a scaffold entry  source=fallback
No hardcoded per-skill folder unless the caller supplies one via config.
'''
from __future__ import annotations
import argparse, json, os, sys
from pathlib import Path

# Make the okf_audit module importable without turning it into a package.
_REPO_ROOT = None
for _anc in [Path(__file__).resolve().parent, *Path(__file__).resolve().parents]:
    if (_anc / '.git').exists() and (_anc / 'VERSIONS.md').exists():
        _REPO_ROOT = _anc
        break
if _REPO_ROOT is None:
    raise SystemExit('resolve_output.py: could not locate repo root (need .git + VERSIONS.md).')
_okf_scripts = _REPO_ROOT / 'star-alliance-skills' / 'okf' / 'scripts'
if str(_okf_scripts) not in sys.path:
    sys.path.insert(0, str(_okf_scripts))
from okf_audit import LAYOUT_RULES  # noqa: E402

def _first_target(pattern_substr: str) -> str:
    for pat, target, _safety in LAYOUT_RULES:
        if pattern_substr in pat:
            return target
    raise KeyError(pattern_substr)

OUTPUT_KIND_MAP = {
    'report': _first_target('STRATEGIST'),
    'diagnostic': _first_target('STRATEGIST'),
    'generated-script': _first_target('gen-'),
    'data': _first_target(r'\.json'),
    'state': '.claude/state/',
    'log': _first_target(r'\.json'),
}

def _project_dir_for(config_path):
    return config_path.parent.parent

def _resolve_rel(root, value):
    p = Path(value).expanduser()
    return p if p.is_absolute() else (root / p)

def find_config(start):
    for anc in [start, *start.parents]:
        cand = anc / '.claude' / 'output.json'
        if cand.is_file():
            return cand
    return None

def _git_root(start):
    for anc in [start, *start.parents]:
        if (anc / '.git').exists() and (anc / 'VERSIONS.md').exists():
            return anc
    return None

def find_convention_root(skill, kind, cwd):
    rel = OUTPUT_KIND_MAP.get(kind)
    if not rel:
        return None
    for anc in [cwd, *cwd.parents]:
        cand = anc / rel.rstrip('/')
        if cand.is_dir():
            return anc
    return _git_root(cwd)

def resolve(skill, kind, cwd=None):
    cwd = (cwd or Path.cwd()).resolve()
    env_dir = os.environ.get('OUTPUT_DIR')
    if env_dir:
        folder = Path(env_dir).expanduser().resolve()
        return {'status': 'resolved', 'source': 'env',
                'folder': str(folder), 'skill': skill, 'kind': kind}
    cfg_path = find_config(cwd)
    if cfg_path:
        try:
            cfg = json.loads(cfg_path.read_text())
        except Exception as e:
            return {'status': 'error', 'source': 'config',
                    'folder': None, 'skill': skill, 'kind': kind,
                    'error': 'output.json parse failed: ' + str(e),
                    'config_path': str(cfg_path)}
        proj = _project_dir_for(cfg_path)
        kinds = (cfg.get('kinds') or {})
        per_kind = (cfg.get('default_kind') and kind not in kinds and cfg['default_kind']) or None
        chosen_kind = kind if kind in kinds else (per_kind if per_kind and per_kind in kinds else None)
        if chosen_kind is not None:
            folder = _resolve_rel(proj, kinds[chosen_kind]).resolve()
            return {'status': 'resolved', 'source': 'config',
                    'folder': str(folder), 'skill': skill, 'kind': kind,
                    'config_path': str(cfg_path), 'matched_kind': chosen_kind}
        folder = _resolve_rel(proj, cfg.get('default_folder', '.claude/output/')).resolve()
        return {'status': 'resolved', 'source': 'config',
                'folder': str(folder), 'skill': skill, 'kind': kind,
                'config_path': str(cfg_path), 'matched_kind': '<default_folder>'}
    if kind in OUTPUT_KIND_MAP:
        rel = OUTPUT_KIND_MAP[kind]
        root = find_convention_root(skill, kind, cwd) or _git_root(cwd) or cwd
        folder = (root / rel.rstrip('/')).resolve()
        return {'status': 'resolved', 'source': 'convention',
                'folder': str(folder), 'skill': skill, 'kind': kind,
                'rel_folder': rel}
    root = _git_root(cwd) or cwd
    proposed = '.claude/output/' + kind + '/'
    return {'status': 'not_found', 'source': 'fallback',
            'folder': str((root / proposed).resolve()), 'skill': skill, 'kind': kind,
            'scaffold': {'config_path': str(root / '.claude' / 'output.json'),
                         'kind_entry': proposed,
                         'hint': "Add to .claude/output.json 'kinds' map, then re-run."},
            'hint': 'No convention for kind=' + kind + '. Re-run with --scaffold after approval to register it in .claude/output.json.'}

def do_scaffold(skill, kind, cwd):
    info = resolve(skill, kind, cwd)
    if info['status'] == 'resolved':
        info['scaffold_result'] = 'already_configured'; return info
    if info['status'] != 'not_found':
        return info
    sc = info['scaffold']
    cfg_path = Path(sc['config_path']); root = cfg_path.parent.parent
    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    if cfg_path.is_file():
        cfg = json.loads(cfg_path.read_text())
        if 'kinds' not in cfg or not isinstance(cfg['kinds'], dict):
            cfg['kinds'] = {}
        cfg['kinds'][info['kind']] = sc['kind_entry']
        cfg.setdefault('notes', '')
        if 'Auto-scaffolded entries' not in cfg['notes']:
            cfg['notes'] = (cfg['notes'] + chr(10) + 'Auto-scaffolded by resolve_output.py --scaffold').strip()
        cfg_path.write_text(json.dumps(cfg, indent=2) + chr(10))
        info['scaffold_result'] = 'merged'
    else:
        cfg = {'kinds': {info['kind']: sc['kind_entry']},
               'default_kind': info['kind'],
               'notes': 'Auto-scaffolded by resolve_output.py --scaffold'}
        cfg_path.write_text(json.dumps(cfg, indent=2) + chr(10))
        info['scaffold_result'] = 'created'
    out = resolve(skill, kind, cwd); out['scaffold_result'] = info['scaffold_result']; return out

def _human(info):
    if info['status'] == 'not_found':
        sc = info['scaffold']
        return ('WARN No convention for kind=' + info['kind'] + '  skill=' + info['skill'] + chr(10) +
                '  Fallback: ' + info['folder'] + chr(10) +
                '  Proposed config entry: ' + sc['config_path'] + '  kinds.' + info['kind'] + ' = "' + sc['kind_entry'] + '"' + chr(10) +
                '  ' + info['hint'])
    if info['status'] == 'error':
        return 'ERROR ' + info['error'] + ' (' + str(info.get('config_path')) + ')'
    return ('OK Output folder  (source=' + info['source'] + ')' + chr(10) +
            '  skill:   ' + info['skill'] + chr(10) +
            '  kind:    ' + info['kind'] + chr(10) +
            '  folder:  ' + info['folder'] + chr(10) +
            ('  rel:     ' + info['rel_folder'] + chr(10) if info['source'] == 'convention' and info.get('rel_folder') else '') +
            ('  matched_kind: ' + info['matched_kind'] + chr(10) if info.get('matched_kind') else '')).rstrip(chr(10))

def main():
    ap = argparse.ArgumentParser(description='Resolve the output folder for a skill artifact.')
    ap.add_argument('skill')
    ap.add_argument('kind')
    ap.add_argument('--cwd', default=os.getcwd())
    ap.add_argument('--json', action='store_true')
    ap.add_argument('--scaffold', action='store_true')
    args = ap.parse_args()
    cwd = Path(args.cwd)
    info = do_scaffold(args.skill, args.kind, cwd) if args.scaffold else resolve(args.skill, args.kind, cwd)
    print(json.dumps(info, indent=2) if args.json else _human(info))
    return 0 if info['status'] == 'resolved' else 1

if __name__ == '__main__':
    sys.exit(main())
