"""Disposable stdio server for MCP transport fixtures.
Modes exercise pagination, errors, EOF, notifications, and deadlines.
"""
import json
import sys
import time

mode = sys.argv[1]
for line in sys.stdin:
    message = json.loads(line)
    method = message.get('method')
    if not method or 'id' not in message:
        continue
    if method == 'initialize':
        result = {'protocolVersion': '2024-11-05', 'capabilities': {}}
    elif method == 'tools/list':
        if not message.get('params', {}).get('cursor'):
            result = {'tools': [], 'nextCursor': 'page-2'}
        else:
            result = {'tools': [{'name': 'Echo', 'inputSchema': {'properties': {'value': {'type': 'string'}}, 'required': ['value']}}]}
    elif mode == 'eof':
        break
    elif mode == 'timeout':
        time.sleep(5)
        continue
    elif mode == 'error':
        print(json.dumps({'jsonrpc': '2.0', 'id': message['id'], 'error': {'code': -32000, 'message': 'fixture error'}}), flush=True)
        continue
    else:
        print(json.dumps({'jsonrpc': '2.0', 'method': 'notifications/message', 'params': {'data': 'fixture'}}), flush=True)
        print('fixture stderr', file=sys.stderr, flush=True)
        result = {'structuredContent': {'value': message['params']['arguments']['value']}, 'content': []}
    print(json.dumps({'jsonrpc': '2.0', 'id': message['id'], 'result': result}), flush=True)
