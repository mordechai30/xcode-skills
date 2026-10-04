"""Create an owned source breakpoint and watch actual debugger state."""
from operations.common import ask, debug_context, save_session


def execute(args, root):
    """Require source and positive line, then retain the session breakpoint.
    Resolution is reported separately from an actual hit.
    """
    ctx, state = debug_context(args, root)
    if state.get('state') not in ('running', 'paused'):
        return ask('No live Debug process is available.', [])
    value = ctx['backend'].debug_action(ctx, 'set_breakpoint', file=str(args.file.resolve()), line=args.line)
    if value['status'] != 'success':
        return value
    bp = value | {'file': str(args.file.resolve()), 'line': args.line}
    ctx['session']['breakpoints'].append(bp)
    save_session(ctx, ctx['session'])
    if not value.get('resolved'):
        return ask('Breakpoint has no resolved locations. It remains pending.') | {'breakpoint': bp}
    return {'status': 'success', 'breakpoint': bp, 'watch': state.get('state') == 'running',
            'message': 'Breakpoint created. A resolved location is not a hit.', 'current': state}
