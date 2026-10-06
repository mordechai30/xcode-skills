"""Pause within the total submission deadline; never resume on expiry."""
import time
from operations.common import ask, debug_context, observe, stop_fields


def execute(args, root):
    """Check expiry before sending interrupt and verify within remaining time.
    Each backend request inherits the same submission deadline.
    """
    deadline = getattr(args, '_deadline', time.monotonic() + 15)
    if time.monotonic() >= deadline:
        return {'status':'uncertain','stage':'pause','state':'uncertain','message':'Pause expired before execution. Use Status.'}
    ctx, state = debug_context(args, root)
    if state.get('state') != 'running':
        return ask('Pause requires a running debugger session.') | stop_fields(state)
    if time.monotonic() >= deadline:
        return {'status':'uncertain','stage':'pause','state':'uncertain','message':'Pause expired before interrupt. Use Status.'}
    value = ctx['backend'].debug_action(ctx, 'pause')
    if value['status'] != 'success':
        return {key:value[key] for key in ('status','error','message') if key in value}
    while time.monotonic() < deadline:
        state = ctx['backend'].debug_status(ctx)
        if state.get('state') != 'running':
            observe(ctx, state)
            return {'status':'success' if state.get('state') == 'paused' else 'uncertain', **stop_fields(state)}
        time.sleep(min(.1, max(0, deadline - time.monotonic())))
    return {'status':'uncertain','stage':'pause','state':'uncertain','message':'Pause expired. Use Status to verify the effect.'}
