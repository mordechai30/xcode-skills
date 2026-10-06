"""Native launch and retained LLDB connection helpers."""
import os
import shlex
from pathlib import Path
import subprocess
import time
from lifecycle.channel import connect
from lifecycle.process import capture_identity, verify_identity, traced
from lifecycle.state import atomic_json
from lifecycle.schemes import launch_arguments
from lifecycle.output import capture_process


def request(ctx, action, **values):
    """Address the existing controller only.
    A missing channel is reported without creating another debugger.
    """
    deadline = ctx.get('request_deadline')
    timeout = min(15, deadline - time.monotonic()) if deadline is not None else 15
    if timeout <= 0:
        raise TimeoutError('Pause expired. Use Status.')
    return connect(ctx['data_dir'], 'd.sock', {'action': action, '_deadline':deadline, **values}, timeout=timeout)


def launch(args, ctx, product):
    """Launch once through LLDB or directly without a debugger.
    Retain owned child handles so cleanup can reap them.
    """
    debug = args.configuration == 'Debug' and not args.no_debugger
    folder = ctx['data_dir']
    arguments = launch_arguments(ctx['selection'])
    working = str(args.working_directory.resolve() if args.working_directory else Path(product['executable']).parent)
    if debug:
        script = Path(__file__).with_name('lldb_controller.py')
        process = subprocess.Popen(['xcrun', 'lldb', '--no-lldbinit', '-b', '-o',
                                    'command script import ' + shlex.quote(str(script)), '-o', 'skill_controller'],
                                   cwd=folder, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        capture_process(process, ctx, 'LLDB diagnostics')
        ctx['runtime']['controller'] = process
        if ctx.get('session'):
            ctx['session']['dedicated'] = [capture_identity(process.pid)]
            atomic_json(folder / 'session.json', ctx['session'])
        deadline = time.monotonic() + 15
        while not (folder / 'd.sock').exists() and process.poll() is None and time.monotonic() < deadline:
            time.sleep(.05)
        if not (folder / 'd.sock').exists():
            raise RuntimeError('LLDB controller did not initialize; Inspect the operation log.')
        launched = request(ctx, 'launch', executable=product['executable'], working_directory=working, arguments=arguments, log=str(ctx['log']))
        if launched['status'] != 'success':
            return launched
        pid = launched['pid']
        dedicated = [capture_identity(process.pid)]
    else:
        process = subprocess.Popen([product['executable'], *arguments], cwd=working, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        capture_process(process, ctx, 'App diagnostics')
        ctx['runtime']['app_child'] = process
        pid = process.pid
        dedicated = []
        launched = {'status': 'success', 'state': 'running'}
    if not debug and process.poll() is not None:
        return {'status':'success','state':'exited','debugger':False,'dedicated':[]}
    identity = capture_identity(pid)
    if debug and (not identity or identity.get('state') == 'Z'):
        fresh = request(ctx, 'status')
        if fresh.get('state') == 'exited':
            return {'status': 'success', 'state': 'exited', 'debugger': True,
                    'dedicated': dedicated, 'debug_state': fresh}
    if ctx.get('session') and identity and verify_identity(identity, product['executable']):
        ctx['session']['app'] = identity
        ctx['session']['dedicated'] = dedicated
        atomic_json(folder / 'session.json', ctx['session'])
    if debug and identity:
        helper = capture_identity(identity['parentPID'])
        if helper and Path(helper['executable']).name == 'debugserver' and helper['parentPID'] == process.pid:
            dedicated.append(helper)
    if not identity and (debug and launched.get('state') == 'exited' or not debug and process.poll() is not None):
        return {'status': 'success', 'state': 'exited', 'debugger': debug, 'dedicated': dedicated}
    if not identity or not verify_identity(identity, product['executable']):
        return {'status': 'uncertain', 'message': 'Launch identity could not be verified.',
                'app': identity, 'debugger': debug, 'dedicated': dedicated}
    attachment = traced(pid)
    return {'status': 'success' if attachment == debug else 'uncertain', 'state': launched['state'], 'app': identity,
            'attachment_verified': attachment == debug,
            'debugger': debug, 'dedicated': dedicated, 'debug_state': launched}


def close(ctx):
    """Close and reap the owned controller after app termination.
    A failed channel does not prevent reaping an owned child handle.
    """
    controller = ctx['runtime'].get('controller')
    if controller and controller.poll() is None:
        try:
            request(ctx, 'close')
            controller.wait(timeout=3)
        except (OSError, RuntimeError, subprocess.TimeoutExpired):
            controller.terminate()
            try:
                controller.wait(timeout=3)
            except subprocess.TimeoutExpired:
                controller.kill()
                controller.wait(timeout=3)
    child = ctx['runtime'].get('app_child')
    if child and child.poll() is not None:
        child.wait()
