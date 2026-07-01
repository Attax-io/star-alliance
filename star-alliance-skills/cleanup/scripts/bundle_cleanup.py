#!/usr/bin/env python3
# ════════════════════════════════════════════════════════════════════════
# bundle_cleanup.py — Cleanup skill `bundle` mode
# (Cloudflare / OpenNext Worker size-wall hygiene)
# ────────────────────────────────────────────────────────────────────────
# The app deploys via @opennextjs/cloudflare, which bundles ALL server/SSR
# code into one Worker script. Cloudflare validates that script against a
# hard size limit: 3 MiB gzipped on the free plan, 10 MiB on paid. Crossing
# it fails the deploy at the very last step (the build still "succeeds").
# It bit the 1.7.60 release (the members Points panel imported `recharts`
# directly, so it was server-rendered into the Worker) and had bitten once
# before (SSR worker 15.4 MiB raw / 3.2 MiB gzip).
#
# Two layers, deliberately split by cost and authority:
#
#   detect   STATIC, build-free, ALWAYS available — the cheap early warning.
#            Scans apps/web for heavy client-only libs (recharts, …) that
#            have leaked into the SSR/Worker import graph because they're
#            imported OUTSIDE the app's established `.body` + dynamic
#            ({ ssr:false }) isolation convention. Exit 2 if any violation
#            (gate-friendly). This is what would have caught CreditStatsBar.
#
#   measure  AUTHORITATIVE but build-gated — the ground truth. gzip the
#            deployed worker entry (`.open-next/worker.js`, per wrangler
#            `main`) and compare to the size wall. If the artifact is
#            absent (the routine case — nobody builds OpenNext locally),
#            DEGRADE-WITH-RECEIPTS (exit 3): say "not measured, run the
#            build", NEVER a silent "size OK".
#
# Why both: the static detector only knows the libs on HEAVY_SSR_LIBS — a
# lib not on the list can still push the Worker over. So the static scan is
# early-warning; the gzip measurement is the hard gate. The `release` mode
# runs `measure` after a build; routine `/cleanup bundle` runs `detect`.
#
# stdlib-only. Subcommands: detect | measure. Mirrors the sibling scripts
# (default_root walk-up, /tmp JSON out, exit-2-on-finding like commit_scope).
# ════════════════════════════════════════════════════════════════════════

import argparse
import gzip
import json
import os
import re
import sys
from pathlib import Path


def default_root() -> str:
    """Locate the lex_council/ monorepo root, machine-independently.

    Walk-up pattern copied from the sibling cleanup scripts (default_root):
      1. CLEANUP_LEX_ROOT env override.
      2. Walk up from cwd looking for `lex_council/apps/web/lib/view-registry.ts`.
      3. Walk up looking for `apps/web/lib/view-registry.ts` directly.
    Falls back to the legacy hard-coded path so import never dies.
    """
    env = os.environ.get("CLEANUP_LEX_ROOT")
    if env:
        return str(Path(env).resolve())
    anchor = Path("apps") / "web" / "lib" / "view-registry.ts"
    cwd = Path.cwd().resolve()
    for parent in [cwd, *cwd.parents]:
        cand = parent / "lex_council"
        if (cand / anchor).is_file():
            return str(cand.resolve())
        if (parent / anchor).is_file():
            return str(parent.resolve())
    return os.path.expanduser("~/Documents/Claude/Projects/Lex Council App/lex_council")


LEX_ROOT = default_root()
WEB = Path(LEX_ROOT) / "apps" / "web"

# ── Heavy client-only libraries that must NEVER enter the SSR/Worker bundle.
# SEED, not a guarantee — a lib not listed here can still bloat the Worker,
# which is why `measure` (the gzip gate) is the ground truth. recharts is the
# proven offender (bit 1.7.60 + an earlier release). Add more as they surface
# (charting / pdf / spreadsheet libs are the usual suspects), but only ones
# that are genuinely client-only and heavy — over-seeding causes false flags.
HEAVY_SSR_LIBS = {
    "recharts",
}

# The app's isolation convention (see the admin analytics charts): a heavy lib
# lives ONLY in a `*.body.tsx` file, whose same-dir sibling `*.tsx` is a thin
# `dynamic(() => import('./X.body'), { ssr: false })` wrapper. recharts then
# loads client-only and never enters the @opennextjs/cloudflare worker bundle.
WORKER_ENTRY = WEB / ".open-next" / "worker.js"  # wrangler.jsonc `main`
FREE_LIMIT = 3 * 1024 * 1024
PAID_LIMIT = 10 * 1024 * 1024


def _paid_plan_signal():
    """Project-scoped Workers-Paid signal so `measure` uses the 10 MiB wall without a
    remembered flag. FREE stays the default for any project lacking the signal. Order:
    env CF_WORKERS_PAID truthy, then a `.cloudflare-paid` marker at the web dir or any
    ancestor up to 3 levels (repo root)."""
    v = os.environ.get("CF_WORKERS_PAID", "").strip().lower()
    if v in {"1", "true", "yes", "on"}:
        return "env CF_WORKERS_PAID"
    d = WEB
    for _ in range(4):
        if (d / ".cloudflare-paid").exists():
            return str(d / ".cloudflare-paid")
        d = d.parent
    return None


SKIP_DIRS = {"node_modules", ".next", ".open-next", ".turbo", "dist", "__tests__", "__pycache__"}
SRC_EXT = (".tsx", ".ts")

# `from 'x'` / `from "x"`  OR  `import('x')` / `import("x")`  — the module
# specifier only. A multi-line import block still puts the `from` clause on its
# own line, so a line scan catches it. We match the IMPORT, never a substring —
# a comment mentioning "recharts" (the Skeleton / activity page) is NOT a hit.
SPEC_RE = re.compile(r"""(?:\bfrom|\bimport\s*\()\s*['"]([^'"]+)['"]""")
SSR_FALSE_RE = re.compile(r"ssr\s*:\s*false")
# `dynamic(` OR `dynamic<Props>(` — the generic form is common (typed wrappers).
DYNAMIC_RE = re.compile(r"\bdynamic\s*(?:<[^>]*>)?\s*\(")
# Floor below which a worker.js is not a real OpenNext build (empty/stale
# placeholder) — measuring it would give a false "under the wall".
MIN_PLAUSIBLE_WORKER = 50 * 1024


def iter_src_files(scope: Path):
    for dirpath, dirnames, filenames in os.walk(scope):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if fn.endswith(SRC_EXT) and not fn.endswith((".test.tsx", ".test.ts", ".d.ts")):
                yield Path(dirpath) / fn


def body_stem(name: str):
    """'CreditStatsBar.body.tsx' -> 'CreditStatsBar' ; else None."""
    for ext in SRC_EXT:
        if name.endswith(".body" + ext):
            return name[: -len(".body" + ext)]
    return None


def wrapper_isolates(wrapper_path: Path, body_basename: str) -> bool:
    """True if `wrapper_path` is a proper dynamic({ssr:false}) wrapper that
    imports `./<body_basename>` (the `.body` sibling) — i.e. real isolation."""
    try:
        txt = wrapper_path.read_text(encoding="utf-8")
    except OSError:
        return False
    if not (DYNAMIC_RE.search(txt) and SSR_FALSE_RE.search(txt)):
        return False
    # the dynamic import must reference this body module
    return bool(re.search(r"['\"][^'\"]*\b" + re.escape(body_basename) + r"\.body['\"]", txt))


def detect(scope: Path):
    """Static scan → list of violations. Three kinds:
      direct-heavy-import          a non-`.body` file imports a heavy lib directly
                                   (it is therefore server-rendered into the Worker)
      broken-isolation             a `*.body` file imports a heavy lib, but its
                                   sibling wrapper is missing or lacks ssr:false
      body-imported-outside-wrapper a `*.body` module is imported by something
                                   other than its own ssr:false wrapper (re-enters SSR
                                   even though the naming looks correct)
    """
    violations = []

    # cache file text + parsed specifiers
    parsed = {}  # path -> (text, [(lineno, spec)])
    for f in iter_src_files(scope):
        try:
            text = f.read_text(encoding="utf-8")
        except OSError:
            continue
        specs = []
        for i, line in enumerate(text.splitlines(), 1):
            for m in SPEC_RE.finditer(line):
                specs.append((i, m.group(1)))
        parsed[f] = (text, specs)

    for f, (text, specs) in parsed.items():
        stem = body_stem(f.name)

        # (A/B) heavy-lib imports in this file
        for lineno, spec in specs:
            lib = spec.split("/")[0] if not spec.startswith("@") else "/".join(spec.split("/")[:2])
            if lib not in HEAVY_SSR_LIBS:
                continue
            if stem is None:
                # non-body file imports a heavy lib directly → SSR'd into Worker
                violations.append({
                    "file": str(f.relative_to(LEX_ROOT)),
                    "line": lineno,
                    "lib": lib,
                    "kind": "direct-heavy-import",
                    "recipe": (
                        f"Split into {f.stem}.body{f.suffix} (move this impl, keep the "
                        f"'use client' + {lib} import) + a thin {f.name} that does "
                        f"dynamic(() => import('./{f.stem}.body'), {{ ssr: false, loading: ... }}). "
                        f"Mirror the admin charts (FileHealth / TaskCompletionTrend / "
                        f"TasksSummaryCard). Keep the same default export name + a "
                        f"height-reserved loading placeholder to avoid layout shift."
                    ),
                })
            else:
                # body file — confirm its sibling wrapper actually isolates it
                sibling = f.with_name(stem + f.suffix)
                if not wrapper_isolates(sibling, stem):
                    violations.append({
                        "file": str(f.relative_to(LEX_ROOT)),
                        "line": lineno,
                        "lib": lib,
                        "kind": "broken-isolation",
                        "recipe": (
                            f"Heavy lib lives in {f.name} but its sibling wrapper "
                            f"{stem}{f.suffix} is missing or lacks `ssr: false`. Make "
                            f"{stem}{f.suffix} a dynamic(() => import('./{stem}.body'), "
                            f"{{ ssr: false }}) wrapper so {lib} stays client-only."
                        ),
                    })

        # (C) does this file import a `*.body` module it shouldn't?
        for lineno, spec in specs:
            if ".body" not in spec:
                continue
            target = spec.split("/")[-1]  # e.g. 'CreditStatsBar.body'
            if not target.endswith(".body"):
                continue
            tstem = target[: -len(".body")]
            # the only legitimate importer is the sibling ssr:false wrapper
            is_sibling_wrapper = (f.stem == tstem) and DYNAMIC_RE.search(text) and SSR_FALSE_RE.search(text)
            if not is_sibling_wrapper:
                violations.append({
                    "file": str(f.relative_to(LEX_ROOT)),
                    "line": lineno,
                    "lib": target,
                    "kind": "body-imported-outside-wrapper",
                    "recipe": (
                        f"`{target}` should only be imported by its own "
                        f"dynamic({{ssr:false}}) wrapper ({tstem}.tsx). Importing it "
                        f"here re-introduces it (and its heavy deps) to the SSR/Worker "
                        f"bundle. Import the wrapper ({tstem}) instead, or route through "
                        f"a dynamic({{ ssr:false }}) import."
                    ),
                })

    violations.sort(key=lambda v: (v["kind"], v["file"], v["line"]))
    return violations


def cmd_detect(args):
    scope = Path(args.scope).resolve() if args.scope else WEB
    if not scope.exists():
        print(f"✗ scope not found: {scope}", file=sys.stderr)
        return 1
    violations = detect(scope)
    out = {
        "generated_for": str(scope),
        "lex_root": LEX_ROOT,
        "heavy_ssr_libs": sorted(HEAVY_SSR_LIBS),
        "convention": ".body.tsx impl + dynamic(() => import('./X.body'), { ssr: false }) wrapper",
        "violation_count": len(violations),
        "violations": violations,
    }
    Path(args.out).write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")

    by_kind = {}
    for v in violations:
        by_kind.setdefault(v["kind"], []).append(v)
    print(f"── bundle detect — heavy libs {sorted(HEAVY_SSR_LIBS)} — scope {scope.relative_to(LEX_ROOT) if scope.is_relative_to(LEX_ROOT) else scope}")
    if not violations:
        print("✓ 0 violations — every heavy-lib importer is behind the .body + dynamic({ssr:false}) convention.")
        print("  (Static scan only — the gzip Worker size is the ground truth; run `measure` after a build.)")
        print(f"  → {args.out}")
        return 0
    print(f"✗ {len(violations)} violation(s) — heavy code leaking into the SSR/Worker bundle:\n")
    for kind, items in by_kind.items():
        print(f"  [{kind}] × {len(items)}")
        for v in items:
            print(f"    {v['file']}:{v['line']}  ({v['lib']})")
            print(f"        ↳ {v['recipe']}")
        print()
    print(f"  → {args.out}")
    return 2  # gate-friendly: non-zero on finding


def cmd_measure(args):
    paid_signal = None if args.paid else _paid_plan_signal()
    paid = args.paid or bool(paid_signal)
    limit = PAID_LIMIT if paid else FREE_LIMIT
    plan = "paid (10 MiB)" if paid else "free (3 MiB)"
    paid_source = ("--paid flag" if args.paid else paid_signal) if paid else None
    result = {"worker_entry": str(WORKER_ENTRY), "plan": plan, "limit_bytes": limit, "paid_source": paid_source}

    # DEGRADE WITH RECEIPTS — never a silent "OK" (skill lesson L28). Both an
    # absent artifact AND an implausibly small one (a 0-byte / stale placeholder)
    # degrade: measuring an empty worker.js would falsely report "under the wall".
    raw_probe = WORKER_ENTRY.read_bytes() if WORKER_ENTRY.exists() else None
    if raw_probe is None or len(raw_probe) < MIN_PLAUSIBLE_WORKER:
        result["status"] = "not-measured"
        if raw_probe is None:
            result["reason"] = "no .open-next/worker.js — OpenNext not built locally"
            print("⚠ NOT MEASURED — no built worker artifact.")
        else:
            result["reason"] = f"worker.js is only {len(raw_probe)} bytes — stale/empty placeholder, not a real build"
            print(f"⚠ NOT MEASURED — worker.js is only {len(raw_probe)} bytes (stale/empty placeholder, not a real build).")
        Path(args.out).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(f"   Expected a freshly-built: {WORKER_ENTRY}")
        print("   Build it first, then re-run:")
        print("     cd lex_council/apps/web && npx opennextjs-cloudflare build")
        print(f"     python3 {sys.argv[0]} measure" + (" --paid" if args.paid else ""))
        print("   (The static `detect` scan is build-free and ran regardless.)")
        return 3

    raw = WORKER_ENTRY.read_bytes()
    gz = gzip.compress(raw, 9)
    raw_mib, gz_mib, lim_mib = len(raw) / 1048576, len(gz) / 1048576, limit / 1048576
    mtime = __import__("datetime").datetime.fromtimestamp(WORKER_ENTRY.stat().st_mtime).isoformat(timespec="seconds")
    over = len(gz) > limit
    result.update({
        "status": "over-limit" if over else "ok",
        "worker_mtime": mtime,
        "raw_bytes": len(raw), "gzip_bytes": len(gz),
        "raw_mib": round(raw_mib, 2), "gzip_mib": round(gz_mib, 2),
    })
    Path(args.out).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")

    print(f"── bundle measure — {WORKER_ENTRY.name} (built {mtime}) — {plan} plan")
    if paid_source and not args.paid:
        print(f"   (paid 10 MiB wall auto-selected via {paid_source})")
    print(f"   raw {raw_mib:.2f} MiB · gzip {gz_mib:.2f} MiB · limit {lim_mib:.0f} MiB")
    if over:
        print(f"✗ OVER the {lim_mib:.0f} MiB Worker wall by {gz_mib - lim_mib:.2f} MiB — deploy will FAIL validation.")
        print("   Fix: run `detect` to find unisolated heavy libs, then split them to .body + dynamic({ssr:false}).")
        print("   (Authoritative number is wrangler's deploy 'Total Upload … gzip:' line; this gzips wrangler `main`.)")
        return 2
    print(f"✓ under the wall ({lim_mib - gz_mib:.2f} MiB headroom).")
    print("   (Authoritative number is wrangler's deploy 'gzip:' line; rebuild if the artifact is stale.)")
    return 0


def main():
    p = argparse.ArgumentParser(description="Cloudflare/OpenNext Worker size hygiene (cleanup `bundle` mode).")
    sub = p.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("detect", help="static scan for heavy libs leaking into the SSR/Worker bundle (build-free)")
    d.add_argument("--scope", help="dir to scan (default apps/web)")
    d.add_argument("--out", default="/tmp/bundle_violations.json")
    d.set_defaults(fn=cmd_detect)

    m = sub.add_parser("measure", help="gzip the built worker entry vs the Cloudflare size wall (build-gated)")
    m.add_argument("--paid", action="store_true", help="force the 10 MiB paid-plan limit (else: free 3 MiB, or auto-paid when CF_WORKERS_PAID / a .cloudflare-paid marker is present)")
    m.add_argument("--out", default="/tmp/bundle_size.json")
    m.set_defaults(fn=cmd_measure)

    args = p.parse_args()
    sys.exit(args.fn(args))


if __name__ == "__main__":
    main()
