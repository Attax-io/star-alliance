#!/usr/bin/env python3
"""
imagegen.py — Star Alliance image-01 weapon runner.

Generates 1024x1024 skill/agent/workflow art tiles via MiniMax image-01.
Output is always JPEG bytes saved with the requested filename (even if .png).
Matches the house format: every *.png tile in skill-art/ is JPEG bytes.

Usage:
    python3 star-alliance-arsenal/imagegen.py "<prompt>" -o skill-art/my-skill.png
    python3 star-alliance-arsenal/imagegen.py "<prompt>" --out workflow-art/my-flow.png

Flags:
    -o / --out   Output path (default: ./imagegen_out.png)
    --dry-run    Print the prompt, don't call the API
    --quality    JPEG quality 1-100 (default: 92)

Key: ~/.config/minimax/m3.key (JWT bearer token)
"""

import argparse
import os
import subprocess
import sys
import json
import tempfile
import urllib.request
import urllib.parse

KEY_PATH = os.path.expanduser("~/.config/minimax/m3.key")
API_URL = "https://api.minimax.io/v1/image_generation"
MODEL = "image-01"
# image-01 rejects prompts at or above this length with API error 2013.
PROMPT_LIMIT = 1500


def read_key() -> str:
    with open(KEY_PATH) as f:
        return f.read().strip()


def generate(prompt: str, key: str) -> str:
    """Call image-01 and return the image URL."""
    if len(prompt) >= PROMPT_LIMIT:
        raise ValueError(
            f"prompt is {len(prompt)} chars; image-01 limit is {PROMPT_LIMIT} "
            "(API error 2013) — shorten the brief"
        )
    payload = json.dumps({
        "model": MODEL,
        "prompt": prompt,
        "aspect_ratio": "1:1",
        "n": 1,
        "prompt_optimizer": True,
        "response_format": "url",
    }).encode()

    req = urllib.request.Request(
        API_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        body = json.loads(resp.read())

    status = body.get("base_resp", {}).get("status_code")
    if status != 0:
        msg = body.get("base_resp", {}).get("status_msg", "unknown error")
        raise RuntimeError(f"image-01 API error {status}: {msg}")

    urls = body["data"]["image_urls"]
    if not urls:
        raise RuntimeError("No image URLs in response")
    return urls[0]


def download_and_save(url: str, out_path: str, quality: int = 92):
    """Download image URL, re-encode as JPEG, save to out_path."""
    # Download to temp file
    with tempfile.NamedTemporaryFile(suffix=".jpeg", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        with urllib.request.urlopen(url, timeout=60) as resp:
            with open(tmp_path, "wb") as f:
                f.write(resp.read())

        # Re-encode as JPEG using sips (always available on macOS)
        # sips preserves 1024x1024; output to a temp jpg then rename
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp2:
            tmp_jpg = tmp2.name

        result = subprocess.run(
            ["sips", "-s", "format", "jpeg",
             "-s", "formatOptions", str(quality),
             tmp_path, "--out", tmp_jpg],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(f"sips failed: {result.stderr}")

        # Verify dimensions
        info = subprocess.run(
            ["sips", "-g", "pixelWidth", "-g", "pixelHeight", tmp_jpg],
            capture_output=True, text=True,
        )
        w = h = None
        for line in info.stdout.splitlines():
            if "pixelWidth" in line:
                w = int(line.split()[-1])
            if "pixelHeight" in line:
                h = int(line.split()[-1])

        if w != 1024 or h != 1024:
            # Resize to 1024x1024
            subprocess.run(
                ["sips", "--resampleHeightWidth", "1024", "1024", tmp_jpg],
                check=True, capture_output=True,
            )

        # Copy to final destination (JPEG bytes, whatever the extension)
        os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
        import shutil
        shutil.copy2(tmp_jpg, out_path)

    finally:
        for p in [tmp_path]:
            try:
                os.unlink(p)
            except FileNotFoundError:
                pass


def main():
    parser = argparse.ArgumentParser(description="Star Alliance image-01 tile forger")
    parser.add_argument("prompt", help="Image generation prompt")
    parser.add_argument("-o", "--out", default="./imagegen_out.png",
                        help="Output path (default: ./imagegen_out.png)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print prompt only, no API call")
    parser.add_argument("--quality", type=int, default=92,
                        help="JPEG quality 1-100 (default: 92)")
    args = parser.parse_args()

    if len(args.prompt) >= PROMPT_LIMIT:
        print(
            f"ERROR: prompt is {len(args.prompt)} chars; image-01 limit is "
            f"{PROMPT_LIMIT} (API error 2013) — shorten the brief.",
            file=sys.stderr,
        )
        return 1

    if args.dry_run:
        print(f"[dry-run] Prompt: {args.prompt}")
        print(f"[dry-run] Output: {args.out}")
        return

    print(f"Forging tile via image-01...")
    key = read_key()
    url = generate(args.prompt, key)
    print(f"Generated: {url[:80]}...")
    download_and_save(url, args.out, quality=args.quality)

    # Final verification
    result = subprocess.run(
        ["file", args.out], capture_output=True, text=True
    )
    info = subprocess.run(
        ["sips", "-g", "pixelWidth", "-g", "pixelHeight", args.out],
        capture_output=True, text=True,
    )
    print(f"Saved: {args.out}")
    print(f"  {result.stdout.strip()}")
    for line in info.stdout.splitlines():
        if "pixel" in line:
            print(f"  {line.strip()}")


if __name__ == "__main__":
    sys.exit(main() or 0)
