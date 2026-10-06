"""Build preparation and failure rules for explicit and embedded builds."""
from lifecycle.state import append_log, atomic_json, clean_required, new_log, previous_build, read_json
from lifecycle.diagnostics import diagnostics
from operations.common import ask, context, current_session, resolve_selection
from operations.clean import execute as clean


def prepare(args, ctx):
    """Create the attempt log and complete prerequisite Clean.
    Failed preparation does not mark a Build as invoked.
    """
    previous = previous_build(ctx['data_dir'], ctx['skill'], args.configuration, ctx['selection'])
    ctx['log'], now = new_log(ctx['data_dir'], ctx['skill'], args.configuration)
    ctx['mark_build'] = lambda: invoked(ctx)
    preflight = ctx['data_dir'] / 'preflight-output.txt'
    if preflight.exists():
        from lifecycle.output import record_detail
        record_detail(ctx,'Diagnostics',diagnostics(preflight.read_text()))
        preflight.unlink()
    for evidence in ctx.pop('evidence', []):
        from lifecycle.output import record_detail
        record_detail(ctx,'Diagnostics',diagnostics(evidence))
    pending = ctx['data_dir'] / ('clean-required-' + args.configuration + '.json')
    if clean_required(previous, now) or read_json(pending, False):
        result = clean(args, ctx)
        if result['status'] != 'success':
            atomic_json(pending, True)
            return {'status':'uncertain' if result['status'] == 'uncertain' else 'failure','stage':'clean','message':result.get('message') or 'Prerequisite Clean failed.','next':'Build was not invoked. Wait for user instruction.','log':str(ctx['log'])}
        pending.unlink(missing_ok=True)
    return {'status': 'success'}


def invoked(ctx):
    """Mark actual backend invocation for Build-age accounting.
    Preparation-only logs remain outside Build history.
    """
    with ctx['log'].open('a') as stream:
        stream.write('Build invoked.\n')


def finish(args, ctx, result):
    """Record Build evidence and perform required failure Clean.
    No retry is made after a failed or uncertain result.
    """
    if result['status'] == 'failure':
        cleaned = clean(args, ctx)
        pending = ctx['data_dir'] / ('clean-required-' + args.configuration + '.json')
        if cleaned['status'] != 'success':
            atomic_json(pending, True)
        else:
            pending.unlink(missing_ok=True)
        cause = result.get('message') or diagnostics(result.get('raw', result)) or 'Build failed.'
        return {'status':'failure','stage':'build','message':cause,'next':'Wait for user instruction.','log':str(ctx['log'])}
    if result['status'] != 'success':
        return {'status':'uncertain','stage':'build','message':result.get('message') or 'Build outcome was not verified.','next':'Reconcile backend state before another Build or Run.','log':str(ctx['log'])}
    return {'status': 'success'}


def execute(args, root):
    """Build the selected configuration without launching.
    Verify the selected executable after backend success.
    """
    ctx = context(args, root)
    if current_session(ctx):
        return ask('An active context requires Kill and cleanup before Build.', ['kill', 'wait'])
    selected = resolve_selection(ctx, args)
    if selected['status'] != 'success':
        return selected
    prepared = prepare(args, ctx)
    if prepared['status'] != 'success':
        return prepared
    result = perform(args, ctx)
    completed = finish(args, ctx, result)
    if completed['status'] != 'success':
        return completed
    product = ctx['backend'].resolve_product(args, ctx)
    return {'status':'success' if product['status'] == 'success' else 'uncertain', 'stage':'build' if product['status'] == 'success' else 'product', 'message':'Built; not launched.' if product['status'] == 'success' else 'Selected executable was not verified.', 'log':str(ctx['log'])}


def perform(args, ctx):
    """Retain backend exceptions as uncertain Build evidence.
    Verified backend failure results still pass through failure Clean.
    """
    try:
        return ctx['backend'].build(args, ctx)
    except (RuntimeError, OSError, TimeoutError) as error:
        return {'status': 'uncertain', 'message': str(error)}
