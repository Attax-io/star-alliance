"""summon — single entry point for routing prompts to guild model backends.

Usage examples:

    # 1. Route to the local minimax backend.
    python summon.py minimax-m3 "Explain quicksort in two sentences."

    # 2. Route to an Ollama cloud bench model (e.g. glm-5.2 -> glm-5.2:cloud).
    python summon.py glm-5.2 "Solve: 17 * 23" --json

    # 3. Opus is Claude-native: dispatched locally, not via a backend script.
    #    The orchestrator should use the Task tool directly.
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
# Two-layer system: no Ollama/cloud bench models remain, so there are no cloud
# tags. Kept as an (empty) fail-safe mirror of models.json so dispatch and the
# conformity FB(tags) check stay satisfied by construction.
_FALLBACK_CLOUD_TAG = {}
_FALLBACK_CLAUDE = {'opus', 'haiku'}

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

KNOWN_IDS = sorted(_KNOWN | {'minimax-m3'} | set(CLOUD_TAG) | CLAUDE)


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
        cmd += _passthrough(args, token_flag='--num-predict')
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

    # 4. Unknown model_id: surface the sorted catalogue and bail.
    print(
        f"summon: unknown model_id {args.model_id!r}. Known: "
        f"{', '.join(KNOWN_IDS)}",
        file=sys.stderr,
    )
    sys.exit(2)


if __name__ == '__main__':
    main()
