#!/usr/bin/env python3
"""minimax - call the MiniMax direct API to generate text.

Usage examples:

  1. Pipe a question into stdin and print the plain answer::

         echo "What is the capital of France?" | python3 minimax.py

  2. Use a system prompt, a custom model and a custom token budget::

         python3 minimax.py -s "You are a concise assistant." \\
             --model MiniMax-M3 --max-tokens 8000 \\
             "Summarise the plot of Hamlet in one paragraph."

  3. Force JSON-shaped output, strip any ```json fences, validate locally
     and re-dump compact to stdout::

         python3 minimax.py --json -s "Return a JSON object with one key 'answer'." \\
             "What is 2+2?"
"""
import argparse
import http.client
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request


API_URL = 'https://api.minimax.io/v1/text/chatcompletion_v2'
API_HOST = 'api.minimax.io'
API_PATH = '/v1/text/chatcompletion_v2'


def resolve_api_key():
    """Return the API key from the env or the config file, else exit 2."""
    key = os.environ.get('MINIMAX_API_KEY', '').strip()
    if key:
        return key
    path = os.path.expanduser('~/.config/minimax/m3.key')
    try:
        with open(path, 'r', encoding='utf-8') as fh:
            key = fh.read().strip()
    except OSError:
        key = ''
    if key:
        return key
    print('minimax: no API key found in $MINIMAX_API_KEY or in ~/.config/minimax/m3.key',
          file=sys.stderr)
    sys.exit(2)


def build_messages(system, prompt):
    msgs = []
    if system:
        msgs.append({'role': 'system', 'content': system})
    msgs.append({'role': 'user', 'content': prompt})
    return msgs


def post_chat(api_key, model, messages, max_tokens, timeout):
    body = json.dumps({
        'model': model,
        'messages': messages,
        'max_tokens': max_tokens,
    }).encode('utf-8')
    req = urllib.request.Request(
        API_URL,
        data=body,
        headers={
            'Authorization': 'Bearer ' + api_key,
            'Content-Type': 'application/json',
        },
        method='POST',
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode('utf-8')
            return json.loads(raw)
    except urllib.error.HTTPError as e:
        try:
            detail = e.read().decode('utf-8', errors='replace')
        except Exception:
            detail = str(e)
        print('minimax: HTTP {0}: {1}'.format(e.code, detail), file=sys.stderr)
        sys.exit(4)
    except urllib.error.URLError as e:
        reason = getattr(e, 'reason', str(e))
        print('minimax: URL error: {0}'.format(reason), file=sys.stderr)
        sys.exit(4)


def _log_call(usage, wall_ms):
    """Record one batch call's spend to the shared ledger (best-effort)."""
    try:
        from arsenal_usage import log_usage
        total = usage.get('total_tokens')
        p_tok = usage.get('prompt_tokens')
        c_tok = usage.get('completion_tokens')
        if c_tok is None and total is not None:
            c_tok = total - (p_tok or 0)
        model_id = os.environ.get('SA_MODEL_ID') or 'minimax-m3'
        log_usage(model_id, 'minimax', p_tok or 0, c_tok or 0, wall_ms=wall_ms)
    except Exception:
        pass


def run_batch(api_key, model, path, default_max_tokens, timeout):
    """Process N prompts from a JSONL file over ONE keep-alive HTTPS connection.

    Each input line is either a bare JSON string (the prompt) or an object with
    keys: prompt (required), system, max_tokens. Results are emitted to stdout as
    JSONL, one per line, IN INPUT ORDER:
        {"i":0,"ok":true,"content":"…","tokens":123}
        {"i":1,"ok":false,"error":"…"}
    A single failed prompt does not abort the batch (its line is ok:false). This
    is the time win: one process + one TCP/TLS connection for the whole fan-out
    instead of N subprocess spawns and N fresh handshakes. Returns an exit code.
    """
    try:
        with open(path, 'r', encoding='utf-8') as fh:
            raw_lines = [ln for ln in (l.strip() for l in fh) if ln]
    except OSError as e:
        print('minimax: cannot read batch file {0}: {1}'.format(path, e), file=sys.stderr)
        return 2

    specs = []
    for ln in raw_lines:
        try:
            obj = json.loads(ln)
        except json.JSONDecodeError:
            obj = ln  # tolerate a bare unquoted line as a literal prompt
        if isinstance(obj, str):
            specs.append({'prompt': obj})
        elif isinstance(obj, dict) and obj.get('prompt'):
            specs.append(obj)
        else:
            specs.append({'prompt': None})  # placeholder → reported as error

    conn = http.client.HTTPSConnection(API_HOST, timeout=timeout)
    headers = {
        'Authorization': 'Bearer ' + api_key,
        'Content-Type': 'application/json',
    }
    any_fail = False
    try:
        for i, spec in enumerate(specs):
            prompt = spec.get('prompt')
            if not prompt or not str(prompt).strip():
                any_fail = True
                print(json.dumps({'i': i, 'ok': False, 'error': 'empty prompt'},
                                 ensure_ascii=False))
                continue
            messages = build_messages(spec.get('system', ''), prompt)
            body = json.dumps({
                'model': model,
                'messages': messages,
                'max_tokens': int(spec.get('max_tokens') or default_max_tokens),
            }).encode('utf-8')
            t0 = time.monotonic()
            try:
                conn.request('POST', API_PATH, body=body, headers=headers)
                resp = conn.getresponse()
                payload = resp.read().decode('utf-8', errors='replace')
                if resp.status != 200:
                    raise RuntimeError('HTTP {0}: {1}'.format(resp.status, payload[:300]))
                data = json.loads(payload)
            except Exception as e:
                # A broken connection mid-batch: reopen once for the remaining items.
                any_fail = True
                try:
                    conn.close()
                    conn = http.client.HTTPSConnection(API_HOST, timeout=timeout)
                except Exception:
                    pass
                print(json.dumps({'i': i, 'ok': False, 'error': str(e)}, ensure_ascii=False))
                continue
            wall_ms = int((time.monotonic() - t0) * 1000)
            usage = data.get('usage') or {}
            _log_call(usage, wall_ms)
            try:
                content = data['choices'][0]['message'].get('content')
            except (KeyError, IndexError, TypeError):
                content = None
            if content is None or not str(content).strip():
                any_fail = True
                print(json.dumps({'i': i, 'ok': False, 'error': 'empty content'},
                                 ensure_ascii=False))
                continue
            print(json.dumps({'i': i, 'ok': True, 'content': content,
                              'tokens': usage.get('total_tokens')}, ensure_ascii=False))
    finally:
        try:
            conn.close()
        except Exception:
            pass
    return 0 if not any_fail else 6


def strip_fences(text):
    """Remove leading/trailing ``` / ```json fences and surrounding whitespace."""
    text = re.sub(r'^\s*```(?:json)?\s*\n?', '', text, count=1, flags=re.IGNORECASE)
    text = re.sub(r'\n?```\s*$', '', text, count=1)
    return text.strip()


def resolve_prompt(args):
    if args.file is not None:
        try:
            with open(args.file, 'r', encoding='utf-8') as fh:
                return fh.read()
        except OSError as e:
            print('minimax: cannot read prompt file {0}: {1}'.format(args.file, e),
                  file=sys.stderr)
            sys.exit(2)
    if args.prompt is None or args.prompt == '-':
        return sys.stdin.read()
    return args.prompt


def main():
    parser = argparse.ArgumentParser(
        prog='minimax',
        description='Call the MiniMax direct API to generate text.',
    )
    parser.add_argument('prompt', nargs='?', default=None,
                        help="User prompt. Use '-' or omit to read from stdin.")
    parser.add_argument('-s', '--system', default='',
                        help='System prompt (default: empty).')
    parser.add_argument('-f', '--file', default=None,
                        help='Read the user prompt from a file path.')
    parser.add_argument('--model', default='MiniMax-M3',
                        help='Model name (default: MiniMax-M3).')
    parser.add_argument('--max-tokens', type=int, default=16000,
                        help='Max tokens for the completion (default: 16000).')
    parser.add_argument('--json', action='store_true',
                        help='Strip ```json fences, validate, and re-dump compact.')
    parser.add_argument('--timeout', type=int, default=180,
                        help='HTTP timeout in seconds (default: 180).')
    args = parser.parse_args()

    prompt = resolve_prompt(args)
    if not prompt or not prompt.strip():
        print('minimax: empty prompt', file=sys.stderr)
        sys.exit(2)

    api_key = resolve_api_key()
    messages = build_messages(args.system, prompt)
    _t0 = time.monotonic()
    data = post_chat(api_key, args.model, messages, args.max_tokens, args.timeout)
    wall_ms = int((time.monotonic() - _t0) * 1000)

    usage = data.get('usage') or {}
    total = usage.get('total_tokens')
    if total is not None:
        print('minimax: {0} tokens'.format(total), file=sys.stderr)

    # Record real spend to the shared delegation ledger (best-effort).
    try:
        from arsenal_usage import log_usage
        p_tok = usage.get('prompt_tokens')
        c_tok = usage.get('completion_tokens')
        if c_tok is None and total is not None:
            c_tok = total - (p_tok or 0)
        model_id = os.environ.get('SA_MODEL_ID') or 'minimax-m3'
        log_usage(model_id, 'minimax', p_tok or 0, c_tok or 0, wall_ms=wall_ms)
    except Exception:
        pass

    try:
        message = data['choices'][0]['message']
    except (KeyError, IndexError, TypeError):
        print('minimax: empty content - raise --max-tokens', file=sys.stderr)
        sys.exit(5)

    # reasoning_content is deliberately ignored; only 'content' is used.
    content = message.get('content')
    if content is None or not str(content).strip():
        print('minimax: empty content - raise --max-tokens', file=sys.stderr)
        sys.exit(5)

    if args.json:
        candidate = strip_fences(content)
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError as e:
            print('minimax: --json parse failed: {0}'.format(e), file=sys.stderr)
            print('--- raw content ---', file=sys.stderr)
            print(content, file=sys.stderr)
            sys.exit(3)
        print(json.dumps(parsed, separators=(',', ':'), ensure_ascii=False))
    else:
        print(content)

    sys.exit(0)


if __name__ == '__main__':
    main()