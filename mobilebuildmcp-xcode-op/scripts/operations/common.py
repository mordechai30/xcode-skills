"""Resolve requests and provide the retained operation context."""
import importlib
import json
from pathlib import Path
from lifecycle.state import atomic_json, read_json
from lifecycle.process import verify_identity


def backend(root):
    """Load the package's own adapter.
    No installed skill is imported by another package.
    """
    name = json.loads((root / 'backend-choice.json').read_text())['backend']
    return importlib.import_module('backend.' + name)


def ask(message, choices=None):
    """Return a request for user input without performing an action.
    Choices describe supported next requests.
    """
    return {'status': 'needs_user_input', 'message': message, 'choices': choices or []}


def context(args, root):
    """Reuse the runtime context or resolve a new container.
    Detailed artifacts use the selected app project's directory.
    """
    if getattr(args, '_context', None) is not None:
        return args._context
    package = getattr(args, 'package', None)
    container = args.project or args.workspace or package
    if not container or not container.exists():
        raise ValueError('Select an existing project or workspace.')
    expected = '.xcodeproj' if args.project else '.xcworkspace'
    if not package and container.suffix != expected:
        raise ValueError('The container suffix does not match the selected input.')
    selection = {key: getattr(args, key, None) for key in
                 ('configuration', 'scheme', 'target', 'destination', 'architecture')}
    selection.update(project=str(args.project.resolve()) if args.project else None,
                     workspace=str(args.workspace.resolve()) if args.workspace else None,
                     derived_data=str(args.derived_data.resolve()) if args.derived_data else None)
    adapter = backend(root)
    if package:
        if getattr(args, 'derived_data', None) or getattr(args, 'architecture', None):
            raise ValueError('SwiftPM uses the current host and its backend build location; omit --derived-data and --architecture.')
        package = package.resolve()
        package = package.parent if package.name == 'Package.swift' else package
        if not (package / 'Package.swift').is_file():
            raise ValueError('Select a Swift package with Package.swift.')
        from backend.swiftpm import Adapter
        adapter = Adapter(adapter)
        selection.update(package=str(package), arguments=getattr(args, 'arguments', []))
    return {'root': root, 'skill': root.name, 'selection': selection,
            'backend': adapter, 'active_path': root / '.active-session.json',
            'runtime': {}, 'session': None}


def resolve_selection(ctx, args, need_destination=True):
    """Discover and select one app, scheme, and destination.
    A workspace uses the owning project returned by build settings.
    """
    found = ctx['backend'].discover(args, ctx)
    ctx['discovery'] = found
    for key in ('scheme', 'target'):
        options = found.get('choices', {}).get(key, [])
        selected = ctx['selection'].get(key)
        if selected is None:
            if len(options) != 1:
                return ask('Select ' + key + '.', options)
            ctx['selection'][key] = options[0]
        elif selected not in options:
            return ask('Unsupported ' + key + ': ' + selected, options)
    owner = found.get('owners', {}).get(ctx['selection']['target'])
    if not owner:
        return ask('The selected app target owning project could not be determined.')
    ctx['selection']['owner_project'] = owner
    ctx['data_dir'] = (Path(owner) if ctx['selection'].get('package') else Path(owner).parent) / ctx['skill']
    ctx['data_dir'].mkdir(parents=True, exist_ok=True)
    if need_destination:
        destination_discovery = getattr(ctx['backend'], 'discover_destinations', None)
        options = destination_discovery(args, ctx) if destination_discovery else None
        if options is None:
            options = found.get('choices', {}).get('destination', [])
        selected = ctx['selection'].get('destination')
        if selected is None:
            if len(options) != 1:
                return ask('Select destination.', options)
            ctx['selection']['destination'] = options[0]
        elif selected not in options:
            return ask('Unsupported destination: ' + selected, options)
    return {'status': 'success', 'selection': ctx['selection']}


def current_session(ctx):
    """Return the retained session or read the active locator.
    A locator blocks replacement even when its channel is lost.
    """
    return ctx.get('session') or read_json(ctx['active_path'])


def save_session(ctx, value):
    """Persist detailed session state and a small skill-level locator.
    The runtime connection itself stays in memory.
    """
    ctx['session'] = value
    if value is None:
        ctx['active_path'].unlink(missing_ok=True)
        return
    atomic_json(ctx['data_dir'] / 'session.json', value)
    atomic_json(ctx['active_path'], {'data_dir': str(ctx['data_dir']),
                                   'selection': ctx['selection'],
                                   'runtime_identity': ctx.get('runtime_identity')})


def debug_context(args, root):
    """Check that follow-up work uses the owned Debug session.
    Refresh state through the retained connection before each request.
    """
    ctx = context(args, root)
    session = ctx.get('session')
    if not session or not session.get('debugger'):
        raise ValueError('This operation requires a debugger-enabled Debug session.')
    state = ctx['backend'].debug_status(ctx)
    if state.get('status') != 'success':
        raise RuntimeError('The retained debugger did not provide verified current state: ' + str(state))
    app = session.get('app')
    if app and state.get('state') != 'exited' and state.get('pid') != app['pid']:
        raise RuntimeError('The debugger process differs from the recorded app. No external session will be adopted.')
    if app and state.get('state') != 'exited' and not verify_identity(app):
        raise RuntimeError('The recorded app identity changed. No reused PID will become this session.')
    observe(ctx, state)
    return ctx, state


def observe(ctx, state):
    """Persist verified execution state and actual session breakpoint hits.
    A resolved location alone never records a breakpoint hit.
    """
    session = ctx.get('session')
    if not session or state.get('status') != 'success':
        return
    session['current_debug_state'] = state
    session['state'] = state.get('state', session.get('state'))
    for breakpoint in session.get('breakpoints', []):
        causes = {number for stop in state.get('stops', []) for number in stop.get('breakpoints', [])}
        if state.get('state') == 'paused' and breakpoint['id'] in causes:
            breakpoint['hit'] = True
            breakpoint['last_stop'] = state
    save_session(ctx, session)
