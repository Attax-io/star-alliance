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
# injects one of three tiers:
#   • NONE (~0 tokens): clearly-chat AND short AND not-large — pure small talk /
#     "what is X?" / acks. Injects nothing; the sidecar still gets written so
#     turn-cost.py and workflow-banner-enforcer.py can read the tier.
#   • LITE (~150 tokens): clearly-small AND clearly-low-stakes turns.
#   • FULL (~1,331 tokens): everything else, including ALL high-stakes turns.
# Tier order (first match wins): stakes → chat → small → else-full. Stakes
# ALWAYS wins over size: a one-line edit to a migration is small but
# high-stakes and takes FULL + halt. Unknown/empty/garbled → FULL (fail-safe).
# The keyword/size lists are POLICY, in data/harness.json → "policy"; edit there,
# not here. Override: SA_GATE=full|lite|none forces that tier instantly.
#
# Each block carries a marker line — SA-GATE:NONE / SA-GATE:LITE / SA-GATE:FULL
# — so the turn-cost Stop hook can record which tier fired and prove the
# savings (Phase 0).
#
# SLASH-SKILL KLAXON FIX (unchanged): a user-typed /slash skill loads via a
# <command-name> injection and never calls the Skill tool, so the ⚡ banner went
# silent. We detect a leading /skill and direct the model to emit it.
# ─────────────────────────────────────────────────────────────────────────────
INPUT=$(cat)

# ── Tier classifier ──────────────────────────────────────────────────────────
# Reads the prompt + data/harness.json policy; prints NONE / LITE / FULL.
# Fails to FULL on ANY ambiguity or error — a broken classifier must never
# WEAKEN the gate.
TIER=$(SA_INPUT="$INPUT" SA_GATE="${SA_GATE:-}" PROJ="${CLAUDE_PROJECT_DIR:-$(pwd)}" python3 - <<'PY'
import os, json, sys
gate = os.environ.get("SA_GATE", "").strip().lower()
if gate == "full":
    print("FULL"); sys.exit(0)
if gate == "lite":
    print("LITE"); sys.exit(0)
if gate == "none":
    print("NONE"); sys.exit(0)
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
chat = pol.get("chat_signals", [])
# Tier order (first match wins):
#   1) stakes → FULL
#   2) chat + short + no large → NONE
#   3) small + short + no large → LITE
#   4) else → FULL
if any(k in p for k in stakes):
    print("FULL"); sys.exit(0)
has_small = any(k in p for k in small)
has_large = any(k in p for k in large)
has_chat  = any(k in p for k in chat)
short = len(p) <= int(pol.get("size_short_chars", 240))
if has_chat and short and not has_large:
    print("NONE"); sys.exit(0)
print("LITE" if (has_small and not has_large and short) else "FULL")
PY
)

# B1 — write tier to sidecar so turn-cost.py can read it reliably.
# The marker SA-GATE:TIER lands in the hook's stdout (system-reminder context),
# not in user-turn text, so turn-cost.py's regex never matched → tier=unknown.
# Sidecar file is the fix: one write here, one read+delete in turn-cost.py.
mkdir -p "${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/state"
printf '%s' "$TIER" > "${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/state/last-tier"

# NONE tier: chat turn — inject ZERO doctrine. The sidecar above is the only
# artifact (so turn-cost.py and workflow-banner-enforcer.py can read the tier
# and act accordingly). A single one-line marker keeps the SA-GATE:TIER grep
# pattern in turn-cost.py working without a body of doctrine to scan.
# We do NOT `exit` here — the slash-skill banner directive below must still
# run on NONE turns (a user could /slash a skill that's also "short and chat"
# shaped by length, and we still want the ⚡ banner to fire).
if [ "$TIER" = "NONE" ]; then
cat <<'EOF'
[SA-GATE:NONE]
EOF
fi

if [ "$TIER" = "LITE" ]; then
cat <<'EOF'
⚔ STAR ALLIANCE ROUTING GATE — LITE (small, low-stakes turn).  [SA-GATE:LITE]
This looks like a quick, easily-reversible change. Proportional path:
  • The Butler OPENS Routing on intake; the STRATEGIST picks the real lane
    (Quick Fix · Standard Mission · …) — Butler voices, Strategist picks, Guild Master
    approves. The Strategist routes; the Butler is the voice (intake, approval gate,
    report) — never the worker.
  • If it IS a quick, low-stakes fix → open, as your FIRST line, the brief:
    ▸ Workflow — Quick Fix
    Deploying 1 agent:
      • The <Member> — <brain model> (planning)
    (Optionally append a doer slot ONLY if a doer call actually ran this turn, and a critic
    slot ONLY if the verify/critic gate actually fired — never stamp a placeholder.)
    then proceed — no approval halt needed for a trivially-reversible edit.
    (Voice-only turn the Butler answers directly? He is NOT an agent — drop the
    "Deploying agents" block and write: "Handled directly by the Butler — <model>.
    No agents deployed.")
  • Hand any doer-grade bulk/transform work to a cheap doer
    (python3 star-alliance-arsenal/summon.py minimax-sub "<prompt>").
  • ESCALATE TO FULL + HALT the instant the task actually touches anything
    high-stakes — migrations, git push/force, prod/deploy, RLS/secrets, renames,
    deletes, or mass/multi-file edits. When unsure, treat as high-stakes: restate
    a one-line brief and wait for "go". Stakes beats size, always.
The 🗺 banner is the gate key: no banner → every work tool is blocked.
EOF
elif [ "$TIER" = "FULL" ]; then
cat <<'EOF'
⚔ STAR ALLIANCE ROUTING GATE (harness-injected, binding) — ROUTE before you act.  [SA-GATE:FULL]
The Butler is your VOICE — he receives the order, translates to plain English, holds the
approval gate, and delivers the final report. He runs as the active session persona (no
separate agent). The STRATEGIST routes — he forms the right member and sequences the work.
Neither does specialist or doer-grade work himself.

WORKFLOW SELECTION — WHO CHOOSES: The Butler OPENS Routing (the universal intake banner:
"▸ Workflow — Routing") on every intake turn. The Butler does NOT pick the real workflow
— that is the Strategist's job. The Strategist reads the cleared brief, selects the right
entry from workflows.json (Quick Fix · Standard Mission · Architecture Build · Design
Sprint · Legal Codex · Market Recon · Skill Forge · …), and the turn continues under that
new banner. If no workflow fits, the Strategist opens Workflow Forge — not the Butler. The
division of labor is fixed: Butler voices, Strategist picks, Guild Master approves.
ONE CARVE-OUT: multi-agent SWARM orchestration is the Butler's, not the Strategist's — only the live top session can fan out parallel workers, so the Butler dispatches the Strategist first (worthiness/workflow) then cuts disjoint slices, fans out N workers in one message, runs a per-slice critic, and integrates + commits once.

STEP 0 · HOLD THE APPROVAL GATE — before ANY build, file write, git op, or other
hard-to-reverse action, the Butler RESTATES the request back as a one-line brief
(member · workflow · what will be touched) and HALTS for the Guild Master's explicit
"go". Clarifying or design questions are NOT approval — narrowing the spec is not
the same as signing off on it. No work starts, and no workflow is forged, until the
Guild Master says go. The Butler frames; the Guild Master approves — the producer of
the brief never self-approves it.

STEP 1 · THE STRATEGIST FORMS THE RIGHT MEMBER — he routes the task to ONE specialist:
  • code · features · bug fixes · refactor code · dev server · tooling · knowledge graph → the-developer (sonnet)
  • database · system design · domain model · structural refactor                        → the-architect (opus)
  • UI · UX · brand kit · image-to-code · visual polish · design system                  → the-designer (sonnet)
  • marketing · growth · SEO · content · email nurture · social/paid · go-to-market      → the-herald (sonnet)
  • investment · trading · market research · portfolio · buy/sell/risk                    → the-merchant (sonnet)
  • skills (sync/upgrade/create) · guild log · daily skill routine                        → the-quartermaster (sonnet)
  • large multi-wave projects · campaigns · bug workflow · performance optimization       → the-strategist (opus)
  • routing · "who handles this" · break the work into waves · sequence members           → the-strategist (opus)
  • load/translate law · legal drafting · multi-locale content                            → the-interpreter (sonnet)
  • GAP-FILLER ONLY — the-connector is NEVER the first routing target for ordinary craft.
    The Strategist routes to the-connector in exactly two cases: (1) DIRECT — when the task itself
    needs a Claude connector (WhatsApp, Gmail, Calendar, web search/fetch, computer-use);
    no other member can reach it, so the connector is the sufficient cause and the seven-try rule
    does NOT apply; (Supabase is NOT in this list — it is now Hermes-direct, available to any
    specialist via `star-alliance-arsenal/supabase.py` running SQL/DDL against the database with
    credentials from an out-of-repo key file, so no Claude connector is needed.) (2) ESCALATION —
    when a craft specialist is genuinely stuck on work that does NOT need a connector, the
    specialist must first log seven real attempts in the guild log, and only after the seventh
    logged attempt may the Strategist escalate the work to the-connector as the sanctioned
    overflow doer. The Connector is not a craft member — design/code/marketing/trading/legal/
    skill work still routes to the named specialist, never to the Connector.
  THE VOICE (not a routing target): the Butler receives the order, translates, holds the
  approval gate (STEP 0), and delivers the final report — running as the session persona.

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
    working turn MUST run inside a declared workflow. Open, as your FIRST line,
    ▸ Workflow — <name>  naming a real workflows.json entry — or forge one via
    Workflow Forge if none fits — BEFORE any tool fires. No workflow line =
    every tool call is blocked. It is the gate key.

STEP 3 · THAT MEMBER WORKS IN TWO LAYERS (weapon-utility):
  Hand doer-grade work — bulk edits, extraction, generation, mechanical transforms, large reads/summaries —
  to the member Hermes profile first:  python3 tools/dispatch.py <agent-name> "<prompt>"
  The member's BRAIN (opus for the Strategist, glm-5.2 for the rest) stays the mind — plan → prompt the
  doer → review against the plan → re-prompt until it conforms. minimax.py is the substitute used only
  when Hermes is unreachable:  python3 star-alliance-arsenal/minimax.py "<prompt>"  (-s · --json · -f)
  No other doer path exists: the sole sanctioned overflow when a member seat cannot do something is
  The Connector, reached directly for connector work, or after seven logged attempts in the guild
  log for escalation when a craft specialist is genuinely stuck. If Hermes AND the substitute are
  both unreachable, STOP and report rather than guessing on a weaker model.

Acting as the Butler to do a specialist's job, OR a member doing doer-grade work in its thinker, is the
EXCEPTION — and must be justified out loud. Tool-access orchestration (git, file writes, MCP) stays with the
working member's thinker; doers cannot run it.

DEPLOYMENT BRIEF (always on, every working turn) — open with a short, professional brief
the Guild Master can read at a glance. Clean and plain — no insider jargon. Format:
  ▸ Workflow — <workflow name>
  Deploying <N> agents:
    • The <Member> — <brain model> (planning) [· <doer model> (execution)] [· <critic model> (critic)]
    • The <Member> — <brain model> (planning) [· <doer model> (execution)] [· <critic model> (critic)]

  THE BUTLER IS THE VOICE, NOT AN AGENT — never list him as a bullet under "Deploying
  agents." He is the session persona who relays every turn; the "Deploying N agents"
  block counts ONLY the specialists actually put on the field. For a CONVERSATION /
  voice-only turn (a greeting, ack, or meta-question the Butler answers directly with no
  specialist), there are zero deployed agents — so DROP the "Deploying agents" block
  entirely and write just the two lines:
    ▸ Workflow — Conversation
    Handled directly by the Butler (the guild's voice) — <model>. No agents deployed.
  Keep the honest model attribution (the model that actually answered); only the "agent"
  label is wrong for the Butler.
RULES:
  • The "▸ Workflow — <name>" line is mandatory and is the gate key (no workflow line →
    tools blocked). Name a real workflows.json entry.
  • List one bullet per agent the workflow deploys. Keep the "<N>" count accurate. The
    cast is the workflow's steps[].actor list (skip `you`/gates).
  • A swarm bullet may read "The <Member> ×<N> — <model>" (member-instance fan-out) —
    the ×N/xN suffix is accepted as-is, no special-casing needed.
  • MODEL SLOTS — TRANSPARENCY RULE: report only what actually ran this turn; never
    stamp a template. Three slots, but execution and critic are CONDITIONAL.
    — Brain (planning) — ALWAYS present. Voice-only turn: the session model that actually
      answered (for example Opus). Dispatched-specialist turn: the member Hermes profile
      brain — its DEFAULT seat chain. Name the model that actually answered if known,
      otherwise say profile-default rather than guessing. Do NOT pin a specific brain
      model for a member class.
    — Doer (execution) — name the doer model ONLY if a doer call actually ran this turn.
      Otherwise omit the slot entirely. Do not write a placeholder doer.
    — Critic — name the critic model ONLY if the verify or critic gate actually fired
      this turn. Otherwise omit the slot entirely. Do not hardcode any critic model.
    A slot naming a model that did not run is a hallucination, not a formality.
  • List each agent as it takes the field — the lead specialist when work begins, and the
    closing the-quartermaster at the conformance step. (The turn-end enforcer needs at least
    one of the workflow's agents listed, or it re-prompts.)
  • When a Skill tool fires it auto-announces "▸ Skill — <name>" — let it land, don't repeat.
Keep it tight: the brief is a few lines, never a wall of text.
EOF
else
  # Tier is NONE (chat turn). The [SA-GATE:NONE] marker is already on stdout
  # above; the if/elif/else structure here exists only so the LITE and FULL
  # banners do NOT print for NONE. Nothing else to emit for chat turns —
  # the slash-skill directive below still runs.
  :
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
        f"▸ Skill — {name}"
    )
PY
exit 0
