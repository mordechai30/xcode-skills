"""Create an owned source breakpoint and watch actual debugger state."""
from pathlib import Path
from operations.common import ask, debug_context, save_session, stop_fields


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
    bp = {key: value[key] for key in ('id','resolved','locations') if key in value} | {'file': str(args.file.resolve()), 'line': args.line}
    locations = [item for item in value.get('locations', []) if item.get('resolved')]
    facts = {'breakpoint':value['id'], 'resolved':bool(value.get('resolved')), 'requested':args.file.name + ':' + str(args.line)}
    if locations:
        location = locations[0]
        facts['location'] = Path(location.get('file') or str(args.file)).name + ':' + str(location['line'])
        facts['relocated'] = location['line'] != args.line
    ctx['session']['breakpoints'].append(bp)
    save_session(ctx, ctx['session'])
    if not value.get('resolved'):
        return ask('Breakpoint has no resolved locations. It remains pending.') | facts
    return {'status': 'success', 'watch': state.get('state') == 'running', **facts, **stop_fields(state)}
