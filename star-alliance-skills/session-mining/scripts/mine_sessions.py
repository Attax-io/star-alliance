#!/usr/bin/env python3
"""mine_sessions.py — pull signal windows out of session transcripts.

Reads a session_map.py TSV (or a list of .jsonl paths) and extracts only the
*signal-bearing* turns — user corrections / requests and the assistant
paragraphs that propose, gap-flag, or distill — never the tool-call noise.
Output is a compact, deduped, per-session digest small enough for the member to
read directly, OR shardable across Claude subagents to summarize in parallel.

Treat every transcript as text and pull bounded windows around markers — this
survives format drift across the stores. The DEFAULT keyword sets target
guild/skill self-improvement mining; override with --user-kw / --asst-kw for
other lenses (bugs, decisions, anything).

Usage:
    python3 mine_sessions.py --map map.tsv --out digest.txt
    python3 mine_sessions.py --jsonl a.jsonl b.jsonl --out digest.txt
    python3 mine_sessions.py --map map.tsv --min-bytes 50000 --cap 40 --out d.txt
"""
import argparse, hashlib, json, os, re, sys

DEFAULT_USER_KW = (
    r"\b(create|merge|new|build|make|extract|forge|add|upgrade|fix|teach)\b"
    r".*\b(skill|workflow|member|arsenal|weapon|installer|mode|hook|routine)\b"
)
DEFAULT_ASST_KW = (
    r"\b(new skill|proposed skill|should be a skill|make .* a skill|turn .* into a skill|"
    r"reusable|worth saving|workflow forge candidate|missing workflow|new workflow|"
    r"skillsmith mode|real gap|not built|none built|empty seat|candidate (skill|workflow))\b"
)
SKIP_USER = ("tool_result", "stop hook", "base directory for this skill")


def text_of(m):
    c = m.get("content")
    if isinstance(c, str):
        return c
    if isinstance(c, list):
        return "\n".join(b.get("text", "") for b in c if isinstance(b, dict) and b.get("type") == "text")
    return ""


def transcripts(args):
    if args.jsonl:
        for p in args.jsonl:
            yield (os.path.basename(p), p)
        return
    for line in open(args.map):
        parts = line.rstrip("\n").split("\t")
        if len(parts) < 4:
            continue
        sz, title, _cli, j = parts[0], parts[1], parts[2], parts[3]
        if not j or not os.path.exists(j):
            continue
        if int(sz or 0) < args.min_bytes:
            continue
        yield (title, j)


def extract(j, U, A, cap):
    """Pull the [tag] para signal lines out of one transcript. Pure: no I/O but the read."""
    seen, lines = set(), []
    for ln in open(j, encoding="utf-8", errors="replace").read().splitlines():
        if cap and len(lines) >= cap:
            break
        try:
            o = json.loads(ln)
        except Exception:
            continue
        m = o.get("message") or o
        role = m.get("role") or o.get("type", "")
        t = text_of(m).strip()
        if not t:
            continue
        if role == "user":
            low = t.lower()
            if t.startswith("<") or any(s in low for s in SKIP_USER):
                continue
            if U.search(t) and len(t) > 20:
                para, tag = t[:600], "U"
            else:
                continue
        elif role == "assistant":
            hit = next((p for p in re.split(r"\n\s*\n", t) if A.search(p)), None)
            if not hit:
                continue
            para, tag = hit.strip()[:700], "A"
        else:
            continue
        k = para[:80]
        if k in seen:
            continue
        seen.add(k)
        lines.append(f"[{tag}] {para}")
    return lines


def sig_of(j):
    """File signature: size:mtime. Changes iff the transcript changed."""
    st = os.stat(j)
    return f"{st.st_size}:{int(st.st_mtime)}"


def main():
    ap = argparse.ArgumentParser()
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--map", help="TSV from session_map.py")
    src.add_argument("--jsonl", nargs="+", help="explicit .jsonl paths")
    ap.add_argument("--out", default="", help="digest file (default: stdout)")
    ap.add_argument("--min-bytes", type=int, default=0, help="skip transcripts smaller than this")
    ap.add_argument("--cap", type=int, default=0, help="max signal lines kept per session (0 = no cap)")
    ap.add_argument("--user-kw", default=DEFAULT_USER_KW)
    ap.add_argument("--asst-kw", default=DEFAULT_ASST_KW)
    ap.add_argument("--cache", default="", help="JSON cache: skip re-scanning transcripts whose size:mtime is unchanged")
    a = ap.parse_args()

    U = re.compile(a.user_kw, re.I)
    A = re.compile(a.asst_kw, re.I)

    # Cache is keyed by the extraction params — change a keyword set or the cap and it rebuilds.
    pfp = hashlib.sha1(f"{a.user_kw}\x00{a.asst_kw}\x00{a.cap}".encode()).hexdigest()[:16]
    cache, hits, scans = {"_params": pfp, "files": {}}, 0, 0
    if a.cache and os.path.exists(a.cache):
        try:
            old = json.load(open(a.cache))
            if old.get("_params") == pfp:
                cache = old
        except Exception:
            pass
    files = cache["files"]

    out = open(a.out, "w") if a.out else sys.stdout
    kept = 0
    for title, j in transcripts(a):
        ja = os.path.abspath(j)
        try:
            sig = sig_of(j)
        except OSError:
            continue
        ent = files.get(ja)
        if a.cache and ent and ent.get("sig") == sig:
            lines = ent["lines"]
            hits += 1
        else:
            lines = extract(j, U, A, a.cap)
            if a.cache:
                files[ja] = {"sig": sig, "lines": lines}
            scans += 1
        if lines:
            out.write(f"\n\n##### {title}\n")
            for ln in lines:
                out.write(ln + "\n")
            kept += len(lines)
    if a.cache:
        json.dump(cache, open(a.cache, "w"))
    if a.out:
        out.close()
        msg = f"signal lines kept: {kept} | bytes: {os.path.getsize(a.out)}"
        if a.cache:
            msg += f" | cache hits: {hits} scanned: {scans}"
        print(msg)


if __name__ == "__main__":
    main()
