"""Build preparation and failure rules for explicit and embedded builds."""
import json
from lifecycle.state import append_log, atomic_json, clean_required, new_log, previous_build, read_json
from operations.common import ask, context, current_session, resolve_selection
from lifecycle.products import record
from operations.clean import execute as clean


def prepare(args, ctx):
    """Create the attempt log and complete prerequisite Clean.
    Failed preparation does not mark a Build as invoked.
    """
    previous = previous_build(ctx['data_dir'], ctx['skill'], args.configuration, ctx['selection'])
    ctx['log'], now = new_log(ctx['data_dir'], ctx['skill'], args.configuration)
    append_log(ctx['log'], 'Selection', json.dumps(ctx['selection']))
    with ctx['log'].open('a') as stream:
        stream.write('BUILD_CONTEXT=' + json.dumps(ctx['selection']) + '\n')
    ctx['mark_build'] = lambda: invoked(ctx)
    append_log(ctx['log'], 'Discovery', json.dumps(ctx['discovery']))
    pending = ctx['data_dir'] / ('clean-required-' + args.configuration + '.json')
    if clean_required(previous, now) or read_json(pending, False):
        result = clean(args, ctx)
        append_log(ctx['log'], 'Prerequisite Clean', json.dumps(result))
        if result['status'] != 'success':
            atomic_json(pending, True)
            return ask('Prerequisite Clean failed. Build was not invoked.') | {'clean': result, 'log': str(ctx['log'])}
        pending.unlink(missing_ok=True)
    return {'status': 'success'}


def invoked(ctx):
    """Mark actual backend invocation for Build-age accounting.
    Preparation-only logs remain outside Build history.
    """
    with ctx['log'].open('a') as stream:
        stream.write('BUILD_INVOKED\n')


def finish(args, ctx, result):
    """Record Build evidence and perform required failure Clean.
    No retry is made after a failed or uncertain result.
    """
    append_log(ctx['log'], 'Build result', json.dumps(result))
    if result['status'] == 'failure':
        cleaned = clean(args, ctx)
        append_log(ctx['log'], 'Failed Build Clean', json.dumps(cleaned))
        pending = ctx['data_dir'] / ('clean-required-' + args.configuration + '.json')
        if cleaned['status'] != 'success':
            atomic_json(pending, True)
        else:
            pending.unlink(missing_ok=True)
        return ask('Build failed. Clean was attempted. Wait for user instruction.') | {'build': result, 'clean': cleaned, 'log': str(ctx['log'])}
    if result['status'] != 'success':
        return ask('Build outcome is uncertain. Inspect evidence before another attempt.') | {'build': result, 'log': str(ctx['log'])}
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
    append_log(ctx['log'], 'Product verification', json.dumps(product))
    if product['status'] == 'success':
        record(ctx, product)
    return {'status': product['status'], 'build': result, 'product': product, 'log': str(ctx['log'])}


def perform(args, ctx):
    """Retain backend exceptions as uncertain Build evidence.
    Verified backend failure results still pass through failure Clean.
    """
    try:
        return ctx['backend'].build(args, ctx)
    except (RuntimeError, OSError, TimeoutError) as error:
        return {'status': 'uncertain', 'message': str(error)}
