#!/usr/bin/env python3
"""
lint_cleanup.py — ESLint + TypeScript cleanup for the /cleanup skill.

Subcommands:
  baseline  Snapshot current ESLint issues to /tmp/lint_baseline.json (L11).
            Run this at session start, BEFORE any campaign edits. `verify` then
            reports "N new on touched files (M pre-existing suppressed)" instead
            of a raw count. Additive — does not touch the detect/classify chain.
  detect    Run `npm run lint -- --format json` from lex_council/, parse output,
            write /tmp/lint_issues.json (one entry per unique error). Also runs
            the view-registry cross-check (L19) and writes the missing-key
            verdict into /tmp/lint_view_registry.json + the architectural tier
            of /tmp/lint_issues.json.
  classify  Read /tmp/lint_issues.json, classify each error as:
              auto-fixable    ESLint --fix can resolve it (formatting, imports, simple rules)
              architectural   Structural issue needing manual review (circular dep, wrong path)
              wip-noise       Pre-existing in a file the current campaign didn't touch
              unknown         No classification matched
            Output: /tmp/lint_issues_classified.json
  apply     Run eslint --fix on auto-fixable issues. Then run tsc to verify.
            Output: /tmp/lint_apply_report.json
  verify    Re-run lint after fixes; report delta vs /tmp/lint_issues.json.
            If /tmp/lint_baseline.json exists, report new-vs-suppressed split
            scoped to git-touched files (L11).
  surface   Print human-readable triage list from /tmp/lint_issues_classified.json.

The project enforces --max-warnings 0, so warnings count as errors.

Two supplementary checks (additive, do not affect SAFE_FIXABLE_RULES / classify):
  - L19 view-registry cross-check: every `VIEWS.<key>` used under apps/web/ must
    be a key in apps/web/lib/view-registry.ts, or it is a guaranteed TS2304
    `Cannot find name 'VIEWS'` / TS2339 break. Surfaced as its own
    "missing-view-registry-key" bucket in the architectural tier.
  - L11 baseline-delta: scope the post-edit warning count to git-touched files so
    pre-existing project-wide warnings do not create false-alarm fatigue.
"""

import json
import sys
import os
import subprocess
import re
from collections import defaultdict
from pathlib import Path

# ── constants ──────────────────────────────────────────────────────────────

ISSUES_FILE     = "/tmp/lint_issues.json"
CLASSIFIED_FILE = "/tmp/lint_issues_classified.json"
APPLY_REPORT    = "/tmp/lint_apply_report.json"
BASELINE_FILE   = "/tmp/lint_baseline.json"
VIEW_REGISTRY_FILE = "/tmp/lint_view_registry.json"


def default_root() -> str:
    """Locate the lex_council/ monorepo root, machine-independently.

    Walk-up pattern copied from scripts/i18n_cleanup.py (default_root). Resolves
    in this order:
      1. CLEANUP_LEX_ROOT env override.
      2. Walk up from cwd looking for a `lex_council/apps/web/lib/view-registry.ts`
         anchor (handles running from the workspace root).
      3. Walk up looking for `apps/web/lib/view-registry.ts` directly
         (handles running from inside lex_council/ itself).
    Falls back to the legacy hard-coded path if nothing is found, so the script
    never crashes at import time — callers surface a clear error instead.
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
    # Legacy fallback (pre-resilience hard-coded path) — kept so import never dies.
    return os.path.expanduser(
        "~/Documents/Claude/Projects/Lex Council App/lex_council"
    )


LEX_ROOT = default_root()

# ESLint rules where --fix is always safe (pure mechanical fixes)
SAFE_FIXABLE_RULES = {
    # Import ordering / unused imports
    "import/order",
    "import/no-duplicates",
    "no-duplicate-imports",
    # TypeScript auto-fixable
    "@typescript-eslint/no-extra-semi",
    "@typescript-eslint/prefer-as-const",
    "@typescript-eslint/no-inferrable-types",
    # React
    "react/jsx-boolean-value",
    "react/self-closing-comp",
    # General
    "no-extra-semi",
    "prefer-const",
    "no-var",
    "eol-last",
    "no-trailing-spaces",
    "semi",
    "quotes",
    "comma-dangle",
    "indent",
    "key-spacing",
    "object-curly-spacing",
    "space-before-function-paren",
    "arrow-spacing",
    "space-infix-ops",
    "space-before-blocks",
    "keyword-spacing",
    "no-multiple-empty-lines",
    "padded-blocks",
    "space-in-parens",
    "array-bracket-spacing",
    "computed-property-spacing",
}

# Rules that are architectural — need manual review
ARCHITECTURAL_RULES = {
    "import/no-cycle",
    "import/no-restricted-paths",
    "no-restricted-imports",
    "no-restricted-syntax",
    "@typescript-eslint/no-explicit-any",       # usually needs a type fix
    "@typescript-eslint/explicit-module-boundary-types",
    "react-hooks/exhaustive-deps",              # often intentional
    "react-hooks/rules-of-hooks",               # always architectural
    "no-console",                               # intentional console.log = architectural
    "@next/next/no-html-link-for-pages",
    "jsx-a11y/",                               # accessibility — architectural
}

# Rules that are almost always noise in this codebase
NOISE_RULES = {
    "no-unused-vars",           # tsc handles this better; ESLint often false-positives
    "@typescript-eslint/no-unused-vars",
}


# ── helpers ────────────────────────────────────────────────────────────────

def run_lint_json(root=None):
    """Run npm run lint with JSON formatter. Returns (stdout, stderr, returncode).

    On timeout, degrades to ("", <msg>, 124) so callers (detect/baseline/verify)
    fall back to empty output instead of crashing with a traceback — the L19
    cross-check still runs because it does not depend on ESLint.
    """
    root = root or LEX_ROOT
    env = os.environ.copy()
    env["FORCE_COLOR"] = "0"
    try:
        result = subprocess.run(
            ["npx", "eslint", "--format", "json", "--ext", ".ts,.tsx",
             "apps/web", "packages"],
            cwd=root,
            capture_output=True,
            text=True,
            env=env,
            timeout=120,
        )
    except subprocess.TimeoutExpired:
        return "", "eslint timed out after 120s", 124
    return result.stdout, result.stderr, result.returncode


def run_lint_text(root=None):
    """Run npm run lint with default formatter (human-readable)."""
    root = root or LEX_ROOT
    try:
        result = subprocess.run(
            ["npm", "run", "lint", "--", "--max-warnings", "0"],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=180,
        )
    except subprocess.TimeoutExpired:
        return "npm run lint timed out after 180s", 124
    return result.stdout + result.stderr, result.returncode


def parse_eslint_json(raw_json):
    """Parse ESLint JSON output into a flat list of issues."""
    try:
        data = json.loads(raw_json)
    except json.JSONDecodeError:
        return []
    issues = []
    for file_result in data:
        filepath = file_result.get("filePath", "")
        # Make path relative to the resolved monorepo root (LEX_ROOT).
        try:
            rel = os.path.relpath(filepath, LEX_ROOT)
        except Exception:
            rel = filepath
        # Skip stale build artifacts: `.next/` carries `*.d 2.ts` duplicate
        # files that produce spurious diagnostics unrelated to source (L11).
        norm = rel.replace(os.sep, "/")
        if norm.startswith(".next/") or "/.next/" in norm:
            continue
        for msg in file_result.get("messages", []):
            issues.append({
                "file": rel,
                "line": msg.get("line", 0),
                "col": msg.get("column", 0),
                "rule": msg.get("ruleId") or "syntax",
                "severity": "error" if msg.get("severity") == 2 else "warning",
                "message": msg.get("message", ""),
                "fixable": msg.get("fix") is not None,
                "suggestions": len(msg.get("suggestions", [])),
            })
    return issues


def dedupe_issues(issues):
    """Dedupe by (file, rule) to avoid counting same error 100× in one file."""
    seen = {}
    for issue in issues:
        key = (issue["file"], issue["rule"])
        if key not in seen:
            seen[key] = issue
            seen[key]["count"] = 1
        else:
            seen[key]["count"] += 1
    return list(seen.values())


# ── L19: view-registry cross-check ───────────────────────────────────────────

# Negative lookbehind: only the standalone `VIEWS` object, never a suffix of
# another identifier (e.g. `LINK_VIEWS.map(` was flagged as a phantom missing
# `VIEWS.map` key when the regex had no left boundary).
VIEWS_USAGE_RE = re.compile(r"(?<![A-Za-z0-9_])VIEWS\.([a-zA-Z_][a-zA-Z0-9_]*)")
# Registry keys are object properties: `  key_name: 'value',` — capture the key.
REGISTRY_KEY_RE = re.compile(r"^\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*:")


def collect_view_usages(root=None):
    """Distinct `VIEWS.<key>` keys used across apps/web/**/*.ts(x).

    Excludes the registry file itself. Mirrors the lesson's
    `grep -oE "VIEWS\\.[a-zA-Z_]+" | grep -v view-registry | sort -u`.
    Returns (distinct_keys:set, total_callsites:int).
    """
    root = root or LEX_ROOT
    web = os.path.join(root, "apps", "web")
    keys = set()
    total = 0
    for dirpath, dirnames, filenames in os.walk(web):
        # Prune build/dep dirs so we only scan source.
        dirnames[:] = [d for d in dirnames if d not in (".next", "node_modules", ".turbo")]
        for fn in filenames:
            if not (fn.endswith(".ts") or fn.endswith(".tsx")):
                continue
            if fn == "view-registry.ts":
                continue
            fp = os.path.join(dirpath, fn)
            try:
                with open(fp, "r", encoding="utf-8", errors="replace") as f:
                    text = f.read()
            except OSError:
                continue
            for m in VIEWS_USAGE_RE.finditer(text):
                keys.add(m.group(1))
                total += 1
    return keys, total


def parse_registry_keys(root=None):
    """Keys defined in apps/web/lib/view-registry.ts (the VIEWS object)."""
    root = root or LEX_ROOT
    reg_path = os.path.join(root, "apps", "web", "lib", "view-registry.ts")
    keys = set()
    if not os.path.isfile(reg_path):
        return keys
    in_views = False
    with open(reg_path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            if not in_views:
                if "VIEWS" in line and "=" in line and "{" in line:
                    in_views = True
                continue
            if line.strip().startswith("}"):
                break
            stripped = line.strip()
            if stripped.startswith("//") or stripped.startswith("*") or stripped.startswith("/*"):
                continue
            m = REGISTRY_KEY_RE.match(line)
            if m:
                keys.add(m.group(1))
    return keys


def check_view_registry(root=None):
    """L19 cross-check: usages-not-in-registry = guaranteed tsc breaks.

    comm-style set difference (usages − registry). Writes
    /tmp/lint_view_registry.json and returns the result dict.
    """
    root = root or LEX_ROOT
    usages, total_callsites = collect_view_usages(root)
    registry = parse_registry_keys(root)
    missing = sorted(usages - registry)  # comm -23: in usages, not in registry
    result = {
        "registry_key_count": len(registry),
        "distinct_usage_count": len(usages),
        "total_callsites": total_callsites,
        "missing_keys": missing,
        "missing_count": len(missing),
    }
    try:
        with open(VIEW_REGISTRY_FILE, "w") as f:
            json.dump(result, f, indent=2)
    except OSError:
        pass
    return result


def view_registry_issues(result):
    """Turn the L19 verdict into architectural-tier issue rows.

    Each missing key becomes its own "missing-view-registry-key" bucket entry so
    it shows up prominently in detect/surface/verify alongside ESLint findings.
    """
    rows = []
    for key in result.get("missing_keys", []):
        rows.append({
            "file": "apps/web/lib/view-registry.ts",
            "line": 0,
            "col": 0,
            "rule": "missing-view-registry-key",
            "severity": "error",
            "message": (
                f"VIEWS.{key} is used under apps/web/ but is NOT a key in "
                f"view-registry.ts — guaranteed TS2304 'Cannot find name VIEWS' "
                f"/ TS2339 break. Add `{key}: '{key}',` to the VIEWS object (W3)."
            ),
            "fixable": False,
            "suggestions": 0,
            "count": 1,
            "tier": "architectural",
        })
    return rows


# ── L11: baseline-delta (git-touched-file scoping) ───────────────────────────

def touched_files(root=None):
    """Repo-relative paths of modified files, per `git status --short`.

    Mirrors L11's awk: rows whose status starts with 'M' (or ' M'). Returns
    paths relative to LEX_ROOT (the git submodule root), normalised to /.
    """
    root = root or LEX_ROOT
    try:
        out = subprocess.run(
            ["git", "status", "--short"],
            cwd=root, capture_output=True, text=True, timeout=30,
        ).stdout
    except (OSError, subprocess.SubprocessError):
        return set()
    files = set()
    for line in out.splitlines():
        if len(line) < 4:
            continue
        status, path = line[:2], line[3:].strip()
        # `awk '$1 ~ /^M/ || $1 == "M"'` — staged- or worktree-modified.
        if "M" in status:
            # Handle rename arrows ("old -> new") defensively.
            if " -> " in path:
                path = path.split(" -> ", 1)[1]
            files.add(path.replace(os.sep, "/"))
    return files


def issue_key(issue):
    """Stable identity for an issue across runs (file, rule, line, col)."""
    return (issue.get("file", ""), issue.get("rule", ""),
            issue.get("line", 0), issue.get("col", 0))


# ── subcommands ────────────────────────────────────────────────────────────

def cmd_baseline():
    """L11: snapshot current ESLint issues to /tmp/lint_baseline.json.

    Run at session start, before campaign edits. `verify` reads this to split
    new-on-touched-files from pre-existing-suppressed. Does not run the L19 check
    or write ISSUES_FILE — it is a pure pre-edit photo of the lint surface.
    """
    print(f"lint_cleanup.py baseline — snapshotting lint surface (root: {LEX_ROOT})")
    stdout, stderr, rc = run_lint_json()
    if not stdout.strip():
        print("  [WARN] JSON output empty; baseline will be empty. ESLint stderr:")
        print((stderr or "")[:800])
        issues = []
    else:
        issues = dedupe_issues(parse_eslint_json(stdout))
    errors   = [i for i in issues if i["severity"] == "error"]
    warnings = [i for i in issues if i["severity"] == "warning"]
    with open(BASELINE_FILE, "w") as f:
        json.dump(issues, f, indent=2)
    print(f"  Baseline: {len(issues)} unique issues "
          f"({len(errors)} errors, {len(warnings)} warnings)")
    print(f"  Wrote → {BASELINE_FILE}")
    return issues


def cmd_detect():
    """Run ESLint JSON formatter, parse and save issues."""
    print(f"lint_cleanup.py detect — running ESLint (root: {LEX_ROOT})...")

    stdout, stderr, rc = run_lint_json()
    if not stdout.strip():
        # Fall back to text parser
        print("  [WARN] JSON output empty, trying text mode...")
        text_out, rc = run_lint_text()
        print(text_out[:2000])
        issues = []
    else:
        issues = parse_eslint_json(stdout)

    issues = dedupe_issues(issues)

    # ── L19: view-registry cross-check (highest-value tsc pre-empt) ──
    vr = check_view_registry()
    vr_rows = view_registry_issues(vr)
    if vr_rows:
        print(f"\n  🚩 VIEW-REGISTRY: {vr['missing_count']} key(s) used but NOT in "
              f"view-registry.ts — each is a guaranteed tsc break:")
        for row_key in vr["missing_keys"]:
            print(f"     VIEWS.{row_key}")
        print(f"     → add to apps/web/lib/view-registry.ts (W3). "
              f"Verdict: {VIEW_REGISTRY_FILE}")
        # Prepend so they lead the architectural tier in surface/verify.
        issues = vr_rows + issues
    else:
        print(f"\n  ✓ view-registry: {vr['distinct_usage_count']} distinct "
              f"VIEWS.<key> usages ({vr['total_callsites']} callsites) all present "
              f"in {vr['registry_key_count']} registry keys.")

    # Count per severity
    errors   = [i for i in issues if i["severity"] == "error"]
    warnings = [i for i in issues if i["severity"] == "warning"]
    print(f"  Found {len(issues)} unique issues "
          f"({len(errors)} errors, {len(warnings)} warnings)")

    with open(ISSUES_FILE, "w") as f:
        json.dump(issues, f, indent=2)
    print(f"  Wrote → {ISSUES_FILE}")
    return issues


def cmd_classify():
    """Classify each issue into a fix tier."""
    if not os.path.exists(ISSUES_FILE):
        print(f"  [ERROR] {ISSUES_FILE} not found. Run detect first.")
        sys.exit(1)
    issues = json.load(open(ISSUES_FILE))

    classified = []
    counts = defaultdict(int)

    for issue in issues:
        rule = issue.get("rule", "")
        fixable = issue.get("fixable", False)

        # Synthetic L19 rows arrive pre-tiered (architectural). Never auto-fixable.
        if rule == "missing-view-registry-key":
            tier = issue.get("tier", "architectural")
        # Explicit rule matches take precedence
        elif rule in NOISE_RULES:
            tier = "wip-noise"
        elif rule in ARCHITECTURAL_RULES or any(rule.startswith(p) for p in ARCHITECTURAL_RULES):
            tier = "architectural"
        elif fixable or rule in SAFE_FIXABLE_RULES:
            tier = "auto-fixable"
        elif rule == "syntax" or "Parsing error" in issue.get("message", ""):
            tier = "architectural"  # syntax errors need manual fix
        elif "no-unused-expressions" in rule:
            # Common trap: ternary used as statement — always architectural
            tier = "architectural"
        elif "@typescript-eslint" in rule and fixable:
            tier = "auto-fixable"
        elif "@typescript-eslint" in rule:
            tier = "architectural"
        else:
            tier = "unknown"

        issue["tier"] = tier
        classified.append(issue)
        counts[tier] += 1

    with open(CLASSIFIED_FILE, "w") as f:
        json.dump(classified, f, indent=2)

    print("\nClassification summary:")
    for tier, count in sorted(counts.items(), key=lambda x: -x[1]):
        print(f"  {tier:<20}: {count}")
    print(f"\nWrote → {CLASSIFIED_FILE}")
    return classified


def cmd_apply():
    """Run eslint --fix for auto-fixable issues, then verify with tsc."""
    if not os.path.exists(CLASSIFIED_FILE):
        print(f"  [ERROR] {CLASSIFIED_FILE} not found. Run classify first.")
        sys.exit(1)

    classified = json.load(open(CLASSIFIED_FILE))
    fixable = [i for i in classified if i.get("tier") == "auto-fixable"]

    if not fixable:
        print("  No auto-fixable issues found.")
        return []

    # Get unique files that have fixable issues
    fix_files = list(set(i["file"] for i in fixable))
    print(f"  Running eslint --fix on {len(fix_files)} files...")

    result = subprocess.run(
        ["npx", "eslint", "--fix", "--ext", ".ts,.tsx"] + fix_files,
        cwd=LEX_ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )
    print(result.stdout[:1000] if result.stdout else "  (no output)")

    # Run tsc to verify no type errors introduced
    print("\n  Running tsc check...")
    tsc_result = subprocess.run(
        ["npx", "turbo", "run", "check-types", "--filter=web", "--force"],
        cwd=LEX_ROOT,
        capture_output=True,
        text=True,
        timeout=180,
    )
    tsc_ok = tsc_result.returncode == 0
    print(f"  tsc: {'PASS' if tsc_ok else 'FAIL'}")
    if not tsc_ok:
        print(tsc_result.stdout[-1500:])

    report = {
        "fixed_files": fix_files,
        "fixable_count": len(fixable),
        "eslint_rc": result.returncode,
        "tsc_ok": tsc_ok,
        "tsc_output": tsc_result.stdout[-1500:] if not tsc_ok else "",
    }
    with open(APPLY_REPORT, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\n  Report → {APPLY_REPORT}")
    return report


def cmd_verify():
    """Re-run lint after fixes; report delta.

    Raw before/after delta vs ISSUES_FILE (unchanged behaviour), PLUS — when a
    baseline exists (L11) — the new-on-touched-files vs pre-existing-suppressed
    split that the lint mode's report MUST use instead of a raw count.
    """
    before_issues = json.load(open(ISSUES_FILE)) if os.path.exists(ISSUES_FILE) else []
    before_count = len(before_issues)

    print("lint_cleanup.py verify — re-running ESLint...")
    stdout, stderr, rc = run_lint_json()
    after_issues = dedupe_issues(parse_eslint_json(stdout))

    # Re-run the L19 cross-check so verify reflects the post-fix registry state.
    vr = check_view_registry()
    vr_rows = view_registry_issues(vr)
    after_issues = vr_rows + after_issues
    after_count = len(after_issues)

    delta = before_count - after_count
    print(f"\nVerification delta:")
    print(f"  Before : {before_count} unique issues")
    print(f"  After  : {after_count} unique issues")
    print(f"  Fixed  : {delta} (negative = new issues introduced)")

    # ── L11: baseline-delta scoped to git-touched files ──
    if os.path.exists(BASELINE_FILE):
        baseline = json.load(open(BASELINE_FILE))
        baseline_keys = {issue_key(i) for i in baseline}
        touched = touched_files()
        # New = present now, absent from baseline.
        new_all = [i for i in after_issues if issue_key(i) not in baseline_keys]
        # ESLint-side issues live in real files; the synthetic view-registry rows
        # are always campaign-relevant, so count them as "new" regardless.
        new_touched = [
            i for i in new_all
            if i.get("rule") == "missing-view-registry-key"
            or i.get("file", "").replace(os.sep, "/") in touched
        ]
        pre_existing = [i for i in after_issues if issue_key(i) in baseline_keys]
        print(f"\n  L11 baseline-delta ({len(touched)} touched file(s)):")
        print(f"    {len(new_touched)} new on campaign-touched files "
              f"({len(pre_existing)} pre-existing suppressed)")
        if new_touched:
            by_rule = defaultdict(list)
            for i in new_touched:
                by_rule[i["rule"]].append(i["file"])
            for rule, files in sorted(by_rule.items(), key=lambda x: -len(x[1]))[:15]:
                print(f"      [{rule}] × {len(files)} → {files[0]}")
    else:
        print(f"\n  [L11] No baseline at {BASELINE_FILE} — run "
              f"`lint_cleanup.py baseline` at session start for new-vs-suppressed split.")

    # Surface remaining architectural + unknown as campaign candidates
    remaining = [i for i in after_issues
                 if i.get("tier","") in ("architectural","unknown") or
                 i["rule"] in ARCHITECTURAL_RULES or
                 i["rule"] == "missing-view-registry-key"]
    if remaining:
        print(f"\n  {len(remaining)} architectural issues (campaign candidates):")
        by_rule = defaultdict(list)
        for i in remaining:
            by_rule[i["rule"]].append(i["file"])
        for rule, files in sorted(by_rule.items(), key=lambda x: -len(x[1]))[:15]:
            print(f"    [{rule}] in {len(files)} file(s): {files[0]}")


def cmd_surface():
    """Print human-readable triage list."""
    if not os.path.exists(CLASSIFIED_FILE):
        print(f"  [ERROR] {CLASSIFIED_FILE} not found. Run classify first.")
        sys.exit(1)

    classified = json.load(open(CLASSIFIED_FILE))
    tiers = defaultdict(list)
    for i in classified:
        tiers[i.get("tier","unknown")].append(i)

    print("\n" + "="*60)
    print("LINT CLEANUP TRIAGE")
    print("="*60)

    # L19 missing-view-registry keys lead the triage: each is a hard tsc break.
    vr_missing = [i for i in classified if i.get("rule") == "missing-view-registry-key"]
    if vr_missing:
        print(f"\n⛔ MISSING VIEW-REGISTRY KEYS ({len(vr_missing)} — guaranteed tsc break, fix first):")
        for i in vr_missing:
            key = i["message"].split()[0].replace("VIEWS.", "")
            print(f"  VIEWS.{key} → add to apps/web/lib/view-registry.ts (W3)")

    if tiers["auto-fixable"]:
        print(f"\n✓ AUTO-FIXABLE ({len(tiers['auto-fixable'])} issues via eslint --fix):")
        by_rule = defaultdict(int)
        for i in tiers["auto-fixable"]:
            by_rule[i["rule"]] += 1
        for rule, cnt in sorted(by_rule.items(), key=lambda x: -x[1])[:10]:
            print(f"  [{rule}] × {cnt}")

    if tiers["architectural"]:
        print(f"\n🚩 ARCHITECTURAL — needs campaign ({len(tiers['architectural'])} issues):")
        by_rule = defaultdict(list)
        for i in tiers["architectural"]:
            # missing-view-registry-key already led the triage above — don't repeat.
            if i.get("rule") == "missing-view-registry-key":
                continue
            by_rule[i["rule"]].append(i["file"])
        for rule, files in sorted(by_rule.items(), key=lambda x: -len(x[1]))[:10]:
            print(f"  [{rule}] in {len(files)} file(s)")
            for f in files[:3]:
                print(f"    {f}")

    if tiers["wip-noise"]:
        print(f"\n  wip-noise: {len(tiers['wip-noise'])} suppressed")
    if tiers["unknown"]:
        print(f"\n? UNKNOWN ({len(tiers['unknown'])} issues):")
        for i in tiers["unknown"][:5]:
            print(f"  [{i['rule']}] {i['file']}:{i['line']} — {i['message'][:80]}")

    print("="*60)


# ── main ───────────────────────────────────────────────────────────────────

COMMANDS = {
    "baseline": cmd_baseline,
    "detect": cmd_detect,
    "classify": cmd_classify,
    "apply": cmd_apply,
    "verify": cmd_verify,
    "surface": cmd_surface,
}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print(f"Usage: python3 lint_cleanup.py <{'|'.join(COMMANDS)}>")
        print(__doc__)
        sys.exit(1)
    COMMANDS[sys.argv[1]]()
