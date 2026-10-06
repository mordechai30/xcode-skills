"""Build once and launch the selected product."""
import json
from operations.build import perform, finish
from operations.common import ask, context, resolve_selection, save_session
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
                      'breakpoints': []})


def execute(args, root):
    """Run once and retain verified ownership records.
    Embedded backends return separate Build and launch evidence.
    """
    ctx = context(args, root)
    if ctx.get('session'):
        return ask('An app context already exists. Kill it before Run.')
    selected = resolve_selection(ctx, args) if not ctx.get('selection_ready') else {'status': 'success'}
    if selected['status'] != 'success':
        return selected
    choose = getattr(ctx['backend'], 'select_run_route', None)
    if choose:
        rejected = choose(args, ctx)
        if rejected:
            return rejected
    embedded = getattr(ctx['backend'], 'embedded_build', lambda a: False)(args)
    product = ctx['backend'].resolve_product(args, ctx) if embedded else {}
    if embedded and product['status'] not in ('success', 'missing'):
        return ask('Selected product evidence is unavailable or uncertain.') | {'product': product}
    if embedded:
        pending(ctx, args, product)
        outcome = ctx['backend'].launch(args, ctx, product)
        build_result = outcome['build']
    else:
        build_result = perform(args, ctx)
    completed = finish(args, ctx, build_result)
    if completed['status'] != 'success':
        if embedded and outcome.get('app'):
            session = outcome | {'selection': ctx['selection'], 'breakpoints': []}
            save_session(ctx, session)
        elif embedded and build_result['status'] == 'failure':
            save_session(ctx, None)
        return completed
    product = ctx['backend'].resolve_product(args, ctx)
    if product['status'] != 'success':
        return ask('Build completed but the selected product could not be verified.') | {'product': product}
    if not embedded:
        pending(ctx, args, product)
        outcome = ctx['backend'].launch(args, ctx, product)
    if outcome.get('state') == 'not_launched':
        save_session(ctx, None)
        ctx['backend'].close(ctx)
        return outcome
    outcome.setdefault('debugger', args.configuration == 'Debug' and not args.no_debugger)
    if not outcome.get('state'):
        outcome['state'] = 'uncertain'
    if outcome.get('status') == 'uncertain' and not outcome.get('message'):
        outcome['message'] = 'Launch verification is incomplete. Use Status before another Run.'
    if ctx.get('session'):
        recorded = ctx['session']['dedicated']
        outcome['dedicated'] = list({entry['pid']: entry for entry in recorded + outcome.get('dedicated', []) if entry}.values())
    session = outcome | {'selection': ctx['selection'], 'product': product,
                         'breakpoints': []}
    if outcome.get('app') or outcome.get('dedicated') or outcome['status'] == 'uncertain' or outcome['state'] == 'exited':
        save_session(ctx, session)
    else:
        save_session(ctx, None)
        ctx['backend'].close(ctx)
    if (outcome.get('app') or {}).get('pid'):
        outcome['pid'] = outcome['app']['pid']
    return {key: outcome[key] for key in ('status', 'state', 'pid', 'debugger', 'message') if key in outcome}
