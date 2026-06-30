#!/usr/bin/env python3
"""
run_all.py — `run all cleanups` orchestrator for the /cleanup skill (R7).

Runs the LOCAL hygiene modes detect-only, then merges every mode's /tmp/*.json
into ONE ranked triage dashboard (/tmp/cleanup_triage.md) with a severity ladder
+ a per-mode "last-run age" line. This is the "what's drifted" report.

Subcommands:
  run           Run each local mode's detect(+classify), then merge → triage report.
  report        Merge whatever /tmp/*.json already exists (no re-run). Fast.

Flags:
  --fast        Skip the two slowest modes (lint ESLint run, consolidate-code 815-file walk).

NOT run here (need their own entry points):
  - postgres  → needs Claude to run the MCP get_advisors/execute_sql first; this
                orchestrator only READS existing /tmp/pg_*.json (run `/cleanup postgres`).
  - language/consolidate APPLY → those MUTATE files; orchestrator is detect-only.

Severity ladder (sort key for the dashboard):
  CRITICAL  security / guaranteed-break  (postgres schema-campaign, lint missing-view-registry-key)
  HIGH      actionable bug / mechanical  (errors code-bug, lint architectural, consolidate-code T1)
  MED       drift to triage              (docs orphans/retired-names, consolidate-code T2, i18n untranslated, followups doable)
  LOW       advisory / informational     (docs code-link, docs broken-wikilink, i18n window.confirm)
"""

import json
import os
import sys
import subprocess
import time
from pathlib import Path


# ── root detection (matches the other scripts' walk-up) ──────────────────────

def default_root():
    starts = [Path(__file__).resolve().parent, Path.cwd().resolve()]
    seen = set()
    for start in starts:
        for parent in [start, *start.parents]:
            if parent in seen:
                continue
            seen.add(parent)
            if (parent / "apps" / "web" / "config" / "app.config.ts").is_file():
                return str(parent)
            cand = parent / "lex_council"
            if (cand / "apps" / "web" / "config" / "app.config.ts").is_file():
                return str(cand)
    return os.path.expanduser("~/Documents/Claude/Projects/Lex Council App/lex_council")


LEX_ROOT = default_root()
SCRIPTS = Path(__file__).resolve().parent
TRIAGE_MD = "/tmp/cleanup_triage.md"

SEV_ORDER = {"CRITICAL": 0, "HIGH": 1, "MED": 2, "LOW": 3}
SEV_MARK = {"CRITICAL": "⛔", "HIGH": "🚩", "MED": "•", "LOW": "·"}


# ── helpers ──────────────────────────────────────────────────────────────────

def load_json(path):
    """Read a /tmp JSON; return None on any failure (missing / malformed)."""
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return None


def run_mode(script, args, timeout):
    """Run `python3 <script> <args...>` from LEX_ROOT, best-effort. Returns (ok, tail)."""
    try:
        r = subprocess.run(
            [sys.executable, str(SCRIPTS / script)] + args,
            cwd=LEX_ROOT, capture_output=True, text=True, timeout=timeout,
        )
        return r.returncode == 0, (r.stdout or "")[-400:]
    except subprocess.TimeoutExpired:
        return False, f"[timeout >{timeout}s]"
    except Exception as e:
        return False, f"[error: {e}]"


def age_str(path):
    """Human age of a file's mtime, or 'never'."""
    try:
        secs = time.time() - os.path.getmtime(path)
    except OSError:
        return "never"
    if secs < 90:
        return "just now"
    if secs < 5400:
        return f"{int(secs // 60)}m ago"
    if secs < 172800:
        return f"{int(secs // 3600)}h ago"
    return f"{int(secs // 86400)}d ago"


# ── per-mode finding extractors (defensive; each returns a list of findings) ──
# finding = {"mode", "sev", "title", "count", "drill"}  (drill = /tmp path to inspect)

def f_lint():
    out = []
    vr = load_json("/tmp/lint_view_registry.json")
    if isinstance(vr, dict) and vr.get("missing_count", 0) > 0:
        out.append({"mode": "lint", "sev": "CRITICAL",
                    "title": f"{vr['missing_count']} VIEWS.<key> usage(s) missing from view-registry.ts (guaranteed TS2304)",
                    "count": vr["missing_count"], "drill": "/tmp/lint_view_registry.json"})
    cls = load_json("/tmp/lint_issues_classified.json")
    if isinstance(cls, list):
        arch = [i for i in cls if i.get("tier") == "architectural"]
        fix = [i for i in cls if i.get("tier") == "auto-fixable"]
        if arch:
            out.append({"mode": "lint", "sev": "HIGH",
                        "title": f"{len(arch)} architectural lint violation(s) — campaign candidates",
                        "count": len(arch), "drill": "/tmp/lint_issues_classified.json"})
        if fix:
            out.append({"mode": "lint", "sev": "MED",
                        "title": f"{len(fix)} auto-fixable lint issue(s) — run `/cleanup lint`",
                        "count": len(fix), "drill": "/tmp/lint_issues_classified.json"})
    return out


def f_docs():
    out = []
    orphans = load_json("/tmp/docs_orphans.json")
    n = len(orphans) if isinstance(orphans, list) else (orphans or {}).get("orphans") if isinstance(orphans, dict) else None
    if isinstance(orphans, dict):
        lst = orphans.get("orphans") or orphans.get("orphan_vault_logs") or []
        n = len(lst) if isinstance(lst, list) else None
    if n:
        out.append({"mode": "docs", "sev": "MED", "title": f"{n} vault-log(s) missing from INDEX.md",
                    "count": n, "drill": "/tmp/docs_orphans.json"})
    rn = load_json("/tmp/docs_retired_names.json")
    if isinstance(rn, (list, dict)):
        total = len(rn) if isinstance(rn, list) else sum(len(v) for v in rn.values() if isinstance(v, list))
        if total:
            out.append({"mode": "docs", "sev": "MED",
                        "title": f"{total} retired-name occurrence(s) in docs (triage — some legit history)",
                        "count": total, "drill": "/tmp/docs_retired_names.json"})
    wl = load_json("/tmp/docs_wikilinks.json")
    if isinstance(wl, dict):
        broken = wl.get("broken_count")
        if broken is None and isinstance(wl.get("broken"), list):
            broken = len(wl["broken"])
        if broken:
            out.append({"mode": "docs", "sev": "LOW", "title": f"{broken} broken .md wikilink(s)",
                        "count": broken, "drill": "/tmp/docs_wikilinks.json"})
    drift = load_json("/tmp/docs_campaign_drift.json")
    if isinstance(drift, list) and drift:
        out.append({"mode": "docs", "sev": "MED",
                    "title": f"{len(drift)} campaign(s) marked in-progress but vault-logged",
                    "count": len(drift), "drill": "/tmp/docs_campaign_drift.json"})
    return out


def f_consolidate_code():
    out = []
    cls = load_json("/tmp/consolidate_code_classified.json")
    if isinstance(cls, dict):
        t1 = cls.get("T1") or cls.get("t1") or []
        t2 = cls.get("T2") or cls.get("t2") or []
        if isinstance(t1, list) and t1:
            out.append({"mode": "consolidate-code", "sev": "HIGH",
                        "title": f"{len(t1)} T1 extract-now candidate(s) (mechanical codemod)",
                        "count": len(t1), "drill": "/tmp/consolidate_code_classified.json"})
        if isinstance(t2, list) and t2:
            out.append({"mode": "consolidate-code", "sev": "MED",
                        "title": f"{len(t2)} T2 needs-campaign candidate(s)",
                        "count": len(t2), "drill": "/tmp/consolidate_code_classified.json"})
    return out


def f_errors():
    out = []
    cls = load_json("/tmp/dev_errors_classified.json")
    if isinstance(cls, list):
        bugs = [e for e in cls if e.get("class") == "code-bug" or e.get("tier") == "code-bug"]
        if bugs:
            out.append({"mode": "errors", "sev": "HIGH", "title": f"{len(bugs)} code-bug(s) in the dev log",
                        "count": len(bugs), "drill": "/tmp/dev_errors_classified.json"})
    return out


def f_i18n():
    out = []
    total = 0
    for loc in ("ar", "es", "fr", "ru", "zh"):
        arr = load_json(f"/tmp/translation_targets_{loc}.json")
        if isinstance(arr, list):
            total += len(arr)
    if total:
        out.append({"mode": "language", "sev": "MED", "title": f"{total} untranslated key(s) across non-EN locales",
                    "count": total, "drill": "/tmp/translation_targets_*.json"})
    wc = load_json("/tmp/i18n_window_confirm.json")
    if isinstance(wc, list) and wc:
        out.append({"mode": "language", "sev": "LOW",
                    "title": f"{len(wc)} window.confirm() call(s) — untranslatable i18n debt",
                    "count": len(wc), "drill": "/tmp/i18n_window_confirm.json"})
    return out


def f_postgres():
    out = []
    cls = load_json("/tmp/pg_issues_classified.json") or load_json("/tmp/pg_issues.json")
    if isinstance(cls, list):
        camp = [i for i in cls if i.get("tier") == "schema-campaign"]
        fix = [i for i in cls if i.get("tier") == "advisory-auto-fix"]
        if camp:
            out.append({"mode": "postgres", "sev": "CRITICAL",
                        "title": f"{len(camp)} schema-campaign DB issue(s) (RLS/security/stale-fn)",
                        "count": len(camp), "drill": "/tmp/pg_issues_classified.json"})
        if fix:
            out.append({"mode": "postgres", "sev": "HIGH",
                        "title": f"{len(fix)} advisory-auto-fix DB issue(s) (e.g. missing FK index)",
                        "count": len(fix), "drill": "/tmp/pg_issues_classified.json"})
    return out


def f_followups():
    out = []
    cls = load_json("/tmp/followup_classified.json")
    if isinstance(cls, (list, dict)):
        items = cls if isinstance(cls, list) else cls.get("items", [])
        doable = [i for i in items if isinstance(i, dict) and "doable" in str(i.get("class", "")).lower()]
        if doable:
            out.append({"mode": "followups", "sev": "MED",
                        "title": f"{len(doable)} doable follow-up(s) from the last closed campaign",
                        "count": len(doable), "drill": "/tmp/followup_classified.json"})
    return out


def f_leaks():
    out = []
    d = load_json("/tmp/i18n_leaks.json")
    if isinstance(d, dict):
        en = d.get("en_absent") or []
        if en:
            out.append({"mode": "leaks", "sev": "HIGH",
                        "title": f"{len(en)} i18n key(s) used in code but ABSENT from EN (render as raw key-path)",
                        "count": len(en), "drill": "/tmp/i18n_leaks.json"})
        la = d.get("locale_absent") or {}
        tot = sum(len(v) for v in la.values()) if isinstance(la, dict) else 0
        if tot:
            out.append({"mode": "leaks", "sev": "MED",
                        "title": f"{tot} key(s) in EN but missing from a non-EN locale (raw in that locale)",
                        "count": tot, "drill": "/tmp/i18n_leaks.json"})
    return out


def f_bundle():
    out = []
    d = load_json("/tmp/bundle_violations.json")
    if isinstance(d, dict):
        n = d.get("violation_count") or 0
        if n:
            out.append({"mode": "bundle", "sev": "HIGH",
                        "title": f"{n} heavy lib(s) leaking into the SSR/Worker bundle (Cloudflare 3 MiB deploy-wall risk)",
                        "count": n, "drill": "/tmp/bundle_violations.json"})
    return out


EXTRACTORS = [f_postgres, f_lint, f_errors, f_consolidate_code, f_docs, f_i18n, f_leaks, f_bundle, f_followups]

# (mode-label, script, [argv per stage], timeout-seconds, skip-when-fast)
RUNS = [
    ("docs",             "docs_cleanup.py",        [["all"]],                          90,  False),
    ("errors",           "errors_cleanup.py",      [["detect"], ["classify"]],         60,  False),
    ("language",         "i18n_cleanup.py",        [["detect"]],                       90,  False),
    ("consolidate-code", "consolidate_code.py",    [["scan"], ["classify"]],          150,  True),
    ("lint",             "lint_cleanup.py",        [["detect"], ["classify"]],        180,  True),
    ("leaks",            "i18n_extract.py",        [["leaks"]],                       120,  False),
    ("bundle",           "bundle_cleanup.py",      [["detect"]],                       60,  False),
]

LAST_RUN_PROBE = {
    "postgres": "/tmp/pg_issues_classified.json",
    "lint": "/tmp/lint_issues.json",
    "errors": "/tmp/dev_errors.json",
    "consolidate-code": "/tmp/consolidate_code_scan.json",
    "docs": "/tmp/docs_orphans.json",
    "language": "/tmp/translation_targets_fr.json",
    "leaks": "/tmp/i18n_leaks.json",
    "bundle": "/tmp/bundle_violations.json",
    "followups": "/tmp/followup_classified.json",
}


# ── subcommands ──────────────────────────────────────────────────────────────

def do_runs(fast):
    print(f"run_all.py — orchestrating local hygiene modes (root: {LEX_ROOT})")
    if fast:
        print("  --fast: skipping lint + consolidate-code (slowest)")
    for label, script, stages, timeout, slow in RUNS:
        if fast and slow:
            print(f"  [skip] {label} (--fast)")
            continue
        per = max(20, timeout // max(1, len(stages)))
        ok_all = True
        for argv in stages:
            ok, tail = run_mode(script, argv, per)
            ok_all = ok_all and ok
        print(f"  {'✓' if ok_all else '⚠'} {label}  ({' '.join(' '.join(s) for s in stages)})")
    print("  [note] postgres needs MCP — run `/cleanup postgres` separately; merging any existing pg JSON.")


def build_report():
    findings = []
    for ex in EXTRACTORS:
        try:
            findings.extend(ex())
        except Exception as e:
            findings.append({"mode": ex.__name__, "sev": "LOW",
                             "title": f"[extractor error: {e}]", "count": 0, "drill": ""})
    findings.sort(key=lambda f: (SEV_ORDER.get(f["sev"], 9), -f.get("count", 0)))

    lines = ["# Cleanup triage — combined drift report", ""]
    if not findings:
        lines.append("✓ No drift surfaced by the modes that have run. (Run `run` first, or per-mode.)")
    else:
        lines.append("| sev | mode | finding | drill-down |")
        lines.append("|---|---|---|---|")
        for f in findings:
            lines.append(f"| {SEV_MARK[f['sev']]} {f['sev']} | {f['mode']} | {f['title']} | `{f['drill']}` |")
    lines += ["", "## Mode last-run age", ""]
    for mode, probe in LAST_RUN_PROBE.items():
        lines.append(f"- **{mode}** — {age_str(probe)}")
    lines += ["", "> Severity ladder: CRITICAL (security/guaranteed-break) → HIGH (actionable) → "
              "MED (triage) → LOW (advisory). postgres + language-apply are NOT auto-run here.", ""]

    report = "\n".join(lines)
    with open(TRIAGE_MD, "w") as f:
        f.write(report)
    print(report)
    print(f"\n→ {TRIAGE_MD}")
    return findings


def cmd_run():
    do_runs(fast="--fast" in sys.argv)
    print()
    build_report()


def cmd_report():
    build_report()


COMMANDS = {"run": cmd_run, "report": cmd_report}

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "run"
    if cmd not in COMMANDS:
        print(f"Usage: python3 run_all.py <{'|'.join(COMMANDS)}> [--fast]")
        print(__doc__)
        sys.exit(1)
    COMMANDS[cmd]()
