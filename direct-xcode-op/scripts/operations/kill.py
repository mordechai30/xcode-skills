"""Terminate app first, then verified dedicated debugger processes."""
from pathlib import Path
from lifecycle.process import capture_identity, terminate_identity, verify_identity, matching_processes
from lifecycle.state import read_json, atomic_json, remove_closed_channels
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
    app_unknown = False
    if not app and session.get('state') in ('launch_pending', 'uncertain'):
        executable = session.get('product', {}).get('executable')
        if not app and (not executable or matching_processes(executable)):
            app_unknown = True
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
    if app_result['status'] == 'zombie' and app_result.get('identity', {}).get('parentPID') == 1:
        app_result = {'status':'success','reason':'terminated; defunct entry awaits system reaping'}
    dedicated = [record for record in session.get('dedicated', []) if record]
    if app_result['status'] == 'zombie' and parent and parent['pid'] != ctx.get('runtime_identity', {}).get('pid'):
        if not any(record['pid'] == parent['pid'] and verify_identity(record) for record in dedicated):
            return ask('App is a zombie under a parent not verified as dedicated. Select parent cleanup.') | {'app': app_result, 'parent': parent}
    collect(ctx)
    try:
        ctx['backend'].close(ctx)
    except (RuntimeError, OSError, TimeoutError) as error:
        from lifecycle.output import record_detail
        record_detail(ctx, 'Diagnostics', 'error: '+str(error))
    collect(ctx)
    helpers = [terminate_identity(record) for record in dedicated]
    if app and capture_identity(app['pid']) is not None and app_result.get('reason') != 'terminated; defunct entry awaits system reaping':
        child = ctx['runtime'].get('app_child')
        if child and child.poll() is not None:
            child.wait()
        app_result = terminate_identity(app)
    complete = not app_unknown and app_result['status'] == 'success' and all(value['status'] == 'success' for value in helpers)
    warning = 'IDE breakpoint may remain.' if any(value['status'] != 'success' for value in breakpoints) else None
    if complete:
        save_session(ctx, None)
    elif app_unknown:
        session['state'] = 'uncertain'
        session['dedicated'] = [record for record, result in zip(dedicated, helpers) if result['status'] != 'success']
        save_session(ctx, session)
    return {'status': 'success' if complete else 'uncertain', 'stage':'kill',
            'helpers':'terminated' if all(value['status'] == 'success' for value in helpers) else 'unverified',
            'app': 'unverified' if app_unknown else 'terminated' if app_result['status'] == 'success' else 'unverified', 'dedicated': helpers, 'breakpoints': breakpoints,
            'warning': warning,
            'message': 'Cleanup complete.' if complete else 'App cleanup is unverified. Reconcile app state before another Run.'}


def recover(root, locator):
    """Kill from verified ownership records after channel loss.
    No debugger is attached or replaced during recovery.
    """
    folder = Path(locator['data_dir'])
    session = read_json(folder / 'session.json')
    session = session or {}
    if session.get('state') == 'closed':
        root.joinpath('.active-session.json').unlink(missing_ok=True)
        folder.joinpath('m.sock').unlink(missing_ok=True)
        return {'status':'success','stage':'kill','app':'terminated','helpers':'terminated'}
    app = session.get('app')
    executable = session.get('product', {}).get('executable')
    app_unknown = not app and session.get('state') != 'exited' and (not executable or bool(matching_processes(executable)))
    parent = capture_identity(app['parentPID']) if app else None
    app_result = terminate_identity(app) if app else {'status':'success'}
    if app_result['status'] == 'zombie' and app_result.get('identity', {}).get('parentPID') == 1:
        app_result = {'status':'success','reason':'terminated; defunct entry awaits system reaping'}
    owned = [entry for entry in session.get('dedicated', []) if entry]
    runtime = locator.get('runtime_identity')
    if runtime:
        owned.append(runtime)
    if app_result['status'] == 'zombie' and parent and not any(entry['pid'] == parent['pid'] and verify_identity(entry) for entry in owned):
        return ask('Zombie parent is not verified as dedicated. Select parent cleanup.') | {'app': app_result, 'parent': parent}
    owned.sort(key=lambda entry: entry['pid'] != (app or {}).get('parentPID'))
    helpers = [terminate_identity(entry) for entry in owned]
    for index, entry in enumerate(owned):
        if capture_identity(entry['pid']) is None:
            helpers[index] = {'status': 'success', 'reason': 'dedicated process disappeared'}
    fresh = capture_identity(app['pid']) if app else None
    if not fresh:
        app_result = {'status': 'success', 'reason': 'app disappeared'}
    complete = not app_unknown and app_result['status'] == 'success' and all(entry['status'] == 'success' for entry in helpers)
    result = {'status': 'success' if complete else 'uncertain', 'stage':'kill',
              'app':'terminated' if complete else 'unverified', 'helpers':'terminated' if all(entry['status'] == 'success' for entry in helpers) else 'unverified',
              'warning': 'IDE breakpoint may remain.' if session.get('breakpoints') else None,
              'message': 'Recovered cleanup complete.' if complete else 'Recovered cleanup remains incomplete.'}
    if complete:
        remove_closed_channels(folder)
        atomic_json(folder / 'session.json', {'state':'closed','configuration':session.get('selection',{}).get('configuration'),'app':'terminated','helpers':'terminated'})
        root.joinpath('.active-session.json').unlink(missing_ok=True)
        folder.joinpath('m.sock').unlink(missing_ok=True)
    else:
        session['state'] = 'uncertain'
        session['dedicated'] = [entry for entry, value in zip(owned, helpers) if value['status'] != 'success']
        atomic_json(folder / 'session.json', session)
    return result
