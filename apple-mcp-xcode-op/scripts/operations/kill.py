"""Terminate app first, then verified dedicated debugger processes."""
from pathlib import Path
from lifecycle.process import capture_identity, terminate_identity, verify_identity, matching_processes
from lifecycle.state import append_log, read_json
from operations.common import ask, context, save_session
from lifecycle.output import collect


def execute(args, root):
    """Use backend termination before verified signal fallback.
    Shared or unrelated parents require the user's choice.
    """
    ctx = context(args, root)
    session = ctx.get('session')
    if not session:
        return ask('No recorded session is available for Kill.')
    app = session.get('app')
    if not app and session.get('state') in ('launch_pending', 'uncertain'):
        if session.get('debugger'):
            try:
                state = ctx['backend'].debug_status(ctx)
            except (RuntimeError, OSError, TimeoutError):
                state = {'state': 'uncertain'}
            candidate = capture_identity(state.get('pid', -1))
            if candidate and verify_identity(candidate, session['product']['executable']):
                app = candidate
                session['app'] = candidate
                save_session(ctx, session)
        executable = session.get('product', {}).get('executable')
        if not app and (not executable or matching_processes(executable)):
            return ask('Launch outcome has no verified app identity. Reconcile it before claiming cleanup.')
    parent = capture_identity(app['parentPID']) if app else None
    breakpoints = []
    if session.get('debugger'):
        for breakpoint in session.get('breakpoints', []):
            try:
                deleted = ctx['backend'].debug_action(ctx, 'delete_breakpoint', id=breakpoint['id'])
            except (RuntimeError, OSError, TimeoutError) as error:
                deleted = {'status': 'failure', 'message': str(error)}
            breakpoints.append({'id': breakpoint['id'], **deleted})
        removed = {entry['id'] for entry in breakpoints if entry['status'] == 'success'}
        session['breakpoints'] = [entry for entry in session.get('breakpoints', []) if entry['id'] not in removed]
        if ctx.get('active_path'):
            save_session(ctx, session)
    try:
        backend = ctx['backend'].stop(ctx) if app else {'status': 'success', 'message': 'No selected executable is currently running.'}
    except (RuntimeError, OSError, TimeoutError) as error:
        backend = {'status': 'failure', 'message': str(error)}
    app_result = terminate_identity(app) if app else {'status': 'success', 'reason': 'already exited'}
    dedicated = [record for record in session.get('dedicated', []) if record]
    if app_result['status'] == 'zombie' and parent and parent['pid'] != ctx.get('runtime_identity', {}).get('pid'):
        if not any(record['pid'] == parent['pid'] and verify_identity(record) for record in dedicated):
            return ask('App is a zombie under a parent not verified as dedicated. Select parent cleanup.') | {'app': app_result, 'parent': parent}
    collect(ctx)
    ctx['backend'].close(ctx)
    collect(ctx)
    helpers = [terminate_identity(record) for record in dedicated]
    if app and capture_identity(app['pid']) is not None:
        child = ctx['runtime'].get('app_child')
        if child and child.poll() is not None:
            child.wait()
        app_result = terminate_identity(app)
    complete = app_result['status'] == 'success' and all(value['status'] == 'success' for value in helpers)
    warning = 'Breakpoint removal was not verified; an IDE breakpoint may remain.' if any(value['status'] != 'success' for value in breakpoints) else None
    if complete:
        save_session(ctx, None)
    return {'status': 'success' if complete else 'needs_user_input',
            'backend': backend, 'app': app_result, 'dedicated': helpers, 'breakpoints': breakpoints,
            'warning': warning,
            'message': ('Cleanup complete. ' + warning if warning else 'Cleanup complete.') if complete else 'Cleanup remains incomplete.'}


def recover(root, locator):
    """Kill from verified ownership records after channel loss.
    No debugger is attached or replaced during recovery.
    """
    folder = Path(locator['data_dir'])
    session = read_json(folder / 'session.json')
    if not session or not session.get('app'):
        return ask('Lost context has no verified app record. Inspect launch evidence before cleanup.')
    app = session['app']
    parent = capture_identity(app['parentPID'])
    app_result = terminate_identity(app)
    owned = [entry for entry in session.get('dedicated', []) if entry]
    runtime = locator.get('runtime_identity')
    if runtime:
        owned.append(runtime)
    if app_result['status'] == 'zombie' and parent and not any(entry['pid'] == parent['pid'] and verify_identity(entry) for entry in owned):
        return ask('Zombie parent is not verified as dedicated. Select parent cleanup.') | {'app': app_result, 'parent': parent}
    owned.sort(key=lambda entry: entry['pid'] != app['parentPID'])
    helpers = [terminate_identity(entry) for entry in owned]
    for index, entry in enumerate(owned):
        if capture_identity(entry['pid']) is None:
            helpers[index] = {'status': 'success', 'reason': 'dedicated process disappeared'}
    fresh = capture_identity(app['pid'])
    if not fresh:
        app_result = {'status': 'success', 'reason': 'app disappeared'}
    complete = app_result['status'] == 'success' and all(entry['status'] == 'success' for entry in helpers)
    result = {'status': 'success' if complete else 'needs_user_input', 'app': app_result, 'dedicated': helpers,
              'warning': 'Breakpoint removal was not verified; an IDE breakpoint may remain.' if session.get('breakpoints') else None,
              'message': ('Recovered cleanup complete. ' + ('Breakpoint removal unverified; an IDE breakpoint may remain.' if session.get('breakpoints') else '')) if complete else 'Recovered cleanup remains incomplete.'}
    if session.get('log'):
        collect({'log': Path(session['log']), 'data_dir': folder, 'runtime': {}})
        append_log(Path(session['log']), 'Kill recovery', str(result))
    if complete:
        root.joinpath('.active-session.json').unlink(missing_ok=True)
    return result
