#!/usr/bin/env python3
"""i18n cleanup utility for Lex Council.

Three subcommands:
  detect   — scan messages/{locale}/*.json, write per-locale target lists
             of (ns, key, en) tuples where the locale value equals EN.
  apply    — read /tmp/translations_{loc}.json (produced by translation agents)
             and write each translated value back into messages/{loc}/{ns}.json.
  verify   — re-run the detector and print the before/after delta.

Default messages root: lex_council/apps/web/public/messages
Override with --root <path> or CLEANUP_MESSAGES_ROOT env var.
"""
from __future__ import annotations
import argparse, collections, glob, json, os, re, subprocess, sys
from pathlib import Path
from typing import Iterable

NAMESPACES = ['admin', 'auth', 'clients', 'common', 'errors', 'members',
              'pageIntros', 'portal', 'public', 'settings', 'toasts']
NON_EN_LOCALES = ['ar', 'es', 'fr', 'ru', 'zh']
ALL_LOCALES = ['en', *NON_EN_LOCALES]

# Brand terms / acronyms / file-tier codes that stay in Latin script across
# every locale. Single-char strings, pure-digit strings, and bare punctuation
# are also skipped (handled by the regex checks below).
BRAND_OR_CODE = {
    'Lex Council', 'LexCouncil', 'Lex',
    'POA', 'NDA', 'OTP',
    'GFN', 'MFN', 'BFN', 'SFN', 'AFN', 'FN',
    'HR', 'CSV', 'PDF', 'URL', 'UI', 'API', 'JSON', 'SQL', 'RLS', 'RPC',
    'TSL', 'WHBD', 'KPI', 'UUID', 'ID', 'IDs',
    'CIS', 'P&L', 'TM', 'PM', 'GCal', 'BC',
}

PLACEHOLDER_RE = re.compile(r'\{[a-zA-Z_][a-zA-Z0-9_]*\}')


def default_root() -> Path:
    env = os.environ.get('CLEANUP_MESSAGES_ROOT')
    if env:
        return Path(env).resolve()
    # walk up from cwd looking for lex_council/apps/web/public/messages
    cwd = Path.cwd().resolve()
    for parent in [cwd, *cwd.parents]:
        cand = parent / 'lex_council' / 'apps' / 'web' / 'public' / 'messages'
        if cand.is_dir():
            return cand
        cand = parent / 'apps' / 'web' / 'public' / 'messages'
        if cand.is_dir():
            return cand
    raise SystemExit("Could not locate messages root. Pass --root or set CLEANUP_MESSAGES_ROOT.")


def flatten(obj, prefix='') -> dict[str, str]:
    out: dict[str, str] = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            p = f"{prefix}.{k}" if prefix else k
            out.update(flatten(v, p))
    elif isinstance(obj, str):
        out[prefix] = obj
    return out


def load_ns(root: Path, loc: str, ns: str) -> dict[str, str]:
    with (root / loc / f'{ns}.json').open('r', encoding='utf-8') as f:
        return flatten(json.load(f))


def is_brand_or_code(s: str) -> bool:
    s = s.strip()
    if not s or len(s) <= 1:
        return True
    if re.fullmatch(r'[0-9]+%?', s):
        return True
    if re.fullmatch(r'[A-Z]{1,4}', s):
        return True
    if re.fullmatch(r'[^\w]+', s):
        return True
    if s in BRAND_OR_CODE:
        return True
    return False


def collect_targets(root: Path, locales: Iterable[str],
                    skip_cognate_es_fr: bool = False) -> dict[str, list[dict]]:
    """For each locale, return list of {ns, key, en} where value == EN."""
    targets: dict[str, list[dict]] = {l: [] for l in locales}
    for ns in NAMESPACES:
        en = load_ns(root, 'en', ns)
        for loc in locales:
            non = load_ns(root, loc, ns)
            for k, v_en in en.items():
                if not isinstance(v_en, str) or not v_en.strip():
                    continue
                v_non = non.get(k, '')
                if not (isinstance(v_non, str) and v_non.strip() == v_en.strip()):
                    continue
                if is_brand_or_code(v_en):
                    continue
                if skip_cognate_es_fr and loc in ('es', 'fr'):
                    # Single-word, no-placeholder → likely valid cognate
                    if ' ' not in v_en and '{' not in v_en:
                        continue
                targets[loc].append({'ns': ns, 'key': k, 'en': v_en})
    return targets


def scan_window_confirm(messages_root: Path) -> list[dict]:
    """Grep apps/web for window.confirm( calls (L16 — untranslatable i18n debt).

    Purely additive surfacing: these strings can't be covered by the key-scan
    because they never reach the JSON. messages_root is .../apps/web/public/
    messages, so .parent.parent is the apps/web tree to grep.
    """
    web_root = messages_root.parent.parent  # public/messages → web
    if not web_root.is_dir():
        return []
    try:
        proc = subprocess.run(
            ['grep', '-rn', '--include=*.ts', '--include=*.tsx',
             r'window\.confirm(', str(web_root)],
            capture_output=True, text=True,
        )
    except FileNotFoundError:
        return []
    hits: list[dict] = []
    for line in proc.stdout.splitlines():
        # grep -rn format: <path>:<lineno>:<text>
        parts = line.split(':', 2)
        if len(parts) < 3:
            continue
        path, lineno, text = parts
        hits.append({'file': path, 'line': lineno, 'text': text.strip()})
    return hits


def cmd_detect(args):
    root = Path(args.root) if args.root else default_root()
    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    locales = args.locales or NON_EN_LOCALES
    targets = collect_targets(root, locales, skip_cognate_es_fr=args.skip_cognates)
    summary = []
    for loc in locales:
        path = out_dir / f'translation_targets_{loc}.json'
        with path.open('w', encoding='utf-8') as f:
            json.dump(targets[loc], f, ensure_ascii=False, indent=2)
        summary.append((loc, len(targets[loc]), str(path)))
    print(f"{'locale':<6} {'targets':>8}  output")
    print('-' * 60)
    for loc, n, p in summary:
        print(f"{loc:<6} {n:>8}  {p}")
    print(f"\nTotal: {sum(n for _, n, _ in summary)} (ns, key, en) tuples across {len(locales)} locales")

    # L16 — additive surfacing: window.confirm() calls are untranslatable i18n debt
    # the key-scan above can't see. Cheap one-grep pass over the apps/web tree.
    confirm_hits = scan_window_confirm(root)
    if confirm_hits:
        n_files = len({h['file'] for h in confirm_hits})
        wc_path = Path('/tmp/i18n_window_confirm.json')
        with wc_path.open('w', encoding='utf-8') as f:
            json.dump(confirm_hits, f, ensure_ascii=False, indent=2)
        print(f"\U0001F6A9 {len(confirm_hits)} window.confirm() calls "
              f"(untranslatable — i18n debt) across {n_files} files → {wc_path}")


def set_nested(d: dict, dotted_key: str, value):
    parts = dotted_key.split('.')
    cur = d
    for p in parts[:-1]:
        if p not in cur or not isinstance(cur[p], dict):
            raise KeyError(f"missing path at {p!r} in {dotted_key!r}")
        cur = cur[p]
    cur[parts[-1]] = value


def cmd_apply(args):
    root = Path(args.root) if args.root else default_root()
    in_dir = Path(args.in_dir).resolve()
    locales = args.locales or NON_EN_LOCALES

    # Pre-flight: validate every file
    print("Pre-flight checks:")
    print(f"{'loc':<4} {'targets':>8} {'returned':>9} {'placeholder_mismatch':>22} {'empty':>6} {'identical':>10}")
    print('-' * 68)
    failures = []
    all_results: dict[str, list] = {}
    for loc in locales:
        tgt_path = in_dir / f'translation_targets_{loc}.json'
        out_path = in_dir / f'translations_{loc}.json'
        if not tgt_path.exists() or not out_path.exists():
            print(f"{loc:<4}  missing target or output file — skipping")
            failures.append(loc)
            continue
        with tgt_path.open() as f:
            targets = json.load(f)
        with out_path.open() as f:
            results = json.load(f)
        if isinstance(results, dict) and 'translations' in results:
            results = results['translations']
        by_key = {(r.get('ns'), r.get('key')): r.get('translated', '') for r in results}
        mismatch = empty = identical = 0
        for t in targets:
            tr = by_key.get((t['ns'], t['key']), '')
            if not isinstance(tr, str) or not tr.strip():
                empty += 1
                continue
            en = t['en']
            if set(PLACEHOLDER_RE.findall(en)) != set(PLACEHOLDER_RE.findall(tr)):
                mismatch += 1
            if tr.strip() == en.strip():
                identical += 1
        print(f"{loc:<4} {len(targets):>8} {len(results):>9} {mismatch:>22} {empty:>6} {identical:>10}")
        if len(results) != len(targets) or mismatch > 0 or empty > 0:
            failures.append(loc)
        all_results[loc] = results

    if failures and not args.force:
        print(f"\nFAILED pre-flight for: {', '.join(failures)}. Pass --force to apply anyway.")
        sys.exit(1)

    # Apply
    print(f"\nApplying translations...")
    per_file: dict[tuple[str, str], list[tuple[str, str]]] = collections.defaultdict(list)
    for loc in locales:
        if loc not in all_results:
            continue
        for r in all_results[loc]:
            per_file[(loc, r['ns'])].append((r['key'], r['translated']))

    total = 0
    for (loc, ns), entries in sorted(per_file.items()):
        path = root / loc / f'{ns}.json'
        with path.open('r', encoding='utf-8') as f:
            data = json.load(f)
        for k, v in entries:
            set_nested(data, k, v)
            total += 1
        with path.open('w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write('\n')
        print(f"  {loc}/{ns}.json  +{len(entries)}")
    print(f"\nWrote {total} translations across {len(per_file)} files.")


def cmd_verify(args):
    root = Path(args.root) if args.root else default_root()
    locales = args.locales or NON_EN_LOCALES
    print(f"{'locale':<6} {'untranslated':>13}")
    print('-' * 22)
    total = 0
    for loc in locales:
        cnt = 0
        for ns in NAMESPACES:
            en = load_ns(root, 'en', ns)
            non = load_ns(root, loc, ns)
            for k, v_en in en.items():
                if not isinstance(v_en, str) or not v_en.strip():
                    continue
                v_non = non.get(k, '')
                if isinstance(v_non, str) and v_non.strip() == v_en.strip():
                    cnt += 1
        print(f"{loc:<6} {cnt:>13}")
        total += cnt
    print(f"{'TOTAL':<6} {total:>13}")
    # JSON parse check
    bad = []
    for path in (root).glob('*/*.json'):
        try:
            with path.open() as f:
                json.load(f)
        except Exception as e:
            bad.append((path, str(e)))
    if bad:
        print(f"\n{len(bad)} JSON files FAILED to parse:")
        for p, e in bad:
            print(f"  {p}: {e}")
        sys.exit(1)
    else:
        print(f"\nAll JSON files parse cleanly.")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest='cmd', required=True)

    p_d = sub.add_parser('detect', help='scan messages/, write per-locale target JSONs')
    p_d.add_argument('--root', help='path to messages root (default: auto-detect)')
    p_d.add_argument('--out-dir', default='/tmp', help='where to write target JSONs (default: /tmp)')
    p_d.add_argument('--locales', nargs='+', choices=NON_EN_LOCALES,
                     help='locales to detect (default: all non-EN)')
    p_d.add_argument('--skip-cognates', action='store_true',
                     help='for ES/FR, skip single-word no-placeholder strings (probable cognates)')
    p_d.set_defaults(func=cmd_detect)

    p_a = sub.add_parser('apply', help='write translations back into messages/{loc}/{ns}.json')
    p_a.add_argument('--root', help='path to messages root (default: auto-detect)')
    p_a.add_argument('--in-dir', default='/tmp', help='where translations_{loc}.json live (default: /tmp)')
    p_a.add_argument('--locales', nargs='+', choices=NON_EN_LOCALES)
    p_a.add_argument('--force', action='store_true', help='apply even if pre-flight checks fail')
    p_a.set_defaults(func=cmd_apply)

    p_v = sub.add_parser('verify', help='re-run untranslated detector + validate all JSON parses')
    p_v.add_argument('--root', help='path to messages root (default: auto-detect)')
    p_v.add_argument('--locales', nargs='+', choices=NON_EN_LOCALES)
    p_v.set_defaults(func=cmd_verify)

    args = ap.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
