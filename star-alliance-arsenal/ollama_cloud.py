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
import urllib.error
import urllib.request


_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL)
_FENCE_RE = re.compile(r"^\s*```(?:json)?\s*\n?(.*?)\n?\s*```\s*$", re.DOTALL)


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

    try:
        with urllib.request.urlopen(req, timeout=args.timeout) as resp:
            raw = resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        print(
            "ollama_cloud: HTTP error {} {}: ".format(e.code, e.reason)
            + "is the ollama daemon running? is the :cloud model pulled?",
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

    # Token usage to stderr if present
    pec = data.get("prompt_eval_count")
    ec = data.get("eval_count")
    if pec is not None or ec is not None:
        pec_s = pec if pec is not None else 0
        ec_s = ec if ec is not None else 0
        print(
            "ollama_cloud: {}+{} tokens".format(pec_s, ec_s),
            file=sys.stderr,
        )

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
