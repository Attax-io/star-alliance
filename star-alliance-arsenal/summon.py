"""summon — single entry point for routing prompts to guild model backends.

Usage examples:

    # 1. Route to the local minimax backend.
    python summon.py minimax-sub "Explain quicksort in two sentences."

    # 2. Route to an Ollama cloud bench model (e.g. glm-5.2 -> glm-5.2:cloud).
    python summon.py glm-5.2 "Solve: 17 * 23" --json

    # 3. Claude models (opus/sonnet/haiku) are reserve models: dispatched via
    #    delegate_task with a model override, not via a backend script.
    python summon.py opus "Draft a release note."
"""

import argparse
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

# Canonical model facts live in models.json (read via models_registry). The
# literals below are a FAIL-SAFE only — used if the registry can't be read so a
# broken file never bricks dispatch. Edit models.json, not these.
_FALLBACK_CLOUD_TAG = {
    'glm-5.2': 'glm-5.2:cloud',
    'kimi-k2.7': 'kimi-k2.7-code:cloud',
}
_FALLBACK_CLAUDE = {'opus', 'sonnet', 'haiku'}

if HERE not in sys.path:
    sys.path.insert(0, HERE)
try:
    import models_registry as _reg
    CLOUD_TAG = _reg.cloud_tags() or _FALLBACK_CLOUD_TAG
    CLAUDE = _reg.claude_ids() or _FALLBACK_CLAUDE
    _KNOWN = _reg.known_ids()
except Exception:
    CLOUD_TAG = _FALLBACK_CLOUD_TAG
    CLAUDE = _FALLBACK_CLAUDE
    _KNOWN = set()

KNOWN_IDS = sorted(_KNOWN | {'minimax-sub', 'minimax-payg'} | set(CLOUD_TAG) | CLAUDE)


def _passthrough(args, token_flag=None, prompt_first=False):
    """Build the trailing flag/positional portion shared by every backend.

    token_flag names the backend's max-output flag (minimax: --max-tokens,
    ollama_cloud: --num-predict); --timeout is shared across both backends.

    prompt_first=True puts the prompt directly after the model positional —
    required by backends (ollama_cloud.py) whose prompt arg uses nargs="?".
    argparse treats an unmatched trailing token as unrecognized when the
    optionals have already been greedily consumed, so the prompt MUST come
    before the optionals for those backends.
    """
    parts = []
    if prompt_first and args.prompt is not None:
        parts.append(args.prompt)
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
    if not prompt_first and args.prompt is not None:
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
    parser.add_argument(
        '--max-tokens',
        type=int,
        default=None,
        help='Max output tokens. Mapped per backend (minimax: --max-tokens, '
             'cloud: --num-predict). Omit for the backend default.',
    )
    parser.add_argument(
        '--timeout',
        type=int,
        default=None,
        help='HTTP timeout in seconds (passthrough). Omit for backend default.',
    )
    args = parser.parse_args()

    # The backends log real token spend to the delegation ledger keyed by the
    # guild model id — pass it through so the dashboard sees canonical names.
    env = dict(os.environ, SA_MODEL_ID=args.model_id)

    # 1. minimax-sub / minimax-payg -> local minimax.py (prompt is trailing positional).
    if args.model_id in {'minimax-sub', 'minimax-payg'}:
        cmd = [sys.executable, os.path.join(HERE, 'minimax.py')]
        cmd += _passthrough(args, token_flag='--max-tokens')
        sys.exit(subprocess.run(cmd, env=env).returncode)

    # 2. CLOUD_TAG models -> ollama_cloud.py with the cloud tag FIRST,
    #    then prompt immediately (nargs="?" argparse trap), then optionals.
    if args.model_id in CLOUD_TAG:
        cmd = [
            sys.executable,
            os.path.join(HERE, 'ollama_cloud.py'),
            CLOUD_TAG[args.model_id],
        ]
        cmd += _passthrough(args, token_flag='--num-predict', prompt_first=True)
        sys.exit(subprocess.run(cmd, env=env).returncode)

    # 3. Claude models are native to the orchestrator; no backend script.
    if args.model_id in CLAUDE:
        print(
            f"summon: {args.model_id} is Claude (native) \u2014 you are the "
            f"orchestrator; use delegate_task with model={args.model_id}, "
            f"no script needed.",
            file=sys.stderr,
        )
        sys.exit(0)

    # 4. Unknown model_id: surface the sorted catalogue and bail.
    print(
        f"summon: unknown model_id {args.model_id!r}. Known: "
        f"{', '.join(KNOWN_IDS)}",
        file=sys.stderr,
    )
    sys.exit(2)


if __name__ == '__main__':
    main()
