#!/usr/bin/env python3
"""i18n cleanup utility for Lex Council — the `language` cleanup mode.

Source of truth (Bug #303): `public.app_translations` (DB). The web build dumps
DB → messages/{locale}/{ns}.json, so an edit that lands ONLY in the JSON is
overwritten by the next build. This tool therefore READS and WRITES the DB; the
JSON is kept in sync as a projection (committed, re-dumped at build time).

Three subcommands:
  detect   — read app_translations (DB), write per-locale target lists of
             (ns, key, en) tuples where the locale value still equals EN.
             Falls back to the committed JSON when no DB credentials are present
             (so an unattended run_all / rotation never breaks).
  apply    — read /tmp/translations_{loc}.json (produced by translation agents),
             pre-flight, then UPSERT each translated value into app_translations
             (prod, service-role REST) and mirror it into messages/{loc}/{ns}.json.
  verify   — re-run the detector (DB) and print the before/after delta.

Transport: service-role REST via the shared _db_translations helper (stdlib, no
MCP/psql) — the same path push/dump-translations.mjs use. The prod project ref
(bqgrpnsvplvicnmzxwkm) is asserted before any write (override: --allow-other-project).

Default messages root: lex_council/apps/web/public/messages
Override with --root <path> or CLEANUP_MESSAGES_ROOT env var.
"""
from __future__ import annotations
import argparse, collections, json, os, re, subprocess, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _db_translations as db  # noqa: E402

# The live 12 namespaces (i18n/request.ts). `tools` is the 12th (added during #303).
NAMESPACES = ['admin', 'auth', 'clients', 'common', 'errors', 'members',
              'pageIntros', 'portal', 'public', 'settings', 'toasts', 'tools']
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


def collect_targets(flat: dict, locales, skip_cognate_es_fr: bool = False) -> dict[str, list[dict]]:
    """For each locale, return list of {ns, key, en} where value == EN. `flat` is
    the {(loc, ns): {key: value}} map from db.flat_map (DB or files)."""
    targets: dict[str, list[dict]] = {l: [] for l in locales}
    for ns in NAMESPACES:
        en = flat.get(('en', ns), {})
        for loc in locales:
            non = flat.get((loc, ns), {})
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
    source, flat = db.flat_map(args.files, args.allow_other, root, NAMESPACES, ['en', *locales])
    targets = collect_targets(flat, locales, skip_cognate_es_fr=args.skip_cognates)
    summary = []
    for loc in locales:
        path = out_dir / f'translation_targets_{loc}.json'
        with path.open('w', encoding='utf-8') as f:
            json.dump(targets[loc], f, ensure_ascii=False, indent=2)
        summary.append((loc, len(targets[loc]), str(path)))
    print(f"source: {db.source_label(source)}")
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

    # Collect every (locale, namespace, key_path, value) row to write.
    rows: list[dict] = []
    per_file: dict[tuple[str, str], list[tuple[str, str]]] = collections.defaultdict(list)
    for loc in locales:
        if loc not in all_results:
            continue
        for r in all_results[loc]:
            tr = r.get('translated', '')
            if not isinstance(tr, str) or not tr.strip():
                continue
            rows.append({'locale': loc, 'namespace': r['ns'], 'key_path': r['key'], 'value': tr})
            per_file[(loc, r['ns'])].append((r['key'], tr))

    # ── Primary write: UPSERT into app_translations (the source of truth) ──
    if not args.files_only:
        env = db.load_env(allow_other=args.allow_other)
        if env is None:
            print("\n[apply] FATAL: no DB credentials (env / apps/web/.env.local). "
                  "app_translations is the source of truth — a JSON-only write is silently "
                  "overwritten by the next build dump. Set NEXT_PUBLIC_SUPABASE_URL + "
                  "SUPABASE_SERVICE_ROLE_KEY, or pass --files-only to deliberately write JSON only.")
            sys.exit(2)
        print(f"\nUpserting {len(rows)} translations → app_translations (prod {env['ref']}, service-role REST)…")
        written = db.upsert_rows(env, rows)
        touched_ns = sorted({r['namespace'] for r in rows})
        print(f"  upserted {written} rows across {len(touched_ns)} namespace(s): {', '.join(touched_ns)}")
    else:
        print("\n[apply] --files-only: skipping the DB upsert (JSON-only; will be overwritten by the next build dump).")

    # ── Mirror into the committed JSON so the working tree reflects the DB ──
    # (The build re-dumps DB→JSON; this keeps the diff reviewable now.)
    print("Mirroring into messages/{loc}/{ns}.json…")
    total = 0
    skipped = 0
    for (loc, ns), entries in sorted(per_file.items()):
        path = root / loc / f'{ns}.json'
        try:
            with path.open('r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            print(f"  {loc}/{ns}.json  (absent — DB has it; next dump will materialize)")
            skipped += len(entries)
            continue
        applied = 0
        for k, v in entries:
            try:
                set_nested(data, k, v)
                applied += 1
                total += 1
            except KeyError:
                # Structural gap in the JSON (key not present yet) — the DB write
                # already captured it; the next build dump will materialize it.
                skipped += 1
        with path.open('w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write('\n')
        print(f"  {loc}/{ns}.json  +{applied}")
    tail = f" ({skipped} deferred to the next build dump)" if skipped else ""
    print(f"\nWrote {total} translations into JSON across {len(per_file)} files{tail}.")
    if not args.files_only:
        print("DB is the source of truth; the committed JSON above mirrors it (build re-dumps).")


def cmd_verify(args):
    root = Path(args.root) if args.root else default_root()
    locales = args.locales or NON_EN_LOCALES
    source, flat = db.flat_map(args.files, args.allow_other, root, NAMESPACES, ['en', *locales])
    print(f"source: {db.source_label(source)}")
    print(f"{'locale':<6} {'untranslated':>13}")
    print('-' * 22)
    total = 0
    for loc in locales:
        cnt = 0
        for ns in NAMESPACES:
            en = flat.get(('en', ns), {})
            non = flat.get((loc, ns), {})
            for k, v_en in en.items():
                if not isinstance(v_en, str) or not v_en.strip():
                    continue
                v_non = non.get(k, '')
                if isinstance(v_non, str) and v_non.strip() == v_en.strip():
                    cnt += 1
        print(f"{loc:<6} {cnt:>13}")
        total += cnt
    print(f"{'TOTAL':<6} {total:>13}")
    # JSON parse check — validates the committed working tree regardless of source.
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


def _add_source_flags(p):
    p.add_argument('--files', action='store_true',
                   help='read the committed JSON instead of the DB (offline / CI)')
    p.add_argument('--allow-other-project', dest='allow_other', action='store_true',
                   help='permit a non-prod Supabase project ref (default: refuse)')


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest='cmd', required=True)

    p_d = sub.add_parser('detect', help='read app_translations (DB), write per-locale target JSONs')
    p_d.add_argument('--root', help='path to messages root (default: auto-detect)')
    p_d.add_argument('--out-dir', default='/tmp', help='where to write target JSONs (default: /tmp)')
    p_d.add_argument('--locales', nargs='+', choices=NON_EN_LOCALES,
                     help='locales to detect (default: all non-EN)')
    p_d.add_argument('--skip-cognates', action='store_true',
                     help='for ES/FR, skip single-word no-placeholder strings (probable cognates)')
    _add_source_flags(p_d)
    p_d.set_defaults(func=cmd_detect)

    p_a = sub.add_parser('apply', help='upsert translations into app_translations + mirror into JSON')
    p_a.add_argument('--root', help='path to messages root (default: auto-detect)')
    p_a.add_argument('--in-dir', default='/tmp', help='where translations_{loc}.json live (default: /tmp)')
    p_a.add_argument('--locales', nargs='+', choices=NON_EN_LOCALES)
    p_a.add_argument('--force', action='store_true', help='apply even if pre-flight checks fail')
    p_a.add_argument('--files-only', action='store_true',
                     help='write JSON only, skip the DB upsert (DANGER: overwritten by the next build dump)')
    p_a.add_argument('--allow-other-project', dest='allow_other', action='store_true',
                     help='permit a non-prod Supabase project ref (default: refuse)')
    p_a.set_defaults(func=cmd_apply)

    p_v = sub.add_parser('verify', help='re-run the untranslated detector + validate all JSON parses')
    p_v.add_argument('--root', help='path to messages root (default: auto-detect)')
    p_v.add_argument('--locales', nargs='+', choices=NON_EN_LOCALES)
    _add_source_flags(p_v)
    p_v.set_defaults(func=cmd_verify)

    args = ap.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
