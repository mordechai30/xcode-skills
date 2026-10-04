"""Thin inspection gateway to the existing debugger connection."""
from operations.common import ask, debug_context, observe


def execute(args, root):
    """Forward the requested command and preserve its actual output.
    Check paused state for common frame, value, and stack queries.
    """
    ctx, state = debug_context(args, root)
    text = args.command.lstrip()
    paused_query = text.startswith(('frame variable', 'frame info', 'thread backtrace', 'bt', 'register read'))
    if paused_query and state.get('state') != 'paused':
        return ask('This inspection requires a paused session. Use Pause first.') | {'current': state}
    value = ctx['backend'].debug_action(ctx, 'command', command=args.command)
    if value.get('response', {}).get('isWaitingForMore'):
        value['current'] = ctx['backend'].debug_status(ctx)
        value['message'] = 'Partial inspection output retained. Current state queried without repeating the command.'
    if value.get('current'):
        observe(ctx, value['current'])
    return value
