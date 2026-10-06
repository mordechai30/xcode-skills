#!/usr/bin/env python3
"""Route macOS operations and retain the skill-owned backend connection.
Follow-up commands reach the same runtime through a relative local socket.
"""
import argparse
from lifecycle.runtime import namespace, serve, start
import json
from pathlib import Path
import sys
import time

from lifecycle.channel import connect
from lifecycle.process import verify_identity
from lifecycle.state import operation_lock, read_json
from lifecycle.output import collect
from lifecycle.response import emit, render
from operations import build, run, set_breakpoint, pause, continue_session, kill, debugger_command, status

# Explicit public operation routing; no reflective module discovery.
OPERATIONS = {"build": build, "run": run, "set-breakpoint": set_breakpoint, "pause": pause,
              "continue": continue_session, "kill": kill, "debugger-command": debugger_command, "status": status}


class RequestParser(argparse.ArgumentParser):
    """Keep help and argument errors on the bounded response path.
    Parsing never writes argparse diagnostics directly to stdout or stderr.
    """
    def error(self, message):
        """Return a parse error to the public entrypoint.
        Full argparse usage is replaced by the local examples reference.
        """
        raise ValueError(message)

    def print_help(self, file=None):
        """Provide compact help through the same public emitter.
        Detailed examples are packaged locally.
        """
        operation = next((word for word in sys.argv[1:] if word in OPERATIONS), '')
        help_text = {
            'build':'build (--project X|--workspace X|--package DIR) --configuration Debug|Release [--scheme NAME] [--target NAME|--product NAME]',
            'run':'run (--project X|--workspace X|--package DIR) --configuration Debug|Release [--no-debugger] [--arguments ARG… last]. Route options: references/examples.md#arguments',
            'set-breakpoint':'set-breakpoint --file PATH --line POSITIVE_NUMBER',
            'debugger-command':'debugger-command --command "LLDB COMMAND" [--detail]',
            'continue':'continue [--keep-breakpoint]',
            'pause':'pause: stop the running Debug app; 15-second limit.',
            'kill':'kill: stop the owned app and its dedicated helpers.',
            'status':'status: report running, paused, exited, unknown, or no app.'}
        emit((help_text.get(operation,'Commands: build run status set-breakpoint pause continue debugger-command kill. Use COMMAND --help. Run outside sandbox.'))+'\n')

from operations.common import ask, context, stop_fields

# Installed package root used for this skill's locator and metadata.
ROOT = Path(__file__).resolve().parents[1]


def parser():
    """Create the shared CLI inputs.
    Private service inputs are accepted only by the runtime entry path.
    """
    result = RequestParser(description='Manage one macOS Xcode app or SwiftPM executable context.')
    result.add_argument('operation', choices=['build', 'run', 'set-breakpoint', 'pause', 'continue', 'kill', 'debugger-command', 'status'])
    for key in ('project', 'workspace', 'package', 'file', 'working-directory', 'derived-data'):
        result.add_argument('--' + key, type=Path)
    result.add_argument('--configuration', choices=['Debug', 'Release'])
    for key in ('scheme', 'destination', 'command'):
        result.add_argument('--' + key)
    result.add_argument('--target')
    result.add_argument('--product')
    result.add_argument('--architecture', choices=['arm64', 'x86_64'])
    result.add_argument('--line', type=int)
    result.add_argument('--no-debugger', action='store_true')
    result.add_argument('--keep-breakpoint', action='store_true')
    result.add_argument('--detail', action='store_true')
    result.add_argument('--arguments', nargs=argparse.REMAINDER, default=None)
    return result


def validate(args):
    """Reject incomplete requests before backend actions.
    Discovery fills selections only when exactly one candidate exists.
    """
    allowed = {'build': {'project','workspace','package','configuration','scheme','target','product','destination','derived_data','architecture'},
               'run': {'project','workspace','package','configuration','scheme','target','product','destination','derived_data','architecture','arguments','working_directory','no_debugger'},
               'set-breakpoint': {'file','line'}, 'continue': {'keep_breakpoint'},
               'debugger-command': {'command','detail'}, 'pause': set(), 'kill': set(), 'status': set()}
    for key, value in vars(args).items():
        if key != 'operation' and value is not None and value is not False and key not in allowed[args.operation]:
            raise ValueError('--' + key.replace('_','-') + ' does not apply to ' + args.operation + '.')
    if args.package and args.target:
        raise ValueError('Use --product for a package; omit --target.')
    if (args.project or args.workspace) and args.product:
        raise ValueError('Use --target for Xcode; omit --product.')
    args.target = args.target or args.product
    if args.package and args.scheme:
        raise ValueError('SwiftPM selection uses --product; omit --scheme.')
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
    Surface the outcome and useful errors in the public response.
    """
    args._context = ctx
    deadline = getattr(args, '_deadline', None)
    if deadline is not None and time.monotonic() >= deadline:
        return {'status':'uncertain','stage':'pause','state':'uncertain','message':'Pause expired before execution. Use Status.'}
    ctx['request_deadline'] = deadline
    try:
        value = OPERATIONS[args.operation].execute(args, ROOT)
    except ValueError as error:
        value = {'status':'failure','stage':'validate','message':str(error)}
    except Exception as error:
        value = {'status': 'uncertain', 'message': str(error)}
    ctx.pop('request_deadline', None)
    collect(ctx)
    for kind in ('warning','error'):
        if ctx.get('public_'+kind):
            value[kind] = ctx.pop('public_'+kind)
            count = ctx.pop('public_'+kind+'_count',1)
            if count > 1:
                value[kind] += ' ('+str(count-1)+' more.)'
    return value


def main():
    """Send a request and report verified outcomes.
    Interrupted watching leaves app and debugger state unchanged.
    """
    if len(sys.argv) > 1 and sys.argv[1] == '_serve':
        serve(Path(sys.argv[2]), ROOT, dispatch)
        return 0
    submitted = time.monotonic()
    args = parser().parse_args()
    validate(args)
    values = {key: str(value.resolve()) if isinstance(value, Path) else value for key, value in vars(args).items()}
    if args.operation == 'pause':
        values['_deadline'] = submitted + 15
    with operation_lock(ROOT, deadline=values.get('_deadline')):
        locator = read_json(ROOT / '.active-session.json')
        if locator:
            if args.operation in ('build', 'run'):
                result = ask('Kill and complete cleanup before Build or another Run.', ['kill', 'wait'])
            elif not locator.get('runtime_identity') or not verify_identity(locator['runtime_identity']):
                if args.operation == 'kill':
                    from operations.kill import recover
                    result = recover(ROOT, locator)
                else:
                    result = ask('App control is unavailable. Use Kill before another Run.', ['kill', 'wait'])
            else:
                try:
                    result = connect(locator['data_dir'], 'm.sock', values, timeout=max(.001, values['_deadline'] - time.monotonic()) if '_deadline' in values else 60)
                except (OSError, RuntimeError) as error:
                    if args.operation == 'kill':
                        from operations.kill import recover
                        result = recover(ROOT, locator)
                    else:
                        result = ask('App control is unavailable: ' + str(error), ['kill', 'wait'])
        elif args.operation == 'run':
            result = start(namespace(values), ROOT)
            locator = read_json(ROOT / '.active-session.json')
        elif args.operation == 'build':
            ctx = context(args, ROOT)
            result = dispatch(args, ctx)
            close = getattr(ctx['backend'], 'close', None)
            if close:
                close(ctx)
        elif args.operation == 'status':
            result = {'status': 'success', 'state': 'none'}
        else:
            result = ask('No skill-owned app session exists. Use Run first.')
    if result.get('watch') and locator:
        try:
            while True:
                state = connect(locator['data_dir'], 'm.sock', {'operation': '_watch'})
                if state.get('state') != 'running':
                    result.update(status=state.get('status', 'uncertain'), **stop_fields(state))
                    result.update({key:state[key] for key in ('warning','error') if state.get(key)})
                    if args.operation == 'set-breakpoint':
                        result['_hit'] = any(result.get('breakpoint') in stop.get('breakpoints',[]) for stop in state.get('stops',[]))
                    break
                time.sleep(.3)
        except KeyboardInterrupt:
            try:
                state = connect(locator['data_dir'], 'm.sock', {'operation': '_watch'})
            except (OSError, RuntimeError):
                state = {'status': 'uncertain', 'state': 'uncertain'}
            result.update(status=state.get('status', 'uncertain'), _interrupted=True, **stop_fields(state))
        except (OSError, RuntimeError) as error:
            result.update(status='uncertain', state='uncertain', message='Watching stopped. Use Status or Kill.')
    result['_detail'] = args.detail
    text = render(result, args.operation)
    emit(text)
    return 0 if result.get('status') == 'success' else 1


def emit_exception(result):
    """Emit one bounded exceptional response.
    Do not query the backend again after interruption.
    """
    operation = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] in OPERATIONS else ''
    text = render(result, operation)
    emit(text)


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except ValueError as error:
        emit({'status':'failure','stage':'validate','message':str(error)},sys.argv[1] if len(sys.argv)>1 and sys.argv[1] in OPERATIONS else '')
        raise SystemExit(2)
    except KeyboardInterrupt:
        emit_exception({'status': 'uncertain', 'message': 'Request interrupted. Use Status.'})
        raise SystemExit(130)
    except Exception as error:
        emit_exception({'status': 'uncertain', 'message': str(error)})
        raise SystemExit(2)
