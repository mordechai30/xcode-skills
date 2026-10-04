"""Launch the selected product after required Build preparation."""
import json
from lifecycle.state import append_log
from operations.build import prepare, perform, finish
from operations.common import ask, context, resolve_selection, save_session
from lifecycle.products import record
from lifecycle.process import capture_identity


def pending(ctx, args, product):
    """Save launch uncertainty and already-created owned connection processes.
    Interrupted calls retain records needed for verified Kill recovery.
    """
    dedicated = []
    for name in ('bridge', 'mobile_server'):
        connection = ctx['runtime'].get(name)
        process = getattr(connection, 'process', None)
        if process:
            identity = capture_identity(process.pid)
            if identity:
                dedicated.append(identity)
    save_session(ctx, {'status': 'uncertain', 'state': 'launch_pending', 'app': None,
                      'debugger': args.configuration == 'Debug' and not args.no_debugger,
                      'dedicated': dedicated, 'selection': ctx['selection'], 'product': product,
                      'log': str(ctx['log']), 'breakpoints': []})


def execute(args, root):
    """Run once and retain verified ownership records.
    Embedded backends return separate Build and launch evidence.
    """
    ctx = context(args, root)
    if ctx.get('session'):
        return ask('An app context already exists. Kill it before Run.')
    if not ctx.get('discovery'):
        selected = resolve_selection(ctx, args)
        if selected['status'] != 'success':
            return selected
    product = ctx['backend'].resolve_product(args, ctx)
    embedded = getattr(ctx['backend'], 'embedded_build', lambda a: False)(args)
    if product['status'] not in ('success', 'missing'):
        return ask('Selected product evidence is unavailable or uncertain.') | {'product': product}
    prepared = prepare(args, ctx)
    if prepared['status'] != 'success':
        return prepared
    if embedded:
        pending(ctx, args, product)
        outcome = ctx['backend'].launch(args, ctx, product)
        build_result = outcome['build']
    else:
        build_result = perform(args, ctx)
    completed = finish(args, ctx, build_result)
    if completed['status'] != 'success':
        if embedded and outcome.get('app'):
            session = outcome | {'selection': ctx['selection'], 'log': str(ctx['log']), 'breakpoints': []}
            save_session(ctx, session)
        elif embedded and build_result['status'] == 'failure':
            save_session(ctx, None)
        return completed
    product = ctx['backend'].resolve_product(args, ctx)
    if product['status'] != 'success':
        return ask('Build completed but the selected product could not be verified.') | {'product': product}
    record(ctx, product)
    if not embedded:
        pending(ctx, args, product)
        outcome = ctx['backend'].launch(args, ctx, product)
    if outcome.get('state') == 'not_launched':
        save_session(ctx, None)
        ctx['backend'].close(ctx)
        return outcome
    outcome.setdefault('debugger', args.configuration == 'Debug' and not args.no_debugger)
    outcome.setdefault('state', 'uncertain')
    append_log(ctx['log'], 'Launch result', json.dumps(outcome))
    if ctx.get('session'):
        recorded = ctx['session']['dedicated']
        outcome['dedicated'] = list({entry['pid']: entry for entry in recorded + outcome.get('dedicated', []) if entry}.values())
    session = outcome | {'selection': ctx['selection'], 'product': product,
                         'log': str(ctx['log']), 'breakpoints': []}
    if outcome.get('app') or outcome.get('dedicated') or outcome['status'] == 'uncertain':
        save_session(ctx, session)
    else:
        save_session(ctx, None)
        ctx['backend'].close(ctx)
    return outcome | {'product': product, 'log': str(ctx['log'])}
