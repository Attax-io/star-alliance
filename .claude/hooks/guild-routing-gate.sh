#!/bin/sh
# ─────────────────────────────────────────────────────────────────────────────
# Star Alliance — GUILD ROUTING GATE  (UserPromptSubmit, harness-injected)
#
# Why this exists: the guild has three layers of doctrine —
#   members-formation (which MEMBER works) → workflows (which procedure) →
#   weapon-utility (which WEAPON inside that member) — but none were ENFORCED.
# The orchestrator kept acting as the Butler AND doing every specialist's job
# AND the doer-grade work itself, all inline on one premium model.
#
# PHASE 1 — PROPORTIONAL GATE. The old hook injected the SAME ~1,331-token
# campaign-grade doctrine on EVERY turn, whether a typo fix or a 12-wave campaign.
# It now governs on two axes — STAKES (reversibility/blast-radius) and SIZE — and
# injects one of two tiers:
#   • LITE (~150 tokens): clearly-small AND clearly-low-stakes turns.
#   • FULL (~1,331 tokens): everything else, including ALL high-stakes turns.
# Stakes ALWAYS wins over size: a one-line edit to a migration is small but
# high-stakes and takes FULL + halt. Unknown/empty/garbled → FULL (fail-safe).
# The keyword/size lists are POLICY, in data/harness.json → "policy"; edit there,
# not here. Override: SA_GATE=full forces the old uniform behavior instantly;
# SA_GATE=lite forces LITE (testing only).
#
# Each block carries a marker line — SA-GATE:LITE / SA-GATE:FULL — so the
# turn-cost Stop hook can record which tier fired and prove the savings (Phase 0).
#
# SLASH-SKILL KLAXON FIX (unchanged): a user-typed /slash skill loads via a
# <command-name> injection and never calls the Skill tool, so the ⚡ banner went
# silent. We detect a leading /skill and direct the model to emit it.
# ─────────────────────────────────────────────────────────────────────────────
INPUT=$(cat)

# ── Tier classifier ──────────────────────────────────────────────────────────
# Reads the prompt + data/harness.json policy; prints LITE or FULL. Fails to
# FULL on ANY ambiguity or error — a broken classifier must never WEAKEN the gate.
TIER=$(SA_INPUT="$INPUT" SA_GATE="${SA_GATE:-}" PROJ="${CLAUDE_PROJECT_DIR:-$(pwd)}" python3 - <<'PY'
import os, json, sys
gate = os.environ.get("SA_GATE", "").strip().lower()
if gate == "full":
    print("FULL"); sys.exit(0)
if gate == "lite":
    print("LITE"); sys.exit(0)
try:
    data = json.loads(os.environ.get("SA_INPUT") or "")
    prompt = (data.get("prompt") or "")
except Exception:
    print("FULL"); sys.exit(0)
p = prompt.lower().strip()
if not p:
    print("FULL"); sys.exit(0)
proj = os.environ.get("PROJ", "")
try:
    pol = json.load(open(os.path.join(proj, "data", "harness.json"))).get("policy", {})
except Exception:
    pol = {}
stakes = pol.get("stakes_keywords", [])
small = pol.get("size_small_signals", [])
large = pol.get("size_large_signals", [])
# Stakes always wins over size.
if any(k in p for k in stakes):
    print("FULL"); sys.exit(0)
has_small = any(k in p for k in small)
has_large = any(k in p for k in large)
short = len(p) <= int(pol.get("size_short_chars", 240))
# Only clearly-small AND clearly-low-stakes AND short → LITE. Else FULL.
print("LITE" if (has_small and not has_large and short) else "FULL")
PY
)

# B1 — write tier to sidecar so turn-cost.py can read it reliably.
# The marker SA-GATE:TIER lands in the hook's stdout (system-reminder context),
# not in user-turn text, so turn-cost.py's regex never matched → tier=unknown.
# Sidecar file is the fix: one write here, one read+delete in turn-cost.py.
mkdir -p "${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/state"
printf '%s' "$TIER" > "${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/state/last-tier"

if [ "$TIER" = "LITE" ]; then
cat <<'EOF'
⚔ STAR ALLIANCE ROUTING GATE — LITE (small, low-stakes turn).  [SA-GATE:LITE]
This looks like a quick, easily-reversible change. Proportional path:
  • ROUTE to ONE specialist (code→the-developer · db→the-architect · UI→the-designer
    · skills/log→the-quartermaster · law→the-translator). The Butler only routes.
  • If it IS a quick, low-stakes fix → declare, as your FIRST line,
    🗺 Starmap Workflow Started: Quick Fix!  then emit the member's
    ⚔ Member reports for duty: <member> using <thinker> and <doer>!  and proceed —
    no approval halt needed for a trivially-reversible edit.
  • Hand any doer-grade bulk/transform work to a cheap doer
    (python3 star-alliance-arsenal/summon.py minimax-m3 "<prompt>").
  • ESCALATE TO FULL + HALT the instant the task actually touches anything
    high-stakes — migrations, git push/force, prod/deploy, RLS/secrets, renames,
    deletes, or mass/multi-file edits. When unsure, treat as high-stakes: restate
    a one-line brief and wait for "go". Stakes beats size, always.
The 🗺 banner is the gate key: no banner → every work tool is blocked.
EOF
else
cat <<'EOF'
⚔ STAR ALLIANCE ROUTING GATE (harness-injected, binding) — ROUTE before you act.  [SA-GATE:FULL]
The Butler ONLY receives + routes; he does NOT do specialist or doer-grade work himself.

STEP 0 · HOLD THE APPROVAL GATE — before ANY build, file write, git op, or other
hard-to-reverse action, the Butler RESTATES the request back as a one-line brief
(member · workflow · what will be touched) and HALTS for the Guild Master's explicit
"go". Clarifying or design questions are NOT approval — narrowing the spec is not
the same as signing off on it. No work starts, and no workflow is forged, until the
Guild Master says go. The Butler frames; the Guild Master approves — the producer of
the brief never self-approves it.

STEP 1 · FORM THE RIGHT MEMBER — match the task to ONE specialist:
  • code · features · bug fixes · refactor code · dev server · tooling · knowledge graph → the-developer (sonnet)
  • database · system design · domain model · structural refactor                        → the-architect (sonnet)
  • UI · UX · brand kit · image-to-code · visual polish · design system                  → the-designer (sonnet)
  • marketing · growth · SEO · content · email nurture · social/paid · go-to-market      → the-herald (opus)
  • investment · trading · market research · portfolio · buy/sell/risk                    → the-merchant (opus)
  • skills (sync/upgrade/create) · guild log · daily skill routine                        → the-quartermaster (sonnet)
  • large multi-wave projects · campaigns · bug workflow · performance optimization       → the-strategist (opus)
  • load/translate law · legal drafting · multi-locale content                            → the-translator (sonnet)
  • pure coordination / "who handles this" / receive an order                             → the-butler (opus)

STEP 2 · FOLLOW THE WORKFLOW (workflows.json) — MANDATORY, not optional:
  Build & Fix:        Quick Fix · Standard Mission · Architecture Build · Bug Cycle · Security Sweep
  Design:             Design Sprint · Art Forge
  Legal:              Legal Codex · Legal Drafting · Tool Forge · Law Harvest
  Research & Intel:   Market Recon · Brand Audit · Relationship Intel
  Guild Self:         Skill Forge · Arsenal Forge · Strategic Audit · Workflow Forge
  Hygiene & Release:  Compliance Audit · Hygiene Rotation · Guild Log Sync · Release Train
  Comms & Automation: Comms Triage · Standing Watch
  ▶ If a workflow fits, FOLLOW its steps — do not improvise your own path.
  ▶ If NO existing workflow fits the request → STOP. Tell the Guild Master and ASK
    to create the workflow (Workflow Forge) BEFORE doing the work. Never proceed
    past a missing workflow on your own.
  ▶ HARD RULE (mechanically enforced by the workflow-gate PreToolUse hook): every
    working turn MUST run inside a declared workflow. Emit, as your FIRST line,
    🗺 Starmap Workflow Started: <name>! naming a real workflows.json entry — or
    forge one via Workflow Forge if none fits — BEFORE any tool fires. No banner =
    every tool call is blocked. The banner is not decoration; it is the gate key.

STEP 3 · THAT MEMBER DRAWS HIS WEAPONS (weapon-utility):
  Hand doer-grade work — bulk edits, extraction, generation, mechanical transforms, large reads/summaries —
  to one of the member's DOER weapons:  python3 star-alliance-arsenal/summon.py <model> "<prompt>"  (-s · --json · -f)
  Scan the member's OWN arsenal left→right: doers before thinkers, cheapest doer first; skip any weapon
  not pulled/reachable (Ollama bench needs `ollama list`). The member's THINKER weapon stays the mind —
  plan → prompt the doer → review against the plan → re-prompt until it conforms. The thinker need NOT be Opus.

Acting as the Butler to do a specialist's job, OR a member doing doer-grade work in its thinker, is the
EXCEPTION — and must be justified out loud. Tool-access orchestration (git, file writes, MCP) stays with the
working member's thinker; doers cannot run it.

HIGH-ALERT · SESSION KLAXON (always on, every session) — emit the matching banner the
INSTANT each event happens, as the first line for that event, exact emoji + punctuation:
  • EACH member the declared workflow names → ⚔ Member reports for duty: <member name> using <thinker weapon(s)> and <doer weapon>!
    The cast is the workflow's own steps[].actor list (skip `you` and the gates). Fire ⚔ the
    instant THAT member takes the field — the lead specialist when work begins, AND the closing
    the-quartermaster at the conformance step, AND any other actor the workflow lists. One ⚔ per
    member as it acts — NOT one ⚔ per workflow. A multi-member workflow emits multiple ⚔ banners.
    (The turn-end banner-enforcer hook derives this same roster from the declared workflow and
    blocks if the lead member never reported.)
  • STEP 2, a workflows.json procedure begins →  🗺 Starmap Workflow Started: <workflow name>!
  • Any Skill tool fires →  ⚡ Member Skill Activated: <skill name>!  (this one is auto-fired by the
    high-alert PreToolUse hook — let it land, do not also repeat it).
One banner per event (per member, per skill, per workflow). No stacking, no echo on trivial/internal steps.
EOF
fi

# ── SLASH-SKILL banner directive ─────────────────────────────────────────────
# /slash skills bypass the Skill tool → the high-alert hook never sees them.
# Detect a leading /skill in this prompt and tell the model to emit the ⚡ banner.
SA_INPUT="$INPUT" SKILLS_DIR="$HOME/.claude/skills" python3 - <<'PY'
import sys, json, os, re
try:
    data = json.loads(os.environ.get("SA_INPUT") or "")
except Exception:
    sys.exit(0)
prompt = (data.get("prompt") or "").lstrip()
m = re.match(r"/([A-Za-z0-9_-]+(?::[A-Za-z0-9_-]+)*)", prompt)
if not m:
    sys.exit(0)
name = m.group(1)
bare = name.split(":")[-1]
# built-in CLI commands that are NOT skills — never announce these
BUILTINS = {
    "caveman", "config", "clear", "help", "fast", "loop", "schedule",
    "permissions", "agents", "doctor", "hooks", "init", "review",
    "compact", "cost", "model", "memory", "resume", "status", "vim",
}
skills_dir = os.environ.get("SKILLS_DIR", "")
is_plugin = ":" in name                                  # /plugin:skill form
is_local  = bool(bare) and os.path.isdir(os.path.join(skills_dir, bare))
if bare in BUILTINS and not is_plugin:
    sys.exit(0)
if is_plugin or is_local:
    print(
        f"\n⚡ SLASH-SKILL DETECTED ({name}) — the high-alert hook cannot see "
        f"/slash skills. Emit, as your FIRST output line, exactly:\n"
        f"⚡ Member Skill Activated: {name}!"
    )
PY
exit 0
