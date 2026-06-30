#!/usr/bin/env python3
"""Shared DB transport for the cleanup skill's i18n modes (Bug #303 follow-up).

`public.app_translations` (prod project bqgrpnsvplvicnmzxwkm) is the single
source of truth for every next-intl UI string (12 namespaces × 6 locales). The
web build dumps DB → `apps/web/public/messages/{locale}/{ns}.json`
(`dump-translations.mjs --soft`), so any edit that lands ONLY in the JSON is
silently overwritten by the next build. The i18n cleanup modes therefore write
the DB; the JSON is kept in sync as a projection (the build re-dumps it).

This module is the Python counterpart to `apps/web/scripts/{dump,push}-translations.mjs`:
service-role REST against the same table, stdlib-only (urllib), no MCP/psql.

Why direct table REST and not the `upsert_translation` / `delete_translation`
RPCs: both are SECURITY DEFINER + programmer-gated (`is_programmer(auth.uid())`).
A service-role call has a NULL `auth.uid()`, so the gate rejects it. The table
itself, however, is reachable by `service_role` (RLS bypassed) — exactly how
`push-translations.mjs` upserts. `delete_translation` is also id-based
(`p_id bigint`), so it can't address a row by (locale, namespace, key_path)
without a prior lookup. Direct REST DELETE on the unique key is the symmetric,
headless-safe path.

Public API:
    load_env(allow_other=False)            -> {'url','key','ref'} or None
    fetch_flat(env, namespaces, locales)   -> {(loc, ns): {key_path: value}}
    upsert_rows(env, rows, chunk=2000)     -> int written          (rows: list of dicts)
    delete_keys(env, ns, key_paths)        -> int deleted-or-matched (all locales)
    count_namespace(env, ns)               -> int

`load_env` returns None (rather than exiting) when credentials are absent, so a
read-only DETECT can fall back to the committed JSON and never crash an
unattended `run_all` / rotation. WRITE paths must treat None as fatal.
"""
from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

# Production guard (CLAUDE.md G2). Mirrors push-translations.mjs EXPECT_PROJECT_REF.
EXPECT_PROJECT_REF = 'bqgrpnsvplvicnmzxwkm'

# The live 12 namespaces (i18n/request.ts) × 6 locales (routing.ts). `tools` is
# the 12th, added by the concurrent actor during #303 — older copies of the
# cleanup scripts omitted it.
ALL_NAMESPACES = ['admin', 'auth', 'members', 'portal', 'clients', 'public',
                  'tools', 'common', 'errors', 'toasts', 'pageIntros', 'settings']
ALL_LOCALES = ['en', 'ar', 'fr', 'ru', 'zh', 'es']

_PAGE = 1000  # PostgREST default max rows per response


# ── env ──────────────────────────────────────────────────────────────────────

def find_env_file() -> Path | None:
    """Locate apps/web/.env.local by walking up from cwd and this file."""
    starts = [Path.cwd().resolve(), Path(__file__).resolve().parent]
    seen: set[Path] = set()
    for start in starts:
        for parent in [start, *start.parents]:
            if parent in seen:
                continue
            seen.add(parent)
            for sub in (('lex_council', 'apps', 'web', '.env.local'),
                        ('apps', 'web', '.env.local')):
                cand = parent.joinpath(*sub)
                if cand.is_file():
                    return cand
    return None


def load_env(allow_other: bool = False) -> dict | None:
    """Read NEXT_PUBLIC_SUPABASE_URL + SUPABASE_SERVICE_ROLE_KEY from the process
    env, else from apps/web/.env.local. Returns {'url','key','ref'} or None when
    credentials are missing. Raises SystemExit if the project ref is not the
    expected prod ref and `allow_other` is False (G2)."""
    url = os.environ.get('NEXT_PUBLIC_SUPABASE_URL')
    key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
    if not url or not key:
        envf = find_env_file()
        if envf:
            for line in envf.read_text(encoding='utf-8').splitlines():
                m = re.match(r'^\s*([A-Z0-9_]+)\s*=\s*(.*)\s*$', line)
                if not m:
                    continue
                v = m.group(2).strip().strip('"').strip("'")
                if m.group(1) == 'NEXT_PUBLIC_SUPABASE_URL' and not url:
                    url = v
                if m.group(1) == 'SUPABASE_SERVICE_ROLE_KEY' and not key:
                    key = v
    if not url or not key:
        return None
    url = url.rstrip('/')
    mm = re.match(r'https://([a-z0-9]+)\.supabase', url)
    ref = mm.group(1) if mm else None
    if ref != EXPECT_PROJECT_REF and not allow_other:
        raise SystemExit(
            f"[db] REFUSING: project ref {ref!r} != expected {EXPECT_PROJECT_REF!r}. "
            f"Pass --allow-other-project to override."
        )
    return {'url': url, 'key': key, 'ref': ref}


# ── REST primitive ───────────────────────────────────────────────────────────

def _req(env: dict, method: str, path: str, body=None, extra_headers=None):
    """Issue one REST call. Returns (status, headers_dict, raw_text)."""
    headers = {'apikey': env['key'], 'Authorization': f"Bearer {env['key']}"}
    data = None
    if body is not None:
        data = json.dumps(body).encode('utf-8')
        headers['Content-Type'] = 'application/json'
    if extra_headers:
        headers.update(extra_headers)
    req = urllib.request.Request(env['url'] + path, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, dict(resp.headers), resp.read().decode('utf-8')
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read().decode('utf-8', 'replace')


# ── reads ────────────────────────────────────────────────────────────────────

def fetch_flat(env: dict, namespaces, locales) -> dict:
    """Return {(loc, ns): {key_path: value}} for the requested namespaces/locales,
    read straight from app_translations. The shape matches the scripts' existing
    `flatten(json)` output, so the comparison logic is source-agnostic."""
    out = {(loc, ns): {} for ns in namespaces for loc in locales}
    loc_set = set(locales)
    for ns in namespaces:
        offset = 0
        while True:
            path = (f"/rest/v1/app_translations?select=locale,key_path,value"
                    f"&namespace=eq.{urllib.parse.quote(ns)}&order=locale,key_path")
            status, _, raw = _req(env, 'GET', path,
                                  extra_headers={'Range': f'{offset}-{offset + _PAGE - 1}',
                                                 'Range-Unit': 'items'})
            if status not in (200, 206):
                raise RuntimeError(f"[db] read {ns} REST {status}: {raw[:300]}")
            batch = json.loads(raw)
            for r in batch:
                if r['locale'] in loc_set:
                    out[(r['locale'], ns)][r['key_path']] = r['value']
            if len(batch) < _PAGE:
                break
            offset += _PAGE
    return out


def count_namespace(env: dict, ns: str) -> int:
    status, hdr, raw = _req(env, 'GET',
                            f"/rest/v1/app_translations?select=locale&namespace=eq.{urllib.parse.quote(ns)}",
                            extra_headers={'Prefer': 'count=exact', 'Range': '0-0',
                                           'Range-Unit': 'items'})
    if status not in (200, 206):
        raise RuntimeError(f"[db] count {ns} REST {status}: {raw[:200]}")
    cr = hdr.get('Content-Range') or hdr.get('content-range') or ''
    try:
        return int(cr.split('/')[1])
    except (IndexError, ValueError):
        return -1


# ── writes ───────────────────────────────────────────────────────────────────

def upsert_rows(env: dict, rows: list, chunk: int = 2000) -> int:
    """Chunked idempotent upsert on the (locale, namespace, key_path) unique key.
    rows: list of {'locale','namespace','key_path','value'} dicts."""
    written = 0
    for i in range(0, len(rows), chunk):
        part = rows[i:i + chunk]
        status, _, raw = _req(
            env, 'POST',
            "/rest/v1/app_translations?on_conflict=locale,namespace,key_path",
            body=part,
            extra_headers={'Prefer': 'resolution=merge-duplicates,return=minimal'},
        )
        if status not in (200, 201, 204):
            raise RuntimeError(f"[db] upsert REST {status}: {raw[:300]}")
        written += len(part)
    return written


def delete_keys(env: dict, ns: str, key_paths, locales=None) -> int:
    """Delete every row matching (namespace=ns, key_path in key_paths) across all
    locales (or only `locales` if given). One scoped DELETE per key_path — clear
    and bulletproof (key_paths are dotted identifiers; the volume per consolidate
    run is small). Returns the number of rows reported deleted.

    SAFETY: never issues a DELETE without a key_path filter — an empty key list
    is a no-op (a namespace-only DELETE would wipe the whole namespace)."""
    key_paths = [k for k in dict.fromkeys(key_paths)]  # de-dupe, preserve order
    if not key_paths:
        return 0
    loc_filter = ''
    if locales:
        loc_in = ','.join(f'"{l}"' for l in locales)
        loc_filter = f"&locale=in.({urllib.parse.quote(loc_in)})"
    deleted = 0
    for k in key_paths:
        path = (f"/rest/v1/app_translations?namespace=eq.{urllib.parse.quote(ns)}"
                f"&key_path=eq.{urllib.parse.quote(k)}{loc_filter}")
        status, _, raw = _req(env, 'DELETE', path,
                              extra_headers={'Prefer': 'return=representation'})
        if status not in (200, 204):
            raise RuntimeError(f"[db] delete {ns}.{k} REST {status}: {raw[:200]}")
        if status == 200 and raw.strip():
            try:
                deleted += len(json.loads(raw))
            except json.JSONDecodeError:
                pass
    return deleted


# ── source resolution (DB-first, JSON fallback) — shared by every i18n mode ──

def _flatten(obj, prefix=''):
    out = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            out.update(_flatten(v, f"{prefix}.{k}" if prefix else k))
    elif isinstance(obj, str):
        out[prefix] = obj
    return out


def file_flat(root, namespaces, locales) -> dict:
    """{(loc, ns): {key_path: value}} read from the committed messages JSON."""
    out = {}
    for ns in namespaces:
        for loc in locales:
            fp = Path(root) / loc / f'{ns}.json'
            out[(loc, ns)] = _flatten(json.loads(fp.read_text(encoding='utf-8'))) if fp.is_file() else {}
    return out


def resolve_source(files: bool, allow_other: bool):
    """('db', env) when prod credentials resolve; ('files', None) when --files is
    passed or no credentials exist. Never raises — a wrong-ref or missing-cred
    read degrades to the committed JSON so an unattended run_all/rotation can't
    crash. (Write paths call load_env() directly and DO treat None as fatal.)"""
    if files:
        return 'files', None
    try:
        env = load_env(allow_other=allow_other)
    except SystemExit as e:
        print(f"{e}\n  → falling back to committed JSON (--files).")
        return 'files', None
    if env is None:
        print("[i18n] no DB credentials (env / apps/web/.env.local) — reading committed JSON "
              "(== app_translations after the last build dump). Pass --files to silence.")
        return 'files', None
    return 'db', env


def flat_map(files: bool, allow_other: bool, root, namespaces, locales):
    """Returns (source_label, {(loc, ns): {key_path: value}}) from DB or files."""
    src, env = resolve_source(files, allow_other)
    if src == 'db':
        return src, fetch_flat(env, namespaces, locales)
    return src, file_flat(root, namespaces, locales)


def source_label(src: str) -> str:
    return 'app_translations (DB)' if src == 'db' else 'committed JSON (files)'


# ── self-test (read-only) ────────────────────────────────────────────────────

if __name__ == '__main__':
    # `python3 _db_translations.py` → read-only connectivity + shape probe.
    # Prints counts only; never the key or row values.
    env = load_env()
    if not env:
        raise SystemExit("[db] no credentials (env or apps/web/.env.local) — cannot probe.")
    print(f"[db] connected ref={env['ref']}")
    total = 0
    for ns in ALL_NAMESPACES:
        n = count_namespace(env, ns)
        total += max(n, 0)
        print(f"     {ns:<12} {n}")
    print(f"[db] total rows across 12 namespaces: {total}")
