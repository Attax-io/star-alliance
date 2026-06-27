#!/usr/bin/env python3
"""
ollama_cloud.py - Call a local Ollama daemon's chat API for Ollama CLOUD models.

Examples:
  # 1. Simple prompt from argument, with a system prompt
  python ollama_cloud.py glm-5.2:cloud "Explain quantum entanglement in 3 sentences." -s "You are a concise physics tutor."

  # 2. Read prompt from stdin (piped input) and validate JSON output
  echo "Return a JSON object with keys name and age for a fictional person." | python ollama_cloud.py glm-5.2:cloud - --json

  # 3. Read prompt from a file with a custom timeout and num_predict
  python ollama_cloud.py glm-5.2:cloud -f prompt.txt --num-predict 8192 --timeout 300
"""

import argparse
import json
import os
import re
import sys
import tempfile
import time
import urllib.error
import urllib.request

try:
    import fcntl  # POSIX only; concurrency guard degrades to no-op without it
except ImportError:  # pragma: no cover - non-POSIX
    fcntl = None


_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL)
_FENCE_RE = re.compile(r"^\s*```(?:json)?\s*\n?(.*?)\n?\s*```\s*$", re.DOTALL)

# --- Concurrency guard -------------------------------------------------------
# Ollama Cloud caps CONCURRENT models by plan: Free=1, Pro=3, Max=10. Beyond the
# cap requests are queued, then REJECTED once the queue fills. A naive parallel
# fan-out (e.g. ultra-brainstorming firing 5 thinkers at once) therefore loses
# the overflow models silently — they look "dead" when the account is just over
# its slot count. This cross-process semaphore makes the arsenal queue LOCALLY
# instead: at most OLLAMA_MAX_CONCURRENT cloud calls hold a slot at a time; the
# rest block until one frees. Set it to your plan's number (default 1 = Free).
_SLOT_DIR = os.path.join(tempfile.gettempdir(), "sa-ollama-slots")
_BUSY_CODES = {429, 503}


def _max_concurrent():
    try:
        return max(1, int(os.environ.get("OLLAMA_MAX_CONCURRENT", "1")))
    except (TypeError, ValueError):
        return 1


class _Semaphore:
    """N-slot cross-process lock via flock on N files. No-op if fcntl absent."""

    def __init__(self, n, wait_timeout):
        self.n = max(1, n)
        self.wait_timeout = wait_timeout
        self._fh = None

    def acquire(self):
        if fcntl is None:
            return True
        try:
            os.makedirs(_SLOT_DIR, exist_ok=True)
        except Exception:
            return True  # can't make slot dir -> don't block the call
        deadline = time.monotonic() + self.wait_timeout
        while True:
            for i in range(self.n):
                path = os.path.join(_SLOT_DIR, "slot-%d.lock" % i)
                try:
                    fh = open(path, "w")
                    fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    self._fh = fh
                    return True
                except OSError:
                    try:
                        fh.close()
                    except Exception:
                        pass
            if time.monotonic() >= deadline:
                print(
                    "ollama_cloud: all {} concurrency slot(s) busy after {}s "
                    "wait - proceeding anyway (may be queued/rejected by Ollama)".format(
                        self.n, self.wait_timeout
                    ),
                    file=sys.stderr,
                )
                return False
            time.sleep(1.5)

    def release(self):
        if self._fh is not None:
            try:
                fcntl.flock(self._fh.fileno(), fcntl.LOCK_UN)
                self._fh.close()
            except Exception:
                pass
            self._fh = None


def strip_think(text):
    """Remove <think>...</think> blocks from text (DOTALL)."""
    if not text:
        return text
    return _THINK_RE.sub("", text).strip()


def strip_fences(text):
    """Strip leading/trailing ``` or ```json fences and surrounding whitespace."""
    if text is None:
        return ""
    s = text.strip()
    m = _FENCE_RE.match(s)
    if m:
        return m.group(1).strip()
    return s


def main():
    parser = argparse.ArgumentParser(
        description="Call a local Ollama daemon chat API for Ollama CLOUD models."
    )
    parser.add_argument("model", help="Cloud model tag, e.g. glm-5.2:cloud")
    parser.add_argument(
        "prompt",
        nargs="?",
        default=None,
        help="Prompt text; use '-' or omit to read stdin (if no -f).",
    )
    parser.add_argument("-s", "--system", default="", help="System prompt")
    parser.add_argument(
        "-f", "--file", default=None, help="Read prompt from this file instead"
    )
    parser.add_argument(
        "--num-predict",
        type=int,
        default=4096,
        help="Max tokens to predict (default 4096; do not lower - thinking eats the budget)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Strip code-fences, validate as JSON, re-dump compact on success",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=180,
        help="HTTP timeout in seconds (default 180)",
    )
    args = parser.parse_args()

    # Resolve prompt source
    if args.file:
        with open(args.file, "r", encoding="utf-8") as fh:
            prompt = fh.read()
    elif args.prompt is None or args.prompt == "-":
        prompt = sys.stdin.read()
    else:
        prompt = args.prompt

    host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
    url = host.rstrip("/") + "/api/chat"

    messages = []
    if args.system:
        messages.append({"role": "system", "content": args.system})
    messages.append({"role": "user", "content": prompt})

    body = {
        "model": args.model,
        "messages": messages,
        "stream": False,
        "options": {"num_predict": args.num_predict},
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    # Hold a concurrency slot for the whole call so we never exceed the plan's
    # cap; on a queue-full / busy reply (429/503) back off and retry rather than
    # losing the model. Slot wait is generous (cloud calls are slow).
    slot_wait = max(args.timeout, 240)
    sem = _Semaphore(_max_concurrent(), slot_wait)
    sem.acquire()
    _t0 = time.monotonic()
    raw = None
    try:
        for attempt in range(5):
            try:
                with urllib.request.urlopen(req, timeout=args.timeout) as resp:
                    raw = resp.read().decode("utf-8")
                break
            except urllib.error.HTTPError as e:
                if e.code in _BUSY_CODES and attempt < 4:
                    backoff = 2 ** attempt  # 1,2,4,8s
                    print(
                        "ollama_cloud: busy ({}), retry {}/4 in {}s".format(
                            e.code, attempt + 1, backoff
                        ),
                        file=sys.stderr,
                    )
                    time.sleep(backoff)
                    continue
                print(
                    "ollama_cloud: HTTP error {} {}: ".format(e.code, e.reason)
                    + "is the ollama daemon running? is the :cloud model pulled? "
                    + "(429/503 = over your Ollama plan's concurrency cap — "
                    + "lower OLLAMA_MAX_CONCURRENT or upgrade the plan)",
                    file=sys.stderr,
                )
                sys.exit(4)
            except urllib.error.URLError as e:
                reason = getattr(e, "reason", e)
                print(
                    "ollama_cloud: URL error: {}: ".format(reason)
                    + "is the ollama daemon running? is the :cloud model pulled?",
                    file=sys.stderr,
                )
                sys.exit(4)
    finally:
        sem.release()

    wall_ms = int((time.monotonic() - _t0) * 1000)

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        print(
            "ollama_cloud: failed to parse response JSON: {}".format(e),
            file=sys.stderr,
        )
        sys.exit(4)

    message = data.get("message") or {}
    content = message.get("content")
    if content is None:
        content = ""
    content = strip_think(content)

    # Token usage to stderr if present, and to the shared delegation ledger.
    pec = data.get("prompt_eval_count")
    ec = data.get("eval_count")
    pec_s = pec if pec is not None else 0
    ec_s = ec if ec is not None else 0
    if pec is not None or ec is not None:
        print(
            "ollama_cloud: {}+{} tokens".format(pec_s, ec_s),
            file=sys.stderr,
        )
    # Log under the guild model id (summon.py sets SA_MODEL_ID); direct callers
    # fall back to stripping the ":cloud" suffix off the tag.
    try:
        from arsenal_usage import log_usage
        model_id = os.environ.get("SA_MODEL_ID") or args.model.replace(":cloud", "")
        log_usage(model_id, "ollama", pec_s, ec_s, wall_ms=wall_ms)
    except Exception:
        pass

    if not content:
        print(
            "ollama_cloud: empty content - raise --num-predict",
            file=sys.stderr,
        )
        sys.exit(5)

    if args.json:
        candidate = strip_fences(content)
        try:
            obj = json.loads(candidate)
        except json.JSONDecodeError:
            print(candidate, file=sys.stderr)
            sys.exit(3)
        sys.stdout.write(json.dumps(obj, separators=(",", ":")))
        sys.stdout.write("\n")
    else:
        sys.stdout.write(content)
        if not content.endswith("\n"):
            sys.stdout.write("\n")

    sys.exit(0)


if __name__ == "__main__":
    main()
