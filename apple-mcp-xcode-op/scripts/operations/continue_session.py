"""Resume a paused session and handle only its responsible breakpoint."""
from operations.common import ask, debug_context, save_session, observe, stop_fields


def execute(args, root):
    """Delete the responsible owned breakpoint unless retention was requested.
    Manual and runtime stops preserve all breakpoints.
    """
    ctx, state = debug_context(args, root)
    if state.get('state') != 'paused':
        return ask('Continue requires a paused debugger session.') | {'current': state}
    owned = {bp['id'] for bp in ctx['session']['breakpoints']}
    causes = {bp for stop in state.get('stops', []) for bp in stop.get('breakpoints', [])}
    responsible = causes & owned
    if len(responsible) > 1 and not args.keep_breakpoint:
        return ask('Several session breakpoints caused the stop. Select which to remove.') | {'breakpoints': sorted(responsible)}
    removed = []
    if responsible and not args.keep_breakpoint:
        for number in responsible:
            deleted = ctx['backend'].debug_action(ctx, 'delete_breakpoint', id=number)
            if deleted['status'] != 'success':
                return deleted
            removed.append(number)
        ctx['session']['breakpoints'] = [bp for bp in ctx['session']['breakpoints'] if bp['id'] not in removed]
        save_session(ctx, ctx['session'])
    resumed = ctx['backend'].debug_action(ctx, 'continue')
    if resumed['status'] != 'success':
        return resumed
    current = ctx['backend'].debug_status(ctx)
    observe(ctx, current)
    facts = {'removed': removed[0]} if len(removed) == 1 else {}
    if args.keep_breakpoint and responsible:
        facts['kept'] = next(iter(responsible)) if len(responsible) == 1 else sorted(responsible)
    return {'status': current['status'], **facts, **stop_fields(current),
            'watch': bool(args.keep_breakpoint and current.get('state') == 'running')}
