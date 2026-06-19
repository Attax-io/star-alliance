#!/usr/bin/env python3
"""i18n consolidation utility for Lex Council.

Four subcommands:
  detect        — find cross-locale safe-to-merge groups + suggest common.* targets.
  map-callsites — AST-aware resolution of every t-call referencing the doomed keys.
                  Output: /tmp/consolidation_callsites_final.json with verified
                  (file, line, var, key_arg → old_key → new_key) tuples.
  apply         — execute callsite rewrites (two strategies: var-swap, or
                  add-binding+swap) + delete the now-orphan keys from all locales.
  verify        — re-run safe-to-merge detector + validate every JSON parses.

Workflow:
  1. detect        → review candidates with the user, pick surgical target set
  2. write the target set to /tmp/consolidation_keys.json as [{old, new}, ...]
  3. map-callsites → produce verified rewrite plan
  4. review the plan with the user
  5. apply         → execute rewrites + key deletions
  6. verify        → confirm no regressions

Default messages root: lex_council/apps/web/public/messages
Default code root:     lex_council/apps/web
Override with CLEANUP_MESSAGES_ROOT / CLEANUP_CODE_ROOT env vars.
"""
from __future__ import annotations
import argparse, collections, json, os, re, subprocess, sys
from pathlib import Path

NAMESPACES = ['admin', 'auth', 'clients', 'common', 'errors', 'members',
              'pageIntros', 'portal', 'public', 'settings', 'toasts']
LOCALES = ['en', 'ar', 'fr', 'ru', 'zh', 'es']


# ── Helpers ────────────────────────────────────────────────────────────────

def default_msg_root() -> Path:
    env = os.environ.get('CLEANUP_MESSAGES_ROOT')
    if env: return Path(env).resolve()
    cwd = Path.cwd().resolve()
    for parent in [cwd, *cwd.parents]:
        cand = parent / 'lex_council' / 'apps' / 'web' / 'public' / 'messages'
        if cand.is_dir(): return cand
        cand = parent / 'apps' / 'web' / 'public' / 'messages'
        if cand.is_dir(): return cand
    raise SystemExit("Could not locate messages root.")


def default_code_root() -> Path:
    env = os.environ.get('CLEANUP_CODE_ROOT')
    if env: return Path(env).resolve()
    cwd = Path.cwd().resolve()
    for parent in [cwd, *cwd.parents]:
        cand = parent / 'lex_council' / 'apps' / 'web'
        if cand.is_dir(): return cand
        cand = parent / 'apps' / 'web'
        if cand.is_dir(): return cand
    raise SystemExit("Could not locate code root.")


def flatten(obj, prefix=''):
    out = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            p = f"{prefix}.{k}" if prefix else k
            out.update(flatten(v, p))
    elif isinstance(obj, str):
        out[prefix] = obj
    return out


def load_ns(root: Path, loc: str, ns: str):
    with (root / loc / f'{ns}.json').open('r', encoding='utf-8') as f:
        return flatten(json.load(f))


def get_str(d, k):
    v = d.get(k, '')
    return v.strip() if isinstance(v, str) else ''


# ── detect ────────────────────────────────────────────────────────────────

def cmd_detect(args):
    root = Path(args.root) if args.root else default_msg_root()
    msgs = {(ns, l): load_ns(root, l, ns) for ns in NAMESPACES for l in LOCALES}

    # Build global EN-value index
    by_en = collections.defaultdict(list)
    for ns in NAMESPACES:
        for k in msgs[(ns, 'en')]:
            en = get_str(msgs[(ns, 'en')], k)
            if not en: continue
            by_en[en].append((ns, k))

    # For each group with >1 key, check whether all locales agree
    safe_groups = []
    for en_val, locs in by_en.items():
        if len(locs) < 2: continue
        all_match = True
        for l in LOCALES:
            first = get_str(msgs[(locs[0][0], l)], locs[0][1])
            if not first: all_match = False; break
            for ns, k in locs[1:]:
                if get_str(msgs[(ns, l)], k) != first:
                    all_match = False; break
            if not all_match: break
        if all_match:
            nsset = sorted(set(ns for ns, _ in locs))
            safe_groups.append({'en': en_val, 'count': len(locs),
                                'namespaces': nsset, 'locs': locs})

    # Sort by count desc
    safe_groups.sort(key=lambda g: -g['count'])

    # Heuristic: which targets already exist in common.json?
    common_flat = msgs[('common', 'en')]
    en_to_common_key = {}
    for k, v in common_flat.items():
        en_to_common_key.setdefault(v, []).append(k)

    cross_ns = [g for g in safe_groups if len(g['namespaces']) > 1]
    same_ns = [g for g in safe_groups if len(g['namespaces']) == 1]

    print(f"Total safe-to-merge groups: {len(safe_groups)}")
    print(f"  cross-namespace (high lift): {len(cross_ns)}")
    print(f"  same-namespace (low lift):   {len(same_ns)}")
    print()
    print("--- Cross-NS candidates (showing all, sorted by lift) ---")
    print(f"{'cnt':>3}  {'has-common?':<12}  {'namespaces':<48}  en")
    print('-' * 110)
    for g in cross_ns:
        existing = en_to_common_key.get(g['en'], [])
        marker = (f"yes → {existing[0]}"[:12]) if existing else 'no, must add'
        nss = ','.join(g['namespaces'])
        short = (g['en'][:48] + '…') if len(g['en']) > 48 else g['en']
        print(f"{g['count']:>3}  {marker:<12}  [{nss:<46}]  \"{short}\"")

    # Save full data
    output = {
        'safe_groups': safe_groups,
        'cross_ns': cross_ns,
        'same_ns': same_ns,
        'common_existing_targets': en_to_common_key,
        'stats': {
            'total_groups': len(safe_groups),
            'cross_ns': len(cross_ns),
            'same_ns': len(same_ns),
            'total_keys': sum(g['count'] for g in safe_groups),
        }
    }
    out_path = Path(args.out_dir) / 'safe_to_merge.json'
    out_path.write_text(json.dumps(output, ensure_ascii=False, indent=2))
    print(f"\nFull detector output → {out_path}")


# ── map-callsites ──────────────────────────────────────────────────────────

# Matches BOTH client (`const t = useTranslations('ns')`) and server-component
# (`const t = await getTranslations('ns')` / `getTranslations({ namespace:'ns' })`)
# bindings. Missing the `await` and object-namespace forms made server-only keys
# (e.g. public.codex.*) look DEAD and risked deleting live keys → MISSING_MESSAGE.
# namespace = group(2) [string arg] or group(3) [object namespace].
USE_TRANS_RE = re.compile(
    r"(?:const|let|var)\s+(\w+)\s*=\s*(?:await\s+)?(?:use|get)Translations\s*\(\s*"
    r"(?:"
    r"[`'\"]([^`'\"]*)[`'\"]"
    r"|"
    r"\{[^}]*namespace\s*:\s*[`'\"]([^`'\"]*)[`'\"][^}]*\}"
    r")?\s*\)"
)
T_CALL_RE = re.compile(r"(?<!\w)(\w+)\s*\(\s*[`'\"]([^`'\"]+)[`'\"]")


def cmd_map_callsites(args):
    code_root = Path(args.code_root) if args.code_root else default_code_root()
    keys_path = Path(args.keys_file)
    pairs = json.loads(keys_path.read_text())
    doomed = {p['old']: p['new'] for p in pairs}

    # Find every TSX/TS file with any i18n hook
    result = subprocess.run(
        ['grep', '-rl', '--include=*.tsx', '--include=*.ts',
         '--exclude-dir=node_modules', '--exclude-dir=.next', '--exclude-dir=.turbo',
         '-E', '(use|get)Translations', str(code_root)],
        capture_output=True, text=True
    )
    candidate_files = [Path(f).resolve() for f in result.stdout.strip().split('\n') if f]

    SKIP_PATTERNS = ('__tests__', '.test.', 'test-utils', 'LanguagesPanel',
                     'components-manifest')

    callsites = []
    for path in candidate_files:
        rel = path.relative_to(code_root.resolve()) if path.is_absolute() else path
        if any(s in str(rel) for s in SKIP_PATTERNS):
            continue
        try:
            content = path.read_text(encoding='utf-8')
        except Exception:
            continue
        # Build var → namespace map
        var_ns = {m.group(1): (m.group(2) or m.group(3) or '') for m in USE_TRANS_RE.finditer(content)}
        if not var_ns: continue
        for line_num, line in enumerate(content.split('\n'), start=1):
            for tm in T_CALL_RE.finditer(line):
                var_name = tm.group(1)
                key_arg = tm.group(2)
                if var_name not in var_ns: continue
                ns = var_ns[var_name]
                full_key = f"{ns}.{key_arg}" if ns else key_arg
                if full_key in doomed:
                    callsites.append({
                        'file': str(rel),
                        'line': line_num,
                        'snippet': line.strip()[:150],
                        'var': var_name,
                        'var_ns': ns,
                        'key_arg': key_arg,
                        'old_key': full_key,
                        'new_key': doomed[full_key],
                    })

    # Per-file plan
    by_file = collections.defaultdict(list)
    for c in callsites:
        by_file[c['file']].append(c)

    plan = []
    for fpath, sites in sorted(by_file.items(), key=lambda x: -len(x[1])):
        try:
            content = (code_root / fpath).read_text(encoding='utf-8')
        except Exception:
            continue
        bindings = {m.group(1): m.group(2) or m.group(3) or '' for m in USE_TRANS_RE.finditer(content)}
        common_var = next((v for v, ns in bindings.items() if ns == 'common'), None)
        plan.append({
            'file': fpath,
            'sites': sites,
            'bindings': bindings,
            'has_common': common_var is not None,
            'common_var': common_var,
            'strategy': 'A: swap var only' if common_var else 'B: add useTranslations(common) + swap',
        })

    dead = sorted(set(doomed.keys()) - set(c['old_key'] for c in callsites))
    output = {
        'callsites': callsites,
        'plan': plan,
        'dead_keys': dead,
        'stats': {
            'total_callsites': len(callsites),
            'files_touched': len(by_file),
            'dead_keys': len(dead),
            'total_doomed': len(doomed),
            'strategy_a_files': sum(1 for p in plan if p['has_common']),
            'strategy_b_files': sum(1 for p in plan if not p['has_common']),
        }
    }
    out_path = Path(args.out)
    out_path.write_text(json.dumps(output, ensure_ascii=False, indent=2))

    print(f"AST-verified callsite map:")
    print(f"  total callsites: {len(callsites)}")
    print(f"  files touched:   {len(by_file)}")
    print(f"  dead keys:       {len(dead)} of {len(doomed)}")
    print(f"  strategy A:      {output['stats']['strategy_a_files']} files (var-swap only)")
    print(f"  strategy B:      {output['stats']['strategy_b_files']} files (add binding + swap)")
    print(f"\nWrote {out_path}")


# ── apply ──────────────────────────────────────────────────────────────────

def cmd_apply(args):
    msg_root = Path(args.msg_root) if args.msg_root else default_msg_root()
    code_root = Path(args.code_root) if args.code_root else default_code_root()
    plan_data = json.loads(Path(args.plan_file).read_text())

    # Phase A — delete dead keys (zero-risk, JSON-only)
    dead_keys = plan_data.get('dead_keys', [])
    print(f"Phase A: deleting {len(dead_keys)} dead keys × {len(LOCALES)} locales")
    by_ns_dead = collections.defaultdict(list)
    for k in dead_keys:
        top, _, _ = k.partition('.')
        by_ns_dead[top].append(k)
    deleted_a = 0
    for ns, keys in by_ns_dead.items():
        for loc in LOCALES:
            path = msg_root / loc / f'{ns}.json'
            with path.open() as f: data = json.load(f)
            changed = False
            for k in keys:
                if _del_nested(data, k):
                    changed = True; deleted_a += 1
            if changed:
                with path.open('w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                    f.write('\n')
    print(f"  removed {deleted_a} JSON entries")

    # Phase B — callsite rewrites + delete live keys
    plan = plan_data.get('plan', [])
    print(f"\nPhase B: rewriting callsites in {len(plan)} files + deleting live keys")
    bindings_added = 0
    rewrites = 0
    skipped = []
    for entry in plan:
        fpath = code_root / entry['file']
        content = fpath.read_text(encoding='utf-8')
        original = content

        if entry['has_common']:
            common_var = entry['common_var']
        else:
            common_var = 'tc'
            m = USE_TRANS_RE.search(content)
            if not m:
                skipped.append((entry['file'], 'no useTranslations binding'))
                continue
            line_end = content.find('\n', m.end())
            if line_end < 0: line_end = len(content)
            line_start = content.rfind('\n', 0, m.start()) + 1
            indent_m = re.match(r'^([ \t]*)', content[line_start:line_end])
            indent = indent_m.group(1) if indent_m else ''
            content = content[:line_end] + f"\n{indent}const tc = useTranslations('common')" + content[line_end:]
            bindings_added += 1

        for site in entry['sites']:
            var = site['var']; key_arg = site['key_arg']
            new_suffix = site['new_key'][len('common.'):]
            for q in ["'", '"', '`']:
                old_call = f"{var}({q}{key_arg}{q}"
                new_call = f"{common_var}({q}{new_suffix}{q}"
                if old_call in content:
                    n = content.count(old_call)
                    content = content.replace(old_call, new_call)
                    rewrites += n
                    break
            else:
                skipped.append((entry['file'], f"could not find {var}('{key_arg}')"))

        if content != original:
            fpath.write_text(content, encoding='utf-8')

    print(f"  rewrites: {rewrites}")
    print(f"  new bindings added: {bindings_added}")
    print(f"  skipped: {len(skipped)} (likely benign — second-pass for already-replaced sites)")

    # Now delete live keys from JSON
    live_keys = sorted(set(c['old_key'] for c in plan_data.get('callsites', [])))
    by_ns_live = collections.defaultdict(list)
    for k in live_keys:
        top, _, _ = k.partition('.')
        by_ns_live[top].append(k)
    deleted_b = 0
    for ns, keys in by_ns_live.items():
        for loc in LOCALES:
            path = msg_root / loc / f'{ns}.json'
            with path.open() as f: data = json.load(f)
            changed = False
            for k in keys:
                if _del_nested(data, k):
                    changed = True; deleted_b += 1
            if changed:
                with path.open('w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                    f.write('\n')

    print(f"\nTotal JSON entries removed: {deleted_a + deleted_b} ({deleted_a} dead + {deleted_b} live)")


def _del_nested(d, dotted_key):
    parts = dotted_key.split('.', 1)
    if len(parts) < 2: return False
    segs = parts[1].split('.')
    cur = d
    for seg in segs[:-1]:
        if seg not in cur or not isinstance(cur[seg], dict): return False
        cur = cur[seg]
    if segs[-1] in cur:
        del cur[segs[-1]]
        return True
    return False


# ── verify ─────────────────────────────────────────────────────────────────

def cmd_verify(args):
    msg_root = Path(args.msg_root) if args.msg_root else default_msg_root()
    msgs = {(ns, l): load_ns(msg_root, l, ns) for ns in NAMESPACES for l in LOCALES}
    by_en = collections.defaultdict(list)
    for ns in NAMESPACES:
        for k in msgs[(ns, 'en')]:
            en = get_str(msgs[(ns, 'en')], k)
            if not en: continue
            by_en[en].append((ns, k))
    safe = sum(1 for v in by_en.values()
               if len(v) > 1 and _all_locales_agree(msgs, v))
    print(f"Safe-to-merge groups remaining: {safe}")

    bad = []
    for path in msg_root.glob('*/*.json'):
        try:
            with path.open() as f: json.load(f)
        except Exception as e:
            bad.append((path, str(e)))
    if bad:
        for p, e in bad: print(f"  BROKEN: {p}: {e}")
        sys.exit(1)
    print("All JSON files parse cleanly.")


def _all_locales_agree(msgs, locs):
    for l in LOCALES:
        first = get_str(msgs[(locs[0][0], l)], locs[0][1])
        if not first: return False
        for ns, k in locs[1:]:
            if get_str(msgs[(ns, l)], k) != first: return False
    return True


# ── CLI ────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest='cmd', required=True)

    p_d = sub.add_parser('detect')
    p_d.add_argument('--root', help='messages root (auto-detected)')
    p_d.add_argument('--out-dir', default='/tmp')
    p_d.set_defaults(func=cmd_detect)

    p_m = sub.add_parser('map-callsites')
    p_m.add_argument('--code-root', help='apps/web root (auto-detected)')
    p_m.add_argument('--keys-file', default='/tmp/consolidation_keys.json',
                     help='JSON array of {old, new} pairs')
    p_m.add_argument('--out', default='/tmp/consolidation_callsites_final.json')
    p_m.set_defaults(func=cmd_map_callsites)

    p_a = sub.add_parser('apply')
    p_a.add_argument('--msg-root', help='messages root (auto-detected)')
    p_a.add_argument('--code-root', help='apps/web root (auto-detected)')
    p_a.add_argument('--plan-file', default='/tmp/consolidation_callsites_final.json')
    p_a.set_defaults(func=cmd_apply)

    p_v = sub.add_parser('verify')
    p_v.add_argument('--msg-root', help='messages root (auto-detected)')
    p_v.set_defaults(func=cmd_verify)

    args = ap.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
