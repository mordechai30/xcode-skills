"""Interrupt a running debugger-enabled Debug session."""
import time
from operations.common import ask, debug_context, observe


def execute(args, root):
    """Pause without terminating, then verify the stop.
    A bounded wait permits fresh backend state to arrive.
    """
    ctx, state = debug_context(args, root)
    if state.get('state') != 'running':
        return ask('Pause requires a running debugger session.') | {'current': state}
    value = ctx['backend'].debug_action(ctx, 'pause')
    if value['status'] != 'success':
        return value
    for _ in range(20):
        state = ctx['backend'].debug_status(ctx)
        if state.get('state') != 'running':
            break
        time.sleep(.1)
    observe(ctx, state)
    return {'status': 'success' if state.get('state') == 'paused' else 'uncertain', 'current': state}
