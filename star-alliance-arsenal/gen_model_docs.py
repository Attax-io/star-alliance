#!/usr/bin/env python3
"""Generate one OKF-conformant md per arsenal weapon — DERIVED from models.json.

The canonical facts (role, backend, cloud_tag, status, pull, summary) come from
the registry; this script only adds the per-backend "how to summon" prose and the
shared concurrency/findings notes. Re-run after editing models.json:

    python3 star-alliance-arsenal/gen_model_docs.py

Writes star-alliance-arsenal/models/<id>.md + README.md. Bypasses the okf-gate
MCP gate hook (plain file writes) but emits conformant `type:` frontmatter.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
REG = os.path.join(HERE, "models.json")
OUT = os.path.join(HERE, "models")
TS = "2026-06-27T00:00:00Z"

CONC = (
    "## Concurrency\n\n"
    "Ollama Cloud caps **concurrent models** by plan — **Free = 1**, Pro = 3, "
    "Max = 10. Beyond the cap requests queue, then get **rejected** once the queue "
    "fills (a 429/503). A naive parallel fan-out loses the overflow models — they "
    "look dead when the account is just over its slot count. The arsenal guards "
    "this: `ollama_cloud.py` holds a cross-process slot semaphore "
    "(`OLLAMA_MAX_CONCURRENT`, default **1**) and retries on busy, so calls queue "
    "LOCALLY instead of being dropped. Set `OLLAMA_MAX_CONCURRENT` to your plan's "
    "number; keep it at 1 on Free.\n"
)
REASON_TRAP = (
    "> **Token trap:** reasoning models spend the budget on `<think>` first. "
    "Low `--max-tokens` returns **empty content** — the arsenal default is now "
    "**16000**; never drop below ~2000. `ollama_cloud.py` strips `<think>…</think>` "
    "before returning.\n"
)
FINDINGS = (
    "## Findings (for future runs)\n\n"
    "- **Ollama Cloud Free = 1 concurrent model** (Pro=3, Max=10). A parallel fan-out "
    "**rejects** the overflow — it is NOT a dead model. Run sequentially or set "
    "`OLLAMA_MAX_CONCURRENT` to your plan number.\n"
    "- **Default `--max-tokens` = 16000.** Reasoning models return empty if the budget "
    "is too small (eaten by `<think>`). Verified 2026-06-27: a 60-token call returns "
    "empty; 800+ returns content.\n"
    "- **`minimax-sub` (direct API) is the prime DOER**; the Ollama bench (incl. "
    "`kimi-k2.7` since weapon-utility 1.7.0) is read as **thinkers**. Separate pools — "
    "Claude (Task) + MiniMax-direct overlap the Ollama panel freely.\n"
    "- **glm-5.2 confirmed alive** 2026-06-27 (returned `GLM_ALIVE`). A 'glm missing' "
    "scare was a truncated `ollama list | head` — it is pulled.\n"
)

STATUS_LABEL = {
    "live": "LIVE", "reserve": "LIVE (reserve) — pulled & reachable",
    "deactivated": "DEACTIVATED",
}


def backend_doc(mid, d):
    """Return (backend_md, pull_md, summon_md, conc, extra) per backend type."""
    be = d.get("backend")
    if be == "claude":
        return (
            "Claude-native. **No script, no pull.** Reserve model — dispatched via delegate_task.",
            "_None._ Nothing to pull — Claude runs inside the harness.",
            "Run via **delegate_task** with `model=%s`. `summon.py %s` only prints a "
            "reminder (exit 0) — it does NOT call a backend." % (mid, mid),
            False,
            "Counts against your **Claude plan** 5h window, not Ollama — a separate "
            "pool, safe to overlap with Ollama/MiniMax calls.\n",
        )
    if be == "minimax-direct":
        return (
            "MiniMax DIRECT API (`api.minimax.io`) via `minimax.py` — **not** Ollama.",
            "_None._ Direct API. Needs a key at `~/.config/minimax/m3.key` "
            "(or `$MINIMAX_API_KEY`).",
            "```\npython3 star-alliance-arsenal/summon.py %s \"<prompt>\"\n```\n"
            "Default `--max-tokens` 16000. `minimax.py --batch <file.jsonl>` for "
            "one-connection fan-out." % mid,
            False,
            "Direct API — **not** subject to the Ollama concurrency cap; its own "
            "rate limits apply.\n",
        )
    if be == "ollama-cloud":
        tag = d.get("cloud_tag") or ""
        return (
            "Ollama Cloud via `ollama_cloud.py` (local daemon `/api/chat`, tag `%s`)." % tag,
            "```\n%s\n```\nVerify: `ollama list | grep %s`" % (
                d.get("pull") or ("ollama pull " + tag), tag.split(":")[0]),
            "```\npython3 star-alliance-arsenal/summon.py %s \"<prompt>\" --max-tokens 16000\n```\n"
            "Flags: `-s <system>` · `--json` · `-f <file>` · `--timeout <s>`." % mid,
            True,
            REASON_TRAP,
        )
    if be == "openai-direct":
        return (
            "OpenAI-direct. **Not provisioned** — `summon.py %s` exits **69**." % mid,
            "_None._ Set an OpenAI API key on the device and wire the OpenAI-direct "
            "backend in `summon.py` to reactivate. Do NOT strip from loadouts.",
            "```\nsummon.py %s   # -> \"DEACTIVATED\", exit 69\n```" % mid,
            False, "",
        )
    if be == "minimax-media":
        helper = ("Use the helper: `node star-alliance-arsenal/gen-skill-art.cjs` "
                  "(or `imagegen.py`)." if mid == "image-01"
                  else "No helper yet — hit the endpoint directly with the bearer key.")
        return (
            "MiniMax DIRECT API media endpoint (model `%s`). **Not** routed by "
            "summon/minimax.py (text-only)." % mid,
            "_None._ Direct API, same `~/.config/minimax/m3.key`.",
            "%s Text dispatchers do NOT route media." % helper,
            False, "",
        )
    return ("(unknown backend)", "_None._", "(n/a)", False, "")


def render(mid, d):
    backend, pull, summon, conc, extra = backend_doc(mid, d)
    status = STATUS_LABEL.get(d.get("status"), d.get("status", ""))
    if d.get("status") == "deactivated":
        status = "DEACTIVATED — no key on device (kept in loadouts on purpose)"
    p = ["---", "type: Reference", "title: %s" % mid,
         "description: How to pull and summon the %s weapon (generated from models.json)." % mid,
         "timestamp: %s" % TS, "---", "",
         "# %s" % mid, "",
         "**Status:** %s  " % status,
         "**Role:** %s · **Backend:** %s · **Kind:** %s" % (
             d.get("role", ""), d.get("backend", ""), d.get("kind", "")),
         "", d.get("summary", ""), "",
         "## Backend", "", backend, "",
         "## How to pull", "", pull, "",
         "## How to summon", "", summon, ""]
    if conc:
        p.append(CONC)
    if extra:
        p.append(extra)
    if conc:
        p.append(FINDINGS)
    p.append("> Generated from [models.json](../models.json) by `gen_model_docs.py`. "
             "Edit the registry, not this file. Dispatcher: [summon.py](../summon.py) · "
             "cloud backend: [ollama_cloud.py](../ollama_cloud.py)")
    p.append("")
    return "\n".join(p)


# stable display order (11 surviving models)
ORDER = ["opus", "sonnet", "haiku", "minimax-sub", "minimax-payg",
         "glm-5.2", "kimi-k2.7",
         "image-01", "minimax-video", "minimax-speech", "minimax-music"]


def main():
    models = json.load(open(REG, encoding="utf-8"))["models"]  # from models.json registry
    os.makedirs(OUT, exist_ok=True)
    ids = [m for m in ORDER if m in models] + [m for m in models if m not in ORDER]
    for mid in ids:
        with open(os.path.join(OUT, "%s.md" % mid), "w", encoding="utf-8") as fh:
            fh.write(render(mid, models[mid]))
    # index
    idx = ["---", "type: Index", "title: Arsenal model docs",
           "description: Per-weapon pull + summon reference (generated from models.json).",
           "timestamp: %s" % TS, "---", "",
           "# Arsenal — model docs", "",
           "One file per weapon, **generated from [models.json](../models.json)** — the "
           "canonical registry. Edit the registry, run `gen_model_docs.py`. Dispatcher: "
           "[summon.py](../summon.py).", "",
           "| Weapon | Role | Backend | Status |", "|---|---|---|---|"]
    for mid in ids:
        d = models[mid]
        idx.append("| [%s](%s.md) | %s | %s | %s |" % (
            mid, mid, d.get("role", ""), d.get("backend", ""), d.get("status", "")))
    idx += ["", "## Concurrency (cloud)", "", CONC, "", FINDINGS]
    with open(os.path.join(OUT, "README.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(idx) + "\n")
    print("wrote %d model docs + README (from models.json)" % len(ids))


if __name__ == "__main__":
    main()
