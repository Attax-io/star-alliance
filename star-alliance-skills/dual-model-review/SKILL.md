---
name: dual-model-review
description: "The dual-review flow that backs the cross-system bridge. A specialist CLI profile receives an order from a Claude Code subagent, dispatches MiniMax-M3 (the doer) to do the actual work, and simultaneously fires Kimi K2.7 (Ollama Cloud) and GLM-5.2 (Ollama Cloud) as parallel reviewer sub-agents through Hermes. Both reviewers must independently pass before the work is reported back. Triggers: 'dual review', 'two reviewers', 'kimi and glm review', 'review in parallel', 'M3 does, reviewers check', 'three-way review', or any time a profile is about to declare a piece of work done for the cross-system bridge. Pairs with weapon-utility (seat doctrine — M3 is the doer, Kimi + GLM are independent thinkers), decompose-and-swarm (when many slices each need dual review), and the cross-system dispatch bridge (tools/dispatch.py)."
metadata:
  version: 1.0.0
type: Skill
---

# Dual-Model Review

The dual-review flow is the cross-system bridge's quality gate. A specialist CLI
profile (Architect, Developer, Designer, Herald, Merchant, Quartermaster,
Translator) receives an order from a Claude Code subagent. It dispatches
**MiniMax-M3** as the doer to do the work, then in **parallel** fires two
**Ollama Cloud** thinker reviewers — **Kimi K2.7** and **GLM-5.2** — through
Hermes sub-agents. Both reviewers must independently PASS before the profile
returns the result to the bridge.

This skill is the **runtime contract** that makes every profile agree on what
"done" means when serving the cross-system bridge.

## What it is / is not

**It is:**
- The standard three-stance review shape used by every CLI profile when serving
  orders from the Claude Code bridge: **1 doer + 2 reviewers in parallel**.
- The explicit, machine-checkable fix for the recurring
  `ollama launch hermes --model X:cloud` invocation error (see §Pitfalls).
- A doctrine of independent verdict, not a fixed script — the reviewer prompts
  are tuned per profile (the Designer reviews visual output; the Merchant
  reviews numerical analysis), but the **shape is universal**.

**It is not:**
- A replacement for the agent's own brain. The brain (the profile's session
  model) still plans, integrates, and reports. M3 does the bulk; the cloud
  reviewers are the independent second pair of eyes — the agent itself remains
  responsible for the final decision.
- A licence to skip [[weapon-utility]] seat doctrine. M3 is the doer (no
  tools). Kimi + GLM are thinkers (tool-capable inside their sub-agent shells).
  Never reverse the seats — see §The seat triangle.
- An always-on review. For trivial work (rename one symbol, copy a file),
  dual review is overkill. See §When to dual-review.

---

## The seat triangle

The dual-review flow holds **three seats at once**. Knowing which model sits in
which seat — and never confusing them — is the load-bearing rule.

```
                       ┌──────────────────────────┐
                       │  Profile brain (thinker) │
                       │  plans + integrates      │
                       └──────────┬───────────────┘
                                  │ dispatches
              ┌───────────────────┴─────────────────────┐
              │                                         │
              ▼                                         ▼
   ┌────────────────────┐                  ┌────────────────────────┐
   │  Doer seat         │                  │  Reviewer seats        │
   │  minimax-m3        │                  │  kimi-k2.7 (cloud)     │
   │  no tools          │                  │  glm-5.2 (cloud)       │
   │  generates the     │                  │  tool-capable thinkers │
   │  artifact          │                  │  fire PARALLEL through │
   └────────────────────┘                  │  Hermes sub-agents     │
                                           └────────────────────────┘
```

- **Doer (minimax-m3)** — the hands. Generates the artifact (code, prose,
  data, markup). Returns text. Holds no Hermes tools — does not patch, write,
  run terminal, or call MCP. This is the §"tool boundary (hard rule)" in
  [[weapon-utility]]: a doer never invokes tools.
- **Reviewers (kimi-k2.7 + glm-5.2)** — both are **Ollama Cloud** bench
  weapons. They are *thinkers* (tool-capable inside their sub-agent shells),
  so each reviewer sub-agent CAN run grep/build/read to verify the artifact.
  They fire **simultaneously** through two Hermes sub-agent dispatches, not
  one after the other.
- **Brain (the profile's session model)** — the integrator. Reads both
  reviewer verdicts, reconciles disagreement, and returns a single PASS /
  CONCERNS / BLOCK to the calling Claude Code subagent.

**Independence rule.** The two reviewer families are deliberately different:
Kimi K2.7 (Moonshot, agentic long-horizon) and GLM-5.2 (Zhipu, coding-first,
multilingual). A reviewer that shares the doer's lineage shares its blind
spots. Two reviewer families = diverse blind spots = the point, not a
coincidence. (This is the same `critic-family != brain-family` invariant
[[weapon-utility]] enforces.)

---

## When to dual-review — and when not to

Dual-review is **standard for the cross-system bridge**, but it is not free.
The two cloud reviewers each cost a request to Ollama Cloud and add wall-clock
parallel latency. So the rule is:

**Dual-review IS the default when:**
- The work touches source files that will be committed (`git diff` after the
  work is non-trivial).
- The deliverable is a public artifact — an article, a legal instrument, a
  campaign, a published analysis.
- The Claude Code subagent's brief says "important" / "production" /
  "user-facing" / "ship" — i.e. anything that won't be caught by the
  developer's local test loop.
- The work is irreversible or expensive to redo (migrations, deploys,
  schema changes, large file deletes).

**Dual-review is OVERKILL when:**
- The change is mechanical and verifiable by a tool (rename one symbol,
  format a file, copy a directory).
- The work is throwaway — a spike, a one-off probe, an exploration.
- A reviewer cannot meaningfully add information (e.g. reviewing a single
  one-line typo).
- The Claude Code subagent's brief is "quick check" / "draft only" /
  "I'll review myself."

When skipping, **say so explicitly in the report to the bridge** —
*"skipped dual review: mechanical rename, verified by tool"*. The bridge
expects the report to be honest about what ran, not silent about what didn't.

---

## The five-step flow

Every dual-reviewed mission runs these five steps in this order. Skipping a
step is a violation.

### Step 1 — Plan and prompt

The profile's brain reads the order from the Claude Code bridge. Writes:
- a one-line routing label for the brain (e.g. "You are the Developer — task:
  implement the foo middleware").
- the M3 doer prompt — a self-contained brief with file paths, contracts,
  acceptance test. Keep under ~2k tokens.
- the two reviewer prompts — each a self-contained brief that names the
  artifact under review, the dimension to review (correctness, security,
  style, completeness — vary it), and the verdict format
  (PASS / CONCERNS / BLOCK with one-line reason).

The reviewer prompts SHOULD disagree on **dimension** (one reviews for
correctness, the other for security or completeness) — that is how two
different families add unique signal instead of duplicating each other.

### Step 2 — Dispatch the doer (M3)

```bash
python3 star-alliance-arsenal/minimax.py "<doer-prompt>"
# or, when reading from a file:
python3 star-alliance-arsenal/minimax.py -f doer-prompt.md
# sized for big generations:
python3 star-alliance-arsenal/minimax.py "<doer-prompt>" --max-tokens 16000 --timeout 600
```

The doer returns the artifact as text. The brain **reviews it inline against
the plan** (the thinker↔doer loop from [[weapon-utility]]) — re-prompting M3
on non-conforming output, escalating only when M3 cannot bring the artifact
into shape.

### Step 3 — Fire the two reviewers IN PARALLEL through Hermes sub-agents

This is the load-bearing step. Both reviewers run **simultaneously** in a
single assistant turn — two `delegate_task` calls in one message, not in
sequence.

Each reviewer sub-agent:
1. Loads the artifact (passed in the brief, or read from disk if the brief
   includes the path).
2. Runs its review dimension — correctness, security, completeness, etc.
3. Returns a structured verdict:

   ```
   VERDICT: PASS | CONCERNS | BLOCK
   DIMENSION: <what was reviewed>
   EVIDENCE: <one-line reason, with file/line/snippet if applicable>
   SUGGESTED FIX: <optional, one line>
   ```

**Why parallel, not sequential.** Sequential review doubles the wall-clock
budget; parallel review uses the same time as one review. The Ollama Cloud
concurrency cap (Free=1, Pro=3, Max=10) is the only rate limit — and it's
already handled by `ollama_cloud.py`'s `_Semaphore` cross-process lock, so
the two parallel dispatches will queue locally until a slot opens, never
silently lose the overflow.

### Step 4 — Integrate the two verdicts

The brain reads both verdicts and decides:

| Verdict A | Verdict B | Integrated result |
|---|---|---|
| PASS | PASS | **Ship.** Both reviewers agree. Return result to bridge. |
| PASS | CONCERNS | **Ship with notes.** Apply the CONCERNS as a follow-up if cheap, or document them in the report. |
| PASS | BLOCK | **Block.** A single BLOCK stops the ship. Re-dispatch the doer with the BLOCK's reason. |
| CONCERNS | CONCERNS | **Block — two concerns compound.** Treat as BLOCK unless both are cosmetic. |
| CONCERNS | BLOCK | **Block.** |
| BLOCK | BLOCK | **Block.** |

A disagreement between the two reviewers (one PASS, one BLOCK) is **the
canonical signal that the review is working** — diverse blind spots caught
something one family missed. Don't average; respect the BLOCK.

### Step 5 — Report to the bridge

Return a single structured report to the calling Claude Code subagent. The
report MUST include:
- WHAT was done (the artifact, file paths, hashes if material).
- The two reviewer verdicts (verbatim).
- The integrated result.
- Anything skipped (with reason) — see §When not to dual-review.

If a reviewer sub-agent timed out or errored, **say so** in the report —
*"Kimi review timed out at 180s; GLM PASSED; partial dual review"*. The
bridge cannot recalibrate if it doesn't know what actually ran.

---

## Invocation — the right way

The recurring error this skill fixes:

```bash
# ❌ WRONG — silently no-ops. `ollama launch hermes` is an integration
# launcher that does NOT accept --model. Only claude/codex/droid do
# (per `ollama launch --help`). No error is raised — Hermes just opens
# with the user's existing model, ignoring --model entirely.
ollama launch hermes --model glm-5.2:cloud
ollama launch hermes --model kimi-k2.7-code:cloud
```

The right invocations for Kimi + GLM through the project's arsenal:

```bash
# ✅ Route through summon.py — translates guild model id → cloud tag,
# handles the Ollama Cloud concurrency cap, logs to the usage ledger
# under the canonical id. This is the entry point every profile uses.

python3 star-alliance-arsenal/summon.py glm-5.2     "<prompt>"
python3 star-alliance-arsenal/summon.py kimi-k2.7   "<prompt>"

# With sizing for big generations (see §"Sizing a big doer job" in
# weapon-utility). --max-tokens translates per backend (--num-predict
# for cloud models) automatically.
python3 star-alliance-arsenal/summon.py glm-5.2 \
    -f reviewer-prompt.md --max-tokens 4096 --timeout 300

# Read prompt from stdin (piped):
echo "<prompt>" | python3 star-alliance-arsenal/summon.py kimi-k2.7 -
```

M3 (the doer) has its own direct entry point — no `summon.py` needed because
M3 has only one backend:

```bash
python3 star-alliance-arsenal/minimax.py "<prompt>"
python3 star-alliance-arsenal/minimax.py -f doer-prompt.md
python3 star-alliance-arsenal/minimax.py "<prompt>" --max-tokens 16000 --timeout 600
```

**Why `summon.py` matters for Kimi + GLM specifically.** Kimi and GLM live on
Ollama Cloud, accessed through the local Ollama daemon's `/api/chat`
endpoint. `summon.py` is the only entry point that:
1. Maps the guild id (`kimi-k2.7`) to the cloud tag (`kimi-k2.7-code:cloud`)
   via the canonical registry (`star-alliance-arsenal/models.json`). The
   tag is what the daemon expects on the wire.
2. Holds the Ollama Cloud concurrency semaphore so parallel reviewers
   don't get silently rejected with 429/503 when the plan's slot count
   is exceeded.
3. Logs usage to `usage-log.jsonl` keyed by the canonical guild id — so
   the dashboard's per-model meter reflects real spend.

Calling `ollama_cloud.py kimi-k2.7-code:cloud "..."` directly works too,
but `summon.py kimi-k2.7 "..."` is preferred because it goes through the
registry.

---

## Pitfalls

These are the failure modes that have actually bitten dual-review runs.
Load them before you start.

### 1. `ollama launch hermes --model X:cloud` — the silent no-op

See §Invocation above. The `hermes` integration in `ollama launch` does NOT
accept `--model` (only claude/codex/droid do per `ollama launch --help`).
The command exits 0 with no model override. **Never use this path.** Always
use `summon.py` or `ollama_cloud.py` directly.

### 2. Prompt-after-optionals argparse trap (now fixed)

`summon.py` historically built argv as
`ollama_cloud.py <model> --num-predict N --timeout T "<prompt>"`. Because
`ollama_cloud.py` declares `prompt` with `nargs="?"`, argparse greedily
consumed the optionals first and then refused the trailing prompt as
"unrecognized arguments". Fixed in summon.py by adding a `prompt_first=True`
mode that puts the prompt immediately after the model positional.
**If you see `error: unrecognized arguments:` from ollama_cloud.py, your
argv order is wrong** — the prompt must come BEFORE the optionals.

### 3. Concurrency cap silently rejects overflow

Ollama Cloud caps concurrent models per plan (Free=1, Pro=3, Max=10). Past
the cap, requests queue, then return 429/503 once the queue fills. A naive
dual-review that fires Kimi + GLM in parallel while something else is
already using the one free slot will see one reviewer fail. `summon.py`'s
built-in semaphore serializes them locally — but if you call `ollama_cloud.py`
directly from your own script, **you must respect the same semaphore**, or
set `OLLAMA_MAX_CONCURRENT` to your plan's slot count.

### 4. Empty content from num-predict starvation

The cloud models burn a non-trivial fraction of `--num-predict` on internal
thinking tokens. A request with `--max-tokens 256` often returns empty
content because the thinking ate the entire budget. **Default to ≥4096 for
cloud models** and only lower it for short-form answers where you've
verified the model doesn't think first.

### 5. Reversing the seats

Calling `summon.py minimax-m3` and asking it to "review this code" is a
category error: M3 is a doer and holds no tools — it cannot grep, run the
build, or read a file. The reviewer sub-agents are thinkers (Kimi + GLM),
and they CAN run tools inside their sub-agent shells. If you need a reviewer
to verify a file path or run a command, dispatch Kimi or GLM, not M3.

### 6. Forgetting to report what ran

The cross-system bridge needs to know which reviewers actually returned.
A review sub-agent that timed out and was retried should be logged in the
report — *"Kimi timed out once, retried with reduced prompt, PASS on retry;
GLM PASSED first try"*. The bridge cannot recalibrate if the report is
silent about partial runs.

### 7. Duplicated review dimensions

If both reviewers review for the same dimension (e.g. both check
correctness), they will produce near-identical verdicts — the second
reviewer adds zero unique signal. Assign **different dimensions**
(correctness + security, completeness + style, etc.) so the diverse blind
spots of the two families actually compound.

### 8. Reporting the artifact, not the verdict

The brain integrates the verdicts — that's its job. The report to the
bridge should report **the integrated decision**, not just dump the raw
verdicts and make the bridge integrate. Two PASS verdicts become
"shipped"; one PASS + one CONCERNS becomes "shipped with notes: …".
A raw verdict dump is a hand-off failure.

---

## Cross-links

- [[weapon-utility]] — the seat doctrine (Brain/Doer/Bench).
  Dual-review uses the Doer seat (M3) for generation and the Bench
  reviewers (Kimi + GLM as thinker sub-agents) for review. Never reverse.
- [[decompose-and-swarm]] — when many slices each need dual review,
  fan out the slices AND fan out two reviewers per slice. Same parallel
  patterns, just one level deeper.
- [[star-alliance-language]] — the report to the bridge is plain English,
  jargon-free, names the verdicts and the integrated result. No stack
  traces, no model code-names the user has to decode.
- The cross-system dispatch bridge — `tools/dispatch.py` in the Claude
  Code project; the hooks at `~/.claude/hooks/sa-pretool.py` route every
  Claude specialist's tool call through dispatch.py to its matching
  Hermes profile.

## Changelog

- **1.0.0** — Initial release. Seat triangle (M3 doer + Kimi/GLM reviewers
  in parallel), five-step flow (plan / do / parallel review / integrate /
  report), explicit invocation rules (use `summon.py`, never
  `ollama launch hermes --model`), pitfalls (silent no-op, argparse trap,
  concurrency cap, num-predict starvation, seat reversal, missing-report,
  duplicated dimensions, raw-verdict hand-off).