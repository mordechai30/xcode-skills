"""Thin inspection gateway to the existing debugger connection."""
from operations.common import ask, debug_context, observe, stop_fields
from lifecycle.state import append_log
import json


def execute(args, root):
    """Forward the requested command and preserve its actual output.
    Refresh state after commands without parsing or restricting their text.
    """
    ctx, state = debug_context(args, root)
    value = ctx['backend'].debug_action(ctx, 'command', command=args.command)
    if value.get('response', {}).get('isWaitingForMore'):
        value['message'] = 'Partial output received. State queried without repeating the command.'
    if not value.get('current'):
        value['current'] = ctx['backend'].debug_status(ctx)
    if value.get('current'):
        observe(ctx, value['current'])
    response = value.get('response', {})
    result = {'status':value.get('status','uncertain'), '_detail':getattr(args,'detail',False)}
    for key in ('output','error','message'):
        text = value.get(key) if value.get(key) is not None else response.get(key)
        if text:
            result[key] = text
    if value.get('current'):
        result.update(stop_fields(value['current']))
    return result
