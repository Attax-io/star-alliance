"""commission_art.py — Art Forge: commission an image asset from a brief.

Star Alliance is now a Claude-only harness — the external image doer (the
MiniMax image-01 backend that imagegen.py used to drive) has been removed with
the rest of the non-Claude doer layer. There is no image backend wired.

This tool therefore always degrades gracefully: it writes an art_log.md
describing the brief + the exact prompt it WOULD send to an image model, and
exits 0 with a clear "no image backend wired" notice. It never fakes an image.
Image generation now belongs to the live session / a designer subagent using a
real image tool, not to this script.

CLI:
    python3 guild/commission_art.py --brief <brief.md> --out <asset.png> [--max-iter N]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
IMAGE_WEAPON = "image-01"


def image_backend_reachable() -> bool:
    """Always False — the external image doer layer has been removed."""
    return False


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
        "> No image was generated (degraded gracefully). Star Alliance is now a "
        "Claude-only harness with no external image doer — generate the asset "
        "from the live session or a designer subagent using a real image tool.\n"
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

    # No image backend is wired in a Claude-only harness — always degrade
    # gracefully: record the brief + intended prompt and exit 0 without faking.
    log_path = write_art_log(
        out, brief, prompt,
        reason="external image doer removed (Claude-only harness)",
    )
    print(f"commission_art: no image backend wired — wrote {log_path}")
    print("commission_art: degraded gracefully (no image faked). Exit 0.")
    return 0


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
