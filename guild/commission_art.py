"""commission_art.py — Art Forge: commission an image asset from a brief.

Drives the REAL image weapon: star-alliance-arsenal/imagegen.py (MiniMax image-01,
direct API, 1024x1024 JPEG-as-png — the same forge that makes every skill/member/
workflow tile). image-01 is NOT routable by summon.py (only text weapons are wired
there), so this calls imagegen.py directly instead.

Degrades gracefully: if imagegen.py or its API key is missing, it writes an
art_log.md describing the brief + the exact prompt it WOULD send, and exits 0 with
a clear "no image backend wired" notice. It never fakes an image.

CLI:
    python3 guild/commission_art.py --brief <brief.md> --out <asset.png> [--max-iter N]
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
IMAGEGEN = REPO_ROOT / "star-alliance-arsenal" / "imagegen.py"
KEY_PATH = Path(os.path.expanduser("~/.config/minimax/m3.key"))
IMAGE_WEAPON = "image-01"


def image_backend_reachable() -> bool:
    """True only if the real imagegen.py forge AND its API key are present."""
    return IMAGEGEN.exists() and KEY_PATH.exists()


def build_prompt(brief_text: str) -> str:
    """The prompt that would be sent to the image weapon."""
    return (
        "Generate a single image asset from this brief. Honor the described "
        "subject, style, palette, and composition. Output one image.\n\n"
        "=== BRIEF ===\n" + brief_text.strip() + "\n"
    )


def write_art_log(out: Path, brief_path: Path, prompt: str, reason: str) -> Path:
    log_path = out.with_name("art_log.md")
    body = (
        "# Art Forge — commission log\n\n"
        f"- Brief: {brief_path}\n"
        f"- Intended output: {out}\n"
        f"- Image weapon: {IMAGE_WEAPON}\n"
        f"- Status: NO IMAGE BACKEND WIRED — {reason}\n\n"
        "## Prompt that WOULD be sent\n\n"
        "```\n" + prompt.rstrip() + "\n```\n\n"
        "> No image was generated (degraded gracefully). Wire image-01 into "
        "summon.py to enable real generation.\n"
    )
    log_path.write_text(body, encoding="utf-8")
    return log_path


def commission(brief: Path, out: Path, max_iter: int) -> int:
    if not brief.exists():
        print(f"ERROR: brief not found: {brief}", file=sys.stderr)
        return 1
    try:
        brief_text = brief.read_text(encoding="utf-8")
    except Exception as exc:
        print(f"ERROR reading brief: {exc}", file=sys.stderr)
        return 1

    prompt = build_prompt(brief_text)
    out.parent.mkdir(parents=True, exist_ok=True)

    if not image_backend_reachable():
        log_path = write_art_log(
            out, brief, prompt,
            reason=f"{IMAGE_WEAPON} is not routable by summon.py on this device",
        )
        print(f"commission_art: no image backend wired — wrote {log_path}")
        print("commission_art: degraded gracefully (no image faked). Exit 0.")
        return 0

    # Image backend reachable: drive imagegen.py for up to max_iter attempts.
    # imagegen.py forges a real 1024x1024 JPEG-as-png at --out and exits 0.
    print(f"commission_art: {IMAGE_WEAPON} reachable via imagegen.py — commissioning (max-iter={max_iter})")
    for i in range(1, max_iter + 1):
        proc = subprocess.run(
            ["python3", str(IMAGEGEN), prompt, "-o", str(out)],
            capture_output=True, text=True,
        )
        if proc.returncode == 0 and out.exists() and out.stat().st_size > 0:
            print(f"commission_art: iteration {i} forged -> {out}")
            return 0
        err = (proc.stderr or proc.stdout or "").strip()
        print(f"  iteration {i}: no asset (exit {proc.returncode})\n{err}")
    print("commission_art: image backend reachable but produced no asset.", file=sys.stderr)
    return 1


def main() -> int:
    ap = argparse.ArgumentParser(description="Art Forge — commission an image from a brief")
    # --in is the workflow-runner's file-rail alias for --brief (resolve_io_args
    # in guild/run.py supplies --in from the step's first `inputs` entry).
    ap.add_argument("--brief", "--in", dest="brief", required=True, help="Path to the brief markdown")
    ap.add_argument("--out", required=True, help="Path for the output asset")
    ap.add_argument("--max-iter", type=int, default=1, help="Max generation attempts")
    args = ap.parse_args()

    brief = Path(args.brief)
    if not brief.is_absolute():
        brief = (REPO_ROOT / brief).resolve()
    out = Path(args.out)
    if not out.is_absolute():
        out = (REPO_ROOT / out).resolve()

    return commission(brief, out, max(1, args.max_iter))


if __name__ == "__main__":
    sys.exit(main())
