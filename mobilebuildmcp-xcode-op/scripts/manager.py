#!/usr/bin/env python3
"""Route macOS operations and retain the skill-owned backend connection.
Follow-up commands reach the same runtime through a relative local socket.
"""
import argparse
import importlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time

from lifecycle.channel import connect
from lifecycle.process import capture_identity, verify_identity
from lifecycle.state import append_log, atomic_json, operation_lock, read_json
from lifecycle.output import collect
from operations.common import ask, context, resolve_selection, observe

# Installed package root used for this skill's locator and metadata.
ROOT = Path(__file__).resolve().parents[1]


def parser():
    """Create the shared CLI inputs.
    Private service inputs are accepted only by the runtime entry path.
    """
    result = argparse.ArgumentParser(description='Manage one macOS Xcode app or SwiftPM executable context.')
    result.add_argument('operation', choices=['build', 'run', 'set-breakpoint', 'pause', 'continue', 'kill', 'debugger-command'])
    for key in ('project', 'workspace', 'package', 'file', 'working-directory', 'derived-data'):
        result.add_argument('--' + key, type=Path)
    result.add_argument('--configuration', choices=['Debug', 'Release'])
    for key in ('scheme', 'destination', 'command'):
        result.add_argument('--' + key)
    result.add_argument('--target', '--product', dest='target')
    result.add_argument('--architecture', choices=['arm64', 'x86_64'])
    result.add_argument('--line', type=int)
    result.add_argument('--no-debugger', action='store_true')
    result.add_argument('--keep-breakpoint', action='store_true')
    result.add_argument('--arguments', nargs=argparse.REMAINDER, default=[])
    return result


def validate(args):
    """Reject incomplete requests before backend actions.
    Discovery fills selections only when exactly one candidate exists.
    """
    if sum(bool(getattr(args, key, None)) for key in ('project', 'workspace', 'package')) > 1:
        raise ValueError('Select one project, workspace, or package.')
    if args.operation in ('build', 'run') and (not (args.project or args.workspace or args.package) or not args.configuration):
        raise ValueError('Build and Run require a container and configuration.')
    if args.operation == 'set-breakpoint' and (not args.file or not args.file.is_file() or not args.line or args.line < 1):
        raise ValueError('Set Breakpoint requires an existing source file and a positive line.')
    if args.operation == 'debugger-command' and not args.command:
        raise ValueError('Inspection requires --command.')
    if args.keep_breakpoint and args.operation != 'continue':
        raise ValueError('--keep-breakpoint applies only to Continue.')


def dispatch(args, ctx):
    """Call one imported operation against the retained context.
    Save complete results and errors in the session log.
    """
    args._context = ctx
    module = 'continue_session' if args.operation == 'continue' else args.operation.replace('-', '_')
    try:
        value = importlib.import_module('operations.' + module).execute(args, ROOT)
    except ValueError as error:
        value = ask(str(error))
    except (RuntimeError, OSError, TimeoutError) as error:
        value = {'status': 'uncertain', 'message': str(error)}
    if ctx.get('log'):
        append_log(ctx['log'], args.operation, json.dumps(value, default=str))
    collect(ctx)
    return value


def namespace(values):
    """Restore JSON requests to argparse inputs.
    Path inputs use the same types as the public CLI.
    """
    for key in ('project', 'workspace', 'package', 'file', 'working_directory', 'derived_data'):
        if values.get(key):
            values[key] = Path(values[key])
    return argparse.Namespace(**values)


def serve(folder):
    """Own the backend connection until required cleanup completes.
    Watching is performed by brief status requests outside this loop.
    """
    bootstrap = read_json(folder / 'runtime-request.json')
    args = namespace(bootstrap['args'])
    ctx = context(args, ROOT)
    ctx.update(data_dir=folder, selection=bootstrap['selection'], discovery=bootstrap['discovery'],
               runtime_identity=capture_identity(os.getpid()))
    ctx['discovery'] = None
    os.chdir(folder)
    with socket.socket(socket.AF_UNIX) as server:
        server.bind('m.sock')
        os.chmod('m.sock', 0o600)
        server.listen(8)
        atomic_json(ROOT / '.active-session.json', {'data_dir': str(folder), 'selection': ctx['selection'],
                                                  'runtime_identity': ctx['runtime_identity']})
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
                    if value.get('state') != 'running' and ctx.get('log'):
                        append_log(ctx['log'], 'Watch ended', json.dumps(value))
                else:
                    request = namespace(message)
                    conflict = message['operation'] != 'run' and any(message.get(key) and str(message[key]) != str(ctx['selection'].get(key))
                                   for key in ('project', 'workspace', 'package', 'configuration', 'scheme', 'target', 'destination'))
                    value = ask('Supplied selection conflicts with the active context.') if conflict else dispatch(request, ctx)
                try:
                    channel.sendall((json.dumps(value, default=str) + '\n').encode())
                except (BrokenPipeError, ConnectionResetError):
                    if ctx.get('log'):
                        append_log(ctx['log'], 'Client disconnected', 'Session remains available after reply loss.')
            if not ctx.get('session') and message.get('operation') in ('kill', 'run'):
                close = getattr(ctx['backend'], 'close', None)
                if close:
                    close(ctx)
                ROOT.joinpath('.active-session.json').unlink(missing_ok=True)
                break
    folder.joinpath('m.sock').unlink(missing_ok=True)


def start(args):
    """Resolve the app owner and start one connection-owning runtime.
    The locator reserves the context before launching the app.
    """
    ctx = context(args, ROOT)
    selected = resolve_selection(ctx, args)
    if selected['status'] != 'success':
        close = getattr(ctx['backend'], 'close', None)
        if close:
            close(ctx)
        return selected
    folder = ctx['data_dir']
    if folder.joinpath('m.sock').exists():
        return ask('An old socket remains. Inspect its runtime and cleanup records before Run.')
    saved_args = {key: str(value) if isinstance(value, Path) else value for key, value in vars(args).items()}
    atomic_json(folder / 'runtime-request.json', {'args': saved_args, 'selection': ctx['selection'],
                                                'discovery': ctx['discovery']})
    close = getattr(ctx['backend'], 'close', None)
    if close:
        close(ctx)
    output = (folder / 'runtime-output.txt').open('a')
    process = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), '_serve', str(folder)],
                               stdout=output, stderr=output, start_new_session=True)
    output.close()
    atomic_json(ROOT / '.active-session.json', {'data_dir': str(folder), 'selection': ctx['selection'],
                                              'runtime_identity': capture_identity(process.pid)})
    deadline = time.monotonic() + 20
    while not (folder / 'm.sock').exists() and process.poll() is None and time.monotonic() < deadline:
        time.sleep(.05)
    if process.poll() is not None or not (folder / 'm.sock').exists():
        return ask('Runtime initialization failed. Inspect runtime-output.txt before cleanup.')
    return connect(folder, 'm.sock', saved_args, timeout=7500)


def main():
    """Send a request and report verified outcomes.
    Interrupted watching leaves app and debugger state unchanged.
    """
    if len(sys.argv) > 1 and sys.argv[1] == '_serve':
        serve(Path(sys.argv[2]))
        return 0
    args = parser().parse_args()
    validate(args)
    values = {key: str(value.resolve()) if isinstance(value, Path) else value for key, value in vars(args).items()}
    with operation_lock(ROOT):
        locator = read_json(ROOT / '.active-session.json')
        if locator:
            if args.operation in ('build', 'run'):
                result = ask('Kill and complete cleanup before Build or another Run.', ['kill', 'wait'])
            elif not locator.get('runtime_identity') or not verify_identity(locator['runtime_identity']):
                if args.operation == 'kill':
                    from operations.kill import recover
                    result = recover(ROOT, locator)
                else:
                    result = ask('Retained runtime is lost. Use Kill recovery; do not attach another debugger.', ['kill', 'wait'])
            else:
                try:
                    result = connect(locator['data_dir'], 'm.sock', values, timeout=120)
                except (OSError, RuntimeError) as error:
                    if args.operation == 'kill':
                        from operations.kill import recover
                        result = recover(ROOT, locator)
                    else:
                        result = ask('Retained channel is lost: ' + str(error), ['kill', 'wait'])
        elif args.operation == 'run':
            result = start(namespace(values))
            locator = read_json(ROOT / '.active-session.json')
        elif args.operation == 'build':
            ctx = context(args, ROOT)
            result = dispatch(args, ctx)
            close = getattr(ctx['backend'], 'close', None)
            if close:
                close(ctx)
        else:
            result = ask('No skill-owned app session exists. Use Run first.')
    print(json.dumps(result, indent=2, default=str), flush=True)
    if result.get('watch') and locator:
        try:
            while True:
                state = connect(locator['data_dir'], 'm.sock', {'operation': '_watch'})
                if state.get('state') != 'running':
                    print(json.dumps(state, indent=2, default=str), flush=True)
                    break
                time.sleep(.3)
        except KeyboardInterrupt:
            print(json.dumps({'status': 'success', 'message': 'Watching interrupted. Session remains available.'}))
    return 0 if result.get('status') == 'success' else 1


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except ValueError as error:
        print(json.dumps(ask(str(error))))
        raise SystemExit(2)
    except (RuntimeError, OSError) as error:
        print(json.dumps({'status': 'uncertain', 'message': str(error)}))
        raise SystemExit(2)
