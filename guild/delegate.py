"""delegate.py — thin subprocess wrapper around star-alliance-arsenal/summon.py.

Importable API:
    delegate(model, prompt, system=None, file=None, timeout=300) -> str
    delegate_many(prompts, model="minimax-sub", timeout=600) -> list[str | None]

CLI:
    python3 guild/delegate.py <model> "<prompt>" [-s SYSTEM] [-f FILE]
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SUMMON = REPO_ROOT / "star-alliance-arsenal" / "summon.py"
MINIMAX = REPO_ROOT / "star-alliance-arsenal" / "minimax.py"


def delegate(model: str, prompt: str, system: str | None = None,
             file: str | None = None, timeout: int = 300) -> str:
    """Invoke summon.py and return the model's answer (stripped).

    Raises RuntimeError on non-zero exit, timeout, or any invocation error.
    Never raises on stdout being empty — the caller decides what that means.
    """
    if not SUMMON.exists():
        raise RuntimeError(f"summon.py not found at {SUMMON}")
    cmd = ["python3", str(SUMMON), str(model), str(prompt)]
    if system:
        cmd += ["-s", str(system)]
    if file:
        cmd += ["-f", str(file)]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"delegate timed out after {timeout}s") from exc
    except FileNotFoundError as exc:
        raise RuntimeError(f"python3 not found on PATH: {exc}") from exc
    except Exception as exc:
        raise RuntimeError(f"delegate could not invoke summon: {exc}") from exc
    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "").strip()
        raise RuntimeError(f"delegate failed (exit {proc.returncode}): {err}")
    return (proc.stdout or "").strip()


def delegate_many(prompts, model: str = "minimax-sub",
                  system: str | None = None, timeout: int = 600) -> list:
    """Run N prompts through ONE process when the backend supports batching.

    For minimax-sub this uses ``minimax.py --batch`` — one subprocess spawn and one
    keep-alive HTTPS connection for the whole fan-out, instead of N spawns and N
    fresh handshakes. Results are returned IN ORDER as a list of strings; a prompt
    that failed comes back as ``None`` (the caller filters/decides). Falls back to
    a sequential ``delegate`` loop for any non-batch backend, so call sites need no
    branching. A single prompt short-circuits to one ``delegate`` call.
    """
    prompts = list(prompts)
    if not prompts:
        return []
    if len(prompts) == 1:
        try:
            return [delegate(model, prompts[0], system=system, timeout=timeout)]
        except RuntimeError:
            return [None]

    if model != "minimax-sub" or not MINIMAX.exists():
        # No batch backend → sequential, but keep the ordered-with-None contract.
        out = []
        for p in prompts:
            try:
                out.append(delegate(model, p, system=system, timeout=timeout))
            except RuntimeError:
                out.append(None)
        return out

    # Write a JSONL spec and invoke minimax.py --batch once.
    tmp = tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False, encoding="utf-8")
    try:
        for p in prompts:
            spec = {"prompt": p}
            if system:
                spec["system"] = system
            tmp.write(json.dumps(spec, ensure_ascii=False) + "\n")
        tmp.close()
        env = dict(os.environ, SA_MODEL_ID="minimax-sub")
        try:
            proc = subprocess.run(
                ["python3", str(MINIMAX), "--batch", tmp.name],
                capture_output=True, text=True, timeout=timeout, env=env,
            )
        except subprocess.TimeoutExpired:
            return [None] * len(prompts)
        results = [None] * len(prompts)
        for line in (proc.stdout or "").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            i = rec.get("i")
            if isinstance(i, int) and 0 <= i < len(results) and rec.get("ok"):
                results[i] = (rec.get("content") or "").strip()
        return results
    finally:
        try:
            os.unlink(tmp.name)
        except OSError:
            pass


def main() -> int:
    ap = argparse.ArgumentParser(description="Call a model via summon.py")
    ap.add_argument("model", help="Model id (e.g. minimax-sub)")
    ap.add_argument("prompt", help="Prompt text")
    ap.add_argument("-s", "--system", default=None, help="System prompt")
    ap.add_argument("-f", "--file", default=None, help="File to feed as context")
    args = ap.parse_args()
    try:
        out = delegate(args.model, args.prompt, system=args.system, file=args.file)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
