"""Build selected products without automatic cleaning or stored history."""
from lifecycle.diagnostics import diagnostics
from operations.common import ask, context, current_session, resolve_selection


def finish(args, ctx, result):
    """Report Build failure or uncertainty without another operation.
    A failed Build never triggers Clean or an automatic retry.
    """
    if result['status'] == 'failure':
        cause = result.get('message') or diagnostics(result.get('raw', result)) or 'Build failed.'
        return {'status':'failure','stage':'build','message':cause}
    if result['status'] != 'success':
        return {'status':'uncertain','stage':'build','message':result.get('message') or 'Build outcome was not verified.','next':'Reconcile backend state before another Build or Run.'}
    return {'status': 'success'}


def execute(args, root):
    """Build the selected configuration without launching.
    Verify the selected executable after backend success.
    """
    ctx = context(args, root)
    if current_session(ctx):
        return ask('Kill the active app before Build.', ['kill', 'wait'])
    selected = resolve_selection(ctx, args)
    if selected['status'] != 'success':
        return selected
    completed = finish(args, ctx, perform(args, ctx))
    if completed['status'] != 'success':
        return completed
    product = ctx['backend'].resolve_product(args, ctx)
    return {'status':'success' if product['status'] == 'success' else 'uncertain', 'stage':'build' if product['status'] == 'success' else 'product', 'message':'Built; not launched.' if product['status'] == 'success' else 'Selected executable was not verified.'}


def perform(args, ctx):
    """Invoke Build once and retain backend exceptions as uncertainty.
    No additional Build or cleanup follows a failure.
    """
    try:
        return ctx['backend'].build(args, ctx)
    except (RuntimeError, OSError, TimeoutError) as error:
        return {'status': 'uncertain', 'message': str(error)}
