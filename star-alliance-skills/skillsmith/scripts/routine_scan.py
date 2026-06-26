#!/usr/bin/env python3
"""skillsmith — routine harvest. Read-only corpus gather for the daily STORM loop.

Stage A of `routine` mode (see references/routine-playbook.md). Gathers, WITHOUT writing
anything outside its --out file:
  • every skill's name, metadata.version, Cowork status, mtime, days-since-change
  • how often each skill is mentioned across the configured roots (your repos + session
    transcripts), within the last --days
  • "friction" snippets — a SESSION-TRANSCRIPT USER TURN that names a skill and smells
    like a problem (error/fail/bug/confus/wrong/should/instead/"didn't work") → the
    UPGRADE signal. Friction is a LIVE-USAGE signal: only a session user turn actually
    *exercises* a skill, so project files (app docs, vault-logs, memory) feed the mention
    count but NEVER friction — they *describe* domain work where a skill name is a topic.
  • recurring task-request keywords in recent sessions that match NO skill → the
    NEW-SKILL signal

Output: a JSON manifest the STORM stage reads. Also prints a short human summary to stdout.
This script makes NO judgments and changes NO skills — it just feeds the model raw signal so
STORM isn't grepping blind.

Roots (defaults, override with --root, repeatable):
  the star-alliance repo · every dir under ~/Documents/Claude/Projects · ~/.claude/projects
  (session transcripts, *.jsonl)

Usage:
  python3 routine_scan.py [--days 14] [--root PATH ...] [--out FILE] [--max-snippets 6]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

FRICTION = re.compile(
    r"(error|fail(ed|ure|s)?|bug|broke|confus|wrong|should(n.t)?|instead|didn.?t work|"
    r"doesn.?t work|annoying|hate|stuck|missing|too (slow|verbose|long)|over-?trigger)",
    re.I,
)
REQUEST = re.compile(
    r"\b(can you|could you|i want|i need|please|build|create|make|add|fix|refactor|"
    r"automate|generate|write|set up|implement)\b",
    re.I,
)
# Source classes that are NEVER real usage friction — they MENTION a skill without
# exercising it, so a FRICTION keyword nearby is noise, not an upgrade signal:
#   • skill/command DEFINITIONS under .claude/skills|commands/ (a skill *described*
#     in its own SKILL.md/references is not a skill *used* — the same principle that
#     already excludes the repo itself);
#   • config permission lists (settings.json / settings.local.json — "Bash(... skill)");
#   • generated vault-log indexes (vault-logs/INDEX.md — title rows, never friction).
# Pre-filter (ledger 2026-06-20): without these, ALL 13 "frictionful" skills were 100%
# definitional/boilerplate noise. DEFINITIONAL files are skipped entirely (mention +
# friction); BOILERPLATE is a per-LINE filter for "consulted / delegate to / invoke the
# X skill" references that live inside legitimately-scanned vault-logs & session prompts.
DEFINITIONAL_PATH = re.compile(
    r"([/\\]\.claude[/\\](skills|commands)[/\\]|[/\\]vault-logs[/\\]INDEX\.)", re.I
)
CONFIG_BASENAMES = {"settings.json", "settings.local.json"}
BOILERPLATE = re.compile(
    r"(docs?\s+consulted|consulted:|delegate to|invoke the |"
    r"\bper [a-z][a-z-]+-workflow\b|read claude\.md)",
    re.I,
)
# A YAML frontmatter `description:` line is a skill/command/spec DEFINITION wherever it
# lives (e.g. a `*-skill-DELTA.md` spec doc), not usage friction — drop it per-line
# (belt-and-suspenders for any description echo outside the .claude/ dirs we now prune).
FRONTMATTER_DESC = re.compile(r"^\s*description:\s*", re.I)
# A USER turn that merely LOCATES / READS / INSTALLS a skill, or pastes its file path,
# is not friction USING it — drop these from the (now session-only) friction signal.
# Ledger 2026-06-20 run 4: after restricting friction to session user turns, the 3
# surviving snippets were all one definitional ask — "Read the … bug-fix-workflow skill
# and report its full mechanics … the skill file is likely under <path> … search for it".
SKILL_META = re.compile(
    r"(read the .{0,40}\bskill\b|the skill file\b|search for it\b|"
    r"report its (full )?mechanics|\.claude[/\\]skills[/\\]|\bskill\.md\b|"
    r"where is the .{0,40}\bskill\b|install (the )?.{0,40}\bskill\b|"
    r"^[-*\s]*[`/].{0,4}/users/)",
    re.I,
)


def is_skill_ref(low_line: str, name: str) -> bool:
    """True when `name` appears as a SKILL/COMMAND REFERENCE, not a bare domain noun.

    The collision class (ledger 2026-06-20 run 4): short common-word skill names —
    `supabase`, `cleanup`, `performance`, `dev-server`, `bug-fix-workflow` — also match the
    PRODUCT / ACTIVITY / TASK they're named after. App session prompts say "Supabase
    project_id=…", "other parallel cleanup sessions", "extract performance lessons", "Fix a
    bug" — a friction word sitting next to the bare noun, but that's the APP's friction, not
    the skill's. v1.1.5 predicted this needs a "usage-vs-topic gate". The gate: a genuine
    skill reference is the slash-command `/name`, or the name next to the word
    "skill/mode/command" ("name skill", "skill name", "name mode"). A bare domain noun is
    not — and the looser "run/use/invoke name" verb-form is rejected on purpose: for a skill
    whose name IS the product/activity it collides hard ("Use the Supabase MCP" = the
    product, "the cleanup runs" = the activity), so it is NOT a reliable skill marker.
    Higher precision, lower recall is the right trade for an autonomous signal: a missed
    genuine friction just isn't auto-surfaced this run; acting on app-noise is worse."""
    n = re.escape(name)
    return bool(re.search(
        rf"(/{n}\b|\b{n}\s+(skill|mode|command)\b|\bskill\s+{n}\b)", low_line))


def is_definitional(fp: Path) -> bool:
    """A skill/command definition, config permission list, or generated log index —
    a mention here is inventory, not usage. Excluded from the mention+friction scan."""
    return bool(DEFINITIONAL_PATH.search(str(fp))) or fp.name in CONFIG_BASENAMES
# text-ish files worth scanning for skill mentions in project trees
TEXT_EXT = {".md", ".mdx", ".txt", ".ts", ".tsx", ".js", ".jsx", ".py", ".json",
            ".sql", ".sh", ".yml", ".yaml", ".toml"}
SKIP_DIRS = {".git", "node_modules", ".next", "__pycache__", "dist", "build",
             ".turbo", ".vercel", "coverage", ".cache",
             # tooling/config/transient, never a usage corpus (ledger 2026-06-20 run 3):
             #   .claude/ holds skills, commands, agents, settings AND .claude/worktrees/ —
             #   agent worktrees are throwaway duplicate repo checkouts whose campaign docs
             #   were the dominant residual friction noise (cleanup×3, supabase×3). The
             #   session-transcripts root is ~/.claude/projects, walked from INSIDE .claude,
             #   so SKIP_DIRS pruning (subdirs only) never touches it.
             ".claude", "worktrees"}
MAX_FILE_BYTES = 2_000_000
STOP = set((
    # articles / glue
    "the a an and or for to of in on with this that your you my our it is are be was were "
    "do does done go going get got use used using like just so but not no yes if then than "
    "from into out up down off all any one two only every each its their them they we he she "
    # skill-domain words + the request verbs themselves (they're how we FOUND the line — not topics)
    "skill skills claude code work working please want wants need needs make makes made making "
    "add adds added adding fix fixes fixed fixing new create creates created creating build builds "
    "built building write writes writing wrote generate set setup implement refactor automate help "
    # generic tech nouns that swamp a bag-of-words
    "file files json line lines page pages row rows column columns table tables function functions "
    "error errors data thing things way ways run running test tests type types value values name names"
).split())


def default_repo() -> Path:
    env = os.environ.get("STAR_ALLIANCE_REPO")
    if env:
        return Path(env).expanduser()
    here = Path(__file__).resolve()
    for anc in here.parents:
        if (anc / "VERSIONS.md").exists() and (anc / ".git").exists():
            return anc
    known = Path.home() / "Documents" / "Claude" / "Projects" / "star-alliance"
    return known if (known / "VERSIONS.md").exists() else here.parents[2]


def read_fm_version_status(skill_md: Path):
    """Return (version, status, desc_chars, body_words, body_lines) — minimal, no deps."""
    text = skill_md.read_text(errors="ignore")
    parts = text.split("---", 2)
    fm, body = (parts[1], parts[2]) if len(parts) >= 3 else ("", text)
    # version: metadata.version, fallback top-level
    ver = ""
    m = re.search(r"(?m)^metadata:\s*$", fm)
    if m:
        seg = fm[m.end():]
        vm = re.search(r"(?m)^[ \t]+version:\s*(.+)$", seg)
        if vm:
            ver = vm.group(1).strip().strip("\"'")
    if not ver:
        tm = re.search(r"(?m)^version:\s*(.+)$", fm)
        ver = tm.group(1).strip().strip("\"'") if tm else "—"
    # description (inline / block) — just need length + angle-bracket check
    dm = re.search(r"(?im)^description:\s*(.*)$", fm)
    desc = ""
    if dm:
        head = dm.group(1).strip()
        if head in (">", "|", ">-", "|-", ">+", "|+", ""):
            for ln in fm[dm.end():].splitlines():
                if re.match(r"^\s+\S", ln) or ln.strip() == "":
                    if ln.strip():
                        desc += " " + ln.strip()
                else:
                    break
        else:
            # mirror skill_registry.get_description: strip surrounding quotes AND
            # unescape \" so the char count matches the authoritative Cowork gate
            # (a quoted desc with N \"-escapes was over-counted by N, producing
            # phantom desc>1024 flags — e.g. cleanup read 1025 here vs 991 there).
            desc = head.strip('"').strip("'").replace('\\"', '"')
    desc = desc.strip()
    bw = len(body.split())
    bl = body.count("\n") + 1
    dc = len(desc)
    if dc > 1024:
        status = "desc>1024"
    elif "<" in desc or ">" in desc:
        status = "desc<>"
    elif bw > 10000:
        status = "body>10k"
    elif bw > 5000 or bl > 500:
        status = "large"
    else:
        status = "lean"
    return ver, status, dc, bw, bl


def discover_skills_root(anchor: Path) -> Path:
    """Layout-aware skills-root discovery (decoupled from the git/exclude anchor).

    The repo was restructured (2026-06): skill dirs moved from the repo TOP LEVEL
    into a `star-alliance-skills/` subdir. `anchor` is the stable git root (used as
    the corpus-exclude anchor); the skills may live at `anchor` OR `anchor/<subdir>`.
    Probe the known layouts in order and return the first dir that actually holds
    at least one `*/SKILL.md`. Falls back to `anchor` so behaviour is unchanged on
    a layout this probe doesn't yet know about."""
    candidates = [anchor, anchor / "star-alliance-skills", anchor / "claude-skills"]
    for c in candidates:
        if c.is_dir() and any(
            d.is_dir() and not d.name.startswith(".") and (d / "SKILL.md").exists()
            for d in c.iterdir()
        ):
            return c
    return anchor


def iter_skill_dirs(skills_root: Path):
    for d in sorted(skills_root.iterdir()):
        if d.is_dir() and not d.name.startswith(".") and (d / "SKILL.md").exists():
            yield d


def newest_mtime(path: Path) -> float:
    """mtime of the most-recently-touched file under a skill dir."""
    best = path.stat().st_mtime
    for root, dirs, files in os.walk(path):
        dirs[:] = [x for x in dirs if x not in SKIP_DIRS]
        for f in files:
            try:
                best = max(best, (Path(root) / f).stat().st_mtime)
            except OSError:
                pass
    return best


def message_texts(raw):
    """Yield (role, text) from a transcript .jsonl (one JSON object per line). Pulls the
    real human/assistant message text out of the JSON so structural keys (sessionId,
    leafUuid, the system skill-list, tool-result blobs) don't pollute the signal."""
    for line in raw.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            obj = json.loads(line)
        except (ValueError, TypeError):
            continue
        # `isMeta: True` marks a HARNESS-INJECTED message — the available-skills/agents
        # catalog (each skill's description echoed verbatim as a standalone ≤1024-char
        # block), system-reminders, hook output. None are the user exercising a skill, so a
        # friction keyword inside is noise. This is the robust signal that subsumes the
        # string-marker drops below — it catches the HEADERLESS description echo a marker
        # can't see (run 3: lex_cleanup's desc, a device skill not even in repo inventory,
        # was mis-flagged as vault-log-compliance ×6 because its text names that skill).
        if obj.get("isMeta") is True:
            continue
        # MACHINE-ORIGIN user turns — NOT lines Atta typed. Ledger 2026-06-20 runs 2–4
        # deferred this class as "needs message-author provenance … not reachable by lexical
        # filters"; the provenance signal turns out to be STRUCTURAL after all. The routine's
        # own Agent/Workflow fan-out injects user-role dispatch prompts (a STORM "MISSION:
        # extract recurring HYGIENE DEBT…" prompt) that read as real turns. They are tagged
        # by one of three structural markers, NONE of which a genuine typed turn carries:
        #   • `isSidechain: True` (+ `agentId`) — the SUBAGENT's own session: the dispatch
        #     prompt is that subagent's first user turn. This is the canonical subagent
        #     marker; a sidechain is by definition not Atta typing.
        #   • `sourceToolAssistantUUID` / `toolUseResult` — the PARENT session's record of a
        #     tool call (tool_result blobs + the dispatched prompt the parent logged).
        # Ground-truthed on a Lex session: 6/6 genuine Atta turns carry NONE of these; every
        # machine turn (incl. the dispatch prompt, in all 4 of its copies) carries one. This
        # closes the last friction-noise class — the routine's own past dispatch prompts.
        if (obj.get("isSidechain") is True
                or "sourceToolAssistantUUID" in obj
                or obj.get("toolUseResult") is not None):
            continue
        role = obj.get("type") or ""
        msg = obj.get("message") if isinstance(obj.get("message"), dict) else None
        if msg and not role:
            role = msg.get("role", "")
        content = msg.get("content") if msg else obj.get("content")
        if isinstance(content, str):
            texts = [content]
        elif isinstance(content, list):
            texts = [b["text"] for b in content
                     if isinstance(b, dict) and isinstance(b.get("text"), str)]
        else:
            continue
        # Drop whole messages that ECHO a skill definition / catalog / control prompt into
        # the transcript — these MENTION skills without the user exercising them, so any
        # friction keyword inside is noise (ledger 2026-06-20). Applies to BOTH string- and
        # list-content messages: the catalog + scheduled-task prompt arrive as STRING content
        # (system-reminder/wrapper appended as one blob), so checking only the list branch
        # missed them (run 3 first-pass bug):
        #   • "base directory for this skill:" — a Skill invocation injecting its FULL
        #     SKILL.md (body + changelog rows that literally describe fixed bugs); 185 such
        #     injections were the dominant residual at run 2.
        #   • "available for use with the skill tool" / "available agent types for the agent
        #     tool" — the system available-skills/agents CATALOG, which echoes EVERY skill's
        #     description (run 2 deferred class A: lex_cleanup's desc was mis-flagged as
        #     vault-log-compliance ×6 friction).
        #   • "<scheduled-task" — the routine's OWN control prompt, re-injected each run (it
        #     flagged skillsmith/impeccable ×3 on the routine's Stage-D line).
        MSG_DROP = ("base directory for this skill:",
                    "available for use with the skill tool",
                    "available agent types for the agent tool",
                    "<scheduled-task")
        if any(mark in t.lower() for t in texts for mark in MSG_DROP):
            continue
        for t in texts:
            yield role, t


def scan_files(roots, names, cutoff, max_snippets):
    """Walk roots, count mentions + collect friction snippets per skill name.

    For session transcripts we look at the USER's words only — the assistant text and the
    per-session system skill-list would otherwise mark every skill 'active'. For project
    files we scan every line."""
    mentions = {n: {"files": 0, "sessions": 0} for n in names}
    friction = {n: [] for n in names}
    request_lines = []

    for root in roots:
        root = Path(root)
        if not root.exists():
            continue
        is_sessions = root.name == "projects" and root.parent.name == ".claude"
        for cur, dirs, files in os.walk(root):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            for fn in files:
                fp = Path(cur) / fn
                if is_definitional(fp):   # skill/command def, config perms, log index — not usage
                    continue
                ext = fp.suffix.lower()
                if is_sessions:
                    if ext != ".jsonl":
                        continue
                elif ext not in TEXT_EXT:
                    continue
                try:
                    st = fp.stat()
                except OSError:
                    continue
                if st.st_mtime < cutoff:
                    continue
                try:
                    raw = fp.read_text(errors="ignore")[:MAX_FILE_BYTES]
                except OSError:
                    continue
                if is_sessions:
                    lines = []
                    for role, m in message_texts(raw):
                        if role == "user":          # user's words = the real usage signal
                            lines.extend(m.splitlines())
                else:
                    lines = raw.splitlines()
                hit_names = set()
                for ln in lines:
                    low = ln.lower()
                    for n in names:
                        if n in low:
                            hit_names.add(n)
                            # FRICTION IS SESSION-ONLY. A project file (app docs, vault-logs,
                            # memory) names a skill as a DOMAIN TOPIC — cleanup the activity,
                            # performance the metric, supabase the product — sitting next to
                            # ordinary software-friction words; it describes work, it doesn't
                            # *use* the skill. 31/36 such snippets were 100% noise across runs
                            # 1–3, which kept trying to path/keyword-filter them. The clean
                            # cut: only a session USER turn exercises a skill, so only there can
                            # there be friction. Project-file mentions still feed mention_total
                            # (topical interest → STORM ranking); they just can't be friction.
                            # Within user turns, SKILL_META drops locate/read/install lines.
                            if (is_sessions and FRICTION.search(ln)
                                    and is_skill_ref(low, n)
                                    and not BOILERPLATE.search(ln)
                                    and not FRONTMATTER_DESC.match(ln)
                                    and not SKILL_META.search(ln)
                                    and len(friction[n]) < max_snippets):
                                friction[n].append({"where": str(fp), "snippet": ln.strip()[:280]})
                    if is_sessions and REQUEST.search(ln) and 8 < len(ln) < 400:
                        request_lines.append(ln.strip())
                for n in hit_names:
                    mentions[n]["sessions" if is_sessions else "files"] += 1
    return mentions, friction, request_lines


def gap_signals(request_lines, names, top=12):
    """Crude new-skill signal: frequent content words in task requests that aren't a skill name."""
    name_tokens = set()
    for n in names:
        name_tokens.update(n.split("-"))
    freq = {}
    for ln in request_lines:
        for w in re.findall(r"[a-zA-Z][a-zA-Z-]{3,}", ln.lower()):
            if w in STOP or w in name_tokens:
                continue
            freq[w] = freq.get(w, 0) + 1
    ranked = sorted(freq.items(), key=lambda kv: -kv[1])[:top]
    return [{"keyword": w, "count": c} for w, c in ranked if c >= 3]


def main():
    ap = argparse.ArgumentParser(description="skillsmith routine harvest (read-only)")
    ap.add_argument("--days", type=int, default=14, help="look-back window for mentions/friction")
    ap.add_argument("--root", action="append", default=[], help="extra root to scan (repeatable)")
    ap.add_argument("--out", type=Path, help="write JSON manifest here (else stdout JSON)")
    ap.add_argument("--max-snippets", type=int, default=6, help="friction snippets kept per skill")
    ap.add_argument("--repo", type=Path, default=default_repo())
    a = ap.parse_args()

    repo = a.repo.expanduser().resolve()      # anchor: stable git root, the corpus-exclude anchor
    skills_root = discover_skills_root(repo)   # layout-aware: repo top-level OR star-alliance-skills/
    now = time.time()
    cutoff = now - a.days * 86400

    # The repo itself is the skill INVENTORY source, not a usage corpus — exclude it from the
    # mention/friction scan (a skill described in its own SKILL.md is not usage signal). Always
    # exclude on `repo` (the git anchor), never on skills_root — else the repo leaks in as a
    # corpus root and SKILL.md bodies inflate mention counts as self-mentions.
    roots = []
    proj_root = Path.home() / "Documents" / "Claude" / "Projects"
    if proj_root.exists():
        for d in sorted(proj_root.iterdir()):
            if d.is_dir() and d.resolve() != repo:
                roots.append(str(d))
    sessions = Path.home() / ".claude" / "projects"
    if sessions.exists():
        roots.append(str(sessions))
    roots.extend(a.root)

    skills = []
    names = []
    for d in iter_skill_dirs(skills_root):
        ver, status, dc, bw, bl = read_fm_version_status(d / "SKILL.md")
        mt = newest_mtime(d)
        skills.append({
            "name": d.name, "version": ver, "status": status,
            "desc_chars": dc, "body_words": bw, "body_lines": bl,
            "days_since_change": round((now - mt) / 86400, 1),
        })
        names.append(d.name)

    mentions, friction, request_lines = scan_files(roots, names, cutoff, a.max_snippets)
    for s in skills:
        n = s["name"]
        s["mentions"] = mentions[n]
        s["friction"] = friction[n]
        s["mention_total"] = mentions[n]["files"] + mentions[n]["sessions"]

    mention_map = {s["name"]: s["mention_total"] for s in skills}
    active = sorted([s["name"] for s in skills if s["mention_total"] > 0],
                    key=lambda n: -mention_map[n])
    frictionful = [s["name"] for s in skills if s["friction"]]
    dormant = [s["name"] for s in skills if s["mention_total"] == 0]

    manifest = {
        "generated_for_days": a.days,
        "inventory_source": str(repo),
        "roots": roots,
        "skill_count": len(skills),
        "skills": skills,
        "gap_signals": gap_signals(request_lines, names),
        "summary": {
            "active_skills": active,
            "frictionful_skills": frictionful,
            "dormant_skills": dormant,
            "request_lines_seen": len(request_lines),
        },
    }

    payload = json.dumps(manifest, indent=2)
    if a.out:
        a.out.parent.mkdir(parents=True, exist_ok=True)
        a.out.write_text(payload)
    else:
        print(payload)

    # human summary to stderr so --out stdout stays clean JSON
    w = sys.stderr.write
    w(f"\nroutine_scan: {len(skills)} skills · window {a.days}d · {len(roots)} roots\n")
    w(f"  active ({len(active)}):     {', '.join(active[:12])}{' …' if len(active) > 12 else ''}\n")
    w(f"  frictionful ({len(frictionful)}): {', '.join(frictionful) or '—'}\n")
    w(f"  dormant ({len(dormant)}):    {', '.join(dormant[:12])}{' …' if len(dormant) > 12 else ''}\n")
    gs = manifest["gap_signals"]
    if gs:
        w("  new-skill hints: " + ", ".join(f"{g['keyword']}×{g['count']}" for g in gs[:8]) + "\n")
    if a.out:
        w(f"  → manifest: {a.out}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
