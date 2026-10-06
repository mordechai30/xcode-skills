"""Report only the state of the owned app. No process is adopted."""
from operations.common import context, observe, stop_fields, save_session
from lifecycle.process import verify_identity, capture_identity


def execute(args, root):
    """Query the retained debugger or the recorded launch identity.
    Missing launch evidence remains uncertain rather than adopting another app.
    """
    ctx = context(args, root)
    session = ctx.get('session')
    if not session:
        return {'status': 'success', 'state': 'none'}
    if session.get('debugger'):
        value = ctx['backend'].debug_status(ctx)
        app = session.get('app')
        if not app and session.get('state') != 'exited':
            return {'status':'uncertain','state':'uncertain','message':'Launch identity is missing. Use Kill to reconcile.'}
        if value.get('state') not in ('exited','uncertain') and app and (value.get('pid') != app['pid'] or not verify_identity(app)):
            return {'status':'uncertain','state':'uncertain','message':'Debugger identity differs from the owned app.'}
        observe(ctx, value)
        return {'status': value.get('status', 'uncertain'), **stop_fields(value), **({'message':value['message']} if value.get('message') else {})}
    app = session.get('app')
    if session.get('state') == 'exited':
        state = 'exited'
    elif not app:
        state = 'uncertain'
    elif verify_identity(app):
        fresh = capture_identity(app['pid'])
        state = 'exited' if fresh and 'Z' in fresh.get('state','') else 'running'
    elif not capture_identity(app['pid']):
        state = 'exited'
    else:
        state = 'uncertain'
    session['state'] = state
    save_session(ctx, session)
    return {'status': 'uncertain' if state == 'uncertain' else 'success', 'state': state}
