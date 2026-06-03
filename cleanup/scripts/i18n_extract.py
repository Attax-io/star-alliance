#!/usr/bin/env python3
"""i18n EXTRACTION utility for Lex Council — the `hardcoded` cleanup mode.

Finds hardcoded user-facing English text still living in components and turns it
into next-intl keys. Complements `i18n_cleanup.py` (which only TRANSLATES keys
that already exist) and `consolidate_cleanup.py` (which DEDUPS keys).

Four subcommands (the deterministic machinery; the .tsx edits + translation are
the agent/recipe layer — see SKILL.md §Mode: hardcoded):

  detect     scan .tsx in scope for hardcoded-literal candidates; apply exclusions;
             reuse-map each against existing keys; emit an inventory + per-file
             agent briefs.  (the W0 grounding + W1 discovery, made deterministic)
  merge      single-writer merge of agent-returned key-map sidecars into
             en/<ns>.json; conflict-detect; reuse-existence check (catches keys an
             agent mislabeled as reuse → would be runtime MISSING_MESSAGE).
  propagate  set the newly-merged keys into all 6 locales (EN value as placeholder
             for non-EN) → parity + makes them visible to `language` mode.
  verify     for every t()-key in the touched .tsx, assert it resolves in en/<ns>.json
             (MISSING_MESSAGE guard) + scan for smart-quote t() calls (TS1127).

Default messages root: lex_council/apps/web/public/messages (walk-up auto-detect).
Override with --root or CLEANUP_MESSAGES_ROOT.  stdlib-only; git via subprocess.
"""
from __future__ import annotations
import argparse, glob, json, os, re, sys
from pathlib import Path

NAMESPACES = ['admin', 'auth', 'clients', 'common', 'errors', 'members',
              'pageIntros', 'portal', 'public', 'settings', 'toasts']
NON_EN_LOCALES = ['ar', 'es', 'fr', 'ru', 'zh']
ALL_LOCALES = ['en', *NON_EN_LOCALES]

# Latin-script terms that are never user-facing translatable copy.
BRAND_OR_CODE = {
    'Lex Council', 'LexCouncil', 'Lex', 'POA', 'NDA', 'OTP', 'GFN', 'MFN', 'BFN',
    'SFN', 'AFN', 'FFN', 'FN', 'HR', 'CSV', 'PDF', 'URL', 'UI', 'API', 'JSON',
    'SQL', 'RLS', 'RPC', 'WHBD', 'KPI', 'UUID', 'ID', 'IDs', 'EGP', 'SEO',
    'CIS', 'P&L', 'TM', 'PM', 'GCal', 'BC', 'KYC', 'REF', 'FP',
}
PLACEHOLDER_RE = re.compile(r'\{[a-zA-Z_][a-zA-Z0-9_]*\}')

# Candidate harvesters. Each yields (context, literal). Conservative — the agent
# layer is the accuracy pass; this is the high-recall candidate + reuse layer.
JSX_TEXT_RE = re.compile(r'>\s*([A-Za-z][^<>{}\n]*?[A-Za-z.!?)\]])\s*<')
PROP_RE = re.compile(
    r'\b(?:label|placeholder|title|aria-?[Ll]abel|alt|heading|subtitle|'
    r'description|tooltip|emptyText|confirmLabel|cancelLabel|message|caption|'
    r'eyebrow|hint|sub)\s*=\s*(?:"([^"{}\n]{2,})"|\'([^\'{}\n]{2,})\')')
CALL_RE = re.compile(
    r'(?:toast\.(?:success|error|info|warning|message)|throw new Error|'
    r'showError|setError|setActionError)\(\s*(?:"([^"{}\n]{2,})"|\'([^\'{}\n]{2,})\')')

EXCLUDE_DIR = ('__tests__', 'node_modules', '.next', '/_dev/', '.stories.')


def default_root() -> Path:
    env = os.environ.get('CLEANUP_MESSAGES_ROOT')
    if env:
        return Path(env).resolve()
    cwd = Path.cwd().resolve()
    for parent in [cwd, *cwd.parents]:
        for sub in (('lex_council', 'apps', 'web', 'public', 'messages'),
                    ('apps', 'web', 'public', 'messages')):
            cand = parent.joinpath(*sub)
            if cand.is_dir():
                return cand
    raise SystemExit("Could not locate messages root. Pass --root or set CLEANUP_MESSAGES_ROOT.")


def web_root(messages_root: Path) -> Path:
    return messages_root.parent.parent  # public/messages -> public -> web


def flatten(obj, prefix=''):
    out = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            out.update(flatten(v, f"{prefix}.{k}" if prefix else k))
    elif isinstance(obj, str):
        out[prefix] = obj
    return out


def load_en(root: Path):
    """{ns: {dotted_key: value}} + a value→fullkey reuse index (common preferred)."""
    per_ns, reuse = {}, {}
    for ns in NAMESPACES:
        fp = root / 'en' / f'{ns}.json'
        if not fp.exists():
            per_ns[ns] = {}; continue
        flat = flatten(json.load(fp.open(encoding='utf-8')))
        per_ns[ns] = flat
        for k, v in flat.items():
            if not isinstance(v, str):
                continue
            full = f'{ns}.{k}'
            norm = v.strip().lower()
            # prefer common.* as the reuse target; otherwise first-seen
            if norm not in reuse or ns == 'common':
                if norm not in reuse or not reuse[norm].startswith('common.'):
                    reuse[norm] = full
    return per_ns, reuse


def is_excluded(s: str) -> tuple[bool, str]:
    s = s.strip()
    if len(s) < 2:
        return True, 'too-short'
    if s in BRAND_OR_CODE:
        return True, 'brand'
    if re.fullmatch(r'[A-Z]{1,5}', s):
        return True, 'acronym'
    if re.fullmatch(r'[^A-Za-z]+', s):
        return True, 'no-letters'
    if re.fullmatch(r'[a-z][a-zA-Z0-9]*', s):
        return True, 'identifier'           # camelCase/snake single token
    if re.fullmatch(r'[a-z0-9_]+', s):
        return True, 'snake-id'
    if '://' in s or '@' in s or s.startswith('/') or s.startswith('http'):
        return True, 'url-or-path'
    if PLACEHOLDER_RE.fullmatch(s):
        return True, 'placeholder-only'
    if not re.search(r'[A-Za-z]{2,}', s):
        return True, 'no-word'
    return False, ''


def ns_for_path(rel: str) -> str:
    if '(admin)' in rel or 'components/dev-tools' in rel:
        return 'admin'
    if '(members)' in rel:
        return 'members'
    if '(clients)' in rel:
        return 'clients'
    if '(auth)' in rel:
        return 'auth'
    if '(portal)' in rel:
        return 'portal'
    if '(public)' in rel:
        return 'public'
    if rel.startswith('components/portal') or 'NavDrawer' in rel or 'Sidebar' in rel:
        return 'portal'
    return 'common'


def slug(s: str, n: int = 40) -> str:
    out = re.sub(r'[^a-z0-9]+', '_', s.strip().lower()).strip('_')
    return out[:n].rstrip('_') or 'label'


def scan_files(wr: Path, scope):
    roots = scope or ['app', 'components', 'lib', 'hooks', 'store']
    seen = set()
    for r in roots:
        base = wr / r
        if base.suffix:                       # explicit file path
            pats = [str(base)]
        else:
            pats = [str(base / '**' / '*.tsx'), str(base / '**' / '*.ts')]
        for pat in pats:
            for fp in glob.glob(pat, recursive=True):
                if not fp.endswith(('.tsx', '.ts')):
                    continue
                if any(x in fp for x in EXCLUDE_DIR) or '.test.' in fp or fp.endswith('.d.ts'):
                    continue
                if fp not in seen:
                    seen.add(fp); yield Path(fp)


def cmd_detect(args):
    root = Path(args.root).resolve() if args.root else default_root()
    wr = web_root(root)
    per_ns, reuse = load_en(root)
    out_dir = Path(args.out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    briefs_dir = out_dir / '_briefs'; briefs_dir.mkdir(exist_ok=True)
    inventory, totals = [], {'files': 0, 'candidates': 0, 'reuse': 0, 'new': 0}
    idx = 0
    for fp in scan_files(wr, args.scope):
        try:
            txt = fp.read_text(encoding='utf-8')
        except Exception:
            continue
        rel = str(fp.relative_to(wr))
        already = bool(re.search(r'useTranslations\(|getTranslations\(', txt))
        ns = ns_for_path(rel)
        base = slug(fp.stem)
        entries, dedupe = [], set()
        for m in JSX_TEXT_RE.finditer(txt):
            _add(entries, dedupe, txt, m.start(), 'jsx', m.group(1), ns, base, reuse)
        for m in PROP_RE.finditer(txt):
            _add(entries, dedupe, txt, m.start(), 'prop', m.group(1) or m.group(2), ns, base, reuse)
        for m in CALL_RE.finditer(txt):
            lit = m.group(1) or m.group(2)
            cns = 'toasts' if 'toast' in txt[m.start():m.start()+12] else 'errors'
            _add(entries, dedupe, txt, m.start(), 'call', lit, cns, base, reuse)
        if not entries:
            continue
        totals['files'] += 1
        totals['candidates'] += len(entries)
        totals['reuse'] += sum(1 for e in entries if e['reuseKey'])
        totals['new'] += sum(1 for e in entries if not e['reuseKey'])
        rec = {'idx': idx, 'file': rel, 'abs': str(fp), 'alreadyUsesI18n': already, 'entries': entries}
        inventory.append(rec)
        if args.briefs:
            (briefs_dir / f'b{idx}.json').write_text(json.dumps(rec, indent=2, ensure_ascii=False), encoding='utf-8')
        idx += 1
    (out_dir / 'inventory.json').write_text(json.dumps(inventory, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f"files-with-candidates: {totals['files']}  candidates: {totals['candidates']}  "
          f"reuse-mappable: {totals['reuse']}  new-keys: {totals['new']}")
    print(f"inventory → {out_dir/'inventory.json'}" + (f"  briefs → {briefs_dir}/b*.json" if args.briefs else ""))
    if totals['files'] > 60:
        print("NOTE: >60 files — app-wide scale. Fan-out (one agent/file) or /conquering-campaign for multi-session.")


def _add(entries, dedupe, txt, pos, ctx, lit, ns, base, reuse):
    lit = (lit or '').strip()
    if lit in dedupe:
        return
    ex, why = is_excluded(lit)
    if ex:
        return
    dedupe.add(lit)
    line = txt.count('\n', 0, pos) + 1
    rk = reuse.get(lit.strip().lower())
    entries.append({
        'line': line, 'literal': lit, 'context': ctx,
        'reuseKey': rk,
        'proposedKey': None if rk else f'{ns}.{base}.{slug(lit)}',
        'namespace': rk.split('.', 1)[0] if rk else ns,
    })


def _set_dotted(d, dotted, val, conflicts, label):
    parts = dotted.split('.'); cur = d
    for p in parts[:-1]:
        nxt = cur.get(p)
        if nxt is None:
            cur[p] = {}; cur = cur[p]
        elif isinstance(nxt, dict):
            cur = nxt
        else:
            conflicts.append(f"{label}:{dotted} (segment '{p}' not an object)"); return False
    leaf = parts[-1]
    if leaf in cur and cur[leaf] != val:
        conflicts.append(f"{label}:{dotted} exists='{cur[leaf]}' new='{val}' (kept existing)"); return False
    if leaf in cur:
        return False
    cur[leaf] = val; return True


def _has_dotted(d, dotted):
    cur = d
    for p in dotted.split('.'):
        if not isinstance(cur, dict) or p not in cur:
            return False
        cur = cur[p]
    return True


def _write_json(fp: Path, d):
    fp.write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n", encoding='utf-8')


def cmd_merge(args):
    """Merge agent key-map sidecars (b*.json with namespace_keys + reused_keys) into en/<ns>.json."""
    root = Path(args.root).resolve() if args.root else default_root()
    sidecars = sorted(glob.glob(os.path.join(args.keys_dir, 'b*.json')))
    agg, reused, notes = {}, {}, []
    for sc in sidecars:
        try:
            r = json.load(open(sc, encoding='utf-8'))
        except Exception as e:
            notes.append(f"parse-fail {os.path.basename(sc)}: {e}"); continue
        for ns, keys in (r.get('namespace_keys') or {}).items():
            if not isinstance(keys, dict):
                continue
            for k, v in keys.items():
                agg.setdefault(ns, {})
                if k in agg[ns] and agg[ns][k] != v:
                    notes.append(f"cross-file clash {ns}.{k}: kept '{agg[ns][k]}' over '{v}'")
                else:
                    agg[ns].setdefault(k, v)
        for rk in (r.get('reused_keys') or []):
            seg = rk.split('.', 1)
            if len(seg) == 2:
                reused.setdefault(seg[0], set()).add(seg[1])
    report = {}
    for ns, keys in sorted(agg.items()):
        fp = root / 'en' / f'{ns}.json'
        if not fp.exists():
            notes.append(f"en/{ns}.json missing — {len(keys)} keys NOT merged"); continue
        d = json.load(fp.open(encoding='utf-8'))
        conflicts = []; added = 0
        for k, v in keys.items():
            if _set_dotted(d, k, v, conflicts, ns):
                added += 1
        _write_json(fp, d)
        report[ns] = sorted(keys.keys())
        print(f"en/{ns}.json: +{added} new ({len(keys)} proposed, {len(conflicts)} conflicts)")
        notes.extend(conflicts[:6])
    # reuse-existence check — the 21-bad-keys catch
    missing = []
    for ns, ks in sorted(reused.items()):
        fp = root / 'en' / f'{ns}.json'
        d = json.load(fp.open(encoding='utf-8')) if fp.exists() else {}
        for k in sorted(ks):
            if not _has_dotted(d, k):
                missing.append(f'{ns}.{k}')
    out = {'merge_report': report, 'missing_reuse': missing, 'notes': notes}
    Path(args.out).write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f"\nmerged {sum(len(v) for v in report.values())} keys across {len(report)} namespaces → report {args.out}")
    if missing:
        print(f"!! {len(missing)} reuse keys DO NOT EXIST (agent mislabeled — recover the literal + add, else runtime MISSING_MESSAGE):")
        for m in missing:
            print('   ', m)
    if notes:
        print(f"({len(notes)} merge notes in report)")


def cmd_propagate(args):
    """Set merged keys into all non-EN locales with the EN value (present-but-EN → translatable)."""
    root = Path(args.root).resolve() if args.root else default_root()
    report = json.load(open(args.report, encoding='utf-8')).get('merge_report', {})
    totals = {l: 0 for l in NON_EN_LOCALES}
    for ns, keys in report.items():
        en = json.load((root / 'en' / f'{ns}.json').open(encoding='utf-8'))
        flat_en = flatten(en)
        for loc in NON_EN_LOCALES:
            fp = root / loc / f'{ns}.json'
            if not fp.exists():
                continue
            d = json.load(fp.open(encoding='utf-8')); conflicts = []; added = 0
            for k in keys:
                v = flat_en.get(k)
                if v is None:
                    continue
                if _set_dotted(d, k, v, conflicts, f'{loc}/{ns}'):
                    added += 1
            if added:
                _write_json(fp, d)
            totals[loc] += added
    print(f"propagated (EN placeholder) per locale: {totals}")
    print("next: run `i18n_cleanup.py detect/apply/verify` (the `language` mode) to translate the now-present-but-EN keys.")


def cmd_verify(args):
    """Every t()-key in touched .tsx must resolve in en/<one of the file's namespaces>; flag smart-quote t()."""
    root = Path(args.root).resolve() if args.root else default_root()
    wr = web_root(root)
    per_ns, _ = load_en(root)
    unresolved, smart = [], []
    use_re = re.compile(r'useTranslations\(\s*[\'"]([^\'"]+)[\'"]')
    call_re = re.compile(r'\b[a-zA-Z]\w*\(\s*[\'"]([a-z][\w]*(?:\.[\w]+)+)[\'"]')
    smart_re = re.compile(r'(?:useTranslations|getTranslations)\(\s*[‘’“”]')
    for fp in scan_files(wr, args.scope):
        try:
            txt = fp.read_text(encoding='utf-8')
        except Exception:
            continue
        if smart_re.search(txt):
            smart.append(str(fp.relative_to(wr)))
        ns_in_file = set(use_re.findall(txt))
        if not ns_in_file:
            continue
        # candidate namespaces: the first segment of each useTranslations arg
        cand_ns = {n.split('.', 1)[0] for n in ns_in_file}
        for key in set(call_re.findall(txt)):
            # try key as full (ns.rest) and as rest under each file namespace
            resolved = False
            top = key.split('.', 1)[0]
            if top in per_ns and (key[len(top) + 1:] in per_ns[top] or key in per_ns.get(top, {})):
                resolved = True
            for n in cand_ns:
                # if useTranslations('admin'), t('attendance.x') → admin.attendance.x
                sub = key
                if n in per_ns and sub in per_ns[n]:
                    resolved = True; break
                # useTranslations('portal.verification_flow') + t('band') → portal.verification_flow.band
                for full_ns in ns_in_file:
                    base = full_ns.split('.', 1)
                    look = (base[1] + '.' if len(base) == 2 else '') + key
                    if base[0] in per_ns and look in per_ns[base[0]]:
                        resolved = True; break
                if resolved:
                    break
            if not resolved and top not in ('http', 'https'):
                unresolved.append(f"{fp.relative_to(wr)}  t('{key}')")
    if smart:
        print(f"!! {len(smart)} files with smart-quote useTranslations/getTranslations (TS1127 — replace with straight quotes):")
        for s in smart:
            print('   ', s)
    if unresolved:
        print(f"!! {len(unresolved)} t()-keys may not resolve (verify against en/*.json — MISSING_MESSAGE risk; some are false positives for dynamic/template keys):")
        for u in unresolved[:60]:
            print('   ', u)
        print(f"   ({len(unresolved)} total)" if len(unresolved) > 60 else "")
    if not smart and not unresolved:
        print("verify clean — no smart-quote calls; all sampled t()-keys resolve.")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest='cmd', required=True)

    d = sub.add_parser('detect', help='scan .tsx for hardcoded-literal candidates + reuse-map + briefs')
    d.add_argument('--root'); d.add_argument('--scope', nargs='+', help='paths under apps/web (default: app components lib hooks store)')
    d.add_argument('--out-dir', default='/tmp/i18n_extract')
    d.add_argument('--briefs', action='store_true', help='also emit per-file agent brief JSONs')
    d.set_defaults(func=cmd_detect)

    m = sub.add_parser('merge', help='merge agent key-map sidecars into en/<ns>.json (single writer) + reuse-existence check')
    m.add_argument('--root'); m.add_argument('--keys-dir', required=True, help='dir of agent b*.json sidecars')
    m.add_argument('--out', default='/tmp/i18n_extract/merge_report.json')
    m.set_defaults(func=cmd_merge)

    p = sub.add_parser('propagate', help='set merged keys into all 6 locales (EN placeholder for non-EN)')
    p.add_argument('--root'); p.add_argument('--report', default='/tmp/i18n_extract/merge_report.json')
    p.set_defaults(func=cmd_propagate)

    v = sub.add_parser('verify', help='assert t()-keys resolve in en/*.json + flag smart-quote calls')
    v.add_argument('--root'); v.add_argument('--scope', nargs='+')
    v.set_defaults(func=cmd_verify)

    args = ap.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
