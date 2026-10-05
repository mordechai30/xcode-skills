"""Emit compact public JSON; full evidence stays in the operation log."""
import json
from pathlib import Path


def render(value, operation=''):
    """Summarize one outcome within the approved UTF-8 byte limit.
    Truncation preserves JSON and points to locally retained evidence.
    """
    status = value.get('status', 'uncertain')
    current = value.get('current', value)
    response = value.get('response', {})
    inspection = operation == 'debugger-command'
    exceptional = status != 'success' or inspection or bool(value.get('warning'))
    limit = 500 if exceptional else 200
    message = value.get('message') or value.get('warning')
    if inspection:
        message = value.get('output') or response.get('output') or value.get('error') or message or 'No inspection output.'
    if not message:
        message = {'build': 'Built; not launched.', 'run': 'Launched.', 'kill': 'App and owned helpers terminated.',
                   'pause': 'Paused.', 'continue': 'Resumed.', 'set-breakpoint': 'Breakpoint set.'}.get(operation, 'Completed.')
    out = {'status': status, 'message': str(message)}
    state = current.get('state') or value.get('state')
    if state:
        out['state'] = state
    if operation == 'run':
        app = value.get('app') or {}
        if app.get('pid'):
            out['pid'] = app['pid']
        if 'debugger' in value:
            out['debugger'] = bool(value['debugger'])
    bp = value.get('breakpoint', {})
    if bp.get('id'):
        out['breakpoint'] = bp['id']
    if value.get('removed') is not None:
        out['removed'] = value['removed']
    stops = current.get('stops', [])
    if bp.get('locations'):
        out['message'] = 'Breakpoint ' + str(bp['id']) + ': requested line ' + str(bp.get('line')) + '; resolved ' + ','.join(str(item.get('line')) for item in bp['locations'])
    if stops and not inspection:
        stop = next((s for s in stops if s.get('breakpoints')), stops[0])
        out['message'] = str(stop.get('description') or out['message']) + ' ' + str(stop.get('frame') or '')
        out['location'] = Path(stop.get('file') or '?').name + ':' + str(stop.get('line', 0))
        out['thread'] = stop.get('thread')
    if status != 'success' and value.get('choices'):
        out['message'] += ' Choices: ' + ', '.join(map(str, value['choices']))
    encode = lambda: json.dumps(out, ensure_ascii=False, separators=(',', ':')) + '\n'
    text = encode()
    if len(text.encode()) > limit:
        out['omitted'] = True
        out['log'] = Path(value.get('log') or 'session log').name.encode()[:80].decode('utf-8', errors='ignore')
        for key in ('thread', 'removed'):
            out.pop(key, None)
        for key in ('location', 'breakpoint', 'pid', 'debugger', 'state'):
            if len(encode().encode()) > limit and key in out and len(json.dumps({k: v for k, v in out.items() if k != 'message'}, ensure_ascii=False).encode()) > limit - 30:
                out.pop(key)
        original = out['message']
        out['message'] = ''
        allowance = max(0, limit - len(encode().encode()))
        out['message'] = original.encode()[:allowance].decode('utf-8', errors='ignore')
        while len(encode().encode()) > limit:
            out['message'] = out['message'][:-1]
        text = encode()
    return text


def emit(value, operation=''):
    """Write the sole public response for one invocation.
    The final newline is included in the measured byte budget.
    """
    print(render(value, operation), end='', flush=True)
