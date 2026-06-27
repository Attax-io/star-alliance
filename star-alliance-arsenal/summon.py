"""summon — single entry point for routing prompts to guild model backends.

Usage examples:

    # 1. Route to the local minimax backend.
    python summon.py minimax-m3 "Explain quicksort in two sentences."

    # 2. Route to an Ollama cloud bench model (e.g. glm-5.2 -> glm-5.2:cloud).
    python summon.py glm-5.2 "Solve: 17 * 23" --json

    # 3. Opus is Claude-native: dispatched locally, not via a backend script.
    #    The orchestrator should use the Task tool directly.
    python summon.py opus "Draft a release note."

    # 4. gpt-5.5 is OpenAI-direct and not provisioned on this device.
    python summon.py gpt-5.5
"""

import argparse
import os
import subprocess
import sys

CLOUD_TAG = {
    'glm-5.2': 'glm-5.2:cloud',
    'kimi-k2.7': 'kimi-k2.7-code:cloud',
    'deepseek-v4-pro': 'deepseek-v4-pro:cloud',
    'nemotron-3-ultra': 'nemotron-3-super:cloud',
    'qwen3.5': 'qwen3.5:cloud',
    'gemma4': 'gemma4:cloud',
}
CLAUDE = {'opus', 'sonnet', 'haiku'}

HERE = os.path.dirname(os.path.abspath(__file__))

KNOWN_IDS = sorted(
    {'minimax-m3', 'gpt-5.5'} | set(CLOUD_TAG) | CLAUDE
)


def _passthrough(args, token_flag=None):
    """Build the trailing flag/positional portion shared by every backend.

    -s VALUE is prepended, --json and -f VALUE are appended, prompt is last.

    token_flag names the backend's max-output flag (minimax: --max-tokens,
    ollama_cloud: --num-predict); --timeout is shared across both backends.
    """
    parts = []
    if args.system is not None:
        parts += ['-s', args.system]
    if getattr(args, 'json'):
        parts.append('--json')
    if args.file is not None:
        parts += ['-f', args.file]
    if getattr(args, 'max_tokens', None) is not None and token_flag:
        parts += [token_flag, str(args.max_tokens)]
    if getattr(args, 'timeout', None) is not None:
        parts += ['--timeout', str(args.timeout)]
    if args.prompt is not None:
        parts.append(args.prompt)
    return parts


def main():
    parser = argparse.ArgumentParser(
        prog='summon',
        description='Dispatch a prompt to the right guild model backend.',
    )
    parser.add_argument('model_id', help='Model identifier to route to.')
    parser.add_argument(
        'prompt',
        nargs='?',
        default=None,
        help='Prompt text. Omit to read from stdin.',
    )
    parser.add_argument(
        '-s', '--system',
        default=None,
        help='System prompt (passthrough).',
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Ask the backend to return JSON.',
    )
    parser.add_argument(
        '-f', '--file',
        default=None,
        help='File to attach (passthrough).',
    )
    args = parser.parse_args()

    # The backends log real token spend to the delegation ledger keyed by the
    # guild model id — pass it through so the dashboard sees canonical names.
    env = dict(os.environ, SA_MODEL_ID=args.model_id)

    # 1. minimax-m3 -> local minimax.py (prompt is trailing positional).
    if args.model_id == 'minimax-m3':
        cmd = [sys.executable, os.path.join(HERE, 'minimax.py')]
        cmd += _passthrough(args, token_flag='--max-tokens')
        sys.exit(subprocess.run(cmd, env=env).returncode)

    # 2. CLOUD_TAG models -> ollama_cloud.py with the cloud tag FIRST,
    #    then the standard passthrough (prompt trailing).
    if args.model_id in CLOUD_TAG:
        cmd = [
            sys.executable,
            os.path.join(HERE, 'ollama_cloud.py'),
            CLOUD_TAG[args.model_id],
        ]
        cmd += _passthrough(args)
        sys.exit(subprocess.run(cmd, env=env).returncode)

    # 3. Claude models are native to the orchestrator; no backend script.
    if args.model_id in CLAUDE:
        print(
            f"summon: {args.model_id} is Claude (native) \u2014 you are the "
            f"orchestrator; use the Task tool with model={args.model_id}, "
            f"no script needed.",
            file=sys.stderr,
        )
        sys.exit(0)

    # 4. gpt-5.5 — DEACTIVATED pending an OpenAI API key (Atta's call, 2026-06-26).
    #    Kept in member loadouts ON PURPOSE; do NOT strip. Reactivate by setting the
    #    OpenAI key on the device and wiring the OpenAI-direct backend here.
    if args.model_id == 'gpt-5.5':
        print(
            "summon: gpt-5.5 is DEACTIVATED — awaiting an OpenAI API key "
            "(OpenAI-direct, no key on device). Reactivate once the key is set.",
            file=sys.stderr,
        )
        sys.exit(69)

    # 5. Unknown model_id: surface the sorted catalogue and bail.
    print(
        f"summon: unknown model_id {args.model_id!r}. Known: "
        f"{', '.join(KNOWN_IDS)}",
        file=sys.stderr,
    )
    sys.exit(2)


if __name__ == '__main__':
    main()
