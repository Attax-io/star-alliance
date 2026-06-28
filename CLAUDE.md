---
type: Document
timestamp: 2026-06-27T10:27:03Z
---

# Star Alliance — Claude Instructions

## Two layers: Claude thinker plans & reviews · MiniMax doer executes bulk

There is **no single "default model"** — there are two roles, and "MiniMax first"
governs only one of them. Don't read it as "route everything to MiniMax."

- **THINKER (the mind).** Each member's session model — a Claude model (Opus/Sonnet
  per the member's `model:`) — is the thinker. It owns the loop: plan → prompt the
  doer → review the return against the plan → re-prompt until it conforms. All
  tool-access orchestration (file edits, bash, git, MCP) stays with the thinker;
  doers cannot run it. The thinker need NOT be Opus.
- **DOER (the hands).** **Doer-grade work — bulk edits, extraction, generation,
  mechanical transforms, large reads/summaries — goes to MiniMax M3 first** (then the
  rest of the member's arsenal, cheapest doer first). This is what "MiniMax first"
  means: it is the **doer default**, not the thinker default.

```
python3 "$STAR_ALLIANCE_ROOT/star-alliance-arsenal/minimax.py" "<prompt>"
# flags: -s <system>  --json  -f <file>  (reads stdin if no arg)
# key: ~/.config/minimax/m3.key
# STAR_ALLIANCE_ROOT set in .claude/settings.json env block
```

**Size threshold (don't offload small jobs).** A MiniMax/Ollama summon costs ~80–100s
wall-time. Only offload doer-grade **bulk** (≳1.5k tokens of output, or many
repetitive transforms). A small job — a few lines, one quick edit — the thinker does
inline; offloading it is net-negative. The weapon-gate reminder restates this on every
summon.

**The thinker keeps the work (does NOT offload to a doer) when:**
- Orchestration logic requires tool access (file edits, bash, MCP)
- Deep multi-step reasoning / judgment the doer can't return structured output for
- The task requires native Claude Code capabilities
- The job is below the size threshold

So: **doer-grade bulk → MiniMax first; thinking, judgment, tool-orchestration, and
small jobs → the member's Claude thinker.**

## Reading discipline (every member)

_Mined from full session history — 46 sessions hit this; it was the single most-repeated correction._

- Files may exceed token caps. Read large or unknown-size files with `offset`/`limit` or `grep` — never a blind full read.
- The instant a full read fails on the token limit, **switch to offset/limit** — never retry the same full read.
- Read a file before editing it (avoids "not read yet" errors); re-read a shared or parallel-touched file immediately before writing if more than ~30s passed.
- In scheduled or autonomous runs, loop files **one at a time**, not all at once.
- **Don't trust harness file/page hints** — verify real length from the tool that reads the file (a "60-page" PDF was 331). For PDF text there is no system `pdftotext` and `pip` is PEP 668-blocked: build a scratchpad venv (`python3 -m venv "$SCRATCH/venv" && "$SCRATCH/venv/bin/pip" install -q pypdf`) and extract per-page.
- **macOS `grep` silently returns NO matches on UTF-8/multibyte files** (e.g. `app.js` with emoji/glyphs) — use `LC_ALL=C grep` or `rg`. Never conclude "content is gone" from one grep miss; confirm with Read/`sed -n 'Np'`. See [[grep-utf8-and-weapon-gate-gotchas]].

## Guild conduct (every member)

- **Don't make unrequested changes** — wait for explicit permission before modifying code or visuals. When the spec is clear, proceed; don't ask permission just to continue.
- **`cancel` = immediate revert** of the prior change-set. Honor an explicit **`proceed`** — don't re-insert your own verification breakpoints.
- Before creating a component, grep for and **reuse** an existing one; reuse design-token constants, never hardcode hex.
- **Read the vault/memory logs before continuing** work started in a prior session.
- **Memory is a graph, not a flat list — read the relevant `core` before working in an area.** `MEMORY.md` is the graph root (index of every memory + the domain cores). Before touching a domain (arsenal · skills · hooks/gates · dashboard · a Lex sub-system), read that domain's core memory first; follow `[[wikilink]]` edges as far as the task needs. Skipping the core read is the #1 cause of incorrect or duplicated work (penpot doctrine, Learning Pool mining 2026-06-28). Link liberally; a `[[name]]` with no file yet marks a core worth writing.
- Save user **confirmations and wins** as feedback memories, not only corrections.
- **Log errors loudly** — never silently swallow them.
- **Confirm destructive git ops** (`reset --hard`, force push) before executing. This is now **mechanically enforced** by the destructive-command gate (`.claude/hooks/destructive-gate.py`, PreToolUse·Bash): `rm -rf`, force-push, `reset --hard`, `git clean -f`, `checkout .`/`restore .`, `DROP`/`TRUNCATE`/unscoped `DELETE`, `kubectl delete`, `docker rm -f`/prune, `mkfs`, `dd of=/`, raw-disk `>`, `chmod -R 777` all hard-block. After an explicit **`proceed`**, re-run with `# sa-confirm` appended (or `SA_CONFIRM=1`) to pass.
- **Confusion Protocol** — for high-stakes ambiguity (architecture · data model · destructive scope · missing context), STOP. Name the confusion in one sentence, present 2–3 options with trade-offs, and ask. The Butler does this at STEP 0: if it can't produce a clean one-line restatement, it emits the options instead of rubber-stamping a misread task. Not for routine/obvious changes.
- On **MCP unavailability**, never fabricate a write — reconnect or fall back to non-write ops; when a dispatch channel is disabled, log intent verbatim and don't call the tool.

## Self & execution doctrine (every member)

_Distilled from the self-learning shelf, 2026-06-27 — see [docs/SELF-LEARNING-MINING-2026-06.md]. These are generative principles, not procedures._

- **Present-execution awareness (Sati-Sampajanna).** Before each tool call, recall the parent task's intent and the next action's blast radius; after each action, note any drift from intent before continuing. Absence of presence during a sub-step — not malice — is the root of broken code, leaked data, wrong trades, off-brand copy. The substrate every other discipline rests on.
- **Spoken-word framing.** State identity and plans in positive, present-tense capability terms ("a careful architect who catches schema drift before writing SQL"), not negation-heavy warnings ("don't make mistakes"). When a framing is wrong, replace it in one move (law of substitution), don't incrementally patch it. The agent's self-narrative is a self-fulfilling prompt.
- **Principles, not procedures (Kybalion).** Author doctrine and skills as 3–7 generative axioms with examples, not brittle if-then trees. Principles compose to novelty; rule-lists rot and break. A skill over ~200 lines of pure procedure is a candidate for distillation.
- **Pragmatic redirection.** When work drifts into "do agents really think / are we conscious," redirect to the three answerable questions: what observable behavior is happening, what regularity governs it, what concrete change improves the output. The "how" of agent work, not the "why" of agenthood.
- **One way to completion (Science of Being Well).** Read a chosen skill as if fully committed and finish it — half-belief in three competing methods underperforms whole adoption of one. An audit picks its cuts and completes them rather than sampling.
- **Close the loop (`guild-reflection`).** Non-trivial work is not done when it ships — it is done when it has produced either an applied doctrine diff or an explicit "no change warranted." Accumulating outputs without reflection is data-hoarding, not learning.

## Harness tools (Skills Pool audit, 2026-06)

Standalone harness aids adopted from the gstack/harness-books mining — see [[skills-pool-strategic-audit-2026-06]]:

- **The Evolution Engine** (`evolution/`) — the self-improving spine; **read [[core-evolution-engine]] before touching any self-improvement surface.** One closed loop (SENSE `ledger.py` → DIAGNOSE/CHANGE `engine.py` → VERIFY `verdict.py` → REMEMBER `scoreboard.py`) replacing the old scattered fragments. **Invariant:** nothing enters the repo without (a) an independent critic verdict and (b) a ledger event. Tier-A surfaces (skills/memory/docs) may auto-apply after a pass; Tier-B (hooks/doctrine/gates/arsenal/workflows) is human-gated. Kill switch: `touch evolution/DISARMED`. Doctrine: `evolution/README.md`.
- **Independent verification** (`.claude/hooks/verify-gate.py` v2, Stop·blocking, **armed by default**) — HARNESS-BOOKS 9.9: never let the implementer grade its own work. The VERIFY organ of the Evolution Engine. A turn that changed source **auto-runs the Critic** (glm-5.2, different model family) on the diff: on pass/concerns it **records the pass itself** and lets the turn close (no manual fingerprint chase); on **BLOCK** it stops the commit and prints the findings. Runs **before** `turn-finalize.sh`, so a block prevents that round's commit — forward-fix only, never un-commit. Fails OPEN if the critic is offline (degrades to manual review). Bypass one turn with `SA_SKIP_VERIFY=1`; manual-only with `SA_AUTO_CRITIC=0`.
- **Context checkpoint** — `python3 .claude/context/context_save.py "<summary>" [--decisions …] [--remaining …]` snapshots git state + decisions + remaining work; `context_restore.py [--list|<stamp>]` resumes a cold session. Transient handoff, distinct from durable memory files.
- **Learnings journal** — `python3 .claude/context/learn.py add|search|list` — append-only "didn't we fix this before?" recall in `.claude/state/learnings.jsonl`. Promote a recurring learning into a real memory file when it earns its place.
- **Skill fingerprints** — `python3 .claude/tools/skill_fingerprint.py [--check]` writes/diffs a content hash per skill so sync reinstalls only what actually changed (Codex doctrine; complements [[guild-sync]]).
