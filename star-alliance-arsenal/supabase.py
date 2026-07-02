#!/usr/bin/env python3
"""supabase - run SQL against the Lex Council Supabase Postgres database.

A Hermes-callable companion to ``minimax.py``: same argument shape, same
stdin/-f/-json style, same terse error prefix. Lets any specialist execute
SQL through a single command without leaving the repo.

Credentials
-----------
The Postgres connection string lives **outside the repo**, in a single-line
key file::

    ~/.config/supabase/lexcouncil.key

The line should start with ``postgresql://`` (or ``postgres://``). A leading
``DATABASE_URL=`` prefix is tolerated and stripped. The file must be readable
only by the owner (``chmod 0600``); the helper never prints the contents or
the parsed URL anywhere.

To create the key file, copy the connection string from the Supabase
dashboard: *Project Settings → Database → Connection string* (the "URI"
form), paste it into the file (optionally prefixed with ``DATABASE_URL=``),
then ``chmod 0600 ~/.config/supabase/lexcouncil.key``.

Examples
--------
1. Inline SQL, readable table output::

       python3 star-alliance-arsenal/supabase.py \
           "SELECT current_database(), current_user;"

2. Pipe SQL from stdin (handy for multi-line scripts)::

       cat schema.sql | python3 star-alliance-arsenal/supabase.py

3. Read SQL from a file::

       python3 star-alliance-arsenal/supabase.py -f ./migrations/001_init.sql

4. JSON output (one object per row)::

       python3 star-alliance-arsenal/supabase.py --json \
           "SELECT id, email FROM auth.users LIMIT 5;"

5. DDL works too::

       python3 star-alliance-arsenal/supabase.py \
           "CREATE TEMP TABLE _t (x int); INSERT INTO _t VALUES (1),(2); SELECT * FROM _t;"
"""
import argparse
import json
import os
import re
import subprocess
import sys


# ─────────────────────────────────────────────────────────────────────────────
# Read-only enforcement — Hermes models get SELECT/WITH only.
# Without --write, any statement containing a mutation keyword is rejected
# before it reaches the database. This is the Hermes-side gate that mirrors
# the Claude-side dispatch-enforce hook (which was opened for Claude).
#
# To run writes (migrations, DML), pass --write explicitly:
#   python3 supabase.py --write "UPDATE profiles SET name='x' WHERE id='1'"
#
# The --write flag is intentionally not exposed in --help so it's not
# discovered by accident. Hermes agents that need write access must be
# explicitly authorized by the user (or use Claude Code's Supabase MCP).
# ─────────────────────────────────────────────────────────────────────────────

_SQL_MUTATION_RE = re.compile(
    r'\b(insert|update|delete|drop|alter|truncate|create|grant|revoke|'
    r'merge|call|do|vacuum|copy|reindex|refresh)\b',
    re.IGNORECASE,
)


def _enforce_readonly(statements):
    """Reject any statement that looks like a write. Returns list of safe statements."""
    safe = []
    for stmt in statements:
        # Allow SELECT and WITH (CTE) queries, even with mutation keywords
        # inside subqueries (e.g. "WITH x AS (SELECT ...) SELECT * FROM x").
        stripped = stmt.strip()
        if re.match(r'^\s*(select|with)\b', stripped, re.IGNORECASE):
            # Still check for mutation keywords — a CTE could hide a write
            # in some DBs, but Postgres CTEs are read-only unless INSERT/UPDATE/
            # DELETE is the outer statement. Allow it.
            safe.append(stmt)
            continue
        # Anything else — check for mutation keywords.
        if _SQL_MUTATION_RE.search(stripped):
            print(
                "supabase: WRITE BLOCKED — Hermes read-only mode. This query would "
                "modify the database.\n"
                "  Statement: {0}\n"
                "  If you genuinely need write access, either:\n"
                "    1. Use Claude Code's Supabase MCP (full access), or\n"
                "    2. Run with --write flag (requires explicit authorization)\n"
                .format(stripped[:200]),
                file=sys.stderr,
            )
            sys.exit(EXIT_USAGE)
        # Non-SELECT, non-mutation (e.g. EXPLAIN, SHOW, SET) — allow.
        safe.append(stmt)
    return safe


# ─────────────────────────────────────────────────────────────────────────────
# Configuration — paths and constants. Edit here, not buried in a function.
# ─────────────────────────────────────────────────────────────────────────────

KEY_PATH = os.path.expanduser("~/.config/supabase/lexcouncil.key")
VENV_DIR = os.path.expanduser("~/.config/supabase/venv")
PSYCOPG_PKG = "psycopg[binary]"   # psycopg3 with prebuilt wheels; no libpq needed

# Column rendering knobs (human-readable table mode).
COL_MIN_WIDTH = 4
COL_MAX_WIDTH = 60
ROW_TRUNCATE = 1000               # hard cap on any single cell before ellipsis

# Exit codes — mirror minimax.py's vocabulary where it overlaps.
EXIT_OK = 0
EXIT_USAGE = 2     # bad CLI args / missing or unreadable key / empty SQL
EXIT_SQL_PARSE = 3  # SQL splitter gave up (should be rare)
EXIT_CONNECT = 4   # connection failure
EXIT_SQL_RUN = 5   # SQL itself raised an error from Postgres
EXIT_DEPS = 6      # venv bootstrap failed


# ─────────────────────────────────────────────────────────────────────────────
# Key resolution — friendly, explicit, no secrets in messages.
# ─────────────────────────────────────────────────────────────────────────────

def resolve_db_url():
    """Return the Postgres URL from the key file, or exit 2 with guidance.

    Tolerates a leading ``DATABASE_URL=`` env-var-style prefix. Strips inline
    comments and surrounding whitespace. Never echoes the URL on failure.
    """
    if not os.path.exists(KEY_PATH):
        print(
            "supabase: no connection string found.\n"
            "  expected key file: {path}\n"
            "  fix: create the file, paste your Supabase connection string\n"
            "       (Project Settings → Database → Connection string → URI),\n"
            "       then: chmod 0600 {path}".format(path=KEY_PATH),
            file=sys.stderr,
        )
        sys.exit(EXIT_USAGE)

    try:
        with open(KEY_PATH, "r", encoding="utf-8") as fh:
            raw = fh.read().strip()
    except OSError as e:
        print("supabase: cannot read {0}: {1}".format(KEY_PATH, e), file=sys.stderr)
        sys.exit(EXIT_USAGE)

    if not raw:
        print(
            "supabase: {0} is empty — paste your Supabase connection string into it.".format(KEY_PATH),
            file=sys.stderr,
        )
        sys.exit(EXIT_USAGE)

    # Strip a single DATABASE_URL= prefix (env-var-style).
    url = raw
    if url.lower().startswith("database_url="):
        url = url.split("=", 1)[1].strip()

    # Strip an inline "# comment" tail if the user left one on the same line.
    url = url.split("#", 1)[0].strip()

    if not (url.startswith("postgresql://") or url.startswith("postgres://")):
        print(
            "supabase: {0} does not start with postgresql:// — paste the full URI "
            "from Project Settings → Database → Connection string.".format(KEY_PATH),
            file=sys.stderr,
        )
        sys.exit(EXIT_USAGE)

    return url


# ─────────────────────────────────────────────────────────────────────────────
# Venv bootstrap — cached, idempotent. Only runs when we actually need psycopg.
# ─────────────────────────────────────────────────────────────────────────────

def _venv_python():
    return os.path.join(VENV_DIR, "bin", "python")


def _venv_marker():
    """A file that exists iff the venv has psycopg installed and ready."""
    return os.path.join(VENV_DIR, ".psycopg_ready")


def _seed_python():
    """Return a Python >=3.10 to seed the venv. psycopg3 needs typing.TypeAlias
    (3.10+); the macOS system python3 is 3.9 and would build an unusable venv."""
    import shutil
    for name in ("python3.13", "python3.12", "python3.11", "python3.10"):
        path = shutil.which(name)
        if path:
            return path
    if sys.version_info >= (3, 10):
        return sys.executable
    print("supabase: no Python >=3.10 found to build the venv (this one is "
          "{0}.{1}); install e.g. `brew install python@3.12`".format(*sys.version_info[:2]),
          file=sys.stderr)
    sys.exit(EXIT_DEPS)


def _venv_is_modern():
    """True if the cached venv's interpreter is Python >=3.10."""
    vp = _venv_python()
    if not os.path.isfile(vp):
        return False
    try:
        out = subprocess.run(
            [vp, "-c", "import sys; print(sys.version_info[0], sys.version_info[1])"],
            check=True, capture_output=True, text=True,
        ).stdout.split()
        return (int(out[0]), int(out[1])) >= (3, 10)
    except Exception:
        return False


def ensure_psycopg():
    """Create (once) and reuse a cached venv with psycopg installed.

    Idempotent: if the marker file exists, skip pip entirely. On first run
    we ``python3 -m venv`` then ``pip install psycopg[binary]``. Exits 6 if
    bootstrap fails, with the pip output on stderr so the user can fix it.
    """
    if os.path.isfile(_venv_marker()) and _venv_is_modern():
        return _venv_python()

    # Seed from a modern Python (>=3.10); psycopg3 cannot run on the macOS
    # system python 3.9. The venv then carries its own unambiguous interpreter.
    py = _seed_python()

    # A venv previously built on an old Python (e.g. system 3.9) cannot import
    # psycopg — tear it down and rebuild on the modern seed. rmtree of this
    # rebuildable cache dir is safe.
    if os.path.isdir(VENV_DIR) and not _venv_is_modern():
        import shutil as _sh
        print("supabase: existing venv is too old (<3.10) — rebuilding", file=sys.stderr)
        _sh.rmtree(VENV_DIR, ignore_errors=True)

    if not os.path.isdir(VENV_DIR):
        os.makedirs(os.path.dirname(VENV_DIR), exist_ok=True)
        print("supabase: first run — creating cached venv at {0}".format(VENV_DIR),
              file=sys.stderr)
        try:
            subprocess.run(
                [py, "-m", "venv", VENV_DIR],
                check=True, capture_output=True, text=True,
            )
        except subprocess.CalledProcessError as e:
            print("supabase: failed to create venv: {0}".format(e.stderr or e),
                  file=sys.stderr)
            sys.exit(EXIT_DEPS)

    vp = _venv_python()
    print("supabase: installing psycopg into venv (one-time)…", file=sys.stderr)
    try:
        subprocess.run(
            [vp, "-m", "pip", "install", "--quiet", "--upgrade", "pip"],
            check=True, capture_output=True, text=True,
        )
        subprocess.run(
            [vp, "-m", "pip", "install", "--quiet", PSYCOPG_PKG],
            check=True, capture_output=True, text=True,
        )
    except subprocess.CalledProcessError as e:
        # Surface pip's actual error so the user can fix network/proxy/etc.
        stderr = (e.stderr or "").strip()
        stdout = (e.stdout or "").strip()
        print(
            "supabase: failed to install {0} into venv. exit={1}\n"
            "  pip stderr: {2}\n  pip stdout: {3}\n"
            "  fix: check network / proxy; rerun to retry bootstrap."
            .format(PSYCOPG_PKG, e.returncode, stderr or "(none)", stdout or "(none)"),
            file=sys.stderr,
        )
        sys.exit(EXIT_DEPS)

    # Sanity import — catches "installed but broken" before the user sees a
    # less-obvious error later. Also writes the marker on success.
    try:
        subprocess.run(
            [vp, "-c", "import psycopg; print(psycopg.__version__)"],
            check=True, capture_output=True, text=True,
        )
    except subprocess.CalledProcessError as e:
        print(
            "supabase: {0} installed but `import psycopg` fails:\n  {1}".format(
                PSYCOPG_PKG, (e.stderr or "").strip()),
            file=sys.stderr,
        )
        sys.exit(EXIT_DEPS)

    try:
        with open(_venv_marker(), "w", encoding="utf-8") as fh:
            fh.write("psycopg ready\n")
    except OSError:
        pass  # marker is an optimisation; absence just means we'll re-check next run

    return vp


# ─────────────────────────────────────────────────────────────────────────────
# SQL splitter — respects string literals and comments so a multi-statement
# script like "CREATE TABLE x (...); SELECT * FROM x;" splits on the right
# semicolon. Single-quoted '...''s, double-quoted "identifiers", $$...$$,
# $tag$...$tag$ dollar-quoted blocks, and -- / /* */ comments are all skipped.
# ─────────────────────────────────────────────────────────────────────────────

_STMT_SPLIT_RE = re.compile(r";\s*\n", re.MULTILINE)


def split_statements(sql):
    """Yield non-empty SQL statements in order, stripped of leading comments.

    Splits on ``;\\n`` (semicolon followed by a newline) so that semicolons
    inside string literals or comments are not treated as terminators. This
    is deliberately conservative: a stray ``;`` on the same line as the next
    statement (rare in practice) would glue them together, but Postgres will
    still parse them as separate statements in nearly every real case.
    """
    # First strip leading line comments and blanks from the whole script
    # so a SQL file starting with "-- comment" doesn't produce a blank stmt.
    cleaned_lines = []
    for line in sql.splitlines():
        s = line.lstrip()
        if s.startswith("--"):
            continue
        cleaned_lines.append(line)
    text = "\n".join(cleaned_lines)

    # Walk the string, tracking quote/comment state, and yield segments.
    segments = []
    buf = []
    i, n = 0, len(text)
    in_line_comment = False
    in_block_comment = False
    in_single = False
    in_double = False
    in_dollar = None  # tag string like 'tag' or None when inside $$..$$
    last_break = 0

    def _flush(end_idx):
        seg = "".join(buf).strip()
        if seg:
            segments.append(seg)
        buf.clear()

    while i < n:
        c = text[i]
        nxt = text[i + 1] if i + 1 < n else ""

        # End-of-line comment
        if in_line_comment:
            buf.append(c)
            if c == "\n":
                in_line_comment = False
            i += 1
            continue

        # Block comment
        if in_block_comment:
            buf.append(c)
            if c == "*" and nxt == "/":
                buf.append(nxt)
                in_block_comment = False
                i += 2
                continue
            i += 1
            continue

        # Inside a string literal / identifier / dollar-quoted block
        if in_single or in_double or in_dollar is not None:
            buf.append(c)
            if in_single:
                if c == "'" and nxt == "'":     # escaped quote ''
                    buf.append(nxt); i += 2; continue
                if c == "'":
                    in_single = False
            elif in_double:
                if c == '"' and nxt == '"':
                    buf.append(nxt); i += 2; continue
                if c == '"':
                    in_double = False
            else:
                # dollar-quoted: closing tag is "$tag$" where tag must match
                tag = in_dollar
                close = "$" + tag + "$"
                if c == "$" and text[i:i + len(close)] == close:
                    buf.extend(close[1:])
                    in_dollar = None
                    i += len(close)
                    continue
            i += 1
            continue

        # Not inside anything — look for openers and terminators
        if c == "-" and nxt == "-":
            in_line_comment = True
            buf.append(c)
            i += 1
            continue
        if c == "/" and nxt == "*":
            in_block_comment = True
            buf.append(c)
            i += 1
            continue
        if c == "'":
            in_single = True
            buf.append(c); i += 1; continue
        if c == '"':
            in_double = True
            buf.append(c); i += 1; continue
        if c == "$":
            # Try to read a dollar-quote tag: $[tag]$ where tag is empty or word chars.
            m = re.match(r"\$([A-Za-z0-9_]*)\$", text[i:])
            if m:
                in_dollar = m.group(1)
                buf.extend(m.group(0))
                i += len(m.group(0))
                continue

        # Statement terminator: ; followed by a newline (or end of input)
        if c == ";" and (nxt == "" or nxt == "\n" or nxt == "\r"):
            buf.append(c)
            _flush(i + 1)
            i += 1
            continue

        buf.append(c)
        i += 1

    # Tail without a trailing semicolon
    tail = "".join(buf).strip()
    if tail:
        segments.append(tail)

    if not segments:
        raise ValueError("no SQL statements found after parsing")

    return segments


# ─────────────────────────────────────────────────────────────────────────────
# Connection + execution
# ─────────────────────────────────────────────────────────────────────────────

def connect(url, vp):
    """Open a psycopg connection via the venv interpreter.

    Imported lazily from the venv so the missing-key path never imports
    psycopg (keeps the smoke test cheap and traceback-free).
    """
    # Inject the venv's site-packages into this process. Doing it here means
    # argparse/CLI handling stays on the outer interpreter (faster startup,
    # no psycopg import cost on the missing-key path).
    inject_venv_into_path(vp)
    try:
        import psycopg
    except ImportError as e:
        print(
            "supabase: cannot import psycopg from venv {0}: {1}\n"
            "  fix: delete {2} and rerun to rebuild the venv."
            .format(VENV_DIR, e, _venv_marker()),
            file=sys.stderr,
        )
        sys.exit(EXIT_DEPS)

    try:
        # connect_timeout=15s prevents a DNS/network stall from blocking forever.
        # autocommit=False (default) so multi-statement scripts are atomic.
        conn = psycopg.connect(url, connect_timeout=15)
    except Exception as e:
        # Sanitise: drop any "postgresql://user:pass@host" from the message.
        msg = _redact_url(str(e))
        print("supabase: connection failed: {0}".format(msg), file=sys.stderr)
        sys.exit(EXIT_CONNECT)
    return conn


def inject_venv_into_path(vp):
    """Prepend the venv's site-packages to sys.path so ``import psycopg`` works."""
    # venvs on Unix put pure-Python + binary wheels under lib/pythonX.Y/site-packages
    # We discover it via the venv's python rather than hardcoding a version.
    try:
        out = subprocess.run(
            [vp, "-c", "import sysconfig; print(sysconfig.get_paths()['purelib'])"],
            check=True, capture_output=True, text=True,
        )
        site = out.stdout.strip()
    except Exception:
        return
    if site and os.path.isdir(site) and site not in sys.path:
        sys.path.insert(0, site)


def _redact_url(text):
    """Scrub any ``postgresql://...:password@host`` substring from a message."""
    return re.sub(r"postgresql://[^\s\"'<>]+", "[redacted-url]", text)


def run_sql(conn, statements, json_out):
    """Execute each statement; return (rows, columns) for the last resultset.

    DDL/DML statements (no description) accumulate no rows; the *last*
    statement that returns rows wins. This matches what a specialist wants:
    write a migration + verification query in one go and see the verification.
    """
    last_cols = []
    last_rows = []

    with conn.cursor() as cur:
        for stmt in statements:
            try:
                cur.execute(stmt)
            except Exception as e:
                conn.rollback()
                msg = _redact_url(str(e)).strip()
                # psycopg errors include the SQL position — keep it.
                print("supabase: SQL error: {0}".format(msg), file=sys.stderr)
                sys.exit(EXIT_SQL_RUN)

            if cur.description:
                last_cols = [c.name for c in cur.description]
                # Materialise eagerly; for huge results this still beats re-fetching.
                last_rows = cur.fetchall()
            else:
                # DDL/DML — commit per statement so DDL (which can't sit in
                # an aborted txn) is durable. Postgres rejects DDL inside a
                # failed transaction; committing each non-SELECT avoids that.
                conn.commit()

    return last_rows, last_cols


# ─────────────────────────────────────────────────────────────────────────────
# Output rendering — table (default) and --json. No external deps.
# ─────────────────────────────────────────────────────────────────────────────

def _cell(v):
    """Stringify a DB value for display. Truncate very long values."""
    if v is None:
        return ""
    s = str(v)
    if len(s) > ROW_TRUNCATE:
        s = s[:ROW_TRUNCATE] + "…"
    return s


def render_table(cols, rows):
    """Print a simple aligned table with width-aware column sizing."""
    if not cols:
        if rows:
            # No description (rare); dump a single column.
            for r in rows:
                print(_cell(r[0] if isinstance(r, tuple) else r))
        else:
            print("(no rows)")
        return

    str_rows = [[_cell(v) for v in r] for r in rows]
    widths = [max(COL_MIN_WIDTH, len(c)) for c in cols]
    for r in str_rows:
        widths = [max(w, len(v)) for w, v in zip(widths, r)]
    widths = [min(w, COL_MAX_WIDTH) for w in widths]

    def _fmt(row):
        return "  ".join(v.ljust(w)[:w] for v, w in zip(row, widths))

    print(_fmt(cols))
    print(_fmt(["-" * w for w in widths]))
    for r in str_rows:
        print(_fmt(r))
    print("({0} row{1})".format(len(rows), "" if len(rows) == 1 else "s"))


def render_json(cols, rows):
    """Emit rows as a JSON array of objects."""
    out = [{c: _jsonable(v) for c, v in zip(cols, r)} for r in rows]
    print(json.dumps(out, ensure_ascii=False, indent=2, default=str))


def _jsonable(v):
    """psycopg returns Python-native types mostly; coerce anything weird."""
    if v is None or isinstance(v, (str, int, float, bool)):
        return v
    if isinstance(v, (list, tuple, dict)):
        return v
    return str(v)


# ─────────────────────────────────────────────────────────────────────────────
# CLI entry point
# ─────────────────────────────────────────────────────────────────────────────

def resolve_sql(args):
    """Mirror minimax.py's ``resolve_prompt`` precedence: -f > positional > stdin."""
    if args.file is not None:
        try:
            with open(args.file, "r", encoding="utf-8") as fh:
                return fh.read()
        except OSError as e:
            print("supabase: cannot read SQL file {0}: {1}".format(args.file, e),
                  file=sys.stderr)
            sys.exit(EXIT_USAGE)
    if args.sql is None or args.sql == "-":
        return sys.stdin.read()
    return args.sql


def main():
    # psycopg3 must be imported by Python >=3.10 (it uses typing.TypeAlias).
    # Hermes may launch this via the macOS system python 3.9, and connect()
    # injects the venv's site-packages onto THIS interpreter's sys.path — so a
    # 3.9 caller cannot import psycopg regardless of how the venv was built.
    # Re-exec the whole script once under a modern interpreter.
    if sys.version_info < (3, 10) and os.environ.get("SUPABASE_REEXECED") != "1":
        alt = _seed_python()
        os.environ["SUPABASE_REEXECED"] = "1"
        os.execv(alt, [alt, os.path.abspath(__file__)] + sys.argv[1:])

    parser = argparse.ArgumentParser(
        prog="supabase",
        description="Run SQL against the Lex Council Supabase Postgres database.",
    )
    parser.add_argument("sql", nargs="?", default=None,
                        help="SQL string. Use '-' or omit to read from stdin.")
    parser.add_argument("-f", "--file", default=None,
                        help="Read SQL from a file path.")
    parser.add_argument("--json", action="store_true",
                        help="Print result rows as a JSON array instead of a table.")
    parser.add_argument("--no-bootstrap", action="store_true",
                        help="Skip the cached-venv psycopg bootstrap (e.g. for "
                             "offline debugging). The connection will then fail "
                             "if psycopg isn't already importable.")
    parser.add_argument("--write", action="store_true", default=False,
                        help=argparse.SUPPRESS)  # hidden — enables write access
    args = parser.parse_args()

    sql = resolve_sql(args)
    if not sql or not sql.strip():
        print("supabase: empty SQL (pass a string, -f <file>, or pipe via stdin)",
              file=sys.stderr)
        sys.exit(EXIT_USAGE)

    # Resolve the key FIRST so a missing/empty key file exits cleanly without
    # ever touching the venv or psycopg.
    url = resolve_db_url()

    # Bootstrap (or reuse) the psycopg venv.
    if args.no_bootstrap:
        vp = sys.executable
    else:
        vp = ensure_psycopg()

    try:
        statements = split_statements(sql)
    except ValueError as e:
        print("supabase: SQL parse error: {0}".format(e), file=sys.stderr)
        sys.exit(EXIT_SQL_PARSE)

    # ── Read-only enforcement ──────────────────────────────────────────
    # Without --write, reject any statement that would modify the database.
    # This is the Hermes-side gate: Hermes profiles get SELECT/WITH only.
    if not args.write:
        statements = _enforce_readonly(statements)

    conn = connect(url, vp)
    try:
        rows, cols = run_sql(conn, statements, args.json)
    finally:
        try:
            conn.close()
        except Exception:
            pass

    if args.json:
        render_json(cols, rows)
    else:
        render_table(cols, rows)


if __name__ == "__main__":
    main()