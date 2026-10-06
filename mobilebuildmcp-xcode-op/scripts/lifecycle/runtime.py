"""Own the retained backend runtime and its local request channel.
The public manager forwards requests without interpreting backend protocols.
"""
import argparse
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time

from lifecycle.channel import connect
from lifecycle.output import collect, capture_process
from lifecycle.process import capture_identity
from lifecycle.state import append_log, atomic_json, read_json
from operations.common import ask, context, resolve_selection, observe


def namespace(values):
    """Restore JSON requests to argparse inputs.
    Path inputs use the same types as the public CLI.
    """
    for key in ('project', 'workspace', 'package', 'file', 'working_directory', 'derived_data'):
        if values.get(key):
            values[key] = Path(values[key])
    return argparse.Namespace(**values)


def serve(folder, root, dispatch):
    """Own the backend connection until required cleanup completes.
    Watching is performed by brief status requests outside this loop.
    """
    bootstrap = read_json(folder / 'runtime-request.json')
    args = namespace(bootstrap['args'])
    (folder / 'runtime-request.json').unlink()
    ctx = context(args, root)
    ctx.update(data_dir=folder, selection=bootstrap['selection'], discovery=bootstrap['discovery'],
               runtime_identity=capture_identity(os.getpid()))
    del bootstrap, args
    os.chdir(folder)
    with socket.socket(socket.AF_UNIX) as server:
        server.bind('m.sock')
        os.chmod('m.sock', 0o600)
        server.listen(8)
        atomic_json(root / '.active-session.json', {'data_dir': str(folder), 'runtime_identity': ctx['runtime_identity']})
        while True:
            channel, _ = server.accept()
            with channel:
                with channel.makefile('r') as stream:
                    message = json.loads(stream.readline())
                if message.get('operation') == '_watch':
                    try:
                        value = ctx['backend'].debug_status(ctx)
                    except (RuntimeError, OSError, TimeoutError) as error:
                        value = {'status': 'uncertain', 'message': str(error)}
                    observe(ctx, value)
                    collect(ctx)
                    if value.get('state') != 'running':
                        for kind in ('warning','error'):
                            if ctx.get('public_'+kind):
                                value[kind] = ctx.pop('public_'+kind)
                                ctx.pop('public_'+kind+'_count',None)
                    if value.get('state') != 'running' and ctx.get('log'):
                        append_log(ctx['log'], 'Watch ended', value.get('state', 'uncertain'))
                else:
                    request = namespace(message)
                    conflict = message['operation'] != 'run' and any(message.get(key) and str(message[key]) != str(ctx['selection'].get(key))
                                   for key in ('project', 'workspace', 'package', 'configuration', 'scheme', 'target', 'destination'))
                    value = ask('Supplied selection conflicts with the active context.') if conflict else dispatch(request, ctx)
                    if message['operation'] == 'run':
                        ctx['selection'].pop('arguments', None)
                        request.arguments = None
                        message.pop('arguments', None)
                try:
                    channel.sendall((json.dumps(value, default=str) + '\n').encode())
                except (BrokenPipeError, ConnectionResetError):
                    if ctx.get('log'):
                        append_log(ctx['log'], 'Client disconnected', 'Session remains available after reply loss.')
            if not ctx.get('session') and message.get('operation') in ('kill', 'run'):
                close = getattr(ctx['backend'], 'close', None)
                if close:
                    close(ctx)
                root.joinpath('.active-session.json').unlink(missing_ok=True)
                break
    folder.joinpath('m.sock').unlink(missing_ok=True)


def start(args, root):
    """Resolve the app owner and start one connection-owning runtime.
    The locator reserves the context before launching the app.
    """
    ctx = context(args, root)
    try:
        selected = resolve_selection(ctx, args, need_destination=False)
    except BaseException:
        ctx['backend'].close(ctx)
        raise
    if selected['status'] != 'success':
        close = getattr(ctx['backend'], 'close', None)
        if close:
            close(ctx)
        return selected
    folder = ctx['data_dir']
    if folder.joinpath('m.sock').exists() and read_json(folder / 'session.json', {}).get('state') == 'closed':
        try:
            connect(folder, 'm.sock', {'operation':'_watch'}, timeout=.2)
        except (ConnectionRefusedError, FileNotFoundError):
            folder.joinpath('m.sock').unlink(missing_ok=True)
    if folder.joinpath('m.sock').exists():
        return ask('App control is not closed. Use Kill before another Run.')
    if ctx.get('evidence'):
        (folder / 'preflight-output.txt').write_text('\n'.join(ctx['evidence']))
    saved_args = {key: str(value) if isinstance(value, Path) else value for key, value in vars(args).items()}
    atomic_json(folder / 'runtime-request.json', {'args': saved_args, 'selection': ctx['selection'],
                                                'discovery': ctx['discovery']})
    close = getattr(ctx['backend'], 'close', None)
    if close:
        close(ctx)
    process = subprocess.Popen([sys.executable, str(root / 'scripts/manager.py'), '_serve', str(folder)],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
    capture_process(process, ctx, 'Runtime diagnostics')
    atomic_json(root / '.active-session.json', {'data_dir': str(folder), 'runtime_identity': capture_identity(process.pid)})
    deadline = time.monotonic() + 20
    while not (folder / 'm.sock').exists() and process.poll() is None and time.monotonic() < deadline:
        time.sleep(.05)
    if process.poll() is not None or not (folder / 'm.sock').exists():
        return ask('App setup failed. Use Kill before another Run.')
    return connect(folder, 'm.sock', saved_args, timeout=7500)


